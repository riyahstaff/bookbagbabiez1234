import pytest

import app.providers.image.fal as fal_image
from app.providers.image.fal import FalImageProvider


class _FakeResponse:
    def __init__(self, json_data=None, content=b""):
        self._json_data = json_data
        self.content = content

    def raise_for_status(self):
        pass

    def json(self):
        return self._json_data


class _FakeClient:
    def __init__(self, calls):
        self.calls = calls

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def post(self, url, headers=None, json=None):
        self.calls.append(("post", url, headers, json))
        return _FakeResponse(
            json_data={
                "images": [{"url": "https://v3b.fal.media/files/x/fake.jpg", "width": 1024, "height": 576}],
                "seed": json.get("seed", 999),
            }
        )

    def get(self, url):
        self.calls.append(("get", url))
        return _FakeResponse(content=b"fake-jpeg-bytes")


def test_generate_image_sends_expected_request_and_parses_response(monkeypatch):
    calls = []
    monkeypatch.setattr("httpx.Client", lambda timeout: _FakeClient(calls))

    provider = FalImageProvider(api_key="test-key")
    result = provider.generate_image(prompt="a lavender jacket", seed=42, width=1024, height=576)

    assert result.image_bytes == b"fake-jpeg-bytes"
    assert result.seed_used == 42
    assert result.model_name == "fal-ai/flux/schnell"

    post_call = calls[0]
    assert post_call[0] == "post"
    assert post_call[1] == "https://fal.run/fal-ai/flux/schnell"
    assert post_call[2] == {"Authorization": "Key test-key"}
    assert post_call[3] == {
        "prompt": "a lavender jacket",
        "image_size": {"width": 1024, "height": 576},
        "num_images": 1,
        "seed": 42,
    }

    get_call = calls[1]
    assert get_call == ("get", "https://v3b.fal.media/files/x/fake.jpg")


def test_generate_image_omits_seed_when_none_given(monkeypatch):
    calls = []
    monkeypatch.setattr("httpx.Client", lambda timeout: _FakeClient(calls))

    provider = FalImageProvider(api_key="test-key")
    provider.generate_image(prompt="no seed here")

    assert "seed" not in calls[0][3]


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("FAL_KEY", raising=False)
    with pytest.raises(RuntimeError):
        FalImageProvider()


def test_api_key_falls_back_to_environment(monkeypatch):
    monkeypatch.setenv("FAL_KEY", "from-env")
    provider = FalImageProvider()
    assert provider.api_key == "from-env"


def test_supports_reference_image_is_true():
    assert FalImageProvider(api_key="test-key").supports_reference_image() is True


class _FakeGetResponse:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass


class _FakeReferenceClient:
    def __init__(self, result_bytes):
        self.result_bytes = result_bytes

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def get(self, url):
        return _FakeGetResponse(self.result_bytes)


def test_generate_image_with_reference_uses_instant_character(monkeypatch):
    upload_calls = []
    queue_calls = []
    monkeypatch.setattr(
        fal_image,
        "upload_file",
        lambda client, key, content, filename, content_type: upload_calls.append(
            (content, filename, content_type)
        )
        or "https://v3b.fal.media/files/x/ref.png",
    )
    monkeypatch.setattr(
        fal_image,
        "run_queue_job",
        lambda client, key, endpoint, payload: queue_calls.append((endpoint, payload))
        or {"images": [{"url": "https://v3b.fal.media/files/x/out.jpg"}], "seed": 12345},
    )
    monkeypatch.setattr(fal_image.httpx, "Client", lambda timeout: _FakeReferenceClient(b"consistent-bytes"))

    provider = FalImageProvider(api_key="test-key")
    result = provider.generate_image(prompt="waving hello", reference_image_bytes=b"ref-image-bytes")

    assert result.image_bytes == b"consistent-bytes"
    assert result.model_name == "fal-ai/instant-character"
    assert result.seed_used == 12345
    assert upload_calls[0][0] == b"ref-image-bytes"
    endpoint, payload = queue_calls[0]
    assert endpoint == "fal-ai/instant-character"
    assert payload == {"prompt": "waving hello", "image_url": "https://v3b.fal.media/files/x/ref.png"}
