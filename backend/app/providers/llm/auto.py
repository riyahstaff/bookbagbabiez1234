import logging

from app.providers.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class AutoLLMProvider(LLMProvider):
    """Tries each candidate provider cheapest-first for this specific prompt,
    falling through to the next one if a call raises - covers "pick whichever
    is cheaper" and "fall back when one is down" with the same logic. Cost is
    estimated as len(text) / 4 (a common rough token approximation - good
    enough to rank two providers against each other, not a precise count)
    times each provider's configured cost_per_1k_tokens. Candidates are only
    ever real, credentialed providers (see _build_auto_provider in
    __init__.py) - this never silently substitutes a free/mock result for a
    failed real one."""

    def __init__(self, candidates: list[tuple[LLMProvider, float]]):
        if not candidates:
            raise RuntimeError(
                "No real LLM provider is configured for 'auto' - set ANTHROPIC_API_KEY "
                "and/or OPENAI_API_KEY."
            )
        self.candidates = candidates

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        estimated_tokens = (len(system_prompt) + len(user_prompt)) / 4
        ranked = sorted(self.candidates, key=lambda candidate: candidate[1] * estimated_tokens)

        last_error: Exception | None = None
        for provider, _cost_per_1k_tokens in ranked:
            try:
                return provider.generate(system_prompt, user_prompt)
            except Exception as exc:  # noqa: BLE001 - any provider failure should trigger fallback
                logger.warning("%s failed, trying next provider: %s", type(provider).__name__, exc)
                last_error = exc

        raise RuntimeError(f"All configured LLM providers failed for this request: {last_error}")
