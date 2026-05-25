"""
CVPilot Phase 3: Auth (User, JWT, bcrypt), Alembic, Rate Limiting, /api/v1 router.
Idempotent. Writes files only.
"""

from __future__ import annotations
from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")

FILES: dict[str, str] = {}

# ---------- core/security.py ----------
FILES["backend/app/core/security.py"] = '''"""
Password hashing (bcrypt via passlib) + JWT issuance/verification.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.app.core.config import settings
from backend.app.core.errors import UnauthorizedError

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

TokenType = Literal["access", "refresh"]


def hash_password(plain: str) -> str:
    return _pwd.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _pwd.verify(plain, hashed)
    except ValueError:
        return False


def _create_token(subject: str, ttl: timedelta, token_type: TokenType, extra: dict[str, Any] | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + ttl).timestamp()),
        "type": token_type,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    return _create_token(
        subject,
        timedelta(minutes=settings.jwt_access_token_expires_min),
        "access",
        extra,
    )


def create_refresh_token(subject: str) -> str:
    return _create_token(
        subject,
        timedelta(days=settings.jwt_refresh_token_expires_days),
        "refresh",
    )


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise UnauthorizedError("Invalid or expired token.") from exc
    if payload.get("type") != expected_type:
        raise UnauthorizedError("Wrong token type.")
    if "sub" not in payload:
        raise UnauthorizedError("Token missing subject.")
    return payload
'''

# ---------- models/user.py ----------
FILES["backend/app/models/user.py"] = '''"""
User ORM model.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
'''

# ---------- models/audit_log.py ----------
FILES["backend/app/models/audit_log.py"] = '''"""
AuditLog ORM model. Append-only event trail.
"""

from __future__ import annotations

import uuid

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    event: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
'''

# ---------- models/__init__.py (re-export) ----------
FILES["backend/app/models/__init__.py"] = '''"""
Import all models here so Alembic autogenerate detects them.
"""

from backend.app.models.user import User  # noqa: F401
from backend.app.models.audit_log import AuditLog  # noqa: F401
'''

# ---------- schemas/auth.py ----------
FILES["backend/app/schemas/auth.py"] = '''"""
Auth request/response schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
'''

# ---------- schemas/user.py ----------
FILES["backend/app/schemas/user.py"] = '''"""
Public user shape returned to clients.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    is_active: bool
    is_premium: bool
    created_at: datetime
'''

# ---------- dependencies/auth.py ----------
FILES["backend/app/dependencies/auth.py"] = '''"""
FastAPI dependency: extract user from Authorization: Bearer <jwt>.
"""

from __future__ import annotations

import uuid

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.core.errors import UnauthorizedError
from backend.app.core.security import decode_token
from backend.app.db.session import get_db
from backend.app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise UnauthorizedError("Missing bearer token.")
    payload = decode_token(token, expected_type="access")
    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise UnauthorizedError("Malformed token subject.") from exc

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or inactive.")
    return user
'''

# ---------- dependencies/rate_limit.py ----------
FILES["backend/app/dependencies/rate_limit.py"] = '''"""
SlowAPI rate limiter, backed by Redis.
Use as a router/endpoint decorator: @limiter.limit("5/minute")
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.app.core.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=str(settings.redis_url),
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
    headers_enabled=True,
)
'''

# ---------- routes/auth.py ----------
FILES["backend/app/routes/auth.py"] = '''"""
Auth routes: register, login, refresh, me.
All write paths emit audit log rows.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.errors import UnauthorizedError, ValidationAppError
from backend.app.core.logging import get_logger
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from backend.app.db.session import get_db
from backend.app.dependencies.auth import get_current_user
from backend.app.dependencies.rate_limit import limiter
from backend.app.models.audit_log import AuditLog
from backend.app.models.user import User
from backend.app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenPair
from backend.app.schemas.user import UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])
log = get_logger("auth")


def _audit(db: Session, *, user_id, event: str, request: Request, payload: dict | None = None) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            event=event,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            payload=payload,
        )
    )


@router.post("/register", response_model=UserPublic, status_code=201)
@limiter.limit("5/minute")
def register(
    request: Request,
    body: RegisterRequest,
    db: Session = Depends(get_db),
) -> UserPublic:
    existing = db.scalar(select(User).where(User.email == body.email.lower()))
    if existing is not None:
        raise ValidationAppError("Email already registered.", code="email_taken")

    user = User(
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        full_name=body.full_name,
    )
    db.add(user)
    db.flush()
    _audit(db, user_id=user.id, event="user.registered", request=request)
    db.commit()
    db.refresh(user)
    log.info("user_registered", user_id=str(user.id))
    return UserPublic.model_validate(user)


@router.post("/login", response_model=TokenPair)
@limiter.limit("10/minute")
def login(
    request: Request,
    body: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenPair:
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not verify_password(body.password, user.password_hash):
        # Audit failed attempts without revealing which side failed.
        _audit(
            db,
            user_id=user.id if user else None,
            event="user.login_failed",
            request=request,
            payload={"email": body.email.lower()},
        )
        db.commit()
        raise UnauthorizedError("Invalid email or password.", code="invalid_credentials")
    if not user.is_active:
        raise UnauthorizedError("Account is disabled.", code="account_disabled")

    pair = TokenPair(
        access_token=create_access_token(str(user.id), extra={"premium": user.is_premium}),
        refresh_token=create_refresh_token(str(user.id)),
    )
    _audit(db, user_id=user.id, event="user.login", request=request)
    db.commit()
    log.info("user_login", user_id=str(user.id))
    return pair


@router.post("/refresh", response_model=TokenPair)
@limiter.limit("30/minute")
def refresh(
    request: Request,
    body: RefreshRequest,
    db: Session = Depends(get_db),
) -> TokenPair:
    payload = decode_token(body.refresh_token, expected_type="refresh")
    user_id = payload["sub"]
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("User no longer valid.")
    return TokenPair(
        access_token=create_access_token(str(user.id), extra={"premium": user.is_premium}),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.get("/me", response_model=UserPublic)
def me(current_user: User = Depends(get_current_user)) -> UserPublic:
    return UserPublic.model_validate(current_user)
'''

# ---------- api/v1 ----------
FILES["api/__init__.py"] = ""
FILES["api/v1/__init__.py"] = ""
FILES["api/v1/router.py"] = '''"""
Versioned API router aggregator. Mounted at /api/v1 in main.py.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.routes import auth

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
'''

# ---------- main.py (updated) ----------
FILES["backend/app/main.py"] = '''"""
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
'''

# ---------- Alembic ----------
FILES["backend/alembic.ini"] = '''# Alembic configuration for CVPilot.
# The DB URL is injected from settings at runtime in env.py.
[alembic]
script_location = backend/app/db/migrations_env
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url =

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
'''

FILES["backend/app/db/migrations_env/__init__.py"] = ""
FILES["backend/app/db/migrations_env/versions/.gitkeep"] = ""

FILES["backend/app/db/migrations_env/env.py"] = '''"""
Alembic environment. Loads SQLAlchemy URL from app settings,
imports models so autogenerate detects them.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from backend.app.core.config import settings
from backend.app.db.base import Base
import backend.app.models  # noqa: F401  (register models)

config = context.config
config.set_main_option("sqlalchemy.url", str(settings.database_url))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=str(settings.database_url),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''

FILES["backend/app/db/migrations_env/script.py.mako"] = '''"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
'''

# ---------- tests ----------
FILES["tests/__init__.py"] = ""
FILES["tests/backend/__init__.py"] = ""

FILES["tests/backend/conftest.py"] = '''"""
Pytest fixtures for backend integration tests.
Uses the real DB defined in .env (cvpilot/cvpilot).
Each test runs in a transaction that is rolled back via a clean-up step.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("APP_ENV", "development")

from backend.app.db.session import engine  # noqa: E402
from backend.app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _ensure_schema() -> None:
    # Alembic migrations must have been run before tests.
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def _cleanup_users() -> None:
    yield
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM audit_logs"))
        conn.execute(text("DELETE FROM users WHERE email LIKE 'pytest+%@cvpilot.test'"))
'''

FILES["tests/backend/test_auth.py"] = '''"""
End-to-end auth test: register -> login -> /me.
"""

from __future__ import annotations

import uuid


def _email() -> str:
    return f"pytest+{uuid.uuid4().hex[:12]}@cvpilot.test"


def test_register_login_me(client) -> None:
    email = _email()
    password = "S3cure!Passw0rd"

    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["email"] == email
    assert body["is_active"] is True

    r = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert r.status_code == 200, r.text
    tokens = r.json()
    access = tokens["access_token"]
    assert tokens["token_type"] == "bearer"

    r = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["email"] == email


def test_login_wrong_password(client) -> None:
    email = _email()
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "S3cure!Passw0rd"},
    )
    r = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "wrong-password"},
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "invalid_credentials"


def test_me_requires_auth(client) -> None:
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401
'''


def write(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  wrote {rel}")


def main() -> None:
    print(f"Phase 3 into: {ROOT}")
    for rel, content in FILES.items():
        write(rel, content)
    print("\nPhase 3 files written.")


if __name__ == "__main__":
    main()
