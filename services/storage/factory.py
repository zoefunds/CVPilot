"""
Factory that returns the configured storage backend.
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
    if settings.storage_backend == "s3":
        # Lazy import so boto3 only loads when S3 is actually selected.
        from services.storage.s3 import S3Storage
        return S3Storage()
    raise NotImplementedError(
        f"Unsupported storage backend: {settings.storage_backend}"
    )
