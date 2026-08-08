from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Character, Series
from app.schemas.character import CharacterCreate, CharacterRead, CharacterUpdate
from app.utils.codes import generate_unique_code, slugify_upper

router = APIRouter(tags=["characters"])


def _get_series_or_404(db: Session, series_id: int) -> Series:
    series = db.get(Series, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    return series


@router.get("/api/series/{series_id}/characters", response_model=list[CharacterRead])
def list_characters(series_id: int, db: Session = Depends(get_db)):
    _get_series_or_404(db, series_id)
    return (
        db.query(Character)
        .filter(Character.series_id == series_id)
        .order_by(Character.id)
        .all()
    )


@router.post("/api/series/{series_id}/characters", response_model=CharacterRead, status_code=201)
def create_character(series_id: int, payload: CharacterCreate, db: Session = Depends(get_db)):
    _get_series_or_404(db, series_id)
    slug = slugify_upper(payload.name)
    code = generate_unique_code(db, Character, Character.character_code, f"CHAR_{slug}")
    character = Character(series_id=series_id, character_code=code, **payload.model_dump())
    db.add(character)
    db.commit()
    db.refresh(character)
    return character


@router.get("/api/characters/{character_id}", response_model=CharacterRead)
def get_character(character_id: int, db: Session = Depends(get_db)):
    character = db.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character


@router.patch("/api/characters/{character_id}", response_model=CharacterRead)
def update_character(character_id: int, payload: CharacterUpdate, db: Session = Depends(get_db)):
    character = db.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(character, field, value)
    db.commit()
    db.refresh(character)
    return character


@router.delete("/api/characters/{character_id}", status_code=204)
def delete_character(character_id: int, db: Session = Depends(get_db)):
    character = db.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    db.delete(character)
    db.commit()
