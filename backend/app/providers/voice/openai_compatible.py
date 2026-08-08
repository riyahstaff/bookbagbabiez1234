import io
import os
import wave

from openai import OpenAI

from app.providers.voice.base import AudioGenerationResult, VoiceProvider


class OpenAICompatibleVoiceProvider(VoiceProvider):
    """Works for real OpenAI TTS, and for any self-hosted server that exposes
    the same POST /audio/speech contract - this is how several community
    wrappers front Chatterbox (resemble-ai/chatterbox, MIT) or CosyVoice2
    (FunAudioLLM/CosyVoice, Apache 2.0), the two providers docs/RESEARCH.md
    recommends as the default, as well as Qwen3-TTS. Point TTS_BASE_URL at it
    - e.g. http://localhost:8880/v1 - and leave TTS_API_KEY unset for local
    servers that don't check it. These are deliberately separate env vars
    from OPENAI_BASE_URL/OPENAI_API_KEY (already claimed by the LLM provider)
    so the story pipeline and the voice pipeline can point at two different
    servers.

    `voice_identifier` is passed through verbatim as the `voice` field, so
    cloning a specific reference voice requires registering it with that
    server out of band first and storing the resulting handle in
    Voice.provider_voice_id - this class has no way to upload reference audio
    itself, since that registration step is not standardized across servers.
    `extra_settings` (Voice.pitch/emotion/generation_settings) is passed as
    `extra_body`, a best-effort passthrough real OpenAI's strict API will
    likely reject but self-hosted servers commonly accept for
    provider-specific knobs (e.g. Chatterbox's exaggeration/cfg_weight).

    Untested against a live server - none of the above expose a public
    endpoint this sandbox can reach - but the request/response shape matches
    OpenAI's real documented /audio/speech API.
    """

    def __init__(self, model: str):
        self.model = model
        self._client = OpenAI(
            api_key=os.environ.get("TTS_API_KEY", "not-needed-for-local-endpoints"),
            base_url=os.environ.get("TTS_BASE_URL") or None,
        )

    def generate_speech(
        self,
        text: str,
        voice_identifier: str,
        speed: float | None = None,
        extra_settings: dict | None = None,
    ) -> AudioGenerationResult:
        kwargs: dict = {
            "model": self.model,
            "voice": voice_identifier,
            "input": text,
            "response_format": "wav",
        }
        if speed:
            kwargs["speed"] = speed
        if extra_settings:
            kwargs["extra_body"] = extra_settings

        response = self._client.audio.speech.create(**kwargs)
        audio_bytes = response.content
        return AudioGenerationResult(
            audio_bytes=audio_bytes,
            model_name=self.model,
            duration_seconds=_wav_duration_seconds(audio_bytes),
        )


def _wav_duration_seconds(audio_bytes: bytes) -> float | None:
    try:
        with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
            return wav_file.getnframes() / wav_file.getframerate()
    except (wave.Error, EOFError):
        return None
