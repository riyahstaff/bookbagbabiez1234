def _create_shot(client) -> int:
    series_id = client.post("/api/series", json={"title": "Space Pals"}).json()["id"]
    episode = client.post(
        f"/api/series/{series_id}/episodes", json={"episode_number": 1, "title": "Pilot"}
    ).json()
    scene = client.post(f"/api/episodes/{episode['id']}/scenes", json={"scene_number": 1}).json()
    shot = client.post(
        f"/api/scenes/{scene['id']}/shots",
        json={"shot_number": 1, "shot_type": "MEDIUM", "dialogue": "No way, we made it!"},
    ).json()
    return shot["id"], series_id


def test_generate_storyboard_populates_quality_score_and_notes(client):
    shot_id, _ = _create_shot(client)
    generation = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={}).json()

    assert generation["quality_score"] == 1.0
    assert "passed" in generation["qc_notes"].lower()


def test_generate_voice_populates_quality_score_and_notes(client):
    shot_id, series_id = _create_shot(client)
    voice_id = client.post(f"/api/series/{series_id}/voices", json={"name": "Marcus Voice"}).json()["id"]

    generation = client.post(
        f"/api/shots/{shot_id}/generate-voice", json={"track": "DIALOGUE", "voice_id": voice_id}
    ).json()

    assert generation["quality_score"] == 1.0
    assert "passed" in generation["qc_notes"].lower()


def test_generate_voice_cache_hit_copies_qc_instead_of_recomputing(client):
    shot_id, series_id = _create_shot(client)
    voice_id = client.post(f"/api/series/{series_id}/voices", json={"name": "Marcus Voice"}).json()["id"]

    first = client.post(
        f"/api/shots/{shot_id}/generate-voice", json={"track": "DIALOGUE", "voice_id": voice_id}
    ).json()
    second = client.post(
        f"/api/shots/{shot_id}/generate-voice", json={"track": "DIALOGUE", "voice_id": voice_id}
    ).json()

    assert first["output_path"] == second["output_path"]  # confirms this hit the cache path
    assert second["quality_score"] == first["quality_score"]
    assert second["qc_notes"] == first["qc_notes"]


def test_generate_video_populates_quality_score_and_notes(client):
    shot_id, _ = _create_shot(client)
    image = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={}).json()
    client.post(f"/api/generations/{image['id']}/approve")

    generation = client.post(f"/api/shots/{shot_id}/generate-video", json={}).json()

    assert generation["quality_score"] == 1.0
    assert "passed" in generation["qc_notes"].lower()


def test_qc_exception_does_not_fail_the_generation(client, monkeypatch):
    import app.api.routers.generations as generations_router

    def _broken_check_image(image_bytes):
        raise RuntimeError("QC blew up")

    monkeypatch.setattr(generations_router, "check_image", _broken_check_image)

    shot_id, _ = _create_shot(client)
    response = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={})
    assert response.status_code == 201
    generation = response.json()

    assert generation["status"] == "COMPLETE"  # QC failure must not fail the generation itself
    assert generation["quality_score"] is None
    assert "QC blew up" in generation["qc_notes"]
