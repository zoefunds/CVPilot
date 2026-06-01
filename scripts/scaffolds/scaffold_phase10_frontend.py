"""
Phase 10 frontend: /verify landing + /verify/[content_hash] page + Share button.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
FILES: dict[str, str] = {}


# Append PublicEvaluation to types — and keep all existing types.
FILES["frontend/src/lib/types.ts"] = '''export interface UserPublic {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_premium: boolean;
  is_superuser: boolean;
  wallet_address: string | null;
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

export interface WalletPublic {
  address: string;
  balance_wei: number;
  balance_gen: string;
  contract_address: string;
}

export interface WalletExport {
  address: string;
  private_key: string;
  warning: string;
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

export interface EvaluationRationale {
  cv_score?: string;
  cover_letter_score?: string;
  job_match_score?: string;
  ats_score?: string;
  competitiveness_score?: string;
  overall_score?: string;
}

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
  overall_score: number | null;
  summary: string | null;
  improved_positioning: string | null;
  recommendations: string[];
  missing_keywords: string[];
  missing_skills: string[];
  weak_statements: string[];
  company_alignment_notes: string[];
  strengths: string[];
  risks: string[];
  rationale: EvaluationRationale | null;
  raw: Record<string, unknown> | null;
  error: string | null;
  contract_tx_hash: string | null;
  content_hash: string | null;
  contract_address: string | null;
  created_at: string;
  updated_at: string;
}

export interface PublicEvaluation {
  content_hash: string;
  contract_address: string;
  found: boolean;
  cv_score: number | null;
  cover_letter_score: number | null;
  job_match_score: number | null;
  ats_score: number | null;
  competitiveness_score: number | null;
  overall_score: number | null;
  summary: string | null;
  improved_positioning: string | null;
  missing_keywords: string[];
  missing_skills: string[];
  recommendations: string[];
  weak_statements: string[];
  company_alignment_notes: string[];
  strengths: string[];
  risks: string[];
  rationale: EvaluationRationale | null;
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


# Append publicApi to api.ts
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
  PublicEvaluation,
  TokenPair,
  UserPublic,
  WalletExport,
  WalletPublic,
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
      err?.details ?? body,
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
      method: 'POST', auth: false,
      body: JSON.stringify({ email, password }),
    });
  },
  register(email: string, password: string, full_name?: string): Promise<UserPublic> {
    return api<UserPublic>('/auth/register', {
      method: 'POST', auth: false,
      body: JSON.stringify({ email, password, full_name: full_name || null }),
    });
  },
  me(): Promise<UserPublic> {
    return api<UserPublic>('/auth/me');
  },
};

export const walletApi = {
  get(): Promise<WalletPublic> { return api<WalletPublic>('/auth/wallet'); },
  export(): Promise<WalletExport> { return api<WalletExport>('/auth/wallet/export', { method: 'POST' }); },
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
  list(): Promise<ApplicationListItem[]> { return api<ApplicationListItem[]>('/applications'); },
  get(id: string): Promise<ApplicationPublic> { return api<ApplicationPublic>(`/applications/${id}`); },
  getEvaluation(id: string): Promise<EvaluationPublic> { return api<EvaluationPublic>(`/applications/${id}/evaluation`); },
  triggerEvaluation(id: string): Promise<EvaluationPublic> { return api<EvaluationPublic>(`/applications/${id}/evaluate`, { method: 'POST' }); },
};

export const publicApi = {
  verify(contentHash: string): Promise<PublicEvaluation> {
    return api<PublicEvaluation>(`/public/verify/${contentHash}`, { auth: false });
  },
};

export interface AdminListAppsOpts {
  status?: string;
  user_id?: string;
  limit?: number;
  offset?: number;
}

export const adminApi = {
  stats(): Promise<AdminStats> { return api<AdminStats>('/admin/stats'); },
  listUsers(limit = 100, offset = 0): Promise<AdminUserListItem[]> {
    return api<AdminUserListItem[]>(`/admin/users?limit=${limit}&offset=${offset}`);
  },
  getUser(id: string): Promise<AdminUserListItem> { return api<AdminUserListItem>(`/admin/users/${id}`); },
  listApplications(opts: AdminListAppsOpts = {}): Promise<AdminApplicationListItem[]> {
    const p = new URLSearchParams();
    if (opts.status) p.set('status', opts.status);
    if (opts.user_id) p.set('user_id', opts.user_id);
    p.set('limit', String(opts.limit ?? 100));
    p.set('offset', String(opts.offset ?? 0));
    return api<AdminApplicationListItem[]>(`/admin/applications?${p.toString()}`);
  },
  getApplication(id: string): Promise<ApplicationPublic> { return api<ApplicationPublic>(`/admin/applications/${id}`); },
  getEvaluation(id: string): Promise<EvaluationPublic> { return api<EvaluationPublic>(`/admin/applications/${id}/evaluation`); },
};
'''


# Reusable display component for public+private
FILES["frontend/src/components/verify/EvaluationDisplay.tsx"] = '''\'use client\';

import { ScoreGauge } from '@/components/ui/ScoreGauge';
import type { PublicEvaluation } from '@/lib/types';

function shortHash(h: string | null | undefined): string {
  if (!h) return '';
  if (h.length <= 14) return h;
  return `${h.slice(0, 8)}\u2026${h.slice(-6)}`;
}

export function EvaluationDisplay({ ev }: { ev: PublicEvaluation }) {
  return (
    <div className="flex flex-col gap-14">
      <section className="rounded-3xl border border-[#1a1814]/10 bg-white/55 p-8 shadow-[0_20px_60px_-30px_rgba(26,24,20,0.3)] sm:p-10">
        <div className="grid items-center gap-10 lg:grid-cols-12">
          <div className="lg:col-span-5">
            <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">
              Overall
            </p>
            <p className="mt-2 font-serif text-7xl text-[#1a1814] sm:text-8xl">
              {ev.overall_score ?? '\u2014'}
            </p>
            <p className="text-xs text-[#3a342c]/70">/ 100</p>

            <div className="mt-5 flex flex-wrap gap-2">
              {ev.competitiveness_score !== null && (
                <span className="rounded-full border border-[#1a1814]/15 bg-white/70 px-3 py-1 text-xs text-[#1a1814]">
                  Competitiveness {ev.competitiveness_score}/100
                </span>
              )}
              <span className="rounded-full bg-[#2b4f3a]/12 px-3 py-1 text-xs text-[#2b4f3a]">
                Verified on StudioNet
              </span>
            </div>
          </div>

          <div className="lg:col-span-7">
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <ScoreGauge label="CV" value={ev.cv_score} />
              <ScoreGauge label="Cover letter" value={ev.cover_letter_score} />
              <ScoreGauge label="Job match" value={ev.job_match_score} />
              <ScoreGauge label="ATS" value={ev.ats_score} />
            </div>
          </div>
        </div>

        {ev.summary && (
          <p className="mt-8 max-w-3xl border-t border-[#1a1814]/10 pt-6 text-[#3a342c]">
            {ev.summary}
          </p>
        )}
      </section>

      {ev.improved_positioning && (
        <section className="rounded-2xl border border-[#2b4f3a]/20 bg-[#2b4f3a]/5 p-6">
          <h2 className="font-serif text-2xl text-[#1f3a2a]">Improved positioning.</h2>
          <p className="mt-3 leading-relaxed text-[#1a1814]">{ev.improved_positioning}</p>
        </section>
      )}

      {(ev.strengths.length > 0 || ev.risks.length > 0) && (
        <section className="grid gap-6 sm:grid-cols-2">
          {ev.strengths.length > 0 && (
            <div>
              <h2 className="font-serif text-2xl">Strengths.</h2>
              <ul className="mt-4 grid gap-3">
                {ev.strengths.map((s, i) => (
                  <li key={i} className="rounded-2xl border border-[#2b4f3a]/25 bg-[#2b4f3a]/8 p-4 text-sm text-[#1f3a2a]">{s}</li>
                ))}
              </ul>
            </div>
          )}
          {ev.risks.length > 0 && (
            <div>
              <h2 className="font-serif text-2xl">Risks.</h2>
              <ul className="mt-4 grid gap-3">
                {ev.risks.map((r, i) => (
                  <li key={i} className="rounded-2xl border border-[#a35f1f]/30 bg-[#a35f1f]/10 p-4 text-sm text-[#a35f1f]">{r}</li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

      {ev.recommendations.length > 0 && (
        <section>
          <h2 className="font-serif text-3xl">Recommendations.</h2>
          <ul className="mt-5 grid gap-3">
            {ev.recommendations.map((r, i) => (
              <li key={i} className="flex items-start gap-4 rounded-2xl border border-[#1a1814]/10 bg-white/60 p-5">
                <span className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-full bg-[#2b4f3a]/15 font-serif text-sm text-[#2b4f3a]">
                  {i + 1}
                </span>
                <p className="text-sm leading-relaxed text-[#1a1814]">{r}</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      {ev.missing_keywords.length > 0 && (
        <section>
          <h2 className="font-serif text-3xl">Missing keywords.</h2>
          <div className="mt-5 flex flex-wrap gap-2">
            {ev.missing_keywords.map((kw) => (
              <span key={kw} className="rounded-full border border-[#1a1814]/15 bg-white/60 px-3 py-1 text-xs text-[#1a1814]">{kw}</span>
            ))}
          </div>
        </section>
      )}

      {ev.rationale && Object.keys(ev.rationale).length > 0 && (
        <section>
          <h2 className="font-serif text-3xl">Score rationale.</h2>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            {Object.entries(ev.rationale)
              .filter(([, v]) => Boolean(v))
              .map(([k, v]) => (
                <div key={k} className="rounded-2xl border border-[#1a1814]/10 bg-white/60 p-4 text-sm">
                  <p className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">{k.replace(/_/g, ' ')}</p>
                  <p className="mt-2 text-[#1a1814]">{v as string}</p>
                </div>
              ))}
          </div>
        </section>
      )}

      <section>
        <h2 className="font-serif text-3xl">Verification.</h2>
        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          <div className="rounded-2xl border border-[#1a1814]/10 bg-white/60 p-4">
            <p className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">Content hash</p>
            <p className="mt-2 break-all font-mono text-xs text-[#1a1814]">{ev.content_hash}</p>
            <p className="mt-2 text-[11px] text-[#3a342c]/70">
              sha256 of the application inputs ({shortHash(ev.content_hash)}).
            </p>
          </div>
          <div className="rounded-2xl border border-[#1a1814]/10 bg-white/60 p-4">
            <p className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">Contract address</p>
            <p className="mt-2 break-all font-mono text-xs text-[#1a1814]">{ev.contract_address}</p>
            <p className="mt-2 text-[11px] text-[#3a342c]/70">
              CVPilotEvaluator on GenLayer StudioNet ({shortHash(ev.contract_address)}).
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
'''


# /verify landing page (paste a hash)
FILES["frontend/src/app/verify/page.tsx"] = '''\'use client\';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormEvent, useState } from 'react';
import { Container } from '@/components/ui/Container';
import { Field } from '@/components/ui/Field';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { appName } from '@/lib/brand';

export default function VerifyLandingPage() {
  const router = useRouter();
  const [hash, setHash] = useState('');
  const [error, setError] = useState<string | null>(null);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const cleaned = hash.trim().toLowerCase();
    if (!/^[0-9a-f]{64}$/.test(cleaned)) {
      setError('That does not look like a 64 character content hash.');
      return;
    }
    router.push(`/verify/${cleaned}`);
  }

  return (
    <main className="min-h-screen">
      <header className="border-b border-[#d9d5c8] bg-[#efece4]/80 backdrop-blur">
        <Container className="flex h-16 items-center justify-between">
          <Link href="/" className="font-serif text-2xl">{appName}</Link>
          <Link href="/" className="text-sm text-[#3a342c] hover:text-[#1a1814]">
            Back to home
          </Link>
        </Container>
      </header>
      <Container className="py-24">
        <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">
          Public verification
        </p>
        <h1 className="mt-3 font-serif text-5xl sm:text-6xl">
          Read any CVPilot evaluation,
          <br />
          <span className="italic text-[#2b4f3a]">straight from the chain.</span>
        </h1>
        <p className="mt-5 max-w-2xl text-[#3a342c]">
          Paste a content hash below. We read the verified evaluation directly
          from the GenLayer Intelligent Contract on StudioNet. No signup. No
          intermediary.
        </p>

        <form onSubmit={onSubmit} className="mt-10 flex max-w-2xl flex-col gap-4">
          <Field label="Content hash" hint="A 64 character hexadecimal SHA-256.">
            <Input
              type="text"
              value={hash}
              onChange={(e) => { setHash(e.target.value); setError(null); }}
              placeholder="e.g. ac4a6e6855d57a17730ea46eb5e15d2a6a4e374ae38722a4dcaaeddc51df1ca4"
              className="font-mono text-sm"
              autoComplete="off"
              spellCheck={false}
            />
          </Field>
          {error && (
            <p className="rounded-2xl border border-[#9b2226]/30 bg-[#9b2226]/10 px-4 py-3 text-sm text-[#9b2226]">
              {error}
            </p>
          )}
          <div>
            <Button type="submit">Verify evaluation</Button>
          </div>
        </form>
      </Container>
    </main>
  );
}
'''


# /verify/[content_hash] page (fetches + renders)
FILES["frontend/src/app/verify/[content_hash]/page.tsx"] = '''\'use client\';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { EvaluationDisplay } from '@/components/verify/EvaluationDisplay';
import { Alert } from '@/components/ui/Alert';
import { Container } from '@/components/ui/Container';
import { ApiError, publicApi } from '@/lib/api';
import { appName } from '@/lib/brand';
import type { PublicEvaluation } from '@/lib/types';

export default function VerifyDetailPage() {
  const params = useParams<{ content_hash: string }>();
  const contentHash = (params?.content_hash || '').toLowerCase();

  const [data, setData] = useState<PublicEvaluation | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    setData(null); setNotFound(false); setError(null);
    (async () => {
      try {
        const ev = await publicApi.verify(contentHash);
        if (!alive) return;
        if (!ev.found) {
          setNotFound(true);
          setData(ev);
        } else {
          setData(ev);
        }
      } catch (e) {
        if (!alive) return;
        if (e instanceof ApiError && e.status === 404) {
          setNotFound(true);
          const body = (e.details && typeof e.details === 'object') ? (e.details as PublicEvaluation) : null;
          if (body) setData(body);
        } else {
          setError(e instanceof ApiError ? e.message : 'Could not load evaluation.');
        }
      }
    })();
    return () => { alive = false; };
  }, [contentHash]);

  return (
    <main className="min-h-screen">
      <header className="border-b border-[#d9d5c8] bg-[#efece4]/80 backdrop-blur sticky top-0 z-10">
        <Container className="flex h-16 items-center justify-between">
          <Link href="/" className="font-serif text-2xl">{appName}</Link>
          <Link href="/verify" className="text-sm text-[#3a342c] hover:text-[#1a1814]">
            Verify another
          </Link>
        </Container>
      </header>

      <Container className="py-14">
        <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">
          Public verification
        </p>
        <h1 className="mt-2 font-serif text-4xl sm:text-5xl">
          On-chain evaluation.
        </h1>
        <p className="mt-2 break-all font-mono text-xs text-[#3a342c]/80">
          {contentHash}
        </p>

        {error && (
          <div className="mt-8">
            <Alert tone="error">{error}</Alert>
          </div>
        )}

        {notFound && data && (
          <div className="mt-10 rounded-2xl border border-[#a35f1f]/40 bg-[#a35f1f]/10 p-6">
            <p className="text-xs uppercase tracking-[0.15em] text-[#a35f1f]">Not found</p>
            <h2 className="mt-2 font-serif text-2xl text-[#1a1814]">
              No evaluation is stored at this hash.
            </h2>
            <p className="mt-3 text-sm text-[#3a342c]">
              Either the hash is wrong, the evaluation has not finalised yet,
              or it lives on a different contract. The contract we checked is
              shown below.
            </p>
            <div className="mt-4 rounded-xl border border-[#a35f1f]/30 bg-white/60 p-3">
              <p className="text-[10px] uppercase tracking-[0.15em] text-[#a35f1f]">Contract</p>
              <p className="mt-1 break-all font-mono text-xs text-[#1a1814]">
                {data.contract_address}
              </p>
            </div>
            <div className="mt-5">
              <Link
                href="/verify"
                className="inline-flex items-center justify-center rounded-full border border-[#1a1814]/30 px-5 py-2 text-sm text-[#1a1814] hover:bg-[#1a1814]/5"
              >
                Try another hash
              </Link>
            </div>
          </div>
        )}

        {data && !notFound && (
          <div className="mt-10">
            <EvaluationDisplay ev={data} />
          </div>
        )}

        {!data && !error && !notFound && (
          <p className="mt-10 text-sm text-[#3a342c]">Reading the contract.</p>
        )}
      </Container>
    </main>
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

# Add a "Share verification link" button to the dashboard detail page
DETAIL = ROOT / "frontend/src/app/dashboard/applications/[id]/page.tsx"
text = DETAIL.read_text(encoding="utf-8")

if "Share verification link" not in text:
    # Inject after the StudioNet badge button block. We anchor on the
    # "Verified on StudioNet" string and add a sibling Share button.
    anchor = '              </button>\n            ) : (\n              <span className="mt-5 inline-block rounded-2xl border'
    if anchor in text:
        # Define a Share button component inline (uses content_hash + window.origin)
        share_block = (
            '              </button>\n'
            '            ) : (\n'
            '              <span className="mt-5 inline-block rounded-2xl border'
        )
        # Add share button right after the Verified badge button by inserting it between </button> and the else branch.
        # Find the </button>\n            ) : ( and after the closing of the conditional, insert a Share button
        # Simpler: inject a Share button inside the comp gauge column area near tx display.
        share_inject = (
            "{ev.content_hash && (\n"
            "              <button\n"
            "                type=\"button\"\n"
            "                onClick={() => onCopy(`${window.location.origin}/verify/${ev.content_hash}`, 'Verification link')}\n"
            "                className=\"mt-3 inline-flex items-center justify-center rounded-full border border-[#1a1814]/30 px-4 py-2 text-xs text-[#1a1814] hover:bg-[#1a1814]/5\"\n"
            "              >\n"
            "                Share verification link\n"
            "              </button>\n"
            "            )}\n            "
        )
        # Insert after the "Scored locally" span block end, before the closing of the .lg:col-span-5 div.
        marker = '              </span>\n            )}'
        if marker in text:
            text = text.replace(marker, '              </span>\n            )}\n            ' + share_inject, 1)
            DETAIL.write_text(text, encoding="utf-8")
            print("  patched dashboard detail page: Share verification link button added")
        else:
            print("  warn: could not find anchor to inject Share button; please add manually")
    else:
        print("  warn: could not locate StudioNet badge anchor; Share button not added")

print("\nPhase 10 frontend scaffold complete.")
