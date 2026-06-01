"""
Evaluation orchestrator. Takes the user wallet PK so the GenLayer LLM
client signs transactions from that user's address.
"""

from __future__ import annotations

from dataclasses import dataclass

from services.llm import LLMEvaluation
from services.llm.factory import get_llm_client


@dataclass(frozen=True)
class EvaluationOutcome:
    report: LLMEvaluation
    backend: str


def run_evaluation(
    *,
    cv_text: str,
    cover_letter_text: str,
    job_text: str,
    job_title: str | None,
    job_url: str,
    linkedin_url: str | None,
    portfolio_url: str | None,
    account_private_key: str | None = None,
) -> EvaluationOutcome:
    client = get_llm_client(account_private_key=account_private_key)
    report = client.evaluate(
        cv_text=cv_text,
        cover_letter_text=cover_letter_text,
        job_text=job_text,
        job_title=job_title,
        job_url=job_url,
        linkedin_url=linkedin_url,
        portfolio_url=portfolio_url,
    )
    return EvaluationOutcome(report=report, backend=report.raw.get("backend", "unknown"))
