"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
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

  const drawerRef = useRef<HTMLElement | null>(null);
  const menuButtonRef = useRef<HTMLButtonElement | null>(null);

  // Focus trap + ESC + restore focus when mobile drawer opens.
  useEffect(() => {
    if (!mobileOpen) return;
    const previouslyFocused = document.activeElement as HTMLElement | null;
    const drawer = drawerRef.current;
    if (!drawer) return;

    const focusables = drawer.querySelectorAll<HTMLElement>(
      'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])',
    );
    const first = focusables[0];
    const last = focusables[focusables.length - 1];
    first?.focus();

    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        e.preventDefault();
        setMobileOpen(false);
      } else if (e.key === "Tab" && focusables.length > 0) {
        const active = document.activeElement;
        if (e.shiftKey && active === first) {
          e.preventDefault();
          last?.focus();
        } else if (!e.shiftKey && active === last) {
          e.preventDefault();
          first?.focus();
        }
      }
    }

    document.addEventListener("keydown", onKey);
    // Lock page scroll while drawer is open.
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
      // Restore focus to the trigger button, or whatever had focus before.
      (menuButtonRef.current || previouslyFocused)?.focus();
    };
  }, [mobileOpen]);

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
        className="mb-8 flex items-center gap-2.5 rounded-lg px-1 py-1 transition-all hover:opacity-90 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1c1c17]/30"
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

      <nav className="flex flex-col gap-1" aria-label="Main">
        {nav.map((item) => {
          const active = isActive(item);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMobileOpen(false)}
              aria-current={active ? "page" : undefined}
              className={[
                "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-[14px] font-medium transition-all duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1c1c17]/30",
                active
                  ? "bg-[#1c1c17] text-white shadow-sm shadow-[#1c1c17]/15"
                  : "text-[#4b463f] hover:translate-x-0.5 hover:bg-[#1c1c17]/5 hover:text-[#1c1c17]",
              ].join(" ")}
            >
              <Icon
                name={item.icon}
                size={18}
                className={active ? "" : "transition-colors group-hover:text-[#1c1c17]"}
              />
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
            className="block rounded-xl border border-[#cdc5bc]/60 bg-[#fcf9f1] p-3 transition-all duration-150 hover:-translate-y-0.5 hover:border-[#cdc5bc] hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1c1c17]/30"
            aria-label={`Wallet balance ${formatGen(wallet.balance_gen)} GEN`}
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">
                Wallet
              </span>
              <span
                aria-hidden="true"
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
          className="flex w-full items-center justify-center gap-2 rounded-lg border border-[#cdc5bc]/60 px-3 py-2.5 text-[13px] font-medium text-[#4b463f] transition-all duration-150 hover:bg-[#1c1c17]/5 hover:text-[#1c1c17] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1c1c17]/30 active:scale-[0.98]"
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
      <aside
        className="fixed inset-y-0 left-0 z-30 hidden w-[244px] flex-col border-r border-[#cdc5bc]/40 bg-[#f6f3eb]/85 px-5 py-6 backdrop-blur-md md:flex"
        aria-label="Sidebar navigation"
      >
        {sidebar}
      </aside>

      {mobileOpen ? (
        <>
          <button
            type="button"
            aria-label="Close menu"
            className="fixed inset-0 z-40 bg-black/35 md:hidden"
            onClick={() => setMobileOpen(false)}
            tabIndex={-1}
          />
          <aside
            ref={drawerRef}
            role="dialog"
            aria-modal="true"
            aria-label="Navigation menu"
            className="fixed inset-y-0 left-0 z-50 flex w-[260px] flex-col border-r border-[#cdc5bc]/40 bg-[#f6f3eb] px-5 py-6 shadow-2xl animate-in slide-in-from-left duration-200 md:hidden"
          >
            {sidebar}
          </aside>
        </>
      ) : null}

      <div className="md:pl-[244px]">
        <header className="sticky top-0 z-20 border-b border-[#cdc5bc]/40 bg-[#fcf9f1]/85 backdrop-blur-md">
          <div className="flex h-14 items-center gap-3 px-4 md:px-8">
            <button
              ref={menuButtonRef}
              type="button"
              className="rounded-lg border border-[#cdc5bc]/60 p-1.5 text-[#4b463f] transition-colors hover:bg-[#1c1c17]/5 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1c1c17]/30 md:hidden"
              onClick={() => setMobileOpen(true)}
              aria-label="Open menu"
              aria-expanded={mobileOpen}
              aria-haspopup="dialog"
            >
              <Icon name="menu" size={18} />
            </button>
            <div className="flex-1" />
            {user ? (
              <div className="flex items-center gap-2.5 rounded-full border border-[#cdc5bc]/40 bg-[#fcf9f1] px-2 py-1 pr-3 transition-shadow hover:shadow-sm">
                <span
                  className="flex h-7 w-7 items-center justify-center rounded-full bg-[#1c1c17] text-[12px] font-bold text-white"
                  aria-hidden="true"
                >
                  {initial}
                </span>
                <div className="hidden flex-col leading-tight md:flex">
                  <span className="text-[12px] font-semibold text-[#1c1c17]">
                    {user.full_name || user.email.split("@")[0]}
                  </span>
                  <span className="text-[10px] text-[#7c766e]">
                    {user.email}
                  </span>
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
