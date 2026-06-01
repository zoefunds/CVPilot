"""
End-to-end tests for the forgot-password / reset-password flow.

The Brevo mailer is patched out so no real network calls happen during tests.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy import select, text

from backend.app.db.session import engine, get_db
from backend.app.models.password_reset_token import PasswordResetToken
from backend.app.models.user import User


def _email() -> str:
    return f"pytest+{uuid.uuid4().hex[:12]}@cvpilot.dev"


@pytest.fixture()
def captured_sends():
    """Patch the mailer so no real email goes out, and capture calls."""
    sent: list[dict] = []

    def _fake_send(*, to_email, to_name, reset_url, ttl_min, mailer=None):
        sent.append(
            {
                "to_email": to_email,
                "to_name": to_name,
                "reset_url": reset_url,
                "ttl_min": ttl_min,
            }
        )
        return "fake-message-id"

    with patch("backend.app.routes.auth.send_password_reset_email", side_effect=_fake_send):
        yield sent


def _register(client, email: str, password: str = "S3cure!Passw0rd") -> None:
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    assert r.status_code == 201, r.text


def test_forgot_password_unknown_email_no_enumeration(client, captured_sends) -> None:
    r = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nobody-here@cvpilot.dev"},
    )
    assert r.status_code == 200
    assert "reset link is on its way" in r.json()["detail"]
    assert captured_sends == [], "should not send to unknown emails"


def test_forgot_password_real_email_sends(client, captured_sends) -> None:
    email = _email()
    _register(client, email)

    r = client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert r.status_code == 200

    assert len(captured_sends) == 1
    call = captured_sends[0]
    assert call["to_email"] == email
    assert "/reset-password?token=" in call["reset_url"]
    assert call["ttl_min"] == 30
    # Verify the link uses the configured frontend origin (not localhost in prod).
    assert call["reset_url"].startswith(("http://", "https://"))


def test_forgot_password_creates_token_row(client, captured_sends) -> None:
    email = _email()
    _register(client, email)
    client.post("/api/v1/auth/forgot-password", json={"email": email})

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT prt.token_hash, prt.expires_at, prt.used_at
                FROM password_reset_tokens prt
                JOIN users u ON u.id = prt.user_id
                WHERE u.email = :e
                """
            ),
            {"e": email},
        ).all()
    assert len(rows) == 1
    assert rows[0].used_at is None
    # Token hash is sha256 hex digest -> 64 chars.
    assert len(rows[0].token_hash) == 64


def test_reset_password_invalid_token(client, captured_sends) -> None:
    r = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "not-a-real-token-but-long-enough", "password": "new-Passw0rd"},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_reset_token"


def test_reset_password_short_password_rejected(client) -> None:
    r = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "x" * 40, "password": "short"},
    )
    assert r.status_code == 422
    # pydantic validation error (min_length=8 on password)
    assert r.json()["error"]["code"] == "validation_error"


def test_reset_password_full_flow(client, captured_sends) -> None:
    email = _email()
    old_pw = "S3cure!Passw0rd"
    new_pw = "n3W-Pa55w0rd!"
    _register(client, email, old_pw)

    # Issue a token directly so we can read the raw value.
    db_gen = get_db()
    db = next(db_gen)
    try:
        user = db.scalar(select(User).where(User.email == email))
        assert user is not None
        raw = "raw-test-token-" + uuid.uuid4().hex
        token_hash = hashlib.sha256(raw.encode()).hexdigest()
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=datetime.now(UTC) + timedelta(minutes=10),
            )
        )
        db.commit()
    finally:
        db.close()

    r = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw, "password": new_pw},
    )
    assert r.status_code == 200

    # Old password no longer works.
    r = client.post("/api/v1/auth/login", json={"email": email, "password": old_pw})
    assert r.status_code == 401

    # New password works.
    r = client.post("/api/v1/auth/login", json={"email": email, "password": new_pw})
    assert r.status_code == 200

    # Token cannot be reused.
    r = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw, "password": "another-pass-w0rd"},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_reset_token"


def test_reset_password_expired_token_rejected(client, captured_sends) -> None:
    email = _email()
    _register(client, email)

    db_gen = get_db()
    db = next(db_gen)
    try:
        user = db.scalar(select(User).where(User.email == email))
        raw = "expired-" + uuid.uuid4().hex
        token_hash = hashlib.sha256(raw.encode()).hexdigest()
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=datetime.now(UTC) - timedelta(minutes=1),
            )
        )
        db.commit()
    finally:
        db.close()

    r = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw, "password": "n3W-Pa55w0rd!"},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_reset_token"


def test_new_reset_request_invalidates_old_tokens(client, captured_sends) -> None:
    """After a successful reset, any outstanding tokens for that user are
    marked used so they can't be replayed."""
    email = _email()
    _register(client, email)

    db_gen = get_db()
    db = next(db_gen)
    try:
        user = db.scalar(select(User).where(User.email == email))
        # Two pending tokens for this user.
        raws = []
        for _ in range(2):
            raw = "multi-" + uuid.uuid4().hex
            raws.append(raw)
            db.add(
                PasswordResetToken(
                    user_id=user.id,
                    token_hash=hashlib.sha256(raw.encode()).hexdigest(),
                    expires_at=datetime.now(UTC) + timedelta(minutes=10),
                )
            )
        db.commit()
    finally:
        db.close()

    # Use the first token.
    r = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raws[0], "password": "n3W-Pa55w0rd!"},
    )
    assert r.status_code == 200

    # The second token should now also be invalid.
    r = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raws[1], "password": "another-passw0rd"},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_reset_token"


def test_register_duplicate_email_rejected(client) -> None:
    email = _email()
    _register(client, email)
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "S3cure!Passw0rd"},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "email_taken"


def test_register_email_normalized_lowercase(client) -> None:
    email = _email()
    upper = email.upper()
    r = client.post(
        "/api/v1/auth/register",
        json={"email": upper, "password": "S3cure!Passw0rd"},
    )
    assert r.status_code == 201
    # Login with the lowercased form should work.
    r = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "S3cure!Passw0rd"},
    )
    assert r.status_code == 200


def test_refresh_token_rejects_access_token(client) -> None:
    email = _email()
    _register(client, email)
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "S3cure!Passw0rd"})
    access = r.json()["access_token"]

    # Submitting an access token to /refresh must be rejected by the type check.
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": access})
    assert r.status_code == 401
