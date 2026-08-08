from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimestampedBase


class Series(TimestampedBase):
    __tablename__ = "series"

    series_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    # The two Series Bible facets actually consumed as LLM context (Phase 3) -
    # world/time-period/tone details, and hard continuity rules ("never do X").
    world_details: Mapped[str | None] = mapped_column(Text, default=None)
    continuity_rules: Mapped[str | None] = mapped_column(Text, default=None)
    genre: Mapped[str | None] = mapped_column(String(100), default=None)
    animation_style: Mapped[str | None] = mapped_column(String(200), default=None)
    target_resolution: Mapped[str] = mapped_column(String(20), default="1280x720")
    default_fps: Mapped[int] = mapped_column(default=24)
    target_episode_length_minutes: Mapped[int] = mapped_column(default=30)
    aspect_ratio: Mapped[str] = mapped_column(String(10), default="16:9")
    visual_style_prompt: Mapped[str | None] = mapped_column(Text, default=None)
    negative_style_prompt: Mapped[str | None] = mapped_column(Text, default=None)
    default_voice_settings: Mapped[str | None] = mapped_column(Text, default=None)
    default_video_provider: Mapped[str | None] = mapped_column(String(100), default=None)
    default_image_provider: Mapped[str | None] = mapped_column(String(100), default=None)

    characters: Mapped[list["Character"]] = relationship(
        back_populates="series", cascade="all, delete-orphan"
    )
    episodes: Mapped[list["Episode"]] = relationship(
        back_populates="series", cascade="all, delete-orphan"
    )
    voices: Mapped[list["Voice"]] = relationship(back_populates="series", cascade="all, delete-orphan")
    locations: Mapped[list["Location"]] = relationship(
        back_populates="series", cascade="all, delete-orphan"
    )
    props: Mapped[list["Prop"]] = relationship(back_populates="series", cascade="all, delete-orphan")
