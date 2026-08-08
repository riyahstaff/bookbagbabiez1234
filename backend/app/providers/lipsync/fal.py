import os

import httpx

from app.providers.fal_client import run_queue_job, upload_file
from app.providers.lipsync.base import LipSyncProvider, LipSyncResult

FAL_API_KEY_ENV_VAR = "FAL_KEY"


class FalLipSyncProvider(LipSyncProvider):
    """Calls fal.ai's hosted MuseTalk (default) or LatentSync (quality_mode)
    endpoint - the exact default/quality-mode split docs/ARCHITECTURE.md
    pins. Required-field names verified for free against the live API (a
    schema-validation failure costs nothing, per fal's queue behavior - see
    fal_client.py); a full successful lip-sync run has NOT been paid for and
    verified end-to-end the way the image/voice/video providers were, since
    that needs a real rendered shot video to be worth spending on rather
    than a throwaway clip.

    MuseTalk and LatentSync name their video input differently
    (source_video_url vs video_url) - everything else about the two calls is
    identical, handled by the endpoint/field_name switch in __init__.
    """

    def __init__(self, api_key: str | None = None, quality_mode: bool = False, timeout_seconds: float = 600.0):
        self.api_key = api_key or os.environ.get(FAL_API_KEY_ENV_VAR)
        if not self.api_key:
            raise RuntimeError(f"{FAL_API_KEY_ENV_VAR} is not set - required for the fal lip-sync provider.")
        self.timeout_seconds = timeout_seconds
        if quality_mode:
            self.endpoint = "fal-ai/latentsync"
            self.video_field_name = "video_url"
            self.model_name = "fal-ai/latentsync"
        else:
            self.endpoint = "fal-ai/musetalk"
            self.video_field_name = "source_video_url"
            self.model_name = "fal-ai/musetalk"

    def sync_lips(self, video_bytes: bytes, video_file_extension: str, audio_bytes: bytes) -> LipSyncResult:
        with httpx.Client(timeout=self.timeout_seconds) as client:
            video_url = upload_file(
                client,
                self.api_key,
                video_bytes,
                filename=f"shot.{video_file_extension}",
                content_type=f"video/{video_file_extension}",
            )
            audio_url = upload_file(
                client, self.api_key, audio_bytes, filename="dialogue.wav", content_type="audio/wav"
            )

            payload = {self.video_field_name: video_url, "audio_url": audio_url}
            data = run_queue_job(client, self.api_key, self.endpoint, payload)
            result_url = data["video"]["url"]

            result_response = client.get(result_url)
            result_response.raise_for_status()

        # Real MuseTalk/LatentSync output is always mp4 regardless of the
        # input container.
        return LipSyncResult(video_bytes=result_response.content, model_name=self.model_name, file_extension="mp4")
