import Link from 'next/link';
import { Container } from '@/components/ui/Container';
import { appName } from '@/lib/brand';

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <main className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-10 border-b border-[#d9d5c8] bg-[#efece4]/80 backdrop-blur">
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
      <div className="flex flex-1 items-start justify-center px-6 py-16 sm:py-24">
        {children}
      </div>
    </main>
  );
}
