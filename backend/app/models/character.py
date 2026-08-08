from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimestampedBase


class Character(TimestampedBase):
    __tablename__ = "characters"

    series_id: Mapped[int] = mapped_column(ForeignKey("series.id"), index=True)
    character_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    age_range: Mapped[str | None] = mapped_column(String(50), default=None)
    height: Mapped[str | None] = mapped_column(String(50), default=None)
    build: Mapped[str | None] = mapped_column(String(100), default=None)
    skin_tone: Mapped[str | None] = mapped_column(String(100), default=None)
    hair: Mapped[str | None] = mapped_column(String(200), default=None)
    facial_features: Mapped[str | None] = mapped_column(Text, default=None)
    clothing: Mapped[str | None] = mapped_column(Text, default=None)
    accessories: Mapped[str | None] = mapped_column(Text, default=None)
    personality: Mapped[str | None] = mapped_column(Text, default=None)
    movement_style: Mapped[str | None] = mapped_column(Text, default=None)
    speaking_style: Mapped[str | None] = mapped_column(Text, default=None)
    accent: Mapped[str | None] = mapped_column(String(100), default=None)
    visual_style_notes: Mapped[str | None] = mapped_column(Text, default=None)
    continuity_restrictions: Mapped[str | None] = mapped_column(Text, default=None)

    series: Mapped["Series"] = relationship(back_populates="characters")
    references: Mapped[list["CharacterReference"]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )
    outfits: Mapped[list["CharacterOutfit"]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )
    voices: Mapped[list["Voice"]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )
