'use client';

import { useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

// Routes a signed-in but unverified user is still allowed to reach. Without
// this list they'd be bounced off the verify-pending page they just landed on.
const VERIFY_ALLOWED = ['/verify-email-pending', '/dashboard/settings'];

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, isLoading } = useAuth();

  const needsVerify =
    !isLoading &&
    isAuthenticated &&
    user !== null &&
    !user.email_verified &&
    !VERIFY_ALLOWED.some((p) => pathname === p || pathname?.startsWith(`${p}/`));

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace('/signin');
      return;
    }
    if (needsVerify) {
      router.replace('/verify-email-pending');
    }
  }, [isLoading, isAuthenticated, needsVerify, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-sm text-[#3a342c]">
        Loading your account.
      </div>
    );
  }
  if (!isAuthenticated || needsVerify) {
    return null;
  }
  return <>{children}</>;
}
