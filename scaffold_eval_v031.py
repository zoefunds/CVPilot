"""
Extend the Evaluation model + schema + LLMEvaluation dataclass + stub + genlayer
client + worker to handle the v0.3.1 contract response shape:
  + overall_score
  + strengths
  + risks
  + improved_positioning
  + rationale (per-score map)
  + content_hash      (the sha256 we feed the contract)
  + contract_address  (so each row points to its on-chain origin)
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
FILES: dict[str, str] = {}


# -----------------------------------------------------------------------------
# 1. backend/app/models/evaluation.py  (add columns)
# -----------------------------------------------------------------------------
FILES["backend/app/models/evaluation.py"] = '''"""
Evaluation ORM. One Evaluation row per Application (latest-wins for now).
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column

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
    __table_args__ = (
        UniqueConstraint("application_id", name="uq_evaluations_application_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        evaluation_status_enum, default="pending", nullable=False
    )
    backend: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Score fields
    cv_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cover_letter_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    job_match_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ats_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    competitiveness_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    overall_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Narrative
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    improved_positioning: Mapped[str | None] = mapped_column(Text, nullable=True)

    # List fields
    recommendations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    missing_keywords: Mapped[list | None] = mapped_column(JSON, nullable=True)
    missing_skills: Mapped[list | None] = mapped_column(JSON, nullable=True)
    weak_statements: Mapped[list | None] = mapped_column(JSON, nullable=True)
    company_alignment_notes: Mapped[list | None] = mapped_column(JSON, nullable=True)
    strengths: Mapped[list | None] = mapped_column(JSON, nullable=True)
    risks: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Per-score rationale (dict)
    rationale: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # On-chain provenance
    raw: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    contract_tx_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    contract_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
'''


# -----------------------------------------------------------------------------
# 2. backend/app/schemas/evaluation.py
# -----------------------------------------------------------------------------
FILES["backend/app/schemas/evaluation.py"] = '''"""
Evaluation response schema. Coerces NULL JSON list columns to empty lists
so a freshly-created pending row never breaks the response.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EvaluationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    application_id: uuid.UUID
    status: str
    backend: str | None = None

    # Scores
    cv_score: int | None = None
    cover_letter_score: int | None = None
    job_match_score: int | None = None
    ats_score: int | None = None
    competitiveness_score: int | None = None
    overall_score: int | None = None

    # Narrative
    summary: str | None = None
    improved_positioning: str | None = None

    # Lists
    recommendations: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    weak_statements: list[str] = Field(default_factory=list)
    company_alignment_notes: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)

    # Per-score rationale
    rationale: dict | None = None

    # Provenance
    raw: dict | None = None
    error: str | None = None
    contract_tx_hash: str | None = None
    content_hash: str | None = None
    contract_address: str | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator(
        "recommendations",
        "missing_keywords",
        "missing_skills",
        "weak_statements",
        "company_alignment_notes",
        "strengths",
        "risks",
        mode="before",
    )
    @classmethod
    def _none_to_list(cls, v):
        return v if v is not None else []
'''


# -----------------------------------------------------------------------------
# 3. services/llm/base.py  (extend dataclass with new fields)
# -----------------------------------------------------------------------------
FILES["services/llm/base.py"] = '''"""
Pluggable LLM client interface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class LLMScore:
    value: int
    label: str
    rationale: str
    signals: dict = field(default_factory=dict)


@dataclass(frozen=True)
class LLMEvaluation:
    cv: LLMScore
    cover_letter: LLMScore
    job_match: LLMScore
    ats: LLMScore
    competitiveness: LLMScore
    overall: LLMScore
    summary: str
    improved_positioning: str
    missing_keywords: list[str]
    missing_skills: list[str]
    recommendations: list[str]
    weak_statements: list[str]
    company_alignment_notes: list[str]
    strengths: list[str]
    risks: list[str]
    rationale: dict
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


# -----------------------------------------------------------------------------
# 4. services/llm/stub.py  (populate new fields too)
# -----------------------------------------------------------------------------
FILES["services/llm/stub.py"] = '''"""
Deterministic LLM stand-in. Returns the same shape as the v0.3.1 contract.
Used in tests and (optionally) dev. Production sets LLM_BACKEND=genlayer.
"""

from __future__ import annotations

import re
from collections import Counter

from services.llm.base import LLMClient, LLMEvaluation, LLMScore

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9+#.\\-]{1,}")
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
_METRIC_CUE = re.compile(
    r"\\b\\d+(?:\\.\\d+)?\\s?(%|x|k|m|million|billion|users|customers|requests|qps|ms|seconds?|hours?|days?|weeks?|months?|years?)\\b",
    re.IGNORECASE,
)
_ATS_BAD_CUES = re.compile(r"[\\u2022\\u25CF\\u25E6\\u25A0]+|<img|<table", re.IGNORECASE)


def _tokens(text):
    return [t.lower() for t in _TOKEN_RE.findall(text or "") if t.lower() not in _STOPWORDS]


def _keyword_overlap(target, candidate):
    t = Counter(_tokens(target))
    c = Counter(_tokens(candidate))
    if not t:
        return 0.0, [], []
    matched = [w for w in t if w in c and len(w) > 2]
    missing = [w for w, n in t.most_common(60) if w not in c and len(w) > 3][:15]
    coverage = len(matched) / max(1, len({w for w in t if len(w) > 2}))
    top_kw_hits = sorted(matched, key=lambda w: t[w], reverse=True)[:10]
    return min(1.0, coverage), top_kw_hits, missing


def _clamp(v, lo=0, hi=100):
    return int(max(lo, min(hi, round(v))))


def _score_cv(cv, job):
    coverage, hits, missing = _keyword_overlap(job, cv)
    n_a = len(_ACHIEVEMENT_CUES.findall(cv))
    n_m = len(_METRIC_CUE.findall(cv))
    length_factor = min(1.0, len(cv) / 1800)
    score = 35 + 35 * coverage + 12 * min(1.0, n_a / 6) + 18 * length_factor
    if n_m:
        score += min(8, n_m * 2)
    return LLMScore(
        value=_clamp(score),
        label="cv",
        rationale=f"Matched {len(hits)} keywords, {n_a} verbs, {n_m} metrics.",
        signals={"keyword_hits": hits, "achievement_verbs": n_a, "metrics_found": n_m},
    ), missing, hits


def _score_cover_letter(cl, job, job_title):
    coverage, hits, _ = _keyword_overlap(job, cl)
    mentions_title = bool(job_title and job_title.lower() in cl.lower())
    addressed = bool(re.search(r"^(dear|hi|hello)\\b", cl.strip(), re.IGNORECASE))
    p = 0
    if mentions_title: p += 12
    if addressed: p += 6
    length_factor = min(1.0, len(cl) / 900)
    score = 30 + 35 * coverage + p + 18 * length_factor
    return LLMScore(
        value=_clamp(score),
        label="cover_letter",
        rationale="Personalisation, addressee, length, keyword alignment.",
        signals={"mentions_title": mentions_title, "addressed": addressed},
    )


def _score_job_match(cv, cl, job):
    cv_cov, _, _ = _keyword_overlap(job, cv)
    cl_cov, _, _ = _keyword_overlap(job, cl)
    return LLMScore(
        value=_clamp(25 + 70 * (0.65 * cv_cov + 0.35 * cl_cov)),
        label="job_match",
        rationale="Weighted CV/CL keyword alignment.",
        signals={},
    )


def _score_ats(cv):
    bad = len(_ATS_BAD_CUES.findall(cv))
    too_short = len(cv) < 800
    has_email = bool(re.search(r"[A-Za-z0-9._%+\\-]+@[A-Za-z0-9.\\-]+", cv))
    has_phone = bool(re.search(r"\\+?\\d[\\d \\-().]{7,}\\d", cv))
    score = 90
    if bad: score -= 10
    if too_short: score -= 15
    if not has_email: score -= 8
    if not has_phone: score -= 5
    return LLMScore(value=_clamp(score), label="ats", rationale="ATS heuristic.", signals={})


def _weak(cv):
    out = []
    for line in cv.splitlines():
        s = line.strip()
        if not s: continue
        if len(s) > 40 and not _ACHIEVEMENT_CUES.search(s) and not _METRIC_CUE.search(s):
            if any(kw in s.lower() for kw in ("responsible for", "duties included", "worked on", "helped with")):
                out.append(s)
    return out[:5]


def _detect_strengths(cv):
    out = []
    if _ACHIEVEMENT_CUES.search(cv): out.append("Uses action verbs for accomplishments.")
    if _METRIC_CUE.search(cv): out.append("Quantifies outcomes with metrics.")
    if "@" in cv: out.append("Contact details are visible to recruiters.")
    return out


def _detect_risks(cv, job):
    out = []
    if len(cv) < 800: out.append("CV body is short and may read as unsupported.")
    if not _METRIC_CUE.search(cv): out.append("No measurable outcomes detected.")
    if not _ACHIEVEMENT_CUES.search(cv): out.append("Few or no strong action verbs.")
    if "team" in (job or "").lower() and "team" not in cv.lower():
        out.append("Job emphasises team collaboration; CV does not.")
    return out


class StubLLMClient(LLMClient):
    def evaluate(
        self, *, cv_text, cover_letter_text, job_text, job_title, job_url, linkedin_url, portfolio_url,
    ) -> LLMEvaluation:
        cv_score, missing_keywords, _hits = _score_cv(cv_text, job_text)
        cl_score = _score_cover_letter(cover_letter_text, job_text, job_title)
        match_score = _score_job_match(cv_text, cover_letter_text, job_text)
        ats_score = _score_ats(cv_text)
        comp = round(0.30 * cv_score.value + 0.20 * cl_score.value + 0.30 * match_score.value + 0.20 * ats_score.value)
        competitiveness = LLMScore(value=_clamp(comp), label="competitiveness", rationale="Weighted blend.", signals={})
        overall_value = round(0.40 * comp + 0.30 * match_score.value + 0.15 * cv_score.value + 0.15 * cl_score.value)
        overall = LLMScore(value=_clamp(overall_value), label="overall", rationale="Holistic blend.", signals={})

        recs = []
        if missing_keywords:
            recs.append(f"Surface these missing job keywords in your CV: {', '.join(missing_keywords[:8])}.")

        improved = ""
        if job_title and missing_keywords:
            improved = (
                f"Reposition yourself as a {job_title} candidate by leading with "
                f"the matching skills ({', '.join(missing_keywords[:3])}) "
                "and a concrete metric in your first bullet."
            )

        rationale = {
            "cv_score": cv_score.rationale,
            "cover_letter_score": cl_score.rationale,
            "job_match_score": match_score.rationale,
            "ats_score": ats_score.rationale,
            "competitiveness_score": competitiveness.rationale,
            "overall_score": overall.rationale,
        }

        return LLMEvaluation(
            cv=cv_score,
            cover_letter=cl_score,
            job_match=match_score,
            ats=ats_score,
            competitiveness=competitiveness,
            overall=overall,
            summary=f"Overall {overall.value}/100. Competitiveness {competitiveness.value}/100.",
            improved_positioning=improved,
            missing_keywords=missing_keywords,
            missing_skills=missing_keywords[:8],
            recommendations=recs,
            weak_statements=_weak(cv_text),
            company_alignment_notes=[],
            strengths=_detect_strengths(cv_text),
            risks=_detect_risks(cv_text, job_text),
            rationale=rationale,
            raw={
                "backend": "stub",
                "version": 1,
                "scores": {
                    "cv": cv_score.value,
                    "cover_letter": cl_score.value,
                    "job_match": match_score.value,
                    "ats": ats_score.value,
                    "competitiveness": competitiveness.value,
                    "overall": overall.value,
                },
            },
        )
'''


# -----------------------------------------------------------------------------
# 5. services/llm/genlayer.py (parse new JSON shape, normalise hash, etc.)
# -----------------------------------------------------------------------------
FILES["services/llm/genlayer.py"] = '''"""
GenLayer Intelligent Contract LLM backend.

Calls the deployed CVPilotEvaluator contract on StudioNet:
  evaluate_application(content_hash, cv, cover_letter, job, title, url, linkedin, portfolio)

The contract caches by content_hash. We:
  1. Compute SHA-256 over a stable normalised JSON of the inputs.
  2. Read get_evaluation(hash); on cache hit, return immediately.
  3. Otherwise write evaluate_application(...) and re-read.
  4. Parse the v0.3.1 schema (includes overall_score, strengths, risks,
     improved_positioning, rationale).
"""

import hashlib
import json
import sys
import time
from typing import Any

from backend.app.core.config import settings
from backend.app.core.errors import AppError
from backend.app.core.logging import get_logger
from services.llm.base import LLMClient, LLMEvaluation, LLMScore

log = get_logger("llm.genlayer")

_CV_MAX = 8000
_CL_MAX = 4000
_JOB_MAX = 6000


class GenLayerClientError(AppError):
    status_code = 502
    code = "genlayer_error"


def _normalised_content_hash(
    *,
    cv: str,
    cl: str,
    job: str,
    title: str,
    job_url: str,
    linkedin_url: str,
    portfolio_url: str,
) -> str:
    payload = json.dumps(
        {
            "cv_text": (cv or "").strip(),
            "cover_letter": (cl or "").strip(),
            "job_text": (job or "").strip(),
            "job_title": (title or "").strip(),
            "job_url": (job_url or "").strip(),
            "linkedin_url": (linkedin_url or "").strip(),
            "portfolio_url": (portfolio_url or "").strip(),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _truncate(s, limit):
    if not s:
        return ""
    return s if len(s) <= limit else s[:limit]


def _install_buffer_shim() -> None:
    if sys.version_info >= (3, 12):
        return
    import collections.abc as _abc
    if hasattr(_abc, "Buffer"):
        return
    try:
        from typing_extensions import Buffer as _Buffer  # type: ignore
        _abc.Buffer = _Buffer  # type: ignore[attr-defined]
    except Exception as exc:  # pragma: no cover
        log.warning("buffer_shim_failed", error=str(exc))


def _import_sdk():
    _install_buffer_shim()
    try:
        from genlayer_py import create_account, create_client  # type: ignore
        from genlayer_py.chains import studionet  # type: ignore
    except Exception as exc:
        raise GenLayerClientError(
            f"genlayer-py SDK is not installed or incompatible: {exc}",
            code="genlayer_sdk_missing",
        ) from exc
    return create_account, create_client, studionet


class GenLayerLLMClient(LLMClient):
    def __init__(self) -> None:
        if not settings.genlayer_contract_address:
            raise GenLayerClientError(
                "GENLAYER_CONTRACT_ADDRESS is not configured.",
                code="genlayer_address_missing",
            )
        create_account, create_client, studionet = _import_sdk()
        pk = (settings.genlayer_account_private_key or "").strip()
        if pk:
            try:
                self._account = create_account(account_private_key=pk)
            except TypeError:
                self._account = create_account(private_key=pk)
        else:
            self._account = create_account()
        self._client = create_client(chain=studionet, account=self._account)
        self._address = settings.genlayer_contract_address
        log.info(
            "genlayer_client_ready",
            address=self._address,
            account=str(getattr(self._account, "address", "")),
        )

    def _read_raw(self, fn, args):
        return self._client.read_contract(
            address=self._address, function_name=fn, args=args
        )

    def _try_read(self, fn, args):
        try:
            return True, self._read_raw(fn, args)
        except Exception as exc:
            log.warning("genlayer_soft_read_failed", fn=fn, error=str(exc))
            return False, None

    def _read(self, fn, args):
        try:
            return self._read_raw(fn, args)
        except Exception as exc:
            raise GenLayerClientError(
                f"GenLayer read_contract({fn}) failed: {exc}",
                code="genlayer_read_failed",
            ) from exc

    def _write(self, fn, args):
        try:
            tx_hash = self._client.write_contract(
                address=self._address, function_name=fn, args=args
            )
        except Exception as exc:
            raise GenLayerClientError(
                f"GenLayer write_contract({fn}) failed: {exc}",
                code="genlayer_write_failed",
            ) from exc
        wait = getattr(self._client, "wait_for_transaction_receipt", None)
        if wait is not None:
            try:
                wait(transaction_hash=tx_hash)
            except TypeError:
                try:
                    wait(tx_hash)
                except Exception as exc:
                    log.warning("genlayer_receipt_wait_failed", error=str(exc))
            except Exception as exc:
                log.warning("genlayer_receipt_wait_failed", error=str(exc))
        return str(tx_hash)

    # ------------------------------------------------------------------------
    def ping(self) -> dict:
        out = {"address": self._address, "version": None, "evaluation_count": None}
        ok, v = self._try_read("contract_version", [])
        if not ok:
            raise GenLayerClientError(
                "Contract is unreachable.",
                code="genlayer_contract_unreachable",
            )
        out["version"] = v
        ok2, c = self._try_read("evaluation_count", [])
        out["evaluation_count"] = c if ok2 else "unavailable"
        return out

    # ------------------------------------------------------------------------
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
        cv = _truncate(cv_text, _CV_MAX)
        cl = _truncate(cover_letter_text, _CL_MAX)
        job = _truncate(job_text, _JOB_MAX)
        title = job_title or ""
        url = job_url or ""

        h = _normalised_content_hash(
            cv=cv, cl=cl, job=job, title=title,
            job_url=url, linkedin_url=linkedin_url or "",
            portfolio_url=portfolio_url or "",
        )

        # 1) Cache check
        ok, existing = self._try_read("get_evaluation", [h])
        if ok and existing:
            log.info("genlayer_cache_hit", content_hash=h[:12])
            return self._build_evaluation(existing, contract_tx_hash=None, content_hash=h)

        # 2) Write
        log.info("genlayer_evaluate_dispatch", content_hash=h[:12])
        tx_hash = self._write(
            "evaluate_application",
            [h, cv, cl, job, title, url, linkedin_url or "", portfolio_url or ""],
        )
        log.info("genlayer_evaluate_landed", content_hash=h[:12], tx_hash=tx_hash)

        # 3) Read back
        ok2, stored = self._try_read("get_evaluation", [h])
        if not ok2 or not stored:
            raise GenLayerClientError(
                "Contract accepted the write but get_evaluation returned empty.",
                code="genlayer_storage_not_persistent",
            )
        return self._build_evaluation(stored, contract_tx_hash=tx_hash, content_hash=h)

    # ------------------------------------------------------------------------
    def _build_evaluation(
        self,
        raw_json,
        *,
        contract_tx_hash: str | None,
        content_hash: str,
    ) -> LLMEvaluation:
        if isinstance(raw_json, dict):
            parsed = raw_json
        else:
            try:
                parsed = json.loads(raw_json)
            except Exception:
                parsed = {}

        rationale_obj = parsed.get("rationale") if isinstance(parsed.get("rationale"), dict) else {}

        def _score(name: str, key: str, rationale_key: str | None = None) -> LLMScore:
            rk = rationale_key or key
            return LLMScore(
                value=int(parsed.get(key, 0) or 0),
                label=name,
                rationale=str(rationale_obj.get(rk, "")),
                signals={},
            )

        cv = _score("cv", "cv_score")
        cl = _score("cover_letter", "cover_letter_score")
        jm = _score("job_match", "job_match_score")
        ats = _score("ats", "ats_score")
        comp = _score("competitiveness", "competitiveness_score")
        overall = _score("overall", "overall_score")

        return LLMEvaluation(
            cv=cv,
            cover_letter=cl,
            job_match=jm,
            ats=ats,
            competitiveness=comp,
            overall=overall,
            summary=str(parsed.get("summary", "")),
            improved_positioning=str(parsed.get("improved_positioning", "")),
            missing_keywords=list(parsed.get("missing_keywords") or []),
            missing_skills=list(parsed.get("missing_skills") or []),
            recommendations=list(parsed.get("recommendations") or []),
            weak_statements=list(parsed.get("weak_statements") or []),
            company_alignment_notes=list(parsed.get("company_alignment_notes") or []),
            strengths=list(parsed.get("strengths") or []),
            risks=list(parsed.get("risks") or []),
            rationale=dict(rationale_obj),
            raw={
                "backend": "genlayer",
                "version": "0.3.1",
                "contract_address": self._address,
                "contract_tx_hash": contract_tx_hash,
                "content_hash": content_hash,
                "scores": {
                    "cv": cv.value,
                    "cover_letter": cl.value,
                    "job_match": jm.value,
                    "ats": ats.value,
                    "competitiveness": comp.value,
                    "overall": overall.value,
                },
                "raw_contract_payload": parsed,
            },
        )
'''


# -----------------------------------------------------------------------------
# 6. workers/tasks/evaluations.py (persist all new fields)
# -----------------------------------------------------------------------------
FILES["workers/tasks/evaluations.py"] = '''"""
Background task: run the evaluation orchestrator on a ready Application
and persist results (including all v0.3.1 fields).
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.logging import get_logger
from backend.app.db.session import SessionLocal
from backend.app.models.application import Application
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

        # Scores
        ev.cv_score = r.cv.value
        ev.cover_letter_score = r.cover_letter.value
        ev.job_match_score = r.job_match.value
        ev.ats_score = r.ats.value
        ev.competitiveness_score = r.competitiveness.value
        ev.overall_score = r.overall.value

        # Narrative
        ev.summary = r.summary
        ev.improved_positioning = r.improved_positioning

        # Lists
        ev.recommendations = list(r.recommendations)
        ev.missing_keywords = list(r.missing_keywords)
        ev.missing_skills = list(r.missing_skills)
        ev.weak_statements = list(r.weak_statements)
        ev.company_alignment_notes = list(r.company_alignment_notes)
        ev.strengths = list(r.strengths)
        ev.risks = list(r.risks)

        # Rationale + provenance
        ev.rationale = dict(r.rationale) if r.rationale else None
        ev.raw = r.raw
        ev.contract_tx_hash = (r.raw or {}).get("contract_tx_hash")
        ev.content_hash = (r.raw or {}).get("content_hash")
        ev.contract_address = (r.raw or {}).get("contract_address") or settings.genlayer_contract_address

        ev.status = "complete"
        app.status = "complete"
        db.commit()
        log.info(
            "evaluation_complete",
            application_id=str(application_id),
            overall=r.overall.value,
            backend=outcome.backend,
            contract_tx_hash=ev.contract_tx_hash,
        )
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        fresh_ev = db.scalar(
            select(Evaluation).where(Evaluation.application_id == application_id)
        )
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


# -----------------------------------------------------------------------------
# 7. tests/backend/test_evaluations.py — assert the new fields
# -----------------------------------------------------------------------------
FILES["tests/backend/test_evaluations.py"] = '''"""
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
        c.drawString(72, y, ln); y -= 18
    c.showPage(); c.save()
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
        "I am thrilled to apply for the Senior Python Engineer role.\\n"
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
'''


def write(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  wrote {rel}")


for rel, content in FILES.items():
    write(rel, content)

print("\nv0.3.1 backend scaffold complete.")
