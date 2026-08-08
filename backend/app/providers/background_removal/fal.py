import os

import httpx

from app.providers.background_removal.base import BackgroundRemovalProvider, BackgroundRemovalResult
from app.providers.fal_client import upload_file

FAL_API_KEY_ENV_VAR = "FAL_KEY"


class FalBackgroundRemovalProvider(BackgroundRemovalProvider):
    """Calls fal.ai's hosted BiRefNet. Chosen after a real side-by-side test
    (against a character rendered on a plain background, the multi-character
    pipeline's actual use case) of the three live candidates found for this:
    fal-ai/birefnet, fal-ai/imageutils/rembg, and fal-ai/bria/background/remove.
    bria's endpoint returned the input image completely unchanged - a dead
    end, not used. birefnet and rembg both produced clean RGBA cutouts, but
    only birefnet preserved the character's own ground shadow, which is what
    sells them as standing on a surface once composited onto a new
    background rather than looking pasted on - so it won out over rembg on
    quality for this specific use.

    Synchronous (fal.run), not the async queue like instant-character - a
    same empty-body probe against all three confirmed image_url is the only
    required field, and BiRefNet is fast enough not to need queueing.
    """

    def __init__(self, api_key: str | None = None, timeout_seconds: float = 60.0):
        self.api_key = api_key or os.environ.get(FAL_API_KEY_ENV_VAR)
        if not self.api_key:
            raise RuntimeError(
                f"{FAL_API_KEY_ENV_VAR} is not set - required for the fal background-removal provider."
            )
        self.timeout_seconds = timeout_seconds

    def remove_background(self, image_bytes: bytes) -> BackgroundRemovalResult:
        with httpx.Client(timeout=self.timeout_seconds) as client:
            image_url = upload_file(
                client, self.api_key, image_bytes, filename="character.png", content_type="image/png"
            )
            response = client.post(
                "https://fal.run/fal-ai/birefnet",
                headers={"Authorization": f"Key {self.api_key}"},
                json={"image_url": image_url},
            )
            response.raise_for_status()
            result_url = response.json()["image"]["url"]

            image_response = client.get(result_url)
            image_response.raise_for_status()

        return BackgroundRemovalResult(image_bytes=image_response.content, model_name="fal-ai/birefnet")
