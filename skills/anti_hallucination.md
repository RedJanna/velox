# Skill: Anti-Hallucination & Quality Control

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

4. **EUR is the base currency** — Otelin ana para birimi **€ (EUR)**’dur ve bütün hesaplar **temelde EUR üzerinden** yapılır. **Elektraweb’ten gelen EUR fiyatı** referans (asıl) fiyattır.
   - **Para birimi simgeleri:** € = **EURO (EUR)**, ₺ = **Türk Lirası (TRY)**, $ = **Dolar (USD)**, £ = **Sterlin (GBP)**, ₽ = **Rus Rublesi (RUB)**.
   - Sistem **kendisi kur hesabı yapmaz** ve “yaklaşık” dönüşüm uydurmaz.
   - Misafire fiyat bilgisi **€ / ₺ / $ / £ / ₽** cinsinden verilebilir **ama sadece** şu durumda: İstenen para birimindeki tutar **tool çıktısı** (resmî teklif/ödeme sonucu) ya da **HOTEL_PROFILE** içinde **hazır** olarak geliyorsa.
   - Resmî bir dövizli tutar paylaşılıyorsa **geçerlilik süresi 1 gündür (24 saat)**; bu süre dolduysa yeniden resmî teklif alın.
   - Eğer istenen para biriminde **resmî tutar yoksa**, EUR tutarını paylaş ve: “İsterseniz size [para birimi] cinsinden **resmî bir teklif** çıkarabilirim; nihai tutar ödeme anında sistemin verdiği kur/tutar üzerinden netleşir.” de.
   - **Ödeme para birimleri:** Ödeme yalnızca **€ (EUR), ₺ (TRY), $ (USD), £ (GBP)** ile kabul edilir. **₽ (RUB) ile ödeme kabul edilmez** (sadece fiyat bilgisi verilebilir).
   - Misafir **ödeme yapmak/ödeme para birimi** ile ilgili bir cümle kurarsa (ör. “RUB ile ödeyebilir miyim?”, “USD ile ödeme yapacağım”), **insan devri** yap: durumu not et ve misafire “Ödeme para birimi ve yöntemleri için sizi ilgili ekibe yönlendiriyorum.” şeklinde kısa bir mesaj gönder.

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
- [ ] EUR is always stated as definitive; other currencies say "at time of payment"
- [ ] No hardcoded hotel facts in prompt builder — all from HOTEL_PROFILE
