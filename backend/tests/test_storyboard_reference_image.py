from app.providers.image import get_image_provider
from app.providers.image.base import ImageGenerationResult, ImageProvider


class _RecordingReferenceProvider(ImageProvider):
    """Records what reference_image_bytes it was called with, so tests can
    assert on exactly what the router decided to pass through."""

    def __init__(self):
        self.calls = []

    def supports_reference_image(self) -> bool:
        return True

    def generate_image(
        self,
        prompt,
        negative_prompt=None,
        seed=None,
        width=1024,
        height=576,
        reference_image_bytes=None,
    ):
        self.calls.append(reference_image_bytes)
        return ImageGenerationResult(image_bytes=b"fake-png", seed_used=seed, model_name="recording-v1")


def _setup(client) -> tuple[int, int]:
    series_id = client.post("/api/series", json={"title": "Space Pals"}).json()["id"]
    episode = client.post(
        f"/api/series/{series_id}/episodes", json={"episode_number": 1, "title": "Pilot"}
    ).json()
    scene = client.post(f"/api/episodes/{episode['id']}/scenes", json={"scene_number": 1}).json()
    shot = client.post(f"/api/scenes/{scene['id']}/shots", json={"shot_number": 1}).json()
    return series_id, shot["id"]


def _upload_reference(client, character_id: int, content: bytes = b"reference-image-bytes") -> None:
    response = client.post(
        f"/api/characters/{character_id}/references",
        data={"category": "FRONT"},
        files={"file": ("front.png", content, "image/png")},
    )
    assert response.status_code == 201


def test_single_visible_character_with_reference_passes_bytes_through(client):
    from app.main import app

    series_id, shot_id = _setup(client)
    marcus = client.post(f"/api/series/{series_id}/characters", json={"name": "Marcus"}).json()
    _upload_reference(client, marcus["id"], b"marcus-reference-bytes")
    client.put(f"/api/shots/{shot_id}/characters", json={"characters": [{"character_id": marcus["id"]}]})

    provider = _RecordingReferenceProvider()
    app.dependency_overrides[get_image_provider] = lambda: provider
    try:
        response = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={})
    finally:
        del app.dependency_overrides[get_image_provider]

    assert response.status_code == 201
    assert provider.calls == [b"marcus-reference-bytes"]


def test_single_visible_character_without_reference_passes_none(client):
    from app.main import app

    series_id, shot_id = _setup(client)
    marcus = client.post(f"/api/series/{series_id}/characters", json={"name": "Marcus"}).json()
    client.put(f"/api/shots/{shot_id}/characters", json={"characters": [{"character_id": marcus["id"]}]})

    provider = _RecordingReferenceProvider()
    app.dependency_overrides[get_image_provider] = lambda: provider
    try:
        client.post(f"/api/shots/{shot_id}/generate-storyboard", json={})
    finally:
        del app.dependency_overrides[get_image_provider]

    assert provider.calls == [None]


def test_multiple_visible_characters_passes_none_even_with_references(client):
    from app.main import app

    series_id, shot_id = _setup(client)
    marcus = client.post(f"/api/series/{series_id}/characters", json={"name": "Marcus"}).json()
    nova = client.post(f"/api/series/{series_id}/characters", json={"name": "Nova"}).json()
    _upload_reference(client, marcus["id"])
    _upload_reference(client, nova["id"])
    client.put(
        f"/api/shots/{shot_id}/characters",
        json={"characters": [{"character_id": marcus["id"]}, {"character_id": nova["id"]}]},
    )

    provider = _RecordingReferenceProvider()
    app.dependency_overrides[get_image_provider] = lambda: provider
    try:
        client.post(f"/api/shots/{shot_id}/generate-storyboard", json={})
    finally:
        del app.dependency_overrides[get_image_provider]

    assert provider.calls == [None]


def test_no_visible_characters_passes_none(client):
    from app.main import app

    _, shot_id = _setup(client)

    provider = _RecordingReferenceProvider()
    app.dependency_overrides[get_image_provider] = lambda: provider
    try:
        client.post(f"/api/shots/{shot_id}/generate-storyboard", json={})
    finally:
        del app.dependency_overrides[get_image_provider]

    assert provider.calls == [None]


def test_provider_without_reference_support_is_never_asked(client):
    # MockImageProvider (the default) doesn't support reference images -
    # this should succeed normally regardless of uploaded references.
    series_id, shot_id = _setup(client)
    marcus = client.post(f"/api/series/{series_id}/characters", json={"name": "Marcus"}).json()
    _upload_reference(client, marcus["id"])
    client.put(f"/api/shots/{shot_id}/characters", json={"characters": [{"character_id": marcus["id"]}]})

    response = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={})
    assert response.status_code == 201
    assert response.json()["status"] == "COMPLETE"


def test_front_category_preferred_over_other_categories(client):
    from app.main import app

    series_id, shot_id = _setup(client)
    marcus = client.post(f"/api/series/{series_id}/characters", json={"name": "Marcus"}).json()
    client.post(
        f"/api/characters/{marcus['id']}/references",
        data={"category": "SIDE"},
        files={"file": ("side.png", b"side-bytes", "image/png")},
    )
    client.post(
        f"/api/characters/{marcus['id']}/references",
        data={"category": "FRONT"},
        files={"file": ("front.png", b"front-bytes", "image/png")},
    )
    client.put(f"/api/shots/{shot_id}/characters", json={"characters": [{"character_id": marcus["id"]}]})

    provider = _RecordingReferenceProvider()
    app.dependency_overrides[get_image_provider] = lambda: provider
    try:
        client.post(f"/api/shots/{shot_id}/generate-storyboard", json={})
    finally:
        del app.dependency_overrides[get_image_provider]

    assert provider.calls == [b"front-bytes"]
