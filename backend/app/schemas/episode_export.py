from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import GenerationStatus


class EpisodeExportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    episode_id: int
    status: GenerationStatus
    output_path: str | None = None
    error_message: str | None = None
    duration_seconds: float | None = None
    include_titles: bool
    include_credits: bool
    include_subtitles: bool
    skipped_shots: list[str] | None = None
    created_at: datetime
    updated_at: datetime


class CreateEpisodeExportRequest(BaseModel):
    include_titles: bool = True
    include_credits: bool = True
    include_subtitles: bool = True


class EpisodeExportPreview(BaseModel):
    renderable_shot_count: int
    skipped_shots: list[str]
