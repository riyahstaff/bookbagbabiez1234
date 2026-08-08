from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import SceneStatus


class SceneCharacterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    character_id: int
    outfit_id: int | None = None


class SceneCharacterAssignment(BaseModel):
    character_id: int
    outfit_id: int | None = None


class SceneCharactersUpdate(BaseModel):
    characters: list[SceneCharacterAssignment]


class SceneBase(BaseModel):
    scene_number: int
    location_id: int | None = None
    time_of_day: str | None = None
    action_description: str | None = None
    dialogue: str | None = None
    narration: str | None = None
    emotional_tone: str | None = None
    continuity_notes: str | None = None
    estimated_duration_seconds: int | None = None


class SceneCreate(SceneBase):
    pass


class SceneUpdate(BaseModel):
    scene_number: int | None = None
    location_id: int | None = None
    time_of_day: str | None = None
    action_description: str | None = None
    dialogue: str | None = None
    narration: str | None = None
    emotional_tone: str | None = None
    continuity_notes: str | None = None
    estimated_duration_seconds: int | None = None
    status: SceneStatus | None = None


class SceneRead(SceneBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    episode_id: int
    status: SceneStatus
    created_at: datetime
    updated_at: datetime
    characters: list[SceneCharacterRead] = []
