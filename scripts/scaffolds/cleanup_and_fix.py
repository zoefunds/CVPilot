"""
1. Move all top-level scaffold_*.py / fix_*.py / update_*.py / patch_*.py /
   sync_*.py / wire_*.py / write_*.py / restore_*.py / cleanup_*.py files
   into scripts/scaffolds/ so the repo root is clean.
2. Patch tests/backend/conftest.py so the autouse cleanup only deletes data
   belonging to test users (pytest+...@cvpilot.dev). Your real data stays.
"""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
ARCHIVE = ROOT / "scripts/scaffolds"
ARCHIVE.mkdir(parents=True, exist_ok=True)

PREFIXES = (
    "scaffold_",
    "fix_",
    "update_",
    "patch_",
    "sync_",
    "wire_",
    "write_",
    "restore_",
    "cleanup_and_fix",  # don't move *this* script while it's running
)

moved = []
for p in sorted(ROOT.glob("*.py")):
    if p.name == "cleanup_and_fix.py":
        continue
    if any(p.name.startswith(prefix) for prefix in PREFIXES):
        target = ARCHIVE / p.name
        shutil.move(str(p), str(target))
        moved.append(p.name)
        print(f"  moved {p.name} -> scripts/scaffolds/")

print(f"\nMoved {len(moved)} files into scripts/scaffolds/")

# Write a small README explaining the folder.
(ARCHIVE / "README.md").write_text(
    """# scaffolds

Historical build scripts. Each one wrote code into the project at a specific
phase of construction. They are not part of the running app; they are the
recipe used to assemble it. Kept for traceability.

Newer code should live under the appropriate domain directory
(`backend/`, `frontend/`, `services/`, `workers/`, etc.). Do not add new
scaffolds here unless you are intentionally archiving build steps.
""",
    encoding="utf-8",
)
print("wrote scripts/scaffolds/README.md")

# ---- Fix conftest.py so pytest does not nuke real user data ----
CONFTEST = ROOT / "tests/backend/conftest.py"
CONFTEST.write_text(
    '''"""
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
''',
    encoding="utf-8",
)
print("patched tests/backend/conftest.py: test-data-only cleanup")
