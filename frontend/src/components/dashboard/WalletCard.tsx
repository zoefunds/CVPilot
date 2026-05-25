'use client';

import { useState } from 'react';
import { ApiError, walletApi } from '@/lib/api';
import { useToast } from '@/contexts/ToastContext';
import { LOW_BALANCE_WEI, useWallet } from '@/contexts/WalletContext';

export function WalletCard() {
  const { wallet, isLoading, error, refresh } = useWallet();
  const [revealed, setRevealed] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const { push } = useToast();

  async function copy(text: string, label: string) {
    try {
      await navigator.clipboard.writeText(text);
      push({ tone: 'success', title: 'Copied.', message: label });
    } catch {
      push({ tone: 'error', title: 'Could not copy.' });
    }
  }

  async function exportKey() {
    if (revealed) { setRevealed(null); return; }
    setExporting(true);
    try {
      const x = await walletApi.export();
      setRevealed(x.private_key);
      push({
        tone: 'info',
        title: 'Private key revealed.',
        message: 'Save it offline. CVPilot will never ask for it.',
      });
    } catch (e) {
      push({
        tone: 'error',
        title: 'Could not export.',
        message: e instanceof ApiError ? e.message : undefined,
      });
    } finally {
      setExporting(false);
    }
  }

  if (error && !wallet) {
    return (
      <div className="rounded-2xl border border-[#9b2226]/30 bg-[#9b2226]/10 p-5 text-sm text-[#9b2226]">
        {error}
      </div>
    );
  }

  if (!wallet) {
    return (
      <div className="rounded-2xl border border-[#1a1814]/10 bg-white/50 p-5 text-sm text-[#3a342c]">
        Loading wallet.
      </div>
    );
  }

  const lowBalance = wallet.balance_wei < LOW_BALANCE_WEI;

  return (
    <div className="rounded-2xl border border-[#1a1814]/10 bg-white/60 p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <h2 className="font-serif text-2xl">Your GenLayer wallet.</h2>
        <span className="rounded-full bg-[#2b4f3a]/10 px-3 py-1 text-[10px] uppercase tracking-[0.15em] text-[#2b4f3a]">
          StudioNet
        </span>
      </div>
      <p className="mt-2 text-sm text-[#3a342c]">
        This wallet signs your on-chain evaluations. You need GEN here for
        validators to run the LLM. Fund it on the StudioNet faucet using the
        address below.
      </p>

      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-[#1a1814]/10 bg-[#efece4]/60 p-4">
          <p className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">
            Address
          </p>
          <p className="mt-2 break-all font-mono text-xs text-[#1a1814]">
            {wallet.address}
          </p>
          <button
            type="button"
            onClick={() => copy(wallet.address, 'Wallet address')}
            className="mt-3 rounded-full border border-[#1a1814]/20 px-3 py-1 text-xs hover:bg-[#1a1814]/5"
          >
            Copy address
          </button>
        </div>

        <div className="rounded-xl border border-[#1a1814]/10 bg-[#efece4]/60 p-4">
          <p className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">
            Balance
          </p>
          <p className="mt-2 font-serif text-3xl text-[#1a1814]">
            {wallet.balance_gen}
            <span className="ml-1 text-xs text-[#3a342c]/70">GEN</span>
          </p>
          <button
            type="button"
            onClick={() => void refresh()}
            disabled={isLoading}
            className="mt-3 rounded-full border border-[#1a1814]/20 px-3 py-1 text-xs hover:bg-[#1a1814]/5 disabled:opacity-60"
          >
            {isLoading ? 'Refreshing…' : 'Refresh'}
          </button>
          {lowBalance && (
            <p className="mt-3 rounded-lg bg-[#a35f1f]/10 px-2.5 py-1.5 text-[11px] text-[#a35f1f]">
              Balance is too low to run an evaluation. Fund the wallet on the
              StudioNet faucet.
            </p>
          )}
        </div>
      </div>

      <div className="mt-5 flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={exportKey}
          disabled={exporting}
          className="rounded-full border border-[#1a1814]/30 px-4 py-2 text-sm text-[#1a1814] hover:bg-[#1a1814]/5 disabled:opacity-60"
        >
          {revealed ? 'Hide private key' : exporting ? 'Working...' : 'Export private key'}
        </button>
        <span className="text-xs text-[#3a342c]/70">
          Audited. Treat the key like a password.
        </span>
      </div>

      {revealed && (
        <div className="mt-4 rounded-xl border border-[#9b2226]/30 bg-[#9b2226]/8 p-4">
          <p className="text-[10px] uppercase tracking-[0.15em] text-[#9b2226]">
            Private key
          </p>
          <p className="mt-2 break-all font-mono text-xs text-[#9b2226]">
            {revealed}
          </p>
          <button
            type="button"
            onClick={() => copy(revealed, 'Private key')}
            className="mt-3 rounded-full border border-[#9b2226]/30 px-3 py-1 text-xs text-[#9b2226] hover:bg-[#9b2226]/15"
          >
            Copy private key
          </button>
          <p className="mt-3 text-[11px] text-[#3a342c]">
            Save this securely. Anyone who has it can move every GEN in this
            wallet. CVPilot will never ask you for it.
          </p>
        </div>
      )}
    </div>
  );
}
