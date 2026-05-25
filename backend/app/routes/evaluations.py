"""
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
