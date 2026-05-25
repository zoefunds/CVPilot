"""
Phase 10 backend: public verification endpoint.
Reads an evaluation directly from the contract by content_hash. Unauthenticated.
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
FILES: dict[str, str] = {}


FILES["backend/app/schemas/public.py"] = '''"""
Public verification response. PII-free.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class PublicEvaluation(BaseModel):
    content_hash: str
    contract_address: str
    found: bool

    cv_score: int | None = None
    cover_letter_score: int | None = None
    job_match_score: int | None = None
    ats_score: int | None = None
    competitiveness_score: int | None = None
    overall_score: int | None = None

    summary: str | None = None
    improved_positioning: str | None = None
    missing_keywords: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    weak_statements: list[str] = Field(default_factory=list)
    company_alignment_notes: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    rationale: dict | None = None

    @field_validator(
        "missing_keywords", "missing_skills", "recommendations",
        "weak_statements", "company_alignment_notes", "strengths", "risks",
        mode="before",
    )
    @classmethod
    def _none_to_list(cls, v):
        return v if v is not None else []
'''


FILES["backend/app/routes/public.py"] = '''"""
Public, unauthenticated verification routes.

GET /api/v1/public/verify/{content_hash}
  Read the evaluation stored on the GenLayer contract for the given hash.
  Returns 200 with PublicEvaluation if found, 404 otherwise.
  Heavily rate-limited.
"""

import re

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.core.errors import NotFoundError, ValidationAppError
from backend.app.core.logging import get_logger
from backend.app.dependencies.rate_limit import limiter
from backend.app.schemas.public import PublicEvaluation
from services.genlayer import fetch_stored_evaluation

router = APIRouter(prefix="/public", tags=["public"])
log = get_logger("public")

_HASH_RE = re.compile(r"^[0-9a-fA-F]{64}$")


@router.get("/verify/{content_hash}", response_model=PublicEvaluation)
@limiter.limit("30/minute")
def verify(request: Request, content_hash: str):
    if not _HASH_RE.match(content_hash or ""):
        raise ValidationAppError(
            "Content hash must be a 64-character hexadecimal SHA-256.",
            code="invalid_content_hash",
        )

    parsed = fetch_stored_evaluation(content_hash)
    if not parsed:
        # Return a 404-style PublicEvaluation so the frontend has the
        # contract address even on miss (useful for "search on explorer").
        return JSONResponse(
            status_code=404,
            content=PublicEvaluation(
                content_hash=content_hash,
                contract_address=settings.genlayer_contract_address,
                found=False,
            ).model_dump(),
        )

    rationale = parsed.get("rationale") if isinstance(parsed.get("rationale"), dict) else None

    log.info("verify_hit", content_hash=content_hash[:12])

    return PublicEvaluation(
        content_hash=content_hash,
        contract_address=settings.genlayer_contract_address,
        found=True,
        cv_score=int(parsed.get("cv_score", 0) or 0),
        cover_letter_score=int(parsed.get("cover_letter_score", 0) or 0),
        job_match_score=int(parsed.get("job_match_score", 0) or 0),
        ats_score=int(parsed.get("ats_score", 0) or 0),
        competitiveness_score=int(parsed.get("competitiveness_score", 0) or 0),
        overall_score=int(parsed.get("overall_score", 0) or 0),
        summary=str(parsed.get("summary", "")) or None,
        improved_positioning=str(parsed.get("improved_positioning", "")) or None,
        missing_keywords=list(parsed.get("missing_keywords") or []),
        missing_skills=list(parsed.get("missing_skills") or []),
        recommendations=list(parsed.get("recommendations") or []),
        weak_statements=list(parsed.get("weak_statements") or []),
        company_alignment_notes=list(parsed.get("company_alignment_notes") or []),
        strengths=list(parsed.get("strengths") or []),
        risks=list(parsed.get("risks") or []),
        rationale=rationale,
    )
'''


# Extend genlayer client with a clean read-only helper.
FILES["services/genlayer/__init__.py"] = '''from services.genlayer.wallet import (  # noqa: F401
    generate_wallet,
    get_balance_wei,
    address_from_private_key,
)
from services.genlayer.read import fetch_stored_evaluation  # noqa: F401
'''


FILES["services/genlayer/read.py"] = '''"""
Read-only GenLayer helpers. Used by the public verify endpoint to fetch a
stored evaluation by content_hash without requiring a user wallet or signing.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Optional


@lru_cache(maxsize=1)
def _client():
    # Lazy import so this module does not pull the SDK at import time.
    from services.llm.genlayer import GenLayerLLMClient
    return GenLayerLLMClient()  # ephemeral account; reads are unsigned


def fetch_stored_evaluation(content_hash: str) -> Optional[dict]:
    """Read get_evaluation(content_hash) from the contract. Returns parsed
    JSON dict or None if missing/empty/unreadable."""
    try:
        client = _client()
    except Exception:
        return None
    ok, raw = client._try_read("get_evaluation", [content_hash])  # noqa: SLF001
    if not ok or not raw:
        return None
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return None
'''


FILES["api/v1/router.py"] = '''"""
Versioned API router aggregator.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.routes import admin, applications, auth, evaluations, public, wallet

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(wallet.router)
api_router.include_router(applications.router)
api_router.include_router(evaluations.router)
api_router.include_router(admin.router)
api_router.include_router(public.router)
'''


FILES["tests/backend/test_public.py"] = '''"""
Tests for the public verify endpoint.
"""

from __future__ import annotations


def test_verify_rejects_malformed_hash(client) -> None:
    r = client.get("/api/v1/public/verify/not-a-hash")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_content_hash"


def test_verify_missing_hash_returns_404(client) -> None:
    # 64 valid hex chars but never stored on the contract.
    fake = "0" * 64
    r = client.get(f"/api/v1/public/verify/{fake}")
    # In stub-test mode the contract read raises NotImplementedError and
    # is caught as None by fetch_stored_evaluation, producing 404.
    assert r.status_code == 404
    body = r.json()
    assert body["content_hash"] == fake
    assert body["found"] is False
'''


def write(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  wrote {rel}")


for rel, content in FILES.items():
    write(rel, content)

print("\nPhase 10 backend scaffold complete.")
