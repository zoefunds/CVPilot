"""
GenLayer wallet helpers: generation, balance reads, native GEN transfers.

Send strategy: sign locally and POST eth_sendRawTransaction directly to
StudioNet's JSON-RPC. We do NOT route the send through genlayer-py because
its client surface has been unstable across versions.
"""

from __future__ import annotations

import sys

import httpx

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


from eth_utils import to_checksum_address  # type: ignore


def _eth_account():
    _install_buffer_shim()
    from eth_account import Account  # type: ignore
    return Account


def generate_wallet() -> tuple[str, str]:
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


# ---------------------------------------------------------------------------
# RPC URL discovery
# ---------------------------------------------------------------------------
def _rpc_url() -> str:
    """Best-effort: ask genlayer-py what URL its studionet chain uses, then
    fall back to settings.genlayer_studionet_rpc."""
    _install_buffer_shim()
    candidates: list[str] = []

    try:
        from genlayer_py.chains import studionet  # type: ignore
        for attr in ("rpc_urls", "rpc_url", "default_rpc_url", "url"):
            v = getattr(studionet, attr, None)
            if not v:
                continue
            if isinstance(v, str):
                candidates.append(v)
            elif isinstance(v, dict):
                default = v.get("default")
                if isinstance(default, dict):
                    http_list = default.get("http") or default.get("https")
                    if isinstance(http_list, list | tuple) and http_list:
                        candidates.append(str(http_list[0]))
                elif isinstance(default, list | tuple) and default:
                    candidates.append(str(default[0]))
                elif isinstance(default, str):
                    candidates.append(default)
                else:
                    for inner in v.values():
                        if isinstance(inner, str):
                            candidates.append(inner)
                            break
            elif isinstance(v, list | tuple) and v:
                candidates.append(str(v[0]))
    except Exception as exc:
        log.warning("rpc_url_sdk_introspect_failed", error=str(exc))

    # Fall back to whatever the operator configured.
    if settings.genlayer_studionet_rpc:
        candidates.append(settings.genlayer_studionet_rpc)

    # Filter to http(s)
    for c in candidates:
        if c.startswith("http://") or c.startswith("https://"):
            return c

    raise WalletError(
        "Could not determine StudioNet RPC URL.",
        code="wallet_rpc_url_missing",
    )


def _rpc_call(url: str, method: str, params: list) -> dict:
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    log.info("rpc_call", url=url, method=method)
    try:
        r = httpx.post(url, json=payload, timeout=30.0)
    except Exception as exc:
        raise WalletError(f"RPC transport failed ({method}): {exc}", code="wallet_rpc_transport") from exc
    if r.status_code != 200:
        raise WalletError(
            f"RPC {method} HTTP {r.status_code}: {r.text[:300]}",
            code="wallet_rpc_http_error",
        )
    try:
        body = r.json()
    except Exception as exc:
        raise WalletError(f"RPC {method} returned non-JSON: {r.text[:300]}", code="wallet_rpc_bad_json") from exc
    if isinstance(body, dict) and body.get("error"):
        err = body["error"]
        raise WalletError(
            f"RPC {method} error: {err.get('message', err)}",
            code="wallet_rpc_error",
            details=err,
        )
    return body if isinstance(body, dict) else {"result": body}


def _hex_to_int(v) -> int:
    if v is None:
        return 0
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        v = v.strip()
        if v.startswith("0x") or v.startswith("0X"):
            try:
                return int(v, 16)
            except ValueError:
                return 0
        try:
            return int(v)
        except ValueError:
            return 0
    return 0


# ---------------------------------------------------------------------------
# Balance
# ---------------------------------------------------------------------------
def get_balance_wei(address: str) -> int:
    if not address:
        return 0
    try:
        url = _rpc_url()
    except WalletError:
        return 0
    try:
        resp = _rpc_call(url, "eth_getBalance", [address, "latest"])
        return max(0, _hex_to_int(resp.get("result")))
    except Exception as exc:
        log.warning("balance_read_failed", address=address, error=str(exc))
        return 0


# ---------------------------------------------------------------------------
# Send
# ---------------------------------------------------------------------------
def send_gen(*, private_key: str, to_address: str, amount_wei: int) -> dict:
    """Sign locally and POST eth_sendRawTransaction. Returns tx info."""
    Account = _eth_account()
    account = Account.from_key(private_key)
    url = _rpc_url()

    nonce = _hex_to_int(_rpc_call(url, "eth_getTransactionCount", [account.address, "latest"]).get("result"))
    chain_id = _hex_to_int(_rpc_call(url, "eth_chainId", []).get("result"))

    try:
        gp_resp = _rpc_call(url, "eth_gasPrice", [])
        gas_price = _hex_to_int(gp_resp.get("result"))
    except Exception as exc:
        log.warning("gas_price_unavailable", error=str(exc))
        gas_price = 0

    try:
        to_checksum = to_checksum_address(to_address)
    except Exception as exc:
        raise WalletError(
            f"Recipient address is not a valid 0x address: {exc}",
            code="recipient_invalid",
        ) from exc

    tx = {
        "nonce": nonce,
        "to": to_checksum,
        "value": int(amount_wei),
        "gas": 21000,
        "gasPrice": gas_price,
        "chainId": chain_id,
    }

    log.info(
        "wallet_send_dispatch",
        from_addr=account.address,
        to=to_address,
        amount_wei=amount_wei,
        nonce=nonce,
        chain_id=chain_id,
        gas_price=gas_price,
    )

    signed = Account.sign_transaction(tx, private_key)
    raw = getattr(signed, "raw_transaction", None) or getattr(signed, "rawTransaction", None)
    if raw is None:
        raise WalletError("Could not obtain raw signed transaction.", code="wallet_send_no_raw")
    raw_hex = raw.hex() if isinstance(raw, bytes | bytearray) else str(raw)
    if not raw_hex.startswith("0x"):
        raw_hex = "0x" + raw_hex

    resp = _rpc_call(url, "eth_sendRawTransaction", [raw_hex])
    tx_hash = resp.get("result")
    if not tx_hash:
        raise WalletError(
            f"RPC eth_sendRawTransaction returned no tx hash. Response: {resp}",
            code="wallet_send_no_tx_hash",
        )

    log.info("wallet_send_landed", tx_hash=tx_hash, from_addr=account.address, to=to_address)
    return {
        "tx_hash": str(tx_hash),
        "from_address": account.address,
        "to_address": to_address,
        "amount_wei": int(amount_wei),
    }
