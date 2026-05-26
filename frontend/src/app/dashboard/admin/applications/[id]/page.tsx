"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ScoreGauge } from "@/components/ui/ScoreGauge";
import { StatusBadge } from "@/components/dashboard/StatusBadge";
import { Alert } from "@/components/ui/Alert";
import { Icon } from "@/components/icons/Icon";
import { ApiError, adminApi } from "@/lib/api";
import type { ApplicationPublic, EvaluationPublic } from "@/lib/types";

function shortHash(h: string | null | undefined): string {
  if (!h) return "";
  if (h.length <= 14) return h;
  return `${h.slice(0, 8)}…${h.slice(-6)}`;
}

function fmt(s: string): string {
  try {
    return new Date(s).toLocaleString();
  } catch {
    return s;
  }
}

export default function AdminApplicationDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id;
  const [app, setApp] = useState<ApplicationPublic | null>(null);
  const [evaluation, setEvaluation] = useState<EvaluationPublic | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    let alive = true;
    (async () => {
      try {
        const a = await adminApi.getApplication(id);
        if (!alive) return;
        setApp(a);
        try {
          const ev = await adminApi.getEvaluation(id);
          if (alive) setEvaluation(ev);
        } catch (e) {
          if (!(e instanceof ApiError && e.status === 404)) {
            throw e;
          }
        }
      } catch (e) {
        if (alive)
          setError(e instanceof ApiError ? e.message : "Could not load.");
      }
    })();
    return () => {
      alive = false;
    };
  }, [id]);

  if (error) {
    return (
      <div className="mx-auto max-w-[1200px] px-6 py-10 md:px-8">
        <Alert tone="error">{error}</Alert>
        <p className="mt-6 text-[13px]">
          <Link
            href="/dashboard/admin/applications"
            className="font-semibold text-[#1c1c17] underline underline-offset-4 hover:text-[#332f28]"
          >
            ← Back to applications
          </Link>
        </p>
      </div>
    );
  }

  if (!app) {
    return (
      <div className="mx-auto max-w-[1200px] px-6 py-10 md:px-8">
        <div className="rounded-2xl border border-dashed border-[#cdc5bc]/70 bg-[#fcf9f1]/50 p-10 text-center text-[13px] text-[#7c766e]">
          Loading…
        </div>
      </div>
    );
  }

  const tx = evaluation?.contract_tx_hash;

  return (
    <div className="mx-auto max-w-[1200px] px-6 py-10 md:px-8">
      <Link
        href="/dashboard/admin/applications"
        className="inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.14em] text-[#4b463f] hover:text-[#1c1c17]"
      >
        ← All applications
      </Link>

      <div className="mt-4 flex flex-wrap items-baseline justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#7c766e]">
            Admin view
          </p>
          <h1
            className="mt-2 text-[30px] leading-tight tracking-tight text-[#1c1c17] md:text-[40px]"
            style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
          >
            {app.job_title || "Untitled posting"}
          </h1>
          <a
            href={app.job_url}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-2 inline-block max-w-full truncate text-[13px] text-[#4b463f] hover:text-[#1c1c17] hover:underline"
          >
            {app.job_url}
          </a>
        </div>
        <StatusBadge status={app.status} />
      </div>

      <section className="mt-8 grid gap-3 sm:grid-cols-3">
        <div className="rounded-2xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">
            User ID
          </p>
          <p className="mt-1.5 break-all font-mono text-[11px] text-[#1c1c17]">
            {app.user_id}
          </p>
        </div>
        <div className="rounded-2xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">
            Created
          </p>
          <p className="mt-1.5 text-[13px] text-[#1c1c17]">
            {fmt(app.created_at)}
          </p>
        </div>
        <div className="rounded-2xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">
            Updated
          </p>
          <p className="mt-1.5 text-[13px] text-[#1c1c17]">
            {fmt(app.updated_at)}
          </p>
        </div>
      </section>

      {app.status === "failed" && app.error ? (
        <div className="mt-8">
          <Alert tone="error">
            <p className="font-semibold">Failure reason</p>
            <p className="mt-1 text-[12px]">{app.error}</p>
          </Alert>
        </div>
      ) : null}

      {evaluation && evaluation.status === "complete" ? (
        <section className="mt-10 rounded-3xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-7 shadow-sm shadow-[#1c1c17]/[0.04] sm:p-9">
          <div className="grid items-center gap-8 lg:grid-cols-12 lg:gap-10">
            <div className="lg:col-span-5">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#7c766e]">
                Competitiveness
              </p>
              <div className="mt-2 flex items-baseline gap-2">
                <span
                  className="text-[64px] font-bold leading-none text-[#1c1c17] sm:text-[80px]"
                  style={{ fontFamily: "Literata, serif" }}
                >
                  {evaluation.competitiveness_score ?? "—"}
                </span>
                <span className="text-[14px] text-[#7c766e]">/100</span>
              </div>
              {tx ? (
                <span className="mt-5 inline-flex flex-col items-start gap-1 rounded-2xl border border-[#1c1c17]/20 bg-[#1c1c17]/5 px-4 py-3">
                  <span className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.16em] text-[#1c1c17]">
                    <Icon name="shield_check" size={12} />
                    Verified on StudioNet
                  </span>
                  <span className="font-mono text-[12px] text-[#1c1c17]">
                    {shortHash(tx)}
                  </span>
                </span>
              ) : (
                <span className="mt-5 inline-block rounded-xl border border-[#cdc5bc] bg-white px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-[#7c766e]">
                  Scored locally
                </span>
              )}
            </div>
            <div className="lg:col-span-7">
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                <ScoreGauge label="CV" value={evaluation.cv_score} />
                <ScoreGauge label="Cover letter" value={evaluation.cover_letter_score} />
                <ScoreGauge label="Job match" value={evaluation.job_match_score} />
                <ScoreGauge label="ATS" value={evaluation.ats_score} />
              </div>
            </div>
          </div>
          {evaluation.summary ? (
            <p className="mt-8 border-t border-[#cdc5bc]/50 pt-6 text-[15px] leading-relaxed text-[#4b463f]">
              {evaluation.summary}
            </p>
          ) : null}
        </section>
      ) : null}

      {evaluation && evaluation.recommendations.length > 0 ? (
        <section className="mt-10">
          <h2
            className="text-[22px] text-[#1c1c17]"
            style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
          >
            Recommendations
          </h2>
          <ul className="mt-4 grid gap-3">
            {evaluation.recommendations.map((r, i) => (
              <li
                key={i}
                className="flex items-start gap-4 rounded-2xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-5"
              >
                <span
                  className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-[#1c1c17] text-[13px] font-bold text-white"
                  style={{ fontFamily: "Literata, serif" }}
                >
                  {i + 1}
                </span>
                <p className="text-[14px] leading-relaxed text-[#1c1c17]">{r}</p>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
