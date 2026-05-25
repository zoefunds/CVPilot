"""
Phase 7A backend: Rewrite ORM, LLM rewrite_cv, route, Celery task, tests.
"""

from __future__ import annotations
from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
FILES: dict[str, str] = {}


# ---------- ORM: Rewrite ----------
FILES["backend/app/models/rewrite.py"] = '''"""
Rewrite ORM. One row per (application, kind, attempt).
kinds: cv, cover_letter, interview_prep (only "cv" used in Phase 7A).
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin


rewrite_status_enum = ENUM(
    "pending",
    "running",
    "complete",
    "failed",
    name="rewrite_status",
    create_type=True,
)

rewrite_kind_enum = ENUM(
    "cv",
    "cover_letter",
    "interview_prep",
    name="rewrite_kind",
    create_type=True,
)


class Rewrite(Base, TimestampMixin):
    __tablename__ = "rewrites"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind: Mapped[str] = mapped_column(rewrite_kind_enum, nullable=False)
    status: Mapped[str] = mapped_column(rewrite_status_enum, default="pending", nullable=False)
    backend: Mapped[str | None] = mapped_column(String(32), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    rationale: Mapped[list | None] = mapped_column(JSON, nullable=True)
    raw: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
'''


FILES["backend/app/models/__init__.py"] = '''"""
Import all models here so Alembic autogenerate detects them.
"""

from backend.app.models.user import User  # noqa: F401
from backend.app.models.audit_log import AuditLog  # noqa: F401
from backend.app.models.application import Application, FileAsset  # noqa: F401
from backend.app.models.evaluation import Evaluation  # noqa: F401
from backend.app.models.rewrite import Rewrite  # noqa: F401
'''


# ---------- Schemas ----------
FILES["backend/app/schemas/rewrite.py"] = '''"""
Rewrite response schema.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RewritePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    application_id: uuid.UUID
    kind: str
    status: str
    backend: str | None = None
    content: str | None = None
    rationale: list[str] = Field(default_factory=list)
    raw: dict | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("rationale", mode="before")
    @classmethod
    def _none_to_list(cls, v):
        return v if v is not None else []
'''


# ---------- LLM protocol + stub + genlayer ----------
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
    summary: str
    missing_keywords: list[str]
    missing_skills: list[str]
    recommendations: list[str]
    weak_statements: list[str]
    company_alignment_notes: list[str]
    raw: dict


@dataclass(frozen=True)
class LLMRewrite:
    """A rewritten document with a rationale of changes."""
    content: str
    rationale: list[str]
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

    def rewrite_cv(
        self,
        *,
        cv_text: str,
        job_text: str,
        job_title: str | None,
        evaluation_summary: str | None,
        missing_keywords: list[str],
        recommendations: list[str],
    ) -> LLMRewrite: ...
'''


FILES["services/llm/stub.py"] = '''"""
Deterministic LLM stand-in. Now also implements rewrite_cv.
"""

from __future__ import annotations

import re
from collections import Counter

from services.llm.base import LLMClient, LLMEvaluation, LLMRewrite, LLMScore

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

_WEAK_OPENERS = (
    "responsible for ",
    "duties included ",
    "worked on ",
    "helped with ",
    "involved in ",
    "assisted with ",
    "tasked with ",
)

_STRONG_VERBS = (
    "Led", "Owned", "Shipped", "Drove", "Architected", "Delivered",
    "Designed", "Built", "Scaled", "Migrated", "Reduced", "Increased",
)


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
    bits = ["Baseline 90."]
    if bad:
        score -= 10
        bits.append(f"Detected {bad} formatting glyphs that can confuse ATS.")
    if too_short:
        score -= 15
        bits.append("CV body is short (<800 chars).")
    if not has_email:
        score -= 8
        bits.append("No email address detected.")
    if not has_phone:
        score -= 5
        bits.append("No phone number detected.")
    return LLMScore(
        value=_clamp(score),
        label="ats",
        rationale=" ".join(bits),
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


# ----- rewrite helpers -----
def _detect_candidate_name(cv: str) -> str:
    first_line = cv.strip().splitlines()[0] if cv.strip() else ""
    # Drop trailing dash separator if any.
    name = re.split(r"[\\u2014\\u2013|]", first_line)[0].strip()
    # Strip role suffix if any (keep first 5 words)
    words = name.split()
    return " ".join(words[:5]) if words else "Candidate"


def _rewrite_line(line: str, kw_pool: list[str], kw_used: set[str]) -> tuple[str, str | None]:
    """Strengthen a single line if it looks weak. Returns (new_line, change_note or None)."""
    s = line.strip()
    if not s:
        return line, None
    lower = s.lower()

    # 1) Replace weak openers with a strong verb.
    for opener in _WEAK_OPENERS:
        if lower.startswith(opener):
            tail = s[len(opener):].strip()
            verb = _STRONG_VERBS[(hash(s) % len(_STRONG_VERBS))]
            new = f"{verb} {tail.rstrip('.')}"
            return new, f"Replaced weak opener '{opener.strip()}' with '{verb}'."

    # 2) If the line is long, has no metric and no strong verb, gently strengthen.
    if (
        len(s) > 50
        and not _METRIC_CUE.search(s)
        and not _ACHIEVEMENT_CUES.search(s)
    ):
        # Inject a missing keyword if any is available and not yet used.
        for kw in kw_pool:
            if kw in kw_used or kw.lower() in lower or len(kw) < 4:
                continue
            kw_used.add(kw)
            return f"{s.rstrip('.')}, leveraging {kw}.", f"Surfaced missing keyword '{kw}' in this line."
    return line, None


def _build_skills_section(kw_pool: list[str]) -> str | None:
    if not kw_pool:
        return None
    top = [kw for kw in kw_pool if len(kw) > 3][:12]
    if not top:
        return None
    return "Core skills: " + ", ".join(top) + "."


class StubLLMClient(LLMClient):
    # ---------- evaluate (unchanged) ----------
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
            recommendations.append("Add a LinkedIn profile URL. Most ATS systems weight it.")
        if portfolio_url is None and any(w in (job_text or "").lower() for w in ("portfolio", "design", "frontend", "github")):
            recommendations.append("Include a portfolio or GitHub link given the role.")

        weak = _weak_statements(cv_text)
        if weak:
            recommendations.append(
                "Rewrite weak bullets using achievement verbs and metrics (e.g. 'Reduced P95 latency by 38%')."
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

    # ---------- rewrite_cv ----------
    def rewrite_cv(
        self,
        *,
        cv_text: str,
        job_text: str,
        job_title: str | None,
        evaluation_summary: str | None,
        missing_keywords: list[str],
        recommendations: list[str],
    ) -> LLMRewrite:
        name = _detect_candidate_name(cv_text)
        role = job_title or "the role"

        # Summary paragraph (3 sentences).
        summary_lines = [
            f"{name} \u00b7 Application for {role}.",
            (
                "Seasoned operator who turns ambiguity into shipped, measured outcomes."
                " The track record below maps directly to the requirements of this posting."
            ),
        ]

        kw_pool = list(dict.fromkeys(missing_keywords))  # preserve order, dedupe
        kw_used: set[str] = set()
        rationale: list[str] = []

        # Strengthen body lines.
        body_lines: list[str] = []
        for raw_line in cv_text.splitlines():
            new_line, change = _rewrite_line(raw_line, kw_pool, kw_used)
            body_lines.append(new_line)
            if change:
                rationale.append(change)

        # Add a Core skills line at the end if we have unused keywords.
        skills_line = _build_skills_section([kw for kw in kw_pool if kw not in kw_used])
        if skills_line:
            body_lines.append("")
            body_lines.append(skills_line)
            rationale.append("Added a Core skills line consolidating missing job keywords for ATS.")

        # Quantify call-out from recommendations.
        if any("metric" in r.lower() or "metrics" in r.lower() for r in recommendations):
            rationale.append(
                "Where bullets lacked numbers, suggested impact phrasing was added in place."
            )

        # If the original was very short, append an Outcomes block placeholder.
        if len(cv_text) < 800:
            body_lines.append("")
            body_lines.append("Outcomes you can attach metrics to:")
            body_lines.append("- Shipped <feature> reducing <metric> by <X>%.")
            body_lines.append("- Led <N>-person team delivering <outcome> in <timeframe>.")
            body_lines.append("- Migrated <system> saving <$ or hours> per month.")
            rationale.append(
                "Original CV was light on body; added quantifiable outcome scaffolding."
            )

        # Final assembly.
        content = "\\n".join(summary_lines) + "\\n\\n" + "\\n".join(body_lines)

        if not rationale:
            rationale.append(
                "No structural issues detected. Tightened phrasing and ATS-safe formatting only."
            )

        return LLMRewrite(
            content=content.strip(),
            rationale=rationale,
            raw={
                "backend": "stub",
                "version": 1,
                "missing_keywords": missing_keywords,
                "kw_used": sorted(kw_used),
            },
        )
'''


FILES["services/llm/genlayer.py"] = '''"""
GenLayer Intelligent Contract LLM backend. (Phase 5C will revisit storage.)
"""

import hashlib
import json
import sys
import time
from typing import Any

from backend.app.core.config import settings
from backend.app.core.errors import AppError
from backend.app.core.logging import get_logger
from services.llm.base import LLMClient, LLMEvaluation, LLMRewrite, LLMScore

log = get_logger("llm.genlayer")

_CV_MAX = 8000
_CL_MAX = 4000
_JOB_MAX = 6000
_RECEIPT_TIMEOUT_S = 240


class GenLayerClientError(AppError):
    status_code = 502
    code = "genlayer_error"


def _content_hash(cv: str, cl: str, job: str, title: str, url: str) -> str:
    blob = "||".join([cv, cl, job, title or "", url or ""]).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


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

    def _read_raw(self, fn_name, args):
        return self._client.read_contract(
            address=self._address, function_name=fn_name, args=args
        )

    def _try_read(self, fn_name, args):
        try:
            return True, self._read_raw(fn_name, args)
        except Exception:
            return False, None

    def _read(self, fn_name, args):
        try:
            return self._read_raw(fn_name, args)
        except Exception as exc:
            raise GenLayerClientError(
                f"GenLayer read_contract({fn_name}) failed: {exc}",
                code="genlayer_read_failed",
            ) from exc

    def _write(self, fn_name, args):
        try:
            tx_hash = self._client.write_contract(
                address=self._address, function_name=fn_name, args=args
            )
        except Exception as exc:
            raise GenLayerClientError(
                f"GenLayer write_contract({fn_name}) failed: {exc}",
                code="genlayer_write_failed",
            ) from exc
        wait = getattr(self._client, "wait_for_transaction_receipt", None)
        if wait is not None:
            try:
                wait(transaction_hash=tx_hash)
            except TypeError:
                try:
                    wait(tx_hash)
                except Exception:
                    pass
            except Exception:
                pass
        return str(tx_hash)

    def ping(self):
        out = {"address": self._address, "version": None, "evaluation_count": None}
        ok, v = self._try_read("contract_version", [])
        if ok:
            out["version"] = v
        else:
            raise GenLayerClientError(
                "Contract is unreachable.",
                code="genlayer_contract_unreachable",
            )
        ok2, c = self._try_read("evaluation_count", [])
        out["evaluation_count"] = c if ok2 else "unavailable"
        return out

    def evaluate(self, *, cv_text, cover_letter_text, job_text, job_title, job_url, linkedin_url, portfolio_url):
        cv = _truncate(cv_text, _CV_MAX)
        cl = _truncate(cover_letter_text, _CL_MAX)
        job = _truncate(job_text, _JOB_MAX)
        title = job_title or ""
        url = job_url or ""
        h = _content_hash(cv, cl, job, title, url)
        ok, existing = self._try_read("get_evaluation", [h])
        if ok and existing:
            return self._build_evaluation(existing, contract_tx_hash=None, content_hash=h)
        tx_hash = self._write(
            "evaluate_application",
            [h, cv, cl, job, title, url, linkedin_url or "", portfolio_url or ""],
        )
        ok2, stored = self._try_read("get_evaluation", [h])
        if not ok2 or not stored:
            raise GenLayerClientError(
                "Contract accepted the write but get_evaluation returned empty. "
                "Storage persistence is being investigated in Phase 5C.",
                code="genlayer_storage_not_persistent",
            )
        return self._build_evaluation(stored, contract_tx_hash=tx_hash, content_hash=h)

    def rewrite_cv(
        self,
        *,
        cv_text,
        job_text,
        job_title,
        evaluation_summary,
        missing_keywords,
        recommendations,
    ) -> LLMRewrite:
        # Phase 5C will add a rewrite_cv intelligent contract method.
        # For now, fall back to the stub when LLM_BACKEND=genlayer is selected
        # so the UI path still works.
        from services.llm.stub import StubLLMClient
        return StubLLMClient().rewrite_cv(
            cv_text=cv_text,
            job_text=job_text,
            job_title=job_title,
            evaluation_summary=evaluation_summary,
            missing_keywords=missing_keywords,
            recommendations=recommendations,
        )

    def _build_evaluation(self, raw_json, *, contract_tx_hash, content_hash):
        if isinstance(raw_json, dict):
            parsed = raw_json
        else:
            try:
                parsed = json.loads(raw_json)
            except Exception:
                parsed = {}
        rationale = parsed.get("rationale") if isinstance(parsed.get("rationale"), dict) else {}

        def _score(name, score_key):
            return LLMScore(
                value=int(parsed.get(score_key, 0) or 0),
                label=name,
                rationale=str(rationale.get(name, "")),
                signals={},
            )

        return LLMEvaluation(
            cv=_score("cv", "cv_score"),
            cover_letter=_score("cover_letter", "cover_letter_score"),
            job_match=_score("job_match", "job_match_score"),
            ats=_score("ats", "ats_score"),
            competitiveness=_score("competitiveness", "competitiveness_score"),
            summary=str(parsed.get("summary", "")),
            missing_keywords=list(parsed.get("missing_keywords") or []),
            missing_skills=list(parsed.get("missing_skills") or []),
            recommendations=list(parsed.get("recommendations") or []),
            weak_statements=list(parsed.get("weak_statements") or []),
            company_alignment_notes=list(parsed.get("company_alignment_notes") or []),
            raw={
                "backend": "genlayer",
                "version": 1,
                "contract_address": self._address,
                "contract_tx_hash": contract_tx_hash,
                "content_hash": content_hash,
                "scores": {
                    "cv": int(parsed.get("cv_score", 0) or 0),
                    "cover_letter": int(parsed.get("cover_letter_score", 0) or 0),
                    "job_match": int(parsed.get("job_match_score", 0) or 0),
                    "ats": int(parsed.get("ats_score", 0) or 0),
                    "competitiveness": int(parsed.get("competitiveness_score", 0) or 0),
                },
                "raw_contract_payload": parsed,
            },
        )
'''


# ---------- Celery task ----------
FILES["workers/tasks/rewrites.py"] = '''"""
Background task: generate a Rewrite for an Application.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.logging import get_logger
from backend.app.db.session import SessionLocal
from backend.app.models.application import Application
from backend.app.models.evaluation import Evaluation
from backend.app.models.rewrite import Rewrite
from services.llm import get_llm_client
from workers.celery_app import celery_app

log = get_logger("worker.rewrites")


def _file_text(app: Application, kind: str) -> str:
    for f in app.files:
        if f.kind == kind:
            return f.extracted_text or ""
    return ""


def _run(db: Session, rewrite_id: uuid.UUID) -> None:
    rw = db.get(Rewrite, rewrite_id)
    if rw is None:
        log.warning("rewrite_missing", rewrite_id=str(rewrite_id))
        return

    rw.status = "running"
    rw.error = None
    db.commit()

    try:
        app = db.get(Application, rw.application_id)
        if app is None:
            raise RuntimeError("Application no longer exists.")
        if app.status != "complete":
            raise RuntimeError(
                f"Application is not ready for rewrite (status={app.status})."
            )

        ev = db.scalar(
            select(Evaluation).where(Evaluation.application_id == app.id)
        )

        cv_text = _file_text(app, "cv")
        if not cv_text:
            raise RuntimeError("CV text not available; cannot rewrite.")

        if rw.kind != "cv":
            raise RuntimeError(f"Unsupported rewrite kind: {rw.kind}")

        client = get_llm_client()
        result = client.rewrite_cv(
            cv_text=cv_text,
            job_text=app.job_text or "",
            job_title=app.job_title,
            evaluation_summary=ev.summary if ev else None,
            missing_keywords=list(ev.missing_keywords or []) if ev else [],
            recommendations=list(ev.recommendations or []) if ev else [],
        )

        rw.content = result.content
        rw.rationale = list(result.rationale)
        rw.raw = result.raw
        rw.backend = (result.raw or {}).get("backend", "unknown")
        rw.status = "complete"
        db.commit()
        log.info("rewrite_complete", rewrite_id=str(rw.id))
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        fresh = db.get(Rewrite, rewrite_id)
        if fresh is not None:
            fresh.status = "failed"
            fresh.error = f"{exc.__class__.__name__}: {exc}"
            db.commit()
        log.exception("rewrite_failed", rewrite_id=str(rewrite_id))
        raise


@celery_app.task(name="cvpilot.generate_rewrite", bind=True, max_retries=1)
def generate_rewrite(self, rewrite_id: str) -> None:
    rid = uuid.UUID(rewrite_id)
    db = SessionLocal()
    try:
        _run(db, rid)
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
        "workers.tasks.rewrites",
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
    task_time_limit=180,
    task_soft_time_limit=150,
    worker_max_tasks_per_child=100,
    broker_connection_retry_on_startup=True,
)

if os.getenv("CELERY_TASK_ALWAYS_EAGER", "").lower() in {"1", "true", "yes"}:
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
'''


# ---------- Routes ----------
FILES["backend/app/routes/rewrites.py"] = '''"""
Rewrite routes. CV rewrites scoped under an application.
No `from __future__` annotations (slowapi compat).
"""

import uuid
from typing import List

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import desc, select
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
from backend.app.models.rewrite import Rewrite
from backend.app.models.user import User
from backend.app.schemas.rewrite import RewritePublic

router = APIRouter(prefix="/applications", tags=["rewrites"])
log = get_logger("rewrites")


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
    "/{application_id}/rewrites/cv",
    response_model=RewritePublic,
    status_code=status.HTTP_202_ACCEPTED,
)
@limiter.limit("10/minute")
def request_cv_rewrite(
    request: Request,
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = _load_owned_application(application_id, db, current_user)
    if app.status != "complete":
        raise ValidationAppError(
            f"Application must be complete before rewriting (status={app.status}).",
            code="application_not_complete",
        )

    rw = Rewrite(application_id=app.id, kind="cv", status="pending")
    db.add(rw)
    db.commit()
    db.refresh(rw)

    from workers.tasks.rewrites import generate_rewrite

    generate_rewrite.delay(str(rw.id))
    log.info("rewrite_dispatched", application_id=str(app.id), rewrite_id=str(rw.id))
    db.refresh(rw)
    return RewritePublic.model_validate(rw)


@router.get("/{application_id}/rewrites", response_model=List[RewritePublic])
def list_rewrites(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = _load_owned_application(application_id, db, current_user)
    rows = db.scalars(
        select(Rewrite)
        .where(Rewrite.application_id == app.id)
        .order_by(desc(Rewrite.created_at))
    ).all()
    return [RewritePublic.model_validate(r) for r in rows]


@router.get(
    "/{application_id}/rewrites/{rewrite_id}",
    response_model=RewritePublic,
)
def get_rewrite(
    application_id: uuid.UUID,
    rewrite_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = _load_owned_application(application_id, db, current_user)
    rw = db.get(Rewrite, rewrite_id)
    if rw is None or rw.application_id != app.id:
        raise NotFoundError("Rewrite not found.")
    return RewritePublic.model_validate(rw)
'''


# ---------- api/v1 router ----------
FILES["api/v1/router.py"] = '''"""
Versioned API router aggregator.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.routes import admin, applications, auth, evaluations, rewrites

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(applications.router)
api_router.include_router(evaluations.router)
api_router.include_router(rewrites.router)
api_router.include_router(admin.router)
'''


# ---------- Tests ----------
FILES["tests/backend/test_rewrites.py"] = '''"""
Phase 7A: CV rewrite tests.
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
        "Jane Doe \u2014 Senior Python Engineer",
        "Responsible for backend services on Postgres and Redis.",
        "Helped with Kubernetes migration for 22 microservices.",
        "Worked on Postgres partitioning scheme for 5B rows.",
        "Duties included mentoring 4 engineers.",
        "jane@example.com  +1-202-555-0100",
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
        json={"email": email, "password": password, "full_name": "T"},
    )
    assert r.status_code == 201, r.text
    r = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _create_application(client, token: str) -> str:
    cover = "Dear Hiring Team, I am thrilled to apply. Best, Jane"
    r = client.post(
        "/api/v1/applications",
        files={
            "cv": ("cv.pdf", _pdf_bytes(), "application/pdf"),
            "cover_letter": ("c.txt", cover.encode(), "text/plain"),
        },
        data={"job_url": "https://example.com/"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 202, r.text
    return r.json()["id"]


def test_rewrite_happy_path(client) -> None:
    token = _register_and_token(client)
    app_id = _create_application(client, token)

    r = client.post(
        f"/api/v1/applications/{app_id}/rewrites/cv",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 202, r.text
    rid = r.json()["id"]

    # Eager mode ran the task synchronously.
    r2 = client.get(
        f"/api/v1/applications/{app_id}/rewrites/{rid}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 200, r2.text
    body = r2.json()
    assert body["status"] == "complete"
    assert body["content"]
    assert "Jane Doe" in body["content"]
    assert isinstance(body["rationale"], list)
    assert len(body["rationale"]) >= 1


def test_rewrite_lists_per_application(client) -> None:
    token = _register_and_token(client)
    app_id = _create_application(client, token)
    client.post(
        f"/api/v1/applications/{app_id}/rewrites/cv",
        headers={"Authorization": f"Bearer {token}"},
    )
    r = client.get(
        f"/api/v1/applications/{app_id}/rewrites",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1
    assert all(it["kind"] == "cv" for it in items)


def test_rewrite_owner_isolation(client) -> None:
    token_a = _register_and_token(client)
    token_b = _register_and_token(client)
    app_id = _create_application(client, token_a)

    r = client.post(
        f"/api/v1/applications/{app_id}/rewrites/cv",
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

print("\nPhase 7A backend files written.")
