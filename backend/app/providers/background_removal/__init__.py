from functools import lru_cache

from app.config import get_settings
from app.providers.background_removal.base import BackgroundRemovalProvider
from app.providers.background_removal.mock import MockBackgroundRemovalProvider


def _build_provider(name: str) -> BackgroundRemovalProvider:
    if name == "mock":
        return MockBackgroundRemovalProvider()
    if name == "fal":
        from app.providers.background_removal.fal import FalBackgroundRemovalProvider

        return FalBackgroundRemovalProvider()
    raise ValueError(f"Unknown background removal provider: {name!r}")


@lru_cache
def get_background_removal_provider() -> BackgroundRemovalProvider:
    settings = get_settings()
    return _build_provider(settings.background_removal_provider)
