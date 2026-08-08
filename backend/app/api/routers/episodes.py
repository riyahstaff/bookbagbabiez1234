from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Episode, Series
from app.schemas.episode import EpisodeCreate, EpisodeRead, EpisodeUpdate

router = APIRouter(tags=["episodes"])


def _get_series_or_404(db: Session, series_id: int) -> Series:
    series = db.get(Series, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    return series


@router.get("/api/series/{series_id}/episodes", response_model=list[EpisodeRead])
def list_episodes(series_id: int, db: Session = Depends(get_db)):
    _get_series_or_404(db, series_id)
    return (
        db.query(Episode)
        .filter(Episode.series_id == series_id)
        .order_by(Episode.episode_number)
        .all()
    )


@router.post("/api/series/{series_id}/episodes", response_model=EpisodeRead, status_code=201)
def create_episode(series_id: int, payload: EpisodeCreate, db: Session = Depends(get_db)):
    _get_series_or_404(db, series_id)
    existing = (
        db.query(Episode)
        .filter(
            Episode.series_id == series_id,
            Episode.episode_number == payload.episode_number,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Episode {payload.episode_number} already exists in this series",
        )
    episode = Episode(
        series_id=series_id,
        episode_code=f"EP_{payload.episode_number:03d}",
        **payload.model_dump(),
    )
    db.add(episode)
    db.commit()
    db.refresh(episode)
    return episode


@router.get("/api/episodes/{episode_id}", response_model=EpisodeRead)
def get_episode(episode_id: int, db: Session = Depends(get_db)):
    episode = db.get(Episode, episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    return episode


@router.patch("/api/episodes/{episode_id}", response_model=EpisodeRead)
def update_episode(episode_id: int, payload: EpisodeUpdate, db: Session = Depends(get_db)):
    episode = db.get(Episode, episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(episode, field, value)
    db.commit()
    db.refresh(episode)
    return episode


@router.delete("/api/episodes/{episode_id}", status_code=204)
def delete_episode(episode_id: int, db: Session = Depends(get_db)):
    episode = db.get(Episode, episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    db.delete(episode)
    db.commit()
