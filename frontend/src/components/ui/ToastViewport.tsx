'use client';

import { useToast } from '@/contexts/ToastContext';

const toneStyles: Record<string, string> = {
  success: 'border-[#2b4f3a]/30 bg-[#2b4f3a]/12 text-[#1f3a2a]',
  error: 'border-[#9b2226]/30 bg-[#9b2226]/12 text-[#9b2226]',
  info: 'border-[#1a1814]/15 bg-white/80 text-[#1a1814]',
};

export function ToastViewport() {
  const { toasts, dismiss } = useToast();
  return (
    <div className="pointer-events-none fixed inset-x-0 top-4 z-50 flex flex-col items-center gap-2 px-4 sm:items-end sm:right-4 sm:left-auto sm:top-6">
      {toasts.map((t) => (
        <div
          key={t.id}
          role="status"
          className={`pointer-events-auto w-full max-w-sm rounded-2xl border px-4 py-3 shadow-[0_18px_45px_-25px_rgba(26,24,20,0.45)] backdrop-blur ${toneStyles[t.tone]}`}
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-medium">{t.title}</p>
              {t.message && (
                <p className="mt-0.5 text-xs opacity-80">{t.message}</p>
              )}
            </div>
            <button
              type="button"
              onClick={() => dismiss(t.id)}
              className="rounded-full px-2 py-1 text-xs opacity-60 hover:opacity-100"
              aria-label="Dismiss"
            >
              ✕
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
