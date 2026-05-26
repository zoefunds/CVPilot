"""
Redis cache for job ingestion results.
Key: job_ingest:sha256(url)[:32]. TTL: 24h.
"""

from __future__ import annotations

import hashlib
import json
from typing import Optional

from backend.app.core.config import settings
from backend.app.core.logging import get_logger

log = get_logger("ingest_cache")
_TTL = 86400


def _key(url: str) -> str:
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]
    return f"job_ingest:{h}"


def _client():
    try:
        import redis
        return redis.Redis.from_url(str(settings.redis_url), socket_timeout=2.0)
    except Exception as exc:
        log.warning("ingest_cache_connect_failed", error=str(exc))
        return None


def get(url: str) -> Optional[dict]:
    client = _client()
    if client is None:
        return None
    try:
        raw = client.get(_key(url))
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as exc:
        log.warning("ingest_cache_get_failed", error=str(exc))
        return None


def put(url: str, value: dict) -> None:
    client = _client()
    if client is None:
        return
    try:
        client.setex(_key(url), _TTL, json.dumps(value, default=str))
    except Exception as exc:
        log.warning("ingest_cache_put_failed", error=str(exc))
