# Velox (NexlumeAI)

WhatsApp AI Receptionist for Hotels.

## AI Agent Read Order

Any AI agent working in this repository must read documents in this order before making changes:

1. `system_prompt_velox.md`
2. `SKILL.md`
3. Relevant files in `skills/`
4. Relevant task file in `tasks/` when the work maps to a planned task

This repository uses a binding rule hierarchy:

1. `skills/security_privacy.md`
2. `skills/anti_hallucination.md`
3. Other files in `skills/`
4. `system_prompt_velox.md`
5. Task-specific instructions in `tasks/`

If rules conflict, higher priority wins. Security and anti-hallucination rules are never overridden by speed pressure or task convenience.

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
| LLM | OpenAI GPT models with function calling |
| WhatsApp | Meta Business API (Cloud API) |
| PMS | Elektraweb API (JWT auth) |
| Auth | Short-lived JWT cookies + TOTP + trusted device sessions |
| Browser Automation | Playwright + Chromium for admin debug report-only scans |
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

# 4. Start backend dependencies
docker compose up -d db redis

# 5. Run migrations before starting the app
python -m velox.db.migrate

# 6. Run the application
uvicorn velox.main:app --reload --port 8001
```

The app will be available at `http://localhost:8001`. Browser requests to `/` redirect to the admin panel.

If the app does not behave as expected, do not start with frontend or prompt assumptions. Start with Docker backend validation: `docker compose ps`, then inspect `app`, `db`, `redis`, related sidecars, health status, logs, env/config, and migration readiness.

### Full Docker Stack

```bash
docker compose up --build
```

This starts all four services: **app** (port 8001), **db** (PostgreSQL), **redis**, and **cloudflared** (tunnel).

### Local Demo Admin

Canli panele gitmeden once backend ve admin panel degisikliklerini yerelde gormek icin ayri demo stack kullanin:

```bash
cp .env.demo.example .env.demo.local
bash scripts/up_local_demo.sh
```

Demo admin adresi:

```text
http://127.0.0.1:8011/admin
```

Bu stack:

- `velox-demo` compose project'i ile calisir
- ayri DB/Redis volume kullanir
- `cloudflared` baslatmaz
- stabil demo runtime icin `uvicorn` reload modu kapali calisir
- app startup sirasinda migration'lari uygular ve script `health + /admin` dogrulamasi bekler

Kod, UI veya schema degisikliginden sonra app'i yeniden baslatmak yeterlidir:

```bash
docker compose --env-file .env.demo.local -f docker-compose.demo.yml -p velox-demo restart app
```

Sadece fallback ihtiyacinda manuel catch-up calistirin:

```bash
docker compose --env-file .env.demo.local -f docker-compose.demo.yml -p velox-demo exec app python -m velox.db.migrate
```

`/api/v1/health/ready` demo env'de Elektra gibi opsiyonel entegrasyon credential'lari eksikse `503` kalabilir; bu, yerel admin panelin acilmasini tek basina engellemez.

Detayli akış: `docs/local_demo_environment.md`

## Production Deployment

```bash
# 1. Prepare production environment
cp .env.production.example .env.production
# Fill in real secrets and credentials

# 2. Start production stack
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build

# 3. Optional manual migration catch-up
docker compose --env-file .env.production -f docker-compose.prod.yml exec app python -m velox.db.migrate

# 4. Verify
curl -fsS http://127.0.0.1:8001/api/v1/health
curl -fsS http://127.0.0.1:8001/api/v1/health/ready
```

Production features: HTTPS redirect, trusted host middleware, memory limits (DB: 512M, Redis: 256M), JSON logging with rotation.

Detailed checklist: `docs/production_deployment.md`

## Documentation Sync Rule

When a change affects one of the following areas, update the matching document in the same task and same commit:

- Prompt behavior, tool/QC/policy logic -> `docs/master_prompt_v2.md`
- Admin panel domain/path or cutover/rollback flow -> `docs/admin_panel_domain_cutover.md`
- Deploy, migration, release, smoke-check flow -> `docs/production_deployment.md`

If none are affected, state that explicitly in the task summary or PR note.

## Debugging Discipline

Velox uses a backend-first debugging policy.

For debugging, diagnosis, regressions, and root cause analysis:

1. Validate backend runtime first with `docker compose ps`
2. Inspect `app`, `db`, `redis`, and relevant sidecars for health, restart loops, readiness, and logs
3. Verify env/config integrity, volumes, ports, network, migrations, DB/Redis connectivity, and health endpoints
4. Only then move to prompt, model, frontend, or UX layers

Do not present a workaround as a final fix. If only a temporary mitigation is applied, label it clearly as a temporary solution and note the permanent fix path.

## Project Structure

```
src/velox/
├── main.py                    # FastAPI entry point
├── config/                    # Settings, constants
├── core/                      # Intent engine, state machine, verification, QC,
│                              # scope classifier, response validator, fallback
│                              # responses, admin debug runner/scan registry,
│                              # structured-output replay helpers
├── llm/                       # OpenAI client, prompt builder, response parser
├── tools/                     # Tool implementations (booking, restaurant, etc.)
├── adapters/                  # External service clients (Elektraweb, WhatsApp)
├── escalation/                # Risk detection, escalation matrix
├── policies/                  # Business rules (approval, payment, cancellation)
├── models/                    # Pydantic data models
├── db/                        # Database connection, repositories, migrations
├── api/                       # FastAPI routes, middleware, embedded admin/chat-lab
│                              # UI modules, admin debug/report-only and WhatsApp
│                              # integration surfaces
└── utils/                     # Logging, i18n, validators, admin/debug auth helpers,
                               # secret encryption, lightweight Prometheus metrics helpers
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
| `GET` | `/api/v1/admin/hotels` | List hotels |
| `GET` | `/api/v1/admin/hotels/{hotel_id}` | Hotel detail |
| `PUT` | `/api/v1/admin/hotels/{hotel_id}/profile` | Update hotel profile |

### Admin — Restaurant Slots

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/admin/hotels/{hotel_id}/restaurant/slots` | Create slot |
| `GET` | `/api/v1/admin/hotels/{hotel_id}/restaurant/slots` | List slots |
| `PUT` | `/api/v1/admin/hotels/{hotel_id}/restaurant/slots/{slot_id}` | Update slot |

### Admin — Transfers

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/admin/hotels/{hotel_id}/transfers/holds` | List transfer holds |
| `POST` | `/api/v1/admin/hotels/{hotel_id}/transfers/holds/{hold_id}/approve` | Approve transfer |
| `POST` | `/api/v1/admin/hotels/{hotel_id}/transfers/holds/{hold_id}/reject` | Reject transfer |

### Admin — Conversations & Holds & Tickets

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/admin/conversations` | List conversations (filterable) |
| `GET` | `/api/v1/admin/conversations/{id}` | Conversation detail + messages |
| `POST` | `/api/v1/admin/conversations/{id}/reset` | Reset conversation state |
| `POST` | `/api/v1/admin/conversations/reset-by-phone` | Reset by phone number |
| `GET` | `/api/v1/admin/holds` | List all holds (stay, restaurant, transfer) |
| `POST` | `/api/v1/admin/holds/{hold_id}/approve` | Approve hold |
| `POST` | `/api/v1/admin/holds/{hold_id}/reject` | Reject hold |
| `GET` | `/api/v1/admin/tickets` | List escalation tickets |
| `PUT` | `/api/v1/admin/tickets/{ticket_id}` | Update ticket |

### Admin — WhatsApp Integration

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/admin/hotels/{hotel_id}/whatsapp/integration` | Current WhatsApp Cloud API connection status |
| `POST` | `/api/v1/admin/hotels/{hotel_id}/whatsapp/integration/manual` | Store manual WhatsApp connection settings with encrypted token data |
| `POST` | `/api/v1/admin/hotels/{hotel_id}/whatsapp/connect-sessions` | Start Meta OAuth / Embedded Signup connection session |
| `GET` | `/api/v1/admin/hotels/{hotel_id}/whatsapp/connect-sessions/{session_id}` | Read connection session status |
| `GET` | `/api/v1/admin/whatsapp/oauth/callback` | Backend-only Meta OAuth callback |
| `GET` | `/api/v1/admin/hotels/{hotel_id}/whatsapp/assets` | List available WhatsApp assets after authorization |
| `POST` | `/api/v1/admin/hotels/{hotel_id}/whatsapp/connect-sessions/{session_id}/complete` | Complete selected WhatsApp asset connection |
| `POST` | `/api/v1/admin/hotels/{hotel_id}/whatsapp/health-check` | Run WhatsApp integration health check |
| `POST` | `/api/v1/admin/hotels/{hotel_id}/whatsapp/webhook/subscribe` | Subscribe/configure WhatsApp webhook |
| `GET` | `/api/v1/admin/hotels/{hotel_id}/whatsapp/templates` | List WhatsApp message templates |
| `POST` | `/api/v1/admin/hotels/{hotel_id}/whatsapp/templates` | Create WhatsApp message template |
| `POST` | `/api/v1/admin/hotels/{hotel_id}/whatsapp/templates/sync` | Sync WhatsApp templates from Meta |

### Admin — Webhooks (External Callbacks)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/webhook/approval` | Approval callback |
| `POST` | `/api/v1/webhook/payment` | Payment callback |
| `POST` | `/api/v1/webhook/transfer` | Transfer callback |

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
- **Privacy** — `PHONE_HASH_SALT` (telefon hash'leme salt değeri)
- **Database** — `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, pool sizing
- **Redis** — `REDIS_URL`, session TTL, rate limit TTL
- **OpenAI** — `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_FALLBACK_MODEL`, temperature, max tokens
- **WhatsApp** — `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_APP_SECRET`, `WHATSAPP_TOKEN_ENCRYPTION_KEY`
- **Meta OAuth / Embedded Signup** — `META_APP_ID`, `META_APP_SECRET`, `META_EMBEDDED_SIGNUP_CONFIG_ID`, `META_WHATSAPP_OAUTH_SCOPES`
- **Elektraweb PMS** — `ELEKTRA_API_BASE_URL`, `ELEKTRA_API_KEY`, `ELEKTRA_HOTEL_ID`, `ELEKTRA_GENERIC_TENANT`, `ELEKTRA_GENERIC_USERCODE`, `ELEKTRA_GENERIC_PASSWORD`
- **Admin Panel** — `ADMIN_JWT_SECRET`, `ADMIN_BOOTSTRAP_TOKEN`, `ADMIN_TOTP_ISSUER`, trusted-device/session settings
- **Admin Debug** — `ADMIN_DEBUG_BROWSER_TARGET_MODE`
- **Media Analysis** — `MEDIA_ANALYSIS_ENABLED`, `MEDIA_MAX_BYTES`, `MEDIA_MAX_IMAGE_DIMENSION`, `MEDIA_RETENTION_HOURS`, `MEDIA_SUPPORTED_MIME_TYPES`
- **Metrics** — `PROMETHEUS_PORT`, `METRICS_ALLOW_PUBLIC`, `METRICS_ALLOWED_CIDRS`
- **Rate Limiting** — per-phone and webhook limits
- **Hotel Config** — `HOTEL_PROFILES_DIR`, `ESCALATION_MATRIX_PATH`, `TEMPLATES_DIR`
- **Tunnel** — `CLOUDFLARE_TUNNEL_TOKEN`

Secrets must stay in environment files or secret stores and must never be committed. When a new environment variable is introduced, update both `.env.example` and the project instruction documents that list required configuration.

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
WhatsApp User
    |
    v
Meta Business API (webhook)
    |
    v
FastAPI Webhook Endpoint
    |
    ├── 1. Signature + Timestamp Validation (HMAC-SHA256, 5 min window)
    |
    ├── 2. Consent Check ── First message? ──YES──> KVKK/GDPR consent message
    |                                               (flow stops until consent)
    |                          NO
    |                          |
    ├── 3. Session Manager (Redis) ── Load/create conversation
    |                                  Key: session:{hotel_id}:{phone_hash}
    |
    ├── 4. Media Intake Gate (optional; config-driven image mime)
    |       ├── Parse metadata (media_id, mime, sha256, caption)
    |       ├── Download + validate size/mime
    |       ├── Normalize image formats
    |       ├── Vision analysis with structured JSON only
    |       └── Low confidence/normalization failure -> fallback + handoff
    |
    ├── 5. LLM Engine (OpenAI GPT + function calling)
    |       |--- Tool calls ──> Tools Layer
    |                            (booking, restaurant, transfer, approval,
    |                             payment, notify, handoff, crm, faq)
    |                            ├── Elektraweb (stay) with circuit breaker
    |                            ├── PostgreSQL (restaurant/transfer)
    |                            └── External APIs with retry + backoff
    |
    ├── 6. QC Gate (7 checks, parallel, ≤500ms budget)
    |       ├── QC1: Intent/Entity    ├── QC5: Format
    |       ├── QC2: Source Check     ├── QC6: Escalation
    |       ├── QC3: Policy Gate      └── QC7: Session
    |       └── QC4: Security
    |       ├── PASS -> Response Parser (USER_MESSAGE + INTERNAL_JSON)
    |       └── FAIL -> Correct / call tool / human handoff
    |
    ├── 7. Handoff & SLA Engine
    |       ├── L1: 30 min  (general questions)
    |       ├── L2: 15 min  (reservation issues)
    |       └── L3: 5 min   (payment/security)
    |
    └── 8. WhatsApp API (send reply)
            ├── Text / Reply Buttons (≤3) / List Message (4+)
            └── DB conversation log + Prometheus metrics
```

## Database

PostgreSQL 16 stores hotel config, conversations, messages, stay/restaurant/transfer holds, admin users and sessions, Chat Lab data, media analysis records, hotel facts, hold archives, admin debug runs, and WhatsApp integration state.

Schema changes are managed through ordered SQL migrations in `src/velox/db/migrations/`. New schema work must include a migration in the same change and should be applied through the migration wrapper before the app starts.

Migrations: `src/velox/db/migrations/`

Manual wrapper: `python -m velox.db.migrate`

---

> **AI Agent'lar:** Kod yazmadan once `SKILL.md` ve `skills/` altindaki ilgili dosyalari oku. Kural hiyerarsisi icin `AGENTS.md`'ye bak.
