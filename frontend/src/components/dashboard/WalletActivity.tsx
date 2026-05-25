'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { ApiError, walletApi } from '@/lib/api';
import type { WalletActivityItem } from '@/lib/types';

function fmtTime(s: string): string {
  try { return new Date(s).toLocaleString(); } catch { return s; }
}

function shortHash(h: string | null | undefined): string {
  if (!h) return '—';
  if (h.length <= 14) return h;
  return `${h.slice(0, 8)}…${h.slice(-6)}`;
}

export function WalletActivity({ refreshKey }: { refreshKey?: number }) {
  const [items, setItems] = useState<WalletActivityItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const data = await walletApi.activity();
        if (alive) setItems(data);
      } catch (e) {
        if (alive) setError(e instanceof ApiError ? e.message : 'Could not load activity.');
      }
    })();
    return () => { alive = false; };
  }, [refreshKey]);

  return (
    <section>
      <div className="flex items-baseline justify-between">
        <h2 className="font-serif text-2xl">Activity.</h2>
        <span className="text-[10px] uppercase tracking-[0.15em] text-[#3a342c]/70">
          on-chain
        </span>
      </div>
      <p className="mt-2 text-sm text-[#3a342c]">
        Your verifiable evaluations and outgoing GEN transfers.
      </p>

      {error && (
        <div className="mt-4 rounded-2xl border border-[#9b2226]/30 bg-[#9b2226]/10 p-4 text-sm text-[#9b2226]">
          {error}
        </div>
      )}

      {items === null && !error && (
        <p className="mt-4 text-sm text-[#3a342c]">Loading.</p>
      )}

      {items && items.length === 0 && (
        <div className="mt-4 rounded-2xl border border-dashed border-[#1a1814]/20 bg-white/40 p-8 text-center text-sm text-[#3a342c]">
          No on-chain activity yet. Run an evaluation or send GEN to begin
          your history.
        </div>
      )}

      {items && items.length > 0 && (
        <ul className="mt-4 divide-y divide-[#d9d5c8] overflow-hidden rounded-2xl border border-[#1a1814]/10 bg-white/40">
          {items.map((it, i) => (
            <li key={(it.tx_hash || it.timestamp) + i} className="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
              <div className="min-w-0">
                <p className="flex flex-wrap items-center gap-2">
                  <span className={[
                    'rounded-full px-2.5 py-0.5 text-[10px] uppercase tracking-[0.15em]',
                    it.kind === 'evaluation'
                      ? 'bg-[#2b4f3a]/12 text-[#2b4f3a]'
                      : 'bg-[#1a1814]/10 text-[#1a1814]',
                  ].join(' ')}>
                    {it.kind === 'evaluation' ? 'Evaluation' : 'Send'}
                  </span>
                  <span className="truncate font-medium text-[#1a1814]">
                    {it.description}
                  </span>
                </p>
                <p className="mt-1 text-xs text-[#3a342c]/70">
                  {fmtTime(it.timestamp)}
                  {it.amount_gen && ` · ${it.amount_gen} GEN`}
                </p>
              </div>
              <div className="flex items-center gap-3 text-xs">
                <span className="font-mono text-[#3a342c]/80">
                  {shortHash(it.tx_hash)}
                </span>
                {it.kind === 'evaluation' && it.application_id && (
                  <Link
                    href={`/dashboard/applications/${it.application_id}`}
                    className="rounded-full border border-[#1a1814]/20 px-3 py-1 text-[#1a1814] hover:bg-[#1a1814]/5"
                  >
                    View
                  </Link>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
