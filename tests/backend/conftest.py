"""
Pytest fixtures for backend integration tests.
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
# Rate limiting is exercised manually; in tests it just causes 429s because
# the Redis backend persists counters across sessions for the testclient IP.
limiter.enabled = False


@pytest.fixture(scope="session", autouse=True)
def _ensure_schema() -> None:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def _cleanup_db() -> None:
    yield
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM evaluations"))
        conn.execute(text("DELETE FROM file_assets"))
        conn.execute(text("DELETE FROM applications"))
        conn.execute(text("DELETE FROM audit_logs"))
        conn.execute(text("DELETE FROM users WHERE email LIKE 'pytest+%@cvpilot.dev'"))
