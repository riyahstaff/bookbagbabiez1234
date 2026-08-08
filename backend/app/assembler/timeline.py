from dataclasses import dataclass

DEFAULT_SHOT_DURATION_SECONDS = 3.0


@dataclass
class ShotSegment:
    shot_id: int
    label: str  # e.g. "Scene 2 Shot 3" - for skip reporting and debugging
    video_path: str  # storage-relative path - a real video, or a still image to hold
    is_static_image: bool
    hold_duration_seconds: float | None  # only set when is_static_image
    dialogue_path: str | None
    dialogue_text: str | None
    narration_path: str | None
    narration_text: str | None


@dataclass
class Timeline:
    segments: list[ShotSegment]
    skipped_shots: list[str]  # labels of shots with neither an active image nor video to render


def build_timeline(episode) -> Timeline:
    """Walks Scenes (by scene_number) -> Shots (by shot_number) and resolves
    each shot's active video (falling back to its active image, held for
    shot.duration_seconds) and active dialogue/narration audio. A shot with
    neither an active image nor an active video can't be rendered at all and
    is skipped, not treated as a hard failure - a partial rough cut is more
    useful than refusing to export anything."""
    segments: list[ShotSegment] = []
    skipped: list[str] = []

    scenes = sorted(episode.scenes, key=lambda scene: scene.scene_number)
    for scene in scenes:
        shots = sorted(scene.shots, key=lambda shot: shot.shot_number)
        for shot in shots:
            label = f"Scene {scene.scene_number} Shot {shot.shot_number}"
            video_generation = shot.active_video_generation
            image_generation = shot.active_image_generation
            dialogue_generation = shot.active_dialogue_generation
            narration_generation = shot.active_narration_generation

            if video_generation and video_generation.output_path:
                video_path = video_generation.output_path
                is_static_image = False
                hold_duration = None
            elif image_generation and image_generation.output_path:
                video_path = image_generation.output_path
                is_static_image = True
                hold_duration = float(shot.duration_seconds or DEFAULT_SHOT_DURATION_SECONDS)
            else:
                skipped.append(label)
                continue

            segments.append(
                ShotSegment(
                    shot_id=shot.id,
                    label=label,
                    video_path=video_path,
                    is_static_image=is_static_image,
                    hold_duration_seconds=hold_duration,
                    dialogue_path=dialogue_generation.output_path if dialogue_generation else None,
                    dialogue_text=shot.dialogue,
                    narration_path=narration_generation.output_path if narration_generation else None,
                    narration_text=shot.narration,
                )
            )

    return Timeline(segments=segments, skipped_shots=skipped)
