from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LipSyncResult:
    video_bytes: bytes
    model_name: str
    # "gif" when a Mock-produced input echoes straight through (see mock.py),
    # "mp4"/"webm" for real providers - same convention as
    # VideoGenerationResult.file_extension, and for the same reason: the
    # frontend picks <video> vs <img> from this, via Generation.output_path.
    file_extension: str


class LipSyncProvider(ABC):
    @abstractmethod
    def sync_lips(self, video_bytes: bytes, video_file_extension: str, audio_bytes: bytes) -> LipSyncResult:
        """Takes an already-rendered shot video and its dialogue/narration
        audio, returns a new video with lip movement matched to the audio -
        the "separate lip-sync pass" docs/RESEARCH.md describes for pilot
        production, run after the shot's video already exists rather than
        as part of initial generation."""
