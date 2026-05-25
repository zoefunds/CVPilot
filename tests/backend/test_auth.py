"""
End-to-end auth test: register -> login -> /me.
"""

from __future__ import annotations

import uuid


def _email() -> str:
    return f"pytest+{uuid.uuid4().hex[:12]}@cvpilot.dev"


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
