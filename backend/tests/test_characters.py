def _create_series(client) -> int:
    return client.post("/api/series", json={"title": "My Cartoon"}).json()["id"]


def test_create_character_generates_code(client):
    series_id = _create_series(client)

    response = client.post(
        f"/api/series/{series_id}/characters",
        json={"name": "Marcus", "description": "The hero", "hair": "Black, short"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["character_code"] == "CHAR_MARCUS_001"
    assert body["series_id"] == series_id


def test_duplicate_character_names_get_distinct_codes(client):
    series_id = _create_series(client)
    first = client.post(f"/api/series/{series_id}/characters", json={"name": "Marcus"}).json()
    second = client.post(f"/api/series/{series_id}/characters", json={"name": "Marcus"}).json()
    assert first["character_code"] == "CHAR_MARCUS_001"
    assert second["character_code"] == "CHAR_MARCUS_002"


def test_list_characters_requires_valid_series(client):
    response = client.get("/api/series/999/characters")
    assert response.status_code == 404


def test_create_character_requires_valid_series(client):
    response = client.post("/api/series/999/characters", json={"name": "Marcus"})
    assert response.status_code == 404


def test_update_and_delete_character(client):
    series_id = _create_series(client)
    character = client.post(f"/api/series/{series_id}/characters", json={"name": "Marcus"}).json()

    response = client.patch(f"/api/characters/{character['id']}", json={"hair": "Bald"})
    assert response.status_code == 200
    assert response.json()["hair"] == "Bald"

    response = client.delete(f"/api/characters/{character['id']}")
    assert response.status_code == 204
    assert client.get(f"/api/characters/{character['id']}").status_code == 404


def test_deleting_series_cascades_to_characters(client):
    series_id = _create_series(client)
    character = client.post(f"/api/series/{series_id}/characters", json={"name": "Marcus"}).json()

    client.delete(f"/api/series/{series_id}")
    assert client.get(f"/api/characters/{character['id']}").status_code == 404
