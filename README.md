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
6. Run the app: `uvicorn velox.main:app --reload --port 8001`

### Docker
```bash
docker-compose up --build
```

## Production
1. Copy `.env.production.example` to `.env.production`
2. Fill real secrets and credentials
3. Start production profile:
```bash
docker compose -f docker-compose.prod.yml up -d --build
```
4. Verify:
```bash
curl -fsS http://127.0.0.1:8001/api/v1/health
curl -fsS http://127.0.0.1:8001/api/v1/health/ready
```

Detailed production checklist: `docs/production_deployment.md`

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
- `GET /api/v1/health/ready` — Readiness check
- `GET /api/v1/webhook/whatsapp` — WhatsApp webhook verification
- `POST /api/v1/webhook/whatsapp` — WhatsApp message handler

## Environment Variables
See `.env.example` for all required configuration variables.

---

> **⚠️ Bu projede değişiklik yapmadan önce `SKILL.md` ve `/skills/` altındaki dosyalara uy.**
