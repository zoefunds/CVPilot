import { Container } from '@/components/ui/Container';

const features = [
  {
    title: 'Real ATS analysis',
    body: 'We mimic the same screening pass recruiters run before a human ever sees your CV. Formatting, contact discovery, keyword density, glyph cleanliness.',
  },
  {
    title: 'Job specific scoring',
    body: 'Paste a job URL. We scrape the posting, distill its real requirements, and grade your application against it, not against a generic rubric.',
  },
  {
    title: 'Actionable rewrites',
    body: 'No vague advice. Every recommendation names the exact missing keyword, the exact weak bullet, the exact line to rewrite.',
  },
  {
    title: 'Verifiable on GenLayer',
    body: 'Every evaluation is recorded under validator consensus on GenLayer StudioNet. Your score is auditable. Your employer can verify it. Recruiters cannot dispute it.',
  },
  {
    title: 'Cover letter intelligence',
    body: 'Personalisation, addressee, role title match, company alignment cues, length budget. Measured per letter, not assumed.',
  },
  {
    title: 'Premium AI rewriting',
    body: 'The same engine that scored you rewrites your CV and drafts an interview ready cover letter, tuned precisely to the posting. Premium quality output, free for every user.',
  },
];

export function Features() {
  return (
    <section className="border-b border-[#d9d5c8] py-24">
      <Container>
        <div className="max-w-3xl">
          <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">
            What we evaluate
          </p>
          <h2 className="mt-3 font-serif text-4xl leading-tight sm:text-5xl">
            The full screening pass,
            <br />
            <span className="italic text-[#2b4f3a]">visible to you first.</span>
          </h2>
        </div>
        <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f) => (
            <div
              key={f.title}
              className="rounded-2xl border border-[#1a1814]/10 bg-white/40 p-6"
            >
              <h3 className="font-serif text-xl">{f.title}</h3>
              <p className="mt-3 text-sm leading-relaxed text-[#3a342c]">
                {f.body}
              </p>
            </div>
          ))}
        </div>
      </Container>
    </section>
  );
}
