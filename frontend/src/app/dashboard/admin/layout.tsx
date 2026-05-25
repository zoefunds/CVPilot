'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { AdminGuard } from '@/components/auth/AdminGuard';
import { Container } from '@/components/ui/Container';

function NavLink({ href, label }: { href: string; label: string }) {
  const pathname = usePathname();
  const active = pathname === href || pathname?.startsWith(href + '/');
  return (
    <Link
      href={href}
      className={[
        'rounded-full px-3 py-1.5 text-xs uppercase tracking-[0.15em] transition-colors',
        active
          ? 'bg-[#1a1814] text-[#efece4]'
          : 'text-[#3a342c] hover:bg-[#1a1814]/5',
      ].join(' ')}
    >
      {label}
    </Link>
  );
}

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <AdminGuard>
      <div className="border-b border-[#d9d5c8] bg-[#efece4]/70">
        <Container className="flex flex-wrap items-center gap-2 py-3">
          <NavLink href="/dashboard/admin" label="Overview" />
          <NavLink href="/dashboard/admin/users" label="Users" />
          <NavLink href="/dashboard/admin/applications" label="Applications" />
        </Container>
      </div>
      {children}
    </AdminGuard>
  );
}
