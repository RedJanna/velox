# Velox (NexlumeAI) — Codex Project Guide

## Project Overview
Velox is a WhatsApp AI Receptionist system for hotels. It handles guest inquiries, reservations (stay, restaurant, transfer), escalation, and CRM logging via WhatsApp using OpenAI GPT models.

## Tech Stack
- **Language**: Python 3.11+
- **Framework**: FastAPI (async)
- **Database**: PostgreSQL (asyncpg)
- **Cache**: Redis (aioredis)
- **LLM**: OpenAI GPT (all models, function calling)
- **WhatsApp**: Meta Business API (Cloud API)
- **Container**: Docker + docker-compose

## Architecture
```
WhatsApp User
    |
    v
Meta Business API (webhook)
    |
    v
FastAPI (src/velox/api/routes/whatsapp_webhook.py)
    |
    v
Session Manager (Redis) -> Load/create conversation
    |
    v
LLM Engine (OpenAI GPT + function calling)
    |--- Tool calls ---> Tools layer (booking, restaurant, transfer, approval, payment, notify, handoff, crm, faq)
    |                        |
    |                        v
    |                    Adapters (Elektraweb for stay, DB for restaurant/transfer)
    |
    v
Response Parser -> USER_MESSAGE + INTERNAL_JSON
    |
    v
WhatsApp API (send reply) + DB (log conversation)
```

## IMPORTANT: SKILL System (Read First!)
Before writing ANY code, you MUST:
1. Read `SKILL.md` — the skill index file
2. Find your current task in the **Task → Skill Map**
3. Read each required skill file from `skills/`
4. Follow every rule in those files while coding
5. Run the **Validation Checklist** from each skill before finishing

Skill files location: `skills/`
- `coding_standards.md` — Async, types, module size, imports (EVERY task)
- `security_privacy.md` — PII, secrets, sanitization, payment data
- `anti_hallucination.md` — Source hierarchy, QC checks, template-first
- `error_handling.md` — Retry patterns, fallback, user-facing errors
- `whatsapp_format.md` — Message limits, formatting, tone
- `testing_qa.md` — Test structure, mocks, coverage

## Key Documents
- `SKILL.md` — **Read this before every task** (skill system entry point)
- `docs/master_prompt_v2.md` — Complete system specification (runtime + product requirements)
- `data/hotel_profiles/kassandra_oludeniz.yaml` — Hotel data for first client
- `data/escalation_matrix.yaml` — Risk flag -> escalation level mapping
- `tasks/` — Step-by-step implementation tasks (follow in order!)

## Implementation Order
Execute tasks in `tasks/` directory sequentially:

1. `01_project_setup.md` — Dependencies, settings, entry point
2. `02_database_models.md` — PostgreSQL schema + migrations
3. `03_config_system.md` — Hotel profile loader, constants, settings
4. `04_elektraweb_adapter.md` — HTTP client for Elektraweb PMS
5. `05_whatsapp_integration.md` — Meta Business API client + webhook
6. `06_llm_engine.md` — OpenAI client, prompt builder, response parser
7. `07_tool_implementations.md` — All tool functions (booking, restaurant, etc.)
8. `08_escalation_engine.md` — Risk detection + escalation matrix
9. `09_admin_api.md` — Admin panel REST API
10. `10_webhook_handlers.md` — Approval + payment webhook processing
11. `11_restaurant_module.md` — Restaurant availability + booking
12. `12_transfer_module.md` — Transfer info + booking
13. `13_testing.md` — Unit, integration, scenario tests
14. `14_docker_deployment.md` — Dockerfile, docker-compose, health checks

## Critical Rules
1. **Never hardcode** hotel-specific data. Everything comes from HOTEL_PROFILE config.
2. **Anti-hallucination**: LLM must only use TOOL outputs + HOTEL_PROFILE data. Never fabricate.
3. **Snake_case** for all internal code. Adapter normalizes external kebab-case.
4. **EUR is base currency**. Never calculate exchange rates in code.
5. **PII safety**: Never log raw phone/email. Hash or mask in logs.
6. **Modular code**: Target 600 lines per file. Split by responsibility if exceeded.
7. **Async everywhere**: Use async/await for all I/O operations.
8. **Type hints**: Use Pydantic models and Python type hints everywhere.

## Auto-Commit Rule
After completing each task, you MUST commit your changes:
```bash
git add -A && git commit -m "Task XX: <short description of what was done>"
```
Replace `XX` with the task number and provide a brief summary. Example:
```bash
git add -A && git commit -m "Task 04: Elektraweb PMS adapter with JWT auth and retry"
```
This is mandatory — do NOT skip the commit step.

## Environment Variables (see .env.example)
All secrets, API keys, and configuration must be in environment variables. Never commit .env files.

## File Structure
```
src/velox/
├── main.py                    # FastAPI entry point
├── config/                    # Settings, constants
├── core/                      # Intent engine, state machine, verification, QC
├── llm/                       # OpenAI client, prompt builder, response parser
├── tools/                     # Tool implementations (booking, restaurant, etc.)
├── adapters/                  # External service clients (Elektraweb, WhatsApp)
├── escalation/                # Risk detection, escalation matrix
├── policies/                  # Business rules (approval, payment, cancellation)
├── models/                    # Pydantic data models
├── db/                        # Database connection, repositories, migrations
├── api/                       # FastAPI routes + middleware
└── utils/                     # Logging, i18n, validators
```
