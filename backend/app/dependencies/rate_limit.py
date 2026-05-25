"""
SlowAPI rate limiter, backed by Redis.
Use as a router/endpoint decorator: @limiter.limit("5/minute")

headers_enabled is set to False to avoid a slowapi 0.1.9 incompatibility
with Starlette's response handling when the decorator tries to inject
rate-limit headers from a non-Response object.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.app.core.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=str(settings.redis_url),
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
    headers_enabled=False,
)
