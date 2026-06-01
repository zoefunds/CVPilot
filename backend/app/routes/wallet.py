"""
Wallet routes.
"""

import re
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.errors import AppError, ValidationAppError
from backend.app.core.logging import get_logger
from backend.app.core.wallet_crypto import decrypt_secret
from backend.app.db.session import get_db
from backend.app.dependencies.auth import get_current_user
from backend.app.dependencies.rate_limit import limiter
from backend.app.models.application import Application
from backend.app.models.audit_log import AuditLog
from backend.app.models.evaluation import Evaluation
from backend.app.models.user import User
from backend.app.schemas.wallet import (
    WalletActivityItem,
    WalletExport,
    WalletPublic,
    WalletSendRequest,
    WalletSendResponse,
)
from services.genlayer import get_balance_wei
from services.genlayer.wallet import WalletError, send_gen

router = APIRouter(prefix="/auth/wallet", tags=["wallet"])
log = get_logger("wallet")

_ADDR_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
_STUDIO_TX_URL = "https://studio.genlayer.com/tx/{}"


def _wei_to_gen_str(wei: int) -> str:
    if wei <= 0:
        return "0"
    return format(Decimal(wei) / Decimal(10**18), "f")


def _gen_to_wei(amount_gen: str) -> int:
    try:
        d = Decimal(amount_gen.strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ValidationAppError("Amount is not a valid number.", code="amount_invalid") from exc
    if d <= 0:
        raise ValidationAppError("Amount must be greater than zero.", code="amount_not_positive")
    if d > Decimal("1000000000"):
        raise ValidationAppError("Amount exceeds sane maximum.", code="amount_too_large")
    return int(d * Decimal(10**18))


def _tx_explorer(tx_hash: str | None) -> str | None:
    if not tx_hash:
        return None
    return _STUDIO_TX_URL.format(tx_hash)


@router.get("", response_model=WalletPublic)
def get_wallet(current_user: User = Depends(get_current_user)):
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
    return WalletExport(address=current_user.wallet_address, private_key=pk)


@router.post("/send", response_model=WalletSendResponse)
@limiter.limit("10/hour")
def send(
    request: Request,
    body: WalletSendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.wallet_address or not current_user.encrypted_private_key:
        raise ValidationAppError("This account has no wallet.", code="wallet_missing")

    if not _ADDR_RE.match(body.to_address):
        raise ValidationAppError(
            "Recipient address must look like 0x followed by 40 hex characters.",
            code="recipient_invalid",
        )
    if body.to_address.lower() == current_user.wallet_address.lower():
        raise ValidationAppError(
            "You cannot send GEN to your own wallet.",
            code="recipient_is_self",
        )

    amount_wei = _gen_to_wei(body.amount_gen)
    balance_wei = get_balance_wei(current_user.wallet_address)
    # Reserve a buffer for gas fees; otherwise the tx itself can fail mid-send.
    if amount_wei + 1_000_000_000_000_000 > balance_wei:
        raise ValidationAppError(
            f"Insufficient balance. Wallet has {_wei_to_gen_str(balance_wei)} GEN; "
            f"need {body.amount_gen} GEN plus a small gas reserve.",
            code="insufficient_balance",
        )

    try:
        pk = decrypt_secret(current_user.encrypted_private_key)
    except ValueError as exc:
        raise ValidationAppError(str(exc), code="wallet_decrypt_failed") from exc

    try:
        result = send_gen(
            private_key=pk,
            to_address=body.to_address,
            amount_wei=amount_wei,
        )
    except WalletError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise AppError(f"Send failed: {exc}", code="wallet_send_failed") from exc

    db.add(
        AuditLog(
            user_id=current_user.id,
            event="wallet.send",
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            payload={
                "from_address": current_user.wallet_address,
                "to_address": body.to_address,
                "amount_wei": amount_wei,
                "tx_hash": result.get("tx_hash"),
            },
        )
    )
    db.commit()

    log.info(
        "wallet_send",
        user_id=str(current_user.id),
        to=body.to_address,
        amount_wei=amount_wei,
        tx_hash=result.get("tx_hash"),
    )

    return WalletSendResponse(
        tx_hash=str(result.get("tx_hash") or ""),
        from_address=current_user.wallet_address,
        to_address=body.to_address,
        amount_wei=amount_wei,
        amount_gen=_wei_to_gen_str(amount_wei),
        explorer_url=_tx_explorer(result.get("tx_hash")),
    )


@router.get("/activity", response_model=list[WalletActivityItem])
def activity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items: list[WalletActivityItem] = []

    # On-chain evaluations.
    eval_rows = db.execute(
        select(Evaluation, Application)
        .join(Application, Application.id == Evaluation.application_id)
        .where(Application.user_id == current_user.id)
        .where(Evaluation.contract_tx_hash.isnot(None))
        .order_by(Evaluation.created_at.desc())
        .limit(50)
    ).all()
    for ev, app in eval_rows:
        items.append(
            WalletActivityItem(
                kind="evaluation",
                timestamp=ev.created_at,
                tx_hash=ev.contract_tx_hash,
                status=ev.status or "complete",
                description=f"Evaluation: {app.job_title or 'Untitled posting'}",
                application_id=str(app.id),
                explorer_url=_tx_explorer(ev.contract_tx_hash),
            )
        )

    # Outbound GEN sends.
    send_rows = db.scalars(
        select(AuditLog)
        .where(AuditLog.user_id == current_user.id)
        .where(AuditLog.event == "wallet.send")
        .order_by(AuditLog.created_at.desc())
        .limit(50)
    ).all()
    for row in send_rows:
        payload = row.payload or {}
        to_addr = payload.get("to_address")
        amount_wei = int(payload.get("amount_wei") or 0)
        items.append(
            WalletActivityItem(
                kind="send",
                timestamp=row.created_at,
                tx_hash=payload.get("tx_hash"),
                status="complete",
                description=(
                    f"Sent {_wei_to_gen_str(amount_wei)} GEN to "
                    f"{(to_addr or '')[:8]}…{(to_addr or '')[-6:]}"
                ),
                to_address=to_addr,
                amount_wei=amount_wei,
                amount_gen=_wei_to_gen_str(amount_wei),
                explorer_url=_tx_explorer(payload.get("tx_hash")),
            )
        )

    items.sort(key=lambda x: x.timestamp, reverse=True)
    return items[:30]
