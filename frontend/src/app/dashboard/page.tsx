"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ApplicationsList } from "@/components/dashboard/ApplicationsList";
import { Icon, type IconName } from "@/components/icons/Icon";
import { useAuth } from "@/contexts/AuthContext";
import { useWallet } from "@/contexts/WalletContext";
import { ApiError, applicationsApi } from "@/lib/api";
import type { ApplicationListItem } from "@/lib/types";

function formatGen(balance: string | undefined): string {
  if (!balance) return "—";
  const num = Number(balance);
  if (Number.isNaN(num)) return balance;
  if (num >= 1) return num.toFixed(2);
  if (num >= 0.001) return num.toFixed(4);
  return num === 0 ? "0" : num.toExponential(2);
}

function greeting() {
  const h = new Date().getHours();
  if (h < 5) return "Up late";
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

const IN_PROGRESS = new Set(["pending", "parsing", "parsed", "evaluating"]);

export default function DashboardPage() {
  const { user } = useAuth();
  const { wallet } = useWallet();
  const [items, setItems] = useState<ApplicationListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const data = await applicationsApi.list();
        if (alive) setItems(data);
      } catch (e) {
        if (alive) {
          setError(e instanceof ApiError ? e.message : "Could not load.");
        }
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const name =
    user?.full_name?.split(" ")[0] ||
    user?.email?.split("@")[0] ||
    "there";

  const total = items?.length ?? 0;
  const verified = items?.filter((i) => i.status === "complete").length ?? 0;
  const inProgress =
    items?.filter((i) => IN_PROGRESS.has(i.status)).length ?? 0;

  return (
    <div className="mx-auto max-w-[1200px] px-6 py-10 md:px-8">
      <div className="mb-8">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#7c766e]">
          {greeting()}
        </p>
        <h1
          className="mt-2 text-[34px] tracking-tight text-[#1c1c17] md:text-[42px]"
          style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
        >
          Hello, {name}.
        </h1>
        <p className="mt-2 max-w-2xl text-[15px] text-[#4b463f]">
          Drop your CV and a job URL and get a verifiable scoring report in
          under a minute.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total applications"
          value={items === null ? "—" : String(total)}
          icon="document"
        />
        <StatCard
          label="Verified onchain"
          value={items === null ? "—" : String(verified)}
          icon="shield_check"
        />
        <StatCard
          label="In progress"
          value={items === null ? "—" : String(inProgress)}
          icon="spark"
        />
        <StatCard
          label="Wallet balance"
          value={`${formatGen(wallet?.balance_gen)} GEN`}
          icon="wallet"
        />
      </div>

      <div className="mt-8 flex flex-col gap-4 rounded-2xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-6 shadow-sm shadow-[#1c1c17]/[0.03] md:flex-row md:items-center md:justify-between">
        <div>
          <h2
            className="text-[20px] text-[#1c1c17]"
            style={{ fontFamily: "Literata, serif", fontWeight: 600 }}
          >
            Start a new evaluation
          </h2>
          <p className="mt-1 max-w-xl text-[14px] text-[#4b463f]">
            Upload your CV, paste a job URL, and we deliver a consensus
            scored breakdown in under a minute.
          </p>
        </div>
        <Link
          href="/dashboard/new"
          className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-[#1c1c17] px-6 py-3 text-[14px] font-semibold text-white shadow-lg shadow-[#1c1c17]/15 transition-all hover:bg-[#332f28] active:scale-95"
        >
          <Icon name="plus" size={16} />
          New evaluation
        </Link>
      </div>

      <section className="mt-10">
        <div className="mb-4 flex items-baseline justify-between">
          <h2
            className="text-[22px] text-[#1c1c17]"
            style={{ fontFamily: "Literata, serif", fontWeight: 600 }}
          >
            Recent evaluations
          </h2>
          {items && items.length > 0 ? (
            <span className="text-[12px] text-[#7c766e]">
              {items.length} total
            </span>
          ) : null}
        </div>
        {error ? (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-5 text-[13px] text-red-800">
            {error}
          </div>
        ) : (
          <ApplicationsList />
        )}
      </section>
    </div>
  );
}

function StatCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon: IconName;
}) {
  return (
    <div className="rounded-2xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-5 transition-all hover:border-[#cdc5bc] hover:shadow-sm">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">
          {label}
        </span>
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#1c1c17]/8 text-[#1c1c17]">
          <Icon name={icon} size={16} />
        </span>
      </div>
      <div
        className="mt-3 text-[28px] font-bold leading-none text-[#1c1c17]"
        style={{ fontFamily: "Literata, serif" }}
      >
        {value}
      </div>
    </div>
  );
}
