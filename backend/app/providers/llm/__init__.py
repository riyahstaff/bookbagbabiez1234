import os
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
    if name == "auto":
        return _build_auto_provider()
    raise ValueError(f"Unknown LLM provider: {name!r}")


def _build_auto_provider() -> LLMProvider:
    # OpenAICompatibleProvider always constructs (it falls back to a
    # placeholder key for local, no-auth endpoints), so "is this a real,
    # credentialed provider" has to be checked here directly against the
    # environment rather than by seeing whether construction succeeds.
    from app.providers.llm.anthropic_provider import AnthropicProvider
    from app.providers.llm.auto import AutoLLMProvider
    from app.providers.llm.openai_compatible import OpenAICompatibleProvider

    settings = get_settings()
    candidates: list[tuple[LLMProvider, float]] = []
    if os.environ.get("ANTHROPIC_API_KEY"):
        candidates.append(
            (AnthropicProvider(model="claude-sonnet-5"), settings.llm_anthropic_cost_per_1k_tokens)
        )
    if os.environ.get("OPENAI_API_KEY"):
        candidates.append(
            (OpenAICompatibleProvider(model="gpt-4o-mini"), settings.llm_openai_cost_per_1k_tokens)
        )
    return AutoLLMProvider(candidates)


@lru_cache
def get_creative_llm() -> LLMProvider:
    settings = get_settings()
    return _build_provider(settings.llm_creative_provider, settings.llm_creative_model)


@lru_cache
def get_mechanical_llm() -> LLMProvider:
    settings = get_settings()
    return _build_provider(settings.llm_mechanical_provider, settings.llm_mechanical_model)
