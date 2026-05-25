"""
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
