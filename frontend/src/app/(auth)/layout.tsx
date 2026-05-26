import Link from "next/link";
import { LogoMark } from "@/components/brand/Logo";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <main
      className="ethereal-gradient relative min-h-screen text-[#1c1c17]"
      style={{ fontFamily: "Inter, sans-serif" }}
    >
      <header className="sticky top-0 z-10 border-b border-[#cdc5bc]/40 bg-[#fcf9f1]/85 backdrop-blur-md">
        <div className="mx-auto flex max-w-[1280px] items-center justify-between px-6 py-3 md:px-10">
          <Link href="/" className="flex items-center gap-2.5">
            <LogoMark size={28} />
            <span
              className="text-[20px] font-bold tracking-tight text-[#1c1c17]"
              style={{ fontFamily: "Literata, serif" }}
            >
              CVPilot
            </span>
          </Link>
          <Link
            href="/"
            className="text-[13px] font-medium text-[#4b463f] transition-colors hover:text-[#1c1c17]"
          >
            Back to home
          </Link>
        </div>
      </header>

      <div className="relative mx-auto flex w-full max-w-[1080px] items-start justify-center px-6 py-16 md:py-24">
        <div className="pointer-events-none absolute -top-20 right-10 -z-10 h-72 w-72 rounded-full bg-[#cdc5bc]/35 blur-3xl" />
        <div className="pointer-events-none absolute bottom-10 left-10 -z-10 h-72 w-72 rounded-full bg-[#655d51]/15 blur-3xl" />
        {children}
      </div>
    </main>
  );
}
