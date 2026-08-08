import json

import pytest

from app.providers.llm.base import LLMProvider
from app.providers.llm.mock import MockLLMProvider


def test_mock_outline_stage():
    llm = MockLLMProvider()
    result = llm.generate("You are a writer.", "Treatment: a robot learns to cook.")
    assert "MOCK OUTLINE" in result


def test_mock_script_stage():
    llm = MockLLMProvider()
    result = llm.generate(
        "Write a screenplay-formatted script for the episode.", "Episode outline:\nAct 1..."
    )
    assert "MOCK SCRIPT" in result


def test_mock_scene_breakdown_stage_uses_known_names():
    llm = MockLLMProvider()
    system = (
        'Respond with ONLY valid JSON matching {"scenes": [...]}\n'
        "Known characters: Marcus, Zara\nKnown locations: Diner"
    )
    result = json.loads(llm.generate(system, "Script:\n...\n\nBreak this script into scenes."))
    assert result["scenes"][0]["location_name"] == "Diner"
    assert "Marcus" in result["scenes"][0]["characters_present"]


def test_mock_shot_breakdown_stage_uses_known_names():
    llm = MockLLMProvider()
    system = 'Respond with ONLY valid JSON matching {"shots": [...]}\nCharacters in this scene: Marcus'
    result = json.loads(llm.generate(system, "Scene 1:\nBreak this scene into a shot list."))
    assert result["shots"][1]["characters_visible"] == ["Marcus"]


def test_anthropic_provider_constructs_without_calling_api(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy-key-for-construction-only")
    from app.providers.llm.anthropic_provider import AnthropicProvider

    provider = AnthropicProvider(model="claude-sonnet-5")
    assert provider.model == "claude-sonnet-5"


def test_openai_compatible_provider_constructs_without_calling_api():
    from app.providers.llm.openai_compatible import OpenAICompatibleProvider

    provider = OpenAICompatibleProvider(model="llama3")
    assert provider.model == "llama3"


def test_provider_factory_defaults_to_mock():
    from app.config import get_settings
    from app.providers.llm import _build_provider

    settings = get_settings()
    provider = _build_provider(settings.llm_creative_provider, settings.llm_creative_model)
    assert isinstance(provider, MockLLMProvider)


class _FakeLLM(LLMProvider):
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = 0

    def generate(self, system_prompt, user_prompt):
        self.calls += 1
        if self.error:
            raise self.error
        return self.response


def test_auto_provider_uses_the_cheaper_candidate():
    from app.providers.llm.auto import AutoLLMProvider

    cheap = _FakeLLM(response="from cheap")
    expensive = _FakeLLM(response="from expensive")
    provider = AutoLLMProvider([(expensive, 1.0), (cheap, 0.01)])

    assert provider.generate("system", "user") == "from cheap"
    assert cheap.calls == 1
    assert expensive.calls == 0


def test_auto_provider_falls_back_when_cheaper_one_fails():
    from app.providers.llm.auto import AutoLLMProvider

    cheap = _FakeLLM(error=RuntimeError("cheap provider is down"))
    expensive = _FakeLLM(response="from expensive")
    provider = AutoLLMProvider([(expensive, 1.0), (cheap, 0.01)])

    assert provider.generate("system", "user") == "from expensive"
    assert cheap.calls == 1
    assert expensive.calls == 1


def test_auto_provider_raises_when_every_candidate_fails():
    from app.providers.llm.auto import AutoLLMProvider

    first = _FakeLLM(error=RuntimeError("first is down"))
    second = _FakeLLM(error=RuntimeError("second is down too"))
    provider = AutoLLMProvider([(first, 0.01), (second, 1.0)])

    with pytest.raises(RuntimeError, match="second is down too"):
        provider.generate("system", "user")


def test_auto_provider_with_no_candidates_raises_at_construction():
    from app.providers.llm.auto import AutoLLMProvider

    with pytest.raises(RuntimeError):
        AutoLLMProvider([])


def test_build_auto_provider_only_includes_credentialed_providers(monkeypatch):
    from app.providers.llm import _build_auto_provider
    from app.providers.llm.anthropic_provider import AnthropicProvider
    from app.providers.llm.openai_compatible import OpenAICompatibleProvider

    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy-key-for-construction-only")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    provider = _build_auto_provider()

    assert len(provider.candidates) == 1
    assert isinstance(provider.candidates[0][0], AnthropicProvider)


def test_build_auto_provider_includes_both_when_both_credentialed(monkeypatch):
    from app.providers.llm import _build_auto_provider

    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy-key-for-construction-only")
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-key-for-construction-only")

    provider = _build_auto_provider()

    assert len(provider.candidates) == 2


def test_build_auto_provider_with_no_credentials_raises(monkeypatch):
    from app.providers.llm import _build_auto_provider

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(RuntimeError):
        _build_auto_provider()
