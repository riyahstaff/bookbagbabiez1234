from functools import lru_cache

from app.config import get_settings
from app.providers.image.base import ImageProvider
from app.providers.image.mock import MockImageProvider


def _build_provider(name: str) -> ImageProvider:
    if name == "mock":
        return MockImageProvider()
    if name == "comfyui":
        from app.providers.image.comfyui import ComfyUIImageProvider

        settings = get_settings()
        return ComfyUIImageProvider(base_url=settings.comfyui_base_url)
    if name == "fal":
        from app.providers.image.fal import FalImageProvider

        return FalImageProvider()
    raise ValueError(f"Unknown image provider: {name!r}")


@lru_cache
def get_image_provider() -> ImageProvider:
    settings = get_settings()
    return _build_provider(settings.image_provider)
