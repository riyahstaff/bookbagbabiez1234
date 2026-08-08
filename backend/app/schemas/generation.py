from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ApprovalStatus, GenerationStatus, GenerationType


class GenerationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shot_id: int
    generation_type: GenerationType
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
    approval_status: ApprovalStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime


class GenerateStoryboardRequest(BaseModel):
    seed: int | None = None
