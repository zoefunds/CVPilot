"""
Centralized typed settings.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="CVPilot", alias="APP_NAME")
    app_env: Literal["development", "staging", "production"] = Field(
        default="development", alias="APP_ENV"
    )
    app_debug: bool = Field(default=True, alias="APP_DEBUG")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    app_secret_key: str = Field(default="change-me", alias="APP_SECRET_KEY")
    app_frontend_origin: str = Field(default="http://localhost:3000", alias="APP_FRONTEND_ORIGIN")

    database_url: PostgresDsn = Field(alias="DATABASE_URL")
    database_pool_size: int = Field(default=10, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, alias="DATABASE_MAX_OVERFLOW")

    redis_url: RedisDsn = Field(alias="REDIS_URL")
    celery_broker_url: str = Field(alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(alias="CELERY_RESULT_BACKEND")

    jwt_secret: str = Field(default="change-me", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expires_min: int = Field(default=720, alias="JWT_ACCESS_TOKEN_EXPIRES_MIN")
    jwt_refresh_token_expires_days: int = Field(default=7, alias="JWT_REFRESH_TOKEN_EXPIRES_DAYS")

    storage_backend: Literal["local", "s3"] = Field(default="local", alias="STORAGE_BACKEND")
    storage_local_path: str = Field(default="./storage/uploads", alias="STORAGE_LOCAL_PATH")
    storage_max_upload_mb: int = Field(default=10, alias="STORAGE_MAX_UPLOAD_MB")

    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")
    rate_limit_burst: int = Field(default=20, alias="RATE_LIMIT_BURST")

    genlayer_studionet_rpc: str = Field(
        default="https://studio.genlayer.com/api", alias="GENLAYER_STUDIONET_RPC"
    )
    genlayer_account_private_key: str = Field(default="", alias="GENLAYER_ACCOUNT_PRIVATE_KEY")
    genlayer_contract_address: str = Field(default="", alias="GENLAYER_CONTRACT_ADDRESS")
    genlayer_llm_model: str = Field(default="default", alias="GENLAYER_LLM_MODEL")
    llm_backend: Literal["stub", "genlayer"] = Field(default="stub", alias="LLM_BACKEND")

    # Wallet + balance gate
    wallet_encryption_salt: str = Field(default="cvpilot-wallet-v1", alias="WALLET_ENCRYPTION_SALT")
    # Min balance (in wei) required before a user can submit an application.
    # 0.5 GEN expressed in wei: 500000000000000000
    min_submit_balance_wei: int = Field(default=500_000_000_000_000_000, alias="MIN_SUBMIT_BALANCE_WEI")
    # When True (production default), only LLM_BACKEND=genlayer is allowed.
    force_genlayer_in_production: bool = Field(default=True, alias="FORCE_GENLAYER_IN_PRODUCTION")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_json: bool = Field(default=True, alias="LOG_JSON")

    # Email (Brevo transactional API)
    brevo_api_key: str = Field(default="", alias="BREVO_API_KEY")
    brevo_sender_email: str = Field(default="", alias="BREVO_SENDER_EMAIL")
    brevo_sender_name: str = Field(default="CVPilot", alias="BREVO_SENDER_NAME")

    # Password reset
    password_reset_token_ttl_min: int = Field(
        default=30, alias="PASSWORD_RESET_TOKEN_TTL_MIN"
    )

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    s = Settings()  # type: ignore[call-arg]
    if s.is_production and s.force_genlayer_in_production and s.llm_backend != "genlayer":
        raise RuntimeError(
            "LLM_BACKEND must be 'genlayer' in production. Set LLM_BACKEND=genlayer or "
            "FORCE_GENLAYER_IN_PRODUCTION=false."
        )
    return s


settings = get_settings()
