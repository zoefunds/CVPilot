import { apiBaseUrl } from './brand';
import { tokenStorage } from './authStorage';
import type {
  JobIngest,
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
  forgotPassword(email: string): Promise<{ detail: string }> {
    return api<{ detail: string }>('/auth/forgot-password', {
      method: 'POST', auth: false,
      body: JSON.stringify({ email }),
    });
  },
  resetPassword(token: string, password: string): Promise<{ detail: string }> {
    return api<{ detail: string }>('/auth/reset-password', {
      method: 'POST', auth: false,
      body: JSON.stringify({ token, password }),
    });
  },
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
export const jobsApi = {
  ingest(url: string): Promise<JobIngest> {
    return api<JobIngest>('/jobs/ingest', {
      method: 'POST',
      body: JSON.stringify({ url }),
    });
  },
};
