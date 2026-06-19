"""
Health endpoints.

  /healthz - liveness (no dependencies)
  /readyz  - readiness (DB, Redis, GenLayer contract)
  /livez   - simplest 200 probe for orchestrators
"""

from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse, Response

from backend.app.core.config import settings
from backend.app.core.logging import get_logger
from backend.app.core.metrics import contract_probe_total
from backend.app.db.session import ping_db

router = APIRouter(tags=["health"])
log = get_logger("health")


def _ping_redis() -> bool:
    try:
        import redis  # type: ignore
        client = redis.Redis.from_url(str(settings.redis_url), socket_timeout=2.0)
        return bool(client.ping())
    except Exception as exc:
        log.warning("readyz_redis_failed", error=str(exc))
        return False


def _ping_genlayer_contract() -> bool:
    if settings.llm_backend != "genlayer":
        return True
    try:
        from services.genlayer.read import _client
        client = _client()
        ok, value = client._try_read("contract_version", [])
        contract_probe_total.labels(result="ok" if ok else "failed").inc()
        return bool(ok and value)
    except Exception as exc:
        log.warning("readyz_contract_failed", error=str(exc))
        contract_probe_total.labels(result="failed").inc()
        return False


@router.get("/healthz")
def healthz() -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "env": settings.app_env,
    }


@router.get("/readyz")
def readyz() -> JSONResponse:
    db_ok = ping_db()
    redis_ok = _ping_redis()
    checks = {
        "database": db_ok,
        "redis": redis_ok,
        "genlayer": _ping_genlayer_contract(),
    }
    # Only DB and Redis gate readiness; GenLayer contract is informational
    # (contract may be warming up on StudioNet after a new deployment)
    core_ok = db_ok and redis_ok
    code = status.HTTP_200_OK if core_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=code,
        content={"status": "ok" if all(checks.values()) else "degraded", "checks": checks},
    )


@router.get("/livez", include_in_schema=False)
def livez() -> Response:
    return Response(status_code=200)
