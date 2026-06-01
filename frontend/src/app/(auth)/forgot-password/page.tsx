"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { authApi, ApiError } from "@/lib/api";
import { Icon } from "@/components/icons/Icon";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await authApi.forgotPassword(email);
      setSent(true);
    } catch (e) {
      if (e instanceof ApiError) setError(e.message);
      else setError("Something went wrong. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="w-full max-w-[460px]">
      <div className="rounded-3xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-8 shadow-xl shadow-[#1c1c17]/[0.06] sm:p-10">
        <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#7c766e]">
          Forgot password
        </p>
        <h1
          className="mt-2 text-[30px] leading-tight tracking-tight text-[#1c1c17] sm:text-[34px]"
          style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
        >
          Reset your password
        </h1>
        <p className="mt-3 text-[14px] text-[#4b463f]">
          Enter your account email and we&apos;ll send you a link to choose a new password.
        </p>

        {sent ? (
          <div className="mt-7 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-4 text-[14px] text-emerald-900">
            <p className="font-semibold">Check your inbox.</p>
            <p className="mt-1 text-[13px] leading-relaxed text-emerald-900/85">
              If an account exists for <span className="font-medium">{email}</span>, a reset link is on its way.
              The link expires in 30 minutes.
            </p>
          </div>
        ) : (
          <form onSubmit={onSubmit} className="mt-7 flex flex-col gap-5">
            {error && (
              <div className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3.5 py-2.5 text-[13px] text-red-800">
                <span aria-hidden className="mt-0.5 text-[14px]">•</span>
                <span>{error}</span>
              </div>
            )}

            <div>
              <label htmlFor="email" className="text-[11px] font-semibold uppercase tracking-[0.12em] text-[#4b463f]">
                Email
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={loading}
                placeholder="you@example.com"
                className="mt-2 w-full rounded-xl border border-[#cdc5bc] bg-white px-4 py-3 text-[15px] text-[#1c1c17] placeholder:text-[#a8a298] transition-all focus:border-[#1c1c17] focus:outline-none focus:ring-2 focus:ring-[#1c1c17]/10 disabled:opacity-60"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="mt-1 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#1c1c17] px-6 py-3.5 text-[15px] font-semibold text-white shadow-lg shadow-[#1c1c17]/15 transition-all hover:bg-[#332f28] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? "Sending…" : "Send reset link"}
              {!loading && <Icon name="send" size={15} />}
            </button>
          </form>
        )}

        <p className="mt-7 text-center text-[13px] text-[#4b463f]">
          Remembered it?{" "}
          <Link
            href="/signin"
            className="font-semibold text-[#1c1c17] underline underline-offset-4 hover:text-[#332f28]"
          >
            Back to sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
