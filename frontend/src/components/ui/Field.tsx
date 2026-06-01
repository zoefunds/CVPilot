import type { ReactNode } from "react";

interface FieldProps {
  label: string;
  hint?: string;
  children: ReactNode;
}

export function Field({ label, hint, children }: FieldProps) {
  return (
    <label className="block">
      <span className="text-[11px] font-semibold uppercase tracking-[0.12em] text-[#4b463f]">
        {label}
      </span>
      <div className="mt-2">{children}</div>
      {hint ? (
        <p className="mt-1.5 text-[12px] text-[#7c766e]">{hint}</p>
      ) : null}
    </label>
  );
}
