"""
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
