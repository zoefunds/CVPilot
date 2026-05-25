'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { StatusBadge } from '@/components/dashboard/StatusBadge';
import { Alert } from '@/components/ui/Alert';
import { Container } from '@/components/ui/Container';
import { ApiError, adminApi } from '@/lib/api';
import type {
  AdminApplicationListItem,
  AdminStats,
  AdminUserListItem,
  ApplicationStatus,
} from '@/lib/types';

function StatTile({
  label,
  value,
  hint,
}: {
  label: string;
  value: string | number;
  hint?: string;
}) {
  return (
    <div className="rounded-2xl border border-[#1a1814]/10 bg-white/60 p-5">
      <p className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">
        {label}
      </p>
      <p className="mt-2 font-serif text-4xl text-[#1a1814]">{value}</p>
      {hint && <p className="mt-1 text-xs text-[#3a342c]/70">{hint}</p>}
    </div>
  );
}

export default function AdminOverviewPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<AdminUserListItem[] | null>(null);
  const [apps, setApps] = useState<AdminApplicationListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const [s, u, a] = await Promise.all([
          adminApi.stats(),
          adminApi.listUsers(5, 0),
          adminApi.listApplications({ limit: 5 }),
        ]);
        if (!alive) return;
        setStats(s);
        setUsers(u);
        setApps(a);
      } catch (e) {
        if (!alive) return;
        setError(e instanceof ApiError ? e.message : 'Could not load admin data.');
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  return (
    <Container className="py-14">
      <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">
        Admin
      </p>
      <h1 className="mt-2 font-serif text-5xl">Overview.</h1>

      {error && (
        <div className="mt-6">
          <Alert tone="error">{error}</Alert>
        </div>
      )}

      <section className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile label="Users" value={stats?.user_count ?? '—'} hint={`+${stats?.last_24h_users ?? 0} last 24h`} />
        <StatTile label="Applications" value={stats?.application_count ?? '—'} hint={`+${stats?.last_24h_applications ?? 0} last 24h`} />
        <StatTile label="Evaluations complete" value={stats?.evaluations_complete ?? '—'} />
        <StatTile label="Evaluations failed" value={stats?.evaluations_failed ?? '—'} />
      </section>

      {stats?.by_status && Object.keys(stats.by_status).length > 0 && (
        <section className="mt-10">
          <h2 className="font-serif text-2xl">Applications by status</h2>
          <div className="mt-4 flex flex-wrap gap-3">
            {Object.entries(stats.by_status).map(([s, n]) => (
              <div
                key={s}
                className="flex items-center gap-3 rounded-full border border-[#1a1814]/10 bg-white/60 px-3 py-1.5"
              >
                <StatusBadge status={s as ApplicationStatus} />
                <span className="text-sm text-[#1a1814]">{n}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="mt-12">
        <div className="flex items-baseline justify-between">
          <h2 className="font-serif text-2xl">Recent users</h2>
          <Link
            href="/dashboard/admin/users"
            className="text-xs uppercase tracking-[0.15em] text-[#3a342c] hover:text-[#1a1814]"
          >
            See all
          </Link>
        </div>
        <div className="mt-4 overflow-hidden rounded-2xl border border-[#1a1814]/10 bg-white/40">
          {users === null ? (
            <p className="p-6 text-sm text-[#3a342c]">Loading.</p>
          ) : users.length === 0 ? (
            <p className="p-6 text-sm text-[#3a342c]">No users yet.</p>
          ) : (
            <ul className="divide-y divide-[#d9d5c8]">
              {users.map((u) => (
                <li
                  key={u.id}
                  className="flex flex-wrap items-center justify-between gap-3 px-5 py-3"
                >
                  <div className="min-w-0">
                    <p className="truncate font-medium text-[#1a1814]">
                      {u.email}
                    </p>
                    <p className="truncate text-xs text-[#3a342c]/70">
                      {u.full_name || 'No name'} · {u.application_count} application
                      {u.application_count === 1 ? '' : 's'}
                    </p>
                  </div>
                  {u.is_superuser && (
                    <span className="rounded-full bg-[#2b4f3a]/12 px-2.5 py-0.5 text-[10px] uppercase tracking-[0.15em] text-[#2b4f3a]">
                      Admin
                    </span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      <section className="mt-12">
        <div className="flex items-baseline justify-between">
          <h2 className="font-serif text-2xl">Recent applications</h2>
          <Link
            href="/dashboard/admin/applications"
            className="text-xs uppercase tracking-[0.15em] text-[#3a342c] hover:text-[#1a1814]"
          >
            See all
          </Link>
        </div>
        <div className="mt-4 overflow-hidden rounded-2xl border border-[#1a1814]/10 bg-white/40">
          {apps === null ? (
            <p className="p-6 text-sm text-[#3a342c]">Loading.</p>
          ) : apps.length === 0 ? (
            <p className="p-6 text-sm text-[#3a342c]">No applications yet.</p>
          ) : (
            <ul className="divide-y divide-[#d9d5c8]">
              {apps.map((a) => (
                <li key={a.id}>
                  <Link
                    href={`/dashboard/admin/applications/${a.id}`}
                    className="flex flex-wrap items-center justify-between gap-3 px-5 py-3 hover:bg-white/60"
                  >
                    <div className="min-w-0">
                      <p className="truncate font-medium text-[#1a1814]">
                        {a.job_title || a.job_url}
                      </p>
                      <p className="truncate text-xs text-[#3a342c]/70">
                        {a.user_email}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      {a.competitiveness !== null && (
                        <span className="font-serif text-lg text-[#1a1814]">
                          {a.competitiveness}
                          <span className="text-xs text-[#3a342c]/60">/100</span>
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
      </section>
    </Container>
  );
}
