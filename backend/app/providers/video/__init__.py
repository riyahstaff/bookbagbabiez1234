from functools import lru_cache

from app.config import get_settings
from app.providers.video.base import VideoProvider
from app.providers.video.mock import MockVideoProvider


def _build_provider(name: str) -> VideoProvider:
    if name == "mock":
        return MockVideoProvider()
    if name == "comfyui":
        from app.providers.video.comfyui import ComfyUIVideoProvider

        settings = get_settings()
        return ComfyUIVideoProvider(base_url=settings.comfyui_base_url)
    if name == "fal":
        from app.providers.video.fal import FalVideoProvider

        return FalVideoProvider()
    raise ValueError(f"Unknown video provider: {name!r}")


@lru_cache
def get_video_provider() -> VideoProvider:
    settings = get_settings()
    return _build_provider(settings.video_provider)
