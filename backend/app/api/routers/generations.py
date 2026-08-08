import hashlib
import json
from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    ApprovalStatus,
    AudioTrack,
    Character,
    CharacterReference,
    CharacterReferenceCategory,
    Generation,
    GenerationStatus,
    GenerationType,
    Shot,
    Voice,
)
from app.pipeline.shot_prompt import build_shot_prompt
from app.providers.image import get_image_provider
from app.providers.image.base import ImageProvider
from app.providers.lipsync import get_lipsync_provider
from app.providers.lipsync.base import LipSyncProvider
from app.providers.video import get_video_provider
from app.providers.video.base import VideoProvider
from app.providers.voice import get_voice_provider
from app.providers.voice.base import VoiceProvider
from app.qc import QCResult, check_audio, check_image, check_video
from app.schemas.generation import (
    GenerateLipSyncRequest,
    GenerateStoryboardRequest,
    GenerateVideoRequest,
    GenerateVoiceRequest,
    GenerationRead,
)
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


def _pick_reference_image(character: Character) -> CharacterReference | None:
    # FRONT is the most identity-representative category when available;
    # any uploaded reference beats none for a single-character shot.
    for reference in character.references:
        if reference.category == CharacterReferenceCategory.FRONT:
            return reference
    return character.references[0] if character.references else None


def _run_qc(generation: Generation, check: Callable[[], QCResult]) -> None:
    # Advisory only - a bug in a QC check must never fail an otherwise
    # successful generation, so leave the score unset (not a false 0.0) and
    # explain why rather than letting the exception propagate.
    try:
        result = check()
        generation.quality_score = result.score
        generation.qc_notes = result.notes
    except Exception as exc:  # noqa: BLE001
        generation.qc_notes = f"Automated QC failed to run: {exc}"


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
    characters_visible = [sc.character for sc in shot.characters]

    if not shot.visual_prompt:
        series = shot.scene.episode.series
        visual_prompt, negative_prompt = build_shot_prompt(shot, shot.scene, series, characters_visible)
        shot.visual_prompt = visual_prompt
        shot.negative_prompt = shot.negative_prompt or negative_prompt
        db.flush()

    reference_image_bytes = None
    if provider.supports_reference_image() and len(characters_visible) == 1:
        reference = _pick_reference_image(characters_visible[0])
        if reference:
            reference_image_bytes = storage.read(reference.image_path)

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
            reference_image_bytes=reference_image_bytes,
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
        _run_qc(generation, lambda: check_image(result.image_bytes))
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
        generation.quality_score = cached.quality_score
        generation.qc_notes = cached.qc_notes
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
            _run_qc(generation, lambda: check_audio(result.audio_bytes))
        except Exception as exc:  # noqa: BLE001 - deliberately broad: any provider failure lands here
            generation.status = GenerationStatus.FAILED
            generation.error_message = str(exc)

    db.commit()
    db.refresh(generation)
    return generation


@router.post("/api/shots/{shot_id}/generate-video", response_model=GenerationRead, status_code=201)
def generate_video(
    shot_id: int,
    payload: GenerateVideoRequest,
    db: Session = Depends(get_db),
    provider: VideoProvider = Depends(get_video_provider),
    storage: StorageBackend = Depends(get_storage),
):
    shot = _get_shot_or_404(db, shot_id)
    reference_generation = shot.active_image_generation

    if not reference_generation or not reference_generation.output_path:
        raise HTTPException(
            status_code=409,
            detail="This shot has no active storyboard image yet - generate and activate one first.",
        )
    if not payload.override_approval_gate and reference_generation.approval_status != ApprovalStatus.APPROVED:
        raise HTTPException(
            status_code=409,
            detail=(
                "This shot's active storyboard image is not approved yet. Approve it first, "
                "or retry with override_approval_gate=true."
            ),
        )

    if not shot.visual_prompt:
        characters_visible = [sc.character for sc in shot.characters]
        series = shot.scene.episode.series
        visual_prompt, negative_prompt = build_shot_prompt(shot, shot.scene, series, characters_visible)
        shot.visual_prompt = visual_prompt
        shot.negative_prompt = shot.negative_prompt or negative_prompt
        db.flush()

    reference_image_bytes = storage.read(reference_generation.output_path)

    generation = Generation(
        shot_id=shot_id,
        generation_type=GenerationType.VIDEO,
        provider_name=type(provider).__name__,
        prompt=shot.visual_prompt,
        negative_prompt=shot.negative_prompt,
        seed=payload.seed,
        status=GenerationStatus.RUNNING,
    )
    db.add(generation)
    db.flush()

    try:
        result = provider.generate_video(
            prompt=shot.visual_prompt or "",
            reference_image_bytes=reference_image_bytes,
            negative_prompt=shot.negative_prompt,
            seed=payload.seed,
            duration_seconds=shot.duration_seconds,
        )
        episode = shot.scene.episode
        relative_path = generation_output_path(
            episode.series.series_code,
            episode.episode_code,
            shot_id,
            f"{generation.id}.{result.file_extension}",
        )
        storage.save(relative_path, result.video_bytes)
        generation.output_path = relative_path
        generation.model_name = result.model_name
        generation.status = GenerationStatus.COMPLETE
        _run_qc(generation, lambda: check_video(result.video_bytes, result.file_extension))
    except Exception as exc:  # noqa: BLE001 - deliberately broad: any provider failure lands here
        generation.status = GenerationStatus.FAILED
        generation.error_message = str(exc)

    db.commit()
    db.refresh(generation)
    return generation


@router.post("/api/shots/{shot_id}/generate-lipsync", response_model=GenerationRead, status_code=201)
def generate_lipsync(
    shot_id: int,
    payload: GenerateLipSyncRequest,
    db: Session = Depends(get_db),
    provider: LipSyncProvider = Depends(get_lipsync_provider),
    storage: StorageBackend = Depends(get_storage),
):
    shot = _get_shot_or_404(db, shot_id)
    video_generation = shot.active_video_generation
    dialogue_generation = shot.active_dialogue_generation

    if not video_generation or not video_generation.output_path:
        raise HTTPException(
            status_code=409,
            detail="This shot has no active video yet - generate and activate one first.",
        )
    if not dialogue_generation or not dialogue_generation.output_path:
        raise HTTPException(
            status_code=409,
            detail="This shot has no active dialogue audio yet - lip-sync needs speech to match to.",
        )
    if not payload.override_approval_gate and video_generation.approval_status != ApprovalStatus.APPROVED:
        raise HTTPException(
            status_code=409,
            detail=(
                "This shot's active video is not approved yet. Approve it first, "
                "or retry with override_approval_gate=true."
            ),
        )

    video_bytes = storage.read(video_generation.output_path)
    video_file_extension = video_generation.output_path.rsplit(".", 1)[-1]
    audio_bytes = storage.read(dialogue_generation.output_path)

    generation = Generation(
        shot_id=shot_id,
        generation_type=GenerationType.VIDEO,
        provider_name=type(provider).__name__,
        status=GenerationStatus.RUNNING,
    )
    db.add(generation)
    db.flush()

    try:
        result = provider.sync_lips(
            video_bytes=video_bytes, video_file_extension=video_file_extension, audio_bytes=audio_bytes
        )
        episode = shot.scene.episode
        relative_path = generation_output_path(
            episode.series.series_code,
            episode.episode_code,
            shot_id,
            f"{generation.id}.{result.file_extension}",
        )
        storage.save(relative_path, result.video_bytes)
        generation.output_path = relative_path
        generation.model_name = result.model_name
        generation.status = GenerationStatus.COMPLETE
        _run_qc(generation, lambda: check_video(result.video_bytes, result.file_extension))
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
