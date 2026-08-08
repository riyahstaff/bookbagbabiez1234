from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CharacterBase(BaseModel):
    name: str
    description: str | None = None
    age_range: str | None = None
    height: str | None = None
    build: str | None = None
    skin_tone: str | None = None
    hair: str | None = None
    facial_features: str | None = None
    clothing: str | None = None
    accessories: str | None = None
    personality: str | None = None
    movement_style: str | None = None
    speaking_style: str | None = None
    accent: str | None = None
    visual_style_notes: str | None = None
    continuity_restrictions: str | None = None


class CharacterCreate(CharacterBase):
    pass


class CharacterUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    age_range: str | None = None
    height: str | None = None
    build: str | None = None
    skin_tone: str | None = None
    hair: str | None = None
    facial_features: str | None = None
    clothing: str | None = None
    accessories: str | None = None
    personality: str | None = None
    movement_style: str | None = None
    speaking_style: str | None = None
    accent: str | None = None
    visual_style_notes: str | None = None
    continuity_restrictions: str | None = None


class CharacterRead(CharacterBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    series_id: int
    character_code: str
    created_at: datetime
    updated_at: datetime
