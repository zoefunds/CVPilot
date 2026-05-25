"""
v0.3.2: wrap gl.nondet.exec_prompt in gl.eq_principle.prompt_comparative
so the runtime accepts the LLM call inside a write method.
"""
from pathlib import Path

TARGET = Path("/Users/macbook/CVPilot/contracts/cvpilot/cvpilot_contract.py")

SRC = '''# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
#
# CVPilotEvaluator v0.3.2
#
# Key change vs v0.3.1: the LLM call is wrapped in
# gl.eq_principle.prompt_comparative(...). Bare gl.nondet.exec_prompt
# inside an @gl.public.write method is rejected by GenLayer with
# `SystemError: 6: forbidden` because validators cannot reach consensus
# on a non-deterministic result without an equivalence principle.

from genlayer import *
import json


_CONTRACT_VERSION = "0.3.2"


class CVPilotEvaluator(gl.Contract):

    evaluations: TreeMap[str, str]
    total_evaluated: u256

    def __init__(self):
        self.total_evaluated = u256(0)

    # -------------------------
    # Views
    # -------------------------
    @gl.public.view
    def contract_version(self) -> str:
        return _CONTRACT_VERSION

    @gl.public.view
    def evaluation_count(self):
        return self.total_evaluated

    @gl.public.view
    def get_evaluation(self, content_hash: str) -> str:
        existing = self.evaluations.get(content_hash, None)
        if existing is None:
            return ""
        return existing

    @gl.public.view
    def has_evaluation(self, content_hash: str) -> bool:
        return self.evaluations.get(content_hash, None) is not None

    # -------------------------
    # Write
    # -------------------------
    @gl.public.write
    def evaluate_application(
        self,
        content_hash: str,
        cv_text: str,
        cover_letter: str,
        job_text: str,
        job_title: str,
        job_url: str,
        linkedin_url: str,
        portfolio_url: str,
    ) -> str:
        existing = self.evaluations.get(content_hash, None)
        if existing is not None:
            return existing

        prompt = f"""
You are CVPilot, an expert ATS evaluator, recruiter, and career coach.

Evaluate the candidate's CV and cover letter against the job description below.

Return ONLY valid JSON. No markdown. No commentary outside the JSON.

JSON schema:
{{
  "cv_score": 0,
  "cover_letter_score": 0,
  "job_match_score": 0,
  "ats_score": 0,
  "competitiveness_score": 0,
  "overall_score": 0,
  "summary": "",
  "missing_keywords": [],
  "missing_skills": [],
  "recommendations": [],
  "weak_statements": [],
  "company_alignment_notes": [],
  "strengths": [],
  "risks": [],
  "improved_positioning": "",
  "rationale": {{
    "cv_score": "",
    "cover_letter_score": "",
    "job_match_score": "",
    "ats_score": "",
    "competitiveness_score": "",
    "overall_score": ""
  }}
}}

Rules:
- All scores must be integers from 0 to 100.
- recommendations must be specific and actionable.
- improved_positioning is a short paragraph.

JOB TITLE:
{job_title}

JOB URL:
{job_url}

LINKEDIN URL:
{linkedin_url}

PORTFOLIO URL:
{portfolio_url}

JOB DESCRIPTION:
{job_text}

CV:
{cv_text}

COVER LETTER:
{cover_letter}
"""

        def _llm_task():
            raw = gl.nondet.exec_prompt(prompt)
            # Coerce to a stable, JSON-parseable string before returning.
            try:
                parsed = json.loads(raw)
            except:
                parsed = {
                    "cv_score": 0,
                    "cover_letter_score": 0,
                    "job_match_score": 0,
                    "ats_score": 0,
                    "competitiveness_score": 0,
                    "overall_score": 0,
                    "summary": str(raw)[:500],
                    "missing_keywords": [],
                    "missing_skills": [],
                    "recommendations": [],
                    "weak_statements": [],
                    "company_alignment_notes": [],
                    "strengths": [],
                    "risks": [],
                    "improved_positioning": "",
                    "rationale": {
                        "cv_score": "LLM output was not valid JSON.",
                        "cover_letter_score": "LLM output was not valid JSON.",
                        "job_match_score": "LLM output was not valid JSON.",
                        "ats_score": "LLM output was not valid JSON.",
                        "competitiveness_score": "LLM output was not valid JSON.",
                        "overall_score": "LLM output was not valid JSON.",
                    },
                }
            return json.dumps(parsed)

        final_result = gl.eq_principle.prompt_comparative(
            task=_llm_task,
            criteria=(
                "Two evaluations are equivalent if they both parse as JSON "
                "with the same top-level keys, all numeric scores differ by "
                "no more than 15 points, and the overall verdict (strong, "
                "mixed, or weak) is the same."
            ),
        )

        self.evaluations[content_hash] = final_result
        self.total_evaluated = self.total_evaluated + u256(1)
        return final_result
'''

TARGET.write_text(SRC, encoding="utf-8")
print(f"wrote {TARGET}")
