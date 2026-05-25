"""
Persist the exact v0.3.1 source you deployed at
0xaFa7186407368dFc09a99eF299f3Cc3BED1c46c2 into the repo so contracts/
remains the canonical record of what's on-chain.
"""
from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
TARGET = ROOT / "contracts/cvpilot/cvpilot_contract.py"

SRC = '''# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
#
# CVPilotEvaluator v0.3.1
# DEPLOYED on StudioNet at: 0xaFa7186407368dFc09a99eF299f3Cc3BED1c46c2
#
# Key fix vs. earlier versions:
#   - Class-level type annotations declare on-chain storage slots.
#   - TreeMap.get(key, None) replaces `key in self.evaluations` to avoid
#     the AttributeError observed in v0.2.16 (`in` over storage maps is
#     unreliable; .get() is the supported lookup).

from genlayer import *
import json


_CONTRACT_VERSION = "0.3.1"


class CVPilotEvaluator(gl.Contract):
    """
    Evaluates CVs, cover letters, and job descriptions using GenLayer
    Intelligent Contracts + LLM reasoning.

    Storage:
      evaluations[content_hash] = JSON evaluation result
      total_evaluated = number of new evaluations stored
    """

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
        existing = self.evaluations.get(content_hash, None)
        return existing is not None

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

Your task is to evaluate a candidate's CV and cover letter against a job description.

Return ONLY valid JSON.
Do not include markdown.
Do not include explanations outside the JSON.

The JSON must follow this exact structure:

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
- Scores must be integers from 0 to 100.
- The overall_score should reflect the whole application strength.
- missing_keywords must contain important terms from the job description missing from the CV or cover letter.
- missing_skills must contain skills the candidate appears not to show clearly.
- recommendations must be practical and specific.
- weak_statements must identify vague, weak, or generic lines.
- company_alignment_notes must explain how well the application aligns with the company/job.
- strengths must identify what is already good.
- risks must identify what could make the applicant less competitive.
- improved_positioning should be a short paragraph explaining how the applicant should present themselves better.

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

        result = gl.nondet.exec_prompt(prompt)

        try:
            parsed = json.loads(result)
        except:
            parsed = {
                "cv_score": 0,
                "cover_letter_score": 0,
                "job_match_score": 0,
                "ats_score": 0,
                "competitiveness_score": 0,
                "overall_score": 0,
                "summary": str(result),
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

        final_result = json.dumps(parsed)
        self.evaluations[content_hash] = final_result
        self.total_evaluated = self.total_evaluated + u256(1)
        return final_result
'''
TARGET.write_text(SRC, encoding="utf-8")
print(f"synced {TARGET}")
