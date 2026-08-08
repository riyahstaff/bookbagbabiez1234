import io

from PIL import Image

from app.pipeline.shot_prompt import build_shot_prompt
from app.providers.image.mock import MockImageProvider


def test_mock_image_provider_produces_real_decodable_image():
    provider = MockImageProvider()
    result = provider.generate_image(prompt="Marcus waves at the camera", seed=42)

    assert result.seed_used == 42
    assert result.model_name == "mock-image-v1"

    image = Image.open(io.BytesIO(result.image_bytes))
    image.load()  # forces full decode, not just header parse
    assert image.format == "PNG"
    assert image.size == (1024, 576)


def test_mock_image_provider_random_seed_when_none_given():
    provider = MockImageProvider()
    result = provider.generate_image(prompt="A quiet diner at dusk")
    assert result.seed_used is not None


def test_mock_image_provider_same_seed_same_color():
    provider = MockImageProvider()
    first = provider.generate_image(prompt="same prompt", seed=7)
    second = provider.generate_image(prompt="same prompt", seed=7)

    first_pixel = Image.open(io.BytesIO(first.image_bytes)).getpixel((512, 288))
    second_pixel = Image.open(io.BytesIO(second.image_bytes)).getpixel((512, 288))
    assert first_pixel == second_pixel


def test_mock_image_provider_respects_custom_dimensions():
    provider = MockImageProvider()
    result = provider.generate_image(prompt="widescreen test", seed=1, width=512, height=288)
    image = Image.open(io.BytesIO(result.image_bytes))
    assert image.size == (512, 288)


class _Character:
    def __init__(self, name, description=None, clothing=None, hair=None):
        self.name = name
        self.description = description
        self.clothing = clothing
        self.hair = hair


class _Location:
    def __init__(self, name, description=None):
        self.name = name
        self.description = description


class _Scene:
    def __init__(self, location=None):
        self.location = location


class _Series:
    def __init__(self, visual_style_prompt=None, negative_style_prompt=None):
        self.visual_style_prompt = visual_style_prompt
        self.negative_style_prompt = negative_style_prompt


class _Shot:
    def __init__(
        self,
        shot_type,
        camera_angle=None,
        camera_movement=None,
        action=None,
        lighting=None,
        emotion=None,
    ):
        self.shot_type = shot_type
        self.camera_angle = camera_angle
        self.camera_movement = camera_movement
        self.action = action
        self.lighting = lighting
        self.emotion = emotion


class _ShotType:
    def __init__(self, value):
        self.value = value


def test_build_shot_prompt_combines_series_character_location_and_shot_fields():
    series = _Series(
        visual_style_prompt="flat 2D cel-shaded cartoon",
        negative_style_prompt="no photorealism, no extra fingers",
    )
    marcus = _Character("Marcus", description="tall and lanky", clothing="red hoodie", hair="short black hair")
    location = _Location("The Diner", description="a cozy 1950s-style diner")
    scene = _Scene(location=location)
    shot = _Shot(
        shot_type=_ShotType("CLOSE_UP"),
        camera_angle="low angle",
        camera_movement="slow push in",
        action="Marcus slides into a booth",
        lighting="warm neon",
        emotion="nervous",
    )

    visual_prompt, negative_prompt = build_shot_prompt(shot, scene, series, [marcus])

    assert visual_prompt.startswith("flat 2D cel-shaded cartoon, close up shot, low angle, camera: slow push in")
    assert "Marcus (tall and lanky, red hoodie, short black hair)" in visual_prompt
    assert "The Diner, a cozy 1950s-style diner" in visual_prompt
    assert "Marcus slides into a booth" in visual_prompt
    assert "warm neon lighting" in visual_prompt
    assert "emotion: nervous" in visual_prompt
    assert negative_prompt == "no photorealism, no extra fingers"


def test_build_shot_prompt_skips_blank_fields():
    series = _Series()
    shot = _Shot(shot_type=_ShotType("WIDE"))
    scene = _Scene(location=None)

    visual_prompt, negative_prompt = build_shot_prompt(shot, scene, series, [])

    assert visual_prompt == "wide shot"
    assert negative_prompt == ""


def test_build_shot_prompt_character_without_descriptors_uses_bare_name():
    series = _Series()
    shot = _Shot(shot_type=_ShotType("MEDIUM"))
    scene = _Scene(location=None)
    nameless_descriptor_character = _Character("Background Kid")

    visual_prompt, _ = build_shot_prompt(shot, scene, series, [nameless_descriptor_character])

    assert "Background Kid" in visual_prompt
    assert "Background Kid (" not in visual_prompt
