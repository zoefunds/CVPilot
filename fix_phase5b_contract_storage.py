"""
Phase 5B Part 2 fix-up:
  1. services/llm/genlayer.py: make ping minimal, make cache-check best-effort.
  2. contracts/cvpilot/cvpilot_contract.py: corrected source with class-level
     type annotations so storage actually persists on-chain. User must redeploy
     this from GenLayer Studio and provide the new contract address.
"""

from __future__ import annotations
from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
FILES: dict[str, str] = {}


# -----------------------------------------------------------------------------
# 1. services/llm/genlayer.py — resilient ping + best-effort cache check
# -----------------------------------------------------------------------------
FILES["services/llm/genlayer.py"] = '''"""
GenLayer Intelligent Contract LLM backend.

Connects to the deployed CVPilotEvaluator contract on StudioNet.

Resilience notes:
- ping() only calls contract_version() (deterministic constant).
- evaluate() does a best-effort cache read; any RPC/contract error is treated
  as a cache miss so we still attempt the write path.
- After write we re-read get_evaluation(hash); if the contract\'s storage
  truly does not persist, we surface that with a clear error.
"""

import hashlib
import json
import sys
import time
from typing import Any

from backend.app.core.config import settings
from backend.app.core.errors import AppError
from backend.app.core.logging import get_logger
from services.llm.base import LLMClient, LLMEvaluation, LLMScore

log = get_logger("llm.genlayer")

_CV_MAX = 8000
_CL_MAX = 4000
_JOB_MAX = 6000
_RECEIPT_TIMEOUT_S = 240


class GenLayerClientError(AppError):
    status_code = 502
    code = "genlayer_error"


def _content_hash(cv: str, cl: str, job: str, title: str, url: str) -> str:
    blob = "||".join([cv, cl, job, title or "", url or ""]).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _truncate(s: str | None, limit: int) -> str:
    if not s:
        return ""
    return s if len(s) <= limit else s[:limit]


def _install_buffer_shim() -> None:
    if sys.version_info >= (3, 12):
        return
    import collections.abc as _abc
    if hasattr(_abc, "Buffer"):
        return
    try:
        from typing_extensions import Buffer as _Buffer  # type: ignore
        _abc.Buffer = _Buffer  # type: ignore[attr-defined]
    except Exception as exc:  # pragma: no cover
        log.warning("buffer_shim_failed", error=str(exc))


def _import_sdk():
    _install_buffer_shim()
    try:
        from genlayer_py import create_account, create_client  # type: ignore
        from genlayer_py.chains import studionet  # type: ignore
    except Exception as exc:
        raise GenLayerClientError(
            f"genlayer-py SDK is not installed or incompatible: {exc}",
            code="genlayer_sdk_missing",
        ) from exc
    return create_account, create_client, studionet


class GenLayerLLMClient(LLMClient):
    def __init__(self) -> None:
        if not settings.genlayer_contract_address:
            raise GenLayerClientError(
                "GENLAYER_CONTRACT_ADDRESS is not configured.",
                code="genlayer_address_missing",
            )
        create_account, create_client, studionet = _import_sdk()

        pk = (settings.genlayer_account_private_key or "").strip()
        if pk:
            try:
                self._account = create_account(account_private_key=pk)
            except TypeError:
                self._account = create_account(private_key=pk)
        else:
            self._account = create_account()

        self._client = create_client(chain=studionet, account=self._account)
        self._address = settings.genlayer_contract_address
        log.info(
            "genlayer_client_ready",
            address=self._address,
            account=str(getattr(self._account, "address", "")),
        )

    # ------------------------------------------------------------------------
    def _read_raw(self, fn_name: str, args: list) -> Any:
        return self._client.read_contract(
            address=self._address,
            function_name=fn_name,
            args=args,
        )

    def _read(self, fn_name: str, args: list) -> Any:
        try:
            return self._read_raw(fn_name, args)
        except Exception as exc:
            raise GenLayerClientError(
                f"GenLayer read_contract({fn_name}) failed: {exc}",
                code="genlayer_read_failed",
            ) from exc

    def _try_read(self, fn_name: str, args: list) -> tuple[bool, Any]:
        """Best-effort read. Returns (ok, value)."""
        try:
            return True, self._read_raw(fn_name, args)
        except Exception as exc:
            log.warning("genlayer_soft_read_failed", fn=fn_name, error=str(exc))
            return False, None

    def _write(self, fn_name: str, args: list) -> str:
        try:
            tx_hash = self._client.write_contract(
                address=self._address,
                function_name=fn_name,
                args=args,
            )
        except Exception as exc:
            raise GenLayerClientError(
                f"GenLayer write_contract({fn_name}) failed: {exc}",
                code="genlayer_write_failed",
            ) from exc

        wait = getattr(self._client, "wait_for_transaction_receipt", None)
        if wait is not None:
            try:
                wait(transaction_hash=tx_hash)
            except TypeError:
                try:
                    wait(tx_hash)
                except Exception as exc:
                    log.warning("genlayer_receipt_wait_failed", error=str(exc))
            except Exception as exc:
                log.warning("genlayer_receipt_wait_failed", error=str(exc))

        return str(tx_hash)

    # ------------------------------------------------------------------------
    def ping(self) -> dict:
        """Minimal connectivity check; only calls the deterministic view."""
        out = {"address": self._address, "version": None, "evaluation_count": None}
        ok, version = self._try_read("contract_version", [])
        if ok:
            out["version"] = version
        else:
            raise GenLayerClientError(
                "Contract is unreachable (contract_version failed).",
                code="genlayer_contract_unreachable",
            )
        ok2, count = self._try_read("evaluation_count", [])
        out["evaluation_count"] = count if ok2 else "unavailable"
        return out

    # ------------------------------------------------------------------------
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
    ) -> LLMEvaluation:
        cv = _truncate(cv_text, _CV_MAX)
        cl = _truncate(cover_letter_text, _CL_MAX)
        job = _truncate(job_text, _JOB_MAX)
        title = job_title or ""
        url = job_url or ""
        h = _content_hash(cv, cl, job, title, url)

        # Best-effort cache check (don\'t hard-fail on view errors).
        ok, existing = self._try_read("get_evaluation", [h])
        if ok and existing:
            log.info("genlayer_cache_hit", content_hash=h[:12])
            return self._build_evaluation(existing, contract_tx_hash=None, content_hash=h)

        log.info("genlayer_evaluate_dispatch", content_hash=h[:12])
        tx_hash = self._write(
            "evaluate_application",
            [h, cv, cl, job, title, url, linkedin_url or "", portfolio_url or ""],
        )
        log.info("genlayer_evaluate_landed", content_hash=h[:12], tx_hash=tx_hash)

        # Read back. If the contract\'s storage is broken, this returns "".
        ok2, stored = self._try_read("get_evaluation", [h])
        if not ok2 or not stored:
            raise GenLayerClientError(
                "Contract accepted the write but get_evaluation returned empty. "
                "The deployed contract likely has missing storage type annotations; "
                "redeploy the contract source from contracts/cvpilot/cvpilot_contract.py "
                "and update GENLAYER_CONTRACT_ADDRESS.",
                code="genlayer_storage_not_persistent",
            )
        return self._build_evaluation(stored, contract_tx_hash=tx_hash, content_hash=h)

    # ------------------------------------------------------------------------
    def _build_evaluation(
        self,
        raw_json: Any,
        *,
        contract_tx_hash: str | None,
        content_hash: str,
    ) -> LLMEvaluation:
        if isinstance(raw_json, dict):
            parsed = raw_json
        else:
            try:
                parsed = json.loads(raw_json)
            except Exception:
                parsed = {}

        rationale = parsed.get("rationale") if isinstance(parsed.get("rationale"), dict) else {}

        def _score(name: str, score_key: str) -> LLMScore:
            return LLMScore(
                value=int(parsed.get(score_key, 0) or 0),
                label=name,
                rationale=str(rationale.get(name, "")),
                signals={},
            )

        return LLMEvaluation(
            cv=_score("cv", "cv_score"),
            cover_letter=_score("cover_letter", "cover_letter_score"),
            job_match=_score("job_match", "job_match_score"),
            ats=_score("ats", "ats_score"),
            competitiveness=_score("competitiveness", "competitiveness_score"),
            summary=str(parsed.get("summary", "")),
            missing_keywords=list(parsed.get("missing_keywords") or []),
            missing_skills=list(parsed.get("missing_skills") or []),
            recommendations=list(parsed.get("recommendations") or []),
            weak_statements=list(parsed.get("weak_statements") or []),
            company_alignment_notes=list(parsed.get("company_alignment_notes") or []),
            raw={
                "backend": "genlayer",
                "version": 1,
                "contract_address": self._address,
                "contract_tx_hash": contract_tx_hash,
                "content_hash": content_hash,
                "scores": {
                    "cv": int(parsed.get("cv_score", 0) or 0),
                    "cover_letter": int(parsed.get("cover_letter_score", 0) or 0),
                    "job_match": int(parsed.get("job_match_score", 0) or 0),
                    "ats": int(parsed.get("ats_score", 0) or 0),
                    "competitiveness": int(parsed.get("competitiveness_score", 0) or 0),
                },
                "raw_contract_payload": parsed,
            },
        )
'''


# -----------------------------------------------------------------------------
# 2. contracts/cvpilot/cvpilot_contract.py — corrected with class-level types
# -----------------------------------------------------------------------------
FILES["contracts/cvpilot/cvpilot_contract.py"] = '''# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
#
# CVPilotEvaluator v0.2.0
# THIS IS A REDEPLOY-READY VERSION. The class-level type annotations
# (total_evaluated: int, evaluations: TreeMap[str, str]) are REQUIRED for
# storage to persist on-chain in GenLayer v0.2.x. The previous deployment
# at 0x26896541a3D18eE4ebc650EB58A9D6Ad79777e26 lacked these and reads of
# total_evaluated raise "execution failed".
#
# DEPLOY:
#   1. Open https://studio.genlayer.com (StudioNet selected)
#   2. Paste this file
#   3. Compile, Deploy (no constructor args)
#   4. Copy the new contract address
#   5. Paste it back to the chat; I will update .env
#
# Backend stays unchanged; only GENLAYER_CONTRACT_ADDRESS in .env changes.

from genlayer import *
import json


_CONTRACT_VERSION = "0.2.0"


class CVPilotEvaluator(gl.Contract):

    # Storage declarations (class-level type annotations are REQUIRED for
    # on-chain persistence in GenLayer v0.2.x).
    evaluations: TreeMap[str, str]
    total_evaluated: int

    def __init__(self):
        self.evaluations = TreeMap[str, str]()
        self.total_evaluated = 0

    # -------------------------
    # Views
    # -------------------------
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
                "summary": result,
                "missing_keywords": [],
                "missing_skills": [],
                "recommendations": [],
                "weak_statements": [],
                "company_alignment_notes": [],
                "rationale": {},
            }

        final_result = json.dumps(parsed)

        self.evaluations[content_hash] = final_result
        self.total_evaluated = self.total_evaluated + 1
        return final_result
'''


def write(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  wrote {rel}")


def main() -> None:
    for rel, content in FILES.items():
        write(rel, content)
    print("\\nPhase 5B contract-storage fix complete.")


if __name__ == "__main__":
    main()
