from anthropic import Anthropic

from app.providers.llm.base import LLMProvider


class AnthropicProvider(LLMProvider):
    """Reads ANTHROPIC_API_KEY from the environment (the SDK's own convention) -
    never pass or store the key anywhere else."""

    def __init__(self, model: str):
        self.model = model
        self._client = Anthropic()

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return "".join(block.text for block in response.content if block.type == "text")
