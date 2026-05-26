"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";
import { ApiError } from "@/lib/api";
import { Icon } from "@/components/icons/Icon";

export default function SignUpPage() {
  const router = useRouter();
  const { signUp, isAuthenticated, isLoading } = useAuth();
  const { push } = useToast();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isAuthenticated, isLoading, router]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setLoading(true);
    try {
      await signUp(email, password, fullName || undefined);
      push({
        tone: "success",
        title: "Account created.",
        message: "Welcome to CVPilot.",
      });
      router.push("/dashboard");
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
          Get started
        </p>
        <h1
          className="mt-2 text-[30px] leading-tight tracking-tight text-[#1c1c17] sm:text-[34px]"
          style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
        >
          Create your account
        </h1>
        <p className="mt-3 text-[14px] text-[#4b463f]">
          Free for everyone. No payment ever requested.
        </p>

        <form onSubmit={onSubmit} className="mt-7 flex flex-col gap-5">
          {error && (
            <div className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3.5 py-2.5 text-[13px] text-red-800">
              <span aria-hidden className="mt-0.5 text-[14px]">•</span>
              <span>{error}</span>
            </div>
          )}

          <div>
            <label htmlFor="fullName" className="text-[11px] font-semibold uppercase tracking-[0.12em] text-[#4b463f]">
              Full name
            </label>
            <input
              id="fullName"
              type="text"
              autoComplete="name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              disabled={loading}
              placeholder="Jane Doe"
              className="mt-2 w-full rounded-xl border border-[#cdc5bc] bg-white px-4 py-3 text-[15px] text-[#1c1c17] placeholder:text-[#a8a298] transition-all focus:border-[#1c1c17] focus:outline-none focus:ring-2 focus:ring-[#1c1c17]/10 disabled:opacity-60"
            />
            <p className="mt-1.5 text-[12px] text-[#7c766e]">Optional. Helps us address you in reports.</p>
          </div>

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

          <div>
            <label htmlFor="password" className="text-[11px] font-semibold uppercase tracking-[0.12em] text-[#4b463f]">
              Password
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
              placeholder="Pick something strong"
              className="mt-2 w-full rounded-xl border border-[#cdc5bc] bg-white px-4 py-3 text-[15px] text-[#1c1c17] placeholder:text-[#a8a298] transition-all focus:border-[#1c1c17] focus:outline-none focus:ring-2 focus:ring-[#1c1c17]/10 disabled:opacity-60"
            />
            <p className="mt-1.5 text-[12px] text-[#7c766e]">At least 8 characters.</p>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="mt-1 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#1c1c17] px-6 py-3.5 text-[15px] font-semibold text-white shadow-lg shadow-[#1c1c17]/15 transition-all hover:bg-[#332f28] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Creating…" : "Create account"}
            {!loading && <Icon name="send" size={15} />}
          </button>
        </form>

        <p className="mt-7 text-center text-[13px] text-[#4b463f]">
          Already a user?{" "}
          <Link
            href="/signin"
            className="font-semibold text-[#1c1c17] underline underline-offset-4 hover:text-[#332f28]"
          >
            Sign in
          </Link>
        </p>
      </div>

      <ul className="mt-6 flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-[12px] text-[#7c766e]">
        <li className="flex items-center gap-1.5">
          <Icon name="shield_check" size={14} className="text-[#1c1c17]" />
          Onchain verifiable evaluations
        </li>
        <li className="flex items-center gap-1.5">
          <Icon name="bolt" size={14} className="text-[#1c1c17]" />
          First evaluation free
        </li>
      </ul>
    </div>
  );
}
