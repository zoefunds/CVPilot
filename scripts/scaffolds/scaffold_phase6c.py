"""
CVPilot Phase 6C: upload flow, applications list, status polling, evaluation display.
"""

from __future__ import annotations
from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
FILES: dict[str, str] = {}


# -----------------------------------------------------------------------------
# lib/types.ts (replaced with the full set)
# -----------------------------------------------------------------------------
FILES["frontend/src/lib/types.ts"] = '''export interface UserPublic {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_premium: boolean;
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
'''


# -----------------------------------------------------------------------------
# lib/api.ts (extended with applicationsApi)
# -----------------------------------------------------------------------------
FILES["frontend/src/lib/api.ts"] = '''import { apiBaseUrl } from './brand';
import { tokenStorage } from './authStorage';
import type {
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
    try {
      body = await res.json();
    } catch {
      body = null;
    }
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
    return api<ApplicationPublic>('/applications', {
      method: 'POST',
      body: fd,
    });
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
    return api<EvaluationPublic>(`/applications/${id}/evaluate`, {
      method: 'POST',
    });
  },
};
'''


# -----------------------------------------------------------------------------
# components/ui/Dropzone.tsx
# -----------------------------------------------------------------------------
FILES["frontend/src/components/ui/Dropzone.tsx"] = '''\'use client\';

import { DragEvent, useId, useRef, useState } from 'react';

interface Props {
  label: string;
  accept?: string;
  file: File | null;
  onFile: (file: File | null) => void;
  disabled?: boolean;
  helperText?: string;
}

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(2)} MB`;
}

export function Dropzone({
  label,
  accept = '.pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain',
  file,
  onFile,
  disabled,
  helperText,
}: Props) {
  const id = useId();
  const ref = useRef<HTMLInputElement | null>(null);
  const [over, setOver] = useState(false);

  function handleDrop(e: DragEvent<HTMLLabelElement>) {
    e.preventDefault();
    setOver(false);
    if (disabled) return;
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) onFile(dropped);
  }

  return (
    <div>
      <label
        htmlFor={id}
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setOver(true);
        }}
        onDragLeave={() => setOver(false)}
        onDrop={handleDrop}
        className={[
          'flex cursor-pointer flex-col items-start gap-2 rounded-2xl border border-dashed px-5 py-6 transition-colors',
          over
            ? 'border-[#2b4f3a] bg-[#2b4f3a]/5'
            : 'border-[#1a1814]/25 bg-white/40 hover:bg-white/60',
          disabled ? 'pointer-events-none opacity-60' : '',
        ].join(' ')}
      >
        <span className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">
          {label}
        </span>
        {file ? (
          <div className="flex w-full items-center justify-between gap-3">
            <div className="min-w-0">
              <p className="truncate font-medium text-[#1a1814]">{file.name}</p>
              <p className="text-xs text-[#3a342c]/70">
                {formatBytes(file.size)} \u00b7 {file.type || 'unknown type'}
              </p>
            </div>
            <button
              type="button"
              onClick={(e) => {
                e.preventDefault();
                onFile(null);
                if (ref.current) ref.current.value = '';
              }}
              className="rounded-full border border-[#1a1814]/30 px-3 py-1 text-xs text-[#1a1814] hover:bg-[#1a1814]/5"
            >
              Replace
            </button>
          </div>
        ) : (
          <div>
            <p className="text-[#1a1814]">
              Drop a file here, or click to choose.
            </p>
            <p className="mt-1 text-xs text-[#3a342c]/70">
              {helperText || 'PDF, DOCX, or TXT. Up to 10 MB.'}
            </p>
          </div>
        )}
        <input
          id={id}
          ref={ref}
          type="file"
          accept={accept}
          className="sr-only"
          disabled={disabled}
          onChange={(e) => onFile(e.target.files?.[0] ?? null)}
        />
      </label>
    </div>
  );
}
'''


# -----------------------------------------------------------------------------
# components/dashboard/StatusBadge.tsx
# -----------------------------------------------------------------------------
FILES["frontend/src/components/dashboard/StatusBadge.tsx"] = '''import type { ApplicationStatus } from '@/lib/types';

const labels: Record<ApplicationStatus, string> = {
  pending: 'Pending',
  processing: 'Processing',
  ready: 'Ready',
  evaluating: 'Evaluating',
  complete: 'Complete',
  failed: 'Failed',
};

const styles: Record<ApplicationStatus, string> = {
  pending: 'bg-[#1a1814]/8 text-[#3a342c]',
  processing: 'bg-[#a35f1f]/12 text-[#a35f1f]',
  ready: 'bg-[#2b4f3a]/10 text-[#2b4f3a]',
  evaluating: 'bg-[#a35f1f]/12 text-[#a35f1f]',
  complete: 'bg-[#2b4f3a]/15 text-[#1f3a2a]',
  failed: 'bg-[#9b2226]/12 text-[#9b2226]',
};

export function StatusBadge({ status }: { status: ApplicationStatus }) {
  const cls = styles[status] || styles.pending;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] uppercase tracking-[0.15em] ${cls}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {labels[status] || status}
    </span>
  );
}
'''


# -----------------------------------------------------------------------------
# components/dashboard/ApplicationsList.tsx
# -----------------------------------------------------------------------------
FILES["frontend/src/components/dashboard/ApplicationsList.tsx"] = '''\'use client\';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { StatusBadge } from '@/components/dashboard/StatusBadge';
import { ApiError, applicationsApi } from '@/lib/api';
import type { ApplicationListItem } from '@/lib/types';

function fmtDate(s: string): string {
  try {
    return new Date(s).toLocaleString();
  } catch {
    return s;
  }
}

function hostnameOf(url: string): string {
  try {
    return new URL(url).hostname;
  } catch {
    return url;
  }
}

export function ApplicationsList() {
  const [items, setItems] = useState<ApplicationListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const data = await applicationsApi.list();
        if (alive) setItems(data);
      } catch (e) {
        if (alive) {
          setError(e instanceof ApiError ? e.message : 'Could not load.');
        }
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  if (error) {
    return (
      <div className="rounded-2xl border border-[#9b2226]/30 bg-[#9b2226]/8 p-6 text-sm text-[#9b2226]">
        {error}
      </div>
    );
  }
  if (items === null) {
    return (
      <div className="rounded-2xl border border-dashed border-[#1a1814]/20 bg-white/40 p-10 text-center text-sm text-[#3a342c]">
        Loading your evaluations.
      </div>
    );
  }
  if (items.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-[#1a1814]/20 bg-white/40 p-10 text-center text-sm text-[#3a342c]">
        Your evaluation history will appear here once you run your first
        scoring pass.
      </div>
    );
  }
  return (
    <ul className="divide-y divide-[#d9d5c8] rounded-2xl border border-[#1a1814]/10 bg-white/40">
      {items.map((a) => (
        <li key={a.id}>
          <Link
            href={`/dashboard/applications/${a.id}`}
            className="flex flex-col gap-2 px-5 py-4 hover:bg-white/60 sm:flex-row sm:items-center sm:justify-between"
          >
            <div className="min-w-0">
              <p className="truncate font-medium text-[#1a1814]">
                {a.job_title || hostnameOf(a.job_url)}
              </p>
              <p className="truncate text-xs text-[#3a342c]/70">
                {a.job_url}
              </p>
            </div>
            <div className="flex items-center gap-4 text-xs text-[#3a342c]/80">
              <span>{fmtDate(a.created_at)}</span>
              <StatusBadge status={a.status} />
            </div>
          </Link>
        </li>
      ))}
    </ul>
  );
}
'''


# -----------------------------------------------------------------------------
# components/dashboard/ScoreCard.tsx
# -----------------------------------------------------------------------------
FILES["frontend/src/components/dashboard/ScoreCard.tsx"] = '''export function ScoreCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: number | null;
  hint?: string;
}) {
  const v = typeof value === 'number' ? value : 0;
  const shown = typeof value === 'number' ? value : '\u2014';
  const cls =
    v >= 75
      ? 'bg-[#2b4f3a]'
      : v >= 50
      ? 'bg-[#a35f1f]'
      : 'bg-[#9b2226]';
  return (
    <div className="rounded-2xl border border-[#1a1814]/10 bg-white/60 p-5">
      <div className="flex items-baseline justify-between">
        <span className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">
          {label}
        </span>
        <span className="font-serif text-3xl">{shown}</span>
      </div>
      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-[#1a1814]/10">
        <div
          className={`h-full ${cls}`}
          style={{ width: `${Math.max(0, Math.min(100, v))}%` }}
        />
      </div>
      {hint && (
        <p className="mt-2 text-[11px] leading-snug text-[#3a342c]/80">
          {hint}
        </p>
      )}
    </div>
  );
}
'''


# -----------------------------------------------------------------------------
# app/dashboard/page.tsx (updated to use real list)
# -----------------------------------------------------------------------------
FILES["frontend/src/app/dashboard/page.tsx"] = '''\'use client\';

import Link from 'next/link';
import { ApplicationsList } from '@/components/dashboard/ApplicationsList';
import { Container } from '@/components/ui/Container';
import { useAuth } from '@/contexts/AuthContext';

export default function DashboardPage() {
  const { user } = useAuth();
  const name = user?.full_name || user?.email?.split('@')[0] || 'there';

  return (
    <Container className="py-16">
      <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">
        Welcome back
      </p>
      <h1 className="mt-3 font-serif text-5xl sm:text-6xl">
        Hello, {name}.
      </h1>
      <p className="mt-4 max-w-2xl text-[#3a342c]">
        Drop your CV and a job URL and get a verifiable scoring report in
        under a minute.
      </p>

      <div className="mt-10 flex flex-wrap gap-3">
        <Link
          href="/dashboard/new"
          className="inline-flex items-center justify-center rounded-full bg-[#1a1814] px-6 py-3 text-sm font-medium text-[#efece4] hover:bg-[#3a342c]"
        >
          Start a new evaluation
        </Link>
      </div>

      <section className="mt-16">
        <div className="flex items-baseline justify-between">
          <h2 className="font-serif text-2xl">Recent applications</h2>
        </div>
        <div className="mt-5">
          <ApplicationsList />
        </div>
      </section>
    </Container>
  );
}
'''


# -----------------------------------------------------------------------------
# app/dashboard/new/page.tsx (upload flow)
# -----------------------------------------------------------------------------
FILES["frontend/src/app/dashboard/new/page.tsx"] = '''\'use client\';

import { useRouter } from 'next/navigation';
import { FormEvent, useState } from 'react';
import { Alert } from '@/components/ui/Alert';
import { Button } from '@/components/ui/Button';
import { Container } from '@/components/ui/Container';
import { Dropzone } from '@/components/ui/Dropzone';
import { Field } from '@/components/ui/Field';
import { Input } from '@/components/ui/Input';
import { ApiError, applicationsApi } from '@/lib/api';

export default function NewApplicationPage() {
  const router = useRouter();
  const [jobUrl, setJobUrl] = useState('');
  const [linkedinUrl, setLinkedinUrl] = useState('');
  const [portfolioUrl, setPortfolioUrl] = useState('');
  const [cv, setCv] = useState<File | null>(null);
  const [coverLetter, setCoverLetter] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (!cv) {
      setError('Please attach your CV.');
      return;
    }
    if (!coverLetter) {
      setError('Please attach your cover letter.');
      return;
    }
    if (!/^https?:\\/\\//i.test(jobUrl)) {
      setError('Job URL must start with http or https.');
      return;
    }

    setLoading(true);
    try {
      const app = await applicationsApi.create({
        job_url: jobUrl,
        linkedin_url: linkedinUrl || undefined,
        portfolio_url: portfolioUrl || undefined,
        cv,
        cover_letter: coverLetter,
      });
      router.push(`/dashboard/applications/${app.id}`);
    } catch (e) {
      if (e instanceof ApiError) setError(e.message);
      else setError('Submission failed. Try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <Container className="py-16">
      <div className="max-w-3xl">
        <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">
          New evaluation
        </p>
        <h1 className="mt-3 font-serif text-5xl">
          Grade your application.
        </h1>
        <p className="mt-4 max-w-2xl text-[#3a342c]">
          We parse your CV and cover letter, fetch the job posting, and run
          the full scoring pass. You will see live status while we work.
        </p>

        <form onSubmit={onSubmit} className="mt-10 flex flex-col gap-6">
          {error && <Alert tone="error">{error}</Alert>}

          <Field label="Job URL" hint="Paste the link to the job posting.">
            <Input
              type="url"
              value={jobUrl}
              onChange={(e) => setJobUrl(e.target.value)}
              required
              disabled={loading}
              placeholder="https://example.com/jobs/senior-engineer"
            />
          </Field>

          <div className="grid gap-5 sm:grid-cols-2">
            <Field
              label="LinkedIn"
              hint="Optional. Recruiters weight it."
            >
              <Input
                type="url"
                value={linkedinUrl}
                onChange={(e) => setLinkedinUrl(e.target.value)}
                disabled={loading}
                placeholder="https://www.linkedin.com/in/you/"
              />
            </Field>
            <Field
              label="Portfolio"
              hint="Optional. Useful for design or engineering roles."
            >
              <Input
                type="url"
                value={portfolioUrl}
                onChange={(e) => setPortfolioUrl(e.target.value)}
                disabled={loading}
                placeholder="https://your.portfolio.site"
              />
            </Field>
          </div>

          <div className="grid gap-5 sm:grid-cols-2">
            <Dropzone
              label="CV"
              file={cv}
              onFile={setCv}
              disabled={loading}
              helperText="PDF, DOCX, or TXT. Up to 10 MB."
            />
            <Dropzone
              label="Cover letter"
              file={coverLetter}
              onFile={setCoverLetter}
              disabled={loading}
              helperText="PDF, DOCX, or TXT. Up to 10 MB."
            />
          </div>

          <div>
            <Button type="submit" disabled={loading}>
              {loading ? 'Submitting...' : 'Run evaluation'}
            </Button>
          </div>
        </form>
      </div>
    </Container>
  );
}
'''


# -----------------------------------------------------------------------------
# app/dashboard/applications/[id]/page.tsx (polling + display)
# -----------------------------------------------------------------------------
FILES["frontend/src/app/dashboard/applications/[id]/page.tsx"] = '''\'use client\';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import { ScoreCard } from '@/components/dashboard/ScoreCard';
import { StatusBadge } from '@/components/dashboard/StatusBadge';
import { Alert } from '@/components/ui/Alert';
import { Container } from '@/components/ui/Container';
import { ApiError, applicationsApi } from '@/lib/api';
import type {
  ApplicationPublic,
  EvaluationPublic,
} from '@/lib/types';

function shortHash(h: string | null | undefined): string {
  if (!h) return '';
  if (h.length <= 14) return h;
  return `${h.slice(0, 8)}\u2026${h.slice(-6)}`;
}

export default function ApplicationDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id;

  const [app, setApp] = useState<ApplicationPublic | null>(null);
  const [evaluation, setEvaluation] = useState<EvaluationPublic | null>(null);
  const [error, setError] = useState<string | null>(null);
  const stopped = useRef(false);

  useEffect(() => {
    stopped.current = false;
    return () => {
      stopped.current = true;
    };
  }, []);

  useEffect(() => {
    if (!id) return;
    let timer: ReturnType<typeof setTimeout>;

    async function tick() {
      try {
        const a = await applicationsApi.get(id);
        if (stopped.current) return;
        setApp(a);

        if (a.status === 'complete' || a.status === 'failed') {
          try {
            const ev = await applicationsApi.getEvaluation(id);
            if (!stopped.current) setEvaluation(ev);
          } catch (e) {
            // 404 if no evaluation yet; ignore silently
            if (!(e instanceof ApiError && e.status === 404)) {
              throw e;
            }
          }
          return;
        }
        timer = setTimeout(tick, 4000);
      } catch (e) {
        if (e instanceof ApiError) setError(e.message);
        else setError('Could not load this application.');
      }
    }
    void tick();
    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [id]);

  if (error) {
    return (
      <Container className="py-16">
        <Alert tone="error">{error}</Alert>
        <p className="mt-6 text-sm">
          <Link href="/dashboard" className="underline">
            Back to dashboard
          </Link>
        </p>
      </Container>
    );
  }

  if (!app) {
    return (
      <Container className="py-16">
        <p className="text-sm text-[#3a342c]">Loading your evaluation.</p>
      </Container>
    );
  }

  const isWorking =
    app.status === 'pending' ||
    app.status === 'processing' ||
    app.status === 'evaluating' ||
    app.status === 'ready';

  return (
    <Container className="py-16">
      <div className="flex flex-wrap items-baseline justify-between gap-4">
        <div className="min-w-0">
          <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">
            Evaluation
          </p>
          <h1 className="mt-2 font-serif text-4xl sm:text-5xl">
            {app.job_title || 'Untitled posting'}
          </h1>
          <a
            href={app.job_url}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-2 inline-block max-w-full truncate text-sm text-[#3a342c]/80 hover:text-[#1a1814]"
          >
            {app.job_url}
          </a>
        </div>
        <StatusBadge status={app.status} />
      </div>

      {isWorking && (
        <div className="mt-10 rounded-2xl border border-[#1a1814]/15 bg-white/50 p-6 text-sm text-[#3a342c]">
          We are working on your evaluation. This page will update
          automatically.
        </div>
      )}

      {app.status === 'failed' && (
        <Alert tone="error">
          <div>
            <p className="font-medium">Evaluation failed.</p>
            {app.error && (
              <p className="mt-1 text-xs">{app.error}</p>
            )}
          </div>
        </Alert>
      )}

      {evaluation && evaluation.status === 'complete' && (
        <EvaluationView ev={evaluation} app={app} />
      )}

      <div className="mt-12">
        <Link
          href="/dashboard"
          className="text-sm text-[#3a342c] underline underline-offset-4 hover:text-[#1a1814]"
        >
          Back to dashboard
        </Link>
      </div>
    </Container>
  );
}


function EvaluationView({
  ev,
  app,
}: {
  ev: EvaluationPublic;
  app: ApplicationPublic;
}) {
  const tx = ev.contract_tx_hash;
  const cv = app.files.find((f) => f.kind === 'cv');
  const cl = app.files.find((f) => f.kind === 'cover_letter');

  return (
    <div className="mt-10 flex flex-col gap-10">
      <section>
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">
              Competitiveness
            </p>
            <p className="mt-1 font-serif text-7xl">
              {ev.competitiveness_score ?? '\u2014'}
            </p>
            <p className="text-xs text-[#3a342c]/70">/ 100</p>
          </div>
          {tx ? (
            <a
              href={`https://studio.genlayer.com/?tx=${tx}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex flex-col items-end rounded-2xl border border-[#2b4f3a]/30 bg-[#2b4f3a]/8 px-4 py-3 text-right transition-colors hover:bg-[#2b4f3a]/15"
            >
              <span className="text-[10px] uppercase tracking-[0.18em] text-[#2b4f3a]">
                Verified on StudioNet
              </span>
              <span className="mt-1 font-mono text-xs text-[#2b4f3a]">
                {shortHash(tx)}
              </span>
            </a>
          ) : (
            <span className="rounded-2xl border border-[#1a1814]/15 bg-white/50 px-3 py-2 text-[10px] uppercase tracking-[0.18em] text-[#3a342c]/80">
              Scored locally
            </span>
          )}
        </div>
        {ev.summary && (
          <p className="mt-6 max-w-3xl text-[#3a342c]">{ev.summary}</p>
        )}
      </section>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <ScoreCard label="CV" value={ev.cv_score} />
        <ScoreCard label="Cover letter" value={ev.cover_letter_score} />
        <ScoreCard label="Job match" value={ev.job_match_score} />
        <ScoreCard label="ATS" value={ev.ats_score} />
      </section>

      {ev.recommendations.length > 0 && (
        <section>
          <h2 className="font-serif text-2xl">Recommendations</h2>
          <ul className="mt-4 grid gap-3">
            {ev.recommendations.map((r, i) => (
              <li
                key={i}
                className="rounded-2xl border border-[#1a1814]/10 bg-white/60 p-4 text-sm text-[#1a1814]"
              >
                {r}
              </li>
            ))}
          </ul>
        </section>
      )}

      {ev.missing_keywords.length > 0 && (
        <section>
          <h2 className="font-serif text-2xl">Missing keywords</h2>
          <div className="mt-4 flex flex-wrap gap-2">
            {ev.missing_keywords.map((kw) => (
              <span
                key={kw}
                className="rounded-full border border-[#1a1814]/15 bg-white/60 px-3 py-1 text-xs text-[#1a1814]"
              >
                {kw}
              </span>
            ))}
          </div>
        </section>
      )}

      {ev.weak_statements.length > 0 && (
        <section>
          <h2 className="font-serif text-2xl">Weak statements</h2>
          <ul className="mt-4 grid gap-3">
            {ev.weak_statements.map((w, i) => (
              <li
                key={i}
                className="rounded-2xl border border-[#a35f1f]/30 bg-[#a35f1f]/8 p-4 text-sm text-[#a35f1f]"
              >
                {w}
              </li>
            ))}
          </ul>
        </section>
      )}

      {ev.company_alignment_notes.length > 0 && (
        <section>
          <h2 className="font-serif text-2xl">Company alignment</h2>
          <ul className="mt-4 grid gap-3">
            {ev.company_alignment_notes.map((c, i) => (
              <li
                key={i}
                className="rounded-2xl border border-[#1a1814]/10 bg-white/60 p-4 text-sm text-[#1a1814]"
              >
                {c}
              </li>
            ))}
          </ul>
        </section>
      )}

      {(cv || cl) && (
        <section>
          <h2 className="font-serif text-2xl">Files</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            {cv && <FileSummary kind="CV" file={cv} />}
            {cl && <FileSummary kind="Cover letter" file={cl} />}
          </div>
        </section>
      )}
    </div>
  );
}

function FileSummary({
  kind,
  file,
}: {
  kind: string;
  file: { original_filename: string; detected_kind: string | null; byte_size: number };
}) {
  return (
    <div className="rounded-2xl border border-[#1a1814]/10 bg-white/60 p-5">
      <p className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">
        {kind}
      </p>
      <p className="mt-2 truncate font-medium text-[#1a1814]">
        {file.original_filename}
      </p>
      <p className="mt-1 text-xs text-[#3a342c]/70">
        {(file.detected_kind || 'unknown').toUpperCase()} \u00b7{' '}
        {(file.byte_size / 1024).toFixed(1)} KB
      </p>
    </div>
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

print("\nPhase 6C files written.")
