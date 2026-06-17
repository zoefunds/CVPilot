"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Alert } from "@/components/ui/Alert";
import { ScoreGauge } from "@/components/ui/ScoreGauge";
import { StatusBadge } from "@/components/dashboard/StatusBadge";
import { Icon } from "@/components/icons/Icon";
import { Skeleton } from "@/components/ui/Skeleton";
import { useToast } from "@/contexts/ToastContext";
import { ApiError, applicationsApi } from "@/lib/api";
import { ExtrasPanel } from "@/components/verify/EvaluationDisplay";
import type { ApplicationPublic, EvaluationPublic } from "@/lib/types";

function shortHash(h: string | null | undefined): string {
  if (!h) return "";
  if (h.length <= 14) return h;
  return `${h.slice(0, 8)}…${h.slice(-6)}`;
}

export default function ApplicationDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id;
  const { push } = useToast();

  const [app, setApp] = useState<ApplicationPublic | null>(null);
  const [evaluation, setEvaluation] = useState<EvaluationPublic | null>(null);
  const [error, setError] = useState<string | null>(null);
  const completed = useRef(false);
  const stopped = useRef(false);

  useEffect(() => {
    stopped.current = false;
    return () => {
      stopped.current = true;
    };
  }, []);

  useEffect(() => {
    if (!id) return;
    let timer: ReturnType<typeof setTimeout>;

    async function tick() {
      try {
        const a = await applicationsApi.get(id);
        if (stopped.current) return;
        setApp(a);

        if (a.status === "complete" || a.status === "failed") {
          try {
            const ev = await applicationsApi.getEvaluation(id);
            if (!stopped.current) setEvaluation(ev);
            if (a.status === "complete" && !completed.current) {
              completed.current = true;
              push({
                tone: "success",
                title: "Evaluation ready.",
                message: "Scroll for scores, strengths, risks, and recommendations.",
              });
            }
            if (a.status === "failed" && !completed.current) {
              completed.current = true;
              push({
                tone: "error",
                title: "Evaluation failed.",
                message: "See the error below.",
              });
            }
          } catch (e) {
            if (!(e instanceof ApiError && e.status === 404)) {
              throw e;
            }
          }
          return;
        }
        timer = setTimeout(tick, 4000);
      } catch (e) {
        if (e instanceof ApiError) setError(e.message);
        else setError("Could not load this application.");
      }
    }
    void tick();
    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [id, push]);

  async function copy(text: string | null | undefined, label: string) {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      push({ tone: "success", title: "Copied.", message: label });
    } catch {
      push({ tone: "error", title: "Could not copy." });
    }
  }

  if (error) {
    return (
      <div className="mx-auto max-w-[1200px] px-6 py-10 md:px-8">
        <Alert tone="error">{error}</Alert>
        <p className="mt-6 text-[13px]">
          <Link
            href="/dashboard"
            className="font-semibold text-[#1c1c17] underline underline-offset-4 hover:text-[#332f28]"
          >
            ← Back to dashboard
          </Link>
        </p>
      </div>
    );
  }

  if (!app) {
    return (
      <div className="mx-auto max-w-[1200px] px-6 py-10 md:px-8">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="mt-3 h-10 w-3/4" />
        <Skeleton className="mt-2 h-3 w-1/2" />
        <div className="mt-10 rounded-3xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-7 sm:p-9">
          <div className="grid items-center gap-8 lg:grid-cols-12">
            <div className="lg:col-span-5">
              <Skeleton className="h-3 w-20" />
              <Skeleton className="mt-3 h-16 w-32" />
              <Skeleton className="mt-5 h-7 w-40" />
            </div>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:col-span-7">
              <Skeleton className="h-32 w-full" />
              <Skeleton className="h-32 w-full" />
              <Skeleton className="h-32 w-full" />
              <Skeleton className="h-32 w-full" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  const isWorking =
    app.status === "pending" ||
    app.status === "processing" ||
    app.status === "evaluating" ||
    app.status === "ready";

  const overall = evaluation?.overall_score ?? null;

  return (
    <>
      <div className="sticky top-14 z-10 border-b border-[#cdc5bc]/40 bg-[#fcf9f1]/85 backdrop-blur-md">
        <div className="mx-auto flex max-w-[1200px] flex-wrap items-center justify-between gap-3 px-6 py-3 md:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-1.5 text-[13px] font-medium text-[#4b463f] transition-colors hover:text-[#1c1c17]"
            >
              <span aria-hidden>←</span> Dashboard
            </Link>
            <span className="hidden text-[#cdc5bc] sm:inline">/</span>
            <span className="hidden truncate text-[13px] font-medium text-[#1c1c17] sm:inline">
              {app.job_title || "Untitled posting"}
            </span>
          </div>
          <div className="flex items-center gap-3">
            {overall !== null ? (
              <span
                className="text-[22px] font-bold leading-none text-[#1c1c17]"
                style={{ fontFamily: "Literata, serif" }}
              >
                {overall}
                <span className="text-[11px] text-[#7c766e]">/100</span>
              </span>
            ) : null}
            <StatusBadge status={app.status} />
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-[1200px] px-6 py-10 md:px-8">
        <header>
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#7c766e]">
            Evaluation
          </p>
          <h1
            className="mt-2 text-[34px] leading-tight tracking-tight text-[#1c1c17] md:text-[44px]"
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
        </header>

        {isWorking ? (
          <div className="mt-8 flex items-start gap-3 rounded-2xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-5">
            <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[#1c1c17]/8 text-[#1c1c17]">
              <Icon name="spark" size={18} />
            </span>
            <div>
              <p className="text-[14px] font-semibold text-[#1c1c17]">Working on it.</p>
              <p className="mt-1 text-[13px] text-[#4b463f]">
                We are parsing your files and fetching the job posting. This
                page updates automatically.
              </p>
            </div>
          </div>
        ) : null}

        {app.status === "failed" ? (
          <div className="mt-8">
            <Alert tone="error">
              <p className="font-semibold">Evaluation failed.</p>
              {app.error ? (
                <p className="mt-1 text-[12px]">{app.error}</p>
              ) : null}
            </Alert>
          </div>
        ) : null}

        {evaluation && evaluation.status === "complete" ? (
          <EvaluationView ev={evaluation} app={app} onCopy={copy} />
        ) : null}
      </div>
    </>
  );
}

function EvaluationView({
  ev,
  app,
  onCopy,
}: {
  ev: EvaluationPublic;
  app: ApplicationPublic;
  onCopy: (text: string | null | undefined, label: string) => void;
}) {
  const cv = app.files.find((f) => f.kind === "cv");
  const cl = app.files.find((f) => f.kind === "cover_letter");
  const tx = ev.contract_tx_hash;
  const heroRef = useRef<HTMLElement | null>(null);
  const [exporting, setExporting] = useState(false);

  async function exportPng() {
    if (!heroRef.current || exporting) return;
    setExporting(true);
    try {
      const { toPng } = await import("html-to-image");
      const dataUrl = await toPng(heroRef.current, {
        cacheBust: true,
        backgroundColor: "#fcf9f1",
        pixelRatio: 2,
      });
      const filename = `cvpilot-${(ev.content_hash || "evaluation").slice(0, 12)}.png`;
      const link = document.createElement("a");
      link.href = dataUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      console.error("export failed", err);
      onCopy("", "Export failed");
    } finally {
      setExporting(false);
    }
  }

  function shareLink() {
    if (!ev.content_hash) return;
    const url = `${window.location.origin}/verify/${ev.content_hash}`;
    void onCopy(url, "Verification link");
  }

  return (
    <div className="mt-10 flex flex-col gap-10">
      <section ref={heroRef} className="rounded-3xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-7 shadow-sm shadow-[#1c1c17]/[0.04] sm:p-9">
        <div className="grid items-center gap-8 lg:grid-cols-12 lg:gap-10">
          <div className="lg:col-span-5">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#7c766e]">
              Overall score
            </p>
            <div className="mt-2 flex items-baseline gap-2">
              <span
                className="text-[72px] font-bold leading-none text-[#1c1c17] sm:text-[88px]"
                style={{ fontFamily: "Literata, serif" }}
              >
                {ev.overall_score ?? "—"}
              </span>
              <span className="text-[14px] text-[#7c766e]">/100</span>
            </div>

            <div className="mt-5 flex flex-wrap gap-2">
              {ev.competitiveness_score !== null ? (
                <span className="inline-flex items-center rounded-full border border-[#cdc5bc] bg-white px-3 py-1 text-[12px] text-[#1c1c17]">
                  Competitiveness {ev.competitiveness_score}/100
                </span>
              ) : null}
              <span className="inline-flex items-center rounded-full border border-[#cdc5bc] bg-white px-3 py-1 text-[12px] text-[#1c1c17]">
                Backend: {ev.backend || "—"}
              </span>
            </div>

            {tx ? (
              <button
                type="button"
                onClick={() => onCopy(tx, "Transaction hash")}
                className="mt-5 inline-flex w-full max-w-md flex-col items-start gap-1 rounded-2xl border border-[#1c1c17]/20 bg-[#1c1c17]/5 px-4 py-3 text-left transition-all hover:border-[#1c1c17]/30 hover:bg-[#1c1c17]/8"
                title="Click to copy"
              >
                <span className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.16em] text-[#1c1c17]">
                  <Icon name="shield_check" size={12} />
                  Verified on StudioNet
                </span>
                <span className="font-mono text-[12px] text-[#1c1c17]">
                  tx {shortHash(tx)}
                </span>
                {ev.content_hash ? (
                  <span className="font-mono text-[10px] text-[#7c766e]">
                    hash {shortHash(ev.content_hash)}
                  </span>
                ) : null}
              </button>
            ) : ev.content_hash && ev.contract_address ? (
              <button
                type="button"
                onClick={() => onCopy(ev.content_hash, "Content hash")}
                className="mt-5 inline-flex w-full max-w-md flex-col items-start gap-1 rounded-2xl border border-[#1c1c17]/20 bg-[#1c1c17]/5 px-4 py-3 text-left transition-all hover:border-[#1c1c17]/30 hover:bg-[#1c1c17]/8"
                title="Cached on chain under this content hash. Click to copy."
              >
                <span className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.16em] text-[#1c1c17]">
                  <Icon name="shield_check" size={12} />
                  Verified on StudioNet · cached
                </span>
                <span className="font-mono text-[12px] text-[#1c1c17]">
                  hash {shortHash(ev.content_hash)}
                </span>
                <span className="text-[10px] text-[#7c766e]">
                  Same inputs already evaluated onchain
                </span>
              </button>
            ) : (
              <span className="mt-5 inline-block rounded-xl border border-[#cdc5bc] bg-white px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-[#7c766e]">
                Scored locally
              </span>
            )}

            {ev.content_hash ? (
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={shareLink}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-[#cdc5bc] bg-white px-4 py-2 text-[12px] font-medium text-[#1c1c17] transition-all hover:bg-[#fcf9f1] active:scale-95"
                >
                  <Icon name="send" size={13} />
                  Share verification link
                </button>
                <button
                  type="button"
                  onClick={exportPng}
                  disabled={exporting}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-[#cdc5bc] bg-white px-4 py-2 text-[12px] font-medium text-[#1c1c17] transition-all hover:bg-[#fcf9f1] active:scale-95 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <Icon name="document" size={13} />
                  {exporting ? "Exporting…" : "Download as image"}
                </button>
              </div>
            ) : null}
          </div>

          <div className="lg:col-span-7">
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <ScoreGauge label="CV" value={ev.cv_score} />
              <ScoreGauge label="Cover letter" value={ev.cover_letter_score} />
              <ScoreGauge label="Job match" value={ev.job_match_score} />
              <ScoreGauge label="ATS" value={ev.ats_score} />
            </div>
          </div>
        </div>

        {ev.summary ? (
          <p className="mt-8 max-w-3xl border-t border-[#cdc5bc]/50 pt-6 text-[15px] leading-relaxed text-[#4b463f]">
            {ev.summary}
          </p>
        ) : null}
      </section>

      {ev.improved_positioning ? (
        <section className="rounded-2xl border border-emerald-200 bg-emerald-50/60 p-6">
          <h2
            className="text-[20px] text-[#1c1c17]"
            style={{ fontFamily: "Literata, serif", fontWeight: 600 }}
          >
            Improved positioning
          </h2>
          <p className="mt-3 text-[14px] leading-relaxed text-[#1c1c17]">
            {ev.improved_positioning}
          </p>
        </section>
      ) : null}

      {(ev.strengths.length > 0 || ev.risks.length > 0) ? (
        <section className="grid gap-5 sm:grid-cols-2">
          {ev.strengths.length > 0 ? (
            <div>
              <h2
                className="text-[20px] text-[#1c1c17]"
                style={{ fontFamily: "Literata, serif", fontWeight: 600 }}
              >
                Strengths
              </h2>
              <ul className="mt-3 grid gap-2.5">
                {ev.strengths.map((s, i) => (
                  <li
                    key={i}
                    className="rounded-xl border border-emerald-200/70 bg-emerald-50/60 p-4 text-[13px] leading-relaxed text-[#1c1c17]"
                  >
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          {ev.risks.length > 0 ? (
            <div>
              <h2
                className="text-[20px] text-[#1c1c17]"
                style={{ fontFamily: "Literata, serif", fontWeight: 600 }}
              >
                Risks
              </h2>
              <ul className="mt-3 grid gap-2.5">
                {ev.risks.map((r, i) => (
                  <li
                    key={i}
                    className="rounded-xl border border-amber-300/70 bg-amber-50/70 p-4 text-[13px] leading-relaxed text-[#1c1c17]"
                  >
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </section>
      ) : null}

      {ev.recommendations.length > 0 ? (
        <section>
          <div className="flex items-baseline justify-between">
            <h2
              className="text-[24px] text-[#1c1c17]"
              style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
            >
              Fix these first
            </h2>
            <span className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">
              {ev.recommendations.length} item
              {ev.recommendations.length === 1 ? "" : "s"}
            </span>
          </div>
          <ul className="mt-4 grid gap-3">
            {ev.recommendations.map((r, i) => (
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

      {ev.missing_keywords.length > 0 ? (
        <section>
          <h2
            className="text-[22px] text-[#1c1c17]"
            style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
          >
            Missing keywords
          </h2>
          <p className="mt-2 text-[13px] text-[#7c766e]">
            These appear in the job posting but not in your CV.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            {ev.missing_keywords.map((kw) => (
              <span
                key={kw}
                className="rounded-full border border-[#cdc5bc] bg-white px-3 py-1 text-[12px] text-[#1c1c17]"
              >
                {kw}
              </span>
            ))}
          </div>
        </section>
      ) : null}

      {ev.missing_skills.length > 0 ? (
        <section>
          <h2
            className="text-[22px] text-[#1c1c17]"
            style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
          >
            Missing skills
          </h2>
          <div className="mt-4 flex flex-wrap gap-2">
            {ev.missing_skills.map((s) => (
              <span
                key={s}
                className="rounded-full border border-[#cdc5bc] bg-white px-3 py-1 text-[12px] text-[#1c1c17]"
              >
                {s}
              </span>
            ))}
          </div>
        </section>
      ) : null}

      {ev.weak_statements.length > 0 ? (
        <section>
          <h2
            className="text-[22px] text-[#1c1c17]"
            style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
          >
            Weak statements
          </h2>
          <ul className="mt-4 grid gap-2.5">
            {ev.weak_statements.map((w, i) => (
              <li
                key={i}
                className="rounded-xl border border-amber-300/70 bg-amber-50/70 p-5 text-[13px] leading-relaxed text-[#1c1c17]"
              >
                {w}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {ev.company_alignment_notes.length > 0 ? (
        <section>
          <h2
            className="text-[22px] text-[#1c1c17]"
            style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
          >
            Company alignment
          </h2>
          <ul className="mt-4 grid gap-2.5">
            {ev.company_alignment_notes.map((c, i) => (
              <li
                key={i}
                className="rounded-xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-5 text-[13px] leading-relaxed text-[#1c1c17]"
              >
                {c}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {ev.rationale && Object.keys(ev.rationale).length > 0 ? (
        <section>
          <h2
            className="text-[22px] text-[#1c1c17]"
            style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
          >
            Score rationale
          </h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {Object.entries(ev.rationale)
              .filter(([, v]) => Boolean(v))
              .map(([k, v]) => (
                <div
                  key={k}
                  className="rounded-2xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-4"
                >
                  <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">
                    {k.replace(/_/g, " ")}
                  </p>
                  <p className="mt-2 text-[13px] leading-relaxed text-[#1c1c17]">
                    {v as string}
                  </p>
                </div>
              ))}
          </div>
        </section>
      ) : null}

      {ev.extras ? <ExtrasPanel extras={ev.extras} /> : null}

      <section>
        <h2
          className="text-[22px] text-[#1c1c17]"
          style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
        >
          Verification
        </h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <div className="rounded-2xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-4">
            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">
              Content hash
            </p>
            <div className="mt-2 flex items-center justify-between gap-3">
              <p className="break-all font-mono text-[11px] text-[#1c1c17]">
                {ev.content_hash || "—"}
              </p>
              {ev.content_hash ? (
                <button
                  type="button"
                  onClick={() => onCopy(ev.content_hash, "Content hash")}
                  className="shrink-0 rounded-lg border border-[#cdc5bc] bg-white px-3 py-1 text-[11px] font-medium text-[#1c1c17] hover:bg-[#fcf9f1]"
                >
                  Copy
                </button>
              ) : null}
            </div>
          </div>
          <div className="rounded-2xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-4">
            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">
              Contract address
            </p>
            <div className="mt-2 flex items-center justify-between gap-3">
              <p className="break-all font-mono text-[11px] text-[#1c1c17]">
                {ev.contract_address || "—"}
              </p>
              {ev.contract_address ? (
                <button
                  type="button"
                  onClick={() => onCopy(ev.contract_address, "Contract address")}
                  className="shrink-0 rounded-lg border border-[#cdc5bc] bg-white px-3 py-1 text-[11px] font-medium text-[#1c1c17] hover:bg-[#fcf9f1]"
                >
                  Copy
                </button>
              ) : null}
            </div>
          </div>
        </div>
      </section>

      {(cv || cl) ? (
        <section>
          <h2
            className="text-[22px] text-[#1c1c17]"
            style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
          >
            Files
          </h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {cv ? <FileSummary kind="CV" file={cv} /> : null}
            {cl ? <FileSummary kind="Cover letter" file={cl} /> : null}
          </div>
        </section>
      ) : null}
    </div>
  );
}

function FileSummary({
  kind,
  file,
}: {
  kind: string;
  file: {
    original_filename: string;
    detected_kind: string | null;
    byte_size: number;
  };
}) {
  return (
    <div className="flex items-start gap-3 rounded-2xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-4">
      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#1c1c17] text-white">
        <Icon name="document" size={18} />
      </span>
      <div className="min-w-0">
        <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">
          {kind}
        </p>
        <p className="mt-1 truncate text-[13px] font-semibold text-[#1c1c17]">
          {file.original_filename}
        </p>
        <p className="mt-0.5 text-[11px] text-[#7c766e]">
          {(file.detected_kind || "unknown").toUpperCase()} ·{" "}
          {(file.byte_size / 1024).toFixed(1)} KB
        </p>
      </div>
    </div>
  );
}
