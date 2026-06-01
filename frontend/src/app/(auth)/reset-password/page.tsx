"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useState } from "react";
import { authApi, ApiError } from "@/lib/api";
import { useToast } from "@/contexts/ToastContext";
import { Icon } from "@/components/icons/Icon";

function ResetPasswordCard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { push } = useToast();
  const token = searchParams.get("token") || "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const hasToken = token.length >= 10;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    try {
      await authApi.resetPassword(token, password);
      push({
        tone: "success",
        title: "Password updated.",
        message: "Sign in with your new password.",
      });
      router.push("/signin");
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
          Choose a new password
        </p>
        <h1
          className="mt-2 text-[30px] leading-tight tracking-tight text-[#1c1c17] sm:text-[34px]"
          style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
        >
          Reset password
        </h1>
        <p className="mt-3 text-[14px] text-[#4b463f]">
          Pick something at least 8 characters long.
        </p>

        {!hasToken ? (
          <div className="mt-7 rounded-xl border border-amber-200 bg-amber-50 px-4 py-4 text-[14px] text-amber-900">
            <p className="font-semibold">This link looks incomplete.</p>
            <p className="mt-1 text-[13px] leading-relaxed text-amber-900/85">
              The reset link is missing its token. Request a fresh one from the{" "}
              <Link href="/forgot-password" className="font-semibold underline underline-offset-4">
                forgot password
              </Link>{" "}
              page.
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
              <label htmlFor="password" className="text-[11px] font-semibold uppercase tracking-[0.12em] text-[#4b463f]">
                New password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                disabled={loading}
                placeholder="At least 8 characters"
                className="mt-2 w-full rounded-xl border border-[#cdc5bc] bg-white px-4 py-3 text-[15px] text-[#1c1c17] placeholder:text-[#a8a298] transition-all focus:border-[#1c1c17] focus:outline-none focus:ring-2 focus:ring-[#1c1c17]/10 disabled:opacity-60"
              />
            </div>

            <div>
              <label htmlFor="confirm" className="text-[11px] font-semibold uppercase tracking-[0.12em] text-[#4b463f]">
                Confirm password
              </label>
              <input
                id="confirm"
                type="password"
                autoComplete="new-password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                required
                minLength={8}
                disabled={loading}
                placeholder="Re-enter your new password"
                className="mt-2 w-full rounded-xl border border-[#cdc5bc] bg-white px-4 py-3 text-[15px] text-[#1c1c17] placeholder:text-[#a8a298] transition-all focus:border-[#1c1c17] focus:outline-none focus:ring-2 focus:ring-[#1c1c17]/10 disabled:opacity-60"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="mt-1 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#1c1c17] px-6 py-3.5 text-[15px] font-semibold text-white shadow-lg shadow-[#1c1c17]/15 transition-all hover:bg-[#332f28] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? "Updating…" : "Update password"}
              {!loading && <Icon name="send" size={15} />}
            </button>
          </form>
        )}

        <p className="mt-7 text-center text-[13px] text-[#4b463f]">
          Back to{" "}
          <Link
            href="/signin"
            className="font-semibold text-[#1c1c17] underline underline-offset-4 hover:text-[#332f28]"
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="w-full max-w-[460px]" />}>
      <ResetPasswordCard />
    </Suspense>
  );
}
