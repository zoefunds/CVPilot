'use client';

import { FormEvent, useEffect, useState } from 'react';
import { ApiError, walletApi } from '@/lib/api';
import { useToast } from '@/contexts/ToastContext';
import { useWallet } from '@/contexts/WalletContext';
import { Field } from '@/components/ui/Field';
import { Input } from '@/components/ui/Input';

interface Props {
  open: boolean;
  onClose: () => void;
}

const ADDR_RE = /^0x[0-9a-fA-F]{40}$/;

function isValidAmount(s: string, balanceGen: string | undefined): { ok: boolean; reason?: string } {
  const n = Number(s);
  if (!s || !Number.isFinite(n) || n <= 0) return { ok: false, reason: 'Enter an amount greater than zero.' };
  const bal = Number(balanceGen || '0');
  if (Number.isFinite(bal) && n > bal) return { ok: false, reason: 'Amount exceeds your balance.' };
  return { ok: true };
}

export function SendGenModal({ open, onClose }: Props) {
  const { wallet, refresh } = useWallet();
  const { push } = useToast();
  const [to, setTo] = useState('');
  const [amount, setAmount] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    if (open) {
      setTo(''); setAmount(''); setError(null); setConfirming(false); setBusy(false);
    }
  }, [open]);

  if (!open) return null;

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!ADDR_RE.test(to.trim())) {
      setError('Recipient must be a 0x address (42 characters).');
      return;
    }
    if (wallet && to.trim().toLowerCase() === wallet.address.toLowerCase()) {
      setError('You cannot send to your own wallet.');
      return;
    }
    const v = isValidAmount(amount, wallet?.balance_gen);
    if (!v.ok) { setError(v.reason || 'Invalid amount.'); return; }
    setConfirming(true);
  }

  async function confirm() {
    setBusy(true);
    setError(null);
    try {
      const res = await walletApi.send({ to_address: to.trim(), amount_gen: amount });
      push({
        tone: 'success',
        title: 'GEN sent.',
        message: `tx ${res.tx_hash.slice(0, 10)}…`,
      });
      void refresh();
      onClose();
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : 'Send failed.';
      setError(msg);
      setConfirming(false);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-30 flex items-center justify-center bg-[#1a1814]/40 backdrop-blur-sm p-4"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="w-full max-w-md rounded-3xl border border-[#1a1814]/10 bg-[#efece4] p-6 shadow-[0_30px_80px_-30px_rgba(26,24,20,0.5)]">
        <div className="flex items-baseline justify-between">
          <h2 className="font-serif text-2xl">Send GEN</h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full px-2 py-1 text-xs text-[#3a342c] hover:bg-[#1a1814]/5"
          >
            Close
          </button>
        </div>
        <p className="mt-2 text-xs text-[#3a342c]">
          From <span className="font-mono">{wallet?.address.slice(0, 8)}…{wallet?.address.slice(-6)}</span>
          {' · '}Balance {wallet?.balance_gen || '0'} GEN
        </p>

        {!confirming ? (
          <form onSubmit={onSubmit} className="mt-5 flex flex-col gap-4">
            <Field label="Recipient" hint="A 0x address on StudioNet.">
              <Input
                value={to}
                onChange={(e) => setTo(e.target.value)}
                placeholder="0x…"
                autoComplete="off"
                spellCheck={false}
                className="font-mono text-sm"
                required
              />
            </Field>
            <Field label="Amount" hint={`Maximum ${wallet?.balance_gen || '0'} GEN.`}>
              <Input
                type="number"
                step="any"
                min="0"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.5"
                required
              />
            </Field>
            {error && (
              <p className="rounded-2xl border border-[#9b2226]/30 bg-[#9b2226]/10 px-4 py-3 text-sm text-[#9b2226]">
                {error}
              </p>
            )}
            <div className="mt-2 flex flex-wrap gap-2">
              <button
                type="submit"
                className="inline-flex items-center justify-center rounded-full bg-[#1a1814] px-5 py-2.5 text-sm font-medium text-[#efece4] hover:bg-[#3a342c]"
              >
                Review
              </button>
              <button
                type="button"
                onClick={onClose}
                className="inline-flex items-center justify-center rounded-full border border-[#1a1814]/30 px-5 py-2.5 text-sm text-[#1a1814] hover:bg-[#1a1814]/5"
              >
                Cancel
              </button>
            </div>
          </form>
        ) : (
          <div className="mt-5 flex flex-col gap-4">
            <div className="rounded-2xl border border-[#1a1814]/15 bg-white/60 p-4">
              <p className="text-[10px] uppercase tracking-[0.15em] text-[#3a342c]">Confirm</p>
              <p className="mt-2 text-sm text-[#1a1814]">
                Send <span className="font-medium">{amount} GEN</span> to:
              </p>
              <p className="mt-1 break-all font-mono text-xs text-[#1a1814]">{to.trim()}</p>
              <p className="mt-3 text-xs text-[#3a342c]/70">
                This transfer is irreversible. Double-check the address.
              </p>
            </div>
            {error && (
              <p className="rounded-2xl border border-[#9b2226]/30 bg-[#9b2226]/10 px-4 py-3 text-sm text-[#9b2226]">
                {error}
              </p>
            )}
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={confirm}
                disabled={busy}
                className="inline-flex items-center justify-center rounded-full bg-[#2b4f3a] px-5 py-2.5 text-sm font-medium text-[#efece4] hover:bg-[#1f3a2a] disabled:opacity-60"
              >
                {busy ? 'Sending…' : 'Confirm send'}
              </button>
              <button
                type="button"
                onClick={() => { setConfirming(false); setError(null); }}
                disabled={busy}
                className="inline-flex items-center justify-center rounded-full border border-[#1a1814]/30 px-5 py-2.5 text-sm text-[#1a1814] hover:bg-[#1a1814]/5 disabled:opacity-60"
              >
                Back
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
