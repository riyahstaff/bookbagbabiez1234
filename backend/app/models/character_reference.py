from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimestampedBase
from app.models.enums import CharacterReferenceCategory


class CharacterReference(TimestampedBase):
    __tablename__ = "character_references"

    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True)
    category: Mapped[CharacterReferenceCategory] = mapped_column(
        SAEnum(CharacterReferenceCategory), index=True
    )
    image_path: Mapped[str] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text, default=None)

    character: Mapped["Character"] = relationship(back_populates="references")
