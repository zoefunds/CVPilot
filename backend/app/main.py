"""
FastAPI application factory.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.v1.router import api_router
from backend.app.core.config import settings
from backend.app.core.errors import register_exception_handlers
from backend.app.core.logging import configure_logging, get_logger
from backend.app.core.startup_guard import assert_safe_startup
from backend.app.dependencies.rate_limit import limiter
from backend.app.middleware.request_id import RequestIDMiddleware
from backend.app.middleware.request_log import RequestLogMiddleware
from backend.app.middleware.security_headers import SecurityHeadersMiddleware
from backend.app.routes import health


def create_app() -> FastAPI:
    assert_safe_startup()
    configure_logging()
    log = get_logger("startup")

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.app_debug,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
    )

    Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        excluded_handlers=["/metrics", "/healthz", "/livez"],
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(RequestLogMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIDMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.app_frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(api_router)

    @app.get("/", tags=["root"])
    def root() -> dict:
        return {
            "app": settings.app_name,
            "version": "0.1.0",
            "docs": "/docs",
            "metrics": "/metrics",
            "health": "/healthz",
            "ready": "/readyz",
        }

    log.info("app_started", env=settings.app_env, debug=settings.app_debug)
    return app


app = create_app()
