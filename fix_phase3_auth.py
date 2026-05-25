"""
Fix Phase 3 bug:
slowapi's @limiter.limit decorator + `from __future__ import annotations`
breaks FastAPI's forward-ref resolution in backend/app/routes/auth.py.

Rewrite that one file with real (non-string) type hints.
"""

from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
TARGET = ROOT / "backend/app/routes/auth.py"

NEW = '''"""
Auth routes: register, login, refresh, me.
All write paths emit audit log rows.
Note: deliberately NO `from __future__ import annotations` here,
because slowapi wraps these handlers and FastAPI cannot resolve
forward-ref strings against slowapi's module globals.
"""

from typing import Optional

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


def _audit(
    db: Session,
    *,
    user_id,
    event: str,
    request: Request,
    payload: Optional[dict] = None,
) -> None:
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
):
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
):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not verify_password(body.password, user.password_hash):
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
):
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
def me(current_user: User = Depends(get_current_user)):
    return UserPublic.model_validate(current_user)
'''


def main() -> None:
    TARGET.write_text(NEW, encoding="utf-8")
    print(f"patched {TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
