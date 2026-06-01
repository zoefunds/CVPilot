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
    // Bootstrap the current user on mount / token change. loadMe synchronizes
    // React state with an external system (the stored token + /me endpoint),
    // which is the documented exception to react-hooks/set-state-in-effect.
    // eslint-disable-next-line react-hooks/set-state-in-effect
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
