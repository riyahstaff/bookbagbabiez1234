from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CharacterOutfitCreate(BaseModel):
    name: str
    description: str | None = None


class CharacterOutfitUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class CharacterOutfitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    character_id: int
    outfit_code: str
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class OutfitReferenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    outfit_id: int
    label: str | None = None
    image_path: str
    notes: str | None = None
    created_at: datetime
