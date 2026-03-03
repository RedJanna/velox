# Skill: Testing & Quality Assurance (v2)

> Kod bilmeyen biri için benzetme: Bu doküman “**prova planı**”dır.
> - **Kısa prova (mutfak tadımı):** Tek bir yemeği (tek bir fonksiyonu) deneriz.
> - **Genel prova (salonda prova):** Birkaç ekip birlikte çalışır (mesaj akışı).
> - **Açılış provası (tam gerçeklik):** Misafirin gerçekten yaşayacağı yol gibi deneriz (staging/E2E).

Bu dokümanın amacı: Sistem değişince “bozuldu mu?” sorusunu **risksiz, hızlı ve gerçeğe yakın** şekilde yanıtlamak.

---

## 0) Önemli ayrım: “Sahte (simülasyon) test” + “Gerçeklik (E2E) test”

Bu projede iki tip test var ve ikisi de gerekli:

1) **Otomatik testler (CI’da çalışır):**
   - Hızlıdır, güvenlidir
   - Dış dünyayı **taklit eder** (Elektraweb/WhatsApp/OpenAI/DB gibi)
   - Amaç: Her kod değişikliğinde hemen hata yakalamak

2) **Gerçeğe dayalı tam akış testleri (Staging/E2E):**
   - Misafirin yaşayacağı yolun **aynısı** denenir
   - Gerçek sistemlere mümkün olduğunca bağlanır (test hesaplarıyla)
   - Amaç: “Sahada çalışır mı?” riskini azaltmak

> Kural: CI testlerinde **asla** gerçek dış servisler çağrılmaz.
> Gerçek çağrılar sadece **staging ortamında**, **test hesaplarıyla** ve **ayrı bir E2E test paketiyle** yapılır.

---

## Rules (Kurallar)

1. **Test every public function** — tools/, adapters/, core/, escalation/, policies/ altındaki her “dışa açık” fonksiyon en az 1 test alır.
2. **Async test support** — `pytest-asyncio` kullan. Async kodu test eden testler `async def` olmalı (`asyncio_mode = "auto"`).
3. **Mock external services in CI** — CI/unit/integration testlerinde gerçek API çağrısı yok.
   - Mock: Elektraweb (httpx), WhatsApp (httpx), OpenAI (client), PostgreSQL (asyncpg pool), Redis (aioredis).
4. **Arrange-Act-Assert** — Hazırla → Çalıştır → Kontrol et. Her test tek davranışı ölçsün.
5. **Test file naming** — `tests/unit/test_{module_name}.py`
6. **Fixture hierarchy** — Ortak fixture: `tests/conftest.py`, modül özel fixture: ilgili test dosyası.
7. **Coverage target** — Genel minimum %80; kritik yollar (escalation, payment, approval) %95+.
8. **Scenario tests** — S001–S047 senaryolarının her biri en az 1 “akış testi” ile doğrulanmalı.
9. **Edge cases matter** — Boş giriş, aşırı uzun giriş, geçersiz tarih, negatif sayı, eksik alan, eşzamanlı istek, timeout, hata akışları.
10. **No test pollution** — Testler sıraya bağlı olmayacak; her test kendi kurar/kendi toplar.

---

## 1) Test katmanları (Ne zaman hangisini kullanırız?)

### 1.1 Unit test (Tek parça testi)
**Ne test eder?** Tek bir fonksiyonun doğru çalışması.  
**Benzetme:** Şefin sosu kaşıkla tadıp “tadı doğru mu?” demesi.

- Çok hızlı
- Dış dünya yok (tamamen simülasyon)

### 1.2 Integration test (Birlikte çalışma testi – kontrollü)
**Ne test eder?** Birkaç parçanın birlikte çalışması (pipeline, policy + escalation).  
**Benzetme:** Mutfak + servis birlikte prova yapar ama restoran kapalıdır.

- Dış servisler yine simüle edilir
- Akış “gerçeğe yakın” ama güvenli

### 1.3 E2E / Staging test (Gerçeğe dayalı tam akış)
**Ne test eder?** Misafirin yaşayacağı uçtan uca deneyim.  
**Benzetme:** Açılış provası: Gerçek menü, gerçek masa, gerçek servis.

- Sadece **staging** ortamında
- Sadece **test hesapları** ve **sahte misafir verisi** ile
- Üretim (production) verisi/numarası kullanılmaz

---

## 2) “Bazı durumlar devre dışı ve olmuş gibi yapılmalı” (Simülasyon anahtarları)

Bazı senaryoları gerçek hayatta yakalamak zordur (servis çökmesi gibi).
Bu yüzden **kontrollü simülasyon** gerekir.

### 2.1 Simülasyon ne zaman gerekli?
- Elektraweb “çökmüş gibi” davranma
- WhatsApp “mesaj gönderemiyor gibi” davranma
- OpenAI “gecikiyor/yanıt vermiyor gibi” davranma
- DB “timeout veriyor gibi” davranma
- “Ödeme konuşuldu” gibi riskli durumlarda **insan devri** tetikleme

### 2.2 Simülasyon nasıl yapılmalı? (gerçeğe benzer)
- Simülasyon, gerçek sistemin vereceği çıktıyı **taklit etmeli**
- “Uydurma” değil, mümkünse **daha önce görülen gerçek çıktılara** benzemeli
- Simülasyon açıkken test çıktısı “simülasyon” diye işaretlenmeli

### 2.3 Örnek simülasyon anahtarları (öneri)
- `SIMULATE_ELEKTRAWEB_DOWN=1`
- `SIMULATE_WHATSAPP_SEND_FAIL=1`
- `SIMULATE_LLM_TIMEOUT=1`
- `SIMULATE_DB_TIMEOUT=1`
- `SIMULATE_PAYMENT_INTENT=1` (payment konuşulursa insan devri akışı)

> Güvenlik: Simülasyon anahtarları üretimde **kapalı** olmalı.
> CI ve staging’de kontrollü şekilde açılır.

---

## 3) “Tamamen gerçeğe dayalı yol” nasıl test edilir?

### 3.1 Staging/E2E test prensipleri
- Mesajlar **gerçek hayattaki gibi** atılır: “Merhaba, 15-18 Temmuz 2 kişi…”
- Sistem, aynı kurallarla cevap verir (WhatsApp formatı, handoff vb.)
- Kullanılan veriler **sahte/anonim** olmalı (gerçek isim/telefon/kart yok)

### 3.2 Gerçek sistemlere bağlanma kuralı
- **WhatsApp:** staging’e bağlı test numarası ile
- **Elektraweb:** mümkünse test oteli / sandbox / kopya ortam
- **DB/Redis:** staging DB (ayrı)
- **Ödeme:** Bu projede ödeme otomatik değilse “gerçek yol”, zaten **insan devri**dir.
  - E2E testte amaç: “Ödeme konuşulursa doğru şekilde insan devri oluyor mu?” kontrolü.

### 3.3 “Gerçeklik testi” kabul kriterleri (örnek)
- S001: Selamlama → tarih/kişi → müsaitlik → teklif → onay → hold
- S024/S029 gibi kritik senaryolarda “risk flag → doğru escalation → ticket” oluşuyor mu?
- WhatsApp mesajı kurallara uyuyor mu (kısa paragraf, tek mesaj, net seçenekler)
- Hata olursa misafire teknik bilgi sızmıyor mu?

### 3.4 Gerçekçi test için ek kurallar (staging/E2E’yi “saha gibi” yapmak)

Bu bölüm, “gerçeğe dayalı test” kısmını daha da sağlamlaştırır.

- **Test verisi kataloğu (hazır sahte misafirler):**  
  10–20 adet sahte misafir profili (isim/telefon sahte), 10–20 tarih aralığı, 3–5 farklı kişi kombinasyonu (2 yetişkin, 2+1 çocuk vb.).  
  Amaç: Her test aynı düzenli veriyle çalışsın, sürpriz olmasın.

- **Staging ortamı temizliği (her koşu öncesi):**  
  Test koşusu başlamadan staging DB’de “test konuşmaları / test hold’lar” temizlenir ya da “test_run_id” ile izole edilir.  
  Amaç: Dün kalan test bugün sonucu bozmasın.

- **Elektraweb test kaynağı kuralı:**  
  Mümkünse **test oteli/sandbox** kullan; değilse “gerçek otelde” test yapıyorsan tarih aralıkları “her zaman müsait olan” özel test aralıkları olmalı.  
  Amaç: Müsaitlik dalgalanması yüzünden testler yalancı kırılmasın.

- **Gerçekçilik ölçümü (başarı kriteri):**  
  Test, sadece “çalıştı” demesin; şu 4 şeyi ölçsün:  
  1) Doğru intent/state/risk_flag  
  2) WhatsApp formatı (tek mesaj, kısa paragraf, net seçenek)  
  3) Teknik kelime sızmıyor mu?  
  4) Ödeme/currency gibi risklerde insan devri oluyor mu?

---

---

## 4) Dil stratejisi: Testler Türkçe yazılır, diğer dillere LLM ile uyarlanır (hız için)

> Hedef: Test yazma ve çalıştırma süresi **hızlı** olsun.
> Bu yüzden “tek kaynak dil” seçiyoruz: **Türkçe**.

### 4.1 Neden Türkçe “tek kaynak” iyi?
- Senaryoları bir kez yazarsın (S001–S047 gibi), tekrar tekrar çoğaltmazsın.
- Hataları tek yerde düzeltirsin.
- Test paketi daha hızlı büyür (kopyala-yapıştır karmaşası olmaz).

### 4.2 Diğer diller nasıl test edilecek? (LLM çeviri katmanı)
Diğer diller için iki adım kullanılır:

1) **Girdi çevirisi:** Türkçe test mesajları, hedef dile LLM ile çevrilir.
2) **Çıktı değerlendirme:** Dil bağımsız kriterlerle yapılır:
   - intent/state/risk_flag gibi **iç JSON** doğru mu?
   - WhatsApp format kuralları (tek mesaj, kısa paragraflar, numaralı seçenek) doğru mu?
   - “Teknik bilgi sızmıyor mu?”, “ödeme konuşulunca insan devri var mı?” gibi davranışlar doğru mu?

> Önemli: “Beklenen metin birebir aynı olsun” yerine, **beklenen davranış** test edilir.
> Böylece çeviri küçük farklılıklar üretse bile testler kırılmaz.

### 4.3 Hız + stabilite için kurallar (LLM ile çeviri testleri)
LLM çevirisi testlerde hızlı olmalı ama “rastgelelik” testleri bozmasın. Bu yüzden:

- **Çeviri sonuçlarını cache’le (kaydet):**
  - İlk çalıştırmada TR → EN/DE/RU/AR vb. çevirileri üret
  - Sonraki çalıştırmalarda aynı senaryo için aynı çeviriyi kullan (dosyadan/fixture’dan)
- **Çeviri için deterministik ayarlar:**
  - temperature = 0
  - mümkünse “translation only” sistem mesajı
- **Çeviri testleri iki seviyeli:**
  1) **Hızlı paket (PR/CI):** Sadece Türkçe + çeviri katmanı unit testleri
  2) **Diller smoke paketi (Nightly/Release):** Her dilden 3–5 kritik senaryo (S001, S024, S029 gibi)

### 4.4 Minimum dil testi planı (öneri)
- **CI/Her PR (en hızlı):**
  - Türkçe senaryoların tamamı
  - Çeviri fonksiyonu için 10 kısa cümlelik golden test (TR→X)
- **Nightly (günlük):**
  - EN/DE/RU/AR: her dilden 3 kritik senaryo
- **Release öncesi:**
  - Hedef pazarlara göre her dilden 5–10 senaryo + 1 E2E akış

### 4.5 Çeviri kuralları (kalite)
- Tarih/sayı/para birimi gibi şeyler **bozulmamalı**
- Özel isimler ve oda tipleri korunmalı
- “Ödeme” gibi riskli kelimeler doğru çevrilmeli (handoff tetikleniyor mu?)


---

## 5) “Gelişmiş Test” butonu fikri (eğitim/ayar sonrası hızlı problem yakalama)

Fikriniz çok iyi: Sistem “eğitildikten” veya prompt/şablonlar güncellendikten sonra **tek tuşla** test koşsun, sorunları bulsun.

Buradaki kritik nokta: “bulur” kısmı otomatik olabilir; “düzeltir” kısmı ise **kontrollü** olmalı (insan onayıyla).  
Çünkü otomatik düzeltme, yanlış bir değişiklik yapıp yeni bir hatayı doğurabilir.

### 5.1 Buton 3 modda çalışmalı (hız + gerçekçilik dengesi)

1) **Hızlı (1–3 dk) — PR/CI modu**  
   - Türkçe senaryoların kritik 10’u (S001, S017, S024, S029, S047…)  
   - Simülasyon anahtarlarıyla “servis çöktü” testleri  
   - Çıktı: “Geçti/Kaldı” + hangi senaryoda kaldı

2) **Orta (5–15 dk) — Regresyon modu**  
   - Türkçe senaryoların büyük kısmı + edge-case  
   - LLM çeviri katmanı testleri (cache’li)  
   - Çıktı: Hata listesi + öneri (hangi kural bozulmuş: format mı, handoff mu, kaynak mı?)

3) **Tam Gerçek (staging/E2E) — Release modu**  
   - Test numarasıyla gerçek mesaj akışı  
   - Mümkünse Elektraweb test kaynağı  
   - Çıktı: Kabul kriterlerine göre rapor + kayıt (transkript)

### 5.2 Buton “sorunu nasıl raporlayacak?”
Her başarısız test için tek sayfalık rapor üretmeli:

- Senaryo kodu (S0xx)
- Misafir mesajları (transkript)
- Sistem cevabı (misafire giden mesaj)
- İç karar (intent/state/risk_flag/hand-off oldu mu?)
- Hangi kural kırıldı? (örn. “tek mesaj” kuralı, “ödeme → insan devri” kuralı)
- Önerilen aksiyon: “template güncelle”, “policy fix”, “handoff koşulu ekle” gibi

### 5.3 “Düzeltme” nasıl olmalı? (güvenli yaklaşım)
- **Otomatik düzeltme yok** (varsayılan).  
- Sistem sadece **öneri** çıkarır ve bir “değişiklik paketi” hazırlar.  
- İnsan onayıyla uygulanır (PR gibi düşünebilirsiniz).

> Eğer yine de otomatik düzeltme isterseniz, bunu sadece “risk olmayan” küçük şeylerle sınırlayın:
> - yazım/format şablonu seçimi
> - mesajın çok uzunsa kısaltma
> - yanlış dil seçimini düzeltme  
> “Politika/ödeme/rezervasyon” gibi kritik konular otomatik düzeltilmemeli.



### 5.4 Rapor formatını netleştirelim (tek sayfalık “denetim raporu”)

> Benzetme: Bu rapor, oteldeki **günlük denetim formu** gibi olmalı.  
> “Nerede kaldı? Ne bozuldu? Misafire yansıdı mı? Ne yapacağız?” sorularına 1 dakikada cevap vermeli.

#### 5.4.1 Raporun 2 katmanı olmalı
1) **Özet (1 sayfa):** Yönetici bakıp hemen karar versin.  
2) **Detay (kanıt):** Ekip “nereden düzelteceğini” anlasın.

---

### 5.5 Özet rapor şablonu (1 sayfa)

**A) Koşu bilgisi**
- Run ID: `TR-2026-03-03-001`
- Mod: `Hızlı / Orta / Tam Gerçek`
- Ortam: `CI / Staging`
- Sürüm: `app_version`, `prompt_version`, `policy_version`
- Dil: `TR kaynak` + test edilen diller (örn. EN/DE/RU/AR)
- Simülasyonlar: Açık olan anahtarlar (örn. `SIMULATE_ELEKTRAWEB_DOWN=1`)

**B) Sonuç özeti**
- Toplam senaryo: 47  
- Geçen: 44  
- Kalan: 3  
- Bloklanan: 0 (dış bağımlılık nedeniyle)  
- Kritik (Release’i durdurur): 1

**C) “Release kapısı” kararı**
- ✅ Yayınlanabilir / ⚠️ Şartlı / ❌ Yayınlanamaz
- Neden? (1–3 maddede)

**D) En önemli 5 bulgu (kısa)**
Her bulgu satırı şu formatta:
- `[Kritik/Orta/Düşük] S029 – Ödeme konuşulunca insan devri olmadı → Misafire yanlış yönlendirme riski`
- `[Orta] S001 – WhatsApp formatı: tek mesaj kuralı bozuldu (2 ayrı mesaj)`

**E) Hızlı aksiyon listesi**
- A1) Handoff kuralı: “payment/currency” tetiklenince insan devri zorunlu (owner: Ops)  
- A2) Mesaj birleştirme: tek mesaj kuralı (owner: Dev)

---

### 5.6 Senaryo bazlı detay kartı (fail olunca)

> Bu kart, her kalan senaryo için 1 tane üretilir. Ama **tek sayfaya sığacak** kadar kısa tutulur.  
> Kanıt gerekiyorsa “Ekler” kısmına gider.

**1) Kimlik**
- Senaryo: `S029`
- Önem: `Kritik / Orta / Düşük`  
- Etkilenen dil: `TR` (veya `EN`)

**2) Amaç**
- “Misafir ödeme para birimi sorarsa insan devri yapılmalı.”

**3) Test girdisi (misafirin yazdığı)**
- TR: “USD ile ödeme yapabilir miyim?”
- (Varsa çeviri): EN: “Can I pay in USD?”

**4) Sistem çıktısı (misafire giden)**
- Tek mesaj mı? ✅/❌  
- Metin: “...”

**5) İç karar (misafir görmez, ekip için)**
- Intent: `payment_question`
- Risk flag: `PAYMENT_INTENT`
- Action: `handoff.create_ticket` ✅/❌

**6) Hangi kural kırıldı? (işaretle)**
- [ ] WhatsApp formatı  
- [ ] Anti-hallucination (kaynak dışı bilgi)  
- [ ] Security/Privacy (kart/OTP uyarısı, masking)  
- [ ] Error handling (insan devri / retry)  
- [ ] Currency/Payment policy

**7) Kanıt**
- Transkript (kısa): 3–8 satır  
- Log referansı: `conversation_id`, `request_id` (varsa)

**8) Muhtemel sebep (kategori)**
- `Template` / `Policy` / `Tool Adapter` / `Data` / `Translation`

**9) Önerilen düzeltme (1–3 adım)**
- “payment/currency tespiti → her durumda handoff”
- “misafir mesaj şablonunu sadeleştir”

**10) Tekrar test planı**
- Hızlı mod: S029 + S024  
- Orta mod: TR tüm kritik senaryolar

---

### 5.7 (Opsiyonel) Raporu makineye uygun saklama (mühendis notu)

Raporun bir de “sistemin anlayacağı” formatı olursa, zamanla otomasyon çok kolaylaşır.  
Öneri: Her koşuda bir `report.json` üret.

**Örnek alanlar (kısa)**
- `run_id`, `mode`, `environment`, `app_version`, `policy_version`, `prompt_version`
- `languages_tested`, `simulation_flags`
- `summary`: `total`, `passed`, `failed`, `blocked`, `critical_failed`
- `failures[]`:  
  - `scenario_id`, `severity`, `language`, `input_messages[]`, `output_message`,  
  - `internal`: `{intent, state, risk_flags[], actions[]}`,  
  - `violations[]`, `evidence`: `{conversation_id, request_id}`,  
  - `suggested_fixes[]`

> Not: Bu JSON’u üretmek, “Gelişmiş Test butonu”nu gelecekte çok daha akıllı hale getirir (trend takibi, otomatik ticket, regression haritası).

## Patterns (Örnekler)

### Basic unit test
```python
import pytest
from velox.config.constants import EscalationLevel, RiskFlag
from velox.escalation.engine import EscalationEngine

@pytest.fixture
def engine(escalation_matrix):
    return EscalationEngine(matrix=escalation_matrix)

async def test_legal_request_triggers_l3(engine):
    result = engine.evaluate(risk_flags=[RiskFlag.LEGAL_REQUEST])
    assert result.level == EscalationLevel.L3
    assert "handoff.create_ticket" in result.actions
    assert result.route_to_role == "ADMIN"
```

### Mocking Elektraweb adapter
```python
from unittest.mock import AsyncMock

@pytest.fixture
def mock_elektraweb():
    client = AsyncMock()
    client.get_availability.return_value = {
        "available": True,
        "rows": [{"room_type_id": 66, "room_type": "PREMIUM", "room_to_sell": 3}],
    }
    return client
```

### Scenario test structure
```python
class TestScenarioS001HotelReservation:
    """Full flow: greeting → dates → availability → quote → confirm → hold."""

    async def test_step1_greeting(self, pipeline):
        response = await pipeline.process("Merhaba, oda bakmak istiyorum")
        assert "hosgeldiniz" in response.user_message.lower()
        assert response.internal_json.intent == "stay_availability"
```

---

## Prohibitions (Yasaklar)

- **CI/unit/integration testlerinde** gerçek dış servis çağrısı YASAK.
- Test sırasına bağlılık YASAK.
- `time.sleep()` YASAK (async uyumlu bekleme kullan).
- Hata akışlarını atlamak YASAK (timeout, fail, invalid input test edilecek).
- Fixture yerine rastgele hardcode test verisi YASAK.
- 30 satırı aşan test YASAK (böl).

> Not: Staging/E2E testleri bu yasaktan ayrı bir pakettir. Orada “gerçek bağlantılar” **izinli** olabilir ama sadece test hesaplarıyla.

---

## Validation Checklist

### CI (Günlük/Her PR)
- [ ] `pytest` sıfır hata
- [ ] Coverage %80+ (kritikler %95+)
- [ ] Tüm dış servisler mock (gerçek çağrı yok)
- [ ] Edge-case testleri var
- [ ] En az 10 senaryo akış testi var (S001, S024, S029, S017, S047)

### Staging / E2E (Release öncesi)
- [ ] Test numarası ile gerçek mesaj akışı çalışıyor
- [ ] Elektraweb/test kaynakları ile teklif akışı çalışıyor (mümkünse)
- [ ] Ödeme konuşulunca insan devri + ticket oluşuyor
- [ ] Misafir mesajlarında teknik kelime yok
- [ ] Simülasyon anahtarları üretimde kapalı
- [ ] Dil stratejisi: TR senaryolar + LLM çeviri cache (stabil) + dillerde smoke test
- [ ] (Öneri) “Gelişmiş Test” butonu: hızlı/orta/tam mod + rapor üretimi + release öncesi zorunlu

