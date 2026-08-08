def _create_episode(client) -> tuple[int, int]:
    series_id = client.post("/api/series", json={"title": "Space Pals"}).json()["id"]
    episode = client.post(
        f"/api/series/{series_id}/episodes",
        json={"episode_number": 1, "title": "Pilot", "treatment": "Marcus and Zara crash-land."},
    ).json()
    return series_id, episode["id"]


def test_generate_outline_writes_outline_field(client):
    _, episode_id = _create_episode(client)
    response = client.post(f"/api/episodes/{episode_id}/generate-outline")
    assert response.status_code == 200
    body = response.json()
    assert body["outline"]
    assert "MOCK OUTLINE" in body["outline"]
    # Generating an outline shouldn't jump the episode straight to SCRIPT_READY.
    assert body["status"] == "DRAFT"


def test_generate_script_writes_script_and_advances_status(client):
    _, episode_id = _create_episode(client)
    client.post(f"/api/episodes/{episode_id}/generate-outline")
    response = client.post(f"/api/episodes/{episode_id}/generate-script")
    assert response.status_code == 200
    body = response.json()
    assert "MOCK SCRIPT" in body["script"]
    assert body["status"] == "SCRIPT_READY"


def test_generate_outline_requires_valid_episode(client):
    response = client.post("/api/episodes/999/generate-outline")
    assert response.status_code == 404
