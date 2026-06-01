import type { ReactNode } from "react";

type Tone = "error" | "info" | "success" | "warning";

const toneStyles: Record<Tone, string> = {
  error: "border-red-200 bg-red-50 text-red-800",
  info: "border-[#cdc5bc] bg-[#f1eee6] text-[#1c1c17]",
  success: "border-emerald-200 bg-emerald-50 text-emerald-800",
  warning: "border-amber-200 bg-amber-50 text-amber-800",
};

export function Alert({
  tone = "info",
  children,
}: {
  tone?: Tone;
  children: ReactNode;
}) {
  return (
    <div
      className={[
        "rounded-xl border px-4 py-3 text-[13px] leading-relaxed",
        toneStyles[tone],
      ].join(" ")}
      role={tone === "error" ? "alert" : undefined}
    >
      {children}
    </div>
  );
}
