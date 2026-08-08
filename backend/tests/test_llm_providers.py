import json

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
