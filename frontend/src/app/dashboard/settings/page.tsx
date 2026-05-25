'use client';

import { useState } from 'react';
import { Alert } from '@/components/ui/Alert';
import { Container } from '@/components/ui/Container';
import { WalletCard } from '@/components/dashboard/WalletCard';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/contexts/ToastContext';

function fmtDate(s: string | undefined): string {
  if (!s) return '—';
  try { return new Date(s).toLocaleString(); } catch { return s; }
}

export default function SettingsPage() {
  const { user, signOut } = useAuth();
  const { push } = useToast();
  const [confirming, setConfirming] = useState(false);

  async function copy(text: string, label: string) {
    try {
      await navigator.clipboard.writeText(text);
      push({ tone: 'success', title: 'Copied', message: `${label} on clipboard.` });
    } catch {
      push({ tone: 'error', title: 'Could not copy', message: 'Browser blocked clipboard access.' });
    }
  }

  return (
    <Container className="py-16">
      <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">Settings</p>
      <h1 className="mt-3 font-serif text-5xl">Your account.</h1>

      <section className="mt-10">
        <WalletCard />
      </section>

      <section className="mt-12 grid gap-6 sm:grid-cols-2">
        <Row label="Email" value={user?.email || ''} onCopy={() => copy(user?.email || '', 'Email')} />
        <Row label="Full name" value={user?.full_name || 'Not set'} />
        <Row label="Account ID" value={user?.id || ''} mono onCopy={() => copy(user?.id || '', 'Account ID')} />
        <Row label="Member since" value={fmtDate(user?.created_at)} />
        <Row label="Account status" value={user?.is_active ? 'Active' : 'Disabled'} />
        <Row label="Tier" value={user?.is_premium ? 'Premium' : 'Free (everything unlocked)'} />
      </section>

      <section className="mt-14 max-w-2xl">
        <h2 className="font-serif text-2xl">Sign out</h2>
        <p className="mt-3 text-sm text-[#3a342c]">
          We will clear your tokens from this browser. Your data stays safe.
        </p>
        {confirming ? (
          <Alert tone="info">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <span>Confirm sign out?</span>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setConfirming(false)}
                  className="rounded-full border border-[#1a1814]/30 px-3 py-1.5 text-xs text-[#1a1814] hover:bg-[#1a1814]/5"
                >Cancel</button>
                <button
                  type="button"
                  onClick={() => { signOut(); push({ tone: 'info', title: 'Signed out' }); }}
                  className="rounded-full bg-[#9b2226] px-3 py-1.5 text-xs text-white hover:bg-[#7c1a1f]"
                >Sign me out</button>
              </div>
            </div>
          </Alert>
        ) : (
          <button
            type="button"
            onClick={() => setConfirming(true)}
            className="mt-4 inline-flex items-center justify-center rounded-full border border-[#1a1814]/30 px-5 py-2.5 text-sm text-[#1a1814] hover:bg-[#1a1814]/5"
          >Sign out of this browser</button>
        )}
      </section>
    </Container>
  );
}

function Row({ label, value, mono, onCopy }: {
  label: string; value: string; mono?: boolean; onCopy?: () => void;
}) {
  return (
    <div className="rounded-2xl border border-[#1a1814]/10 bg-white/50 p-5">
      <p className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">{label}</p>
      <div className="mt-2 flex items-center justify-between gap-3">
        <p className={`min-w-0 truncate text-[#1a1814] ${mono ? 'font-mono text-sm' : ''}`}>{value}</p>
        {onCopy && (
          <button
            type="button"
            onClick={onCopy}
            className="shrink-0 rounded-full border border-[#1a1814]/20 px-3 py-1 text-xs text-[#1a1814] hover:bg-[#1a1814]/5"
          >Copy</button>
        )}
      </div>
    </div>
  );
}
