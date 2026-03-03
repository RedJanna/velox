# Skill: Coding Standards (v2)

> Bu doküman, ekipte herkesin **aynı dilde** ve **aynı düzenle** kod yazması için bir “işletme kılavuzu”dur.
> Kod bilmiyorsanız şöyle düşünün: Bu, mutfakta **her aşçının aynı tarife ve hijyen kuralına uyması** gibi.

## Amaç

- Kodun **okunabilir** olması (başkası da rahat anlayabilsin)
- Kodun **bozulmaya daha az yatkın** olması (hata ve sürpriz azalsın)
- Kodun **hızlı çalışması** (özellikle aynı anda çok misafir mesaj atarken)
- Kodun **güvenli** olması (yanlış veri/sızıntı olmasın)

## Hızlı Özet (1 dakikalık)

- “Güncel Python” kullan.
- Dış dünya ile konuşurken (internet/veritabanı/dosya) **bekleyerek** çalış (bloklama yok).
- Her fonksiyonun giriş/çıkışı **etiketli** olsun (tip bilgisi).
- Sistemler arası giden-gelen veriyi **standart form** gibi tanımla (Pydantic).
- İsimlendirme, dosya boyutu, import düzeni… hepsi **aynı standartta**.

---

## Kurallar (Ne demek? Neden? Günlük hayattan benzetme)

### 1) Python 3.11+
**Ne demek?** Güncel Python özellikleri kullanılacak.  
**Neden?** Daha temiz ve daha az hata çıkaran yazım şekilleri var.  
**Benzetme:** Eski telefon yerine yeni telefon kullanmak gibi.

### 2) “Async everywhere” (Bekleyerek çalışma)
**Ne demek?** İnternet / veritabanı / dosya gibi yavaş işler yapılırken sistem “donmasın”.  
**Neden?** Aynı anda 50 misafire cevap gelir; biri yavaşlarsa diğerleri beklemesin.  
**Benzetme:** Tek kasiyer tek müşteriyi beklerse kuyruk uzar. “Bekleyerek çalışma” çok kasiyer gibi davranmayı sağlar.

**Yasak örnekler:** `requests`, `time.sleep()` gibi “herkesi bekleten” şeyler.  
**Doğru:** `httpx` (async), `asyncio.sleep()`.

### 3) Type hints (Her şey etiketli)
**Ne demek?** Her fonksiyon “ne alır, ne verir” net yazılacak.  
**Neden?** Yanlış tipte veri gelince hata erken yakalanır.  
**Benzetme:** Kabloların üstünde “Elektrik / İnternet” yazması gibi; yanlış yere takmazsın.

### 4) Pydantic (Standart form)
**Ne demek?** Sistemler arası veri alışverişi “form” gibi tanımlanacak.  
**Neden?** Herkes farklı format kullanırsa karışır.  
**Benzetme:** Otel check-in formu. Herkes aynı formu doldurursa resepsiyon hızlı çalışır.

> “Sınırdan geçen veri” = API girişi/çıkışı, DB satırı, tool giriş/çıkışı vb.

### 5) İsimlendirme (snake_case / PascalCase / UPPER_SNAKE_CASE)
**Ne demek?** Her şeyin adı aynı kurala göre.  
**Neden?** Dosyaları bulmak kolaylaşır, ekip dili ortak olur.  
**Benzetme:** Otelde oda numaraları bir standarda göre olursa kimse kaybolmaz.

- Değişken/fonksiyon/dosya/DB sütunu: `snake_case`
- Sınıf isimleri: `PascalCase`
- Sabitler: `UPPER_SNAKE_CASE`

### 6) Dosya boyutu sınırı (hedef 600 satır)
**Ne demek?** Çok büyüyen dosyalar sorumluluk bazlı bölünecek. `main.py` kısa kalacak.
**Neden?** Dev bir dosyada hata saklanır, bakım zorlaşır.
**Benzetme:** Tek dev depo yerine raf raf düzenli depo.

**Hedef:** 600 satır/dosya. Aşılırsa **mantıksal sorumluluk** bazında böl.
**İstisnalar (600+ olabilir):**
- SQL migration dosyaları (tek transaction bütünlüğü gerekir)
- Enum/constant tanım dosyaları (bölmek import karmaşası yaratır)
- Test dosyaları (bir modülün tüm testleri tek dosyada kalabilir)

**⚠️ Yasak olan:** Yapay bölme (dosyayı rastgele 600'er satıra kesmek). Bölme her zaman **tek sorumluluk prensibine** göre yapılır.

### 7) Imports (Malzeme rafı düzeni)
**Ne demek?** İçe aktarmalar düzenli ve tahmin edilebilir olacak.  
**Neden?** “Bu nereden gelmiş?” sorusu azalır.  
**Benzetme:** Market rafları: önce temel gıda, sonra markalı ürün, sonra kendi ev yapımı.

Sıra: **stdlib → third-party → local**  
Ve mümkünse **mutlak import** (adres tam yazılır), göreli import (.. ile) tercih edilmez.

### 8) Hardcoded yok (Merkezî kaynak)
**Ne demek?** Otel bilgisi “kodun içine” gömülmeyecek.  
**Neden?** Otel değişirse kodu yeniden yazmak zorunda kalırsın.  
**Benzetme:** Menü fiyatını garsonun kafasından söylemesi yerine, menüden okuması.

- Otel özel verileri: `HOTEL_PROFILE`
- Ayarlar: `settings.py` (env)
- “Sihirli sayılar”: `constants.py`

### 9) Docstrings (Etiket)
**Ne demek?** Dışarıya açık her fonksiyon/sınıf 1 satır açıklama alacak.  
**Neden?** Kodun “niyeti” anlaşılır.  
**Benzetme:** Kavanozun üstünde “şeker” yazması.

### 10) print() yok, structlog var (Kayıt defteri)
**Ne demek?** Rastgele ekrana yazmak yerine sistemli log tutulacak.  
**Neden?** Hata olduğunda “ne oldu?” diye geriye dönüp bakabilmek için.  
**Benzetme:** Otelde olay defteri; “Şu saatte şu oldu” gibi düzenli kayıt.

> Not: Loglarda kişisel bilgi yazma konusu ayrıca **security_privacy.md** ile uyumlu olmalı.

---

## Kalıp Örnekler (Bu dokümanın “tarif kartları”)

### Async fonksiyon şablonu
```python
async def get_availability(
    hotel_id: int,
    checkin_date: date,
    checkout_date: date,
) -> AvailabilityResponse:
    """Fetch room availability from Elektraweb."""
    # implementation
```

### Pydantic model şablonu
```python
class StayDraft(BaseModel):
    checkin_date: date
    checkout_date: date
    adults: int
    chd_ages: list[int] = Field(default_factory=list)
    notes: str | None = None
```

### Enum kullanımı (ham string yerine)
```python
from velox.config.constants import Intent, ConversationState

if intent == Intent.STAY_AVAILABILITY:
    ...
state = ConversationState.NEEDS_VERIFICATION
```

### Repository pattern (veritabanı erişimi için tek kapı)
```python
class ReservationRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get_by_id(self, hold_id: str) -> StayHold | None:
        row = await self._pool.fetchrow(
            "SELECT * FROM stay_holds WHERE hold_id = $1", hold_id
        )
        return StayHold(**dict(row)) if row else None
```

---

## Kesin Yasaklar (Kırmızı Çizgiler)

- `requests` kullanma → async `httpx` kullan
- `time.sleep()` kullanma → `asyncio.sleep()` kullan
- `hotel_id=21966` gibi sabit yazma → parametre/ayar/HOTEL_PROFILE
- `from X import *` yok
- `.env` commit yok
- SQL’de f-string ile birleştirme yok → parametreli sorgu (`$1`, `$2`)
- Hedef 600 satır/dosya — aşılırsa sorumluluk bazlı böl (istisnalar: migration, enum, test)

---

## Geliştirme Önerileri (Dokümana ekleyebileceğimiz şeyler)

Aşağıdakiler “ekip büyüyünce hayat kurtaran” bölümler olur:

1) **“İyi örnek / kötü örnek”** mini galerisi  
   - bloklayan kod vs bekleyen kod  
   - hardcoded vs config  
   - kötü isim vs iyi isim

2) **Dosya & klasör düzeni**  
   - `api/`, `services/`, `repositories/`, `models/`, `config/` gibi önerilen yapı

3) **Kod inceleme (PR) kontrol listesi**  
   - “Bu değişiklik kişisel veri logluyor mu?”  
   - “Hata olursa insan devri var mı?” (error_handling.md ile uyum)

4) **Log standardı**  
   - Hangi olaylar loglanır, hangi alanlar asla yazılmaz (telefon, kart vs.)

5) **Komutlar (tek satır kullanım)**  
   - `ruff check` / `mypy --strict` ne yapar, nasıl çalıştırılır (kısa açıklama)

---

## Validation Checklist

- [ ] Tüm fonksiyonlarda tip bilgisi var (girdi + çıktı)
- [ ] Tüm I/O async
- [ ] Dosyalar hedef 600 satır altında (istisnalar: migration, enum, test)
- [ ] Otel/ayar değerleri hardcoded değil
- [ ] Import sırası düzgün: stdlib → third-party → local
- [ ] Sınırdan geçen veriler Pydantic model
- [ ] SQL birleştirme yok (parametreli sorgu var)
- [ ] `ruff check` sıfır hata
- [ ] `mypy --strict` geçiyor (ya da sadece beklenen istisnalar var)
