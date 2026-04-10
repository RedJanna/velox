# Velox (NexlumeAI) — Codex Project Guide

## Mandatory Bootstrap

This file is the permanent repository entry point for Codex-style agents.

Treat this section as binding startup behavior, not as optional documentation.

Before any coding, debugging, documentation, configuration, or review work:

1. Open `system_prompt_velox.md`
2. Open `SKILL.md`
3. Open only the skill files relevant to the current task
4. Apply the rule hierarchy exactly as defined there
5. Only then start analysis, edits, tests, or explanations

Hard rules:

- Do not wait for the user to resend `system_prompt_velox.md`.
- Do not treat a pasted file path as "already loaded".
- If `system_prompt_velox.md` was not read in the current task, bootstrap is incomplete.
- If rules conflict, follow the documented hierarchy instead of improvising.

Permanent usage:

- For tools that support repository instruction files, `AGENTS.md` is the canonical auto-load entry point.
- For tools that support project-level custom instructions, save this once:

`Always read AGENTS.md from the repo root first, then follow its required read order before doing any work.`

- For tools that support neither repo instructions nor project instructions, the user must paste the critical rules manually at chat start.

> **Sürüm:** v5.4 | **Son güncelleme:** 2026-04-10 09:15:00
> **Değişiklik özeti:** Elektra Generic API kimlik bilgileri ve rezervasyon karti voucher/not senkronu icin gereken env degiskenleri eklendi.

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
FastAPI Webhook Endpoint
    |
    ├── 1. Signature + Timestamp Validation (HMAC-SHA256, 5 min window)
    |
    ├── 2. Consent Check ── İlk mesaj mı? ──YES──> KVKK/GDPR onay mesajı gönder
    |                                                 (onay gelene kadar akış durur)
    |                          NO
    |                          |
    ├── 3. Session Manager (Redis) ── Load/create conversation
    |                                  Key: session:{hotel_id}:{phone_hash}
    |
    ├── 4. Media Intake Gate (opsiyonel; config-driven image mime)
    |       ├── Metadata parse (media_id, mime, sha256, caption)
    |       ├── Download + size/mime doğrulama
    |       ├── Normalize (JPEG/PNG direct; WEBP/TIFF/HEIC/HEIF -> PNG/JPEG)
    |       ├── Vision analyze (structured JSON only)
    |       └── Düşük güven/normalizasyon hata -> fallback + handoff
    |
    ├── 5. LLM Engine (OpenAI GPT + function calling)
    |       |
    |       |--- Tool calls ──> Tools Layer ──────────────────────────┐
    |       |                   (booking, restaurant, transfer,      |
    |       |                    approval, payment, notify,          |
    |       |                    handoff, crm, faq)                  |
    |       |                   Stay onayinda: create -> readback    |
    |       |                   doğrulaması olmadan PAYMENT_PENDING yok|
    |       |                        |                               |
    |       |                        v                               |
    |       |                   Adapters                             |
    |       |                   ├── Elektraweb (stay) ◄── Circuit Breaker
    |       |                   ├── PostgreSQL (restaurant/transfer)  |
    |       |                   └── External APIs ◄── Retry + Backoff |
    |       |                                                        |
    |       v                                                        |
    ├── 6. QC Gate (7 checks, parallel, ≤500ms budget)               |
    |       ├── QC1: Intent/Entity    ├── QC5: Format                |
    |       ├── QC2: Source Check     ├── QC6: Escalation            |
    |       ├── QC3: Policy Gate      └── QC7: Session               |
    |       └── QC4: Security                                        |
    |       |                                                        |
    |       ├── PASS ──> Response Parser (USER_MESSAGE + INTERNAL_JSON)
    |       └── FAIL ──> Düzelt / Tool çağır / İnsan devri           |
    |                                                                |
    ├── 7. Handoff & SLA Engine                                      |
    |       ├── L1: 30 min  (genel sorular)                          |
    |       ├── L2: 15 min  (rezervasyon sorunları)                  |
    |       └── L3: 5 min   (ödeme/güvenlik)                         |
    |       └── Follow-up: %100 → hatırlatma, %300 → escalate       |
    |
    └── 8. WhatsApp API (send reply)
            ├── Text / Reply Buttons (≤3) / List Message (4+)
            └── DB (log conversation) + Metrics (Prometheus)
```

## Required Read Order
Before doing any project work, read documents in this order:

1. `system_prompt_velox.md` — master AI operating rules, backend-first debugging discipline, documentation sync rules
2. `SKILL.md` — skill index, rule hierarchy, task-to-skill map
3. Relevant files in `skills/` for the current task
4. The matching task file in `tasks/` if the work maps to a planned task

> **Binding rule:** `system_prompt_velox.md` is not optional context. Any coding, debugging, documentation, or configuration task starts there.

## IMPORTANT: SKILL System (Read First!)
Before writing ANY code, you MUST:
1. Read `system_prompt_velox.md`
2. Read `SKILL.md` — the skill index file (**Rule Hierarchy dahil!**)
3. Find your current task in the **Task → Skill Map**
4. Read each required skill file from `skills/`
5. Follow every rule in those files while coding
6. Run the **Validation Checklist** from each skill before finishing

> **Kural Hiyerarşisi:** `SKILL.md` içindeki "Rule Hierarchy" tablosu tüm dosyalar için geçerlidir.
> Çakışma olursa: security_privacy > anti_hallucination > diğer skill'ler > system_prompt > task

Skill files location: `skills/`
- `coding_standards.md` — Async, types, module size, imports (EVERY backend task)
- `frontend_standards.md` — React/TypeScript, component structure, admin panel UI (EVERY frontend task)
- `security_privacy.md` — PII, secrets, sanitization, payment data
- `anti_hallucination.md` — Source hierarchy, QC checks, template-first
- `error_handling.md` — Retry patterns, fallback, user-facing errors
- `whatsapp_format.md` — Message limits, formatting, tone
- `testing_qa.md` — Test structure, mocks, coverage
- `observability.md` — Health checks, metrics, logging, tracing, alerting

> **Zorunlu problem analizi sırası:** Hata ayıklama, teşhis veya kök neden analizi yapılırken ilk inceleme alanı backend katmanıdır. Docker üstündeki `app`, `db`, `redis` ve probleme temas eden ilgili yan servislerin durum/healthcheck/log/config/bağımlılık doğrulaması yapılmadan frontend, prompt veya model davranışı hakkında hüküm verilmez.

## Key Documents
- `system_prompt_velox.md` — **Read this before every task**; AI operating rules, backend-first debug disiplini, doküman senkronizasyon yükümlülüğü
- `SKILL.md` — **Read this before every task** (skill system entry point)
- `docs/master_prompt_v2.md` — Complete system specification (runtime + product requirements)
- `docs/admin_panel_domain_cutover.md` — Admin panel domain/path cutover planı, geçiş sırası ve rollback adımları
- `docs/production_deployment.md` — Production deploy runbook'u, migration ve doğrulama adımları
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
9. **Admin auth**: Access token kısa ömürlü kalır; tekrar TOTP azaltma sadece doğrulanmış trusted device ile yapılır, 2FA kapatılmaz.
10. **Migration disiplini**: DB schema değişikliği (yeni tablo/sütun/index/constraint) içeren her işte migration dosyası zorunludur ve deploy akışında otomatik çalıştırılır; sadece manuel psql adımına bırakılmaz.
11. **Backend-first debugging zorunlu**: Problem analizi, hata ayıklama ve root cause analysis `docker compose` üstündeki backend servislerinin (`app`, `db`, `redis`, gerekiyorsa ilgili ingress/worker yan servisleri) durum, healthcheck, log, env/config, dependency readiness ve migration bütünlüğü doğrulanarak başlar; bu adım tamamlanmadan frontend/prompt/model katmanına geçilmez.
12. **Kanıt temelli teşhis**: Hata mesajını tekrar etmek root cause analysis değildir. Belirti, tetikleyici ve sistemik neden ayrı ayrı ortaya konur; hipotezler tek tek test edilir.
13. **Geçici çözüm etiketleme**: Workaround uygulanırsa bunu açıkça `geçici çözüm` diye işaretle; kalıcı çözümü ayrıca belirt.
14. **Yarım iş bırakma**: Kullanıcı düzenleme veya düzeltme istiyorsa analizde durma; değişikliği uygula, doğrula, kalan riskleri net yaz.

## Operational Discipline

- **Zero fluff:** Gereksiz giriş, konu dışı tavsiye, süslü dil yok.
- **Short but complete:** Teknik detay yeterli olacak, tekrar olmayacak.
- **Evidence first:** Sonuca değil kanıta git; emin olunmayan şey varsayım olarak etiketlenir.
- **Root cause first:** Belirtiyi kapatmak yerine nedeni ayır ve tekrarını önle.
- **Backend before frontend:** Backend sözleşmesi ve runtime sağlığı netleşmeden frontend tahminiyle ilerleme.
- **Observable debugging:** Log, request flow, dependency state, config/env, migration ve data integrity kontrol edilir.

## Backend-First Debug Protocol

Debugging, diagnosis, regression review, performance analysis, and root cause analysis must start with backend runtime validation.

Minimum order:

1. Run `docker compose ps` or equivalent and inspect `app`, `db`, `redis`, plus flow-related sidecars
2. Check `unhealthy`, `restarting`, `exited`, readiness failure, or restart loops
3. Inspect container logs to locate the first break in the error chain
4. Validate env/config, ports, volumes, networks, `depends_on`, migrations/schema, DB/Redis connectivity, and health endpoints
5. Only after backend health is understood move to prompt, model, frontend, or UX layers

> **Binding rule:** A diagnosis completed without Docker backend validation is incomplete and must not be treated as a finished root cause analysis.

## Critical Docs Sync Gate

If the current change affects one of the following areas, update the matching document in the same task and same commit:

- Prompt behavior, LLM flow, tool logic, QC or policy behavior -> `docs/master_prompt_v2.md`
- Admin panel domain/path, proxy/ingress routing, cutover or rollback -> `docs/admin_panel_domain_cutover.md`
- Deploy commands, migration/release flow, smoke checks, production validation -> `docs/production_deployment.md`

If none apply, state that explicitly in the task summary.

## ULTRATHINK Protocol

If the developer explicitly writes `ULTRATHINK`, switch to deeper analysis mode:

- Expand technical depth and edge-case coverage
- Review performance, security, scalability, maintainability, and failure modes
- Avoid early closure on the first plausible answer

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

### Migration Automation Policy (Manual adımı azaltmak için zorunlu akış)

- **Amaç:** Kod değişikliği sonrası "migration çalıştırmayı unutma" riskini ortadan kaldırmak.
- **Kural 1:** Migration gerektiren her task'ta migration dosyası aynı commit içinde yer alır.
- **Kural 2:** Migration uygulama adımı mümkünse tek komutla standartlaştırılır (`make migrate` veya eşdeğer script).
- **Kural 3:** Lokal geliştirmede backend başlatmadan önce migration komutu çalıştırılır; manuel SQL komutu istisna/fallback olarak kalır.
- **Kural 4:** CI/CD hattında migration kontrolü zorunludur; migration uygulanmadan deploy tamamlanmış sayılmaz.
- **Kural 5:** Runtime'da migration eksikliği tespit edilirse endpoint 500 yerine anlamlı 503 + aksiyon mesajı döndürmelidir.
- **Kural 6 (LLM operasyon davranışı):** Migration eksikliği hatasında LLM kullanıcıdan izin isteyip komutu kendisi uygular; kullanıcıyı uzun manuel adım listesiyle bırakmaz.
- **Kural 7 (Tek satır komut standardı):** PowerShell/terminal satır bölünmesi kaynaklı hata riskine karşı migration komutları tek satır verilir. Çok satırlı örnek sadece açıkça istenirse paylaşılır.
- **Kural 8 (İzin/escalation):** Komut sandbox veya yetki nedeniyle escalated izin gerektiriyorsa LLM doğrudan izin talebi açar; önce kullanıcıya uzun teknik açıklama gönderip beklemez.
- **Kural 9 (Doğrulama sonrası adım):** Migration çalıştıktan sonra LLM standart olarak `app restart` + ilgili endpoint smoke check adımını önerir veya uygular.

> **Standartlaştırma notu:** Projede bir migration wrapper komutu tanımlandığında AGENTS.md ve README aynı komutu referans almalıdır.

> **⚠️ Güvenlik notu:** `git add -A` kullanırken `.gitignore` dosyasının güncel olduğundan emin ol.
> `.env`, `*.pem`, `credentials.*`, `secrets.*` gibi hassas dosyalar `.gitignore`'da **mutlaka** listelenmeli.
> Commit öncesi `git status` ile eklenen dosyaları kontrol et — hassas dosya görürsen **commit etme**, uyar.

## Required .gitignore Entries
The following patterns **MUST** be in `.gitignore` before any commit. If missing, add them first:

```gitignore
# Secrets & credentials
.env
.env.*
*.pem
*.key
credentials.*
secrets.*
**/secret_*
*.p12

# Python
__pycache__/
*.pyc
.mypy_cache/
.pytest_cache/
.ruff_cache/
*.egg-info/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Docker
docker-compose.override.yml

# Logs (local)
*.log
logs/
```

> **Kural:** Her `git add -A` öncesi `git status` çalıştır.
> Yukarıdaki pattern'lara uyan dosya staged'daysa **commit etme**, `.gitignore`'u düzelt.

## Multi-Tenant Architecture (İkinci Otel ve Sonrası)

> **Durum:** Şu an tek otel (Kassandra Ölüdeniz) ile çalışıyoruz. İkinci otel eklendiğinde
> aşağıdaki mimari kararlar uygulanacak. Bu bölüm **planlama rehberi**dir — henüz uygulanmadı.

### Tenant izolasyon stratejisi

| Katman | Mevcut (tek otel) | Multi-tenant hedef |
|--------|-------------------|-------------------|
| **HOTEL_PROFILE** | Tek YAML dosyası | `hotel_id` bazlı YAML veya DB tablosu |
| **Veritabanı** | Tek schema | Shared DB + `hotel_id` sütunu (her tabloda) |
| **Redis** | Tek namespace | `hotel:{hotel_id}:*` key prefix |
| **WhatsApp** | Tek numara | Otel başına ayrı numara (WABA per hotel) |
| **LLM Prompt** | Tek system prompt | `hotel_id` bazlı dinamik prompt assembly |
| **Webhook** | Tek endpoint | Tek endpoint + `hotel_id` routing (phone number → hotel mapping) |

### Kritik tasarım kararları

1. **Shared DB, tenant column:** Her tabloya `hotel_id: int` eklenir. Tüm sorgular `WHERE hotel_id = $N` içerir. ORM/repository katmanında zorunlu filtre.
2. **Phone → Hotel mapping:** Gelen WhatsApp numarası hangi otele ait? `whatsapp_numbers` tablosu: `phone_number → hotel_id`. Webhook'ta ilk adım bu lookup.
3. **HOTEL_PROFILE loader:** `hotel_id` parametresi alır, ilgili profili yükler. Cache: Redis ile `hotel:profile:{hotel_id}` (TTL: 1 saat).
4. **Session isolation:** Redis session key: `session:{hotel_id}:{guest_phone_hash}`. Farklı otellerdeki aynı misafir ayrı session'larda.
5. **Admin panel:** Her kullanıcı bir veya birden fazla `hotel_id`'ye bağlı. JWT token'da `hotel_ids: list[int]`. API middleware'de hotel_id filtresi zorunlu.
6. **Adapter config:** Elektraweb credentials otel bazlı. `adapters/elektraweb.py` → `hotel_id` ile doğru credential set'i seçer.

### Uygulama sırası (ikinci otel eklenirken)

1. DB migration: Tüm tablolara `hotel_id` sütunu + index
2. `whatsapp_numbers` tablosu oluştur
3. Repository layer: Tüm sorgulara `hotel_id` filtresi ekle
4. HOTEL_PROFILE loader'ı `hotel_id` parametreli yap
5. Redis key'lere `hotel:{hotel_id}:` prefix ekle
6. Admin panel: hotel selector + JWT hotel_ids
7. Webhook router: phone → hotel_id mapping
8. Test: İki farklı hotel_id ile uçtan uca test

### Yasak kararlar

- **Ayrı DB instance / schema per hotel:** Gereksiz karmaşıklık, bakım maliyeti yüksek.
- **Ayrı deployment per hotel:** Tek codebase, tek deployment. Otel farkı sadece config seviyesinde.
- **Hardcoded hotel_id kontrolleri:** `if hotel_id == 1` gibi kodlar yasak. Her şey config-driven.

## Environment Variables

All secrets, API keys, and configuration must be in environment variables. Never commit `.env` files.

### Zorunlu ENV değişkenleri

| Değişken | Açıklama | Örnek | Kaynak |
|----------|----------|-------|--------|
| `OPENAI_API_KEY` | OpenAI GPT API anahtarı | `sk-...` | OpenAI Dashboard |
| `WHATSAPP_ACCESS_TOKEN` | Meta Business API erişim token'ı | `EAA...` | Meta Business Suite |
| `WHATSAPP_VERIFY_TOKEN` | Webhook doğrulama token'ı (kendin belirle) | `velox-webhook-2024` | Manuel |
| `WHATSAPP_PHONE_NUMBER_ID` | WhatsApp Business telefon numarası ID'si | `10234...` | Meta Business Suite |
| `WHATSAPP_APP_SECRET` | WhatsApp webhook HMAC-SHA256 imza secret'ı | `abc123...` | Meta Business Suite |
| `DB_HOST` | PostgreSQL host | `db` | Hosting |
| `DB_PORT` | PostgreSQL port | `5432` | Hosting |
| `DB_NAME` | PostgreSQL veritabanı adı | `velox` | Hosting |
| `DB_USER` | PostgreSQL kullanıcı adı | `velox` | Hosting |
| `DB_PASSWORD` | PostgreSQL şifresi | `***` | Hosting |
| `REDIS_URL` | Redis bağlantı adresi | `redis://localhost:6379/0` | Hosting |
| `PHONE_HASH_SALT` | Telefon numarası hash'leme için salt (rainbow table koruması) | `random-32-char-string` | Manuel üret |
| `ELEKTRA_API_BASE_URL` | Elektraweb PMS API base URL | `https://api.elektraweb.com` | Elektraweb |
| `ELEKTRA_API_KEY` | Elektraweb API anahtarı | `***` | Elektraweb |
| `ELEKTRA_GENERIC_TENANT` | Elektra Generic API tenant değeri | `21966` | Elektraweb |
| `ELEKTRA_GENERIC_USERCODE` | Elektra Generic API kullanıcı kodu | `***` | Elektraweb |
| `ELEKTRA_GENERIC_PASSWORD` | Elektra Generic API şifresi | `***` | Elektraweb |
| `ADMIN_JWT_SECRET` | Admin panel JWT imzalama anahtarı | `random-64-char-string` | Manuel üret |
| `ADMIN_WEBHOOK_SECRET` | Admin webhook HMAC secret | `***` | Manuel üret |

### Opsiyonel ENV değişkenleri

| Değişken | Açıklama | Varsayılan |
|----------|----------|-----------|
| `APP_LOG_LEVEL` | Log seviyesi | `INFO` |
| `QC_TIMEOUT_MS` | QC gate tek check timeout (ms) | `500` |
| `CIRCUIT_BREAKER_THRESHOLD` | Circuit breaker hata eşiği | `5` |
| `CIRCUIT_BREAKER_RECOVERY_S` | Circuit breaker recovery süresi (saniye) | `30` |
| `REDIS_SESSION_TTL_SECONDS` | Redis session TTL (saniye) | `1800` |
| `SENTRY_DSN` | Sentry error tracking DSN | _(boş = devre dışı)_ |
| `PROMETHEUS_PORT` | Prometheus metrics port | `9090` |
| `METRICS_ALLOW_PUBLIC` | `/metrics` endpoint'ini herkese açar; varsayılan olarak kapalı tutulmalıdır | `false` |
| `METRICS_ALLOWED_CIDRS` | `/metrics` endpoint'ine erişebilecek CIDR allowlist'i | `127.0.0.1/32,::1/128,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16` |
| `MEDIA_ANALYSIS_ENABLED` | Inbound image analysis feature flag | `true` |
| `MEDIA_MAX_BYTES` | Inbound media maksimum dosya boyutu (byte) | `8388608` |
| `MEDIA_MAX_IMAGE_DIMENSION` | Görsel normalize sonrası max kenar piksel sınırı | `2048` |
| `MEDIA_RETENTION_HOURS` | Medya analiz kaydı saklama süresi (saat) | `24` |
| `MEDIA_SUPPORTED_MIME_TYPES` | Desteklenen inbound image mime listesi (virgüllü) | `image/jpeg,image/jpg,image/png,image/webp,image/tiff,image/heic,image/heif` |
| `ELEKTRA_GENERIC_API_BASE_URL` | Elektra Generic API base URL | `https://4001.hoteladvisor.net` |
| `ELEKTRA_GENERIC_LOGIN_TOKEN` | Günlük geçerli Generic API token override; sadece geçici operasyonel fallback olarak kullanılmalıdır | _(boş = devre dışı)_ |

> **Kural:** Yeni bir ENV değişkeni eklendiğinde bu tabloyu güncelle ve `.env.example` dosyasına da ekle.

## AGENTS.md Bakım Politikası

> **Bu bölüm neden var:** Proje sahibi günde çok sayıda LLM oturumu açar ve sürekli iterasyon yapar.
> AGENTS.md, her yeni oturumda projeye ilk kez bakan bir LLM'in okuduğu **kök referans dosyasıdır.**
> Bu dosyadaki bilgi eski kalırsa, LLM yanlış mimari varsayımlarla kod üretir. Bu bölüm, dosyanın
> ne zaman, nasıl ve hangi koşullarda güncellenmesi gerektiğini tanımlar.

### 1. Zorunlu güncelleme tetikleyicileri

Aşağıdaki değişiklik türlerinden **herhangi biri** yapıldığında AGENTS.md **mutlaka** güncellenir:

| Değişiklik türü | Güncellenmesi gereken bölüm |
|-----------------|----------------------------|
| Yeni dizin veya modül eklendi/silindi (`src/velox/` altında) | **File Structure** |
| Mesaj işleme akışına yeni bir adım eklendi/çıkarıldı (yeni gate, yeni kontrol noktası, yeni middleware) | **Architecture diyagramı** |
| Mevcut bir akış adımının davranışı köklü şekilde değişti (ör. QC gate 7→8 check oldu, circuit breaker mantığı değişti) | **Architecture diyagramı** |
| Yeni bir dış bağımlılık/servis eklendi (ör. yeni PMS, yeni ödeme sağlayıcı, yeni API) | **Architecture diyagramı + Tech Stack** |
| Tech Stack değişti (Python sürümü, DB değişikliği, yeni framework) | **Tech Stack** |
| Yeni skill dosyası oluşturuldu veya mevcut biri silindi/yeniden adlandırıldı | **Skill files listesi** |
| Yeni task dosyası eklendi | **Implementation Order** |
| Yeni zorunlu veya opsiyonel ENV değişkeni eklendi | **Environment Variables tabloları** |
| Critical Rules'a yeni kural eklendi veya mevcut kural değişti | **Critical Rules** |
| `.gitignore`'a yeni pattern eklenmesi gerekti | **Required .gitignore Entries** |
| Multi-tenant planında karar değişikliği yapıldı | **Multi-Tenant Architecture** |

### 1.1 Kritik doküman senkronizasyon kuralı (zorunlu)

`docs/master_prompt_v2.md`, `docs/admin_panel_domain_cutover.md`, `docs/production_deployment.md` dosyaları için aşağıdaki kural geçerlidir:

- Kodu etkileyen değişiklik ilgili kritik dokümanı etkiliyorsa, doküman güncellemesi **aynı commit** içinde yapılır.
- Değişiklik ilgili dokümanı etkilemiyorsa commit mesajına kısa not düşülür: `[NO-DOC-UPDATE:<doc_adi>:<kisa_gerekce>]`.
- Aynı değişiklik birden fazla kritik dokümanı etkiliyorsa hepsi birlikte güncellenir; parçalı ve ertelenmiş güncelleme yapılmaz.

Kritik doküman tetikleyici matrisi:

| Değişiklik türü | Güncellenmesi zorunlu doküman |
|-----------------|-------------------------------|
| LLM davranışı, araç sırası, QC/policy, prompt akışı, yanıt formatı veya ürün kuralı değişikliği | `docs/master_prompt_v2.md` |
| Admin panel domain/path, reverse proxy, route, auth giriş yolu veya cutover/rollback planı değişikliği | `docs/admin_panel_domain_cutover.md` |
| Deploy komutu, compose/runbook, migration akışı, healthcheck/smoke check, release adımları değişikliği | `docs/production_deployment.md` |

### 2. Güncelleme GEREKTİRMEYEN durumlar

Aşağıdaki değişiklikler AGENTS.md'yi **etkilemez** — gereksiz güncelleme yapma:

- Mevcut bir dosya içindeki bug fix veya refactor (mimari değişiklik yoksa)
- Skill dosyası içindeki kural ekleme/düzeltme (skill dosyasının kendisi yeterli)
- Test ekleme veya test düzeltme
- HOTEL_PROFILE veri güncellemesi (otel bilgisi değişikliği)
- Template veya mesaj şablonu değişikliği
- Mevcut ENV değişkeninin değerini değiştirme (yeni değişken eklemediğin sürece)
- Kod stili veya formatlama değişiklikleri

### 3. Architecture diyagramı koruma kuralı

**Mimari diyagram bu dosyanın en kritik bölümüdür.** Kurallar:

- Diyagram, mesajın WhatsApp'tan gelişinden yanıt gönderilmesine kadar olan **tüm adımları** göstermelidir.
- Diyagramda **numaralanmış adımlar** kullanılır (1, 2, 3...). Yeni adım eklendiğinde sıra güncellenir.
- Her adımın yanında kısa açıklama ve varsa performans/limit bilgisi bulunur.
- Diyagramda gösterilmeyen bir akış adımı gerçek kodda **var olmamalıdır**; var olan her adım diyagramda **görünmelidir**.
- Diyagram sadece ASCII art ile çizilir — görsel bağımlılık olmaz, her LLM okuyabilir.

**Diyagram güncelleme testi:** Yaptığın değişiklikten sonra şu soruyu sor:
> "Bir LLM bu diyagrama bakarak sistemin uçtan uca akışını doğru anlayabilir mi?"
> Cevap HAYIR ise → diyagramı güncelle. Cevap EVET ise → dokunma.

### 4. Oturum sonu hızlı kontrol (Quick Check)

Her LLM oturumunun **sonunda**, aşağıdaki 9 soruluk kontrol listesini çalıştır.
Herhangi birine **EVET** cevabı varsa, ilgili bölümü güncelle:

```
AGENTS.md QUICK CHECK (oturum sonu)
─────────────────────────────────────
[ ] Yeni bir dizin veya dosya yapısı değişikliği yaptım mı?          → File Structure
[ ] Mesaj işleme akışına yeni bir adım ekledim/çıkardım mı?          → Architecture diyagramı
[ ] Yeni bir ENV değişkeni tanımladım mı?                             → Environment Variables
[ ] Yeni bir skill dosyası oluşturdum veya sildim mi?                 → Skill files listesi
[ ] Tech stack'e yeni bir teknoloji/servis ekledim mi?                → Tech Stack
[ ] Critical Rules'da bir kuralı değiştirdim veya yeni kural mı var? → Critical Rules
[ ] Prompt/LLM ürün davranışı veya tool policy değişti mi?            → docs/master_prompt_v2.md
[ ] Admin domain/path/cutover/rollback akışı değişti mi?              → docs/admin_panel_domain_cutover.md
[ ] Deploy/migration/runbook/health adımı değişti mi?                 → docs/production_deployment.md
─────────────────────────────────────
Tüm cevaplar HAYIR → AGENTS.md güncelleme gerekmiyor.
En az bir cevap EVET → İlgili bölümü güncelle + sürüm bloğunu güncelle.
```

### 5. Sürüm bloğu güncelleme kuralı

Dosyanın en üstündeki sürüm bloğu, her güncelleme sonrası şu formatta güncellenir:

```
> **Sürüm:** v{major}.{minor} | **Son güncelleme:** {YYYY-MM-DD HH:MM:SS}
> **Değişiklik özeti:** {Tek cümleyle ne değişti}
```

- **Major (v3.0, v4.0...):** Mimari diyagram değişikliği veya yeni bölüm eklenmesi
- **Minor (v2.1, v2.2...):** Mevcut bölümlere satır/tablo eklenmesi, ENV güncellemesi, düzeltmeler

### 6. Uygulanma sorumluluğu

- Bu kurallar **projeyle çalışan her LLM** için geçerlidir (Claude, Codex, Copilot, GPT, Gemini).
- LLM, oturum içinde yaptığı değişikliklerden AGENTS.md'yi etkileyen bir durum tespit ederse, **oturum bitmeden önce** güncellemeyi kendisi yapar veya geliştiriciye hatırlatır.
- Geliştirici açıkça "AGENTS.md'yi güncelleme" demedikçe, LLM Quick Check sonucuna göre güncelleme önerir.
- Bu politika `system_prompt_velox.md` §3 ile uyumludur: eski bilgi dokümanda tutulmaz, güncelliğini yitirmiş içerik silinir veya düzeltilir.

## File Structure
```
src/velox/
├── main.py                    # FastAPI entry point
├── config/                    # Settings, constants
├── core/                      # Intent engine, state machine, verification, QC, scope classifier, response validator, fallback responses, structured-output replay helpers
├── llm/                       # OpenAI client, prompt builder, response parser
├── tools/                     # Tool implementations (booking, restaurant, etc.)
├── adapters/                  # External service clients (Elektraweb, WhatsApp)
├── escalation/                # Risk detection, escalation matrix
├── policies/                  # Business rules (approval, payment, cancellation)
├── models/                    # Pydantic data models
├── db/                        # Database connection, repositories, migrations
├── api/                       # FastAPI routes, middleware, embedded admin/chat-lab UI modules
└── utils/                     # Logging, i18n, validators, lightweight Prometheus metrics helpers
```
