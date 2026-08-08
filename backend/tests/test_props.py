def _create_series(client) -> int:
    return client.post("/api/series", json={"title": "My Cartoon"}).json()["id"]


def test_create_prop_uses_bare_descriptive_code(client):
    series_id = _create_series(client)
    response = client.post(f"/api/series/{series_id}/props", json={"name": "Magic Book"})
    assert response.status_code == 201
    assert response.json()["prop_code"] == "PROP_MAGIC_BOOK"


def test_duplicate_prop_name_falls_back_to_numbered_suffix(client):
    series_id = _create_series(client)
    first = client.post(f"/api/series/{series_id}/props", json={"name": "Magic Book"}).json()
    second = client.post(f"/api/series/{series_id}/props", json={"name": "Magic Book"}).json()
    assert first["prop_code"] == "PROP_MAGIC_BOOK"
    assert second["prop_code"] == "PROP_MAGIC_BOOK_2"


def test_update_and_delete_prop(client):
    series_id = _create_series(client)
    prop = client.post(f"/api/series/{series_id}/props", json={"name": "Police Badge"}).json()

    response = client.patch(f"/api/props/{prop['id']}", json={"description": "Standard issue, silver"})
    assert response.status_code == 200
    assert response.json()["description"] == "Standard issue, silver"

    response = client.delete(f"/api/props/{prop['id']}")
    assert response.status_code == 204
    assert client.get(f"/api/series/{series_id}/props").json() == []


def test_prop_reference_upload_list_delete(client, test_storage):
    series_id = _create_series(client)
    prop = client.post(f"/api/series/{series_id}/props", json={"name": "Red Phone"}).json()

    upload = client.post(
        f"/api/props/{prop['id']}/references",
        data={"label": "on the wall"},
        files={"file": ("phone.png", b"fake-png-bytes", "image/png")},
    )
    assert upload.status_code == 201
    reference = upload.json()
    assert test_storage.exists(reference["image_path"])

    listed = client.get(f"/api/props/{prop['id']}/references").json()
    assert len(listed) == 1

    response = client.delete(f"/api/prop-references/{reference['id']}")
    assert response.status_code == 204
    assert not test_storage.exists(reference["image_path"])
