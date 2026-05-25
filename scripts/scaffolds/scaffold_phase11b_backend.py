"""
Phase 11B backend: Send GEN + Activity history.
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
FILES: dict[str, str] = {}


FILES["backend/app/schemas/wallet.py"] = '''"""
Wallet response schemas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class WalletPublic(BaseModel):
    address: str
    balance_wei: int
    balance_gen: str
    contract_address: str


class WalletExport(BaseModel):
    address: str
    private_key: str
    warning: str = (
        "Treat this private key like a password. Anyone with this key "
        "can move every GEN in this wallet. CVPilot never asks you to "
        "share it. Save it offline."
    )


class WalletSendRequest(BaseModel):
    to_address: str = Field(..., min_length=42, max_length=42)
    amount_gen: str = Field(..., min_length=1, max_length=64, description="Amount in GEN, decimal string. e.g. '0.5'")


class WalletSendResponse(BaseModel):
    tx_hash: str
    from_address: str
    to_address: str
    amount_wei: int
    amount_gen: str
    explorer_url: str | None = None


class WalletActivityItem(BaseModel):
    kind: Literal["evaluation", "send"]
    timestamp: datetime
    tx_hash: str | None = None
    status: str
    description: str
    to_address: str | None = None
    amount_wei: int | None = None
    amount_gen: str | None = None
    application_id: str | None = None
    explorer_url: str | None = None
'''


FILES["backend/app/routes/wallet.py"] = '''"""
Wallet routes.
"""

import re
from decimal import Decimal, InvalidOperation
from typing import List

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
from services.genlayer.wallet import send_gen, WalletError

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
    except (InvalidOperation, AttributeError):
        raise ValidationAppError("Amount is not a valid number.", code="amount_invalid")
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


@router.get("/activity", response_model=List[WalletActivityItem])
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
                    f"{(to_addr or '')[:8]}\u2026{(to_addr or '')[-6:]}"
                ),
                to_address=to_addr,
                amount_wei=amount_wei,
                amount_gen=_wei_to_gen_str(amount_wei),
                explorer_url=_tx_explorer(payload.get("tx_hash")),
            )
        )

    items.sort(key=lambda x: x.timestamp, reverse=True)
    return items[:30]
'''


FILES["services/genlayer/wallet.py"] = '''"""
GenLayer wallet helpers: generation, balance reads, native GEN transfers.
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


def _genlayer_read_only_client():
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
    if not address:
        return 0
    client = _genlayer_read_only_client()
    for fn in (_balance_via_eth_attr, _balance_via_direct, _balance_via_provider):
        try:
            v = fn(client, address)
            if isinstance(v, int):
                return max(0, v)
        except Exception as exc:
            log.warning("genlayer_balance_strategy_failed", error=str(exc))
    log.error("genlayer_balance_unreadable", address=address)
    return 0


# ---------------------------------------------------------------------------
# Send GEN
# ---------------------------------------------------------------------------
def _make_signed_client(private_key: str):
    _install_buffer_shim()
    from genlayer_py import create_account, create_client  # type: ignore
    from genlayer_py.chains import studionet  # type: ignore
    try:
        account = create_account(account_private_key=private_key)
    except TypeError:
        account = create_account(private_key=private_key)
    client = create_client(chain=studionet, account=account)
    return account, client


def _send_via_client_send_transaction(client, account, to_address: str, amount_wei: int) -> str | None:
    fn = getattr(client, "send_transaction", None)
    if fn is None:
        return None
    candidates = [
        {"to": to_address, "value": amount_wei, "account": account},
        {"to": to_address, "value": amount_wei},
        {"transaction": {"to": to_address, "value": amount_wei}},
    ]
    for kw in candidates:
        try:
            tx_hash = fn(**kw)
            return str(tx_hash)
        except TypeError:
            continue
        except Exception as exc:
            log.warning("genlayer_send_client_method_failed", error=str(exc))
            return None
    return None


def _send_via_eth_raw(client, account, private_key: str, to_address: str, amount_wei: int) -> str | None:
    eth = getattr(client, "eth", None)
    if eth is None:
        return None
    try:
        from eth_account import Account  # type: ignore
        nonce_fn = getattr(eth, "get_transaction_count", None) or getattr(eth, "getTransactionCount", None)
        chain_id = getattr(eth, "chain_id", None)
        gas_price_fn = getattr(eth, "gas_price", None)
        if callable(gas_price_fn):
            gas_price = gas_price_fn()
        else:
            gas_price = gas_price_fn
        nonce = nonce_fn(account.address) if nonce_fn else 0
        tx = {
            "nonce": int(nonce),
            "to": to_address,
            "value": int(amount_wei),
            "gas": 21000,
            "gasPrice": int(gas_price or 0),
            "chainId": int(chain_id) if chain_id is not None else 0,
        }
        signed = Account.sign_transaction(tx, private_key)
        raw = getattr(signed, "raw_transaction", None) or getattr(signed, "rawTransaction", None)
        if raw is None:
            return None
        send_raw = getattr(eth, "send_raw_transaction", None) or getattr(eth, "sendRawTransaction", None)
        if send_raw is None:
            return None
        tx_hash = send_raw(raw)
        return tx_hash.hex() if hasattr(tx_hash, "hex") else str(tx_hash)
    except Exception as exc:
        log.warning("genlayer_send_eth_raw_failed", error=str(exc))
        return None


def _send_via_provider(client, account, private_key: str, to_address: str, amount_wei: int) -> str | None:
    """Last-resort: build, sign, and send via the underlying JSON-RPC provider."""
    provider = getattr(client, "provider", None)
    if provider is None or not hasattr(provider, "make_request"):
        return None
    try:
        from eth_account import Account  # type: ignore
        nonce_resp = provider.make_request("eth_getTransactionCount", [account.address, "latest"])
        nonce_hex = nonce_resp.get("result") if isinstance(nonce_resp, dict) else nonce_resp
        nonce = int(nonce_hex, 16) if isinstance(nonce_hex, str) and nonce_hex.startswith("0x") else int(nonce_hex or 0)

        chain_resp = provider.make_request("eth_chainId", [])
        chain_hex = chain_resp.get("result") if isinstance(chain_resp, dict) else chain_resp
        chain_id = int(chain_hex, 16) if isinstance(chain_hex, str) and chain_hex.startswith("0x") else int(chain_hex or 0)

        gp_resp = provider.make_request("eth_gasPrice", [])
        gp_hex = gp_resp.get("result") if isinstance(gp_resp, dict) else gp_resp
        gas_price = int(gp_hex, 16) if isinstance(gp_hex, str) and gp_hex.startswith("0x") else int(gp_hex or 0)

        tx = {
            "nonce": nonce,
            "to": to_address,
            "value": int(amount_wei),
            "gas": 21000,
            "gasPrice": gas_price,
            "chainId": chain_id,
        }
        signed = Account.sign_transaction(tx, private_key)
        raw = getattr(signed, "raw_transaction", None) or getattr(signed, "rawTransaction", None)
        if raw is None:
            return None
        raw_hex = "0x" + raw.hex() if not raw.hex().startswith("0x") else raw.hex()
        tx_resp = provider.make_request("eth_sendRawTransaction", [raw_hex])
        return tx_resp.get("result") if isinstance(tx_resp, dict) else str(tx_resp)
    except Exception as exc:
        log.warning("genlayer_send_provider_failed", error=str(exc))
        return None


def send_gen(*, private_key: str, to_address: str, amount_wei: int) -> dict:
    """Send native GEN from the wallet to recipient. Returns tx info dict."""
    account, client = _make_signed_client(private_key)
    log.info("wallet_send_dispatch", to=to_address, amount_wei=amount_wei, from_addr=account.address)

    tx_hash = (
        _send_via_client_send_transaction(client, account, to_address, amount_wei)
        or _send_via_eth_raw(client, account, private_key, to_address, amount_wei)
        or _send_via_provider(client, account, private_key, to_address, amount_wei)
    )

    if not tx_hash:
        raise WalletError(
            "All known send strategies failed against this GenLayer SDK build. "
            "Please report the genlayer-py version.",
            code="wallet_send_unsupported",
        )

    return {
        "tx_hash": str(tx_hash),
        "from_address": account.address,
        "to_address": to_address,
        "amount_wei": amount_wei,
    }
'''


def write(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  wrote {rel}")


for rel, content in FILES.items():
    write(rel, content)

print("\nPhase 11B backend complete.")
