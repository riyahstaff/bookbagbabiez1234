from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ShotType
from app.schemas.generation import GenerationRead


class ShotCharacterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    character_id: int
    outfit_id: int | None = None


class ShotCharacterAssignment(BaseModel):
    character_id: int
    outfit_id: int | None = None


class ShotCharactersUpdate(BaseModel):
    characters: list[ShotCharacterAssignment]


class ShotBase(BaseModel):
    shot_number: int
    shot_type: ShotType = ShotType.MEDIUM
    camera_angle: str | None = None
    camera_movement: str | None = None
    action: str | None = None
    dialogue: str | None = None
    narration: str | None = None
    emotion: str | None = None
    lighting: str | None = None
    duration_seconds: int | None = None
    visual_prompt: str | None = None
    negative_prompt: str | None = None


class ShotCreate(ShotBase):
    pass


class ShotUpdate(BaseModel):
    shot_number: int | None = None
    shot_type: ShotType | None = None
    camera_angle: str | None = None
    camera_movement: str | None = None
    action: str | None = None
    dialogue: str | None = None
    narration: str | None = None
    emotion: str | None = None
    lighting: str | None = None
    duration_seconds: int | None = None
    visual_prompt: str | None = None
    negative_prompt: str | None = None


class ShotRead(ShotBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scene_id: int
    created_at: datetime
    updated_at: datetime
    characters: list[ShotCharacterRead] = []
    active_generation: GenerationRead | None = None
