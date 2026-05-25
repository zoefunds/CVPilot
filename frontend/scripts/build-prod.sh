#!/usr/bin/env bash
# Production build for the CVPilot frontend.
#
# Vercel runs `next build` directly via vercel.json. This script is the
# parity copy for local prod-mode builds, smoke testing, and CI.

set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> Node version"
node --version

echo "==> Clean previous build"
rm -rf .next

echo "==> Install (frozen)"
if [[ -f package-lock.json ]]; then
  npm ci
else
  npm install
fi

echo "==> Lint"
npm run lint --silent

echo "==> Type check"
npx --yes tsc --noEmit

echo "==> Build"
NODE_ENV=production npm run build

echo "==> Build artifact"
ls -1 .next | head -10

echo "==> Done. Start with: npm run start"
