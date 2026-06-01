"""
Choose an LLM backend. genlayer is per-call (signed by the user wallet).
"""

from __future__ import annotations

from backend.app.core.config import settings
from services.llm.base import LLMClient
from services.llm.stub import StubLLMClient


def get_llm_client(*, account_private_key: str | None = None) -> LLMClient:
    if settings.llm_backend == "stub":
        return StubLLMClient()
    if settings.llm_backend == "genlayer":
        from services.llm.genlayer import GenLayerLLMClient
        return GenLayerLLMClient(account_private_key=account_private_key)
    raise ValueError(f"Unknown LLM_BACKEND: {settings.llm_backend}")
