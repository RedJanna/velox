# Skill: Error Handling (v2)

> Kod bilmeyen biri için kısa benzetme: Bu doküman, resepsiyondaki “Bir şey ters giderse ne yapacağız?” prosedürüdür.
> Telefon düşmezse 3 kere deneriz, yine olmazsa “konuyu ekibe devrediyoruz” deriz ve misafiri panikletmeyiz.

---

## Bu dokümanın amacı

- Misafir **hata görmesin** (teknik detay yok).
- Sistem **aynı hatayı sonsuza kadar tekrarlamasın** (kısır döngü yok).
- Ekip **hızlı teşhis** edebilsin (kayıtlar düzenli olsun).
- Bazı işler bozulsa bile sistem **kısmen çalışmaya devam etsin**.

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
- Sonraki sağlık kontrolünde düzelirse tekrar dene

**Benzetme:** Elektrik sigortası atınca aynı anda tekrar tekrar açmaya çalışmazsın.

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

## 8) Devre (handoff) kuralları

3 deneme bitti ve hâlâ sorun varsa:
- `TOOL_ERROR_REPEAT` risk işareti ekle
- L2/OPS ekibine ticket oluştur
- Misafire sakin mesaj dön

**Misafir ödeme ile ilgili bir şey söylerse** (örn. “USD ile ödeyeceğim”, “kart numaram...”) bu da riskli olduğundan:
- Teknik hata olmasa bile **insan devri** yapılmalı (security_privacy.md ve anti_hallucination kurallarıyla uyumlu)

---

## 9) Yasaklar (Kırmızı çizgiler)

- Sonsuz deneme yok → max 3
- Hataları “yutmak” yok → mutlaka kayda geç
- Misafire teknik detay yok
- Sistemi kilitleyen bekleme yok (bloklama yok)

---

## 10) Kontrol listesi (Validation Checklist)

- [ ] Tüm dış çağrılar 3 deneme + 1/3/5 sn bekleme ile sarılı
- [ ] Tüm dış çağrılarda timeout var (10s), LLM (30s), DB (5s)
- [ ] 3 başarısızlıktan sonra `TOOL_ERROR_REPEAT` ekleniyor
- [ ] Misafir mesajında teknik kelime/kod yok
- [ ] Kayıtlar standart alanlarla tutuluyor (servis, hotel_id, attempt, duration)
- [ ] Elektraweb yokken SSS/restoran/transfer/handoff çalışıyor
- [ ] Sürekli bozulmada servis çağrısı kesiliyor (`TOOL_UNAVAILABLE`)

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
