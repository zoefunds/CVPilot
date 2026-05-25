"""
Production-mode configuration guard.

Called once at app boot. In production, refuses to start the process if
any insecure default leaks into the running configuration. Fails loud
rather than silently insecure.
"""

from __future__ import annotations

from backend.app.core.config import settings
from backend.app.core.logging import get_logger

log = get_logger("startup_guard")


# Known unsafe sentinels that must never appear in production.
_UNSAFE_SECRETS = {
    "",
    "change_me",
    "changeme",
    "dev",
    "development",
    "secret",
    "supersecret",
    "please_change_me",
    "cvpilot_dev_secret",
}


def _check_secret_key(errors: list[str]) -> None:
    key = (settings.app_secret_key or "").strip()
    if key.lower() in _UNSAFE_SECRETS or len(key) < 32:
        errors.append(
            "APP_SECRET_KEY is unset, default, or shorter than 32 chars."
        )


def _check_debug(errors: list[str]) -> None:
    if settings.app_debug:
        errors.append("APP_DEBUG must be false in production.")


def _check_cors(errors: list[str]) -> None:
    origin = (settings.app_frontend_origin or "").strip()
    if origin in {"", "*"}:
        errors.append("APP_FRONTEND_ORIGIN must be an explicit https origin.")
    if origin.startswith("http://") and "localhost" not in origin and "127.0.0.1" not in origin:
        errors.append("APP_FRONTEND_ORIGIN must use https in production.")
    if "localhost" in origin or "127.0.0.1" in origin:
        errors.append("APP_FRONTEND_ORIGIN must not point at localhost in production.")


def _check_llm_backend(errors: list[str]) -> None:
    if settings.llm_backend != "genlayer":
        errors.append(
            f"LLM_BACKEND must be 'genlayer' in production (got {settings.llm_backend!r})."
        )


def _check_contract(errors: list[str]) -> None:
    addr = (getattr(settings, "genlayer_contract_address", "") or "").strip()
    if not addr.startswith("0x") or len(addr) != 42:
        errors.append("GENLAYER_CONTRACT_ADDRESS is missing or malformed.")


def assert_safe_startup() -> None:
    """Raise RuntimeError with all violations joined if running in
    production with any unsafe default. No-op in dev/staging/test."""
    if not settings.is_production:
        log.info("startup_guard_skipped", env=settings.app_env)
        return
    errors: list[str] = []
    _check_secret_key(errors)
    _check_debug(errors)
    _check_cors(errors)
    _check_llm_backend(errors)
    _check_contract(errors)
    if errors:
        joined = " | ".join(errors)
        log.error("startup_guard_failed", violations=errors)
        raise RuntimeError(f"Refusing to start: insecure production config: {joined}")
    log.info("startup_guard_passed", env=settings.app_env)
