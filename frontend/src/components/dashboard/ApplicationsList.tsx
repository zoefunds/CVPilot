'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { StatusBadge } from '@/components/dashboard/StatusBadge';
import { ApiError, applicationsApi } from '@/lib/api';
import type { ApplicationListItem } from '@/lib/types';

function fmtDate(s: string): string {
  try {
    return new Date(s).toLocaleString();
  } catch {
    return s;
  }
}

function hostnameOf(url: string): string {
  try {
    return new URL(url).hostname;
  } catch {
    return url;
  }
}

export function ApplicationsList() {
  const [items, setItems] = useState<ApplicationListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const data = await applicationsApi.list();
        if (alive) setItems(data);
      } catch (e) {
        if (alive) {
          setError(e instanceof ApiError ? e.message : 'Could not load.');
        }
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  if (error) {
    return (
      <div className="rounded-2xl border border-[#9b2226]/30 bg-[#9b2226]/8 p-6 text-sm text-[#9b2226]">
        {error}
      </div>
    );
  }
  if (items === null) {
    return (
      <div className="rounded-2xl border border-dashed border-[#1a1814]/20 bg-white/40 p-10 text-center text-sm text-[#3a342c]">
        Loading your evaluations.
      </div>
    );
  }
  if (items.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-[#1a1814]/20 bg-white/40 p-10 text-center text-sm text-[#3a342c]">
        Your evaluation history will appear here once you run your first
        scoring pass.
      </div>
    );
  }
  return (
    <ul className="divide-y divide-[#d9d5c8] rounded-2xl border border-[#1a1814]/10 bg-white/40">
      {items.map((a) => (
        <li key={a.id}>
          <Link
            href={`/dashboard/applications/${a.id}`}
            className="flex flex-col gap-2 px-5 py-4 hover:bg-white/60 sm:flex-row sm:items-center sm:justify-between"
          >
            <div className="min-w-0">
              <p className="truncate font-medium text-[#1a1814]">
                {a.job_title || hostnameOf(a.job_url)}
              </p>
              <p className="truncate text-xs text-[#3a342c]/70">
                {a.job_url}
              </p>
            </div>
            <div className="flex items-center gap-4 text-xs text-[#3a342c]/80">
              <span>{fmtDate(a.created_at)}</span>
              <StatusBadge status={a.status} />
            </div>
          </Link>
        </li>
      ))}
    </ul>
  );
}
