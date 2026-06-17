"""
Switch backend to the freshly deployed contract address and sync the repo
contract source to what is actually on-chain.
"""

from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
ADDR = "0xEEE67a3D702B15E417010317430938B0626a7641"

# 1. Update .env
env_path = ROOT / ".env"
lines = env_path.read_text(encoding="utf-8").splitlines()
out = []
seen = False
for ln in lines:
    if ln.startswith("GENLAYER_CONTRACT_ADDRESS"):
        out.append(f"GENLAYER_CONTRACT_ADDRESS={ADDR}")
        seen = True
    else:
        out.append(ln)
if not seen:
    out.append(f"GENLAYER_CONTRACT_ADDRESS={ADDR}")
env_path.write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"set GENLAYER_CONTRACT_ADDRESS={ADDR}")

# 2. Sync repo contract file to what is actually deployed
contract_src = '''# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
#
# CVPilotEvaluator v0.2.0
# DEPLOYED on StudioNet at: 0xEEE67a3D702B15E417010317430938B0626a7641
#
# Lesson learned: in v0.2.16, parameter/return type hints on @gl.public methods
# break execution. Plain Python (no annotations) is the safe path. Storage
# fields are initialised directly in __init__ without class-level types.

from genlayer import *
import json


_CONTRACT_VERSION = "0.2.0"


class CVPilotEvaluator(gl.Contract):

    def __init__(self):
        self.evaluations = {}
        self.total_evaluated = 0

    # -------------------------
    # VIEWS (NO TYPE HINTS)
    # -------------------------
    @gl.public.view
    def contract_version(self):
        return _CONTRACT_VERSION

    @gl.public.view
    def evaluation_count(self):
        return self.total_evaluated

    @gl.public.view
    def get_evaluation(self, content_hash):
        return self.evaluations.get(content_hash, "")

    @gl.public.view
    def has_evaluation(self, content_hash):
        return content_hash in self.evaluations

    # -------------------------
    # WRITE
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
Return ONLY JSON.

cv_score, cover_letter_score, job_match_score,
ats_score, competitiveness_score,
summary,
missing_keywords,
missing_skills,
recommendations,
weak_statements,
company_alignment_notes,
rationale

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

        self.evaluations[content_hash] = json.dumps(parsed)
        self.total_evaluated += 1

        return self.evaluations[content_hash]
'''
(ROOT / "contracts/cvpilot/cvpilot_contract.py").write_text(contract_src, encoding="utf-8")
print("synced contracts/cvpilot/cvpilot_contract.py to deployed source")
