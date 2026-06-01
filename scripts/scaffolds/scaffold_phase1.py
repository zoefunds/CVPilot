"""
CVPilot Phase 1 Scaffolder
Creates the full production folder structure, .gitignore, .env.example,
README.md, and pyproject.toml. Pure stdlib, no installs.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")

DIRECTORIES = [
    "backend",
    "backend/app",
    "backend/app/core",
    "backend/app/models",
    "backend/app/schemas",
    "backend/app/routes",
    "backend/app/dependencies",
    "backend/app/middleware",
    "backend/app/db",
    "backend/app/db/migrations",
    "backend/app/utils",
    "api",
    "api/v1",
    "frontend",
    "frontend/src",
    "frontend/src/app",
    "frontend/src/components",
    "frontend/src/components/ui",
    "frontend/src/components/layout",
    "frontend/src/components/dashboard",
    "frontend/src/components/analysis",
    "frontend/src/lib",
    "frontend/src/hooks",
    "frontend/src/types",
    "frontend/src/styles",
    "frontend/public",
    "contracts",
    "contracts/cvpilot",
    "contracts/deploy",
    "contracts/abis",
    "services",
    "services/scoring",
    "services/ats",
    "services/evaluation",
    "services/parsing",
    "services/genlayer",
    "services/contract_bridge",
    "workers",
    "workers/tasks",
    "workers/queues",
    "security",
    "security/rate_limit",
    "security/validation",
    "security/auth",
    "security/audit",
    "analytics",
    "analytics/events",
    "analytics/aggregations",
    "monitoring",
    "monitoring/health",
    "monitoring/logging",
    "monitoring/metrics",
    "storage",
    "storage/local",
    "storage/uploads",
    "storage/processed",
    "shared",
    "shared/types",
    "shared/enums",
    "shared/constants",
    "shared/dto",
    "tests",
    "tests/backend",
    "tests/frontend",
    "tests/integration",
    "tests/contracts",
    "scripts",
    "scripts/dev",
    "scripts/deploy",
    "scripts/db",
    "configs",
    "configs/dev",
    "configs/prod",
    "configs/staging",
    "docs",
    "docs/architecture",
    "docs/api",
    "docs/contracts",
    "docs/runbooks",
]

GITIGNORE = """# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
.env
.env.local
.env.*.local

# Node / Next.js
node_modules/
.next/
out/
.turbo/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# OS
.DS_Store
Thumbs.db

# IDE
.idea/
.vscode/

# Storage (keep folders, ignore contents)
storage/uploads/*
storage/processed/*
!storage/uploads/.gitkeep
!storage/processed/.gitkeep

# Logs
logs/
*.log

# Coverage / tests
.coverage
.pytest_cache/
htmlcov/
coverage/

# Build artifacts
dist/
build/
"""

ENV_EXAMPLE = """# ---------------------------------------------------------
# CVPilot Environment Variables (example)
# Copy to .env and fill in real values.
# ---------------------------------------------------------

# --- App ---
APP_NAME=CVPilot
APP_ENV=development
APP_DEBUG=true
APP_HOST=0.0.0.0
APP_PORT=8000
APP_SECRET_KEY=change-me-to-a-long-random-string
APP_FRONTEND_ORIGIN=http://localhost:3000

# --- Database (PostgreSQL) ---
DATABASE_URL=postgresql+psycopg2://cvpilot:cvpilot@localhost:5432/cvpilot
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# --- Redis ---
REDIS_URL=redis://localhost:6379/0

# --- Celery ---
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# --- JWT ---
JWT_SECRET=change-me-to-a-long-random-string
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRES_MIN=30
JWT_REFRESH_TOKEN_EXPIRES_DAYS=7

# --- Storage ---
STORAGE_BACKEND=local
STORAGE_LOCAL_PATH=./storage/uploads
STORAGE_MAX_UPLOAD_MB=10

# --- Rate limit ---
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=20

# --- GenLayer ---
GENLAYER_STUDIONET_RPC=https://studio.genlayer.com/api
GENLAYER_ACCOUNT_PRIVATE_KEY=
GENLAYER_CONTRACT_ADDRESS=
GENLAYER_LLM_MODEL=default

# --- Frontend (Next.js) ---
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_NAME=CVPilot
NEXT_PUBLIC_BRAND_COLOR=#efece4

# --- Logging ---
LOG_LEVEL=INFO
LOG_JSON=true
"""

README = """# CVPilot

AI Job Application Intelligence Platform.

CVPilot evaluates CVs, cover letters, and job descriptions using the
GenLayer Intelligent Contracts + LLM stack, returning transparent and
verifiable scoring plus actionable recommendations.

## Stack

- Frontend: Next.js + TypeScript + TailwindCSS (brand color `#efece4`)
- Backend: FastAPI + SQLAlchemy + PostgreSQL
- Cache: Redis
- Queue: Celery
- AI: GenLayer LLM
- Blockchain: GenLayer Intelligent Contracts (StudioNet)

## Project layout

See `docs/architecture/` for the full architecture overview.

## Quick start

Setup is incremental. See `docs/runbooks/setup.md` (added in Phase 2).
"""

PYPROJECT = """[project]
name = "cvpilot"
version = "0.1.0"
description = "CVPilot - AI Job Application Intelligence Platform"
requires-python = ">=3.11"

[tool.black]
line-length = 100
target-version = ["py311"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "S", "N", "C4", "SIM"]
ignore = ["S101"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra -q"
"""


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  wrote {path.relative_to(ROOT)}")


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    print(f"Scaffolding into: {ROOT}")

    for d in DIRECTORIES:
        dir_path = ROOT / d
        dir_path.mkdir(parents=True, exist_ok=True)
        keep = dir_path / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")
        print(f"  mkdir {d}")

    write(ROOT / ".gitignore", GITIGNORE)
    write(ROOT / ".env.example", ENV_EXAMPLE)
    write(ROOT / "README.md", README)
    write(ROOT / "pyproject.toml", PYPROJECT)

    print("\nPhase 1 scaffold complete.")


if __name__ == "__main__":
    main()
