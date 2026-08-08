import subprocess

import pytest
from PIL import Image

from app.assembler import ffmpeg_ops


def _probe_streams(path) -> list[dict]:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _real_png(tmp_path, name="ref.png"):
    image = Image.new("RGB", (320, 180), color=(90, 130, 200))
    path = tmp_path / name
    image.save(path, format="PNG")
    return path


def test_image_to_video_produces_real_video_of_requested_duration(tmp_path):
    image_path = _real_png(tmp_path)
    output = tmp_path / "out.mp4"

    ffmpeg_ops.image_to_video(image_path, duration_seconds=2.0, width=320, height=180, fps=24, output_path=output)

    assert output.exists()
    duration = ffmpeg_ops.probe_duration(output)
    assert abs(duration - 2.0) < 0.2
    assert _probe_streams(output) == ["video"]


def test_prepare_audio_track_silence_has_requested_duration(tmp_path):
    output = tmp_path / "silence.wav"
    ffmpeg_ops.prepare_audio_track([], duration_seconds=1.5, output_path=output)

    assert output.exists()
    duration = ffmpeg_ops.probe_duration(output)
    assert abs(duration - 1.5) < 0.2


def test_prepare_audio_track_pads_a_short_single_input(tmp_path):
    short_audio = tmp_path / "short.wav"
    ffmpeg_ops.run_ffmpeg(
        ["-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=0.5", str(short_audio)]
    )

    output = tmp_path / "padded.wav"
    ffmpeg_ops.prepare_audio_track([short_audio], duration_seconds=2.0, output_path=output)

    duration = ffmpeg_ops.probe_duration(output)
    assert abs(duration - 2.0) < 0.2


def test_prepare_audio_track_trims_a_long_single_input(tmp_path):
    long_audio = tmp_path / "long.wav"
    ffmpeg_ops.run_ffmpeg(
        ["-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=5", str(long_audio)]
    )

    output = tmp_path / "trimmed.wav"
    ffmpeg_ops.prepare_audio_track([long_audio], duration_seconds=1.0, output_path=output)

    duration = ffmpeg_ops.probe_duration(output)
    assert abs(duration - 1.0) < 0.2


def test_prepare_audio_track_mixes_two_inputs(tmp_path):
    first = tmp_path / "a.wav"
    second = tmp_path / "b.wav"
    ffmpeg_ops.run_ffmpeg(["-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=2", str(first)])
    ffmpeg_ops.run_ffmpeg(["-y", "-f", "lavfi", "-i", "sine=frequency=880:duration=2", str(second)])

    output = tmp_path / "mixed.wav"
    ffmpeg_ops.prepare_audio_track([first, second], duration_seconds=2.0, output_path=output)

    duration = ffmpeg_ops.probe_duration(output)
    assert abs(duration - 2.0) < 0.2


def test_render_shot_clip_combines_video_and_audio(tmp_path):
    image_path = _real_png(tmp_path)
    video_path = tmp_path / "video.mp4"
    ffmpeg_ops.image_to_video(image_path, 1.5, 320, 180, 24, video_path)

    audio_path = tmp_path / "audio.wav"
    ffmpeg_ops.prepare_audio_track([], 1.5, audio_path)

    output = tmp_path / "clip.mp4"
    ffmpeg_ops.render_shot_clip(video_path, audio_path, 320, 180, 24, output)

    assert sorted(_probe_streams(output)) == ["audio", "video"]
    assert abs(ffmpeg_ops.probe_duration(output) - 1.5) < 0.2


def test_concat_clips_sums_durations(tmp_path):
    clip_paths = []
    for index in range(3):
        image_path = _real_png(tmp_path, f"ref_{index}.png")
        video_path = tmp_path / f"video_{index}.mp4"
        ffmpeg_ops.image_to_video(image_path, 1.0, 320, 180, 24, video_path)
        audio_path = tmp_path / f"audio_{index}.wav"
        ffmpeg_ops.prepare_audio_track([], 1.0, audio_path)
        clip_path = tmp_path / f"clip_{index}.mp4"
        ffmpeg_ops.render_shot_clip(video_path, audio_path, 320, 180, 24, clip_path)
        clip_paths.append(clip_path)

    output = tmp_path / "concatenated.mp4"
    ffmpeg_ops.concat_clips(clip_paths, output)

    assert abs(ffmpeg_ops.probe_duration(output) - 3.0) < 0.3


def test_mux_subtitles_adds_a_subtitle_stream(tmp_path):
    image_path = _real_png(tmp_path)
    video_path = tmp_path / "video.mp4"
    ffmpeg_ops.image_to_video(image_path, 1.0, 320, 180, 24, video_path)
    audio_path = tmp_path / "audio.wav"
    ffmpeg_ops.prepare_audio_track([], 1.0, audio_path)
    clip = tmp_path / "clip.mp4"
    ffmpeg_ops.render_shot_clip(video_path, audio_path, 320, 180, 24, clip)

    srt_path = tmp_path / "subs.srt"
    srt_path.write_text("1\n00:00:00,000 --> 00:00:01,000\nHello\n")

    output = tmp_path / "with_subs.mp4"
    ffmpeg_ops.mux_subtitles(clip, srt_path, output)

    assert sorted(_probe_streams(output)) == ["audio", "subtitle", "video"]


def test_run_ffmpeg_raises_with_stderr_on_failure(tmp_path):
    with pytest.raises(RuntimeError):
        ffmpeg_ops.run_ffmpeg(["-y", "-i", str(tmp_path / "does-not-exist.mp4"), str(tmp_path / "out.mp4")])


def test_probe_duration_raises_for_a_missing_file(tmp_path):
    with pytest.raises(RuntimeError):
        ffmpeg_ops.probe_duration(tmp_path / "does-not-exist.mp4")
