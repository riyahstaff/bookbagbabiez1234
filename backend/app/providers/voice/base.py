from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AudioGenerationResult:
    audio_bytes: bytes
    model_name: str
    duration_seconds: float | None = None


class VoiceProvider(ABC):
    @abstractmethod
    def generate_speech(
        self,
        text: str,
        voice_identifier: str,
        speed: float | None = None,
        extra_settings: dict | None = None,
    ) -> AudioGenerationResult: ...
