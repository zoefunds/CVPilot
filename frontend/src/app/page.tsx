import Link from "next/link";
import { LogoMark } from "@/components/brand/Logo";
import { Icon, type IconName } from "@/components/icons/Icon";

const metrics = [
  { value: "92%", label: "ATS Pass Rate" },
  { value: "12k+", label: "CVs Verified" },
  { value: "< 60s", label: "Analysis Time" },
  { value: "GenLayer", label: "Onchain Consensus" },
];

const features: { icon: IconName; title: string; body: string }[] = [
  { icon: "filter", title: "Real ATS analysis", body: "We mimic the same screening pass recruiters run before a human ever sees your CV. Formatting, contact discovery, keyword density." },
  { icon: "analytics", title: "Job specific scoring", body: "Paste a job URL. We scrape the posting, distill its real requirements, and grade your application against it specifically." },
  { icon: "edit", title: "Actionable rewrites", body: "No vague advice. Every recommendation names the exact missing keyword, the exact weak bullet, and the exact line to rewrite." },
  { icon: "shield_check", title: "Verifiable on GenLayer", body: "Every evaluation is recorded under validator consensus. Your score is auditable, verifiable, and undisputed by recruiters." },
  { icon: "psychology", title: "Cover letter intelligence", body: "Personalization, role title match, and company alignment cues. Measured per letter to ensure maximum relevance." },
];

const steps = [
  { n: 1, title: "Smart contract ingestion", body: "Your CV and job URL are securely parsed by Intelligent Contracts on GenLayer." },
  { n: 2, title: "Validator verification", body: "Three independent LLM validators score your application to reach objective consensus." },
  { n: 3, title: "Immutable receipt", body: "Final scores are timestamped and signed, providing proof of excellence for any recipient." },
];

export default function LandingPage() {
  return (
    <div className="ethereal-gradient min-h-screen text-[#1c1c17]" style={{ fontFamily: "Inter, sans-serif" }}>
      <nav className="fixed inset-x-0 top-0 z-50 border-b border-[#cdc5bc]/40 bg-[#fcf9f1]/85 backdrop-blur-md">
        <div className="mx-auto flex max-w-[1280px] items-center justify-between px-6 py-3 md:px-10">
          <Link href="/" className="flex items-center gap-2.5">
            <LogoMark size={30} />
            <span className="text-[22px] font-bold tracking-tight text-[#1c1c17]" style={{ fontFamily: "Literata, serif" }}>CVPilot</span>
          </Link>
          <div className="hidden items-center gap-7 md:flex">
            <a href="#features" className="text-[14px] font-semibold text-[#1c1c17]">Features</a>
            <a href="#how" className="text-[14px] text-[#4b463f] transition-colors hover:text-[#1c1c17]">How it works</a>
            <a href="#cta" className="text-[14px] text-[#4b463f] transition-colors hover:text-[#1c1c17]">Pricing</a>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/signin" className="hidden rounded-lg px-4 py-2 text-[14px] font-medium text-[#4b463f] transition-all hover:bg-[#f1eee6] active:scale-95 sm:inline-block">Sign in</Link>
            <Link href="/signup" className="rounded-lg bg-[#1c1c17] px-5 py-2.5 text-[14px] font-semibold text-white transition-all hover:bg-[#332f28] active:scale-95">Get started</Link>
          </div>
        </div>
      </nav>

      <main className="relative overflow-hidden pt-28 md:pt-32">
        <div className="hero-glow" />

        <section className="mx-auto mb-24 max-w-[1280px] px-6 md:px-10">
          <div className="grid grid-cols-1 items-center gap-12 md:grid-cols-12 md:gap-8">
            <div className="flex flex-col items-start gap-7 md:col-span-7">
              <div className="inline-flex items-center gap-2 rounded-full border border-[#cdc5bc]/60 bg-[#f1eee6] px-3 py-1.5">
                <Icon name="verified" size={14} className="text-[#1c1c17]" />
                <span className="text-[11px] font-semibold uppercase tracking-[0.12em] text-[#1c1c17]">Verifiable AI scoring on GenLayer</span>
              </div>
              <h1 className="text-[40px] leading-[1.05] tracking-tight text-[#1c1c17] md:text-[58px]" style={{ fontFamily: "Literata, serif", fontWeight: 700 }}>
                Stop sending applications<br />
                <span className="text-[#7c766e]">that quietly fail.</span>
              </h1>
              <p className="max-w-[560px] text-[17px] leading-relaxed text-[#4b463f] md:text-[18px]">
                CVPilot is an intelligent infrastructure that evaluates your CV and cover letter against the actual job. Keyword by keyword. We tell you, with onchain verifiable scoring, exactly what to fix before you hit send.
              </p>
              <div className="flex w-full flex-col gap-3 sm:flex-row sm:gap-3">
                <Link href="/signup" className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#1c1c17] px-7 py-3.5 text-[15px] font-semibold text-white shadow-lg shadow-[#1c1c17]/15 transition-all hover:bg-[#332f28] hover:shadow-xl hover:shadow-[#1c1c17]/20 active:scale-95">
                  Get my application graded
                  <Icon name="send" size={16} />
                </Link>
                <Link href="/signin" className="inline-flex items-center justify-center rounded-xl border border-[#cdc5bc] bg-white/70 px-7 py-3.5 text-[15px] font-medium text-[#1c1c17] transition-all hover:bg-white hover:shadow-sm active:scale-95">
                  I already have an account
                </Link>
              </div>
              <p className="flex items-center gap-2 text-[13px] font-medium text-[#7c766e]">
                <Icon name="bolt" size={14} className="text-[#1c1c17]" />
                Free to use. No sign up wall on the first evaluation.
              </p>
            </div>

            <div className="relative md:col-span-5">
              <div className="relative z-10 overflow-hidden rounded-[20px] border border-[#cdc5bc]/50 bg-[#fcf9f1] p-6 shadow-2xl shadow-[#1c1c17]/10">
                <div className="mb-6 flex items-start justify-between">
                  <div className="flex flex-col gap-1">
                    <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#7c766e]">Competitiveness</span>
                    <div className="flex items-baseline gap-1.5">
                      <span className="text-[44px] font-bold leading-none text-[#1c1c17]" style={{ fontFamily: "Literata, serif" }}>75</span>
                      <span className="text-[14px] text-[#7c766e]">/100</span>
                    </div>
                  </div>
                  <span className="rounded-md bg-[#1c1c17]/8 px-2 py-1 font-mono text-[10px] text-[#1c1c17]">0xc9A5…8A9e</span>
                </div>
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between rounded-lg border border-[#cdc5bc]/40 bg-white p-3">
                    <span className="text-[13px] text-[#1c1c17]">ATS Optimization</span>
                    <span className="text-[12px] font-bold text-[#1c1c17]">88%</span>
                  </div>
                  <div className="flex items-center justify-between rounded-lg border border-[#cdc5bc]/40 bg-white p-3">
                    <span className="text-[13px] text-[#1c1c17]">Skill Keyword Match</span>
                    <span className="text-[12px] font-bold text-[#1c1c17]">71%</span>
                  </div>
                  <div className="rounded-lg border border-[#1c1c17]/15 bg-[#1c1c17]/5 p-3">
                    <p className="mb-1 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-[#1c1c17]">
                      <Icon name="spark" size={12} />
                      Recommended action
                    </p>
                    <p className="text-[13px] leading-relaxed text-[#4b463f]">Mention &ldquo;distributed systems&rdquo; in your CV. Add a metric to line 2…</p>
                  </div>
                </div>
              </div>
              <div className="absolute -bottom-10 -left-10 -z-10 h-72 w-72 rounded-full bg-[#655d51]/15 blur-3xl" />
              <div className="absolute -top-10 -right-10 -z-10 h-56 w-56 rounded-full bg-[#cdc5bc]/40 blur-3xl" />
            </div>
          </div>
        </section>

        <section className="border-y border-[#cdc5bc]/40 bg-[#f1eee6]/60 py-14">
          <div className="mx-auto grid max-w-[1280px] grid-cols-2 gap-6 px-6 text-center md:grid-cols-4 md:px-10">
            {metrics.map((m) => (
              <div key={m.label} className="flex flex-col gap-1.5">
                <span className="text-[30px] font-extrabold text-[#1c1c17] md:text-[34px]" style={{ fontFamily: "Literata, serif" }}>{m.value}</span>
                <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#7c766e]">{m.label}</span>
              </div>
            ))}
          </div>
        </section>

        <section id="features" className="mx-auto max-w-[1280px] px-6 py-24 md:px-10">
          <div className="mb-12 max-w-[600px]">
            <span className="mb-3 block text-[10px] font-semibold uppercase tracking-[0.18em] text-[#1c1c17]">What we evaluate</span>
            <h2 className="text-[34px] leading-[1.1] tracking-tight text-[#1c1c17] md:text-[46px]" style={{ fontFamily: "Literata, serif", fontWeight: 700 }}>
              The full screening pass,<br /><span className="text-[#7c766e]">visible to you first.</span>
            </h2>
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3 md:gap-5">
            {features.map((f) => (
              <div key={f.title} className="group rounded-2xl border border-[#cdc5bc]/50 bg-[#fcf9f1]/80 p-6 transition-all hover:border-[#1c1c17]/30 hover:bg-[#fcf9f1] hover:shadow-lg hover:shadow-[#1c1c17]/5">
                <div className="mb-5 flex h-10 w-10 items-center justify-center rounded-lg bg-[#1c1c17]/8 text-[#1c1c17] transition-all group-hover:bg-[#1c1c17] group-hover:text-[#fcf9f1]">
                  <Icon name={f.icon} size={20} />
                </div>
                <h3 className="mb-2 text-[19px] text-[#1c1c17]" style={{ fontFamily: "Literata, serif", fontWeight: 600 }}>{f.title}</h3>
                <p className="text-[14px] leading-relaxed text-[#4b463f]">{f.body}</p>
              </div>
            ))}
          </div>
        </section>

        <section id="how" className="bg-[#1c1c17] py-24 text-[#fcf9f1]">
          <div className="mx-auto grid max-w-[1280px] grid-cols-1 items-center gap-14 px-6 md:grid-cols-2 md:px-10">
            <div>
              <span className="mb-3 block text-[10px] font-semibold uppercase tracking-[0.18em] text-[#cdc5bc]">The GenLayer advantage</span>
              <h2 className="mb-8 text-[34px] leading-[1.1] md:text-[46px]" style={{ fontFamily: "Literata, serif", fontWeight: 700 }}>
                Consensus driven<br />scoring infrastructure.
              </h2>
              <div className="space-y-6">
                {steps.map((s) => (
                  <div key={s.n} className="flex gap-4">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#fcf9f1]/15 text-[13px] font-bold text-[#fcf9f1]">{s.n}</div>
                    <div>
                      <h4 className="mb-1 text-[16px] font-semibold text-[#fcf9f1]">{s.title}</h4>
                      <p className="text-[14px] leading-relaxed text-[#cdc5bc]">{s.body}</p>
                    </div>
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
                        <Icon name={i === 4 ? "verified" : i % 2 === 0 ? "analytics" : "shield_check"} size={20} />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              <div className="absolute -bottom-6 -right-6 -z-10 h-40 w-40 rounded-full bg-[#cdc5bc]/10 blur-3xl" />
            </div>
          </div>
        </section>

        <section id="cta" className="relative overflow-hidden py-28">
          <div className="relative z-10 mx-auto max-w-[720px] px-6 text-center md:px-10">
            <span className="mb-5 block text-[10px] font-semibold uppercase tracking-[0.18em] text-[#1c1c17]">Stop guessing</span>
            <h2 className="mb-6 text-[34px] leading-[1.1] tracking-tight text-[#1c1c17] md:text-[48px]" style={{ fontFamily: "Literata, serif", fontWeight: 700 }}>
              See exactly where your application falls short.
            </h2>
            <p className="mb-9 text-[17px] leading-relaxed text-[#4b463f]">
              Upload your CV, drop in the job URL, and we deliver a consensus scored breakdown in under a minute. Always free.
            </p>
            <div className="flex flex-col justify-center gap-3 sm:flex-row">
              <Link href="/signup" className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#1c1c17] px-8 py-3.5 text-[15px] font-semibold text-white shadow-xl shadow-[#1c1c17]/15 transition-all hover:bg-[#332f28] active:scale-95">
                Get my application graded
                <Icon name="send" size={16} />
              </Link>
              <Link href="/signin" className="inline-flex items-center justify-center rounded-xl border border-[#cdc5bc] bg-white/70 px-8 py-3.5 text-[15px] font-semibold text-[#1c1c17] transition-all hover:bg-white active:scale-95">
                Sign in
              </Link>
            </div>
          </div>
          <div className="absolute bottom-0 left-1/2 -z-10 h-1/2 w-[120%] -translate-x-1/2 rounded-full bg-gradient-to-t from-[#1c1c17]/5 to-transparent blur-[120px]" />
        </section>
      </main>

      <footer className="border-t border-[#cdc5bc]/40 bg-[#f1eee6]/50">
        <div className="mx-auto flex max-w-[1280px] flex-col items-center justify-between gap-5 px-6 py-8 md:flex-row md:px-10">
          <div className="flex flex-col items-center gap-2 md:items-start">
            <Link href="/" className="flex items-center gap-2">
              <LogoMark size={24} />
              <span className="text-[18px] font-bold text-[#1c1c17]" style={{ fontFamily: "Literata, serif" }}>CVPilot</span>
            </Link>
            <p className="text-[12px] text-[#7c766e]">© 2026 CVPilot. Verifiable AI for job applications.</p>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-x-5 gap-y-2">
            <a href="/terms" className="text-[12px] text-[#4b463f] hover:text-[#1c1c17] hover:underline">Terms</a>
            <a href="/privacy" className="text-[12px] text-[#4b463f] hover:text-[#1c1c17] hover:underline">Privacy</a>
            <a href="/security" className="text-[12px] text-[#4b463f] hover:text-[#1c1c17] hover:underline">Security</a>
            <a href="/contact" className="text-[12px] text-[#4b463f] hover:text-[#1c1c17] hover:underline">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
