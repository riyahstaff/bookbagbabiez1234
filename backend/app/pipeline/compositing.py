import io
import re

from PIL import Image

from app.models import Character, Scene, Series, Shot
from app.providers.background_removal.base import BackgroundRemovalProvider
from app.providers.image.base import ImageGenerationResult, ImageProvider

CANVAS_WIDTH = 1024
CANVAS_HEIGHT = 576
# Tallest character in a shot is scaled to this fraction of the canvas
# height; everyone else is scaled relative to them (see _parse_height_inches)
# so a teacher still reads as taller than the kids instead of everyone
# rendering at one flat size.
TALLEST_CHARACTER_HEIGHT_FRACTION = 0.85
# All characters' feet land on this line, regardless of height, so they read
# as standing together on the same floor instead of independently floating.
GROUND_LINE_FRACTION = 0.95

_FEET_INCHES = re.compile(r"(\d+)\s*'\s*(\d+)?\s*\"?")
_CENTIMETERS = re.compile(r"(\d+(?:\.\d+)?)\s*cm\b", re.IGNORECASE)
_METERS = re.compile(r"(\d+(?:\.\d+)?)\s*m(?:eters?)?\b", re.IGNORECASE)
# Used whenever a character's Character.height field is empty or doesn't
# match any pattern above, so unparsed heights fall back to "about the same
# as everyone else" instead of distorting the layout.
_DEFAULT_HEIGHT_INCHES = 54.0


def _parse_height_inches(height: str | None) -> float:
    if not height:
        return _DEFAULT_HEIGHT_INCHES
    match = _FEET_INCHES.search(height)
    if match:
        feet = int(match.group(1))
        inches = int(match.group(2)) if match.group(2) else 0
        return float(feet * 12 + inches)
    match = _CENTIMETERS.search(height)
    if match:
        return float(match.group(1)) / 2.54
    match = _METERS.search(height)
    if match:
        return float(match.group(1)) * 39.3701
    return _DEFAULT_HEIGHT_INCHES


def _fit_cover(image: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    """Resize+crop to fill target_size exactly without distorting aspect
    ratio - CSS background-size: cover, for backdrop plates and reused
    Location reference art that rarely arrive pre-sized to the canvas."""
    target_w, target_h = target_size
    src_w, src_h = image.size
    scale = max(target_w / src_w, target_h / src_h)
    resized = image.resize((round(src_w * scale), round(src_h * scale)), Image.LANCZOS)
    left = (resized.width - target_w) // 2
    top = (resized.height - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


def _build_background_prompt(shot: Shot, scene: Scene, series: Series) -> str:
    parts = []
    if series.visual_style_prompt:
        parts.append(series.visual_style_prompt)
    parts.append(f"{shot.shot_type.value.replace('_', ' ').lower()} shot")
    if shot.camera_angle:
        parts.append(shot.camera_angle)
    if scene.location:
        parts.append(", ".join(b for b in (scene.location.name, scene.location.description) if b))
    if shot.lighting:
        parts.append(f"{shot.lighting} lighting")
    # A background with strong one-point perspective (e.g. a street
    # receding to a vanishing point) fights the ground-line placement below:
    # two characters at the same screen height read as wildly different
    # depths instead of standing together, confirmed by a real test render.
    # Flat staging with an eye-level camera is what actually makes ground-
    # line placement look plausible.
    parts.append(
        "empty background plate, no characters, no people, flat staging, "
        "eye-level camera, minimal forced perspective"
    )
    return ", ".join(parts)


def _build_character_prompt(character: Character, shot: Shot, series: Series) -> str:
    # Deliberately omits shot.action and camera framing: this character is
    # rendered completely alone (no scene partner in frame), so an action
    # like "hands Nia the book" would ask the model to draw a one-sided
    # gesture at nothing. "full body, standing pose" is the one framing this
    # path supports - compositing can put consistent, well-scaled characters
    # in the same scene, not literal physical interaction between them.
    parts = []
    if series.visual_style_prompt:
        parts.append(series.visual_style_prompt)
    descriptor = ", ".join(b for b in (character.description, character.clothing, character.hair) if b)
    parts.append(f"{character.name} ({descriptor})" if descriptor else character.name)
    if shot.emotion:
        parts.append(f"emotion: {shot.emotion}")
    if shot.lighting:
        parts.append(f"{shot.lighting} lighting")
    parts.append(
        "full body, standing pose, facing forward, on a plain flat solid light gray background, "
        "no other objects, no scenery, no background"
    )
    return ", ".join(parts)


def composite_multi_character_shot(
    *,
    shot: Shot,
    scene: Scene,
    series: Series,
    characters: list[Character],
    reference_bytes_by_character: dict[int, bytes],
    location_background_bytes: bytes | None,
    image_provider: ImageProvider,
    background_removal_provider: BackgroundRemovalProvider,
    seed: int | None,
) -> ImageGenerationResult:
    """Fallback for shots with 2+ visible characters who all have an
    uploaded reference: image_provider.generate_image() only locks identity
    for a single reference per call (see FalImageProvider), so instead of
    falling back to plain text generation for every character at once, each
    one is generated alone (identity-locked to their own reference) on a
    plain background, cut out, and pasted onto a shared scene background -
    scaled by their relative Character.height and bottom-aligned to one
    ground line so they read as standing together, not independently pasted.
    Only called when every visible character has a reference; see
    generate_storyboard()."""
    model_names: list[str] = []
    seed_used = seed

    if location_background_bytes is not None:
        background = Image.open(io.BytesIO(location_background_bytes)).convert("RGBA")
    else:
        background_result = image_provider.generate_image(
            prompt=_build_background_prompt(shot, scene, series),
            seed=seed,
            width=CANVAS_WIDTH,
            height=CANVAS_HEIGHT,
        )
        model_names.append(background_result.model_name)
        seed_used = background_result.seed_used or seed_used
        background = Image.open(io.BytesIO(background_result.image_bytes)).convert("RGBA")
    canvas = _fit_cover(background, (CANVAS_WIDTH, CANVAS_HEIGHT))

    cutouts: list[Image.Image] = []
    height_inches: list[float] = []
    for character in characters:
        image_result = image_provider.generate_image(
            prompt=_build_character_prompt(character, shot, series),
            seed=seed,
            reference_image_bytes=reference_bytes_by_character[character.id],
        )
        model_names.append(image_result.model_name)
        seed_used = image_result.seed_used or seed_used

        removal_result = background_removal_provider.remove_background(image_result.image_bytes)
        model_names.append(removal_result.model_name)

        cutout = Image.open(io.BytesIO(removal_result.image_bytes)).convert("RGBA")
        bbox = cutout.split()[-1].getbbox()
        if bbox:
            cutout = cutout.crop(bbox)
        cutouts.append(cutout)
        height_inches.append(_parse_height_inches(character.height))

    tallest_inches = max(height_inches)
    tallest_target_height = CANVAS_HEIGHT * TALLEST_CHARACTER_HEIGHT_FRACTION
    ground_y = round(CANVAS_HEIGHT * GROUND_LINE_FRACTION)
    slot_width = CANVAS_WIDTH / len(cutouts)

    for index, (cutout, inches) in enumerate(zip(cutouts, height_inches)):
        target_height = round(tallest_target_height * (inches / tallest_inches))
        scale = target_height / cutout.height
        scaled = cutout.resize((max(1, round(cutout.width * scale)), target_height), Image.LANCZOS)

        slot_center_x = round(slot_width * (index + 0.5))
        paste_x = slot_center_x - scaled.width // 2
        paste_y = ground_y - scaled.height
        canvas.paste(scaled, (paste_x, paste_y), scaled)

    buffer = io.BytesIO()
    canvas.convert("RGB").save(buffer, format="PNG")
    # Dedup while preserving first-seen order, so e.g. two characters sharing
    # "fal-ai/instant-character" don't repeat it - keeps Generation.model_name
    # (String(200)) readable instead of an ever-growing per-character list.
    unique_model_names = list(dict.fromkeys(model_names))
    return ImageGenerationResult(
        image_bytes=buffer.getvalue(),
        seed_used=seed_used,
        model_name=", ".join(unique_model_names),
    )
