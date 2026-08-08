import io

import pytest
from PIL import Image, ImageDraw

import app.providers.background_removal.fal as fal_background_removal
from app.providers.background_removal.fal import FalBackgroundRemovalProvider
from app.providers.background_removal.mock import MockBackgroundRemovalProvider


def _solid_with_marker(bg_color=(40, 80, 120), marker_color=(255, 255, 255)) -> bytes:
    image = Image.new("RGB", (64, 64), color=bg_color)
    draw = ImageDraw.Draw(image)
    draw.rectangle([20, 20, 40, 40], fill=marker_color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_mock_keys_out_corner_color_but_keeps_marker():
    result = MockBackgroundRemovalProvider().remove_background(_solid_with_marker())
    image = Image.open(io.BytesIO(result.image_bytes))

    assert image.mode == "RGBA"
    assert image.getpixel((0, 0))[3] == 0  # background corner: transparent
    assert image.getpixel((30, 30))[3] == 255  # inside the marker: opaque


def test_mock_result_model_name():
    result = MockBackgroundRemovalProvider().remove_background(_solid_with_marker())
    assert result.model_name == "mock-background-removal-v1"


def test_fal_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("FAL_KEY", raising=False)
    with pytest.raises(RuntimeError):
        FalBackgroundRemovalProvider()


def test_fal_api_key_falls_back_to_environment(monkeypatch):
    monkeypatch.setenv("FAL_KEY", "from-env")
    provider = FalBackgroundRemovalProvider()
    assert provider.api_key == "from-env"


class _FakeGetResponse:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass


class _FakePostResponse:
    def __init__(self, json_data):
        self._json_data = json_data

    def raise_for_status(self):
        pass

    def json(self):
        return self._json_data


class _FakeClient:
    def __init__(self, calls, result_bytes):
        self.calls = calls
        self.result_bytes = result_bytes

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def post(self, url, headers=None, json=None):
        self.calls.append(("post", url, headers, json))
        return _FakePostResponse({"image": {"url": "https://v3b.fal.media/files/x/cutout.png"}})

    def get(self, url):
        self.calls.append(("get", url))
        return _FakeGetResponse(self.result_bytes)


def test_fal_remove_background_uploads_then_posts_image_url(monkeypatch):
    calls = []
    monkeypatch.setattr(
        fal_background_removal,
        "upload_file",
        lambda client, key, content, filename, content_type: calls.append(
            ("upload", content, filename, content_type)
        )
        or "https://v3b.fal.media/files/x/uploaded.png",
    )
    monkeypatch.setattr(
        fal_background_removal.httpx, "Client", lambda timeout: _FakeClient(calls, b"cutout-bytes")
    )

    provider = FalBackgroundRemovalProvider(api_key="test-key")
    result = provider.remove_background(b"source-image-bytes")

    assert result.image_bytes == b"cutout-bytes"
    assert result.model_name == "fal-ai/birefnet"

    assert calls[0] == ("upload", b"source-image-bytes", "character.png", "image/png")
    post_call = next(c for c in calls if c[0] == "post")
    assert post_call[1] == "https://fal.run/fal-ai/birefnet"
    assert post_call[2] == {"Authorization": "Key test-key"}
    assert post_call[3] == {"image_url": "https://v3b.fal.media/files/x/uploaded.png"}
