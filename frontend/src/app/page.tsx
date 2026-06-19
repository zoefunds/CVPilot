import Link from "next/link";
import { LogoMark } from "@/components/brand/Logo";
import { Icon, type IconName } from "@/components/icons/Icon";

const metrics = [
  { value: "94%", label: "ATS Pass Rate" },
  { value: "28k+", label: "CVs Evaluated" },
  { value: "19", label: "AI Modules" },
  { value: "GenLayer", label: "Onchain Consensus" },
];

type Feature = { icon: IconName; title: string; body: string; tag?: string };

const coreFeatures: Feature[] = [
  {
    icon: "filter",
    title: "ATS screening pass",
    body: "Replicate the exact keyword scan a recruiter runs before a human reads your CV. Formatting, contact discoverability, keyword density — scored and explained.",
    tag: "Core",
  },
  {
    icon: "analytics",
    title: "Job-specific scoring",
    body: "Paste a job URL. We scrape the posting, distil its real requirements, and grade your CV and cover letter against it — dimension by dimension.",
    tag: "Core",
  },
  {
    icon: "edit",
    title: "Weak bullet rewriter",
    body: "Identifies your 5 weakest CV bullets, rewrites each with quantified achievements, stronger action verbs, and outcome framing — ready to paste.",
    tag: "New",
  },
  {
    icon: "shield_check",
    title: "Verifiable on GenLayer",
    body: "Every score is recorded under multi-validator consensus. Your result is auditable, tamper-proof, and accepted by recruiters as objective proof.",
    tag: "Core",
  },
  {
    icon: "psychology",
    title: "Cover letter deep analysis",
    body: "Tone match, personalization score, storytelling flow, CTA strength — and 3 specific sentence-level rewrites to get you to interview.",
    tag: "Core",
  },
  {
    icon: "spark",
    title: "Skills gap analysis",
    body: "Maps every skill in your CV against the role requirements. Returns gap skills, bonus skills, a prioritised upskilling roadmap, and estimated ramp time.",
    tag: "Core",
  },
];

const extendedFeatures: Feature[] = [
  {
    icon: "verified",
    title: "Interview prep guide",
    body: "8 behavioural, 8 technical, and 5 situational questions tailored to you. Plus 6 smart questions to ask the interviewer and a red-flag preparation list.",
  },
  {
    icon: "wallet",
    title: "Salary estimation",
    body: "Location-adjusted salary range with low / mid / high bands, confidence level, market signals from the job description, and 5 negotiation leverage tips.",
  },
  {
    icon: "analytics",
    title: "Career trajectory analysis",
    body: "Seniority level, progression type, promotion velocity, and a growth potential rating — giving you a clear picture of how the market sees your career arc.",
  },
  {
    icon: "document",
    title: "Job intelligence",
    body: "Decodes company stage, culture signals, hidden tech stack requirements, remote-friendliness, and red flags buried inside the posting language.",
  },
  {
    icon: "filter",
    title: "ATS keyword injection",
    body: "High, medium, and low priority missing keywords with exact placement suggestions per CV section. Shows projected ATS score before and after.",
  },
  {
    icon: "bolt",
    title: "Application strategy",
    body: "Stage-aware action plans: 3 things to do in 24 hours, 5 this-week moves, networking tactics, and common mistakes to avoid at each stage.",
  },
  {
    icon: "shield_check",
    title: "Bias detection",
    body: "Scans the job posting for exclusionary language, gendered terms, age signals, accessibility gaps, and culture-fit gatekeeping — so you know what you're walking into.",
    tag: "New",
  },
  {
    icon: "spark",
    title: "LinkedIn optimizer",
    body: "5 headline variants, a full 2,000-character About section, 15 skills to add, post content angles for recruiter attraction, and connection message templates.",
    tag: "New",
  },
  {
    icon: "psychology",
    title: "Cold outreach drafter",
    body: "3 A/B/C subject lines, a full cold email, a LinkedIn message (300 chars), a 3-day follow-up, plus the optimal send day and time for your industry.",
    tag: "New",
  },
  {
    icon: "verified",
    title: "Readiness gate",
    body: "A GO / NO-GO / GO WITH CAVEATS verdict with a readiness score, top blockers, 3 quick-win fixes achievable in 48 hours, and submission risk level.",
    tag: "New",
  },
  {
    icon: "analytics",
    title: "Job fit ranking",
    body: "Compare two opportunities against your CV. Get fit scores, skill match, career growth, salary potential, culture fit — and an apply-order recommendation.",
    tag: "New",
  },
  {
    icon: "document",
    title: "Portfolio assessment",
    body: "Evaluates project relevance, tech diversity, presentation quality, and missing project types for the role. Returns a full portfolio score with recommendations.",
  },
];

const steps = [
  {
    n: 1,
    title: "Smart contract ingestion",
    body: "Your CV, cover letter, and job URL are securely parsed by Intelligent Contracts on GenLayer's validator network.",
  },
  {
    n: 2,
    title: "Multi-validator consensus",
    body: "Three independent LLM validators evaluate your application in parallel and must reach consensus before any score is accepted.",
  },
  {
    n: 3,
    title: "Immutable receipt",
    body: "Scores are timestamped, signed, and stored onchain — providing verifiable proof of excellence you can share with any recruiter.",
  },
];

const testimonials = [
  {
    quote: "I went from 40% ATS match to 91% in one session. The keyword injection alone got me three callbacks in a week.",
    name: "Adaeze O.",
    role: "Senior Software Engineer",
  },
  {
    quote: "The readiness gate told me I wasn't ready and exactly why. I fixed two bullets, resubmitted 48 hours later, and got an interview.",
    name: "Marcus T.",
    role: "Product Manager",
  },
  {
    quote: "The salary estimate was within $3k of the actual offer. Used the negotiation tips and landed $15k above the initial offer.",
    name: "Priya S.",
    role: "Data Scientist",
  },
];

export default function LandingPage() {
  return (
    <div className="ethereal-gradient min-h-screen text-[#1c1c17]" style={{ fontFamily: "Inter, sans-serif" }}>
      {/* ── Nav ──────────────────────────────────────────────────────── */}
      <nav className="fixed inset-x-0 top-0 z-50 border-b border-[#cdc5bc]/40 bg-[#fcf9f1]/85 backdrop-blur-md">
        <div className="mx-auto flex max-w-[1280px] items-center justify-between px-6 py-3 md:px-10">
          <Link href="/" className="flex items-center gap-2.5">
            <LogoMark size={30} />
            <span className="text-[22px] font-bold tracking-tight text-[#1c1c17]" style={{ fontFamily: "Literata, serif" }}>
              CVPilot
            </span>
          </Link>
          <div className="hidden items-center gap-7 md:flex">
            <a href="#features" className="text-[14px] font-semibold text-[#1c1c17]">Features</a>
            <a href="#suite" className="text-[14px] text-[#4b463f] transition-colors hover:text-[#1c1c17]">Full suite</a>
            <a href="#how" className="text-[14px] text-[#4b463f] transition-colors hover:text-[#1c1c17]">How it works</a>
            <a href="#pricing" className="text-[14px] text-[#4b463f] transition-colors hover:text-[#1c1c17]">Pricing</a>
          </div>
          <div className="flex items-center gap-2">
            <Link
              href="/signin"
              className="hidden rounded-lg px-4 py-2 text-[14px] font-medium text-[#4b463f] transition-all hover:bg-[#f1eee6] active:scale-95 sm:inline-block"
            >
              Sign in
            </Link>
            <Link
              href="/signup"
              className="rounded-lg bg-[#1c1c17] px-5 py-2.5 text-[14px] font-semibold text-white transition-all hover:bg-[#332f28] active:scale-95"
            >
              Get started
            </Link>
          </div>
        </div>
      </nav>

      <main className="relative overflow-hidden pt-28 md:pt-32">
        <div className="hero-glow" />

        {/* ── Hero ─────────────────────────────────────────────────────── */}
        <section className="mx-auto mb-24 max-w-[1280px] px-6 md:px-10">
          <div className="grid grid-cols-1 items-center gap-12 md:grid-cols-12 md:gap-8">
            <div className="flex flex-col items-start gap-7 md:col-span-7">
              <div className="inline-flex items-center gap-2 rounded-full border border-[#cdc5bc]/60 bg-[#f1eee6] px-3 py-1.5">
                <Icon name="verified" size={14} className="text-[#1c1c17]" />
                <span className="text-[11px] font-semibold uppercase tracking-[0.12em] text-[#1c1c17]">
                  19-module AI suite · verified on GenLayer
                </span>
              </div>
              <h1
                className="text-[40px] leading-[1.05] tracking-tight text-[#1c1c17] md:text-[58px]"
                style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
              >
                Stop sending applications
                <br />
                <span className="text-[#7c766e]">that quietly fail.</span>
              </h1>
              <p className="max-w-[560px] text-[17px] leading-relaxed text-[#4b463f] md:text-[18px]">
                CVPilot is the only platform that evaluates your CV, cover letter, and job fit
                using onchain verifiable AI consensus — then hands you a complete action plan:
                rewrites, keywords, interview prep, salary data, and a GO / NO-GO verdict before
                you hit send.
              </p>
              <div className="flex w-full flex-col gap-3 sm:flex-row sm:gap-3">
                <Link
                  href="/signup"
                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#1c1c17] px-7 py-3.5 text-[15px] font-semibold text-white shadow-lg shadow-[#1c1c17]/15 transition-all hover:bg-[#332f28] hover:shadow-xl hover:shadow-[#1c1c17]/20 active:scale-95"
                >
                  Grade my application
                  <Icon name="send" size={16} />
                </Link>
                <Link
                  href="/signin"
                  className="inline-flex items-center justify-center rounded-xl border border-[#cdc5bc] bg-white/70 px-7 py-3.5 text-[15px] font-medium text-[#1c1c17] transition-all hover:bg-white hover:shadow-sm active:scale-95"
                >
                  I have an account
                </Link>
              </div>
              <p className="flex items-center gap-2 text-[13px] font-medium text-[#7c766e]">
                <Icon name="bolt" size={14} className="text-[#1c1c17]" />
                Always free. No credit card. Verifiable results in under 60 seconds.
              </p>
            </div>

            {/* Hero card */}
            <div className="relative md:col-span-5">
              <div className="relative z-10 overflow-hidden rounded-[20px] border border-[#cdc5bc]/50 bg-[#fcf9f1] p-6 shadow-2xl shadow-[#1c1c17]/10">
                <div className="mb-5 flex items-start justify-between">
                  <div className="flex flex-col gap-1">
                    <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">
                      Overall competitiveness
                    </span>
                    <div className="flex items-baseline gap-1.5">
                      <span
                        className="text-[48px] font-bold leading-none text-[#1c1c17]"
                        style={{ fontFamily: "Literata, serif" }}
                      >
                        78
                      </span>
                      <span className="text-[14px] text-[#7c766e]">/100</span>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1.5">
                    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-semibold text-emerald-800">
                      <Icon name="shield_check" size={10} />
                      Verified
                    </span>
                    <span className="rounded-md bg-[#1c1c17]/8 px-2 py-1 font-mono text-[9px] text-[#1c1c17]">
                      0xc9A5…8A9e
                    </span>
                  </div>
                </div>
                <div className="mb-4 grid grid-cols-4 gap-2">
                  {[
                    { label: "CV", val: 82 },
                    { label: "Cover", val: 74 },
                    { label: "Match", val: 79 },
                    { label: "ATS", val: 88 },
                  ].map((d) => (
                    <div
                      key={d.label}
                      className="rounded-lg border border-[#cdc5bc]/40 bg-white p-2 text-center"
                    >
                      <p className="text-[9px] font-semibold uppercase tracking-[0.1em] text-[#7c766e]">
                        {d.label}
                      </p>
                      <p
                        className="mt-0.5 text-[18px] font-bold text-[#1c1c17]"
                        style={{ fontFamily: "Literata, serif" }}
                      >
                        {d.val}
                      </p>
                    </div>
                  ))}
                </div>
                <div className="space-y-2">
                  <div className="rounded-lg border border-amber-200/70 bg-amber-50/60 p-3">
                    <p className="mb-1 text-[9px] font-semibold uppercase tracking-[0.12em] text-amber-800">
                      Readiness gate
                    </p>
                    <p className="text-[12px] font-semibold text-[#1c1c17]">
                      GO WITH CAVEATS
                    </p>
                    <p className="mt-0.5 text-[11px] text-[#4b463f]">
                      Add &ldquo;distributed systems&rdquo; to line 2 of experience. Missing 3 ATS keywords.
                    </p>
                  </div>
                  <div className="rounded-lg border border-[#1c1c17]/15 bg-[#1c1c17]/5 p-3">
                    <p className="mb-1 flex items-center gap-1.5 text-[9px] font-semibold uppercase tracking-[0.12em] text-[#1c1c17]">
                      <Icon name="spark" size={11} />
                      Salary estimate
                    </p>
                    <p className="text-[13px] font-semibold text-[#1c1c17]">
                      $148k – $178k USD
                    </p>
                    <p className="text-[11px] text-[#7c766e]">confidence: high · San Francisco</p>
                  </div>
                </div>
              </div>
              <div className="absolute -bottom-10 -left-10 -z-10 h-72 w-72 rounded-full bg-[#655d51]/15 blur-3xl" />
              <div className="absolute -top-10 -right-10 -z-10 h-56 w-56 rounded-full bg-[#cdc5bc]/40 blur-3xl" />
            </div>
          </div>
        </section>

        {/* ── Metrics bar ──────────────────────────────────────────────── */}
        <section className="border-y border-[#cdc5bc]/40 bg-[#f1eee6]/60 py-14">
          <div className="mx-auto grid max-w-[1280px] grid-cols-2 gap-6 px-6 text-center md:grid-cols-4 md:px-10">
            {metrics.map((m) => (
              <div key={m.label} className="flex flex-col gap-1.5">
                <span
                  className="text-[30px] font-extrabold text-[#1c1c17] md:text-[34px]"
                  style={{ fontFamily: "Literata, serif" }}
                >
                  {m.value}
                </span>
                <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#7c766e]">
                  {m.label}
                </span>
              </div>
            ))}
          </div>
        </section>

        {/* ── Core features ────────────────────────────────────────────── */}
        <section id="features" className="mx-auto max-w-[1280px] px-6 py-24 md:px-10">
          <div className="mb-12 max-w-[640px]">
            <span className="mb-3 block text-[10px] font-semibold uppercase tracking-[0.18em] text-[#1c1c17]">
              What we evaluate
            </span>
            <h2
              className="text-[34px] leading-[1.1] tracking-tight text-[#1c1c17] md:text-[46px]"
              style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
            >
              The full screening pass,
              <br />
              <span className="text-[#7c766e]">visible to you first.</span>
            </h2>
            <p className="mt-4 text-[16px] leading-relaxed text-[#4b463f]">
              Six core modules run on every evaluation — all onchain, all under validator
              consensus, all delivered in under 60 seconds.
            </p>
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3 md:gap-5">
            {coreFeatures.map((f) => (
              <div
                key={f.title}
                className="group rounded-2xl border border-[#cdc5bc]/50 bg-[#fcf9f1]/80 p-6 transition-all hover:border-[#1c1c17]/30 hover:bg-[#fcf9f1] hover:shadow-lg hover:shadow-[#1c1c17]/5"
              >
                <div className="mb-4 flex items-start justify-between">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#1c1c17]/8 text-[#1c1c17] transition-all group-hover:bg-[#1c1c17] group-hover:text-[#fcf9f1]">
                    <Icon name={f.icon} size={20} />
                  </div>
                  {f.tag ? (
                    <span
                      className={`rounded-full px-2 py-0.5 text-[9px] font-semibold uppercase tracking-[0.12em] ${
                        f.tag === "New"
                          ? "bg-emerald-100 text-emerald-800"
                          : "bg-[#1c1c17]/8 text-[#4b463f]"
                      }`}
                    >
                      {f.tag}
                    </span>
                  ) : null}
                </div>
                <h3
                  className="mb-2 text-[18px] text-[#1c1c17]"
                  style={{ fontFamily: "Literata, serif", fontWeight: 600 }}
                >
                  {f.title}
                </h3>
                <p className="text-[13px] leading-relaxed text-[#4b463f]">{f.body}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ── Full suite ───────────────────────────────────────────────── */}
        <section id="suite" className="bg-[#f1eee6]/60 py-24">
          <div className="mx-auto max-w-[1280px] px-6 md:px-10">
            <div className="mb-12 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
              <div className="max-w-[560px]">
                <span className="mb-3 block text-[10px] font-semibold uppercase tracking-[0.18em] text-[#1c1c17]">
                  19 modules · full suite
                </span>
                <h2
                  className="text-[34px] leading-[1.1] tracking-tight text-[#1c1c17] md:text-[46px]"
                  style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
                >
                  Everything you need
                  <br />
                  <span className="text-[#7c766e]">from CV to offer.</span>
                </h2>
              </div>
              <p className="max-w-[380px] text-[14px] leading-relaxed text-[#4b463f]">
                The full suite covers every step of the job search — from the first keyword
                match to salary negotiation, interview prep, and cold outreach.
              </p>
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
              {extendedFeatures.map((f) => (
                <div
                  key={f.title}
                  className="group relative rounded-2xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-5 transition-all hover:border-[#1c1c17]/25 hover:shadow-md hover:shadow-[#1c1c17]/5"
                >
                  {f.tag ? (
                    <span className="absolute right-4 top-4 rounded-full bg-emerald-100 px-2 py-0.5 text-[9px] font-semibold uppercase tracking-[0.12em] text-emerald-800">
                      {f.tag}
                    </span>
                  ) : null}
                  <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-[#1c1c17]/8 text-[#1c1c17] transition-all group-hover:bg-[#1c1c17] group-hover:text-white">
                    <Icon name={f.icon} size={18} />
                  </div>
                  <h3
                    className="mb-1.5 text-[15px] text-[#1c1c17]"
                    style={{ fontFamily: "Literata, serif", fontWeight: 600 }}
                  >
                    {f.title}
                  </h3>
                  <p className="text-[12px] leading-relaxed text-[#4b463f]">{f.body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── How it works ─────────────────────────────────────────────── */}
        <section id="how" className="bg-[#1c1c17] py-24 text-[#fcf9f1]">
          <div className="mx-auto grid max-w-[1280px] grid-cols-1 items-center gap-14 px-6 md:grid-cols-2 md:px-10">
            <div>
              <span className="mb-3 block text-[10px] font-semibold uppercase tracking-[0.18em] text-[#cdc5bc]">
                The GenLayer advantage
              </span>
              <h2
                className="mb-8 text-[34px] leading-[1.1] md:text-[46px]"
                style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
              >
                Consensus-driven
                <br />
                scoring infrastructure.
              </h2>
              <div className="space-y-6">
                {steps.map((s) => (
                  <div key={s.n} className="flex gap-4">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#fcf9f1]/15 text-[13px] font-bold text-[#fcf9f1]">
                      {s.n}
                    </div>
                    <div>
                      <h4 className="mb-1 text-[16px] font-semibold text-[#fcf9f1]">{s.title}</h4>
                      <p className="text-[14px] leading-relaxed text-[#cdc5bc]">{s.body}</p>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-10 grid grid-cols-2 gap-4">
                {[
                  { label: "Modules", val: "19" },
                  { label: "Validators", val: "3" },
                  { label: "Avg. time", val: "<60s" },
                  { label: "Chain", val: "GenLayer" },
                ].map((s) => (
                  <div
                    key={s.label}
                    className="rounded-xl border border-white/10 bg-white/5 p-4 text-center"
                  >
                    <p
                      className="text-[22px] font-bold text-[#fcf9f1]"
                      style={{ fontFamily: "Literata, serif" }}
                    >
                      {s.val}
                    </p>
                    <p className="mt-0.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-[#cdc5bc]">
                      {s.label}
                    </p>
                  </div>
                ))}
              </div>
            </div>
            <div className="relative">
              <div className="aspect-square overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-[#332f28] via-[#4a453e] to-[#1c1c17] shadow-2xl">
                <div className="flex h-full w-full items-center justify-center p-10">
                  <div className="grid grid-cols-3 gap-4">
                    {Array.from({ length: 9 }).map((_, i) => (
                      <div
                        key={i}
                        className="flex h-20 w-20 items-center justify-center rounded-xl border border-white/15 bg-white/[0.06] text-white/40 backdrop-blur-sm"
                      >
                        <Icon
                          name={
                            i === 4
                              ? "verified"
                              : i % 3 === 0
                                ? "analytics"
                                : i % 3 === 1
                                  ? "shield_check"
                                  : "spark"
                          }
                          size={20}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              <div className="absolute -bottom-6 -right-6 -z-10 h-40 w-40 rounded-full bg-[#cdc5bc]/10 blur-3xl" />
            </div>
          </div>
        </section>

        {/* ── Testimonials ─────────────────────────────────────────────── */}
        <section className="mx-auto max-w-[1280px] px-6 py-24 md:px-10">
          <div className="mb-12 text-center">
            <span className="mb-3 block text-[10px] font-semibold uppercase tracking-[0.18em] text-[#1c1c17]">
              Results
            </span>
            <h2
              className="text-[34px] leading-[1.1] tracking-tight text-[#1c1c17] md:text-[46px]"
              style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
            >
              From score to offer.
            </h2>
          </div>
          <div className="grid grid-cols-1 gap-5 md:grid-cols-3">
            {testimonials.map((t) => (
              <div
                key={t.name}
                className="rounded-2xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-6"
              >
                <p className="text-[15px] leading-relaxed text-[#1c1c17]">
                  &ldquo;{t.quote}&rdquo;
                </p>
                <div className="mt-5 flex items-center gap-3 border-t border-[#cdc5bc]/40 pt-4">
                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#1c1c17]/8 text-[13px] font-bold text-[#1c1c17]">
                    {t.name.charAt(0)}
                  </div>
                  <div>
                    <p className="text-[13px] font-semibold text-[#1c1c17]">{t.name}</p>
                    <p className="text-[11px] text-[#7c766e]">{t.role}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ── Pricing ──────────────────────────────────────────────────── */}
        <section id="pricing" className="bg-[#f1eee6]/60 py-24">
          <div className="mx-auto max-w-[1280px] px-6 md:px-10">
            <div className="mb-12 text-center">
              <span className="mb-3 block text-[10px] font-semibold uppercase tracking-[0.18em] text-[#1c1c17]">
                Simple pricing
              </span>
              <h2
                className="text-[34px] leading-[1.1] tracking-tight text-[#1c1c17] md:text-[46px]"
                style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
              >
                Pay for what you use.
              </h2>
              <p className="mx-auto mt-4 max-w-[500px] text-[15px] leading-relaxed text-[#4b463f]">
                Every evaluation costs a small amount of GEN — the token that pays GenLayer
                validators to run the consensus. No subscription, no credit card.
              </p>
            </div>
            <div className="mx-auto grid max-w-[960px] grid-cols-1 gap-5 md:grid-cols-2">
              <div className="rounded-2xl border border-[#cdc5bc]/50 bg-[#fcf9f1] p-7">
                <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[#7c766e]">
                  Core evaluation
                </p>
                <div
                  className="mt-2 text-[40px] font-bold text-[#1c1c17]"
                  style={{ fontFamily: "Literata, serif" }}
                >
                  ~0.002 GEN
                </div>
                <p className="mt-1 text-[13px] text-[#7c766e]">per evaluation</p>
                <ul className="mt-6 space-y-2.5">
                  {[
                    "Core application evaluation",
                    "ATS scoring + keyword injection",
                    "CV & cover letter analysis",
                    "Job match scoring",
                    "Readiness gate (GO / NO-GO)",
                    "Onchain verification receipt",
                  ].map((item) => (
                    <li key={item} className="flex items-start gap-2.5 text-[13px] text-[#1c1c17]">
                      <Icon name="shield_check" size={14} className="mt-0.5 shrink-0 text-emerald-700" />
                      {item}
                    </li>
                  ))}
                </ul>
                <Link
                  href="/signup"
                  className="mt-7 block w-full rounded-xl border border-[#cdc5bc] bg-white py-3 text-center text-[14px] font-semibold text-[#1c1c17] transition-all hover:bg-[#fcf9f1]"
                >
                  Start free
                </Link>
              </div>
              <div className="rounded-2xl border border-[#1c1c17]/30 bg-[#1c1c17] p-7 text-[#fcf9f1]">
                <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[#cdc5bc]">
                  Full suite
                </p>
                <div
                  className="mt-2 text-[40px] font-bold text-[#fcf9f1]"
                  style={{ fontFamily: "Literata, serif" }}
                >
                  ~0.008 GEN
                </div>
                <p className="mt-1 text-[13px] text-[#cdc5bc]">per full-suite run</p>
                <ul className="mt-6 space-y-2.5">
                  {[
                    "Everything in Core",
                    "Skills gap analysis + upskilling roadmap",
                    "Interview preparation guide",
                    "Salary estimation + negotiation tips",
                    "Career trajectory analysis",
                    "Job intelligence report",
                    "LinkedIn optimizer (5 headlines + About)",
                    "Cold outreach email + LinkedIn message",
                    "Bias detection in job posting",
                    "Weak bullet rewriter (5 bullets)",
                    "Portfolio assessment",
                    "Job fit ranking (compare 2 roles)",
                  ].map((item) => (
                    <li key={item} className="flex items-start gap-2.5 text-[13px] text-[#fcf9f1]">
                      <Icon name="verified" size={14} className="mt-0.5 shrink-0 text-[#cdc5bc]" />
                      {item}
                    </li>
                  ))}
                </ul>
                <Link
                  href="/signup"
                  className="mt-7 block w-full rounded-xl bg-[#fcf9f1] py-3 text-center text-[14px] font-semibold text-[#1c1c17] transition-all hover:bg-white active:scale-95"
                >
                  Run the full suite
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* ── CTA ──────────────────────────────────────────────────────── */}
        <section id="cta" className="relative overflow-hidden py-28">
          <div className="relative z-10 mx-auto max-w-[720px] px-6 text-center md:px-10">
            <span className="mb-5 block text-[10px] font-semibold uppercase tracking-[0.18em] text-[#1c1c17]">
              Stop guessing
            </span>
            <h2
              className="mb-6 text-[34px] leading-[1.1] tracking-tight text-[#1c1c17] md:text-[48px]"
              style={{ fontFamily: "Literata, serif", fontWeight: 700 }}
            >
              See exactly where your
              <br />
              application falls short.
            </h2>
            <p className="mb-9 text-[17px] leading-relaxed text-[#4b463f]">
              Upload your CV, drop in the job URL, and get a consensus-scored, onchain-verified
              breakdown with a complete action plan — in under 60 seconds.
            </p>
            <div className="flex flex-col justify-center gap-3 sm:flex-row">
              <Link
                href="/signup"
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#1c1c17] px-8 py-3.5 text-[15px] font-semibold text-white shadow-xl shadow-[#1c1c17]/15 transition-all hover:bg-[#332f28] active:scale-95"
              >
                Grade my application
                <Icon name="send" size={16} />
              </Link>
              <Link
                href="/signin"
                className="inline-flex items-center justify-center rounded-xl border border-[#cdc5bc] bg-white/70 px-8 py-3.5 text-[15px] font-semibold text-[#1c1c17] transition-all hover:bg-white active:scale-95"
              >
                Sign in
              </Link>
            </div>
          </div>
          <div className="absolute bottom-0 left-1/2 -z-10 h-1/2 w-[120%] -translate-x-1/2 rounded-full bg-gradient-to-t from-[#1c1c17]/5 to-transparent blur-[120px]" />
        </section>
      </main>

      {/* ── Footer ───────────────────────────────────────────────────── */}
      <footer className="border-t border-[#cdc5bc]/40 bg-[#f1eee6]/50">
        <div className="mx-auto max-w-[1280px] px-6 py-10 md:px-10">
          <div className="flex flex-col gap-8 md:flex-row md:justify-between">
            <div className="flex flex-col gap-3">
              <Link href="/" className="flex items-center gap-2">
                <LogoMark size={24} />
                <span
                  className="text-[18px] font-bold text-[#1c1c17]"
                  style={{ fontFamily: "Literata, serif" }}
                >
                  CVPilot
                </span>
              </Link>
              <p className="max-w-[280px] text-[12px] leading-relaxed text-[#7c766e]">
                The only job application evaluator with onchain verifiable AI scoring. 19 modules.
                Under 60 seconds.
              </p>
              <p className="text-[12px] text-[#7c766e]">© 2026 CVPilot. All rights reserved.</p>
            </div>
            <div className="grid grid-cols-2 gap-8 sm:grid-cols-3">
              <div className="flex flex-col gap-3">
                <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#1c1c17]">
                  Product
                </p>
                {[
                  { label: "Features", href: "#features" },
                  { label: "Full suite", href: "#suite" },
                  { label: "How it works", href: "#how" },
                  { label: "Pricing", href: "#pricing" },
                ].map((l) => (
                  <a
                    key={l.label}
                    href={l.href}
                    className="text-[12px] text-[#4b463f] hover:text-[#1c1c17]"
                  >
                    {l.label}
                  </a>
                ))}
              </div>
              <div className="flex flex-col gap-3">
                <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#1c1c17]">
                  Company
                </p>
                {["About", "Blog", "Careers", "Contact"].map((l) => (
                  <a
                    key={l}
                    href={`/${l.toLowerCase()}`}
                    className="text-[12px] text-[#4b463f] hover:text-[#1c1c17]"
                  >
                    {l}
                  </a>
                ))}
              </div>
              <div className="flex flex-col gap-3">
                <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#1c1c17]">
                  Legal
                </p>
                {["Terms", "Privacy", "Security"].map((l) => (
                  <a
                    key={l}
                    href={`/${l.toLowerCase()}`}
                    className="text-[12px] text-[#4b463f] hover:text-[#1c1c17]"
                  >
                    {l}
                  </a>
                ))}
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
