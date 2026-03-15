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

`001_initial.sql` is automatically applied by Postgres when the volume is first created.
For existing volumes, apply pending versioned migrations with one command:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml exec db sh -lc 'for f in /docker-entrypoint-initdb.d/00[2-9]_*.sql; do psql -v ON_ERROR_STOP=1 -U "$DB_USER" -d "$DB_NAME" -f "$f"; done'
```

## 4. Verify Health and Readiness
```bash
curl -fsS http://127.0.0.1:8001/api/v1/health
curl -fsS http://127.0.0.1:8001/api/v1/health/ready
```

`/api/v1/health/ready` returns HTTP `200` when all checks are green, otherwise HTTP `503`.

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
