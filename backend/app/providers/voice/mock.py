import hashlib
import io
import math
import struct
import wave

from app.providers.voice.base import AudioGenerationResult, VoiceProvider


class MockVoiceProvider(VoiceProvider):
    """Writes a real, decodable WAV file - a plain sine tone, not empty/fake
    bytes - so the approval workflow has something real to play without a
    GPU or downloaded model weights. Duration scales with text length; pitch
    is derived from the voice identifier so different voices are at least
    audibly distinct from each other."""

    SAMPLE_RATE = 22050

    def generate_speech(
        self,
        text: str,
        voice_identifier: str,
        speed: float | None = None,
        extra_settings: dict | None = None,
    ) -> AudioGenerationResult:
        speed_factor = speed if speed and speed > 0 else 1.0
        seconds = max(0.5, min(12.0, len(text) * 0.06 / speed_factor))
        digest = hashlib.sha256(voice_identifier.encode()).digest()
        frequency = 220 + (digest[0] % 440)
        num_samples = int(self.SAMPLE_RATE * seconds)

        frames = bytearray()
        for i in range(num_samples):
            sample = int(9000 * math.sin(2 * math.pi * frequency * i / self.SAMPLE_RATE))
            frames += struct.pack("<h", sample)

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.SAMPLE_RATE)
            wav_file.writeframes(bytes(frames))

        return AudioGenerationResult(
            audio_bytes=buffer.getvalue(), model_name="mock-voice-v1", duration_seconds=seconds
        )
