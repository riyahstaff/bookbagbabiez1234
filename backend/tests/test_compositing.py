import io
from types import SimpleNamespace

import pytest
from PIL import Image

from app.models.enums import ShotType
from app.pipeline.compositing import (
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    _parse_height_inches,
    composite_multi_character_shot,
)
from app.providers.background_removal.base import BackgroundRemovalResult
from app.providers.image.base import ImageGenerationResult


@pytest.mark.parametrize(
    ("height", "expected_inches"),
    [
        ("4'6\"", 54),
        ("5'0\"", 60),
        ("5'", 60),
        ("150cm", 150 / 2.54),
        ("1.5m", 1.5 * 39.3701),
        ("tall and lanky", 54.0),  # unparseable -> falls back to the default
        (None, 54.0),
        ("", 54.0),
    ],
)
def test_parse_height_inches(height, expected_inches):
    assert _parse_height_inches(height) == pytest.approx(expected_inches, rel=1e-3)


def _character(character_id, name, height=None, color=(200, 50, 50)):
    return SimpleNamespace(
        id=character_id,
        name=name,
        description=None,
        clothing=None,
        hair=None,
        height=height,
    ), color


def _flat_png(size, color) -> bytes:
    image = Image.new("RGB", size, color=color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


class _FakeImageProvider:
    """Returns a solid-color rectangle per call, keyed by the character name
    embedded in the prompt (or a generic plate for the background call), so
    tests can tell which pixels in the final composite came from which
    call without needing a real generative model."""

    def __init__(self, color_by_name: dict[str, tuple[int, int, int]]):
        self.color_by_name = color_by_name
        self.calls: list[dict] = []

    def generate_image(self, prompt, negative_prompt=None, seed=None, width=1024, height=576, reference_image_bytes=None):
        self.calls.append({"prompt": prompt, "reference_image_bytes": reference_image_bytes})
        color = next((c for name, c in self.color_by_name.items() if name in prompt), (30, 30, 30))
        # A fixed-size figure so relative scaling in the composite is driven
        # entirely by composite_multi_character_shot's own height logic, not
        # by this fake returning different raw sizes per character.
        size = (width, height) if reference_image_bytes is None else (200, 400)
        return ImageGenerationResult(image_bytes=_flat_png(size, color), seed_used=seed or 7, model_name=f"fake-image({color})")


class _PassthroughBackgroundRemovalProvider:
    def __init__(self):
        self.calls = 0

    def remove_background(self, image_bytes: bytes) -> BackgroundRemovalResult:
        self.calls += 1
        image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return BackgroundRemovalResult(image_bytes=buffer.getvalue(), model_name="fake-bgremoval")


def _column_height_for_color(image: Image.Image, color: tuple[int, int, int]) -> int:
    """Pixel height of the tallest contiguous run of `color` anywhere in the
    image - a proxy for "how tall did this character render" without the
    test needing to know exact paste coordinates."""
    pixels = image.convert("RGB")
    width, height = pixels.size
    best = 0
    for x in range(0, width, 2):
        run = 0
        best_run = 0
        for y in range(height):
            if pixels.getpixel((x, y)) == color:
                run += 1
                best_run = max(best_run, run)
            else:
                run = 0
        best = max(best, best_run)
    return best


def test_composite_scales_characters_by_relative_height_and_shares_ground_line():
    tall_character, tall_color = _character(1, "Teacher", height="6'0\"", color=(200, 50, 50))
    short_character, short_color = _character(2, "Student", height="3'0\"", color=(50, 50, 200))

    image_provider = _FakeImageProvider({"Teacher": tall_color, "Student": short_color})
    background_removal_provider = _PassthroughBackgroundRemovalProvider()

    shot = SimpleNamespace(shot_type=ShotType.WIDE, camera_angle=None, lighting=None, emotion=None)
    scene = SimpleNamespace(location=None)
    series = SimpleNamespace(visual_style_prompt=None)

    result = composite_multi_character_shot(
        shot=shot,
        scene=scene,
        series=series,
        characters=[tall_character, short_character],
        reference_bytes_by_character={1: b"teacher-ref", 2: b"student-ref"},
        location_background_bytes=None,
        image_provider=image_provider,
        background_removal_provider=background_removal_provider,
        seed=None,
    )

    image = Image.open(io.BytesIO(result.image_bytes))
    assert image.size == (CANVAS_WIDTH, CANVAS_HEIGHT)

    tall_height = _column_height_for_color(image, tall_color)
    short_height = _column_height_for_color(image, short_color)
    assert tall_height > short_height > 0
    # 6' vs 3' is a 2x ratio - the composited pixel heights should land close
    # to that same ratio, not just "taller by some amount".
    assert tall_height / short_height == pytest.approx(2.0, rel=0.15)

    # One background-plate call (no Location art available) + one call per
    # character, each carrying that character's own reference bytes through.
    assert len(image_provider.calls) == 3
    reference_calls = [c["reference_image_bytes"] for c in image_provider.calls if c["reference_image_bytes"]]
    assert sorted(reference_calls) == [b"student-ref", b"teacher-ref"]
    assert background_removal_provider.calls == 2


def test_composite_reuses_location_background_without_generating_one():
    character_a, color_a = _character(1, "Meek", height=None)
    character_b, color_b = _character(2, "Mook", height=None)

    image_provider = _FakeImageProvider({"Meek": color_a, "Mook": color_b})
    background_removal_provider = _PassthroughBackgroundRemovalProvider()

    shot = SimpleNamespace(shot_type=ShotType.WIDE, camera_angle=None, lighting=None, emotion=None)
    scene = SimpleNamespace(location=None)
    series = SimpleNamespace(visual_style_prompt=None)

    location_background = _flat_png((640, 360), (10, 200, 10))

    result = composite_multi_character_shot(
        shot=shot,
        scene=scene,
        series=series,
        characters=[character_a, character_b],
        reference_bytes_by_character={1: b"meek-ref", 2: b"mook-ref"},
        location_background_bytes=location_background,
        image_provider=image_provider,
        background_removal_provider=background_removal_provider,
        seed=None,
    )

    # No background-plate call: only the two character calls.
    assert len(image_provider.calls) == 2
    image = Image.open(io.BytesIO(result.image_bytes))
    assert image.size == (CANVAS_WIDTH, CANVAS_HEIGHT)
    # A strip of the reused location background should still show through
    # near the top, since neither character's cutout reaches that high.
    assert image.getpixel((5, 5)) == (10, 200, 10)


def test_composite_model_name_dedups_repeated_model_names():
    character_a, color_a = _character(1, "Meek")
    character_b, color_b = _character(2, "Mook")
    # Both characters resolve to the exact same fake color/model, so the
    # dedup logic has something real to collapse.
    image_provider = _FakeImageProvider({"Meek": (99, 99, 99), "Mook": (99, 99, 99)})
    background_removal_provider = _PassthroughBackgroundRemovalProvider()

    shot = SimpleNamespace(shot_type=ShotType.WIDE, camera_angle=None, lighting=None, emotion=None)
    scene = SimpleNamespace(location=None)
    series = SimpleNamespace(visual_style_prompt=None)

    result = composite_multi_character_shot(
        shot=shot,
        scene=scene,
        series=series,
        characters=[character_a, character_b],
        reference_bytes_by_character={1: b"a", 2: b"b"},
        location_background_bytes=_flat_png((10, 10), (0, 0, 0)),
        image_provider=image_provider,
        background_removal_provider=background_removal_provider,
        seed=None,
    )

    assert result.model_name.count("fake-image((99, 99, 99))") == 1
