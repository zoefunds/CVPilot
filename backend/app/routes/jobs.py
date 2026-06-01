"""
POST /api/v1/jobs/ingest -> structured job fields.
"""

from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, HttpUrl

from backend.app.core.errors import ValidationAppError
from backend.app.core.logging import get_logger
from backend.app.dependencies.auth import get_current_user
from backend.app.models.user import User
from services.jobfetch import cache as ingest_cache
from services.jobfetch.extractor import extract_job_fields
from services.jobfetch.fetcher import fetch_job_posting

router = APIRouter(prefix="/jobs", tags=["jobs"])
log = get_logger("jobs.ingest")


class IngestRequest(BaseModel):
    url: HttpUrl


class IngestResponse(BaseModel):
    url: str
    title: str | None = None
    company: str | None = None
    location: str | None = None
    employment_type: str | None = None
    description: str | None = None
    fetched_at: str
    cache_hit: bool = False


@router.post("/ingest", response_model=IngestResponse)
def ingest_job(
    request: Request,
    body: IngestRequest,
    current_user: User = Depends(get_current_user),
):
    url = str(body.url)
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValidationAppError("URL must use http or https.")

    cached = ingest_cache.get(url)
    if cached:
        log.info("ingest_cache_hit", url=url, user_id=str(current_user.id))
        return IngestResponse(**cached, cache_hit=True)

    posting = fetch_job_posting(url)
    raw_html = getattr(posting, "html", None) or ""
    extracted = extract_job_fields(raw_html, url=url, fallback_title=posting.title)

    now = datetime.now(UTC).isoformat()
    result = {
        "url": posting.final_url or url,
        "title": extracted.title,
        "company": extracted.company,
        "location": extracted.location,
        "employment_type": extracted.employment_type,
        "description": extracted.description,
        "fetched_at": now,
    }
    ingest_cache.put(url, result)
    log.info(
        "ingest_complete",
        url=url,
        user_id=str(current_user.id),
        has_title=bool(result["title"]),
        has_company=bool(result["company"]),
    )
    return IngestResponse(**result, cache_hit=False)
