import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.assembler import cards, ffmpeg_ops, subtitles
from app.assembler.timeline import ShotSegment, build_timeline
from app.storage.base import StorageBackend

CARD_DURATION_SECONDS = 3.0


class AssemblyError(RuntimeError):
    pass


@dataclass
class AssemblyResult:
    duration_seconds: float
    skipped_shots: list[str]


def assemble_episode(
    episode,
    storage: StorageBackend,
    output_path: Path,
    include_titles: bool = True,
    include_credits: bool = True,
    include_subtitles: bool = True,
) -> AssemblyResult:
    if shutil.which("ffmpeg") is None:
        raise AssemblyError(
            "ffmpeg is not installed or not on PATH - required for episode export."
        )

    series = episode.series
    width, height = (int(part) for part in series.target_resolution.lower().split("x"))
    fps = series.default_fps

    timeline = build_timeline(episode)
    if not timeline.segments:
        raise AssemblyError(
            "This episode has no shots with an approved image or video to assemble yet."
        )

    with tempfile.TemporaryDirectory(prefix="acs_assembly_") as tmp_dir_name:
        tmp_dir = Path(tmp_dir_name)
        clip_paths: list[Path] = []
        cue_cursor = 0.0
        srt_cues: list[tuple[float, float, str]] = []

        if include_titles:
            title_clip = tmp_dir / "card_title.mp4"
            _render_card_clip(
                cards.render_title_card(series.title, episode.title, episode.episode_code, width, height),
                CARD_DURATION_SECONDS,
                width,
                height,
                fps,
                tmp_dir,
                title_clip,
                "title",
            )
            clip_paths.append(title_clip)
            cue_cursor += CARD_DURATION_SECONDS

        for index, segment in enumerate(timeline.segments):
            clip_path = tmp_dir / f"shot_{index}.mp4"
            duration = _render_shot_segment(segment, storage, tmp_dir, index, width, height, fps, clip_path)
            clip_paths.append(clip_path)

            cue_text = " / ".join(
                text for text in (segment.dialogue_text, segment.narration_text) if text
            )
            if cue_text:
                srt_cues.append((cue_cursor, cue_cursor + duration, cue_text))
            cue_cursor += duration

        if include_credits:
            credits_clip = tmp_dir / "card_credits.mp4"
            character_names = sorted({character.name for character in _characters_in_episode(episode)})
            _render_card_clip(
                cards.render_credits_card(series.title, character_names, width, height),
                CARD_DURATION_SECONDS,
                width,
                height,
                fps,
                tmp_dir,
                credits_clip,
                "credits",
            )
            clip_paths.append(credits_clip)

        concatenated = tmp_dir / "concatenated.mp4"
        ffmpeg_ops.concat_clips(clip_paths, concatenated)

        final_clip = concatenated
        if include_subtitles and srt_cues:
            srt_path = tmp_dir / "subtitles.srt"
            srt_path.write_text(subtitles.build_srt(srt_cues))
            with_subs = tmp_dir / "with_subs.mp4"
            ffmpeg_ops.mux_subtitles(concatenated, srt_path, with_subs)
            final_clip = with_subs

        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(final_clip, output_path)

    duration_seconds = ffmpeg_ops.probe_duration(output_path)
    return AssemblyResult(duration_seconds=duration_seconds, skipped_shots=timeline.skipped_shots)


def _materialize(storage: StorageBackend, relative_path: str, tmp_dir: Path, name: str) -> Path:
    content = storage.read(relative_path)
    suffix = Path(relative_path).suffix
    path = tmp_dir / f"{name}{suffix}"
    path.write_bytes(content)
    return path


def _render_shot_segment(
    segment: ShotSegment,
    storage: StorageBackend,
    tmp_dir: Path,
    index: int,
    width: int,
    height: int,
    fps: int,
    output_path: Path,
) -> float:
    video_path = _materialize(storage, segment.video_path, tmp_dir, f"shot_{index}_video")

    if segment.is_static_image:
        duration = segment.hold_duration_seconds or 0.0
        looped_path = tmp_dir / f"shot_{index}_looped.mp4"
        ffmpeg_ops.image_to_video(video_path, duration, width, height, fps, looped_path)
        video_path = looped_path
    else:
        duration = ffmpeg_ops.probe_duration(video_path)

    audio_inputs: list[Path] = []
    if segment.dialogue_path:
        audio_inputs.append(_materialize(storage, segment.dialogue_path, tmp_dir, f"shot_{index}_dialogue"))
    if segment.narration_path:
        audio_inputs.append(_materialize(storage, segment.narration_path, tmp_dir, f"shot_{index}_narration"))

    # .wav, not .aac: a raw ADTS AAC stream has no reliable container-level
    # duration metadata, which would make any later probe_duration() call on
    # it (there aren't any right now, but a future change might add one)
    # silently return the wrong number - see ffmpeg_ops tests for the
    # concrete difference this made.
    audio_path = tmp_dir / f"shot_{index}_audio.wav"
    ffmpeg_ops.prepare_audio_track(audio_inputs, duration, audio_path)

    ffmpeg_ops.render_shot_clip(video_path, audio_path, width, height, fps, output_path)
    return duration


def _render_card_clip(
    image_bytes: bytes,
    duration: float,
    width: int,
    height: int,
    fps: int,
    tmp_dir: Path,
    output_path: Path,
    name: str,
) -> None:
    image_path = tmp_dir / f"{name}_card.png"
    image_path.write_bytes(image_bytes)
    silence_path = tmp_dir / f"{name}_silence.wav"
    ffmpeg_ops.prepare_audio_track([], duration, silence_path)
    looped_path = tmp_dir / f"{name}_looped.mp4"
    ffmpeg_ops.image_to_video(image_path, duration, width, height, fps, looped_path)
    ffmpeg_ops.render_shot_clip(looped_path, silence_path, width, height, fps, output_path)


def _characters_in_episode(episode):
    characters = set()
    for scene in episode.scenes:
        for scene_character in scene.characters:
            characters.add(scene_character.character)
    return characters
