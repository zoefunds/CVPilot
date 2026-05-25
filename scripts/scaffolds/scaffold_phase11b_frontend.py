"""
Phase 11B frontend: SendGenModal, WalletActivity, integration in WalletCard
and the Settings page.
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
FILES: dict[str, str] = {}


# ----- types -----
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

export interface WalletSendRequest {
  to_address: string;
  amount_gen: string;
}

export interface WalletSendResponse {
  tx_hash: string;
  from_address: string;
  to_address: string;
  amount_wei: number;
  amount_gen: string;
  explorer_url: string | null;
}

export type WalletActivityKind = 'evaluation' | 'send';

export interface WalletActivityItem {
  kind: WalletActivityKind;
  timestamp: string;
  tx_hash: string | null;
  status: string;
  description: string;
  to_address: string | null;
  amount_wei: number | null;
  amount_gen: string | null;
  application_id: string | null;
  explorer_url: string | null;
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


# ----- walletApi extension -----
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
  WalletActivityItem,
  WalletExport,
  WalletPublic,
  WalletSendRequest,
  WalletSendResponse,
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
  me(): Promise<UserPublic> { return api<UserPublic>('/auth/me'); },
};

export const walletApi = {
  get(): Promise<WalletPublic> { return api<WalletPublic>('/auth/wallet'); },
  export(): Promise<WalletExport> { return api<WalletExport>('/auth/wallet/export', { method: 'POST' }); },
  send(input: WalletSendRequest): Promise<WalletSendResponse> {
    return api<WalletSendResponse>('/auth/wallet/send', {
      method: 'POST',
      body: JSON.stringify(input),
    });
  },
  activity(): Promise<WalletActivityItem[]> {
    return api<WalletActivityItem[]>('/auth/wallet/activity');
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


# ----- SendGenModal -----
FILES["frontend/src/components/dashboard/SendGenModal.tsx"] = '''\'use client\';

import { FormEvent, useEffect, useState } from 'react';
import { ApiError, walletApi } from '@/lib/api';
import { useToast } from '@/contexts/ToastContext';
import { useWallet } from '@/contexts/WalletContext';
import { Field } from '@/components/ui/Field';
import { Input } from '@/components/ui/Input';

interface Props {
  open: boolean;
  onClose: () => void;
}

const ADDR_RE = /^0x[0-9a-fA-F]{40}$/;

function isValidAmount(s: string, balanceGen: string | undefined): { ok: boolean; reason?: string } {
  const n = Number(s);
  if (!s || !Number.isFinite(n) || n <= 0) return { ok: false, reason: 'Enter an amount greater than zero.' };
  const bal = Number(balanceGen || '0');
  if (Number.isFinite(bal) && n > bal) return { ok: false, reason: 'Amount exceeds your balance.' };
  return { ok: true };
}

export function SendGenModal({ open, onClose }: Props) {
  const { wallet, refresh } = useWallet();
  const { push } = useToast();
  const [to, setTo] = useState('');
  const [amount, setAmount] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    if (open) {
      setTo(''); setAmount(''); setError(null); setConfirming(false); setBusy(false);
    }
  }, [open]);

  if (!open) return null;

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!ADDR_RE.test(to.trim())) {
      setError('Recipient must be a 0x address (42 characters).');
      return;
    }
    if (wallet && to.trim().toLowerCase() === wallet.address.toLowerCase()) {
      setError('You cannot send to your own wallet.');
      return;
    }
    const v = isValidAmount(amount, wallet?.balance_gen);
    if (!v.ok) { setError(v.reason || 'Invalid amount.'); return; }
    setConfirming(true);
  }

  async function confirm() {
    setBusy(true);
    setError(null);
    try {
      const res = await walletApi.send({ to_address: to.trim(), amount_gen: amount });
      push({
        tone: 'success',
        title: 'GEN sent.',
        message: `tx ${res.tx_hash.slice(0, 10)}\u2026`,
      });
      void refresh();
      onClose();
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : 'Send failed.';
      setError(msg);
      setConfirming(false);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-30 flex items-center justify-center bg-[#1a1814]/40 backdrop-blur-sm p-4"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="w-full max-w-md rounded-3xl border border-[#1a1814]/10 bg-[#efece4] p-6 shadow-[0_30px_80px_-30px_rgba(26,24,20,0.5)]">
        <div className="flex items-baseline justify-between">
          <h2 className="font-serif text-2xl">Send GEN</h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full px-2 py-1 text-xs text-[#3a342c] hover:bg-[#1a1814]/5"
          >
            Close
          </button>
        </div>
        <p className="mt-2 text-xs text-[#3a342c]">
          From <span className="font-mono">{wallet?.address.slice(0, 8)}\u2026{wallet?.address.slice(-6)}</span>
          {' \u00b7 '}Balance {wallet?.balance_gen || '0'} GEN
        </p>

        {!confirming ? (
          <form onSubmit={onSubmit} className="mt-5 flex flex-col gap-4">
            <Field label="Recipient" hint="A 0x address on StudioNet.">
              <Input
                value={to}
                onChange={(e) => setTo(e.target.value)}
                placeholder="0x\u2026"
                autoComplete="off"
                spellCheck={false}
                className="font-mono text-sm"
                required
              />
            </Field>
            <Field label="Amount" hint={`Maximum ${wallet?.balance_gen || '0'} GEN.`}>
              <Input
                type="number"
                step="any"
                min="0"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.5"
                required
              />
            </Field>
            {error && (
              <p className="rounded-2xl border border-[#9b2226]/30 bg-[#9b2226]/10 px-4 py-3 text-sm text-[#9b2226]">
                {error}
              </p>
            )}
            <div className="mt-2 flex flex-wrap gap-2">
              <button
                type="submit"
                className="inline-flex items-center justify-center rounded-full bg-[#1a1814] px-5 py-2.5 text-sm font-medium text-[#efece4] hover:bg-[#3a342c]"
              >
                Review
              </button>
              <button
                type="button"
                onClick={onClose}
                className="inline-flex items-center justify-center rounded-full border border-[#1a1814]/30 px-5 py-2.5 text-sm text-[#1a1814] hover:bg-[#1a1814]/5"
              >
                Cancel
              </button>
            </div>
          </form>
        ) : (
          <div className="mt-5 flex flex-col gap-4">
            <div className="rounded-2xl border border-[#1a1814]/15 bg-white/60 p-4">
              <p className="text-[10px] uppercase tracking-[0.15em] text-[#3a342c]">Confirm</p>
              <p className="mt-2 text-sm text-[#1a1814]">
                Send <span className="font-medium">{amount} GEN</span> to:
              </p>
              <p className="mt-1 break-all font-mono text-xs text-[#1a1814]">{to.trim()}</p>
              <p className="mt-3 text-xs text-[#3a342c]/70">
                This transfer is irreversible. Double-check the address.
              </p>
            </div>
            {error && (
              <p className="rounded-2xl border border-[#9b2226]/30 bg-[#9b2226]/10 px-4 py-3 text-sm text-[#9b2226]">
                {error}
              </p>
            )}
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={confirm}
                disabled={busy}
                className="inline-flex items-center justify-center rounded-full bg-[#2b4f3a] px-5 py-2.5 text-sm font-medium text-[#efece4] hover:bg-[#1f3a2a] disabled:opacity-60"
              >
                {busy ? 'Sending\u2026' : 'Confirm send'}
              </button>
              <button
                type="button"
                onClick={() => { setConfirming(false); setError(null); }}
                disabled={busy}
                className="inline-flex items-center justify-center rounded-full border border-[#1a1814]/30 px-5 py-2.5 text-sm text-[#1a1814] hover:bg-[#1a1814]/5 disabled:opacity-60"
              >
                Back
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
'''


# ----- WalletActivity -----
FILES["frontend/src/components/dashboard/WalletActivity.tsx"] = '''\'use client\';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { ApiError, walletApi } from '@/lib/api';
import type { WalletActivityItem } from '@/lib/types';

function fmtTime(s: string): string {
  try { return new Date(s).toLocaleString(); } catch { return s; }
}

function shortHash(h: string | null | undefined): string {
  if (!h) return '\u2014';
  if (h.length <= 14) return h;
  return `${h.slice(0, 8)}\u2026${h.slice(-6)}`;
}

export function WalletActivity({ refreshKey }: { refreshKey?: number }) {
  const [items, setItems] = useState<WalletActivityItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const data = await walletApi.activity();
        if (alive) setItems(data);
      } catch (e) {
        if (alive) setError(e instanceof ApiError ? e.message : 'Could not load activity.');
      }
    })();
    return () => { alive = false; };
  }, [refreshKey]);

  return (
    <section>
      <div className="flex items-baseline justify-between">
        <h2 className="font-serif text-2xl">Activity.</h2>
        <span className="text-[10px] uppercase tracking-[0.15em] text-[#3a342c]/70">
          on-chain
        </span>
      </div>
      <p className="mt-2 text-sm text-[#3a342c]">
        Your verifiable evaluations and outgoing GEN transfers.
      </p>

      {error && (
        <div className="mt-4 rounded-2xl border border-[#9b2226]/30 bg-[#9b2226]/10 p-4 text-sm text-[#9b2226]">
          {error}
        </div>
      )}

      {items === null && !error && (
        <p className="mt-4 text-sm text-[#3a342c]">Loading.</p>
      )}

      {items && items.length === 0 && (
        <div className="mt-4 rounded-2xl border border-dashed border-[#1a1814]/20 bg-white/40 p-8 text-center text-sm text-[#3a342c]">
          No on-chain activity yet. Run an evaluation or send GEN to begin
          your history.
        </div>
      )}

      {items && items.length > 0 && (
        <ul className="mt-4 divide-y divide-[#d9d5c8] overflow-hidden rounded-2xl border border-[#1a1814]/10 bg-white/40">
          {items.map((it, i) => (
            <li key={(it.tx_hash || it.timestamp) + i} className="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
              <div className="min-w-0">
                <p className="flex flex-wrap items-center gap-2">
                  <span className={[
                    'rounded-full px-2.5 py-0.5 text-[10px] uppercase tracking-[0.15em]',
                    it.kind === 'evaluation'
                      ? 'bg-[#2b4f3a]/12 text-[#2b4f3a]'
                      : 'bg-[#1a1814]/10 text-[#1a1814]',
                  ].join(' ')}>
                    {it.kind === 'evaluation' ? 'Evaluation' : 'Send'}
                  </span>
                  <span className="truncate font-medium text-[#1a1814]">
                    {it.description}
                  </span>
                </p>
                <p className="mt-1 text-xs text-[#3a342c]/70">
                  {fmtTime(it.timestamp)}
                  {it.amount_gen && ` \u00b7 ${it.amount_gen} GEN`}
                </p>
              </div>
              <div className="flex items-center gap-3 text-xs">
                <span className="font-mono text-[#3a342c]/80">
                  {shortHash(it.tx_hash)}
                </span>
                {it.kind === 'evaluation' && it.application_id && (
                  <Link
                    href={`/dashboard/applications/${it.application_id}`}
                    className="rounded-full border border-[#1a1814]/20 px-3 py-1 text-[#1a1814] hover:bg-[#1a1814]/5"
                  >
                    View
                  </Link>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
'''


# ----- WalletCard with Send button + activity stitching -----
FILES["frontend/src/components/dashboard/WalletCard.tsx"] = '''\'use client\';

import { useState } from 'react';
import { ApiError, walletApi } from '@/lib/api';
import { useToast } from '@/contexts/ToastContext';
import { LOW_BALANCE_WEI, useWallet } from '@/contexts/WalletContext';
import { SendGenModal } from '@/components/dashboard/SendGenModal';

export function WalletCard({ onActivityChanged }: { onActivityChanged?: () => void }) {
  const { wallet, isLoading, error, refresh } = useWallet();
  const [revealed, setRevealed] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [sendOpen, setSendOpen] = useState(false);
  const { push } = useToast();

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

  if (error && !wallet) {
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

  const lowBalance = wallet.balance_wei < LOW_BALANCE_WEI;

  return (
    <>
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
            <p className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">Address</p>
            <p className="mt-2 break-all font-mono text-xs text-[#1a1814]">{wallet.address}</p>
            <button
              type="button"
              onClick={() => copy(wallet.address, 'Wallet address')}
              className="mt-3 rounded-full border border-[#1a1814]/20 px-3 py-1 text-xs hover:bg-[#1a1814]/5"
            >
              Copy address
            </button>
          </div>

          <div className="rounded-xl border border-[#1a1814]/10 bg-[#efece4]/60 p-4">
            <p className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">Balance</p>
            <p className="mt-2 font-serif text-3xl text-[#1a1814]">
              {wallet.balance_gen}
              <span className="ml-1 text-xs text-[#3a342c]/70">GEN</span>
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => void refresh()}
                disabled={isLoading}
                className="rounded-full border border-[#1a1814]/20 px-3 py-1 text-xs hover:bg-[#1a1814]/5 disabled:opacity-60"
              >
                {isLoading ? 'Refreshing\u2026' : 'Refresh'}
              </button>
              <button
                type="button"
                onClick={() => setSendOpen(true)}
                disabled={wallet.balance_wei === 0}
                className="rounded-full bg-[#1a1814] px-3 py-1 text-xs text-[#efece4] hover:bg-[#3a342c] disabled:opacity-50"
              >
                Send GEN
              </button>
            </div>
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
            <p className="text-[10px] uppercase tracking-[0.15em] text-[#9b2226]">Private key</p>
            <p className="mt-2 break-all font-mono text-xs text-[#9b2226]">{revealed}</p>
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

      <SendGenModal
        open={sendOpen}
        onClose={() => {
          setSendOpen(false);
          onActivityChanged?.();
        }}
      />
    </>
  );
}
'''


# ----- Settings page mounting WalletActivity below WalletCard -----
FILES["frontend/src/app/dashboard/settings/page.tsx"] = '''\'use client\';

import { useState } from 'react';
import { Alert } from '@/components/ui/Alert';
import { Container } from '@/components/ui/Container';
import { WalletCard } from '@/components/dashboard/WalletCard';
import { WalletActivity } from '@/components/dashboard/WalletActivity';
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
  const [activityKey, setActivityKey] = useState(0);

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
        <WalletCard onActivityChanged={() => setActivityKey((k) => k + 1)} />
      </section>

      <section className="mt-10">
        <WalletActivity refreshKey={activityKey} />
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


def write(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  wrote {rel}")


for rel, content in FILES.items():
    write(rel, content)

print("\nPhase 11B frontend complete.")
