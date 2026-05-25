'use client';

import Link from 'next/link';
import { ApplicationsList } from '@/components/dashboard/ApplicationsList';
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
        </div>
        <div className="mt-5">
          <ApplicationsList />
        </div>
      </section>
    </Container>
  );
}
