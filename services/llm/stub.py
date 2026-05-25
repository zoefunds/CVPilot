"""
Deterministic LLM stand-in. Returns the same shape as the v0.3.1 contract.
Used in tests and (optionally) dev. Production sets LLM_BACKEND=genlayer.
"""

from __future__ import annotations

import re
from collections import Counter

from services.llm.base import LLMClient, LLMEvaluation, LLMScore

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9+#.\-]{1,}")
_STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "have", "has",
    "are", "you", "your", "our", "will", "into", "to", "of", "in", "on",
    "at", "by", "as", "an", "a", "is", "be", "we", "or", "it", "i", "ll",
    "re", "ve", "s", "t", "d",
}
_ACHIEVEMENT_CUES = re.compile(
    r"\b(led|owned|shipped|launched|increased|reduced|scaled|saved|"
    r"grew|delivered|drove|migrated|architected|built|designed)\b",
    re.IGNORECASE,
)
_METRIC_CUE = re.compile(
    r"\b\d+(?:\.\d+)?\s?(%|x|k|m|million|billion|users|customers|requests|qps|ms|seconds?|hours?|days?|weeks?|months?|years?)\b",
    re.IGNORECASE,
)
_ATS_BAD_CUES = re.compile(r"[\u2022\u25CF\u25E6\u25A0]+|<img|<table", re.IGNORECASE)


def _tokens(text):
    return [t.lower() for t in _TOKEN_RE.findall(text or "") if t.lower() not in _STOPWORDS]


def _keyword_overlap(target, candidate):
    t = Counter(_tokens(target))
    c = Counter(_tokens(candidate))
    if not t:
        return 0.0, [], []
    matched = [w for w in t if w in c and len(w) > 2]
    missing = [w for w, n in t.most_common(60) if w not in c and len(w) > 3][:15]
    coverage = len(matched) / max(1, len({w for w in t if len(w) > 2}))
    top_kw_hits = sorted(matched, key=lambda w: t[w], reverse=True)[:10]
    return min(1.0, coverage), top_kw_hits, missing


def _clamp(v, lo=0, hi=100):
    return int(max(lo, min(hi, round(v))))


def _score_cv(cv, job):
    coverage, hits, missing = _keyword_overlap(job, cv)
    n_a = len(_ACHIEVEMENT_CUES.findall(cv))
    n_m = len(_METRIC_CUE.findall(cv))
    length_factor = min(1.0, len(cv) / 1800)
    score = 35 + 35 * coverage + 12 * min(1.0, n_a / 6) + 18 * length_factor
    if n_m:
        score += min(8, n_m * 2)
    return LLMScore(
        value=_clamp(score),
        label="cv",
        rationale=f"Matched {len(hits)} keywords, {n_a} verbs, {n_m} metrics.",
        signals={"keyword_hits": hits, "achievement_verbs": n_a, "metrics_found": n_m},
    ), missing, hits


def _score_cover_letter(cl, job, job_title):
    coverage, hits, _ = _keyword_overlap(job, cl)
    mentions_title = bool(job_title and job_title.lower() in cl.lower())
    addressed = bool(re.search(r"^(dear|hi|hello)\b", cl.strip(), re.IGNORECASE))
    p = 0
    if mentions_title: p += 12
    if addressed: p += 6
    length_factor = min(1.0, len(cl) / 900)
    score = 30 + 35 * coverage + p + 18 * length_factor
    return LLMScore(
        value=_clamp(score),
        label="cover_letter",
        rationale="Personalisation, addressee, length, keyword alignment.",
        signals={"mentions_title": mentions_title, "addressed": addressed},
    )


def _score_job_match(cv, cl, job):
    cv_cov, _, _ = _keyword_overlap(job, cv)
    cl_cov, _, _ = _keyword_overlap(job, cl)
    return LLMScore(
        value=_clamp(25 + 70 * (0.65 * cv_cov + 0.35 * cl_cov)),
        label="job_match",
        rationale="Weighted CV/CL keyword alignment.",
        signals={},
    )


def _score_ats(cv):
    bad = len(_ATS_BAD_CUES.findall(cv))
    too_short = len(cv) < 800
    has_email = bool(re.search(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+", cv))
    has_phone = bool(re.search(r"\+?\d[\d \-().]{7,}\d", cv))
    score = 90
    if bad: score -= 10
    if too_short: score -= 15
    if not has_email: score -= 8
    if not has_phone: score -= 5
    return LLMScore(value=_clamp(score), label="ats", rationale="ATS heuristic.", signals={})


def _weak(cv):
    out = []
    for line in cv.splitlines():
        s = line.strip()
        if not s: continue
        if len(s) > 40 and not _ACHIEVEMENT_CUES.search(s) and not _METRIC_CUE.search(s):
            if any(kw in s.lower() for kw in ("responsible for", "duties included", "worked on", "helped with")):
                out.append(s)
    return out[:5]


def _detect_strengths(cv):
    out = []
    if _ACHIEVEMENT_CUES.search(cv): out.append("Uses action verbs for accomplishments.")
    if _METRIC_CUE.search(cv): out.append("Quantifies outcomes with metrics.")
    if "@" in cv: out.append("Contact details are visible to recruiters.")
    return out


def _detect_risks(cv, job):
    out = []
    if len(cv) < 800: out.append("CV body is short and may read as unsupported.")
    if not _METRIC_CUE.search(cv): out.append("No measurable outcomes detected.")
    if not _ACHIEVEMENT_CUES.search(cv): out.append("Few or no strong action verbs.")
    if "team" in (job or "").lower() and "team" not in cv.lower():
        out.append("Job emphasises team collaboration; CV does not.")
    return out


class StubLLMClient(LLMClient):
    def evaluate(
        self, *, cv_text, cover_letter_text, job_text, job_title, job_url, linkedin_url, portfolio_url,
    ) -> LLMEvaluation:
        cv_score, missing_keywords, _hits = _score_cv(cv_text, job_text)
        cl_score = _score_cover_letter(cover_letter_text, job_text, job_title)
        match_score = _score_job_match(cv_text, cover_letter_text, job_text)
        ats_score = _score_ats(cv_text)
        comp = round(0.30 * cv_score.value + 0.20 * cl_score.value + 0.30 * match_score.value + 0.20 * ats_score.value)
        competitiveness = LLMScore(value=_clamp(comp), label="competitiveness", rationale="Weighted blend.", signals={})
        overall_value = round(0.40 * comp + 0.30 * match_score.value + 0.15 * cv_score.value + 0.15 * cl_score.value)
        overall = LLMScore(value=_clamp(overall_value), label="overall", rationale="Holistic blend.", signals={})

        recs = []
        if missing_keywords:
            recs.append(f"Surface these missing job keywords in your CV: {', '.join(missing_keywords[:8])}.")

        improved = ""
        if job_title and missing_keywords:
            improved = (
                f"Reposition yourself as a {job_title} candidate by leading with "
                f"the matching skills ({', '.join(missing_keywords[:3])}) "
                "and a concrete metric in your first bullet."
            )

        rationale = {
            "cv_score": cv_score.rationale,
            "cover_letter_score": cl_score.rationale,
            "job_match_score": match_score.rationale,
            "ats_score": ats_score.rationale,
            "competitiveness_score": competitiveness.rationale,
            "overall_score": overall.rationale,
        }

        return LLMEvaluation(
            cv=cv_score,
            cover_letter=cl_score,
            job_match=match_score,
            ats=ats_score,
            competitiveness=competitiveness,
            overall=overall,
            summary=f"Overall {overall.value}/100. Competitiveness {competitiveness.value}/100.",
            improved_positioning=improved,
            missing_keywords=missing_keywords,
            missing_skills=missing_keywords[:8],
            recommendations=recs,
            weak_statements=_weak(cv_text),
            company_alignment_notes=[],
            strengths=_detect_strengths(cv_text),
            risks=_detect_risks(cv_text, job_text),
            rationale=rationale,
            raw={
                "backend": "stub",
                "version": 1,
                "scores": {
                    "cv": cv_score.value,
                    "cover_letter": cl_score.value,
                    "job_match": match_score.value,
                    "ats": ats_score.value,
                    "competitiveness": competitiveness.value,
                    "overall": overall.value,
                },
            },
        )
