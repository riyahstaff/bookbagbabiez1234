import subprocess
from pathlib import Path

from app.api.routers import episode_exports as episode_exports_router


def _probe_stream_types(path: Path) -> list[str]:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return sorted(line.strip() for line in result.stdout.splitlines() if line.strip())


def _write_to_tmp(test_storage, relative_path: str, tmp_path: Path, name: str) -> Path:
    content = test_storage.read(relative_path)
    out = tmp_path / name
    out.write_bytes(content)
    return out


def _make_shot_with_full_media(client, scene_id, shot_number, voice_id) -> dict:
    shot = client.post(
        f"/api/scenes/{scene_id}/shots",
        json={
            "shot_number": shot_number,
            "dialogue": f"Line for shot {shot_number}",
        },
    ).json()
    image = client.post(f"/api/shots/{shot['id']}/generate-storyboard", json={}).json()
    client.post(f"/api/generations/{image['id']}/approve")
    dialogue = client.post(
        f"/api/shots/{shot['id']}/generate-voice", json={"track": "DIALOGUE", "voice_id": voice_id}
    ).json()
    client.post(f"/api/generations/{dialogue['id']}/approve")
    video = client.post(f"/api/shots/{shot['id']}/generate-video", json={}).json()
    client.post(f"/api/generations/{video['id']}/activate")
    return shot


def _setup_full_episode(client) -> tuple[int, int]:
    series_id = client.post("/api/series", json={"title": "Space Pals"}).json()["id"]
    marcus = client.post(f"/api/series/{series_id}/characters", json={"name": "Marcus"}).json()
    episode = client.post(
        f"/api/series/{series_id}/episodes", json={"episode_number": 1, "title": "Pilot"}
    ).json()
    scene = client.post(f"/api/episodes/{episode['id']}/scenes", json={"scene_number": 1}).json()
    client.put(
        f"/api/scenes/{scene['id']}/characters", json={"characters": [{"character_id": marcus["id"]}]}
    )
    voice_id = client.post(f"/api/series/{series_id}/voices", json={"name": "Marcus Voice"}).json()["id"]

    _make_shot_with_full_media(client, scene["id"], 1, voice_id)
    _make_shot_with_full_media(client, scene["id"], 2, voice_id)

    return episode["id"], series_id


def test_export_happy_path_with_all_options(client, test_storage, tmp_path):
    episode_id, _ = _setup_full_episode(client)

    response = client.post(
        f"/api/episodes/{episode_id}/export",
        json={"include_titles": True, "include_credits": True, "include_subtitles": True},
    )
    assert response.status_code == 201
    export = response.json()

    assert export["status"] == "COMPLETE"
    assert export["output_path"]
    assert export["duration_seconds"] > 0
    assert export["skipped_shots"] == []
    assert test_storage.exists(export["output_path"])

    local_copy = _write_to_tmp(test_storage, export["output_path"], tmp_path, "export.mp4")
    assert _probe_stream_types(local_copy) == ["audio", "subtitle", "video"]

    episode = client.get(f"/api/episodes/{episode_id}").json()
    assert episode["status"] == "QC"


def test_export_without_extras_is_shorter_and_has_no_subtitles(client, test_storage, tmp_path):
    episode_id, _ = _setup_full_episode(client)

    with_extras = client.post(
        f"/api/episodes/{episode_id}/export",
        json={"include_titles": True, "include_credits": True, "include_subtitles": True},
    ).json()
    without_extras = client.post(
        f"/api/episodes/{episode_id}/export",
        json={"include_titles": False, "include_credits": False, "include_subtitles": False},
    ).json()

    assert without_extras["duration_seconds"] < with_extras["duration_seconds"]

    local_copy = _write_to_tmp(test_storage, without_extras["output_path"], tmp_path, "no_extras.mp4")
    assert _probe_stream_types(local_copy) == ["audio", "video"]


def test_export_list_orders_newest_first(client):
    episode_id, _ = _setup_full_episode(client)
    first = client.post(f"/api/episodes/{episode_id}/export", json={}).json()
    second = client.post(f"/api/episodes/{episode_id}/export", json={}).json()

    listed = client.get(f"/api/episodes/{episode_id}/exports").json()
    assert [item["id"] for item in listed] == [second["id"], first["id"]]


def test_export_preview_reports_renderable_count_and_skipped_shots(client):
    series_id = client.post("/api/series", json={"title": "Space Pals"}).json()["id"]
    episode = client.post(
        f"/api/series/{series_id}/episodes", json={"episode_number": 1, "title": "Pilot"}
    ).json()
    scene = client.post(f"/api/episodes/{episode['id']}/scenes", json={"scene_number": 1}).json()
    voice_id = client.post(f"/api/series/{series_id}/voices", json={"name": "Voice"}).json()["id"]

    _make_shot_with_full_media(client, scene["id"], 1, voice_id)
    client.post(f"/api/scenes/{scene['id']}/shots", json={"shot_number": 2})  # nothing rendered for this one

    preview = client.get(f"/api/episodes/{episode['id']}/export-preview").json()
    assert preview["renderable_shot_count"] == 1
    assert preview["skipped_shots"] == ["Scene 1 Shot 2"]


def test_export_preview_on_missing_episode_404s(client):
    response = client.get("/api/episodes/999999/export-preview")
    assert response.status_code == 404


def test_export_blocked_with_no_renderable_shots(client):
    series_id = client.post("/api/series", json={"title": "Space Pals"}).json()["id"]
    episode = client.post(
        f"/api/series/{series_id}/episodes", json={"episode_number": 1, "title": "Pilot"}
    ).json()

    response = client.post(f"/api/episodes/{episode['id']}/export", json={})
    assert response.status_code == 409


def test_export_on_missing_episode_404s(client):
    response = client.post("/api/episodes/999999/export", json={})
    assert response.status_code == 404


def test_export_reports_skipped_shots_but_still_succeeds(client):
    series_id = client.post("/api/series", json={"title": "Space Pals"}).json()["id"]
    episode = client.post(
        f"/api/series/{series_id}/episodes", json={"episode_number": 1, "title": "Pilot"}
    ).json()
    scene = client.post(f"/api/episodes/{episode['id']}/scenes", json={"scene_number": 1}).json()
    voice_id = client.post(f"/api/series/{series_id}/voices", json={"name": "Voice"}).json()["id"]

    _make_shot_with_full_media(client, scene["id"], 1, voice_id)
    client.post(f"/api/scenes/{scene['id']}/shots", json={"shot_number": 2})  # nothing rendered for this one

    export = client.post(f"/api/episodes/{episode['id']}/export", json={}).json()

    assert export["status"] == "COMPLETE"
    assert export["skipped_shots"] == ["Scene 1 Shot 2"]


def test_export_failure_reverts_episode_status_and_records_error(client, monkeypatch):
    episode_id, _ = _setup_full_episode(client)
    original_status = client.get(f"/api/episodes/{episode_id}").json()["status"]

    def _broken_assemble(*args, **kwargs):
        raise RuntimeError("simulated ffmpeg crash")

    monkeypatch.setattr(episode_exports_router, "assemble_episode", _broken_assemble)

    response = client.post(f"/api/episodes/{episode_id}/export", json={})
    assert response.status_code == 201
    export = response.json()
    assert export["status"] == "FAILED"
    assert "simulated ffmpeg crash" in export["error_message"]

    episode = client.get(f"/api/episodes/{episode_id}").json()
    assert episode["status"] == original_status


def test_delete_export_removes_row_and_file(client, test_storage):
    episode_id, _ = _setup_full_episode(client)
    export = client.post(f"/api/episodes/{episode_id}/export", json={}).json()
    assert test_storage.exists(export["output_path"])

    response = client.delete(f"/api/exports/{export['id']}")
    assert response.status_code == 204
    assert not test_storage.exists(export["output_path"])
    assert client.get(f"/api/episodes/{episode_id}/exports").json() == []


def test_delete_export_on_missing_id_404s(client):
    response = client.delete("/api/exports/999999")
    assert response.status_code == 404
