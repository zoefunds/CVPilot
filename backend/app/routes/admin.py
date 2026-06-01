"""
Admin routes. All gated by get_current_admin (is_superuser=true).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from backend.app.core.errors import NotFoundError
from backend.app.db.session import get_db
from backend.app.dependencies.admin import get_current_admin
from backend.app.models.application import Application
from backend.app.models.evaluation import Evaluation
from backend.app.models.user import User
from backend.app.schemas.admin import (
    AdminApplicationListItem,
    AdminStats,
    AdminUserListItem,
)
from backend.app.schemas.application import ApplicationPublic
from backend.app.schemas.evaluation import EvaluationPublic

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/stats", response_model=AdminStats)
def stats(db: Session = Depends(get_db)) -> AdminStats:
    user_count = db.scalar(select(func.count(User.id))) or 0
    app_count = db.scalar(select(func.count(Application.id))) or 0

    rows = db.execute(
        select(Application.status, func.count(Application.id))
        .group_by(Application.status)
    ).all()
    by_status = {str(s): int(c) for s, c in rows}

    eval_complete = (
        db.scalar(
            select(func.count(Evaluation.id)).where(Evaluation.status == "complete")
        )
        or 0
    )
    eval_failed = (
        db.scalar(
            select(func.count(Evaluation.id)).where(Evaluation.status == "failed")
        )
        or 0
    )

    since = datetime.now(UTC) - timedelta(hours=24)
    last_24h_users = (
        db.scalar(select(func.count(User.id)).where(User.created_at >= since)) or 0
    )
    last_24h_apps = (
        db.scalar(
            select(func.count(Application.id)).where(Application.created_at >= since)
        )
        or 0
    )

    return AdminStats(
        user_count=int(user_count),
        application_count=int(app_count),
        evaluations_complete=int(eval_complete),
        evaluations_failed=int(eval_failed),
        last_24h_users=int(last_24h_users),
        last_24h_applications=int(last_24h_apps),
        by_status=by_status,
    )


@router.get("/users", response_model=list[AdminUserListItem])
def list_users(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> list[AdminUserListItem]:
    counts_sq = (
        select(
            Application.user_id.label("uid"),
            func.count(Application.id).label("cnt"),
            func.max(Application.created_at).label("last_at"),
        )
        .group_by(Application.user_id)
        .subquery()
    )
    rows = db.execute(
        select(User, func.coalesce(counts_sq.c.cnt, 0), counts_sq.c.last_at)
        .outerjoin(counts_sq, counts_sq.c.uid == User.id)
        .order_by(desc(User.created_at))
        .limit(limit)
        .offset(offset)
    ).all()
    return [
        AdminUserListItem(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            is_active=u.is_active,
            is_premium=u.is_premium,
            is_superuser=u.is_superuser,
            created_at=u.created_at,
            application_count=int(cnt or 0),
            last_application_at=last_at,
        )
        for u, cnt, last_at in rows
    ]


@router.get("/users/{user_id}", response_model=AdminUserListItem)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)) -> AdminUserListItem:
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found.")
    cnt = (
        db.scalar(
            select(func.count(Application.id)).where(Application.user_id == user_id)
        )
        or 0
    )
    last = db.scalar(
        select(func.max(Application.created_at)).where(Application.user_id == user_id)
    )
    return AdminUserListItem(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_premium=user.is_premium,
        is_superuser=user.is_superuser,
        created_at=user.created_at,
        application_count=int(cnt or 0),
        last_application_at=last,
    )


@router.get("/applications", response_model=list[AdminApplicationListItem])
def list_applications(
    status: str | None = Query(default=None),
    user_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> list[AdminApplicationListItem]:
    q = (
        select(
            Application,
            User.email,
            Evaluation.competitiveness_score,
            Evaluation.id,
        )
        .join(User, User.id == Application.user_id)
        .outerjoin(Evaluation, Evaluation.application_id == Application.id)
        .order_by(desc(Application.created_at))
        .limit(limit)
        .offset(offset)
    )
    if status:
        q = q.where(Application.status == status)
    if user_id:
        q = q.where(Application.user_id == user_id)

    rows = db.execute(q).all()
    return [
        AdminApplicationListItem(
            id=app.id,
            user_id=app.user_id,
            user_email=email,
            job_url=app.job_url,
            job_title=app.job_title,
            status=app.status,
            created_at=app.created_at,
            has_evaluation=ev_id is not None,
            competitiveness=comp,
        )
        for app, email, comp, ev_id in rows
    ]


@router.get("/applications/{application_id}", response_model=ApplicationPublic)
def get_application(
    application_id: uuid.UUID, db: Session = Depends(get_db)
) -> ApplicationPublic:
    app = db.get(Application, application_id)
    if app is None:
        raise NotFoundError("Application not found.")
    return ApplicationPublic.model_validate(app)


@router.get(
    "/applications/{application_id}/evaluation",
    response_model=EvaluationPublic,
)
def get_evaluation(
    application_id: uuid.UUID, db: Session = Depends(get_db)
) -> EvaluationPublic:
    app = db.get(Application, application_id)
    if app is None:
        raise NotFoundError("Application not found.")
    ev = db.scalar(
        select(Evaluation).where(Evaluation.application_id == application_id)
    )
    if ev is None:
        raise NotFoundError("Evaluation not yet created for this application.")
    return EvaluationPublic.model_validate(ev)
