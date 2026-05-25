"""
Phase 9 backend: per-user GenLayer wallets, encrypted at rest, exportable,
balance-checked at submission time, used to sign evaluation transactions.
"""

from __future__ import annotations
from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
FILES: dict[str, str] = {}


# -----------------------------------------------------------------------------
# 1. config: add wallet-related settings
# -----------------------------------------------------------------------------
FILES["backend/app/core/config.py"] = '''"""
Centralized typed settings.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="CVPilot", alias="APP_NAME")
    app_env: Literal["development", "staging", "production"] = Field(
        default="development", alias="APP_ENV"
    )
    app_debug: bool = Field(default=True, alias="APP_DEBUG")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    app_secret_key: str = Field(default="change-me", alias="APP_SECRET_KEY")
    app_frontend_origin: str = Field(default="http://localhost:3000", alias="APP_FRONTEND_ORIGIN")

    database_url: PostgresDsn = Field(alias="DATABASE_URL")
    database_pool_size: int = Field(default=10, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, alias="DATABASE_MAX_OVERFLOW")

    redis_url: RedisDsn = Field(alias="REDIS_URL")
    celery_broker_url: str = Field(alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(alias="CELERY_RESULT_BACKEND")

    jwt_secret: str = Field(default="change-me", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expires_min: int = Field(default=30, alias="JWT_ACCESS_TOKEN_EXPIRES_MIN")
    jwt_refresh_token_expires_days: int = Field(default=7, alias="JWT_REFRESH_TOKEN_EXPIRES_DAYS")

    storage_backend: Literal["local", "s3"] = Field(default="local", alias="STORAGE_BACKEND")
    storage_local_path: str = Field(default="./storage/uploads", alias="STORAGE_LOCAL_PATH")
    storage_max_upload_mb: int = Field(default=10, alias="STORAGE_MAX_UPLOAD_MB")

    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")
    rate_limit_burst: int = Field(default=20, alias="RATE_LIMIT_BURST")

    genlayer_studionet_rpc: str = Field(default="https://studio.genlayer.com/api", alias="GENLAYER_STUDIONET_RPC")
    genlayer_account_private_key: str = Field(default="", alias="GENLAYER_ACCOUNT_PRIVATE_KEY")
    genlayer_contract_address: str = Field(default="", alias="GENLAYER_CONTRACT_ADDRESS")
    genlayer_llm_model: str = Field(default="default", alias="GENLAYER_LLM_MODEL")
    llm_backend: Literal["stub", "genlayer"] = Field(default="stub", alias="LLM_BACKEND")

    # Wallet + balance gate
    wallet_encryption_salt: str = Field(default="cvpilot-wallet-v1", alias="WALLET_ENCRYPTION_SALT")
    # Min balance (in wei) required before a user can submit an application.
    # 0.5 GEN expressed in wei: 500000000000000000
    min_submit_balance_wei: int = Field(default=500_000_000_000_000_000, alias="MIN_SUBMIT_BALANCE_WEI")
    # When True (production default), only LLM_BACKEND=genlayer is allowed.
    force_genlayer_in_production: bool = Field(default=True, alias="FORCE_GENLAYER_IN_PRODUCTION")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_json: bool = Field(default=True, alias="LOG_JSON")

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    s = Settings()  # type: ignore[call-arg]
    if s.is_production and s.force_genlayer_in_production and s.llm_backend != "genlayer":
        raise RuntimeError(
            "LLM_BACKEND must be 'genlayer' in production. Set LLM_BACKEND=genlayer or "
            "FORCE_GENLAYER_IN_PRODUCTION=false."
        )
    return s


settings = get_settings()
'''


# -----------------------------------------------------------------------------
# 2. backend/app/core/wallet_crypto.py — Fernet encryption tied to APP_SECRET_KEY
# -----------------------------------------------------------------------------
FILES["backend/app/core/wallet_crypto.py"] = '''"""
Symmetric encryption for at-rest storage of wallet private keys.
Key is derived from APP_SECRET_KEY via PBKDF2-HMAC-SHA256.
"""

from __future__ import annotations

import base64
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from backend.app.core.config import settings


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=settings.wallet_encryption_salt.encode("utf-8"),
        iterations=200_000,
    )
    key_bytes = kdf.derive(settings.app_secret_key.encode("utf-8"))
    return Fernet(base64.urlsafe_b64encode(key_bytes))


def encrypt_secret(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_secret(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Could not decrypt wallet private key. Wrong APP_SECRET_KEY?") from exc
'''


# -----------------------------------------------------------------------------
# 3. backend/app/models/user.py — add wallet columns
# -----------------------------------------------------------------------------
FILES["backend/app/models/user.py"] = '''"""
User ORM model.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # GenLayer wallet (permanent, generated at registration)
    wallet_address: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, index=True)
    encrypted_private_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
'''


# -----------------------------------------------------------------------------
# 4. services/genlayer/__init__.py + wallet.py — wallet generation + balance reads
# -----------------------------------------------------------------------------
FILES["services/genlayer/__init__.py"] = '''from services.genlayer.wallet import (  # noqa: F401
    generate_wallet,
    get_balance_wei,
    address_from_private_key,
)
'''

FILES["services/genlayer/wallet.py"] = '''"""
GenLayer wallet helpers.

generate_wallet() -> (address, private_key_hex)
get_balance_wei(address) -> int       (live GEN balance, in wei)
address_from_private_key(pk) -> str   (derives address from hex private key)
"""

from __future__ import annotations

import sys
from typing import Tuple

from backend.app.core.config import settings
from backend.app.core.errors import AppError
from backend.app.core.logging import get_logger

log = get_logger("genlayer.wallet")


class WalletError(AppError):
    status_code = 502
    code = "wallet_error"


def _install_buffer_shim() -> None:
    if sys.version_info >= (3, 12):
        return
    import collections.abc as _abc
    if hasattr(_abc, "Buffer"):
        return
    try:
        from typing_extensions import Buffer as _Buffer  # type: ignore
        _abc.Buffer = _Buffer  # type: ignore[attr-defined]
    except Exception:
        pass


def _eth_account():
    _install_buffer_shim()
    from eth_account import Account  # type: ignore
    return Account


def generate_wallet() -> Tuple[str, str]:
    Account = _eth_account()
    acct = Account.create()
    address = acct.address
    pk_hex = acct.key.hex()
    if not pk_hex.startswith("0x"):
        pk_hex = "0x" + pk_hex
    return address, pk_hex


def address_from_private_key(pk_hex: str) -> str:
    Account = _eth_account()
    return Account.from_key(pk_hex).address


def _genlayer_client():
    _install_buffer_shim()
    if not settings.genlayer_contract_address:
        raise WalletError("GENLAYER_CONTRACT_ADDRESS is not configured.", code="genlayer_address_missing")
    try:
        from genlayer_py import create_client  # type: ignore
        from genlayer_py.chains import studionet  # type: ignore
    except Exception as exc:
        raise WalletError(f"genlayer-py SDK unavailable: {exc}", code="genlayer_sdk_missing") from exc
    return create_client(chain=studionet)


def _balance_via_eth_attr(client, address: str) -> int | None:
    eth = getattr(client, "eth", None)
    if eth is None:
        return None
    fn = getattr(eth, "get_balance", None) or getattr(eth, "getBalance", None)
    if fn is None:
        return None
    try:
        return int(fn(address))
    except Exception as exc:
        log.warning("genlayer_balance_eth_failed", error=str(exc))
        return None


def _balance_via_direct(client, address: str) -> int | None:
    for name in ("get_balance", "getBalance", "balance_of"):
        fn = getattr(client, name, None)
        if fn is None:
            continue
        try:
            return int(fn(address))
        except Exception as exc:
            log.warning("genlayer_balance_direct_failed", method=name, error=str(exc))
    return None


def _balance_via_provider(client, address: str) -> int | None:
    provider = getattr(client, "provider", None)
    if provider is None:
        return None
    make_request = getattr(provider, "make_request", None)
    if make_request is None:
        return None
    try:
        resp = make_request("eth_getBalance", [address, "latest"])
        val = resp.get("result") if isinstance(resp, dict) else resp
        if isinstance(val, str):
            return int(val, 16) if val.startswith("0x") else int(val)
        if isinstance(val, int):
            return val
    except Exception as exc:
        log.warning("genlayer_balance_provider_failed", error=str(exc))
    return None


def get_balance_wei(address: str) -> int:
    """
    Returns the GEN balance (in wei) of the address on StudioNet.
    Tries several SDK shapes to be robust across genlayer-py versions.
    Returns 0 if we cannot read for any reason (rather than raising) so
    a balance check never falsely blocks a user with a network blip.
    """
    if not address:
        return 0
    client = _genlayer_client()

    for fn in (_balance_via_eth_attr, _balance_via_direct, _balance_via_provider):
        try:
            v = fn(client, address)
            if isinstance(v, int):
                return max(0, v)
        except Exception as exc:
            log.warning("genlayer_balance_strategy_failed", error=str(exc))

    log.error("genlayer_balance_unreadable", address=address)
    return 0
'''


# -----------------------------------------------------------------------------
# 5. backend/app/routes/auth.py — generate wallet on register
# -----------------------------------------------------------------------------
FILES["backend/app/routes/auth.py"] = '''"""
Auth routes: register (now generates a wallet), login, refresh, me.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.errors import UnauthorizedError, ValidationAppError
from backend.app.core.logging import get_logger
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from backend.app.core.wallet_crypto import encrypt_secret
from backend.app.db.session import get_db
from backend.app.dependencies.auth import get_current_user
from backend.app.dependencies.rate_limit import limiter
from backend.app.models.audit_log import AuditLog
from backend.app.models.user import User
from backend.app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenPair
from backend.app.schemas.user import UserPublic
from services.genlayer import generate_wallet

router = APIRouter(prefix="/auth", tags=["auth"])
log = get_logger("auth")


def _audit(db: Session, *, user_id, event: str, request: Request, payload=None) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            event=event,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            payload=payload,
        )
    )


@router.post("/register", response_model=UserPublic, status_code=201)
@limiter.limit("5/minute")
def register(
    request: Request,
    body: RegisterRequest,
    db: Session = Depends(get_db),
):
    existing = db.scalar(select(User).where(User.email == body.email.lower()))
    if existing is not None:
        raise ValidationAppError("Email already registered.", code="email_taken")

    # Generate a fresh GenLayer wallet for this user.
    address, pk_hex = generate_wallet()

    user = User(
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        wallet_address=address,
        encrypted_private_key=encrypt_secret(pk_hex),
    )
    db.add(user)
    db.flush()
    _audit(
        db,
        user_id=user.id,
        event="user.registered",
        request=request,
        payload={"wallet_address": address},
    )
    db.commit()
    db.refresh(user)
    log.info("user_registered", user_id=str(user.id), wallet_address=address)
    return UserPublic.model_validate(user)


@router.post("/login", response_model=TokenPair)
@limiter.limit("10/minute")
def login(
    request: Request,
    body: LoginRequest,
    db: Session = Depends(get_db),
):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not verify_password(body.password, user.password_hash):
        _audit(
            db,
            user_id=user.id if user else None,
            event="user.login_failed",
            request=request,
            payload={"email": body.email.lower()},
        )
        db.commit()
        raise UnauthorizedError("Invalid email or password.", code="invalid_credentials")
    if not user.is_active:
        raise UnauthorizedError("Account is disabled.", code="account_disabled")

    pair = TokenPair(
        access_token=create_access_token(str(user.id), extra={"premium": user.is_premium}),
        refresh_token=create_refresh_token(str(user.id)),
    )
    _audit(db, user_id=user.id, event="user.login", request=request)
    db.commit()
    return pair


@router.post("/refresh", response_model=TokenPair)
@limiter.limit("30/minute")
def refresh(
    request: Request,
    body: RefreshRequest,
    db: Session = Depends(get_db),
):
    payload = decode_token(body.refresh_token, expected_type="refresh")
    user_id = payload["sub"]
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("User no longer valid.")
    return TokenPair(
        access_token=create_access_token(str(user.id), extra={"premium": user.is_premium}),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.get("/me", response_model=UserPublic)
def me(current_user: User = Depends(get_current_user)):
    return UserPublic.model_validate(current_user)
'''


# -----------------------------------------------------------------------------
# 6. backend/app/schemas/user.py — expose wallet_address
# -----------------------------------------------------------------------------
FILES["backend/app/schemas/user.py"] = '''"""
Public user shape returned to clients.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    is_active: bool
    is_premium: bool
    is_superuser: bool
    wallet_address: str | None = None
    created_at: datetime
'''


# -----------------------------------------------------------------------------
# 7. Wallet schemas + route
# -----------------------------------------------------------------------------
FILES["backend/app/schemas/wallet.py"] = '''"""
Wallet response schemas.
"""

from __future__ import annotations

from pydantic import BaseModel


class WalletPublic(BaseModel):
    address: str
    balance_wei: int
    balance_gen: str       # decimal string with 18-decimal denomination
    contract_address: str  # so the UI can deep-link to the explorer


class WalletExport(BaseModel):
    address: str
    private_key: str
    warning: str = (
        "Treat this private key like a password. Anyone with this key "
        "can move every GEN in this wallet. CVPilot never asks you to "
        "share it. Save it offline."
    )
'''


FILES["backend/app/routes/wallet.py"] = '''"""
Wallet routes:
  GET  /api/v1/auth/wallet         -> address + live balance
  POST /api/v1/auth/wallet/export  -> decrypted private key (audited)
"""

from decimal import Decimal

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.errors import ValidationAppError
from backend.app.core.logging import get_logger
from backend.app.core.wallet_crypto import decrypt_secret
from backend.app.db.session import get_db
from backend.app.dependencies.auth import get_current_user
from backend.app.dependencies.rate_limit import limiter
from backend.app.models.audit_log import AuditLog
from backend.app.models.user import User
from backend.app.schemas.wallet import WalletExport, WalletPublic
from services.genlayer import get_balance_wei

router = APIRouter(prefix="/auth/wallet", tags=["wallet"])
log = get_logger("wallet")


def _wei_to_gen_str(wei: int) -> str:
    if wei <= 0:
        return "0"
    return format(Decimal(wei) / Decimal(10**18), "f")


@router.get("", response_model=WalletPublic)
def get_wallet(
    current_user: User = Depends(get_current_user),
):
    if not current_user.wallet_address:
        raise ValidationAppError("This account has no wallet.", code="wallet_missing")
    balance = get_balance_wei(current_user.wallet_address)
    return WalletPublic(
        address=current_user.wallet_address,
        balance_wei=balance,
        balance_gen=_wei_to_gen_str(balance),
        contract_address=settings.genlayer_contract_address,
    )


@router.post("/export", response_model=WalletExport)
@limiter.limit("5/hour")
def export_wallet(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.wallet_address or not current_user.encrypted_private_key:
        raise ValidationAppError("This account has no wallet.", code="wallet_missing")
    try:
        pk = decrypt_secret(current_user.encrypted_private_key)
    except ValueError as exc:
        raise ValidationAppError(str(exc), code="wallet_decrypt_failed") from exc

    db.add(
        AuditLog(
            user_id=current_user.id,
            event="wallet.private_key_exported",
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            payload={"wallet_address": current_user.wallet_address},
        )
    )
    db.commit()
    log.warning(
        "wallet_private_key_exported",
        user_id=str(current_user.id),
        wallet_address=current_user.wallet_address,
    )
    return WalletExport(
        address=current_user.wallet_address,
        private_key=pk,
    )
'''


# -----------------------------------------------------------------------------
# 8. api/v1/router.py — mount wallet
# -----------------------------------------------------------------------------
FILES["api/v1/router.py"] = '''"""
Versioned API router aggregator.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.routes import admin, applications, auth, evaluations, wallet

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(wallet.router)
api_router.include_router(applications.router)
api_router.include_router(evaluations.router)
api_router.include_router(admin.router)
'''


# -----------------------------------------------------------------------------
# 9. Balance gate in POST /api/v1/applications
# -----------------------------------------------------------------------------
FILES["backend/app/routes/applications.py"] = '''"""
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
    rows = db.scalars(
        select(Application).where(Application.user_id == current_user.id).order_by(Application.created_at.desc())
    ).all()
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
# 10. LLM factory + orchestrator + worker — sign with USER's wallet
# -----------------------------------------------------------------------------
FILES["services/llm/factory.py"] = '''"""
Choose an LLM backend. genlayer is per-call (signed by the user wallet).
"""

from __future__ import annotations

from typing import Optional

from backend.app.core.config import settings
from services.llm.base import LLMClient
from services.llm.stub import StubLLMClient


def get_llm_client(*, account_private_key: Optional[str] = None) -> LLMClient:
    if settings.llm_backend == "stub":
        return StubLLMClient()
    if settings.llm_backend == "genlayer":
        from services.llm.genlayer import GenLayerLLMClient
        return GenLayerLLMClient(account_private_key=account_private_key)
    raise ValueError(f"Unknown LLM_BACKEND: {settings.llm_backend}")
'''


FILES["services/evaluation/orchestrator.py"] = '''"""
Evaluation orchestrator. Takes the user wallet PK so the GenLayer LLM
client signs transactions from that user's address.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from services.llm import LLMEvaluation
from services.llm.factory import get_llm_client


@dataclass(frozen=True)
class EvaluationOutcome:
    report: LLMEvaluation
    backend: str


def run_evaluation(
    *,
    cv_text: str,
    cover_letter_text: str,
    job_text: str,
    job_title: str | None,
    job_url: str,
    linkedin_url: str | None,
    portfolio_url: str | None,
    account_private_key: Optional[str] = None,
) -> EvaluationOutcome:
    client = get_llm_client(account_private_key=account_private_key)
    report = client.evaluate(
        cv_text=cv_text,
        cover_letter_text=cover_letter_text,
        job_text=job_text,
        job_title=job_title,
        job_url=job_url,
        linkedin_url=linkedin_url,
        portfolio_url=portfolio_url,
    )
    return EvaluationOutcome(report=report, backend=report.raw.get("backend", "unknown"))
'''


FILES["workers/tasks/evaluations.py"] = '''"""
Background task: run the evaluation orchestrator using the application
owner's wallet to sign GenLayer transactions.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.logging import get_logger
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


@celery_app.task(name="cvpilot.evaluate_application", bind=True, max_retries=2)
def evaluate_application(self, application_id: str) -> None:
    aid = uuid.UUID(application_id)
    db = SessionLocal()
    try:
        _run(db, aid)
    finally:
        db.close()
'''


# -----------------------------------------------------------------------------
# 11. services/llm/genlayer.py — accept a private key per invocation
# -----------------------------------------------------------------------------
FILES["services/llm/genlayer.py"] = '''"""
GenLayer Intelligent Contract LLM backend. Per-user signing.
"""

import hashlib
import json
import sys
import time
from typing import Any, Optional

from backend.app.core.config import settings
from backend.app.core.errors import AppError
from backend.app.core.logging import get_logger
from services.llm.base import LLMClient, LLMEvaluation, LLMScore

log = get_logger("llm.genlayer")

_CV_MAX = 8000
_CL_MAX = 4000
_JOB_MAX = 6000
_READ_POLL_S = 120
_READ_INTERVAL_S = 3


class GenLayerClientError(AppError):
    status_code = 502
    code = "genlayer_error"


def _normalised_content_hash(*, cv, cl, job, title, job_url, linkedin_url, portfolio_url):
    payload = json.dumps(
        {
            "cv_text": (cv or "").strip(),
            "cover_letter": (cl or "").strip(),
            "job_text": (job or "").strip(),
            "job_title": (title or "").strip(),
            "job_url": (job_url or "").strip(),
            "linkedin_url": (linkedin_url or "").strip(),
            "portfolio_url": (portfolio_url or "").strip(),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _truncate(s, limit):
    if not s:
        return ""
    return s if len(s) <= limit else s[:limit]


def _install_buffer_shim() -> None:
    if sys.version_info >= (3, 12):
        return
    import collections.abc as _abc
    if hasattr(_abc, "Buffer"):
        return
    try:
        from typing_extensions import Buffer as _Buffer  # type: ignore
        _abc.Buffer = _Buffer  # type: ignore[attr-defined]
    except Exception:
        pass


def _import_sdk():
    _install_buffer_shim()
    try:
        from genlayer_py import create_account, create_client  # type: ignore
        from genlayer_py.chains import studionet  # type: ignore
        try:
            from genlayer_py.types import TransactionStatus  # type: ignore
        except Exception:
            TransactionStatus = None
    except Exception as exc:
        raise GenLayerClientError(
            f"genlayer-py SDK is not installed or incompatible: {exc}",
            code="genlayer_sdk_missing",
        ) from exc
    return create_account, create_client, studionet, TransactionStatus


def _serialise_receipt(receipt) -> dict:
    out: dict = {}
    if receipt is None:
        return out
    for attr in ("status", "consensus_result", "execution_result", "result", "tx_hash", "transaction_hash", "error", "error_message", "stdout", "stderr"):
        try:
            v = getattr(receipt, attr, None)
            if v is None:
                continue
            out[attr] = str(v)[:2000]
        except Exception:
            continue
    return out


class GenLayerLLMClient(LLMClient):
    def __init__(self, *, account_private_key: Optional[str] = None) -> None:
        if not settings.genlayer_contract_address:
            raise GenLayerClientError("GENLAYER_CONTRACT_ADDRESS is not configured.", code="genlayer_address_missing")
        create_account, create_client, studionet, TransactionStatus = _import_sdk()
        self._TransactionStatus = TransactionStatus

        pk = (account_private_key or settings.genlayer_account_private_key or "").strip()
        if pk:
            try:
                self._account = create_account(account_private_key=pk)
            except TypeError:
                self._account = create_account(private_key=pk)
        else:
            # Ephemeral account: only safe for reads. Writes will be forbidden.
            self._account = create_account()
        self._client = create_client(chain=studionet, account=self._account)
        self._address = settings.genlayer_contract_address
        log.info(
            "genlayer_client_ready",
            address=self._address,
            account=str(getattr(self._account, "address", "")),
            using_user_wallet=bool(account_private_key),
        )

    # ------------------------------------------------------------------------
    def _read_raw(self, fn, args):
        return self._client.read_contract(address=self._address, function_name=fn, args=args)

    def _try_read(self, fn, args):
        try:
            return True, self._read_raw(fn, args)
        except Exception as exc:
            log.warning("genlayer_soft_read_failed", fn=fn, error=str(exc))
            return False, None

    def _wait_for_finalized(self, tx_hash):
        wait = getattr(self._client, "wait_for_transaction_receipt", None)
        if wait is None:
            return None
        ts = self._TransactionStatus
        finalized = getattr(ts, "FINALIZED", None) if ts else None
        attempts = []
        if finalized is not None:
            attempts.append({"transaction_hash": tx_hash, "status": finalized, "retries": 60, "interval": 3000})
        attempts.append({"transaction_hash": tx_hash, "retries": 60, "interval": 3000})
        attempts.append({"transaction_hash": tx_hash})
        for kw in attempts:
            try:
                return wait(**kw)
            except TypeError:
                continue
            except Exception as exc:
                log.warning("genlayer_finalize_wait_failed", error=str(exc))
                return None
        try:
            return wait(tx_hash)
        except Exception as exc:
            log.warning("genlayer_finalize_wait_failed_all", error=str(exc))
            return None

    def _write_and_finalize(self, fn, args):
        try:
            tx_hash = self._client.write_contract(address=self._address, function_name=fn, args=args)
        except Exception as exc:
            raise GenLayerClientError(f"GenLayer write_contract({fn}) failed: {exc}", code="genlayer_write_failed") from exc
        receipt = self._wait_for_finalized(tx_hash)
        return str(tx_hash), receipt

    def ping(self) -> dict:
        out = {"address": self._address, "version": None, "evaluation_count": None}
        ok, v = self._try_read("contract_version", [])
        if not ok:
            raise GenLayerClientError("Contract is unreachable.", code="genlayer_contract_unreachable")
        out["version"] = v
        ok2, c = self._try_read("evaluation_count", [])
        out["evaluation_count"] = c if ok2 else "unavailable"
        return out

    def evaluate(self, *, cv_text, cover_letter_text, job_text, job_title, job_url, linkedin_url, portfolio_url) -> LLMEvaluation:
        cv = _truncate(cv_text, _CV_MAX)
        cl = _truncate(cover_letter_text, _CL_MAX)
        job = _truncate(job_text, _JOB_MAX)
        title = job_title or ""
        url = job_url or ""
        h = _normalised_content_hash(cv=cv, cl=cl, job=job, title=title, job_url=url, linkedin_url=linkedin_url or "", portfolio_url=portfolio_url or "")

        ok, existing = self._try_read("get_evaluation", [h])
        if ok and existing:
            return self._build_evaluation(existing, contract_tx_hash=None, content_hash=h, receipt=None)

        log.info("genlayer_evaluate_dispatch", content_hash=h[:12])
        tx_hash, receipt = self._write_and_finalize("evaluate_application", [h, cv, cl, job, title, url, linkedin_url or "", portfolio_url or ""])
        receipt_dict = _serialise_receipt(receipt)
        log.info("genlayer_evaluate_landed", content_hash=h[:12], tx_hash=tx_hash, receipt=receipt_dict)

        deadline = time.time() + _READ_POLL_S
        stored, polls = None, 0
        while time.time() < deadline:
            polls += 1
            last_ok, candidate = self._try_read("get_evaluation", [h])
            if last_ok and candidate:
                stored = candidate
                break
            time.sleep(_READ_INTERVAL_S)
        log.info("genlayer_read_poll_done", content_hash=h[:12], polls=polls, found=stored is not None)

        if not stored:
            raise GenLayerClientError(
                f"Contract accepted the write but get_evaluation returned empty after {polls} polls. "
                f"Tx {tx_hash}. Receipt: {json.dumps(receipt_dict)[:1500]}",
                code="genlayer_storage_not_persistent",
            )
        return self._build_evaluation(stored, contract_tx_hash=tx_hash, content_hash=h, receipt=receipt_dict)

    def _build_evaluation(self, raw_json, *, contract_tx_hash, content_hash, receipt) -> LLMEvaluation:
        parsed = raw_json if isinstance(raw_json, dict) else (json.loads(raw_json) if raw_json else {})
        if not isinstance(parsed, dict):
            parsed = {}
        rationale_obj = parsed.get("rationale") if isinstance(parsed.get("rationale"), dict) else {}

        def _score(name, key):
            return LLMScore(
                value=int(parsed.get(key, 0) or 0),
                label=name,
                rationale=str(rationale_obj.get(key, "")),
                signals={},
            )

        cv = _score("cv", "cv_score")
        cl = _score("cover_letter", "cover_letter_score")
        jm = _score("job_match", "job_match_score")
        ats = _score("ats", "ats_score")
        comp = _score("competitiveness", "competitiveness_score")
        overall = _score("overall", "overall_score")

        return LLMEvaluation(
            cv=cv, cover_letter=cl, job_match=jm, ats=ats, competitiveness=comp, overall=overall,
            summary=str(parsed.get("summary", "")),
            improved_positioning=str(parsed.get("improved_positioning", "")),
            missing_keywords=list(parsed.get("missing_keywords") or []),
            missing_skills=list(parsed.get("missing_skills") or []),
            recommendations=list(parsed.get("recommendations") or []),
            weak_statements=list(parsed.get("weak_statements") or []),
            company_alignment_notes=list(parsed.get("company_alignment_notes") or []),
            strengths=list(parsed.get("strengths") or []),
            risks=list(parsed.get("risks") or []),
            rationale=dict(rationale_obj),
            raw={
                "backend": "genlayer",
                "version": "0.3.1",
                "contract_address": self._address,
                "contract_tx_hash": contract_tx_hash,
                "content_hash": content_hash,
                "receipt": receipt or {},
                "scores": {
                    "cv": cv.value, "cover_letter": cl.value, "job_match": jm.value,
                    "ats": ats.value, "competitiveness": comp.value, "overall": overall.value,
                },
                "raw_contract_payload": parsed,
            },
        )
'''


def write(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  wrote {rel}")


for rel, content in FILES.items():
    write(rel, content)

print("\nPhase 9 backend scaffold complete.")
