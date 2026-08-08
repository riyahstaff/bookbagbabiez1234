from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Character, CharacterOutfit, OutfitReference
from app.schemas.character_outfit import (
    CharacterOutfitCreate,
    CharacterOutfitRead,
    CharacterOutfitUpdate,
    OutfitReferenceRead,
)
from app.storage import get_storage
from app.storage.base import StorageBackend
from app.utils.codes import generate_unique_slug_code, slugify_upper
from app.utils.paths import outfit_reference_path

router = APIRouter(tags=["character-outfits"])


def _get_character_or_404(db: Session, character_id: int) -> Character:
    character = db.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character


def _get_outfit_or_404(db: Session, outfit_id: int) -> CharacterOutfit:
    outfit = db.get(CharacterOutfit, outfit_id)
    if not outfit:
        raise HTTPException(status_code=404, detail="Outfit not found")
    return outfit


@router.get("/api/characters/{character_id}/outfits", response_model=list[CharacterOutfitRead])
def list_outfits(character_id: int, db: Session = Depends(get_db)):
    _get_character_or_404(db, character_id)
    return (
        db.query(CharacterOutfit)
        .filter(CharacterOutfit.character_id == character_id)
        .order_by(CharacterOutfit.id)
        .all()
    )


@router.post("/api/characters/{character_id}/outfits", response_model=CharacterOutfitRead, status_code=201)
def create_outfit(character_id: int, payload: CharacterOutfitCreate, db: Session = Depends(get_db)):
    character = _get_character_or_404(db, character_id)
    character_slug = slugify_upper(character.name)
    outfit_slug = slugify_upper(payload.name)
    code = generate_unique_slug_code(
        db, CharacterOutfit, CharacterOutfit.outfit_code, f"OUTFIT_{character_slug}_{outfit_slug}"
    )
    outfit = CharacterOutfit(character_id=character_id, outfit_code=code, **payload.model_dump())
    db.add(outfit)
    db.commit()
    db.refresh(outfit)
    return outfit


@router.patch("/api/character-outfits/{outfit_id}", response_model=CharacterOutfitRead)
def update_outfit(outfit_id: int, payload: CharacterOutfitUpdate, db: Session = Depends(get_db)):
    outfit = _get_outfit_or_404(db, outfit_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(outfit, field, value)
    db.commit()
    db.refresh(outfit)
    return outfit


@router.delete("/api/character-outfits/{outfit_id}", status_code=204)
def delete_outfit(
    outfit_id: int,
    db: Session = Depends(get_db),
    storage: StorageBackend = Depends(get_storage),
):
    outfit = _get_outfit_or_404(db, outfit_id)
    for reference in outfit.references:
        storage.delete(reference.image_path)
    db.delete(outfit)
    db.commit()


@router.get("/api/character-outfits/{outfit_id}/references", response_model=list[OutfitReferenceRead])
def list_outfit_references(outfit_id: int, db: Session = Depends(get_db)):
    _get_outfit_or_404(db, outfit_id)
    return (
        db.query(OutfitReference)
        .filter(OutfitReference.outfit_id == outfit_id)
        .order_by(OutfitReference.id)
        .all()
    )


@router.post(
    "/api/character-outfits/{outfit_id}/references", response_model=OutfitReferenceRead, status_code=201
)
async def upload_outfit_reference(
    outfit_id: int,
    label: str | None = Form(None),
    notes: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    storage: StorageBackend = Depends(get_storage),
):
    outfit = _get_outfit_or_404(db, outfit_id)
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="Reference must be an image file")
    content = await file.read()
    character = outfit.character
    relative_path = outfit_reference_path(
        character.series.series_code,
        character.character_code,
        outfit.outfit_code,
        file.filename or "reference.png",
    )
    storage.save(relative_path, content)

    reference = OutfitReference(outfit_id=outfit_id, label=label, image_path=relative_path, notes=notes)
    db.add(reference)
    db.commit()
    db.refresh(reference)
    return reference


@router.delete("/api/outfit-references/{reference_id}", status_code=204)
def delete_outfit_reference(
    reference_id: int,
    db: Session = Depends(get_db),
    storage: StorageBackend = Depends(get_storage),
):
    reference = db.get(OutfitReference, reference_id)
    if not reference:
        raise HTTPException(status_code=404, detail="Reference not found")
    storage.delete(reference.image_path)
    db.delete(reference)
    db.commit()
