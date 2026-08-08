import pytest

from app.providers.image import get_image_provider
from app.providers.image.base import ImageGenerationResult, ImageProvider


def _create_shot(client) -> tuple[int, int, int]:
    series_id = client.post("/api/series", json={"title": "Space Pals"}).json()["id"]
    marcus = client.post(f"/api/series/{series_id}/characters", json={"name": "Marcus"}).json()
    episode = client.post(
        f"/api/series/{series_id}/episodes", json={"episode_number": 1, "title": "Pilot"}
    ).json()
    scene = client.post(f"/api/episodes/{episode['id']}/scenes", json={"scene_number": 1}).json()
    client.put(
        f"/api/scenes/{scene['id']}/characters", json={"characters": [{"character_id": marcus["id"]}]}
    )
    shot = client.post(
        f"/api/scenes/{scene['id']}/shots", json={"shot_number": 1, "shot_type": "MEDIUM"}
    ).json()
    client.put(
        f"/api/shots/{shot['id']}/characters", json={"characters": [{"character_id": marcus["id"]}]}
    )
    return series_id, scene["id"], shot["id"]


def test_generate_storyboard_builds_prompt_when_missing(client):
    _, _, shot_id = _create_shot(client)

    response = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={})
    assert response.status_code == 201
    generation = response.json()

    assert generation["status"] == "COMPLETE"
    assert generation["approval_status"] == "PENDING"
    assert generation["is_active"] is False
    assert generation["provider_name"] == "MockImageProvider"
    assert generation["output_path"]
    assert "Marcus" in generation["prompt"]

    shot = client.get(f"/api/shots/{shot_id}").json()
    assert shot["visual_prompt"] == generation["prompt"]


def test_generate_storyboard_reuses_existing_shot_prompt(client):
    _, _, shot_id = _create_shot(client)
    client.patch(f"/api/shots/{shot_id}", json={"visual_prompt": "a hand-authored prompt"})

    response = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={})
    generation = response.json()

    assert generation["prompt"] == "a hand-authored prompt"


def test_generate_storyboard_persists_file_to_storage(client, test_storage):
    _, _, shot_id = _create_shot(client)

    generation = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={}).json()

    assert test_storage.exists(generation["output_path"])


def test_generate_storyboard_respects_explicit_seed(client):
    _, _, shot_id = _create_shot(client)

    generation = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={"seed": 12345}).json()

    assert generation["seed"] == 12345


def test_generate_storyboard_clamps_oversized_seed_instead_of_crashing(client):
    # SQLite can only store a signed 64-bit integer; a real fal-ai/
    # instant-character response returned a seed above that range and
    # crashed db.commit() with OverflowError - this is that exact value.
    _, _, shot_id = _create_shot(client)
    oversized_seed = 2**64 - 1

    response = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={"seed": oversized_seed})

    assert response.status_code == 201
    generation = response.json()
    assert generation["status"] == "COMPLETE"
    assert generation["seed"] == oversized_seed % (2**63)


def test_generate_storyboard_on_missing_shot_404s(client):
    response = client.post("/api/shots/999999/generate-storyboard", json={})
    assert response.status_code == 404


def test_list_generations_ordered_most_recent_first(client):
    _, _, shot_id = _create_shot(client)

    first = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={}).json()
    second = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={}).json()

    listed = client.get(f"/api/shots/{shot_id}/generations").json()
    assert [g["id"] for g in listed] == [second["id"], first["id"]]


class _FailingImageProvider(ImageProvider):
    def generate_image(
        self, prompt, negative_prompt=None, seed=None, width=1024, height=576, reference_image_bytes=None
    ):
        raise RuntimeError("provider is down")


def test_generate_storyboard_records_failure_instead_of_raising(client):
    from app.main import app

    _, _, shot_id = _create_shot(client)
    app.dependency_overrides[get_image_provider] = lambda: _FailingImageProvider()
    try:
        response = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={})
    finally:
        del app.dependency_overrides[get_image_provider]

    assert response.status_code == 201
    generation = response.json()
    assert generation["status"] == "FAILED"
    assert generation["error_message"] == "provider is down"
    assert generation["output_path"] is None

    listed = client.get(f"/api/shots/{shot_id}/generations").json()
    assert len(listed) == 1


def test_approve_generation_activates_and_deactivates_siblings(client):
    _, _, shot_id = _create_shot(client)
    first = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={}).json()
    second = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={}).json()

    approved = client.post(f"/api/generations/{second['id']}/approve").json()
    assert approved["approval_status"] == "APPROVED"
    assert approved["is_active"] is True

    sibling = client.get(f"/api/shots/{shot_id}/generations").json()
    first_after = next(g for g in sibling if g["id"] == first["id"])
    assert first_after["is_active"] is False


def test_reject_generation_marks_rejected_and_inactive(client):
    _, _, shot_id = _create_shot(client)
    generation = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={}).json()
    client.post(f"/api/generations/{generation['id']}/approve")

    rejected = client.post(f"/api/generations/{generation['id']}/reject").json()
    assert rejected["approval_status"] == "REJECTED"
    assert rejected["is_active"] is False


def test_activate_generation_switches_active_without_touching_approval(client):
    _, _, shot_id = _create_shot(client)
    first = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={}).json()
    second = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={}).json()

    client.post(f"/api/generations/{first['id']}/approve")
    activated = client.post(f"/api/generations/{second['id']}/activate").json()

    assert activated["is_active"] is True
    assert activated["approval_status"] == "PENDING"

    first_after = client.get(f"/api/shots/{shot_id}/generations").json()
    first_after = next(g for g in first_after if g["id"] == first["id"])
    assert first_after["is_active"] is False
    assert first_after["approval_status"] == "APPROVED"


def test_activate_on_missing_generation_404s(client):
    response = client.post("/api/generations/999999/activate")
    assert response.status_code == 404


def test_delete_generation_removes_row_and_file(client, test_storage):
    _, _, shot_id = _create_shot(client)
    generation = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={}).json()
    assert test_storage.exists(generation["output_path"])

    response = client.delete(f"/api/generations/{generation['id']}")
    assert response.status_code == 204

    assert not test_storage.exists(generation["output_path"])
    assert client.get(f"/api/shots/{shot_id}/generations").json() == []


def test_shot_exposes_active_image_generation_summary(client):
    _, _, shot_id = _create_shot(client)
    shot = client.get(f"/api/shots/{shot_id}").json()
    assert shot["active_image_generation"] is None

    first = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={}).json()
    shot = client.get(f"/api/shots/{shot_id}").json()
    assert shot["active_image_generation"] is None  # not active until approved/activated

    client.post(f"/api/generations/{first['id']}/approve")
    shot = client.get(f"/api/shots/{shot_id}").json()
    assert shot["active_image_generation"]["id"] == first["id"]
    assert shot["active_image_generation"]["approval_status"] == "APPROVED"


def test_scene_shot_list_also_exposes_active_image_generation(client):
    _, scene_id, shot_id = _create_shot(client)
    generation = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={}).json()
    client.post(f"/api/generations/{generation['id']}/activate")

    shots = client.get(f"/api/scenes/{scene_id}/shots").json()
    shot = next(s for s in shots if s["id"] == shot_id)
    assert shot["active_image_generation"]["id"] == generation["id"]


def test_delete_on_missing_generation_404s(client):
    response = client.delete("/api/generations/999999")
    assert response.status_code == 404


def test_delete_failed_generation_without_output_path_does_not_crash(client):
    from app.main import app

    _, _, shot_id = _create_shot(client)
    app.dependency_overrides[get_image_provider] = lambda: _FailingImageProvider()
    try:
        generation = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={}).json()
    finally:
        del app.dependency_overrides[get_image_provider]
    assert generation["output_path"] is None

    response = client.delete(f"/api/generations/{generation['id']}")
    assert response.status_code == 204
