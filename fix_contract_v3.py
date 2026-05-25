"""
Write the v0.3.0 contract source with class-level type annotations so storage
actually persists. User redeploys via GenLayer Studio and provides the new
contract address.
"""
from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
TARGET = ROOT / "contracts/cvpilot/cvpilot_contract.py"

SRC = '''# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
#
# CVPilotEvaluator v0.3.0
# THE KEY FIX: class-level type annotations are required for state to persist
# across calls in GenLayer v0.2.x. Without them, attributes set inside
# __init__ are lost after the deploy transaction (verified by the
# AttributeError seen on the previous deployment at
# 0xc9A54400efaE50e1F3DdfBac9FD5DB78Ef648A9e).
#
# Deploy:
#   1. Open https://studio.genlayer.com  (StudioNet selected)
#   2. Paste this file
#   3. Compile, Deploy (no constructor args)
#   4. Call contract_version() -> "0.3.0", evaluation_count() -> 0
#   5. Send the new contract address to the chat
#
# If compilation fails on the storage annotations, paste me the exact
# Studio error and I will adjust the type names. The patterns below are
# what current GenLayer docs prescribe.

from genlayer import *
import json


_CONTRACT_VERSION = "0.3.0"


class CVPilotEvaluator(gl.Contract):

    # Persistent storage. Class-level annotations create storage slots that
    # the runtime actually persists between calls.
    evaluations: TreeMap[str, str]
    total_evaluated: u256

    def __init__(self):
        # TreeMap[str, str] storage is auto-initialised by the SDK; we only
        # initialise the counter explicitly.
        self.total_evaluated = u256(0)

    # -------------------------
    # Views (no parameter or return annotations beyond storage)
    # -------------------------
    @gl.public.view
    def contract_version(self):
        return _CONTRACT_VERSION

    @gl.public.view
    def evaluation_count(self):
        return self.total_evaluated

    @gl.public.view
    def get_evaluation(self, content_hash):
        if content_hash in self.evaluations:
            return self.evaluations[content_hash]
        return ""

    @gl.public.view
    def has_evaluation(self, content_hash):
        return content_hash in self.evaluations

    # -------------------------
    # Write
    # -------------------------
    @gl.public.write
    def evaluate_application(
        self,
        content_hash,
        cv_text,
        cover_letter,
        job_text,
        job_title,
        job_url,
        linkedin_url,
        portfolio_url,
    ):
        if content_hash in self.evaluations:
            return self.evaluations[content_hash]

        prompt = f"""
You are an ATS and recruiter system.

Return ONLY valid JSON with:
cv_score, cover_letter_score, job_match_score,
ats_score, competitiveness_score,
summary, missing_keywords, missing_skills,
recommendations, weak_statements,
company_alignment_notes,
rationale object.

JOB TITLE:
{job_title}

JOB:
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
                "summary": str(result),
                "missing_keywords": [],
                "missing_skills": [],
                "recommendations": [],
                "weak_statements": [],
                "company_alignment_notes": [],
                "rationale": {},
            }

        final_result = json.dumps(parsed)
        self.evaluations[content_hash] = final_result
        self.total_evaluated = self.total_evaluated + u256(1)
        return final_result
'''

TARGET.write_text(SRC, encoding="utf-8")
print(f"wrote {TARGET}")
