from app.providers.lipsync import get_lipsync_provider
from app.providers.lipsync.base import LipSyncProvider, LipSyncResult


def _create_shot_with_video_and_dialogue(client) -> tuple[int, int, int]:
    series_id = client.post("/api/series", json={"title": "Space Pals"}).json()["id"]
    episode = client.post(
        f"/api/series/{series_id}/episodes", json={"episode_number": 1, "title": "Pilot"}
    ).json()
    scene = client.post(f"/api/episodes/{episode['id']}/scenes", json={"scene_number": 1}).json()
    shot = client.post(
        f"/api/scenes/{scene['id']}/shots",
        json={"shot_number": 1, "shot_type": "MEDIUM", "dialogue": "No way, we made it!"},
    ).json()
    shot_id = shot["id"]
    voice_id = client.post(f"/api/series/{series_id}/voices", json={"name": "Voice"}).json()["id"]

    image = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={}).json()
    client.post(f"/api/generations/{image['id']}/approve")

    dialogue = client.post(
        f"/api/shots/{shot_id}/generate-voice", json={"track": "DIALOGUE", "voice_id": voice_id}
    ).json()
    client.post(f"/api/generations/{dialogue['id']}/approve")

    video = client.post(f"/api/shots/{shot_id}/generate-video", json={}).json()
    client.post(f"/api/generations/{video['id']}/approve")

    return shot_id, video["id"], dialogue["id"]


def test_generate_lipsync_happy_path_preserves_mock_gif_extension(client):
    shot_id, video_id, _ = _create_shot_with_video_and_dialogue(client)

    response = client.post(f"/api/shots/{shot_id}/generate-lipsync", json={})
    assert response.status_code == 201
    generation = response.json()

    assert generation["status"] == "COMPLETE"
    assert generation["generation_type"] == "VIDEO"
    assert generation["output_path"].endswith(".gif")  # Mock echoes the input container through


def test_generate_lipsync_and_plain_video_share_the_active_video_slot(client):
    shot_id, video_id, _ = _create_shot_with_video_and_dialogue(client)

    lipsync = client.post(f"/api/shots/{shot_id}/generate-lipsync", json={}).json()
    client.post(f"/api/generations/{lipsync['id']}/activate")

    shot = client.get(f"/api/shots/{shot_id}").json()
    assert shot["active_video_generation"]["id"] == lipsync["id"]

    # Activating the original plain video again takes the slot back.
    client.post(f"/api/generations/{video_id}/activate")
    shot = client.get(f"/api/shots/{shot_id}").json()
    assert shot["active_video_generation"]["id"] == video_id


def test_generate_lipsync_blocked_with_no_active_video(client):
    series_id = client.post("/api/series", json={"title": "Space Pals"}).json()["id"]
    episode = client.post(
        f"/api/series/{series_id}/episodes", json={"episode_number": 1, "title": "Pilot"}
    ).json()
    scene = client.post(f"/api/episodes/{episode['id']}/scenes", json={"scene_number": 1}).json()
    shot = client.post(f"/api/scenes/{scene['id']}/shots", json={"shot_number": 1}).json()

    response = client.post(f"/api/shots/{shot['id']}/generate-lipsync", json={})
    assert response.status_code == 409


def test_generate_lipsync_blocked_with_no_active_dialogue(client):
    series_id = client.post("/api/series", json={"title": "Space Pals"}).json()["id"]
    episode = client.post(
        f"/api/series/{series_id}/episodes", json={"episode_number": 1, "title": "Pilot"}
    ).json()
    scene = client.post(f"/api/episodes/{episode['id']}/scenes", json={"scene_number": 1}).json()
    shot = client.post(f"/api/scenes/{scene['id']}/shots", json={"shot_number": 1}).json()
    shot_id = shot["id"]

    image = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={}).json()
    client.post(f"/api/generations/{image['id']}/approve")
    client.post(f"/api/shots/{shot_id}/generate-video", json={})
    video = client.get(f"/api/shots/{shot_id}/generations").json()[0]
    client.post(f"/api/generations/{video['id']}/approve")

    response = client.post(f"/api/shots/{shot_id}/generate-lipsync", json={})
    assert response.status_code == 409


def test_generate_lipsync_blocked_with_unapproved_video(client):
    shot_id, video_id, _ = _create_shot_with_video_and_dialogue(client)
    client.post(f"/api/generations/{video_id}/reject")

    response = client.post(f"/api/shots/{shot_id}/generate-lipsync", json={})
    assert response.status_code == 409


def test_generate_lipsync_override_bypasses_approval_check(client):
    series_id = client.post("/api/series", json={"title": "Space Pals"}).json()["id"]
    episode = client.post(
        f"/api/series/{series_id}/episodes", json={"episode_number": 1, "title": "Pilot"}
    ).json()
    scene = client.post(f"/api/episodes/{episode['id']}/scenes", json={"scene_number": 1}).json()
    shot = client.post(
        f"/api/scenes/{scene['id']}/shots",
        json={"shot_number": 1, "dialogue": "No way, we made it!"},
    ).json()
    shot_id = shot["id"]
    voice_id = client.post(f"/api/series/{series_id}/voices", json={"name": "Voice"}).json()["id"]

    image = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={}).json()
    client.post(f"/api/generations/{image['id']}/approve")
    dialogue = client.post(
        f"/api/shots/{shot_id}/generate-voice", json={"track": "DIALOGUE", "voice_id": voice_id}
    ).json()
    client.post(f"/api/generations/{dialogue['id']}/approve")
    video = client.post(f"/api/shots/{shot_id}/generate-video", json={}).json()
    client.post(f"/api/generations/{video['id']}/activate")  # active, but not approved

    response = client.post(f"/api/shots/{shot_id}/generate-lipsync", json={"override_approval_gate": True})
    assert response.status_code == 201
    assert response.json()["status"] == "COMPLETE"


def test_generate_lipsync_on_missing_shot_404s(client):
    response = client.post("/api/shots/999999/generate-lipsync", json={})
    assert response.status_code == 404


class _FailingLipSyncProvider(LipSyncProvider):
    def sync_lips(self, video_bytes, video_file_extension, audio_bytes):
        raise RuntimeError("lip-sync model is down")


def test_generate_lipsync_records_failure_instead_of_raising(client):
    from app.main import app

    shot_id, _, _ = _create_shot_with_video_and_dialogue(client)
    app.dependency_overrides[get_lipsync_provider] = lambda: _FailingLipSyncProvider()
    try:
        response = client.post(f"/api/shots/{shot_id}/generate-lipsync", json={})
    finally:
        del app.dependency_overrides[get_lipsync_provider]

    assert response.status_code == 201
    generation = response.json()
    assert generation["status"] == "FAILED"
    assert generation["error_message"] == "lip-sync model is down"
    assert generation["output_path"] is None
