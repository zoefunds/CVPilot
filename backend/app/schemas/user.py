"""
Public user shape returned to clients.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    is_active: bool
    is_premium: bool
    is_superuser: bool
    email_verified: bool = False
    wallet_address: str | None = None
    created_at: datetime

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):  # type: ignore[override]
        # Derive `email_verified` from the ORM's email_verified_at timestamp.
        if hasattr(obj, "email_verified_at"):
            data = {
                "id": obj.id,
                "email": obj.email,
                "full_name": obj.full_name,
                "is_active": obj.is_active,
                "is_premium": obj.is_premium,
                "is_superuser": obj.is_superuser,
                "email_verified": obj.email_verified_at is not None,
                "wallet_address": obj.wallet_address,
                "created_at": obj.created_at,
            }
            return super().model_validate(data, *args, **kwargs)
        return super().model_validate(obj, *args, **kwargs)
