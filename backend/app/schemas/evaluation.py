"""
Evaluation response schema. Coerces NULL JSON list columns to empty lists
so a freshly-created pending row never breaks the response.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EvaluationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    application_id: uuid.UUID
    status: str
    backend: str | None = None

    # Scores
    cv_score: int | None = None
    cover_letter_score: int | None = None
    job_match_score: int | None = None
    ats_score: int | None = None
    competitiveness_score: int | None = None
    overall_score: int | None = None

    # Narrative
    summary: str | None = None
    improved_positioning: str | None = None

    # Lists
    recommendations: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    weak_statements: list[str] = Field(default_factory=list)
    company_alignment_notes: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)

    # Per-score rationale
    rationale: dict | None = None

    # Extended analyses (skills gap, career, cover letter, salary)
    extras: dict | None = None

    # Provenance
    raw: dict | None = None
    error: str | None = None
    contract_tx_hash: str | None = None
    content_hash: str | None = None
    contract_address: str | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator(
        "recommendations",
        "missing_keywords",
        "missing_skills",
        "weak_statements",
        "company_alignment_notes",
        "strengths",
        "risks",
        mode="before",
    )
    @classmethod
    def _none_to_list(cls, v):
        return v if v is not None else []
