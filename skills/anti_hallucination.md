# Skill: Anti-Hallucination & Quality Control

> **Hiyerarşi:** Bu dosya `SKILL.md` hiyerarşisinde **Öncelik 2** seviyesindedir.
> Sadece `security_privacy.md` bu dosyanın kurallarını geçersiz kılabilir.
> Diğer tüm skill dosyaları, `system_prompt_velox.md` ve task talimatları bu kurallara tabidir.

## 0) Kapsam ve çalışma notları

- **Kapsam:** LLM yanıt kuralları, kaynak doğrulama, QC gate ve şablon önceliği
- **İlişkili dosyalar:** `security_privacy.md`, `whatsapp_format.md`, `error_handling.md`, `docs/master_prompt_v2.md`
- **Temel ilke:** Kanıtsız iddia yok; doğrulanmayan bilgi ya net şekilde belirsiz diye işaretlenir ya da insan devrine alınır

---

## 1) Kurallar

1. **Kaynak hiyerarşisi** — LLM, "tesis gerçeği" sayılabilecek bilgileri yalnızca şu kaynaklardan ve şu öncelik sırasıyla kullanabilir:
   - (1) Tool çıktıları (availability, quote, reservation, approval, payment sonuçları)
   - (2) `HOTEL_PROFILE` (admin tarafından yönetilen otel verisi)
   - (3) Enjekte edilen alt belgeler: `FACILITY_POLICIES`, `FAQ_DATA`, `TEMPLATE_LIBRARY`, `SCENARIO_PLAYBOOK`, `ESCALATION_MATRIX`
   - Kaynak yoksa **uydurma yapma**. "Bunu doğrulamam gerekiyor" de veya handoff kaydı aç.

2. **Önce şablon kullan** — Serbest metin üretmeden önce `TEMPLATE_LIBRARY` şablonlarını kullan. Şablon seçimi `intent + language + state` ile yapılır. Değişkenler yalnızca tool veya `HOTEL_PROFILE` verisiyle doldurulur. Uygun şablon yoksa kısa serbest metin üretilebilir; ama kaynak kuralları yine geçerlidir.

3. **Her yanıt öncesi QC gate çalıştır** — Çıktı üretmeden önce şu 7 kontrol içerden çalıştırılır:
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

5. **İnternet varsayımı yapma** — Runtime sırasında LLM internet erişimine sahip değildir. "Web sitesine göre" deme ve `HOTEL_PROFILE` dışında harici URL referansı verme.

6. **Menü/yemek bilgisi uydurma** — Menü, yemek, tatlı, içecek önerisi YALNIZCA `HOTEL_PROFILE.restaurant.menu` kataloğundan verilebilir. Katalog boşsa veya tanımlı değilse: "Güncel menümüz hakkında sizi restoranımız veya resepsiyon ile yönlendirebilirim" de. LLM eğitim verisinden yemek/tatlı/içecek önerisi üretmek **kesinlikle yasaktır**. Bu kural, fiyat için `booking.quote` gerektirmesi ile aynı seviyededir.

7. **Tool'suz fiziksel operasyon taahhüdü verme** — "Hazırlıyorum", "gönderiyorum", "sipariş alıyorum" gibi fiziksel işlem taahhüdü ancak ilgili tool (ör. `room_service.create_order`) başarıyla çağrıldıktan sonra verilebilir. Tool çağrılmadan taahhüt vermek halüsinasyon olarak değerlendirilir ve `PHYSICAL_OPERATION_REQUEST` risk flag'i tetikler.

## Kalıp Örnekler

### System prompt birleştirme (`prompt_builder.py`)
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

### QC kontrol implementasyonu
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

### Şablon seçimi
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

## Kesin Yasaklar

- `booking.quote` tool çıktısı gelmeden fiyat söyleme
- `booking.availability` tool çıktısı gelmeden müsaitlik söyleme
- `HOTEL_PROFILE` dışında otel özelliği, imkan veya politika uydurma
- Kur hesaplama veya tahmini döviz dönüşümü yapma
- "Web sitesine göre" diyerek harici veri kaynağı referansı verme
- QC gate'i atlama; kontrol fail ederse soru sor, tool çağır veya escalate et
- Uygun şablon varken uzun serbest metin üretme
- Kesin süre verme; "10 dakika içinde" yerine "en kısa sürede" de
- `HOTEL_PROFILE.restaurant.menu` kataloğu olmadan menü/yemek/tatlı/içecek önerisi yapmak
- `room_service.create_order` tool çağrılmadan oda servisi siparişi taahhüt etmek
- Herhangi bir tool çağrılmadan fiziksel operasyon ("hazırlatıyorum", "gönderiyorum") taahhüdü vermek
- Menü kataloğunda olmayan ürünleri (LLM eğitim verisinden) önermek

## Kontrol Listesi

- [ ] System prompt içinde `HOTEL_PROFILE` ve `FACILITY_POLICIES` var
- [ ] Gösterilen her fiyat bir `booking.quote` tool çağrısına dayanıyor
- [ ] Her müsaitlik iddiası bir `booking.availability` tool çağrısına dayanıyor
- [ ] QC1-QC7 kontrolleri implement edildi ve her yanıt öncesi çalışıyor
- [ ] Serbest metin üretmeden önce şablon seçimi deneniyor
- [ ] Uygun şablon bulunmazsa `TEMPLATE_MISSING` risk flag'i loglanıyor
- [ ] EUR her zaman referans fiyat olarak gösteriliyor; diğer para birimleri "ödeme anında kur" notu ile
- [ ] Tanınan para birimi tablosundaki kategorilere uygun davranılıyor (ödeme destekli vs sadece bilgi vs tanınmayan)
- [ ] Tanınmayan para birimlerinde EUR fiyat + bilgilendirme yapılıyor (insan devri yok)
- [ ] Ödeme desteklenmeyen para biriminde ödeme konuşması → insan devri
- [ ] Prompt builder içinde hardcoded otel bilgisi yok; her şey `HOTEL_PROFILE` üzerinden geliyor
- [ ] QC check'ler `asyncio.gather` ile paralel çalışıyor (seri değil)
- [ ] QC gate toplam süresi ≤500ms (logda `qc_duration_ms` alanı var)
- [ ] QC fail durumunda öncelik sırası uygulanıyor (Security > Escalation > Policy > Source > Intent > Format > Session)
- [ ] Tek QC check timeout'u tanımlı (500ms) ve `QC_TIMEOUT` flag'i loglanıyor
- [ ] Menü/yemek/tatlı önerisi yapılmadan önce `HOTEL_PROFILE.restaurant.menu` kataloğu kontrol ediliyor
- [ ] Menü kataloğu boşsa LLM serbest menü önerisi üretmiyor; misafiri restorana/resepsiyona yönlendiriyor
- [ ] Oda servisi siparişi `room_service.create_order` tool çağrısı olmadan taahhüt edilmiyor
- [ ] Fiziksel operasyon taahhüdü ("hazırlatıyorum", "gönderiyorum") tool çağrısı olmadan verilmiyor
- [ ] `response_validator` toolless commitment pattern'ı yakalıyor ve güvenli handoff mesajına çeviriyor
- [ ] `vegan` / `vegetarian` anahtar kelimeleri `ALLERGY_ALERT` risk flag'ini tetikliyor
- [ ] Her sipariş/oda servisi talebi CHEF + OPS rollerine `notify.send` ile bildiriliyor
- [ ] `PHYSICAL_OPERATION_REQUEST` ve `MENU_HALLUCINATION_RISK` risk flag'leri escalation matrix'te tanımlı
