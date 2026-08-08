import hashlib
import io
import random
import textwrap

from PIL import Image, ImageDraw

from app.providers.image.base import ImageGenerationResult, ImageProvider


class MockImageProvider(ImageProvider):
    """Draws a real, decodable placeholder image with the prompt baked in as
    text - not empty/fake bytes - so Demo Mode and the approval workflow are
    visually meaningful without a GPU or downloaded model weights."""

    def generate_image(
        self,
        prompt: str,
        negative_prompt: str | None = None,
        seed: int | None = None,
        width: int = 1024,
        height: int = 576,
        reference_image_bytes: bytes | None = None,
    ) -> ImageGenerationResult:
        seed_used = seed if seed is not None else random.randint(0, 2**31 - 1)
        color = _color_from_seed(seed_used)

        image = Image.new("RGB", (width, height), color=color)
        draw = ImageDraw.Draw(image)
        draw.rectangle([8, 8, width - 8, height - 8], outline="white", width=3)
        draw.text((24, 24), "MOCK STORYBOARD (no real model called)", fill="white")
        draw.text((24, 60), textwrap.fill(prompt, width=60), fill="white")
        draw.text((24, height - 32), f"seed={seed_used}", fill="white")

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return ImageGenerationResult(
            image_bytes=buffer.getvalue(), seed_used=seed_used, model_name="mock-image-v1"
        )


def _color_from_seed(seed: int) -> tuple[int, int, int]:
    digest = hashlib.sha256(str(seed).encode()).digest()
    return digest[0], digest[1], digest[2]
