from app.providers.voice import get_voice_provider
from app.providers.voice.base import AudioGenerationResult, VoiceProvider


class _CountingVoiceProvider(VoiceProvider):
    def __init__(self):
        self.calls = 0

    def generate_speech(self, text, voice_identifier, speed=None, extra_settings=None):
        self.calls += 1
        return AudioGenerationResult(
            audio_bytes=f"fake-audio-{self.calls}".encode(), model_name="counting-mock"
        )


def _create_series_with_shot(client) -> tuple[int, int, int]:
    series_id = client.post("/api/series", json={"title": "Space Pals"}).json()["id"]
    marcus = client.post(f"/api/series/{series_id}/characters", json={"name": "Marcus"}).json()
    episode = client.post(
        f"/api/series/{series_id}/episodes", json={"episode_number": 1, "title": "Pilot"}
    ).json()
    scene = client.post(f"/api/episodes/{episode['id']}/scenes", json={"scene_number": 1}).json()
    shot = client.post(
        f"/api/scenes/{scene['id']}/shots",
        json={
            "shot_number": 1,
            "shot_type": "MEDIUM",
            "dialogue": "No way, we made it!",
            "narration": "Meanwhile, across town...",
        },
    ).json()
    client.put(
        f"/api/shots/{shot['id']}/characters", json={"characters": [{"character_id": marcus["id"]}]}
    )
    marcus_voice = client.post(
        f"/api/series/{series_id}/voices", json={"name": "Marcus Voice", "character_id": marcus["id"]}
    ).json()
    narrator_voice = client.post(
        f"/api/series/{series_id}/voices", json={"name": "Narrator", "character_id": None}
    ).json()
    return shot["id"], marcus_voice["id"], narrator_voice["id"]


def test_generate_voice_dialogue_happy_path(client):
    shot_id, marcus_voice_id, _ = _create_series_with_shot(client)

    response = client.post(
        f"/api/shots/{shot_id}/generate-voice", json={"track": "DIALOGUE", "voice_id": marcus_voice_id}
    )
    assert response.status_code == 201
    generation = response.json()

    assert generation["status"] == "COMPLETE"
    assert generation["generation_type"] == "VOICE"
    assert generation["audio_track"] == "DIALOGUE"
    assert generation["voice_id"] == marcus_voice_id
    assert generation["prompt"] == "No way, we made it!"
    assert generation["output_path"]


def test_generate_voice_narration_happy_path(client, test_storage):
    shot_id, _, narrator_voice_id = _create_series_with_shot(client)

    generation = client.post(
        f"/api/shots/{shot_id}/generate-voice", json={"track": "NARRATION", "voice_id": narrator_voice_id}
    ).json()

    assert generation["audio_track"] == "NARRATION"
    assert generation["prompt"] == "Meanwhile, across town..."
    assert test_storage.exists(generation["output_path"])


def test_generate_voice_rejects_voice_from_another_series(client):
    shot_id, _, _ = _create_series_with_shot(client)
    other_series_id = client.post("/api/series", json={"title": "Other Show"}).json()["id"]
    other_voice_id = client.post(
        f"/api/series/{other_series_id}/voices", json={"name": "Intruder"}
    ).json()["id"]

    response = client.post(
        f"/api/shots/{shot_id}/generate-voice", json={"track": "DIALOGUE", "voice_id": other_voice_id}
    )
    assert response.status_code == 400


def test_generate_voice_rejects_missing_voice(client):
    shot_id, _, _ = _create_series_with_shot(client)
    response = client.post(
        f"/api/shots/{shot_id}/generate-voice", json={"track": "DIALOGUE", "voice_id": 999999}
    )
    assert response.status_code == 400


def test_generate_voice_rejects_empty_track_text(client):
    shot_id, marcus_voice_id, _ = _create_series_with_shot(client)
    client.patch(f"/api/shots/{shot_id}", json={"dialogue": None})

    response = client.post(
        f"/api/shots/{shot_id}/generate-voice", json={"track": "DIALOGUE", "voice_id": marcus_voice_id}
    )
    assert response.status_code == 400


def test_generate_voice_on_missing_shot_404s(client):
    response = client.post(
        "/api/shots/999999/generate-voice", json={"track": "DIALOGUE", "voice_id": 1}
    )
    assert response.status_code == 404


def test_generate_voice_cache_hit_skips_provider_call(client):
    from app.main import app

    shot_id, marcus_voice_id, _ = _create_series_with_shot(client)
    stub = _CountingVoiceProvider()
    app.dependency_overrides[get_voice_provider] = lambda: stub
    try:
        first = client.post(
            f"/api/shots/{shot_id}/generate-voice", json={"track": "DIALOGUE", "voice_id": marcus_voice_id}
        ).json()
        second = client.post(
            f"/api/shots/{shot_id}/generate-voice", json={"track": "DIALOGUE", "voice_id": marcus_voice_id}
        ).json()
    finally:
        del app.dependency_overrides[get_voice_provider]

    assert stub.calls == 1
    assert first["output_path"] == second["output_path"]
    assert first["id"] != second["id"]


def test_generate_voice_force_regenerate_bypasses_cache(client):
    from app.main import app

    shot_id, marcus_voice_id, _ = _create_series_with_shot(client)
    stub = _CountingVoiceProvider()
    app.dependency_overrides[get_voice_provider] = lambda: stub
    try:
        first = client.post(
            f"/api/shots/{shot_id}/generate-voice", json={"track": "DIALOGUE", "voice_id": marcus_voice_id}
        ).json()
        second = client.post(
            f"/api/shots/{shot_id}/generate-voice",
            json={"track": "DIALOGUE", "voice_id": marcus_voice_id, "force_regenerate": True},
        ).json()
    finally:
        del app.dependency_overrides[get_voice_provider]

    assert stub.calls == 2
    assert first["output_path"] != second["output_path"]


def test_generate_voice_cache_hit_across_different_shots(client):
    from app.main import app

    shot_id, marcus_voice_id, _ = _create_series_with_shot(client)
    scene_id = client.get(f"/api/shots/{shot_id}").json()["scene_id"]
    other_shot = client.post(
        f"/api/scenes/{scene_id}/shots",
        json={"shot_number": 2, "shot_type": "MEDIUM", "dialogue": "No way, we made it!"},
    ).json()

    stub = _CountingVoiceProvider()
    app.dependency_overrides[get_voice_provider] = lambda: stub
    try:
        first = client.post(
            f"/api/shots/{shot_id}/generate-voice", json={"track": "DIALOGUE", "voice_id": marcus_voice_id}
        ).json()
        second = client.post(
            f"/api/shots/{other_shot['id']}/generate-voice",
            json={"track": "DIALOGUE", "voice_id": marcus_voice_id},
        ).json()
    finally:
        del app.dependency_overrides[get_voice_provider]

    assert stub.calls == 1
    assert first["output_path"] == second["output_path"]
    assert first["shot_id"] != second["shot_id"]


def test_changing_voice_settings_invalidates_cache(client):
    from app.main import app

    shot_id, marcus_voice_id, _ = _create_series_with_shot(client)
    stub = _CountingVoiceProvider()
    app.dependency_overrides[get_voice_provider] = lambda: stub
    try:
        first = client.post(
            f"/api/shots/{shot_id}/generate-voice", json={"track": "DIALOGUE", "voice_id": marcus_voice_id}
        ).json()
        client.patch(f"/api/voices/{marcus_voice_id}", json={"speed": 1.5})
        second = client.post(
            f"/api/shots/{shot_id}/generate-voice", json={"track": "DIALOGUE", "voice_id": marcus_voice_id}
        ).json()
    finally:
        del app.dependency_overrides[get_voice_provider]

    assert stub.calls == 2
    assert first["output_path"] != second["output_path"]


def test_different_seeds_are_not_cache_hits_against_each_other(client):
    from app.main import app

    shot_id, marcus_voice_id, _ = _create_series_with_shot(client)
    stub = _CountingVoiceProvider()
    app.dependency_overrides[get_voice_provider] = lambda: stub
    try:
        first = client.post(
            f"/api/shots/{shot_id}/generate-voice",
            json={"track": "DIALOGUE", "voice_id": marcus_voice_id, "seed": 1},
        ).json()
        second = client.post(
            f"/api/shots/{shot_id}/generate-voice",
            json={"track": "DIALOGUE", "voice_id": marcus_voice_id, "seed": 2},
        ).json()
        same_seed_again = client.post(
            f"/api/shots/{shot_id}/generate-voice",
            json={"track": "DIALOGUE", "voice_id": marcus_voice_id, "seed": 1},
        ).json()
    finally:
        del app.dependency_overrides[get_voice_provider]

    assert stub.calls == 2
    assert first["output_path"] != second["output_path"]
    assert same_seed_again["output_path"] == first["output_path"]


def test_delete_shared_cached_file_keeps_it_until_last_reference(client, test_storage):
    shot_id, marcus_voice_id, _ = _create_series_with_shot(client)
    first = client.post(
        f"/api/shots/{shot_id}/generate-voice", json={"track": "DIALOGUE", "voice_id": marcus_voice_id}
    ).json()
    second = client.post(
        f"/api/shots/{shot_id}/generate-voice", json={"track": "DIALOGUE", "voice_id": marcus_voice_id}
    ).json()
    assert first["output_path"] == second["output_path"]

    client.delete(f"/api/generations/{first['id']}")
    assert test_storage.exists(second["output_path"])

    client.delete(f"/api/generations/{second['id']}")
    assert not test_storage.exists(second["output_path"])


def test_activation_is_scoped_by_type_and_track(client):
    shot_id, marcus_voice_id, narrator_voice_id = _create_series_with_shot(client)

    image_gen = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={}).json()
    dialogue_gen = client.post(
        f"/api/shots/{shot_id}/generate-voice", json={"track": "DIALOGUE", "voice_id": marcus_voice_id}
    ).json()
    narration_gen = client.post(
        f"/api/shots/{shot_id}/generate-voice", json={"track": "NARRATION", "voice_id": narrator_voice_id}
    ).json()

    client.post(f"/api/generations/{image_gen['id']}/activate")
    client.post(f"/api/generations/{dialogue_gen['id']}/activate")
    client.post(f"/api/generations/{narration_gen['id']}/activate")

    shot = client.get(f"/api/shots/{shot_id}").json()
    assert shot["active_image_generation"]["id"] == image_gen["id"]
    assert shot["active_dialogue_generation"]["id"] == dialogue_gen["id"]
    assert shot["active_narration_generation"]["id"] == narration_gen["id"]

    # Activating a second dialogue take must not disturb the image or narration actives.
    dialogue_gen_2 = client.post(
        f"/api/shots/{shot_id}/generate-voice",
        json={"track": "DIALOGUE", "voice_id": marcus_voice_id, "force_regenerate": True},
    ).json()
    client.post(f"/api/generations/{dialogue_gen_2['id']}/activate")

    shot = client.get(f"/api/shots/{shot_id}").json()
    assert shot["active_dialogue_generation"]["id"] == dialogue_gen_2["id"]
    assert shot["active_image_generation"]["id"] == image_gen["id"]
    assert shot["active_narration_generation"]["id"] == narration_gen["id"]
