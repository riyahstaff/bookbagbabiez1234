from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ImageGenerationResult:
    image_bytes: bytes
    seed_used: int | None
    model_name: str


class ImageProvider(ABC):
    @abstractmethod
    def generate_image(
        self,
        prompt: str,
        negative_prompt: str | None = None,
        seed: int | None = None,
        width: int = 1024,
        height: int = 576,
    ) -> ImageGenerationResult: ...

    def supports_seed(self) -> bool:
        return True

    def supports_reference_image(self) -> bool:
        """Whether this provider can be conditioned on Character/Location Bible
        reference images (IP-Adapter/ControlNet-style), not just a text prompt.
        No bundled provider supports this yet - descriptive prompting (see
        pipeline/shot_prompt.py) covers a real chunk of the consistency benefit
        without it. Left here so a future provider can opt in."""
        return False
