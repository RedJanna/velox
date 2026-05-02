# AI Telesekreter Discovery

> Son guncelleme: 2026-05-02
> Durum: On entegrasyon kesif ve planlama notu

Bu dosya, Velox projesine telefon santrali icin AI telesekreter ekleme surecinde kalici calisma notudur. AI telesekreter ile ilgili her yeni isten once bu dosya okunmalidir.

Ilgili plan dosyasi:
- `docs/ai_telesekreter_voice_lab_plan.md` - canli santral oncesi Voice Lab akisi, test matrisi, kabul kriterleri ve Turkcell teknik kontrol listesi

Onemli ayrim:
- Bu dosya planlama, karar ve acik soru kaynagidir.
- Misafire soylenebilecek otel gercekleri icin ana runtime kaynak `data/hotel_profiles/kassandra_oludeniz.yaml` dosyasidir.
- Fiyat, musaitlik, rezervasyon kontrolu ve odeme gibi konularda kesin cevap sadece tool/PMS ciktisina dayanmalidir.

## 1. Su Ana Kadar Verilen Kararlar

### Telefon altyapisi

- Mevcut telefon altyapisi: Turkcell santral.
- Turkcell panelinde `cagri yonlendirme` ozelligi var.
- Gorsel incelemesine gore dis entegrasyon kismen var.
- SIP/Trunk tarafi Tek Ofis/Business Trunk paketlerinde mumkun gorunuyor; AI santral entegrasyonu icin Turkcell satis/musteri yoneticisiyle netlestirilmesi gerekiyor.
- Standart Mobil Santral panelinde gelen cagrinin sesini webhook/API ile AI sistemine aktaran acik bir public API gorunmuyor.

Ilk teknik varsayim:
- Canli entegrasyondan once Voice Lab benzeri lokal/prototip test ortami kurulacak.
- Turkcell canli entegrasyonu icin ilk aday yol `cagri yonlendirme -> AI telefon hatti/SIP hedefi`.
- SIP/Trunk destegi netlesirse dogrudan ses akisi entegrasyonu degerlendirilecek.

### Ilk surum kapsami

Ilk surumda AI telesekreter:
- Genel otel bilgilerini yanitlar.
- Konaklama talebi icin tarih, kisi sayisi, cocuk bilgisi ve oda tercihi gibi gerekli bilgileri toplar.
- Restoran, transfer, konaklama, odeme, sikayet ve yetkili talebi gibi niyetleri siniflandirir.
- Emin olmadigi, tool gerektiren veya operasyonel risk tasiyan durumlarda insan devri yapar.
- Fiyat ve musaitlik uydurmaz.
- Odeme bilgisi, kart numarasi, CVV veya OTP istemez.

Ilk surumda hedeflenmeyenler:
- Odeme alma.
- Kart bilgisi toplama.
- Tool/PMS dogrulamasi olmadan kesin rezervasyon onayi verme.
- Indirim veya kur sabitleme sozu verme.

### Dil plani

- Ilk surum: Turkce, Ingilizce, Rusca.
- Sonraki faz: Fransizca ve Almanca.
- Rusca yanitlarda da kaynak kurali degismez; cevaplar HOTEL_PROFILE veya tool ciktisindan turetilir.

### Insan devri

- Insan devri durumlari mevcut Velox handoff/escalation mantigi ile uyumlu olacak.
- Odeme, guvenlik, belirsiz rezervasyon, PMS kontrolu, sikayet, yetkili talebi, tool hatasi ve guvenilir cevap verilememe durumlari insan devrine gider.
- AI, insan devri gereken bir durumda gecikmeden admin/ilgili ekip bildirimi olusturmalidir.

### Cagri kaydi

- Cagrilar kaydedilecek.
- Canliya cikmadan once KVKK/GDPR icin gorusme basinda kisa bilgilendirme zorunlu olacak.
- Kayitlar icin saklama suresi, erisim rolleri, maskeleme/anonimlestirme ve silme talebi sureci netlestirilmeden canliya cikilmayacak.

Onerilen acilis metni:

```text
Merhaba, Kassandra Oludeniz'e hos geldiniz. Hizmet kalitesi ve talebinizi karsilayabilmemiz icin gorusmemiz kayit altina alinabilir. Size nasil yardimci olabilirim?
```

## 2. Kassandra Icin Mevcut Kaynak Cevaplar

Asagidaki bilgiler repo icindeki `data/hotel_profiles/kassandra_oludeniz.yaml` dosyasindan alinmistir:

- Denize uzaklik: Belcekiz Plaji'na 300 metre.
- Ozel plaj: Ozel plaj yok.
- Transfer: Dalaman Havalimani tek yon 75 EUR; Antalya Havalimani tek yon 220 EUR.
- Konsept: Oda + kahvalti. Kahvalti 08:00-10:30 arasinda acik bufe.
- Otopark: Otelin kendi otoparki yok; ucretsiz cadde parki ve otelin karsisinda ucretli ozel otopark var. Misafire yalnizca "otopark yok" diye cevap verilmemeli.
- Cocuk politikasi: Tum yaslar kabul edilir. Ek yatak ve bebek besigi ucretsizdir; Penthouse Land haric.
- Erken giris: Musaitlige gore degerlendirilir; planlanan varis saati alinmalidir.
- Gec giris: Check-in 14:00 sonrasi yapilir; resepsiyon 7/24 aciktir. 00:00 sonrasi varis icin onceden bilgi istenir.
- Odeme yontemleri: Kredi karti, nakit, havale, POS, odeme linki ve mail order vardir. Odeme linki ve mail order insan devri gerektirir.
- Kur sabitleme: HOTEL_PROFILE icinde kesin kur sabitleme bilgisi yoktur; AI kesin konusmamalidir.
- Indirim: AI indirim vaat etmemelidir; satis ekibine yonlendirmelidir.
- Rezervasyon numarasi kontrolu: Sadece PMS/tool kontrolu ile cevaplanmalidir.
- Oludeniz plaj karakteri: Belcekiz/halk plaji tasli ve yer yer kumlu, denizi derindir. Kumburnu/Milli Park tarafi daha kumlu ve sigdir; yuzmek icin daha rahat bir secenektir.

## 3. Kullanici Tarafindan Verilen Ornek Sorular

Ilk test setine eklenecek sorular:

1. "3 Mayis ile 5 Mayis tarihleri arasinda iki yetiskin icin fiyat bilgisi alabilir miyim?"
2. "Denize uzakliginiz ne kadar?"
3. "Plajda sizlere ait ozel bir alan bulunmakta mi?"
4. "Havalimanindan transfer var mi?"
5. "Bu gece icin musaitliginiz var mi?"
6. "Her sey dahil konseptiniz var mi?"
7. "Konseptiniz nedir?"
8. "Uc kisi konaklama yapmayi dusunuyoruz. Ucuncu kisiye ek yatak mi ekliyorsunuz?"
9. "Kredi karti icin taksitlendirme uyguluyor musunuz?"
10. "Odeme yontemleriniz nedir veya odeme politikalariniz nedir?"
11. "Otelinizde otopark var mi?"
12. "Rezervasyonlar olusturuldugunda kur sabitleniyor mu?"
13. "Konaklama fiyati konusunda yardimci olur musunuz? Indirim yapar misiniz?"
14. "Otelinizde cocuk konaklayabiliyor mu?"
15. "Erken giris yapabilir miyim?"
16. "Gec giris yapacagim. Resepsiyonunuz 7/24 acik mi?"
17. "12345678 nolu rezervasyonu kontrol edebilir misiniz? Sisteminizde goruluyor mu?"
18. "Oludeniz tasli mi, derin mi?"

## 4. Cevap Uretim Kurallari

- Fiyat icin `booking.quote` veya esdeger resmi tool ciktisi gerekir.
- Musaitlik icin `booking.availability` veya esdeger resmi tool ciktisi gerekir.
- Rezervasyon numarasi kontrolu PMS/tool olmadan yapilmaz.
- Odeme, taksit, mail order, odeme linki ve kart konularinda gerektiginde insan devri yapilir.
- AI kart numarasi, CVV, OTP veya banka sifresi istemez.
- HOTEL_PROFILE icinde olmayan otel, plaj, bolge, menu veya politika bilgisi uydurulmaz.
- Misafir konusurken dil degistirirse AI ayni dilde devam etmeye calisir; emin degilse kisa netlestirme sorusu sorar.
- Gurultu, sessizlik veya anlasilmayan ses durumunda en fazla iki kez netlestirme yapilir; sonra insan devrine gidilir.

## 5. Birinci Hafta Uygulama Plani

1. Bu kesif dosyasini ve HOTEL_PROFILE kaynaklarini guncel tut.
2. Voice Lab icin hedef akisi tanimla: mikrofon -> metne cevirme -> Velox cevap motoru -> sese cevirme.
3. Telefon entegrasyonu olmadan lokal sesli prototip hazirla.
4. Turkce, Ingilizce ve Rusca icin temel test senaryolarini olustur.
5. Cagri kaydi KVKK acilis metni, saklama suresi ve erisim kurallarini netlestir.
6. Turkcell tarafinda cagri yonlendirme, SIP/Trunk ve dis entegrasyon imkanlarini teknik olarak dogrula.
7. Basari kriterlerini olc: dogru niyet, dogru veri toplama, halusinasyon yok, dogru insan devri, makul gecikme.

## 6. Acik Sorular ve Blockerlar

- Turkcell santral AI tarafina cagriyi hangi teknik yolla aktaracak: sadece yonlendirme mi, SIP/Trunk mi?
- AI hattindan insana aktarim hangi dahili numara/kuyruk ile yapilacak?
- Cagri kayitlari nerede tutulacak: Turkcell panelinde mi, Velox tarafinda mi?
- Cagri kayitlari icin saklama suresi, erisim rolleri ve silme akisi netlesmeli.
- Rusca yanitlarda runtime'in dogrulanmis kaynak metnini guvenli bicimde cevirmesi test edilmeli.

## 7. Duzeltme Protokolu

Kullanici daha sonra karar degistirmek isterse su format tercih edilir:

```text
AI telesekreter kesif notu duzeltmesi:
- Eski: Ilk surumde Turkce, Ingilizce ve Rusca olacak.
- Yeni: Ilk surumde sadece Turkce ve Ingilizce olacak.
```

Misafire soylenmesi gereken otel gercegi degisirse:

```text
Hotel profile duzeltmesi:
- Konu: Oludeniz plaj bilgisi
- Yeni cevap: ...
```

Planlama bilgisi bu dosyaya, misafire soylenebilir otel gercegi ise `data/hotel_profiles/kassandra_oludeniz.yaml` dosyasina islenir.

## 8. Uygulama Durumu

- Voice Lab plan dosyasi olusturuldu: `docs/ai_telesekreter_voice_lab_plan.md`.
- Ilk deterministik Voice Lab runner eklendi: `src/velox/voice_lab/`.
- Demo/admin paneline `Voice Lab` ekrani ve read-only API eklendi.
- Demo/admin panelindeki `Voice Lab` ekranina tarayici tabanli ses onizleme eklendi; karsilama metni ve son mock yanit Turkce, Ingilizce veya Rusca secimine gore dinlenebilir.
- Voice Lab ses onizlemesine tarayici ses tipi secimi, konusma hizi ve ton ayari eklendi. Bu ayar mevcut demo sesini denemek icindir; profesyonel ve daha gercekci final ses icin resmi neural TTS saglayici/model secimi henuz yapilmadi.
- Profesyonel ses icin OpenAI Realtime `gpt-realtime-1.5` ana aday olarak secildi. Demo Voice Lab ekranina WebRTC tabanli OpenAI Realtime mikrofon oturumu eklendi; OpenAI API anahtari tarayiciya verilmez. Backend `/v1/realtime/client_secrets` uzerinden kisa omurlu client secret uretir, tarayici SDP teklifini bu ephemeral secret ile OpenAI `/v1/realtime/calls` endpoint'ine `application/sdp` olarak gonderir.
- Realtime Voice Lab varsayilan sesi `marin` olarak kalir; kalite oncelikli denemeler icin `marin` ve `cedar` onerilir. Panelde resmi built-in Realtime sesleri `alloy`, `ash`, `ballad`, `coral`, `echo`, `sage`, `shimmer`, `verse`, `marin` ve `cedar` secilebilir; `OPENAI_REALTIME_MODEL` ve `OPENAI_REALTIME_VOICE` ENV degiskenleriyle varsayilan degistirilebilir.
- V001-V018 senaryo matrisi kod tarafinda otomatik kosulabilir hale getirildi.
- Test kapsami eklendi: fiyat/musaitlik tool zorunlulugu, otopark, Oludeniz plaj karakteri, odeme/taksit handoff, kart verisi maskeleme ve rezervasyon lookup tool zorunlulugu.
- Canli Turkcell ve gercek PMS sorgusu henuz eklenmedi; Realtime ses testi demo/admin Voice Lab kapsamina alindi ve canli santral oncesi pilot olarak kullanilacak.
