'use client';

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
