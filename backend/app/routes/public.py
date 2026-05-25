"""
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
