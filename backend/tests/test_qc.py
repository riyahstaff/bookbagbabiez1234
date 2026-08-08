import io
import wave

from PIL import Image

from app.providers.image.mock import MockImageProvider
from app.providers.video.mock import MockVideoProvider
from app.providers.voice.mock import MockVoiceProvider
from app.qc import check_audio, check_image, check_video


def _png_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_check_image_passes_a_real_varied_image():
    real = MockImageProvider().generate_image(prompt="a busy diner at dusk", seed=1).image_bytes
    result = check_image(real)
    assert result.score == 1.0


def test_check_image_flags_a_blank_solid_color_image():
    blank = _png_bytes(Image.new("RGB", (200, 100), color=(120, 120, 120)))
    result = check_image(blank)
    assert result.score < 1.0
    assert "blank" in result.notes.lower()


def test_check_image_flags_an_all_black_image():
    result = check_image(_png_bytes(Image.new("RGB", (200, 100), color=(0, 0, 0))))
    assert result.score < 1.0


def test_check_image_flags_an_all_white_image():
    result = check_image(_png_bytes(Image.new("RGB", (200, 100), color=(255, 255, 255))))
    assert result.score < 1.0


def test_check_audio_passes_a_real_tone():
    real = MockVoiceProvider().generate_speech("a real line of dialogue", "VOICE_1").audio_bytes
    result = check_audio(real)
    assert result.score == 1.0


def test_check_audio_flags_silence():
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(22050)
        wav_file.writeframes(b"\x00\x00" * 22050)
    result = check_audio(buffer.getvalue())
    assert result.score < 1.0
    assert "silent" in result.notes.lower()


def test_check_audio_skips_non_16_bit_gracefully():
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(1)  # 8-bit - not analyzed
        wav_file.setframerate(22050)
        wav_file.writeframes(bytes([128]) * 22050)
    result = check_audio(buffer.getvalue())
    assert result.score == 1.0
    assert "skipped" in result.notes.lower()


def _reference_image_bytes() -> bytes:
    return MockImageProvider().generate_image(prompt="a diner at dusk", seed=1).image_bytes


def test_check_video_passes_mock_gif():
    video = MockVideoProvider().generate_video(
        prompt="camera push in", reference_image_bytes=_reference_image_bytes(), seed=1
    ).video_bytes
    result = check_video(video, "gif")
    assert result.score == 1.0


def test_check_video_flags_a_blank_gif():
    frame = Image.new("RGB", (100, 100), color=(80, 80, 80))
    buffer = io.BytesIO()
    frame.save(buffer, format="GIF", save_all=True, append_images=[frame, frame], duration=100, loop=0)
    result = check_video(buffer.getvalue(), "gif")
    assert result.score < 1.0
    assert "flagged" in result.notes.lower()


def test_check_video_skips_non_gif_extension_gracefully():
    result = check_video(b"not-a-real-mp4-but-that-is-fine", "mp4")
    assert result.score == 1.0
    assert "skipped" in result.notes.lower()


def test_check_video_gracefully_handles_undecodable_bytes():
    result = check_video(b"complete garbage, not an image at all", "gif")
    assert result.score == 1.0
    assert "skipped" in result.notes.lower()
