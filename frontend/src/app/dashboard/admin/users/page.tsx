'use client';

import { useEffect, useState } from 'react';
import { Alert } from '@/components/ui/Alert';
import { Container } from '@/components/ui/Container';
import { useToast } from '@/contexts/ToastContext';
import { ApiError, adminApi } from '@/lib/api';
import type { AdminUserListItem } from '@/lib/types';

function fmt(s: string | null | undefined): string {
  if (!s) return '—';
  try {
    return new Date(s).toLocaleString();
  } catch {
    return s;
  }
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUserListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { push } = useToast();

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const u = await adminApi.listUsers(200);
        if (alive) setUsers(u);
      } catch (e) {
        if (alive) setError(e instanceof ApiError ? e.message : 'Could not load.');
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  async function copy(v: string, label: string) {
    try {
      await navigator.clipboard.writeText(v);
      push({ tone: 'success', title: 'Copied', message: `${label} on clipboard.` });
    } catch {
      push({ tone: 'error', title: 'Could not copy.' });
    }
  }

  return (
    <Container className="py-14">
      <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">Admin</p>
      <h1 className="mt-2 font-serif text-5xl">All users.</h1>

      {error && (
        <div className="mt-6">
          <Alert tone="error">{error}</Alert>
        </div>
      )}

      <div className="mt-8 overflow-hidden rounded-2xl border border-[#1a1814]/10 bg-white/40">
        {users === null ? (
          <p className="p-6 text-sm text-[#3a342c]">Loading.</p>
        ) : users.length === 0 ? (
          <p className="p-6 text-sm text-[#3a342c]">No users yet.</p>
        ) : (
          <ul className="divide-y divide-[#d9d5c8]">
            {users.map((u) => (
              <li key={u.id} className="px-5 py-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="truncate font-medium text-[#1a1814]">
                        {u.email}
                      </p>
                      {u.is_superuser && (
                        <span className="rounded-full bg-[#2b4f3a]/12 px-2 py-0.5 text-[10px] uppercase tracking-[0.15em] text-[#2b4f3a]">
                          Admin
                        </span>
                      )}
                      {!u.is_active && (
                        <span className="rounded-full bg-[#9b2226]/12 px-2 py-0.5 text-[10px] uppercase tracking-[0.15em] text-[#9b2226]">
                          Disabled
                        </span>
                      )}
                    </div>
                    <p className="mt-0.5 text-xs text-[#3a342c]/70">
                      {u.full_name || 'No name'}
                    </p>
                    <p className="mt-2 font-mono text-[10px] text-[#3a342c]/60">
                      {u.id}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-1 text-xs text-[#3a342c]">
                    <span>{u.application_count} applications</span>
                    <span className="text-[#3a342c]/70">
                      Joined {fmt(u.created_at)}
                    </span>
                    <span className="text-[#3a342c]/70">
                      Last app {fmt(u.last_application_at)}
                    </span>
                    <div className="mt-1 flex gap-2">
                      <button
                        type="button"
                        onClick={() => copy(u.email, 'Email')}
                        className="rounded-full border border-[#1a1814]/20 px-2.5 py-0.5 text-[10px] uppercase tracking-[0.15em] text-[#1a1814] hover:bg-[#1a1814]/5"
                      >
                        Copy email
                      </button>
                      <button
                        type="button"
                        onClick={() => copy(u.id, 'Account ID')}
                        className="rounded-full border border-[#1a1814]/20 px-2.5 py-0.5 text-[10px] uppercase tracking-[0.15em] text-[#1a1814] hover:bg-[#1a1814]/5"
                      >
                        Copy ID
                      </button>
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Container>
  );
}
