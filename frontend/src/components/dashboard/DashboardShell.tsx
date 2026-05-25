'use client';

import Link from 'next/link';
import { Container } from '@/components/ui/Container';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/contexts/ToastContext';
import { WalletBalanceChip } from '@/components/dashboard/WalletBalanceChip';
import { appName } from '@/lib/brand';

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const { user, signOut } = useAuth();
  const { push } = useToast();
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-20 border-b border-[#d9d5c8] bg-[#efece4]/85 backdrop-blur supports-[backdrop-filter]:bg-[#efece4]/70">
        <Container className="flex h-16 items-center justify-between gap-3">
          <Link href="/dashboard" className="font-serif text-2xl">
            {appName}
          </Link>
          <nav className="flex items-center gap-3 text-sm sm:gap-4">
            <Link
              href="/dashboard"
              className="hidden text-[#3a342c] hover:text-[#1a1814] sm:inline"
            >
              Dashboard
            </Link>
            <Link
              href="/dashboard/new"
              className="text-[#3a342c] hover:text-[#1a1814]"
            >
              New
            </Link>
            <Link
              href="/dashboard/settings"
              className="text-[#3a342c] hover:text-[#1a1814]"
            >
              Settings
            </Link>
            {user?.is_superuser && (
              <Link
                href="/dashboard/admin"
                className="inline-flex items-center gap-1.5 rounded-full bg-[#2b4f3a]/12 px-2.5 py-1 text-xs uppercase tracking-[0.15em] text-[#2b4f3a] hover:bg-[#2b4f3a]/20"
              >
                <span className="h-1.5 w-1.5 rounded-full bg-[#2b4f3a]" />
                Admin
              </Link>
            )}
            <WalletBalanceChip />
            <button
              type="button"
              onClick={() => {
                signOut();
                push({ tone: 'info', title: 'Signed out' });
              }}
              className="rounded-full border border-[#1a1814]/30 px-3 py-1.5 text-xs text-[#1a1814] hover:bg-[#1a1814]/5"
            >
              Sign out
            </button>
          </nav>
        </Container>
      </header>
      <main className="flex-1">{children}</main>
    </div>
  );
}
