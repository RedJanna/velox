# Skill: Security & Privacy (v2)

> **Hiyerarşi:** Bu dosya `SKILL.md` hiyerarşisinde **Öncelik 1 (En yüksek)** seviyesindedir.
> Bu dosyadaki kurallar **asla override edilemez** — diğer tüm dosyalar bu kurallara tabidir.

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

**Dar istisna (sadece Chat Lab / admin import):**
- Yalnızca **admin tarafından manuel analiz** için kullanılan **Chat Lab import klasöründe**,
  konuşma geçmişi `.json` dosya adında **gerçek telefon numarası** görünebilir.
- Bu istisna sadece **yerel/admin kullanımına** yöneliktir.
- Bu istisna **veritabanı**, **uygulama logları**, **webhook kayıtları**, **genel API çıktıları**
  ve **production çalışma akışı** için **geçerli değildir**.

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

> Not: Chat Lab import istisnası **loglar** için geçerli değildir.
> Gerçek telefon numarası sadece adminin yerel import dosya adı/görünümü için kullanılabilir.

**Benzetme:** Olay defterine “Ali Veli, telefon 05xx…” yazmak yerine “Misafir #A12” yazmak.

### 2.7 Kapıdaki mühür (Webhook signature + replay protection)
Dışarıdan gelen her “kapı zili” (webhook) için **iki kontrol** yapılır:

1. **İmza kontrolü:** “Bu gerçekten WhatsApp’tan mı geldi?” → HMAC-SHA256 doğrulaması
2. **Zaman kontrolü:** “Bu eski bir istek mi?” → 5 dakikadan eski webhook’lar reddedilir (replay attack koruması)

- İmzası tutmayan istekler **içeri alınmaz** (403).
- Timestamp’ı eski olan istekler **içeri alınmaz** (403).

**Benzetme:** Kargo tesliminde hem “mühür” hem “tarih” kontrolü — eski tarihli sahte teslimat kabul edilmez.

### 2.8 Aşırı istek olursa fren (Rate limiting)
Aynı numara/IP kısa sürede çok istek atarsa:
- geçici engel uygulanır
- admin bilgilendirilir
- eşikler `settings.py`’dan gelir

**Benzetme:** Bir kişi sürekli kapıyı çalıyorsa güvenlik müdahalesi.

### 2.9 Admin panel: kısa ömürlü anahtar + 2 aşama (JWT + 2FA)
Admin panelde:
- oturum anahtarı **kısa süreli** (60 dk)
- access token frontend tarafında **httpOnly cookie** ile tutulur
- kullanıcı isterse aynı tarayıcı için **trusted device** süresi tanımlanabilir
- trusted device sadece daha önce OTP ile doğrulanmış cihazda çalışır; **2FA kapatılmaz**
- session/hatırlama süresi dolunca yeniden giriş gerekir
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

**Tek istisna:**
- Admin-only Chat Lab import klasöründeki `.json` dosya adında ve admin ekranındaki import seçim
  listesinde gerçek telefon numarası gösterilebilir.
- Bu istisna ham telefonun DB/log/webhook içine yayılmasına izin vermez.

---

## 4) Veri Koruma & Yasal Uyumluluk (KVKK / GDPR)

> ⚠️ Bu bölüm **öneri değil, zorunluluktur.** Türkiye'de KVKK, AB misafirleri için GDPR geçerlidir.
> İhlal durumunda yasal yaptırım riski vardır.

### 4.1 Veri saklama süresi (Data retention) — ZORUNLU

Kişisel veri içeren her kayıt için **maksimum saklama süresi** tanımlıdır.
Süre dolduğunda veri **silinir veya anonimleştirilir** — “belki lazım olur” geçerli değildir.

| Veri türü | Maks. saklama süresi | Süre sonunda ne olur? |
|-----------|---------------------|----------------------|
| Uygulama logları (PII içeren) | **30 gün** | Silinir |
| Konuşma kayıtları | **90 gün** | Anonimleştirilir (telefon/isim kaldırılır) |
| Escalation ticket'ları | **180 gün** | Sadece istatistiksel özet kalır |
| Webhook ham payload'ları | **7 gün** | Silinir |
| Session verileri (Redis) | **24 saat** (TTL) | Otomatik expire |

> **Kural:** Bu süreler `settings.py` veya `constants.py`'da tanımlanır, hardcoded değildir.
> Admin panelden değiştirilebilir olmalıdır (minimum süreler korunarak).

**Benzetme:** Eski güvenlik kamera kayıtlarının süre sonunda silinmesi — yasal zorunluluk.

### 4.2 Rıza yönetimi (Consent management) — ZORUNLU

Misafirden kişisel veri toplamadan önce **bilgilendirme ve rıza** gerekir.

- **İlk mesaj senaryosu:** Misafir WhatsApp üzerinden ilk kez iletişime geçtiğinde,
  sistem kısa bir bilgilendirme mesajı gönderir:
  - TR: “Merhaba! Size yardımcı olabilmem için bazı bilgilerinizi (isim, tarih vb.) kullanmam gerekebilir. Gizlilik politikamız: [kısa link]. Devam ederek bilgi paylaşımını onaylıyorsunuz.”
  - EN: “Hello! To assist you, I may need some of your information (name, dates, etc.). Privacy policy: [short link]. By continuing, you consent to sharing information.”
- Bu mesaj **sadece ilk etkileşimde** gönderilir (session'da `consent_shown: true` flag'i tutulur).
- Rıza mesajı `TEMPLATE_LIBRARY`'de yönetilir.

**Benzetme:** Otele giriş formunda “kişisel verileriniz şu amaçla kullanılacaktır” yazması.

### 4.3 Unutulma hakkı (Right to erasure — GDPR Article 17 / KVKK m.11)

Misafir “verilerimi silin” derse:

1. **İnsan devri** yapılır (bu işlem otomatik yapılamaz, admin onayı gerekir)
2. Admin panelde **”Veri Silme Talebi”** oluşturulur
3. Silme kapsamı:
   - Konuşma geçmişi → silinir veya anonimleştirilir
   - Telefon hash'i → silinir (artık eşleştirilemez)
   - Log kayıtları → kişisel veri alanları maskelenir
   - Elektraweb'deki veriler → otel yönetimine bildirilir (sistem kontrolü dışında)
4. İşlem tamamlandığında misafire bilgilendirme yapılır
5. Tüm silme talepleri **audit log**'da tutulur (talebin kendisi saklanır, silinen veri saklanmaz)

**Süre:** KVKK gereği en geç **30 gün** içinde tamamlanmalıdır.

**Benzetme:** Otelden “bütün kayıtlarımı silin” talebi — yasal hakkı var, yapmak zorunlu.

### 4.4 Yetki prensibi: “En az yetki” (Least privilege) — ZORUNLU
- Her kullanıcı/servis sadece ihtiyacı olan erişimi alır.
- Admin panel erişimi **rol bazlıdır** (sadece gerekli ekranlar).
- Roller: `SUPER_ADMIN`, `MANAGER`, `SALES`, `VIEWER` (minimum 4 seviye)
- DB kullanıcısı sadece gerekli tablo/işlemlere erişir (SELECT/INSERT/UPDATE — DROP yok).

**Benzetme:** Her personelin her odaya anahtarı olmaması.

### 4.5 İhlal olursa ne yapılır? (Incident response) — ZORUNLU

| Adım | İşlem | Maks. süre |
|------|-------|-----------|
| 1 | Şüpheli durumu tespit et, erişimi kısıtla | Anında |
| 2 | Etki alanını belirle (hangi veriler, kaç misafir?) | 4 saat |
| 3 | Admin/yönetimi bilgilendir | 4 saat |
| 4 | KVKK Kurulu'na bildirim (ciddi ihlallerde) | 72 saat |
| 5 | Etkilenen misafirleri bilgilendir (gerekiyorsa) | 72 saat |
| 6 | Kalıcı düzeltme uygula | 7 gün |
| 7 | Incident raporu hazırla ve sakla | 14 gün |

**Benzetme:** Yangın tatbikatı: “olursa ne yapacağımız belli” — artık zaman sınırlarıyla.

---

## 5) Validation Checklist (kontrol listesi)

- [ ] DB’de ham PII yok (telefon `phone_hash`)
- [ ] Loglarda ham telefon/e-posta/isim yok (mask/hash var)
- [ ] Chat Lab import istisnası varsa sadece admin-only yerel dosya adı/görünümü ile sınırlı
- [ ] Kart/CVV/OTP yakalanınca misafire uyarı + insan devri var
- [ ] Tüm webhooks imza kontrolünden geçiyor
- [ ] Rate limit aktif (numara + IP)
- [ ] Secrets kodda değil (ENV’de)
- [ ] SQL sorguları parametreli (birleştirme yok)
- [ ] Misafire iç hata detayları gösterilmiyor
- [ ] Admin panel access token kısa ömürlü cookie, trusted device sadece OTP sonrası aktif
- [ ] Veri saklama süreleri tanımlı ve uygulanıyor (log 30 gün, konuşma 90 gün, webhook 7 gün)
- [ ] En az yetki / rol bazlı erişim var (SUPER_ADMIN, MANAGER, SALES, VIEWER)
- [ ] İlk etkileşimde consent (rıza) mesajı gönderiliyor
- [ ] Unutulma hakkı (veri silme talebi) akışı mevcut
- [ ] Phone hash salt'ı ENV'den alınıyor (PHONE_HASH_SALT)
- [ ] Webhook doğrulaması imza + timestamp kontrolü içeriyor (replay protection)
- [ ] Incident response prosedürü tanımlı (72 saat KVKK bildirimi)

---

## (Mühendis Notu) Teknik örnekler

> Bu bölüm, ekip uygularken “nasıl yapacağız?” diye bakabilsin diye var. Misafir mesajlarında kullanılmaz.

### Phone hashing (telefon parmak izi)

> **⚠️ Salt zorunludur.** Telefon numaraları sınırlı bir kümedir (ülke kodu + 10-11 rakam).
> Salt olmadan SHA-256 hash'i rainbow table saldırısıyla kırılabilir.
> Salt değeri `PHONE_HASH_SALT` ortam değişkeninden alınır.

```python
import hashlib
import os

# Salt ENV'den alınır — .env dosyasında tanımlı olmalı
PHONE_HASH_SALT: str = os.environ["PHONE_HASH_SALT"]

def hash_phone(phone: str) -> str:
    """One-way salted hash for storage. Rainbow table resistant."""
    salted = f"{PHONE_HASH_SALT}{phone}"
    return hashlib.sha256(salted.encode()).hexdigest()

def mask_phone(phone: str) -> str:
    """Masked display: +90 5** *** **77"""
    if len(phone) < 6:
        return "***"
    return phone[:4] + " " + "*" * (len(phone) - 6) + " " + phone[-2:]
```

> **Kural:** Aynı telefon numarası her zaman aynı hash'i üretmeli (lookup yapılabilsin).
> Bu yüzden salt sabittir (her hash'te farklı salt değil). Ama salt'ın kendisi gizli kalmalı (ENV'de).

### Payment data detection and rejection (kart verisi yakalama)
```python
import re

CARD_PATTERN = re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b")

def contains_payment_data(text: str) -> bool:
    """Check if user message contains credit card numbers."""
    return bool(CARD_PATTERN.search(text))
```

### Webhook signature validation (kapı mührü)

> **⚠️ Replay attack koruması zorunludur.**
> Sadece imza kontrolü yetmez — eski bir geçerli webhook yeniden gönderilebilir.
> Webhook'un timestamp'ı kontrol edilir ve 5 dakikadan eski istekler reddedilir.

```python
import hmac
import hashlib
import time

# Replay attack penceresi: 5 dakika (300 saniye)
WEBHOOK_MAX_AGE_SECONDS: int = 300

def validate_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify webhook HMAC-SHA256 signature."""
    expected = hmac.new(
        key=secret.encode(),
        msg=payload,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)

def validate_webhook_timestamp(timestamp: int | str) -> bool:
    """Reject webhooks older than WEBHOOK_MAX_AGE_SECONDS (replay attack protection)."""
    try:
        ts = int(timestamp)
    except (ValueError, TypeError):
        return False
    age = abs(time.time() - ts)
    return age <= WEBHOOK_MAX_AGE_SECONDS

def validate_webhook(
    payload: bytes,
    signature: str,
    timestamp: int | str,
    secret: str,
) -> bool:
    """Full webhook validation: signature + replay protection."""
    if not validate_webhook_timestamp(timestamp):
        return False  # Too old or too far in future — reject
    return validate_signature(payload, signature, secret)
```

> **Kural:** Her webhook handler'da `validate_webhook()` çağrılmalı.
> Sadece `validate_signature()` tek başına **yetersizdir** — replay attack'a açık bırakır.

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
