"""
Phase 9 frontend: UserPublic gains wallet_address, walletApi added,
Settings page shows the wallet card with live balance + export, /dashboard/new
catches 402 insufficient_balance and shows a top-up panel.
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


# Append walletApi
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

export const walletApi = {
  get(): Promise<WalletPublic> {
    return api<WalletPublic>('/auth/wallet');
  },
  export(): Promise<WalletExport> {
    return api<WalletExport>('/auth/wallet/export', { method: 'POST' });
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
  stats(): Promise<AdminStats> { return api<AdminStats>('/admin/stats'); },
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


FILES["frontend/src/components/dashboard/WalletCard.tsx"] = '''\'use client\';

import { useEffect, useState } from 'react';
import { ApiError, walletApi } from '@/lib/api';
import { useToast } from '@/contexts/ToastContext';
import type { WalletPublic } from '@/lib/types';

export function WalletCard() {
  const [wallet, setWallet] = useState<WalletPublic | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [revealed, setRevealed] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const { push } = useToast();

  async function load() {
    try {
      const w = await walletApi.get();
      setWallet(w);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not load wallet.');
    }
  }

  useEffect(() => { void load(); }, []);

  async function copy(text: string, label: string) {
    try {
      await navigator.clipboard.writeText(text);
      push({ tone: 'success', title: 'Copied.', message: label });
    } catch {
      push({ tone: 'error', title: 'Could not copy.' });
    }
  }

  async function exportKey() {
    if (revealed) { setRevealed(null); return; }
    setExporting(true);
    try {
      const x = await walletApi.export();
      setRevealed(x.private_key);
      push({
        tone: 'info',
        title: 'Private key revealed.',
        message: 'Save it offline. CVPilot will never ask for it.',
      });
    } catch (e) {
      push({
        tone: 'error',
        title: 'Could not export.',
        message: e instanceof ApiError ? e.message : undefined,
      });
    } finally {
      setExporting(false);
    }
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-[#9b2226]/30 bg-[#9b2226]/10 p-5 text-sm text-[#9b2226]">
        {error}
      </div>
    );
  }

  if (!wallet) {
    return (
      <div className="rounded-2xl border border-[#1a1814]/10 bg-white/50 p-5 text-sm text-[#3a342c]">
        Loading wallet.
      </div>
    );
  }

  const lowBalance = wallet.balance_wei < 500_000_000_000_000_000; // 0.5 GEN

  return (
    <div className="rounded-2xl border border-[#1a1814]/10 bg-white/60 p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <h2 className="font-serif text-2xl">Your GenLayer wallet.</h2>
        <span className="rounded-full bg-[#2b4f3a]/10 px-3 py-1 text-[10px] uppercase tracking-[0.15em] text-[#2b4f3a]">
          StudioNet
        </span>
      </div>
      <p className="mt-2 text-sm text-[#3a342c]">
        This wallet signs your on-chain evaluations. You need GEN here for
        validators to run the LLM. Fund it on the StudioNet faucet using the
        address below.
      </p>

      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-[#1a1814]/10 bg-[#efece4]/60 p-4">
          <p className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">
            Address
          </p>
          <p className="mt-2 break-all font-mono text-xs text-[#1a1814]">
            {wallet.address}
          </p>
          <button
            type="button"
            onClick={() => copy(wallet.address, 'Wallet address')}
            className="mt-3 rounded-full border border-[#1a1814]/20 px-3 py-1 text-xs hover:bg-[#1a1814]/5"
          >
            Copy address
          </button>
        </div>

        <div className="rounded-xl border border-[#1a1814]/10 bg-[#efece4]/60 p-4">
          <p className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">
            Balance
          </p>
          <p className="mt-2 font-serif text-3xl text-[#1a1814]">
            {wallet.balance_gen}
            <span className="ml-1 text-xs text-[#3a342c]/70">GEN</span>
          </p>
          <button
            type="button"
            onClick={load}
            className="mt-3 rounded-full border border-[#1a1814]/20 px-3 py-1 text-xs hover:bg-[#1a1814]/5"
          >
            Refresh
          </button>
          {lowBalance && (
            <p className="mt-3 rounded-lg bg-[#a35f1f]/10 px-2.5 py-1.5 text-[11px] text-[#a35f1f]">
              Balance is too low to run an evaluation. Fund the wallet on the
              StudioNet faucet.
            </p>
          )}
        </div>
      </div>

      <div className="mt-5 flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={exportKey}
          disabled={exporting}
          className="rounded-full border border-[#1a1814]/30 px-4 py-2 text-sm text-[#1a1814] hover:bg-[#1a1814]/5 disabled:opacity-60"
        >
          {revealed ? 'Hide private key' : exporting ? 'Working...' : 'Export private key'}
        </button>
        <span className="text-xs text-[#3a342c]/70">
          Audited. Treat the key like a password.
        </span>
      </div>

      {revealed && (
        <div className="mt-4 rounded-xl border border-[#9b2226]/30 bg-[#9b2226]/8 p-4">
          <p className="text-[10px] uppercase tracking-[0.15em] text-[#9b2226]">
            Private key
          </p>
          <p className="mt-2 break-all font-mono text-xs text-[#9b2226]">
            {revealed}
          </p>
          <button
            type="button"
            onClick={() => copy(revealed, 'Private key')}
            className="mt-3 rounded-full border border-[#9b2226]/30 px-3 py-1 text-xs text-[#9b2226] hover:bg-[#9b2226]/15"
          >
            Copy private key
          </button>
          <p className="mt-3 text-[11px] text-[#3a342c]">
            Save this securely. Anyone who has it can move every GEN in this
            wallet. CVPilot will never ask you for it.
          </p>
        </div>
      )}
    </div>
  );
}
'''


# Replace settings page to mount the WalletCard
FILES["frontend/src/app/dashboard/settings/page.tsx"] = '''\'use client\';

import { useState } from 'react';
import { Alert } from '@/components/ui/Alert';
import { Container } from '@/components/ui/Container';
import { WalletCard } from '@/components/dashboard/WalletCard';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/contexts/ToastContext';

function fmtDate(s: string | undefined): string {
  if (!s) return '\u2014';
  try { return new Date(s).toLocaleString(); } catch { return s; }
}

export default function SettingsPage() {
  const { user, signOut } = useAuth();
  const { push } = useToast();
  const [confirming, setConfirming] = useState(false);

  async function copy(text: string, label: string) {
    try {
      await navigator.clipboard.writeText(text);
      push({ tone: 'success', title: 'Copied', message: `${label} on clipboard.` });
    } catch {
      push({ tone: 'error', title: 'Could not copy', message: 'Browser blocked clipboard access.' });
    }
  }

  return (
    <Container className="py-16">
      <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">Settings</p>
      <h1 className="mt-3 font-serif text-5xl">Your account.</h1>

      <section className="mt-10">
        <WalletCard />
      </section>

      <section className="mt-12 grid gap-6 sm:grid-cols-2">
        <Row label="Email" value={user?.email || ''} onCopy={() => copy(user?.email || '', 'Email')} />
        <Row label="Full name" value={user?.full_name || 'Not set'} />
        <Row label="Account ID" value={user?.id || ''} mono onCopy={() => copy(user?.id || '', 'Account ID')} />
        <Row label="Member since" value={fmtDate(user?.created_at)} />
        <Row label="Account status" value={user?.is_active ? 'Active' : 'Disabled'} />
        <Row label="Tier" value={user?.is_premium ? 'Premium' : 'Free (everything unlocked)'} />
      </section>

      <section className="mt-14 max-w-2xl">
        <h2 className="font-serif text-2xl">Sign out</h2>
        <p className="mt-3 text-sm text-[#3a342c]">
          We will clear your tokens from this browser. Your data stays safe.
        </p>
        {confirming ? (
          <Alert tone="info">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <span>Confirm sign out?</span>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setConfirming(false)}
                  className="rounded-full border border-[#1a1814]/30 px-3 py-1.5 text-xs text-[#1a1814] hover:bg-[#1a1814]/5"
                >Cancel</button>
                <button
                  type="button"
                  onClick={() => { signOut(); push({ tone: 'info', title: 'Signed out' }); }}
                  className="rounded-full bg-[#9b2226] px-3 py-1.5 text-xs text-white hover:bg-[#7c1a1f]"
                >Sign me out</button>
              </div>
            </div>
          </Alert>
        ) : (
          <button
            type="button"
            onClick={() => setConfirming(true)}
            className="mt-4 inline-flex items-center justify-center rounded-full border border-[#1a1814]/30 px-5 py-2.5 text-sm text-[#1a1814] hover:bg-[#1a1814]/5"
          >Sign out of this browser</button>
        )}
      </section>
    </Container>
  );
}

function Row({ label, value, mono, onCopy }: {
  label: string; value: string; mono?: boolean; onCopy?: () => void;
}) {
  return (
    <div className="rounded-2xl border border-[#1a1814]/10 bg-white/50 p-5">
      <p className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">{label}</p>
      <div className="mt-2 flex items-center justify-between gap-3">
        <p className={`min-w-0 truncate text-[#1a1814] ${mono ? 'font-mono text-sm' : ''}`}>{value}</p>
        {onCopy && (
          <button
            type="button"
            onClick={onCopy}
            className="shrink-0 rounded-full border border-[#1a1814]/20 px-3 py-1 text-xs text-[#1a1814] hover:bg-[#1a1814]/5"
          >Copy</button>
        )}
      </div>
    </div>
  );
}
'''


# Update /dashboard/new to handle 402
FILES["frontend/src/app/dashboard/new/page.tsx"] = '''\'use client\';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormEvent, useState } from 'react';
import { Alert } from '@/components/ui/Alert';
import { Button } from '@/components/ui/Button';
import { Container } from '@/components/ui/Container';
import { Dropzone } from '@/components/ui/Dropzone';
import { Field } from '@/components/ui/Field';
import { Input } from '@/components/ui/Input';
import { ApiError, applicationsApi } from '@/lib/api';

interface InsufficientBalanceDetails {
  wallet_address: string;
  balance_wei: number;
  required_wei: number;
}

function isBalanceDetails(d: unknown): d is InsufficientBalanceDetails {
  return typeof d === 'object' && d !== null
    && 'wallet_address' in d && 'balance_wei' in d && 'required_wei' in d;
}

function weiToGen(wei: number): string {
  if (!wei) return '0';
  return (wei / 1e18).toFixed(4);
}

export default function NewApplicationPage() {
  const router = useRouter();
  const [jobUrl, setJobUrl] = useState('');
  const [linkedinUrl, setLinkedinUrl] = useState('');
  const [portfolioUrl, setPortfolioUrl] = useState('');
  const [cv, setCv] = useState<File | null>(null);
  const [coverLetter, setCoverLetter] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [insufficient, setInsufficient] = useState<InsufficientBalanceDetails | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setInsufficient(null);

    if (!cv) { setError('Please attach your CV.'); return; }
    if (!coverLetter) { setError('Please attach your cover letter.'); return; }
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
      if (e instanceof ApiError && e.status === 402 && isBalanceDetails(e.details)) {
        setInsufficient(e.details);
      } else if (e instanceof ApiError) {
        setError(e.message);
      } else {
        setError('Submission failed. Try again.');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <Container className="py-16">
      <div className="max-w-3xl">
        <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">New evaluation</p>
        <h1 className="mt-3 font-serif text-5xl">Grade your application.</h1>
        <p className="mt-4 max-w-2xl text-[#3a342c]">
          We parse your CV and cover letter, fetch the job posting, and run
          the on-chain evaluation. You will see live status while we work.
        </p>

        {insufficient && (
          <div className="mt-8 rounded-2xl border border-[#a35f1f]/40 bg-[#a35f1f]/10 p-6">
            <p className="text-xs uppercase tracking-[0.15em] text-[#a35f1f]">
              Top up your wallet
            </p>
            <h2 className="mt-2 font-serif text-2xl text-[#1a1814]">
              Not enough GEN to run this evaluation.
            </h2>
            <p className="mt-3 text-sm text-[#3a342c]">
              Validators need to be paid in GEN to run the on-chain LLM.
              Fund your wallet via the StudioNet faucet, then submit again.
            </p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-[#a35f1f]/30 bg-white/60 p-3">
                <p className="text-[10px] uppercase tracking-[0.15em] text-[#a35f1f]">Your wallet</p>
                <p className="mt-1 break-all font-mono text-xs text-[#1a1814]">
                  {insufficient.wallet_address}
                </p>
              </div>
              <div className="rounded-xl border border-[#a35f1f]/30 bg-white/60 p-3">
                <p className="text-[10px] uppercase tracking-[0.15em] text-[#a35f1f]">Balance / needed</p>
                <p className="mt-1 text-sm text-[#1a1814]">
                  {weiToGen(insufficient.balance_wei)} GEN / {weiToGen(insufficient.required_wei)} GEN
                </p>
              </div>
            </div>
            <div className="mt-5 flex flex-wrap gap-3 text-sm">
              <Link
                href="/dashboard/settings"
                className="inline-flex items-center justify-center rounded-full bg-[#1a1814] px-5 py-2 text-[#efece4] hover:bg-[#3a342c]"
              >
                Open my wallet
              </Link>
              <a
                href="https://studio.genlayer.com/"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center rounded-full border border-[#1a1814]/30 px-5 py-2 text-[#1a1814] hover:bg-[#1a1814]/5"
              >
                Open StudioNet
              </a>
            </div>
          </div>
        )}

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
            <Field label="LinkedIn" hint="Optional. Recruiters weight it.">
              <Input
                type="url"
                value={linkedinUrl}
                onChange={(e) => setLinkedinUrl(e.target.value)}
                disabled={loading}
                placeholder="https://www.linkedin.com/in/you/"
              />
            </Field>
            <Field label="Portfolio" hint="Optional. Useful for design or engineering roles.">
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
            <Dropzone label="CV" file={cv} onFile={setCv} disabled={loading} />
            <Dropzone label="Cover letter" file={coverLetter} onFile={setCoverLetter} disabled={loading} />
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


def write(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  wrote {rel}")


for rel, content in FILES.items():
    write(rel, content)

print("\nPhase 9 frontend scaffold complete.")
