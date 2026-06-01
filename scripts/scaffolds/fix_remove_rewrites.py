"""
Remove rewrite imports/references across the backend and frontend.
"""

from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
FILES: dict[str, str] = {}


# Backend: models/__init__.py — drop Rewrite import
FILES["backend/app/models/__init__.py"] = '''"""
Import all models here so Alembic autogenerate detects them.
"""

from backend.app.models.user import User  # noqa: F401
from backend.app.models.audit_log import AuditLog  # noqa: F401
from backend.app.models.application import Application, FileAsset  # noqa: F401
from backend.app.models.evaluation import Evaluation  # noqa: F401
'''


# Backend: api/v1/router.py — drop rewrites router
FILES["api/v1/router.py"] = '''"""
Versioned API router aggregator.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.routes import admin, applications, auth, evaluations

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(applications.router)
api_router.include_router(evaluations.router)
api_router.include_router(admin.router)
'''


# Backend: workers/celery_app.py — drop rewrites task include
FILES["workers/celery_app.py"] = '''"""
Celery application factory.
"""

from __future__ import annotations

import os

from celery import Celery

from backend.app.core.config import settings

celery_app = Celery(
    "cvpilot",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "workers.tasks.applications",
        "workers.tasks.evaluations",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=180,
    task_soft_time_limit=150,
    worker_max_tasks_per_child=100,
    broker_connection_retry_on_startup=True,
)

if os.getenv("CELERY_TASK_ALWAYS_EAGER", "").lower() in {"1", "true", "yes"}:
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
'''


# Backend: services/llm/base.py — drop LLMRewrite + rewrite_cv protocol method
FILES["services/llm/base.py"] = '''"""
Pluggable LLM client interface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class LLMScore:
    value: int
    label: str
    rationale: str
    signals: dict = field(default_factory=dict)


@dataclass(frozen=True)
class LLMEvaluation:
    cv: LLMScore
    cover_letter: LLMScore
    job_match: LLMScore
    ats: LLMScore
    competitiveness: LLMScore
    summary: str
    missing_keywords: list[str]
    missing_skills: list[str]
    recommendations: list[str]
    weak_statements: list[str]
    company_alignment_notes: list[str]
    raw: dict


class LLMClient(Protocol):
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
    ) -> LLMEvaluation: ...
'''


# Frontend: lib/types.ts — drop Rewrite* types
FILES["frontend/src/lib/types.ts"] = '''export interface UserPublic {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_premium: boolean;
  is_superuser: boolean;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}

export type ApplicationStatus =
  | 'pending'
  | 'processing'
  | 'ready'
  | 'evaluating'
  | 'complete'
  | 'failed';

export type FileKind = 'cv' | 'cover_letter';

export interface FileAssetPublic {
  id: string;
  kind: FileKind;
  original_filename: string;
  content_type: string;
  byte_size: number;
  detected_kind: string | null;
  extracted_text: string | null;
}

export interface ApplicationPublic {
  id: string;
  job_url: string;
  job_final_url: string | null;
  job_title: string | null;
  job_text: string | null;
  linkedin_url: string | null;
  portfolio_url: string | null;
  status: ApplicationStatus;
  error: string | null;
  created_at: string;
  updated_at: string;
  files: FileAssetPublic[];
}

export interface ApplicationListItem {
  id: string;
  job_url: string;
  job_title: string | null;
  status: ApplicationStatus;
  created_at: string;
}

export type EvaluationStatus = 'pending' | 'running' | 'complete' | 'failed';

export interface EvaluationPublic {
  id: string;
  application_id: string;
  status: EvaluationStatus;
  backend: string | null;
  cv_score: number | null;
  cover_letter_score: number | null;
  job_match_score: number | null;
  ats_score: number | null;
  competitiveness_score: number | null;
  summary: string | null;
  recommendations: string[];
  missing_keywords: string[];
  missing_skills: string[];
  weak_statements: string[];
  company_alignment_notes: string[];
  raw: Record<string, unknown> | null;
  error: string | null;
  contract_tx_hash: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdminStats {
  user_count: number;
  application_count: number;
  evaluations_complete: number;
  evaluations_failed: number;
  last_24h_users: number;
  last_24h_applications: number;
  by_status: Record<string, number>;
}

export interface AdminUserListItem {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_premium: boolean;
  is_superuser: boolean;
  created_at: string;
  application_count: number;
  last_application_at: string | null;
}

export interface AdminApplicationListItem {
  id: string;
  user_id: string;
  user_email: string;
  job_url: string;
  job_title: string | null;
  status: ApplicationStatus;
  created_at: string;
  has_evaluation: boolean;
  competitiveness: number | null;
}
'''


# Frontend: lib/api.ts — drop rewritesApi + RewritePublic import
FILES["frontend/src/lib/api.ts"] = '''import { apiBaseUrl } from './brand';
import { tokenStorage } from './authStorage';
import type {
  AdminApplicationListItem,
  AdminStats,
  AdminUserListItem,
  ApiErrorBody,
  ApplicationListItem,
  ApplicationPublic,
  EvaluationPublic,
  TokenPair,
  UserPublic,
} from './types';

export class ApiError extends Error {
  status: number;
  code: string;
  details?: unknown;
  constructor(status: number, code: string, message: string, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

interface FetchOpts extends RequestInit {
  auth?: boolean;
}

async function rawFetch<T>(path: string, opts: FetchOpts = {}): Promise<T> {
  const headers = new Headers(opts.headers);
  const wantAuth = opts.auth !== false;
  if (wantAuth) {
    const token = tokenStorage.getAccess();
    if (token) headers.set('Authorization', `Bearer ${token}`);
  }
  const isFormData = typeof FormData !== 'undefined' && opts.body instanceof FormData;
  if (!headers.has('Content-Type') && !isFormData && opts.body) {
    headers.set('Content-Type', 'application/json');
  }
  const res = await fetch(`${apiBaseUrl}${path}`, { ...opts, headers });
  let body: unknown = null;
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) {
    try { body = await res.json(); } catch { body = null; }
  }
  if (!res.ok) {
    const errBody = body as ApiErrorBody | null;
    const err = errBody?.error;
    throw new ApiError(
      res.status,
      err?.code || 'http_error',
      err?.message || `HTTP ${res.status}`,
      err?.details,
    );
  }
  return body as T;
}

async function refreshAccess(): Promise<boolean> {
  const refresh = tokenStorage.getRefresh();
  if (!refresh) return false;
  try {
    const tokens = await rawFetch<TokenPair>('/auth/refresh', {
      method: 'POST',
      auth: false,
      body: JSON.stringify({ refresh_token: refresh }),
    });
    tokenStorage.set(tokens.access_token, tokens.refresh_token);
    return true;
  } catch {
    tokenStorage.clear();
    return false;
  }
}

export async function api<T>(path: string, opts: FetchOpts = {}): Promise<T> {
  try {
    return await rawFetch<T>(path, opts);
  } catch (e) {
    if (e instanceof ApiError && e.status === 401 && opts.auth !== false) {
      const ok = await refreshAccess();
      if (ok) return await rawFetch<T>(path, opts);
    }
    throw e;
  }
}

export const authApi = {
  login(email: string, password: string): Promise<TokenPair> {
    return api<TokenPair>('/auth/login', {
      method: 'POST',
      auth: false,
      body: JSON.stringify({ email, password }),
    });
  },
  register(email: string, password: string, full_name?: string): Promise<UserPublic> {
    return api<UserPublic>('/auth/register', {
      method: 'POST',
      auth: false,
      body: JSON.stringify({ email, password, full_name: full_name || null }),
    });
  },
  me(): Promise<UserPublic> {
    return api<UserPublic>('/auth/me');
  },
};

export interface CreateApplicationInput {
  job_url: string;
  linkedin_url?: string;
  portfolio_url?: string;
  cv: File;
  cover_letter: File;
}

export const applicationsApi = {
  create(input: CreateApplicationInput): Promise<ApplicationPublic> {
    const fd = new FormData();
    fd.append('job_url', input.job_url);
    if (input.linkedin_url) fd.append('linkedin_url', input.linkedin_url);
    if (input.portfolio_url) fd.append('portfolio_url', input.portfolio_url);
    fd.append('cv', input.cv, input.cv.name);
    fd.append('cover_letter', input.cover_letter, input.cover_letter.name);
    return api<ApplicationPublic>('/applications', { method: 'POST', body: fd });
  },
  list(): Promise<ApplicationListItem[]> {
    return api<ApplicationListItem[]>('/applications');
  },
  get(id: string): Promise<ApplicationPublic> {
    return api<ApplicationPublic>(`/applications/${id}`);
  },
  getEvaluation(id: string): Promise<EvaluationPublic> {
    return api<EvaluationPublic>(`/applications/${id}/evaluation`);
  },
  triggerEvaluation(id: string): Promise<EvaluationPublic> {
    return api<EvaluationPublic>(`/applications/${id}/evaluate`, { method: 'POST' });
  },
};

export interface AdminListAppsOpts {
  status?: string;
  user_id?: string;
  limit?: number;
  offset?: number;
}

export const adminApi = {
  stats(): Promise<AdminStats> {
    return api<AdminStats>('/admin/stats');
  },
  listUsers(limit = 100, offset = 0): Promise<AdminUserListItem[]> {
    return api<AdminUserListItem[]>(`/admin/users?limit=${limit}&offset=${offset}`);
  },
  getUser(id: string): Promise<AdminUserListItem> {
    return api<AdminUserListItem>(`/admin/users/${id}`);
  },
  listApplications(opts: AdminListAppsOpts = {}): Promise<AdminApplicationListItem[]> {
    const p = new URLSearchParams();
    if (opts.status) p.set('status', opts.status);
    if (opts.user_id) p.set('user_id', opts.user_id);
    p.set('limit', String(opts.limit ?? 100));
    p.set('offset', String(opts.offset ?? 0));
    return api<AdminApplicationListItem[]>(`/admin/applications?${p.toString()}`);
  },
  getApplication(id: string): Promise<ApplicationPublic> {
    return api<ApplicationPublic>(`/admin/applications/${id}`);
  },
  getEvaluation(id: string): Promise<EvaluationPublic> {
    return api<EvaluationPublic>(`/admin/applications/${id}/evaluation`);
  },
};
'''


# Frontend: services/llm/stub.py — drop rewrite_cv
FILES["services/llm/stub.py"] = '''"""
Deterministic LLM stand-in (kept for tests / dev only). Production uses
LLM_BACKEND=genlayer.
"""

from __future__ import annotations

import re
from collections import Counter

from services.llm.base import LLMClient, LLMEvaluation, LLMScore

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9+#.\\-]{1,}")
_STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "have", "has",
    "are", "you", "your", "our", "will", "into", "to", "of", "in", "on",
    "at", "by", "as", "an", "a", "is", "be", "we", "or", "it", "i", "ll",
    "re", "ve", "s", "t", "d",
}
_ACHIEVEMENT_CUES = re.compile(
    r"\\b(led|owned|shipped|launched|increased|reduced|scaled|saved|"
    r"grew|delivered|drove|migrated|architected|built|designed)\\b",
    re.IGNORECASE,
)
_METRIC_CUE = re.compile(
    r"\\b\\d+(?:\\.\\d+)?\\s?(%|x|k|m|million|billion|users|customers|requests|qps|ms|seconds?|hours?|days?|weeks?|months?|years?)\\b",
    re.IGNORECASE,
)
_ATS_BAD_CUES = re.compile(r"[\\u2022\\u25CF\\u25E6\\u25A0]+|<img|<table", re.IGNORECASE)


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
    n_achievements = len(_ACHIEVEMENT_CUES.findall(cv))
    n_metrics = len(_METRIC_CUE.findall(cv))
    length_factor = min(1.0, len(cv) / 1800)
    score = 35 + 35 * coverage + 12 * min(1.0, n_achievements / 6) + 18 * length_factor
    if n_metrics:
        score += min(8, n_metrics * 2)
    return (
        LLMScore(
            value=_clamp(score),
            label="cv",
            rationale=f"Matched {len(hits)} job keywords, {n_achievements} verbs, {n_metrics} metrics.",
            signals={"keyword_hits": hits, "achievement_verbs": n_achievements, "metrics_found": n_metrics, "length_chars": len(cv)},
        ),
        missing,
        hits,
    )


def _score_cover_letter(cl, job, job_title):
    coverage, hits, _missing = _keyword_overlap(job, cl)
    mentions_title = bool(job_title and job_title.lower() in cl.lower())
    addressed = bool(re.search(r"^(dear|hi|hello)\\b", cl.strip(), re.IGNORECASE))
    p = 0
    if mentions_title: p += 12
    if addressed: p += 6
    length_factor = min(1.0, len(cl) / 900)
    score = 30 + 35 * coverage + p + 18 * length_factor
    return LLMScore(
        value=_clamp(score),
        label="cover_letter",
        rationale="Auto.",
        signals={"keyword_hits": hits, "mentions_title": mentions_title, "addressed": addressed, "length_chars": len(cl)},
    )


def _score_job_match(cv, cl, job):
    cv_cov, _, _ = _keyword_overlap(job, cv)
    cl_cov, _, _ = _keyword_overlap(job, cl)
    combined = 0.65 * cv_cov + 0.35 * cl_cov
    return LLMScore(
        value=_clamp(25 + 70 * combined),
        label="job_match",
        rationale="Weighted CV/CL keyword alignment.",
        signals={"cv_coverage": round(cv_cov, 3), "cover_letter_coverage": round(cl_cov, 3)},
    )


def _score_ats(cv):
    bad = len(_ATS_BAD_CUES.findall(cv))
    too_short = len(cv) < 800
    has_email = bool(re.search(r"[A-Za-z0-9._%+\\-]+@[A-Za-z0-9.\\-]+", cv))
    has_phone = bool(re.search(r"\\+?\\d[\\d \\-().]{7,}\\d", cv))
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
        recs = []
        if missing_keywords:
            recs.append(f"Surface these missing job keywords in your CV: {', '.join(missing_keywords[:8])}.")
        return LLMEvaluation(
            cv=cv_score, cover_letter=cl_score, job_match=match_score, ats=ats_score, competitiveness=competitiveness,
            summary=f"Competitiveness {competitiveness.value}/100.",
            missing_keywords=missing_keywords, missing_skills=missing_keywords[:8], recommendations=recs,
            weak_statements=_weak(cv_text), company_alignment_notes=[],
            raw={"backend": "stub", "version": 1, "scores": {
                "cv": cv_score.value, "cover_letter": cl_score.value, "job_match": match_score.value,
                "ats": ats_score.value, "competitiveness": competitiveness.value,
            }},
        )
'''


# Frontend: app/dashboard/applications/[id]/page.tsx — remove RewritePanel import + usage
# We do this in a separate step via in-place patch.


def write(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  wrote {rel}")


for rel, content in FILES.items():
    write(rel, content)


# In-place patch for the detail page
DETAIL = ROOT / "frontend/src/app/dashboard/applications/[id]/page.tsx"
text = DETAIL.read_text(encoding="utf-8")
text = text.replace(
    "import { RewritePanel } from '@/components/dashboard/RewritePanel';\n",
    "",
)
text = text.replace(
    "      <RewritePanel application={app} />\n\n",
    "",
)
DETAIL.write_text(text, encoding="utf-8")
print("  patched evaluation detail page (removed RewritePanel import + usage)")


# Delete the panel component file
RP = ROOT / "frontend/src/components/dashboard/RewritePanel.tsx"
if RP.exists():
    RP.unlink()
    print(f"  removed {RP.relative_to(ROOT)}")


# Also clean up the services/llm/genlayer.py rewrite_cv method by rewriting the file
GENLAYER = ROOT / "services/llm/genlayer.py"
genlayer_src = GENLAYER.read_text(encoding="utf-8")
# Remove the rewrite_cv method block
import re as _re

genlayer_src = _re.sub(
    r"    def rewrite_cv\(.*?return StubLLMClient\(\)\.rewrite_cv\([^)]*\)\n",
    "",
    genlayer_src,
    flags=_re.DOTALL,
)
# Remove the LLMRewrite import if present
genlayer_src = genlayer_src.replace(
    "from services.llm.base import LLMClient, LLMEvaluation, LLMRewrite, LLMScore",
    "from services.llm.base import LLMClient, LLMEvaluation, LLMScore",
)
GENLAYER.write_text(genlayer_src, encoding="utf-8")
print(f"  cleaned {GENLAYER.relative_to(ROOT)}")


print("\nRewrite removal complete.")
