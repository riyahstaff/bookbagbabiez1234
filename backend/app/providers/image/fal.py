import os

import httpx

from app.providers.image.base import ImageGenerationResult, ImageProvider

FAL_API_KEY_ENV_VAR = "FAL_KEY"


class FalImageProvider(ImageProvider):
    """Calls fal.ai's hosted fal-ai/flux/schnell endpoint - the pinned FLUX.1
    [schnell] choice from docs/ARCHITECTURE.md, as a pay-per-call hosted
    alternative to self-hosting it behind ComfyUI. Request/response shape
    verified against the live API (custom image_size, seed echo, images[0].url
    on fal.media), not just documentation.

    flux/schnell has no negative-prompt input, so negative_prompt is accepted
    for interface compatibility but not sent.
    """

    model_name = "fal-ai/flux/schnell"

    def __init__(self, api_key: str | None = None, timeout_seconds: float = 60.0):
        self.api_key = api_key or os.environ.get(FAL_API_KEY_ENV_VAR)
        if not self.api_key:
            raise RuntimeError(f"{FAL_API_KEY_ENV_VAR} is not set - required for the fal image provider.")
        self.timeout_seconds = timeout_seconds

    def generate_image(
        self,
        prompt: str,
        negative_prompt: str | None = None,
        seed: int | None = None,
        width: int = 1024,
        height: int = 576,
    ) -> ImageGenerationResult:
        payload: dict = {
            "prompt": prompt,
            "image_size": {"width": width, "height": height},
            "num_images": 1,
        }
        if seed is not None:
            payload["seed"] = seed

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(
                "https://fal.run/fal-ai/flux/schnell",
                headers={"Authorization": f"Key {self.api_key}"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            image_url = data["images"][0]["url"]
            seed_used = data.get("seed", seed)

            image_response = client.get(image_url)
            image_response.raise_for_status()

        return ImageGenerationResult(
            image_bytes=image_response.content, seed_used=seed_used, model_name=self.model_name
        )
