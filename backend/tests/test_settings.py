def test_upsert_project_setting_idempotent(client):
    response = client.put("/api/settings/project", json={"key": "thrifty_mode", "value": "true"})
    assert response.status_code == 200
    assert response.json()["value"] == "true"

    response = client.put("/api/settings/project", json={"key": "thrifty_mode", "value": "false"})
    assert response.status_code == 200
    assert response.json()["value"] == "false"

    response = client.get("/api/settings/project")
    assert len(response.json()) == 1


def test_provider_configuration_crud(client):
    response = client.post(
        "/api/settings/providers",
        json={"capability": "VIDEO", "provider_name": "wan_ti2v_5b", "is_default": True},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["capability"] == "VIDEO"

    response = client.patch(
        f"/api/settings/providers/{body['id']}", json={"provider_name": "mock_video"}
    )
    assert response.status_code == 200
    assert response.json()["provider_name"] == "mock_video"

    response = client.delete(f"/api/settings/providers/{body['id']}")
    assert response.status_code == 204


def test_invalid_capability_rejected(client):
    response = client.post(
        "/api/settings/providers",
        json={"capability": "NOT_A_CAPABILITY", "provider_name": "x"},
    )
    assert response.status_code == 422
