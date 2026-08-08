from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import LocationReferenceCategory


class LocationBase(BaseModel):
    name: str
    description: str | None = None
    lighting_notes: str | None = None
    time_of_day_notes: str | None = None
    camera_reference_notes: str | None = None
    important_props: str | None = None
    continuity_rules: str | None = None


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    lighting_notes: str | None = None
    time_of_day_notes: str | None = None
    camera_reference_notes: str | None = None
    important_props: str | None = None
    continuity_rules: str | None = None


class LocationRead(LocationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    series_id: int
    location_code: str
    created_at: datetime
    updated_at: datetime


class LocationReferenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    location_id: int
    category: LocationReferenceCategory
    image_path: str
    notes: str | None = None
    created_at: datetime
