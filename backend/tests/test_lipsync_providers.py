import pytest

import app.providers.lipsync.fal as fal_lipsync
from app.providers.lipsync.mock import MockLipSyncProvider


def test_mock_lipsync_returns_input_video_unchanged():
    provider = MockLipSyncProvider()
    result = provider.sync_lips(
        video_bytes=b"some-video-bytes", video_file_extension="gif", audio_bytes=b"some-audio-bytes"
    )

    assert result.video_bytes == b"some-video-bytes"
    assert result.model_name == "mock-lipsync-v1"
    assert result.file_extension == "gif"


class _FakeGetResponse:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass


class _FakeClient:
    def __init__(self, result_bytes):
        self.result_bytes = result_bytes

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def get(self, url):
        return _FakeGetResponse(self.result_bytes)


def test_default_mode_uses_musetalk_with_source_video_url_field(monkeypatch):
    upload_calls = []
    queue_calls = []
    monkeypatch.setattr(
        fal_lipsync,
        "upload_file",
        lambda client, key, content, filename, content_type: upload_calls.append(
            (content, filename, content_type)
        )
        or f"https://v3b.fal.media/files/x/{filename}",
    )
    monkeypatch.setattr(
        fal_lipsync,
        "run_queue_job",
        lambda client, key, endpoint, payload: queue_calls.append((endpoint, payload))
        or {"video": {"url": "https://v3b.fal.media/files/x/out.mp4"}},
    )
    monkeypatch.setattr(fal_lipsync.httpx, "Client", lambda timeout: _FakeClient(b"synced-video-bytes"))

    provider = fal_lipsync.FalLipSyncProvider(api_key="test-key")
    result = provider.sync_lips(video_bytes=b"video", video_file_extension="mp4", audio_bytes=b"audio")

    assert result.video_bytes == b"synced-video-bytes"
    assert result.model_name == "fal-ai/musetalk"
    assert result.file_extension == "mp4"
    endpoint, payload = queue_calls[0]
    assert endpoint == "fal-ai/musetalk"
    assert payload == {
        "source_video_url": "https://v3b.fal.media/files/x/shot.mp4",
        "audio_url": "https://v3b.fal.media/files/x/dialogue.wav",
    }


def test_quality_mode_uses_latentsync_with_video_url_field(monkeypatch):
    queue_calls = []
    monkeypatch.setattr(fal_lipsync, "upload_file", lambda client, key, content, filename, content_type: f"https://v3b.fal.media/files/x/{filename}")
    monkeypatch.setattr(
        fal_lipsync,
        "run_queue_job",
        lambda client, key, endpoint, payload: queue_calls.append((endpoint, payload))
        or {"video": {"url": "https://v3b.fal.media/files/x/out.mp4"}},
    )
    monkeypatch.setattr(fal_lipsync.httpx, "Client", lambda timeout: _FakeClient(b"synced"))

    provider = fal_lipsync.FalLipSyncProvider(api_key="test-key", quality_mode=True)
    provider.sync_lips(video_bytes=b"video", video_file_extension="mp4", audio_bytes=b"audio")

    endpoint, payload = queue_calls[0]
    assert endpoint == "fal-ai/latentsync"
    assert payload == {
        "video_url": "https://v3b.fal.media/files/x/shot.mp4",
        "audio_url": "https://v3b.fal.media/files/x/dialogue.wav",
    }


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("FAL_KEY", raising=False)
    with pytest.raises(RuntimeError):
        fal_lipsync.FalLipSyncProvider()
