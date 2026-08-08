from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class VideoGenerationResult:
    video_bytes: bytes
    model_name: str
    # "mp4"/"webm" for real providers, "gif" for Mock (no ffmpeg/muxer
    # available in this dev environment - see mock.py). The frontend decides
    # <video> vs <img> from this, via the extension on Generation.output_path.
    file_extension: str
    duration_seconds: float | None = None


class VideoProvider(ABC):
    @abstractmethod
    def generate_video(
        self,
        prompt: str,
        reference_image_bytes: bytes,
        negative_prompt: str | None = None,
        seed: int | None = None,
        duration_seconds: float | None = None,
        width: int = 1280,
        height: int = 720,
    ) -> VideoGenerationResult: ...
