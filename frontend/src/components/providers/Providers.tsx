'use client';

import { AuthProvider } from '@/contexts/AuthContext';
import { ToastProvider } from '@/contexts/ToastContext';
import { WalletProvider } from '@/contexts/WalletContext';
import { ToastViewport } from '@/components/ui/ToastViewport';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ToastProvider>
      <AuthProvider>
        <WalletProvider>
          {children}
          <ToastViewport />
        </WalletProvider>
      </AuthProvider>
    </ToastProvider>
  );
}
