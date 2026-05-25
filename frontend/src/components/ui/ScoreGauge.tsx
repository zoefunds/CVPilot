interface Props {
  value: number | null;
  label: string;
  size?: number;
  hint?: string;
}

function bandColor(v: number): string {
  if (v >= 75) return '#2b4f3a';
  if (v >= 50) return '#a35f1f';
  return '#9b2226';
}

export function ScoreGauge({ value, label, size = 132, hint }: Props) {
  const v = typeof value === 'number' ? Math.max(0, Math.min(100, value)) : 0;
  const shown = typeof value === 'number' ? value : '—';
  const stroke = 10;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const dash = (v / 100) * c;
  const color = bandColor(v);
  return (
    <div className="flex flex-col items-center text-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            stroke="rgba(26,24,20,0.08)"
            strokeWidth={stroke}
            fill="none"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            stroke={color}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={`${dash} ${c}`}
            fill="none"
            style={{ transition: 'stroke-dasharray 700ms ease-out' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-serif text-4xl text-[#1a1814]">{shown}</span>
          <span className="text-[10px] uppercase tracking-[0.15em] text-[#3a342c]/70">
            / 100
          </span>
        </div>
      </div>
      <p className="mt-3 text-xs uppercase tracking-[0.15em] text-[#3a342c]">
        {label}
      </p>
      {hint && (
        <p className="mt-1 max-w-[18ch] text-[11px] leading-snug text-[#3a342c]/70">
          {hint}
        </p>
      )}
    </div>
  );
}
