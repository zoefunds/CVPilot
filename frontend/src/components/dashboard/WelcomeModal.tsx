"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { LogoMark } from "@/components/brand/Logo";
import { Icon } from "@/components/icons/Icon";

const STORAGE_KEY = "cvpilot.welcome_dismissed";

const pillars = [
  {
    icon: "shield_check" as const,
    title: "Verifiable scoring",
    body: "Every evaluation is recorded under three-validator consensus on GenLayer StudioNet, so recruiters can verify your score without trusting us.",
  },
  {
    icon: "wallet" as const,
    title: "Onchain wallet",
    body: "Your built-in wallet pays validators to run the LLM. Fund it from the StudioNet faucet using the address in Settings.",
  },
  {
    icon: "bolt" as const,
    title: "Always free",
    body: "We never charge money. The wallet uses StudioNet test tokens, so every evaluation stays free for every user.",
  },
];

export function WelcomeModal() {
  const [open, setOpen] = useState(false);

  // Only run on the client. Show only if the user has not dismissed before.
  useEffect(() => {
    try {
      const dismissed = localStorage.getItem(STORAGE_KEY) === "1";
      if (!dismissed) setOpen(true);
    } catch {
      // localStorage unavailable: never auto-show.
    }
  }, []);

  // ESC closes; lock background scroll while open.
  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        e.preventDefault();
        dismiss();
      }
    }
    document.addEventListener("keydown", onKey);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  function dismiss() {
    try {
      localStorage.setItem(STORAGE_KEY, "1");
    } catch {
      // ignore
    }
    setOpen(false);
  }

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[#1c1c17]/50 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="welcome-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) dismiss();
      }}
    >
      <div className="w-full max-w-[640px] rounded-3xl border border-[#cdc5bc]/60 bg-[#fcf9f1] p-7 shadow-2xl shadow-[#1c1c17]/20 sm:p-9">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <LogoMark size={36} />
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[#7c766e]">
                Welcome to CVPilot
              </p>
              <h2
                id="welcome-title"
                className="mt-1 text-[24px] leading-tight text-[#1c1c17] sm:text-[28px]"
                style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
              >
                Verifiable AI for job applications
              </h2>
            </div>
          </div>
          <button
            type="button"
            onClick={dismiss}
            className="rounded-lg p-1.5 text-[#4b463f] transition-colors hover:bg-[#1c1c17]/5 hover:text-[#1c1c17] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1c1c17]/30"
            aria-label="Close welcome"
          >
            ✕
          </button>
        </div>

        <p className="mt-3 text-[14px] leading-relaxed text-[#4b463f]">
          Three things to know before you submit your first evaluation.
        </p>

        <ul className="mt-6 flex flex-col gap-3">
          {pillars.map((p, i) => (
            <li
              key={p.title}
              className="flex items-start gap-3 rounded-2xl border border-[#cdc5bc]/50 bg-white p-4"
            >
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[#1c1c17] text-white">
                <Icon name={p.icon} size={16} />
              </span>
              <div>
                <h3
                  className="text-[15px] text-[#1c1c17]"
                  style={{ fontFamily: "Literata, serif", fontWeight: 600 }}
                >
                  {i + 1}. {p.title}
                </h3>
                <p className="mt-1 text-[13px] leading-relaxed text-[#4b463f]">
                  {p.body}
                </p>
              </div>
            </li>
          ))}
        </ul>

        <div className="mt-7 flex flex-wrap items-center justify-between gap-3">
          <p className="text-[11px] text-[#7c766e]">
            Need help later? Everything is also in Settings.
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={dismiss}
              className="inline-flex items-center justify-center rounded-xl border border-[#cdc5bc] bg-white px-5 py-2.5 text-[13px] font-medium text-[#1c1c17] hover:bg-[#fcf9f1] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1c1c17]/30"
            >
              Skip for now
            </button>
            <Link
              href="/dashboard/settings"
              onClick={dismiss}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#1c1c17] px-6 py-2.5 text-[13px] font-semibold text-white shadow-lg shadow-[#1c1c17]/15 transition-all hover:bg-[#332f28] active:scale-95 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1c1c17]/30"
            >
              Open my wallet
              <Icon name="chevron_right" size={13} />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
