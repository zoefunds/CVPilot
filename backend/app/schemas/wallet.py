"""
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
