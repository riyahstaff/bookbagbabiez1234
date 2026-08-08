from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Character, Series, Voice
from app.schemas.voice import VoiceCreate, VoiceRead, VoiceUpdate
from app.storage import get_storage
from app.storage.base import StorageBackend
from app.utils.codes import generate_unique_code, slugify_upper
from app.utils.paths import voice_reference_audio_path

router = APIRouter(tags=["voices"])


def _get_series_or_404(db: Session, series_id: int) -> Series:
    series = db.get(Series, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    return series


def _get_voice_or_404(db: Session, voice_id: int) -> Voice:
    voice = db.get(Voice, voice_id)
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    return voice


def _validate_character(db: Session, series_id: int, character_id: int | None) -> None:
    if character_id is None:
        return
    character = db.get(Character, character_id)
    if not character or character.series_id != series_id:
        raise HTTPException(status_code=400, detail="character_id must belong to this series")


@router.get("/api/series/{series_id}/voices", response_model=list[VoiceRead])
def list_voices(series_id: int, db: Session = Depends(get_db)):
    _get_series_or_404(db, series_id)
    return db.query(Voice).filter(Voice.series_id == series_id).order_by(Voice.id).all()


@router.post("/api/series/{series_id}/voices", response_model=VoiceRead, status_code=201)
def create_voice(series_id: int, payload: VoiceCreate, db: Session = Depends(get_db)):
    _get_series_or_404(db, series_id)
    _validate_character(db, series_id, payload.character_id)
    code = generate_unique_code(db, Voice, Voice.voice_code, f"VOICE_{slugify_upper(payload.name)}")
    voice = Voice(series_id=series_id, voice_code=code, **payload.model_dump())
    db.add(voice)
    db.commit()
    db.refresh(voice)
    return voice


@router.get("/api/voices/{voice_id}", response_model=VoiceRead)
def get_voice(voice_id: int, db: Session = Depends(get_db)):
    return _get_voice_or_404(db, voice_id)


@router.patch("/api/voices/{voice_id}", response_model=VoiceRead)
def update_voice(voice_id: int, payload: VoiceUpdate, db: Session = Depends(get_db)):
    voice = _get_voice_or_404(db, voice_id)
    if "character_id" in payload.model_fields_set:
        _validate_character(db, voice.series_id, payload.character_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(voice, field, value)
    db.commit()
    db.refresh(voice)
    return voice


@router.delete("/api/voices/{voice_id}", status_code=204)
def delete_voice(
    voice_id: int,
    db: Session = Depends(get_db),
    storage: StorageBackend = Depends(get_storage),
):
    voice = _get_voice_or_404(db, voice_id)
    if voice.reference_audio_path:
        storage.delete(voice.reference_audio_path)
    db.delete(voice)
    db.commit()


@router.post("/api/voices/{voice_id}/reference-audio", response_model=VoiceRead)
async def upload_voice_reference_audio(
    voice_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    storage: StorageBackend = Depends(get_storage),
):
    voice = _get_voice_or_404(db, voice_id)
    if not (file.content_type or "").startswith("audio/"):
        raise HTTPException(status_code=400, detail="Reference must be an audio file")
    content = await file.read()
    if voice.reference_audio_path:
        storage.delete(voice.reference_audio_path)
    relative_path = voice_reference_audio_path(
        voice.series.series_code, voice.voice_code, file.filename or "reference.wav"
    )
    storage.save(relative_path, content)
    voice.reference_audio_path = relative_path
    db.commit()
    db.refresh(voice)
    return voice
