import pytest
from pydantic import BaseModel

from app.pipeline.structured import StructuredGenerationError, generate_structured
from app.providers.llm.base import LLMProvider


class _Point(BaseModel):
    x: int
    y: int


class _AlwaysValid(LLMProvider):
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        return '{"x": 1, "y": 2}'


class _InvalidThenValid(LLMProvider):
    def __init__(self):
        self.calls = 0

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.calls += 1
        if self.calls == 1:
            return "not json at all"
        return '{"x": 3, "y": 4}'


class _AlwaysInvalid(LLMProvider):
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        return "still not json"


def test_generate_structured_parses_valid_json():
    result = generate_structured(_AlwaysValid(), "sys", "user", _Point)
    assert result == _Point(x=1, y=2)


def test_generate_structured_strips_markdown_fences():
    class _Fenced(LLMProvider):
        def generate(self, system_prompt: str, user_prompt: str) -> str:
            return '```json\n{"x": 5, "y": 6}\n```'

    result = generate_structured(_Fenced(), "sys", "user", _Point)
    assert result == _Point(x=5, y=6)


def test_generate_structured_retries_once_on_invalid_json():
    provider = _InvalidThenValid()
    result = generate_structured(provider, "sys", "user", _Point, max_attempts=2)
    assert result == _Point(x=3, y=4)
    assert provider.calls == 2


def test_generate_structured_raises_after_exhausting_attempts():
    with pytest.raises(StructuredGenerationError):
        generate_structured(_AlwaysInvalid(), "sys", "user", _Point, max_attempts=2)
