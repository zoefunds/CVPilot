"""
CVPilot Phase 6B: auth pages, typed API client, AuthContext, protected dashboard.
Uses /signin and /signup routes (no dashes).
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
'''


FILES["frontend/src/lib/authStorage.ts"] = '''const ACCESS = 'cvpilot.access_token';
const REFRESH = 'cvpilot.refresh_token';

function safeWindow(): Window | null {
  return typeof window === 'undefined' ? null : window;
}

export const tokenStorage = {
  getAccess(): string | null {
    return safeWindow()?.localStorage.getItem(ACCESS) ?? null;
  },
  getRefresh(): string | null {
    return safeWindow()?.localStorage.getItem(REFRESH) ?? null;
  },
  set(access: string, refresh: string): void {
    const w = safeWindow();
    if (!w) return;
    w.localStorage.setItem(ACCESS, access);
    w.localStorage.setItem(REFRESH, refresh);
  },
  clear(): void {
    const w = safeWindow();
    if (!w) return;
    w.localStorage.removeItem(ACCESS);
    w.localStorage.removeItem(REFRESH);
  },
};
'''


FILES["frontend/src/lib/api.ts"] = '''import { apiBaseUrl } from './brand';
import { tokenStorage } from './authStorage';
import type { ApiErrorBody, TokenPair, UserPublic } from './types';

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
  register(
    email: string,
    password: string,
    full_name?: string,
  ): Promise<UserPublic> {
    return api<UserPublic>('/auth/register', {
      method: 'POST',
      auth: false,
      body: JSON.stringify({
        email,
        password,
        full_name: full_name || null,
      }),
    });
  },
  me(): Promise<UserPublic> {
    return api<UserPublic>('/auth/me');
  },
};
'''


FILES["frontend/src/contexts/AuthContext.tsx"] = '''\'use client\';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { useRouter } from 'next/navigation';
import { ApiError, authApi } from '@/lib/api';
import { tokenStorage } from '@/lib/authStorage';
import type { UserPublic } from '@/lib/types';

interface AuthState {
  user: UserPublic | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, fullName?: string) => Promise<void>;
  signOut: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<UserPublic | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadMe = useCallback(async () => {
    if (!tokenStorage.getAccess()) {
      setUser(null);
      setIsLoading(false);
      return;
    }
    try {
      const me = await authApi.me();
      setUser(me);
    } catch (e) {
      if (e instanceof ApiError && (e.status === 401 || e.status === 403)) {
        tokenStorage.clear();
      }
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadMe();
  }, [loadMe]);

  const signIn = useCallback(async (email: string, password: string) => {
    const tokens = await authApi.login(email.toLowerCase().trim(), password);
    tokenStorage.set(tokens.access_token, tokens.refresh_token);
    const me = await authApi.me();
    setUser(me);
  }, []);

  const signUp = useCallback(
    async (email: string, password: string, fullName?: string) => {
      const cleanEmail = email.toLowerCase().trim();
      await authApi.register(cleanEmail, password, fullName);
      const tokens = await authApi.login(cleanEmail, password);
      tokenStorage.set(tokens.access_token, tokens.refresh_token);
      const me = await authApi.me();
      setUser(me);
    },
    [],
  );

  const signOut = useCallback(() => {
    tokenStorage.clear();
    setUser(null);
    router.push('/');
  }, [router]);

  const value = useMemo<AuthState>(
    () => ({
      user,
      isLoading,
      isAuthenticated: !!user,
      signIn,
      signUp,
      signOut,
      refreshUser: loadMe,
    }),
    [user, isLoading, signIn, signUp, signOut, loadMe],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}
'''


FILES["frontend/src/components/providers/Providers.tsx"] = '''\'use client\';

import { AuthProvider } from '@/contexts/AuthContext';

export function Providers({ children }: { children: React.ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}
'''


FILES["frontend/src/components/ui/Input.tsx"] = '''import { forwardRef, InputHTMLAttributes } from 'react';

export const Input = forwardRef<
  HTMLInputElement,
  InputHTMLAttributes<HTMLInputElement>
>(function Input({ className = '', ...rest }, ref) {
  const base =
    'w-full rounded-2xl border border-[#1a1814]/15 bg-white/60 px-4 py-3 text-[#1a1814] placeholder:text-[#3a342c]/50 outline-none transition-colors focus:border-[#2b4f3a] focus:bg-white disabled:opacity-60';
  return <input ref={ref} className={`${base} ${className}`} {...rest} />;
});
'''


FILES["frontend/src/components/ui/Field.tsx"] = '''import { ReactNode } from 'react';

export function Field({
  label,
  hint,
  error,
  children,
}: {
  label: string;
  hint?: string;
  error?: string;
  children: ReactNode;
}) {
  return (
    <div>
      <label className="mb-1.5 block text-xs uppercase tracking-[0.15em] text-[#3a342c]">
        {label}
      </label>
      {children}
      {hint && !error && (
        <p className="mt-1.5 text-xs text-[#3a342c]/70">{hint}</p>
      )}
      {error && (
        <p className="mt-1.5 text-xs text-[#9b2226]">{error}</p>
      )}
    </div>
  );
}
'''


FILES["frontend/src/components/ui/Alert.tsx"] = '''import { ReactNode } from 'react';

type Tone = 'error' | 'success' | 'info';

const tones: Record<Tone, string> = {
  error: 'border-[#9b2226]/30 bg-[#9b2226]/10 text-[#9b2226]',
  success: 'border-[#2b4f3a]/30 bg-[#2b4f3a]/10 text-[#1f3a2a]',
  info: 'border-[#1a1814]/15 bg-[#1a1814]/5 text-[#1a1814]',
};

export function Alert({
  children,
  tone = 'info',
}: {
  children: ReactNode;
  tone?: Tone;
}) {
  return (
    <div className={`rounded-2xl border px-4 py-3 text-sm ${tones[tone]}`}>
      {children}
    </div>
  );
}
'''


FILES["frontend/src/components/auth/AuthGuard.tsx"] = '''\'use client\';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace('/signin');
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-sm text-[#3a342c]">
        Loading your account.
      </div>
    );
  }
  if (!isAuthenticated) {
    return null;
  }
  return <>{children}</>;
}
'''


FILES["frontend/src/components/dashboard/DashboardShell.tsx"] = '''\'use client\';

import Link from 'next/link';
import { Container } from '@/components/ui/Container';
import { useAuth } from '@/contexts/AuthContext';
import { appName } from '@/lib/brand';

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const { user, signOut } = useAuth();
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-10 border-b border-[#d9d5c8] bg-[#efece4]/80 backdrop-blur supports-[backdrop-filter]:bg-[#efece4]/70">
        <Container className="flex h-16 items-center justify-between">
          <Link href="/dashboard" className="font-serif text-2xl">
            {appName}
          </Link>
          <nav className="flex items-center gap-5 text-sm">
            <Link
              href="/dashboard"
              className="text-[#3a342c] hover:text-[#1a1814]"
            >
              Dashboard
            </Link>
            <Link
              href="/dashboard/new"
              className="text-[#3a342c] hover:text-[#1a1814]"
            >
              New evaluation
            </Link>
            <span className="hidden text-[#3a342c]/60 sm:inline">
              {user?.email}
            </span>
            <button
              type="button"
              onClick={signOut}
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


FILES["frontend/src/app/(auth)/layout.tsx"] = '''import Link from 'next/link';
import { Container } from '@/components/ui/Container';
import { appName } from '@/lib/brand';

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <main className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-10 border-b border-[#d9d5c8] bg-[#efece4]/80 backdrop-blur">
        <Container className="flex h-16 items-center justify-between">
          <Link href="/" className="font-serif text-2xl">
            {appName}
          </Link>
          <Link
            href="/"
            className="text-sm text-[#3a342c] hover:text-[#1a1814]"
          >
            Back to home
          </Link>
        </Container>
      </header>
      <div className="flex flex-1 items-start justify-center px-6 py-16 sm:py-24">
        {children}
      </div>
    </main>
  );
}
'''


FILES["frontend/src/app/(auth)/signin/page.tsx"] = '''\'use client\';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormEvent, useEffect, useState } from 'react';
import { Alert } from '@/components/ui/Alert';
import { Button } from '@/components/ui/Button';
import { Field } from '@/components/ui/Field';
import { Input } from '@/components/ui/Input';
import { useAuth } from '@/contexts/AuthContext';
import { ApiError } from '@/lib/api';

export default function SignInPage() {
  const router = useRouter();
  const { signIn, isAuthenticated, isLoading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace('/dashboard');
    }
  }, [isAuthenticated, isLoading, router]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await signIn(email, password);
      router.push('/dashboard');
    } catch (e) {
      if (e instanceof ApiError) setError(e.message);
      else setError('Something went wrong. Try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="w-full max-w-md">
      <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">
        Welcome back
      </p>
      <h1 className="mt-2 font-serif text-4xl sm:text-5xl">
        Sign in to your account.
      </h1>
      <p className="mt-3 text-sm text-[#3a342c]">
        Pick up where you left off.
      </p>

      <form onSubmit={onSubmit} className="mt-10 flex flex-col gap-5">
        {error && <Alert tone="error">{error}</Alert>}
        <Field label="Email">
          <Input
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={loading}
            placeholder="you@example.com"
          />
        </Field>
        <Field label="Password">
          <Input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            disabled={loading}
            placeholder="Your password"
          />
        </Field>
        <Button type="submit" disabled={loading}>
          {loading ? 'Signing in...' : 'Sign in'}
        </Button>
      </form>

      <p className="mt-8 text-sm text-[#3a342c]">
        New here?{' '}
        <Link
          href="/signup"
          className="font-medium text-[#1a1814] underline underline-offset-4 hover:text-[#2b4f3a]"
        >
          Create an account
        </Link>
      </p>
    </div>
  );
}
'''


FILES["frontend/src/app/(auth)/signup/page.tsx"] = '''\'use client\';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormEvent, useEffect, useState } from 'react';
import { Alert } from '@/components/ui/Alert';
import { Button } from '@/components/ui/Button';
import { Field } from '@/components/ui/Field';
import { Input } from '@/components/ui/Input';
import { useAuth } from '@/contexts/AuthContext';
import { ApiError } from '@/lib/api';

export default function SignUpPage() {
  const router = useRouter();
  const { signUp, isAuthenticated, isLoading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace('/dashboard');
    }
  }, [isAuthenticated, isLoading, router]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    setLoading(true);
    try {
      await signUp(email, password, fullName || undefined);
      router.push('/dashboard');
    } catch (e) {
      if (e instanceof ApiError) setError(e.message);
      else setError('Something went wrong. Try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="w-full max-w-md">
      <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">
        Get started
      </p>
      <h1 className="mt-2 font-serif text-4xl sm:text-5xl">
        Create your account.
      </h1>
      <p className="mt-3 text-sm text-[#3a342c]">
        Free for everyone. No payment ever requested.
      </p>

      <form onSubmit={onSubmit} className="mt-10 flex flex-col gap-5">
        {error && <Alert tone="error">{error}</Alert>}
        <Field
          label="Full name"
          hint="Optional. Helps us address you in reports."
        >
          <Input
            type="text"
            autoComplete="name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            disabled={loading}
            placeholder="Jane Doe"
          />
        </Field>
        <Field label="Email">
          <Input
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={loading}
            placeholder="you@example.com"
          />
        </Field>
        <Field label="Password" hint="At least 8 characters.">
          <Input
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            disabled={loading}
            placeholder="Pick something strong"
          />
        </Field>
        <Button type="submit" disabled={loading}>
          {loading ? 'Creating...' : 'Create account'}
        </Button>
      </form>

      <p className="mt-8 text-sm text-[#3a342c]">
        Already a user?{' '}
        <Link
          href="/signin"
          className="font-medium text-[#1a1814] underline underline-offset-4 hover:text-[#2b4f3a]"
        >
          Sign in
        </Link>
      </p>
    </div>
  );
}
'''


FILES["frontend/src/app/dashboard/layout.tsx"] = '''import { AuthGuard } from '@/components/auth/AuthGuard';
import { DashboardShell } from '@/components/dashboard/DashboardShell';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthGuard>
      <DashboardShell>{children}</DashboardShell>
    </AuthGuard>
  );
}
'''


FILES["frontend/src/app/dashboard/page.tsx"] = '''\'use client\';

import Link from 'next/link';
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
          <span className="text-xs uppercase tracking-[0.15em] text-[#3a342c]/70">
            Coming next
          </span>
        </div>
        <div className="mt-4 rounded-2xl border border-dashed border-[#1a1814]/20 bg-white/40 p-10 text-center text-sm text-[#3a342c]">
          Your evaluation history will appear here once you run your first
          scoring pass.
        </div>
      </section>
    </Container>
  );
}
'''


# -------------------------------------------------------------------------
# Updated: root layout (wrap in <Providers>)
# -------------------------------------------------------------------------
FILES["frontend/src/app/layout.tsx"] = '''import type { Metadata } from 'next';
import { Inter, Instrument_Serif } from 'next/font/google';
import { Providers } from '@/components/providers/Providers';
import { appName } from '@/lib/brand';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
});

const serif = Instrument_Serif({
  weight: '400',
  subsets: ['latin'],
  variable: '--font-serif',
  display: 'swap',
});

export const metadata: Metadata = {
  title: `${appName}. AI Job Application Intelligence.`,
  description:
    'CVPilot evaluates your CV, cover letter, and job match with verifiable AI scoring on GenLayer StudioNet. Get the truth before you apply.',
  applicationName: appName,
  themeColor: '#efece4',
  openGraph: {
    title: `${appName}. AI Job Application Intelligence.`,
    description:
      'Verifiable CV scoring, cover letter analysis and recommendations powered by GenLayer Intelligent Contracts.',
    type: 'website',
  },
  icons: { icon: '/favicon.ico' },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${serif.variable}`}>
      <body className="min-h-screen bg-[#efece4] text-[#1a1814] antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
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


# -------------------------------------------------------------------------
# In-place patches: /sign-in -> /signin, /sign-up -> /signup
# in Hero.tsx, page.tsx (landing), Footer.tsx
# -------------------------------------------------------------------------
PATCHES = [
    "frontend/src/components/marketing/Hero.tsx",
    "frontend/src/app/page.tsx",
    "frontend/src/components/marketing/Footer.tsx",
]
for rel in PATCHES:
    p = ROOT / rel
    text = p.read_text(encoding="utf-8")
    new = text.replace('"/sign-in"', '"/signin"').replace('"/sign-up"', '"/signup"')
    if new != text:
        p.write_text(new, encoding="utf-8")
        print(f"  patched links in {rel}")
    else:
        print(f"  skip {rel} (no matching links)")

print("\nPhase 6B files written.")
