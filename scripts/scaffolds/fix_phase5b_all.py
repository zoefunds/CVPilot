"""
Phase 5B fix-up:
  1. Buffer compat shim in services/llm/genlayer.py so genlayer-py 0.8.x
     imports successfully on Python 3.11.
  2. EvaluationPublic schema coerces NULL JSON list columns to [].
  3. Replace contracts/cvpilot/cvpilot_contract.py with the actually-deployed
     source so the repo is the canonical record of what's on-chain.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
FILES: dict[str, str] = {}


# -----------------------------------------------------------------------------
# 1. services/llm/genlayer.py — add Buffer shim
# -----------------------------------------------------------------------------
FILES["services/llm/genlayer.py"] = '''"""
GenLayer Intelligent Contract LLM backend.

Calls the deployed CVPilotEvaluator contract on StudioNet:
  evaluate_application(content_hash, cv, cover_letter, job, title, url, linkedin, portfolio)

The contract stores results by content_hash for idempotency. We:
  1. Compute the SHA-256 content hash of (cv || cl || job || title || url).
  2. Check the on-chain cache via get_evaluation(hash).
  3. If miss, write evaluate_application(...), wait for receipt, then re-read.
  4. Parse the returned JSON into LLMEvaluation and attach the tx hash.
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

_RECEIPT_TIMEOUT_S = 180


class GenLayerClientError(AppError):
    status_code = 502
    code = "genlayer_error"


def _content_hash(cv: str, cl: str, job: str, title: str, url: str) -> str:
    blob = "||".join([cv, cl, job, title or "", url or ""]).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _truncate(s: str | None, limit: int) -> str:
    if not s:
        return ""
    return s if len(s) <= limit else s[:limit]


def _install_buffer_shim() -> None:
    """
    genlayer-py 0.8.x imports `from collections.abc import Buffer`, which
    only exists in Python 3.12+ (PEP 688). On 3.11 we patch it in from
    typing_extensions (already a transitive dependency).
    """
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

    # ------------------------------------------------------------------------
    def _read(self, fn_name: str, args: list) -> Any:
        try:
            return self._client.read_contract(
                address=self._address,
                function_name=fn_name,
                function_args=args,
            )
        except Exception as exc:
            raise GenLayerClientError(
                f"GenLayer read_contract({fn_name}) failed: {exc}",
                code="genlayer_read_failed",
            ) from exc

    def _write(self, fn_name: str, args: list, *, pending_hash: str | None = None) -> str:
        try:
            tx_hash = self._client.write_contract(
                address=self._address,
                function_name=fn_name,
                function_args=args,
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
                wait(tx_hash)
            except Exception as exc:
                log.warning("genlayer_receipt_wait_failed", error=str(exc))
        elif pending_hash:
            deadline = time.time() + _RECEIPT_TIMEOUT_S
            while time.time() < deadline:
                time.sleep(2)
                try:
                    if self._read("has_evaluation", [pending_hash]):
                        break
                except Exception:
                    continue

        return str(tx_hash)

    # ------------------------------------------------------------------------
    def ping(self) -> dict:
        return {
            "address": self._address,
            "version": self._read("contract_version", []),
            "evaluation_count": self._read("evaluation_count", []),
        }

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
        h = _content_hash(cv, cl, job, title, url)

        existing = self._read("get_evaluation", [h])
        if existing:
            log.info("genlayer_cache_hit", content_hash=h[:12])
            return self._build_evaluation(existing, contract_tx_hash=None, content_hash=h)

        log.info("genlayer_evaluate_dispatch", content_hash=h[:12])
        tx_hash = self._write(
            "evaluate_application",
            [h, cv, cl, job, title, url, linkedin_url or "", portfolio_url or ""],
            pending_hash=h,
        )
        log.info("genlayer_evaluate_landed", content_hash=h[:12], tx_hash=tx_hash)

        stored = self._read("get_evaluation", [h])
        if not stored:
            raise GenLayerClientError(
                "Contract returned empty evaluation after write.",
                code="genlayer_empty_after_write",
            )
        return self._build_evaluation(stored, contract_tx_hash=tx_hash, content_hash=h)

    # ------------------------------------------------------------------------
    def _build_evaluation(
        self,
        raw_json: Any,
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

        rationale = parsed.get("rationale") if isinstance(parsed.get("rationale"), dict) else {}

        def _score(name: str, score_key: str) -> LLMScore:
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


# -----------------------------------------------------------------------------
# 2. backend/app/schemas/evaluation.py — coerce None -> [] on list fields
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

    @field_validator(
        "recommendations",
        "missing_keywords",
        "missing_skills",
        "weak_statements",
        "company_alignment_notes",
        mode="before",
    )
    @classmethod
    def _none_to_list(cls, v):
        if v is None:
            return []
        return v
'''


# -----------------------------------------------------------------------------
# 3. contracts/cvpilot/cvpilot_contract.py — sync to actually-deployed source
# -----------------------------------------------------------------------------
FILES["contracts/cvpilot/cvpilot_contract.py"] = '''# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
#
# THIS IS THE CONTRACT ACTUALLY DEPLOYED ON STUDIONET.
# Deployed address: 0xDb65251DDB51Fcb20dfA9bbaE17D80efa4cd8bac
# Version: 0.1.0
#
# Do not edit this file unless you intend to redeploy the contract
# and update GENLAYER_CONTRACT_ADDRESS in .env.

from genlayer import *
import json


_CONTRACT_VERSION = "0.1.0"


class CVPilotEvaluator(gl.Contract):

    def __init__(self):
        self.evaluations = {}
        self.total_evaluated = 0

    # -------------------------
    # Views
    # -------------------------
    @gl.public.view
    def contract_version(self):
        return _CONTRACT_VERSION

    @gl.public.view
    def evaluation_count(self):
        return self.total_evaluated

    @gl.public.view
    def get_evaluation(self, content_hash):
        if content_hash in self.evaluations:
            return self.evaluations[content_hash]
        return ""

    @gl.public.view
    def has_evaluation(self, content_hash):
        return content_hash in self.evaluations

    # -------------------------
    # Write
    # -------------------------
    @gl.public.write
    def evaluate_application(
        self,
        content_hash,
        cv_text,
        cover_letter,
        job_text,
        job_title,
        job_url,
        linkedin_url,
        portfolio_url,
    ):

        if content_hash in self.evaluations:
            return self.evaluations[content_hash]

        prompt = f"""
You are an ATS and recruiter system.

Return ONLY valid JSON with:
cv_score, cover_letter_score, job_match_score,
ats_score, competitiveness_score,
summary, missing_keywords, missing_skills,
recommendations, weak_statements,
company_alignment_notes,
rationale object.

JOB TITLE:
{job_title}

JOB:
{job_text}

CV:
{cv_text}

COVER LETTER:
{cover_letter}
"""

        result = gl.nondet.exec_prompt(prompt)

        # basic safety fallback (IMPORTANT for schema stability)
        try:
            parsed = json.loads(result)
        except:
            parsed = {
                "cv_score": 0,
                "cover_letter_score": 0,
                "job_match_score": 0,
                "ats_score": 0,
                "competitiveness_score": 0,
                "summary": result,
                "missing_keywords": [],
                "missing_skills": [],
                "recommendations": [],
                "weak_statements": [],
                "company_alignment_notes": [],
                "rationale": {},
            }

        final_result = json.dumps(parsed)

        self.evaluations[content_hash] = final_result
        self.total_evaluated += 1
        return final_result
'''


def write(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  wrote {rel}")


def main() -> None:
    for rel, content in FILES.items():
        write(rel, content)
    print("\nPhase 5B fix-up complete.")


if __name__ == "__main__":
    main()
