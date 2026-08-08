from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ApprovalStatus, Generation, GenerationStatus, GenerationType, Shot
from app.pipeline.shot_prompt import build_shot_prompt
from app.providers.image import get_image_provider
from app.providers.image.base import ImageProvider
from app.schemas.generation import GenerateStoryboardRequest, GenerationRead
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
    db.query(Generation).filter(
        Generation.shot_id == generation.shot_id, Generation.id != generation.id
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
        storage.delete(generation.output_path)
    db.delete(generation)
    db.commit()
