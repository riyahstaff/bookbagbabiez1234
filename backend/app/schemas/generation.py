from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ApprovalStatus, AudioTrack, GenerationStatus, GenerationType


class GenerationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shot_id: int
    generation_type: GenerationType
    audio_track: AudioTrack | None = None
    voice_id: int | None = None
    provider_name: str
    model_name: str | None = None
    workflow_version: str | None = None
    prompt: str | None = None
    negative_prompt: str | None = None
    seed: int | None = None
    generation_settings: dict | None = None
    status: GenerationStatus
    error_message: str | None = None
    output_path: str | None = None
    preview_path: str | None = None
    quality_score: float | None = None
    qc_notes: str | None = None
    approval_status: ApprovalStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime


class GenerateStoryboardRequest(BaseModel):
    seed: int | None = None


class GenerateVoiceRequest(BaseModel):
    track: AudioTrack
    voice_id: int
    seed: int | None = None
    force_regenerate: bool = False


class GenerateVideoRequest(BaseModel):
    seed: int | None = None
    override_approval_gate: bool = False
