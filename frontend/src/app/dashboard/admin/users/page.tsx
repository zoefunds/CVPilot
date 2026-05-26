"use client";

import { useEffect, useState } from "react";
import { Alert } from "@/components/ui/Alert";
import { Icon } from "@/components/icons/Icon";
import { useToast } from "@/contexts/ToastContext";
import { ApiError, adminApi } from "@/lib/api";
import type { AdminUserListItem } from "@/lib/types";

function fmt(s: string | null | undefined): string {
  if (!s) return "—";
  try {
    return new Date(s).toLocaleString();
  } catch {
    return s;
  }
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUserListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { push } = useToast();

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const u = await adminApi.listUsers(200);
        if (alive) setUsers(u);
      } catch (e) {
        if (alive)
          setError(e instanceof ApiError ? e.message : "Could not load.");
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  async function copy(v: string, label: string) {
    try {
      await navigator.clipboard.writeText(v);
      push({
        tone: "success",
        title: "Copied",
        message: `${label} on clipboard.`,
      });
    } catch {
      push({ tone: "error", title: "Could not copy." });
    }
  }

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
          All users
        </h1>
      </div>

      {error ? (
        <div className="mb-6">
          <Alert tone="error">{error}</Alert>
        </div>
      ) : null}

      <div className="overflow-hidden rounded-2xl border border-[#cdc5bc]/50 bg-[#fcf9f1]">
        {users === null ? (
          <p className="p-6 text-[13px] text-[#7c766e]">Loading…</p>
        ) : users.length === 0 ? (
          <p className="p-6 text-[13px] text-[#7c766e]">No users yet.</p>
        ) : (
          <ul className="divide-y divide-[#cdc5bc]/40">
            {users.map((u) => (
              <li key={u.id} className="px-5 py-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="truncate text-[14px] font-semibold text-[#1c1c17]">
                        {u.email}
                      </p>
                      {u.is_superuser ? (
                        <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-emerald-800">
                          Admin
                        </span>
                      ) : null}
                      {!u.is_active ? (
                        <span className="rounded-full bg-red-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-red-800">
                          Disabled
                        </span>
                      ) : null}
                    </div>
                    <p className="mt-0.5 text-[12px] text-[#7c766e]">
                      {u.full_name || "No name"}
                    </p>
                    <p className="mt-2 font-mono text-[10px] text-[#a8a298]">
                      {u.id}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-1 text-[11px] text-[#4b463f]">
                    <span className="font-medium text-[#1c1c17]">
                      {u.application_count} applications
                    </span>
                    <span className="text-[#7c766e]">
                      Joined {fmt(u.created_at)}
                    </span>
                    <span className="text-[#7c766e]">
                      Last app {fmt(u.last_application_at)}
                    </span>
                    <div className="mt-1 flex gap-1.5">
                      <button
                        type="button"
                        onClick={() => copy(u.email, "Email")}
                        className="rounded-lg border border-[#cdc5bc] bg-white px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-[#1c1c17] hover:bg-[#fcf9f1]"
                      >
                        Copy email
                      </button>
                      <button
                        type="button"
                        onClick={() => copy(u.id, "Account ID")}
                        className="rounded-lg border border-[#cdc5bc] bg-white px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-[#1c1c17] hover:bg-[#fcf9f1]"
                      >
                        Copy ID
                      </button>
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
