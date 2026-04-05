# Production Deployment Guide

## 1. Prepare Environment
1. Copy the production template:
   ```bash
   cp .env.production.example .env.production
   ```
2. Fill all required secrets in `.env.production`.
3. Ensure `.env.production` is not committed (already ignored by `.gitignore`).

## 2. Build and Start Stack
```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```

Service ports:
- API: `http://127.0.0.1:8001`
- PostgreSQL: internal container network (`db:5432`)
- Redis: internal container network (`redis:6379`)

## 3. Run Database Migration

The app now runs the versioned SQL migration runner during startup and `/api/v1/health/ready`
stays `503` until migrations are consistent.

If you need to force a manual catch-up before or after a rollout, use the same one-line wrapper:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml exec app python -m velox.db.migrate
```

## 4. Verify Health and Readiness
```bash
curl -fsS http://127.0.0.1:8001/api/v1/health
curl -fsS http://127.0.0.1:8001/api/v1/health/ready
curl -fsS http://127.0.0.1:8001/metrics | head
```

`/api/v1/health/ready` returns HTTP `200` when all checks are green, otherwise HTTP `503`.
The readiness payload now includes a `migrations` check so pending SQL drift is visible immediately.
`/metrics` exposes Prometheus-style runtime counters, including prompt truncation, structured-output recovery/fallback, and deterministic intent-domain-guard signals.
By default the endpoint only serves loopback/private-network clients. Override this only when your scrape path is protected:

```bash
METRICS_ALLOW_PUBLIC=false
METRICS_ALLOWED_CIDRS=127.0.0.1/32,::1/128,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16
```

To inspect persisted structured-output failures against the current code without dumping full message bodies:

```bash
DB_HOST=127.0.0.1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv-wsl/bin/python scripts/replay_structured_output_failures.py --limit 20 --summary-only
```

Add `--run-llm` to measure how many historical failures still reproduce under the live pipeline.
Use `--since-hours 24` for the last day, or `--since 2026-04-04T00:00:00Z --until 2026-04-04T23:59:59Z` for an explicit UTC window.
The replay summary now also reports `intent_domain_guard_counts` so you can see how many historical turns were salvaged by deterministic domain remapping.
It also reports `assistant_created_at_window` so ops can confirm the sampled time slice matches the requested replay window.

## 5. CI/CD
GitHub Actions workflow: `.github/workflows/ci.yml`
- `test`: pytest + coverage + ruff + mypy
- `docker`: container build smoke test
- `security`: Trivy scan for CRITICAL/HIGH issues

## 6. Production Checklist
- [ ] All env vars set in `.env.production`
- [ ] DB migration ran successfully
- [ ] Hotel profile YAML loaded
- [ ] WhatsApp webhook URL configured in Meta Business Manager
- [ ] Elektraweb API credentials validated
- [ ] OpenAI API key active with sufficient quota
- [ ] Redis running and accessible
- [ ] Health check returns 200
- [ ] Readiness check returns all green
- [ ] Metrics endpoint responds with Prometheus text
- [ ] Rate limiting active
- [ ] Logs shipping to monitoring (optional: Grafana/Loki)
