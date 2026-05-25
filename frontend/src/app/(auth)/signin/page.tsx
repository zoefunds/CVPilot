'use client';

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
