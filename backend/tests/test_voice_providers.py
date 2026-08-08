import io
import wave

from app.providers.voice.mock import MockVoiceProvider


def _decode(audio_bytes: bytes) -> wave.Wave_read:
    return wave.open(io.BytesIO(audio_bytes), "rb")


def test_mock_voice_provider_produces_real_decodable_wav():
    provider = MockVoiceProvider()
    result = provider.generate_speech("Hello there, this is a line of dialogue.", "VOICE_MARCUS_001")

    assert result.model_name == "mock-voice-v1"
    assert result.duration_seconds is not None

    with _decode(result.audio_bytes) as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getnframes() > 0
        computed_duration = wav_file.getnframes() / wav_file.getframerate()
        assert abs(computed_duration - result.duration_seconds) < 0.01


def test_mock_voice_provider_duration_scales_with_text_length():
    provider = MockVoiceProvider()
    short = provider.generate_speech("Hi.", "VOICE_MARCUS_001")
    long = provider.generate_speech("This is a much longer line of dialogue than the short one.", "VOICE_MARCUS_001")
    assert long.duration_seconds > short.duration_seconds


def test_mock_voice_provider_respects_speed():
    provider = MockVoiceProvider()
    normal = provider.generate_speech("A line of dialogue for pacing.", "VOICE_MARCUS_001", speed=1.0)
    fast = provider.generate_speech("A line of dialogue for pacing.", "VOICE_MARCUS_001", speed=2.0)
    assert fast.duration_seconds < normal.duration_seconds


def test_mock_voice_provider_zero_speed_does_not_crash():
    provider = MockVoiceProvider()
    result = provider.generate_speech("short line", "VOICE_MARCUS_001", speed=0)
    assert result.duration_seconds is not None


def test_mock_voice_provider_different_voices_produce_different_audio():
    provider = MockVoiceProvider()
    a = provider.generate_speech("same text", "VOICE_MARCUS_001")
    b = provider.generate_speech("same text", "VOICE_NARRATOR_001")
    assert a.audio_bytes != b.audio_bytes


def test_mock_voice_provider_deterministic_for_same_inputs():
    provider = MockVoiceProvider()
    a = provider.generate_speech("same text", "VOICE_MARCUS_001", speed=1.0)
    b = provider.generate_speech("same text", "VOICE_MARCUS_001", speed=1.0)
    assert a.audio_bytes == b.audio_bytes
