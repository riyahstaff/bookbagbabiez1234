from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Series
from app.schemas.series import SeriesCreate, SeriesRead, SeriesUpdate
from app.utils.codes import generate_unique_code

router = APIRouter(prefix="/api/series", tags=["series"])


@router.get("", response_model=list[SeriesRead])
def list_series(db: Session = Depends(get_db)):
    return db.query(Series).order_by(Series.id).all()


@router.post("", response_model=SeriesRead, status_code=201)
def create_series(payload: SeriesCreate, db: Session = Depends(get_db)):
    code = generate_unique_code(db, Series, Series.series_code, "SERIES")
    series = Series(series_code=code, **payload.model_dump())
    db.add(series)
    db.commit()
    db.refresh(series)
    return series


@router.get("/{series_id}", response_model=SeriesRead)
def get_series(series_id: int, db: Session = Depends(get_db)):
    series = db.get(Series, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    return series


@router.patch("/{series_id}", response_model=SeriesRead)
def update_series(series_id: int, payload: SeriesUpdate, db: Session = Depends(get_db)):
    series = db.get(Series, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(series, field, value)
    db.commit()
    db.refresh(series)
    return series


@router.delete("/{series_id}", status_code=204)
def delete_series(series_id: int, db: Session = Depends(get_db)):
    series = db.get(Series, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    db.delete(series)
    db.commit()
