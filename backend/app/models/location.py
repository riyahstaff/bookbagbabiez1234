from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimestampedBase
from app.models.enums import LocationReferenceCategory


class Location(TimestampedBase):
    __tablename__ = "locations"

    series_id: Mapped[int] = mapped_column(ForeignKey("series.id"), index=True)
    location_code: Mapped[str] = mapped_column(String(96), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    lighting_notes: Mapped[str | None] = mapped_column(Text, default=None)
    time_of_day_notes: Mapped[str | None] = mapped_column(Text, default=None)
    camera_reference_notes: Mapped[str | None] = mapped_column(Text, default=None)
    important_props: Mapped[str | None] = mapped_column(Text, default=None)
    continuity_rules: Mapped[str | None] = mapped_column(Text, default=None)

    series: Mapped["Series"] = relationship(back_populates="locations")
    references: Mapped[list["LocationReference"]] = relationship(
        back_populates="location", cascade="all, delete-orphan"
    )


class LocationReference(TimestampedBase):
    __tablename__ = "location_references"

    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), index=True)
    category: Mapped[LocationReferenceCategory] = mapped_column(
        SAEnum(LocationReferenceCategory), index=True
    )
    image_path: Mapped[str] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text, default=None)

    location: Mapped["Location"] = relationship(back_populates="references")
