from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimestampedBase
from app.models.enums import AudioTrack, GenerationType, ShotType


class Shot(TimestampedBase):
    __tablename__ = "shots"
    __table_args__ = (UniqueConstraint("scene_id", "shot_number", name="uq_shot_scene_number"),)

    scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"), index=True)
    shot_number: Mapped[int] = mapped_column(Integer)
    shot_type: Mapped[ShotType] = mapped_column(SAEnum(ShotType), default=ShotType.MEDIUM, nullable=False)
    camera_angle: Mapped[str | None] = mapped_column(Text, default=None)
    camera_movement: Mapped[str | None] = mapped_column(Text, default=None)
    action: Mapped[str | None] = mapped_column(Text, default=None)
    dialogue: Mapped[str | None] = mapped_column(Text, default=None)
    narration: Mapped[str | None] = mapped_column(Text, default=None)
    emotion: Mapped[str | None] = mapped_column(Text, default=None)
    lighting: Mapped[str | None] = mapped_column(Text, default=None)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, default=None)
    # Editable by the user before any generation is requested - constructed from
    # the Series/Character Bible plus this shot's fields, per docs/ARCHITECTURE.md.
    visual_prompt: Mapped[str | None] = mapped_column(Text, default=None)
    negative_prompt: Mapped[str | None] = mapped_column(Text, default=None)

    scene: Mapped["Scene"] = relationship(back_populates="shots")
    characters: Mapped[list["ShotCharacter"]] = relationship(
        back_populates="shot", cascade="all, delete-orphan"
    )
    generations: Mapped[list["Generation"]] = relationship(
        back_populates="shot", cascade="all, delete-orphan"
    )

    @property
    def active_image_generation(self) -> "Generation | None":
        return next(
            (g for g in self.generations if g.is_active and g.generation_type == GenerationType.IMAGE),
            None,
        )

    @property
    def active_dialogue_generation(self) -> "Generation | None":
        return next(
            (g for g in self.generations if g.is_active and g.audio_track == AudioTrack.DIALOGUE),
            None,
        )

    @property
    def active_narration_generation(self) -> "Generation | None":
        return next(
            (g for g in self.generations if g.is_active and g.audio_track == AudioTrack.NARRATION),
            None,
        )

    @property
    def active_video_generation(self) -> "Generation | None":
        return next(
            (g for g in self.generations if g.is_active and g.generation_type == GenerationType.VIDEO),
            None,
        )


class ShotCharacter(TimestampedBase):
    __tablename__ = "shot_characters"
    __table_args__ = (UniqueConstraint("shot_id", "character_id", name="uq_shot_character"),)

    shot_id: Mapped[int] = mapped_column(ForeignKey("shots.id"), index=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True)
    outfit_id: Mapped[int | None] = mapped_column(ForeignKey("character_outfits.id"), default=None)

    shot: Mapped["Shot"] = relationship(back_populates="characters")
    character: Mapped["Character"] = relationship()
    outfit: Mapped["CharacterOutfit | None"] = relationship()
