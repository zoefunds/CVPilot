"use client";

import { useState } from "react";
import { Alert } from "@/components/ui/Alert";
import { WalletCard } from "@/components/dashboard/WalletCard";
import { WalletActivity } from "@/components/dashboard/WalletActivity";
import { Icon } from "@/components/icons/Icon";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";
import { ApiError, authApi } from "@/lib/api";

function fmtDate(s: string | undefined): string {
  if (!s) return "—";
  try {
    return new Date(s).toLocaleString();
  } catch {
    return s;
  }
}

export default function SettingsPage() {
  const { user, signOut } = useAuth();
  const { push } = useToast();
  const [confirming, setConfirming] = useState(false);
  const [activityKey, setActivityKey] = useState(0);
  const [resending, setResending] = useState(false);

  async function resendVerification() {
    setResending(true);
    try {
      await authApi.sendVerification();
      push({
        tone: "success",
        title: "Verification email sent.",
        message: "Check your inbox (and spam folder).",
      });
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : "Could not send the email.";
      push({ tone: "error", title: "Send failed", message: msg });
    } finally {
      setResending(false);
    }
  }

  async function copy(text: string, label: string) {
    try {
      await navigator.clipboard.writeText(text);
      push({
        tone: "success",
        title: "Copied",
        message: `${label} on clipboard.`,
      });
    } catch {
      push({
        tone: "error",
        title: "Could not copy",
        message: "Browser blocked clipboard access.",
      });
    }
  }

  return (
    <div className="mx-auto max-w-[1200px] px-6 py-10 md:px-8">
      <div className="mb-8">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#7c766e]">
          Settings
        </p>
        <h1
          className="mt-2 text-[34px] tracking-tight text-[#1c1c17] md:text-[42px]"
          style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
        >
          Your account
        </h1>
      </div>

      {user && !user.email_verified ? (
        <section className="mb-8">
          <Alert tone="warning">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="font-semibold">Your email isn&apos;t verified yet.</p>
                <p className="mt-1 text-[12px] text-amber-900/85">
                  Confirm <span className="font-medium">{user.email}</span> to unlock the dashboard.
                </p>
              </div>
              <button
                type="button"
                onClick={resendVerification}
                disabled={resending}
                className="rounded-lg bg-[#1c1c17] px-3 py-1.5 text-[12px] font-semibold text-white hover:bg-[#332f28] disabled:opacity-60"
              >
                {resending ? "Sending…" : "Send verification email"}
              </button>
            </div>
          </Alert>
        </section>
      ) : null}

      <section className="mb-10">
        <WalletCard onActivityChanged={() => setActivityKey((k) => k + 1)} />
      </section>

      <section className="mb-10">
        <WalletActivity refreshKey={activityKey} />
      </section>

      <section className="mb-10">
        <h2
          className="text-[22px] text-[#1c1c17]"
          style={{ fontFamily: "Literata, serif", fontWeight: 600 }}
        >
          Account
        </h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <Row
            label="Email"
            value={user?.email || ""}
            onCopy={() => copy(user?.email || "", "Email")}
          />
          <Row label="Full name" value={user?.full_name || "Not set"} />
          <Row
            label="Account ID"
            value={user?.id || ""}
            mono
            onCopy={() => copy(user?.id || "", "Account ID")}
          />
          <Row label="Member since" value={fmtDate(user?.created_at)} />
          <Row
            label="Account status"
            value={user?.is_active ? "Active" : "Disabled"}
          />
          <Row
            label="Tier"
            value={
              user?.is_premium ? "Premium" : "Free (everything unlocked)"
            }
          />
        </div>
      </section>

      <section className="max-w-2xl">
        <h2
          className="text-[22px] text-[#1c1c17]"
          style={{ fontFamily: "Literata, serif", fontWeight: 600 }}
        >
          Sign out
        </h2>
        <p className="mt-2 text-[13px] text-[#4b463f]">
          We will clear your tokens from this browser. Your data stays safe.
        </p>
        {confirming ? (
          <div className="mt-4">
            <Alert tone="warning">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <span className="font-medium">Confirm sign out?</span>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setConfirming(false)}
                    className="rounded-lg border border-amber-300/70 bg-white px-3 py-1.5 text-[11px] font-medium text-[#1c1c17] hover:bg-amber-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      signOut();
                      push({ tone: "info", title: "Signed out" });
                    }}
                    className="rounded-lg bg-red-600 px-3 py-1.5 text-[11px] font-semibold text-white hover:bg-red-700"
                  >
                    Sign me out
                  </button>
                </div>
              </div>
            </Alert>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setConfirming(true)}
            className="mt-4 inline-flex items-center gap-2 rounded-xl border border-[#cdc5bc] bg-white px-5 py-2.5 text-[13px] font-medium text-[#1c1c17] hover:bg-[#fcf9f1]"
          >
            <Icon name="logout" size={14} />
            Sign out of this browser
          </button>
        )}
      </section>
    </div>
  );
}

function Row({
  label,
  value,
  mono,
  onCopy,
}: {
  label: string;
  value: string;
  mono?: boolean;
  onCopy?: () => void;
}) {
  return (
    <div className="rounded-2xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-4">
      <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">
        {label}
      </p>
      <div className="mt-2 flex items-center justify-between gap-3">
        <p
          className={`min-w-0 truncate text-[14px] text-[#1c1c17] ${
            mono ? "font-mono text-[12px]" : ""
          }`}
        >
          {value}
        </p>
        {onCopy ? (
          <button
            type="button"
            onClick={onCopy}
            className="shrink-0 rounded-lg border border-[#cdc5bc] bg-white px-3 py-1 text-[11px] font-medium text-[#1c1c17] hover:bg-[#fcf9f1]"
          >
            Copy
          </button>
        ) : null}
      </div>
    </div>
  );
}
