from functools import lru_cache

from app.config import get_settings
from app.providers.lipsync.base import LipSyncProvider
from app.providers.lipsync.mock import MockLipSyncProvider


def _build_provider(name: str, quality_mode: bool) -> LipSyncProvider:
    if name == "mock":
        return MockLipSyncProvider()
    if name == "fal":
        from app.providers.lipsync.fal import FalLipSyncProvider

        return FalLipSyncProvider(quality_mode=quality_mode)
    raise ValueError(f"Unknown lipsync provider: {name!r}")


@lru_cache
def get_lipsync_provider() -> LipSyncProvider:
    settings = get_settings()
    return _build_provider(settings.lipsync_provider, settings.lipsync_quality_mode)
