# Skill: Observability & Monitoring

> **Hiyerarşi:** Bu dosya `SKILL.md` hiyerarşisinde **Öncelik 3** seviyesindedir.
> `security_privacy.md` ve `anti_hallucination.md` kuralları bu dosyadan önce gelir.

> Kod bilmeyen biri için benzetme: Bu doküman, otelin **güvenlik kamerası + sensör + alarm sistemi** kılavuzudur.
> Amaç: Sistem çalışırken "sağlıklı mı?", "yavaşlıyor mu?", "bir şey bozuldu mu?" sorularına
> **gerçek zamanlı ve geçmişe dönük** cevap verebilmek.

---

## 0) Bu dokümanın kapsamı

- **Kapsam:** Velox backend + admin panel için izleme, ölçüm, uyarı ve iz takibi kuralları
- **İlişkili dosyalar:**
  - `error_handling.md` — Hata olunca ne yapılır (bu dosya: hatayı nasıl görürüz)
  - `security_privacy.md` — Logda PII yasağı (bu dosya: neyi loglarız)
  - `coding_standards.md` — structlog kullanımı (bu dosya: log formatı ve metrikleri)

---

## 1) Üç Sütun: Log, Metric, Trace

| Sütun | Ne işe yarar? | Araç önerisi |
|-------|---------------|-------------|
| **Logging** | "Ne oldu?" — olayların kaydı | `structlog` (JSON format) |
| **Metrics** | "Ne kadar?" — sayaçlar, süreler, oranlar | Prometheus + Grafana |
| **Tracing** | "Nasıl aktı?" — bir isteğin uçtan uca yolu | OpenTelemetry (OTLP) |

**Benzetme:**
- Log = Olay defteri ("Saat 14:00'te şu oldu")
- Metric = Dashboard göstergeleri ("Bugün 200 misafir, ortalama yanıt 3sn")
- Trace = Bir misafirin "baştan sona" yolculuk haritası

---

## 2) Health Checks (Sağlık Kontrolleri)

### 2.1 Endpoint
FastAPI'de `/health` ve `/health/detailed` endpoint'leri olmalı.

| Endpoint | Erişim | Çıktı |
|----------|--------|-------|
| `GET /health` | Public (load balancer için) | `{"status": "ok"}` veya `{"status": "degraded"}` |
| `GET /health/detailed` | Admin-only (JWT gerekli) | Her bağımlılığın durumu ayrı ayrı |

### 2.2 Kontrol edilecek bağımlılıklar

| Bağımlılık | Kontrol yöntemi | Sağlıklı kriteri | Kontrol sıklığı |
|------------|----------------|-------------------|-----------------|
| PostgreSQL | `SELECT 1` | < 1sn yanıt | Her 15 sn |
| Redis | `PING` | < 500ms yanıt | Her 15 sn |
| Elektraweb API | Basit GET (auth check) | < 5sn yanıt, 200 status | Her 60 sn |
| OpenAI API | — (on-demand) | Son 5dk'da başarılı çağrı var mı | Pasif izleme |
| WhatsApp API | — (on-demand) | Son 5dk'da başarılı gönderim var mı | Pasif izleme |

### 2.3 Toplam sistem durumu

```python
def get_system_status(checks: dict[str, bool]) -> str:
    """
    'ok'       — Tüm bağımlılıklar sağlıklı
    'degraded' — Bazıları çalışmıyor ama sistem kısmen hizmet veriyor
    'down'     — Kritik bağımlılık (DB veya Redis+DB) çökmüş
    """
    if all(checks.values()):
        return "ok"
    critical = {"postgresql", "redis"}
    if not any(checks.get(c, False) for c in critical):
        return "down"
    return "degraded"
```

---

## 3) Metrics (Ölçümler)

### 3.1 Zorunlu metrikler

| Metric adı | Tip | Açıklama |
|------------|-----|----------|
| `velox_requests_total` | Counter | Toplam gelen istek sayısı (endpoint, method, status) |
| `velox_request_duration_seconds` | Histogram | İstek işleme süresi (endpoint bazlı) |
| `velox_whatsapp_messages_sent_total` | Counter | Gönderilen WhatsApp mesaj sayısı (status: success/fail) |
| `velox_whatsapp_messages_received_total` | Counter | Alınan WhatsApp mesaj sayısı |
| `velox_llm_calls_total` | Counter | LLM çağrı sayısı (model, status) |
| `velox_llm_duration_seconds` | Histogram | LLM yanıt süresi |
| `velox_llm_tokens_total` | Counter | Kullanılan token sayısı (prompt + completion) |
| `velox_qc_duration_seconds` | Histogram | QC gate toplam süresi |
| `velox_qc_failures_total` | Counter | QC check başarısızlık sayısı (check_name bazlı) |
| `velox_escalations_total` | Counter | Escalation sayısı (level: L1/L2/L3) |
| `velox_handoff_open_tickets` | Gauge | Şu an açık handoff ticket sayısı |
| `velox_handoff_sla_breaches_total` | Counter | SLA aşımı sayısı (level bazlı) |
| `velox_circuit_breaker_state` | Gauge | Circuit breaker durumu (0=closed, 1=open, 0.5=half-open) |
| `velox_elektraweb_calls_total` | Counter | Elektraweb API çağrı sayısı (endpoint, status) |
| `velox_elektraweb_duration_seconds` | Histogram | Elektraweb yanıt süresi |
| `velox_active_conversations` | Gauge | Aktif konuşma sayısı |
| `velox_db_pool_size` | Gauge | DB connection pool kullanımı |
| `velox_redis_connections` | Gauge | Redis bağlantı sayısı |

### 3.2 Metric kuralları

- Metric isimleri `velox_` prefix ile başlar
- Label'larda **asla PII olmaz** (telefon, isim vb.)
- Histogram bucket'ları: `[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0]`
- Prometheus scrape endpoint: `/metrics` (admin-only veya internal network)

---

## 4) Structured Logging (Yapılandırılmış Loglar)

### 4.1 Log formatı

Tüm loglar **JSON formatında** `structlog` ile yazılır.

```python
import structlog

logger = structlog.get_logger()

# Doğru kullanım
logger.info(
    "whatsapp_message_received",
    hotel_id=hotel_id,
    conversation_id=conversation_id,
    intent=detected_intent,
    message_length=len(message),
    # ⚠️ phone veya isim YAZILMAZ — security_privacy.md kuralı
)
```

### 4.2 Zorunlu log alanları (her log satırında)

| Alan | Açıklama |
|------|----------|
| `timestamp` | ISO 8601 formatı |
| `level` | info / warning / error / critical |
| `event` | Olay adı (snake_case) |
| `hotel_id` | Otel kimliği |
| `conversation_id` | Konuşma kimliği (varsa) |
| `request_id` | Tekil istek kimliği (tracing için) |
| `service` | Hangi modül (llm / elektraweb / whatsapp / db / qc) |
| `duration_ms` | İşlem süresi (varsa) |

### 4.3 Log seviyeleri

| Seviye | Ne zaman kullanılır? | Örnek |
|--------|---------------------|-------|
| `DEBUG` | Geliştirme detayı (production'da kapalı) | Template seçim detayı |
| `INFO` | Normal iş olayları | Mesaj alındı, yanıt gönderildi |
| `WARNING` | Dikkat gerektiren ama kırıcı olmayan | QC check yavaş, retry yapılıyor |
| `ERROR` | Başarısız işlem, fallback devrede | Elektraweb timeout, LLM hatası |
| `CRITICAL` | Sistem bütünlüğü tehlikede | DB bağlantısı kayıp, tüm retry'lar başarısız |

### 4.4 Asla loglanmayacaklar (security_privacy.md uyumu)

- Ham telefon numarası → `phone_hash` kullan
- Tam isim → `guest_id` veya maskelenmiş isim
- E-posta → maskelenmiş (`g***@example.com`)
- Kart/CVV/OTP → loglanmaz, `PAYMENT_DATA_DETECTED` flag'i yazılır
- API key / token / şifre → asla

---

## 5) Distributed Tracing (İz Takibi)

### 5.1 Neden gerekli?

Bir misafir mesajı şu yoldan geçer:
```
WhatsApp webhook → FastAPI → Session load (Redis) → LLM call (OpenAI)
→ Tool call (Elektraweb) → QC gate → Response format → WhatsApp send → DB log
```

Sorun olduğunda "nerede yavaşladı?" sorusunu cevaplamak için **her adım izlenmeli**.

### 5.2 Kurallar

- Her gelen HTTP isteğinde bir `request_id` (trace_id) oluşturulur
- Bu ID tüm alt çağrılara (span) geçirilir
- OpenTelemetry SDK kullanılır (vendor-agnostic)
- Span adlandırma: `velox.{service}.{operation}` (ör: `velox.llm.completion`, `velox.elektraweb.get_availability`)

### 5.3 Minimum span'ler

| Span | Parent | Ölçülen süre |
|------|--------|-------------|
| `velox.webhook.process` | Root | Tüm webhook işleme süresi |
| `velox.session.load` | webhook.process | Redis session yükleme |
| `velox.llm.completion` | webhook.process | OpenAI API çağrısı |
| `velox.tool.{tool_name}` | llm.completion | Her tool çağrısı |
| `velox.qc.gate` | webhook.process | QC gate toplam süresi |
| `velox.whatsapp.send` | webhook.process | WhatsApp mesaj gönderimi |
| `velox.db.log` | webhook.process | DB'ye log yazma |

---

## 6) Alerting (Uyarı Kuralları)

### 6.1 Alert seviyeleri

| Seviye | Anlamı | Bildirim kanalı | Beklenen aksiyon |
|--------|--------|-----------------|-----------------|
| 🔴 **CRITICAL** | Sistem ciddi şekilde etkilenmiş | Slack + SMS + Email | **Anında** müdahale |
| ⚠️ **WARNING** | Performans düşüyor veya eşik yaklaşıyor | Slack + Email | **1 saat** içinde incele |
| ℹ️ **INFO** | Bilgilendirme, dikkat gerektirmez | Slack (opsiyonel) | Günlük raporda incele |

### 6.2 Zorunlu alert kuralları

| Alert | Koşul | Seviye |
|-------|-------|--------|
| DB bağlantısı kayıp | Health check 2x üst üste fail | 🔴 CRITICAL |
| Redis bağlantısı kayıp | Health check 2x üst üste fail | 🔴 CRITICAL |
| WhatsApp gönderim başarısızlığı | Son 5dk'da %50+ fail oranı | 🔴 CRITICAL |
| LLM yanıt süresi yüksek | p95 > 15sn (5dk pencere) | ⚠️ WARNING |
| LLM hata oranı yüksek | Son 5dk'da %20+ fail | ⚠️ WARNING |
| Circuit breaker açıldı | Herhangi bir servis OPEN durumda | ⚠️ WARNING |
| QC gate yavaş | p95 > 500ms (5dk pencere) | ⚠️ WARNING |
| Handoff SLA aşımı | Herhangi bir ticket SLA'yı aştı | ⚠️ WARNING |
| Elektraweb yanıt yok | Circuit breaker OPEN + 5dk geçti | ⚠️ WARNING |
| Günlük mesaj hacmi anomali | Bugünkü hacim, son 7 gün ortalamasının 3x üstünde | ℹ️ INFO |

### 6.3 Alert kuralları

- Alert **tekrar tekrar tetiklenmez** — ilk tetiklemeden sonra **en az 15dk** sessizlik süresi (dedup)
- Alert çözüldüğünde **"resolved"** bildirimi gider
- Her alert'te şu bilgiler olmalı: metric adı, mevcut değer, eşik, etkilenen servis, önerilen aksiyon

---

## 7) Dashboard (Gösterge Paneli)

Admin panelde veya Grafana'da şu dashboard'lar olmalı:

### 7.1 Operasyonel Dashboard (Canlı)
- Aktif konuşma sayısı
- Son 1 saatte gelen/giden mesaj sayısı
- Sistem durumu (ok / degraded / down)
- Açık handoff ticket sayısı
- Circuit breaker durumları

### 7.2 Performans Dashboard
- Ortalama ve p95 yanıt süresi (son 24 saat)
- LLM token kullanımı (günlük/haftalık)
- QC gate süresi trendi
- Elektraweb yanıt süresi trendi

### 7.3 Hata Dashboard
- Hata oranı (son 24 saat, servis bazlı)
- Retry sayısı trendi
- Escalation dağılımı (L1/L2/L3)
- SLA aşım oranı

---

## 8) Kesin Yasaklar (Kırmızı Çizgiler)

- Log/metric/trace'de **PII olmaz** (telefon, isim, e-posta, kart) → security_privacy.md kuralı
- `print()` kullanılmaz → `structlog` kullan
- Metric label'larında kardinalite patlaması yok (ör: `phone_number` label'ı **yasak**)
- Alert spam yok → dedup süresi en az 15dk
- Health check endpoint'i iş mantığı çalıştırmaz (sadece bağlantı kontrolü)
- Production'da `DEBUG` seviye log **kapalı** olmalı

---

## 9) Validation Checklist

- [ ] `/health` endpoint'i var ve load balancer'a bağlı
- [ ] `/health/detailed` endpoint'i var ve admin-only
- [ ] PostgreSQL, Redis health check'leri 15sn aralıkla çalışıyor
- [ ] Tüm zorunlu metrikler tanımlı ve `/metrics` endpoint'inden erişilebilir
- [ ] Loglar JSON formatında, structlog ile yazılıyor
- [ ] Her log satırında zorunlu alanlar var (timestamp, level, event, hotel_id, request_id, service)
- [ ] Loglarda PII yok (phone_hash kullanılıyor)
- [ ] OpenTelemetry tracing entegre ve minimum span'ler tanımlı
- [ ] request_id tüm alt çağrılara geçiriliyor
- [ ] Alert kuralları tanımlı ve bildirim kanalları yapılandırılmış
- [ ] Alert dedup süresi en az 15dk
- [ ] Circuit breaker durumu metric olarak izlenebilir
- [ ] LLM token kullanımı izlenebilir
- [ ] Production'da DEBUG log kapalı
