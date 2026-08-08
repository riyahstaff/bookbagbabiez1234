import pytest

from app.providers.fal_client import run_queue_job, upload_file


class _FakeResponse:
    def __init__(self, json_data=None, status_code=200, text=""):
        self._json_data = json_data
        self.status_code = status_code
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._json_data


class _FakeClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.requests = []

    def post(self, url, headers=None, json=None, content=None):
        self.requests.append(("post", url, headers, json, content))
        return self._responses.pop(0)

    def get(self, url, headers=None):
        self.requests.append(("get", url, headers))
        return self._responses.pop(0)


def test_upload_file_does_auth_then_upload_and_returns_access_url():
    client = _FakeClient(
        [
            _FakeResponse(json_data={"token": "tok123", "base_url": "https://v3b.fal.media"}),
            _FakeResponse(json_data={"access_url": "https://v3b.fal.media/files/x/pic.png", "uploaded": True}),
        ]
    )

    url = upload_file(client, "test-key", b"bytes", filename="pic.png", content_type="image/png")

    assert url == "https://v3b.fal.media/files/x/pic.png"
    auth_call, upload_call = client.requests
    assert auth_call[1] == "https://rest.alpha.fal.ai/storage/auth/token"
    assert auth_call[2] == {"Authorization": "Key test-key"}
    assert upload_call[1] == "https://v3b.fal.media/files/upload"
    assert upload_call[2] == {
        "Authorization": "Bearer tok123",
        "Content-Type": "image/png",
        "X-Fal-File-Name": "pic.png",
    }
    assert upload_call[4] == b"bytes"


def test_run_queue_job_polls_until_completed_then_fetches_response():
    client = _FakeClient(
        [
            _FakeResponse(
                json_data={
                    "status": "IN_QUEUE",
                    "request_id": "r1",
                    "status_url": "https://queue.fal.run/x/requests/r1/status",
                    "response_url": "https://queue.fal.run/x/requests/r1",
                }
            ),
            _FakeResponse(json_data={"status": "IN_PROGRESS"}),
            _FakeResponse(json_data={"status": "COMPLETED"}),
            _FakeResponse(json_data={"video": {"url": "https://v3b.fal.media/files/x/out.mp4"}}),
        ]
    )

    result = run_queue_job(client, "test-key", "some/endpoint", {"prompt": "hi"}, poll_interval_seconds=0)

    assert result == {"video": {"url": "https://v3b.fal.media/files/x/out.mp4"}}
    submit_call = client.requests[0]
    assert submit_call[1] == "https://queue.fal.run/some/endpoint"
    assert submit_call[3] == {"prompt": "hi"}


def test_run_queue_job_raises_on_failed_status():
    client = _FakeClient(
        [
            _FakeResponse(
                json_data={
                    "status": "IN_QUEUE",
                    "request_id": "r1",
                    "status_url": "https://queue.fal.run/x/requests/r1/status",
                    "response_url": "https://queue.fal.run/x/requests/r1",
                }
            ),
            _FakeResponse(json_data={"status": "FAILED"}),
        ]
    )

    with pytest.raises(RuntimeError, match="failed with status FAILED"):
        run_queue_job(client, "test-key", "some/endpoint", {}, poll_interval_seconds=0)


def test_run_queue_job_raises_when_response_is_an_error():
    client = _FakeClient(
        [
            _FakeResponse(
                json_data={
                    "status": "IN_QUEUE",
                    "request_id": "r1",
                    "status_url": "https://queue.fal.run/x/requests/r1/status",
                    "response_url": "https://queue.fal.run/x/requests/r1",
                }
            ),
            _FakeResponse(json_data={"status": "COMPLETED"}),
            _FakeResponse(status_code=422, text="missing field"),
        ]
    )

    with pytest.raises(RuntimeError, match="response error"):
        run_queue_job(client, "test-key", "some/endpoint", {}, poll_interval_seconds=0)
