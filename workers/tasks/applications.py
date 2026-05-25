"""
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
