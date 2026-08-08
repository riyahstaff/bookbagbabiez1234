from abc import ABC, abstractmethod
from pathlib import Path


class StorageBackend(ABC):
    """Where uploaded reference assets (images, audio) live.

    Local filesystem for now; the interface is deliberately small so an
    S3-compatible backend can be dropped in later without touching callers.
    """

    @abstractmethod
    def save(self, relative_path: str, content: bytes) -> str:
        """Persist content at relative_path, returning the path it was stored under."""

    @abstractmethod
    def save_file(self, relative_path: str, source_path: Path) -> str:
        """Persist the file at source_path under relative_path, returning the
        path it was stored under. Prefer this over save() for large files
        (e.g. assembled episode exports) - avoids holding the whole thing in
        memory as bytes the way save() does."""

    @abstractmethod
    def delete(self, relative_path: str) -> None:
        """Remove the file at relative_path. No-op if it doesn't exist."""

    @abstractmethod
    def exists(self, relative_path: str) -> bool: ...

    @abstractmethod
    def read(self, relative_path: str) -> bytes:
        """Read back the bytes stored at relative_path. Raises if missing."""
