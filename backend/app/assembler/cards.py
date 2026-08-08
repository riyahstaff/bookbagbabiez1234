import io
import textwrap

from PIL import Image, ImageDraw


def _centered_text(draw: ImageDraw.ImageDraw, text: str, y: int, width: int, fill: str = "white") -> None:
    bbox = draw.textbbox((0, 0), text)
    text_width = bbox[2] - bbox[0]
    x = max(0, (width - text_width) // 2)
    draw.text((x, y), text, fill=fill)


def render_title_card(series_title: str, episode_title: str, episode_code: str, width: int, height: int) -> bytes:
    """A real, decodable placeholder title card - Pillow's built-in bitmap
    font, not ffmpeg's drawtext filter, since that needs a font available to
    fontconfig at render time and this doesn't. Same "real but plain, not
    fake" convention as the Mock providers."""
    image = Image.new("RGB", (width, height), color=(18, 18, 28))
    draw = ImageDraw.Draw(image)
    center_y = height // 2
    _centered_text(draw, series_title, center_y - 20, width)
    _centered_text(draw, f"{episode_code}: {episode_title}", center_y + 4, width)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def render_credits_card(series_title: str, character_names: list[str], width: int, height: int) -> bytes:
    image = Image.new("RGB", (width, height), color=(18, 18, 28))
    draw = ImageDraw.Draw(image)
    center_y = height // 2
    _centered_text(draw, "The End", center_y - 40, width)
    _centered_text(draw, series_title, center_y - 16, width)
    if character_names:
        featuring = "Featuring: " + ", ".join(character_names)
        for offset, line in enumerate(textwrap.wrap(featuring, width=60)):
            _centered_text(draw, line, center_y + 12 + offset * 14, width)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
