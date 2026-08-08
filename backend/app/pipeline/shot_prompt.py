from app.models import Character, Scene, Series, Shot


def build_shot_prompt(
    shot: Shot, scene: Scene, series: Series, characters_visible: list[Character]
) -> tuple[str, str]:
    """Deterministic (non-LLM) prompt construction: Series visual style +
    per-character Bible descriptions + location + this shot's own fields.
    Text-only for now - no bundled ImageProvider supports reference-image
    conditioning yet (see ImageProvider.supports_reference_image), but naming
    each character's established hair/clothing/skin tone here is what
    actually fights drift without it."""
    parts: list[str] = []

    if series.visual_style_prompt:
        parts.append(series.visual_style_prompt)

    parts.append(f"{shot.shot_type.value.replace('_', ' ').lower()} shot")
    if shot.camera_angle:
        parts.append(shot.camera_angle)
    if shot.camera_movement:
        parts.append(f"camera: {shot.camera_movement}")

    for character in characters_visible:
        descriptor = ", ".join(b for b in (character.description, character.clothing, character.hair) if b)
        parts.append(f"{character.name} ({descriptor})" if descriptor else character.name)

    if scene.location:
        parts.append(", ".join(b for b in (scene.location.name, scene.location.description) if b))

    if shot.action:
        parts.append(shot.action)
    if shot.lighting:
        parts.append(f"{shot.lighting} lighting")
    if shot.emotion:
        parts.append(f"emotion: {shot.emotion}")

    visual_prompt = ", ".join(part for part in parts if part)
    negative_prompt = series.negative_style_prompt or ""
    return visual_prompt, negative_prompt
