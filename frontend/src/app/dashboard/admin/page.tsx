"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { StatusBadge } from "@/components/dashboard/StatusBadge";
import { Alert } from "@/components/ui/Alert";
import { Icon, type IconName } from "@/components/icons/Icon";
import { ApiError, adminApi } from "@/lib/api";
import type {
  AdminApplicationListItem,
  AdminStats,
  AdminUserListItem,
  ApplicationStatus,
} from "@/lib/types";

function StatTile({
  label,
  value,
  hint,
  icon,
}: {
  label: string;
  value: string | number;
  hint?: string;
  icon: IconName;
}) {
  return (
    <div className="rounded-2xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-5">
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
      {hint ? (
        <p className="mt-1.5 text-[11px] text-[#7c766e]">{hint}</p>
      ) : null}
    </div>
  );
}

export default function AdminOverviewPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<AdminUserListItem[] | null>(null);
  const [apps, setApps] = useState<AdminApplicationListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const [s, u, a] = await Promise.all([
          adminApi.stats(),
          adminApi.listUsers(5, 0),
          adminApi.listApplications({ limit: 5 }),
        ]);
        if (!alive) return;
        setStats(s);
        setUsers(u);
        setApps(a);
      } catch (e) {
        if (!alive) return;
        setError(
          e instanceof ApiError ? e.message : "Could not load admin data.",
        );
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

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
          Overview
        </h1>
      </div>

      {error ? (
        <div className="mb-6">
          <Alert tone="error">{error}</Alert>
        </div>
      ) : null}

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile
          label="Users"
          value={stats?.user_count ?? "—"}
          hint={`+${stats?.last_24h_users ?? 0} last 24h`}
          icon="document"
        />
        <StatTile
          label="Applications"
          value={stats?.application_count ?? "—"}
          hint={`+${stats?.last_24h_applications ?? 0} last 24h`}
          icon="grid"
        />
        <StatTile
          label="Evaluations complete"
          value={stats?.evaluations_complete ?? "—"}
          icon="shield_check"
        />
        <StatTile
          label="Evaluations failed"
          value={stats?.evaluations_failed ?? "—"}
          icon="spark"
        />
      </section>

      {stats?.by_status && Object.keys(stats.by_status).length > 0 ? (
        <section className="mt-10">
          <h2
            className="text-[20px] text-[#1c1c17]"
            style={{ fontFamily: "Literata, serif", fontWeight: 600 }}
          >
            Applications by status
          </h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {Object.entries(stats.by_status).map(([s, n]) => (
              <div
                key={s}
                className="flex items-center gap-2.5 rounded-full border border-[#cdc5bc] bg-white px-3 py-1.5"
              >
                <StatusBadge status={s as ApplicationStatus} />
                <span className="text-[13px] font-semibold text-[#1c1c17]">
                  {n}
                </span>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <section className="mt-10">
        <div className="flex items-baseline justify-between">
          <h2
            className="text-[20px] text-[#1c1c17]"
            style={{ fontFamily: "Literata, serif", fontWeight: 600 }}
          >
            Recent users
          </h2>
          <Link
            href="/dashboard/admin/users"
            className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#4b463f] hover:text-[#1c1c17]"
          >
            See all →
          </Link>
        </div>
        <div className="mt-3 overflow-hidden rounded-2xl border border-[#cdc5bc]/50 bg-[#fcf9f1]">
          {users === null ? (
            <p className="p-6 text-[13px] text-[#7c766e]">Loading…</p>
          ) : users.length === 0 ? (
            <p className="p-6 text-[13px] text-[#7c766e]">No users yet.</p>
          ) : (
            <ul className="divide-y divide-[#cdc5bc]/40">
              {users.map((u) => (
                <li
                  key={u.id}
                  className="flex flex-wrap items-center justify-between gap-3 px-5 py-3.5"
                >
                  <div className="min-w-0">
                    <p className="truncate text-[14px] font-semibold text-[#1c1c17]">
                      {u.email}
                    </p>
                    <p className="truncate text-[11px] text-[#7c766e]">
                      {u.full_name || "No name"} · {u.application_count}{" "}
                      application
                      {u.application_count === 1 ? "" : "s"}
                    </p>
                  </div>
                  {u.is_superuser ? (
                    <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-emerald-800">
                      Admin
                    </span>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      <section className="mt-10">
        <div className="flex items-baseline justify-between">
          <h2
            className="text-[20px] text-[#1c1c17]"
            style={{ fontFamily: "Literata, serif", fontWeight: 600 }}
          >
            Recent applications
          </h2>
          <Link
            href="/dashboard/admin/applications"
            className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#4b463f] hover:text-[#1c1c17]"
          >
            See all →
          </Link>
        </div>
        <div className="mt-3 overflow-hidden rounded-2xl border border-[#cdc5bc]/50 bg-[#fcf9f1]">
          {apps === null ? (
            <p className="p-6 text-[13px] text-[#7c766e]">Loading…</p>
          ) : apps.length === 0 ? (
            <p className="p-6 text-[13px] text-[#7c766e]">
              No applications yet.
            </p>
          ) : (
            <ul className="divide-y divide-[#cdc5bc]/40">
              {apps.map((a) => (
                <li key={a.id}>
                  <Link
                    href={`/dashboard/admin/applications/${a.id}`}
                    className="flex flex-wrap items-center justify-between gap-3 px-5 py-3.5 transition-colors hover:bg-[#1c1c17]/[0.03]"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-[14px] font-semibold text-[#1c1c17]">
                        {a.job_title || a.job_url}
                      </p>
                      <p className="truncate text-[11px] text-[#7c766e]">
                        {a.user_email}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      {a.competitiveness !== null ? (
                        <span
                          className="text-[16px] font-bold text-[#1c1c17]"
                          style={{ fontFamily: "Literata, serif" }}
                        >
                          {a.competitiveness}
                          <span className="text-[10px] text-[#7c766e]">
                            /100
                          </span>
                        </span>
                      ) : null}
                      <StatusBadge status={a.status} />
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>
    </div>
  );
}
