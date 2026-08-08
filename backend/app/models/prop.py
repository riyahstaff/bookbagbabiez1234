from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimestampedBase


class Prop(TimestampedBase):
    __tablename__ = "props"

    series_id: Mapped[int] = mapped_column(ForeignKey("series.id"), index=True)
    prop_code: Mapped[str] = mapped_column(String(96), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, default=None)

    series: Mapped["Series"] = relationship(back_populates="props")
    references: Mapped[list["PropReference"]] = relationship(
        back_populates="prop", cascade="all, delete-orphan"
    )


class PropReference(TimestampedBase):
    __tablename__ = "prop_references"

    prop_id: Mapped[int] = mapped_column(ForeignKey("props.id"), index=True)
    label: Mapped[str | None] = mapped_column(String(200), default=None)
    image_path: Mapped[str] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text, default=None)

    prop: Mapped["Prop"] = relationship(back_populates="references")
