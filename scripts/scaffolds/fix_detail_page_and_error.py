"""
Fix two longstanding bugs:
  1. frontend/src/app/dashboard/applications/[id]/page.tsx
     The Share-verification-link button was injected into the wrong scope
     (referencing ev/onCopy from outside EvaluationView). Rewrite the file
     cleanly with the Share button correctly placed inside EvaluationView.
  2. frontend/src/app/error.tsx
     Nested error.tsx must NOT render <html><body>; that is the job of
     global-error.tsx or the root layout. Removing the wrappers fixes the
     'body cannot contain a nested html' hydration warning.
"""
from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
FILES: dict[str, str] = {}


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

  async function copy(text: string | null | undefined, label: string) {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      push({ tone: 'success', title: 'Copied.', message: label });
    } catch {
      push({ tone: 'error', title: 'Could not copy.' });
    }
  }

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

  const overall = evaluation?.overall_score ?? null;

  return (
    <>
      {/* Sticky summary bar */}
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
                {app.error && <p className="mt-1 text-xs">{app.error}</p>}
              </div>
            </Alert>
          </div>
        )}

        {evaluation && evaluation.status === 'complete' && (
          <EvaluationView ev={evaluation} app={app} onCopy={copy} />
        )}
      </Container>
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
  const cv = app.files.find((f) => f.kind === 'cv');
  const cl = app.files.find((f) => f.kind === 'cover_letter');
  const tx = ev.contract_tx_hash;

  function shareLink() {
    if (!ev.content_hash) return;
    const url = `${window.location.origin}/verify/${ev.content_hash}`;
    void onCopy(url, 'Verification link');
  }

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

            {ev.content_hash && (
              <div className="mt-3">
                <button
                  type="button"
                  onClick={shareLink}
                  className="inline-flex items-center justify-center rounded-full border border-[#1a1814]/30 px-4 py-2 text-xs text-[#1a1814] hover:bg-[#1a1814]/5"
                >
                  Share verification link
                </button>
              </div>
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
            <p className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">Content hash</p>
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
            <p className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">Contract address</p>
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


# Nested error boundary must not render its own <html><body>.
FILES["frontend/src/app/error.tsx"] = '''\'use client\';

import Link from 'next/link';
import { useEffect } from 'react';
import { Container } from '@/components/ui/Container';
import { appName } from '@/lib/brand';

export default function NestedError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
     
    console.error('App error boundary caught:', error);
  }, [error]);

  return (
    <main className="min-h-screen">
      <header className="border-b border-[#d9d5c8]">
        <Container className="flex h-16 items-center justify-between">
          <Link href="/" className="font-serif text-2xl">
            {appName}
          </Link>
        </Container>
      </header>
      <Container className="py-24 sm:py-32">
        <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">
          Unexpected error
        </p>
        <h1 className="mt-3 font-serif text-6xl">
          Something went sideways.
        </h1>
        <p className="mt-4 max-w-xl text-[#3a342c]">
          We logged the failure. You can try again, or head back home.
          If this keeps happening, please reach out.
        </p>
        <div className="mt-10 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={reset}
            className="inline-flex items-center justify-center rounded-full bg-[#1a1814] px-6 py-3 text-sm font-medium text-[#efece4] hover:bg-[#3a342c]"
          >
            Try again
          </button>
          <Link
            href="/dashboard"
            className="inline-flex items-center justify-center rounded-full border border-[#1a1814]/30 px-6 py-3 text-sm font-medium text-[#1a1814] hover:bg-[#1a1814]/5"
          >
            Back to dashboard
          </Link>
        </div>
      </Container>
    </main>
  );
}
'''


# (Optional) bonus: a proper global-error.tsx so framework-level crashes still
# have a branded fallback. global-error renders its own html/body.
FILES["frontend/src/app/global-error.tsx"] = '''\'use client\';

import { useEffect } from 'react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
     
    console.error('Global error boundary caught:', error);
  }, [error]);

  return (
    <html lang="en">
      <body
        style={{
          fontFamily: 'ui-sans-serif, system-ui',
          background: '#efece4',
          color: '#1a1814',
          minHeight: '100vh',
          margin: 0,
          padding: '48px',
        }}
      >
        <p style={{ textTransform: 'uppercase', letterSpacing: '0.18em', fontSize: 12 }}>
          Fatal error
        </p>
        <h1 style={{ fontFamily: 'ui-serif, Georgia, serif', fontSize: 56, marginTop: 12 }}>
          Something went very sideways.
        </h1>
        <p style={{ maxWidth: 540, marginTop: 12 }}>
          The application could not render at all. Reloading may help.
        </p>
        <button
          type="button"
          onClick={reset}
          style={{
            marginTop: 32,
            background: '#1a1814',
            color: '#efece4',
            border: 0,
            borderRadius: 999,
            padding: '12px 24px',
            cursor: 'pointer',
          }}
        >
          Try again
        </button>
      </body>
    </html>
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

print("\nDetail page + error boundary fixed.")
