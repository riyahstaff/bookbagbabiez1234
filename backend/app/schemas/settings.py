from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ProviderCapability


class ProjectSettingUpsert(BaseModel):
    key: str
    value: str | None = None


class ProjectSettingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    value: str | None = None
    updated_at: datetime


class ProviderConfigurationCreate(BaseModel):
    capability: ProviderCapability
    provider_name: str
    is_default: bool = False
    config: dict | None = None


class ProviderConfigurationUpdate(BaseModel):
    provider_name: str | None = None
    is_default: bool | None = None
    config: dict | None = None


class ProviderConfigurationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    capability: str
    provider_name: str
    is_default: bool
    config: dict | None = None
    created_at: datetime
    updated_at: datetime
