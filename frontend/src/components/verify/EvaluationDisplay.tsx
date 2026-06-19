"use client";

import { ScoreGauge } from "@/components/ui/ScoreGauge";
import { Icon } from "@/components/icons/Icon";
import type { BiasAnalysis, CareerAnalysis, CoverLetterAnalysis, EvaluationExtras, LinkedInOptimisation, OutreachDraft, PublicEvaluation, ReadinessGate, SalaryEstimate, SkillsAnalysis, WeakBulletRewrite } from "@/lib/types";

function shortHash(h: string | null | undefined): string {
  if (!h) return "";
  if (h.length <= 14) return h;
  return `${h.slice(0, 8)}…${h.slice(-6)}`;
}

export function EvaluationDisplay({ ev }: { ev: PublicEvaluation }) {
  return (
    <div className="flex flex-col gap-10">
      <section className="rounded-3xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-7 shadow-sm shadow-[#1c1c17]/[0.04] sm:p-9">
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
              <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-emerald-800">
                <Icon name="shield_check" size={12} />
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
          <h2
            className="text-[24px] text-[#1c1c17]"
            style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
          >
            Recommendations
          </h2>
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
            <p className="mt-2 break-all font-mono text-[11px] text-[#1c1c17]">
              {ev.content_hash}
            </p>
            <p className="mt-2 text-[11px] text-[#7c766e]">
              sha256 of the application inputs ({shortHash(ev.content_hash)}).
            </p>
          </div>
          <div className="rounded-2xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-4">
            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">
              Contract address
            </p>
            <p className="mt-2 break-all font-mono text-[11px] text-[#1c1c17]">
              {ev.contract_address}
            </p>
            <p className="mt-2 text-[11px] text-[#7c766e]">
              CVPilotEvaluator on GenLayer StudioNet ({shortHash(ev.contract_address)}).
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Extended analyses panel (rendered when extras are present)
// ─────────────────────────────────────────────────────────────────────────────

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="text-[22px] text-[#1c1c17]" style={{ fontFamily: "Literata, serif", fontWeight: 700 }}>
      {children}
    </h2>
  );
}

function Pill({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded-full border border-[#cdc5bc] bg-white px-3 py-1 text-[12px] text-[#1c1c17]">
      {children}
    </span>
  );
}

function BulletList({ items }: { items: string[] }) {
  if (!items?.length) return null;
  return (
    <ul className="mt-3 grid gap-2">
      {items.map((item, i) => (
        <li key={i} className="flex items-start gap-2 text-[13px] leading-relaxed text-[#1c1c17]">
          <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-[#1c1c17]" />
          {item}
        </li>
      ))}
    </ul>
  );
}

function SkillsPanel({ data }: { data: SkillsAnalysis }) {
  return (
    <section className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <SectionTitle>Skills gap</SectionTitle>
        <span className="rounded-full bg-[#1c1c17] px-3 py-1 text-[12px] font-semibold text-white">
          {data.skill_match_score}/100 match
        </span>
      </div>

      {data.summary ? (
        <p className="text-[14px] leading-relaxed text-[#4b463f]">{data.summary}</p>
      ) : null}

      <div className="grid gap-5 sm:grid-cols-2">
        {data.gap_skills?.length > 0 && (
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">Skills to develop</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {data.gap_skills.map((s) => (
                <span key={s} className="rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-[12px] text-amber-900">{s}</span>
              ))}
            </div>
          </div>
        )}
        {data.bonus_skills?.length > 0 && (
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">Bonus skills</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {data.bonus_skills.map((s) => (
                <span key={s} className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-[12px] text-emerald-800">{s}</span>
              ))}
            </div>
          </div>
        )}
      </div>

      {data.upskilling_roadmap?.length > 0 && (
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">
            Upskilling roadmap {data.estimated_ramp_weeks ? `· ~${data.estimated_ramp_weeks} weeks` : ""}
          </p>
          <ol className="mt-3 grid gap-2">
            {data.upskilling_roadmap.map((step, i) => (
              <li key={i} className="flex items-start gap-3 rounded-xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-3">
                <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-[#1c1c17] text-[11px] font-bold text-white">
                  {i + 1}
                </span>
                <span className="text-[13px] leading-relaxed text-[#1c1c17]">{step}</span>
              </li>
            ))}
          </ol>
        </div>
      )}
    </section>
  );
}

function CareerPanel({ data }: { data: CareerAnalysis }) {
  return (
    <section className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center gap-3">
        <SectionTitle>Career trajectory</SectionTitle>
        <div className="flex flex-wrap gap-2">
          <Pill>{data.seniority_level?.replace(/_/g, " ")}</Pill>
          <Pill>{data.progression_type}</Pill>
          {data.years_of_experience > 0 && <Pill>{data.years_of_experience} yrs exp.</Pill>}
          <Pill>velocity: {data.promotion_velocity}</Pill>
        </div>
      </div>

      {data.summary ? (
        <p className="text-[14px] leading-relaxed text-[#4b463f]">{data.summary}</p>
      ) : null}

      <div className="grid gap-5 sm:grid-cols-2">
        {data.career_highlights?.length > 0 && (
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">Highlights</p>
            <BulletList items={data.career_highlights} />
          </div>
        )}
        {data.specialist_areas?.length > 0 && (
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">Specialist areas</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {data.specialist_areas.map((s) => <Pill key={s}>{s}</Pill>)}
            </div>
          </div>
        )}
      </div>

      {data.risks?.length > 0 && (
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">Flags</p>
          <BulletList items={data.risks} />
        </div>
      )}
    </section>
  );
}

function CoverLetterPanel({ data }: { data: CoverLetterAnalysis }) {
  return (
    <section className="flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <SectionTitle>Cover letter analysis</SectionTitle>
        <span className="rounded-full bg-[#1c1c17] px-3 py-1 text-[12px] font-semibold text-white">
          {data.score}/100
        </span>
      </div>

      <div className="flex flex-wrap gap-2">
        <Pill>tone: {data.tone_match}</Pill>
        <Pill>CTA: {data.call_to_action_strength?.replace(/_/g, " ")}</Pill>
        <Pill>length: {data.length_appropriateness?.replace(/_/g, " ")}</Pill>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {[
          { label: "Personalisation", val: data.personalization_score },
          { label: "Storytelling", val: data.storytelling_score },
          { label: "Keywords", val: data.keyword_density_score },
        ].map(({ label, val }) => (
          <div key={label} className="rounded-xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-4 text-center">
            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">{label}</p>
            <p className="mt-1 text-[28px] font-bold text-[#1c1c17]">{val}</p>
            <p className="text-[10px] text-[#7c766e]">/100</p>
          </div>
        ))}
      </div>

      {data.suggested_rewrites?.length > 0 && (
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">Suggested rewrites</p>
          <ul className="mt-3 grid gap-3">
            {data.suggested_rewrites.map((r, i) => (
              <li key={i} className="rounded-xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-4 text-[13px] italic leading-relaxed text-[#4b463f]">
                "{r}"
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

function SalaryPanel({ data }: { data: SalaryEstimate }) {
  return (
    <section className="flex flex-col gap-5">
      <SectionTitle>Salary estimate</SectionTitle>

      <div className="rounded-2xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-6">
        <div className="flex flex-wrap items-end gap-6">
          <div className="text-center">
            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">Range low</p>
            <p className="mt-1 text-[26px] font-bold text-[#1c1c17]">
              {data.currency} {data.range_low?.toLocaleString()}
            </p>
          </div>
          <div className="text-center">
            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">Mid</p>
            <p className="mt-1 text-[36px] font-bold text-[#1c1c17]">
              {data.currency} {data.range_mid?.toLocaleString()}
            </p>
          </div>
          <div className="text-center">
            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">Range high</p>
            <p className="mt-1 text-[26px] font-bold text-[#1c1c17]">
              {data.currency} {data.range_high?.toLocaleString()}
            </p>
          </div>
          <span className="rounded-full border border-[#cdc5bc] bg-white px-3 py-1 text-[12px] text-[#1c1c17]">
            confidence: {data.confidence}
          </span>
        </div>

        {data.rationale ? (
          <p className="mt-4 text-[13px] leading-relaxed text-[#4b463f]">{data.rationale}</p>
        ) : null}
      </div>

      {data.negotiation_tips?.length > 0 && (
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">Negotiation tips</p>
          <BulletList items={data.negotiation_tips} />
        </div>
      )}
    </section>
  );
}

function ReadinessPanel({ data }: { data: ReadinessGate }) {
  const verdictColor =
    data.go_no_go === "GO" ? "bg-emerald-100 text-emerald-800" :
    data.go_no_go === "NO_GO" ? "bg-red-100 text-red-800" :
    "bg-amber-100 text-amber-800";

  return (
    <section className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center gap-3">
        <SectionTitle>Readiness gate</SectionTitle>
        <span className={`rounded-full px-4 py-1 text-[13px] font-bold uppercase tracking-wide ${verdictColor}`}>
          {data.go_no_go?.replace(/_/g, " ")}
        </span>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {[
          { label: "Readiness score", val: data.readiness_score },
          { label: "Min. score to apply", val: data.minimum_score_to_apply },
          { label: "Prep days needed", val: data.estimated_prep_days },
        ].map(({ label, val }) => (
          <div key={label} className="rounded-xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-4 text-center">
            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">{label}</p>
            <p className="mt-1 text-[28px] font-bold text-[#1c1c17]">{val}</p>
          </div>
        ))}
      </div>

      {data.verdict_rationale ? (
        <p className="text-[14px] leading-relaxed text-[#4b463f]">{data.verdict_rationale}</p>
      ) : null}

      <div className="grid gap-5 sm:grid-cols-2">
        {data.top_blockers?.length > 0 && (
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">Top blockers</p>
            <BulletList items={data.top_blockers} />
          </div>
        )}
        {data.quick_wins?.length > 0 && (
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-emerald-700">Quick wins</p>
            <ul className="mt-3 grid gap-2">
              {data.quick_wins.map((item, i) => (
                <li key={i} className="flex items-start gap-2 text-[13px] leading-relaxed text-emerald-800">
                  <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-600" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </section>
  );
}

function BiasPanel({ data }: { data: BiasAnalysis }) {
  const scoreColor = data.bias_score <= 25 ? "bg-emerald-100 text-emerald-800" :
    data.bias_score <= 60 ? "bg-amber-100 text-amber-800" : "bg-red-100 text-red-800";

  return (
    <section className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center gap-3">
        <SectionTitle>Bias detection</SectionTitle>
        <span className={`rounded-full px-3 py-1 text-[12px] font-semibold ${scoreColor}`}>
          Bias score {data.bias_score}/100
        </span>
      </div>

      {data.summary ? <p className="text-[14px] leading-relaxed text-[#4b463f]">{data.summary}</p> : null}

      <div className="grid gap-5 sm:grid-cols-2">
        {data.detected_biases?.length > 0 && (
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-red-700">Detected biases</p>
            <BulletList items={data.detected_biases} />
          </div>
        )}
        {data.inclusive_signals?.length > 0 && (
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-emerald-700">Inclusive signals</p>
            <BulletList items={data.inclusive_signals} />
          </div>
        )}
      </div>

      {data.recommendations?.length > 0 && (
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">Recommendations</p>
          <BulletList items={data.recommendations} />
        </div>
      )}
    </section>
  );
}

function LinkedInPanel({ data }: { data: LinkedInOptimisation }) {
  return (
    <section className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center gap-3">
        <SectionTitle>LinkedIn optimisation</SectionTitle>
        <span className="rounded-full bg-[#0077b5] px-3 py-1 text-[12px] font-semibold text-white">
          Profile strength {data.profile_strength_score}/100
        </span>
      </div>

      {data.headline_options?.length > 0 && (
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">Headline options</p>
          <ul className="mt-3 grid gap-2">
            {data.headline_options.map((h, i) => (
              <li key={i} className="rounded-xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-3 text-[13px] font-medium text-[#1c1c17]">
                "{h}"
              </li>
            ))}
          </ul>
        </div>
      )}

      {data.about_section ? (
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">About section draft</p>
          <p className="mt-2 rounded-xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-4 text-[13px] leading-relaxed italic text-[#4b463f]">
            {data.about_section}
          </p>
        </div>
      ) : null}

      <div className="grid gap-5 sm:grid-cols-2">
        {data.key_skills_to_add?.length > 0 && (
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">Skills to add</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {data.key_skills_to_add.map((s) => <Pill key={s}>{s}</Pill>)}
            </div>
          </div>
        )}
        {data.network_growth_tips?.length > 0 && (
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">Network growth tips</p>
            <BulletList items={data.network_growth_tips} />
          </div>
        )}
      </div>
    </section>
  );
}

function OutreachPanel({ data }: { data: OutreachDraft }) {
  return (
    <section className="flex flex-col gap-5">
      <SectionTitle>Cold outreach</SectionTitle>

      {data.subject_lines?.length > 0 && (
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">Subject lines</p>
          <ul className="mt-3 grid gap-2">
            {data.subject_lines.map((s, i) => (
              <li key={i} className="rounded-xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-3 text-[13px] font-medium text-[#1c1c17]">
                {s}
              </li>
            ))}
          </ul>
        </div>
      )}

      {data.email_body ? (
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">Email draft</p>
          <p className="mt-2 whitespace-pre-line rounded-xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-4 text-[13px] leading-relaxed text-[#4b463f]">
            {data.email_body}
          </p>
        </div>
      ) : null}

      {data.linkedin_message ? (
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">LinkedIn message</p>
          <p className="mt-2 rounded-xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-4 text-[13px] leading-relaxed italic text-[#4b463f]">
            {data.linkedin_message}
          </p>
        </div>
      ) : null}

      {data.personalization_hooks?.length > 0 && (
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">Personalisation hooks</p>
          <BulletList items={data.personalization_hooks} />
        </div>
      )}
    </section>
  );
}

function WeakBulletPanel({ data }: { data: WeakBulletRewrite }) {
  return (
    <section className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center gap-3">
        <SectionTitle>Bullet rewriter</SectionTitle>
        {data.impact_improvement_score > 0 && (
          <span className="rounded-full bg-[#1c1c17] px-3 py-1 text-[12px] font-semibold text-white">
            +{data.impact_improvement_score} impact score
          </span>
        )}
      </div>

      {data.weak_bullets?.length > 0 && data.rewritten_bullets?.length > 0 && (
        <div className="grid gap-3">
          {data.weak_bullets.map((weak, i) => (
            <div key={i} className="rounded-2xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-4">
              <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-red-600">Before</p>
              <p className="mt-1 text-[13px] leading-relaxed text-[#4b463f] line-through">{weak}</p>
              {data.rewritten_bullets[i] && (
                <>
                  <p className="mt-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-emerald-700">After</p>
                  <p className="mt-1 text-[13px] font-medium leading-relaxed text-[#1c1c17]">{data.rewritten_bullets[i]}</p>
                </>
              )}
            </div>
          ))}
        </div>
      )}

      {data.action_verb_upgrades?.length > 0 && (
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">Action verb upgrades</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {data.action_verb_upgrades.map((v) => <Pill key={v}>{v}</Pill>)}
          </div>
        </div>
      )}
    </section>
  );
}

export function ExtrasPanel({ extras }: { extras: EvaluationExtras }) {
  const hasAny =
    extras.skills_analysis || extras.career_analysis ||
    extras.cover_letter_analysis || extras.salary_estimate ||
    extras.readiness_gate || extras.bias_analysis ||
    extras.linkedin_optimisation || extras.outreach_draft ||
    extras.weak_bullet_rewrite;
  if (!hasAny) return null;

  return (
    <div className="flex flex-col gap-10">
      {extras.readiness_gate && <ReadinessPanel data={extras.readiness_gate} />}
      {extras.skills_analysis && <SkillsPanel data={extras.skills_analysis} />}
      {extras.salary_estimate && <SalaryPanel data={extras.salary_estimate} />}
      {extras.career_analysis && <CareerPanel data={extras.career_analysis} />}
      {extras.cover_letter_analysis && <CoverLetterPanel data={extras.cover_letter_analysis} />}
      {extras.weak_bullet_rewrite && <WeakBulletPanel data={extras.weak_bullet_rewrite} />}
      {extras.bias_analysis && <BiasPanel data={extras.bias_analysis} />}
      {extras.linkedin_optimisation && <LinkedInPanel data={extras.linkedin_optimisation} />}
      {extras.outreach_draft && <OutreachPanel data={extras.outreach_draft} />}
    </div>
  );
}
