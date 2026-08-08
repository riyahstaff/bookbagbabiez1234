def _create_series(client) -> int:
    return client.post("/api/series", json={"title": "My Cartoon"}).json()["id"]


def test_create_location_generates_numbered_code(client):
    series_id = _create_series(client)
    response = client.post(f"/api/series/{series_id}/locations", json={"name": "Diner"})
    assert response.status_code == 201
    assert response.json()["location_code"] == "LOCATION_DINER_001"


def test_update_and_delete_location(client):
    series_id = _create_series(client)
    location = client.post(f"/api/series/{series_id}/locations", json={"name": "Diner"}).json()

    response = client.patch(f"/api/locations/{location['id']}", json={"lighting_notes": "warm, neon signage"})
    assert response.status_code == 200
    assert response.json()["lighting_notes"] == "warm, neon signage"

    response = client.delete(f"/api/locations/{location['id']}")
    assert response.status_code == 204
    assert client.get(f"/api/series/{series_id}/locations").json() == []


def test_location_reference_upload_list_delete(client, test_storage):
    series_id = _create_series(client)
    location = client.post(f"/api/series/{series_id}/locations", json={"name": "Diner"}).json()

    upload = client.post(
        f"/api/locations/{location['id']}/references",
        data={"category": "WIDE_ESTABLISHING"},
        files={"file": ("diner-wide.png", b"fake-png-bytes", "image/png")},
    )
    assert upload.status_code == 201
    reference = upload.json()
    assert reference["category"] == "WIDE_ESTABLISHING"
    assert test_storage.exists(reference["image_path"])

    listed = client.get(f"/api/locations/{location['id']}/references").json()
    assert len(listed) == 1

    response = client.delete(f"/api/location-references/{reference['id']}")
    assert response.status_code == 204
    assert not test_storage.exists(reference["image_path"])


def test_location_requires_valid_category(client):
    series_id = _create_series(client)
    location = client.post(f"/api/series/{series_id}/locations", json={"name": "Diner"}).json()
    response = client.post(
        f"/api/locations/{location['id']}/references",
        data={"category": "NOT_A_REAL_CATEGORY"},
        files={"file": ("x.png", b"fake-png-bytes", "image/png")},
    )
    assert response.status_code == 422
