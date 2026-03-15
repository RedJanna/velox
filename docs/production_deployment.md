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
```

`/api/v1/health/ready` returns HTTP `200` when all checks are green, otherwise HTTP `503`.
The readiness payload now includes a `migrations` check so pending SQL drift is visible immediately.

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
- [ ] Rate limiting active
- [ ] Logs shipping to monitoring (optional: Grafana/Loki)
