"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { LogoMark } from "@/components/brand/Logo";
import { Icon } from "@/components/icons/Icon";

export default function VerifyLandingPage() {
  const router = useRouter();
  const [hash, setHash] = useState("");
  const [error, setError] = useState<string | null>(null);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const cleaned = hash.trim().toLowerCase();
    if (!/^[0-9a-f]{64}$/.test(cleaned)) {
      setError("That does not look like a 64 character content hash.");
      return;
    }
    router.push(`/verify/${cleaned}`);
  }

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

      <section className="mx-auto max-w-[860px] px-6 pt-20 pb-24 md:px-10 md:pt-28">
        <div className="inline-flex items-center gap-2 rounded-full border border-[#cdc5bc]/60 bg-[#f1eee6] px-3 py-1.5">
          <Icon name="shield_check" size={14} className="text-[#1c1c17]" />
          <span className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#1c1c17]">
            Public verification
          </span>
        </div>
        <h1
          className="mt-5 text-[40px] leading-[1.05] tracking-tight text-[#1c1c17] md:text-[58px]"
          style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
        >
          Read any CVPilot evaluation
          <br />
          <span className="text-[#7c766e]">straight from the chain.</span>
        </h1>
        <p className="mt-5 max-w-2xl text-[17px] leading-relaxed text-[#4b463f]">
          Paste a content hash below. We read the verified evaluation directly
          from the GenLayer Intelligent Contract on StudioNet. No signup. No
          intermediary.
        </p>

        <form onSubmit={onSubmit} className="mt-10 flex flex-col gap-4">
          <div>
            <label className="text-[11px] font-semibold uppercase tracking-[0.12em] text-[#4b463f]">
              Content hash
            </label>
            <input
              type="text"
              value={hash}
              onChange={(e) => {
                setHash(e.target.value);
                setError(null);
              }}
              placeholder="ac4a6e6855d57a17730ea46eb5e15d2a6a4e374ae38722a4dcaaeddc51df1ca4"
              autoComplete="off"
              spellCheck={false}
              className="mt-2 w-full rounded-xl border border-[#cdc5bc] bg-white px-4 py-3 font-mono text-[13px] text-[#1c1c17] placeholder:text-[#a8a298] focus:border-[#1c1c17] focus:outline-none focus:ring-2 focus:ring-[#1c1c17]/10"
            />
            <p className="mt-1.5 text-[12px] text-[#7c766e]">
              A 64 character hexadecimal SHA-256.
            </p>
          </div>
          {error ? (
            <div className="rounded-lg border border-red-200 bg-red-50 px-3.5 py-2.5 text-[13px] text-red-800">
              {error}
            </div>
          ) : null}
          <div>
            <button
              type="submit"
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#1c1c17] px-7 py-3.5 text-[15px] font-semibold text-white shadow-lg shadow-[#1c1c17]/15 transition-all hover:bg-[#332f28] active:scale-95"
            >
              Verify evaluation
              <Icon name="chevron_right" size={14} />
            </button>
          </div>
        </form>

        <div className="mt-14 grid gap-4 sm:grid-cols-3">
          <Trust icon="shield_check" title="Onchain consensus" body="Every evaluation finalised by three validators on GenLayer StudioNet." />
          <Trust icon="check" title="Auditable" body="Same hash always returns the same scores. No retroactive edits." />
          <Trust icon="bolt" title="No account needed" body="Recruiters verify in one click. No signup, no friction." />
        </div>
      </section>
    </main>
  );
}

function Trust({ icon, title, body }: { icon: "shield_check" | "check" | "bolt"; title: string; body: string }) {
  return (
    <div className="rounded-2xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-5">
      <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#1c1c17]/8 text-[#1c1c17]">
        <Icon name={icon} size={16} />
      </span>
      <h3
        className="mt-3 text-[15px] text-[#1c1c17]"
        style={{ fontFamily: "Literata, serif", fontWeight: 600 }}
      >
        {title}
      </h3>
      <p className="mt-1 text-[12px] leading-relaxed text-[#4b463f]">{body}</p>
    </div>
  );
}
