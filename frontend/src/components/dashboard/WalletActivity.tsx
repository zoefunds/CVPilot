"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Icon } from "@/components/icons/Icon";
import { ApiError, walletApi } from "@/lib/api";
import type { WalletActivityItem } from "@/lib/types";

function fmtTime(s: string): string {
  try {
    return new Date(s).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  } catch {
    return s;
  }
}

function shortHash(h: string | null | undefined): string {
  if (!h) return "—";
  if (h.length <= 14) return h;
  return `${h.slice(0, 8)}…${h.slice(-6)}`;
}

export function WalletActivity({ refreshKey }: { refreshKey?: number }) {
  const [items, setItems] = useState<WalletActivityItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const data = await walletApi.activity();
        if (alive) setItems(data);
      } catch (e) {
        if (alive)
          setError(
            e instanceof ApiError ? e.message : "Could not load activity.",
          );
      }
    })();
    return () => {
      alive = false;
    };
  }, [refreshKey]);

  return (
    <section>
      <div className="flex items-baseline justify-between">
        <h2
          className="text-[22px] text-[#1c1c17]"
          style={{ fontFamily: "Literata, serif", fontWeight: 600 }}
        >
          Activity
        </h2>
        <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[#7c766e]">
          Onchain
        </span>
      </div>
      <p className="mt-1 text-[13px] text-[#4b463f]">
        Your verifiable evaluations and outgoing GEN transfers.
      </p>

      {error ? (
        <div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-[13px] text-red-800">
          {error}
        </div>
      ) : null}

      {items === null && !error ? (
        <div className="mt-4 rounded-2xl border border-dashed border-[#cdc5bc]/70 bg-[#fcf9f1]/50 p-8 text-center text-[13px] text-[#7c766e]">
          Loading activity…
        </div>
      ) : null}

      {items && items.length === 0 ? (
        <div className="mt-4 rounded-2xl border border-dashed border-[#cdc5bc]/70 bg-[#fcf9f1]/50 p-8 text-center">
          <p className="text-[14px] font-medium text-[#1c1c17]">
            No onchain activity yet
          </p>
          <p className="mt-1 text-[13px] text-[#7c766e]">
            Run an evaluation or send GEN to begin your history.
          </p>
        </div>
      ) : null}

      {items && items.length > 0 ? (
        <ul className="mt-4 overflow-hidden rounded-2xl border border-[#cdc5bc]/50 bg-[#fcf9f1] divide-y divide-[#cdc5bc]/40">
          {items.map((it, i) => (
            <li
              key={(it.tx_hash || it.timestamp) + i}
              className="flex flex-wrap items-center justify-between gap-3 px-5 py-4"
            >
              <div className="flex min-w-0 items-start gap-3">
                <span
                  className={[
                    "mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
                    it.kind === "evaluation"
                      ? "bg-emerald-100 text-emerald-700"
                      : "bg-[#1c1c17]/8 text-[#1c1c17]",
                  ].join(" ")}
                >
                  <Icon
                    name={it.kind === "evaluation" ? "shield_check" : "send"}
                    size={16}
                  />
                </span>
                <div className="min-w-0">
                  <p className="flex flex-wrap items-center gap-2">
                    <span
                      className={[
                        "rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.14em]",
                        it.kind === "evaluation"
                          ? "bg-emerald-100 text-emerald-800"
                          : "bg-[#1c1c17]/8 text-[#1c1c17]",
                      ].join(" ")}
                    >
                      {it.kind === "evaluation" ? "Evaluation" : "Send"}
                    </span>
                    <span className="truncate text-[13px] font-semibold text-[#1c1c17]">
                      {it.description}
                    </span>
                  </p>
                  <p className="mt-1 text-[11px] text-[#7c766e]">
                    {fmtTime(it.timestamp)}
                    {it.amount_gen ? ` · ${it.amount_gen} GEN` : ""}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2.5 text-[11px]">
                <span className="font-mono text-[#7c766e]">
                  {shortHash(it.tx_hash)}
                </span>
                {it.kind === "evaluation" && it.application_id ? (
                  <Link
                    href={`/dashboard/applications/${it.application_id}`}
                    className="rounded-lg border border-[#cdc5bc] bg-white px-3 py-1 text-[#1c1c17] hover:bg-[#fcf9f1]"
                  >
                    View
                  </Link>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
