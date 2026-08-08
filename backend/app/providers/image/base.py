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
        reference_image_bytes: bytes | None = None,
    ) -> ImageGenerationResult:
        """reference_image_bytes is a single character's uploaded Character
        Bible reference image, passed only when supports_reference_image()
        is True and the caller has exactly one visible character with one
        available - see generate_storyboard(). Providers that can't use it
        (supports_reference_image() False) should just ignore the argument
        rather than erroring, so callers don't need a provider-specific
        branch."""
        ...

    def supports_seed(self) -> bool:
        return True

    def supports_reference_image(self) -> bool:
        """Whether this provider can be conditioned on a single Character
        Bible reference image (identity-preserving generation), not just a
        text prompt. Descriptive prompting (see pipeline/shot_prompt.py)
        covers a real chunk of the consistency benefit without it, but
        drifts across separate generations the way a fixed reference image
        doesn't."""
        return False
