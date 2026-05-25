"""
Background task: run the evaluation orchestrator and emit metrics.
"""

from __future__ import annotations

import time
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.logging import get_logger
from backend.app.core.metrics import evaluation_duration_seconds, evaluations_total
from backend.app.core.wallet_crypto import decrypt_secret
from backend.app.db.session import SessionLocal
from backend.app.models.application import Application
from backend.app.models.evaluation import Evaluation
from backend.app.models.user import User
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


def _user_private_key(db: Session, user_id) -> str | None:
    if settings.llm_backend != "genlayer":
        return None
    user = db.get(User, user_id)
    if user is None or not user.encrypted_private_key:
        return None
    try:
        return decrypt_secret(user.encrypted_private_key)
    except Exception as exc:
        log.error("user_wallet_decrypt_failed", user_id=str(user_id), error=str(exc))
        return None


def _run(db: Session, application_id: uuid.UUID) -> None:
    app = db.get(Application, application_id)
    if app is None:
        return
    if app.status != "ready":
        return

    ev = _get_or_create_evaluation(db, application_id)
    ev.status = "running"
    ev.error = None
    db.commit()

    app.status = "evaluating"
    db.commit()

    started = time.perf_counter()
    backend_label = settings.llm_backend
    final_status = "failed"
    try:
        pk = _user_private_key(db, app.user_id)
        outcome = run_evaluation(
            cv_text=_file_text(app, "cv"),
            cover_letter_text=_file_text(app, "cover_letter"),
            job_text=app.job_text or "",
            job_title=app.job_title,
            job_url=app.job_url,
            linkedin_url=app.linkedin_url,
            portfolio_url=app.portfolio_url,
            account_private_key=pk,
        )
        r = outcome.report
        backend_label = outcome.backend
        ev.backend = outcome.backend
        ev.cv_score = r.cv.value
        ev.cover_letter_score = r.cover_letter.value
        ev.job_match_score = r.job_match.value
        ev.ats_score = r.ats.value
        ev.competitiveness_score = r.competitiveness.value
        ev.overall_score = r.overall.value
        ev.summary = r.summary
        ev.improved_positioning = r.improved_positioning
        ev.recommendations = list(r.recommendations)
        ev.missing_keywords = list(r.missing_keywords)
        ev.missing_skills = list(r.missing_skills)
        ev.weak_statements = list(r.weak_statements)
        ev.company_alignment_notes = list(r.company_alignment_notes)
        ev.strengths = list(r.strengths)
        ev.risks = list(r.risks)
        ev.rationale = dict(r.rationale) if r.rationale else None
        ev.raw = r.raw
        ev.contract_tx_hash = (r.raw or {}).get("contract_tx_hash")
        ev.content_hash = (r.raw or {}).get("content_hash")
        ev.contract_address = (r.raw or {}).get("contract_address") or settings.genlayer_contract_address
        ev.status = "complete"
        app.status = "complete"
        db.commit()
        final_status = "complete"
        log.info(
            "evaluation_complete",
            application_id=str(application_id),
            overall=r.overall.value,
            backend=outcome.backend,
            contract_tx_hash=ev.contract_tx_hash,
        )
    except Exception as exc:
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
    finally:
        evaluation_duration_seconds.labels(backend=backend_label).observe(
            time.perf_counter() - started
        )
        evaluations_total.labels(backend=backend_label, status=final_status).inc()


@celery_app.task(name="cvpilot.evaluate_application", bind=True, max_retries=2)
def evaluate_application(self, application_id: str) -> None:
    aid = uuid.UUID(application_id)
    db = SessionLocal()
    try:
        _run(db, aid)
    finally:
        db.close()
