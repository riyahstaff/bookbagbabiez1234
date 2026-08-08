import io
import os
import wave

import httpx

from app.providers.voice.base import AudioGenerationResult, VoiceProvider

FAL_API_KEY_ENV_VAR = "FAL_KEY"


class FalVoiceProvider(VoiceProvider):
    """Calls fal.ai's hosted fal-ai/chatterbox/text-to-speech endpoint - the
    pinned Chatterbox choice from docs/ARCHITECTURE.md. Request/response
    shape verified against the live API (text-only body, audio.url on
    fal.media, unknown extra fields silently ignored rather than rejected).

    Known limitation: Chatterbox's real differentiator is zero-shot voice
    cloning from a short reference clip, via an audio_url input - but
    generate_speech() only receives voice_identifier (an opaque string, per
    the existing VoiceProvider contract used by OpenAICompatibleVoiceProvider
    too), not Voice.reference_audio_path. Every character currently gets
    Chatterbox's same default voice until that plumbing is added.
    voice_identifier is accepted for interface compatibility but unused.
    """

    model_name = "fal-ai/chatterbox/text-to-speech"

    def __init__(self, api_key: str | None = None, timeout_seconds: float = 120.0):
        self.api_key = api_key or os.environ.get(FAL_API_KEY_ENV_VAR)
        if not self.api_key:
            raise RuntimeError(f"{FAL_API_KEY_ENV_VAR} is not set - required for the fal voice provider.")
        self.timeout_seconds = timeout_seconds

    def generate_speech(
        self,
        text: str,
        voice_identifier: str,
        speed: float | None = None,
        extra_settings: dict | None = None,
    ) -> AudioGenerationResult:
        payload: dict = {"text": text}
        if speed is not None:
            payload["speed"] = speed
        if extra_settings:
            payload.update(extra_settings)

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(
                "https://fal.run/fal-ai/chatterbox/text-to-speech",
                headers={"Authorization": f"Key {self.api_key}"},
                json=payload,
            )
            response.raise_for_status()
            audio_url = response.json()["audio"]["url"]

            audio_response = client.get(audio_url)
            audio_response.raise_for_status()
            audio_bytes = audio_response.content

        return AudioGenerationResult(
            audio_bytes=audio_bytes,
            model_name=self.model_name,
            duration_seconds=_wav_duration_seconds(audio_bytes),
        )


def _wav_duration_seconds(audio_bytes: bytes) -> float | None:
    try:
        with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
            return wav_file.getnframes() / wav_file.getframerate()
    except (wave.Error, EOFError):
        return None
