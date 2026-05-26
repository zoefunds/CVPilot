"""
Celery application factory.
"""

from __future__ import annotations

import os
import ssl

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
    task_time_limit=1500,
    task_soft_time_limit=1380,
    worker_max_tasks_per_child=100,
    broker_connection_retry_on_startup=True,
)

# TLS Redis (rediss://) requires explicit ssl_cert_reqs. Apply via config
# dict so we do not depend on URL query-string parsing.
_broker_url = str(settings.celery_broker_url or "")
_backend_url = str(settings.celery_result_backend or "")
if _broker_url.startswith("rediss"):
    celery_app.conf.broker_use_ssl = {"ssl_cert_reqs": ssl.CERT_REQUIRED}
if _backend_url.startswith("rediss"):
    celery_app.conf.redis_backend_use_ssl = {"ssl_cert_reqs": ssl.CERT_REQUIRED}

if os.getenv("CELERY_TASK_ALWAYS_EAGER", "").lower() in {"1", "true", "yes"}:
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
