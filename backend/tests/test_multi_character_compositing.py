import io

from PIL import Image

from app.providers.background_removal import get_background_removal_provider
from app.providers.background_removal.base import BackgroundRemovalResult
from app.providers.image import get_image_provider
from app.providers.image.base import ImageGenerationResult, ImageProvider


def _real_png(size=(200, 400), color=(120, 60, 200)) -> bytes:
    image = Image.new("RGB", size, color=color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


class _RealImageRecordingProvider(ImageProvider):
    """Like the plain _RecordingReferenceProvider used elsewhere, but returns
    genuine decodable PNGs - required here because, unlike the plain
    single-reference path, the compositing path actually opens returned
    bytes with Pillow (crop/resize/paste), not just save-to-disk."""

    def __init__(self):
        self.calls: list[dict] = []

    def supports_reference_image(self) -> bool:
        return True

    def generate_image(
        self, prompt, negative_prompt=None, seed=None, width=1024, height=576, reference_image_bytes=None
    ):
        self.calls.append({"prompt": prompt, "reference_image_bytes": reference_image_bytes})
        size = (width, height) if reference_image_bytes is None else (200, 400)
        return ImageGenerationResult(
            image_bytes=_real_png(size), seed_used=seed or 123, model_name="real-recording-image-v1"
        )


class _PassthroughBackgroundRemovalProvider:
    def __init__(self):
        self.calls = 0

    def remove_background(self, image_bytes: bytes) -> BackgroundRemovalResult:
        self.calls += 1
        image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return BackgroundRemovalResult(image_bytes=buffer.getvalue(), model_name="real-recording-bgremoval-v1")


def _setup_two_characters_with_references(client) -> tuple[int, int, int, int]:
    series_id = client.post("/api/series", json={"title": "Space Pals"}).json()["id"]
    marcus = client.post(f"/api/series/{series_id}/characters", json={"name": "Marcus"}).json()
    nova = client.post(f"/api/series/{series_id}/characters", json={"name": "Nova"}).json()
    for character_id, content in ((marcus["id"], b"marcus-ref"), (nova["id"], b"nova-ref")):
        response = client.post(
            f"/api/characters/{character_id}/references",
            data={"category": "FRONT"},
            files={"file": ("front.png", content, "image/png")},
        )
        assert response.status_code == 201
    episode = client.post(
        f"/api/series/{series_id}/episodes", json={"episode_number": 1, "title": "Pilot"}
    ).json()
    scene = client.post(f"/api/episodes/{episode['id']}/scenes", json={"scene_number": 1}).json()
    shot = client.post(f"/api/scenes/{scene['id']}/shots", json={"shot_number": 1}).json()
    client.put(
        f"/api/shots/{shot['id']}/characters",
        json={"characters": [{"character_id": marcus["id"]}, {"character_id": nova["id"]}]},
    )
    return series_id, scene["id"], shot["id"], episode["id"]


def test_all_characters_with_references_triggers_compositing(client, test_storage):
    from app.main import app

    _, _, shot_id, _ = _setup_two_characters_with_references(client)

    image_provider = _RealImageRecordingProvider()
    background_removal_provider = _PassthroughBackgroundRemovalProvider()
    app.dependency_overrides[get_image_provider] = lambda: image_provider
    app.dependency_overrides[get_background_removal_provider] = lambda: background_removal_provider
    try:
        response = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={})
    finally:
        del app.dependency_overrides[get_image_provider]
        del app.dependency_overrides[get_background_removal_provider]

    assert response.status_code == 201
    generation = response.json()
    assert generation["status"] == "COMPLETE"
    assert "composite" in generation["provider_name"].lower()

    # One background-plate call (no Location art uploaded) + one per
    # character, each carrying that character's own reference bytes.
    assert len(image_provider.calls) == 3
    reference_bytes = sorted(c["reference_image_bytes"] for c in image_provider.calls if c["reference_image_bytes"])
    assert reference_bytes == [b"marcus-ref", b"nova-ref"]
    assert background_removal_provider.calls == 2

    output_bytes = test_storage.read(generation["output_path"])
    image = Image.open(io.BytesIO(output_bytes))
    assert image.size == (1024, 576)


def test_compositing_reuses_location_reference_art(client, test_storage):
    from app.main import app

    series_id, scene_id, shot_id, _ = _setup_two_characters_with_references(client)

    location = client.post(
        f"/api/series/{series_id}/locations", json={"name": "Classroom"}
    ).json()
    upload_response = client.post(
        f"/api/locations/{location['id']}/references",
        data={"category": "WIDE_ESTABLISHING"},
        files={"file": ("wide.png", _real_png((640, 360), (10, 200, 10)), "image/png")},
    )
    assert upload_response.status_code == 201
    client.patch(f"/api/scenes/{scene_id}", json={"location_id": location["id"]})

    image_provider = _RealImageRecordingProvider()
    background_removal_provider = _PassthroughBackgroundRemovalProvider()
    app.dependency_overrides[get_image_provider] = lambda: image_provider
    app.dependency_overrides[get_background_removal_provider] = lambda: background_removal_provider
    try:
        response = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={})
    finally:
        del app.dependency_overrides[get_image_provider]
        del app.dependency_overrides[get_background_removal_provider]

    assert response.status_code == 201
    # Only the two per-character calls - no extra background-plate call,
    # since the Location's own reference art was reused instead.
    assert len(image_provider.calls) == 2

    output_bytes = test_storage.read(response.json()["output_path"])
    image = Image.open(io.BytesIO(output_bytes)).convert("RGB")
    assert image.size == (1024, 576)


def test_compositing_never_reached_when_provider_lacks_reference_support(client):
    # The default MockImageProvider always returns False from
    # supports_reference_image() - even with 2 fully-referenced characters,
    # this must take the plain existing path untouched.
    _, _, shot_id, _ = _setup_two_characters_with_references(client)

    response = client.post(f"/api/shots/{shot_id}/generate-storyboard", json={})
    assert response.status_code == 201
    generation = response.json()
    assert generation["status"] == "COMPLETE"
    assert generation["provider_name"] == "MockImageProvider"
