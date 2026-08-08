def test_create_and_list_series(client):
    response = client.post(
        "/api/series",
        json={"title": "My Cartoon", "genre": "Comedy", "aspect_ratio": "16:9"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "My Cartoon"
    assert body["series_code"] == "SERIES_001"

    response = client.get("/api/series")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_update_delete_series(client):
    created = client.post("/api/series", json={"title": "Space Pals"}).json()
    series_id = created["id"]

    response = client.get(f"/api/series/{series_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Space Pals"

    response = client.patch(f"/api/series/{series_id}", json={"genre": "Sci-Fi"})
    assert response.status_code == 200
    assert response.json()["genre"] == "Sci-Fi"

    response = client.delete(f"/api/series/{series_id}")
    assert response.status_code == 204

    response = client.get(f"/api/series/{series_id}")
    assert response.status_code == 404


def test_get_missing_series_404(client):
    response = client.get("/api/series/999")
    assert response.status_code == 404


def test_series_codes_increment(client):
    first = client.post("/api/series", json={"title": "Show A"}).json()
    second = client.post("/api/series", json={"title": "Show B"}).json()
    assert first["series_code"] == "SERIES_001"
    assert second["series_code"] == "SERIES_002"
