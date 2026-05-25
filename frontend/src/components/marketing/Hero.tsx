import { Button } from '@/components/ui/Button';
import { Container } from '@/components/ui/Container';

export function Hero() {
  return (
    <section className="bg_paper border-b border-[#d9d5c8]">
      <Container className="py-24 sm:py-32">
        <div className="grid items-center gap-16 lg:grid-cols-12">
          <div className="lg:col-span-7">
            <span className="inline-flex items-center gap-2 rounded-full border border-[#1a1814]/15 bg-white/40 px-3 py-1 text-xs uppercase tracking-[0.18em] text-[#3a342c]">
              <span className="h-1.5 w-1.5 rounded-full bg-[#2b4f3a]" />
              Verifiable AI scoring on GenLayer
            </span>
            <h1 className="mt-6 font-serif text-5xl leading-[1.05] sm:text-6xl lg:text-7xl">
              Stop sending applications
              <br />
              <span className="italic text-[#2b4f3a]">that quietly fail.</span>
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-relaxed text-[#3a342c]">
              CVPilot is an intelligent infrastructure that evaluates your
              CV and cover letter against the actual job. Keyword by keyword.
              Skill by skill. Achievement by achievement. We tell you, with
              onchain verifiable scoring, exactly what to fix before you hit
              send.
            </p>
            <div className="mt-10 flex flex-wrap gap-3">
              <Button href="/signup">Get my application graded</Button>
              <Button href="/signin" variant="ghost">
                I already have an account
              </Button>
            </div>
            <p className="mt-5 text-xs text-[#3a342c]/70">
              Free to use. No sign up wall on the first evaluation.
            </p>
          </div>

          <div className="lg:col-span-5">
            <MockScorecard />
          </div>
        </div>
      </Container>
    </section>
  );
}

function MockScorecard() {
  const scores = [
    { label: 'CV', value: 78, hint: '7 keyword matches' },
    { label: 'Cover Letter', value: 64, hint: 'Personalisation: medium' },
    { label: 'Job Match', value: 71, hint: 'Strong technical fit' },
    { label: 'ATS', value: 88, hint: 'Cleanly parseable' },
  ];
  const competitiveness = 75;
  return (
    <div className="rounded-3xl border border-[#1a1814]/10 bg-white/60 p-7 shadow-[0_20px_60px_-30px_rgba(26,24,20,0.35)] backdrop-blur-sm">
      <div className="flex items-baseline justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">
            Competitiveness
          </p>
          <p className="mt-1 font-serif text-6xl">{competitiveness}</p>
          <p className="text-xs text-[#3a342c]/70">/ 100</p>
        </div>
        <div className="flex flex-col items-end">
          <span className="rounded-full bg-[#2b4f3a]/10 px-2.5 py-1 text-[10px] uppercase tracking-widest text-[#2b4f3a]">
            Verified
          </span>
          <span className="mt-2 font-mono text-[10px] text-[#3a342c]/60">
            0xc9A5…8A9e
          </span>
        </div>
      </div>
      <div className="mt-6 grid grid-cols-2 gap-3">
        {scores.map((s) => (
          <div
            key={s.label}
            className="rounded-2xl border border-[#1a1814]/10 bg-[#efece4]/70 p-4"
          >
            <div className="flex items-baseline justify-between">
              <span className="text-xs uppercase tracking-[0.15em] text-[#3a342c]">
                {s.label}
              </span>
              <span className="font-serif text-2xl">{s.value}</span>
            </div>
            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-[#1a1814]/10">
              <div
                className="h-full bg-[#2b4f3a]"
                style={{ width: `${s.value}%` }}
              />
            </div>
            <p className="mt-2 text-[11px] leading-snug text-[#3a342c]/80">
              {s.hint}
            </p>
          </div>
        ))}
      </div>
      <div className="mt-6 rounded-2xl border border-dashed border-[#1a1814]/20 p-4 text-xs text-[#3a342c]">
        <p className="font-medium text-[#1a1814]">3 recommendations queued</p>
        <p className="mt-1">
          Mention &ldquo;distributed systems&rdquo; in your CV. Add a metric to
          line 2 of your cover letter. Reference the role title in the opener.
        </p>
      </div>
    </div>
  );
}
