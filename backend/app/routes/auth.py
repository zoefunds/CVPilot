"""
Auth routes: register (now generates a wallet), login, refresh, me,
forgot-password, reset-password.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
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
from backend.app.models.email_verification_token import EmailVerificationToken
from backend.app.models.password_reset_token import PasswordResetToken
from backend.app.models.user import User
from backend.app.schemas.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    ResetPasswordResponse,
    SendVerificationResponse,
    TokenPair,
    VerifyEmailRequest,
    VerifyEmailResponse,
)
from backend.app.schemas.user import UserPublic
from services.genlayer import generate_wallet
from services.mailer import send_email_verification_email, send_password_reset_email
from services.mailer.brevo import MailerError, MailerNotConfiguredError

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
    background_tasks: BackgroundTasks,
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
    # Issue a verification token + dispatch the email as a background task so
    # the registration response isn't blocked by Brevo latency.
    _issue_verification_token(db, user, request, background_tasks)
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


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _build_reset_url(token: str) -> str:
    origin = settings.app_frontend_origin.rstrip("/")
    return f"{origin}/reset-password?token={token}"


def _build_verify_url(token: str) -> str:
    origin = settings.app_frontend_origin.rstrip("/")
    return f"{origin}/verify-email?token={token}"


def _issue_verification_token(
    db: Session,
    user: User,
    request: Request,
    background_tasks: BackgroundTasks,
) -> None:
    """Create a one-time verification token + dispatch the email.

    Caller owns the surrounding db.commit(). The send is dispatched as a
    background task so request latency isn't tied to Brevo.
    """
    raw_token = secrets.token_urlsafe(48)
    token_hash = _hash_token(raw_token)
    ttl_min = settings.email_verification_token_ttl_min
    expires_at = datetime.now(UTC) + timedelta(minutes=ttl_min)

    db.add(
        EmailVerificationToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
    )
    _audit(
        db,
        user_id=user.id,
        event="email_verification.requested",
        request=request,
    )

    verify_url = _build_verify_url(raw_token)
    user_name = user.full_name
    user_email = user.email

    def _send() -> None:
        try:
            send_email_verification_email(
                to_email=user_email,
                to_name=user_name,
                verify_url=verify_url,
                ttl_min=ttl_min,
            )
        except MailerNotConfiguredError:
            log.error("verification_mailer_not_configured", email=user_email)
        except MailerError as exc:
            log.error("verification_send_failed", email=user_email, error=str(exc))

    background_tasks.add_task(_send)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
@limiter.limit("5/minute")
def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Request a password reset email.

    Always returns 200 with the same body to prevent account enumeration.
    The actual email send is dispatched as a background task so timing
    doesn't leak whether the address is registered.
    """
    email = body.email.lower()
    user = db.scalar(select(User).where(User.email == email))

    # Audit the attempt regardless of outcome.
    _audit(
        db,
        user_id=user.id if user else None,
        event="password_reset.requested",
        request=request,
        payload={"email": email, "user_found": user is not None},
    )

    if user is not None and user.is_active:
        raw_token = secrets.token_urlsafe(48)
        token_hash = _hash_token(raw_token)
        ttl_min = settings.password_reset_token_ttl_min
        expires_at = datetime.now(UTC) + timedelta(minutes=ttl_min)

        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
        )
        db.commit()

        reset_url = _build_reset_url(raw_token)
        user_name = user.full_name
        user_email = user.email

        def _send() -> None:
            try:
                send_password_reset_email(
                    to_email=user_email,
                    to_name=user_name,
                    reset_url=reset_url,
                    ttl_min=ttl_min,
                )
            except MailerNotConfiguredError:
                log.error("password_reset_mailer_not_configured", email=user_email)
            except MailerError as exc:
                log.error("password_reset_send_failed", email=user_email, error=str(exc))

        background_tasks.add_task(_send)
    else:
        db.commit()

    return ForgotPasswordResponse()


@router.post("/reset-password", response_model=ResetPasswordResponse)
@limiter.limit("10/minute")
def reset_password(
    request: Request,
    body: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    token_hash = _hash_token(body.token)
    now = datetime.now(UTC)

    record = db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )
    if (
        record is None
        or record.used_at is not None
        or record.expires_at <= now
    ):
        _audit(
            db,
            user_id=record.user_id if record else None,
            event="password_reset.failed",
            request=request,
            payload={"reason": "invalid_or_expired"},
        )
        db.commit()
        raise ValidationAppError(
            "This reset link is invalid or has expired.",
            code="invalid_reset_token",
        )

    user = db.get(User, record.user_id)
    if user is None or not user.is_active:
        _audit(
            db,
            user_id=record.user_id,
            event="password_reset.failed",
            request=request,
            payload={"reason": "user_inactive_or_missing"},
        )
        db.commit()
        raise ValidationAppError(
            "This reset link is invalid or has expired.",
            code="invalid_reset_token",
        )

    user.password_hash = hash_password(body.password)
    record.used_at = now
    # Invalidate any other outstanding tokens for this user.
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None),
        PasswordResetToken.id != record.id,
    ).update({PasswordResetToken.used_at: now})

    _audit(db, user_id=user.id, event="password_reset.completed", request=request)
    db.commit()
    log.info("password_reset_completed", user_id=str(user.id))
    return ResetPasswordResponse()


@router.post("/send-verification", response_model=SendVerificationResponse)
@limiter.limit("3/minute")
def send_verification(
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Resend the email verification link.

    Always returns 200 with the same body, regardless of whether the user is
    already verified. Idempotent for repeated taps.
    """
    if current_user.email_verified_at is not None:
        # Already verified; no-op (and no email).
        return SendVerificationResponse()

    # Invalidate any outstanding tokens for this user before issuing a new one.
    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == current_user.id,
        EmailVerificationToken.used_at.is_(None),
    ).update({EmailVerificationToken.used_at: datetime.now(UTC)})

    _issue_verification_token(db, current_user, request, background_tasks)
    db.commit()
    return SendVerificationResponse()


@router.post("/verify-email", response_model=VerifyEmailResponse)
@limiter.limit("10/minute")
def verify_email(
    request: Request,
    body: VerifyEmailRequest,
    db: Session = Depends(get_db),
):
    token_hash = _hash_token(body.token)
    now = datetime.now(UTC)

    record = db.scalar(
        select(EmailVerificationToken).where(EmailVerificationToken.token_hash == token_hash)
    )
    if (
        record is None
        or record.used_at is not None
        or record.expires_at <= now
    ):
        _audit(
            db,
            user_id=record.user_id if record else None,
            event="email_verification.failed",
            request=request,
            payload={"reason": "invalid_or_expired"},
        )
        db.commit()
        raise ValidationAppError(
            "This verification link is invalid or has expired.",
            code="invalid_verification_token",
        )

    user = db.get(User, record.user_id)
    if user is None or not user.is_active:
        _audit(
            db,
            user_id=record.user_id,
            event="email_verification.failed",
            request=request,
            payload={"reason": "user_inactive_or_missing"},
        )
        db.commit()
        raise ValidationAppError(
            "This verification link is invalid or has expired.",
            code="invalid_verification_token",
        )

    if user.email_verified_at is None:
        user.email_verified_at = now
    record.used_at = now
    # Invalidate any other outstanding verification tokens for this user.
    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user.id,
        EmailVerificationToken.used_at.is_(None),
        EmailVerificationToken.id != record.id,
    ).update({EmailVerificationToken.used_at: now})

    _audit(db, user_id=user.id, event="email_verification.completed", request=request)
    db.commit()
    log.info("email_verification_completed", user_id=str(user.id))
    return VerifyEmailResponse()
