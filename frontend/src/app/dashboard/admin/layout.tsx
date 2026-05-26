"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { AdminGuard } from "@/components/auth/AdminGuard";

function NavLink({ href, label }: { href: string; label: string }) {
  const pathname = usePathname();
  const active = pathname === href || pathname?.startsWith(href + "/");
  return (
    <Link
      href={href}
      className={[
        "rounded-lg px-3.5 py-1.5 text-[12px] font-semibold uppercase tracking-[0.14em] transition-colors",
        active
          ? "bg-[#1c1c17] text-white"
          : "text-[#4b463f] hover:bg-[#1c1c17]/5 hover:text-[#1c1c17]",
      ].join(" ")}
    >
      {label}
    </Link>
  );
}

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AdminGuard>
      <div className="sticky top-14 z-10 border-b border-[#cdc5bc]/40 bg-[#fcf9f1]/85 backdrop-blur-md">
        <div className="mx-auto flex max-w-[1200px] flex-wrap items-center gap-1.5 px-6 py-2.5 md:px-8">
          <NavLink href="/dashboard/admin" label="Overview" />
          <NavLink href="/dashboard/admin/users" label="Users" />
          <NavLink href="/dashboard/admin/applications" label="Applications" />
        </div>
      </div>
      {children}
    </AdminGuard>
  );
}
