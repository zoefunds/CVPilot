"""
Local filesystem implementation of FileStorage.
Files live under settings.storage_local_path (default ./storage/uploads).
Keys may contain forward slashes; they are translated to subdirectories.
"""

from __future__ import annotations

import os
from pathlib import Path

from backend.app.core.config import settings
from services.storage.base import FileStorage, StoredFile


class LocalFileStorage(FileStorage):
    def __init__(self, root: str | None = None) -> None:
        self.root = Path(root or settings.storage_local_path).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # Defense in depth: never let a key escape the root.
        key = key.lstrip("/").replace("..", "_")
        p = (self.root / key).resolve()
        if not str(p).startswith(str(self.root)):
            raise ValueError("Path traversal attempt rejected.")
        return p

    def save(self, key: str, data: bytes, content_type: str) -> StoredFile:
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "wb") as f:
            f.write(data)
        return StoredFile(key=key, byte_size=len(data), content_type=content_type)

    def read(self, key: str) -> bytes:
        with open(self._path(key), "rb") as f:
            return f.read()

    def delete(self, key: str) -> None:
        p = self._path(key)
        if p.exists():
            os.remove(p)

    def exists(self, key: str) -> bool:
        return self._path(key).exists()
