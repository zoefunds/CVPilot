# CVPilot Intelligent Contract

GenLayer Intelligent Contract powering verifiable, consensus-driven evaluation
of job applications (CV + cover letter + job description + career intelligence).

## Deployed contract

| Property | Value |
|----------|-------|
| Contract | `CVPilotEvaluator` |
| Version | `1.0.1` |
| Network | GenLayer StudioNet |
| Address | `0x67FaB6A5551B3cc3544d85ab75aC35d888356770` |
| Explorer | https://studio.genlayer.com/explorer |

## Source

`cvpilot_contract.py` — 1,298 lines, 12 public write methods, full suite.

## Capabilities

| Method | Description |
|--------|-------------|
| `evaluate_application` | Full ATS + recruiter scoring (5 weighted dimensions) |
| `analyse_skills_gap` | Required vs candidate skills + upskilling roadmap |
| `generate_interview_prep` | Behavioral, technical, situational, culture-fit Qs |
| `estimate_salary` | Range + negotiation tips for target location |
| `assess_portfolio` | Live portfolio fetch + quality scoring |
| `analyse_career_trajectory` | Seniority, progression, velocity, growth potential |
| `analyse_cover_letter` | Tone, personalisation, storytelling, CTA strength |
| `analyse_job_posting` | Company stage, tech stack, red flags, culture signals |
| `suggest_ats_keywords` | Priority keyword injection map per CV section |
| `rewrite_positioning` | AI-drafted professional summary (tone-controlled) |
| `advise_application_strategy` | Stage-aware next-step playbook |
| `run_full_suite` | All core analyses in a single transaction with caching |

## Redeploy to StudioNet

If you need to redeploy (e.g. after contract changes):

1. Open **https://studio.genlayer.com** and connect your wallet (StudioNet).
2. Create a new project and paste the contents of `cvpilot_contract.py`.
3. Click **Compile** — no errors expected.
4. Click **Deploy** — constructor takes no arguments.
5. Copy the new contract address.
6. Update `GENLAYER_CONTRACT_ADDRESS` in:
   - `.env`
   - `.env.production.example`
   - `frontend/.env.production.example`
   - `docs/runbooks/deploy.md`
   - This README.
7. Update Fly.io secrets:
   ```bash
   fly secrets set -a cvpilot-api GENLAYER_CONTRACT_ADDRESS="0x..."
   fly secrets set -a cvpilot-worker GENLAYER_CONTRACT_ADDRESS="0x..."
   ```
8. Redeploy backend:
   ```bash
   fly deploy -c fly.api.toml
   fly deploy -c fly.worker.toml
   ```
9. Redeploy frontend: push to `main` (Vercel auto-deploys).

## Design principles

- **Idempotency** — same inputs hash to the same cache key; re-evaluating
  returns the stored verdict with zero extra LLM consensus calls.
- **Schema safety** — the contract normalises LLM output before storage;
  the backend never sees malformed JSON.
- **Validator consensus** — every write method uses `gl.eq_principle.prompt_comparative`
  so multiple validators must agree (within tolerance) before state is written.
  That is CVPilot's trust and verifiability layer.
- **On-chain auditability** — results are keyed by `content_hash` (derived
  from the application inputs). Anyone can replay the lookup and verify the verdict.
- **Schema compatibility** — no `from __future__ import annotations`; all
  `@gl.public.*` parameters use primitive types that the GenLayer schema
  generator can resolve at class-definition time.
