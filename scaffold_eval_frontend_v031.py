"""
Frontend extension for v0.3.1: extend EvaluationPublic type, rewrite the
detail page to render overall, strengths, risks, improved positioning,
content hash, and contract address.
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
FILES: dict[str, str] = {}


FILES["frontend/src/lib/types.ts"] = '''export interface UserPublic {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_premium: boolean;
  is_superuser: boolean;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}

export type ApplicationStatus =
  | 'pending'
  | 'processing'
  | 'ready'
  | 'evaluating'
  | 'complete'
  | 'failed';

export type FileKind = 'cv' | 'cover_letter';

export interface FileAssetPublic {
  id: string;
  kind: FileKind;
  original_filename: string;
  content_type: string;
  byte_size: number;
  detected_kind: string | null;
  extracted_text: string | null;
}

export interface ApplicationPublic {
  id: string;
  job_url: string;
  job_final_url: string | null;
  job_title: string | null;
  job_text: string | null;
  linkedin_url: string | null;
  portfolio_url: string | null;
  status: ApplicationStatus;
  error: string | null;
  created_at: string;
  updated_at: string;
  files: FileAssetPublic[];
}

export interface ApplicationListItem {
  id: string;
  job_url: string;
  job_title: string | null;
  status: ApplicationStatus;
  created_at: string;
}

export type EvaluationStatus = 'pending' | 'running' | 'complete' | 'failed';

export interface EvaluationRationale {
  cv_score?: string;
  cover_letter_score?: string;
  job_match_score?: string;
  ats_score?: string;
  competitiveness_score?: string;
  overall_score?: string;
}

export interface EvaluationPublic {
  id: string;
  application_id: string;
  status: EvaluationStatus;
  backend: string | null;
  cv_score: number | null;
  cover_letter_score: number | null;
  job_match_score: number | null;
  ats_score: number | null;
  competitiveness_score: number | null;
  overall_score: number | null;
  summary: string | null;
  improved_positioning: string | null;
  recommendations: string[];
  missing_keywords: string[];
  missing_skills: string[];
  weak_statements: string[];
  company_alignment_notes: string[];
  strengths: string[];
  risks: string[];
  rationale: EvaluationRationale | null;
  raw: Record<string, unknown> | null;
  error: string | null;
  contract_tx_hash: string | null;
  content_hash: string | null;
  contract_address: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdminStats {
  user_count: number;
  application_count: number;
  evaluations_complete: number;
  evaluations_failed: number;
  last_24h_users: number;
  last_24h_applications: number;
  by_status: Record<string, number>;
}

export interface AdminUserListItem {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_premium: boolean;
  is_superuser: boolean;
  created_at: string;
  application_count: number;
  last_application_at: string | null;
}

export interface AdminApplicationListItem {
  id: string;
  user_id: string;
  user_email: string;
  job_url: string;
  job_title: string | null;
  status: ApplicationStatus;
  created_at: string;
  has_evaluation: boolean;
  competitiveness: number | null;
}
'''


FILES["frontend/src/app/dashboard/applications/[id]/page.tsx"] = '''\'use client\';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import { ScoreGauge } from '@/components/ui/ScoreGauge';
import { StatusBadge } from '@/components/dashboard/StatusBadge';
import { Alert } from '@/components/ui/Alert';
import { Container } from '@/components/ui/Container';
import { useToast } from '@/contexts/ToastContext';
import { ApiError, applicationsApi } from '@/lib/api';
import type {
  ApplicationPublic,
  EvaluationPublic,
} from '@/lib/types';

function shortHash(h: string | null | undefined): string {
  if (!h) return '';
  if (h.length <= 14) return h;
  return `${h.slice(0, 8)}\u2026${h.slice(-6)}`;
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

        if (a.status === 'complete' || a.status === 'failed') {
          try {
            const ev = await applicationsApi.getEvaluation(id);
            if (!stopped.current) setEvaluation(ev);
            if (a.status === 'complete' && !completed.current) {
              completed.current = true;
              push({
                tone: 'success',
                title: 'Evaluation ready.',
                message: 'Scroll for scores, strengths, risks, and recommendations.',
              });
            }
            if (a.status === 'failed' && !completed.current) {
              completed.current = true;
              push({
                tone: 'error',
                title: 'Evaluation failed.',
                message: 'See the error below.',
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
        else setError('Could not load this application.');
      }
    }
    void tick();
    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [id, push]);

  if (error) {
    return (
      <Container className="py-16">
        <Alert tone="error">{error}</Alert>
        <p className="mt-6 text-sm">
          <Link href="/dashboard" className="underline">
            Back to dashboard
          </Link>
        </p>
      </Container>
    );
  }

  if (!app) {
    return (
      <Container className="py-16">
        <p className="text-sm text-[#3a342c]">Loading your evaluation.</p>
      </Container>
    );
  }

  const isWorking =
    app.status === 'pending' ||
    app.status === 'processing' ||
    app.status === 'evaluating' ||
    app.status === 'ready';

  const tx = evaluation?.contract_tx_hash || null;
  const overall = evaluation?.overall_score ?? null;

  async function copy(text: string | null | undefined, label: string) {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      push({ tone: 'success', title: 'Copied.', message: label });
    } catch {
      push({ tone: 'error', title: 'Could not copy.' });
    }
  }

  return (
    <>
      <div className="sticky top-16 z-10 border-b border-[#d9d5c8] bg-[#efece4]/85 backdrop-blur supports-[backdrop-filter]:bg-[#efece4]/70">
        <Container className="flex flex-wrap items-center justify-between gap-3 py-3 text-sm">
          <div className="flex min-w-0 items-center gap-3">
            <Link href="/dashboard" className="text-[#3a342c] hover:text-[#1a1814]">
              \u2190 Dashboard
            </Link>
            <span className="hidden text-[#3a342c]/40 sm:inline">|</span>
            <span className="truncate font-medium text-[#1a1814]">
              {app.job_title || 'Untitled posting'}
            </span>
          </div>
          <div className="flex items-center gap-3">
            {overall !== null && (
              <span className="font-serif text-2xl text-[#1a1814]">
                {overall}
                <span className="text-xs text-[#3a342c]/70"> /100</span>
              </span>
            )}
            <StatusBadge status={app.status} />
          </div>
        </Container>
      </div>

      <Container className="py-12">
        <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">
          Evaluation
        </p>
        <h1 className="mt-2 font-serif text-4xl sm:text-5xl">
          {app.job_title || 'Untitled posting'}
        </h1>
        <a
          href={app.job_url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-2 inline-block max-w-full truncate text-sm text-[#3a342c]/80 hover:text-[#1a1814]"
        >
          {app.job_url}
        </a>

        {isWorking && (
          <div className="mt-8 rounded-2xl border border-[#1a1814]/15 bg-white/50 p-6 text-sm text-[#3a342c]">
            <p className="font-medium text-[#1a1814]">Working on it.</p>
            <p className="mt-1 text-[#3a342c]/80">
              We are parsing your files and fetching the job posting. This
              page updates automatically.
            </p>
          </div>
        )}

        {app.status === 'failed' && (
          <div className="mt-8">
            <Alert tone="error">
              <div>
                <p className="font-medium">Evaluation failed.</p>
                {app.error && (
                  <p className="mt-1 text-xs">{app.error}</p>
                )}
              </div>
            </Alert>
          </div>
        )}

        {evaluation && evaluation.status === 'complete' && (
          <EvaluationView
            ev={evaluation}
            app={app}
            tx={tx}
            onCopy={copy}
          />
        )}
      </Container>
    </>
  );
}


function EvaluationView({
  ev,
  app,
  tx,
  onCopy,
}: {
  ev: EvaluationPublic;
  app: ApplicationPublic;
  tx: string | null;
  onCopy: (text: string | null | undefined, label: string) => void;
}) {
  const cv = app.files.find((f) => f.kind === 'cv');
  const cl = app.files.find((f) => f.kind === 'cover_letter');

  return (
    <div className="mt-12 flex flex-col gap-14">
      <section className="rounded-3xl border border-[#1a1814]/10 bg-white/55 p-8 shadow-[0_20px_60px_-30px_rgba(26,24,20,0.3)] sm:p-10">
        <div className="grid items-center gap-10 lg:grid-cols-12">
          <div className="lg:col-span-5">
            <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">
              Overall
            </p>
            <p className="mt-2 font-serif text-7xl text-[#1a1814] sm:text-8xl">
              {ev.overall_score ?? '\u2014'}
            </p>
            <p className="text-xs text-[#3a342c]/70">/ 100</p>

            <div className="mt-5 flex flex-wrap gap-2">
              {ev.competitiveness_score !== null && (
                <span className="rounded-full border border-[#1a1814]/15 bg-white/70 px-3 py-1 text-xs text-[#1a1814]">
                  Competitiveness {ev.competitiveness_score}/100
                </span>
              )}
              <span className="rounded-full border border-[#1a1814]/15 bg-white/70 px-3 py-1 text-xs text-[#1a1814]">
                Backend: {ev.backend || '\u2014'}
              </span>
            </div>

            {tx ? (
              <button
                type="button"
                onClick={() => onCopy(tx, 'Transaction hash')}
                className="mt-5 inline-flex flex-col items-start rounded-2xl border border-[#2b4f3a]/30 bg-[#2b4f3a]/10 px-4 py-3 text-left transition-colors hover:bg-[#2b4f3a]/20"
                title="Click to copy"
              >
                <span className="text-[10px] uppercase tracking-[0.18em] text-[#2b4f3a]">
                  Verified on StudioNet
                </span>
                <span className="mt-1 font-mono text-xs text-[#2b4f3a]">
                  tx {shortHash(tx)}
                </span>
                {ev.content_hash && (
                  <span className="mt-0.5 font-mono text-[10px] text-[#2b4f3a]/70">
                    hash {shortHash(ev.content_hash)}
                  </span>
                )}
              </button>
            ) : (
              <span className="mt-5 inline-block rounded-2xl border border-[#1a1814]/15 bg-white/60 px-3 py-2 text-[10px] uppercase tracking-[0.18em] text-[#3a342c]/80">
                Scored locally
              </span>
            )}
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

        {ev.summary && (
          <p className="mt-8 max-w-3xl border-t border-[#1a1814]/10 pt-6 text-[#3a342c]">
            {ev.summary}
          </p>
        )}
      </section>

      {ev.improved_positioning && (
        <section className="rounded-2xl border border-[#2b4f3a]/20 bg-[#2b4f3a]/5 p-6">
          <h2 className="font-serif text-2xl text-[#1f3a2a]">Improved positioning.</h2>
          <p className="mt-3 leading-relaxed text-[#1a1814]">
            {ev.improved_positioning}
          </p>
        </section>
      )}

      {(ev.strengths.length > 0 || ev.risks.length > 0) && (
        <section className="grid gap-6 sm:grid-cols-2">
          {ev.strengths.length > 0 && (
            <div>
              <h2 className="font-serif text-2xl">Strengths.</h2>
              <ul className="mt-4 grid gap-3">
                {ev.strengths.map((s, i) => (
                  <li
                    key={i}
                    className="rounded-2xl border border-[#2b4f3a]/25 bg-[#2b4f3a]/8 p-4 text-sm text-[#1f3a2a]"
                  >
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {ev.risks.length > 0 && (
            <div>
              <h2 className="font-serif text-2xl">Risks.</h2>
              <ul className="mt-4 grid gap-3">
                {ev.risks.map((r, i) => (
                  <li
                    key={i}
                    className="rounded-2xl border border-[#a35f1f]/30 bg-[#a35f1f]/10 p-4 text-sm text-[#a35f1f]"
                  >
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

      {ev.recommendations.length > 0 && (
        <section>
          <div className="flex items-baseline justify-between">
            <h2 className="font-serif text-3xl">Fix these first.</h2>
            <span className="text-xs uppercase tracking-[0.15em] text-[#3a342c]/70">
              {ev.recommendations.length} item
              {ev.recommendations.length === 1 ? '' : 's'}
            </span>
          </div>
          <ul className="mt-5 grid gap-3">
            {ev.recommendations.map((r, i) => (
              <li
                key={i}
                className="flex items-start gap-4 rounded-2xl border border-[#1a1814]/10 bg-white/60 p-5"
              >
                <span className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-full bg-[#2b4f3a]/15 font-serif text-sm text-[#2b4f3a]">
                  {i + 1}
                </span>
                <p className="text-sm leading-relaxed text-[#1a1814]">{r}</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      {ev.missing_keywords.length > 0 && (
        <section>
          <h2 className="font-serif text-3xl">Missing keywords.</h2>
          <p className="mt-2 text-sm text-[#3a342c]">
            These appear in the job posting but not in your CV.
          </p>
          <div className="mt-5 flex flex-wrap gap-2">
            {ev.missing_keywords.map((kw) => (
              <span
                key={kw}
                className="rounded-full border border-[#1a1814]/15 bg-white/60 px-3 py-1 text-xs text-[#1a1814]"
              >
                {kw}
              </span>
            ))}
          </div>
        </section>
      )}

      {ev.missing_skills.length > 0 && (
        <section>
          <h2 className="font-serif text-3xl">Missing skills.</h2>
          <div className="mt-5 flex flex-wrap gap-2">
            {ev.missing_skills.map((s) => (
              <span
                key={s}
                className="rounded-full border border-[#1a1814]/15 bg-white/60 px-3 py-1 text-xs text-[#1a1814]"
              >
                {s}
              </span>
            ))}
          </div>
        </section>
      )}

      {ev.weak_statements.length > 0 && (
        <section>
          <h2 className="font-serif text-3xl">Weak statements.</h2>
          <ul className="mt-5 grid gap-3">
            {ev.weak_statements.map((w, i) => (
              <li
                key={i}
                className="rounded-2xl border border-[#a35f1f]/30 bg-[#a35f1f]/10 p-5 text-sm text-[#a35f1f]"
              >
                {w}
              </li>
            ))}
          </ul>
        </section>
      )}

      {ev.company_alignment_notes.length > 0 && (
        <section>
          <h2 className="font-serif text-3xl">Company alignment.</h2>
          <ul className="mt-5 grid gap-3">
            {ev.company_alignment_notes.map((c, i) => (
              <li
                key={i}
                className="rounded-2xl border border-[#1a1814]/10 bg-white/60 p-5 text-sm text-[#1a1814]"
              >
                {c}
              </li>
            ))}
          </ul>
        </section>
      )}

      {ev.rationale && Object.keys(ev.rationale).length > 0 && (
        <section>
          <h2 className="font-serif text-3xl">Score rationale.</h2>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            {Object.entries(ev.rationale)
              .filter(([, v]) => Boolean(v))
              .map(([k, v]) => (
                <div
                  key={k}
                  className="rounded-2xl border border-[#1a1814]/10 bg-white/60 p-4 text-sm"
                >
                  <p className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">
                    {k.replace(/_/g, ' ')}
                  </p>
                  <p className="mt-2 text-[#1a1814]">{v as string}</p>
                </div>
              ))}
          </div>
        </section>
      )}

      <section>
        <h2 className="font-serif text-3xl">Verification.</h2>
        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          <div className="rounded-2xl border border-[#1a1814]/10 bg-white/60 p-4">
            <p className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">
              Content hash
            </p>
            <div className="mt-2 flex items-center justify-between gap-3">
              <p className="break-all font-mono text-xs text-[#1a1814]">
                {ev.content_hash || '\u2014'}
              </p>
              {ev.content_hash && (
                <button
                  type="button"
                  onClick={() => onCopy(ev.content_hash, 'Content hash')}
                  className="shrink-0 rounded-full border border-[#1a1814]/20 px-3 py-1 text-xs text-[#1a1814] hover:bg-[#1a1814]/5"
                >
                  Copy
                </button>
              )}
            </div>
          </div>
          <div className="rounded-2xl border border-[#1a1814]/10 bg-white/60 p-4">
            <p className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">
              Contract address
            </p>
            <div className="mt-2 flex items-center justify-between gap-3">
              <p className="break-all font-mono text-xs text-[#1a1814]">
                {ev.contract_address || '\u2014'}
              </p>
              {ev.contract_address && (
                <button
                  type="button"
                  onClick={() => onCopy(ev.contract_address, 'Contract address')}
                  className="shrink-0 rounded-full border border-[#1a1814]/20 px-3 py-1 text-xs text-[#1a1814] hover:bg-[#1a1814]/5"
                >
                  Copy
                </button>
              )}
            </div>
          </div>
        </div>
      </section>

      {(cv || cl) && (
        <section>
          <h2 className="font-serif text-3xl">Files.</h2>
          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            {cv && <FileSummary kind="CV" file={cv} />}
            {cl && <FileSummary kind="Cover letter" file={cl} />}
          </div>
        </section>
      )}
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
    <div className="rounded-2xl border border-[#1a1814]/10 bg-white/60 p-5">
      <p className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">
        {kind}
      </p>
      <p className="mt-2 truncate font-medium text-[#1a1814]">
        {file.original_filename}
      </p>
      <p className="mt-1 text-xs text-[#3a342c]/70">
        {(file.detected_kind || 'unknown').toUpperCase()} \u00b7{' '}
        {(file.byte_size / 1024).toFixed(1)} KB
      </p>
    </div>
  );
}
'''


def write(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  wrote {rel}")


for rel, content in FILES.items():
    write(rel, content)

print("\nv0.3.1 frontend scaffold complete.")
