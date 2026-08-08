from sqlalchemy import JSON, Boolean, Float, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimestampedBase
from app.models.enums import GenerationStatus


class EpisodeExport(TimestampedBase):
    """One attempt at assembling an episode's approved shots into a single
    exported video - image/voice/video Generations feed *into* this, but
    this is never itself approved/rejected/versioned-as-active the way they
    are; it's a mechanical render of already-approved content, not a
    creative asset. Every attempt is a row, same never-overwrite convention
    as Generation."""

    __tablename__ = "episode_exports"

    episode_id: Mapped[int] = mapped_column(ForeignKey("episodes.id"), index=True)
    status: Mapped[GenerationStatus] = mapped_column(
        SAEnum(GenerationStatus), default=GenerationStatus.RUNNING, nullable=False
    )
    output_path: Mapped[str | None] = mapped_column(String(500), default=None)
    error_message: Mapped[str | None] = mapped_column(Text, default=None)
    duration_seconds: Mapped[float | None] = mapped_column(Float, default=None)
    include_titles: Mapped[bool] = mapped_column(Boolean, default=True)
    include_credits: Mapped[bool] = mapped_column(Boolean, default=True)
    include_subtitles: Mapped[bool] = mapped_column(Boolean, default=True)
    # "Scene N Shot M" labels skipped for having neither an active image nor
    # an active video to render - see app/assembler/timeline.py.
    skipped_shots: Mapped[list[str] | None] = mapped_column(JSON, default=None)

    episode: Mapped["Episode"] = relationship()
