import struct
import wave
from io import BytesIO

import pytest

from app.providers.voice.fal import FalVoiceProvider


def _real_wav_bytes(seconds: float = 0.5, framerate: int = 16000) -> bytes:
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(framerate)
        frame_count = int(seconds * framerate)
        wav_file.writeframes(struct.pack("<" + "h" * frame_count, *([0] * frame_count)))
    return buffer.getvalue()


class _FakeResponse:
    def __init__(self, json_data=None, content=b""):
        self._json_data = json_data
        self.content = content

    def raise_for_status(self):
        pass

    def json(self):
        return self._json_data


class _FakeClient:
    def __init__(self, calls, audio_bytes):
        self.calls = calls
        self.audio_bytes = audio_bytes

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def post(self, url, headers=None, json=None):
        self.calls.append(("post", url, headers, json))
        return _FakeResponse(json_data={"audio": {"url": "https://v3b.fal.media/files/x/fake.wav"}})

    def get(self, url):
        self.calls.append(("get", url))
        return _FakeResponse(content=self.audio_bytes)


def test_generate_speech_sends_text_and_parses_response(monkeypatch):
    calls = []
    wav_bytes = _real_wav_bytes(seconds=0.5)
    monkeypatch.setattr("httpx.Client", lambda timeout: _FakeClient(calls, wav_bytes))

    provider = FalVoiceProvider(api_key="test-key")
    result = provider.generate_speech(text="Good looking out.", voice_identifier="VOICE_001")

    assert result.audio_bytes == wav_bytes
    assert result.model_name == "fal-ai/chatterbox/text-to-speech"
    assert result.duration_seconds == pytest.approx(0.5, abs=0.01)

    post_call = calls[0]
    assert post_call[1] == "https://fal.run/fal-ai/chatterbox/text-to-speech"
    assert post_call[2] == {"Authorization": "Key test-key"}
    assert post_call[3] == {"text": "Good looking out."}


def test_generate_speech_passes_through_speed_and_extra_settings(monkeypatch):
    calls = []
    monkeypatch.setattr("httpx.Client", lambda timeout: _FakeClient(calls, _real_wav_bytes()))

    provider = FalVoiceProvider(api_key="test-key")
    provider.generate_speech(
        text="hello",
        voice_identifier="VOICE_001",
        speed=1.2,
        extra_settings={"emotion": "warm", "seed": 7},
    )

    assert calls[0][3] == {"text": "hello", "speed": 1.2, "emotion": "warm", "seed": 7}


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("FAL_KEY", raising=False)
    with pytest.raises(RuntimeError):
        FalVoiceProvider()
