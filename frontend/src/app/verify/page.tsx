'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormEvent, useState } from 'react';
import { Container } from '@/components/ui/Container';
import { Field } from '@/components/ui/Field';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { appName } from '@/lib/brand';

export default function VerifyLandingPage() {
  const router = useRouter();
  const [hash, setHash] = useState('');
  const [error, setError] = useState<string | null>(null);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const cleaned = hash.trim().toLowerCase();
    if (!/^[0-9a-f]{64}$/.test(cleaned)) {
      setError('That does not look like a 64 character content hash.');
      return;
    }
    router.push(`/verify/${cleaned}`);
  }

  return (
    <main className="min-h-screen">
      <header className="border-b border-[#d9d5c8] bg-[#efece4]/80 backdrop-blur">
        <Container className="flex h-16 items-center justify-between">
          <Link href="/" className="font-serif text-2xl">{appName}</Link>
          <Link href="/" className="text-sm text-[#3a342c] hover:text-[#1a1814]">
            Back to home
          </Link>
        </Container>
      </header>
      <Container className="py-24">
        <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">
          Public verification
        </p>
        <h1 className="mt-3 font-serif text-5xl sm:text-6xl">
          Read any CVPilot evaluation,
          <br />
          <span className="italic text-[#2b4f3a]">straight from the chain.</span>
        </h1>
        <p className="mt-5 max-w-2xl text-[#3a342c]">
          Paste a content hash below. We read the verified evaluation directly
          from the GenLayer Intelligent Contract on StudioNet. No signup. No
          intermediary.
        </p>

        <form onSubmit={onSubmit} className="mt-10 flex max-w-2xl flex-col gap-4">
          <Field label="Content hash" hint="A 64 character hexadecimal SHA-256.">
            <Input
              type="text"
              value={hash}
              onChange={(e) => { setHash(e.target.value); setError(null); }}
              placeholder="e.g. ac4a6e6855d57a17730ea46eb5e15d2a6a4e374ae38722a4dcaaeddc51df1ca4"
              className="font-mono text-sm"
              autoComplete="off"
              spellCheck={false}
            />
          </Field>
          {error && (
            <p className="rounded-2xl border border-[#9b2226]/30 bg-[#9b2226]/10 px-4 py-3 text-sm text-[#9b2226]">
              {error}
            </p>
          )}
          <div>
            <Button type="submit">Verify evaluation</Button>
          </div>
        </form>
      </Container>
    </main>
  );
}
