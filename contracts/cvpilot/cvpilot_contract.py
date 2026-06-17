# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
#
# CVPilotEvaluator v1.0.0  –  Production
# Reference: https://skills.genlayer.com/
#
# GenLayer schema rules (from genvm source — runners/genlayer-py-std):
#   1. NO "from __future__ import annotations" — schema generator inspects
#      annotations eagerly at class-definition time; lazy strings break it.
#   2. Every @gl.public.view / @gl.public.write parameter MUST have a type
#      annotation that the schema generator can resolve (str, int, bool, u256,
#      Address, etc.).  Private helpers are excluded from schema generation.
#   3. Storage fields must use only: TreeMap[K,V], DynArray[T], Array[T,N],
#      u8..u256, i8..i256, str, bool, Address, bigint, Lazy, Keccak256.
#   4. Bare gl.nondet.exec_prompt() inside a @gl.public.write body is
#      forbidden (SystemError 6).  Wrap every LLM call in a nested def and
#      pass it to gl.eq_principle.prompt_comparative / prompt_non_comparative.

import json
import re

from genlayer import *

_CONTRACT_VERSION = "1.0.3"

# ── Scoring weights (must sum to 100) ────────────────────────────────────────
_W_CV       = 30
_W_COVER    = 20
_W_MATCH    = 25
_W_ATS      = 15
_W_COMPETE  = 10

# ── Verdict thresholds ───────────────────────────────────────────────────────
_STRONG = 62
_MIXED  = 35

# ── Score equivalence tolerance ──────────────────────────────────────────────
_TOL = 40

# ── Candidate history cap ────────────────────────────────────────────────────
_MAX_HIST = 50


# ────────────────────────────────────────────────────────────────────────────
# Module-level pure helpers  (not part of contract storage or schema)
# ────────────────────────────────────────────────────────────────────────────

def _clean(raw):
    s = str(raw).replace("```json", "").replace("```", "").strip()
    a = s.find("{")
    b = s.rfind("}")
    if a != -1 and b != -1:
        s = s[a : b + 1]
    s = re.sub(r",\s*([}\]])", r"\1", s)
    return s


def _parse(raw, fallback):
    try:
        return json.loads(_clean(raw))
    except Exception:
        return fallback


def _verdict(score):
    if score >= _STRONG:
        return "strong"
    if score >= _MIXED:
        return "mixed"
    return "weak"


# ── JSON schemas embedded as strings ─────────────────────────────────────────

_EVAL_SCHEMA = """{
  "cv_score": 0, "cover_letter_score": 0, "job_match_score": 0,
  "ats_score": 0, "competitiveness_score": 0, "overall_score": 0,
  "summary": "", "missing_keywords": [], "missing_skills": [],
  "recommendations": [], "weak_statements": [],
  "company_alignment_notes": [], "strengths": [], "risks": [],
  "improved_positioning": "",
  "rationale": {
    "cv_score": "", "cover_letter_score": "", "job_match_score": "",
    "ats_score": "", "competitiveness_score": "", "overall_score": ""
  }
}"""

_EVAL_CRITERIA = (
    "Two CVPilot evaluations are equivalent if: "
    "(1) both are valid JSON with the same top-level keys; "
    "(2) corresponding scores differ by no more than " + str(_TOL) + " points; "
    "(3) the overall verdict may differ by one or even two tiers if the score pattern is still directionally similar; "
    "(4) recommendations and strengths express generally similar career advice."
)

_SKILLS_SCHEMA = """{
  "candidate_skills": [], "required_skills": [], "gap_skills": [],
  "bonus_skills": [], "skill_match_score": 0,
  "skill_categories": {
    "technical": [], "soft": [], "domain": [], "certifications": []
  },
  "upskilling_roadmap": [], "estimated_ramp_weeks": 0, "summary": ""
}"""

_INTERVIEW_SCHEMA = """{
  "behavioral_questions": [], "technical_questions": [],
  "situational_questions": [], "culture_fit_questions": [],
  "questions_to_ask_interviewer": [], "talking_points": [],
  "red_flags_to_address": [], "preparation_tips": []
}"""

_SALARY_SCHEMA = """{
  "currency": "USD",
  "range_low": 0, "range_mid": 0, "range_high": 0,
  "confidence": "low", "rationale": "",
  "negotiation_tips": [], "market_signals": []
}"""

_PORTFOLIO_SCHEMA = """{
  "portfolio_score": 0, "project_highlights": [],
  "missing_project_types": [],
  "technology_diversity_score": 0, "presentation_quality_score": 0,
  "strengths": [], "weaknesses": [], "recommendations": [], "summary": ""
}"""

_CAREER_SCHEMA = """{
  "trajectory_score": 0, "progression_type": "",
  "years_of_experience": 0, "seniority_level": "",
  "career_highlights": [], "career_gaps": [],
  "promotion_velocity": "", "industry_breadth": [],
  "specialist_areas": [], "growth_potential": "",
  "risks": [], "summary": ""
}"""

_COVER_LETTER_SCHEMA = """{
  "score": 0, "tone_match": "", "personalization_score": 0,
  "storytelling_score": 0, "call_to_action_strength": "",
  "keyword_density_score": 0, "length_appropriateness": "",
  "strengths": [], "weaknesses": [],
  "suggested_rewrites": [], "summary": ""
}"""

_JOB_INTEL_SCHEMA = """{
  "company_stage": "", "team_culture_signals": [],
  "tech_stack_signals": [], "growth_indicators": [],
  "red_flags": [], "role_complexity": "",
  "required_seniority": "", "remote_friendliness": "",
  "diversity_signals": [], "salary_signals": [], "summary": ""
}"""

_ATS_SCHEMA = """{
  "high_priority_keywords": [],
  "medium_priority_keywords": [],
  "low_priority_keywords": [],
  "suggested_cv_sections": {
    "summary": [], "experience": [], "skills": [], "education": []
  },
  "ats_score_before": 0,
  "estimated_ats_score_after": 0,
  "notes": ""
}"""

_STRATEGY_SCHEMA = """{
  "stage": "",
  "immediate_actions": [],
  "this_week_actions": [],
  "networking_moves": [],
  "research_targets": [],
  "mindset_tips": [],
  "common_mistakes_to_avoid": [],
  "success_metrics": [],
  "timeline_days": 0,
  "summary": ""
}"""


# ════════════════════════════════════════════════════════════════════════════
#  Contract
# ════════════════════════════════════════════════════════════════════════════

class CVPilotEvaluator(gl.Contract):

    # ── Core caches (content_hash → JSON string) ─────────────────────────
    evaluations:           TreeMap[str, str]
    skills_analyses:       TreeMap[str, str]
    interview_preps:       TreeMap[str, str]
    salary_estimates:      TreeMap[str, str]
    portfolio_assessments: TreeMap[str, str]
    career_analyses:       TreeMap[str, str]
    cover_letter_analyses: TreeMap[str, str]
    job_intel_cache:       TreeMap[str, str]

    # ── Candidate / job indexes (url → comma-joined hash list) ───────────
    candidate_history: TreeMap[str, str]
    job_history:       TreeMap[str, str]

    # ── Counters ─────────────────────────────────────────────────────────
    total_evaluated:             u256
    total_skills_analyses:       u256
    total_interview_preps:       u256
    total_salary_estimates:      u256
    total_portfolio_assessments: u256
    total_career_analyses:       u256
    total_cover_letter_analyses: u256
    total_job_intel:             u256

    # ── Admin ─────────────────────────────────────────────────────────────
    owner:          str
    paused:         bool
    paused_reason:  str
    web_fetch_on:   bool

    # ─────────────────────────────────────────────────────────────────────
    def __init__(self) -> None:
        self.total_evaluated             = u256(0)
        self.total_skills_analyses       = u256(0)
        self.total_interview_preps       = u256(0)
        self.total_salary_estimates      = u256(0)
        self.total_portfolio_assessments = u256(0)
        self.total_career_analyses       = u256(0)
        self.total_cover_letter_analyses = u256(0)
        self.total_job_intel             = u256(0)
        self.owner         = gl.message.sender_address.as_hex
        self.paused        = False
        self.paused_reason = ""
        self.web_fetch_on  = True

    # ── Private guards ────────────────────────────────────────────────────

    def _check_live(self):
        if self.paused:
            raise Exception("Contract paused: " + self.paused_reason)

    def _check_owner(self):
        if gl.message.sender_address.as_hex != self.owner:
            raise Exception("Owner only.")

    def _index_push(self, store: TreeMap, key: str, val: str):
        existing = store.get(key, "")
        if existing:
            parts = existing.split(",")
            if val not in parts:
                parts.append(val)
                if len(parts) > _MAX_HIST:
                    parts = parts[-_MAX_HIST:]
                store[key] = ",".join(parts)
        else:
            store[key] = val

    # ════════════════════════════════════════════════════════════════════
    #  Admin
    # ════════════════════════════════════════════════════════════════════

    @gl.public.write
    def pause(self, reason: str) -> None:
        self._check_owner()
        self.paused = True
        self.paused_reason = reason

    @gl.public.write
    def unpause(self) -> None:
        self._check_owner()
        self.paused = False
        self.paused_reason = ""

    @gl.public.write
    def transfer_ownership(self, new_owner: str) -> None:
        self._check_owner()
        self.owner = new_owner

    @gl.public.write
    def set_web_fetch(self, enabled: bool) -> None:
        self._check_owner()
        self.web_fetch_on = enabled

    # ════════════════════════════════════════════════════════════════════
    #  Views — admin / meta
    # ════════════════════════════════════════════════════════════════════

    @gl.public.view
    def contract_version(self) -> str:
        return _CONTRACT_VERSION

    @gl.public.view
    def get_owner(self) -> str:
        return self.owner

    @gl.public.view
    def is_paused(self) -> bool:
        return self.paused

    @gl.public.view
    def get_paused_reason(self) -> str:
        return self.paused_reason

    # ════════════════════════════════════════════════════════════════════
    #  Views — counters
    # ════════════════════════════════════════════════════════════════════

    @gl.public.view
    def evaluation_count(self) -> u256:
        return self.total_evaluated

    @gl.public.view
    def skills_count(self) -> u256:
        return self.total_skills_analyses

    @gl.public.view
    def interview_count(self) -> u256:
        return self.total_interview_preps

    @gl.public.view
    def salary_count(self) -> u256:
        return self.total_salary_estimates

    @gl.public.view
    def portfolio_count(self) -> u256:
        return self.total_portfolio_assessments

    @gl.public.view
    def career_count(self) -> u256:
        return self.total_career_analyses

    @gl.public.view
    def cover_letter_count(self) -> u256:
        return self.total_cover_letter_analyses

    @gl.public.view
    def job_intel_count(self) -> u256:
        return self.total_job_intel

    @gl.public.view
    def get_all_counts(self) -> str:
        return json.dumps({
            "evaluations":           int(self.total_evaluated),
            "skills_analyses":       int(self.total_skills_analyses),
            "interview_preps":       int(self.total_interview_preps),
            "salary_estimates":      int(self.total_salary_estimates),
            "portfolio_assessments": int(self.total_portfolio_assessments),
            "career_analyses":       int(self.total_career_analyses),
            "cover_letter_analyses": int(self.total_cover_letter_analyses),
            "job_intel":             int(self.total_job_intel),
        })

    # ════════════════════════════════════════════════════════════════════
    #  Views — cache lookups
    # ════════════════════════════════════════════════════════════════════

    @gl.public.view
    def has_evaluation(self, content_hash: str) -> bool:
        return self.evaluations.get(content_hash, None) is not None

    @gl.public.view
    def get_evaluation(self, content_hash: str) -> str:
        return self.evaluations.get(content_hash, "")

    @gl.public.view
    def has_skills_analysis(self, content_hash: str) -> bool:
        return self.skills_analyses.get(content_hash, None) is not None

    @gl.public.view
    def get_skills_analysis(self, content_hash: str) -> str:
        return self.skills_analyses.get(content_hash, "")

    @gl.public.view
    def has_interview_prep(self, content_hash: str) -> bool:
        return self.interview_preps.get(content_hash, None) is not None

    @gl.public.view
    def get_interview_prep(self, content_hash: str) -> str:
        return self.interview_preps.get(content_hash, "")

    @gl.public.view
    def has_salary_estimate(self, content_hash: str) -> bool:
        return self.salary_estimates.get(content_hash, None) is not None

    @gl.public.view
    def get_salary_estimate(self, content_hash: str) -> str:
        return self.salary_estimates.get(content_hash, "")

    @gl.public.view
    def has_portfolio_assessment(self, content_hash: str) -> bool:
        return self.portfolio_assessments.get(content_hash, None) is not None

    @gl.public.view
    def get_portfolio_assessment(self, content_hash: str) -> str:
        return self.portfolio_assessments.get(content_hash, "")

    @gl.public.view
    def has_career_analysis(self, content_hash: str) -> bool:
        return self.career_analyses.get(content_hash, None) is not None

    @gl.public.view
    def get_career_analysis(self, content_hash: str) -> str:
        return self.career_analyses.get(content_hash, "")

    @gl.public.view
    def has_cover_letter_analysis(self, content_hash: str) -> bool:
        return self.cover_letter_analyses.get(content_hash, None) is not None

    @gl.public.view
    def get_cover_letter_analysis(self, content_hash: str) -> str:
        return self.cover_letter_analyses.get(content_hash, "")

    @gl.public.view
    def has_job_intel(self, job_hash: str) -> bool:
        return self.job_intel_cache.get(job_hash, None) is not None

    @gl.public.view
    def get_job_intel(self, job_hash: str) -> str:
        return self.job_intel_cache.get(job_hash, "")

    @gl.public.view
    def get_candidate_history(self, linkedin_url: str) -> str:
        return self.candidate_history.get(linkedin_url, "")

    @gl.public.view
    def get_job_history(self, job_url: str) -> str:
        return self.job_history.get(job_url, "")

    @gl.public.view
    def get_full_profile(self, content_hash: str) -> str:
        return json.dumps({
            "evaluation":           _parse(self.evaluations.get(content_hash, "{}"), {}),
            "skills_analysis":      _parse(self.skills_analyses.get(content_hash, "{}"), {}),
            "interview_prep":       _parse(self.interview_preps.get(content_hash, "{}"), {}),
            "salary_estimate":      _parse(self.salary_estimates.get(content_hash, "{}"), {}),
            "portfolio_assessment": _parse(self.portfolio_assessments.get(content_hash, "{}"), {}),
            "career_analysis":      _parse(self.career_analyses.get(content_hash, "{}"), {}),
            "cover_letter_analysis":_parse(self.cover_letter_analyses.get(content_hash, "{}"), {}),
        })

    # ════════════════════════════════════════════════════════════════════
    #  1. Full Application Evaluation
    # ════════════════════════════════════════════════════════════════════

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
        self._check_live()

        cached = self.evaluations.get(content_hash, None)
        if cached is not None:
            return cached

        prompt = (
            "You are CVPilot — an expert ATS evaluator, recruiter, and career coach.\n"
            "Evaluate the candidate's application for the role below.\n\n"
            "Return ONLY valid JSON (no markdown, no commentary) matching this schema:\n"
            + _EVAL_SCHEMA + "\n\n"
            "Rules:\n"
            "- All scores: integers 0–100.\n"
            "- Scoring weights: cv=" + str(_W_CV) + "% cover=" + str(_W_COVER) +
            "% match=" + str(_W_MATCH) + "% ats=" + str(_W_ATS) +
            "% compete=" + str(_W_COMPETE) + "%.\n"
            "- overall_score = weighted average of the five scores.\n"
            "- recommendations: specific, actionable bullet points.\n"
            "- improved_positioning: short paragraph rebranding the candidate.\n"
            "- rationale: brief explanation for each score.\n"
            "- All array fields must be arrays of strings.\n\n"
            "JOB TITLE: " + job_title + "\n"
            "JOB URL: " + job_url + "\n"
            "LINKEDIN: " + linkedin_url + "\n"
            "PORTFOLIO: " + portfolio_url + "\n\n"
            "JOB DESCRIPTION:\n" + job_text + "\n\n"
            "CV:\n" + cv_text + "\n\n"
            "COVER LETTER:\n" + cover_letter
        )

        _fb_rationale = {k: "parse error" for k in [
            "cv_score", "cover_letter_score", "job_match_score",
            "ats_score", "competitiveness_score", "overall_score",
        ]}
        _fb = {
            "cv_score": 0, "cover_letter_score": 0, "job_match_score": 0,
            "ats_score": 0, "competitiveness_score": 0, "overall_score": 0,
            "summary": "", "missing_keywords": [], "missing_skills": [],
            "recommendations": [], "weak_statements": [],
            "company_alignment_notes": [], "strengths": [], "risks": [],
            "improved_positioning": "", "rationale": _fb_rationale,
        }

        def _run():
            raw = gl.nondet.exec_prompt(prompt)
            return json.dumps(_parse(str(raw), _fb), sort_keys=True)

        result = gl.eq_principle.prompt_non_comparative(
            task=_run,
            criteria="Return a valid JSON string matching the schema. Minor wording differences are acceptable.",
        )

        self.evaluations[content_hash] = result
        self.total_evaluated = self.total_evaluated + u256(1)
        if linkedin_url:
            self._index_push(self.candidate_history, linkedin_url, content_hash)
        if job_url:
            self._index_push(self.job_history, job_url, content_hash)
        return result

    # ════════════════════════════════════════════════════════════════════
    #  2. Skills Gap Analysis
    # ════════════════════════════════════════════════════════════════════

    @gl.public.write
    def analyse_skills_gap(
        self,
        content_hash: str,
        cv_text: str,
        job_text: str,
        job_title: str,
    ) -> str:
        self._check_live()

        cached = self.skills_analyses.get(content_hash, None)
        if cached is not None:
            return cached

        prompt = (
            "You are a senior technical recruiter and skills taxonomy expert.\n"
            "Perform a deep skills gap analysis for the candidate applying to the role below.\n\n"
            "Return ONLY valid JSON (no markdown) matching this schema:\n"
            + _SKILLS_SCHEMA + "\n\n"
            "Rules:\n"
            "- candidate_skills: every skill evidenced in the CV.\n"
            "- required_skills: every skill required/preferred in the job description.\n"
            "- gap_skills: required_skills NOT in candidate_skills.\n"
            "- bonus_skills: candidate skills exceeding requirements.\n"
            "- skill_match_score: integer 0–100.\n"
            "- skill_categories: classify ALL skills into technical/soft/domain/certifications.\n"
            "- upskilling_roadmap: ordered learning steps to close the gap.\n"
            "- estimated_ramp_weeks: realistic integer to close the gap.\n\n"
            "JOB TITLE: " + job_title + "\n\n"
            "JOB DESCRIPTION:\n" + job_text + "\n\n"
            "CV:\n" + cv_text
        )

        _fb = {
            "candidate_skills": [], "required_skills": [], "gap_skills": [],
            "bonus_skills": [], "skill_match_score": 0,
            "skill_categories": {"technical": [], "soft": [], "domain": [], "certifications": []},
            "upskilling_roadmap": [], "estimated_ramp_weeks": 0, "summary": "",
        }
        criteria = (
            "Equivalent if: (1) valid JSON; "
            "(2) gap_skills overlap on at least a few important skills; "
            "(3) skill_match_score differs by no more than 40; "
            "(4) upskilling_roadmap steps are directionally similar."
        )

        def _run():
            raw = gl.nondet.exec_prompt(prompt)
            return json.dumps(_parse(str(raw), _fb), sort_keys=True)

        result = gl.eq_principle.prompt_non_comparative(
            task=_run,
            criteria="Return valid JSON. Keep the main missing skills and roadmap directionally similar.",
        )
        self.skills_analyses[content_hash] = result
        self.total_skills_analyses = self.total_skills_analyses + u256(1)
        return result

    # ════════════════════════════════════════════════════════════════════
    #  3. Interview Preparation
    # ════════════════════════════════════════════════════════════════════

    @gl.public.write
    def generate_interview_prep(
        self,
        content_hash: str,
        cv_text: str,
        job_text: str,
        job_title: str,
        company_name: str,
    ) -> str:
        self._check_live()

        cached = self.interview_preps.get(content_hash, None)
        if cached is not None:
            return cached

        prompt = (
            "You are a professional interview coach with deep expertise in hiring for "
            + job_title + " roles.\n"
            "Generate a comprehensive interview preparation guide.\n\n"
            "Return ONLY valid JSON (no markdown) matching this schema:\n"
            + _INTERVIEW_SCHEMA + "\n\n"
            "Rules:\n"
            "- behavioral_questions: 8 STAR-format questions tailored to the candidate.\n"
            "- technical_questions: 8 role-specific technical questions.\n"
            "- situational_questions: 5 hypothetical scenario questions.\n"
            "- culture_fit_questions: 5 values/culture alignment questions.\n"
            "- questions_to_ask_interviewer: 6 smart questions to ask.\n"
            "- talking_points: 6 key narrative bullets.\n"
            "- red_flags_to_address: gaps the candidate should proactively address.\n"
            "- preparation_tips: 6 practical tips for this role and company.\n\n"
            "COMPANY: " + company_name + "\n"
            "JOB TITLE: " + job_title + "\n\n"
            "JOB DESCRIPTION:\n" + job_text + "\n\n"
            "CV:\n" + cv_text
        )

        _fb = {
            "behavioral_questions": [], "technical_questions": [],
            "situational_questions": [], "culture_fit_questions": [],
            "questions_to_ask_interviewer": [], "talking_points": [],
            "red_flags_to_address": [], "preparation_tips": [],
        }
        criteria = (
            "Equivalent if: (1) valid JSON; "
            "(2) behavioral_questions are role-relevant; "
            "(3) technical_questions address overlapping core competency areas; "
            "(4) talking_points capture similar narrative angles."
        )

        def _run():
            raw = gl.nondet.exec_prompt(prompt)
            return json.dumps(_parse(str(raw), _fb), sort_keys=True)

        result = gl.eq_principle.prompt_non_comparative(
            task=_run,
            criteria="Return valid JSON. Keep the important question themes and talking points relevant.",
        )
        self.interview_preps[content_hash] = result
        self.total_interview_preps = self.total_interview_preps + u256(1)
        return result

    # ════════════════════════════════════════════════════════════════════
    #  4. Salary Estimation
    # ════════════════════════════════════════════════════════════════════

    @gl.public.write
    def estimate_salary(
        self,
        content_hash: str,
        cv_text: str,
        job_text: str,
        job_title: str,
        location: str,
    ) -> str:
        self._check_live()

        cached = self.salary_estimates.get(content_hash, None)
        if cached is not None:
            return cached

        prompt = (
            "You are a compensation specialist with up-to-date salary benchmarks.\n"
            "Estimate a realistic salary range for this candidate.\n\n"
            "Return ONLY valid JSON (no markdown) matching this schema:\n"
            + _SALARY_SCHEMA + "\n\n"
            "Rules:\n"
            "- currency: ISO 4217 code matching the location.\n"
            "- range_low / range_mid / range_high: realistic integers.\n"
            "- confidence: one of 'low', 'medium', 'high'.\n"
            "- negotiation_tips: 5 actionable tips.\n"
            "- market_signals: key signals from the job description.\n\n"
            "LOCATION: " + location + "\n"
            "JOB TITLE: " + job_title + "\n\n"
            "JOB DESCRIPTION:\n" + job_text + "\n\n"
            "CV:\n" + cv_text
        )

        _fb = {
            "currency": "USD", "range_low": 0, "range_mid": 0, "range_high": 0,
            "confidence": "low", "rationale": "",
            "negotiation_tips": [], "market_signals": [],
        }
        criteria = (
            "Equivalent if: (1) valid JSON; "
            "(2) range_mid values differ by no more than 45%; "
            "(3) confidence and currency are the same; "
            "(4) negotiation_tips address similar leverage points."
        )

        def _run():
            raw = gl.nondet.exec_prompt(prompt)
            return json.dumps(_parse(str(raw), _fb), sort_keys=True)

        result = gl.eq_principle.prompt_non_comparative(
            task=_run,
            criteria="Return valid JSON. Keep the salary estimate and leverage points broadly sensible.",
        )
        self.salary_estimates[content_hash] = result
        self.total_salary_estimates = self.total_salary_estimates + u256(1)
        return result

    # ════════════════════════════════════════════════════════════════════
    #  5. Portfolio Assessment
    # ════════════════════════════════════════════════════════════════════

    @gl.public.write
    def assess_portfolio(
        self,
        content_hash: str,
        portfolio_url: str,
        cv_text: str,
        job_title: str,
    ) -> str:
        self._check_live()

        cached = self.portfolio_assessments.get(content_hash, None)
        if cached is not None:
            return cached

        portfolio_content = ""
        if self.web_fetch_on and portfolio_url:
            _url = portfolio_url

            def _fetch():
                try:
                    return gl.get_webpage(_url, mode="text")
                except Exception as exc:
                    return "[fetch error: " + str(exc) + "]"

            portfolio_content = gl.eq_principle.prompt_non_comparative(
                task=_fetch,
                criteria="Return the fetched page text as-is, or a readable error string if fetching fails.",
            )

        prompt = (
            "You are a senior hiring manager evaluating a portfolio for a "
            + job_title + " role.\n"
            "Assess the quality, relevance, and professionalism of the portfolio.\n\n"
            "Return ONLY valid JSON (no markdown) matching this schema:\n"
            + _PORTFOLIO_SCHEMA + "\n\n"
            "Rules:\n"
            "- portfolio_score: 0–100 overall quality.\n"
            "- project_highlights: top 5 projects worth mentioning in an interview.\n"
            "- missing_project_types: types of work missing for this role.\n"
            "- technology_diversity_score and presentation_quality_score: 0–100.\n"
            "- recommendations: 5 actionable improvements.\n\n"
            "PORTFOLIO URL: " + portfolio_url + "\n"
            "JOB TITLE: " + job_title + "\n\n"
            "PORTFOLIO CONTENT:\n"
            + (portfolio_content or "(not fetched — infer from CV)") + "\n\n"
            "CV:\n" + cv_text
        )

        _fb = {
            "portfolio_score": 0, "project_highlights": [],
            "missing_project_types": [], "technology_diversity_score": 0,
            "presentation_quality_score": 0, "strengths": [], "weaknesses": [],
            "recommendations": [], "summary": "",
        }
        criteria = (
            "Equivalent if: (1) valid JSON; "
            "(2) portfolio_score within 40 pts; "
            "(3) technology_diversity_score and presentation_quality_score within 40 pts; "
            "(4) project_highlights reference similar work."
        )

        def _run():
            raw = gl.nondet.exec_prompt(prompt)
            return json.dumps(_parse(str(raw), _fb), sort_keys=True)

        result = gl.eq_principle.prompt_non_comparative(
            task=_run,
            criteria="Return valid JSON. Keep the portfolio assessment generally aligned with the evidence.",
        )
        self.portfolio_assessments[content_hash] = result
        self.total_portfolio_assessments = self.total_portfolio_assessments + u256(1)
        return result

    # ════════════════════════════════════════════════════════════════════
    #  6. Career Trajectory Analysis
    # ════════════════════════════════════════════════════════════════════

    @gl.public.write
    def analyse_career_trajectory(
        self,
        content_hash: str,
        cv_text: str,
        target_role: str,
    ) -> str:
        self._check_live()

        cached = self.career_analyses.get(content_hash, None)
        if cached is not None:
            return cached

        prompt = (
            "You are an executive career coach specialising in trajectory analysis.\n"
            "Analyse this candidate's career progression for the target role.\n\n"
            "Return ONLY valid JSON (no markdown) matching this schema:\n"
            + _CAREER_SCHEMA + "\n\n"
            "Rules:\n"
            "- trajectory_score: 0–100.\n"
            "- progression_type: one of linear/lateral/upward/specialist/generalist/pivot.\n"
            "- years_of_experience: total integer years.\n"
            "- seniority_level: intern/junior/mid/senior/staff/principal/director/executive.\n"
            "- promotion_velocity: fast/average/slow relative to industry norms.\n"
            "- growth_potential: high/medium/low with one sentence justification.\n\n"
            "TARGET ROLE: " + target_role + "\n\n"
            "CV:\n" + cv_text
        )

        _fb = {
            "trajectory_score": 0, "progression_type": "linear",
            "years_of_experience": 0, "seniority_level": "mid",
            "career_highlights": [], "career_gaps": [],
            "promotion_velocity": "average", "industry_breadth": [],
            "specialist_areas": [], "growth_potential": "medium",
            "risks": [], "summary": "",
        }
        criteria = (
            "Equivalent if: (1) valid JSON; "
            "(2) trajectory_score within 40 pts; "
            "(3) seniority_level and progression_type are the same; "
            "(4) years_of_experience differ by no more than 2."
        )

        def _run():
            raw = gl.nondet.exec_prompt(prompt)
            return json.dumps(_parse(str(raw), _fb), sort_keys=True)

        result = gl.eq_principle.prompt_non_comparative(
            task=_run,
            criteria="Return valid JSON. Keep the career trajectory assessment broadly aligned.",
        )
        self.career_analyses[content_hash] = result
        self.total_career_analyses = self.total_career_analyses + u256(1)
        return result

    # ════════════════════════════════════════════════════════════════════
    #  7. Standalone Cover Letter Analysis
    # ════════════════════════════════════════════════════════════════════

    @gl.public.write
    def analyse_cover_letter(
        self,
        content_hash: str,
        cover_letter: str,
        job_text: str,
        job_title: str,
        company_name: str,
    ) -> str:
        self._check_live()

        cached = self.cover_letter_analyses.get(content_hash, None)
        if cached is not None:
            return cached

        prompt = (
            "You are a professional cover letter specialist and writing coach.\n"
            "Critically evaluate this cover letter for a " + job_title + " role at " + company_name + ".\n\n"
            "Return ONLY valid JSON (no markdown) matching this schema:\n"
            + _COVER_LETTER_SCHEMA + "\n\n"
            "Rules:\n"
            "- score: 0–100 overall quality.\n"
            "- tone_match: one of perfect/good/neutral/mismatched.\n"
            "- personalization_score: 0–100 (tailoring to company/role).\n"
            "- storytelling_score: 0–100 (narrative flow).\n"
            "- call_to_action_strength: strong/average/weak/missing.\n"
            "- keyword_density_score: 0–100 (ATS keyword coverage).\n"
            "- length_appropriateness: too_short/ideal/too_long.\n"
            "- suggested_rewrites: 3 specific sentence-level rewrites.\n\n"
            "COMPANY: " + company_name + "\n"
            "JOB TITLE: " + job_title + "\n\n"
            "JOB DESCRIPTION:\n" + job_text + "\n\n"
            "COVER LETTER:\n" + cover_letter
        )

        _fb = {
            "score": 0, "tone_match": "neutral", "personalization_score": 0,
            "storytelling_score": 0, "call_to_action_strength": "weak",
            "keyword_density_score": 0, "length_appropriateness": "ideal",
            "strengths": [], "weaknesses": [], "suggested_rewrites": [], "summary": "",
        }
        criteria = (
            "Equivalent if: (1) valid JSON; "
            "(2) score within 40 pts; "
            "(3) tone_match and call_to_action_strength are the same; "
            "(4) strengths and weaknesses express similar themes."
        )

        def _run():
            raw = gl.nondet.exec_prompt(prompt)
            return json.dumps(_parse(str(raw), _fb), sort_keys=True)

        result = gl.eq_principle.prompt_non_comparative(
            task=_run,
            criteria="Return valid JSON. Keep the cover letter themes and tone assessment broadly aligned.",
        )
        self.cover_letter_analyses[content_hash] = result
        self.total_cover_letter_analyses = self.total_cover_letter_analyses + u256(1)
        return result

    # ════════════════════════════════════════════════════════════════════
    #  8. Job Intelligence Analysis
    # ════════════════════════════════════════════════════════════════════

    @gl.public.write
    def analyse_job_posting(
        self,
        job_hash: str,
        job_text: str,
        job_title: str,
        company_name: str,
        job_url: str,
    ) -> str:
        self._check_live()

        cached = self.job_intel_cache.get(job_hash, None)
        if cached is not None:
            return cached

        web_content = ""
        if self.web_fetch_on and job_url:
            _url = job_url

            def _fetch():
                try:
                    return gl.get_webpage(_url, mode="text")
                except Exception as exc:
                    return "[fetch error: " + str(exc) + "]"

            web_content = gl.eq_principle.prompt_non_comparative(
                task=_fetch,
                criteria="Return the fetched page text as-is, or a readable error string if fetching fails.",
            )

        prompt = (
            "You are a talent intelligence analyst decoding job postings.\n\n"
            "Return ONLY valid JSON (no markdown) matching this schema:\n"
            + _JOB_INTEL_SCHEMA + "\n\n"
            "Rules:\n"
            "- company_stage: seed/series_a/series_b/series_c_plus/public/enterprise/unknown.\n"
            "- team_culture_signals: 5 culture phrases extracted from the text.\n"
            "- tech_stack_signals: all technologies explicitly or implicitly mentioned.\n"
            "- role_complexity: junior_friendly/mid_level/senior_complex/specialist.\n"
            "- remote_friendliness: fully_remote/hybrid/on_site/unspecified.\n\n"
            "COMPANY: " + company_name + "\n"
            "JOB TITLE: " + job_title + "\n"
            "JOB URL: " + job_url + "\n\n"
            "JOB DESCRIPTION:\n" + job_text + "\n\n"
            "ADDITIONAL WEB CONTENT:\n" + (web_content or "(not fetched)")
        )

        _fb = {
            "company_stage": "unknown", "team_culture_signals": [],
            "tech_stack_signals": [], "growth_indicators": [],
            "red_flags": [], "role_complexity": "mid_level",
            "required_seniority": "unspecified", "remote_friendliness": "unspecified",
            "diversity_signals": [], "salary_signals": [], "summary": "",
        }
        criteria = (
            "Equivalent if: (1) valid JSON; "
            "(2) company_stage, remote_friendliness, role_complexity are the same; "
            "(3) tech_stack_signals reference overlapping or adjacent core technologies; "
            "(4) red_flags express similar concerns."
        )

        def _run():
            raw = gl.nondet.exec_prompt(prompt)
            return json.dumps(_parse(str(raw), _fb), sort_keys=True)

        result = gl.eq_principle.prompt_non_comparative(
            task=_run,
            criteria="Return valid JSON. Keep the job intelligence broadly aligned with the description.",
        )
        self.job_intel_cache[job_hash] = result
        self.total_job_intel = self.total_job_intel + u256(1)
        return result

    # ════════════════════════════════════════════════════════════════════
    #  9. ATS Keyword Injection Suggestions
    # ════════════════════════════════════════════════════════════════════

    @gl.public.write
    def suggest_ats_keywords(
        self,
        content_hash: str,
        cv_text: str,
        job_text: str,
    ) -> str:
        self._check_live()

        store_key = "ats_" + content_hash
        cached = self.evaluations.get(store_key, None)
        if cached is not None:
            return cached

        prompt = (
            "You are an ATS optimisation expert.\n"
            "Identify the highest-impact keywords missing from the CV.\n\n"
            "Return ONLY valid JSON (no markdown) matching this schema:\n"
            + _ATS_SCHEMA + "\n\n"
            "Rules:\n"
            "- high_priority_keywords: top 10 missing keywords by job-description frequency.\n"
            "- medium/low: further keywords in descending frequency.\n"
            "- suggested_cv_sections: where each high-priority keyword should be inserted.\n"
            "- ats_score_before / estimated_ats_score_after: integers 0–100.\n\n"
            "JOB DESCRIPTION:\n" + job_text + "\n\n"
            "CV:\n" + cv_text
        )

        _fb = {
            "high_priority_keywords": [], "medium_priority_keywords": [],
            "low_priority_keywords": [],
            "suggested_cv_sections": {"summary": [], "experience": [], "skills": [], "education": []},
            "ats_score_before": 0, "estimated_ats_score_after": 0, "notes": "",
        }
        criteria = (
            "Equivalent if: (1) valid JSON; "
            "(2) high_priority_keywords share some of the same keywords; "
            "(3) ats_score_before and estimated_ats_score_after each differ by no more than 30."
        )

        def _run():
            raw = gl.nondet.exec_prompt(prompt)
            return json.dumps(_parse(str(raw), _fb), sort_keys=True)

        result = gl.eq_principle.prompt_non_comparative(
            task=_run,
            criteria="Return valid JSON. Keep the ATS keyword recommendations broadly similar.",
        )
        self.evaluations[store_key] = result
        return result

    # ════════════════════════════════════════════════════════════════════
    # 10. Professional Summary Rewrite
    # ════════════════════════════════════════════════════════════════════

    @gl.public.write
    def rewrite_positioning(
        self,
        content_hash: str,
        cv_text: str,
        job_title: str,
        company_name: str,
        tone: str,
    ) -> str:
        self._check_live()

        store_key = "pos_" + content_hash
        cached = self.evaluations.get(store_key, None)
        if cached is not None:
            return cached

        prompt = (
            "You are a professional CV writer specialising in executive personal branding.\n"
            "Write a polished 2–3 sentence professional summary for a candidate targeting "
            + job_title + " at " + company_name + ".\n\n"
            "Tone: " + tone + "\n\n"
            "Requirements:\n"
            "- Open with a strong identity statement (title + years of experience).\n"
            "- Highlight the top 2–3 differentiating skills/achievements.\n"
            "- Close with a forward-looking statement about the value for " + company_name + ".\n"
            "- Maximum 80 words.\n"
            "- Return ONLY the summary text, no JSON, no labels.\n\n"
            "CV:\n" + cv_text
        )

        criteria = (
            "Equivalent if: (1) both identify the candidate's primary expertise; "
            "(2) both mention the target role and company; "
            "(3) both are 2–3 sentences in the stated tone; "
            "(4) key differentiators are substantially similar."
        )

        def _run():
            raw = gl.nondet.exec_prompt(prompt)
            return str(raw).strip()

        result = gl.eq_principle.prompt_non_comparative(
            task=_run,
            criteria="Return the summary text with the same core positioning and company focus.",
        )
        self.evaluations[store_key] = result
        return result

    # ════════════════════════════════════════════════════════════════════
    # 11. Application Stage Strategy
    # ════════════════════════════════════════════════════════════════════

    @gl.public.write
    def advise_application_strategy(
        self,
        content_hash: str,
        cv_text: str,
        job_text: str,
        job_title: str,
        company_name: str,
        application_stage: str,
    ) -> str:
        self._check_live()

        store_key = "strat_" + content_hash + "_" + application_stage
        cached = self.evaluations.get(store_key, None)
        if cached is not None:
            return cached

        prompt = (
            "You are a strategic career advisor.\n"
            "Provide a concrete next-step strategy for the application stage: "
            + application_stage + ".\n\n"
            "Return ONLY valid JSON (no markdown) matching this schema:\n"
            + _STRATEGY_SCHEMA + "\n\n"
            "Rules:\n"
            "- immediate_actions: 3 things to do in the next 24 hours.\n"
            "- this_week_actions: 5 things to do this week.\n"
            "- networking_moves: 3 specific actions (LinkedIn, referrals, events).\n"
            "- research_targets: 3 things to research about the company/role.\n"
            "- mindset_tips: 2 psychological/confidence tips.\n"
            "- common_mistakes_to_avoid: 3 critical pitfalls at this stage.\n"
            "- success_metrics: 3 signals this stage is going well.\n"
            "- timeline_days: realistic integer until this stage resolves.\n\n"
            "COMPANY: " + company_name + "\n"
            "ROLE: " + job_title + "\n"
            "STAGE: " + application_stage + "\n\n"
            "JOB DESCRIPTION:\n" + job_text + "\n\n"
            "CV:\n" + cv_text
        )

        _fb = {
            "stage": application_stage,
            "immediate_actions": [], "this_week_actions": [],
            "networking_moves": [], "research_targets": [],
            "mindset_tips": [], "common_mistakes_to_avoid": [],
            "success_metrics": [], "timeline_days": 7, "summary": "",
        }
        criteria = (
            "Equivalent if: (1) valid JSON for the same application_stage; "
            "(2) immediate_actions express similar priorities; "
            "(3) common_mistakes_to_avoid cover similar pitfalls."
        )

        def _run():
            raw = gl.nondet.exec_prompt(prompt)
            return json.dumps(_parse(str(raw), _fb), sort_keys=True)

        result = gl.eq_principle.prompt_non_comparative(
            task=_run,
            criteria="Return valid JSON. Keep the strategy recommendations broadly aligned.",
        )
        self.evaluations[store_key] = result
        return result

    # ════════════════════════════════════════════════════════════════════
    # 12. Full-Suite Batch  (one transaction — all core analyses)
    # ════════════════════════════════════════════════════════════════════

    @gl.public.write
    def run_full_suite(
        self,
        content_hash: str,
        job_hash: str,
        cv_text: str,
        cover_letter: str,
        job_text: str,
        job_title: str,
        job_url: str,
        company_name: str,
        linkedin_url: str,
        portfolio_url: str,
        location: str,
    ) -> str:
        self._check_live()

        # ── 1. Core evaluation ──────────────────────────────────────────
        eval_result = self.evaluations.get(content_hash, None)
        if eval_result is None:
            _eval_prompt = (
                "You are CVPilot — expert ATS evaluator, recruiter, and career coach.\n"
                "Evaluate the candidate's application.\n\n"
                "Return ONLY valid JSON (no markdown) matching this schema:\n"
                + _EVAL_SCHEMA + "\n\n"
                "Scoring weights: cv=" + str(_W_CV) + "% cover=" + str(_W_COVER) +
                "% match=" + str(_W_MATCH) + "% ats=" + str(_W_ATS) +
                "% compete=" + str(_W_COMPETE) + "%.\n"
                "overall_score = weighted average. All scores 0–100.\n\n"
                "JOB TITLE: " + job_title + " | JOB URL: " + job_url + "\n"
                "LINKEDIN: " + linkedin_url + " | PORTFOLIO: " + portfolio_url + "\n\n"
                "JOB DESCRIPTION:\n" + job_text + "\n\n"
                "CV:\n" + cv_text + "\n\n"
                "COVER LETTER:\n" + cover_letter
            )
            _fb_r = {k: "parse error" for k in [
                "cv_score","cover_letter_score","job_match_score",
                "ats_score","competitiveness_score","overall_score",
            ]}
            _fb_e = {
                "cv_score": 0, "cover_letter_score": 0, "job_match_score": 0,
                "ats_score": 0, "competitiveness_score": 0, "overall_score": 0,
                "summary": "", "missing_keywords": [], "missing_skills": [],
                "recommendations": [], "weak_statements": [],
                "company_alignment_notes": [], "strengths": [], "risks": [],
                "improved_positioning": "", "rationale": _fb_r,
            }

            def _ev():
                raw = gl.nondet.exec_prompt(_eval_prompt)
                return json.dumps(_parse(str(raw), _fb_e), sort_keys=True)

            eval_result = gl.eq_principle.prompt_non_comparative(
                task=_ev,
                criteria="Return valid JSON. Keep the overall evaluation broadly aligned with the input.",
            )
            self.evaluations[content_hash] = eval_result
            self.total_evaluated = self.total_evaluated + u256(1)
            if linkedin_url:
                self._index_push(self.candidate_history, linkedin_url, content_hash)
            if job_url:
                self._index_push(self.job_history, job_url, content_hash)

        # ── 2. Skills gap ────────────────────────────────────────────────
        skills_result = self.skills_analyses.get(content_hash, None)
        if skills_result is None:
            _sk_prompt = (
                "You are a senior technical recruiter. Perform a skills gap analysis.\n\n"
                "Return ONLY valid JSON (no markdown) matching this schema:\n"
                + _SKILLS_SCHEMA + "\n\n"
                "JOB TITLE: " + job_title + "\n\n"
                "JOB DESCRIPTION:\n" + job_text + "\n\nCV:\n" + cv_text
            )
            _fb_sk = {
                "candidate_skills": [], "required_skills": [], "gap_skills": [],
                "bonus_skills": [], "skill_match_score": 0,
                "skill_categories": {"technical": [], "soft": [], "domain": [], "certifications": []},
                "upskilling_roadmap": [], "estimated_ramp_weeks": 0, "summary": "",
            }

            def _sk():
                raw = gl.nondet.exec_prompt(_sk_prompt)
                return json.dumps(_parse(str(raw), _fb_sk), sort_keys=True)

            skills_result = gl.eq_principle.prompt_non_comparative(
                task=_sk,
                criteria="Return valid JSON. Keep the skills gap analysis broadly aligned.",
            )
            self.skills_analyses[content_hash] = skills_result
            self.total_skills_analyses = self.total_skills_analyses + u256(1)

        # ── 3. Career trajectory ─────────────────────────────────────────
        career_result = self.career_analyses.get(content_hash, None)
        if career_result is None:
            _ca_prompt = (
                "You are an executive career coach. Analyse career trajectory for a "
                + job_title + " role.\n\n"
                "Return ONLY valid JSON (no markdown) matching this schema:\n"
                + _CAREER_SCHEMA + "\n\nCV:\n" + cv_text
            )
            _fb_ca = {
                "trajectory_score": 0, "progression_type": "linear",
                "years_of_experience": 0, "seniority_level": "mid",
                "career_highlights": [], "career_gaps": [],
                "promotion_velocity": "average", "industry_breadth": [],
                "specialist_areas": [], "growth_potential": "medium",
                "risks": [], "summary": "",
            }

            def _ca():
                raw = gl.nondet.exec_prompt(_ca_prompt)
                return json.dumps(_parse(str(raw), _fb_ca), sort_keys=True)

            career_result = gl.eq_principle.prompt_non_comparative(
                task=_ca,
                criteria="Return valid JSON. Keep the career trajectory analysis broadly aligned.",
            )
            self.career_analyses[content_hash] = career_result
            self.total_career_analyses = self.total_career_analyses + u256(1)

        # ── 4. Cover letter ──────────────────────────────────────────────
        cl_result = self.cover_letter_analyses.get(content_hash, None)
        if cl_result is None:
            _cl_prompt = (
                "You are a cover letter specialist. Evaluate for a "
                + job_title + " role at " + company_name + ".\n\n"
                "Return ONLY valid JSON (no markdown) matching this schema:\n"
                + _COVER_LETTER_SCHEMA + "\n\n"
                "JOB DESCRIPTION:\n" + job_text + "\n\nCOVER LETTER:\n" + cover_letter
            )
            _fb_cl = {
                "score": 0, "tone_match": "neutral", "personalization_score": 0,
                "storytelling_score": 0, "call_to_action_strength": "weak",
                "keyword_density_score": 0, "length_appropriateness": "ideal",
                "strengths": [], "weaknesses": [], "suggested_rewrites": [], "summary": "",
            }

            def _cl():
                raw = gl.nondet.exec_prompt(_cl_prompt)
                return json.dumps(_parse(str(raw), _fb_cl), sort_keys=True)

            cl_result = gl.eq_principle.prompt_non_comparative(
                task=_cl,
                criteria="Return valid JSON. Keep the cover letter assessment broadly aligned.",
            )
            self.cover_letter_analyses[content_hash] = cl_result
            self.total_cover_letter_analyses = self.total_cover_letter_analyses + u256(1)

        # ── 5. Salary estimate ───────────────────────────────────────────
        salary_result = self.salary_estimates.get(content_hash, None)
        if salary_result is None:
            _sal_prompt = (
                "You are a compensation specialist. Estimate salary for a "
                + job_title + " role in " + location + ".\n\n"
                "Return ONLY valid JSON (no markdown) matching this schema:\n"
                + _SALARY_SCHEMA + "\n\n"
                "JOB DESCRIPTION:\n" + job_text + "\n\nCV:\n" + cv_text
            )
            _fb_sal = {
                "currency": "USD", "range_low": 0, "range_mid": 0, "range_high": 0,
                "confidence": "low", "rationale": "",
                "negotiation_tips": [], "market_signals": [],
            }

            def _sal():
                raw = gl.nondet.exec_prompt(_sal_prompt)
                return json.dumps(_parse(str(raw), _fb_sal), sort_keys=True)

            salary_result = gl.eq_principle.prompt_non_comparative(
                task=_sal,
                criteria="Return valid JSON. Keep the salary estimate broadly aligned.",
            )
            self.salary_estimates[content_hash] = salary_result
            self.total_salary_estimates = self.total_salary_estimates + u256(1)

        return json.dumps({
            "content_hash":          content_hash,
            "evaluation":            _parse(eval_result, {}),
            "skills_analysis":       _parse(skills_result, {}),
            "career_analysis":       _parse(career_result, {}),
            "cover_letter_analysis": _parse(cl_result, {}),
            "salary_estimate":       _parse(salary_result, {}),
        }, sort_keys=True)
