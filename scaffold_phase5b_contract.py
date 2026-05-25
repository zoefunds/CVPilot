"""
CVPilot Phase 5B Part 1.
Writes the GenLayer Intelligent Contract and StudioNet deploy runbook.
"""

from __future__ import annotations
from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")

FILES: dict[str, str] = {}

# -----------------------------------------------------------------------------
# Intelligent Contract
# -----------------------------------------------------------------------------
FILES["contracts/cvpilot/cvpilot_contract.py"] = '''"""
CVPilot Intelligent Contract.

A GenLayer Intelligent Contract that evaluates a job application
(CV + cover letter + job description) under validator consensus
and stores the result on-chain, keyed by a content hash.

Deploy target: StudioNet
Author: CVPilot
Version: 0.1.0

Methods:
    evaluate_application(...)   -> JSON string (write)
    get_evaluation(content_hash) -> JSON string (view, "" if missing)
    evaluation_count()           -> int (view)
    contract_version()           -> str (view)

The returned JSON object has the exact shape the backend expects:
{
  "cv_score": int,                    # 0..100
  "cover_letter_score": int,          # 0..100
  "job_match_score": int,             # 0..100
  "ats_score": int,                   # 0..100
  "competitiveness_score": int,       # 0..100
  "summary": str,
  "missing_keywords": [str],
  "missing_skills":   [str],
  "recommendations":  [str],
  "weak_statements":  [str],
  "company_alignment_notes": [str],
  "rationale": {
    "cv": str,
    "cover_letter": str,
    "job_match": str,
    "ats": str,
    "competitiveness": str
  },
  "version": int
}
"""

from genlayer import *

import json
import hashlib


_CONTRACT_VERSION = "0.1.0"

# Conservative caps to keep prompt budget predictable across validators.
_MAX_CV_CHARS = 8000
_MAX_COVER_LETTER_CHARS = 4000
_MAX_JOB_CHARS = 6000


def _truncate(s: str, limit: int) -> str:
    if s is None:
        return ""
    return s if len(s) <= limit else s[:limit]


def _content_hash(cv: str, cl: str, job: str, job_title: str, job_url: str) -> str:
    blob = "||".join([cv, cl, job, job_title, job_url]).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _clamp_int(value, lo: int = 0, hi: int = 100) -> int:
    try:
        v = int(value)
    except Exception:
        v = 0
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def _coerce_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value if x is not None]
    if isinstance(value, str):
        return [value] if value else []
    return []


def _normalize_result(parsed: dict) -> dict:
    """Force a stable shape so downstream consumers never crash."""
    rationale = parsed.get("rationale") or {}
    if not isinstance(rationale, dict):
        rationale = {}

    normalized = {
        "cv_score": _clamp_int(parsed.get("cv_score", 0)),
        "cover_letter_score": _clamp_int(parsed.get("cover_letter_score", 0)),
        "job_match_score": _clamp_int(parsed.get("job_match_score", 0)),
        "ats_score": _clamp_int(parsed.get("ats_score", 0)),
        "competitiveness_score": _clamp_int(parsed.get("competitiveness_score", 0)),
        "summary": str(parsed.get("summary", ""))[:1200],
        "missing_keywords": _coerce_list(parsed.get("missing_keywords"))[:25],
        "missing_skills": _coerce_list(parsed.get("missing_skills"))[:20],
        "recommendations": _coerce_list(parsed.get("recommendations"))[:15],
        "weak_statements": _coerce_list(parsed.get("weak_statements"))[:15],
        "company_alignment_notes": _coerce_list(parsed.get("company_alignment_notes"))[:10],
        "rationale": {
            "cv": str(rationale.get("cv", ""))[:600],
            "cover_letter": str(rationale.get("cover_letter", ""))[:600],
            "job_match": str(rationale.get("job_match", ""))[:600],
            "ats": str(rationale.get("ats", ""))[:600],
            "competitiveness": str(rationale.get("competitiveness", ""))[:600],
        },
        "version": 1,
    }
    return normalized


@gl.contract
class CVPilotEvaluator:
    """On-chain CV / job-fit evaluator with verifiable LLM consensus."""

    # Persistent state: content_hash -> evaluation JSON
    evaluations: TreeMap[str, str]
    total_evaluated: int

    def __init__(self) -> None:
        self.evaluations = TreeMap[str, str]()
        self.total_evaluated = 0

    # -------------------------------------------------------------------------
    # Views
    # -------------------------------------------------------------------------
    @gl.public.view
    def contract_version(self) -> str:
        return _CONTRACT_VERSION

    @gl.public.view
    def evaluation_count(self) -> int:
        return self.total_evaluated

    @gl.public.view
    def get_evaluation(self, content_hash: str) -> str:
        if content_hash in self.evaluations:
            return self.evaluations[content_hash]
        return ""

    @gl.public.view
    def has_evaluation(self, content_hash: str) -> bool:
        return content_hash in self.evaluations

    # -------------------------------------------------------------------------
    # Write: evaluate_application
    # -------------------------------------------------------------------------
    @gl.public.write
    def evaluate_application(
        self,
        cv_text: str,
        cover_letter_text: str,
        job_text: str,
        job_title: str,
        job_url: str,
        linkedin_url: str,
        portfolio_url: str,
    ) -> str:
        cv = _truncate(cv_text, _MAX_CV_CHARS)
        cl = _truncate(cover_letter_text, _MAX_COVER_LETTER_CHARS)
        job = _truncate(job_text, _MAX_JOB_CHARS)

        h = _content_hash(cv, cl, job, job_title or "", job_url or "")

        # Idempotency: same inputs return the previously consensus-stored result.
        if h in self.evaluations:
            return self.evaluations[h]

        prompt = f"""You are a senior recruiter and ATS expert. Evaluate the following job
application objectively and return ONLY a single JSON object with these EXACT keys:

  cv_score (integer 0-100)
  cover_letter_score (integer 0-100)
  job_match_score (integer 0-100)
  ats_score (integer 0-100)
  competitiveness_score (integer 0-100)
  summary (string, one paragraph)
  missing_keywords (list of strings - keywords from the job not present in the CV)
  missing_skills (list of strings - hard skills from the job missing from the CV)
  recommendations (list of strings - concrete, actionable improvements)
  weak_statements (list of strings - bullets in the CV that should be rewritten)
  company_alignment_notes (list of strings - mission/values/culture observations)
  rationale (object with keys cv, cover_letter, job_match, ats, competitiveness - each a short string)

Output a SINGLE JSON object. Do NOT wrap it in markdown fences. Do NOT add any commentary.

== JOB TITLE ==
{job_title}

== JOB URL ==
{job_url}

== JOB DESCRIPTION ==
{job}

== CV ==
{cv}

== COVER LETTER ==
{cl}

== LINKEDIN ==
{linkedin_url}

== PORTFOLIO ==
{portfolio_url}
"""

        def llm_task() -> str:
            raw = gl.nondet.exec_prompt(prompt)
            cleaned = (raw or "").strip()
            # Strip code fences defensively
            if cleaned.startswith("```"):
                cleaned = cleaned.strip("`")
                if cleaned.lower().startswith("json"):
                    cleaned = cleaned[4:].lstrip()
            # Find the outermost JSON object boundaries
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start == -1 or end == -1 or end <= start:
                # Force structurally valid fallback
                return json.dumps(_normalize_result({}))
            payload = cleaned[start : end + 1]
            try:
                parsed = json.loads(payload)
            except Exception:
                parsed = {}
            return json.dumps(_normalize_result(parsed if isinstance(parsed, dict) else {}))

        result_json = gl.eq_principle.prompt_comparative(
            task=llm_task,
            criteria=(
                "Two evaluations are equivalent if EVERY numeric score "
                "(cv_score, cover_letter_score, job_match_score, ats_score, "
                "competitiveness_score) differs by at most 10 points, AND "
                "the recommendations lists share at least one item in spirit, "
                "AND the summaries convey the same overall verdict "
                "(strong / mixed / weak)."
            ),
        )

        # Persist consensus result.
        self.evaluations[h] = result_json
        self.total_evaluated = self.total_evaluated + 1
        return result_json
'''

# -----------------------------------------------------------------------------
# Deploy runbook (contracts/cvpilot/README.md)
# -----------------------------------------------------------------------------
FILES["contracts/cvpilot/README.md"] = '''# CVPilot Intelligent Contract

A GenLayer Intelligent Contract that performs verifiable, consensus-driven
evaluation of a job application (CV + cover letter + job description).

## Source

`cvpilot_contract.py`

## Deploy to StudioNet (web IDE)

You will deploy this contract once and paste the resulting address back into
the project. After that, every `LLM_BACKEND=genlayer` evaluation calls this
on-chain contract instead of the local stub.

### 1. Open GenLayer Studio

Visit **https://studio.genlayer.com**

If you have not connected a wallet/account yet, follow the Studio onboarding.
Make sure the network selector shows **StudioNet**.

### 2. Paste the contract

1. In Studio, open a new contract / project.
2. Copy the entire contents of `cvpilot_contract.py`.
3. Paste it into the Studio code editor.

### 3. Compile

Click **Compile**. You should see no errors. The Studio tooling will detect
the `@gl.contract` class `CVPilotEvaluator`.

### 4. Deploy

1. Click **Deploy**.
2. Constructor takes no arguments — leave fields blank.
3. Confirm the transaction.
4. Wait for finalization (a few seconds on StudioNet).

### 5. Copy the contract address

Studio will display the deployed contract address (`0x...`).
**Copy this address.** It is what we will paste into `.env`:
GENLAYER_CONTRACT_ADDRESS=0xYourDeployedAddressHere

### 6. Smoke-test from Studio
In the Studio UI you can call methods directly:
- `contract_version()` should return `"0.1.0"`.
- `evaluation_count()` should return `0`.
- `has_evaluation("0x0000...")` should return `false`.
You don't need to call `evaluate_application` from Studio — our backend will
drive that call in Phase 5B Part 2.
### 7. Hand the address back
Paste the contract address into this chat. I will:
1. Update `.env` (`GENLAYER_CONTRACT_ADDRESS=...`).
2. Implement `services/llm/genlayer.py` to call this contract.
3. Add a smoke test that flips `LLM_BACKEND=genlayer` and runs a real
   on-chain evaluation.
## Why this design
- **Idempotency** — same inputs hash to the same key, so re-evaluating costs
  no extra LLM consensus calls and returns the canonical stored verdict.
- **Schema stability** — the contract NORMALIZES the LLM output before
  storage, so backend code never sees malformed JSON.
- **Validator consensus** — `gl.eq_principle.prompt_comparative` enforces
  that multiple validators must agree (within tolerance) on the scoring
  before it lands on-chain. That is CVPilot's trust layer.
- **On-chain auditability** — every evaluation lives in `evaluations`
  keyed by `sha256(cv || cover_letter || job || title || url)`. Anyone
  can replay the lookup and verify the verdict.
'''
# Mirror the runbook under docs/ for our docs tree.
FILES["docs/contracts/deploy.md"] = FILES["contracts/cvpilot/README.md"]
def write(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  wrote {rel}")
def main() -> None:
    print(f"Phase 5B Part 1 into: {ROOT}")
    for rel, content in FILES.items():
        write(rel, content)
    print("\nPhase 5B Part 1 files written.")
if __name__ == "__main__":
    main()
