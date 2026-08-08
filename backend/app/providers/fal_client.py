"""Shared fal.ai plumbing used by more than one provider: uploading a local
file to fal's storage (required before referencing it as an image_url/
audio_url/video_url input) and polling the async job queue that the slower
models (video, lip-sync) use instead of a synchronous response.

Request/response shapes below are verified against the live API, not just
documentation: the storage auth-token/upload two-step, and the queue's
submit -> status -> response flow (including that a schema-validation
failure still reports queue status COMPLETED - the actual error only shows
up in the response body, not the status).
"""

import time

import httpx


def upload_file(client: httpx.Client, api_key: str, content: bytes, filename: str, content_type: str) -> str:
    auth_response = client.post(
        "https://rest.alpha.fal.ai/storage/auth/token",
        headers={"Authorization": f"Key {api_key}"},
        json={},
    )
    auth_response.raise_for_status()
    auth = auth_response.json()

    upload_response = client.post(
        f"{auth['base_url']}/files/upload",
        headers={
            "Authorization": f"Bearer {auth['token']}",
            "Content-Type": content_type,
            "X-Fal-File-Name": filename,
        },
        content=content,
    )
    upload_response.raise_for_status()
    return upload_response.json()["access_url"]


def run_queue_job(
    client: httpx.Client,
    api_key: str,
    endpoint: str,
    payload: dict,
    poll_interval_seconds: float = 3.0,
    timeout_seconds: float = 600.0,
) -> dict:
    submit_response = client.post(
        f"https://queue.fal.run/{endpoint}",
        headers={"Authorization": f"Key {api_key}"},
        json=payload,
    )
    submit_response.raise_for_status()
    submission = submit_response.json()

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        status_response = client.get(submission["status_url"], headers={"Authorization": f"Key {api_key}"})
        status_response.raise_for_status()
        status = status_response.json()["status"]
        if status == "COMPLETED":
            break
        if status in ("ERROR", "FAILED"):
            raise RuntimeError(f"fal job {submission['request_id']} failed with status {status}")
        time.sleep(poll_interval_seconds)
    else:
        raise TimeoutError(f"fal job {submission['request_id']} did not finish within {timeout_seconds}s")

    response = client.get(submission["response_url"], headers={"Authorization": f"Key {api_key}"})
    if response.status_code >= 400:
        raise RuntimeError(f"fal job {submission['request_id']} response error: {response.text[:1000]}")
    return response.json()
