from pydantic import BaseModel


class SceneDraft(BaseModel):
    scene_number: int
    location_name: str | None = None
    time_of_day: str | None = None
    characters_present: list[str] = []
    action_description: str | None = None
    dialogue: str | None = None
    narration: str | None = None
    emotional_tone: str | None = None
    estimated_duration_seconds: int | None = None


class SceneBreakdown(BaseModel):
    scenes: list[SceneDraft]


class ShotDraft(BaseModel):
    shot_number: int
    shot_type: str
    camera_angle: str | None = None
    camera_movement: str | None = None
    characters_visible: list[str] = []
    action: str | None = None
    dialogue: str | None = None
    narration: str | None = None
    emotion: str | None = None
    lighting: str | None = None
    duration_seconds: int | None = None


class ShotBreakdown(BaseModel):
    shots: list[ShotDraft]
