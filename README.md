# CVPilot

CVPilot is a verifiable AI platform for job applications. It runs your CV, cover letter, and a job posting through a 19-module GenLayer Intelligent Contract — every score is reached by multi-validator consensus on GenLayer StudioNet, so the result is auditable onchain rather than a hidden black-box number.

Live: **https://cvpilot-theta.vercel.app**

---

## How it works for a user

### Step 1 — Create an account
Sign up at `/signup`. After confirming your email, you land on the dashboard.

### Step 2 — Fund your wallet
Every evaluation runs onchain and pays validators in GEN test tokens. Go to **Settings → Wallet**, copy your wallet address, and paste it into the GenLayer StudioNet faucet to receive tokens. You need at least ~0.005 GEN per full evaluation. The faucet provides test tokens for free.

### Step 3 — Start a new evaluation
Click **New evaluation** on the dashboard. Fill in:

| Field | Required | Notes |
|---|---|---|
| Job URL | Yes | Jobberman, LinkedIn, Indeed, Greenhouse, Lever, most public boards |
| CV | Yes | PDF, DOCX, or TXT |
| Cover letter | No | Unlocks cover letter scores and personalisation analysis |
| LinkedIn URL | No | Used for reputation and LinkedIn optimisation modules |
| Portfolio URL | No | Used for portfolio assessment module |

Click **Preview** to auto-fetch the job title and description before submitting.

### Step 4 — Wait ~60 seconds
The backend dispatches `run_full_suite` to the GenLayer contract. Five validators run LLM inference independently and reach consensus. Results are stored onchain and fetched back to the dashboard.

### Step 5 — Read your 19-module report
Your evaluation detail page shows:

| Module | What it tells you |
|---|---|
| Overall score | Weighted composite of the five primary scores (0–100) |
| CV score | Clarity, relevance, and presentation of your CV |
| Cover letter score | Tone, personalisation, storytelling, and CTA strength |
| Job match | How well your experience maps to this specific role |
| ATS score | Keyword density and ATS-friendliness |
| Competitiveness | Where you stand against typical applicants |
| Skills gap | Missing vs. present skills with upskilling roadmap |
| Career trajectory | Seniority, progression velocity, highlights, risks |
| Salary estimate | Market range low / mid / high with negotiation tips |
| Interview prep | Behavioural, technical, situational, and culture-fit questions |
| Portfolio assessment | Project quality, diversity, and presentation scores |
| ATS keyword booster | Priority keywords to add to each CV section |
| Positioning rewrite | Revised executive summary for this role |
| Application strategy | Stage-aware next steps (24 h, this week, networking) |
| **Readiness gate** | **GO / NO-GO / GO WITH CAVEATS** verdict with blockers |
| **Bias detection** | Exclusionary language, gendered terms, age signals in the JD |
| **LinkedIn optimisation** | Headline options, About section draft, skills to add |
| **Cold outreach** | Subject lines, email draft, LinkedIn message |
| **Bullet rewriter** | Before/after rewrites of your 5 weakest CV bullets |

### Step 6 — Share or verify
Every completed evaluation has a unique verification link (`/verify/<content_hash>`). Share it with recruiters or employers — they can confirm the score is genuine without trusting CVPilot.

---

## Architecture

```
User browser
    ↓
Next.js (Vercel)
    ↓
FastAPI backend (Fly.io — cvpilot-api)
    ↓ enqueues job
Celery worker (Fly.io — cvpilot-worker)
    ↓ calls GenLayer SDK
GenLayer StudioNet
    ↓ 5 validators run LLM + reach consensus
CVPilotEvaluator contract (cvpilot_contract.py)
    ↓ stores result onchain by content hash
Worker polls get_evaluation → stores in Postgres
    ↓
Frontend polls API → renders report
```

### Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16 + TypeScript + TailwindCSS |
| Backend | FastAPI + SQLAlchemy + PostgreSQL |
| Queue | Celery + Redis |
| LLM / consensus | GenLayer StudioNet |
| Contract | Python Intelligent Contract (CVPilotEvaluator v2.1.0) |

---

## Contract

The GenLayer contract is the trust core of the platform.

**Current address:** `0x66caC4e3960efE68958F971C6287b8Cc8A1502d3`

**Version:** 2.1.0 — 19 modules, 30 LLM calls, all using `prompt_non_comparative`.

Key design decisions:
- All LLM calls use `gl.eq_principle.prompt_non_comparative(fn, task=..., criteria=...)` so validators verify execution trace rather than comparing stochastic LLM outputs — eliminating consensus failures.
- `web_fetch_on = False` by default to prevent per-validator page divergence.
- `_COMPACT` rules appended to every prompt cap string length (40 words) and array size (5 items) to reduce output variance.
- Results cached by `content_hash` (SHA-256 of inputs) — same submission always returns the same canonical result.

Public write methods:

```
evaluate_application       analyse_skills_gap        generate_interview_prep
estimate_salary            assess_portfolio           analyse_career_trajectory
analyse_cover_letter       analyse_job_posting        suggest_ats_keywords
rewrite_positioning        advise_application_strategy
detect_job_bias            optimise_linkedin          compute_reputation
draft_outreach             gate_readiness             rank_job_fit
rewrite_weak_bullets       run_full_suite             run_extended_suite
```

See [`contracts/cvpilot/README.md`](contracts/cvpilot/README.md) for the full ABI.

---

## Repository layout

```
contracts/cvpilot/       GenLayer contract source (cvpilot_contract.py)
frontend/                Next.js app
  src/app/               Pages (dashboard, auth, verify, admin)
  src/components/        UI components and module panels
  src/lib/               API client and TypeScript types
backend/                 FastAPI app, models, routes
workers/                 Celery task definitions
services/llm/            GenLayer SDK wrapper (genlayer.py)
docs/                    Architecture notes and runbooks
scripts/                 Operational helpers
```

---

## Local development

```bash
# 1. Python deps
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Fill env
cp .env.example .env   # then edit with your values

# 3. Start Postgres + Redis
docker compose up -d db redis

# 4. Run migrations
alembic upgrade head

# 5. API
uvicorn backend.app.main:app --reload --port 8000

# 6. Worker (separate terminal)
celery -A workers.celery_app worker --loglevel=info

# 7. Frontend (separate terminal)
cd frontend && npm install && npm run dev
```

Open `http://localhost:3000`.

---

## Deployment

### Wire a new contract address

```bash
# 1. Update all config files
OLD="0x<old>" NEW="0x<new>"
for f in .env .env.production.example frontend/.env.production.example \
          README.md contracts/cvpilot/README.md docs/runbooks/deploy.md \
          contracts/cvpilot/cvpilot_contract.py; do
  sed -i '' "s/$OLD/$NEW/g" "$f"
done

# 2. Commit + push
git add -A && git commit -m "Wire contract address $NEW" && git push

# 3. Update Fly secrets (in parallel)
fly secrets set GENLAYER_CONTRACT_ADDRESS="$NEW" --app cvpilot-api &
fly secrets set GENLAYER_CONTRACT_ADDRESS="$NEW" --app cvpilot-worker &
wait

# 4. Deploy frontend
cd frontend && vercel --prod
```

### Backend — Fly.io

```bash
fly deploy -c fly.api.toml      # API
fly deploy -c fly.worker.toml   # Worker
```

### Frontend — Vercel

Push to `main` — Vercel auto-deploys. Or run `cd frontend && vercel --prod`.

### Contract

Deploy the contract on GenLayer StudioNet via the GenLayer Studio or CLI, then wire the new address as above. See [`contracts/cvpilot/README.md`](contracts/cvpilot/README.md).

---

## Key concepts

**Content hash** — SHA-256 of the evaluation inputs (CV text, cover letter, job text, URLs). Used as the onchain cache key. Same inputs → same hash → contract returns cached result instantly.

**Consensus result** — The output agreed on by ≥3 of 5 validators running the same contract method independently on GenLayer StudioNet.

**`prompt_non_comparative`** — The GenLayer SDK's equivalence primitive for non-deterministic LLM calls. `fn()` returns the raw input data; `task=` provides the instructions; validators verify the execution trace rather than comparing LLM outputs directly. This is why CVPilot never gets stuck in "undetermined" consensus.

**Verification link** — `/verify/<content_hash>` is a public, shareable page that reads the stored result directly from the contract. No login required.

---

## Environment variables

| Variable | Where | Purpose |
|---|---|---|
| `GENLAYER_CONTRACT_ADDRESS` | API + Worker (Fly secrets) | Contract address to call |
| `NEXT_PUBLIC_GENLAYER_CONTRACT_ADDRESS` | Frontend (Vercel env) | Displayed in verification UI |
| `DATABASE_URL` | API + Worker | Postgres connection string |
| `REDIS_URL` | API + Worker | Celery broker + result backend |
| `SECRET_KEY` | API | JWT signing key |

---

## More docs

- [`docs/runbooks/deploy.md`](docs/runbooks/deploy.md) — step-by-step deployment playbook
- [`contracts/cvpilot/README.md`](contracts/cvpilot/README.md) — contract ABI, version history, deployment notes
- [`docs/architecture/`](docs/architecture) — system diagrams
