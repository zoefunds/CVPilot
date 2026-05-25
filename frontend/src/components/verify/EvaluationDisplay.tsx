'use client';

import { ScoreGauge } from '@/components/ui/ScoreGauge';
import type { PublicEvaluation } from '@/lib/types';

function shortHash(h: string | null | undefined): string {
  if (!h) return '';
  if (h.length <= 14) return h;
  return `${h.slice(0, 8)}…${h.slice(-6)}`;
}

export function EvaluationDisplay({ ev }: { ev: PublicEvaluation }) {
  return (
    <div className="flex flex-col gap-14">
      <section className="rounded-3xl border border-[#1a1814]/10 bg-white/55 p-8 shadow-[0_20px_60px_-30px_rgba(26,24,20,0.3)] sm:p-10">
        <div className="grid items-center gap-10 lg:grid-cols-12">
          <div className="lg:col-span-5">
            <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">
              Overall
            </p>
            <p className="mt-2 font-serif text-7xl text-[#1a1814] sm:text-8xl">
              {ev.overall_score ?? '—'}
            </p>
            <p className="text-xs text-[#3a342c]/70">/ 100</p>

            <div className="mt-5 flex flex-wrap gap-2">
              {ev.competitiveness_score !== null && (
                <span className="rounded-full border border-[#1a1814]/15 bg-white/70 px-3 py-1 text-xs text-[#1a1814]">
                  Competitiveness {ev.competitiveness_score}/100
                </span>
              )}
              <span className="rounded-full bg-[#2b4f3a]/12 px-3 py-1 text-xs text-[#2b4f3a]">
                Verified on StudioNet
              </span>
            </div>
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
          <p className="mt-3 leading-relaxed text-[#1a1814]">{ev.improved_positioning}</p>
        </section>
      )}

      {(ev.strengths.length > 0 || ev.risks.length > 0) && (
        <section className="grid gap-6 sm:grid-cols-2">
          {ev.strengths.length > 0 && (
            <div>
              <h2 className="font-serif text-2xl">Strengths.</h2>
              <ul className="mt-4 grid gap-3">
                {ev.strengths.map((s, i) => (
                  <li key={i} className="rounded-2xl border border-[#2b4f3a]/25 bg-[#2b4f3a]/8 p-4 text-sm text-[#1f3a2a]">{s}</li>
                ))}
              </ul>
            </div>
          )}
          {ev.risks.length > 0 && (
            <div>
              <h2 className="font-serif text-2xl">Risks.</h2>
              <ul className="mt-4 grid gap-3">
                {ev.risks.map((r, i) => (
                  <li key={i} className="rounded-2xl border border-[#a35f1f]/30 bg-[#a35f1f]/10 p-4 text-sm text-[#a35f1f]">{r}</li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

      {ev.recommendations.length > 0 && (
        <section>
          <h2 className="font-serif text-3xl">Recommendations.</h2>
          <ul className="mt-5 grid gap-3">
            {ev.recommendations.map((r, i) => (
              <li key={i} className="flex items-start gap-4 rounded-2xl border border-[#1a1814]/10 bg-white/60 p-5">
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
          <div className="mt-5 flex flex-wrap gap-2">
            {ev.missing_keywords.map((kw) => (
              <span key={kw} className="rounded-full border border-[#1a1814]/15 bg-white/60 px-3 py-1 text-xs text-[#1a1814]">{kw}</span>
            ))}
          </div>
        </section>
      )}

      {ev.rationale && Object.keys(ev.rationale).length > 0 && (
        <section>
          <h2 className="font-serif text-3xl">Score rationale.</h2>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            {Object.entries(ev.rationale)
              .filter(([, v]) => Boolean(v))
              .map(([k, v]) => (
                <div key={k} className="rounded-2xl border border-[#1a1814]/10 bg-white/60 p-4 text-sm">
                  <p className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">{k.replace(/_/g, ' ')}</p>
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
            <p className="mt-2 break-all font-mono text-xs text-[#1a1814]">{ev.content_hash}</p>
            <p className="mt-2 text-[11px] text-[#3a342c]/70">
              sha256 of the application inputs ({shortHash(ev.content_hash)}).
            </p>
          </div>
          <div className="rounded-2xl border border-[#1a1814]/10 bg-white/60 p-4">
            <p className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">Contract address</p>
            <p className="mt-2 break-all font-mono text-xs text-[#1a1814]">{ev.contract_address}</p>
            <p className="mt-2 text-[11px] text-[#3a342c]/70">
              CVPilotEvaluator on GenLayer StudioNet ({shortHash(ev.contract_address)}).
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
