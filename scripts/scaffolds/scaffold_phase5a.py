"""
CVPilot Phase 5A: Evaluation engine + pluggable LLM (stub now, GenLayer in 5B).
Writes every file. Idempotent.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")

FILES: dict[str, str] = {}

# -----------------------------------------------------------------------------
# services/llm: pluggable LLM client (stub for now)
# -----------------------------------------------------------------------------
FILES["services/llm/__init__.py"] = '''from services.llm.factory import get_llm_client  # noqa: F401
from services.llm.base import LLMClient, LLMEvaluation, LLMScore  # noqa: F401
'''

FILES["services/llm/base.py"] = '''"""
Pluggable LLM client interface.
Two implementations:
  - stub: deterministic heuristic scoring (dev/tests).
  - genlayer: calls a deployed Intelligent Contract (Phase 5B).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class LLMScore:
    value: int            # 0..100
    label: str            # e.g. "cv", "cover_letter", "job_match", "ats", "competitiveness"
    rationale: str
    signals: dict = field(default_factory=dict)


@dataclass(frozen=True)
class LLMEvaluation:
    cv: LLMScore
    cover_letter: LLMScore
    job_match: LLMScore
    ats: LLMScore
    competitiveness: LLMScore
    summary: str
    missing_keywords: list[str]
    missing_skills: list[str]
    recommendations: list[str]
    weak_statements: list[str]
    company_alignment_notes: list[str]
    raw: dict


class LLMClient(Protocol):
    def evaluate(
        self,
        *,
        cv_text: str,
        cover_letter_text: str,
        job_text: str,
        job_title: str | None,
        job_url: str,
        linkedin_url: str | None,
        portfolio_url: str | None,
    ) -> LLMEvaluation: ...
'''

FILES["services/llm/stub.py"] = '''"""
Deterministic, fast, dependency-free LLM stand-in.
Produces structurally-correct LLMEvaluation results so the rest of the
system (Celery, DB, API, frontend) can be exercised end-to-end without
calling out to GenLayer / OpenAI / anything network.

Scoring philosophy:
  - Real signals (token overlap, length, formatting cues) so scores
    actually correlate with content quality.
  - Stable across runs (no randomness).
  - Same inputs => same outputs (auditability).
"""

from __future__ import annotations

import re
from collections import Counter

from services.llm.base import LLMClient, LLMEvaluation, LLMScore

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9+#.\-]{1,}")
_STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "have", "has",
    "are", "you", "your", "our", "will", "into", "to", "of", "in", "on",
    "at", "by", "as", "an", "a", "is", "be", "we", "or", "it", "i", "ll",
    "re", "ve", "s", "t", "d",
}
_ACHIEVEMENT_CUES = re.compile(
    r"\\b(led|owned|shipped|launched|increased|reduced|scaled|saved|"
    r"grew|delivered|drove|migrated|architected|built|designed)\\b",
    re.IGNORECASE,
)
_METRIC_CUE = re.compile(r"\\b\\d+(?:\\.\\d+)?\\s?(%|x|k|m|million|billion|users|customers|requests|qps|ms|seconds?|hours?|days?|weeks?|months?|years?)\\b", re.IGNORECASE)
_ATS_BAD_CUES = re.compile(r"[\\u2022\\u25CF\\u25E6\\u25A0]+|<img|<table", re.IGNORECASE)


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "") if t.lower() not in _STOPWORDS]


def _keyword_overlap(target: str, candidate: str) -> tuple[float, list[str], list[str]]:
    t = Counter(_tokens(target))
    c = Counter(_tokens(candidate))
    if not t:
        return 0.0, [], []
    matched = [w for w in t if w in c and len(w) > 2]
    missing = [w for w, n in t.most_common(60) if w not in c and len(w) > 3][:15]
    coverage = len(matched) / max(1, len({w for w in t if len(w) > 2}))
    top_kw_hits = sorted(matched, key=lambda w: t[w], reverse=True)[:10]
    return min(1.0, coverage), top_kw_hits, missing


def _clamp(v: float, lo: int = 0, hi: int = 100) -> int:
    return int(max(lo, min(hi, round(v))))


def _score_cv(cv: str, job: str) -> tuple[LLMScore, list[str], list[str]]:
    coverage, hits, missing = _keyword_overlap(job, cv)
    n_achievements = len(_ACHIEVEMENT_CUES.findall(cv))
    n_metrics = len(_METRIC_CUE.findall(cv))
    length_factor = min(1.0, len(cv) / 1800)
    score = 35 + 35 * coverage + 12 * min(1.0, n_achievements / 6) + 18 * length_factor
    if n_metrics:
        score += min(8, n_metrics * 2)
    return (
        LLMScore(
            value=_clamp(score),
            label="cv",
            rationale=(
                f"CV matched {len(hits)} job-related keywords, "
                f"includes {n_achievements} achievement verbs and {n_metrics} quantified results."
            ),
            signals={
                "keyword_hits": hits,
                "achievement_verbs": n_achievements,
                "metrics_found": n_metrics,
                "length_chars": len(cv),
            },
        ),
        missing,
        hits,
    )


def _score_cover_letter(cl: str, job: str, job_title: str | None) -> LLMScore:
    coverage, hits, _missing = _keyword_overlap(job, cl)
    mentions_title = bool(job_title and job_title.lower() in cl.lower())
    addressed = bool(re.search(r"^(dear|hi|hello)\\b", cl.strip(), re.IGNORECASE))
    personalisation = 0
    if mentions_title:
        personalisation += 12
    if addressed:
        personalisation += 6
    if "i am thrilled" in cl.lower() or "i am excited" in cl.lower():
        personalisation += 4
    length_factor = min(1.0, len(cl) / 900)
    score = 30 + 35 * coverage + personalisation + 18 * length_factor
    return LLMScore(
        value=_clamp(score),
        label="cover_letter",
        rationale=(
            f"Cover letter shares {len(hits)} key terms with the job, "
            f"{'mentions the role title' if mentions_title else 'does not mention the role title'}, "
            f"{'is properly addressed' if addressed else 'is not addressed to a recipient'}."
        ),
        signals={
            "keyword_hits": hits,
            "mentions_title": mentions_title,
            "addressed": addressed,
            "length_chars": len(cl),
        },
    )


def _score_job_match(cv: str, cl: str, job: str) -> LLMScore:
    cv_cov, cv_hits, _ = _keyword_overlap(job, cv)
    cl_cov, _cl_hits, _ = _keyword_overlap(job, cl)
    combined = 0.65 * cv_cov + 0.35 * cl_cov
    score = 25 + 70 * combined
    return LLMScore(
        value=_clamp(score),
        label="job_match",
        rationale=(
            f"Combined CV ({int(cv_cov * 100)}%) and cover-letter ({int(cl_cov * 100)}%) "
            "keyword alignment with the job description."
        ),
        signals={"cv_coverage": round(cv_cov, 3), "cover_letter_coverage": round(cl_cov, 3), "top_overlap": cv_hits},
    )


def _score_ats(cv: str) -> LLMScore:
    bad = len(_ATS_BAD_CUES.findall(cv))
    too_short = len(cv) < 800
    has_email = bool(re.search(r"[A-Za-z0-9._%+\\-]+@[A-Za-z0-9.\\-]+", cv))
    has_phone = bool(re.search(r"\\+?\\d[\\d \\-().]{7,}\\d", cv))
    score = 90
    rationale_bits = ["Baseline 90."]
    if bad:
        score -= 10
        rationale_bits.append(f"Detected {bad} formatting glyphs that can confuse ATS.")
    if too_short:
        score -= 15
        rationale_bits.append("CV body is short (<800 chars); ATS may flag as light on content.")
    if not has_email:
        score -= 8
        rationale_bits.append("No email address detected.")
    if not has_phone:
        score -= 5
        rationale_bits.append("No phone number detected.")
    return LLMScore(
        value=_clamp(score),
        label="ats",
        rationale=" ".join(rationale_bits),
        signals={"bad_glyphs": bad, "too_short": too_short, "has_email": has_email, "has_phone": has_phone},
    )


def _weak_statements(cv: str) -> list[str]:
    weak: list[str] = []
    for line in cv.splitlines():
        s = line.strip()
        if not s:
            continue
        if len(s) > 40 and not _ACHIEVEMENT_CUES.search(s) and not _METRIC_CUE.search(s):
            if any(kw in s.lower() for kw in ("responsible for", "duties included", "worked on", "helped with")):
                weak.append(s)
    return weak[:5]


def _company_alignment_notes(cl: str, job: str) -> list[str]:
    notes: list[str] = []
    if "mission" not in cl.lower() and "mission" in job.lower():
        notes.append("Job posting mentions company mission; cover letter does not reference it.")
    if "values" not in cl.lower() and "values" in job.lower():
        notes.append("Job posting references company values; tie at least one of your experiences to them.")
    if "team" in job.lower() and "team" not in cl.lower():
        notes.append("Posting emphasises team dynamics; consider a sentence on collaboration style.")
    return notes


class StubLLMClient(LLMClient):
    def evaluate(
        self,
        *,
        cv_text: str,
        cover_letter_text: str,
        job_text: str,
        job_title: str | None,
        job_url: str,
        linkedin_url: str | None,
        portfolio_url: str | None,
    ) -> LLMEvaluation:
        cv_score, missing_keywords, _hits = _score_cv(cv_text, job_text)
        cl_score = _score_cover_letter(cover_letter_text, job_text, job_title)
        match_score = _score_job_match(cv_text, cover_letter_text, job_text)
        ats_score = _score_ats(cv_text)
        comp_value = round(
            0.30 * cv_score.value
            + 0.20 * cl_score.value
            + 0.30 * match_score.value
            + 0.20 * ats_score.value
        )
        competitiveness = LLMScore(
            value=_clamp(comp_value),
            label="competitiveness",
            rationale="Weighted blend: 30% CV / 20% Cover Letter / 30% Job Match / 20% ATS.",
            signals={
                "cv": cv_score.value,
                "cover_letter": cl_score.value,
                "job_match": match_score.value,
                "ats": ats_score.value,
            },
        )

        recommendations: list[str] = []
        if missing_keywords:
            recommendations.append(
                f"Surface these missing job keywords in your CV: {', '.join(missing_keywords[:8])}."
            )
        if cl_score.signals.get("addressed") is False:
            recommendations.append("Address the cover letter to a named hiring manager or team.")
        if cl_score.signals.get("mentions_title") is False and job_title:
            recommendations.append(f"Reference the exact role title \\"{job_title}\\" in the cover letter.")
        if ats_score.signals.get("too_short"):
            recommendations.append("Expand the CV body with measurable outcomes (revenue, latency, headcount).")
        if linkedin_url is None:
            recommendations.append("Add a LinkedIn profile URL — most ATS systems weight it.")
        if portfolio_url is None and any(w in (job_text or "").lower() for w in ("portfolio", "design", "frontend", "github")):
            recommendations.append("Include a portfolio or GitHub link given the role.")

        weak = _weak_statements(cv_text)
        if weak:
            recommendations.append(
                "Rewrite weak bullets using achievement verbs + metrics (e.g. 'Reduced P95 latency by 38%')."
            )

        summary = (
            f"Competitiveness {competitiveness.value}/100. "
            f"Strongest area: {max((cv_score, cl_score, match_score, ats_score), key=lambda s: s.value).label}. "
            f"Weakest: {min((cv_score, cl_score, match_score, ats_score), key=lambda s: s.value).label}."
        )

        return LLMEvaluation(
            cv=cv_score,
            cover_letter=cl_score,
            job_match=match_score,
            ats=ats_score,
            competitiveness=competitiveness,
            summary=summary,
            missing_keywords=missing_keywords,
            missing_skills=missing_keywords[:8],
            recommendations=recommendations,
            weak_statements=weak,
            company_alignment_notes=_company_alignment_notes(cover_letter_text, job_text),
            raw={
                "backend": "stub",
                "version": 1,
                "scores": {
                    "cv": cv_score.value,
                    "cover_letter": cl_score.value,
                    "job_match": match_score.value,
                    "ats": ats_score.value,
                    "competitiveness": competitiveness.value,
                },
            },
        )
'''

FILES["services/llm/genlayer.py"] = '''"""
GenLayer Intelligent Contract LLM client (Phase 5B will fill this in).
Currently raises NotImplementedError so the factory makes it obvious
when this backend is selected without a deployed contract address.
"""

from __future__ import annotations

from services.llm.base import LLMClient, LLMEvaluation


class GenLayerLLMClient(LLMClient):
    def evaluate(
        self,
        *,
        cv_text: str,
        cover_letter_text: str,
        job_text: str,
        job_title: str | None,
        job_url: str,
        linkedin_url: str | None,
        portfolio_url: str | None,
    ) -> LLMEvaluation:
        raise NotImplementedError(
            "GenLayer LLM backend is wired in Phase 5B. Set LLM_BACKEND=stub for now."
        )
'''

FILES["services/llm/factory.py"] = '''"""
Choose an LLM backend based on settings.llm_backend.
"""

from __future__ import annotations

from functools import lru_cache

from backend.app.core.config import settings
from services.llm.base import LLMClient
from services.llm.stub import StubLLMClient


@lru_cache(maxsize=1)
def get_llm_client() -> LLMClient:
    if settings.llm_backend == "stub":
        return StubLLMClient()
    if settings.llm_backend == "genlayer":
        from services.llm.genlayer import GenLayerLLMClient
        return GenLayerLLMClient()
    raise ValueError(f"Unknown LLM_BACKEND: {settings.llm_backend}")
'''

# -----------------------------------------------------------------------------
# services/evaluation: orchestrator
# -----------------------------------------------------------------------------
FILES["services/evaluation/__init__.py"] = '''from services.evaluation.orchestrator import run_evaluation, EvaluationOutcome  # noqa: F401
'''

FILES["services/evaluation/orchestrator.py"] = '''"""
Evaluation orchestrator. Composes inputs and calls the configured LLM client.
Pure function-style; no DB writes here.
"""

from __future__ import annotations

from dataclasses import dataclass

from services.llm import LLMEvaluation, get_llm_client


@dataclass(frozen=True)
class EvaluationOutcome:
    report: LLMEvaluation
    backend: str


def run_evaluation(
    *,
    cv_text: str,
    cover_letter_text: str,
    job_text: str,
    job_title: str | None,
    job_url: str,
    linkedin_url: str | None,
    portfolio_url: str | None,
) -> EvaluationOutcome:
    client = get_llm_client()
    report = client.evaluate(
        cv_text=cv_text,
        cover_letter_text=cover_letter_text,
        job_text=job_text,
        job_title=job_title,
        job_url=job_url,
        linkedin_url=linkedin_url,
        portfolio_url=portfolio_url,
    )
    return EvaluationOutcome(report=report, backend=report.raw.get("backend", "unknown"))
'''

# -----------------------------------------------------------------------------
# ORM: Evaluation
# -----------------------------------------------------------------------------
FILES["backend/app/models/evaluation.py"] = '''"""
Evaluation ORM. One Evaluation row per Application (latest-wins for now).
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin

evaluation_status_enum = ENUM(
    "pending",
    "running",
    "complete",
    "failed",
    name="evaluation_status",
    create_type=True,
)


class Evaluation(Base, TimestampMixin):
    __tablename__ = "evaluations"
    __table_args__ = (UniqueConstraint("application_id", name="uq_evaluations_application_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(evaluation_status_enum, default="pending", nullable=False)
    backend: Mapped[str | None] = mapped_column(String(32), nullable=True)
    cv_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cover_letter_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    job_match_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ats_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    competitiveness_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    missing_keywords: Mapped[list | None] = mapped_column(JSON, nullable=True)
    missing_skills: Mapped[list | None] = mapped_column(JSON, nullable=True)
    weak_statements: Mapped[list | None] = mapped_column(JSON, nullable=True)
    company_alignment_notes: Mapped[list | None] = mapped_column(JSON, nullable=True)
    raw: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    contract_tx_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
'''

FILES["backend/app/models/__init__.py"] = '''"""
Import all models here so Alembic autogenerate detects them.
"""

from backend.app.models.user import User  # noqa: F401
from backend.app.models.audit_log import AuditLog  # noqa: F401
from backend.app.models.application import Application, FileAsset  # noqa: F401
from backend.app.models.evaluation import Evaluation  # noqa: F401
'''

# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------
FILES["backend/app/schemas/evaluation.py"] = '''"""
Evaluation response schema.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EvaluationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    application_id: uuid.UUID
    status: str
    backend: str | None = None
    cv_score: int | None = None
    cover_letter_score: int | None = None
    job_match_score: int | None = None
    ats_score: int | None = None
    competitiveness_score: int | None = None
    summary: str | None = None
    recommendations: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    weak_statements: list[str] = Field(default_factory=list)
    company_alignment_notes: list[str] = Field(default_factory=list)
    raw: dict | None = None
    error: str | None = None
    contract_tx_hash: str | None = None
    created_at: datetime
    updated_at: datetime
'''

# -----------------------------------------------------------------------------
# Celery: evaluate task + chain after parse
# -----------------------------------------------------------------------------
FILES["workers/tasks/applications.py"] = '''"""
Background task: process an Application end-to-end (parse + fetch),
then chain the evaluation task on success.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from backend.app.core.logging import get_logger
from backend.app.db.session import SessionLocal
from backend.app.models.application import Application
from services.jobfetch import fetch_job_posting
from services.parsing import extract_text
from services.storage import get_storage
from workers.celery_app import celery_app

log = get_logger("worker.applications")


def _process(db: Session, application_id: uuid.UUID) -> None:
    app = db.get(Application, application_id)
    if app is None:
        log.warning("application_missing", application_id=str(application_id))
        return

    app.status = "processing"
    app.error = None
    db.commit()

    storage = get_storage()
    try:
        for asset in app.files:
            raw = storage.read(asset.storage_key)
            kind, text = extract_text(asset.original_filename, raw)
            asset.detected_kind = kind.value
            asset.extracted_text = text

        posting = fetch_job_posting(app.job_url)
        app.job_final_url = posting.final_url
        app.job_title = posting.title or None
        app.job_text = posting.text

        app.status = "ready"
        db.commit()
        log.info("application_ready", application_id=str(app.id))
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        fresh = db.get(Application, application_id)
        if fresh is not None:
            fresh.status = "failed"
            fresh.error = f"{exc.__class__.__name__}: {exc}"
            db.commit()
        log.exception("application_failed", application_id=str(application_id))
        raise


@celery_app.task(name="cvpilot.process_application", bind=True, max_retries=2)
def process_application(self, application_id: str) -> None:
    aid = uuid.UUID(application_id)
    db = SessionLocal()
    try:
        _process(db, aid)
    finally:
        db.close()

    # Chain evaluation on success. Imported lazily to avoid circular imports.
    from workers.tasks.evaluations import evaluate_application

    evaluate_application.delay(application_id)
'''

FILES["workers/tasks/evaluations.py"] = '''"""
Background task: run the evaluation orchestrator on a ready Application
and persist results to the evaluations table.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.logging import get_logger
from backend.app.db.session import SessionLocal
from backend.app.models.application import Application, FileAsset
from backend.app.models.evaluation import Evaluation
from services.evaluation import run_evaluation
from workers.celery_app import celery_app

log = get_logger("worker.evaluations")


def _get_or_create_evaluation(db: Session, application_id: uuid.UUID) -> Evaluation:
    ev = db.scalar(select(Evaluation).where(Evaluation.application_id == application_id))
    if ev is None:
        ev = Evaluation(application_id=application_id, status="pending")
        db.add(ev)
        db.flush()
    return ev


def _file_text(application: Application, kind: str) -> str:
    for f in application.files:
        if f.kind == kind:
            return f.extracted_text or ""
    return ""


def _run(db: Session, application_id: uuid.UUID) -> None:
    app = db.get(Application, application_id)
    if app is None:
        log.warning("evaluation_application_missing", application_id=str(application_id))
        return
    if app.status != "ready":
        log.info(
            "evaluation_skipped_not_ready",
            application_id=str(application_id),
            status=app.status,
        )
        return

    ev = _get_or_create_evaluation(db, application_id)
    ev.status = "running"
    ev.error = None
    db.commit()

    app.status = "evaluating"
    db.commit()

    try:
        outcome = run_evaluation(
            cv_text=_file_text(app, "cv"),
            cover_letter_text=_file_text(app, "cover_letter"),
            job_text=app.job_text or "",
            job_title=app.job_title,
            job_url=app.job_url,
            linkedin_url=app.linkedin_url,
            portfolio_url=app.portfolio_url,
        )
        r = outcome.report
        ev.backend = outcome.backend
        ev.cv_score = r.cv.value
        ev.cover_letter_score = r.cover_letter.value
        ev.job_match_score = r.job_match.value
        ev.ats_score = r.ats.value
        ev.competitiveness_score = r.competitiveness.value
        ev.summary = r.summary
        ev.recommendations = list(r.recommendations)
        ev.missing_keywords = list(r.missing_keywords)
        ev.missing_skills = list(r.missing_skills)
        ev.weak_statements = list(r.weak_statements)
        ev.company_alignment_notes = list(r.company_alignment_notes)
        ev.raw = r.raw
        ev.status = "complete"
        app.status = "complete"
        db.commit()
        log.info(
            "evaluation_complete",
            application_id=str(application_id),
            competitiveness=r.competitiveness.value,
        )
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        fresh_ev = db.scalar(select(Evaluation).where(Evaluation.application_id == application_id))
        if fresh_ev is not None:
            fresh_ev.status = "failed"
            fresh_ev.error = f"{exc.__class__.__name__}: {exc}"
            db.commit()
        fresh_app = db.get(Application, application_id)
        if fresh_app is not None:
            fresh_app.status = "failed"
            fresh_app.error = f"evaluation_error: {exc}"
            db.commit()
        log.exception("evaluation_failed", application_id=str(application_id))
        raise


@celery_app.task(name="cvpilot.evaluate_application", bind=True, max_retries=2)
def evaluate_application(self, application_id: str) -> None:
    aid = uuid.UUID(application_id)
    db = SessionLocal()
    try:
        _run(db, aid)
    finally:
        db.close()
'''

FILES["workers/celery_app.py"] = '''"""
Celery application factory.
"""

from __future__ import annotations

import os

from celery import Celery

from backend.app.core.config import settings

celery_app = Celery(
    "cvpilot",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "workers.tasks.applications",
        "workers.tasks.evaluations",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=120,
    task_soft_time_limit=90,
    worker_max_tasks_per_child=100,
    broker_connection_retry_on_startup=True,
)

if os.getenv("CELERY_TASK_ALWAYS_EAGER", "").lower() in {"1", "true", "yes"}:
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
'''

# -----------------------------------------------------------------------------
# Routes: evaluations
# -----------------------------------------------------------------------------
FILES["backend/app/routes/evaluations.py"] = '''"""
Evaluation routes nested under /applications/{application_id}.
Deliberately no `from __future__ import annotations` (slowapi compatibility).
"""

import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.errors import (
    ForbiddenError,
    NotFoundError,
    ValidationAppError,
)
from backend.app.core.logging import get_logger
from backend.app.db.session import get_db
from backend.app.dependencies.auth import get_current_user
from backend.app.dependencies.rate_limit import limiter
from backend.app.models.application import Application
from backend.app.models.evaluation import Evaluation
from backend.app.models.user import User
from backend.app.schemas.evaluation import EvaluationPublic

router = APIRouter(prefix="/applications", tags=["evaluations"])
log = get_logger("evaluations")


def _load_owned_application(
    application_id: uuid.UUID, db: Session, user: User
) -> Application:
    app = db.get(Application, application_id)
    if app is None:
        raise NotFoundError("Application not found.")
    if app.user_id != user.id:
        raise ForbiddenError("You do not own this application.")
    return app


@router.post(
    "/{application_id}/evaluate",
    response_model=EvaluationPublic,
    status_code=status.HTTP_202_ACCEPTED,
)
@limiter.limit("20/minute")
def trigger_evaluation(
    request: Request,
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = _load_owned_application(application_id, db, current_user)
    if app.status not in ("ready", "complete", "failed"):
        raise ValidationAppError(
            f"Application is not ready for evaluation (status={app.status}).",
            code="application_not_ready",
        )

    ev = db.scalar(select(Evaluation).where(Evaluation.application_id == app.id))
    if ev is None:
        ev = Evaluation(application_id=app.id, status="pending")
        db.add(ev)
        db.commit()
        db.refresh(ev)

    # Dispatch (idempotent). Eager mode runs inline; real worker handles otherwise.
    from workers.tasks.evaluations import evaluate_application

    evaluate_application.delay(str(app.id))
    log.info("evaluation_dispatched", application_id=str(app.id))

    db.refresh(ev)
    return EvaluationPublic.model_validate(ev)


@router.get("/{application_id}/evaluation", response_model=EvaluationPublic)
def get_evaluation(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = _load_owned_application(application_id, db, current_user)
    ev = db.scalar(select(Evaluation).where(Evaluation.application_id == app.id))
    if ev is None:
        raise NotFoundError("Evaluation has not been created for this application yet.")
    return EvaluationPublic.model_validate(ev)
'''

# -----------------------------------------------------------------------------
# api/v1 router: register evaluations
# -----------------------------------------------------------------------------
FILES["api/v1/router.py"] = '''"""
Versioned API router aggregator. Mounted at /api/v1 in main.py.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.routes import applications, auth, evaluations

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(applications.router)
api_router.include_router(evaluations.router)
'''

# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------
FILES["tests/backend/conftest.py"] = '''"""
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
from backend.app.main import app  # noqa: E402


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
'''

FILES["tests/backend/test_evaluations.py"] = '''"""
End-to-end test for the Evaluation pipeline.
Stub LLM backend produces deterministic scores; we just assert the wiring,
status transitions, ownership, and that the chain runs after parse.
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
        "Jane Doe — Senior Python Engineer",
        "Led FastAPI service rebuild reducing P95 latency by 38%.",
        "Shipped Kubernetes migration for 22 microservices.",
        "Designed Postgres partitioning scheme for 5B rows.",
        "Mentored 4 engineers; team velocity grew 2x.",
        "jane@example.com  +1-202-555-0100",
    ]
    y = 720
    for line in lines:
        c.drawString(72, y, line); y -= 18
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
        "Dear Hiring Team,\\n"
        "I am thrilled to apply for the Senior Python Engineer role. "
        "My experience scaling FastAPI and Postgres directly matches your needs. "
        "Best,\\nJane"
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
    for k in (
        "cv_score",
        "cover_letter_score",
        "job_match_score",
        "ats_score",
        "competitiveness_score",
    ):
        assert isinstance(ev[k], int) and 0 <= ev[k] <= 100, (k, ev[k])
    assert ev["summary"]
    assert isinstance(ev["recommendations"], list)

    # Application should also be marked complete now.
    r = client.get(
        f"/api/v1/applications/{app_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.json()["status"] == "complete"


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
    # Single Evaluation row (uniqueness constraint).
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
'''


def write(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  wrote {rel}")


def main() -> None:
    print(f"Phase 5A into: {ROOT}")
    for rel, content in FILES.items():
        write(rel, content)
    print("\nPhase 5A files written.")


if __name__ == "__main__":
    main()
