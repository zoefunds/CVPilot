"""
Application request/response schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FileAssetPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: str
    original_filename: str
    content_type: str
    byte_size: int
    detected_kind: str | None = None
    extracted_text: str | None = None


class ApplicationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_url: str
    job_final_url: str | None = None
    job_title: str | None = None
    job_text: str | None = None
    linkedin_url: str | None = None
    portfolio_url: str | None = None
    status: str
    error: str | None = None
    created_at: datetime
    updated_at: datetime
    files: list[FileAssetPublic] = Field(default_factory=list)


class ApplicationListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_url: str
    job_title: str | None = None
    status: str
    created_at: datetime
