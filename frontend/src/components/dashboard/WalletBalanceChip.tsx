'use client';

import Link from 'next/link';
import { LOW_BALANCE_WEI, useWallet } from '@/contexts/WalletContext';

function formatGen(balance: string | undefined): string {
  if (!balance) return '—';
  // Trim trailing zeros for readability while preserving small balances.
  const num = Number(balance);
  if (Number.isNaN(num)) return balance;
  if (num >= 1) return num.toFixed(2);
  if (num >= 0.001) return num.toFixed(4);
  return num === 0 ? '0' : num.toExponential(2);
}

export function WalletBalanceChip() {
  const { wallet, isLoading } = useWallet();

  if (!wallet) {
    return (
      <span className="hidden items-center gap-1.5 rounded-full border border-[#1a1814]/15 bg-white/40 px-3 py-1 text-[10px] uppercase tracking-[0.15em] text-[#3a342c]/70 sm:inline-flex">
        <span className="h-1.5 w-1.5 rounded-full bg-[#3a342c]/40" />
        {isLoading ? 'Wallet…' : 'Wallet'}
      </span>
    );
  }

  const low = wallet.balance_wei < LOW_BALANCE_WEI;
  const cls = low
    ? 'border-[#a35f1f]/40 bg-[#a35f1f]/12 text-[#a35f1f]'
    : 'border-[#2b4f3a]/30 bg-[#2b4f3a]/10 text-[#2b4f3a]';
  const dot = low ? 'bg-[#a35f1f]' : 'bg-[#2b4f3a]';

  return (
    <Link
      href="/dashboard/settings"
      className={[
        'inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs transition-colors',
        cls,
        'hover:opacity-80',
      ].join(' ')}
      title={low ? 'Low balance. Top up to keep submitting.' : 'Your GenLayer wallet balance'}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${dot}`} />
      <span className="font-medium">{formatGen(wallet.balance_gen)} GEN</span>
    </Link>
  );
}
