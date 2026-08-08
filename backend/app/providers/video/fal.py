import os

import httpx

from app.providers.fal_client import run_queue_job, upload_file
from app.providers.video.base import VideoGenerationResult, VideoProvider

FAL_API_KEY_ENV_VAR = "FAL_KEY"


class FalVideoProvider(VideoProvider):
    """Calls fal.ai's hosted fal-ai/wan/v2.2-5b/image-to-video endpoint - the
    pinned Wan2.2-TI2V-5B choice from docs/ARCHITECTURE.md, as a pay-per-call
    hosted alternative to self-hosting it behind ComfyUI. Runs through fal's
    async job queue (this model is too slow for a synchronous response) and
    needs the reference image uploaded to fal's storage first, since the
    model takes an image_url, not raw bytes - both steps verified against the
    live API. Costs real money per call (~$0.06/video-second at the cheapest
    valid resolution, 580p - 480p is rejected by this specific model despite
    appearing in fal's general Wan pricing table).

    negative_prompt is accepted for interface compatibility but not sent -
    this model's schema doesn't document one.
    """

    model_name = "fal-ai/wan/v2.2-5b/image-to-video"

    def __init__(self, api_key: str | None = None, timeout_seconds: float = 600.0):
        self.api_key = api_key or os.environ.get(FAL_API_KEY_ENV_VAR)
        if not self.api_key:
            raise RuntimeError(f"{FAL_API_KEY_ENV_VAR} is not set - required for the fal video provider.")
        self.timeout_seconds = timeout_seconds

    def generate_video(
        self,
        prompt: str,
        reference_image_bytes: bytes,
        negative_prompt: str | None = None,
        seed: int | None = None,
        duration_seconds: float | None = None,
        width: int = 1280,
        height: int = 720,
    ) -> VideoGenerationResult:
        with httpx.Client(timeout=self.timeout_seconds) as client:
            image_url = upload_file(
                client, self.api_key, reference_image_bytes, filename="reference.png", content_type="image/png"
            )

            payload: dict = {
                "prompt": prompt,
                "image_url": image_url,
                "resolution": "720p" if height >= 720 else "580p",
            }
            if seed is not None:
                payload["seed"] = seed

            data = run_queue_job(client, self.api_key, "fal-ai/wan/v2.2-5b/image-to-video", payload)
            video_url = data["video"]["url"]

            video_response = client.get(video_url)
            video_response.raise_for_status()

        return VideoGenerationResult(
            video_bytes=video_response.content,
            model_name=self.model_name,
            file_extension="mp4",
            duration_seconds=duration_seconds,
        )
