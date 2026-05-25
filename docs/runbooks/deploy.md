# Deploy Runbook

Two supported targets: Fly.io (recommended, two apps) and Render
(single repo, multi-service). Both build from buildpacks. No Docker.

## Prerequisites

- Postgres 15 instance with TLS (Fly Postgres, Neon, Supabase, or RDS).
- Redis 7 instance reachable from both API and worker.
- A funded GenLayer Studio wallet for the contract owner (one-time).
- Frontend hosted separately (Vercel recommended).

## First-time setup (Fly.io)

1. Create the two apps:

       fly apps create cvpilot-api
       fly apps create cvpilot-worker

2. Provision Postgres and Redis (Fly or external). Capture the DSNs.

3. Set secrets on both apps. The same values go on api and worker:

       fly secrets set -a cvpilot-api \
         APP_SECRET_KEY="$(openssl rand -base64 48)" \
         DATABASE_URL="postgresql+psycopg://..." \
         REDIS_URL="redis://..." \
         APP_FRONTEND_ORIGIN="https://cvpilot.app" \
         GENLAYER_CONTRACT_ADDRESS="0x8A28F70Bb580724d3d32453C8bC171B18d0Bc073"

   Repeat with -a cvpilot-worker using the same values.

4. Deploy the API. The release_command runs alembic upgrade head:

       fly deploy -c fly.api.toml

5. Deploy the worker:

       fly deploy -c fly.worker.toml

6. Confirm /readyz returns 200 with three green checks:

       curl -s https://cvpilot-api.fly.dev/readyz | python3 -m json.tool

## First-time setup (Render)

1. Create a new Web Service from this repo. Render auto-detects Python
   from pyproject.toml and uses the Procfile.
2. Add an associated Worker service pointing at the same repo, using
   the worker process from the Procfile.
3. Add a Postgres add-on and a Redis add-on. Render injects DATABASE_URL
   and REDIS_URL.
4. Add the remaining env vars from .env.production.example as secrets.
5. The release command in the Procfile runs migrations on each deploy.

## Routine deploys

       git push origin main
       fly deploy -c fly.api.toml
       fly deploy -c fly.worker.toml

The api release command runs alembic upgrade head before swapping
traffic. If migrations fail, the deploy aborts and the previous
instance keeps serving.

## Migrations

- Always generate migrations locally with: alembic revision --autogenerate -m "..."
- Review the generated file. Autogenerate misses enum changes,
  constraint renames, and server defaults.
- Test against a database snapshot before deploying.
- Never edit a migration that has already shipped. Add a new one.

## Rollback

API rollback (Fly):

       fly releases -a cvpilot-api
       fly releases rollback <VERSION> -a cvpilot-api

If a forward migration is incompatible with the previous code, you
must either roll forward with a fix or write a compensating migration.
Do not blindly downgrade.

## Smoke tests after deploy

1. curl https://cvpilot-api.fly.dev/readyz                # three green checks
2. curl https://cvpilot-api.fly.dev/metrics | grep cvpilot_   # custom metrics present
3. Register a throwaway account, submit an application, verify the
   evaluation completes and the contract_tx_hash appears on the
   detail page.
4. Open the public /verify/<hash> route in an incognito window; it
   must load without auth.

## Capacity notes

- API: start at 1 machine x 1 GiB. Two uvicorn workers per machine.
  Scale horizontally by raising min_machines_running.
- Worker: start at 1 machine x 1 GiB. concurrency=2 is appropriate
  for GenLayer-bound work since each evaluation is mostly waiting.
  Add machines, not concurrency, to scale.


## Frontend (Vercel)

The frontend is a Next.js app. Recommended host: Vercel. The repo ships
frontend/vercel.json with API rewrites and edge security headers.

1. Import the repo into Vercel. Set the project root to `frontend/`.
2. Add env vars from frontend/.env.production.example.
3. Confirm the rewrite target in frontend/vercel.json points at your
   API host (cvpilot-api.fly.dev by default).
4. Trigger a deploy. Vercel runs `next build` from vercel.json.
5. Smoke test: load /, sign in, submit an application, open the
   /verify/<hash> page in an incognito window.

To reproduce the prod build locally:

    bash frontend/scripts/build-prod.sh
    cd frontend && npm run start
