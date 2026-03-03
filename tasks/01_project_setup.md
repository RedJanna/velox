# Task 01: Project Setup

> **BEFORE YOU START — Read these skill files:**
> - `skills/coding_standards.md`

## Objective
Install all dependencies, verify the FastAPI application starts correctly, confirm settings load from `.env`, and create a project README.

## Prerequisites
- Python 3.11+ installed
- Docker and docker-compose installed
- Git repository initialized

---

## Step 1: Install Dependencies

1. Open a terminal in the project root: `C:\Users\gonen\Desktop\velox\DİKKAT\velox\`
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux/Mac
   # or .venv\Scripts\activate  # Windows
   ```
3. Install the project in editable mode with dev dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
4. Verify all packages install without errors. The dependencies are defined in `pyproject.toml` and include:
   - `fastapi>=0.115.0`
   - `uvicorn[standard]>=0.32.0`
   - `asyncpg>=0.30.0`
   - `redis[hiredis]>=5.2.0`
   - `openai>=1.60.0`
   - `httpx>=0.28.0`
   - `pydantic>=2.10.0`
   - `pydantic-settings>=2.7.0`
   - `pyyaml>=6.0.2`
   - `structlog>=24.4.0`
   - `python-dotenv>=1.0.1`
   - `python-multipart>=0.0.18`
   - `orjson>=3.10.0`
   - `python-jose[cryptography]>=3.3.0`
   - `passlib[bcrypt]>=1.7.4`
   - `phonenumbers>=8.13.0`

**Source file**: `pyproject.toml`

---

## Step 2: Create .env from Example

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. The `.env` file is already structured with all required variables. For local development, the defaults are sufficient. Do NOT change secrets in committed files.

**Source file**: `.env.example`

---

## Step 3: Verify Settings Load

1. The settings module is already implemented at `src/velox/config/settings.py`.
2. Verify it loads correctly by running a quick check:
   ```bash
   python -c "from velox.config.settings import settings; print(settings.app_env, settings.db_host, settings.openai_model)"
   ```
3. Expected output: `development localhost gpt-4o`
4. The `Settings` class uses `pydantic-settings` with `BaseSettings` and loads from `.env` automatically.

**Source file**: `src/velox/config/settings.py`

---

## Step 4: Verify FastAPI App Starts

1. The entry point is already defined at `src/velox/main.py`.
2. Start the app:
   ```bash
   uvicorn velox.main:app --host 0.0.0.0 --port 8000 --reload
   ```
3. The app should start without errors. The lifespan handler has TODO stubs for DB/Redis/config loading (those are implemented in later tasks).
4. Test the root endpoint:
   ```bash
   curl http://localhost:8000/
   ```
5. **Expected response**:
   ```json
   {"service": "velox", "status": "running"}
   ```

**Source file**: `src/velox/main.py`

---

## Step 5: Add Health Check Endpoint

Create a health check router at `src/velox/api/routes/health.py`:

```python
"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}
```

Then register the router in `src/velox/main.py`. Uncomment or add:

```python
from velox.api.routes import health
app.include_router(health.router, prefix="/api/v1")
```

**Verify**:
```bash
curl http://localhost:8000/api/v1/health
# Expected: {"status": "healthy"}
```

**Files to create**:
- `src/velox/api/routes/health.py`

**Files to modify**:
- `src/velox/main.py` — add the health router import and `include_router` call

---

## Step 6: Set Up Logging with structlog

Create `src/velox/utils/logging.py`:

```python
"""Structured logging setup using structlog."""

import logging
import structlog
from velox.config.settings import settings


def setup_logging() -> None:
    """Configure structlog for the application."""
    log_level = getattr(logging, settings.app_log_level.upper(), logging.INFO)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if settings.app_debug else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

Call `setup_logging()` at the top of the lifespan function in `src/velox/main.py`:

```python
from velox.utils.logging import setup_logging

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    # ... rest of startup
    yield
    # ... shutdown
```

**Files to create**:
- `src/velox/utils/logging.py`

**Files to modify**:
- `src/velox/main.py` — import and call `setup_logging()`

---

## Step 7: Create README.md

Create `README.md` in the project root with this content:

```markdown
# Velox (NexlumeAI)

WhatsApp AI Receptionist for Hotels.

## Overview
Velox is an AI-powered receptionist that handles guest inquiries, reservations (stay, restaurant, transfer), escalation, and CRM logging via WhatsApp using OpenAI GPT models.

## Tech Stack
- **Language**: Python 3.11+
- **Framework**: FastAPI (async)
- **Database**: PostgreSQL 16 (asyncpg)
- **Cache**: Redis 7
- **LLM**: OpenAI GPT (gpt-4o, function calling)
- **WhatsApp**: Meta Business API (Cloud API)
- **Container**: Docker + docker-compose

## Quick Start

### Prerequisites
- Python 3.11+
- Docker & docker-compose
- OpenAI API key
- Meta WhatsApp Business API credentials
- Elektraweb PMS API credentials

### Setup
1. Clone the repository
2. Copy environment file: `cp .env.example .env`
3. Fill in your API keys in `.env`
4. Install dependencies: `pip install -e ".[dev]"`
5. Start infrastructure: `docker-compose up -d db redis`
6. Run the app: `uvicorn velox.main:app --reload`

### Docker
```bash
docker-compose up --build
```

## Project Structure
```
src/velox/
├── main.py              # FastAPI entry point
├── config/              # Settings, constants
├── core/                # Hotel profile loader, template engine
├── llm/                 # OpenAI client, prompt builder, response parser
├── tools/               # Tool implementations (booking, restaurant, etc.)
├── adapters/            # External service clients (Elektraweb, WhatsApp)
├── escalation/          # Risk detection, escalation matrix
├── policies/            # Business rules
├── models/              # Pydantic data models
├── db/                  # Database connection, repositories, migrations
├── api/                 # FastAPI routes + middleware
└── utils/               # Logging, validators
```

## API Endpoints
- `GET /` — Service status
- `GET /api/v1/health` — Health check
- `GET /api/v1/webhook/whatsapp` — WhatsApp webhook verification
- `POST /api/v1/webhook/whatsapp` — WhatsApp message handler

## Environment Variables
See `.env.example` for all required configuration variables.
```

**Files to create**:
- `README.md`

---

## Step 8: Verify Docker Build

1. Build the Docker image:
   ```bash
   docker build -t velox .
   ```
2. Verify it builds without errors.
3. Start the full stack:
   ```bash
   docker-compose up -d
   ```
4. Verify all services are healthy:
   ```bash
   docker-compose ps
   ```
   - `app`: running on port 8000
   - `db`: PostgreSQL healthy on port 5432
   - `redis`: Redis healthy on port 6379

**Source files**: `Dockerfile`, `docker-compose.yml`

---

## Verification Checklist

- [ ] `pip install -e ".[dev]"` succeeds without errors
- [ ] `.env` file exists with all required variables
- [ ] `python -c "from velox.config.settings import settings; print(settings.app_env)"` prints `development`
- [ ] `uvicorn velox.main:app` starts without errors
- [ ] `GET /` returns `{"service": "velox", "status": "running"}`
- [ ] `GET /api/v1/health` returns `{"status": "healthy"}`
- [ ] `docker build -t velox .` succeeds
- [ ] `docker-compose up -d` starts all 3 services
- [ ] structlog produces formatted log output on startup

---

## Files Created in This Task
| File | Purpose |
|------|---------|
| `src/velox/api/routes/health.py` | Health check endpoint |
| `src/velox/utils/logging.py` | Structured logging setup |
| `README.md` | Project documentation |

## Files Modified in This Task
| File | Change |
|------|--------|
| `src/velox/main.py` | Register health router, call setup_logging() |
