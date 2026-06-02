"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ApiError, authApi } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { Icon } from "@/components/icons/Icon";

export default function VerifyEmailPendingPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading } = useAuth();
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // If unauthenticated, bounce to signin. If already verified, go to dashboard.
  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      router.replace("/signin");
      return;
    }
    if (user?.email_verified) {
      router.replace("/dashboard");
    }
  }, [isLoading, isAuthenticated, user?.email_verified, router]);

  async function onResend() {
    setError(null);
    setSending(true);
    try {
      await authApi.sendVerification();
      setSent(true);
    } catch (e) {
      if (e instanceof ApiError) setError(e.message);
      else setError("Could not send the email. Try again.");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="w-full max-w-[460px]">
      <div className="rounded-3xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-8 shadow-xl shadow-[#1c1c17]/[0.06] sm:p-10">
        <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#7c766e]">
          One more step
        </p>
        <h1
          className="mt-2 text-[30px] leading-tight tracking-tight text-[#1c1c17] sm:text-[34px]"
          style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
        >
          Verify your email
        </h1>
        <p className="mt-3 text-[14px] text-[#4b463f]">
          We sent a confirmation link to{" "}
          <span className="font-semibold text-[#1c1c17]">{user?.email || "your address"}</span>.
          Click it to unlock your dashboard. The link expires in 24 hours.
        </p>

        {sent ? (
          <div className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-[13px] text-emerald-900">
            A fresh link is on its way. Check your inbox (and spam folder).
          </div>
        ) : null}

        {error ? (
          <div className="mt-6 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3.5 py-2.5 text-[13px] text-red-800">
            <span aria-hidden className="mt-0.5 text-[14px]">•</span>
            <span>{error}</span>
          </div>
        ) : null}

        <button
          type="button"
          onClick={onResend}
          disabled={sending}
          className="mt-7 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#1c1c17] px-6 py-3.5 text-[15px] font-semibold text-white shadow-lg shadow-[#1c1c17]/15 transition-all hover:bg-[#332f28] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60"
        >
          {sending ? "Sending…" : sent ? "Resend again" : "Resend verification email"}
          {!sending && <Icon name="send" size={15} />}
        </button>

        <p className="mt-6 text-center text-[12px] text-[#7c766e]">
          Wrong email?{" "}
          <Link
            href="/dashboard/settings"
            className="font-semibold text-[#1c1c17] underline underline-offset-4"
          >
            Open settings
          </Link>
        </p>
      </div>
    </div>
  );
}
