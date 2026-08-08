import shutil
import subprocess
from pathlib import Path


def _require_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise RuntimeError(
            "ffmpeg/ffprobe are not installed or not on PATH - required for episode export. "
            "The Docker image installs this; for local development, install ffmpeg with your "
            "system package manager."
        )


def run_ffmpeg(args: list[str]) -> None:
    _require_ffmpeg()
    result = subprocess.run(["ffmpeg", "-nostdin", *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr[-2000:]}")


def probe_duration(path: Path) -> float:
    _require_ffmpeg()
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(f"ffprobe failed to read duration of {path}: {result.stderr[-1000:]}")
    return float(result.stdout.strip())


def _scale_pad_filter(width: int, height: int) -> str:
    return (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1"
    )


def image_to_video(image_path: Path, duration_seconds: float, width: int, height: int, fps: int, output_path: Path) -> None:
    run_ffmpeg(
        [
            "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-t", str(duration_seconds),
            "-vf", _scale_pad_filter(width, height),
            "-r", str(fps),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            str(output_path),
        ]
    )


def prepare_audio_track(audio_paths: list[Path], duration_seconds: float, output_path: Path) -> None:
    """Always produces an audio file of exactly duration_seconds - silence if
    no inputs, the single input padded/trimmed if one, or a mix of all of
    them padded/trimmed if more than one. Shot audio duration rarely matches
    its video's duration exactly (a line might be shorter or longer than the
    shot's intended length), so the video's duration always wins here."""
    if not audio_paths:
        run_ffmpeg(
            ["-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", str(duration_seconds), str(output_path)]
        )
        return

    inputs: list[str] = []
    for path in audio_paths:
        inputs += ["-i", str(path)]

    if len(audio_paths) == 1:
        run_ffmpeg(
            [
                "-y", *inputs,
                "-af", "apad",
                "-t", str(duration_seconds),
                "-ar", "44100", "-ac", "2",
                str(output_path),
            ]
        )
        return

    run_ffmpeg(
        [
            "-y", *inputs,
            "-filter_complex", f"amix=inputs={len(audio_paths)}:duration=longest,apad",
            "-t", str(duration_seconds),
            "-ar", "44100", "-ac", "2",
            str(output_path),
        ]
    )


def render_shot_clip(
    video_path: Path, audio_path: Path, width: int, height: int, fps: int, output_path: Path
) -> None:
    """Normalizes video+audio into one mp4 clip at a consistent
    resolution/fps/codec, so every clip can later be stream-copy concatenated
    without re-encoding again."""
    run_ffmpeg(
        [
            "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-vf", _scale_pad_filter(width, height),
            "-r", str(fps),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-ar", "44100", "-ac", "2",
            "-shortest",
            str(output_path),
        ]
    )


def concat_clips(clip_paths: list[Path], output_path: Path) -> None:
    list_file = output_path.parent / f"{output_path.stem}_concat_list.txt"
    list_file.write_text("\n".join(f"file '{path}'" for path in clip_paths))
    run_ffmpeg(["-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(output_path)])


def mux_subtitles(video_path: Path, srt_path: Path, output_path: Path) -> None:
    run_ffmpeg(
        [
            "-y",
            "-i", str(video_path),
            "-i", str(srt_path),
            "-c", "copy",
            "-c:s", "mov_text",
            "-metadata:s:s:0", "language=eng",
            str(output_path),
        ]
    )
