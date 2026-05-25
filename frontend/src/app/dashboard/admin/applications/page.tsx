'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { StatusBadge } from '@/components/dashboard/StatusBadge';
import { Alert } from '@/components/ui/Alert';
import { Container } from '@/components/ui/Container';
import { ApiError, adminApi } from '@/lib/api';
import type {
  AdminApplicationListItem,
  ApplicationStatus,
} from '@/lib/types';

const STATUS_OPTIONS: { value: '' | ApplicationStatus; label: string }[] = [
  { value: '', label: 'All' },
  { value: 'pending', label: 'Pending' },
  { value: 'processing', label: 'Processing' },
  { value: 'ready', label: 'Ready' },
  { value: 'evaluating', label: 'Evaluating' },
  { value: 'complete', label: 'Complete' },
  { value: 'failed', label: 'Failed' },
];

function fmt(s: string): string {
  try {
    return new Date(s).toLocaleString();
  } catch {
    return s;
  }
}

export default function AdminApplicationsPage() {
  const [status, setStatus] = useState<'' | ApplicationStatus>('');
  const [apps, setApps] = useState<AdminApplicationListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    setApps(null);
    setError(null);
    (async () => {
      try {
        const items = await adminApi.listApplications({
          status: status || undefined,
          limit: 200,
        });
        if (alive) setApps(items);
      } catch (e) {
        if (alive) setError(e instanceof ApiError ? e.message : 'Could not load.');
      }
    })();
    return () => {
      alive = false;
    };
  }, [status]);

  return (
    <Container className="py-14">
      <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">Admin</p>
      <h1 className="mt-2 font-serif text-5xl">All applications.</h1>

      <div className="mt-8 flex flex-wrap items-center gap-2">
        {STATUS_OPTIONS.map((opt) => (
          <button
            key={opt.value || 'all'}
            type="button"
            onClick={() => setStatus(opt.value)}
            className={[
              'rounded-full px-3 py-1.5 text-xs uppercase tracking-[0.15em] transition-colors',
              status === opt.value
                ? 'bg-[#1a1814] text-[#efece4]'
                : 'border border-[#1a1814]/20 text-[#1a1814] hover:bg-[#1a1814]/5',
            ].join(' ')}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="mt-6">
          <Alert tone="error">{error}</Alert>
        </div>
      )}

      <div className="mt-6 overflow-hidden rounded-2xl border border-[#1a1814]/10 bg-white/40">
        {apps === null ? (
          <p className="p-6 text-sm text-[#3a342c]">Loading.</p>
        ) : apps.length === 0 ? (
          <p className="p-6 text-sm text-[#3a342c]">No applications match.</p>
        ) : (
          <ul className="divide-y divide-[#d9d5c8]">
            {apps.map((a) => (
              <li key={a.id}>
                <Link
                  href={`/dashboard/admin/applications/${a.id}`}
                  className="flex flex-wrap items-center justify-between gap-3 px-5 py-4 hover:bg-white/60"
                >
                  <div className="min-w-0">
                    <p className="truncate font-medium text-[#1a1814]">
                      {a.job_title || a.job_url}
                    </p>
                    <p className="truncate text-xs text-[#3a342c]/70">
                      {a.user_email} · {fmt(a.created_at)}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 text-xs">
                    {a.competitiveness !== null && (
                      <span className="font-serif text-lg text-[#1a1814]">
                        {a.competitiveness}
                        <span className="text-[10px] text-[#3a342c]/60">/100</span>
                      </span>
                    )}
                    <StatusBadge status={a.status} />
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Container>
  );
}
