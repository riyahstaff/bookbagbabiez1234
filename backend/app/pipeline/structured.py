import json

from pydantic import BaseModel, ValidationError

from app.providers.llm.base import LLMProvider


class StructuredGenerationError(Exception):
    pass


def generate_structured(
    llm: LLMProvider,
    system_prompt: str,
    user_prompt: str,
    schema: type[BaseModel],
    max_attempts: int = 2,
) -> BaseModel:
    """Ask the LLM for JSON matching `schema`, retrying once with the parse
    error fed back if the first attempt isn't valid. Deliberately not relying
    on any provider-specific "JSON mode" - see providers/llm/base.py."""
    prompt = user_prompt
    last_error: Exception | None = None
    last_raw = ""
    for _ in range(max_attempts):
        raw = llm.generate(system_prompt, prompt)
        last_raw = raw
        json_text = _extract_json(raw)
        try:
            data = json.loads(json_text)
            return schema.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = exc
            prompt = (
                f"{user_prompt}\n\n"
                "Your previous response could not be parsed as valid JSON matching the required "
                f"schema. Error: {exc}\nPrevious response was:\n{raw}\n\n"
                "Respond again with ONLY valid JSON, no other text, no markdown fences."
            )
    raise StructuredGenerationError(
        f"LLM did not return valid structured output after {max_attempts} attempt(s): {last_error}. "
        f"Last raw response: {last_raw[:500]}"
    )


def _extract_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()
