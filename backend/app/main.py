"""
FastAPI application factory.
Wires logging, middleware, CORS, error handlers, rate limiter, and routers.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.v1.router import api_router
from backend.app.core.config import settings
from backend.app.core.errors import register_exception_handlers
from backend.app.core.logging import configure_logging, get_logger
from backend.app.dependencies.rate_limit import limiter
from backend.app.middleware.request_id import RequestIDMiddleware
from backend.app.routes import health


def create_app() -> FastAPI:
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

    # Rate limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # Other middleware
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.app_frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # Errors
    register_exception_handlers(app)

    # Routes
    app.include_router(health.router)
    app.include_router(api_router)

    @app.get("/", tags=["root"])
    def root() -> dict:
        return {"app": settings.app_name, "version": "0.1.0", "docs": "/docs"}

    log.info("app_started", env=settings.app_env, debug=settings.app_debug)
    return app


app = create_app()
