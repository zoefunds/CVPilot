export function ScoreCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: number | null;
  hint?: string;
}) {
  const v = typeof value === 'number' ? value : 0;
  const shown = typeof value === 'number' ? value : '—';
  const cls =
    v >= 75
      ? 'bg-[#2b4f3a]'
      : v >= 50
      ? 'bg-[#a35f1f]'
      : 'bg-[#9b2226]';
  return (
    <div className="rounded-2xl border border-[#1a1814]/10 bg-white/60 p-5">
      <div className="flex items-baseline justify-between">
        <span className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">
          {label}
        </span>
        <span className="font-serif text-3xl">{shown}</span>
      </div>
      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-[#1a1814]/10">
        <div
          className={`h-full ${cls}`}
          style={{ width: `${Math.max(0, Math.min(100, v))}%` }}
        />
      </div>
      {hint && (
        <p className="mt-2 text-[11px] leading-snug text-[#3a342c]/80">
          {hint}
        </p>
      )}
    </div>
  );
}
