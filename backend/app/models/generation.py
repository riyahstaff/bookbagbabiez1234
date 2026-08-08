from sqlalchemy import JSON, Boolean, Float, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimestampedBase
from app.models.enums import ApprovalStatus, AudioTrack, GenerationStatus, GenerationType


class Generation(TimestampedBase):
    """One attempt at producing media for a shot - image (Phase 4), voice
    (Phase 5), or video (Phase 6, same table). Every attempt is a row; never
    overwritten or deleted automatically. Shot.characters/etc. describe what
    *should* be in the shot; a Generation records what a specific provider
    call *produced* from that description at a specific point in time."""

    __tablename__ = "generations"

    shot_id: Mapped[int] = mapped_column(ForeignKey("shots.id"), index=True)
    generation_type: Mapped[GenerationType] = mapped_column(SAEnum(GenerationType), index=True)
    # Only set for generation_type=VOICE - which of a shot's two text fields
    # this attempt voiced. None for IMAGE/VIDEO.
    audio_track: Mapped[AudioTrack | None] = mapped_column(SAEnum(AudioTrack), default=None)
    # Only set for generation_type=VOICE - which Voice spoke this line.
    voice_id: Mapped[int | None] = mapped_column(ForeignKey("voices.id"), index=True, default=None)
    provider_name: Mapped[str] = mapped_column(String(100))
    model_name: Mapped[str | None] = mapped_column(String(200), default=None)
    workflow_version: Mapped[str | None] = mapped_column(String(100), default=None)
    # Snapshot of the prompt actually used - Shot.visual_prompt may change later,
    # this is what *produced this specific file*. For VOICE, this is the
    # dialogue/narration text that was synthesized.
    prompt: Mapped[str | None] = mapped_column(Text, default=None)
    negative_prompt: Mapped[str | None] = mapped_column(Text, default=None)
    seed: Mapped[int | None] = mapped_column(Integer, default=None)
    generation_settings: Mapped[dict | None] = mapped_column(JSON, default=None)
    # VOICE only: sha256 of (text, voice_id, voice settings) at generation time,
    # so identical dialogue/narration is never resynthesized - see
    # generate_voice() in api/routers/generations.py. Shared across shots and
    # episodes; a content-hash match reuses the same output_path rather than
    # calling the provider again.
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True, default=None)
    status: Mapped[GenerationStatus] = mapped_column(
        SAEnum(GenerationStatus), default=GenerationStatus.QUEUED, nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, default=None)
    output_path: Mapped[str | None] = mapped_column(String(500), default=None)
    preview_path: Mapped[str | None] = mapped_column(String(500), default=None)
    # Set automatically by app/qc/ right after a generation completes -
    # advisory only, never blocks approve/reject/activate. See qc_notes for
    # what specifically was (or wasn't) flagged.
    quality_score: Mapped[float | None] = mapped_column(Float, default=None)
    qc_notes: Mapped[str | None] = mapped_column(Text, default=None)
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        SAEnum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False
    )
    # At most one active generation per (shot, generation_type, audio_track) -
    # enforced in the router, not the DB, same pattern as Voice.is_default /
    # ProviderConfiguration.is_default.
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    shot: Mapped["Shot"] = relationship(back_populates="generations")
    voice: Mapped["Voice | None"] = relationship()
