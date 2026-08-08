from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class BackgroundRemovalResult:
    image_bytes: bytes  # RGBA PNG with a transparent background
    model_name: str


class BackgroundRemovalProvider(ABC):
    @abstractmethod
    def remove_background(self, image_bytes: bytes) -> BackgroundRemovalResult:
        """Cuts the main subject out of image_bytes onto a transparent
        background. Used only by the multi-character compositing pipeline
        (see pipeline/compositing.py) to isolate each character generated on
        a plain background before pasting them onto a shared scene
        background - single-character shots never call this."""
