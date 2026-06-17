# CVPilot

AI-powered job application intelligence platform. CVPilot evaluates CVs, cover letters,
and job descriptions using GenLayer Intelligent Contracts + LLM consensus, returning
transparent, verifiable scoring and actionable career recommendations.

---

## Live deployments

| Service | URL |
|---------|-----|
| Frontend (Vercel) | https://cvpilot-theta.vercel.app |
| Backend API (Fly.io) | https://cvpilot-api.fly.dev |
| Worker (Fly.io) | https://cvpilot-worker.fly.dev |
| GenLayer StudioNet | https://studio.genlayer.com |

---

## Smart contract

| Property | Value |
|----------|-------|
| Contract | `CVPilotEvaluator` |
| Version | `1.0.1` |
| Network | GenLayer StudioNet |
| Address | `0x67FaB6A5551B3cc3544d85ab75aC35d888356770` |
| Explorer | https://studio.genlayer.com/explorer |
| Source | [`contracts/cvpilot/cvpilot_contract.py`](contracts/cvpilot/cvpilot_contract.py) |

### Contract capabilities

| # | Method | What it does |
|---|--------|-------------|
| 1 | `evaluate_application` | Full ATS + recruiter evaluation across 5 weighted dimensions |
| 2 | `analyse_skills_gap` | Candidate vs required skills with upskilling roadmap |
| 3 | `generate_interview_prep` | Behavioral, technical, situational & culture-fit questions |
| 4 | `estimate_salary` | Salary range + negotiation tips for target location |
| 5 | `assess_portfolio` | Live portfolio fetch + quality scoring |
| 6 | `analyse_career_trajectory` | Seniority, progression type, promotion velocity, risks |
| 7 | `analyse_cover_letter` | Tone, personalisation, storytelling, CTA strength |
| 8 | `analyse_job_posting` | Company stage, tech stack, red flags, culture signals |
| 9 | `suggest_ats_keywords` | Priority keyword injection map per CV section |
| 10 | `rewrite_positioning` | AI-drafted professional summary (tone-controlled) |
| 11 | `advise_application_strategy` | Stage-aware next-step playbook |
| 12 | `run_full_suite` | All core analyses in one transaction with caching |

All write methods use `gl.eq_principle.prompt_comparative` to reach GenLayer validator
consensus on non-deterministic LLM outputs before writing to chain state.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 · TypeScript · TailwindCSS |
| Backend | FastAPI · SQLAlchemy · Alembic |
| Database | PostgreSQL 15 |
| Cache / Queue | Redis 7 · Celery |
| AI / Blockchain | GenLayer Intelligent Contracts (StudioNet) |
| Frontend host | Vercel |
| Backend host | Fly.io (two apps: api + worker) |
| Email | Brevo (transactional) |

---

## Repository layout

```
CVPilot/
├── contracts/
│   └── cvpilot/
│       └── cvpilot_contract.py   # GenLayer Intelligent Contract (v1.0.0)
├── backend/
│   ├── app/
│   │   ├── core/         # Config, startup guard, security
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   ├── routes/       # FastAPI routers
│   │   └── db/           # Alembic migrations
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js App Router pages
│   │   ├── components/   # React components
│   │   └── lib/          # API client, types, utils
│   └── vercel.json       # Vercel config + API rewrites
├── workers/
│   └── tasks/            # Celery tasks (evaluation pipeline)
├── services/
│   └── llm/
│       └── genlayer.py   # GenLayer SDK client wrapper
├── docs/
│   ├── architecture/
│   ├── contracts/
│   └── runbooks/
├── fly.api.toml          # Fly.io API app config
├── fly.worker.toml       # Fly.io worker app config
├── Procfile              # Process definitions
└── pyproject.toml        # Python project config
```

---

## Environment variables

### Backend / Worker

Copy `.env.example` to `.env` and fill in the values.

| Variable | Description |
|----------|-------------|
| `APP_SECRET_KEY` | 64-char random secret (`openssl rand -base64 48`) |
| `DATABASE_URL` | PostgreSQL DSN (`postgresql+psycopg://...`) |
| `REDIS_URL` | Redis DSN |
| `GENLAYER_CONTRACT_ADDRESS` | `0x67FaB6A5551B3cc3544d85ab75aC35d888356770` |
| `GENLAYER_STUDIONET_RPC` | `https://studio.genlayer.com/api` |
| `GENLAYER_ACCOUNT_PRIVATE_KEY` | Funded StudioNet wallet private key |
| `APP_FRONTEND_ORIGIN` | CORS origin (`https://cvpilot-theta.vercel.app`) |
| `BREVO_API_KEY` | Brevo transactional email key |
| `BREVO_SENDER_EMAIL` | Verified sender address |

### Frontend

Copy `frontend/.env.production.example` and set as Vercel environment variables.

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_BASE_URL` | `/api` (proxied via Vercel rewrites) |
| `NEXT_PUBLIC_GENLAYER_CONTRACT_ADDRESS` | `0x67FaB6A5551B3cc3544d85ab75aC35d888356770` |
| `NEXT_PUBLIC_GENLAYER_EXPLORER` | `https://studio.genlayer.com/explorer` |
| `NEXT_PUBLIC_SITE_ORIGIN` | `https://cvpilot-theta.vercel.app` |

---

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

---

## Deploy

### Backend (Fly.io)

```bash
# Update contract address secret on both apps
fly secrets set -a cvpilot-api \
  GENLAYER_CONTRACT_ADDRESS="0x67FaB6A5551B3cc3544d85ab75aC35d888356770"

fly secrets set -a cvpilot-worker \
  GENLAYER_CONTRACT_ADDRESS="0x67FaB6A5551B3cc3544d85ab75aC35d888356770"

# Deploy
fly deploy -c fly.api.toml
fly deploy -c fly.worker.toml
```

### Frontend (Vercel)

Push to `main` — Vercel auto-deploys on every push.
Ensure `NEXT_PUBLIC_GENLAYER_CONTRACT_ADDRESS` is set to
`0x67FaB6A5551B3cc3544d85ab75aC35d888356770` in the Vercel project settings.

Full deploy runbook: [`docs/runbooks/deploy.md`](docs/runbooks/deploy.md)

---

## Verification

Every evaluation result is anchored on-chain. The public
`/verify/<content_hash>` route shows the full result, contract address,
and transaction hash — verifiable by anyone without an account.

Contract address: `0x67FaB6A5551B3cc3544d85ab75aC35d888356770`
Explorer: https://studio.genlayer.com/explorer
