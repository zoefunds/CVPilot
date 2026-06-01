"""
Phase 5B Part 2: real GenLayer LLM client + persistence of contract_tx_hash.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")

FILES: dict[str, str] = {}

# -----------------------------------------------------------------------------
# services/llm/genlayer.py
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
import time
from typing import Any

from backend.app.core.config import settings
from backend.app.core.errors import AppError
from backend.app.core.logging import get_logger
from services.llm.base import LLMClient, LLMEvaluation, LLMScore

log = get_logger("llm.genlayer")

# Conservative truncations to match the contract\'s own prompt budgets.
_CV_MAX = 8000
_CL_MAX = 4000
_JOB_MAX = 6000

_RECEIPT_TIMEOUT_S = 180  # StudioNet typically finalises in a few seconds; allow margin.


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


def _import_sdk():
    """Lazy import so the rest of the app still boots when genlayer-py is missing."""
    try:
        from genlayer_py import create_account, create_client  # type: ignore
        from genlayer_py.chains import studionet  # type: ignore
    except Exception as exc:  # pragma: no cover
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
                # Older/newer SDKs sometimes use a different kwarg name.
                self._account = create_account(private_key=pk)
        else:
            # Ephemeral account for transactions (fine on StudioNet).
            self._account = create_account()

        self._client = create_client(chain=studionet, account=self._account)
        self._address = settings.genlayer_contract_address
        log.info(
            "genlayer_client_ready",
            address=self._address,
            account=str(getattr(self._account, "address", "")),
        )

    # -------------------------------------------------------------------------
    # SDK helpers
    # -------------------------------------------------------------------------
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

    def _write(self, fn_name: str, args: list) -> str:
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

        # Wait for receipt (some SDK builds expose wait_for_transaction_receipt).
        wait = getattr(self._client, "wait_for_transaction_receipt", None)
        if wait is not None:
            try:
                wait(transaction_hash=tx_hash)
            except TypeError:
                wait(tx_hash)
            except Exception as exc:
                # Don\'t hard-fail: the read-back below will tell us if it landed.
                log.warning("genlayer_receipt_wait_failed", error=str(exc))
        else:
            # Fallback poll: read until we see the hash present.
            deadline = time.time() + _RECEIPT_TIMEOUT_S
            while time.time() < deadline:
                time.sleep(2)
                if self._read("has_evaluation", [self._pending_hash]):  # noqa: SLF001
                    break

        return str(tx_hash)

    # -------------------------------------------------------------------------
    # Public connectivity probe
    # -------------------------------------------------------------------------
    def ping(self) -> dict:
        version = self._read("contract_version", [])
        count = self._read("evaluation_count", [])
        return {
            "address": self._address,
            "version": version,
            "evaluation_count": count,
        }

    # -------------------------------------------------------------------------
    # Main evaluate
    # -------------------------------------------------------------------------
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
        self._pending_hash = h  # noqa: SLF001  (used by fallback poll)

        # 1) Cache check
        existing = self._read("get_evaluation", [h])
        if existing:
            log.info("genlayer_cache_hit", content_hash=h[:12])
            return self._build_evaluation(existing, contract_tx_hash=None, content_hash=h)

        log.info("genlayer_evaluate_dispatch", content_hash=h[:12])
        tx_hash = self._write(
            "evaluate_application",
            [h, cv, cl, job, title, url, linkedin_url or "", portfolio_url or ""],
        )
        log.info("genlayer_evaluate_landed", content_hash=h[:12], tx_hash=tx_hash)

        # 2) Read back the now-persisted JSON
        stored = self._read("get_evaluation", [h])
        if not stored:
            raise GenLayerClientError(
                "Contract returned empty evaluation after write.",
                code="genlayer_empty_after_write",
            )
        return self._build_evaluation(stored, contract_tx_hash=tx_hash, content_hash=h)

    # -------------------------------------------------------------------------
    # JSON -> LLMEvaluation
    # -------------------------------------------------------------------------
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
# workers/tasks/evaluations.py: persist contract_tx_hash
# -----------------------------------------------------------------------------
FILES["workers/tasks/evaluations.py"] = '''"""
Background task: run the evaluation orchestrator on a ready Application
and persist results (including any GenLayer contract tx hash).
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

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
        ev.contract_tx_hash = (r.raw or {}).get("contract_tx_hash")
        ev.status = "complete"
        app.status = "complete"
        db.commit()
        log.info(
            "evaluation_complete",
            application_id=str(application_id),
            competitiveness=r.competitiveness.value,
            backend=outcome.backend,
            contract_tx_hash=ev.contract_tx_hash,
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


def write(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  wrote {rel}")


def main() -> None:
    print(f"Phase 5B Part 2 into: {ROOT}")
    for rel, content in FILES.items():
        write(rel, content)
    print("\nPhase 5B Part 2 files written.")


if __name__ == "__main__":
    main()
