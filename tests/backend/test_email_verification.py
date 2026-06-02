"""
End-to-end tests for the email verification flow.

Brevo mailer is patched so no real network calls happen.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy import select

from backend.app.db.session import engine, get_db
from backend.app.models.email_verification_token import EmailVerificationToken
from backend.app.models.user import User


def _email() -> str:
    return f"pytest+{uuid.uuid4().hex[:12]}@cvpilot.dev"


@pytest.fixture()
def captured_verify_sends():
    sent: list[dict] = []

    def _fake(*, to_email, to_name, verify_url, ttl_min, mailer=None):
        sent.append(
            {
                "to_email": to_email,
                "to_name": to_name,
                "verify_url": verify_url,
                "ttl_min": ttl_min,
            }
        )
        return "fake-message-id"

    with patch(
        "backend.app.routes.auth.send_email_verification_email", side_effect=_fake
    ):
        yield sent


def _register(client, email: str, password: str = "S3cure!Passw0rd"):
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    assert r.status_code == 201, r.text
    return r.json()


def _login(client, email: str, password: str = "S3cure!Passw0rd") -> str:
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_register_dispatches_verification_email(client, captured_verify_sends):
    email = _email()
    _register(client, email)
    assert len(captured_verify_sends) == 1
    call = captured_verify_sends[0]
    assert call["to_email"] == email
    assert "/verify-email?token=" in call["verify_url"]
    assert call["ttl_min"] == 1440  # 24h default


def test_register_creates_unverified_user(client, captured_verify_sends):
    email = _email()
    body = _register(client, email)
    # UserPublic.email_verified should be False on a fresh register.
    assert body["email_verified"] is False


def test_me_reflects_unverified_state(client, captured_verify_sends):
    email = _email()
    _register(client, email)
    token = _login(client, email)
    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email_verified"] is False


def test_verify_email_invalid_token(client):
    r = client.post(
        "/api/v1/auth/verify-email",
        json={"token": "not-a-real-token-but-long-enough"},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_verification_token"


def test_verify_email_full_flow(client, captured_verify_sends):
    email = _email()
    _register(client, email)

    # Mint a token directly so we know its raw value.
    db = next(get_db())
    try:
        user = db.scalar(select(User).where(User.email == email))
        raw = "verify-" + uuid.uuid4().hex
        db.add(
            EmailVerificationToken(
                user_id=user.id,
                token_hash=hashlib.sha256(raw.encode()).hexdigest(),
                expires_at=datetime.now(UTC) + timedelta(hours=1),
            )
        )
        db.commit()
    finally:
        db.close()

    r = client.post("/api/v1/auth/verify-email", json={"token": raw})
    assert r.status_code == 200

    # /me should now report verified.
    access = _login(client, email)
    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert r.status_code == 200
    assert r.json()["email_verified"] is True

    # Token cannot be reused.
    r = client.post("/api/v1/auth/verify-email", json={"token": raw})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_verification_token"


def test_verify_email_expired_token_rejected(client, captured_verify_sends):
    email = _email()
    _register(client, email)

    db = next(get_db())
    try:
        user = db.scalar(select(User).where(User.email == email))
        raw = "expired-" + uuid.uuid4().hex
        db.add(
            EmailVerificationToken(
                user_id=user.id,
                token_hash=hashlib.sha256(raw.encode()).hexdigest(),
                expires_at=datetime.now(UTC) - timedelta(minutes=1),
            )
        )
        db.commit()
    finally:
        db.close()

    r = client.post("/api/v1/auth/verify-email", json={"token": raw})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_verification_token"


def test_send_verification_requires_auth(client):
    r = client.post("/api/v1/auth/send-verification")
    assert r.status_code == 401


def test_send_verification_resend_invalidates_old_token(client, captured_verify_sends):
    """Calling send-verification while a token is outstanding should mark the
    old one used (only the newest token works)."""
    email = _email()
    _register(client, email)
    access = _login(client, email)

    # The register already issued one token. Capture its hash from DB.
    with engine.connect() as conn:
        from sqlalchemy import text as _t

        first_hash = conn.execute(
            _t(
                """
                SELECT prt.token_hash FROM email_verification_tokens prt
                JOIN users u ON u.id = prt.user_id
                WHERE u.email = :e ORDER BY prt.created_at DESC LIMIT 1
                """
            ),
            {"e": email},
        ).scalar_one()

    # Ask for a resend.
    r = client.post(
        "/api/v1/auth/send-verification",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert r.status_code == 200

    # The first token should now be used.
    with engine.connect() as conn:
        from sqlalchemy import text as _t

        used_at = conn.execute(
            _t("SELECT used_at FROM email_verification_tokens WHERE token_hash = :h"),
            {"h": first_hash},
        ).scalar_one()
    assert used_at is not None


def test_send_verification_idempotent_when_already_verified(client, captured_verify_sends):
    """If the user is already verified, send-verification still returns 200
    but issues no token / no email."""
    email = _email()
    _register(client, email)

    # Mark verified directly.
    db = next(get_db())
    try:
        user = db.scalar(select(User).where(User.email == email))
        user.email_verified_at = datetime.now(UTC)
        db.commit()
    finally:
        db.close()

    access = _login(client, email)

    sends_before = len(captured_verify_sends)
    r = client.post(
        "/api/v1/auth/send-verification",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert r.status_code == 200
    # No new mail sent.
    assert len(captured_verify_sends) == sends_before
