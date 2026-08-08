from sqlalchemy import JSON, Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TimestampedBase


class ProjectSetting(TimestampedBase):
    __tablename__ = "project_settings"

    key: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    value: Mapped[str | None] = mapped_column(Text, default=None)


class ProviderConfiguration(TimestampedBase):
    __tablename__ = "provider_configurations"

    # Stored as plain text (validated against ProviderCapability at the API layer)
    # rather than a DB-level enum, so adding a new capability later never needs a migration.
    capability: Mapped[str] = mapped_column(String(50), index=True)
    provider_name: Mapped[str] = mapped_column(String(100))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    config: Mapped[dict | None] = mapped_column(JSON, default=None)
