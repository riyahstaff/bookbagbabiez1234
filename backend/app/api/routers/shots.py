from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.llm_helpers import run_llm_stage
from app.database import get_db
from app.models import Character, Scene, SceneStatus, Shot, ShotCharacter, ShotType
from app.pipeline.generation import generate_shot_breakdown
from app.pipeline.shot_prompt import build_shot_prompt
from app.providers.llm import get_mechanical_llm
from app.providers.llm.base import LLMProvider
from app.schemas.shot import ShotCharactersUpdate, ShotCreate, ShotRead, ShotUpdate

router = APIRouter(tags=["shots"])


def _get_scene_or_404(db: Session, scene_id: int) -> Scene:
    scene = db.get(Scene, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    return scene


def _get_shot_or_404(db: Session, shot_id: int) -> Shot:
    shot = db.get(Shot, shot_id)
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")
    return shot


@router.get("/api/scenes/{scene_id}/shots", response_model=list[ShotRead])
def list_shots(scene_id: int, db: Session = Depends(get_db)):
    _get_scene_or_404(db, scene_id)
    return db.query(Shot).filter(Shot.scene_id == scene_id).order_by(Shot.shot_number).all()


@router.post("/api/scenes/{scene_id}/shots", response_model=ShotRead, status_code=201)
def create_shot(scene_id: int, payload: ShotCreate, db: Session = Depends(get_db)):
    _get_scene_or_404(db, scene_id)
    existing = (
        db.query(Shot).filter(Shot.scene_id == scene_id, Shot.shot_number == payload.shot_number).first()
    )
    if existing:
        raise HTTPException(
            status_code=409, detail=f"Shot {payload.shot_number} already exists in this scene"
        )
    shot = Shot(scene_id=scene_id, **payload.model_dump())
    db.add(shot)
    db.commit()
    db.refresh(shot)
    return shot


@router.post("/api/scenes/{scene_id}/generate-shots", response_model=list[ShotRead], status_code=201)
def generate_shots(
    scene_id: int, db: Session = Depends(get_db), llm: LLMProvider = Depends(get_mechanical_llm)
):
    scene = _get_scene_or_404(db, scene_id)
    if db.query(Shot).filter(Shot.scene_id == scene_id).first():
        raise HTTPException(
            status_code=409,
            detail="This scene already has shots. Delete them first if you want to regenerate.",
        )
    characters_in_scene = [sc.character for sc in scene.characters]
    series = scene.episode.series

    breakdown = run_llm_stage(generate_shot_breakdown, llm, scene, series, characters_in_scene)

    character_by_name = {c.name.lower(): c for c in characters_in_scene}

    shots = []
    for draft in breakdown.shots:
        shot = Shot(
            scene_id=scene_id,
            shot_number=draft.shot_number,
            shot_type=_coerce_shot_type(draft.shot_type),
            camera_angle=draft.camera_angle,
            camera_movement=draft.camera_movement,
            action=draft.action,
            dialogue=draft.dialogue,
            narration=draft.narration,
            emotion=draft.emotion,
            lighting=draft.lighting,
            duration_seconds=draft.duration_seconds,
        )
        db.add(shot)
        db.flush()
        for name in draft.characters_visible:
            character = character_by_name.get(name.lower())
            if character:
                db.add(ShotCharacter(shot_id=shot.id, character_id=character.id))
        shots.append(shot)

    scene.status = SceneStatus.SHOTS_READY
    db.commit()
    for shot in shots:
        db.refresh(shot)
    return shots


@router.get("/api/shots/{shot_id}", response_model=ShotRead)
def get_shot(shot_id: int, db: Session = Depends(get_db)):
    return _get_shot_or_404(db, shot_id)


@router.patch("/api/shots/{shot_id}", response_model=ShotRead)
def update_shot(shot_id: int, payload: ShotUpdate, db: Session = Depends(get_db)):
    shot = _get_shot_or_404(db, shot_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(shot, field, value)
    db.commit()
    db.refresh(shot)
    return shot


@router.delete("/api/shots/{shot_id}", status_code=204)
def delete_shot(shot_id: int, db: Session = Depends(get_db)):
    shot = _get_shot_or_404(db, shot_id)
    db.delete(shot)
    db.commit()


@router.put("/api/shots/{shot_id}/characters", response_model=ShotRead)
def set_shot_characters(shot_id: int, payload: ShotCharactersUpdate, db: Session = Depends(get_db)):
    shot = _get_shot_or_404(db, shot_id)
    series_id = shot.scene.episode.series_id
    for assignment in payload.characters:
        character = db.get(Character, assignment.character_id)
        if not character or character.series_id != series_id:
            raise HTTPException(
                status_code=400, detail=f"character_id {assignment.character_id} is not in this series"
            )
    db.query(ShotCharacter).filter(ShotCharacter.shot_id == shot_id).delete()
    for assignment in payload.characters:
        db.add(
            ShotCharacter(
                shot_id=shot_id, character_id=assignment.character_id, outfit_id=assignment.outfit_id
            )
        )
    db.commit()
    db.refresh(shot)
    return shot


@router.post("/api/shots/{shot_id}/build-prompt", response_model=ShotRead)
def build_prompt(shot_id: int, db: Session = Depends(get_db)):
    shot = _get_shot_or_404(db, shot_id)
    characters_visible = [sc.character for sc in shot.characters]
    series = shot.scene.episode.series
    visual_prompt, negative_prompt = build_shot_prompt(shot, shot.scene, series, characters_visible)
    shot.visual_prompt = visual_prompt
    shot.negative_prompt = negative_prompt
    db.commit()
    db.refresh(shot)
    return shot


def _coerce_shot_type(value: str) -> ShotType:
    try:
        return ShotType(value.upper())
    except ValueError:
        return ShotType.MEDIUM
