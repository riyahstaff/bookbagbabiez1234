from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PropBase(BaseModel):
    name: str
    description: str | None = None


class PropCreate(PropBase):
    pass


class PropUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class PropRead(PropBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    series_id: int
    prop_code: str
    created_at: datetime
    updated_at: datetime


class PropReferenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prop_id: int
    label: str | None = None
    image_path: str
    notes: str | None = None
    created_at: datetime
