def _create_series(client) -> int:
    return client.post("/api/series", json={"title": "My Cartoon"}).json()["id"]


def test_create_episode_generates_code_and_defaults_status(client):
    series_id = _create_series(client)

    response = client.post(
        f"/api/series/{series_id}/episodes",
        json={"episode_number": 1, "title": "Pilot"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["episode_code"] == "EP_001"
    assert body["status"] == "DRAFT"


def test_duplicate_episode_number_conflicts(client):
    series_id = _create_series(client)
    client.post(f"/api/series/{series_id}/episodes", json={"episode_number": 1, "title": "Pilot"})
    response = client.post(
        f"/api/series/{series_id}/episodes", json={"episode_number": 1, "title": "Pilot Redo"}
    )
    assert response.status_code == 409


def test_two_series_can_each_have_episode_one(client):
    series_a = _create_series(client)
    series_b = _create_series(client)
    a = client.post(f"/api/series/{series_a}/episodes", json={"episode_number": 1, "title": "A1"}).json()
    b = client.post(f"/api/series/{series_b}/episodes", json={"episode_number": 1, "title": "B1"}).json()
    assert a["episode_code"] == "EP_001"
    assert b["episode_code"] == "EP_001"
    assert a["series_id"] != b["series_id"]


def test_update_episode_status(client):
    series_id = _create_series(client)
    episode = client.post(
        f"/api/series/{series_id}/episodes", json={"episode_number": 1, "title": "Pilot"}
    ).json()

    response = client.patch(f"/api/episodes/{episode['id']}", json={"status": "SCRIPT_READY"})
    assert response.status_code == 200
    assert response.json()["status"] == "SCRIPT_READY"


def test_invalid_status_rejected(client):
    series_id = _create_series(client)
    episode = client.post(
        f"/api/series/{series_id}/episodes", json={"episode_number": 1, "title": "Pilot"}
    ).json()

    response = client.patch(f"/api/episodes/{episode['id']}", json={"status": "NOT_REAL"})
    assert response.status_code == 422
