"""
Symmetric encryption for at-rest storage of wallet private keys.
Key is derived from APP_SECRET_KEY via PBKDF2-HMAC-SHA256.
"""

from __future__ import annotations

import base64
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from backend.app.core.config import settings


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=settings.wallet_encryption_salt.encode("utf-8"),
        iterations=200_000,
    )
    key_bytes = kdf.derive(settings.app_secret_key.encode("utf-8"))
    return Fernet(base64.urlsafe_b64encode(key_bytes))


def encrypt_secret(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_secret(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Could not decrypt wallet private key. Wrong APP_SECRET_KEY?") from exc
