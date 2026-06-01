"""
Phase 7A frontend recovery: write the three files that the previous scaffold
silently skipped because the heredoc was truncated before the write loop.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
FILES: dict[str, str] = {}


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

export type RewriteStatus = 'pending' | 'running' | 'complete' | 'failed';
export type RewriteKind = 'cv' | 'cover_letter' | 'interview_prep';

export interface RewritePublic {
  id: string;
  application_id: string;
  kind: RewriteKind;
  status: RewriteStatus;
  backend: string | null;
  content: string | null;
  rationale: string[];
  raw: Record<string, unknown> | null;
  error: string | null;
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
  RewritePublic,
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

export const rewritesApi = {
  list(applicationId: string): Promise<RewritePublic[]> {
    return api<RewritePublic[]>(`/applications/${applicationId}/rewrites`);
  },
  get(applicationId: string, rewriteId: string): Promise<RewritePublic> {
    return api<RewritePublic>(`/applications/${applicationId}/rewrites/${rewriteId}`);
  },
  requestCv(applicationId: string): Promise<RewritePublic> {
    return api<RewritePublic>(`/applications/${applicationId}/rewrites/cv`, {
      method: 'POST',
    });
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


FILES["frontend/src/components/dashboard/RewritePanel.tsx"] = '''\'use client\';

import { useEffect, useState } from 'react';
import { ApiError, rewritesApi } from '@/lib/api';
import { useToast } from '@/contexts/ToastContext';
import type { ApplicationPublic, RewritePublic } from '@/lib/types';

interface Props {
  application: ApplicationPublic;
}

function fmt(s: string): string {
  try { return new Date(s).toLocaleString(); } catch { return s; }
}

export function RewritePanel({ application }: Props) {
  const [rewrites, setRewrites] = useState<RewritePublic[] | null>(null);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { push } = useToast();

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const list = await rewritesApi.list(application.id);
        if (!alive) return;
        setRewrites(list);
        if (list.length > 0) setActiveId(list[0].id);
      } catch (e) {
        if (alive) setError(e instanceof ApiError ? e.message : 'Could not load.');
      }
    })();
    return () => { alive = false; };
  }, [application.id]);

  useEffect(() => {
    if (!activeId) return;
    const active = rewrites?.find((r) => r.id === activeId);
    if (!active || active.status === 'complete' || active.status === 'failed') return;

    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    async function tick() {
      try {
        const updated = await rewritesApi.get(application.id, activeId!);
        if (stopped) return;
        setRewrites((cur) =>
          (cur || []).map((r) => (r.id === updated.id ? updated : r)),
        );
        if (updated.status === 'complete') {
          push({ tone: 'success', title: 'Rewrite ready.', message: 'See your new CV draft below.' });
          return;
        }
        if (updated.status === 'failed') {
          push({ tone: 'error', title: 'Rewrite failed.', message: updated.error || undefined });
          return;
        }
        timer = setTimeout(tick, 3000);
      } catch (e) {
        if (!stopped) {
          setError(e instanceof ApiError ? e.message : 'Could not refresh.');
        }
      }
    }
    void tick();
    return () => { stopped = true; if (timer) clearTimeout(timer); };
  }, [activeId, application.id, push, rewrites]);

  async function requestRewrite() {
    setBusy(true);
    setError(null);
    try {
      const created = await rewritesApi.requestCv(application.id);
      setRewrites((cur) => [created, ...(cur || [])]);
      setActiveId(created.id);
      push({ tone: 'info', title: 'Working on your rewrite.' });
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : 'Could not start rewrite.';
      setError(msg);
      push({ tone: 'error', title: 'Could not start.', message: msg });
    } finally {
      setBusy(false);
    }
  }

  const active = activeId ? rewrites?.find((r) => r.id === activeId) : null;
  const cvFile = application.files.find((f) => f.kind === 'cv');
  const original = cvFile?.extracted_text || '';

  async function copyContent() {
    if (!active?.content) return;
    try {
      await navigator.clipboard.writeText(active.content);
      push({ tone: 'success', title: 'Copied rewritten CV.' });
    } catch {
      push({ tone: 'error', title: 'Could not copy.' });
    }
  }

  return (
    <section>
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <div>
          <h2 className="font-serif text-3xl">Rewrite my CV.</h2>
          <p className="mt-2 max-w-2xl text-sm text-[#3a342c]">
            Use the evaluation above to produce a stronger draft. We surface
            missing keywords, sharpen weak bullets, and tighten the structure
            for ATS.
          </p>
        </div>
        <button
          type="button"
          onClick={requestRewrite}
          disabled={busy}
          className="inline-flex items-center justify-center rounded-full bg-[#2b4f3a] px-5 py-2.5 text-sm font-medium text-[#efece4] hover:bg-[#1f3a2a] disabled:opacity-60"
        >
          {busy ? 'Starting...' : (rewrites && rewrites.length > 0 ? 'Generate new draft' : 'Generate first draft')}
        </button>
      </div>

      {error && (
        <p className="mt-4 rounded-2xl border border-[#9b2226]/30 bg-[#9b2226]/10 p-4 text-sm text-[#9b2226]">
          {error}
        </p>
      )}

      {rewrites === null && (
        <p className="mt-6 text-sm text-[#3a342c]">Loading drafts.</p>
      )}

      {rewrites && rewrites.length > 1 && (
        <div className="mt-6 flex flex-wrap gap-2">
          {rewrites.map((r) => (
            <button
              key={r.id}
              type="button"
              onClick={() => setActiveId(r.id)}
              className={[
                'rounded-full px-3 py-1.5 text-xs uppercase tracking-[0.15em]',
                activeId === r.id
                  ? 'bg-[#1a1814] text-[#efece4]'
                  : 'border border-[#1a1814]/20 text-[#1a1814] hover:bg-[#1a1814]/5',
              ].join(' ')}
            >
              {fmt(r.created_at)} \u00b7 {r.status}
            </button>
          ))}
        </div>
      )}

      {active && (
        <div className="mt-8 grid gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border border-[#1a1814]/10 bg-white/50 p-6">
            <div className="flex items-baseline justify-between">
              <h3 className="font-serif text-xl">Original</h3>
              <span className="text-[10px] uppercase tracking-[0.15em] text-[#3a342c]/70">
                As uploaded
              </span>
            </div>
            <pre className="mt-4 max-h-[480px] overflow-auto whitespace-pre-wrap font-sans text-sm leading-relaxed text-[#1a1814]">
              {original || 'No CV text available.'}
            </pre>
          </div>

          <div className="rounded-2xl border border-[#2b4f3a]/25 bg-[#2b4f3a]/5 p-6">
            <div className="flex items-baseline justify-between gap-3">
              <h3 className="font-serif text-xl text-[#1f3a2a]">
                Rewritten draft
              </h3>
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase tracking-[0.15em] text-[#2b4f3a]">
                  {active.status}
                </span>
                {active.status === 'complete' && active.content && (
                  <button
                    type="button"
                    onClick={copyContent}
                    className="rounded-full border border-[#2b4f3a]/30 px-3 py-1 text-xs text-[#2b4f3a] hover:bg-[#2b4f3a]/15"
                  >
                    Copy
                  </button>
                )}
              </div>
            </div>
            {active.status === 'pending' || active.status === 'running' ? (
              <p className="mt-6 text-sm text-[#3a342c]">
                Drafting your rewrite. This page updates automatically.
              </p>
            ) : active.status === 'failed' ? (
              <p className="mt-6 text-sm text-[#9b2226]">
                {active.error || 'Rewrite failed.'}
              </p>
            ) : (
              <>
                <pre className="mt-4 max-h-[480px] overflow-auto whitespace-pre-wrap font-sans text-sm leading-relaxed text-[#1a1814]">
                  {active.content || ''}
                </pre>
                {active.rationale.length > 0 && (
                  <div className="mt-5 border-t border-[#2b4f3a]/20 pt-5">
                    <p className="text-xs uppercase tracking-[0.15em] text-[#2b4f3a]">
                      What we changed
                    </p>
                    <ul className="mt-3 grid gap-2 text-sm text-[#1a1814]">
                      {active.rationale.map((r, i) => (
                        <li
                          key={i}
                          className="rounded-xl border border-[#2b4f3a]/20 bg-white/70 px-3 py-2"
                        >
                          {r}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
'''


def write(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  wrote {rel}")


for rel, content in FILES.items():
    write(rel, content)

print("\nPhase 7A frontend recovery complete.")
