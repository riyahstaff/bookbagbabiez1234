import io

from PIL import Image, ImageChops

from app.providers.background_removal.base import BackgroundRemovalProvider, BackgroundRemovalResult

# Anything within this much per-channel difference of the corner color is
# treated as background. MockImageProvider (and this provider's own real
# usage) both produce flat, unshaded solid-color backgrounds, so a plain
# corner-color chroma-key is a real (if crude) removal, not a fake one - it
# genuinely keys out the mock's background the same way a real
# background-removal model would key out a photo backdrop.
_THRESHOLD = 32


class MockBackgroundRemovalProvider(BackgroundRemovalProvider):
    """Chroma-keys out whatever solid color sits in the image's top-left
    corner - zero cost, zero setup, and a real (not faked) removal against
    the flat-color backgrounds MockImageProvider draws, so Demo Mode's
    multi-character compositing path is visually meaningful without a
    FAL_KEY."""

    def remove_background(self, image_bytes: bytes) -> BackgroundRemovalResult:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        rgb = image.convert("RGB")
        corner_color = rgb.getpixel((0, 0))

        solid_corner = Image.new("RGB", rgb.size, corner_color)
        diff = ImageChops.difference(rgb, solid_corner)
        # Weighted sum of the three channel diffs (matrix mode "L") stands in
        # for "how far from the corner color", cheaply and fully vectorized.
        distance = diff.convert("L", matrix=(1, 1, 1, 0))
        alpha = distance.point(lambda p: 0 if p < _THRESHOLD else 255)

        image.putalpha(alpha)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return BackgroundRemovalResult(image_bytes=buffer.getvalue(), model_name="mock-background-removal-v1")
