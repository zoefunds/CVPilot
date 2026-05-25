"""
Applications API. Enforces a balance gate before accepting a submission
when running against the GenLayer backend (so users never end up with
stuck pending or failed-forbidden evaluations because their wallet has
no GEN to pay validators).
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.errors import (
    AppError,
    ForbiddenError,
    NotFoundError,
    ValidationAppError,
)
from backend.app.core.logging import get_logger
from backend.app.db.session import get_db
from backend.app.dependencies.auth import get_current_user
from backend.app.dependencies.rate_limit import limiter
from backend.app.models.application import Application, FileAsset
from backend.app.models.user import User
from backend.app.schemas.application import (
    ApplicationListItem,
    ApplicationPublic,
)
from services.genlayer import get_balance_wei
from services.storage import get_storage

router = APIRouter(prefix="/applications", tags=["applications"])
log = get_logger("applications")

_ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}


class InsufficientBalanceError(AppError):
    status_code = 402
    code = "insufficient_balance"


def _validate_upload(file: UploadFile, label: str) -> bytes:
    if file is None or not file.filename:
        raise ValidationAppError(f"{label} file is required.", code=f"{label}_missing")
    data = file.file.read()
    max_bytes = settings.storage_max_upload_mb * 1024 * 1024
    if len(data) == 0:
        raise ValidationAppError(f"{label} file is empty.", code=f"{label}_empty")
    if len(data) > max_bytes:
        raise ValidationAppError(
            f"{label} file exceeds {settings.storage_max_upload_mb} MB limit.",
            code=f"{label}_too_large",
        )
    if file.content_type and file.content_type not in _ALLOWED_CONTENT_TYPES:
        log.info("upload_unexpected_content_type", label=label, content_type=file.content_type)
    return data


def _store_file(storage, *, user_id, application_id, kind, filename, data, content_type):
    safe_name = filename.replace("/", "_").replace("\\", "_")
    key = f"{user_id}/{application_id}/{kind}-{uuid.uuid4().hex}-{safe_name}"
    stored = storage.save(key, data, content_type)
    return FileAsset(
        application_id=application_id,
        kind=kind,
        original_filename=filename,
        storage_key=stored.key,
        content_type=content_type,
        byte_size=stored.byte_size,
    )


def _check_balance_or_raise(user: User) -> None:
    """Balance gate. Only active when LLM_BACKEND=genlayer."""
    if settings.llm_backend != "genlayer":
        return
    if not user.wallet_address:
        raise InsufficientBalanceError(
            "Your account does not have a wallet yet. Sign out and register again.",
            code="wallet_missing",
        )
    balance = get_balance_wei(user.wallet_address)
    required = settings.min_submit_balance_wei
    if balance < required:
        raise InsufficientBalanceError(
            "Your wallet does not have enough GEN to submit an evaluation.",
            code="insufficient_balance",
            details={
                "wallet_address": user.wallet_address,
                "balance_wei": balance,
                "required_wei": required,
            },
        )


@router.post("", response_model=ApplicationPublic, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("20/minute")
def create_application(
    request: Request,
    job_url: str = Form(..., min_length=8, max_length=2048),
    linkedin_url: Optional[str] = Form(default=None, max_length=2048),
    portfolio_url: Optional[str] = Form(default=None, max_length=2048),
    cv: UploadFile = File(...),
    cover_letter: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not (job_url.startswith("http://") or job_url.startswith("https://")):
        raise ValidationAppError("job_url must start with http or https", code="job_url_invalid")

    _check_balance_or_raise(current_user)

    cv_bytes = _validate_upload(cv, "cv")
    cl_bytes = _validate_upload(cover_letter, "cover_letter")

    application = Application(
        user_id=current_user.id,
        job_url=job_url,
        linkedin_url=linkedin_url or None,
        portfolio_url=portfolio_url or None,
        status="pending",
    )
    db.add(application)
    db.flush()

    storage = get_storage()
    db.add(_store_file(
        storage, user_id=current_user.id, application_id=application.id,
        kind="cv", filename=cv.filename, data=cv_bytes,
        content_type=cv.content_type or "application/octet-stream",
    ))
    db.add(_store_file(
        storage, user_id=current_user.id, application_id=application.id,
        kind="cover_letter", filename=cover_letter.filename, data=cl_bytes,
        content_type=cover_letter.content_type or "application/octet-stream",
    ))
    db.commit()
    db.refresh(application)

    from workers.tasks.applications import process_application
    process_application.delay(str(application.id))
    log.info("application_created", application_id=str(application.id), user_id=str(current_user.id))
    return ApplicationPublic.model_validate(application)


@router.get("", response_model=list[ApplicationListItem])
def list_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Dashboard list: show applications that produced a real on-chain write,
    plus in-progress and failed ones. Hide completed evaluations that have
    no contract_tx_hash (cache hits or stub-only) so the dashboard reflects
    real chain activity.
    """
    from backend.app.models.evaluation import Evaluation

    rows = db.execute(
        select(Application)
        .outerjoin(Evaluation, Evaluation.application_id == Application.id)
        .where(Application.user_id == current_user.id)
        .where(
            (Application.status != "complete")
            | (Evaluation.contract_tx_hash.isnot(None))
        )
        .order_by(Application.created_at.desc())
    ).scalars().unique().all()
    return [ApplicationListItem.model_validate(r) for r in rows]


@router.get("/{application_id}", response_model=ApplicationPublic)
def get_application(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = db.get(Application, application_id)
    if app is None:
        raise NotFoundError("Application not found.")
    if app.user_id != current_user.id:
        raise ForbiddenError("You do not own this application.")
    return ApplicationPublic.model_validate(app)
