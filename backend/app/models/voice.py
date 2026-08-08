from sqlalchemy import JSON, Boolean, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimestampedBase


class Voice(TimestampedBase):
    __tablename__ = "voices"

    series_id: Mapped[int] = mapped_column(ForeignKey("series.id"), index=True)
    character_id: Mapped[int | None] = mapped_column(
        ForeignKey("characters.id"), index=True, default=None
    )
    voice_code: Mapped[str] = mapped_column(String(96), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    provider: Mapped[str | None] = mapped_column(String(100), default=None)
    provider_voice_id: Mapped[str | None] = mapped_column(String(200), default=None)
    reference_audio_path: Mapped[str | None] = mapped_column(String(500), default=None)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    speaking_style: Mapped[str | None] = mapped_column(Text, default=None)
    speed: Mapped[float | None] = mapped_column(Float, default=None)
    pitch: Mapped[float | None] = mapped_column(Float, default=None)
    emotion: Mapped[str | None] = mapped_column(String(100), default=None)
    generation_settings: Mapped[dict | None] = mapped_column(JSON, default=None)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    series: Mapped["Series"] = relationship(back_populates="voices")
    character: Mapped["Character | None"] = relationship(back_populates="voices")
