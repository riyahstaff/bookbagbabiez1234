from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Prop, PropReference, Series
from app.schemas.prop import PropCreate, PropRead, PropReferenceRead, PropUpdate
from app.storage import get_storage
from app.storage.base import StorageBackend
from app.utils.codes import generate_unique_slug_code, slugify_upper
from app.utils.paths import prop_reference_path

router = APIRouter(tags=["props"])


def _get_series_or_404(db: Session, series_id: int) -> Series:
    series = db.get(Series, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    return series


def _get_prop_or_404(db: Session, prop_id: int) -> Prop:
    prop = db.get(Prop, prop_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Prop not found")
    return prop


@router.get("/api/series/{series_id}/props", response_model=list[PropRead])
def list_props(series_id: int, db: Session = Depends(get_db)):
    _get_series_or_404(db, series_id)
    return db.query(Prop).filter(Prop.series_id == series_id).order_by(Prop.id).all()


@router.post("/api/series/{series_id}/props", response_model=PropRead, status_code=201)
def create_prop(series_id: int, payload: PropCreate, db: Session = Depends(get_db)):
    _get_series_or_404(db, series_id)
    code = generate_unique_slug_code(db, Prop, Prop.prop_code, f"PROP_{slugify_upper(payload.name)}")
    prop = Prop(series_id=series_id, prop_code=code, **payload.model_dump())
    db.add(prop)
    db.commit()
    db.refresh(prop)
    return prop


@router.get("/api/props/{prop_id}", response_model=PropRead)
def get_prop(prop_id: int, db: Session = Depends(get_db)):
    return _get_prop_or_404(db, prop_id)


@router.patch("/api/props/{prop_id}", response_model=PropRead)
def update_prop(prop_id: int, payload: PropUpdate, db: Session = Depends(get_db)):
    prop = _get_prop_or_404(db, prop_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(prop, field, value)
    db.commit()
    db.refresh(prop)
    return prop


@router.delete("/api/props/{prop_id}", status_code=204)
def delete_prop(prop_id: int, db: Session = Depends(get_db)):
    prop = _get_prop_or_404(db, prop_id)
    db.delete(prop)
    db.commit()


@router.get("/api/props/{prop_id}/references", response_model=list[PropReferenceRead])
def list_prop_references(prop_id: int, db: Session = Depends(get_db)):
    _get_prop_or_404(db, prop_id)
    return (
        db.query(PropReference).filter(PropReference.prop_id == prop_id).order_by(PropReference.id).all()
    )


@router.post("/api/props/{prop_id}/references", response_model=PropReferenceRead, status_code=201)
async def upload_prop_reference(
    prop_id: int,
    label: str | None = Form(None),
    notes: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    storage: StorageBackend = Depends(get_storage),
):
    prop = _get_prop_or_404(db, prop_id)
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="Reference must be an image file")
    content = await file.read()
    relative_path = prop_reference_path(
        prop.series.series_code, prop.prop_code, file.filename or "reference.png"
    )
    storage.save(relative_path, content)

    reference = PropReference(prop_id=prop_id, label=label, image_path=relative_path, notes=notes)
    db.add(reference)
    db.commit()
    db.refresh(reference)
    return reference


@router.delete("/api/prop-references/{reference_id}", status_code=204)
def delete_prop_reference(
    reference_id: int,
    db: Session = Depends(get_db),
    storage: StorageBackend = Depends(get_storage),
):
    reference = db.get(PropReference, reference_id)
    if not reference:
        raise HTTPException(status_code=404, detail="Reference not found")
    storage.delete(reference.image_path)
    db.delete(reference)
    db.commit()
