from pathlib import Path

from app.storage.base import StorageBackend


class LocalStorageBackend(StorageBackend):
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, relative_path: str, content: bytes) -> str:
        full_path = self.root / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)
        return relative_path

    def delete(self, relative_path: str) -> None:
        full_path = self.root / relative_path
        if full_path.exists():
            full_path.unlink()

    def exists(self, relative_path: str) -> bool:
        return (self.root / relative_path).exists()
