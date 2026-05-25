#!/usr/bin/env bash
# End-to-end GenLayer evaluation smoke test.
# Runs login -> submit -> poll -> fetch -> pretty-print, all in one shell.
set -euo pipefail

API="${API:-http://localhost:8000}"
EMAIL="${EMAIL:-founder@cvpilot.dev}"
PASSWORD="${PASSWORD:-S3cure!Passw0rd}"
CV="${CV:-/tmp/cv.pdf}"
COVER="${COVER:-/tmp/cover.txt}"
JOB_URL="${JOB_URL:-https://example.com/}"
MAX_POLLS="${MAX_POLLS:-36}"
POLL_INTERVAL="${POLL_INTERVAL:-10}"

[ -f "$CV" ] || { echo "Missing CV file at $CV"; exit 1; }
[ -f "$COVER" ] || { echo "Missing cover letter at $COVER"; exit 1; }

echo "==> healthz"
curl -fsS "$API/healthz" >/dev/null || { echo "API not reachable at $API"; exit 1; }
echo "ok"

echo "==> login as $EMAIL"
ACCESS=$(curl -fsS -X POST "$API/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
[ -n "$ACCESS" ] || { echo "Empty access token"; exit 1; }
echo "ok (token ${ACCESS:0:30}...)"

echo "==> submit application"
APP_JSON=$(curl -fsS -X POST "$API/api/v1/applications" \
  -H "Authorization: Bearer $ACCESS" \
  -F "job_url=$JOB_URL" \
  -F "linkedin_url=https://www.linkedin.com/in/example/" \
  -F "cv=@$CV;type=application/pdf" \
  -F "cover_letter=@$COVER;type=text/plain")
APP_ID=$(echo "$APP_JSON" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
[ -n "$APP_ID" ] || { echo "Failed to create application: $APP_JSON"; exit 1; }
echo "APP_ID=$APP_ID"

echo "==> polling status (max ${MAX_POLLS} x ${POLL_INTERVAL}s)"
for i in $(seq 1 "$MAX_POLLS"); do
  STATUS=$(curl -fsS "$API/api/v1/applications/$APP_ID" \
    -H "Authorization: Bearer $ACCESS" \
    | python3 -c "import sys,json;print(json.load(sys.stdin)['status'])")
  printf "[%02d] status=%s\n" "$i" "$STATUS"
  case "$STATUS" in
    complete|failed) break ;;
  esac
  sleep "$POLL_INTERVAL"
done

echo
echo "==> final application"
curl -fsS "$API/api/v1/applications/$APP_ID" \
  -H "Authorization: Bearer $ACCESS" \
  | python3 -m json.tool

echo
echo "==> final evaluation"
curl -fsS "$API/api/v1/applications/$APP_ID/evaluation" \
  -H "Authorization: Bearer $ACCESS" \
  | python3 -m json.tool

echo
echo "APP_ID=$APP_ID  (kept for follow-up curls)"
