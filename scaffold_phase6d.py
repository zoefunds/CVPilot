"""
CVPilot Phase 6D: gauges, toasts, sticky summary, 404/error pages, settings,
mobile polish.
"""

from __future__ import annotations
from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
FILES: dict[str, str] = {}


# -----------------------------------------------------------------------------
# components/ui/ScoreGauge.tsx
# -----------------------------------------------------------------------------
FILES["frontend/src/components/ui/ScoreGauge.tsx"] = '''interface Props {
  value: number | null;
  label: string;
  size?: number;
  hint?: string;
}

function bandColor(v: number): string {
  if (v >= 75) return '#2b4f3a';
  if (v >= 50) return '#a35f1f';
  return '#9b2226';
}

export function ScoreGauge({ value, label, size = 132, hint }: Props) {
  const v = typeof value === 'number' ? Math.max(0, Math.min(100, value)) : 0;
  const shown = typeof value === 'number' ? value : '\u2014';
  const stroke = 10;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const dash = (v / 100) * c;
  const color = bandColor(v);
  return (
    <div className="flex flex-col items-center text-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            stroke="rgba(26,24,20,0.08)"
            strokeWidth={stroke}
            fill="none"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            stroke={color}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={`${dash} ${c}`}
            fill="none"
            style={{ transition: 'stroke-dasharray 700ms ease-out' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-serif text-4xl text-[#1a1814]">{shown}</span>
          <span className="text-[10px] uppercase tracking-[0.15em] text-[#3a342c]/70">
            / 100
          </span>
        </div>
      </div>
      <p className="mt-3 text-xs uppercase tracking-[0.15em] text-[#3a342c]">
        {label}
      </p>
      {hint && (
        <p className="mt-1 max-w-[18ch] text-[11px] leading-snug text-[#3a342c]/70">
          {hint}
        </p>
      )}
    </div>
  );
}
'''


# -----------------------------------------------------------------------------
# contexts/ToastContext.tsx
# -----------------------------------------------------------------------------
FILES["frontend/src/contexts/ToastContext.tsx"] = '''\'use client\';

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from 'react';

export type ToastTone = 'success' | 'error' | 'info';

export interface Toast {
  id: number;
  tone: ToastTone;
  title: string;
  message?: string;
}

interface ToastContextValue {
  toasts: Toast[];
  push: (t: Omit<Toast, 'id'>) => void;
  dismiss: (id: number) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

let nextId = 1;

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const dismiss = useCallback((id: number) => {
    setToasts((cur) => cur.filter((t) => t.id !== id));
  }, []);

  const push = useCallback(
    (t: Omit<Toast, 'id'>) => {
      const id = nextId++;
      setToasts((cur) => [...cur, { ...t, id }]);
      setTimeout(() => dismiss(id), 4500);
    },
    [dismiss],
  );

  const value = useMemo(
    () => ({ toasts, push, dismiss }),
    [toasts, push, dismiss],
  );

  return <ToastContext.Provider value={value}>{children}</ToastContext.Provider>;
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used inside <ToastProvider>');
  return ctx;
}
'''


# -----------------------------------------------------------------------------
# components/ui/ToastViewport.tsx
# -----------------------------------------------------------------------------
FILES["frontend/src/components/ui/ToastViewport.tsx"] = '''\'use client\';

import { useToast } from '@/contexts/ToastContext';

const toneStyles: Record<string, string> = {
  success: 'border-[#2b4f3a]/30 bg-[#2b4f3a]/12 text-[#1f3a2a]',
  error: 'border-[#9b2226]/30 bg-[#9b2226]/12 text-[#9b2226]',
  info: 'border-[#1a1814]/15 bg-white/80 text-[#1a1814]',
};

export function ToastViewport() {
  const { toasts, dismiss } = useToast();
  return (
    <div className="pointer-events-none fixed inset-x-0 top-4 z-50 flex flex-col items-center gap-2 px-4 sm:items-end sm:right-4 sm:left-auto sm:top-6">
      {toasts.map((t) => (
        <div
          key={t.id}
          role="status"
          className={`pointer-events-auto w-full max-w-sm rounded-2xl border px-4 py-3 shadow-[0_18px_45px_-25px_rgba(26,24,20,0.45)] backdrop-blur ${toneStyles[t.tone]}`}
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-medium">{t.title}</p>
              {t.message && (
                <p className="mt-0.5 text-xs opacity-80">{t.message}</p>
              )}
            </div>
            <button
              type="button"
              onClick={() => dismiss(t.id)}
              className="rounded-full px-2 py-1 text-xs opacity-60 hover:opacity-100"
              aria-label="Dismiss"
            >
              \u2715
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
'''


# -----------------------------------------------------------------------------
# components/providers/Providers.tsx (wrap with ToastProvider + viewport)
# -----------------------------------------------------------------------------
FILES["frontend/src/components/providers/Providers.tsx"] = '''\'use client\';

import { AuthProvider } from '@/contexts/AuthContext';
import { ToastProvider } from '@/contexts/ToastContext';
import { ToastViewport } from '@/components/ui/ToastViewport';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ToastProvider>
      <AuthProvider>
        {children}
        <ToastViewport />
      </AuthProvider>
    </ToastProvider>
  );
}
'''


# -----------------------------------------------------------------------------
# app/not-found.tsx
# -----------------------------------------------------------------------------
FILES["frontend/src/app/not-found.tsx"] = '''import Link from 'next/link';
import { Container } from '@/components/ui/Container';
import { appName } from '@/lib/brand';

export default function NotFound() {
  return (
    <main className="min-h-screen">
      <header className="border-b border-[#d9d5c8]">
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
      <Container className="py-24 sm:py-32">
        <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">
          404
        </p>
        <h1 className="mt-3 font-serif text-6xl sm:text-7xl">
          We could not find that page.
        </h1>
        <p className="mt-4 max-w-xl text-[#3a342c]">
          The link may be old, or the page may have moved. Head back to your
          dashboard and try again.
        </p>
        <div className="mt-10 flex flex-wrap gap-3">
          <Link
            href="/dashboard"
            className="inline-flex items-center justify-center rounded-full bg-[#1a1814] px-6 py-3 text-sm font-medium text-[#efece4] hover:bg-[#3a342c]"
          >
            Go to dashboard
          </Link>
          <Link
            href="/"
            className="inline-flex items-center justify-center rounded-full border border-[#1a1814]/30 px-6 py-3 text-sm font-medium text-[#1a1814] hover:bg-[#1a1814]/5"
          >
            Back to home
          </Link>
        </div>
      </Container>
    </main>
  );
}
'''


# -----------------------------------------------------------------------------
# app/error.tsx (client error boundary)
# -----------------------------------------------------------------------------
FILES["frontend/src/app/error.tsx"] = '''\'use client\';

import Link from 'next/link';
import { useEffect } from 'react';
import { Container } from '@/components/ui/Container';
import { appName } from '@/lib/brand';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Useful for debugging in the browser console.
     
    console.error('App error boundary caught:', error);
  }, [error]);

  return (
    <html lang="en">
      <body className="min-h-screen bg-[#efece4] text-[#1a1814] antialiased">
        <main className="min-h-screen">
          <header className="border-b border-[#d9d5c8]">
            <Container className="flex h-16 items-center justify-between">
              <Link href="/" className="font-serif text-2xl">
                {appName}
              </Link>
            </Container>
          </header>
          <Container className="py-24 sm:py-32">
            <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">
              Unexpected error
            </p>
            <h1 className="mt-3 font-serif text-6xl">
              Something went sideways.
            </h1>
            <p className="mt-4 max-w-xl text-[#3a342c]">
              We logged the failure. You can try again, or head back home.
              If this keeps happening, please reach out.
            </p>
            <div className="mt-10 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={reset}
                className="inline-flex items-center justify-center rounded-full bg-[#1a1814] px-6 py-3 text-sm font-medium text-[#efece4] hover:bg-[#3a342c]"
              >
                Try again
              </button>
              <Link
                href="/dashboard"
                className="inline-flex items-center justify-center rounded-full border border-[#1a1814]/30 px-6 py-3 text-sm font-medium text-[#1a1814] hover:bg-[#1a1814]/5"
              >
                Back to dashboard
              </Link>
            </div>
          </Container>
        </main>
      </body>
    </html>
  );
}
'''


# -----------------------------------------------------------------------------
# app/dashboard/settings/page.tsx
# -----------------------------------------------------------------------------
FILES["frontend/src/app/dashboard/settings/page.tsx"] = '''\'use client\';

import { useState } from 'react';
import { Alert } from '@/components/ui/Alert';
import { Container } from '@/components/ui/Container';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/contexts/ToastContext';

function fmtDate(s: string | undefined): string {
  if (!s) return '\u2014';
  try {
    return new Date(s).toLocaleString();
  } catch {
    return s;
  }
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
      <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">
        Settings
      </p>
      <h1 className="mt-3 font-serif text-5xl">Your account.</h1>

      <section className="mt-10 grid gap-6 sm:grid-cols-2">
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
          We will clear your tokens from this browser. Your data stays safe on
          the server.
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
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => {
                    signOut();
                    push({ tone: 'info', title: 'Signed out' });
                  }}
                  className="rounded-full bg-[#9b2226] px-3 py-1.5 text-xs text-white hover:bg-[#7c1a1f]"
                >
                  Sign me out
                </button>
              </div>
            </div>
          </Alert>
        ) : (
          <button
            type="button"
            onClick={() => setConfirming(true)}
            className="mt-4 inline-flex items-center justify-center rounded-full border border-[#1a1814]/30 px-5 py-2.5 text-sm text-[#1a1814] hover:bg-[#1a1814]/5"
          >
            Sign out of this browser
          </button>
        )}
      </section>
    </Container>
  );
}

function Row({
  label,
  value,
  mono,
  onCopy,
}: {
  label: string;
  value: string;
  mono?: boolean;
  onCopy?: () => void;
}) {
  return (
    <div className="rounded-2xl border border-[#1a1814]/10 bg-white/50 p-5">
      <p className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">
        {label}
      </p>
      <div className="mt-2 flex items-center justify-between gap-3">
        <p className={`min-w-0 truncate text-[#1a1814] ${mono ? 'font-mono text-sm' : ''}`}>
          {value}
        </p>
        {onCopy && (
          <button
            type="button"
            onClick={onCopy}
            className="shrink-0 rounded-full border border-[#1a1814]/20 px-3 py-1 text-xs text-[#1a1814] hover:bg-[#1a1814]/5"
          >
            Copy
          </button>
        )}
      </div>
    </div>
  );
}
'''


# -----------------------------------------------------------------------------
# components/dashboard/DashboardShell.tsx (add Settings link + mobile)
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
# app/(auth)/signin/page.tsx (toast on success)
# -----------------------------------------------------------------------------
FILES["frontend/src/app/(auth)/signin/page.tsx"] = '''\'use client\';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormEvent, useEffect, useState } from 'react';
import { Alert } from '@/components/ui/Alert';
import { Button } from '@/components/ui/Button';
import { Field } from '@/components/ui/Field';
import { Input } from '@/components/ui/Input';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/contexts/ToastContext';
import { ApiError } from '@/lib/api';

export default function SignInPage() {
  const router = useRouter();
  const { signIn, isAuthenticated, isLoading } = useAuth();
  const { push } = useToast();
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
      push({ tone: 'success', title: 'Welcome back.' });
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


# -----------------------------------------------------------------------------
# app/(auth)/signup/page.tsx (toast on success)
# -----------------------------------------------------------------------------
FILES["frontend/src/app/(auth)/signup/page.tsx"] = '''\'use client\';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormEvent, useEffect, useState } from 'react';
import { Alert } from '@/components/ui/Alert';
import { Button } from '@/components/ui/Button';
import { Field } from '@/components/ui/Field';
import { Input } from '@/components/ui/Input';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/contexts/ToastContext';
import { ApiError } from '@/lib/api';

export default function SignUpPage() {
  const router = useRouter();
  const { signUp, isAuthenticated, isLoading } = useAuth();
  const { push } = useToast();
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
      push({
        tone: 'success',
        title: 'Account created.',
        message: 'Welcome to CVPilot.',
      });
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


# -----------------------------------------------------------------------------
# app/dashboard/applications/[id]/page.tsx (gauges + sticky summary)
# -----------------------------------------------------------------------------
FILES["frontend/src/app/dashboard/applications/[id]/page.tsx"] = '''\'use client\';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import { ScoreGauge } from '@/components/ui/ScoreGauge';
import { StatusBadge } from '@/components/dashboard/StatusBadge';
import { Alert } from '@/components/ui/Alert';
import { Container } from '@/components/ui/Container';
import { useToast } from '@/contexts/ToastContext';
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
  const { push } = useToast();

  const [app, setApp] = useState<ApplicationPublic | null>(null);
  const [evaluation, setEvaluation] = useState<EvaluationPublic | null>(null);
  const [error, setError] = useState<string | null>(null);
  const completed = useRef(false);
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
            if (a.status === 'complete' && !completed.current) {
              completed.current = true;
              push({
                tone: 'success',
                title: 'Evaluation ready.',
                message: 'Scroll down for your scores and recommendations.',
              });
            }
            if (a.status === 'failed' && !completed.current) {
              completed.current = true;
              push({
                tone: 'error',
                title: 'Evaluation failed.',
                message: 'See the error below.',
              });
            }
          } catch (e) {
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
  }, [id, push]);

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

  const tx = evaluation?.contract_tx_hash || null;
  const comp = evaluation?.competitiveness_score ?? null;

  async function copyHash() {
    if (!tx) return;
    try {
      await navigator.clipboard.writeText(tx);
      push({ tone: 'success', title: 'Hash copied.' });
    } catch {
      push({ tone: 'error', title: 'Could not copy.' });
    }
  }

  return (
    <>
      {/* Sticky summary bar (always visible while scrolling) */}
      <div className="sticky top-16 z-10 border-b border-[#d9d5c8] bg-[#efece4]/85 backdrop-blur supports-[backdrop-filter]:bg-[#efece4]/70">
        <Container className="flex flex-wrap items-center justify-between gap-3 py-3 text-sm">
          <div className="flex min-w-0 items-center gap-3">
            <Link href="/dashboard" className="text-[#3a342c] hover:text-[#1a1814]">
              \u2190 Dashboard
            </Link>
            <span className="hidden text-[#3a342c]/40 sm:inline">|</span>
            <span className="truncate font-medium text-[#1a1814]">
              {app.job_title || 'Untitled posting'}
            </span>
          </div>
          <div className="flex items-center gap-3">
            {comp !== null && (
              <span className="font-serif text-2xl text-[#1a1814]">
                {comp}
                <span className="text-xs text-[#3a342c]/70"> /100</span>
              </span>
            )}
            <StatusBadge status={app.status} />
          </div>
        </Container>
      </div>

      <Container className="py-12">
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

        {isWorking && (
          <div className="mt-8 rounded-2xl border border-[#1a1814]/15 bg-white/50 p-6 text-sm text-[#3a342c]">
            <p className="font-medium text-[#1a1814]">Working on it.</p>
            <p className="mt-1 text-[#3a342c]/80">
              We are parsing your files and fetching the job posting. This
              page updates automatically.
            </p>
          </div>
        )}

        {app.status === 'failed' && (
          <div className="mt-8">
            <Alert tone="error">
              <div>
                <p className="font-medium">Evaluation failed.</p>
                {app.error && (
                  <p className="mt-1 text-xs">{app.error}</p>
                )}
              </div>
            </Alert>
          </div>
        )}

        {evaluation && evaluation.status === 'complete' && (
          <EvaluationView
            ev={evaluation}
            app={app}
            tx={tx}
            onCopyHash={copyHash}
          />
        )}
      </Container>
    </>
  );
}


function EvaluationView({
  ev,
  app,
  tx,
  onCopyHash,
}: {
  ev: EvaluationPublic;
  app: ApplicationPublic;
  tx: string | null;
  onCopyHash: () => void;
}) {
  const cv = app.files.find((f) => f.kind === 'cv');
  const cl = app.files.find((f) => f.kind === 'cover_letter');

  return (
    <div className="mt-12 flex flex-col gap-14">
      {/* HERO BLOCK */}
      <section className="rounded-3xl border border-[#1a1814]/10 bg-white/55 p-8 shadow-[0_20px_60px_-30px_rgba(26,24,20,0.3)] sm:p-10">
        <div className="grid items-center gap-10 lg:grid-cols-12">
          <div className="lg:col-span-5">
            <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">
              Competitiveness
            </p>
            <p className="mt-2 font-serif text-7xl text-[#1a1814] sm:text-8xl">
              {ev.competitiveness_score ?? '\u2014'}
            </p>
            <p className="text-xs text-[#3a342c]/70">/ 100</p>
            {tx ? (
              <button
                type="button"
                onClick={onCopyHash}
                className="mt-5 inline-flex flex-col items-start rounded-2xl border border-[#2b4f3a]/30 bg-[#2b4f3a]/10 px-4 py-3 text-left transition-colors hover:bg-[#2b4f3a]/20"
                title="Click to copy"
              >
                <span className="text-[10px] uppercase tracking-[0.18em] text-[#2b4f3a]">
                  Verified on StudioNet
                </span>
                <span className="mt-1 font-mono text-xs text-[#2b4f3a]">
                  {shortHash(tx)}
                </span>
              </button>
            ) : (
              <span className="mt-5 inline-block rounded-2xl border border-[#1a1814]/15 bg-white/60 px-3 py-2 text-[10px] uppercase tracking-[0.18em] text-[#3a342c]/80">
                Scored locally
              </span>
            )}
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

      {ev.recommendations.length > 0 && (
        <section>
          <div className="flex items-baseline justify-between">
            <h2 className="font-serif text-3xl">Fix these first.</h2>
            <span className="text-xs uppercase tracking-[0.15em] text-[#3a342c]/70">
              {ev.recommendations.length} item
              {ev.recommendations.length === 1 ? '' : 's'}
            </span>
          </div>
          <ul className="mt-5 grid gap-3">
            {ev.recommendations.map((r, i) => (
              <li
                key={i}
                className="flex items-start gap-4 rounded-2xl border border-[#1a1814]/10 bg-white/60 p-5"
              >
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
          <p className="mt-2 text-sm text-[#3a342c]">
            These appear in the job posting but not in your CV.
          </p>
          <div className="mt-5 flex flex-wrap gap-2">
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
          <h2 className="font-serif text-3xl">Weak statements.</h2>
          <p className="mt-2 text-sm text-[#3a342c]">
            Lines in your CV that read passive or vague.
          </p>
          <ul className="mt-5 grid gap-3">
            {ev.weak_statements.map((w, i) => (
              <li
                key={i}
                className="rounded-2xl border border-[#a35f1f]/30 bg-[#a35f1f]/10 p-5 text-sm text-[#a35f1f]"
              >
                {w}
              </li>
            ))}
          </ul>
        </section>
      )}

      {ev.company_alignment_notes.length > 0 && (
        <section>
          <h2 className="font-serif text-3xl">Company alignment.</h2>
          <ul className="mt-5 grid gap-3">
            {ev.company_alignment_notes.map((c, i) => (
              <li
                key={i}
                className="rounded-2xl border border-[#1a1814]/10 bg-white/60 p-5 text-sm text-[#1a1814]"
              >
                {c}
              </li>
            ))}
          </ul>
        </section>
      )}

      {(cv || cl) && (
        <section>
          <h2 className="font-serif text-3xl">Files.</h2>
          <div className="mt-5 grid gap-4 sm:grid-cols-2">
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
  file: {
    original_filename: string;
    detected_kind: string | null;
    byte_size: number;
  };
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

print("\nPhase 6D files written.")
