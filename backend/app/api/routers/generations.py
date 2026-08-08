import hashlib
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    ApprovalStatus,
    AudioTrack,
    Generation,
    GenerationStatus,
    GenerationType,
    Shot,
    Voice,
)
from app.pipeline.shot_prompt import build_shot_prompt
from app.providers.image import get_image_provider
from app.providers.image.base import ImageProvider
from app.providers.voice import get_voice_provider
from app.providers.voice.base import VoiceProvider
from app.schemas.generation import GenerateStoryboardRequest, GenerateVoiceRequest, GenerationRead
from app.storage import get_storage
from app.storage.base import StorageBackend
from app.utils.paths import generation_output_path

router = APIRouter(tags=["generations"])


def _get_shot_or_404(db: Session, shot_id: int) -> Shot:
    shot = db.get(Shot, shot_id)
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")
    return shot


def _get_generation_or_404(db: Session, generation_id: int) -> Generation:
    generation = db.get(Generation, generation_id)
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")
    return generation


@router.get("/api/shots/{shot_id}/generations", response_model=list[GenerationRead])
def list_generations(shot_id: int, db: Session = Depends(get_db)):
    _get_shot_or_404(db, shot_id)
    return (
        db.query(Generation)
        .filter(Generation.shot_id == shot_id)
        .order_by(Generation.id.desc())
        .all()
    )


@router.post(
    "/api/shots/{shot_id}/generate-storyboard", response_model=GenerationRead, status_code=201
)
def generate_storyboard(
    shot_id: int,
    payload: GenerateStoryboardRequest,
    db: Session = Depends(get_db),
    provider: ImageProvider = Depends(get_image_provider),
    storage: StorageBackend = Depends(get_storage),
):
    shot = _get_shot_or_404(db, shot_id)

    if not shot.visual_prompt:
        characters_visible = [sc.character for sc in shot.characters]
        series = shot.scene.episode.series
        visual_prompt, negative_prompt = build_shot_prompt(shot, shot.scene, series, characters_visible)
        shot.visual_prompt = visual_prompt
        shot.negative_prompt = shot.negative_prompt or negative_prompt
        db.flush()

    generation = Generation(
        shot_id=shot_id,
        generation_type=GenerationType.IMAGE,
        provider_name=type(provider).__name__,
        prompt=shot.visual_prompt,
        negative_prompt=shot.negative_prompt,
        seed=payload.seed,
        status=GenerationStatus.RUNNING,
    )
    db.add(generation)
    db.flush()

    try:
        result = provider.generate_image(
            prompt=shot.visual_prompt or "",
            negative_prompt=shot.negative_prompt,
            seed=payload.seed,
        )
        episode = shot.scene.episode
        relative_path = generation_output_path(
            episode.series.series_code, episode.episode_code, shot_id, f"{generation.id}.png"
        )
        storage.save(relative_path, result.image_bytes)
        generation.output_path = relative_path
        generation.model_name = result.model_name
        generation.seed = result.seed_used
        generation.status = GenerationStatus.COMPLETE
    except Exception as exc:  # noqa: BLE001 - deliberately broad: any provider failure lands here
        generation.status = GenerationStatus.FAILED
        generation.error_message = str(exc)

    db.commit()
    db.refresh(generation)
    return generation


def _voice_content_hash(text: str, voice_id: int, settings_snapshot: dict) -> str:
    payload = json.dumps(
        {"text": text, "voice_id": voice_id, "settings": settings_snapshot}, sort_keys=True
    )
    return hashlib.sha256(payload.encode()).hexdigest()


@router.post("/api/shots/{shot_id}/generate-voice", response_model=GenerationRead, status_code=201)
def generate_voice(
    shot_id: int,
    payload: GenerateVoiceRequest,
    db: Session = Depends(get_db),
    provider: VoiceProvider = Depends(get_voice_provider),
    storage: StorageBackend = Depends(get_storage),
):
    shot = _get_shot_or_404(db, shot_id)
    series_id = shot.scene.episode.series_id

    voice = db.get(Voice, payload.voice_id)
    if not voice or voice.series_id != series_id:
        raise HTTPException(status_code=400, detail="voice_id is not in this series")

    text = shot.dialogue if payload.track == AudioTrack.DIALOGUE else shot.narration
    if not text:
        raise HTTPException(
            status_code=400, detail=f"Shot has no {payload.track.value.lower()} text to synthesize"
        )

    settings_snapshot = {
        "speed": voice.speed,
        "pitch": voice.pitch,
        "emotion": voice.emotion,
        "seed": payload.seed,
        **(voice.generation_settings or {}),
    }
    content_hash = _voice_content_hash(text, voice.id, settings_snapshot)

    cached: Generation | None = None
    if not payload.force_regenerate:
        cached = (
            db.query(Generation)
            .filter(
                Generation.generation_type == GenerationType.VOICE,
                Generation.content_hash == content_hash,
                Generation.status == GenerationStatus.COMPLETE,
            )
            .first()
        )

    generation = Generation(
        shot_id=shot_id,
        generation_type=GenerationType.VOICE,
        audio_track=payload.track,
        voice_id=voice.id,
        provider_name=type(provider).__name__,
        prompt=text,
        seed=payload.seed,
        content_hash=content_hash,
        status=GenerationStatus.RUNNING,
    )
    db.add(generation)
    db.flush()

    if cached is not None:
        generation.output_path = cached.output_path
        generation.model_name = cached.model_name
        generation.status = GenerationStatus.COMPLETE
    else:
        try:
            extra_settings = {
                k: v
                for k, v in {"pitch": voice.pitch, "emotion": voice.emotion, "seed": payload.seed}.items()
                if v is not None
            }
            extra_settings.update(voice.generation_settings or {})
            result = provider.generate_speech(
                text=text,
                voice_identifier=voice.provider_voice_id or voice.voice_code,
                speed=voice.speed,
                extra_settings=extra_settings or None,
            )
            episode = shot.scene.episode
            relative_path = generation_output_path(
                episode.series.series_code, episode.episode_code, shot_id, f"{generation.id}.wav"
            )
            storage.save(relative_path, result.audio_bytes)
            generation.output_path = relative_path
            generation.model_name = result.model_name
            generation.status = GenerationStatus.COMPLETE
        except Exception as exc:  # noqa: BLE001 - deliberately broad: any provider failure lands here
            generation.status = GenerationStatus.FAILED
            generation.error_message = str(exc)

    db.commit()
    db.refresh(generation)
    return generation


@router.post("/api/generations/{generation_id}/approve", response_model=GenerationRead)
def approve_generation(generation_id: int, db: Session = Depends(get_db)):
    generation = _get_generation_or_404(db, generation_id)
    generation.approval_status = ApprovalStatus.APPROVED
    _activate(db, generation)
    db.commit()
    db.refresh(generation)
    return generation


@router.post("/api/generations/{generation_id}/reject", response_model=GenerationRead)
def reject_generation(generation_id: int, db: Session = Depends(get_db)):
    generation = _get_generation_or_404(db, generation_id)
    generation.approval_status = ApprovalStatus.REJECTED
    generation.is_active = False
    db.commit()
    db.refresh(generation)
    return generation


@router.post("/api/generations/{generation_id}/activate", response_model=GenerationRead)
def activate_generation(generation_id: int, db: Session = Depends(get_db)):
    generation = _get_generation_or_404(db, generation_id)
    _activate(db, generation)
    db.commit()
    db.refresh(generation)
    return generation


def _activate(db: Session, generation: Generation) -> None:
    # Scoped by (shot_id, generation_type, audio_track), not just shot_id: a
    # shot can have an active storyboard image, an active dialogue take, and
    # an active narration take all at once, and activating one must not
    # clear the other two.
    db.query(Generation).filter(
        Generation.shot_id == generation.shot_id,
        Generation.generation_type == generation.generation_type,
        Generation.audio_track == generation.audio_track,
        Generation.id != generation.id,
    ).update({"is_active": False})
    generation.is_active = True


@router.delete("/api/generations/{generation_id}", status_code=204)
def delete_generation(
    generation_id: int,
    db: Session = Depends(get_db),
    storage: StorageBackend = Depends(get_storage),
):
    generation = _get_generation_or_404(db, generation_id)
    if generation.output_path:
        # A cache hit in generate_voice() can leave two rows pointing at the
        # same physical file - only delete it once nothing else references it.
        still_referenced = (
            db.query(Generation)
            .filter(Generation.output_path == generation.output_path, Generation.id != generation.id)
            .first()
        )
        if not still_referenced:
            storage.delete(generation.output_path)
    db.delete(generation)
    db.commit()
