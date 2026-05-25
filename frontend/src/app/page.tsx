import { Features } from '@/components/marketing/Features';
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
    <header className="border-b border-[#d9d5c8] bg-[#efece4]/80 backdrop-blur supports-[backdrop-filter]:bg-[#efece4]/70 sticky top-0 z-10">
      <Container className="flex h-16 items-center justify-between">
        <Link href="/" className="font-serif text-2xl">
          {appName}
        </Link>
        <nav className="flex items-center gap-6 text-sm">
          <Link
            href="/signin"
            className="text-[#3a342c] hover:text-[#1a1814]"
          >
            Sign in
          </Link>
          <Link
            href="/signup"
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
            scored breakdown in under a minute. Always free.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link
              href="/signup"
              className="inline-flex items-center justify-center rounded-full bg-[#efece4] px-6 py-3 text-sm font-medium text-[#1a1814] hover:bg-white"
            >
              Get my application graded
            </Link>
            <Link
              href="/signin"
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
