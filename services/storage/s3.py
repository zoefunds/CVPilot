"""
S3-compatible storage. Works with Tigris (Fly), AWS S3, Cloudflare R2,
and MinIO. Reads credentials and endpoint from standard AWS_* env vars
that boto3 already understands.
"""

from __future__ import annotations

import os
from functools import lru_cache

import boto3
from botocore.exceptions import ClientError

from services.storage.base import FileStorage, StoredFile


@lru_cache(maxsize=1)
def _client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ.get("AWS_ENDPOINT_URL_S3")
        or os.environ.get("AWS_ENDPOINT_URL"),
        region_name=os.environ.get("AWS_REGION", "auto"),
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    )


def _bucket() -> str:
    name = os.environ.get("BUCKET_NAME")
    if not name:
        raise RuntimeError(
            "BUCKET_NAME env var must be set when STORAGE_BACKEND=s3."
        )
    return name


class S3Storage(FileStorage):
    def save(self, key: str, data: bytes, content_type: str) -> StoredFile:
        _client().put_object(
            Bucket=_bucket(),
            Key=key,
            Body=data,
            ContentType=content_type or "application/octet-stream",
        )
        return StoredFile(
            key=key, byte_size=len(data), content_type=content_type
        )

    def read(self, key: str) -> bytes:
        resp = _client().get_object(Bucket=_bucket(), Key=key)
        return resp["Body"].read()

    def delete(self, key: str) -> None:
        _client().delete_object(Bucket=_bucket(), Key=key)

    def exists(self, key: str) -> bool:
        try:
            _client().head_object(Bucket=_bucket(), Key=key)
            return True
        except ClientError:
            return False
