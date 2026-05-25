"""
Structured per-request log middleware.
"""

from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.app.core.logging import get_logger

log = get_logger("http")


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    if route is not None and getattr(route, "path", None):
        return route.path
    return request.url.path


class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        status = 500
        try:
            response: Response = await call_next(request)
            status = response.status_code
            return response
        finally:
            elapsed_ms = round((time.perf_counter() - start) * 1000.0, 1)
            route = _route_template(request)
            quiet = route in {"/metrics", "/healthz", "/livez"}
            if not quiet:
                log.info(
                    "http_request",
                    method=request.method,
                    route=route,
                    status=status,
                    duration_ms=elapsed_ms,
                )
