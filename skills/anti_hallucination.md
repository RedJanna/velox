# Skill: Anti-Hallucination & Quality Control

> **Hiyerarşi:** Bu dosya `SKILL.md` hiyerarşisinde **Öncelik 2** seviyesindedir.
> Sadece `security_privacy.md` bu dosyanın kurallarını geçersiz kılabilir.
> Diğer tüm skill dosyaları, `system_prompt_velox.md` ve task talimatları bu kurallara tabidir.

## Rules

1. **Source hierarchy** — The LLM may only state "facility facts" from these sources, in priority order:
   - (1) Tool outputs (availability, quote, reservation, approval, payment results)
   - (2) HOTEL_PROFILE (admin-managed hotel data)
   - (3) Injected sub-documents: FACILITY_POLICIES, FAQ_DATA, TEMPLATE_LIBRARY, SCENARIO_PLAYBOOK, ESCALATION_MATRIX
   - If no source exists: do NOT fabricate. Say "I need to verify this" or open a handoff ticket.

2. **Template-first** — Use TEMPLATE_LIBRARY templates before generating free text. Select template by: intent + language + state. Fill variables only from TOOL or HOTEL_PROFILE data. If no template matches: generate short premium text, but still obey source rules.

3. **QC gate before every response** — Run these 7 checks internally before producing output:
   - QC1: Intent & entity extraction — are critical fields missing?
   - QC2: Source check — is every claim backed by TOOL/HOTEL_PROFILE/POLICY?
   - QC3: Policy gate — do cancel/prepayment/approval rules match A9?
   - QC4: Security — am I requesting unnecessary PII or payment data?
   - QC5: WhatsApp format — short message, clear options, no overload?
   - QC6: Escalation gate — any risk_flags? Is L1/L2/L3 needed?
   - QC7: Session gate — is conversation still active? Is context consistent?

   **QC gate performans bütçesi:**

   > ⚠️ QC gate misafir yanıt süresini şişirmemeli. Toplam bütçe: **maksimum 500ms**.

   | Kontrol | Maks. süre | Yöntem | Paralel mi? |
   |---------|-----------|--------|-------------|
   | QC1: Intent/entity | 50ms | In-memory regex + dict lookup | ✅ Evet |
   | QC2: Source check | 100ms | Response text vs kaynak karşılaştırma | ✅ Evet |
   | QC3: Policy gate | 50ms | Policy rules dict lookup | ✅ Evet |
   | QC4: Security | 50ms | PII/payment pattern regex | ✅ Evet |
   | QC5: Format | 30ms | Length + structure check | ✅ Evet |
   | QC6: Escalation | 50ms | Risk flag evaluation | ✅ Evet |
   | QC7: Session | 50ms | Redis session check | ✅ Evet |
   | **Toplam (paralel)** | **≤ 150ms** | `asyncio.gather` ile paralel | — |
   | **Toplam (seri, worst case)** | **≤ 500ms** | Fallback: Redis yavaşsa | — |

   **Kurallar:**
   - QC check'leri **`asyncio.gather`** ile paralel çalıştırılır (seri değil)
   - Tek bir QC check 500ms'yi aşarsa → o check **timeout** olur ve `QC_TIMEOUT` risk flag'i eklenir
   - QC gate toplamı 500ms'yi aşarsa → yanıt yine gönderilir ama `QC_SLOW` uyarısı loglanır
   - QC check'ler **LLM çağrısı yapmaz** — sadece in-memory/Redis operasyonları

   **QC fail durumunda öncelik sırası:**
   1. QC4 (Security) fail → **hemen insan devri** (bekleme yok)
   2. QC6 (Escalation) fail → **risk seviyesine göre** L1/L2/L3 devri
   3. QC3 (Policy) fail → **yanıtı düzelt** veya insan devri
   4. QC2 (Source) fail → **tool çağır** veya "doğrulamam gerekiyor" de
   5. QC1 (Intent) fail → **misafire soru sor** (netleştirme)
   6. QC5 (Format) fail → **yanıtı yeniden formatla** (otomatik)
   7. QC7 (Session) fail → **session'ı yenile** veya yeni konuşma başlat

4. **EUR is the base currency** — Otelin ana para birimi **€ (EUR)**’dur ve bütün hesaplar **temelde EUR üzerinden** yapılır. **Elektraweb’ten gelen EUR fiyatı** referans (asıl) fiyattır.

   ### 4.1 Tanınan para birimleri

   | Kategori | Para birimleri | Fiyat gösterimi | Ödeme kabul |
   |----------|---------------|-----------------|-------------|
   | **Birincil** | € EUR | ✅ Her zaman (referans) | ✅ Evet |
   | **Ödeme destekli** | ₺ TRY, $ USD, £ GBP | ✅ Tool/HOTEL_PROFILE verisi varsa | ✅ Evet |
   | **Sadece bilgi** | ₽ RUB | ✅ Tool/HOTEL_PROFILE verisi varsa | ❌ Hayır |
   | **Tanınan ama resmî teklif yok** | د.إ AED, ر.س SAR, CHF, SEK, NOK, DKK, PLN, CZK, ILS, CNY, JPY, KRW, INR, BRL, ZAR, AUD, CAD, NZD, HKD, SGD, THB, MYR, IDR, PHP, EGP, QAR, BHD, KWD, OMR | ❌ Resmî teklif çıkartılamaz | ❌ Hayır |

   ### 4.2 Temel kurallar

   - Sistem **kendisi kur hesabı yapmaz** ve “yaklaşık” dönüşüm uydurmaz.
   - Misafire fiyat bilgisi **sadece** şu durumda verilebilir: İstenen para birimindeki tutar **tool çıktısı** (resmî teklif/ödeme sonucu) ya da **HOTEL_PROFILE** içinde **hazır** olarak geliyorsa.
   - Resmî bir dövizli tutar paylaşılıyorsa **geçerlilik süresi 1 gündür (24 saat)**; bu süre dolduysa yeniden resmî teklif alın.

   ### 4.3 Bilinen para biriminde resmî tutar yoksa

   EUR tutarını paylaş ve misafirin diline uygun şablonu kullan:

   - **TR:** “Fiyatımız *[tutar] EUR*’dur. İsterseniz size [para birimi] cinsinden resmî bir teklif çıkarabilirim; nihai tutar ödeme anında sistemin verdiği kur üzerinden netleşir.”
   - **EN:** “The rate is *[amount] EUR*. I can prepare an official quote in [currency] if you’d like; the final amount will be based on the exchange rate at the time of payment.”
   - **RU:** “Стоимость составляет *[сумма] EUR*. Могу подготовить официальное предложение в [валюта]; окончательная сумма определяется по курсу на момент оплаты.”
   - **DE:** “Der Preis beträgt *[Betrag] EUR*. Gerne erstelle ich Ihnen ein offizielles Angebot in [Währung]; der endgültige Betrag richtet sich nach dem Wechselkurs zum Zeitpunkt der Zahlung.”

   ### 4.4 Tanınmayan para birimi istenirse

   Misafir tabloda **hiç olmayan** bir para biriminden bahsederse:
   - EUR fiyatını paylaş
   - “Bu para biriminde resmî teklif çıkarma imkânımız bulunmuyor. Fiyatlarımız EUR bazlıdır.” de
   - İnsan devri **gerekmez** (sadece bilgilendirme yeterli)

   ### 4.5 Ödeme para birimi konuşmaları → İnsan devri

   - **Ödeme para birimleri:** Ödeme yalnızca **€ (EUR), ₺ (TRY), $ (USD), £ (GBP)** ile kabul edilir.
   - **₽ (RUB) ile ödeme kabul edilmez** (sadece fiyat bilgisi verilebilir).
   - **Tanınan ama ödeme desteklenmeyen** para birimlerinde (AED, SAR, CHF vb.) ödeme kabul edilmez.
   - Misafir **ödeme yapmak / ödeme para birimi** ile ilgili bir cümle kurarsa (ör. “RUB ile ödeyebilir miyim?”, “AED ile ödeme yapacağım”), **insan devri** yap: durumu not et ve misafire “Ödeme para birimi ve yöntemleri için sizi ilgili ekibe yönlendiriyorum.” şeklinde kısa bir mesaj gönder.
   - **İstisna:** EUR, TRY, USD, GBP ile ödeme konuşmaları normal akışta devam eder (insan devri gerekmez, ödeme tool’u kullanılır).

5. **No internet assumptions** — The LLM does not have internet access during runtime. Never say "according to the website" or reference external URLs not in HOTEL_PROFILE.

## Patterns

### System prompt assembly (prompt_builder.py)
```python
def build_system_prompt(
    hotel_profile: HotelProfile,
    escalation_matrix: list[EscalationMatrixEntry],
    conversation_history: list[Message],
    active_scenario: dict | None = None,
) -> str:
    """
    Assemble system prompt layers:
    1. Master prompt A-section (role, rules, tone)
    2. HOTEL_PROFILE (dynamic hotel data)
    3. FACILITY_POLICIES (from hotel profile)
    4. FAQ_DATA (from hotel profile)
    5. ESCALATION_MATRIX (risk flag rules)
    6. Active scenario context (if detected)
    7. TEMPLATE_LIBRARY subset (relevant templates)
    8. Conversation summary + recent messages
    """
```

### QC check implementation
```python
class QualityControl:
    def run_all_checks(self, response: LLMResponse, context: ConversationContext) -> QCResult:
        results = [
            self._qc1_intent_entities(response, context),
            self._qc2_source_check(response, context),
            self._qc3_policy_gate(response, context),
            self._qc4_security(response),
            self._qc5_format(response),
            self._qc6_escalation(response, context),
            self._qc7_session(context),
        ]
        failed = [r for r in results if not r.passed]
        return QCResult(passed=len(failed) == 0, failures=failed)
```

### Template selection
```python
def select_template(
    intent: str, language: str, state: str, templates: list[Template]
) -> Template | None:
    """Find best matching template. Returns None if no match (free text fallback)."""
    for t in templates:
        if t.intent == intent and t.state == state and language in t.languages:
            return t
    # Fallback: match by intent + language only
    for t in templates:
        if t.intent == intent and language in t.languages:
            return t
    return None  # Log TEMPLATE_MISSING risk flag
```

## Prohibitions

- **NEVER** state a price that did not come from `booking.quote` tool output.
- **NEVER** state room availability that did not come from `booking.availability` tool output.
- **NEVER** invent hotel features, amenities, or policies not in HOTEL_PROFILE.
- **NEVER** calculate or estimate currency exchange rates.
- **NEVER** say "according to the website" or reference external data sources.
- **NEVER** skip the QC gate — if any check fails, ask a question, call a tool, or escalate.
- **NEVER** generate long free text when a matching template exists.
- **NEVER** promise specific timelines ("you'll hear back in 10 minutes") — say "as soon as possible."

## Validation Checklist

- [ ] System prompt includes HOTEL_PROFILE and FACILITY_POLICIES
- [ ] Every price shown to user traces back to a `booking.quote` tool call
- [ ] Every availability claim traces back to a `booking.availability` tool call
- [ ] QC1-QC7 checks are implemented and run before every response
- [ ] Template selection is attempted before free text generation
- [ ] TEMPLATE_MISSING risk flag is logged when no template found
- [ ] EUR her zaman referans fiyat olarak gösteriliyor; diğer para birimleri "ödeme anında kur" notu ile
- [ ] Tanınan para birimi tablosundaki kategorilere uygun davranılıyor (ödeme destekli vs sadece bilgi vs tanınmayan)
- [ ] Tanınmayan para birimlerinde EUR fiyat + bilgilendirme yapılıyor (insan devri yok)
- [ ] Ödeme desteklenmeyen para biriminde ödeme konuşması → insan devri
- [ ] No hardcoded hotel facts in prompt builder — all from HOTEL_PROFILE
- [ ] QC check'ler `asyncio.gather` ile paralel çalışıyor (seri değil)
- [ ] QC gate toplam süresi ≤500ms (logda `qc_duration_ms` alanı var)
- [ ] QC fail durumunda öncelik sırası uygulanıyor (Security > Escalation > Policy > Source > Intent > Format > Session)
- [ ] Tek QC check timeout'u tanımlı (500ms) ve `QC_TIMEOUT` flag'i loglanıyor
