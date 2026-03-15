# Skill: Error Handling (v2)

> **Hiyerarşi:** Bu dosya `SKILL.md` hiyerarşisinde **Öncelik 3** seviyesindedir.
> `security_privacy.md` ve `anti_hallucination.md` kuralları bu dosyadan önce gelir.

> Kod bilmeyen biri için kısa benzetme: Bu doküman, resepsiyondaki “Bir şey ters giderse ne yapacağız?” prosedürüdür.
> Telefon düşmezse 3 kere deneriz, yine olmazsa “konuyu ekibe devrediyoruz” deriz ve misafiri panikletmeyiz.

---

## Bu dokümanın amacı

- Misafir **hata görmesin** (teknik detay yok).
- Sistem **aynı hatayı sonsuza kadar tekrarlamasın** (kısır döngü yok).
- Ekip **hızlı teşhis** edebilsin (kayıtlar düzenli olsun).
- Bazı işler bozulsa bile sistem **kısmen çalışmaya devam etsin**.
- Hata teşhisi, retry/fallback/handoff kararı verilmeden önce Docker backend runtime doğrulansın.

### 0.1) Backend-first teşhis kapısı

Bir hata, timeout, bağlantı sorunu, regresyon veya "neden çalışmıyor?" durumu görüldüğünde:

1. Önce `docker compose ps` veya eşdeğeri ile `app`, `db`, `redis` ve ilgili yan servislerin durumunu kontrol et.
2. Healthcheck, restart loop, `unhealthy`/`restarting`/`exited` durumlarını ayır.
3. Container loglarını incele; hatanın uygulama mı, veritabanı mı, Redis mi, ağ mı, migration mı kaynaklı olduğunu daralt.
4. Env/config, volume, network, port, dependency readiness ve migration/schema uyumunu doğrula.
5. Bu doğrulama tamamlanmadan "geçici servis hatası", "retry ile düzelir", "sadece frontend sorunu" veya "model/prompt problemi" kararı verme.

> **Kural:** Retry/backoff politikası kör uygulanmaz. Önce backend runtime sağlığı doğrulanır; sistemik container/bağımlılık problemi varsa onu düzeltmeden tekrar deneme stratejisi ana çözüm gibi sunulmaz.

---

## 1) Temel akış: “Dene → Dene → Dene → Devret”

Bir dış servisle konuşurken (ör. Elektraweb / WhatsApp / OpenAI / veritabanı):

1. **1. deneme**
2. Olmazsa **kısa bekle** → **2. deneme**
3. Olmazsa **biraz daha bekle** → **3. deneme**
4. Hâlâ olmuyorsa:
   - Kendi kendine tekrar etmeyi bırak
   - Konuyu **insana devret (L2/OPS)**
   - Misafire **kısa, sakin** bir mesaj gönder

### Bekleme süreleri (standart)
- 1. deneme sonrası: **1 saniye**
- 2. deneme sonrası: **3 saniye**
- 3. deneme sonrası: **5 saniye**
- Toplam deneme: **en fazla 3** (sonsuz deneme yok)

> **Önemli:** Backend container'ı `unhealthy`, `restarting`, migration uyumsuz veya dependency bağlantısı kopuksa bu durum "geçici retry adayı" değil, önce runtime düzeltmesi gerektiren operasyonel arızadır.

---

## 2) Misafire ne yazılır?

### Altın kural: “İçeriyi gösterme”
Misafir **asla** şu şeyleri görmemeli:
- “500 hatası”, “404”, link/URL, teknik hata metni, veri tabanı hatası, sistem adı

Misafirin göreceği tek şey bunun gibi olmalı:

**TR örnek:**
> “Şu an sistemimizde geçici bir sorun yaşanmaktadır. Ekibimiz en kısa sürede sizinle ilgilenecektir.”

**EN örnek:**
> “We're experiencing a temporary issue. Our team will assist you shortly.”

> Not: Misafire “10 dakika içinde” gibi kesin süre verme. “En kısa sürede” de.

---

## 3) Hata türü: Ne zaman tekrar denemeli, ne zaman denememeli?

### Tekrar denemeye uygun (genelde geçici)
- Servis cevap vermedi / çok yavaş kaldı (zaman aşımı)
- Servis geçici olarak yoğun (ara sıra oluyor)

**Benzetme:** Telefon meşgulse tekrar ararsın.

### Tekrar denemeye uygun olmayan (genelde “yanlış bilgi/istek”)
- Misafir eksik bilgi verdi (tarih yok, kişi sayısı yok)
- Format yanlış (tarih anlaşılmıyor)

**Benzetme:** Yanlış numarayı 3 kere aramak çözmez; doğru numarayı istemek gerekir.

> Bu dokümanın “retry” kısmı esasen **servis hataları** içindir. Misafirden kaynaklı eksik/yanlış bilgi varsa, “soru sorup netleştirme” yapılır (anti_hallucination.md ile uyumlu).

---

## 4) Süre sınırları: “Çok uzarsa kes”

- Dış servis çağrıları: **10 saniye** içinde cevap gelmezse “başarısız” say
- LLM çağrıları: **30 saniye**
- Veritabanı sorguları: **5 saniye**

**Benzetme:** Müşteri beklerken resepsiyonun donması yerine, kısa sürede “ben bunu ekibe aktaracağım” demek.

---

## 5) Sürekli bozuluyorsa: “Sigorta atar” (Circuit breaker)

Eğer bir servis **60 saniye içinde 5+ kez** patlıyorsa:
- O servisi “şu an sorunlu” olarak işaretle (`TOOL_UNAVAILABLE`)
- Bir süre o servisi çağırmayı bırak (aynı duvara çarpmayı bırak)

### Circuit breaker durumları ve geçişleri

```
CLOSED (normal) ──5 hata/60sn──▶ OPEN (devre dışı)
                                     │
                                  30 sn bekle
                                     │
                                     ▼
                               HALF-OPEN (deneme)
                                   /        \
                              başarılı     başarısız
                                 │            │
                                 ▼            ▼
                              CLOSED        OPEN
                             (normal)    (tekrar bekle)
```

| Durum | Açıklama | Süre |
|-------|----------|------|
| **CLOSED** | Normal çalışma, tüm istekler gider | — |
| **OPEN** | Servis devre dışı, hiç istek gitmez, doğrudan fallback çalışır | **30 saniye** |
| **HALF-OPEN** | Tek bir deneme isteği gönderilir (sağlık kontrolü) | Tek istek |

- **OPEN → HALF-OPEN geçişi:** 30 saniye sonra otomatik (bu süre `settings.py`'dan gelir)
- **HALF-OPEN → CLOSED:** Deneme başarılıysa normal moda dön
- **HALF-OPEN → OPEN:** Deneme başarısızsa tekrar 30 sn bekle
- **Sağlık kontrolü:** HALF-OPEN'da gönderilen istek, gerçek bir kullanıcı isteğidir (ayrı health endpoint değil)

> **Kural:** Circuit breaker durumu **Redis'te** tutulur (tüm instance'lar görsün).
> Redis çökmüşse in-memory fallback kullanılır (instance-local).

**Benzetme:** Elektrik sigortası atınca 30 sn bekle, sonra bir kez dene, çalışıyorsa aç.

---

## 6) Kısmi çalışma: “Bazı hizmetler yürür, bazıları durur” (Graceful degradation)

Elektraweb çalışmıyorsa bile sistem şunları yapabilmeli:
- SSS / bilgi soruları
- Restoran rezervasyonu
- Transfer bilgisi
- Şikâyet kaydı
- İnsan devri (handoff)

Ama şunlar bloke olur:
- Oda müsaitliği
- Fiyat teklifi
- Rezervasyon oluşturma / değiştirme / iptal

**Benzetme:** Asansör bozulduysa merdivenle bazı işler yürür ama ağır eşya taşıma zorlaşır.

### 6.1 Cascading failure tablosu: “Bu çökerse ne olur?”

Her kritik bağımlılık için “çökerse ne olur, ne yapılır?” tablosu:

| Bağımlılık | Çökerse ne etkilenir? | Fallback | Misafire etki | Admin bildirim |
|------------|----------------------|----------|---------------|----------------|
| **Elektraweb** | Oda müsaitliği, fiyat teklifi, rezervasyon CRUD | SSS/restoran/transfer/handoff çalışır. Müsaitlik isteklerine: “Ekibimize iletiyorum.” | Kısmi — bilgi soruları çalışır | ⚠️ Hemen alert |
| **PostgreSQL (DB)** | Konuşma geçmişi, ticket, log yazma | In-memory queue → DB gelince replay. Yeni konuşmalar başlatılabilir ama geçmiş yüklenemez. | Yüksek — geçmiş kayıp riski | 🔴 Kritik alert |
| **Redis** | Session yönetimi, rate limiting, cache | In-memory dict fallback (tek instance, kısa ömürlü). Rate limiting gevşer. | Orta — session kayıp olabilir | ⚠️ Hemen alert |
| **OpenAI (LLM)** | Tüm akıllı yanıtlar, intent algılama | Template-only mod: misafir mesajına en yakın hazır şablonu gönder + insan devri. | Yüksek — sadece şablonlar çalışır | ⚠️ Hemen alert |
| **WhatsApp API** | Mesaj gönderimi | Mesajları kuyruğa al (DB/Redis), API gelince sırayla gönder. Gelen webhook'ları işlemeye devam et. | Çok yüksek — misafir cevap alamaz | 🔴 Kritik alert |
| **Redis + DB birlikte** | Neredeyse her şey | Sistemi **maintenance moduna** al. Tüm isteklere sabit mesaj: “Kısa süreliğine bakımdayız.” | Tam — sistem durur | 🔴 Acil müdahale |

> **Kural:** Her bağımlılık için fallback kodu **önceden yazılmış ve test edilmiş** olmalıdır.
> “Çökünce düşünürüz” yaklaşımı **yasaktır**.

**Benzetme:** Otelin acil durum planı: “yangın olursa hangi kapıdan çık, su kesilirse ne yap” — önceden planlanmış.

---

## 7) İçeride kayıt tutma: “Olay defteri” (Structured logging)

Her hata, ekip tarafından hızlı bulunabilsin diye standart bilgilerle kaydedilir:
- hata türü (error_type)
- hangi servis (elektraweb/whatsapp/openai/db)
- hotel_id
- conversation_id
- kaçıncı deneme (attempt_number)
- cevap kodu (response_code) *varsa*
- kaç ms sürdü (duration_ms)

**Benzetme:** Otel olay defterinde “ne oldu, nerede oldu, kaçıncı kez oldu” yazması gibi.

> Gizlilik: Kayıtlarda telefon/isim gibi kişisel veriler maskelenmeli (security_privacy.md ile uyumlu).

---

## 8) Devre (handoff) kuralları ve SLA

3 deneme bitti ve hâlâ sorun varsa:
- `TOOL_ERROR_REPEAT` risk işareti ekle
- L2/OPS ekibine ticket oluştur
- Misafire sakin mesaj dön

**Misafir ödeme ile ilgili bir şey söylerse** (örn. “USD ile ödeyeceğim”, “kart numaram...”) bu da riskli olduğundan:
- Teknik hata olmasa bile **insan devri** yapılmalı (security_privacy.md ve anti_hallucination kurallarıyla uyumlu)

### 8.1 Handoff SLA (Yanıt Süresi Taahhüdü)

İnsan devri yapıldığında misafir **cevapsız kalmamalıdır**.

| Escalation seviyesi | İlk yanıt süresi (SLA) | Takip mekanizması |
|---------------------|------------------------|-------------------|
| **L1** (genel sorular, bilgi) | **30 dakika** | 30 dk sonra admin'e hatırlatma |
| **L2** (ödeme, teknik hata, şikâyet) | **15 dakika** | 15 dk sonra hatırlatma, 45 dk sonra L3'e escalate |
| **L3** (hukuki, güvenlik, kriz) | **5 dakika** | 5 dk sonra hatırlatma, 15 dk sonra SUPER_ADMIN'e |

### 8.2 Follow-up mekanizması (otomatik hatırlatma)

İnsan devri sonrası **insan yanıt vermezse** sistem otomatik adım atar:

1. **SLA süresinin %100'ü dolduğunda:** Admin panelde + bildirim kanalında (Slack/email) hatırlatma
2. **SLA süresinin %300'ü dolduğunda:** Bir üst seviyeye escalation (L1→L2, L2→L3)
3. **SLA süresinin %500'ü dolduğunda:** Misafire proaktif mesaj gönder:
   - TR: “Talebiniz ekibimize iletildi. En kısa sürede sizinle iletişime geçilecektir. Anlayışınız için teşekkür ederiz.”
   - EN: “Your request has been forwarded to our team. We will contact you as soon as possible. Thank you for your patience.”

> **Kural:** Misafire proaktif mesaj **en fazla 1 kez** gönderilir (spam olmasın).
> Ticket kapatılana kadar admin panelde **açık** olarak görünür.

### 8.3 Ticket durumları

| Durum | Anlamı |
|-------|--------|
| `OPEN` | Oluşturuldu, henüz kimse yanıt vermedi |
| `IN_PROGRESS` | Ekip üyesi atandı / yanıt hazırlanıyor |
| `WAITING_GUEST` | Misafirden bilgi/onay bekleniyor |
| `RESOLVED` | Çözüldü, misafir bilgilendirildi |
| `EXPIRED` | SLA aşıldı, escalate edildi |

**Benzetme:** Otelde “şu misafirin talebi 15 dakikadır cevapsız — müdür devralıyor” sistemi.

---

## 9) Yasaklar (Kırmızı çizgiler)

- Sonsuz deneme yok → max 3
- Hataları “yutmak” yok → mutlaka kayda geç
- Misafire teknik detay yok
- Sistemi kilitleyen bekleme yok (bloklama yok)
- Docker backend runtime doğrulanmadan retry/fallback/root cause kararı kesinleştirmek yok

---

## 10) Kontrol listesi (Validation Checklist)

- [ ] Debug/RCA işlerinde önce `app`, `db`, `redis` ve ilgili yan servislerin container state, healthcheck, restart ve logları kontrol edildi
- [ ] Retry/fallback kararı vermeden önce env/config, network, port, readiness ve migration/schema uyumu doğrulandı
- [ ] Tüm dış çağrılar 3 deneme + 1/3/5 sn bekleme ile sarılı
- [ ] Tüm dış çağrılarda timeout var (10s), LLM (30s), DB (5s)
- [ ] 3 başarısızlıktan sonra `TOOL_ERROR_REPEAT` ekleniyor
- [ ] Misafir mesajında teknik kelime/kod yok
- [ ] Kayıtlar standart alanlarla tutuluyor (servis, hotel_id, attempt, duration)
- [ ] Elektraweb yokken SSS/restoran/transfer/handoff çalışıyor
- [ ] Sürekli bozulmada servis çağrısı kesiliyor (`TOOL_UNAVAILABLE`)
- [ ] Circuit breaker 3 durumlu (CLOSED/OPEN/HALF-OPEN) ve recovery süresi tanımlı (30sn)
- [ ] Her kritik bağımlılık için cascading failure fallback'i yazılmış ve test edilmiş
- [ ] DB çökünce in-memory queue + replay mekanizması var
- [ ] Redis çökünce in-memory dict fallback var
- [ ] LLM çökünce template-only mod + insan devri çalışıyor
- [ ] Handoff SLA süreleri tanımlı (L1: 30dk, L2: 15dk, L3: 5dk)
- [ ] Handoff follow-up otomatik hatırlatması aktif
- [ ] Ticket durumları (OPEN/IN_PROGRESS/WAITING_GUEST/RESOLVED/EXPIRED) takip ediliyor

---


---

## 11) Karar tablosu: “Tekrar dene mi, soru sor mu, devret mi?”

> Amaç: Aynı durumda herkes aynı kararı versin.

Aşağıdaki tabloyu “resepsiyon aklı” gibi düşünün:

| Durum (Ne oldu?) | Misafirden mi kaynaklı? | Ne yapacağız? | Misafire ne yazacağız? |
|---|---:|---|---|
| Servis cevap vermiyor / zaman aşımı | Hayır | 1/3/5 sn bekleyerek **3 kez dene**. Olmazsa **insan devri**. | “Şu an yardımcı olamıyorum. Konuyu ekibimize iletiyorum; en kısa sürede dönüş yapılacak.” |
| Servis “geçici yoğun” gibi davranıyor | Hayır | **3 kez dene**. Olmazsa **insan devri**. | Aynı |
| Servis “yetkisiz/anahtar hatası” (izin sorunu) | Hayır | **Tekrar deneme** (boşa). **Hemen insan devri**. | “Sizi ilgili ekibe yönlendiriyorum.” |
| Veritabanı yavaş / bağlantı kopuk | Hayır | 1/3/5 sn ile **3 kez dene**. Olmazsa **insan devri**. | “Şu an talebinizi tamamlayamıyorum. Konuyu ekibimize iletiyorum; en kısa sürede dönüş yapılacak.” |
| Mesaj çok uzun / format bozuk (tarih anlaşılmıyor) | Evet | **Tekrar deneme yok.** Misafirden **net bilgi iste**. | “Tarihleri gün/ay/yıl şeklinde yazar mısınız?” |
| Eksik bilgi var (tarih yok, kişi sayısı yok) | Evet | **Soru sor**, netleştir. | “Giriş-çıkış tarihlerini ve yetişkin sayısını paylaşır mısınız?” |
| Misafir “ödeme yapacağım / para birimi / kart” dedi | Karma/Risk | **Hemen insan devri** (hata olmasa bile). | “Ödeme/para birimi konusunda sizi ilgili ekibe yönlendiriyorum.” |
| Misafir kart bilgisi/OTP yazdı (yanlışlıkla) | Riskli | **Hemen insan devri** + “buraya yazmayın” uyarısı | “Güvenliğiniz için kart/OTP bilgisi paylaşmayınız. Sizi ekibe yönlendiriyorum.” |
| Aynı servis 60 sn’de 5+ kez patlıyor | Hayır | Servisi **TOOL_UNAVAILABLE** yap, bir süre çağırma, **degrade** moduna geç | “Geçici sorun var…” + gerekiyorsa “ekibe yönlendirdim” |

---

## 12) Misafir mesaj şablonları (hazır cümleler)

> Haklısınız: Misafire “iç sistem / servis / çekmek / otomatik” gibi ifadeler **fazla teknik** kalır.
> Bu şablonlarda şu kelimeler **kullanılmaz**: “sistem”, “servis”, “Elektraweb”, “WhatsApp”, “otomatik”, “veritabanı”, “timeout”, “hata kodu”.

Kural: Kısa, sakin, çözüm odaklı. Ya **bilgi iste** ya da **insan devri** yap.

### 12.1 Genel gecikme / şu an tamamlayamama
**TR**
- “Şu an talebinizi hemen sonuçlandıramıyorum. Konuyu ekibimize iletiyorum; en kısa sürede size dönüş yapılacak.”
- “Kısa bir gecikme için kusura bakmayın. Ekibimiz sizinle en kısa sürede iletişime geçecek.”

**EN**
- “I can’t finalize your request right now. I’m forwarding it to our team and they will get back to you shortly.”
- “Sorry for the delay. Our team will contact you as soon as possible.”

### 12.2 Bilgi eksikse (misafirden net bilgi isteme)
**TR**
- “Yardımcı olabilmem için giriş ve çıkış tarihlerinizi (gün/ay/yıl) ve yetişkin sayısını paylaşır mısınız?”
- “Çocuk varsa yaşlarını da yazar mısınız?”

**EN**
- “To assist you, could you share your check-in/check-out dates (day/month/year) and number of adults?”
- “If there are children, please share their ages as well.”

### 12.3 Mesajlaşma gecikmesi (yanıt gecikebilir)
**TR**
- “Mesajınızı aldım. Yanıtım kısa süre gecikebilir; ekibimiz en kısa sürede size dönüş yapacak.”
- “Sizi ilgili ekibe yönlendiriyorum; en kısa sürede iletişime geçecekler.”

**EN**
- “I received your message. My reply may be slightly delayed; our team will get back to you shortly.”
- “I’m forwarding your request to the relevant team; they will contact you shortly.”

### 12.4 İşlem tamamlanamadı (herhangi bir nedenle)
**TR**
- “Talebinizi şu an tamamlayamadım. Konuyu ekibimize iletiyorum; en kısa sürede sizinle iletişime geçecekler.”
- “İşlemi tamamlamak için ekibimize devrediyorum.”

**EN**
- “I couldn’t complete your request at the moment. I’m forwarding it to our team and they will contact you shortly.”
- “I’m handing this over to our team to complete the request.”

### 12.5 Ödeme / para birimi konuşulursa (her durumda insan devri)
**TR**
- “Ödeme ve para birimi konularında sizi ilgili ekibe yönlendiriyorum. En kısa sürede sizinle iletişime geçecekler.”
- (Misafir kart/OTP yazdıysa) “Güvenliğiniz için kart/OTP bilgisi paylaşmayınız. Sizi ilgili ekibe yönlendiriyorum.”

**EN**
- “For payment and currency matters, I’m forwarding your request to our team. They will contact you shortly.”
- (If card/OTP was shared) “For your security, please do not share card/OTP details. I’m forwarding this to our team.”



## (Mühendis Notu) Örnek Şablonlar

> Bu bölüm kod bilmeyenler için şart değil; ama ekip için “hazır parça” gibi.

- Retry/backoff şablonu
- Timeout wrapper
- Degrade kontrolü
- Misafir hata mesajı sözlüğü
