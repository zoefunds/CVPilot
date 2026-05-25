"""
CVPilot Phase 2 Backend Bootstrap
Writes the FastAPI backend skeleton:
  - requirements.txt
  - core/config.py (typed settings)
  - core/logging.py (structlog JSON)
  - core/errors.py (centralized exception handlers)
  - db/base.py, db/session.py (SQLAlchemy)
  - middleware/request_id.py
  - routes/health.py
  - main.py (app factory)
Pure stdlib. Idempotent.
"""

from __future__ import annotations
from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
BACKEND = ROOT / "backend"

FILES: dict[str, str] = {}

FILES["backend/requirements.txt"] = """fastapi==0.115.4
uvicorn[standard]==0.32.0
pydantic==2.9.2
pydantic-settings==2.6.1
SQLAlchemy==2.0.36
psycopg2-binary==2.9.10
alembic==1.13.3
python-dotenv==1.0.1
structlog==24.4.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
redis==5.2.0
celery==5.4.0
slowapi==0.1.9
httpx==0.27.2
python-multipart==0.0.12
email-validator==2.2.0
pytest==8.3.3
pytest-asyncio==0.24.0
ruff==0.7.2
black==24.10.0
"""

FILES["backend/__init__.py"] = ""
FILES["backend/app/__init__.py"] = ""
FILES["backend/app/core/__init__.py"] = ""
FILES["backend/app/db/__init__.py"] = ""
FILES["backend/app/middleware/__init__.py"] = ""
FILES["backend/app/routes/__init__.py"] = ""
FILES["backend/app/models/__init__.py"] = ""
FILES["backend/app/schemas/__init__.py"] = ""
FILES["backend/app/dependencies/__init__.py"] = ""
FILES["backend/app/utils/__init__.py"] = ""

FILES["backend/app/core/config.py"] = '''"""
Centralized typed settings.
Loaded once at import time from environment / .env.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    app_name: str = Field(default="CVPilot", alias="APP_NAME")
    app_env: Literal["development", "staging", "production"] = Field(
        default="development", alias="APP_ENV"
    )
    app_debug: bool = Field(default=True, alias="APP_DEBUG")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    app_secret_key: str = Field(default="change-me", alias="APP_SECRET_KEY")
    app_frontend_origin: str = Field(
        default="http://localhost:3000", alias="APP_FRONTEND_ORIGIN"
    )

    # --- Database ---
    database_url: PostgresDsn = Field(alias="DATABASE_URL")
    database_pool_size: int = Field(default=10, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, alias="DATABASE_MAX_OVERFLOW")

    # --- Redis ---
    redis_url: RedisDsn = Field(alias="REDIS_URL")

    # --- Celery ---
    celery_broker_url: str = Field(alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(alias="CELERY_RESULT_BACKEND")

    # --- JWT ---
    jwt_secret: str = Field(default="change-me", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expires_min: int = Field(default=30, alias="JWT_ACCESS_TOKEN_EXPIRES_MIN")
    jwt_refresh_token_expires_days: int = Field(default=7, alias="JWT_REFRESH_TOKEN_EXPIRES_DAYS")

    # --- Storage ---
    storage_backend: Literal["local", "s3"] = Field(default="local", alias="STORAGE_BACKEND")
    storage_local_path: str = Field(default="./storage/uploads", alias="STORAGE_LOCAL_PATH")
    storage_max_upload_mb: int = Field(default=10, alias="STORAGE_MAX_UPLOAD_MB")

    # --- Rate limit ---
    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")
    rate_limit_burst: int = Field(default=20, alias="RATE_LIMIT_BURST")

    # --- GenLayer ---
    genlayer_studionet_rpc: str = Field(
        default="https://studio.genlayer.com/api", alias="GENLAYER_STUDIONET_RPC"
    )
    genlayer_account_private_key: str = Field(default="", alias="GENLAYER_ACCOUNT_PRIVATE_KEY")
    genlayer_contract_address: str = Field(default="", alias="GENLAYER_CONTRACT_ADDRESS")
    genlayer_llm_model: str = Field(default="default", alias="GENLAYER_LLM_MODEL")

    # --- Logging ---
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_json: bool = Field(default=True, alias="LOG_JSON")

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
'''

FILES["backend/app/core/logging.py"] = '''"""
Structured logging configuration using structlog.
JSON output in production, pretty output in dev.
"""

from __future__ import annotations

import logging
import sys

import structlog

from backend.app.core.config import settings


def configure_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.log_json:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name) if name else structlog.get_logger()
'''

FILES["backend/app/core/errors.py"] = '''"""
Centralized error handling.
Defines an AppError base, and FastAPI exception handlers
that emit consistent JSON envelopes and never leak internals.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.core.logging import get_logger

log = get_logger("errors")


class AppError(Exception):
    """Base application error. Always safe to surface."""

    status_code: int = 400
    code: str = "app_error"

    def __init__(self, message: str, *, code: str | None = None, details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        self.details = details


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"


class ValidationAppError(AppError):
    status_code = 422
    code = "validation_error"


class RateLimitError(AppError):
    status_code = 429
    code = "rate_limited"


def _envelope(code: str, message: str, *, details: Any = None) -> dict:
    body: dict = {"error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return body


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        log.warning(
            "app_error",
            code=exc.code,
            message=exc.message,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(exc.code, exc.message, details=exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        log.info("validation_error", path=request.url.path, errors=exc.errors())
        return JSONResponse(
            status_code=422,
            content=_envelope(
                "validation_error",
                "Invalid request payload.",
                details=exc.errors(),
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        log.info("http_error", status=exc.status_code, path=request.url.path)
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope("http_error", str(exc.detail)),
        )

    @app.exception_handler(Exception)
    async def _unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled_exception", path=request.url.path)
        return JSONResponse(
            status_code=500,
            content=_envelope("internal_error", "An unexpected error occurred."),
        )
'''

FILES["backend/app/db/base.py"] = '''"""
SQLAlchemy declarative base + common mixins.
All ORM models import Base from here.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# Naming convention so Alembic produces stable constraint names.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
'''

FILES["backend/app/db/session.py"] = '''"""
SQLAlchemy engine + session factory.
Provides a FastAPI dependency `get_db` for request-scoped sessions.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import settings

engine = create_engine(
    str(settings.database_url),
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ping_db() -> bool:
    """Lightweight DB connectivity check used by /readyz."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
'''

FILES["backend/app/middleware/request_id.py"] = '''"""
Request-ID middleware.
Assigns a UUID per request, binds it into structlog contextvars,
and echoes it back as X-Request-ID for client correlation.
"""

from __future__ import annotations

import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get(HEADER) or uuid.uuid4().hex
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=rid,
            method=request.method,
            path=request.url.path,
        )
        response: Response = await call_next(request)
        response.headers[HEADER] = rid
        return response
'''

FILES["backend/app/routes/health.py"] = '''"""
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
'''

FILES["backend/app/main.py"] = '''"""
FastAPI application factory.
Wires logging, middleware, CORS, error handlers, and routers.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.core.errors import register_exception_handlers
from backend.app.core.logging import configure_logging, get_logger
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

    # Middleware
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

    @app.get("/", tags=["root"])
    def root() -> dict:
        return {"app": settings.app_name, "version": "0.1.0", "docs": "/docs"}

    log.info("app_started", env=settings.app_env, debug=settings.app_debug)
    return app


app = create_app()
'''


def write(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  wrote {rel}")


def main() -> None:
    print(f"Phase 2 backend bootstrap into: {ROOT}")
    for rel, content in FILES.items():
        write(rel, content)
    print("\nPhase 2 files written.")


if __name__ == "__main__":
    main()
