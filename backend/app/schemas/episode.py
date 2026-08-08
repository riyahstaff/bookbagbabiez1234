from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import EpisodeStatus


class EpisodeBase(BaseModel):
    episode_number: int
    title: str
    summary: str | None = None
    treatment: str | None = None
    script: str | None = None
    narration: str | None = None
    target_runtime_seconds: int | None = None
    current_estimated_runtime_seconds: int | None = None


class EpisodeCreate(EpisodeBase):
    pass


class EpisodeUpdate(BaseModel):
    episode_number: int | None = None
    title: str | None = None
    summary: str | None = None
    treatment: str | None = None
    script: str | None = None
    narration: str | None = None
    target_runtime_seconds: int | None = None
    current_estimated_runtime_seconds: int | None = None
    status: EpisodeStatus | None = None


class EpisodeRead(EpisodeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    series_id: int
    episode_code: str
    status: EpisodeStatus
    created_at: datetime
    updated_at: datetime
