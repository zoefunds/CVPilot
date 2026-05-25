"""
Pluggable LLM client interface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class LLMScore:
    value: int
    label: str
    rationale: str
    signals: dict = field(default_factory=dict)


@dataclass(frozen=True)
class LLMEvaluation:
    cv: LLMScore
    cover_letter: LLMScore
    job_match: LLMScore
    ats: LLMScore
    competitiveness: LLMScore
    overall: LLMScore
    summary: str
    improved_positioning: str
    missing_keywords: list[str]
    missing_skills: list[str]
    recommendations: list[str]
    weak_statements: list[str]
    company_alignment_notes: list[str]
    strengths: list[str]
    risks: list[str]
    rationale: dict
    raw: dict


class LLMClient(Protocol):
    def evaluate(
        self,
        *,
        cv_text: str,
        cover_letter_text: str,
        job_text: str,
        job_title: str | None,
        job_url: str,
        linkedin_url: str | None,
        portfolio_url: str | None,
    ) -> LLMEvaluation: ...
