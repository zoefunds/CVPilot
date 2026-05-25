"""
Disable slowapi's decorator-level header injection.
slowapi 0.1.9 + starlette 0.41 raises:
  'parameter `response` must be an instance of starlette.responses.Response'
when the decorator runs because endpoints don't expose a Response kwarg.
We keep rate-limit *enforcement* (the decorator + middleware) but skip
header injection. Limits still work; X-RateLimit-* headers are simply
not emitted. We'll re-enable them properly in a later phase if needed.
"""

from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
TARGET = ROOT / "backend/app/dependencies/rate_limit.py"

NEW = '''"""
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
'''


def main() -> None:
    TARGET.write_text(NEW, encoding="utf-8")
    print(f"patched {TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
