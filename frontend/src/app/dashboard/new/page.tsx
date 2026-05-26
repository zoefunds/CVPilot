"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Dropzone } from "@/components/ui/Dropzone";
import { Field } from "@/components/ui/Field";
import { Input } from "@/components/ui/Input";
import { Icon } from "@/components/icons/Icon";
import { ApiError, applicationsApi, jobsApi } from "@/lib/api";
import type { JobIngest } from "@/lib/types";

interface InsufficientBalanceDetails {
  wallet_address: string;
  balance_wei: number;
  required_wei: number;
}

function isBalanceDetails(d: unknown): d is InsufficientBalanceDetails {
  return (
    typeof d === "object" &&
    d !== null &&
    "wallet_address" in d &&
    "balance_wei" in d &&
    "required_wei" in d
  );
}

function weiToGen(wei: number): string {
  if (!wei) return "0";
  return (wei / 1e18).toFixed(4);
}

function truncate(s: string | null, max = 280): string {
  if (!s) return "";
  s = s.trim();
  if (s.length <= max) return s;
  return s.slice(0, max).trimEnd() + "…";
}

export default function NewApplicationPage() {
  const router = useRouter();
  const [jobUrl, setJobUrl] = useState("");
  const [linkedinUrl, setLinkedinUrl] = useState("");
  const [portfolioUrl, setPortfolioUrl] = useState("");
  const [cv, setCv] = useState<File | null>(null);
  const [coverLetter, setCoverLetter] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [insufficient, setInsufficient] = useState<InsufficientBalanceDetails | null>(null);

  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [preview, setPreview] = useState<JobIngest | null>(null);

  async function onPreview() {
    setPreviewError(null);
    setPreview(null);
    if (!/^https?:\/\//i.test(jobUrl)) {
      setPreviewError("Paste a job URL first (must start with http or https).");
      return;
    }
    setPreviewLoading(true);
    try {
      const res = await jobsApi.ingest(jobUrl);
      setPreview(res);
      if (res.title) {
        // Replace user-pasted URL with the canonical (post-redirect) one.
        setJobUrl(res.url);
      }
    } catch (e) {
      setPreviewError(
        e instanceof ApiError ? e.message : "Could not load preview.",
      );
    } finally {
      setPreviewLoading(false);
    }
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setInsufficient(null);

    if (!cv) {
      setError("Please attach your CV.");
      return;
    }
    if (!coverLetter) {
      setError("Please attach your cover letter.");
      return;
    }
    if (!/^https?:\/\//i.test(jobUrl)) {
      setError("Job URL must start with http or https.");
      return;
    }

    setLoading(true);
    try {
      const app = await applicationsApi.create({
        job_url: jobUrl,
        linkedin_url: linkedinUrl || undefined,
        portfolio_url: portfolioUrl || undefined,
        cv,
        cover_letter: coverLetter,
      });
      router.push(`/dashboard/applications/${app.id}`);
    } catch (e) {
      if (e instanceof ApiError && e.status === 402 && isBalanceDetails(e.details)) {
        setInsufficient(e.details);
      } else if (e instanceof ApiError) {
        setError(e.message);
      } else {
        setError("Submission failed. Try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-[1000px] px-6 py-10 md:px-8">
      <div className="mb-8 max-w-2xl">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#7c766e]">
          New evaluation
        </p>
        <h1
          className="mt-2 text-[34px] tracking-tight text-[#1c1c17] md:text-[42px]"
          style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
        >
          Grade your application
        </h1>
        <p className="mt-2 text-[15px] text-[#4b463f]">
          We parse your CV and cover letter, fetch the job posting, and run the
          onchain evaluation. You will see live status while we work.
        </p>
      </div>

      {insufficient ? (
        <div className="mb-8 rounded-2xl border border-amber-300/60 bg-amber-50 p-6">
          <div className="flex items-start gap-3">
            <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-amber-200 text-amber-900">
              <Icon name="wallet" size={18} />
            </span>
            <div className="flex-1">
              <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-amber-900">
                Top up your wallet
              </p>
              <h2 className="mt-1 text-[22px] text-[#1c1c17]" style={{ fontFamily: "Literata, serif", fontWeight: 600 }}>
                Not enough GEN to run this evaluation.
              </h2>
              <p className="mt-2 text-[14px] text-[#4b463f]">
                Validators need to be paid in GEN to run the onchain LLM. Fund
                your wallet via the StudioNet faucet, then submit again.
              </p>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <div className="rounded-xl border border-amber-200 bg-white p-3">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-amber-900">Your wallet</p>
                  <p className="mt-1.5 break-all font-mono text-[11px] text-[#1c1c17]">{insufficient.wallet_address}</p>
                </div>
                <div className="rounded-xl border border-amber-200 bg-white p-3">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-amber-900">Balance / needed</p>
                  <p className="mt-1.5 text-[13px] text-[#1c1c17]">
                    <span className="font-semibold">{weiToGen(insufficient.balance_wei)}</span> /{" "}
                    <span className="font-semibold">{weiToGen(insufficient.required_wei)}</span> GEN
                  </p>
                </div>
              </div>
              <div className="mt-5 flex flex-wrap gap-3">
                <Link href="/dashboard/settings" className="inline-flex items-center gap-2 rounded-xl bg-[#1c1c17] px-5 py-2.5 text-[13px] font-semibold text-white transition-all hover:bg-[#332f28] active:scale-95">
                  <Icon name="wallet" size={14} />
                  Open my wallet
                </Link>
                <a href="https://studio.genlayer.com/" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 rounded-xl border border-[#cdc5bc] bg-white px-5 py-2.5 text-[13px] font-semibold text-[#1c1c17] transition-all hover:bg-[#fcf9f1] active:scale-95">
                  Open StudioNet
                </a>
              </div>
            </div>
          </div>
        </div>
      ) : null}

      <form onSubmit={onSubmit} className="rounded-3xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-6 shadow-sm shadow-[#1c1c17]/[0.03] sm:p-8">
        <div className="flex flex-col gap-5">
          {error ? <Alert tone="error">{error}</Alert> : null}

          <div>
            <Field label="Job URL" hint="Paste the link to the job posting.">
              <div className="flex gap-2">
                <Input
                  type="url"
                  value={jobUrl}
                  onChange={(e) => {
                    setJobUrl(e.target.value);
                    setPreview(null);
                    setPreviewError(null);
                  }}
                  required
                  disabled={loading || previewLoading}
                  placeholder="https://example.com/jobs/senior-engineer"
                />
                <button
                  type="button"
                  onClick={onPreview}
                  disabled={loading || previewLoading || !jobUrl}
                  className="inline-flex shrink-0 items-center gap-1.5 rounded-xl border border-[#cdc5bc] bg-white px-4 py-3 text-[13px] font-medium text-[#1c1c17] transition-all hover:bg-[#fcf9f1] active:scale-95 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <Icon name="spark" size={14} />
                  {previewLoading ? "Loading…" : "Preview"}
                </button>
              </div>
            </Field>
            {previewError ? (
              <div className="mt-3">
                <Alert tone="warning">{previewError}</Alert>
              </div>
            ) : null}
            {preview ? (
              <div className="mt-3 rounded-2xl border border-[#cdc5bc]/60 bg-white p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">
                      <Icon name="shield_check" size={11} className="text-emerald-700" />
                      Posting preview
                      {preview.cache_hit ? (
                        <span className="ml-1 rounded-full bg-[#1c1c17]/8 px-1.5 py-0.5 text-[9px] font-semibold text-[#4b463f]">
                          cached
                        </span>
                      ) : null}
                    </p>
                    <h3
                      className="mt-1 text-[16px] leading-tight text-[#1c1c17]"
                      style={{ fontFamily: "Literata, serif", fontWeight: 600 }}
                    >
                      {preview.title || "Untitled posting"}
                    </h3>
                    <p className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-[12px] text-[#4b463f]">
                      {preview.company ? <span>{preview.company}</span> : null}
                      {preview.location ? (
                        <span className="text-[#7c766e]">· {preview.location}</span>
                      ) : null}
                      {preview.employment_type ? (
                        <span className="text-[#7c766e]">· {preview.employment_type}</span>
                      ) : null}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setPreview(null);
                      setPreviewError(null);
                    }}
                    className="shrink-0 rounded-md p-1 text-[#7c766e] hover:bg-[#1c1c17]/5 hover:text-[#1c1c17]"
                    aria-label="Dismiss preview"
                  >
                    ✕
                  </button>
                </div>
                {preview.description ? (
                  <p className="mt-3 whitespace-pre-line border-t border-[#cdc5bc]/40 pt-3 text-[12px] leading-relaxed text-[#4b463f]">
                    {truncate(preview.description, 380)}
                  </p>
                ) : null}
                <p className="mt-3 text-[10px] text-[#7c766e]">
                  This is what we will hand to the validators. If anything looks
                  wrong, edit the URL or run the evaluation anyway.
                </p>
              </div>
            ) : null}
          </div>

          <div className="grid gap-5 sm:grid-cols-2">
            <Field label="LinkedIn" hint="Optional. Recruiters weight it.">
              <Input
                type="url"
                value={linkedinUrl}
                onChange={(e) => setLinkedinUrl(e.target.value)}
                disabled={loading}
                placeholder="https://www.linkedin.com/in/you/"
              />
            </Field>
            <Field label="Portfolio" hint="Optional. Useful for design or engineering roles.">
              <Input
                type="url"
                value={portfolioUrl}
                onChange={(e) => setPortfolioUrl(e.target.value)}
                disabled={loading}
                placeholder="https://your.portfolio.site"
              />
            </Field>
          </div>

          <div className="grid gap-5 sm:grid-cols-2">
            <Dropzone label="CV" file={cv} onFile={setCv} disabled={loading} />
            <Dropzone label="Cover letter" file={coverLetter} onFile={setCoverLetter} disabled={loading} />
          </div>

          <div className="pt-3">
            <Button type="submit" size="lg" disabled={loading}>
              {loading ? "Submitting…" : "Run evaluation"}
              {loading ? null : <Icon name="send" size={15} />}
            </Button>
          </div>
        </div>
      </form>

      <p className="mt-6 flex items-center gap-2 text-[12px] text-[#7c766e]">
        <Icon name="shield_check" size={14} className="text-[#1c1c17]" />
        Every evaluation is recorded under validator consensus on GenLayer
        StudioNet.
      </p>
    </div>
  );
}
