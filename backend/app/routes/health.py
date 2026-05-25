"""
Health endpoints:
  /healthz - liveness (process is up)
  /readyz  - readiness (DB reachable)
"""

from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.db.session import ping_db

router = APIRouter(tags=["health"])


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
    body = {"status": "ok" if db_ok else "degraded", "checks": {"database": db_ok}}
    code = status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=code, content=body)
