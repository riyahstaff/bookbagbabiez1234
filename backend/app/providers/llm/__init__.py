from functools import lru_cache

from app.config import get_settings
from app.providers.llm.base import LLMProvider
from app.providers.llm.mock import MockLLMProvider


def _build_provider(name: str, model: str | None) -> LLMProvider:
    if name == "mock":
        return MockLLMProvider()
    if name == "anthropic":
        from app.providers.llm.anthropic_provider import AnthropicProvider

        return AnthropicProvider(model=model or "claude-sonnet-5")
    if name == "openai_compatible":
        from app.providers.llm.openai_compatible import OpenAICompatibleProvider

        return OpenAICompatibleProvider(model=model or "gpt-4o-mini")
    raise ValueError(f"Unknown LLM provider: {name!r}")


@lru_cache
def get_creative_llm() -> LLMProvider:
    settings = get_settings()
    return _build_provider(settings.llm_creative_provider, settings.llm_creative_model)


@lru_cache
def get_mechanical_llm() -> LLMProvider:
    settings = get_settings()
    return _build_provider(settings.llm_mechanical_provider, settings.llm_mechanical_model)
