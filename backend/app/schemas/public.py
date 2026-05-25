"""
Public verification response. PII-free.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class PublicEvaluation(BaseModel):
    content_hash: str
    contract_address: str
    found: bool

    cv_score: int | None = None
    cover_letter_score: int | None = None
    job_match_score: int | None = None
    ats_score: int | None = None
    competitiveness_score: int | None = None
    overall_score: int | None = None

    summary: str | None = None
    improved_positioning: str | None = None
    missing_keywords: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    weak_statements: list[str] = Field(default_factory=list)
    company_alignment_notes: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    rationale: dict | None = None

    @field_validator(
        "missing_keywords", "missing_skills", "recommendations",
        "weak_statements", "company_alignment_notes", "strengths", "risks",
        mode="before",
    )
    @classmethod
    def _none_to_list(cls, v):
        return v if v is not None else []
