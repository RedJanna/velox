# Task 14: Docker Deployment & DevOps

> **BEFORE YOU START — Read these skill files:**
> - `skills/coding_standards.md`
> - `skills/security_privacy.md`

## Objective
Finalize Docker configuration, health checks, CI/CD pipeline, and production deployment readiness.

## Reference
- `docs/master_prompt_v2.md` — B8 (DevOps)
- Existing `Dockerfile` and `docker-compose.yml`

## Tasks

### 1. Finalize Dockerfile

The existing Dockerfile is a good start. Add multi-stage build:

```dockerfile
# Build stage
FROM python:3.11-slim AS builder
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir --target=/deps .

# Runtime stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /deps /usr/local/lib/python3.11/site-packages
COPY src/ src/
COPY data/ data/

RUN useradd -m velox
USER velox

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "velox.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

### 2. Health Check Endpoints

Implement `src/velox/api/routes/health.py`:

```python
router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
async def health_check():
    """Basic health check — is the service running?"""
    return {"status": "ok", "service": "velox", "version": "0.1.0"}

@router.get("/ready")
async def readiness_check():
    """Readiness check — are all dependencies available?"""
    checks = {
        "database": await check_db(),
        "redis": await check_redis(),
        "openai": await check_openai_api_key(),
        "elektraweb": await check_elektraweb(),
        "hotel_profiles_loaded": check_profiles_loaded(),
    }
    all_ok = all(v["ok"] for v in checks.values())
    status_code = 200 if all_ok else 503
    return JSONResponse(
        content={"status": "ready" if all_ok else "not_ready", "checks": checks},
        status_code=status_code,
    )
```

### 3. Docker Compose Production Profile

Create `docker-compose.prod.yml`:
```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    deploy:
      replicas: 2
      restart_policy:
        condition: on-failure
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  db:
    image: postgres:16-alpine
    volumes:
      - pgdata:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          memory: 512M

  redis:
    image: redis:7-alpine
    deploy:
      resources:
        limits:
          memory: 256M
```

### 4. GitHub Actions CI/CD

Create `.github/workflows/ci.yml`:
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: velox_test
          POSTGRES_USER: velox
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]
      redis:
        image: redis:7-alpine
        ports: ["6379:6379"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev]"
      - run: pytest --cov=velox
      - run: ruff check src/
      - run: mypy src/

  docker:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t velox:latest .
      - run: docker run --rm velox:latest python -c "import velox; print('OK')"
```

### 5. Security Scanning

Add Trivy scan step:
```yaml
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t velox:latest .
      - uses: aquasecurity/trivy-action@master
        with:
          image-ref: velox:latest
          severity: CRITICAL,HIGH
```

### 6. Structured Logging

Update `src/velox/utils/logger.py`:
```python
import structlog

def setup_logging(log_level: str = "INFO"):
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

# Usage:
# logger = structlog.get_logger()
# logger.info("message_received", hotel_id=21966, phone_hash="abc123")
```

### 7. Production Checklist

- [ ] All env vars set in .env.production
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

## Expected Outcome
- Single `docker-compose up` starts entire stack
- Health/readiness probes work for orchestration
- CI pipeline runs tests + lint + type check + security scan
- Production deployment guide is clear
