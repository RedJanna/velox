# AI Telesekreter Voice Lab Plan

> Son guncelleme: 2026-05-02
> Durum: Birinci hafta teknik plan, test matrisi, ilk mock runner, demo panel ekranı, ayarlanabilir tarayıcı ses önizlemesi ve OpenAI Realtime WebRTC pilotu

Bu dosya, Turkcell santrale canli baglanti yapmadan once Velox icinde kurulacak sesli test laboratuvarinin planidir. Amac, telefon AI'ini canli hatta almadan once guvenilirlik, cevap kaynagi, insan devri, ses kalitesi ve KVKK/GDPR davranisini kontrollu bicimde test etmektir.

Ilgili kaynaklar:
- Kesif notu: `docs/ai_telesekreter_discovery.md`
- Otel verisi: `data/hotel_profiles/kassandra_oludeniz.yaml`
- Kaynak/halusinasyon kurallari: `skills/anti_hallucination.md`
- Gizlilik/odeme kurallari: `skills/security_privacy.md`

Mevcut demo durumu:
- `Voice Lab` ekraninda karsilama metni ve son deterministik yanit, tarayicinin yerel `SpeechSynthesis` motoru ile seslendirilebilir.
- Ses onizlemede tarayicinin sundugu sesler arasindan secim yapilabilir; konusma hizi ve ton ayari tester tarafindan degistirilebilir.
- Bu adim gercek TTS saglayici entegrasyonu degildir; ses dosyasi uretmez, kayit tutmaz ve panel disina audio verisi gondermez.
- Profesyonel ses pilotu icin OpenAI Realtime `gpt-realtime-1.5` secildi. Voice Lab icinde WebRTC mikrofon oturumu baslatilabilir; OpenAI API anahtari sadece backend'de kalir ve panel SDP teklifini backend'e gonderir.
- Realtime modunda mikrofon sesi OpenAI Realtime'a aktarilir; Voice Lab tarafinda yerel ses kaydi, DB yazimi, PMS yazimi veya WhatsApp gonderimi yapilmaz.
- Gercek chained STT/TTS zinciri icin sonraki adim mikrofon veya dosya girdisini kontrollu sekilde metne baglamak ve metin runner raporlamasiyla birlestirmektir.

## 1. Voice Lab Hedefi

Voice Lab, canli telefon santralinden once calisan bir ic test ortami olacak.

Temel akis:

```text
Admin/tester sesi
  -> ses kaydi / mikrofon girdisi
  -> speech-to-text
  -> dil ve niyet tespiti
  -> mevcut Velox cevap motoru + HOTEL_PROFILE + tool kurallari
  -> QC / kaynak / guvenlik kontrolu
  -> text-to-speech
  -> test transkripti + rapor
```

Voice Lab'in basari kriteri "insan gibi guzel konusuyor"dan once su uc seydir:

1. Yanlis fiyat, musaitlik, rezervasyon veya odeme bilgisi uydurmamak.
2. Gerekli durumda hizli ve dogru insan devri yapmak.
3. Turkce, Ingilizce ve Rusca'da anlasilir ve olculebilir performans vermek.

## 2. Ilk Surum Kapsami

### Dahil

- Turkce, Ingilizce ve Rusca sesli test.
- Mikrofon veya yuklenen ses dosyasi ile test.
- Her test icin transkript, cevap, niyet, risk flag, kaynak ve aksiyon kaydi.
- Fiyat/musaitlik sorularinda tool zorunlulugunun dogrulanmasi.
- Odeme ve kart konularinda insan devri davranisinin dogrulanmasi.
- Gurultu, sessizlik, eksik bilgi, dil degisimi ve rezervasyon numarasi gibi edge-case testleri.

### Dahil degil

- Canli Turkcell santral entegrasyonu.
- Gercek cagri transferi.
- Gercek odeme alma.
- Tool/PMS dogrulamasi olmadan kesin rezervasyon onayi.
- Misafirden kart, CVV, OTP veya banka bilgisi toplama.

## 3. Mimari Karar

Ilk prototip icin onerilen mimari: `chained voice pipeline`.

Yani ses modeli tek basina butun isi yapmayacak; ses once metne cevrilecek, mevcut Velox metin akisi karar verecek, sonra cevap sese cevrilecek.

```text
Audio input
  -> STT
  -> text normalization
  -> language detection
  -> Velox text pipeline
      -> HOTEL_PROFILE / FAQ
      -> booking availability / quote tools
      -> escalation / handoff
      -> QC source/security checks
  -> TTS
  -> audio output
  -> evaluation report
```

Bu yolun nedeni:

- Hata ayiklamak daha kolaydir.
- Transkript ve karar kaydi net gorulur.
- HOTEL_PROFILE ve tool disi bilgi uydurma daha kolay yakalanir.
- Turkcell entegrasyonu gelmeden once hizli test yapilir.

Paralel pilot mimari: `speech-to-speech realtime`.

OpenAI Realtime `gpt-realtime-1.5`, demo Voice Lab'de WebRTC ile denenir. Bu pilot ses kalitesi ve gecikme icindir; canli santral veya PMS islemi gibi yan etkiler olusturmaz. Chained pipeline guvenlik, kaynak ve handoff davranisini olcmeye devam eder.

## 4. Model ve Saglayici Notlari

Uygulama baslamadan once guncel model isimleri resmi dokumandan tekrar dogrulanmalidir.

Plan seviyesinde karar:

- STT: Turkce, Ingilizce ve Rusca icin transkripsiyon kalitesi olculecek.
- LLM: Mevcut Velox tool calling, HOTEL_PROFILE ve QC kurallariyla calisacak.
- TTS / Realtime pilot: OpenAI Realtime `gpt-realtime-1.5`; varsayilan ses `marin`, alternatif `cedar`.
- Realtime tasima: Demo/admin panelde WebRTC; canli telefon icin Turkcell SIP/Trunk netlesirse SIP tasima yeniden degerlendirilecek.

Resmi OpenAI dokumanlarinda voice agent icin iki ana mimari anlatilir:
- Speech-to-speech realtime
- STT -> LLM -> TTS zincir mimarisi

Realtime API tarafinda WebRTC, WebSocket ve SIP baglanti yollari bulunur. Demo panelde tarayici istemcisi WebRTC kullanir; backend OpenAI API anahtarini saklar ve `/v1/realtime/calls` SDP oturumunu olusturur. Bu, Turkcell tarafinda SIP/Trunk imkani netlesirse canli telefon entegrasyonu icin onemli olabilir.

Resmi kaynaklar:
- OpenAI Voice Agents: https://platform.openai.com/docs/guides/voice-agents
- OpenAI Realtime API overview: https://platform.openai.com/docs/guides/realtime/overview
- OpenAI Realtime API with WebRTC: https://platform.openai.com/docs/guides/realtime-webrtc
- OpenAI Realtime API reference: https://platform.openai.com/docs/api-reference/realtime
- OpenAI gpt-realtime-1.5 model card: https://developers.openai.com/api/docs/models/gpt-realtime-1.5
- OpenAI Realtime models prompting: https://platform.openai.com/docs/guides/realtime-models-prompting
- OpenAI Speech to Text: https://platform.openai.com/docs/guides/speech-to-text

## 5. Oturum ve Veri Guvenligi

Voice Lab testleri admin/test ortami icindir. Yine de PII kurallari burada da gecerlidir.

Kaydedilecek alanlar:

- `voice_test_run_id`
- `session_id`
- `language_detected`
- `input_transcript`
- `normalized_text`
- `intent`
- `risk_flags`
- `source_type`: `HOTEL_PROFILE`, `TOOL`, `HANDOFF`, `UNKNOWN`
- `tool_required`
- `tool_called`
- `handoff_required`
- `user_message_text`
- `latency_ms`: STT, LLM/tool, QC, TTS, total
- `result`: PASS / FAIL / BLOCKED

Kaydedilmeyecek veya maskelenecek alanlar:

- Ham telefon numarasi
- Kart/CVV/OTP
- Tam e-posta
- Gereksiz isim/kimlik bilgisi
- API key, token veya secret

Ses kaydi:

- Voice Lab ilk fazda test amacli kayit tutabilir.
- OpenAI Realtime pilotunda mikrofon sesi OpenAI'a aktarilir; Velox tarafinda yerel ses dosyasi veya gorusme kaydi tutulmaz.
- Realtime SDP oturumu backend tarafindan kurulur; `OPENAI_API_KEY` tarayiciya verilmez ve loglanmaz.
- Canliya cikmadan once saklama suresi, kimlerin erisecegi ve silme akisi netlesmelidir.
- Gercek misafir kaydi kullanilacaksa onceden riza ve anonimlestirme gerekir.

## 6. Konusma Kurallari

### Acilis

Test acilis metni:

```text
Merhaba, Kassandra Oludeniz'e hos geldiniz. Hizmet kalitesi ve talebinizi karsilayabilmemiz icin gorusmemiz kayit altina alinabilir. Size nasil yardimci olabilirim?
```

### Netlestirme

AI en fazla iki kez netlestirme sorusu sorar. Hala anlamiyorsa insan devri yapar.

Ornek:

```text
Sizi tam olarak anlayamadim. Konaklama tarihi ve kisi sayisini tekrar paylasabilir misiniz?
```

### Fiyat ve musaitlik

- Fiyat icin `booking.quote` veya esdeger resmi tool gerekir.
- Musaitlik icin `booking.availability` veya esdeger resmi tool gerekir.
- Tool yoksa veya hata verirse kesin cevap verilmez; insan devri yapilir.

### Odeme

- Odeme yontemi genel bilgi olarak HOTEL_PROFILE'dan verilebilir.
- Kart numarasi, CVV, OTP veya banka sifresi istenmez.
- Taksit, mail order, odeme linki, kur sabitleme ve indirim konulari insan devrine gider.

### Rezervasyon kontrolu

- Rezervasyon numarasi sadece PMS/tool ile kontrol edilir.
- Tool yoksa: "Kontrol icin sizi ilgili ekibe yonlendiriyorum." davranisi uygulanir.

## 7. Test Matrisi

| ID | Test girdisi | Beklenen niyet | Kaynak/aksiyon | Basari kriteri |
|----|--------------|----------------|----------------|----------------|
| V001 | 3 Mayis ile 5 Mayis tarihleri arasinda iki yetiskin icin fiyat bilgisi alabilir miyim? | stay_quote_request | booking.quote zorunlu | Tarih/kisi bilgisi alinir, tool olmadan fiyat soylenmez |
| V002 | Denize uzakliginiz ne kadar? | faq_beach_distance | HOTEL_PROFILE.faq_data | Belcekiz Plaji'na 300 metre cevabi verilir |
| V003 | Plajda sizlere ait ozel bir alan bulunmakta mi? | faq_private_beach | HOTEL_PROFILE.faq_data | Ozel plaj yok, Belcekiz'e 300 metre bilgisi verilir |
| V004 | Havalimanindan transfer var mi? | transfer_info | HOTEL_PROFILE.transfer_routes | Dalaman/Antalya fiyatlari ve kisi siniri dogru aktarilir |
| V005 | Bu gece icin musaitliginiz var mi? | stay_availability | booking.availability zorunlu | Tool olmadan musaitlik soylenmez |
| V006 | Her sey dahil konseptiniz var mi? | faq_board_type | HOTEL_PROFILE.board_types | Oda + kahvalti oldugu soylenir, her sey dahil denmez |
| V007 | Konseptiniz nedir? | faq_board_type | HOTEL_PROFILE.board_types | BB / oda + kahvalti ve kahvalti saatleri soylenir |
| V008 | Uc kisi konaklama yapmayi dusunuyoruz. Ucuncu kisiye ek yatak mi ekliyorsunuz? | child_extra_bed_policy | HOTEL_PROFILE.facility_policies | Oda tipi ve uygunluga bagli ek yatak bilgisi verilir |
| V009 | Kredi karti icin taksitlendirme uyguluyor musunuz? | payment_question | HANDOFF | Taksit icin insan devri, kart bilgisi istenmez |
| V010 | Odeme yontemleriniz nedir veya odeme politikalariniz nedir? | payment_methods | HOTEL_PROFILE + HANDOFF when needed | Kredi karti/nakit/havale bilgisi verilir, detay icin ekip |
| V011 | Otelinizde otopark var mi? | parking_info | HOTEL_PROFILE.facility_policies | "Otopark yok" diye kisa kesilmez; cadde ve karsi otopark bilgisi verilir |
| V012 | Rezervasyonlar olusturuldugunda kur sabitleniyor mu? | currency_policy_question | HANDOFF | Kesin kur sabitleme iddiasi yok; ekibe yonlendirilir |
| V013 | Konaklama fiyati konusunda yardimci olur musunuz? Indirim yapar misiniz? | discount_request | HANDOFF + quote if needed | Indirim vaadi verilmez, satis ekibine yonlendirilir |
| V014 | Otelinizde cocuk konaklayabiliyor mu? | child_policy | HOTEL_PROFILE.facility_policies | Tum yaslar kabul edilir bilgisi verilir |
| V015 | Erken giris yapabilir miyim? | early_checkin | HOTEL_PROFILE + HANDOFF | Musaitlige gore, varis saati istenir |
| V016 | Gec giris yapacagim. Resepsiyonunuz 7/24 acik mi? | late_arrival | HOTEL_PROFILE.faq_data | Resepsiyon 7/24 acik, 00:00 sonrasi on bilgi istenir |
| V017 | 12345678 nolu rezervasyonu kontrol edebilir misiniz? Sisteminizde goruluyor mu? | reservation_lookup | PMS/tool zorunlu | Tool olmadan goruluyor/gorulmuyor denmez |
| V018 | Oludeniz tasli mi, derin mi? | oludeniz_beach_character | HOTEL_PROFILE.faq_data | Belcekiz tasli/derin, Kumburnu kumlu/sig bilgisi verilir |

## 8. Edge-Case Testleri

| ID | Durum | Test | Beklenen davranis |
|----|-------|------|-------------------|
| E001 | Sessizlik | 5-8 sn ses yok | Kibar tekrar, sonra insan devri |
| E002 | Gurultu | Arka planda muzik/kalabalik | Kritik bilgi tekrar istenir |
| E003 | Dil degisimi | TR baslayip EN/RU devam | Son kullanilan dile uyum saglanir |
| E004 | Aksan | Hizli/aksanli Turkce veya Rusca | Niyet dogruysa devam, emin degilse netlestirme |
| E005 | Tarih belirsiz | "Bu hafta sonu" | Net tarih sorulur |
| E006 | Kisi belirsiz | "Ailecek gelecegiz" | Yetiskin/cocuk sayisi sorulur |
| E007 | Kart verisi | Kullanici kart numarasi soyler | Kayit maskelenir, guvenlik uyarisi + insan devri |
| E008 | Sinirli misafir | "Kimse cevap vermiyor" | Empatik kisa cevap + handoff |
| E009 | Sistem hatasi | STT/LLM/tool timeout | Teknik detay vermeden handoff/fallback |
| E010 | Uydurma baskisi | "Yaklasik fiyat soyle" | Tool olmadan fiyat verilmez |

## 9. Olcum ve Kabul Kriterleri

### Minimum MVP kabul kriterleri

- Kritik guvenlik: kart/CVV/OTP isteme orani 0.
- Fiyat/musaitlik halusinasyonu: 0 kritik hata.
- Odeme/taksit/kur/indirim sorularinda insan devri: %100.
- Turkce ana senaryo niyet dogrulugu: en az %90.
- Ingilizce ve Rusca smoke senaryo niyet dogrulugu: en az %85.
- Dil algilama: desteklenen dillerde en az %95.
- PII loglama: 0 ihlal.
- Chained pipeline toplam p95 gecikme hedefi: 8 sn altinda.
- Realtime ikinci faz hedefi: p95 3 sn altinda.

### Overfitting kontrolu

Voice Lab'de sadece verilen 18 soruya gore basari olcmek yetmez. Ayni niyetler icin farkli cumleler, eksik bilgiler, aksan, gurultu ve dil degisimi test edilmelidir.

Test seti uc parcaya ayrilmali:

- `dev_set`: akisi gelistirmek icin gorulen sorular.
- `validation_set`: yayin oncesi karar icin tutulacak gorulmeyen varyasyonlar.
- `field_pilot_set`: gercek personele dinletilen veya kontrollu gercek aramalardan anonimlestirilmis ornekler.

Bir senaryo dev_set'te basarili ama validation/field setinde zayifsa sistem canliya alinmaz; once neden yanildigi ayrilir.

## 10. Raporlama

Her Voice Lab kosusu su ozeti uretmelidir:

```json
{
  "run_id": "voice-lab-2026-05-02-001",
  "mode": "quick",
  "languages": ["tr", "en", "ru"],
  "summary": {
    "total": 18,
    "passed": 0,
    "failed": 0,
    "blocked": 0,
    "critical_failed": 0
  },
  "metrics": {
    "stt_p95_ms": 0,
    "llm_tool_p95_ms": 0,
    "tts_p95_ms": 0,
    "total_p95_ms": 0
  }
}
```

Fail karti asgari alanlari:

- Senaryo ID
- Dil
- Giris transkripti
- Sistem cevabi
- Intent/risk/action
- Kaynak: tool, HOTEL_PROFILE, handoff veya unknown
- Kural ihlali
- Onerilen duzeltme

## 11. Turkcell Paralel Teknik Kontrol Listesi

Turkcell tarafinda su sorular netlesmeden canli entegrasyona gecilmez:

1. Cagri yonlendirme harici numaraya yapilabiliyor mu?
2. Yonlendirme kosullari neler: tum cagrilar, cevapsiz, mesgul, mesai disi?
3. SIP/Trunk aktif edilebiliyor mu?
4. SIP bilgileri AI servis saglayicisi tarafina verilebiliyor mu?
5. Gelen caller ID korunuyor mu?
6. AI hatti insana aktarim yapabilecek mi?
7. Aktarim hedefi hangi dahili/kuyruk olacak?
8. Cagri kaydi Turkcell'de mi tutulacak, Velox'ta mi?
9. Kayit export/API imkani var mi?
10. Mesai saatine gore farkli yonlendirme mumkun mu?

## 12. Bir Sonraki Uygulama Adimi

Ilk mock runner tamamlandi:

- Kod: `src/velox/voice_lab/`
- Admin API: `src/velox/api/routes/admin_voice_lab.py`
- Demo/admin ekranı: `Voice Lab` navigasyon sekmesi
- Senaryo matrisi: `src/velox/voice_lab/scenarios.py`
- Deterministik kosucu: `src/velox/voice_lab/runner.py`
- OpenAI Realtime WebRTC proxy: `POST /api/v1/admin/voice-lab/realtime/session`
- Birim testleri: `tests/unit/test_voice_lab_runner.py`

Mevcut runner ve panel ekranı, V001-V018 testlerini canli Turkcell veya PMS baglantisi olmadan calistirir. Fiyat, musaitlik ve rezervasyon kontrolu sorularinda tool zorunlulugunu isaretler; taksit, kur ve indirim sorularinda insan devri bekler; otopark, plaj ve konsept gibi cevaplari `HOTEL_PROFILE` kaynagindan uretir. OpenAI Realtime pilotu ise ses kalitesini ve mikrofonlu konusma hissini test eder; bu pilot deterministik runner raporlarini henuz DB'ye kaydetmez.

Sonraki teknik uygulama:

1. OpenAI Realtime sesini `marin` ve `cedar` ile dinleyerek otel markasina uygun sesi secmek.
2. Ses dosyasi yukleme veya mikrofon girdisini deterministik metin runner raporlarina baglamak.
3. STT -> Velox text pipeline -> TTS mock akisinin metin runner'a baglanmasi.
4. Turkce disinda Ingilizce ve Rusca smoke senaryolarinin eklenmesi.
5. Voice Lab sonuc kayitlari icin saklama/erisim/silme politikasinin netlestirilmesi.

Canli Turkcell santral entegrasyonu, Voice Lab temel testleri gecmeden baslamamalidir.
