"""
Phase 11A frontend: WalletContext, top-bar WalletBalanceChip,
session-expired toast on AuthContext, WalletCard reads shared state.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
FILES: dict[str, str] = {}


# WalletContext: shared live balance state
FILES["frontend/src/contexts/WalletContext.tsx"] = '''\'use client\';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { ApiError, walletApi } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import type { WalletPublic } from '@/lib/types';

const REFRESH_MS = 60_000;
// 0.5 GEN expressed in wei
export const LOW_BALANCE_WEI = 500_000_000_000_000_000;

interface WalletState {
  wallet: WalletPublic | null;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

const WalletContext = createContext<WalletState | null>(null);

export function WalletProvider({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user } = useAuth();
  const [wallet, setWallet] = useState<WalletPublic | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const refresh = useCallback(async () => {
    if (!isAuthenticated) {
      setWallet(null);
      setError(null);
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    try {
      const w = await walletApi.get();
      setWallet(w);
      setError(null);
    } catch (e) {
      // Soft fail: keep the previous balance visible so the UI does not
      // suddenly blank on a transient network blip.
      const msg = e instanceof ApiError ? e.message : 'Could not refresh wallet.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  // Refresh on auth changes.
  useEffect(() => {
    void refresh();
  }, [refresh, user?.id]);

  // Poll while authenticated.
  useEffect(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (!isAuthenticated) return;
    timerRef.current = setInterval(() => {
      void refresh();
    }, REFRESH_MS);
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [isAuthenticated, refresh]);

  const value = useMemo<WalletState>(
    () => ({ wallet, isLoading, error, refresh }),
    [wallet, isLoading, error, refresh],
  );

  return <WalletContext.Provider value={value}>{children}</WalletContext.Provider>;
}

export function useWallet(): WalletState {
  const ctx = useContext(WalletContext);
  if (!ctx) throw new Error('useWallet must be used inside <WalletProvider>');
  return ctx;
}
'''


# WalletBalanceChip in the top bar
FILES["frontend/src/components/dashboard/WalletBalanceChip.tsx"] = '''\'use client\';

import Link from 'next/link';
import { LOW_BALANCE_WEI, useWallet } from '@/contexts/WalletContext';

function formatGen(balance: string | undefined): string {
  if (!balance) return '\u2014';
  // Trim trailing zeros for readability while preserving small balances.
  const num = Number(balance);
  if (Number.isNaN(num)) return balance;
  if (num >= 1) return num.toFixed(2);
  if (num >= 0.001) return num.toFixed(4);
  return num === 0 ? '0' : num.toExponential(2);
}

export function WalletBalanceChip() {
  const { wallet, isLoading } = useWallet();

  if (!wallet) {
    return (
      <span className="hidden items-center gap-1.5 rounded-full border border-[#1a1814]/15 bg-white/40 px-3 py-1 text-[10px] uppercase tracking-[0.15em] text-[#3a342c]/70 sm:inline-flex">
        <span className="h-1.5 w-1.5 rounded-full bg-[#3a342c]/40" />
        {isLoading ? 'Wallet\u2026' : 'Wallet'}
      </span>
    );
  }

  const low = wallet.balance_wei < LOW_BALANCE_WEI;
  const cls = low
    ? 'border-[#a35f1f]/40 bg-[#a35f1f]/12 text-[#a35f1f]'
    : 'border-[#2b4f3a]/30 bg-[#2b4f3a]/10 text-[#2b4f3a]';
  const dot = low ? 'bg-[#a35f1f]' : 'bg-[#2b4f3a]';

  return (
    <Link
      href="/dashboard/settings"
      className={[
        'inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs transition-colors',
        cls,
        'hover:opacity-80',
      ].join(' ')}
      title={low ? 'Low balance. Top up to keep submitting.' : 'Your GenLayer wallet balance'}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${dot}`} />
      <span className="font-medium">{formatGen(wallet.balance_gen)} GEN</span>
    </Link>
  );
}
'''


# AuthContext: push a toast on session-expiry
FILES["frontend/src/contexts/AuthContext.tsx"] = '''\'use client\';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { useRouter } from 'next/navigation';
import { ApiError, authApi } from '@/lib/api';
import { tokenStorage } from '@/lib/authStorage';
import { useToast } from '@/contexts/ToastContext';
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
  const { push } = useToast();
  const [user, setUser] = useState<UserPublic | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  // Remember whether the user was previously authenticated so we can show a
  // "session expired" toast on involuntary sign-outs (but not on first load).
  const wasAuthenticated = useRef(false);

  const loadMe = useCallback(async () => {
    if (!tokenStorage.getAccess()) {
      if (wasAuthenticated.current) {
        push({
          tone: 'info',
          title: 'Session expired.',
          message: 'Sign in again to continue.',
        });
        wasAuthenticated.current = false;
      }
      setUser(null);
      setIsLoading(false);
      return;
    }
    try {
      const me = await authApi.me();
      setUser(me);
      wasAuthenticated.current = true;
    } catch (e) {
      const expired = e instanceof ApiError && (e.status === 401 || e.status === 403);
      if (expired) {
        tokenStorage.clear();
        if (wasAuthenticated.current) {
          push({
            tone: 'info',
            title: 'Session expired.',
            message: 'Sign in again to continue.',
          });
        }
        wasAuthenticated.current = false;
      }
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, [push]);

  useEffect(() => {
    void loadMe();
  }, [loadMe]);

  const signIn = useCallback(async (email: string, password: string) => {
    const tokens = await authApi.login(email.toLowerCase().trim(), password);
    tokenStorage.set(tokens.access_token, tokens.refresh_token);
    const me = await authApi.me();
    setUser(me);
    wasAuthenticated.current = true;
  }, []);

  const signUp = useCallback(
    async (email: string, password: string, fullName?: string) => {
      const cleanEmail = email.toLowerCase().trim();
      await authApi.register(cleanEmail, password, fullName);
      const tokens = await authApi.login(cleanEmail, password);
      tokenStorage.set(tokens.access_token, tokens.refresh_token);
      const me = await authApi.me();
      setUser(me);
      wasAuthenticated.current = true;
    },
    [],
  );

  const signOut = useCallback(() => {
    tokenStorage.clear();
    setUser(null);
    wasAuthenticated.current = false;
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


# Providers: wrap with WalletProvider
FILES["frontend/src/components/providers/Providers.tsx"] = '''\'use client\';

import { AuthProvider } from '@/contexts/AuthContext';
import { ToastProvider } from '@/contexts/ToastContext';
import { WalletProvider } from '@/contexts/WalletContext';
import { ToastViewport } from '@/components/ui/ToastViewport';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ToastProvider>
      <AuthProvider>
        <WalletProvider>
          {children}
          <ToastViewport />
        </WalletProvider>
      </AuthProvider>
    </ToastProvider>
  );
}
'''


# DashboardShell: mount WalletBalanceChip
FILES["frontend/src/components/dashboard/DashboardShell.tsx"] = '''\'use client\';

import Link from 'next/link';
import { Container } from '@/components/ui/Container';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/contexts/ToastContext';
import { WalletBalanceChip } from '@/components/dashboard/WalletBalanceChip';
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
          <nav className="flex items-center gap-3 text-sm sm:gap-4">
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
            <WalletBalanceChip />
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


# WalletCard: read from shared context
FILES["frontend/src/components/dashboard/WalletCard.tsx"] = '''\'use client\';

import { useState } from 'react';
import { ApiError, walletApi } from '@/lib/api';
import { useToast } from '@/contexts/ToastContext';
import { LOW_BALANCE_WEI, useWallet } from '@/contexts/WalletContext';

export function WalletCard() {
  const { wallet, isLoading, error, refresh } = useWallet();
  const [revealed, setRevealed] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
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
            onClick={() => void refresh()}
            disabled={isLoading}
            className="mt-3 rounded-full border border-[#1a1814]/20 px-3 py-1 text-xs hover:bg-[#1a1814]/5 disabled:opacity-60"
          >
            {isLoading ? 'Refreshing\u2026' : 'Refresh'}
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


def write(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  wrote {rel}")


for rel, content in FILES.items():
    write(rel, content)

print("\nPhase 11A frontend complete.")
