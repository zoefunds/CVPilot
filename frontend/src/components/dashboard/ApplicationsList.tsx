"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { StatusBadge } from "@/components/dashboard/StatusBadge";
import { Icon } from "@/components/icons/Icon";
import { ApiError, applicationsApi } from "@/lib/api";
import type { ApplicationListItem } from "@/lib/types";

function fmtDate(s: string): string {
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

function hostnameOf(url: string): string {
  try {
    return new URL(url).hostname;
  } catch {
    return url;
  }
}

export function ApplicationsList() {
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

  if (error) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-5 text-[13px] text-red-800">
        {error}
      </div>
    );
  }

  if (items === null) {
    return (
      <div className="rounded-2xl border border-dashed border-[#cdc5bc]/70 bg-[#fcf9f1]/50 p-10 text-center text-[13px] text-[#7c766e]">
        Loading your evaluations…
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-[#cdc5bc]/70 bg-[#fcf9f1]/50 p-10 text-center">
        <p className="text-[14px] font-medium text-[#1c1c17]">
          No evaluations yet
        </p>
        <p className="mt-1 text-[13px] text-[#7c766e]">
          Your evaluation history will appear here once you run your first
          scoring pass.
        </p>
        <Link
          href="/dashboard/new"
          className="mt-5 inline-flex items-center justify-center gap-2 rounded-xl bg-[#1c1c17] px-5 py-2.5 text-[13px] font-semibold text-white transition-all hover:bg-[#332f28] active:scale-95"
        >
          <Icon name="plus" size={14} />
          Start a new evaluation
        </Link>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-[#cdc5bc]/50 bg-[#fcf9f1]">
      <ul className="divide-y divide-[#cdc5bc]/40">
        {items.map((a) => (
          <li key={a.id}>
            <Link
              href={`/dashboard/applications/${a.id}`}
              className="group flex flex-col gap-2 px-5 py-4 transition-colors hover:bg-[#1c1c17]/[0.03] sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="min-w-0">
                <p className="truncate text-[15px] font-semibold text-[#1c1c17]">
                  {a.job_title || hostnameOf(a.job_url)}
                </p>
                <p className="truncate text-[12px] text-[#7c766e]">
                  {a.job_url}
                </p>
              </div>
              <div className="flex items-center gap-4 text-[12px] text-[#4b463f]">
                <span className="hidden sm:inline">{fmtDate(a.created_at)}</span>
                <StatusBadge status={a.status} />
                <Icon
                  name="chevron_right"
                  size={14}
                  className="text-[#7c766e] transition-transform group-hover:translate-x-0.5"
                />
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
