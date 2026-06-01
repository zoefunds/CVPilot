"""
GenLayer Intelligent Contract LLM backend. Per-user signing.
"""

import hashlib
import json
import sys
import time

from backend.app.core.config import settings
from backend.app.core.errors import AppError
from backend.app.core.logging import get_logger
from services.llm.base import LLMClient, LLMEvaluation, LLMScore

log = get_logger("llm.genlayer")

_CV_MAX = 8000
_CL_MAX = 4000
_JOB_MAX = 6000
_READ_POLL_S = 240
_READ_INTERVAL_S = 5


class GenLayerClientError(AppError):
    status_code = 502
    code = "genlayer_error"


def _normalised_content_hash(*, cv, cl, job, title, job_url, linkedin_url, portfolio_url):
    payload = json.dumps(
        {
            "cv_text": (cv or "").strip(),
            "cover_letter": (cl or "").strip(),
            "job_text": (job or "").strip(),
            "job_title": (title or "").strip(),
            "job_url": (job_url or "").strip(),
            "linkedin_url": (linkedin_url or "").strip(),
            "portfolio_url": (portfolio_url or "").strip(),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _truncate(s, limit):
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
    except Exception:
        pass


def _import_sdk():
    _install_buffer_shim()
    try:
        from genlayer_py import create_account, create_client  # type: ignore
        from genlayer_py.chains import studionet  # type: ignore
        try:
            from genlayer_py.types import TransactionStatus  # type: ignore
        except Exception:
            TransactionStatus = None
    except Exception as exc:
        raise GenLayerClientError(
            f"genlayer-py SDK is not installed or incompatible: {exc}",
            code="genlayer_sdk_missing",
        ) from exc
    return create_account, create_client, studionet, TransactionStatus


def _serialise_receipt(receipt) -> dict:
    out: dict = {}
    if receipt is None:
        return out
    for attr in ("status", "consensus_result", "execution_result", "result", "tx_hash", "transaction_hash", "error", "error_message", "stdout", "stderr"):
        try:
            v = getattr(receipt, attr, None)
            if v is None:
                continue
            out[attr] = str(v)[:2000]
        except Exception:
            continue
    return out



def _extract_eval_json_from_receipt(receipt) -> str | None:
    """Recursively search a finalized receipt for our evaluation JSON.

    The GenLayer SDK puts the leader's return value somewhere in the
    consensus_data tree, but the exact path varies between SDK versions.
    Rather than depend on a specific shape, we walk the whole structure
    and grab the first string that parses to a dict with our well-known
    evaluation keys.
    """
    target_keys = ("overall_score", "cv_score", "ats_score")

    def _try_parse(s: str):
        s = s.strip()
        # GenVM sometimes double-encodes: "\"{...}\""
        if s.startswith('"') and s.endswith('"'):
            try:
                inner = json.loads(s)
                if isinstance(inner, str):
                    s = inner
            except Exception:
                pass
        if not (s.startswith("{") and s.endswith("}")):
            return None
        if not any(k in s for k in target_keys):
            return None
        try:
            parsed = json.loads(s)
        except Exception:
            return None
        if isinstance(parsed, dict) and any(k in parsed for k in target_keys):
            return s
        return None

    seen: set[int] = set()

    def _walk(obj):
        oid = id(obj)
        if oid in seen:
            return None
        seen.add(oid)
        if isinstance(obj, str):
            return _try_parse(obj)
        if isinstance(obj, bytes | bytearray):
            try:
                return _try_parse(obj.decode("utf-8", errors="ignore"))
            except Exception:
                return None
        if isinstance(obj, dict):
            for v in obj.values():
                r = _walk(v)
                if r:
                    return r
            return None
        if isinstance(obj, list | tuple | set):
            for v in obj:
                r = _walk(v)
                if r:
                    return r
            return None
        if hasattr(obj, "__dict__"):
            try:
                for v in vars(obj).values():
                    r = _walk(v)
                    if r:
                        return r
            except Exception:
                pass
        return None

    return _walk(receipt)


class GenLayerLLMClient(LLMClient):
    def __init__(self, *, account_private_key: str | None = None) -> None:
        if not settings.genlayer_contract_address:
            raise GenLayerClientError("GENLAYER_CONTRACT_ADDRESS is not configured.", code="genlayer_address_missing")
        create_account, create_client, studionet, TransactionStatus = _import_sdk()
        self._TransactionStatus = TransactionStatus

        pk = (account_private_key or settings.genlayer_account_private_key or "").strip()
        if pk:
            try:
                self._account = create_account(account_private_key=pk)
            except TypeError:
                self._account = create_account(private_key=pk)
        else:
            # Ephemeral account: only safe for reads. Writes will be forbidden.
            self._account = create_account()
        self._client = create_client(chain=studionet, account=self._account)
        self._address = settings.genlayer_contract_address
        log.info(
            "genlayer_client_ready",
            address=self._address,
            account=str(getattr(self._account, "address", "")),
            using_user_wallet=bool(account_private_key),
        )

    # ------------------------------------------------------------------------
    def _read_raw(self, fn, args):
        return self._client.read_contract(address=self._address, function_name=fn, args=args)

    def _try_read(self, fn, args):
        try:
            return True, self._read_raw(fn, args)
        except Exception as exc:
            log.warning("genlayer_soft_read_failed", fn=fn, error=str(exc))
            return False, None

    def _wait_for_finalized(self, tx_hash):
        wait = getattr(self._client, "wait_for_transaction_receipt", None)
        if wait is None:
            return None
        ts = self._TransactionStatus
        finalized = getattr(ts, "FINALIZED", None) if ts else None
        attempts = []
        if finalized is not None:
            attempts.append({"transaction_hash": tx_hash, "status": finalized, "retries": 240, "interval": 5000})
        attempts.append({"transaction_hash": tx_hash, "retries": 240, "interval": 5000})
        attempts.append({"transaction_hash": tx_hash})
        for kw in attempts:
            try:
                return wait(**kw)
            except TypeError:
                continue
            except Exception as exc:
                log.warning("genlayer_finalize_wait_failed", error=str(exc))
                return None
        try:
            return wait(tx_hash)
        except Exception as exc:
            log.warning("genlayer_finalize_wait_failed_all", error=str(exc))
            return None

    def _write_and_finalize(self, fn, args):
        try:
            tx_hash = self._client.write_contract(address=self._address, function_name=fn, args=args)
        except Exception as exc:
            raise GenLayerClientError(f"GenLayer write_contract({fn}) failed: {exc}", code="genlayer_write_failed") from exc
        receipt = self._wait_for_finalized(tx_hash)
        return str(tx_hash), receipt

    def ping(self) -> dict:
        out = {"address": self._address, "version": None, "evaluation_count": None}
        ok, v = self._try_read("contract_version", [])
        if not ok:
            raise GenLayerClientError("Contract is unreachable.", code="genlayer_contract_unreachable")
        out["version"] = v
        ok2, c = self._try_read("evaluation_count", [])
        out["evaluation_count"] = c if ok2 else "unavailable"
        return out

    def evaluate(self, *, cv_text, cover_letter_text, job_text, job_title, job_url, linkedin_url, portfolio_url) -> LLMEvaluation:
        cv = _truncate(cv_text, _CV_MAX)
        cl = _truncate(cover_letter_text, _CL_MAX)
        job = _truncate(job_text, _JOB_MAX)
        title = job_title or ""
        url = job_url or ""
        h = _normalised_content_hash(cv=cv, cl=cl, job=job, title=title, job_url=url, linkedin_url=linkedin_url or "", portfolio_url=portfolio_url or "")

        ok, existing = self._try_read("get_evaluation", [h])
        if ok and existing:
            return self._build_evaluation(existing, contract_tx_hash=None, content_hash=h, receipt=None)

        log.info("genlayer_evaluate_dispatch", content_hash=h[:12])
        tx_hash, receipt = self._write_and_finalize("evaluate_application", [h, cv, cl, job, title, url, linkedin_url or "", portfolio_url or ""])
        receipt_dict = _serialise_receipt(receipt)
        log.info("genlayer_evaluate_landed", content_hash=h[:12], tx_hash=tx_hash, receipt=receipt_dict)

        deadline = time.time() + _READ_POLL_S
        stored, polls = None, 0
        while time.time() < deadline:
            polls += 1
            last_ok, candidate = self._try_read("get_evaluation", [h])
            if last_ok and candidate:
                stored = candidate
                break
            time.sleep(_READ_INTERVAL_S)
        log.info("genlayer_read_poll_done", content_hash=h[:12], polls=polls, found=stored is not None)

        if not stored:
            # Fallback: extract the evaluation JSON directly from the
            # receipt. The leader validator returned the JSON as part of
            # the transaction, so even if the on-chain storage poll comes
            # back empty (read replica lag, indexing issue, or contract
            # storage quirk), the data is still in the receipt we already
            # have.
            from_receipt = _extract_eval_json_from_receipt(receipt)
            if from_receipt:
                log.warning(
                    "genlayer_used_receipt_fallback",
                    content_hash=h[:12],
                    tx_hash=tx_hash,
                    polls=polls,
                )
                return self._build_evaluation(
                    from_receipt,
                    contract_tx_hash=tx_hash,
                    content_hash=h,
                    receipt=receipt_dict,
                )
            raise GenLayerClientError(
                f"Contract accepted the write but get_evaluation returned empty after {polls} polls "
                f"and the receipt did not contain a parsable evaluation. "
                f"Tx {tx_hash}. Receipt: {json.dumps(receipt_dict)[:1500]}",
                code="genlayer_storage_not_persistent",
            )
        return self._build_evaluation(stored, contract_tx_hash=tx_hash, content_hash=h, receipt=receipt_dict)

    def _build_evaluation(self, raw_json, *, contract_tx_hash, content_hash, receipt) -> LLMEvaluation:
        parsed = raw_json if isinstance(raw_json, dict) else (json.loads(raw_json) if raw_json else {})
        if not isinstance(parsed, dict):
            parsed = {}
        rationale_obj = parsed.get("rationale") if isinstance(parsed.get("rationale"), dict) else {}

        def _score(name, key):
            return LLMScore(
                value=int(parsed.get(key, 0) or 0),
                label=name,
                rationale=str(rationale_obj.get(key, "")),
                signals={},
            )

        cv = _score("cv", "cv_score")
        cl = _score("cover_letter", "cover_letter_score")
        jm = _score("job_match", "job_match_score")
        ats = _score("ats", "ats_score")
        comp = _score("competitiveness", "competitiveness_score")
        overall = _score("overall", "overall_score")

        return LLMEvaluation(
            cv=cv, cover_letter=cl, job_match=jm, ats=ats, competitiveness=comp, overall=overall,
            summary=str(parsed.get("summary", "")),
            improved_positioning=str(parsed.get("improved_positioning", "")),
            missing_keywords=list(parsed.get("missing_keywords") or []),
            missing_skills=list(parsed.get("missing_skills") or []),
            recommendations=list(parsed.get("recommendations") or []),
            weak_statements=list(parsed.get("weak_statements") or []),
            company_alignment_notes=list(parsed.get("company_alignment_notes") or []),
            strengths=list(parsed.get("strengths") or []),
            risks=list(parsed.get("risks") or []),
            rationale=dict(rationale_obj),
            raw={
                "backend": "genlayer",
                "version": "0.3.1",
                "contract_address": self._address,
                "contract_tx_hash": contract_tx_hash,
                "content_hash": content_hash,
                "receipt": receipt or {},
                "scores": {
                    "cv": cv.value, "cover_letter": cl.value, "job_match": jm.value,
                    "ats": ats.value, "competitiveness": comp.value, "overall": overall.value,
                },
                "raw_contract_payload": parsed,
            },
        )
