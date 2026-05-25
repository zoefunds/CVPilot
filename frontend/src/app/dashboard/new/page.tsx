'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormEvent, useState } from 'react';
import { Alert } from '@/components/ui/Alert';
import { Button } from '@/components/ui/Button';
import { Container } from '@/components/ui/Container';
import { Dropzone } from '@/components/ui/Dropzone';
import { Field } from '@/components/ui/Field';
import { Input } from '@/components/ui/Input';
import { ApiError, applicationsApi } from '@/lib/api';

interface InsufficientBalanceDetails {
  wallet_address: string;
  balance_wei: number;
  required_wei: number;
}

function isBalanceDetails(d: unknown): d is InsufficientBalanceDetails {
  return typeof d === 'object' && d !== null
    && 'wallet_address' in d && 'balance_wei' in d && 'required_wei' in d;
}

function weiToGen(wei: number): string {
  if (!wei) return '0';
  return (wei / 1e18).toFixed(4);
}

export default function NewApplicationPage() {
  const router = useRouter();
  const [jobUrl, setJobUrl] = useState('');
  const [linkedinUrl, setLinkedinUrl] = useState('');
  const [portfolioUrl, setPortfolioUrl] = useState('');
  const [cv, setCv] = useState<File | null>(null);
  const [coverLetter, setCoverLetter] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [insufficient, setInsufficient] = useState<InsufficientBalanceDetails | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setInsufficient(null);

    if (!cv) { setError('Please attach your CV.'); return; }
    if (!coverLetter) { setError('Please attach your cover letter.'); return; }
    if (!/^https?:\/\//i.test(jobUrl)) {
      setError('Job URL must start with http or https.');
      return;
    }

    setLoading(true);
    try {
      const app = await applicationsApi.create({
        job_url: jobUrl,
        linkedin_url: linkedinUrl || undefined,
        portfolio_url: portfolioUrl || undefined,
        cv,
        cover_letter: coverLetter,
      });
      router.push(`/dashboard/applications/${app.id}`);
    } catch (e) {
      if (e instanceof ApiError && e.status === 402 && isBalanceDetails(e.details)) {
        setInsufficient(e.details);
      } else if (e instanceof ApiError) {
        setError(e.message);
      } else {
        setError('Submission failed. Try again.');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <Container className="py-16">
      <div className="max-w-3xl">
        <p className="text-xs uppercase tracking-[0.18em] text-[#3a342c]">New evaluation</p>
        <h1 className="mt-3 font-serif text-5xl">Grade your application.</h1>
        <p className="mt-4 max-w-2xl text-[#3a342c]">
          We parse your CV and cover letter, fetch the job posting, and run
          the on-chain evaluation. You will see live status while we work.
        </p>

        {insufficient && (
          <div className="mt-8 rounded-2xl border border-[#a35f1f]/40 bg-[#a35f1f]/10 p-6">
            <p className="text-xs uppercase tracking-[0.15em] text-[#a35f1f]">
              Top up your wallet
            </p>
            <h2 className="mt-2 font-serif text-2xl text-[#1a1814]">
              Not enough GEN to run this evaluation.
            </h2>
            <p className="mt-3 text-sm text-[#3a342c]">
              Validators need to be paid in GEN to run the on-chain LLM.
              Fund your wallet via the StudioNet faucet, then submit again.
            </p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-[#a35f1f]/30 bg-white/60 p-3">
                <p className="text-[10px] uppercase tracking-[0.15em] text-[#a35f1f]">Your wallet</p>
                <p className="mt-1 break-all font-mono text-xs text-[#1a1814]">
                  {insufficient.wallet_address}
                </p>
              </div>
              <div className="rounded-xl border border-[#a35f1f]/30 bg-white/60 p-3">
                <p className="text-[10px] uppercase tracking-[0.15em] text-[#a35f1f]">Balance / needed</p>
                <p className="mt-1 text-sm text-[#1a1814]">
                  {weiToGen(insufficient.balance_wei)} GEN / {weiToGen(insufficient.required_wei)} GEN
                </p>
              </div>
            </div>
            <div className="mt-5 flex flex-wrap gap-3 text-sm">
              <Link
                href="/dashboard/settings"
                className="inline-flex items-center justify-center rounded-full bg-[#1a1814] px-5 py-2 text-[#efece4] hover:bg-[#3a342c]"
              >
                Open my wallet
              </Link>
              <a
                href="https://studio.genlayer.com/"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center rounded-full border border-[#1a1814]/30 px-5 py-2 text-[#1a1814] hover:bg-[#1a1814]/5"
              >
                Open StudioNet
              </a>
            </div>
          </div>
        )}

        <form onSubmit={onSubmit} className="mt-10 flex flex-col gap-6">
          {error && <Alert tone="error">{error}</Alert>}

          <Field label="Job URL" hint="Paste the link to the job posting.">
            <Input
              type="url"
              value={jobUrl}
              onChange={(e) => setJobUrl(e.target.value)}
              required
              disabled={loading}
              placeholder="https://example.com/jobs/senior-engineer"
            />
          </Field>

          <div className="grid gap-5 sm:grid-cols-2">
            <Field label="LinkedIn" hint="Optional. Recruiters weight it.">
              <Input
                type="url"
                value={linkedinUrl}
                onChange={(e) => setLinkedinUrl(e.target.value)}
                disabled={loading}
                placeholder="https://www.linkedin.com/in/you/"
              />
            </Field>
            <Field label="Portfolio" hint="Optional. Useful for design or engineering roles.">
              <Input
                type="url"
                value={portfolioUrl}
                onChange={(e) => setPortfolioUrl(e.target.value)}
                disabled={loading}
                placeholder="https://your.portfolio.site"
              />
            </Field>
          </div>

          <div className="grid gap-5 sm:grid-cols-2">
            <Dropzone label="CV" file={cv} onFile={setCv} disabled={loading} />
            <Dropzone label="Cover letter" file={coverLetter} onFile={setCoverLetter} disabled={loading} />
          </div>

          <div>
            <Button type="submit" disabled={loading}>
              {loading ? 'Submitting...' : 'Run evaluation'}
            </Button>
          </div>
        </form>
      </div>
    </Container>
  );
}
