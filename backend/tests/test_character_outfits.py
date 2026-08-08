def _create_character(client) -> tuple[int, int]:
    series_id = client.post("/api/series", json={"title": "My Cartoon"}).json()["id"]
    character = client.post(f"/api/series/{series_id}/characters", json={"name": "Marcus"}).json()
    return series_id, character["id"]


def test_create_outfit_uses_bare_descriptive_code(client):
    _, character_id = _create_character(client)
    outfit = client.post(f"/api/characters/{character_id}/outfits", json={"name": "Casual"}).json()
    assert outfit["outfit_code"] == "OUTFIT_MARCUS_CASUAL"


def test_duplicate_outfit_name_falls_back_to_numbered_suffix(client):
    _, character_id = _create_character(client)
    first = client.post(f"/api/characters/{character_id}/outfits", json={"name": "Casual"}).json()
    second = client.post(f"/api/characters/{character_id}/outfits", json={"name": "Casual"}).json()
    assert first["outfit_code"] == "OUTFIT_MARCUS_CASUAL"
    assert second["outfit_code"] == "OUTFIT_MARCUS_CASUAL_2"


def test_create_outfit_requires_valid_character(client):
    response = client.post("/api/characters/999/outfits", json={"name": "Casual"})
    assert response.status_code == 404


def test_update_and_delete_outfit(client):
    _, character_id = _create_character(client)
    outfit = client.post(f"/api/characters/{character_id}/outfits", json={"name": "Work"}).json()

    response = client.patch(f"/api/character-outfits/{outfit['id']}", json={"description": "Diner uniform"})
    assert response.status_code == 200
    assert response.json()["description"] == "Diner uniform"

    response = client.delete(f"/api/character-outfits/{outfit['id']}")
    assert response.status_code == 204
    assert client.get(f"/api/characters/{character_id}/outfits").json() == []


def test_outfit_reference_upload_list_delete(client, test_storage):
    _, character_id = _create_character(client)
    outfit = client.post(f"/api/characters/{character_id}/outfits", json={"name": "Formal"}).json()

    upload = client.post(
        f"/api/character-outfits/{outfit['id']}/references",
        data={"label": "front"},
        files={"file": ("formal.png", b"fake-png-bytes", "image/png")},
    )
    assert upload.status_code == 201
    reference = upload.json()
    assert test_storage.exists(reference["image_path"])

    listed = client.get(f"/api/character-outfits/{outfit['id']}/references").json()
    assert len(listed) == 1

    response = client.delete(f"/api/outfit-references/{reference['id']}")
    assert response.status_code == 204
    assert not test_storage.exists(reference["image_path"])


def test_deleting_outfit_cleans_up_its_reference_files(client, test_storage):
    _, character_id = _create_character(client)
    outfit = client.post(f"/api/characters/{character_id}/outfits", json={"name": "Winter"}).json()
    reference = client.post(
        f"/api/character-outfits/{outfit['id']}/references",
        files={"file": ("winter.png", b"fake-png-bytes", "image/png")},
    ).json()
    assert test_storage.exists(reference["image_path"])

    client.delete(f"/api/character-outfits/{outfit['id']}")
    assert not test_storage.exists(reference["image_path"])
