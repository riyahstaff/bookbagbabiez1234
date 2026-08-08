from app.providers.video import get_video_provider
from app.providers.video.base import VideoProvider


def _create_shot(client) -> int:
    series_id = client.post("/api/series", json={"title": "Space Pals"}).json()["id"]
    episode = client.post(
        f"/api/series/{series_id}/episodes", json={"episode_number": 1, "title": "Pilot"}
    ).json()
    scene = client.post(f"/api/episodes/{episode['id']}/scenes", json={"scene_number": 1}).json()
    shot = client.post(
        f"/api/scenes/{scene['id']}/shots",
        json={"shot_number": 1, "shot_type": "MEDIUM", "duration_seconds": 3},
    ).json()
    return shot["id"]


def _create_shot_with_approved_image(client) -> tuple[int, int]:
    shot_id = _create_shot(client)
    image = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={}).json()
    client.post(f"/api/generations/{image['id']}/approve")
    return shot_id, image["id"]


def test_generate_video_happy_path(client):
    shot_id, _ = _create_shot_with_approved_image(client)

    response = client.post(f"/api/shots/{shot_id}/generate-video", json={})
    assert response.status_code == 201
    generation = response.json()

    assert generation["status"] == "COMPLETE"
    assert generation["generation_type"] == "VIDEO"
    assert generation["output_path"]
    assert generation["output_path"].endswith(".gif")  # Mock provider
    assert generation["prompt"]


def test_generate_video_blocked_with_no_image_at_all(client):
    shot_id = _create_shot(client)
    response = client.post(f"/api/shots/{shot_id}/generate-video", json={})
    assert response.status_code == 409


def test_generate_video_blocked_with_active_but_unapproved_image(client):
    shot_id = _create_shot(client)
    image = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={}).json()
    client.post(f"/api/generations/{image['id']}/activate")  # active, but not approved

    response = client.post(f"/api/shots/{shot_id}/generate-video", json={})
    assert response.status_code == 409


def test_generate_video_override_bypasses_approval_check(client):
    shot_id = _create_shot(client)
    image = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={}).json()
    client.post(f"/api/generations/{image['id']}/activate")

    response = client.post(f"/api/shots/{shot_id}/generate-video", json={"override_approval_gate": True})
    assert response.status_code == 201
    assert response.json()["status"] == "COMPLETE"


def test_generate_video_override_does_not_help_with_no_image_at_all(client):
    shot_id = _create_shot(client)
    response = client.post(f"/api/shots/{shot_id}/generate-video", json={"override_approval_gate": True})
    assert response.status_code == 409


def test_generate_video_on_missing_shot_404s(client):
    response = client.post("/api/shots/999999/generate-video", json={})
    assert response.status_code == 404


class _FailingVideoProvider(VideoProvider):
    def generate_video(
        self,
        prompt,
        reference_image_bytes,
        negative_prompt=None,
        seed=None,
        duration_seconds=None,
        width=1280,
        height=720,
    ):
        raise RuntimeError("GPU is down")


def test_generate_video_records_failure_instead_of_raising(client):
    from app.main import app

    shot_id, _ = _create_shot_with_approved_image(client)
    app.dependency_overrides[get_video_provider] = lambda: _FailingVideoProvider()
    try:
        response = client.post(f"/api/shots/{shot_id}/generate-video", json={})
    finally:
        del app.dependency_overrides[get_video_provider]

    assert response.status_code == 201
    generation = response.json()
    assert generation["status"] == "FAILED"
    assert generation["error_message"] == "GPU is down"
    assert generation["output_path"] is None


def test_video_generation_does_not_disturb_other_active_generations(client):
    shot_id, image_id = _create_shot_with_approved_image(client)

    video = client.post(f"/api/shots/{shot_id}/generate-video", json={}).json()
    client.post(f"/api/generations/{video['id']}/activate")

    shot = client.get(f"/api/shots/{shot_id}").json()
    assert shot["active_image_generation"]["id"] == image_id
    assert shot["active_video_generation"]["id"] == video["id"]

    # Generate and activate a second video version - only the video slot changes.
    video_2 = client.post(f"/api/shots/{shot_id}/generate-video", json={}).json()
    client.post(f"/api/generations/{video_2['id']}/activate")

    shot = client.get(f"/api/shots/{shot_id}").json()
    assert shot["active_image_generation"]["id"] == image_id
    assert shot["active_video_generation"]["id"] == video_2["id"]


def test_all_four_generation_types_active_simultaneously(client):
    series_id = client.post("/api/series", json={"title": "Space Pals"}).json()["id"]
    marcus = client.post(f"/api/series/{series_id}/characters", json={"name": "Marcus"}).json()
    episode = client.post(
        f"/api/series/{series_id}/episodes", json={"episode_number": 1, "title": "Pilot"}
    ).json()
    scene = client.post(f"/api/episodes/{episode['id']}/scenes", json={"scene_number": 1}).json()
    shot = client.post(
        f"/api/scenes/{scene['id']}/shots",
        json={
            "shot_number": 1,
            "shot_type": "MEDIUM",
            "dialogue": "No way, we made it!",
            "narration": "Meanwhile, across town...",
        },
    ).json()
    shot_id = shot["id"]
    marcus_voice_id = client.post(
        f"/api/series/{series_id}/voices", json={"name": "Marcus Voice", "character_id": marcus["id"]}
    ).json()["id"]
    narrator_voice_id = client.post(
        f"/api/series/{series_id}/voices", json={"name": "Narrator"}
    ).json()["id"]

    image = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={}).json()
    client.post(f"/api/generations/{image['id']}/approve")

    dialogue = client.post(
        f"/api/shots/{shot_id}/generate-voice", json={"track": "DIALOGUE", "voice_id": marcus_voice_id}
    ).json()
    client.post(f"/api/generations/{dialogue['id']}/approve")

    narration = client.post(
        f"/api/shots/{shot_id}/generate-voice", json={"track": "NARRATION", "voice_id": narrator_voice_id}
    ).json()
    client.post(f"/api/generations/{narration['id']}/activate")

    video = client.post(f"/api/shots/{shot_id}/generate-video", json={}).json()
    client.post(f"/api/generations/{video['id']}/activate")

    shot = client.get(f"/api/shots/{shot_id}").json()
    assert shot["active_image_generation"]["id"] == image["id"]
    assert shot["active_dialogue_generation"]["id"] == dialogue["id"]
    assert shot["active_narration_generation"]["id"] == narration["id"]
    assert shot["active_video_generation"]["id"] == video["id"]
