def _create_series_and_character(client) -> tuple[int, int]:
    series_id = client.post("/api/series", json={"title": "My Cartoon"}).json()["id"]
    character = client.post(f"/api/series/{series_id}/characters", json={"name": "Marcus"}).json()
    return series_id, character["id"]


def test_create_standalone_narrator_voice(client):
    series_id = client.post("/api/series", json={"title": "My Cartoon"}).json()["id"]
    response = client.post(f"/api/series/{series_id}/voices", json={"name": "Narrator"})
    assert response.status_code == 201
    body = response.json()
    assert body["voice_code"] == "VOICE_NARRATOR_001"
    assert body["character_id"] is None


def test_create_voice_linked_to_character(client):
    series_id, character_id = _create_series_and_character(client)
    response = client.post(
        f"/api/series/{series_id}/voices",
        json={"name": "Marcus Main", "character_id": character_id, "provider": "chatterbox"},
    )
    assert response.status_code == 201
    assert response.json()["character_id"] == character_id


def test_voice_rejects_character_from_another_series(client):
    series_id, _ = _create_series_and_character(client)
    other_series_id = client.post("/api/series", json={"title": "Other Show"}).json()["id"]
    other_character = client.post(
        f"/api/series/{other_series_id}/characters", json={"name": "Zara"}
    ).json()

    response = client.post(
        f"/api/series/{series_id}/voices",
        json={"name": "Bad Link", "character_id": other_character["id"]},
    )
    assert response.status_code == 400


def test_upload_and_replace_reference_audio(client, test_storage):
    series_id = client.post("/api/series", json={"title": "My Cartoon"}).json()["id"]
    voice = client.post(f"/api/series/{series_id}/voices", json={"name": "Narrator"}).json()

    first = client.post(
        f"/api/voices/{voice['id']}/reference-audio",
        files={"file": ("ref1.wav", b"fake-wav-bytes", "audio/wav")},
    )
    assert first.status_code == 200
    first_path = first.json()["reference_audio_path"]
    assert test_storage.exists(first_path)

    second = client.post(
        f"/api/voices/{voice['id']}/reference-audio",
        files={"file": ("ref2.wav", b"more-fake-wav-bytes", "audio/wav")},
    )
    assert second.status_code == 200
    second_path = second.json()["reference_audio_path"]
    assert second_path != first_path
    assert test_storage.exists(second_path)
    assert not test_storage.exists(first_path)


def test_rejects_non_audio_reference(client):
    series_id = client.post("/api/series", json={"title": "My Cartoon"}).json()["id"]
    voice = client.post(f"/api/series/{series_id}/voices", json={"name": "Narrator"}).json()
    response = client.post(
        f"/api/voices/{voice['id']}/reference-audio",
        files={"file": ("notes.txt", b"not audio", "text/plain")},
    )
    assert response.status_code == 400


def test_delete_voice_removes_reference_audio(client, test_storage):
    series_id = client.post("/api/series", json={"title": "My Cartoon"}).json()["id"]
    voice = client.post(f"/api/series/{series_id}/voices", json={"name": "Narrator"}).json()
    uploaded = client.post(
        f"/api/voices/{voice['id']}/reference-audio",
        files={"file": ("ref.wav", b"fake-wav-bytes", "audio/wav")},
    ).json()

    client.delete(f"/api/voices/{voice['id']}")
    assert not test_storage.exists(uploaded["reference_audio_path"])
