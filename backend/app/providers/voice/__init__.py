from functools import lru_cache

from app.config import get_settings
from app.providers.voice.base import VoiceProvider
from app.providers.voice.mock import MockVoiceProvider


def _build_provider(name: str, model: str | None) -> VoiceProvider:
    if name == "mock":
        return MockVoiceProvider()
    if name == "openai_compatible":
        from app.providers.voice.openai_compatible import OpenAICompatibleVoiceProvider

        return OpenAICompatibleVoiceProvider(model=model or "tts-1")
    raise ValueError(f"Unknown voice provider: {name!r}")


@lru_cache
def get_voice_provider() -> VoiceProvider:
    settings = get_settings()
    return _build_provider(settings.voice_provider, settings.voice_model)
