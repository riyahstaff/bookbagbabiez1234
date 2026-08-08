from app.assembler.timeline import build_timeline
from app.models import Episode


def _setup_episode(client) -> tuple[int, int, int]:
    series_id = client.post("/api/series", json={"title": "Space Pals"}).json()["id"]
    episode = client.post(
        f"/api/series/{series_id}/episodes", json={"episode_number": 1, "title": "Pilot"}
    ).json()
    scene1 = client.post(f"/api/episodes/{episode['id']}/scenes", json={"scene_number": 1}).json()
    scene2 = client.post(f"/api/episodes/{episode['id']}/scenes", json={"scene_number": 2}).json()
    return episode["id"], scene1["id"], scene2["id"]


def _add_shot(client, scene_id, shot_number, **fields):
    return client.post(
        f"/api/scenes/{scene_id}/shots", json={"shot_number": shot_number, **fields}
    ).json()


def test_build_timeline_resolves_video_over_image_and_orders_by_scene_and_shot(client, db_session):
    episode_id, scene1_id, scene2_id = _setup_episode(client)

    # Scene 1, Shot 2 (out of number order on purpose) gets a video.
    shot_with_video = _add_shot(client, scene1_id, 2)
    video_gen = client.post(f"/api/shots/{shot_with_video['id']}/generate-storyboard", json={}).json()
    client.post(f"/api/generations/{video_gen['id']}/approve")
    video = client.post(f"/api/shots/{shot_with_video['id']}/generate-video", json={}).json()
    client.post(f"/api/generations/{video['id']}/activate")

    # Scene 1, Shot 1 only ever gets an image - no video.
    shot_with_image_only = _add_shot(client, scene1_id, 1, duration_seconds=5)
    image_gen = client.post(f"/api/shots/{shot_with_image_only['id']}/generate-storyboard", json={}).json()
    client.post(f"/api/generations/{image_gen['id']}/approve")

    # Scene 2, Shot 1 has nothing at all - must be skipped.
    _add_shot(client, scene2_id, 1)

    episode = db_session.get(Episode, episode_id)
    timeline = build_timeline(episode)

    assert timeline.skipped_shots == ["Scene 2 Shot 1"]
    assert len(timeline.segments) == 2
    # Scene 1 Shot 1 (image-only) must come before Scene 1 Shot 2 (video), by
    # shot_number order, regardless of creation order.
    first, second = timeline.segments
    assert first.shot_id == shot_with_image_only["id"]
    assert first.is_static_image is True
    assert first.hold_duration_seconds == 5.0
    assert second.shot_id == shot_with_video["id"]
    assert second.is_static_image is False
    assert second.hold_duration_seconds is None


def test_build_timeline_includes_active_dialogue_and_narration(client, db_session):
    episode_id, scene1_id, _ = _setup_episode(client)
    series_id = client.get(f"/api/episodes/{episode_id}").json()["series_id"]
    voice_id = client.post(f"/api/series/{series_id}/voices", json={"name": "Narrator"}).json()["id"]

    shot = _add_shot(
        client, scene1_id, 1, dialogue="No way, we made it!", narration="Meanwhile, across town..."
    )
    image_gen = client.post(f"/api/shots/{shot['id']}/generate-storyboard", json={}).json()
    client.post(f"/api/generations/{image_gen['id']}/approve")
    dialogue_gen = client.post(
        f"/api/shots/{shot['id']}/generate-voice", json={"track": "DIALOGUE", "voice_id": voice_id}
    ).json()
    client.post(f"/api/generations/{dialogue_gen['id']}/approve")
    narration_gen = client.post(
        f"/api/shots/{shot['id']}/generate-voice", json={"track": "NARRATION", "voice_id": voice_id}
    ).json()
    client.post(f"/api/generations/{narration_gen['id']}/activate")

    episode = db_session.get(Episode, episode_id)
    timeline = build_timeline(episode)

    assert len(timeline.segments) == 1
    segment = timeline.segments[0]
    assert segment.dialogue_text == "No way, we made it!"
    assert segment.dialogue_path == dialogue_gen["output_path"]
    assert segment.narration_text == "Meanwhile, across town..."
    assert segment.narration_path == narration_gen["output_path"]


def test_build_timeline_with_no_shots_at_all_is_empty(client, db_session):
    episode_id, _, _ = _setup_episode(client)
    episode = db_session.get(Episode, episode_id)
    timeline = build_timeline(episode)
    assert timeline.segments == []
    assert timeline.skipped_shots == []
