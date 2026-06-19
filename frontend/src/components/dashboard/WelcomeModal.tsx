"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { LogoMark } from "@/components/brand/Logo";
import { Icon, type IconName } from "@/components/icons/Icon";

const STORAGE_KEY = "cvpilot.welcome_dismissed";

interface Step {
  icon: IconName;
  label: string;
  title: string;
  body: string;
  cta?: { label: string; href: string };
}

const STEPS: Step[] = [
  {
    icon: "wallet",
    label: "Step 1 of 4",
    title: "Fund your onchain wallet",
    body: "CVPilot uses GenLayer StudioNet to run AI evaluations under validator consensus. Your wallet pays the validators in GEN test tokens — completely free. Go to Settings → copy your wallet address → paste it into the StudioNet faucet to receive tokens.",
    cta: { label: "Open Settings → Wallet", href: "/dashboard/settings" },
  },
  {
    icon: "document",
    label: "Step 2 of 4",
    title: "Upload your CV (and optionally cover letter)",
    body: "CVPilot accepts PDF, DOCX, and TXT. Upload your CV and, if you have one, your cover letter. The cover letter unlocks the cover letter analysis and personalisation scores. You can skip it and add it later.",
    cta: { label: "Start a new evaluation", href: "/dashboard/new" },
  },
  {
    icon: "analytics",
    label: "Step 3 of 4",
    title: "Paste the job posting URL",
    body: "CVPilot fetches and parses the job page automatically. Paste any Jobberman, LinkedIn, Indeed, or company career-site URL. You'll see a live preview of the title, company, and description before you submit.",
  },
  {
    icon: "shield_check",
    label: "Step 4 of 4",
    title: "Read your 19-module report",
    body: "After ~60 seconds you'll receive scores for ATS compatibility, job match, skills gap, salary estimate, career trajectory, bias detection, readiness gate (GO / NO-GO), bullet rewrites, LinkedIn optimisation, and cold outreach — all verifiable on GenLayer StudioNet.",
  },
];

export function WelcomeModal() {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(0);

  useEffect(() => {
    try {
      const dismissed = localStorage.getItem(STORAGE_KEY) === "1";
      if (!dismissed) setOpen(true);
    } catch {
      // localStorage unavailable
    }
  }, []);

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") { e.preventDefault(); dismiss(); }
      if (e.key === "ArrowRight") setStep((s) => Math.min(s + 1, STEPS.length - 1));
      if (e.key === "ArrowLeft") setStep((s) => Math.max(s - 1, 0));
    }
    document.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.removeEventListener("keydown", onKey); document.body.style.overflow = prev; };
  }, [open]);

  function dismiss() {
    try { localStorage.setItem(STORAGE_KEY, "1"); } catch { /* ignore */ }
    setOpen(false);
  }

  if (!open) return null;

  const current = STEPS[step];
  const isLast = step === STEPS.length - 1;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[#1c1c17]/50 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="welcome-title"
      onClick={(e) => { if (e.target === e.currentTarget) dismiss(); }}
    >
      <div className="w-full max-w-[560px] rounded-3xl border border-[#cdc5bc]/60 bg-[#fcf9f1] shadow-2xl shadow-[#1c1c17]/20">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#cdc5bc]/40 px-7 py-5">
          <div className="flex items-center gap-3">
            <LogoMark size={28} />
            <p className="text-[13px] font-semibold text-[#1c1c17]">Getting started with CVPilot</p>
          </div>
          <button
            type="button"
            onClick={dismiss}
            className="rounded-lg p-1.5 text-[#7c766e] transition-colors hover:bg-[#1c1c17]/5 hover:text-[#1c1c17] focus:outline-none"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Step indicator */}
        <div className="flex gap-1.5 px-7 pt-5">
          {STEPS.map((_, i) => (
            <button
              key={i}
              type="button"
              onClick={() => setStep(i)}
              className={`h-1.5 flex-1 rounded-full transition-all ${i === step ? "bg-[#1c1c17]" : i < step ? "bg-[#1c1c17]/40" : "bg-[#cdc5bc]"}`}
              aria-label={`Go to step ${i + 1}`}
            />
          ))}
        </div>

        {/* Content */}
        <div className="px-7 pb-3 pt-5">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[#7c766e]">
            {current.label}
          </p>
          <div className="mt-3 flex items-start gap-4">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#1c1c17] text-white">
              <Icon name={current.icon} size={18} />
            </span>
            <div>
              <h2
                id="welcome-title"
                className="text-[20px] leading-snug text-[#1c1c17]"
                style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
              >
                {current.title}
              </h2>
              <p className="mt-3 text-[14px] leading-relaxed text-[#4b463f]">
                {current.body}
              </p>
            </div>
          </div>
        </div>

        {/* Pro tip */}
        {step === 0 && (
          <div className="mx-7 mb-2 mt-1 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3">
            <p className="text-[12px] text-amber-800">
              <span className="font-semibold">Pro tip:</span> You need at least 0.005 GEN to run a full evaluation. The faucet gives you plenty.
            </p>
          </div>
        )}
        {step === 2 && (
          <div className="mx-7 mb-2 mt-1 rounded-xl border border-[#cdc5bc]/50 bg-white px-4 py-3">
            <p className="text-[12px] text-[#4b463f]">
              <span className="font-semibold">Supported sites:</span> Jobberman, LinkedIn, Indeed, Workday, Greenhouse, Lever, and most public job boards.
            </p>
          </div>
        )}
        {step === 3 && (
          <div className="mx-7 mb-2 mt-1 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3">
            <p className="text-[12px] text-emerald-800">
              <span className="font-semibold">Your results are permanent.</span> Each evaluation is stored onchain by content hash — share the verification link with recruiters or employers.
            </p>
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between gap-3 border-t border-[#cdc5bc]/40 px-7 py-5">
          <button
            type="button"
            onClick={dismiss}
            className="text-[12px] text-[#7c766e] hover:text-[#1c1c17]"
          >
            Skip walkthrough
          </button>

          <div className="flex gap-2">
            {step > 0 && (
              <button
                type="button"
                onClick={() => setStep((s) => s - 1)}
                className="inline-flex items-center gap-1.5 rounded-xl border border-[#cdc5bc] bg-white px-4 py-2 text-[13px] font-medium text-[#1c1c17] hover:bg-[#fcf9f1]"
              >
                ← Back
              </button>
            )}

            {current.cta && !isLast ? (
              <Link
                href={current.cta.href}
                onClick={dismiss}
                className="inline-flex items-center gap-1.5 rounded-xl border border-[#cdc5bc] bg-white px-4 py-2 text-[13px] font-medium text-[#1c1c17] hover:bg-[#fcf9f1]"
              >
                {current.cta.label}
              </Link>
            ) : null}

            {isLast ? (
              <Link
                href="/dashboard/new"
                onClick={dismiss}
                className="inline-flex items-center gap-2 rounded-xl bg-[#1c1c17] px-6 py-2.5 text-[13px] font-semibold text-white shadow-lg shadow-[#1c1c17]/15 transition-all hover:bg-[#332f28] active:scale-95"
              >
                Start my first evaluation
                <Icon name="chevron_right" size={13} />
              </Link>
            ) : (
              <button
                type="button"
                onClick={() => setStep((s) => s + 1)}
                className="inline-flex items-center gap-2 rounded-xl bg-[#1c1c17] px-6 py-2.5 text-[13px] font-semibold text-white shadow-lg shadow-[#1c1c17]/15 transition-all hover:bg-[#332f28] active:scale-95"
              >
                Next
                <Icon name="chevron_right" size={13} />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
