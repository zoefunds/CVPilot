"""
Password hashing (bcrypt, called directly) + JWT issuance/verification.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import bcrypt
from jose import JWTError, jwt

from backend.app.core.config import settings
from backend.app.core.errors import UnauthorizedError

# bcrypt only considers the first 72 bytes of a secret. Truncate explicitly
# to match Django/Devise behavior and to keep verification stable for any
# password length we allow at the schema layer.
_BCRYPT_MAX_BYTES = 72

TokenType = Literal["access", "refresh"]


def _to_bcrypt_secret(plain: str) -> bytes:
    return plain.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(plain: str) -> str:
    hashed = bcrypt.hashpw(_to_bcrypt_secret(plain), bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_to_bcrypt_secret(plain), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _create_token(
    subject: str,
    ttl: timedelta,
    token_type: TokenType,
    extra: dict[str, Any] | None = None,
) -> str:
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
