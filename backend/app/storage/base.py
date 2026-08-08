from abc import ABC, abstractmethod


class StorageBackend(ABC):
    """Where uploaded reference assets (images, audio) live.

    Local filesystem for now; the interface is deliberately small so an
    S3-compatible backend can be dropped in later without touching callers.
    """

    @abstractmethod
    def save(self, relative_path: str, content: bytes) -> str:
        """Persist content at relative_path, returning the path it was stored under."""

    @abstractmethod
    def delete(self, relative_path: str) -> None:
        """Remove the file at relative_path. No-op if it doesn't exist."""

    @abstractmethod
    def exists(self, relative_path: str) -> bool: ...

    @abstractmethod
    def read(self, relative_path: str) -> bytes:
        """Read back the bytes stored at relative_path. Raises if missing."""
