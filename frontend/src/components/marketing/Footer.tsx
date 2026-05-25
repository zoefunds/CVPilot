import { Container } from '@/components/ui/Container';
import { appName } from '@/lib/brand';

export function Footer() {
  return (
    <footer className="py-14 text-sm text-[#3a342c]">
      <Container className="flex flex-col items-start gap-6 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="font-serif text-2xl text-[#1a1814]">{appName}</p>
          <p className="mt-1 text-xs text-[#3a342c]/70">
            AI Job Application Intelligence · powered by GenLayer
            Intelligent Contracts
          </p>
        </div>
        <div className="flex flex-wrap gap-6 text-xs uppercase tracking-[0.15em]">
          <a href="/signin" className="hover:text-[#1a1814]">
            Sign in
          </a>
          <a href="/signup" className="hover:text-[#1a1814]">
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
