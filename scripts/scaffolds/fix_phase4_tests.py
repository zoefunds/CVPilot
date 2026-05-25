"""
Rewrite tests/backend/test_applications.py with a reportlab-based PDF
fixture so extract_text() finds real on-page text.
"""

from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
TARGET = ROOT / "tests/backend/test_applications.py"

NEW = '''"""
End-to-end test for the Applications API.
Builds a real text-bearing PDF via reportlab so pypdf.extract_text()
finds real content (not just metadata).
"""

from __future__ import annotations

import io
import uuid

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas


def _pdf_bytes(body: str = "Senior Python Engineer with 8 years experience in FastAPI, Postgres, and Kubernetes.") -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    c.setFont("Helvetica", 12)
    y = 720
    for line in body.splitlines() or [body]:
        c.drawString(72, y, line)
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


def test_create_application_happy_path(client) -> None:
    token = _register_and_token(client)

    cover_letter_text = (
        "Dear Hiring Team,\\n"
        "I am thrilled to apply for this role. My background in Python and\\n"
        "distributed systems aligns directly with your needs.\\n"
        "Best,\\nA Candidate"
    )

    files = {
        "cv": ("cv.pdf", _pdf_bytes(), "application/pdf"),
        "cover_letter": ("cover.txt", cover_letter_text.encode("utf-8"), "text/plain"),
    }
    data = {
        "job_url": "https://example.com/",
        "linkedin_url": "https://www.linkedin.com/in/example/",
        "portfolio_url": "https://example.com/portfolio",
    }

    r = client.post(
        "/api/v1/applications",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 202, r.text
    body = r.json()
    app_id = body["id"]
    assert len(body["files"]) == 2

    r2 = client.get(
        f"/api/v1/applications/{app_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 200, r2.text
    final = r2.json()
    assert final["status"] == "ready", final
    assert final["job_text"], "job_text should be populated after fetch"
    assert all(f["extracted_text"] for f in final["files"]), final["files"]


def test_create_application_rejects_bad_job_url(client) -> None:
    token = _register_and_token(client)
    files = {
        "cv": ("cv.pdf", _pdf_bytes(), "application/pdf"),
        "cover_letter": ("cover.txt", b"hello world", "text/plain"),
    }
    r = client.post(
        "/api/v1/applications",
        files=files,
        data={"job_url": "ftp://nope.invalid"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "job_url_invalid"


def test_list_and_isolation(client) -> None:
    token_a = _register_and_token(client)
    token_b = _register_and_token(client)

    r = client.post(
        "/api/v1/applications",
        files={
            "cv": ("cv.pdf", _pdf_bytes(), "application/pdf"),
            "cover_letter": ("c.txt", b"hello world", "text/plain"),
        },
        data={"job_url": "https://example.com/"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert r.status_code == 202, r.text
    app_id = r.json()["id"]

    r = client.get(
        f"/api/v1/applications/{app_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert r.status_code == 403

    r = client.get(
        "/api/v1/applications",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert r.status_code == 200
    assert r.json() == []


def test_unauthenticated_rejected(client) -> None:
    r = client.get("/api/v1/applications")
    assert r.status_code == 401
'''


def main() -> None:
    TARGET.write_text(NEW, encoding="utf-8")
    print(f"patched {TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
