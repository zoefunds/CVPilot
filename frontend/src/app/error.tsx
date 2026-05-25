'use client';

import Link from 'next/link';
import { useEffect } from 'react';
import { Container } from '@/components/ui/Container';
import { appName } from '@/lib/brand';

export default function NestedError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
     
    console.error('App error boundary caught:', error);
  }, [error]);

  return (
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
  );
}
