# Skill: Security & Privacy (v2)

> Kod bilmeyen biri için benzetme: Bu doküman, otelin **kasa + anahtar + kamera + resepsiyon protokolü** gibidir.
> Amaç: Misafirin bilgisi **gereksiz yere toplanmasın**, toplandıysa **güvende kalsın**, kimseye **sızmasın**.

---

## 0) Bu doküman neyi garanti eder?

- Misafir bilgileri **minimum** düzeyde tutulur (gerekmeyeni hiç istemeyiz).
- “Kredi kartı / şifre / tek kullanımlık kod” gibi **çok hassas bilgiler asla alınmaz**.
- Dışarıdan gelen istekler (WhatsApp vb.) “gerçek mi sahte mi?” diye **kimlik kontrolünden** geçer.
- Sistem bir saldırı / kötü niyet görürse **yavaşlatır / engeller** ve yöneticiyi haberdar eder.
- Misafire asla “içeride ne oldu” gibi teknik detay gösterilmez.

---

## 1) Temel prensipler (insan diliyle)

### 1.1 “Gereken kadarını al”
Misafirden sadece **o anki iş için gerekli** bilgiyi iste.
- Örn: Oda sorusu için kart bilgisi, kimlik no vb. istenmez.
- “Lazım olur” diye bilgi toplamak yasak.

**Benzetme:** Resepsiyon herkesin kimliğinin fotokopisini “belki lazım olur” diye istemez.

### 1.2 “Kasaya koy, dışarıda bırakma”
Topladığın hassas bilgiyi:
- mümkünse **hiç saklama**
- saklanacaksa **maskeli** ya da **geri döndürülemez** şekilde sakla

**Benzetme:** Anahtarı masada bırakmak yerine kasaya koymak.

### 1.3 “Misafire mutfak gösterme”
Misafir mesajlarında:
- hata kodu, sistem adı, teknik açıklama, link, iç detay yok.

**Benzetme:** Misafire “mutfakta şu makine bozuldu” demek yerine “Kısa bir gecikme var, ekibimiz ilgileniyor” demek.

---

## 2) Kurallar (net ve uygulanabilir)

### 2.1 Kişisel veriyi azalt (PII minimization)
Sadece gerekli veriyi al.
- Telefon, isim, tarih gibi şeyler **gerekliyse** istenir.
- Gereksizse hiç istenmez.


### 2.3 Kart / ödeme bilgisi asla alınmaz (No payment data)
Sistem **asla** şu bilgileri istemez veya işlemez:
- kredi kartı numarası
- CVV
- OTP (tek kullanımlık kod)
- banka şifresi / hesap bilgileri

Ödeme süreci **insan (SATIŞ ekibi)** tarafından yürütülür.

Misafir sohbet içinde kart bilgisi yazarsa:
1) İç kayıtlarda (loglarda) **maskelenir**  
2) Misafire şu mesaj gönderilir:

**TR:** “Güvenliğiniz için lütfen kart/OTP gibi ödeme bilgilerinizi buradan paylaşmayınız. Sizi ilgili ekibe yönlendiriyorum.”  
**EN:** “For your security, please do not share card/OTP details here. I’m forwarding this to our team.”

> Not: Misafir ödeme / para birimi / ödeme yöntemi ile ilgili bir cümle kurarsa **insan devri** yapılır (error_handling.md ile uyumlu).

### 2.4 Şifreler / anahtarlar kodun içinde olmaz (Secrets in ENV)
- API anahtarları, token’lar, şifreler **koda yazılmaz**
- Ayarlarda/konfigürasyonda da (yaml vb.) yazılmaz
- Sadece **ortam değişkenlerinde** tutulur (`.env` / Docker secrets)
- Loglara asla düşmez

**Benzetme:** Kasanın şifresini kapıya yapıştırmamak.

### 2.5 Gelen mesaj “temizlenir” (Input sanitization)
WhatsApp’tan gelen her mesaj işlenmeden önce:
- Çok uzun mesajlar sınırlandırılır (max 4096 karakter)
- Zararlı içerik (script vb.) ayıklanır
- Tarih formatı, sayı aralığı gibi şeyler kontrol edilir
- Aşırı büyük payload kesilir/ reddedilir

**Benzetme:** Otelde kapıdaki X-ray: içeri girmeden kontrol.

### 2.6 Kayıt defterinde kişisel bilgi yok (Log masking)
Loglar düzenli tutulur ama:
- ham telefon, e-posta, tam isim **loglanmaz**
- gerekiyorsa maskeli / hash’li hali yazılır
- misafirle ilişkilendirilebilecek “hassas kimlik” alanları korunur

**Benzetme:** Olay defterine “Ali Veli, telefon 05xx…” yazmak yerine “Misafir #A12” yazmak.

### 2.7 Kapıdaki mühür (Webhook signature validation)
Dışarıdan gelen her “kapı zili” (webhook) için:
- “Bu gerçekten WhatsApp’tan mı geldi?” kontrolü yapılır.
- İmzası tutmayan istekler **içeri alınmaz** (403).

**Benzetme:** Kargo tesliminde “mühür” kontrolü.

### 2.8 Aşırı istek olursa fren (Rate limiting)
Aynı numara/IP kısa sürede çok istek atarsa:
- geçici engel uygulanır
- admin bilgilendirilir
- eşikler `settings.py`’dan gelir

**Benzetme:** Bir kişi sürekli kapıyı çalıyorsa güvenlik müdahalesi.

### 2.9 Admin panel: kısa ömürlü anahtar + 2 aşama (JWT + 2FA)
Admin panelde:
- oturum anahtarı **kısa süreli** (60 dk)
- süresi bitince yeniden giriş gerekir
- 2 aşamalı doğrulama (Google Authenticator / TOTP) kullanılır

**Benzetme:** Personel kartı + ekstra PIN.

---

## 3) Kesin yasaklar (kırmızı çizgiler)

- Ham telefon / e-posta veritabanında tutulmaz (hash/mask zorunlu)
- Loglarda ham kişisel bilgi tutulmaz
- Kart / CVV / OTP asla alınmaz
- Anahtar/token/şifre kod içine yazılmaz
- İmzasız webhook işlenmez
- SQL sorgusunda metin birleştirme yapılmaz (enjeksiyon riski)
- Misafire iç hata detayları gösterilmez (stack trace, DB hatası vb.)
- Dış orkestrasyon aracı (örn. n8n) kullanılmaz; tüm mantık FastAPI içinde çalışır

---

## 4) Eklemeyi önerdiğim (gerçekten faydalı) yeni kurallar

> Bu bölüm “gerçekten gerekli mi?” sorusunun cevabı: **Evet**, çünkü aşağıdakiler pratikte en çok sorun çıkaran alanlar.

### 4.1 Veri saklama süresi (Data retention)
- Loglar: örn. **30 gün** sakla, sonra sil
- Konuşma kayıtları: iş ihtiyacına göre örn. **90 gün** sonra anonimleştir
- Ticket kayıtları: sadece gerekli alanları sakla

**Benzetme:** Eski güvenlik kamera kayıtlarının süre sonunda silinmesi.

> Süreleri siz belirlersiniz; ben dokümana “değiştirilebilir alan” olarak koydum.

### 4.2 Yetki prensibi: “En az yetki”
- Her kullanıcı/servis sadece ihtiyacı olan erişimi alır.
- Admin panel erişimi rol bazlıdır (sadece gerekli ekranlar).

**Benzetme:** Her personelin her odaya anahtarı olmaması.

### 4.3 İhlal olursa ne yapılır? (Incident checklist)
- Şüpheli durum tespit → erişimi kısıtla
- Logları incele → etki alanını belirle
- Gerekirse misafirleri bilgilendir (politikaya göre)
- Kalıcı düzeltme → tekrar etmesin

**Benzetme:** Yangın tatbikatı: “olursa ne yapacağımız belli”.

---

## 5) Validation Checklist (kontrol listesi)

- [ ] DB’de ham PII yok (telefon `phone_hash`)
- [ ] Loglarda ham telefon/e-posta/isim yok (mask/hash var)
- [ ] Kart/CVV/OTP yakalanınca misafire uyarı + insan devri var
- [ ] Tüm webhooks imza kontrolünden geçiyor
- [ ] Rate limit aktif (numara + IP)
- [ ] Secrets kodda değil (ENV’de)
- [ ] SQL sorguları parametreli (birleştirme yok)
- [ ] Misafire iç hata detayları gösterilmiyor
- [ ] Admin panel JWT kısa ömür + 2FA
- [ ] (Öneri) Log retention / veri saklama süresi uygulanıyor
- [ ] (Öneri) En az yetki / rol bazlı erişim var

---

## (Mühendis Notu) Teknik örnekler

> Bu bölüm, ekip uygularken “nasıl yapacağız?” diye bakabilsin diye var. Misafir mesajlarında kullanılmaz.

### Phone hashing (telefon parmak izi)
```python
import hashlib

def hash_phone(phone: str) -> str:
    """One-way hash for storage."""
    return hashlib.sha256(phone.encode()).hexdigest()

def mask_phone(phone: str) -> str:
    """Masked display: +90 5** *** **77"""
    if len(phone) < 6:
        return "***"
    return phone[:4] + " " + "*" * (len(phone) - 6) + " " + phone[-2:]
```

### Payment data detection and rejection (kart verisi yakalama)
```python
import re

CARD_PATTERN = re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b")

def contains_payment_data(text: str) -> bool:
    """Check if user message contains credit card numbers."""
    return bool(CARD_PATTERN.search(text))
```

### Webhook signature validation (kapı mührü)
```python
import hmac
import hashlib

def validate_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

### Parameterized SQL (asla metin birleştirme)
```python
# CORRECT
row = await pool.fetchrow(
    "SELECT * FROM conversations WHERE hotel_id = $1 AND phone_hash = $2",
    hotel_id, phone_hash
)

# WRONG — SQL injection risk
row = await pool.fetchrow(
    f"SELECT * FROM conversations WHERE hotel_id = {hotel_id}"  # NEVER
)
```
