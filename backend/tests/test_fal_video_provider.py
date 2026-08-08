import pytest

import app.providers.video.fal as fal_video


class _FakeGetResponse:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass


class _FakeClient:
    def __init__(self, video_bytes):
        self.video_bytes = video_bytes
        self.get_urls = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def get(self, url):
        self.get_urls.append(url)
        return _FakeGetResponse(self.video_bytes)


def test_generate_video_uploads_image_submits_job_and_downloads_result(monkeypatch):
    upload_calls = []
    queue_calls = []

    def fake_upload_file(client, api_key, content, filename, content_type):
        upload_calls.append((api_key, content, filename, content_type))
        return "https://v3b.fal.media/files/x/uploaded.png"

    def fake_run_queue_job(client, api_key, endpoint, payload):
        queue_calls.append((api_key, endpoint, payload))
        return {"video": {"url": "https://v3b.fal.media/files/x/out.mp4"}}

    monkeypatch.setattr(fal_video, "upload_file", fake_upload_file)
    monkeypatch.setattr(fal_video, "run_queue_job", fake_run_queue_job)
    monkeypatch.setattr(fal_video.httpx, "Client", lambda timeout: _FakeClient(b"fake-mp4-bytes"))

    provider = fal_video.FalVideoProvider(api_key="test-key")
    result = provider.generate_video(
        prompt="a girl waves", reference_image_bytes=b"ref-bytes", seed=42, width=1280, height=720
    )

    assert result.video_bytes == b"fake-mp4-bytes"
    assert result.model_name == "fal-ai/wan/v2.2-5b/image-to-video"
    assert result.file_extension == "mp4"

    assert upload_calls[0][1] == b"ref-bytes"
    _, endpoint, payload = queue_calls[0]
    assert endpoint == "fal-ai/wan/v2.2-5b/image-to-video"
    assert payload == {
        "prompt": "a girl waves",
        "image_url": "https://v3b.fal.media/files/x/uploaded.png",
        "resolution": "720p",
        "seed": 42,
    }


def test_generate_video_uses_580p_below_720_height(monkeypatch):
    monkeypatch.setattr(fal_video, "upload_file", lambda *a, **k: "https://v3b.fal.media/files/x/u.png")
    captured = {}

    def fake_run_queue_job(client, api_key, endpoint, payload):
        captured.update(payload)
        return {"video": {"url": "https://v3b.fal.media/files/x/out.mp4"}}

    monkeypatch.setattr(fal_video, "run_queue_job", fake_run_queue_job)
    monkeypatch.setattr(fal_video.httpx, "Client", lambda timeout: _FakeClient(b"bytes"))

    provider = fal_video.FalVideoProvider(api_key="test-key")
    provider.generate_video(prompt="p", reference_image_bytes=b"x", width=854, height=480)

    assert captured["resolution"] == "580p"


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("FAL_KEY", raising=False)
    with pytest.raises(RuntimeError):
        fal_video.FalVideoProvider()
