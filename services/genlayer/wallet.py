"""
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
