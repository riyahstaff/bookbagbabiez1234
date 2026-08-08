from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimestampedBase
from app.models.enums import EpisodeStatus


class Episode(TimestampedBase):
    __tablename__ = "episodes"
    __table_args__ = (
        UniqueConstraint("series_id", "episode_number", name="uq_episode_series_number"),
    )

    series_id: Mapped[int] = mapped_column(ForeignKey("series.id"), index=True)
    # NOTE: episode_code (e.g. "EP_001") is only unique *within* a series, not globally -
    # the on-disk layout nests it under the series folder, so two series can each have EP_001.
    episode_code: Mapped[str] = mapped_column(String(32), index=True)
    episode_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str | None] = mapped_column(Text, default=None)
    treatment: Mapped[str | None] = mapped_column(Text, default=None)
    outline: Mapped[str | None] = mapped_column(Text, default=None)
    script: Mapped[str | None] = mapped_column(Text, default=None)
    narration: Mapped[str | None] = mapped_column(Text, default=None)
    target_runtime_seconds: Mapped[int | None] = mapped_column(Integer, default=None)
    current_estimated_runtime_seconds: Mapped[int | None] = mapped_column(Integer, default=None)
    status: Mapped[EpisodeStatus] = mapped_column(
        SAEnum(EpisodeStatus), default=EpisodeStatus.DRAFT, nullable=False
    )

    series: Mapped["Series"] = relationship(back_populates="episodes")
    scenes: Mapped[list["Scene"]] = relationship(back_populates="episode", cascade="all, delete-orphan")
