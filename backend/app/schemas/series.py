from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SeriesBase(BaseModel):
    title: str
    description: str | None = None
    genre: str | None = None
    animation_style: str | None = None
    target_resolution: str = "1280x720"
    default_fps: int = 24
    target_episode_length_minutes: int = 30
    aspect_ratio: str = "16:9"
    visual_style_prompt: str | None = None
    negative_style_prompt: str | None = None
    default_voice_settings: str | None = None
    default_video_provider: str | None = None
    default_image_provider: str | None = None


class SeriesCreate(SeriesBase):
    pass


class SeriesUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    genre: str | None = None
    animation_style: str | None = None
    target_resolution: str | None = None
    default_fps: int | None = None
    target_episode_length_minutes: int | None = None
    aspect_ratio: str | None = None
    visual_style_prompt: str | None = None
    negative_style_prompt: str | None = None
    default_voice_settings: str | None = None
    default_video_provider: str | None = None
    default_image_provider: str | None = None


class SeriesRead(SeriesBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    series_code: str
    created_at: datetime
    updated_at: datetime
