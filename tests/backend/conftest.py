"""
Pytest fixtures for backend integration tests.

The autouse cleanup ONLY removes data created by test users (emails matching
pytest+...@cvpilot.dev). Your founder account and any real evaluations are
left untouched, so running the test suite no longer wipes live data.
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
os.environ.setdefault("LLM_BACKEND", "stub")
os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"

from backend.app.db.session import engine  # noqa: E402
from backend.app.dependencies.rate_limit import limiter  # noqa: E402
from backend.app.main import app  # noqa: E402

# Disable the slowapi limiter for the entire test session.
limiter.enabled = False


@pytest.fixture(scope="session", autouse=True)
def _ensure_schema() -> None:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def _cleanup_test_data() -> None:
    """Remove only test artefacts (emails like pytest+...@cvpilot.dev).
    Real user data is preserved across test runs."""
    yield
    with engine.begin() as conn:
        # Evaluations belonging to test users.
        conn.execute(
            text("""
                DELETE FROM evaluations
                WHERE application_id IN (
                    SELECT a.id
                    FROM applications a
                    JOIN users u ON u.id = a.user_id
                    WHERE u.email LIKE 'pytest+%@cvpilot.dev'
                )
            """)
        )
        # File assets belonging to test users.
        conn.execute(
            text("""
                DELETE FROM file_assets
                WHERE application_id IN (
                    SELECT a.id
                    FROM applications a
                    JOIN users u ON u.id = a.user_id
                    WHERE u.email LIKE 'pytest+%@cvpilot.dev'
                )
            """)
        )
        # Applications belonging to test users.
        conn.execute(
            text("""
                DELETE FROM applications
                WHERE user_id IN (
                    SELECT id FROM users WHERE email LIKE 'pytest+%@cvpilot.dev'
                )
            """)
        )
        # Audit logs of test users.
        conn.execute(
            text("""
                DELETE FROM audit_logs
                WHERE user_id IN (
                    SELECT id FROM users WHERE email LIKE 'pytest+%@cvpilot.dev'
                )
            """)
        )
        # The test users themselves.
        conn.execute(
            text("DELETE FROM users WHERE email LIKE 'pytest+%@cvpilot.dev'")
        )
