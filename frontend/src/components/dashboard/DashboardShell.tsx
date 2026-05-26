"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";
import { LOW_BALANCE_WEI, useWallet } from "@/contexts/WalletContext";
import { LogoMark } from "@/components/brand/Logo";
import { Icon, type IconName } from "@/components/icons/Icon";

type NavItem = {
  href: string;
  label: string;
  icon: IconName;
  matchPrefix?: boolean;
};

function formatGen(balance: string | undefined): string {
  if (!balance) return "—";
  const num = Number(balance);
  if (Number.isNaN(num)) return balance;
  if (num >= 1) return num.toFixed(2);
  if (num >= 0.001) return num.toFixed(4);
  return num === 0 ? "0" : num.toExponential(2);
}

function navItemsFor(isSuperuser: boolean): NavItem[] {
  const base: NavItem[] = [
    { href: "/dashboard", label: "Overview", icon: "grid" },
    { href: "/dashboard/new", label: "New evaluation", icon: "plus" },
    { href: "/dashboard/settings", label: "Wallet & settings", icon: "settings" },
  ];
  if (isSuperuser) {
    base.push({
      href: "/dashboard/admin",
      label: "Admin",
      icon: "shield_check",
      matchPrefix: true,
    });
  }
  return base;
}

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const { user, signOut } = useAuth();
  const { push } = useToast();
  const { wallet } = useWallet();
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  const nav = navItemsFor(Boolean(user?.is_superuser));

  const isActive = (item: NavItem) => {
    if (!pathname) return false;
    if (item.matchPrefix) return pathname.startsWith(item.href);
    return pathname === item.href;
  };

  function handleSignOut() {
    signOut();
    push({ tone: "info", title: "Signed out" });
  }

  const initial = (user?.full_name || user?.email || "?")
    .trim()
    .charAt(0)
    .toUpperCase();

  const sidebar = (
    <div className="flex h-full flex-col">
      <Link
        href="/dashboard"
        onClick={() => setMobileOpen(false)}
        className="mb-8 flex items-center gap-2.5 px-1"
      >
        <LogoMark size={30} />
        <div className="flex flex-col leading-none">
          <span
            className="text-[18px] font-bold tracking-tight text-[#1c1c17]"
            style={{ fontFamily: "Literata, serif" }}
          >
            CVPilot
          </span>
          <span className="mt-1 text-[10px] font-medium uppercase tracking-[0.14em] text-[#7c766e]">
            Verifiable AI
          </span>
        </div>
      </Link>

      <nav className="flex flex-col gap-1">
        {nav.map((item) => {
          const active = isActive(item);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMobileOpen(false)}
              className={[
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-[14px] font-medium transition-colors",
                active
                  ? "bg-[#1c1c17] text-white"
                  : "text-[#4b463f] hover:bg-[#1c1c17]/5 hover:text-[#1c1c17]",
              ].join(" ")}
            >
              <Icon name={item.icon} size={18} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto flex flex-col gap-3 pt-6">
        {wallet ? (
          <Link
            href="/dashboard/settings"
            onClick={() => setMobileOpen(false)}
            className="block rounded-xl border border-[#cdc5bc]/60 bg-[#fcf9f1] p-3 transition-all hover:border-[#cdc5bc] hover:shadow-sm"
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">
                Wallet
              </span>
              <span
                className={[
                  "h-1.5 w-1.5 rounded-full",
                  wallet.balance_wei < LOW_BALANCE_WEI ? "bg-amber-600" : "bg-emerald-600",
                ].join(" ")}
              />
            </div>
            <div className="mt-1 flex items-baseline gap-1">
              <span
                className="text-[20px] font-bold text-[#1c1c17]"
                style={{ fontFamily: "Literata, serif" }}
              >
                {formatGen(wallet.balance_gen)}
              </span>
              <span className="text-[11px] text-[#7c766e]">GEN</span>
            </div>
          </Link>
        ) : null}
        <button
          type="button"
          onClick={handleSignOut}
          className="flex w-full items-center justify-center gap-2 rounded-lg border border-[#cdc5bc]/60 px-3 py-2.5 text-[13px] font-medium text-[#4b463f] transition-colors hover:bg-[#1c1c17]/5 hover:text-[#1c1c17]"
        >
          <Icon name="logout" size={16} />
          Sign out
        </button>
      </div>
    </div>
  );

  return (
    <div
      className="ethereal-gradient min-h-screen text-[#1c1c17]"
      style={{ fontFamily: "Inter, sans-serif" }}
    >
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-[244px] flex-col border-r border-[#cdc5bc]/40 bg-[#f6f3eb]/85 px-5 py-6 backdrop-blur-md md:flex">
        {sidebar}
      </aside>

      {mobileOpen ? (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/35 md:hidden"
            onClick={() => setMobileOpen(false)}
          />
          <aside className="fixed inset-y-0 left-0 z-50 flex w-[260px] flex-col border-r border-[#cdc5bc]/40 bg-[#f6f3eb] px-5 py-6 md:hidden">
            {sidebar}
          </aside>
        </>
      ) : null}

      <div className="md:pl-[244px]">
        <header className="sticky top-0 z-20 border-b border-[#cdc5bc]/40 bg-[#fcf9f1]/85 backdrop-blur-md">
          <div className="flex h-14 items-center gap-3 px-4 md:px-8">
            <button
              type="button"
              className="rounded-lg border border-[#cdc5bc]/60 p-1.5 text-[#4b463f] transition-colors hover:bg-[#1c1c17]/5 md:hidden"
              onClick={() => setMobileOpen(true)}
              aria-label="Open menu"
            >
              <Icon name="menu" size={18} />
            </button>
            <div className="flex-1" />
            {user ? (
              <div className="flex items-center gap-2.5 rounded-full border border-[#cdc5bc]/40 bg-[#fcf9f1] px-2 py-1 pr-3">
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-[#1c1c17] text-[12px] font-bold text-white">
                  {initial}
                </span>
                <div className="hidden flex-col leading-tight md:flex">
                  <span className="text-[12px] font-semibold text-[#1c1c17]">
                    {user.full_name || user.email.split("@")[0]}
                  </span>
                  <span className="text-[10px] text-[#7c766e]">{user.email}</span>
                </div>
              </div>
            ) : null}
          </div>
        </header>

        <main>{children}</main>
      </div>
    </div>
  );
}
