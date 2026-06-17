"""
Read-only GenLayer helpers. Used by the public verify endpoint to fetch a
stored evaluation by content_hash without requiring a user wallet or signing.
"""

from __future__ import annotations

import json
from functools import lru_cache


@lru_cache(maxsize=1)
def _client():
    # Lazy import so this module does not pull the SDK at import time.
    from services.llm.genlayer import GenLayerLLMClient
    return GenLayerLLMClient()  # ephemeral account; reads are unsigned


def fetch_extras(content_hash: str) -> dict:
    """Best-effort read of supplementary analyses stored by run_full_suite."""
    try:
        client = _client()
    except Exception:
        return {}
    out: dict = {}
    for key, fn in [
        ("skills_analysis",       "get_skills_analysis"),
        ("career_analysis",       "get_career_analysis"),
        ("cover_letter_analysis", "get_cover_letter_analysis"),
        ("salary_estimate",       "get_salary_estimate"),
    ]:
        ok, raw = client._try_read(fn, [content_hash])  # noqa: SLF001
        if ok and raw:
            try:
                out[key] = json.loads(raw) if isinstance(raw, str) else raw
            except Exception:
                pass
    return out


def fetch_stored_evaluation(content_hash: str) -> dict | None:
    """Read get_evaluation(content_hash) from the contract. Returns parsed
    JSON dict or None if missing/empty/unreadable."""
    try:
        client = _client()
    except Exception:
        return None
    ok, raw = client._try_read("get_evaluation", [content_hash])  # noqa: SLF001
    if not ok or not raw:
        return None
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return None
