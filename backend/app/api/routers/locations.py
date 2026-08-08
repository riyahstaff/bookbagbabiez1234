from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Location, LocationReference, Series
from app.models.enums import LocationReferenceCategory
from app.schemas.location import LocationCreate, LocationRead, LocationReferenceRead, LocationUpdate
from app.storage import get_storage
from app.storage.base import StorageBackend
from app.utils.codes import generate_unique_code, slugify_upper
from app.utils.paths import location_reference_path

router = APIRouter(tags=["locations"])


def _get_series_or_404(db: Session, series_id: int) -> Series:
    series = db.get(Series, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    return series


def _get_location_or_404(db: Session, location_id: int) -> Location:
    location = db.get(Location, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location


@router.get("/api/series/{series_id}/locations", response_model=list[LocationRead])
def list_locations(series_id: int, db: Session = Depends(get_db)):
    _get_series_or_404(db, series_id)
    return db.query(Location).filter(Location.series_id == series_id).order_by(Location.id).all()


@router.post("/api/series/{series_id}/locations", response_model=LocationRead, status_code=201)
def create_location(series_id: int, payload: LocationCreate, db: Session = Depends(get_db)):
    _get_series_or_404(db, series_id)
    code = generate_unique_code(
        db, Location, Location.location_code, f"LOCATION_{slugify_upper(payload.name)}"
    )
    location = Location(series_id=series_id, location_code=code, **payload.model_dump())
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


@router.get("/api/locations/{location_id}", response_model=LocationRead)
def get_location(location_id: int, db: Session = Depends(get_db)):
    return _get_location_or_404(db, location_id)


@router.patch("/api/locations/{location_id}", response_model=LocationRead)
def update_location(location_id: int, payload: LocationUpdate, db: Session = Depends(get_db)):
    location = _get_location_or_404(db, location_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(location, field, value)
    db.commit()
    db.refresh(location)
    return location


@router.delete("/api/locations/{location_id}", status_code=204)
def delete_location(location_id: int, db: Session = Depends(get_db)):
    location = _get_location_or_404(db, location_id)
    db.delete(location)
    db.commit()


@router.get("/api/locations/{location_id}/references", response_model=list[LocationReferenceRead])
def list_location_references(location_id: int, db: Session = Depends(get_db)):
    _get_location_or_404(db, location_id)
    return (
        db.query(LocationReference)
        .filter(LocationReference.location_id == location_id)
        .order_by(LocationReference.category, LocationReference.id)
        .all()
    )


@router.post(
    "/api/locations/{location_id}/references", response_model=LocationReferenceRead, status_code=201
)
async def upload_location_reference(
    location_id: int,
    category: LocationReferenceCategory = Form(...),
    notes: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    storage: StorageBackend = Depends(get_storage),
):
    location = _get_location_or_404(db, location_id)
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="Reference must be an image file")
    content = await file.read()
    relative_path = location_reference_path(
        location.series.series_code, location.location_code, file.filename or "reference.png"
    )
    storage.save(relative_path, content)

    reference = LocationReference(
        location_id=location_id, category=category, image_path=relative_path, notes=notes
    )
    db.add(reference)
    db.commit()
    db.refresh(reference)
    return reference


@router.delete("/api/location-references/{reference_id}", status_code=204)
def delete_location_reference(
    reference_id: int,
    db: Session = Depends(get_db),
    storage: StorageBackend = Depends(get_storage),
):
    reference = db.get(LocationReference, reference_id)
    if not reference:
        raise HTTPException(status_code=404, detail="Reference not found")
    storage.delete(reference.image_path)
    db.delete(reference)
    db.commit()
