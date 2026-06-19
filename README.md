# CVPilot

CVPilot is a job-application intelligence platform that helps a candidate
understand how a CV, cover letter, portfolio, and job description fit together.
It combines a web app, backend services, and a GenLayer Intelligent Contract to
produce verifiable application analysis instead of a hidden black-box score.

## What the website does

The website is the user-facing dashboard for the application.

- Upload or submit a CV, cover letter, and job details.
- Generate application scores and breakdowns.
- Review skills gaps, salary guidance, interview prep, and strategy advice.
- Track historical evaluations by content hash.
- Inspect a verification page for a specific evaluation result.
- Manage account settings, applications, and admin views.

## What the contract does

The on-chain GenLayer contract is the trust layer behind the platform.

- Receives the application inputs from the backend.
- Runs nondeterministic LLM reasoning inside GenLayer.
- Uses validator consensus to finalize results.
- Normalizes JSON so the backend stores clean data.
- Caches results by content hash so the same submission returns the same
  canonical output.
- Exposes analysis methods for evaluation, skills gaps, salary, portfolio,
  career trajectory, cover letter review, job intelligence, ATS keywords,
  positioning, and application strategy.

The contract address currently wired into the app is:

`0x66caC4e3960efE68958F971C6287b8Cc8A1502d3`

## How the system fits together

1. The frontend collects user inputs and displays results.
2. The backend validates the request, stores metadata, and calls GenLayer.
3. The contract generates a result using nondeterministic prompts.
4. GenLayer validators compare the outputs and reach consensus.
5. The backend stores the finalized JSON response.
6. The frontend renders the result and verification view.

## Stack

- Frontend: Next.js + TypeScript + TailwindCSS
- Backend: FastAPI + SQLAlchemy + PostgreSQL
- Cache: Redis
- Queue: Celery
- LLM / consensus: GenLayer
- Blockchain: GenLayer Intelligent Contracts on StudioNet

## Key concepts

- Content hash: the stable key used to identify one application submission.
- Consensus result: the finalized output after validator agreement.
- Nondeterminism: LLM variability that is intentionally preserved inside the
  contract so GenLayer can resolve it through consensus.
- Verification: the public route and dashboard views that let users inspect a
  stored result by hash.

## Repository layout

- [`contracts/`](contracts) - GenLayer contract source and contract docs.
- [`frontend/`](frontend) - Next.js app.
- [`backend/`](backend) - API and database models.
- [`workers/`](workers) - asynchronous background jobs.
- [`services/`](services) - shared GenLayer and LLM client code.
- [`docs/`](docs) - deployment and architecture notes.
- [`scripts/`](scripts) - scaffolds and operational helpers.

## Deployment overview

- Frontend: Vercel
- API: Fly.io
- Worker: Fly.io
- Contract network: GenLayer StudioNet

## Environment variables

The live deployment depends on `GENLAYER_CONTRACT_ADDRESS` being set in the API
and worker environments, and `NEXT_PUBLIC_GENLAYER_CONTRACT_ADDRESS` being set
for the frontend where required by the UI.

## Local development

```bash
# 1. Python deps
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Copy and fill env
cp .env.example .env

# 3. Start services (Postgres + Redis via Docker or local)
docker compose up -d db redis   # if you have a compose file

# 4. Run migrations
alembic upgrade head

# 5. Start API
uvicorn backend.app.main:app --reload --port 8000

# 6. Start worker (separate terminal)
celery -A workers.celery_app worker --loglevel=info

# 7. Frontend (separate terminal)
cd frontend && npm install && npm run dev
```

## Deploy

### Backend (Fly.io)

```bash
# Update contract address secret on both apps
fly secrets set -a cvpilot-api \
  GENLAYER_CONTRACT_ADDRESS="0x66caC4e3960efE68958F971C6287b8Cc8A1502d3"

fly secrets set -a cvpilot-worker \
  GENLAYER_CONTRACT_ADDRESS="0x66caC4e3960efE68958F971C6287b8Cc8A1502d3"

# Deploy API and worker
fly deploy -c fly.api.toml
fly deploy -c fly.worker.toml
```

### Frontend (Vercel)

Push to `main` and Vercel auto-deploys, or run a manual production deploy from
the `frontend/` directory.

### Contract

The contract is deployed separately on GenLayer StudioNet. See
[`contracts/cvpilot/README.md`](contracts/cvpilot/README.md) for the contract
deployment workflow.

## Contract summary

CVPilotEvaluator is the on-chain contract that powers the platform’s verifiable
scoring and analysis:

- `evaluate_application` for the main application review
- `analyse_skills_gap` for skills matching and ramp-up planning
- `generate_interview_prep` for interview question generation
- `estimate_salary` for compensation guidance
- `assess_portfolio` for portfolio quality review
- `analyse_career_trajectory` for growth and seniority analysis
- `analyse_cover_letter` for cover letter review
- `analyse_job_posting` for job intelligence extraction
- `suggest_ats_keywords` for ATS keyword recommendations
- `rewrite_positioning` for executive summary rewrites
- `advise_application_strategy` for stage-aware next steps
- `run_full_suite` for the full evaluation bundle

## Why it exists

- It gives the app a transparent and auditable source of truth.
- It keeps the LLM output inside validator consensus instead of trusting a
  single model response.
- It lets the backend and dashboard present one canonical result per submission.

## More docs

- [`docs/runbooks/deploy.md`](docs/runbooks/deploy.md)
- [`contracts/cvpilot/README.md`](contracts/cvpilot/README.md)
- [`docs/architecture/`](docs/architecture)
