"""
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
