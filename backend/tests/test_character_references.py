def _create_character(client) -> tuple[int, int]:
    series_id = client.post("/api/series", json={"title": "My Cartoon"}).json()["id"]
    character = client.post(f"/api/series/{series_id}/characters", json={"name": "Marcus"}).json()
    return series_id, character["id"]


def test_upload_and_list_reference(client, test_storage):
    _, character_id = _create_character(client)

    response = client.post(
        f"/api/characters/{character_id}/references",
        data={"category": "FRONT", "notes": "clean front view"},
        files={"file": ("front.png", b"fake-png-bytes", "image/png")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["category"] == "FRONT"
    assert body["notes"] == "clean front view"
    assert test_storage.exists(body["image_path"])

    response = client.get(f"/api/characters/{character_id}/references")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_rejects_non_image_upload(client):
    _, character_id = _create_character(client)
    response = client.post(
        f"/api/characters/{character_id}/references",
        data={"category": "FRONT"},
        files={"file": ("notes.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 400


def test_upload_requires_valid_character(client):
    response = client.post(
        "/api/characters/999/references",
        data={"category": "FRONT"},
        files={"file": ("front.png", b"fake-png-bytes", "image/png")},
    )
    assert response.status_code == 404


def test_delete_reference_removes_file(client, test_storage):
    _, character_id = _create_character(client)
    reference = client.post(
        f"/api/characters/{character_id}/references",
        data={"category": "CLOSE_UP"},
        files={"file": ("close.png", b"fake-png-bytes", "image/png")},
    ).json()
    assert test_storage.exists(reference["image_path"])

    response = client.delete(f"/api/character-references/{reference['id']}")
    assert response.status_code == 204
    assert not test_storage.exists(reference["image_path"])
    assert client.get(f"/api/characters/{character_id}/references").json() == []
