"""
Phase 6A fix:
  1. Detect Tailwind major version in frontend/package.json.
  2. Write globals.css with the matching directive style
     (v4: @import "tailwindcss";   v3: @tailwind base/components/utilities;).
  3. Rewrite copy across layout / page / Hero / Features removing every
     dash character ("-", "\u2013", "\u2014") from user-visible text.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path("/Users/macbook/CVPilot")
FRONTEND = ROOT / "frontend"
PKG = FRONTEND / "package.json"


def detect_tailwind_major() -> int:
    data = json.loads(PKG.read_text(encoding="utf-8"))
    dep = (
        data.get("devDependencies", {}).get("tailwindcss")
        or data.get("dependencies", {}).get("tailwindcss")
        or ""
    )
    if not dep:
        return 4
    digits = re.search(r"(\d+)", dep)
    return int(digits.group(1)) if digits else 4


tw_major = detect_tailwind_major()
print(f"Detected Tailwind major: {tw_major}")


# ---------------- globals.css ----------------
if tw_major >= 4:
    GLOBALS_CSS = '''/*
  CVPilot global styles. Tailwind v4.
  Brand color: #efece4
*/

@import "tailwindcss";

@theme {
  --color-brand: #efece4;
  --color-brand-soft: #f6f4ee;
  --color-ink: #1a1814;
  --color-ink-soft: #3a342c;
  --color-accent: #2b4f3a;
  --color-accent-soft: #cfd9d0;
  --color-line: #d9d5c8;
  --font-display: ui-serif, Georgia, "Times New Roman", serif;
}

:root {
  --brand: #efece4;
  --brand-soft: #f6f4ee;
  --ink: #1a1814;
  --ink-soft: #3a342c;
  --accent: #2b4f3a;
  --accent-soft: #cfd9d0;
  --line: #d9d5c8;
}

html,
body {
  background-color: var(--brand);
  color: var(--ink);
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}

::selection {
  background: var(--accent);
  color: var(--brand);
}

a:focus-visible,
button:focus-visible,
input:focus-visible,
textarea:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
  border-radius: 4px;
}

.bg_paper {
  background-color: var(--brand);
  background-image: radial-gradient(
    circle at 1px 1px,
    rgba(0, 0, 0, 0.035) 1px,
    transparent 0
  );
  background-size: 18px 18px;
}
'''
else:
    GLOBALS_CSS = '''/*
  CVPilot global styles. Tailwind v3.
  Brand color: #efece4
*/

@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --brand: #efece4;
  --brand-soft: #f6f4ee;
  --ink: #1a1814;
  --ink-soft: #3a342c;
  --accent: #2b4f3a;
  --accent-soft: #cfd9d0;
  --line: #d9d5c8;
}

html,
body {
  background-color: var(--brand);
  color: var(--ink);
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}

::selection {
  background: var(--accent);
  color: var(--brand);
}

a:focus-visible,
button:focus-visible,
input:focus-visible,
textarea:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
  border-radius: 4px;
}

.bg_paper {
  background-color: var(--brand);
  background-image: radial-gradient(
    circle at 1px 1px,
    rgba(0, 0, 0, 0.035) 1px,
    transparent 0
  );
  background-size: 18px 18px;
}
'''


# ---------------- layout.tsx ----------------
LAYOUT_TSX = '''import type { Metadata } from 'next';
import { Inter, Instrument_Serif } from 'next/font/google';
import { appName } from '@/lib/brand';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
});

const serif = Instrument_Serif({
  weight: '400',
  subsets: ['latin'],
  variable: '--font-serif',
  display: 'swap',
});

export const metadata: Metadata = {
  title: `${appName}. AI Job Application Intelligence.`,
  description:
    'CVPilot evaluates your CV, cover letter, and job match with verifiable AI scoring on GenLayer StudioNet. Get the truth before you apply.',
  applicationName: appName,
  themeColor: '#efece4',
  openGraph: {
    title: `${appName}. AI Job Application Intelligence.`,
    description:
      'Verifiable CV scoring, cover letter analysis and recommendations powered by GenLayer Intelligent Contracts.',
    type: 'website',
  },
  icons: { icon: '/favicon.ico' },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${serif.variable}`}>
      <body className="min-h-screen bg-[#efece4] text-[#1a1814] antialiased">
        {children}
      </body>
    </html>
  );
}
'''


# ---------------- Hero.tsx ----------------
HERO_TSX = '''import { Button } from '@/components/ui/Button';
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
              <Button href="/sign-up">Get my application graded</Button>
              <Button href="/sign-in" variant="ghost">
                I already have an account
              </Button>
            </div>
            <p className="mt-5 text-xs text-[#3a342c]/70">
              No credit card. Free tier covers your first 3 evaluations.
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
            0xc9A5\u20268A9e
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
'''


# ---------------- Features.tsx ----------------
FEATURES_TSX = '''import { Container } from '@/components/ui/Container';

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
    body: 'When you upgrade, the same engine that scored you rewrites your CV and drafts an interview grade cover letter, tuned to the posting.',
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
'''


# ---------------- page.tsx ----------------
PAGE_TSX = '''import { Features } from '@/components/marketing/Features';
import { Footer } from '@/components/marketing/Footer';
import { Hero } from '@/components/marketing/Hero';
import { Container } from '@/components/ui/Container';
import { appName } from '@/lib/brand';
import Link from 'next/link';

export default function HomePage() {
  return (
    <main>
      <TopBar />
      <Hero />
      <Features />
      <ClosingCTA />
      <Footer />
    </main>
  );
}

function TopBar() {
  return (
    <header className="border_b border-[#d9d5c8] bg-[#efece4]/80 backdrop-blur supports-[backdrop-filter]:bg-[#efece4]/70 sticky top-0 z-10">
      <Container className="flex h-16 items-center justify-between">
        <Link href="/" className="font-serif text-2xl">
          {appName}
        </Link>
        <nav className="flex items-center gap-6 text-sm">
          <Link
            href="/sign-in"
            className="text-[#3a342c] hover:text-[#1a1814]"
          >
            Sign in
          </Link>
          <Link
            href="/sign-up"
            className="rounded-full bg-[#1a1814] px-4 py-2 text-[#efece4] hover:bg-[#3a342c]"
          >
            Get started
          </Link>
        </nav>
      </Container>
    </header>
  );
}

function ClosingCTA() {
  return (
    <section className="py-24">
      <Container>
        <div className="rounded-3xl border border-[#1a1814]/15 bg-[#1a1814] px-10 py-16 text-center text-[#efece4] sm:px-16">
          <p className="text-xs uppercase tracking-[0.2em] text-[#efece4]/60">
            Stop guessing
          </p>
          <h2 className="mt-4 font-serif text-4xl leading-tight sm:text-5xl">
            See exactly where your application falls short.
          </h2>
          <p className="mx-auto mt-5 max-w-2xl text-sm text-[#efece4]/80 sm:text-base">
            Upload your CV, drop in the job URL, and we deliver a consensus
            scored breakdown in under a minute. Free for your first three
            evaluations.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link
              href="/sign-up"
              className="inline-flex items-center justify-center rounded-full bg-[#efece4] px-6 py-3 text-sm font-medium text-[#1a1814] hover:bg-white"
            >
              Get my application graded
            </Link>
            <Link
              href="/sign-in"
              className="inline-flex items-center justify-center rounded-full border border-[#efece4]/30 px-6 py-3 text-sm font-medium text-[#efece4] hover:bg-[#efece4]/10"
            >
              Sign in
            </Link>
          </div>
        </div>
      </Container>
    </section>
  );
}
'''


# ---------------- Footer.tsx ----------------
FOOTER_TSX = '''import { Container } from '@/components/ui/Container';
import { appName } from '@/lib/brand';

export function Footer() {
  return (
    <footer className="py-14 text-sm text-[#3a342c]">
      <Container className="flex flex-col items-start gap-6 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="font-serif text-2xl text-[#1a1814]">{appName}</p>
          <p className="mt-1 text-xs text-[#3a342c]/70">
            AI Job Application Intelligence \u00b7 powered by GenLayer
            Intelligent Contracts
          </p>
        </div>
        <div className="flex flex-wrap gap-6 text-xs uppercase tracking-[0.15em]">
          <a href="/sign-in" className="hover:text-[#1a1814]">
            Sign in
          </a>
          <a href="/sign-up" className="hover:text-[#1a1814]">
            Sign up
          </a>
          <a
            href="https://docs.genlayer.com/"
            target="_blank"
            rel="noreferrer noopener"
            className="hover:text-[#1a1814]"
          >
            GenLayer
          </a>
        </div>
      </Container>
    </footer>
  );
}
'''


FILES = {
    "frontend/src/app/globals.css": GLOBALS_CSS,
    "frontend/src/app/layout.tsx": LAYOUT_TSX,
    "frontend/src/app/page.tsx": PAGE_TSX,
    "frontend/src/components/marketing/Hero.tsx": HERO_TSX,
    "frontend/src/components/marketing/Features.tsx": FEATURES_TSX,
    "frontend/src/components/marketing/Footer.tsx": FOOTER_TSX,
}


def write(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  wrote {rel}")


for rel, content in FILES.items():
    write(rel, content)

print("\nPhase 6A fix complete.")
