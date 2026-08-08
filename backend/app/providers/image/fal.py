import os

import httpx

from app.providers.fal_client import run_queue_job, upload_file
from app.providers.image.base import ImageGenerationResult, ImageProvider

FAL_API_KEY_ENV_VAR = "FAL_KEY"


class FalImageProvider(ImageProvider):
    """Calls fal.ai's hosted FLUX endpoints - the pinned FLUX.1 [schnell]
    choice from docs/ARCHITECTURE.md, as a pay-per-call hosted alternative to
    self-hosting it behind ComfyUI. Request/response shapes verified against
    the live API, not just documentation.

    Without a reference image: fal-ai/flux/schnell (synchronous, fast, no
    negative-prompt input - accepted for interface compatibility but not
    sent). With one: fal-ai/instant-character (async queue - identity-
    preserving generation from a single reference image, chosen over
    photoreal-face tools like ip-adapter-face-id since it's built for
    stylized/illustrated characters, matching this app's flat-vector
    animation style, not face-recognition embeddings). supports_reference_image()
    is True specifically because of this second path.
    """

    def __init__(self, api_key: str | None = None, timeout_seconds: float = 120.0):
        self.api_key = api_key or os.environ.get(FAL_API_KEY_ENV_VAR)
        if not self.api_key:
            raise RuntimeError(f"{FAL_API_KEY_ENV_VAR} is not set - required for the fal image provider.")
        self.timeout_seconds = timeout_seconds

    def supports_reference_image(self) -> bool:
        return True

    def generate_image(
        self,
        prompt: str,
        negative_prompt: str | None = None,
        seed: int | None = None,
        width: int = 1024,
        height: int = 576,
        reference_image_bytes: bytes | None = None,
    ) -> ImageGenerationResult:
        if reference_image_bytes is not None:
            return self._generate_from_reference(prompt, reference_image_bytes)
        return self._generate_from_text(prompt, seed, width, height)

    def _generate_from_text(
        self, prompt: str, seed: int | None, width: int, height: int
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
            image_bytes=image_response.content, seed_used=seed_used, model_name="fal-ai/flux/schnell"
        )

    def _generate_from_reference(self, prompt: str, reference_image_bytes: bytes) -> ImageGenerationResult:
        with httpx.Client(timeout=self.timeout_seconds) as client:
            image_url = upload_file(
                client,
                self.api_key,
                reference_image_bytes,
                filename="character_reference.png",
                content_type="image/png",
            )
            data = run_queue_job(
                client, self.api_key, "fal-ai/instant-character", {"prompt": prompt, "image_url": image_url}
            )
            result_url = data["images"][0]["url"]

            image_response = client.get(result_url)
            image_response.raise_for_status()

        return ImageGenerationResult(
            image_bytes=image_response.content,
            seed_used=data.get("seed"),
            model_name="fal-ai/instant-character",
        )
