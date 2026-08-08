import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.assembler import AssemblyError, assemble_episode
from app.assembler.timeline import build_timeline
from app.database import get_db
from app.models import Episode, EpisodeExport, EpisodeStatus, GenerationStatus
from app.schemas.episode_export import (
    CreateEpisodeExportRequest,
    EpisodeExportPreview,
    EpisodeExportRead,
)
from app.storage import get_storage
from app.storage.base import StorageBackend
from app.utils.paths import episode_export_path

router = APIRouter(tags=["episode-exports"])


def _get_episode_or_404(db: Session, episode_id: int) -> Episode:
    episode = db.get(Episode, episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    return episode


def _get_export_or_404(db: Session, export_id: int) -> EpisodeExport:
    export = db.get(EpisodeExport, export_id)
    if not export:
        raise HTTPException(status_code=404, detail="Export not found")
    return export


@router.get("/api/episodes/{episode_id}/exports", response_model=list[EpisodeExportRead])
def list_exports(episode_id: int, db: Session = Depends(get_db)):
    _get_episode_or_404(db, episode_id)
    return (
        db.query(EpisodeExport)
        .filter(EpisodeExport.episode_id == episode_id)
        .order_by(EpisodeExport.id.desc())
        .all()
    )


@router.get("/api/episodes/{episode_id}/export-preview", response_model=EpisodeExportPreview)
def preview_export(episode_id: int, db: Session = Depends(get_db)):
    episode = _get_episode_or_404(db, episode_id)
    timeline = build_timeline(episode)
    return EpisodeExportPreview(
        renderable_shot_count=len(timeline.segments),
        skipped_shots=timeline.skipped_shots,
    )


@router.post("/api/episodes/{episode_id}/export", response_model=EpisodeExportRead, status_code=201)
def create_export(
    episode_id: int,
    payload: CreateEpisodeExportRequest,
    db: Session = Depends(get_db),
    storage: StorageBackend = Depends(get_storage),
):
    episode = _get_episode_or_404(db, episode_id)
    if not build_timeline(episode).segments:
        raise HTTPException(
            status_code=409,
            detail="This episode has no shots with an approved image or video to assemble yet.",
        )
    previous_status = episode.status

    export = EpisodeExport(
        episode_id=episode_id,
        status=GenerationStatus.RUNNING,
        include_titles=payload.include_titles,
        include_credits=payload.include_credits,
        include_subtitles=payload.include_subtitles,
    )
    db.add(export)
    episode.status = EpisodeStatus.RENDERING
    db.flush()

    try:
        with tempfile.TemporaryDirectory(prefix="acs_export_") as scratch_dir:
            scratch_output = Path(scratch_dir) / f"{export.id}.mp4"
            result = assemble_episode(
                episode,
                storage,
                scratch_output,
                include_titles=payload.include_titles,
                include_credits=payload.include_credits,
                include_subtitles=payload.include_subtitles,
            )
            relative_path = episode_export_path(
                episode.series.series_code, episode.episode_code, f"{export.id}.mp4"
            )
            storage.save_file(relative_path, scratch_output)

        export.output_path = relative_path
        export.duration_seconds = result.duration_seconds
        export.skipped_shots = result.skipped_shots
        export.status = GenerationStatus.COMPLETE
        episode.status = EpisodeStatus.QC
    except AssemblyError as exc:
        export.status = GenerationStatus.FAILED
        export.error_message = str(exc)
        episode.status = previous_status
    except Exception as exc:  # noqa: BLE001 - deliberately broad: any ffmpeg/IO failure lands here
        export.status = GenerationStatus.FAILED
        export.error_message = str(exc)
        episode.status = previous_status

    db.commit()
    db.refresh(export)
    return export


@router.delete("/api/exports/{export_id}", status_code=204)
def delete_export(
    export_id: int,
    db: Session = Depends(get_db),
    storage: StorageBackend = Depends(get_storage),
):
    export = _get_export_or_404(db, export_id)
    if export.output_path:
        storage.delete(export.output_path)
    db.delete(export)
    db.commit()
