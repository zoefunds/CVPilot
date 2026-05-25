"""
Admin endpoint smoke tests.
"""

from __future__ import annotations

import uuid

from sqlalchemy import text

from backend.app.db.session import engine


def _email() -> str:
    return f"pytest+{uuid.uuid4().hex[:12]}@cvpilot.dev"


def _register_and_token(client, *, promote: bool = False) -> tuple[str, str]:
    email = _email()
    password = "S3cure!Passw0rd"
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "T"},
    )
    assert r.status_code == 201, r.text

    if promote:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE users SET is_superuser = true WHERE email = :e"),
                {"e": email.lower()},
            )

    r = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert r.status_code == 200, r.text
    return email, r.json()["access_token"]


def test_admin_required_blocks_non_admin(client) -> None:
    _, token = _register_and_token(client, promote=False)
    r = client.get(
        "/api/v1/admin/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "admin_required"


def test_admin_can_view_stats(client) -> None:
    _, token = _register_and_token(client, promote=True)
    r = client.get(
        "/api/v1/admin/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    for key in (
        "user_count",
        "application_count",
        "evaluations_complete",
        "evaluations_failed",
        "last_24h_users",
        "last_24h_applications",
        "by_status",
    ):
        assert key in body


def test_admin_can_list_users(client) -> None:
    _, token = _register_and_token(client, promote=True)
    r = client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    users = r.json()
    assert isinstance(users, list)
    assert any(u.get("is_superuser") is True for u in users)


def test_admin_can_list_applications_empty(client) -> None:
    _, token = _register_and_token(client, promote=True)
    r = client.get(
        "/api/v1/admin/applications",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    assert r.json() == []


def test_admin_unauthenticated_blocked(client) -> None:
    r = client.get("/api/v1/admin/stats")
    assert r.status_code == 401
