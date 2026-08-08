from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.llm_helpers import run_llm_stage
from app.database import get_db
from app.models import (
    Character,
    Episode,
    EpisodeStatus,
    Location,
    Scene,
    SceneCharacter,
)
from app.pipeline.generation import generate_scene_breakdown
from app.providers.llm import get_mechanical_llm
from app.providers.llm.base import LLMProvider
from app.schemas.scene import SceneCharactersUpdate, SceneCreate, SceneRead, SceneUpdate

router = APIRouter(tags=["scenes"])


def _get_episode_or_404(db: Session, episode_id: int) -> Episode:
    episode = db.get(Episode, episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    return episode


def _get_scene_or_404(db: Session, scene_id: int) -> Scene:
    scene = db.get(Scene, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    return scene


@router.get("/api/episodes/{episode_id}/scenes", response_model=list[SceneRead])
def list_scenes(episode_id: int, db: Session = Depends(get_db)):
    _get_episode_or_404(db, episode_id)
    return db.query(Scene).filter(Scene.episode_id == episode_id).order_by(Scene.scene_number).all()


@router.post("/api/episodes/{episode_id}/scenes", response_model=SceneRead, status_code=201)
def create_scene(episode_id: int, payload: SceneCreate, db: Session = Depends(get_db)):
    _get_episode_or_404(db, episode_id)
    existing = (
        db.query(Scene)
        .filter(Scene.episode_id == episode_id, Scene.scene_number == payload.scene_number)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409, detail=f"Scene {payload.scene_number} already exists in this episode"
        )
    scene = Scene(episode_id=episode_id, **payload.model_dump())
    db.add(scene)
    db.commit()
    db.refresh(scene)
    return scene


@router.post(
    "/api/episodes/{episode_id}/generate-scenes", response_model=list[SceneRead], status_code=201
)
def generate_scenes(
    episode_id: int, db: Session = Depends(get_db), llm: LLMProvider = Depends(get_mechanical_llm)
):
    episode = _get_episode_or_404(db, episode_id)
    if db.query(Scene).filter(Scene.episode_id == episode_id).first():
        raise HTTPException(
            status_code=409,
            detail="This episode already has scenes. Delete them first if you want to regenerate.",
        )
    characters = db.query(Character).filter(Character.series_id == episode.series_id).all()
    locations = db.query(Location).filter(Location.series_id == episode.series_id).all()

    breakdown = run_llm_stage(
        generate_scene_breakdown, llm, episode, episode.series, characters, locations
    )

    character_by_name = {c.name.lower(): c for c in characters}
    location_by_name = {location.name.lower(): location for location in locations}

    scenes = []
    for draft in breakdown.scenes:
        location = location_by_name.get((draft.location_name or "").lower())
        scene = Scene(
            episode_id=episode_id,
            scene_number=draft.scene_number,
            location_id=location.id if location else None,
            time_of_day=draft.time_of_day,
            action_description=draft.action_description,
            dialogue=draft.dialogue,
            narration=draft.narration,
            emotional_tone=draft.emotional_tone,
            estimated_duration_seconds=draft.estimated_duration_seconds,
        )
        db.add(scene)
        db.flush()
        for name in draft.characters_present:
            character = character_by_name.get(name.lower())
            if character:
                db.add(SceneCharacter(scene_id=scene.id, character_id=character.id))
        scenes.append(scene)

    episode.status = EpisodeStatus.SCENES_READY
    db.commit()
    for scene in scenes:
        db.refresh(scene)
    return scenes


@router.get("/api/scenes/{scene_id}", response_model=SceneRead)
def get_scene(scene_id: int, db: Session = Depends(get_db)):
    return _get_scene_or_404(db, scene_id)


@router.patch("/api/scenes/{scene_id}", response_model=SceneRead)
def update_scene(scene_id: int, payload: SceneUpdate, db: Session = Depends(get_db)):
    scene = _get_scene_or_404(db, scene_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(scene, field, value)
    db.commit()
    db.refresh(scene)
    return scene


@router.delete("/api/scenes/{scene_id}", status_code=204)
def delete_scene(scene_id: int, db: Session = Depends(get_db)):
    scene = _get_scene_or_404(db, scene_id)
    db.delete(scene)
    db.commit()


@router.put("/api/scenes/{scene_id}/characters", response_model=SceneRead)
def set_scene_characters(scene_id: int, payload: SceneCharactersUpdate, db: Session = Depends(get_db)):
    scene = _get_scene_or_404(db, scene_id)
    for assignment in payload.characters:
        character = db.get(Character, assignment.character_id)
        if not character or character.series_id != scene.episode.series_id:
            raise HTTPException(
                status_code=400, detail=f"character_id {assignment.character_id} is not in this series"
            )
    db.query(SceneCharacter).filter(SceneCharacter.scene_id == scene_id).delete()
    for assignment in payload.characters:
        db.add(
            SceneCharacter(
                scene_id=scene_id, character_id=assignment.character_id, outfit_id=assignment.outfit_id
            )
        )
    db.commit()
    db.refresh(scene)
    return scene
