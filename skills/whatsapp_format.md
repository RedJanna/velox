# Skill: WhatsApp Message Formatting (v2)

> **Hiyerarşi:** Bu dosya `SKILL.md` hiyerarşisinde **Öncelik 3** seviyesindedir.
> `security_privacy.md` ve `anti_hallucination.md` kuralları bu dosyadan önce gelir.

> Kod bilmeyen biri için benzetme: Bu doküman, resepsiyonun "WhatsApp konuşma adabı"dır.
> Amaç: Misafir mesajı **tek bakışta anlasın**, **yanlış anlamasın**, **güvende hissetsin**.

---

## 0) Neden bu kadar kural var?

WhatsApp'ta misafir:
- hızlı okur (uzun metni atlar),
- ekranda "duvar yazısı" görünce kaçabilir,
- teknik kelimeleri görünce güvensizlik hisseder.

Bu yüzden mesaj: **kısa + düzenli + tek parça + misafir dili** olmalı.

---

## 1) Altın kurallar (özet)

- **Tek mesaj:** Her cevap tek WhatsApp mesajı olmalı. (Bölmek yok.)
- **Kısa paragraflar:** 3 satırı geçmesin, araya boşluk koy.
- **Seçenekler numaralı:** 1-2-3 şeklinde.
- **Vurgu az:** *kalın* sadece fiyat/tarih/oda adı gibi kritik yerlerde.
- **Emoji az:** en fazla 3–4 tane, "işaret" gibi kullan.
- **Dil tutarlılığı:** Misafir hangi dilde başladıysa o dilde devam.

---

## 2) Kuralları "misafir gözüyle" anlatım (teker teker)

### 2.1 4096 karakter sınırı
WhatsApp'ta tek bir mesajın yazı sınırı var. Aşarsan mesaj ya gitmez ya da okunmaz.

**v2 iyileştirmesi (daha gerçekçi):**
- "... devam ediyor" demek yerine:
  - "Detay isterseniz *Devam* yazabilirsiniz."
  Çünkü aynı turda ikinci mesaj atmak zaten yasak.

### 2.2 Tek mesaj kuralı
Tek bir cevap = tek WhatsApp mesajı.
**Benzetme:** Misafire aynı anda 3 ayrı not bırakmak yerine tek bir düzgün not.

### 2.3 Kısa paragraf kuralı
En fazla 3 satır, araya boşluk.
**Benzetme:** Menüde tek sayfada, bölümlere ayrılmış yazı.

### 2.4 Numaralı seçenekler
Oda / saat / politika seçenekleri numaralı verilir.
**Benzetme:** "1-2-3 hangisini istersiniz?" demek karar vermeyi hızlandırır.

### 2.5 WhatsApp yazı biçimi (kalın/italik)
WhatsApp'ın desteklediği vurgu biçimleri var. *Kalın* en faydalısı.
**Kural:** `code` asla kullanılmaz (misafir dili değil).

### 2.6 Emoji politikası
Emoji "süs" değil, işaret olmalı. En fazla 3–4 emoji.
**Yasak:** emoji zinciri (✅✅✅) ve aşırı coşkulu emojiler.

### 2.7 Resmî hitap (Siz dili)
Türkçe: her zaman "Siz".
Diğer dillerde de aynı "resmî" seviye.

### 2.8 Teknik kelime yok
Misafire "hold_id / ticket_id / API" gibi iç terimler görünmez.
**v2 ek kuralı:** Misafire "arka plan" anlatma:
- "sistem", "entegrasyon", "servis", "çekmek", "otomatik" gibi kelimeleri de kullanmamaya çalış.

### 2.9 Onay özeti standart format
Rezervasyon onayı istenirken aynı özet formatı kullanılır.
**Benzetme:** Fiş gibi: tarih, oda, kişi, toplam → "Evet" yazın.

### 2.10 Dil tutarlılığı
Misafir hangi dilde başladıysa o dilde devam; misafir istemedikçe dil değiştirme.

---

## 3) Mesaj iskeleti (her mesaj için "tek kalıp")

1) **Selam / kısa giriş**
2) **Durum özeti (1–2 satır)**
3) **Seçenekler veya istenen bilgiler**
4) **Net çağrı (misafirden ne istiyoruz?)**
5) **Kibar kapanış**

---

## 4) Para birimi ve sayı gösterimi (karışıklığı azaltmak)

- Tutarı her zaman "sayı + para birimi" şeklinde yaz: `950 EUR`, `42.000 TRY`, `120 USD`, `95 GBP`, `3.500 RUB`.
- Sembol (€, ₺, $) kullanılabilir ama **karışıklık olmasın** diye mümkünse kodla birlikte ver.

> Not: Para birimi/ödeme konusu açılırsa, içerik kuralı gereği "insan devri" gerekir (error_handling / security kuralları).
> Bu doküman formatı anlatır; ödeme kararını değil.

---

## 5) 4096'yı aşarsa neyi kesiyoruz? (öncelik sırası)

Mesaj uzarsa, aşağıdaki sırayla "en az önemli" kısımlar kesilir:
1) Ek açıklamalar / uzun notlar
2) Uzun politika metinleri
3) Çok fazla seçenek (ilk 3–5 seçenek kalsın)
4) En sona her zaman **misafirin yapacağı aksiyon** kalsın

---

## 6) Interactive Message Types (WhatsApp Business API)

> WhatsApp Business API sadece düz metin değil, **yapısal mesaj tipleri** de destekler.
> Bu tipler misafir deneyimini iyileştirir ve seçim kolaylığı sağlar.

### 6.1 Desteklenen mesaj tipleri

| Tip | Ne zaman kullanılır? | Maks. seçenek | Örnek kullanım |
|-----|---------------------|---------------|----------------|
| **Text** | Genel bilgilendirme, SSS | — | Selamlama, bilgi yanıtı |
| **Reply Buttons** | 2-3 net seçenek | **3 buton** | "Evet / Hayır / Detay" |
| **List Message** | 4+ seçenek veya kategorili seçim | **10 öğe, 10 bölüm** | Oda tipi seçimi, tarih seçenekleri |
| **Location Request** | Konum istemek (transfer vb.) | — | "Konumunuzu paylaşır mısınız?" |

### 6.2 Ne zaman text yerine interactive kullan?

- **2-3 seçenek → Reply Buttons:** Misafir tek dokunuşla seçer, yazma hatası olmaz.
- **4+ seçenek → List Message:** Oda tipleri, restoran menüsü vb. düzenli listelenir.
- **Evet/Hayır onay → Reply Buttons:** "Onaylıyor musunuz?" → [Evet] [Hayır] butonları.

### 6.3 Interactive mesaj kuralları

- **Buton metni:** Maks. 20 karakter, kısa ve net ("Evet", "Detay Gör", "İptal")
- **Liste başlığı:** Maks. 24 karakter
- **Liste açıklaması:** Maks. 72 karakter
- **Fallback:** Interactive mesaj gönderilemezse (eski WhatsApp sürümü), numaralı text mesajına düş
- **Karıştırma yok:** Aynı mesajda hem buton hem liste **olmaz**

**Benzetme:** Resepsiyondaki dokunmatik ekran — misafir parmaklıyla seçiyor, yazmak zorunda değil.

---

## 7) Media Handling (Misafirden gelen medya)

> Misafir sadece yazı göndermez — fotoğraf, video, konum, belge de gönderebilir.
> Sistem bunlara nasıl tepki verir?

### 7.1 Gelen medya türleri ve tepkiler

| Medya türü | Sistem tepkisi | İnsan devri? |
|------------|---------------|-------------|
| **Fotoğraf** | Logla (metadata: boyut, tip). İçeriği analiz etme. Misafire: "Fotoğrafınızı aldım. İlgili ekibe iletiyorum." | ✅ Evet |
| **Video** | Logla (metadata). Misafire: "Videounuzu aldım. İlgili ekibe iletiyorum." | ✅ Evet |
| **Ses mesajı** | Logla (metadata). Misafire: "Sesli mesajınızı aldım. Yardımcı olmam için yazılı olarak iletirseniz daha hızlı dönüş yapabilirim." | ❌ Hayır (yazılı iste) |
| **Konum** | Koordinatları kaydet. Transfer bağlamında kullanılabilir. | Bağlama göre |
| **Belge (PDF vb.)** | Logla (metadata, dosya adı). Misafire: "Belgenizi aldım. İlgili ekibe iletiyorum." | ✅ Evet |
| **Sticker / GIF** | Yok say, yanıt verme. | ❌ Hayır |
| **Kart bilgisi içeren fotoğraf** | **Asla işleme** — hemen insan devri + güvenlik uyarısı | ✅ Hemen |

### 7.2 Media kuralları

- Sistem **fotoğraf / video içeriğini analiz etmez** (OCR, image recognition vb. yok — gizlilik riski)
- Media dosyaları **uzun süre saklanmaz** — `security_privacy.md` veri saklama kuralları geçerli
- Gelen media hakkında **metadata loglanır** (boyut, tip, timestamp) ama **dosya içeriği loglanmaz**
- Misafire "fotoğraf gönderdiğiniz için teşekkürler" gibi gereksiz yanıt verilmez — kısa ve net

### 7.3 Sistem tarafından gönderilen medya

Sistem şu durumlarda medya gönderebilir:
- **Konum:** Otel konumunu Google Maps linki olarak (HOTEL_PROFILE'dan)
- **Belge:** Rezervasyon onay PDF'i (ileride eklenebilir)
- **Fotoğraf:** Oda/otel fotoğrafları (HOTEL_PROFILE'da URL varsa)

> **Kural:** Gönderilen her medyanın kaynağı **HOTEL_PROFILE** olmalı.
> Sistem kendi fotoğraf/belge üretmez.

---

## 8) Yasaklar (kırmızı çizgiler)

- 4096'yı aşma
- Tek cevapta çok mesaj atma
- WhatsApp mesajında code block / başlık / HTML kullanma
- "sen" dili kullanma
- İç kimlikleri (hold_id, ticket_id vb.) misafire gösterme
- Emoji zinciri kullanma
- Kesin süre verme ("10 dakika içinde") → "en kısa sürede" de
- Gelen fotoğraf/videoyu OCR veya image recognition ile analiz etme
- Kart bilgisi içeren fotoğrafı işleme (hemen insan devri)

---

## 9) Validation Checklist (kontrol listesi)

- [ ] 4096 karakteri geçmiyor
- [ ] Tek mesaj
- [ ] Seçenekler numaralı (veya interactive buttons/list kullanılıyor)
- [ ] Emoji en fazla 4
- [ ] Resmî hitap
- [ ] Teknik kelime yok (+ "arka plan" kelimeleri yok)
- [ ] Onay özeti standart formatta
- [ ] Dil tutarlı
- [ ] 2-3 seçenekte Reply Buttons, 4+ seçenekte List Message değerlendirildi
- [ ] Interactive mesaj fallback'i var (eski client için text)
- [ ] Gelen fotoğraf/video/belge için insan devri akışı var
- [ ] Ses mesajı için "yazılı olarak iletin" yanıtı var
- [ ] Gelen media metadata loglanıyor, içerik loglanmıyor

---

## Patterns (mühendis notu)

### Message formatter (v2)
```python
def format_whatsapp_message(text: str, max_length: int = 4096) -> str:
    if len(text) <= max_length:
        return text

    truncated = text[: max_length - 80]  # CTA için pay bırak
    last_newline = truncated.rfind("\n")
    if last_newline > max_length * 0.8:
        truncated = truncated[:last_newline]

    return truncated + "\n\nDetay isterseniz *Devam* yazabilirsiniz."
```

### Interactive message builder (yeni)
```python
from enum import Enum

class MessageType(Enum):
    TEXT = "text"
    REPLY_BUTTONS = "interactive_buttons"
    LIST = "interactive_list"

def choose_message_type(options_count: int) -> MessageType:
    """Select best WhatsApp message type based on option count."""
    if options_count == 0:
        return MessageType.TEXT
    if options_count <= 3:
        return MessageType.REPLY_BUTTONS
    return MessageType.LIST
```

### Media handler (yeni)
```python
SUPPORTED_MEDIA_TYPES = {"image", "video", "audio", "document", "location", "sticker"}
HANDOFF_MEDIA_TYPES = {"image", "video", "document"}  # İnsan devri gereken tipler
IGNORE_MEDIA_TYPES = {"sticker"}  # Yanıt verilmeyen tipler

async def handle_incoming_media(
    media_type: str,
    metadata: dict,
    conversation_id: str,
) -> str | None:
    """Process incoming media, return response message or None (ignore)."""
    if media_type in IGNORE_MEDIA_TYPES:
        return None  # Sticker/GIF — yok say

    # Metadata logla (içerik değil)
    logger.info(
        "media_received",
        media_type=media_type,
        file_size=metadata.get("file_size"),
        mime_type=metadata.get("mime_type"),
        conversation_id=conversation_id,
    )

    if media_type == "audio":
        return "Sesli mesajınızı aldım. Yardımcı olmam için yazılı olarak iletirseniz daha hızlı dönüş yapabilirim."

    if media_type in HANDOFF_MEDIA_TYPES:
        # İnsan devri tetikle
        return "Dosyanızı aldım. İlgili ekibe iletiyorum; en kısa sürede size dönüş yapacaklar."

    if media_type == "location":
        return None  # Konum bağlama göre işlenir (transfer modülü)

    return None
```
