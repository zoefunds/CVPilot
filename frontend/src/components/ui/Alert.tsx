import { ReactNode } from 'react';

type Tone = 'error' | 'success' | 'info';

const tones: Record<Tone, string> = {
  error: 'border-[#9b2226]/30 bg-[#9b2226]/10 text-[#9b2226]',
  success: 'border-[#2b4f3a]/30 bg-[#2b4f3a]/10 text-[#1f3a2a]',
  info: 'border-[#1a1814]/15 bg-[#1a1814]/5 text-[#1a1814]',
};

export function Alert({
  children,
  tone = 'info',
}: {
  children: ReactNode;
  tone?: Tone;
}) {
  return (
    <div className={`rounded-2xl border px-4 py-3 text-sm ${tones[tone]}`}>
      {children}
    </div>
  );
}
