"""
End-to-end test for the Evaluation pipeline (v0.3.1 schema).
"""

from __future__ import annotations

import io
import uuid

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas


def _pdf_bytes() -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    c.setFont("Helvetica", 12)
    lines = [
        "Jane Doe Senior Python Engineer",
        "Led FastAPI service rebuild reducing P95 latency by 38%.",
        "Shipped Kubernetes migration for 22 microservices.",
        "Designed Postgres partitioning scheme for 5B rows.",
        "Mentored 4 engineers; team velocity grew 2x.",
        "jane@example.com  +1 202 555 0100",
    ]
    y = 720
    for ln in lines:
        c.drawString(72, y, ln)
        y -= 18
    c.showPage()
    c.save()
    return buf.getvalue()


def _email() -> str:
    return f"pytest+{uuid.uuid4().hex[:12]}@cvpilot.dev"


def _register_and_token(client) -> str:
    email = _email()
    password = "S3cure!Passw0rd"
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    assert r.status_code == 201, r.text
    r = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _create_application(client, token: str) -> str:
    cover = (
        "Dear Hiring Team,\n"
        "I am thrilled to apply for the Senior Python Engineer role.\n"
        "Best,\nJane"
    )
    r = client.post(
        "/api/v1/applications",
        files={
            "cv": ("cv.pdf", _pdf_bytes(), "application/pdf"),
            "cover_letter": ("cover.txt", cover.encode("utf-8"), "text/plain"),
        },
        data={
            "job_url": "https://example.com/",
            "linkedin_url": "https://www.linkedin.com/in/example/",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 202, r.text
    return r.json()["id"]


def test_evaluation_autoruns_after_parse(client) -> None:
    token = _register_and_token(client)
    app_id = _create_application(client, token)

    r = client.get(
        f"/api/v1/applications/{app_id}/evaluation",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    ev = r.json()
    assert ev["status"] == "complete", ev
    assert ev["backend"] == "stub"
    for key in (
        "cv_score",
        "cover_letter_score",
        "job_match_score",
        "ats_score",
        "competitiveness_score",
        "overall_score",
    ):
        assert isinstance(ev[key], int) and 0 <= ev[key] <= 100, (key, ev[key])
    for list_key in ("strengths", "risks", "recommendations", "missing_keywords"):
        assert isinstance(ev[list_key], list)
    assert ev["summary"]


def test_get_evaluation_404_before_creation(client) -> None:
    token = _register_and_token(client)
    r = client.get(
        f"/api/v1/applications/{uuid.uuid4()}/evaluation",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 404


def test_evaluation_idempotent_retrigger(client) -> None:
    token = _register_and_token(client)
    app_id = _create_application(client, token)
    r1 = client.post(
        f"/api/v1/applications/{app_id}/evaluate",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r1.status_code == 202, r1.text
    r2 = client.post(
        f"/api/v1/applications/{app_id}/evaluate",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 202, r2.text
    assert r1.json()["id"] == r2.json()["id"]


def test_evaluation_owner_isolation(client) -> None:
    token_a = _register_and_token(client)
    token_b = _register_and_token(client)
    app_id = _create_application(client, token_a)
    r = client.get(
        f"/api/v1/applications/{app_id}/evaluation",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert r.status_code == 403
