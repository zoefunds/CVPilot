'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ScoreGauge } from '@/components/ui/ScoreGauge';
import { StatusBadge } from '@/components/dashboard/StatusBadge';
import { Alert } from '@/components/ui/Alert';
import { Container } from '@/components/ui/Container';
import { ApiError, adminApi } from '@/lib/api';
import type {
  ApplicationPublic,
  EvaluationPublic,
} from '@/lib/types';

function shortHash(h: string | null | undefined): string {
  if (!h) return '';
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
        if (alive) setError(e instanceof ApiError ? e.message : 'Could not load.');
      }
    })();
    return () => {
      alive = false;
    };
  }, [id]);

  if (error) {
    return (
      <Container className="py-14">
        <Alert tone="error">{error}</Alert>
        <p className="mt-6 text-sm">
          <Link href="/dashboard/admin/applications" className="underline">
            Back to applications
          </Link>
        </p>
      </Container>
    );
  }

  if (!app) {
    return (
      <Container className="py-14">
        <p className="text-sm text-[#3a342c]">Loading.</p>
      </Container>
    );
  }

  const tx = evaluation?.contract_tx_hash;

  return (
    <Container className="py-14">
      <Link
        href="/dashboard/admin/applications"
        className="text-xs uppercase tracking-[0.15em] text-[#3a342c] hover:text-[#1a1814]"
      >
        ← All applications
      </Link>

      <div className="mt-4 flex flex-wrap items-baseline justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">
            Admin view
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
        </div>
        <StatusBadge status={app.status} />
      </div>

      <section className="mt-8 grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-[#1a1814]/10 bg-white/60 p-4">
          <p className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">User ID</p>
          <p className="mt-1 break-all font-mono text-xs text-[#1a1814]">{app.user_id}</p>
        </div>
        <div className="rounded-2xl border border-[#1a1814]/10 bg-white/60 p-4">
          <p className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">Created</p>
          <p className="mt-1 text-sm text-[#1a1814]">{fmt(app.created_at)}</p>
        </div>
        <div className="rounded-2xl border border-[#1a1814]/10 bg-white/60 p-4">
          <p className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">Updated</p>
          <p className="mt-1 text-sm text-[#1a1814]">{fmt(app.updated_at)}</p>
        </div>
      </section>

      {app.status === 'failed' && app.error && (
        <div className="mt-8">
          <Alert tone="error">
            <p className="font-medium">Failure reason</p>
            <p className="mt-1 text-xs">{app.error}</p>
          </Alert>
        </div>
      )}

      {evaluation && evaluation.status === 'complete' && (
        <section className="mt-10 rounded-3xl border border-[#1a1814]/10 bg-white/55 p-8">
          <div className="grid items-center gap-10 lg:grid-cols-12">
            <div className="lg:col-span-5">
              <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">
                Competitiveness
              </p>
              <p className="mt-2 font-serif text-7xl text-[#1a1814]">
                {evaluation.competitiveness_score ?? '—'}
              </p>
              <p className="text-xs text-[#3a342c]/70">/ 100</p>
              {tx ? (
                <span className="mt-5 inline-flex flex-col rounded-2xl border border-[#2b4f3a]/30 bg-[#2b4f3a]/10 px-4 py-3">
                  <span className="text-[10px] uppercase tracking-[0.18em] text-[#2b4f3a]">
                    Verified on StudioNet
                  </span>
                  <span className="mt-1 font-mono text-xs text-[#2b4f3a]">
                    {shortHash(tx)}
                  </span>
                </span>
              ) : (
                <span className="mt-5 inline-block rounded-2xl border border-[#1a1814]/15 bg-white/60 px-3 py-2 text-[10px] uppercase tracking-[0.18em] text-[#3a342c]/80">
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
          {evaluation.summary && (
            <p className="mt-8 border-t border-[#1a1814]/10 pt-6 text-[#3a342c]">
              {evaluation.summary}
            </p>
          )}
        </section>
      )}

      {evaluation && evaluation.recommendations.length > 0 && (
        <section className="mt-10">
          <h2 className="font-serif text-2xl">Recommendations</h2>
          <ul className="mt-4 grid gap-3">
            {evaluation.recommendations.map((r, i) => (
              <li
                key={i}
                className="rounded-2xl border border-[#1a1814]/10 bg-white/60 p-4 text-sm text-[#1a1814]"
              >
                {r}
              </li>
            ))}
          </ul>
        </section>
      )}
    </Container>
  );
}
