"""
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
    task_time_limit=540,
    task_soft_time_limit=480,
    worker_max_tasks_per_child=100,
    broker_connection_retry_on_startup=True,
)

if os.getenv("CELERY_TASK_ALWAYS_EAGER", "").lower() in {"1", "true", "yes"}:
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
