"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";
import { ApiError, authApi } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { Icon } from "@/components/icons/Icon";

type Status = "checking" | "ok" | "invalid" | "missing";

function VerifyEmailCard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";
  const { isAuthenticated, refreshUser } = useAuth();
  const [status, setStatus] = useState<Status>(token.length >= 10 ? "checking" : "missing");
  const [error, setError] = useState<string | null>(null);
  const calledOnce = useRef(false);

  useEffect(() => {
    if (calledOnce.current) return;
    if (status !== "checking") return;
    calledOnce.current = true;
    (async () => {
      try {
        await authApi.verifyEmail(token);
        // Refresh the auth context so AuthGuard sees email_verified=true on
        // the next navigation.
        try {
          await refreshUser();
        } catch {
          // ignore: even unauthenticated users land here from the email link
        }
        setStatus("ok");
      } catch (e) {
        setStatus("invalid");
        if (e instanceof ApiError) setError(e.message);
        else setError("Could not verify this link.");
      }
    })();
  }, [token, status, refreshUser]);

  return (
    <div className="w-full max-w-[460px]">
      <div className="rounded-3xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-8 shadow-xl shadow-[#1c1c17]/[0.06] sm:p-10">
        <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#7c766e]">
          Email verification
        </p>
        <h1
          className="mt-2 text-[30px] leading-tight tracking-tight text-[#1c1c17] sm:text-[34px]"
          style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
        >
          {status === "ok" ? "You're all set." : "Confirming your email…"}
        </h1>

        {status === "missing" && (
          <div className="mt-7 rounded-xl border border-amber-200 bg-amber-50 px-4 py-4 text-[14px] text-amber-900">
            <p className="font-semibold">This link looks incomplete.</p>
            <p className="mt-1 text-[13px] leading-relaxed text-amber-900/85">
              The verification link is missing its token. Sign in and request a new one from the{" "}
              <Link href="/verify-email-pending" className="font-semibold underline underline-offset-4">
                verification page
              </Link>
              .
            </p>
          </div>
        )}

        {status === "checking" && (
          <p className="mt-7 text-[14px] text-[#4b463f]">Just a moment.</p>
        )}

        {status === "ok" && (
          <>
            <p className="mt-3 text-[14px] text-[#4b463f]">
              Your email is now verified. You can head to your dashboard whenever you&apos;re ready.
            </p>
            <button
              type="button"
              onClick={() => router.replace(isAuthenticated ? "/dashboard" : "/signin")}
              className="mt-7 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#1c1c17] px-6 py-3.5 text-[15px] font-semibold text-white shadow-lg shadow-[#1c1c17]/15 transition-all hover:bg-[#332f28] active:scale-[0.98]"
            >
              {isAuthenticated ? "Go to dashboard" : "Sign in"}
              <Icon name="send" size={15} />
            </button>
          </>
        )}

        {status === "invalid" && (
          <div className="mt-7 rounded-xl border border-red-200 bg-red-50 px-4 py-4 text-[14px] text-red-800">
            <p className="font-semibold">This link didn&apos;t work.</p>
            <p className="mt-1 text-[13px] leading-relaxed text-red-800/90">
              {error || "It may have expired or already been used."} You can request a fresh one from
              the{" "}
              <Link href="/verify-email-pending" className="font-semibold underline underline-offset-4">
                verification page
              </Link>
              .
            </p>
          </div>
        )}

        <p className="mt-7 text-center text-[13px] text-[#4b463f]">
          Need to sign in?{" "}
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

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<div className="w-full max-w-[460px]" />}>
      <VerifyEmailCard />
    </Suspense>
  );
}
