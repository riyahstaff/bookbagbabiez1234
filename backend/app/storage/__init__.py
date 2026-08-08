from functools import lru_cache

from app.config import DATA_DIR
from app.storage.local import LocalStorageBackend


@lru_cache
def get_storage() -> LocalStorageBackend:
    return LocalStorageBackend(DATA_DIR / "series")
