import Link from 'next/link';
import { Container } from '@/components/ui/Container';
import { appName } from '@/lib/brand';

export default function NotFound() {
  return (
    <main className="min-h-screen">
      <header className="border-b border-[#d9d5c8]">
        <Container className="flex h-16 items-center justify-between">
          <Link href="/" className="font-serif text-2xl">
            {appName}
          </Link>
          <Link
            href="/"
            className="text-sm text-[#3a342c] hover:text-[#1a1814]"
          >
            Back to home
          </Link>
        </Container>
      </header>
      <Container className="py-24 sm:py-32">
        <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">
          404
        </p>
        <h1 className="mt-3 font-serif text-6xl sm:text-7xl">
          We could not find that page.
        </h1>
        <p className="mt-4 max-w-xl text-[#3a342c]">
          The link may be old, or the page may have moved. Head back to your
          dashboard and try again.
        </p>
        <div className="mt-10 flex flex-wrap gap-3">
          <Link
            href="/dashboard"
            className="inline-flex items-center justify-center rounded-full bg-[#1a1814] px-6 py-3 text-sm font-medium text-[#efece4] hover:bg-[#3a342c]"
          >
            Go to dashboard
          </Link>
          <Link
            href="/"
            className="inline-flex items-center justify-center rounded-full border border-[#1a1814]/30 px-6 py-3 text-sm font-medium text-[#1a1814] hover:bg-[#1a1814]/5"
          >
            Back to home
          </Link>
        </div>
      </Container>
    </main>
  );
}
