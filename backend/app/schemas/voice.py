from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VoiceBase(BaseModel):
    name: str
    character_id: int | None = None
    provider: str | None = None
    provider_voice_id: str | None = None
    description: str | None = None
    speaking_style: str | None = None
    speed: float | None = None
    pitch: float | None = None
    emotion: str | None = None
    generation_settings: dict | None = None
    is_default: bool = False


class VoiceCreate(VoiceBase):
    pass


class VoiceUpdate(BaseModel):
    name: str | None = None
    character_id: int | None = None
    provider: str | None = None
    provider_voice_id: str | None = None
    description: str | None = None
    speaking_style: str | None = None
    speed: float | None = None
    pitch: float | None = None
    emotion: str | None = None
    generation_settings: dict | None = None
    is_default: bool | None = None


class VoiceRead(VoiceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    series_id: int
    voice_code: str
    reference_audio_path: str | None = None
    created_at: datetime
    updated_at: datetime
