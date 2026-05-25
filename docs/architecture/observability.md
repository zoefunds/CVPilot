# CVPilot Observability

## Endpoints

| Path        | Purpose                                  |
|-------------|------------------------------------------|
| `/healthz`  | Liveness (no dependencies)               |
| `/livez`    | Even simpler liveness probe              |
| `/readyz`   | Readiness: DB + Redis + GenLayer contract|
| `/metrics`  | Prometheus scrape endpoint               |

## Standard HTTP metrics

Emitted by `prometheus-fastapi-instrumentator`:

- `http_requests_total{method, handler, status_code}`
- `http_request_duration_seconds{method, handler}`
- `http_requests_in_progress{method, handler}`

`handler` is the FastAPI route template, not the resolved URL.

## CVPilot business metrics

| Metric                                | Labels             | Source                              |
|---------------------------------------|--------------------|-------------------------------------|
| `cvpilot_evaluations_total`           | backend, status    | Celery evaluation task              |
| `cvpilot_evaluation_duration_seconds` | backend            | Celery evaluation task              |
| `cvpilot_applications_submitted_total`| result             | `POST /api/v1/applications`         |
| `cvpilot_wallet_send_total`           | status             | `POST /api/v1/auth/wallet/send`     |
| `cvpilot_contract_probe_total`        | result             | `/readyz` GenLayer reachability     |

## Structured request log

One JSON log line per request via structlog: method, route (template), status,
duration_ms, request_id, user_id (when authenticated). `/metrics`, `/healthz`,
`/livez` are excluded to keep the log quiet.

## Suggested Grafana panels

1. **RPS** — `sum(rate(http_requests_total[1m])) by (handler)`
2. **p95 latency** — `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, handler))`
3. **5xx rate** — `sum(rate(http_requests_total{status_code="5xx"}[5m])) / sum(rate(http_requests_total[5m]))`
4. **Evaluation throughput** — `sum(rate(cvpilot_evaluations_total[5m])) by (backend, status)`
5. **Evaluation p95** — `histogram_quantile(0.95, sum(rate(cvpilot_evaluation_duration_seconds_bucket[10m])) by (le, backend))`
6. **Submission gate** — `sum(rate(cvpilot_applications_submitted_total[5m])) by (result)`
7. **Wallet activity** — `sum(rate(cvpilot_wallet_send_total[1h])) by (status)`

## Local exploration

cat > docs/architecture/observability.md <<'PHASE12A'
# CVPilot Observability

## Endpoints

| Path        | Purpose                                  |
|-------------|------------------------------------------|
| `/healthz`  | Liveness (no dependencies)               |
| `/livez`    | Even simpler liveness probe              |
| `/readyz`   | Readiness: DB + Redis + GenLayer contract|
| `/metrics`  | Prometheus scrape endpoint               |

## Standard HTTP metrics

Emitted by `prometheus-fastapi-instrumentator`:

- `http_requests_total{method, handler, status_code}`
- `http_request_duration_seconds{method, handler}`
- `http_requests_in_progress{method, handler}`

`handler` is the FastAPI route template, not the resolved URL.

## CVPilot business metrics

| Metric                                | Labels             | Source                              |
|---------------------------------------|--------------------|-------------------------------------|
| `cvpilot_evaluations_total`           | backend, status    | Celery evaluation task              |
| `cvpilot_evaluation_duration_seconds` | backend            | Celery evaluation task              |
| `cvpilot_applications_submitted_total`| result             | `POST /api/v1/applications`         |
| `cvpilot_wallet_send_total`           | status             | `POST /api/v1/auth/wallet/send`     |
| `cvpilot_contract_probe_total`        | result             | `/readyz` GenLayer reachability     |

## Structured request log

One JSON log line per request via structlog: method, route (template), status,
duration_ms, request_id, user_id (when authenticated). `/metrics`, `/healthz`,
`/livez` are excluded to keep the log quiet.

## Suggested Grafana panels

1. **RPS** — `sum(rate(http_requests_total[1m])) by (handler)`
2. **p95 latency** — `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, handler))`
3. **5xx rate** — `sum(rate(http_requests_total{status_code="5xx"}[5m])) / sum(rate(http_requests_total[5m]))`
4. **Evaluation throughput** — `sum(rate(cvpilot_evaluations_total[5m])) by (backend, status)`
5. **Evaluation p95** — `histogram_quantile(0.95, sum(rate(cvpilot_evaluation_duration_seconds_bucket[10m])) by (le, backend))`
6. **Submission gate** — `sum(rate(cvpilot_applications_submitted_total[5m])) by (result)`
7. **Wallet activity** — `sum(rate(cvpilot_wallet_send_total[1h])) by (status)`

## Local exploration
curl -s http://localhost:8000/metrics | head -40
curl -s http://localhost:8000/readyz | python3 -m json.tool

