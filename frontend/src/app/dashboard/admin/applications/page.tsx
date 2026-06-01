"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { StatusBadge } from "@/components/dashboard/StatusBadge";
import { Alert } from "@/components/ui/Alert";
import { Icon } from "@/components/icons/Icon";
import { ApiError, adminApi } from "@/lib/api";
import type {
  AdminApplicationListItem,
  ApplicationStatus,
} from "@/lib/types";

const STATUS_OPTIONS: { value: "" | ApplicationStatus; label: string }[] = [
  { value: "", label: "All" },
  { value: "pending", label: "Pending" },
  { value: "processing", label: "Processing" },
  { value: "ready", label: "Ready" },
  { value: "evaluating", label: "Evaluating" },
  { value: "complete", label: "Complete" },
  { value: "failed", label: "Failed" },
];

function fmt(s: string): string {
  try {
    return new Date(s).toLocaleString();
  } catch {
    return s;
  }
}

export default function AdminApplicationsPage() {
  const [status, setStatus] = useState<"" | ApplicationStatus>("");
  const [apps, setApps] = useState<AdminApplicationListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Re-fetch whenever the status filter changes.
  useEffect(() => {
    let alive = true;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setApps(null);
    setError(null);
    (async () => {
      try {
        const items = await adminApi.listApplications({
          status: status || undefined,
          limit: 200,
        });
        if (alive) setApps(items);
      } catch (e) {
        if (alive)
          setError(e instanceof ApiError ? e.message : "Could not load.");
      }
    })();
    return () => {
      alive = false;
    };
  }, [status]);

  return (
    <div className="mx-auto max-w-[1200px] px-6 py-10 md:px-8">
      <div className="mb-8">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#7c766e]">
          Admin
        </p>
        <h1
          className="mt-2 text-[34px] tracking-tight text-[#1c1c17] md:text-[42px]"
          style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
        >
          All applications
        </h1>
      </div>

      <div className="mb-6 flex flex-wrap items-center gap-2">
        {STATUS_OPTIONS.map((opt) => (
          <button
            key={opt.value || "all"}
            type="button"
            onClick={() => setStatus(opt.value)}
            className={[
              "rounded-lg px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.14em] transition-colors",
              status === opt.value
                ? "bg-[#1c1c17] text-white"
                : "border border-[#cdc5bc] bg-white text-[#4b463f] hover:bg-[#fcf9f1] hover:text-[#1c1c17]",
            ].join(" ")}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {error ? (
        <div className="mb-6">
          <Alert tone="error">{error}</Alert>
        </div>
      ) : null}

      <div className="overflow-hidden rounded-2xl border border-[#cdc5bc]/50 bg-[#fcf9f1]">
        {apps === null ? (
          <p className="p-6 text-[13px] text-[#7c766e]">Loading…</p>
        ) : apps.length === 0 ? (
          <p className="p-6 text-[13px] text-[#7c766e]">
            No applications match.
          </p>
        ) : (
          <ul className="divide-y divide-[#cdc5bc]/40">
            {apps.map((a) => (
              <li key={a.id}>
                <Link
                  href={`/dashboard/admin/applications/${a.id}`}
                  className="group flex flex-wrap items-center justify-between gap-3 px-5 py-4 transition-colors hover:bg-[#1c1c17]/[0.03]"
                >
                  <div className="min-w-0">
                    <p className="truncate text-[14px] font-semibold text-[#1c1c17]">
                      {a.job_title || a.job_url}
                    </p>
                    <p className="truncate text-[11px] text-[#7c766e]">
                      {a.user_email} · {fmt(a.created_at)}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 text-[11px]">
                    {a.competitiveness !== null ? (
                      <span
                        className="text-[16px] font-bold text-[#1c1c17]"
                        style={{ fontFamily: "Literata, serif" }}
                      >
                        {a.competitiveness}
                        <span className="text-[10px] text-[#7c766e]">/100</span>
                      </span>
                    ) : null}
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
        )}
      </div>
    </div>
  );
}
