"""
Admin response schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class AdminStats(BaseModel):
    user_count: int
    application_count: int
    evaluations_complete: int
    evaluations_failed: int
    last_24h_users: int
    last_24h_applications: int
    by_status: dict[str, int]


class AdminUserListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    is_active: bool
    is_premium: bool
    is_superuser: bool
    created_at: datetime
    application_count: int = 0
    last_application_at: datetime | None = None


class AdminApplicationListItem(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    user_email: EmailStr
    job_url: str
    job_title: str | None
    status: str
    created_at: datetime
    has_evaluation: bool = False
    competitiveness: int | None = None
