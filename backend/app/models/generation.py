from sqlalchemy import JSON, Boolean, Float, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimestampedBase
from app.models.enums import ApprovalStatus, GenerationStatus, GenerationType


class Generation(TimestampedBase):
    """One attempt at producing media for a shot - image (Phase 4) or video
    (Phase 6, same table). Every attempt is a row; never overwritten or
    deleted automatically. Shot.characters/etc. describe what *should* be in
    the shot; a Generation records what a specific provider call *produced*
    from that description at a specific point in time."""

    __tablename__ = "generations"

    shot_id: Mapped[int] = mapped_column(ForeignKey("shots.id"), index=True)
    generation_type: Mapped[GenerationType] = mapped_column(SAEnum(GenerationType), index=True)
    provider_name: Mapped[str] = mapped_column(String(100))
    model_name: Mapped[str | None] = mapped_column(String(200), default=None)
    workflow_version: Mapped[str | None] = mapped_column(String(100), default=None)
    # Snapshot of the prompt actually used - Shot.visual_prompt may change later,
    # this is what *produced this specific file*.
    prompt: Mapped[str | None] = mapped_column(Text, default=None)
    negative_prompt: Mapped[str | None] = mapped_column(Text, default=None)
    seed: Mapped[int | None] = mapped_column(Integer, default=None)
    generation_settings: Mapped[dict | None] = mapped_column(JSON, default=None)
    status: Mapped[GenerationStatus] = mapped_column(
        SAEnum(GenerationStatus), default=GenerationStatus.QUEUED, nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, default=None)
    output_path: Mapped[str | None] = mapped_column(String(500), default=None)
    preview_path: Mapped[str | None] = mapped_column(String(500), default=None)
    quality_score: Mapped[float | None] = mapped_column(Float, default=None)
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        SAEnum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False
    )
    # At most one active generation per shot - enforced in the router, not the
    # DB, same pattern as Voice.is_default / ProviderConfiguration.is_default.
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    shot: Mapped["Shot"] = relationship(back_populates="generations")
