import { ReactNode } from 'react';

export function Field({
  label,
  hint,
  error,
  children,
}: {
  label: string;
  hint?: string;
  error?: string;
  children: ReactNode;
}) {
  return (
    <div>
      <label className="mb-1.5 block text-xs uppercase tracking-[0.15em] text-[#3a342c]">
        {label}
      </label>
      {children}
      {hint && !error && (
        <p className="mt-1.5 text-xs text-[#3a342c]/70">{hint}</p>
      )}
      {error && (
        <p className="mt-1.5 text-xs text-[#9b2226]">{error}</p>
      )}
    </div>
  );
}
