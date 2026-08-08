from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Plain text-in, text-out generation. Deliberately minimal: structured

    (JSON) output is handled by prompting + parsing at the pipeline layer,
    not by provider-specific "JSON mode" flags - that keeps this interface
    portable down to small local models that may not support real JSON mode.
    """

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str: ...
