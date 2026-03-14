# Velox (NexlumeAI)

WhatsApp AI Receptionist for Hotels.

## Overview

Velox is an AI-powered hotel receptionist that communicates with guests via WhatsApp. It handles booking inquiries, restaurant reservations, airport transfer bookings, escalation to staff, and CRM logging — all through natural conversation powered by OpenAI GPT with function calling.

### Key Capabilities

- **Reservation Management** — check availability, create/modify/cancel bookings via Elektraweb PMS
- **Restaurant Reservations** — slot-based table booking with capacity management
- **Airport Transfers** — transfer inquiry and booking flow
- **Smart Escalation** — 3-tier risk detection (L1/L2/L3) with SLA enforcement
- **QC Gate** — 7 parallel quality checks on every AI response (intent, source, policy, security, format, escalation, session)
- **Admin Panel** — web-based dashboard with TOTP 2FA, trusted-device session controls, conversation viewer, hold management, ticket tracking
- **Chat Lab** — built-in test/evaluation interface for prompt tuning and scenario replay
- **Multi-language** — Turkish & English guest support with language detection

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.11+ |
| Framework | FastAPI (fully async) |
| Database | PostgreSQL 16 (asyncpg) |
| Cache / Session | Redis 7 (hiredis) |
| LLM | OpenAI GPT (gpt-4o + gpt-4o-mini fallback, function calling) |
| WhatsApp | Meta Business API (Cloud API v21.0) |
| PMS | Elektraweb API (JWT auth) |
| Auth | Short-lived JWT cookies + TOTP + trusted device sessions |
| Tunnel | Cloudflare Tunnel (webhook ingress) |
| Container | Docker + docker-compose |
| CI/CD | GitHub Actions (test → build → security scan) |
| Linting | Ruff, MyPy (strict), pre-commit |

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & docker-compose
- OpenAI API key
- Meta WhatsApp Business API credentials
- Elektraweb PMS API credentials

### Local Development

```bash
# 1. Clone and enter the project
git clone <repo-url> && cd velox

# 2. Create environment file
cp .env.example .env
# Fill in API keys and secrets in .env

# 3. Install dependencies
pip install -e ".[dev]"

# 4. Start database and cache
docker-compose up -d db redis

# 5. Run the application
uvicorn velox.main:app --reload --port 8001
```

The app will be available at `http://localhost:8001`. Browser requests to `/` redirect to the admin panel.

### Full Docker Stack

```bash
docker-compose up --build
```

This starts all four services: **app** (port 8001), **db** (PostgreSQL), **redis**, and **cloudflared** (tunnel).

## Production Deployment

```bash
# 1. Prepare production environment
cp .env.production.example .env.production
# Fill in real secrets and credentials

# 2. Start production stack (2 app replicas)
docker compose -f docker-compose.prod.yml up -d --build

# 3. Verify
curl -fsS http://127.0.0.1:8001/api/v1/health
curl -fsS http://127.0.0.1:8001/api/v1/health/ready
```

Production features: 2 app replicas, HTTPS redirect, trusted host middleware, memory limits (DB: 512M, Redis: 256M), JSON logging with rotation.

Detailed checklist: `docs/production_deployment.md`

## Project Structure

```
src/velox/
├── main.py              # FastAPI entry point, lifespan management
├── config/              # Settings (pydantic-settings), constants
├── core/                # Intent engine, state machine, QC gate, pipeline, hotel profile loader
├── llm/                 # OpenAI client, prompt builder, response parser
├── tools/               # Tool implementations (booking, restaurant, transfer, FAQ, etc.)
├── adapters/            # External service clients
│   ├── elektraweb/      #   Elektraweb PMS (HTTP + JWT)
│   └── whatsapp/        #   Meta Business API
├── escalation/          # Risk detection, escalation matrix, SLA engine
├── policies/            # Business rules
├── models/              # Pydantic data models
├── db/                  # asyncpg pool, repositories, SQL migrations
├── api/
│   ├── routes/          # health, admin, admin_portal, admin_session,
│   │                    # whatsapp_webhook, admin_webhook, admin_panel_ui, test_chat
│   └── middleware/      # Auth, rate limiting
└── utils/               # Structured logging, i18n, validators
```

Other top-level directories:

```
data/
├── hotel_profiles/      # YAML config per hotel (e.g. kassandra_oludeniz.yaml)
├── templates/           # Jinja2 message templates (tr/, en/)
├── escalation_matrix.yaml
├── scenarios/           # Test scenarios for Chat Lab
├── chat_lab_feedback/   # Feedback storage
└── chat_lab_imports/    # Scenario import files

docs/                    # Production deployment docs, master prompt spec
tasks/                   # 14 sequential implementation task specs
skills/                  # AI agent coding rules (8 skill files)
tests/                   # pytest test suite
scripts/                 # Utility scripts
```

## API Endpoints

### Health

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Service status (JSON) / admin panel redirect (browser) |
| `GET` | `/api/v1/health` | Liveness probe |
| `GET` | `/api/v1/health/ready` | Readiness probe (DB, Redis, OpenAI, Elektraweb, profiles) |

### WhatsApp Webhook

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/webhook/whatsapp` | Meta webhook verification |
| `POST` | `/api/v1/webhook/whatsapp` | Incoming message handler |

### Admin Panel

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/admin` | Admin panel UI (SPA) |
| `POST` | `/api/v1/admin/login` | Username/password + TOTP or trusted-device login |
| `POST` | `/api/v1/admin/logout` | End active access session, keep trusted device if present |
| `GET` | `/api/v1/admin/me` | Current user info |
| `GET` | `/api/v1/admin/dashboard/overview` | Dashboard statistics |
| `GET` | `/api/v1/admin/system/overview` | System health overview |
| `GET` | `/api/v1/admin/session/status` | Login-screen trusted-device status |
| `POST` | `/api/v1/admin/session/refresh` | Restore short-lived access cookie from remembered session |
| `GET` | `/api/v1/admin/session/preferences` | Current browser session/verification preferences |
| `PUT` | `/api/v1/admin/session/preferences` | Update trusted-device and remember-session durations |
| `POST` | `/api/v1/admin/session/forget-device` | Revoke trusted-device state for current browser |
| `POST` | `/api/v1/admin/reload-config` | Hot-reload hotel profiles |

### Admin — Bootstrap & Recovery

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/admin/bootstrap/status` | First-run setup status |
| `POST` | `/api/v1/admin/bootstrap` | Create initial admin user + TOTP QR |
| `POST` | `/api/v1/admin/bootstrap/recover-totp` | TOTP recovery flow |

### Admin — Hotels

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/hotels` | List hotels |
| `GET` | `/api/v1/hotels/{hotel_id}` | Hotel detail |
| `PUT` | `/api/v1/hotels/{hotel_id}/profile` | Update hotel profile |

### Admin — Restaurant Slots

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/hotels/{hotel_id}/restaurant/slots` | Create slot |
| `GET` | `/api/v1/hotels/{hotel_id}/restaurant/slots` | List slots |
| `PUT` | `/api/v1/hotels/{hotel_id}/restaurant/slots/{slot_id}` | Update slot |

### Admin — Transfers

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/hotels/{hotel_id}/transfers/holds` | List transfer holds |
| `POST` | `/api/v1/hotels/{hotel_id}/transfers/holds/{hold_id}/approve` | Approve transfer |
| `POST` | `/api/v1/hotels/{hotel_id}/transfers/holds/{hold_id}/reject` | Reject transfer |

### Admin — Conversations & Holds & Tickets

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/conversations` | List conversations (filterable) |
| `GET` | `/api/v1/conversations/{id}` | Conversation detail + messages |
| `POST` | `/api/v1/conversations/{id}/reset` | Reset conversation state |
| `POST` | `/api/v1/conversations/reset-by-phone` | Reset by phone number |
| `GET` | `/api/v1/holds` | List all holds (stay, restaurant, transfer) |
| `POST` | `/api/v1/holds/{hold_id}/approve` | Approve hold |
| `POST` | `/api/v1/holds/{hold_id}/reject` | Reject hold |
| `GET` | `/api/v1/tickets` | List escalation tickets |
| `PUT` | `/api/v1/tickets/{ticket_id}` | Update ticket |

### Admin — Webhooks (External Callbacks)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/webhooks/approval` | Approval callback |
| `POST` | `/api/v1/webhooks/payment` | Payment callback |
| `POST` | `/api/v1/webhooks/transfer` | Transfer callback |

### Chat Lab (Test Interface)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/chat-lab` | Chat Lab UI |
| `POST` | `/api/v1/chat` | Send test message |
| `GET` | `/api/v1/chat/history` | Get chat history |
| `POST` | `/api/v1/chat/reset` | Reset test session |
| `GET` | `/api/v1/chat/export` | Export conversation |
| `GET` | `/api/v1/chat/feedback-catalog` | Feedback categories |
| `POST` | `/api/v1/chat/feedback` | Submit feedback |
| `GET` | `/api/v1/chat/import-files` | List importable scenarios |
| `POST` | `/api/v1/chat/import-load` | Load scenario |
| `POST` | `/api/v1/chat/report` | Generate evaluation report |
| `GET` | `/api/v1/models` | Available LLM models |
| `POST` | `/api/v1/model` | Switch active model |

## Environment Variables

All configuration is managed via environment variables. See `.env.example` for the full list, grouped by:

- **Application** — `APP_ENV`, `APP_PORT`, `APP_SECRET_KEY`, `PUBLIC_BASE_URL`
- **Database** — `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, pool sizing
- **Redis** — `REDIS_URL`, session TTL, rate limit TTL
- **OpenAI** — `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_FALLBACK_MODEL`, temperature, max tokens
- **WhatsApp** — `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_APP_SECRET`
- **Elektraweb PMS** — `ELEKTRA_API_BASE_URL`, `ELEKTRA_API_KEY`, `ELEKTRA_HOTEL_ID`
- **Admin Panel** — `ADMIN_JWT_SECRET`, `ADMIN_BOOTSTRAP_TOKEN`, `ADMIN_TOTP_ISSUER`
- **Rate Limiting** — per-phone and webhook limits
- **Hotel Config** — `HOTEL_PROFILES_DIR`, `ESCALATION_MATRIX_PATH`, `TEMPLATES_DIR`
- **Tunnel** — `CLOUDFLARE_TUNNEL_TOKEN`

## Development

### Code Quality

```bash
# Lint
ruff check src/

# Format
ruff format src/

# Type check
mypy src/

# Tests with coverage
pytest --cov=velox

# All checks (via pre-commit)
pre-commit run --all-files
```

### CI/CD Pipeline

GitHub Actions runs on every push:

1. **Test** — pytest + ruff + mypy (with PostgreSQL 16 & Redis 7 services)
2. **Docker** — build image + import verification
3. **Security** — Trivy vulnerability scan (CRITICAL & HIGH severity)

## Architecture

```
Guest (WhatsApp)
  │
  ▼
┌─────────────────────────────────┐
│  1. Webhook Validation          │  HMAC-SHA256 signature + 5 min timestamp
│  2. Consent Check               │  KVKK/GDPR
│  3. Session Manager (Redis)     │  Load/create conversation state
│  4. LLM Engine (OpenAI GPT)     │  Function calling → Tools → Adapters
│  5. QC Gate (7 checks, ≤500ms)  │  Intent, Source, Policy, Security,
│                                 │  Format, Escalation, Session
│  6. Escalation Engine           │  L1: 30min / L2: 15min / L3: 5min SLA
│  7. Send Reply (WhatsApp API)   │  + DB logging + metrics
└─────────────────────────────────┘
  │
  ▼
Admin Panel (dashboard, holds, tickets, Chat Lab)
```

## Database

PostgreSQL 16 with 10 tables:

`hotels`, `conversations`, `messages`, `stay_holds`, `restaurant_holds`, `transfer_holds`, `admin_users`, `chat_lab_feedback`, `chat_lab_import_logs`, `scenarios`

Migrations: `src/velox/db/migrations/`

---

> **AI Agent'lar:** Kod yazmadan once `SKILL.md` ve `skills/` altindaki ilgili dosyalari oku. Kural hiyerarsisi icin `AGENTS.md`'ye bak.
