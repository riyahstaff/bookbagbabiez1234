def _create_scene_with_character(client) -> tuple[int, int, int]:
    series_id = client.post("/api/series", json={"title": "Space Pals"}).json()["id"]
    marcus = client.post(f"/api/series/{series_id}/characters", json={"name": "Marcus"}).json()
    episode = client.post(
        f"/api/series/{series_id}/episodes", json={"episode_number": 1, "title": "Pilot"}
    ).json()
    scene = client.post(f"/api/episodes/{episode['id']}/scenes", json={"scene_number": 1}).json()
    client.put(f"/api/scenes/{scene['id']}/characters", json={"characters": [{"character_id": marcus["id"]}]})
    return series_id, scene["id"], marcus["id"]


def test_generate_shots_resolves_known_characters(client):
    _, scene_id, marcus_id = _create_scene_with_character(client)

    response = client.post(f"/api/scenes/{scene_id}/generate-shots")
    assert response.status_code == 201
    shots = response.json()
    assert len(shots) == 2
    assert shots[0]["shot_type"] == "ESTABLISHING"

    shot_with_character = next(s for s in shots if s["characters"])
    assert shot_with_character["characters"][0]["character_id"] == marcus_id

    scene = client.get(f"/api/scenes/{scene_id}").json()
    assert scene["status"] == "SHOTS_READY"


def test_generate_shots_is_blocked_once_shots_exist(client):
    _, scene_id, _ = _create_scene_with_character(client)
    client.post(f"/api/scenes/{scene_id}/generate-shots")

    response = client.post(f"/api/scenes/{scene_id}/generate-shots")
    assert response.status_code == 409


def test_manual_shot_crud_and_prompts(client):
    _, scene_id, _ = _create_scene_with_character(client)

    created = client.post(
        f"/api/scenes/{scene_id}/shots",
        json={"shot_number": 1, "shot_type": "CLOSE_UP", "visual_prompt": "Marcus, worried expression"},
    )
    assert created.status_code == 201
    shot = created.json()
    assert shot["shot_type"] == "CLOSE_UP"

    duplicate = client.post(f"/api/scenes/{scene_id}/shots", json={"shot_number": 1})
    assert duplicate.status_code == 409

    updated = client.patch(f"/api/shots/{shot['id']}", json={"negative_prompt": "no extra limbs"})
    assert updated.status_code == 200
    assert updated.json()["negative_prompt"] == "no extra limbs"

    deleted = client.delete(f"/api/shots/{shot['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/api/scenes/{scene_id}/shots").json() == []


def test_invalid_shot_type_rejected(client):
    _, scene_id, _ = _create_scene_with_character(client)
    response = client.post(f"/api/scenes/{scene_id}/shots", json={"shot_number": 1, "shot_type": "NOT_REAL"})
    assert response.status_code == 422
