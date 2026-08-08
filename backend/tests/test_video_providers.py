import io

from PIL import Image

from app.providers.image.mock import MockImageProvider
from app.providers.video.mock import MockVideoProvider


def _reference_image_bytes() -> bytes:
    return MockImageProvider().generate_image(prompt="a diner at dusk", seed=1).image_bytes


def test_mock_video_provider_produces_real_decodable_animated_gif():
    provider = MockVideoProvider()
    result = provider.generate_video(
        prompt="camera slowly pushes in", reference_image_bytes=_reference_image_bytes(), seed=42
    )

    assert result.model_name == "mock-video-v1"
    assert result.file_extension == "gif"
    assert result.duration_seconds is not None

    image = Image.open(io.BytesIO(result.video_bytes))
    frame_count = 0
    try:
        while True:
            image.seek(frame_count)
            frame_count += 1
    except EOFError:
        pass
    assert frame_count > 1  # actually animated, not a single still frame


def test_mock_video_provider_duration_defaults_and_clamps():
    provider = MockVideoProvider()
    ref = _reference_image_bytes()

    default = provider.generate_video(prompt="p", reference_image_bytes=ref, seed=1)
    assert default.duration_seconds == 4.0

    clamped_low = provider.generate_video(
        prompt="p", reference_image_bytes=ref, seed=1, duration_seconds=0.1
    )
    assert clamped_low.duration_seconds == 1.0

    clamped_high = provider.generate_video(
        prompt="p", reference_image_bytes=ref, seed=1, duration_seconds=999
    )
    assert clamped_high.duration_seconds == 6.0


def test_mock_video_provider_random_seed_when_none_given():
    provider = MockVideoProvider()
    result = provider.generate_video(prompt="p", reference_image_bytes=_reference_image_bytes())
    assert result.video_bytes


def test_mock_video_provider_respects_custom_dimensions():
    provider = MockVideoProvider()
    result = provider.generate_video(
        prompt="p", reference_image_bytes=_reference_image_bytes(), seed=1, width=320, height=180
    )
    image = Image.open(io.BytesIO(result.video_bytes))
    assert image.size == (320, 180)
