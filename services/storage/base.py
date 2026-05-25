"""
Storage abstraction. Designed so a future S3/R2/GCS implementation
just provides this Protocol; routes do not change.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class StoredFile:
    key: str
    byte_size: int
    content_type: str


class FileStorage(Protocol):
    def save(self, key: str, data: bytes, content_type: str) -> StoredFile: ...
    def read(self, key: str) -> bytes: ...
    def delete(self, key: str) -> None: ...
    def exists(self, key: str) -> bool: ...
