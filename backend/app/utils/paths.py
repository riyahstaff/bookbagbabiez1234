import uuid
from pathlib import PurePosixPath


def _asset_path(*parts: str, filename: str) -> str:
    ext = PurePosixPath(filename).suffix
    return "/".join((*parts, f"{uuid.uuid4().hex}{ext}"))


def character_reference_path(series_code: str, character_code: str, filename: str) -> str:
    return _asset_path(series_code, "characters", character_code, "references", filename=filename)


def outfit_reference_path(series_code: str, character_code: str, outfit_code: str, filename: str) -> str:
    return _asset_path(
        series_code, "characters", character_code, "outfits", outfit_code, filename=filename
    )


def voice_reference_audio_path(series_code: str, voice_code: str, filename: str) -> str:
    return _asset_path(series_code, "voices", voice_code, filename=filename)


def location_reference_path(series_code: str, location_code: str, filename: str) -> str:
    return _asset_path(series_code, "locations", location_code, "references", filename=filename)


def prop_reference_path(series_code: str, prop_code: str, filename: str) -> str:
    return _asset_path(series_code, "props", prop_code, "references", filename=filename)


def generation_output_path(
    series_code: str, episode_code: str, shot_id: int, filename: str
) -> str:
    return _asset_path(
        series_code, "episodes", episode_code, "shots", str(shot_id), "generations", filename=filename
    )


def episode_export_path(series_code: str, episode_code: str, filename: str) -> str:
    return _asset_path(series_code, "episodes", episode_code, "episode_output", filename=filename)
