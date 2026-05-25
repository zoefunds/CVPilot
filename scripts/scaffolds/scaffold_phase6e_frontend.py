"""
CVPilot Phase 6E frontend: admin guard, navigation, overview, users, applications.
"""

from __future__ import annotations
from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
FILES: dict[str, str] = {}


# -----------------------------------------------------------------------------
# lib/types.ts (re-write including is_superuser + admin types)
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# lib/api.ts (extended with adminApi)
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# components/auth/AdminGuard.tsx
# -----------------------------------------------------------------------------
FILES["frontend/src/components/auth/AdminGuard.tsx"] = '''\'use client\';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

export function AdminGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, isLoading, isAuthenticated } = useAuth();

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      router.replace('/signin');
    } else if (!user?.is_superuser) {
      router.replace('/dashboard');
    }
  }, [isAuthenticated, isLoading, user, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-sm text-[#3a342c]">
        Checking permissions.
      </div>
    );
  }
  if (!isAuthenticated || !user?.is_superuser) {
    return null;
  }
  return <>{children}</>;
}
'''


# -----------------------------------------------------------------------------
# components/dashboard/DashboardShell.tsx (conditional Admin link)
# -----------------------------------------------------------------------------
FILES["frontend/src/components/dashboard/DashboardShell.tsx"] = '''\'use client\';

import Link from 'next/link';
import { Container } from '@/components/ui/Container';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/contexts/ToastContext';
import { appName } from '@/lib/brand';

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const { user, signOut } = useAuth();
  const { push } = useToast();
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-20 border-b border-[#d9d5c8] bg-[#efece4]/85 backdrop-blur supports-[backdrop-filter]:bg-[#efece4]/70">
        <Container className="flex h-16 items-center justify-between gap-3">
          <Link href="/dashboard" className="font-serif text-2xl">
            {appName}
          </Link>
          <nav className="flex items-center gap-3 text-sm sm:gap-5">
            <Link
              href="/dashboard"
              className="hidden text-[#3a342c] hover:text-[#1a1814] sm:inline"
            >
              Dashboard
            </Link>
            <Link
              href="/dashboard/new"
              className="text-[#3a342c] hover:text-[#1a1814]"
            >
              New
            </Link>
            <Link
              href="/dashboard/settings"
              className="text-[#3a342c] hover:text-[#1a1814]"
            >
              Settings
            </Link>
            {user?.is_superuser && (
              <Link
                href="/dashboard/admin"
                className="inline-flex items-center gap-1.5 rounded-full bg-[#2b4f3a]/12 px-2.5 py-1 text-xs uppercase tracking-[0.15em] text-[#2b4f3a] hover:bg-[#2b4f3a]/20"
              >
                <span className="h-1.5 w-1.5 rounded-full bg-[#2b4f3a]" />
                Admin
              </Link>
            )}
            <span className="hidden max-w-[16ch] truncate text-[#3a342c]/60 lg:inline">
              {user?.email}
            </span>
            <button
              type="button"
              onClick={() => {
                signOut();
                push({ tone: 'info', title: 'Signed out' });
              }}
              className="rounded-full border border-[#1a1814]/30 px-3 py-1.5 text-xs text-[#1a1814] hover:bg-[#1a1814]/5"
            >
              Sign out
            </button>
          </nav>
        </Container>
      </header>
      <main className="flex-1">{children}</main>
    </div>
  );
}
'''


# -----------------------------------------------------------------------------
# app/dashboard/admin/layout.tsx
# -----------------------------------------------------------------------------
FILES["frontend/src/app/dashboard/admin/layout.tsx"] = '''\'use client\';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { AdminGuard } from '@/components/auth/AdminGuard';
import { Container } from '@/components/ui/Container';

function NavLink({ href, label }: { href: string; label: string }) {
  const pathname = usePathname();
  const active = pathname === href || pathname?.startsWith(href + '/');
  return (
    <Link
      href={href}
      className={[
        'rounded-full px-3 py-1.5 text-xs uppercase tracking-[0.15em] transition-colors',
        active
          ? 'bg-[#1a1814] text-[#efece4]'
          : 'text-[#3a342c] hover:bg-[#1a1814]/5',
      ].join(' ')}
    >
      {label}
    </Link>
  );
}

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <AdminGuard>
      <div className="border-b border-[#d9d5c8] bg-[#efece4]/70">
        <Container className="flex flex-wrap items-center gap-2 py-3">
          <NavLink href="/dashboard/admin" label="Overview" />
          <NavLink href="/dashboard/admin/users" label="Users" />
          <NavLink href="/dashboard/admin/applications" label="Applications" />
        </Container>
      </div>
      {children}
    </AdminGuard>
  );
}
'''


# -----------------------------------------------------------------------------
# app/dashboard/admin/page.tsx (overview)
# -----------------------------------------------------------------------------
FILES["frontend/src/app/dashboard/admin/page.tsx"] = '''\'use client\';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { StatusBadge } from '@/components/dashboard/StatusBadge';
import { Alert } from '@/components/ui/Alert';
import { Container } from '@/components/ui/Container';
import { ApiError, adminApi } from '@/lib/api';
import type {
  AdminApplicationListItem,
  AdminStats,
  AdminUserListItem,
  ApplicationStatus,
} from '@/lib/types';

function StatTile({
  label,
  value,
  hint,
}: {
  label: string;
  value: string | number;
  hint?: string;
}) {
  return (
    <div className="rounded-2xl border border-[#1a1814]/10 bg-white/60 p-5">
      <p className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">
        {label}
      </p>
      <p className="mt-2 font-serif text-4xl text-[#1a1814]">{value}</p>
      {hint && <p className="mt-1 text-xs text-[#3a342c]/70">{hint}</p>}
    </div>
  );
}

export default function AdminOverviewPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<AdminUserListItem[] | null>(null);
  const [apps, setApps] = useState<AdminApplicationListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const [s, u, a] = await Promise.all([
          adminApi.stats(),
          adminApi.listUsers(5, 0),
          adminApi.listApplications({ limit: 5 }),
        ]);
        if (!alive) return;
        setStats(s);
        setUsers(u);
        setApps(a);
      } catch (e) {
        if (!alive) return;
        setError(e instanceof ApiError ? e.message : 'Could not load admin data.');
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  return (
    <Container className="py-14">
      <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">
        Admin
      </p>
      <h1 className="mt-2 font-serif text-5xl">Overview.</h1>

      {error && (
        <div className="mt-6">
          <Alert tone="error">{error}</Alert>
        </div>
      )}

      <section className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile label="Users" value={stats?.user_count ?? '\u2014'} hint={`+${stats?.last_24h_users ?? 0} last 24h`} />
        <StatTile label="Applications" value={stats?.application_count ?? '\u2014'} hint={`+${stats?.last_24h_applications ?? 0} last 24h`} />
        <StatTile label="Evaluations complete" value={stats?.evaluations_complete ?? '\u2014'} />
        <StatTile label="Evaluations failed" value={stats?.evaluations_failed ?? '\u2014'} />
      </section>

      {stats?.by_status && Object.keys(stats.by_status).length > 0 && (
        <section className="mt-10">
          <h2 className="font-serif text-2xl">Applications by status</h2>
          <div className="mt-4 flex flex-wrap gap-3">
            {Object.entries(stats.by_status).map(([s, n]) => (
              <div
                key={s}
                className="flex items-center gap-3 rounded-full border border-[#1a1814]/10 bg-white/60 px-3 py-1.5"
              >
                <StatusBadge status={s as ApplicationStatus} />
                <span className="text-sm text-[#1a1814]">{n}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="mt-12">
        <div className="flex items-baseline justify-between">
          <h2 className="font-serif text-2xl">Recent users</h2>
          <Link
            href="/dashboard/admin/users"
            className="text-xs uppercase tracking-[0.15em] text-[#3a342c] hover:text-[#1a1814]"
          >
            See all
          </Link>
        </div>
        <div className="mt-4 overflow-hidden rounded-2xl border border-[#1a1814]/10 bg-white/40">
          {users === null ? (
            <p className="p-6 text-sm text-[#3a342c]">Loading.</p>
          ) : users.length === 0 ? (
            <p className="p-6 text-sm text-[#3a342c]">No users yet.</p>
          ) : (
            <ul className="divide-y divide-[#d9d5c8]">
              {users.map((u) => (
                <li
                  key={u.id}
                  className="flex flex-wrap items-center justify-between gap-3 px-5 py-3"
                >
                  <div className="min-w-0">
                    <p className="truncate font-medium text-[#1a1814]">
                      {u.email}
                    </p>
                    <p className="truncate text-xs text-[#3a342c]/70">
                      {u.full_name || 'No name'} \u00b7 {u.application_count} application
                      {u.application_count === 1 ? '' : 's'}
                    </p>
                  </div>
                  {u.is_superuser && (
                    <span className="rounded-full bg-[#2b4f3a]/12 px-2.5 py-0.5 text-[10px] uppercase tracking-[0.15em] text-[#2b4f3a]">
                      Admin
                    </span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      <section className="mt-12">
        <div className="flex items-baseline justify-between">
          <h2 className="font-serif text-2xl">Recent applications</h2>
          <Link
            href="/dashboard/admin/applications"
            className="text-xs uppercase tracking-[0.15em] text-[#3a342c] hover:text-[#1a1814]"
          >
            See all
          </Link>
        </div>
        <div className="mt-4 overflow-hidden rounded-2xl border border-[#1a1814]/10 bg-white/40">
          {apps === null ? (
            <p className="p-6 text-sm text-[#3a342c]">Loading.</p>
          ) : apps.length === 0 ? (
            <p className="p-6 text-sm text-[#3a342c]">No applications yet.</p>
          ) : (
            <ul className="divide-y divide-[#d9d5c8]">
              {apps.map((a) => (
                <li key={a.id}>
                  <Link
                    href={`/dashboard/admin/applications/${a.id}`}
                    className="flex flex-wrap items-center justify-between gap-3 px-5 py-3 hover:bg-white/60"
                  >
                    <div className="min-w-0">
                      <p className="truncate font-medium text-[#1a1814]">
                        {a.job_title || a.job_url}
                      </p>
                      <p className="truncate text-xs text-[#3a342c]/70">
                        {a.user_email}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      {a.competitiveness !== null && (
                        <span className="font-serif text-lg text-[#1a1814]">
                          {a.competitiveness}
                          <span className="text-xs text-[#3a342c]/60">/100</span>
                        </span>
                      )}
                      <StatusBadge status={a.status} />
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>
    </Container>
  );
}
'''


# -----------------------------------------------------------------------------
# app/dashboard/admin/users/page.tsx (full users table)
# -----------------------------------------------------------------------------
FILES["frontend/src/app/dashboard/admin/users/page.tsx"] = '''\'use client\';

import { useEffect, useState } from 'react';
import { Alert } from '@/components/ui/Alert';
import { Container } from '@/components/ui/Container';
import { useToast } from '@/contexts/ToastContext';
import { ApiError, adminApi } from '@/lib/api';
import type { AdminUserListItem } from '@/lib/types';

function fmt(s: string | null | undefined): string {
  if (!s) return '\u2014';
  try {
    return new Date(s).toLocaleString();
  } catch {
    return s;
  }
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUserListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { push } = useToast();

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const u = await adminApi.listUsers(200);
        if (alive) setUsers(u);
      } catch (e) {
        if (alive) setError(e instanceof ApiError ? e.message : 'Could not load.');
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  async function copy(v: string, label: string) {
    try {
      await navigator.clipboard.writeText(v);
      push({ tone: 'success', title: 'Copied', message: `${label} on clipboard.` });
    } catch {
      push({ tone: 'error', title: 'Could not copy.' });
    }
  }

  return (
    <Container className="py-14">
      <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">Admin</p>
      <h1 className="mt-2 font-serif text-5xl">All users.</h1>

      {error && (
        <div className="mt-6">
          <Alert tone="error">{error}</Alert>
        </div>
      )}

      <div className="mt-8 overflow-hidden rounded-2xl border border-[#1a1814]/10 bg-white/40">
        {users === null ? (
          <p className="p-6 text-sm text-[#3a342c]">Loading.</p>
        ) : users.length === 0 ? (
          <p className="p-6 text-sm text-[#3a342c]">No users yet.</p>
        ) : (
          <ul className="divide-y divide-[#d9d5c8]">
            {users.map((u) => (
              <li key={u.id} className="px-5 py-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="truncate font-medium text-[#1a1814]">
                        {u.email}
                      </p>
                      {u.is_superuser && (
                        <span className="rounded-full bg-[#2b4f3a]/12 px-2 py-0.5 text-[10px] uppercase tracking-[0.15em] text-[#2b4f3a]">
                          Admin
                        </span>
                      )}
                      {!u.is_active && (
                        <span className="rounded-full bg-[#9b2226]/12 px-2 py-0.5 text-[10px] uppercase tracking-[0.15em] text-[#9b2226]">
                          Disabled
                        </span>
                      )}
                    </div>
                    <p className="mt-0.5 text-xs text-[#3a342c]/70">
                      {u.full_name || 'No name'}
                    </p>
                    <p className="mt-2 font-mono text-[10px] text-[#3a342c]/60">
                      {u.id}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-1 text-xs text-[#3a342c]">
                    <span>{u.application_count} applications</span>
                    <span className="text-[#3a342c]/70">
                      Joined {fmt(u.created_at)}
                    </span>
                    <span className="text-[#3a342c]/70">
                      Last app {fmt(u.last_application_at)}
                    </span>
                    <div className="mt-1 flex gap-2">
                      <button
                        type="button"
                        onClick={() => copy(u.email, 'Email')}
                        className="rounded-full border border-[#1a1814]/20 px-2.5 py-0.5 text-[10px] uppercase tracking-[0.15em] text-[#1a1814] hover:bg-[#1a1814]/5"
                      >
                        Copy email
                      </button>
                      <button
                        type="button"
                        onClick={() => copy(u.id, 'Account ID')}
                        className="rounded-full border border-[#1a1814]/20 px-2.5 py-0.5 text-[10px] uppercase tracking-[0.15em] text-[#1a1814] hover:bg-[#1a1814]/5"
                      >
                        Copy ID
                      </button>
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Container>
  );
}
'''


# -----------------------------------------------------------------------------
# app/dashboard/admin/applications/page.tsx (all apps with filter)
# -----------------------------------------------------------------------------
FILES["frontend/src/app/dashboard/admin/applications/page.tsx"] = '''\'use client\';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { StatusBadge } from '@/components/dashboard/StatusBadge';
import { Alert } from '@/components/ui/Alert';
import { Container } from '@/components/ui/Container';
import { ApiError, adminApi } from '@/lib/api';
import type {
  AdminApplicationListItem,
  ApplicationStatus,
} from '@/lib/types';

const STATUS_OPTIONS: { value: '' | ApplicationStatus; label: string }[] = [
  { value: '', label: 'All' },
  { value: 'pending', label: 'Pending' },
  { value: 'processing', label: 'Processing' },
  { value: 'ready', label: 'Ready' },
  { value: 'evaluating', label: 'Evaluating' },
  { value: 'complete', label: 'Complete' },
  { value: 'failed', label: 'Failed' },
];

function fmt(s: string): string {
  try {
    return new Date(s).toLocaleString();
  } catch {
    return s;
  }
}

export default function AdminApplicationsPage() {
  const [status, setStatus] = useState<'' | ApplicationStatus>('');
  const [apps, setApps] = useState<AdminApplicationListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    setApps(null);
    setError(null);
    (async () => {
      try {
        const items = await adminApi.listApplications({
          status: status || undefined,
          limit: 200,
        });
        if (alive) setApps(items);
      } catch (e) {
        if (alive) setError(e instanceof ApiError ? e.message : 'Could not load.');
      }
    })();
    return () => {
      alive = false;
    };
  }, [status]);

  return (
    <Container className="py-14">
      <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">Admin</p>
      <h1 className="mt-2 font-serif text-5xl">All applications.</h1>

      <div className="mt-8 flex flex-wrap items-center gap-2">
        {STATUS_OPTIONS.map((opt) => (
          <button
            key={opt.value || 'all'}
            type="button"
            onClick={() => setStatus(opt.value)}
            className={[
              'rounded-full px-3 py-1.5 text-xs uppercase tracking-[0.15em] transition-colors',
              status === opt.value
                ? 'bg-[#1a1814] text-[#efece4]'
                : 'border border-[#1a1814]/20 text-[#1a1814] hover:bg-[#1a1814]/5',
            ].join(' ')}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="mt-6">
          <Alert tone="error">{error}</Alert>
        </div>
      )}

      <div className="mt-6 overflow-hidden rounded-2xl border border-[#1a1814]/10 bg-white/40">
        {apps === null ? (
          <p className="p-6 text-sm text-[#3a342c]">Loading.</p>
        ) : apps.length === 0 ? (
          <p className="p-6 text-sm text-[#3a342c]">No applications match.</p>
        ) : (
          <ul className="divide-y divide-[#d9d5c8]">
            {apps.map((a) => (
              <li key={a.id}>
                <Link
                  href={`/dashboard/admin/applications/${a.id}`}
                  className="flex flex-wrap items-center justify-between gap-3 px-5 py-4 hover:bg-white/60"
                >
                  <div className="min-w-0">
                    <p className="truncate font-medium text-[#1a1814]">
                      {a.job_title || a.job_url}
                    </p>
                    <p className="truncate text-xs text-[#3a342c]/70">
                      {a.user_email} \u00b7 {fmt(a.created_at)}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 text-xs">
                    {a.competitiveness !== null && (
                      <span className="font-serif text-lg text-[#1a1814]">
                        {a.competitiveness}
                        <span className="text-[10px] text-[#3a342c]/60">/100</span>
                      </span>
                    )}
                    <StatusBadge status={a.status} />
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Container>
  );
}
'''


# -----------------------------------------------------------------------------
# app/dashboard/admin/applications/[id]/page.tsx
# -----------------------------------------------------------------------------
FILES["frontend/src/app/dashboard/admin/applications/[id]/page.tsx"] = '''\'use client\';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ScoreGauge } from '@/components/ui/ScoreGauge';
import { StatusBadge } from '@/components/dashboard/StatusBadge';
import { Alert } from '@/components/ui/Alert';
import { Container } from '@/components/ui/Container';
import { ApiError, adminApi } from '@/lib/api';
import type {
  ApplicationPublic,
  EvaluationPublic,
} from '@/lib/types';

function shortHash(h: string | null | undefined): string {
  if (!h) return '';
  if (h.length <= 14) return h;
  return `${h.slice(0, 8)}\u2026${h.slice(-6)}`;
}

function fmt(s: string): string {
  try {
    return new Date(s).toLocaleString();
  } catch {
    return s;
  }
}

export default function AdminApplicationDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id;
  const [app, setApp] = useState<ApplicationPublic | null>(null);
  const [evaluation, setEvaluation] = useState<EvaluationPublic | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    let alive = true;
    (async () => {
      try {
        const a = await adminApi.getApplication(id);
        if (!alive) return;
        setApp(a);
        try {
          const ev = await adminApi.getEvaluation(id);
          if (alive) setEvaluation(ev);
        } catch (e) {
          if (!(e instanceof ApiError && e.status === 404)) {
            throw e;
          }
        }
      } catch (e) {
        if (alive) setError(e instanceof ApiError ? e.message : 'Could not load.');
      }
    })();
    return () => {
      alive = false;
    };
  }, [id]);

  if (error) {
    return (
      <Container className="py-14">
        <Alert tone="error">{error}</Alert>
        <p className="mt-6 text-sm">
          <Link href="/dashboard/admin/applications" className="underline">
            Back to applications
          </Link>
        </p>
      </Container>
    );
  }

  if (!app) {
    return (
      <Container className="py-14">
        <p className="text-sm text-[#3a342c]">Loading.</p>
      </Container>
    );
  }

  const tx = evaluation?.contract_tx_hash;

  return (
    <Container className="py-14">
      <Link
        href="/dashboard/admin/applications"
        className="text-xs uppercase tracking-[0.15em] text-[#3a342c] hover:text-[#1a1814]"
      >
        \u2190 All applications
      </Link>

      <div className="mt-4 flex flex-wrap items-baseline justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">
            Admin view
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

      <section className="mt-8 grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-[#1a1814]/10 bg-white/60 p-4">
          <p className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">User ID</p>
          <p className="mt-1 break-all font-mono text-xs text-[#1a1814]">{app.user_id}</p>
        </div>
        <div className="rounded-2xl border border-[#1a1814]/10 bg-white/60 p-4">
          <p className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">Created</p>
          <p className="mt-1 text-sm text-[#1a1814]">{fmt(app.created_at)}</p>
        </div>
        <div className="rounded-2xl border border-[#1a1814]/10 bg-white/60 p-4">
          <p className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">Updated</p>
          <p className="mt-1 text-sm text-[#1a1814]">{fmt(app.updated_at)}</p>
        </div>
      </section>

      {app.status === 'failed' && app.error && (
        <div className="mt-8">
          <Alert tone="error">
            <p className="font-medium">Failure reason</p>
            <p className="mt-1 text-xs">{app.error}</p>
          </Alert>
        </div>
      )}

      {evaluation && evaluation.status === 'complete' && (
        <section className="mt-10 rounded-3xl border border-[#1a1814]/10 bg-white/55 p-8">
          <div className="grid items-center gap-10 lg:grid-cols-12">
            <div className="lg:col-span-5">
              <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">
                Competitiveness
              </p>
              <p className="mt-2 font-serif text-7xl text-[#1a1814]">
                {evaluation.competitiveness_score ?? '\u2014'}
              </p>
              <p className="text-xs text-[#3a342c]/70">/ 100</p>
              {tx ? (
                <span className="mt-5 inline-flex flex-col rounded-2xl border border-[#2b4f3a]/30 bg-[#2b4f3a]/10 px-4 py-3">
                  <span className="text-[10px] uppercase tracking-[0.18em] text-[#2b4f3a]">
                    Verified on StudioNet
                  </span>
                  <span className="mt-1 font-mono text-xs text-[#2b4f3a]">
                    {shortHash(tx)}
                  </span>
                </span>
              ) : (
                <span className="mt-5 inline-block rounded-2xl border border-[#1a1814]/15 bg-white/60 px-3 py-2 text-[10px] uppercase tracking-[0.18em] text-[#3a342c]/80">
                  Scored locally
                </span>
              )}
            </div>
            <div className="lg:col-span-7">
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                <ScoreGauge label="CV" value={evaluation.cv_score} />
                <ScoreGauge label="Cover letter" value={evaluation.cover_letter_score} />
                <ScoreGauge label="Job match" value={evaluation.job_match_score} />
                <ScoreGauge label="ATS" value={evaluation.ats_score} />
              </div>
            </div>
          </div>
          {evaluation.summary && (
            <p className="mt-8 border-t border-[#1a1814]/10 pt-6 text-[#3a342c]">
              {evaluation.summary}
            </p>
          )}
        </section>
      )}

      {evaluation && evaluation.recommendations.length > 0 && (
        <section className="mt-10">
          <h2 className="font-serif text-2xl">Recommendations</h2>
          <ul className="mt-4 grid gap-3">
            {evaluation.recommendations.map((r, i) => (
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
    </Container>
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

print("\nFrontend Phase 6E files written.")
