from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Character, CharacterReference
from app.models.enums import CharacterReferenceCategory
from app.schemas.character_reference import CharacterReferenceRead
from app.storage import get_storage
from app.storage.base import StorageBackend
from app.utils.paths import character_reference_path

router = APIRouter(tags=["character-references"])


def _get_character_or_404(db: Session, character_id: int) -> Character:
    character = db.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character


@router.get("/api/characters/{character_id}/references", response_model=list[CharacterReferenceRead])
def list_character_references(character_id: int, db: Session = Depends(get_db)):
    _get_character_or_404(db, character_id)
    return (
        db.query(CharacterReference)
        .filter(CharacterReference.character_id == character_id)
        .order_by(CharacterReference.category, CharacterReference.id)
        .all()
    )


@router.post(
    "/api/characters/{character_id}/references",
    response_model=CharacterReferenceRead,
    status_code=201,
)
async def upload_character_reference(
    character_id: int,
    category: CharacterReferenceCategory = Form(...),
    notes: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    storage: StorageBackend = Depends(get_storage),
):
    character = _get_character_or_404(db, character_id)
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="Reference must be an image file")
    content = await file.read()
    relative_path = character_reference_path(
        character.series.series_code, character.character_code, file.filename or "reference.png"
    )
    storage.save(relative_path, content)

    reference = CharacterReference(
        character_id=character_id, category=category, image_path=relative_path, notes=notes
    )
    db.add(reference)
    db.commit()
    db.refresh(reference)
    return reference


@router.delete("/api/character-references/{reference_id}", status_code=204)
def delete_character_reference(
    reference_id: int,
    db: Session = Depends(get_db),
    storage: StorageBackend = Depends(get_storage),
):
    reference = db.get(CharacterReference, reference_id)
    if not reference:
        raise HTTPException(status_code=404, detail="Reference not found")
    storage.delete(reference.image_path)
    db.delete(reference)
    db.commit()
