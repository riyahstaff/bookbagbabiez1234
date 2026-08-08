def _create_episode_with_bible(client) -> tuple[int, int]:
    series_id = client.post("/api/series", json={"title": "Space Pals"}).json()["id"]
    client.post(f"/api/series/{series_id}/characters", json={"name": "Marcus"})
    client.post(f"/api/series/{series_id}/characters", json={"name": "Zara"})
    client.post(f"/api/series/{series_id}/locations", json={"name": "Diner"})
    episode = client.post(
        f"/api/series/{series_id}/episodes",
        json={"episode_number": 1, "title": "Pilot", "script": "placeholder script"},
    ).json()
    return series_id, episode["id"]


def test_generate_scenes_resolves_known_characters_and_locations(client):
    _, episode_id = _create_episode_with_bible(client)

    response = client.post(f"/api/episodes/{episode_id}/generate-scenes")
    assert response.status_code == 201
    scenes = response.json()
    assert len(scenes) == 2
    assert scenes[0]["location_id"] is not None

    location_response = client.get(f"/api/locations/{scenes[0]['location_id']}")
    assert location_response.json()["name"] == "Diner"

    character_ids = {c["character_id"] for c in scenes[0]["characters"]}
    assert len(character_ids) >= 1

    episode = client.get(f"/api/episodes/{episode_id}").json()
    assert episode["status"] == "SCENES_READY"


def test_generate_scenes_is_blocked_once_scenes_exist(client):
    _, episode_id = _create_episode_with_bible(client)
    client.post(f"/api/episodes/{episode_id}/generate-scenes")

    response = client.post(f"/api/episodes/{episode_id}/generate-scenes")
    assert response.status_code == 409


def test_manual_scene_crud(client):
    _, episode_id = _create_episode_with_bible(client)

    created = client.post(
        f"/api/episodes/{episode_id}/scenes",
        json={"scene_number": 1, "action_description": "Manual scene, no AI involved."},
    )
    assert created.status_code == 201
    scene = created.json()

    duplicate = client.post(
        f"/api/episodes/{episode_id}/scenes", json={"scene_number": 1, "action_description": "dup"}
    )
    assert duplicate.status_code == 409

    updated = client.patch(f"/api/scenes/{scene['id']}", json={"emotional_tone": "hopeful"})
    assert updated.status_code == 200
    assert updated.json()["emotional_tone"] == "hopeful"

    deleted = client.delete(f"/api/scenes/{scene['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/api/episodes/{episode_id}/scenes").json() == []


def test_set_scene_characters_validates_series_membership(client):
    series_id, episode_id = _create_episode_with_bible(client)
    scene = client.post(f"/api/episodes/{episode_id}/scenes", json={"scene_number": 1}).json()
    marcus = client.get(f"/api/series/{series_id}/characters").json()[0]

    other_series_id = client.post("/api/series", json={"title": "Other Show"}).json()["id"]
    outsider = client.post(f"/api/series/{other_series_id}/characters", json={"name": "Outsider"}).json()

    bad = client.put(
        f"/api/scenes/{scene['id']}/characters", json={"characters": [{"character_id": outsider["id"]}]}
    )
    assert bad.status_code == 400

    good = client.put(
        f"/api/scenes/{scene['id']}/characters", json={"characters": [{"character_id": marcus["id"]}]}
    )
    assert good.status_code == 200
    assert [c["character_id"] for c in good.json()["characters"]] == [marcus["id"]]
