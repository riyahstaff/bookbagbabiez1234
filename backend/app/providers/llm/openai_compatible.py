import os

from openai import OpenAI

from app.providers.llm.base import LLMProvider


class OpenAICompatibleProvider(LLMProvider):
    """Works for real OpenAI, and for any local OpenAI-compatible endpoint
    (Ollama, vLLM, etc.) by pointing OPENAI_BASE_URL at it - e.g.
    http://localhost:11434/v1 for Ollama. No separate "Ollama provider" needed.
    """

    def __init__(self, model: str):
        self.model = model
        self._client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY", "not-needed-for-local-endpoints"),
            base_url=os.environ.get("OPENAI_BASE_URL") or None,
        )

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content or ""
