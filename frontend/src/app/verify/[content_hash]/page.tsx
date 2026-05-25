'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { EvaluationDisplay } from '@/components/verify/EvaluationDisplay';
import { Alert } from '@/components/ui/Alert';
import { Container } from '@/components/ui/Container';
import { ApiError, publicApi } from '@/lib/api';
import { appName } from '@/lib/brand';
import type { PublicEvaluation } from '@/lib/types';

export default function VerifyDetailPage() {
  const params = useParams<{ content_hash: string }>();
  const contentHash = (params?.content_hash || '').toLowerCase();

  const [data, setData] = useState<PublicEvaluation | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    setData(null); setNotFound(false); setError(null);
    (async () => {
      try {
        const ev = await publicApi.verify(contentHash);
        if (!alive) return;
        if (!ev.found) {
          setNotFound(true);
          setData(ev);
        } else {
          setData(ev);
        }
      } catch (e) {
        if (!alive) return;
        if (e instanceof ApiError && e.status === 404) {
          setNotFound(true);
          const body = (e.details && typeof e.details === 'object') ? (e.details as PublicEvaluation) : null;
          if (body) setData(body);
        } else {
          setError(e instanceof ApiError ? e.message : 'Could not load evaluation.');
        }
      }
    })();
    return () => { alive = false; };
  }, [contentHash]);

  return (
    <main className="min-h-screen">
      <header className="border-b border-[#d9d5c8] bg-[#efece4]/80 backdrop-blur sticky top-0 z-10">
        <Container className="flex h-16 items-center justify-between">
          <Link href="/" className="font-serif text-2xl">{appName}</Link>
          <Link href="/verify" className="text-sm text-[#3a342c] hover:text-[#1a1814]">
            Verify another
          </Link>
        </Container>
      </header>

      <Container className="py-14">
        <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">
          Public verification
        </p>
        <h1 className="mt-2 font-serif text-4xl sm:text-5xl">
          On-chain evaluation.
        </h1>
        <p className="mt-2 break-all font-mono text-xs text-[#3a342c]/80">
          {contentHash}
        </p>

        {error && (
          <div className="mt-8">
            <Alert tone="error">{error}</Alert>
          </div>
        )}

        {notFound && data && (
          <div className="mt-10 rounded-2xl border border-[#a35f1f]/40 bg-[#a35f1f]/10 p-6">
            <p className="text-xs uppercase tracking-[0.15em] text-[#a35f1f]">Not found</p>
            <h2 className="mt-2 font-serif text-2xl text-[#1a1814]">
              No evaluation is stored at this hash.
            </h2>
            <p className="mt-3 text-sm text-[#3a342c]">
              Either the hash is wrong, the evaluation has not finalised yet,
              or it lives on a different contract. The contract we checked is
              shown below.
            </p>
            <div className="mt-4 rounded-xl border border-[#a35f1f]/30 bg-white/60 p-3">
              <p className="text-[10px] uppercase tracking-[0.15em] text-[#a35f1f]">Contract</p>
              <p className="mt-1 break-all font-mono text-xs text-[#1a1814]">
                {data.contract_address}
              </p>
            </div>
            <div className="mt-5">
              <Link
                href="/verify"
                className="inline-flex items-center justify-center rounded-full border border-[#1a1814]/30 px-5 py-2 text-sm text-[#1a1814] hover:bg-[#1a1814]/5"
              >
                Try another hash
              </Link>
            </div>
          </div>
        )}

        {data && !notFound && (
          <div className="mt-10">
            <EvaluationDisplay ev={data} />
          </div>
        )}

        {!data && !error && !notFound && (
          <p className="mt-10 text-sm text-[#3a342c]">Reading the contract.</p>
        )}
      </Container>
    </main>
  );
}
