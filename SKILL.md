# SKILL System — Velox Project

## What Is This?
This file is the **entry point** for all AI coding agents (Codex, Claude, Copilot, etc.) working on the Velox project. It defines which rule files ("skills") must be read before writing any code.

**RULE: Never write or modify code without reading the relevant skill files first.**
**RULE: For debugging, diagnosis, and root cause analysis tasks, validate the Docker backend runtime before any frontend, prompt, or model-level analysis.**

---

## Rule Hierarchy (Kural Hiyerarşisi)

Kurallar arasında çakışma olursa aşağıdaki öncelik sırası geçerlidir.
Üst sıradaki kural **her zaman** alt sıradakini geçersiz kılar.

| Öncelik | Kaynak | Açıklama |
|---------|--------|----------|
| 1 (En yüksek) | `skills/security_privacy.md` | Güvenlik & gizlilik — **asla override edilemez** |
| 2 | `skills/anti_hallucination.md` | Kaynak doğrulama & QC gate kuralları |
| 3 | Diğer skill dosyaları | `error_handling`, `whatsapp_format`, `coding_standards`, `testing_qa`, `frontend_standards`, `observability` |
| 4 | `system_prompt_velox.md` | AI agent davranış & çalışma kuralları |
| 5 (En düşük) | Task-specific talimatlar | `tasks/` klasöründeki görev dosyaları |

> **Çakışma durumunda:** Dur, çakışmayı geliştirici/admin'e açıkla, kararı bekle.
> Güvenlik kuralları (Öncelik 1) için beklemeye **gerek yok** — doğrudan güvenlik kuralını uygula.

---

## How It Works

1. Before starting any task, read this file (`SKILL.md`)
2. If the task is debugging, diagnosis, or root cause analysis, start with Docker backend validation: inspect `app`, `db`, `redis`, and relevant sidecars for container state, health checks, logs, config/env integrity, dependency readiness, and migration compatibility
3. Find your task in the **Task → Skill Map** below
4. Read each listed skill file from the `skills/` directory
5. Follow every rule in those files while writing code
6. Before marking a task as done, run the **Validation Checklist** from each skill

> **Bağlayıcı debug sırası:** `SKILL.md` + gerekli skill dosyaları okunur, ardından Docker backend doğrulaması yapılır; bu doğrulama tamamlanmadan prompt, model, frontend veya saf UI katmanına geçilmez.

---

## Skill Files

| File | Scope | When to Read |
|------|-------|-------------|
| `skills/coding_standards.md` | Async patterns, type hints, module size, imports, naming | **Every task** (backend) |
| `skills/frontend_standards.md` | React/TypeScript, component structure, admin panel UI, a11y | **Every frontend/admin panel task** |
| `skills/security_privacy.md` | PII handling, secrets, input sanitization, payment data | Tasks touching user data, auth, payments |
| `skills/anti_hallucination.md` | Source hierarchy, QC checks, template-first, no fabrication | Tasks touching LLM, prompts, responses |
| `skills/error_handling.md` | Retry patterns, fallback chains, user-facing error rules | Tasks touching external APIs, tools, adapters, failure diagnosis |
| `skills/whatsapp_format.md` | Message limits, formatting, emoji policy, tone | Tasks touching message output, templates |
| `skills/testing_qa.md` | Test structure, mock strategy, coverage rules, scenario tests | Tasks that include writing tests |
| `skills/observability.md` | Health checks, metrics, logging, tracing, alerting | Tasks touching monitoring, logging, health checks, or any debugging/root cause analysis |

---

## Task → Skill Map

| Task | Required Skills |
|------|----------------|
| `01_project_setup` | `coding_standards` |
| `02_database_models` | `coding_standards`, `security_privacy` |
| `03_config_system` | `coding_standards` |
| `04_elektraweb_adapter` | `coding_standards`, `error_handling`, `security_privacy` |
| `05_whatsapp_integration` | `coding_standards`, `error_handling`, `security_privacy`, `whatsapp_format` |
| `06_llm_engine` | `coding_standards`, `anti_hallucination`, `error_handling` |
| `07_tool_implementations` | `coding_standards`, `error_handling`, `security_privacy` |
| `08_escalation_engine` | `coding_standards`, `anti_hallucination` |
| `09_admin_api` | `coding_standards`, `security_privacy`, `frontend_standards` |
| `10_webhook_handlers` | `coding_standards`, `error_handling`, `security_privacy` |
| `11_restaurant_module` | `coding_standards`, `error_handling` |
| `12_transfer_module` | `coding_standards`, `error_handling` |
| `13_testing` | `coding_standards`, `testing_qa` |
| `14_docker_deployment` | `coding_standards`, `security_privacy`, `observability` |
| `problem_analysis_root_cause` | `coding_standards`, `error_handling`, `observability` + alanla ilgili diğer skill'ler |

---

## Updating Skills

Skills are **living documents**. To update:
1. Edit the relevant file in `skills/`
2. All future tasks automatically pick up the change
3. No need to update individual task files

**Never delete a skill file** — mark rules as deprecated with `[DEPRECATED]` prefix instead.

---

## Conflict Resolution

Çakışma durumunda **Rule Hierarchy** tablosundaki öncelik sırası uygulanır:

1. **Öncelik 1-2 (security, anti-hallucination) her zaman kazanır** — override edilemez
2. **Skill kazanır** güvenlik/veri bütünlüğü kurallarında
3. **Task kazanır** implementasyon-spesifik kararlarda (hangi kütüphane, hangi pattern)
4. **Belirsizse:** Dur, çakışmayı açıkla, geliştirici kararını bekle
