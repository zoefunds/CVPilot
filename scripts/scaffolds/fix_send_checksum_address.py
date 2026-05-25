"""
eth_account rejects all-lowercase 0x addresses for the `to` field of a
transaction. Normalise via eth_utils.to_checksum_address before signing.
"""
from pathlib import Path

TARGET = Path("/Users/macbook/CVPilot/services/genlayer/wallet.py")
text = TARGET.read_text(encoding="utf-8")

# Add the import (best-effort placement near eth_account use).
if "from eth_utils import to_checksum_address" not in text:
    text = text.replace(
        "def _eth_account():",
        "from eth_utils import to_checksum_address  # type: ignore\n\n\ndef _eth_account():",
        1,
    )

# In send_gen, normalise to_address before constructing the tx.
OLD_TX = '''    tx = {
        "nonce": nonce,
        "to": to_address,
        "value": int(amount_wei),
        "gas": 21000,
        "gasPrice": gas_price,
        "chainId": chain_id,
    }'''

NEW_TX = '''    try:
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
    }'''

if OLD_TX in text:
    text = text.replace(OLD_TX, NEW_TX)
    print("patched tx dict to use checksum address")
else:
    print("warn: tx anchor not found; manual review needed")

TARGET.write_text(text, encoding="utf-8")
print(f"wrote {TARGET}")
