from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimestampedBase


class CharacterOutfit(TimestampedBase):
    __tablename__ = "character_outfits"

    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True)
    outfit_code: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, default=None)

    character: Mapped["Character"] = relationship(back_populates="outfits")
    references: Mapped[list["OutfitReference"]] = relationship(
        back_populates="outfit", cascade="all, delete-orphan"
    )


class OutfitReference(TimestampedBase):
    __tablename__ = "outfit_references"

    outfit_id: Mapped[int] = mapped_column(ForeignKey("character_outfits.id"), index=True)
    label: Mapped[str | None] = mapped_column(String(200), default=None)
    image_path: Mapped[str] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text, default=None)

    outfit: Mapped["CharacterOutfit"] = relationship(back_populates="references")
