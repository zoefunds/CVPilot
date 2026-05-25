"""
Factory that returns the configured storage backend.
Today: local. Tomorrow: switch on settings.storage_backend.
"""

from __future__ import annotations

from functools import lru_cache

from backend.app.core.config import settings
from services.storage.base import FileStorage
from services.storage.local import LocalFileStorage


@lru_cache(maxsize=1)
def get_storage() -> FileStorage:
    if settings.storage_backend == "local":
        return LocalFileStorage()
    raise NotImplementedError(f"Unsupported storage backend: {settings.storage_backend}")
