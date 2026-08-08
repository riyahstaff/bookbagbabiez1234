from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimestampedBase
from app.models.enums import SceneStatus


class Scene(TimestampedBase):
    __tablename__ = "scenes"
    __table_args__ = (UniqueConstraint("episode_id", "scene_number", name="uq_scene_episode_number"),)

    episode_id: Mapped[int] = mapped_column(ForeignKey("episodes.id"), index=True)
    scene_number: Mapped[int] = mapped_column(Integer)
    location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), index=True, default=None)
    time_of_day: Mapped[str | None] = mapped_column(Text, default=None)
    action_description: Mapped[str | None] = mapped_column(Text, default=None)
    dialogue: Mapped[str | None] = mapped_column(Text, default=None)
    narration: Mapped[str | None] = mapped_column(Text, default=None)
    emotional_tone: Mapped[str | None] = mapped_column(Text, default=None)
    continuity_notes: Mapped[str | None] = mapped_column(Text, default=None)
    estimated_duration_seconds: Mapped[int | None] = mapped_column(Integer, default=None)
    status: Mapped[SceneStatus] = mapped_column(SAEnum(SceneStatus), default=SceneStatus.DRAFT, nullable=False)

    episode: Mapped["Episode"] = relationship(back_populates="scenes")
    location: Mapped["Location | None"] = relationship()
    characters: Mapped[list["SceneCharacter"]] = relationship(
        back_populates="scene", cascade="all, delete-orphan"
    )
    shots: Mapped[list["Shot"]] = relationship(back_populates="scene", cascade="all, delete-orphan")


class SceneCharacter(TimestampedBase):
    __tablename__ = "scene_characters"
    __table_args__ = (UniqueConstraint("scene_id", "character_id", name="uq_scene_character"),)

    scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"), index=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True)
    # Which outfit this character wears in this scene, if decided yet - kept optional
    # since wardrobe assignment doesn't matter until generation exists (Phase 4+).
    outfit_id: Mapped[int | None] = mapped_column(ForeignKey("character_outfits.id"), default=None)

    scene: Mapped["Scene"] = relationship(back_populates="characters")
    character: Mapped["Character"] = relationship()
    outfit: Mapped["CharacterOutfit | None"] = relationship()
