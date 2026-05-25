"""
Phase 12A: observability scaffold.
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
FILES: dict[str, str] = {}


# -----------------------------------------------------------------------------
# Custom business metrics
# -----------------------------------------------------------------------------
FILES["backend/app/core/metrics.py"] = '''"""
Custom CVPilot business metrics. Standard HTTP metrics are emitted by the
Instrumentator in main.py automatically (request_count, duration, etc.).
This module adds product-specific counters.
"""

from __future__ import annotations

from prometheus_client import Counter, Histogram

# Evaluations
evaluations_total = Counter(
    "cvpilot_evaluations_total",
    "Evaluations completed, partitioned by backend and final status.",
    labelnames=("backend", "status"),
)
evaluation_duration_seconds = Histogram(
    "cvpilot_evaluation_duration_seconds",
    "End-to-end evaluation duration (Celery task wall-clock).",
    labelnames=("backend",),
    buckets=(1, 5, 10, 30, 60, 120, 240, 480),
)

# Applications
applications_submitted_total = Counter(
    "cvpilot_applications_submitted_total",
    "Application submissions partitioned by result of the balance / validation gate.",
    labelnames=("result",),  # accepted | rejected_balance | rejected_validation
)

# Wallet
wallet_send_total = Counter(
    "cvpilot_wallet_send_total",
    "Outbound GEN transfers partitioned by status.",
    labelnames=("status",),  # success | failed
)

# Contract reads (only used when we explicitly probe)
contract_probe_total = Counter(
    "cvpilot_contract_probe_total",
    "Health probes of the deployed CVPilot contract.",
    labelnames=("result",),  # ok | failed
)
'''


# -----------------------------------------------------------------------------
# Request log middleware
# -----------------------------------------------------------------------------
FILES["backend/app/middleware/request_log.py"] = '''"""
Structured per-request log middleware.

Emits one log line per completed request via structlog, including:
  method, route (template), status, duration_ms, request_id, user_id?

The RequestIDMiddleware (already mounted) populates structlog contextvars
with request_id; this middleware adds method/path/status/duration on completion.
"""

from __future__ import annotations

import time

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.app.core.logging import get_logger

log = get_logger("http")


def _route_template(request: Request) -> str:
    """Return the FastAPI route template (e.g. /applications/{id}) so log
    cardinality stays sane. Falls back to the raw path if no route matched."""
    route = request.scope.get("route")
    if route is not None and getattr(route, "path", None):
        return route.path
    return request.url.path


class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        status = 500
        response: Response | None = None
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            elapsed_ms = round((time.perf_counter() - start) * 1000.0, 1)
            route = _route_template(request)
            user_id = None
            try:
                user_id = getattr(request.state, "user_id", None)
            except Exception:
                user_id = None

            # Skip noisy paths from the structured log (still in Prom).
            quiet = route in {"/metrics", "/healthz"}
            if not quiet:
                log.info(
                    "http_request",
                    method=request.method,
                    route=route,
                    status=status,
                    duration_ms=elapsed_ms,
                    user_id=str(user_id) if user_id else None,
                )
'''


# -----------------------------------------------------------------------------
# Update middleware/__init__.py to re-export new middleware (optional)
# -----------------------------------------------------------------------------
FILES["backend/app/middleware/__init__.py"] = ''


# -----------------------------------------------------------------------------
# Health route extended
# -----------------------------------------------------------------------------
FILES["backend/app/routes/health.py"] = '''"""
Health endpoints.

  /healthz  - liveness only (no dependencies)
  /readyz   - readiness: pings DB, Redis, GenLayer contract
"""

from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse, Response

from backend.app.core.config import settings
from backend.app.core.logging import get_logger
from backend.app.core.metrics import contract_probe_total
from backend.app.db.session import ping_db

router = APIRouter(tags=["health"])
log = get_logger("health")


def _ping_redis() -> bool:
    try:
        import redis  # type: ignore
        client = redis.Redis.from_url(str(settings.redis_url), socket_timeout=2.0)
        return bool(client.ping())
    except Exception as exc:
        log.warning("readyz_redis_failed", error=str(exc))
        return False


def _ping_genlayer_contract() -> bool:
    if settings.llm_backend != "genlayer":
        # Not configured to require the contract; treat as N/A (healthy).
        return True
    try:
        # Lightweight read; same defensive pattern as services.genlayer.read.
        from services.genlayer.read import _client  # noqa: SLF001
        client = _client()
        ok, version = (False, None)
        try:
            ok, version = True, client._try_read("contract_version", [])[1]  # noqa: SLF001
        except Exception as exc:
            log.warning("readyz_contract_failed", error=str(exc))
            return False
        contract_probe_total.labels(result="ok" if ok else "failed").inc()
        return ok and version is not None
    except Exception as exc:
        log.warning("readyz_contract_failed", error=str(exc))
        contract_probe_total.labels(result="failed").inc()
        return False


@router.get("/healthz")
def healthz() -> dict:
    """Liveness: process is up. No dependencies."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "env": settings.app_env,
    }


@router.get("/readyz")
def readyz() -> JSONResponse:
    checks = {
        "database": ping_db(),
        "redis": _ping_redis(),
        "genlayer": _ping_genlayer_contract(),
    }
    all_ok = all(checks.values())
    code = status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=code,
        content={
            "status": "ok" if all_ok else "degraded",
            "checks": checks,
        },
    )


@router.get("/livez", include_in_schema=False)
def livez() -> Response:
    """Simplest possible 200 for container liveness probes."""
    return Response(status_code=200)
'''


# -----------------------------------------------------------------------------
# main.py: wire up Prometheus instrumentator + request log middleware
# -----------------------------------------------------------------------------
FILES["backend/app/main.py"] = '''"""
FastAPI application factory.
Wires logging, middleware, CORS, error handlers, rate limiter, observability,
and routers.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.v1.router import api_router
from backend.app.core.config import settings
from backend.app.core.errors import register_exception_handlers
from backend.app.core.logging import configure_logging, get_logger
from backend.app.dependencies.rate_limit import limiter
from backend.app.middleware.request_id import RequestIDMiddleware
from backend.app.middleware.request_log import RequestLogMiddleware
from backend.app.routes import health


def create_app() -> FastAPI:
    configure_logging()
    log = get_logger("startup")

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.app_debug,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
    )

    # Prometheus metrics. Must be registered before the app starts handling
    # requests. Excludes /metrics, /healthz, /livez itself from being counted.
    Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        excluded_handlers=["/metrics", "/healthz", "/livez"],
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

    # Rate limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # Request log + request id (added in reverse-execution order: last added
    # runs first on the way in, last on the way out; we want request_id
    # populated before request_log emits)
    app.add_middleware(RequestLogMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.app_frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # Errors
    register_exception_handlers(app)

    # Routes
    app.include_router(health.router)
    app.include_router(api_router)

    @app.get("/", tags=["root"])
    def root() -> dict:
        return {
            "app": settings.app_name,
            "version": "0.1.0",
            "docs": "/docs",
            "metrics": "/metrics",
            "health": "/healthz",
            "ready": "/readyz",
        }

    log.info("app_started", env=settings.app_env, debug=settings.app_debug)
    return app


app = create_app()
'''


# -----------------------------------------------------------------------------
# Hook business metrics into the existing code paths
# -----------------------------------------------------------------------------
FILES["workers/tasks/evaluations.py"] = '''"""
Background task: run the evaluation orchestrator using the application
owner's wallet to sign GenLayer transactions.
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
    except Exception as exc:  # noqa: BLE001
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
'''


# Applications route: counter on submission outcome
FILES["backend/app/routes/applications.py"] = '''"""
Applications API with balance-gated submission and submission metrics.
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
from backend.app.core.metrics import applications_submitted_total
from backend.app.db.session import get_db
from backend.app.dependencies.auth import get_current_user
from backend.app.dependencies.rate_limit import limiter
from backend.app.models.application import Application, FileAsset
from backend.app.models.evaluation import Evaluation  # noqa: F401  (used in list query)
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
    safe_name = filename.replace("/", "_").replace("\\\\", "_")
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
        applications_submitted_total.labels(result="rejected_validation").inc()
        raise ValidationAppError("job_url must start with http or https", code="job_url_invalid")

    try:
        _check_balance_or_raise(current_user)
    except InsufficientBalanceError:
        applications_submitted_total.labels(result="rejected_balance").inc()
        raise

    try:
        cv_bytes = _validate_upload(cv, "cv")
        cl_bytes = _validate_upload(cover_letter, "cover_letter")
    except ValidationAppError:
        applications_submitted_total.labels(result="rejected_validation").inc()
        raise

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
    applications_submitted_total.labels(result="accepted").inc()
    return ApplicationPublic.model_validate(application)


@router.get("", response_model=list[ApplicationListItem])
def list_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Dashboard list: show applications that produced a real on-chain write,
    plus in-progress and failed ones. Hide cache-hit completions.
    """
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
'''


# -----------------------------------------------------------------------------
# Observability docs
# -----------------------------------------------------------------------------
FILES["docs/architecture/observability.md"] = '''# CVPilot Observability

## Endpoints

| Path        | Purpose                                  | Notes                                         |
|-------------|------------------------------------------|-----------------------------------------------|
| `/healthz`  | Liveness probe                           | No dependencies. Always 200 if process is up. |
| `/livez`    | Even simpler container liveness          | Hidden from OpenAPI.                          |
| `/readyz`   | Readiness probe (DB, Redis, GenLayer)    | 200 only when all checks pass; 503 otherwise. |
| `/metrics`  | Prometheus scrape endpoint               | Standard HTTP metrics + CVPilot business.     |

## Standard HTTP metrics

Emitted by `prometheus-fastapi-instrumentator`:

- `http_requests_total{method, handler, status_code}` — request count.
- `http_request_duration_seconds{method, handler}` — request duration histogram.
- `http_request_size_bytes{method, handler}` and `http_response_size_bytes`.
- `http_requests_in_progress{method, handler}`.

`handler` is the **FastAPI route template** (e.g. `/api/v1/applications/{application_id}`), not the resolved URL, to keep cardinality bounded.

## CVPilot business metrics

| Metric                                       | Labels                       | Source                                   |
|----------------------------------------------|------------------------------|------------------------------------------|
| `cvpilot_evaluations_total`                  | `backend`, `status`          | Celery `evaluate_application` task       |
| `cvpilot_evaluation_duration_seconds`        | `backend`                    | Celery `evaluate_application` task       |
| `cvpilot_applications_submitted_total`       | `result`                     | `POST /api/v1/applications`              |
| `cvpilot_wallet_send_total`                  | `status`                     | `POST /api/v1/auth/wallet/send`          |
| `cvpilot_contract_probe_total`               | `result`                     | `/readyz` GenLayer reachability check     |

## Structured request log

Every non-quiet request emits a single JSON line via structlog:

```json
{
  "event": "http_request",
  "method": "POST",
  "route": "/api/v1/applications",
  "status": 202,
  "duration_ms": 412.3,
  "request_id": "8ac3f617d10844689da4b2abec6411ea",
  "user_id": "f5812320-b418-414b-8722-f0f37b111d88"
}
/metrics, /healthz, /livez are excluded from this log to avoid noise from scrapers.

Recommended Grafana dashboard panels
RPS — sum(rate(http_requests_total[1m])) by (handler)
p95 latency — histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, handler))
Error rate — sum(rate(http_requests_total{status_code=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))
Evaluation throughput — sum(rate(cvpilot_evaluations_total[5m])) by (backend, status)
Evaluation latency (genlayer) — histogram_quantile(0.95, sum(rate(cvpilot_evaluation_duration_seconds_bucket{backend="genlayer"}[10m])) by (le))
Submission gate — sum(rate(cvpilot_applications_submitted_total[5m])) by (result)
Wallet activity — sum(rate(cvpilot_wallet_send_total[1h])) by (status)
Readiness — alert when up{job="cvpilot"} == 1 AND /readyz returns 503 for > 1 minute.
Local exploration
curl -s http://localhost:8000/metrics | head -40
curl -s http://localhost:8000/readyz | python3 -m json.tool
'''

def write(rel: str, content: str) -> None:
p = ROOT / rel
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(content, encoding="utf-8")
print(f" wrote {rel}")

for rel, content in FILES.items():
write(rel, content)

print("\nPhase 12A scaffold complete.")
