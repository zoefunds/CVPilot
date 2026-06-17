"""
Point CVPilot at the working v0.3.3 contract and persist the deployed source
into the repo as the canonical record.
"""
from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
ADDR = "0x58D88438Ce840A31d9951048929521963E9396f0"

# 1) Update .env
env = ROOT / ".env"
lines = env.read_text(encoding="utf-8").splitlines()
out, seen = [], False
for ln in lines:
    if ln.startswith("GENLAYER_CONTRACT_ADDRESS"):
        out.append(f"GENLAYER_CONTRACT_ADDRESS={ADDR}")
        seen = True
    else:
        out.append(ln)
if not seen:
    out.append(f"GENLAYER_CONTRACT_ADDRESS={ADDR}")
env.write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"set GENLAYER_CONTRACT_ADDRESS={ADDR}")

# 2) Sync contract source to what is actually deployed at that address.
target = ROOT / "contracts/cvpilot/cvpilot_contract.py"
target.write_text(
    '''# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
#
# CVPilotEvaluator v0.3.3
# DEPLOYED on StudioNet at: 0x58D88438Ce840A31d9951048929521963E9396f0
#
# Key working pattern:
#   * Storage declared via class-level type annotations
#       evaluations: TreeMap[str, str]
#       total_evaluated: u256
#   * LLM call wrapped in gl.eq_principle.prompt_comparative(callable, criteria)
#     to satisfy GenLayer consensus on non-deterministic outputs.
#     Bare gl.nondet.exec_prompt inside a write method is rejected with
#     SystemError: 6: forbidden.

from genlayer import *
import json


_CONTRACT_VERSION = "0.3.3"


class CVPilotEvaluator(gl.Contract):

    evaluations: TreeMap[str, str]
    total_evaluated: u256

    def __init__(self):
        self.total_evaluated = u256(0)

    @gl.public.view
    def contract_version(self) -> str:
        return _CONTRACT_VERSION

    @gl.public.view
    def evaluation_count(self) -> u256:
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
- improved_positioning must be a short paragraph.
- missing_keywords, missing_skills, recommendations, weak_statements,
  company_alignment_notes, strengths, and risks must be arrays of strings.
- rationale must explain each score briefly.
- Return valid JSON only.

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

        def get_evaluation_from_llm():
            raw = gl.nondet.exec_prompt(prompt)
            cleaned = str(raw)
            cleaned = cleaned.replace("```json", "")
            cleaned = cleaned.replace("```", "")
            cleaned = cleaned.strip()
            try:
                parsed = json.loads(cleaned)
            except:
                parsed = {
                    "cv_score": 0,
                    "cover_letter_score": 0,
                    "job_match_score": 0,
                    "ats_score": 0,
                    "competitiveness_score": 0,
                    "overall_score": 0,
                    "summary": cleaned[:500],
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
                        "overall_score": "LLM output was not valid JSON."
                    }
                }
            return json.dumps(parsed, sort_keys=True)

        final_result = gl.eq_principle.prompt_comparative(
            get_evaluation_from_llm,
            """
Two CVPilot evaluations are equivalent if:

1. Both outputs are valid JSON strings.
2. Both outputs contain the same top-level schema fields.
3. All numeric scores are integers from 0 to 100.
4. Score differences are acceptable if each corresponding score differs by no more than 15 points.
5. The overall hiring verdict must be the same:
   - strong if overall_score is 75 or above
   - mixed if overall_score is between 50 and 74
   - weak if overall_score is below 50
6. Recommendations, risks, strengths, and missing skills do not need exact wording, but must express substantially similar career advice.
7. The evaluation must be based on the provided CV, cover letter, job description, job title, and URLs.
"""
        )

        self.evaluations[content_hash] = final_result
        self.total_evaluated = self.total_evaluated + u256(1)
        return final_result
''',
    encoding="utf-8",
)
print(f"synced {target}")
