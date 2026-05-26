"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { LogoMark } from "@/components/brand/Logo";
import { EvaluationDisplay } from "@/components/verify/EvaluationDisplay";
import { Alert } from "@/components/ui/Alert";
import { Icon } from "@/components/icons/Icon";
import { ApiError, publicApi } from "@/lib/api";
import type { PublicEvaluation } from "@/lib/types";

export default function VerifyDetailPage() {
  const params = useParams<{ content_hash: string }>();
  const contentHash = (params?.content_hash || "").toLowerCase();

  const [data, setData] = useState<PublicEvaluation | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    setData(null);
    setNotFound(false);
    setError(null);
    (async () => {
      try {
        const ev = await publicApi.verify(contentHash);
        if (!alive) return;
        if (!ev.found) {
          setNotFound(true);
          setData(ev);
        } else {
          setData(ev);
        }
      } catch (e) {
        if (!alive) return;
        if (e instanceof ApiError && e.status === 404) {
          setNotFound(true);
          const body =
            e.details && typeof e.details === "object"
              ? (e.details as PublicEvaluation)
              : null;
          if (body) setData(body);
        } else {
          setError(
            e instanceof ApiError ? e.message : "Could not load evaluation.",
          );
        }
      }
    })();
    return () => {
      alive = false;
    };
  }, [contentHash]);

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
            href="/verify"
            className="inline-flex items-center gap-1.5 text-[13px] font-medium text-[#4b463f] transition-colors hover:text-[#1c1c17]"
          >
            Verify another
            <Icon name="chevron_right" size={12} />
          </Link>
        </div>
      </header>

      <section className="mx-auto max-w-[1100px] px-6 py-14 md:px-10">
        <div className="inline-flex items-center gap-2 rounded-full border border-[#cdc5bc]/60 bg-[#f1eee6] px-3 py-1.5">
          <Icon name="shield_check" size={14} className="text-[#1c1c17]" />
          <span className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#1c1c17]">
            Public verification
          </span>
        </div>
        <h1
          className="mt-4 text-[34px] leading-tight tracking-tight text-[#1c1c17] md:text-[44px]"
          style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
        >
          Onchain evaluation
        </h1>
        <p className="mt-2 break-all font-mono text-[11px] text-[#7c766e] sm:text-[12px]">
          {contentHash}
        </p>

        {error ? (
          <div className="mt-8">
            <Alert tone="error">{error}</Alert>
          </div>
        ) : null}

        {notFound && data ? (
          <div className="mt-10 rounded-2xl border border-amber-300/60 bg-amber-50 p-6">
            <div className="flex items-start gap-3">
              <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-amber-200 text-amber-900">
                <Icon name="shield_check" size={18} />
              </span>
              <div className="flex-1">
                <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-amber-900">
                  Not found
                </p>
                <h2
                  className="mt-1 text-[22px] text-[#1c1c17]"
                  style={{ fontFamily: "Literata, serif", fontWeight: 600 }}
                >
                  No evaluation is stored at this hash.
                </h2>
                <p className="mt-2 text-[14px] text-[#4b463f]">
                  Either the hash is wrong, the evaluation has not finalised
                  yet, or it lives on a different contract. The contract we
                  checked is shown below.
                </p>
                <div className="mt-4 rounded-xl border border-amber-200 bg-white p-3">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-amber-900">
                    Contract
                  </p>
                  <p className="mt-1.5 break-all font-mono text-[11px] text-[#1c1c17]">
                    {data.contract_address}
                  </p>
                </div>
                <div className="mt-5">
                  <Link
                    href="/verify"
                    className="inline-flex items-center gap-1.5 rounded-xl border border-[#cdc5bc] bg-white px-5 py-2.5 text-[13px] font-semibold text-[#1c1c17] hover:bg-[#fcf9f1]"
                  >
                    Try another hash
                  </Link>
                </div>
              </div>
            </div>
          </div>
        ) : null}

        {data && !notFound ? (
          <div className="mt-10">
            <EvaluationDisplay ev={data} />
          </div>
        ) : null}

        {!data && !error && !notFound ? (
          <div className="mt-10 rounded-2xl border border-dashed border-[#cdc5bc]/70 bg-[#fcf9f1]/50 p-10 text-center text-[13px] text-[#7c766e]">
            Reading the contract…
          </div>
        ) : null}
      </section>
    </main>
  );
}
