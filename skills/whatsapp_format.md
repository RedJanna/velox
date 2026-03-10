# Skill: WhatsApp Message Formatting (v2)

> Kod bilmeyen biri için benzetme: Bu doküman, resepsiyonun “WhatsApp konuşma adabı”dır.  
> Amaç: Misafir mesajı **tek bakışta anlasın**, **yanlış anlamasın**, **güvende hissetsin**.

---

## 0) Neden bu kadar kural var?

WhatsApp’ta misafir:
- hızlı okur (uzun metni atlar),
- ekranda “duvar yazısı” görünce kaçabilir,
- teknik kelimeleri görünce güvensizlik hisseder.

Bu yüzden mesaj: **kısa + düzenli + tek parça + misafir dili** olmalı.

---

## 1) Altın kurallar (özet)

- **Tek mesaj:** Her cevap tek WhatsApp mesajı olmalı. (Bölmek yok.)
- **Kısa paragraflar:** 3 satırı geçmesin, araya boşluk koy.
- **Seçenekler numaralı:** 1-2-3 şeklinde.
- **Vurgu az:** *kalın* sadece fiyat/tarih/oda adı gibi kritik yerlerde.
- **Emoji az:** en fazla 3–4 tane, “işaret” gibi kullan.
- **Dil tutarlılığı:** Misafir hangi dilde başladıysa o dilde devam.

Bu temel kurallar dosyanın orijinalinde de var. fileciteturn6file0L5-L39

---

## 2) Kuralları “misafir gözüyle” anlatım (teker teker)

### 2.1 4096 karakter sınırı
WhatsApp’ta tek bir mesajın yazı sınırı var. Aşarsan mesaj ya gitmez ya da okunmaz. fileciteturn6file0L5-L6

**v2 iyileştirmesi (daha gerçekçi):**
- “... devam ediyor” demek yerine:
  - “Detay isterseniz *Devam* yazabilirsiniz.”  
  Çünkü aynı turda ikinci mesaj atmak zaten yasak. fileciteturn6file0L6-L7

### 2.2 Tek mesaj kuralı
Tek bir cevap = tek WhatsApp mesajı. fileciteturn6file0L6-L7  
**Benzetme:** Misafire aynı anda 3 ayrı not bırakmak yerine tek bir düzgün not.

### 2.3 Kısa paragraf kuralı
En fazla 3 satır, araya boşluk. fileciteturn6file0L7-L8  
**Benzetme:** Menüde tek sayfada, bölümlere ayrılmış yazı.

### 2.4 Numaralı seçenekler
Oda / saat / politika seçenekleri numaralı verilir. fileciteturn6file0L8-L12  
**Benzetme:** “1-2-3 hangisini istersiniz?” demek karar vermeyi hızlandırır.

### 2.5 WhatsApp yazı biçimi (kalın/italik)
WhatsApp’ın desteklediği vurgu biçimleri var. *Kalın* en faydalısı. fileciteturn6file0L13-L18  
**Kural:** `code` asla kullanılmaz (misafir dili değil). fileciteturn6file0L17-L18

### 2.6 Emoji politikası
Emoji “süs” değil, işaret olmalı. En fazla 3–4 emoji. fileciteturn6file0L18-L26  
**Yasak:** emoji zinciri (✅✅✅) ve aşırı coşkulu emojiler. fileciteturn6file0L25-L26

### 2.7 Resmî hitap (Siz dili)
Türkçe: her zaman “Siz”. fileciteturn6file0L26-L27  
Diğer dillerde de aynı “resmî” seviye.

### 2.8 Teknik kelime yok
Misafire “hold_id / ticket_id / API” gibi iç terimler görünmez. fileciteturn6file0L27-L28  
**v2 ek kuralı:** Misafire “arka plan” anlatma:
- “sistem”, “entegrasyon”, “servis”, “çekmek”, “otomatik” gibi kelimeleri de kullanmamaya çalış.

### 2.9 Onay özeti standart format
Rezervasyon onayı istenirken aynı özet formatı kullanılır. fileciteturn6file0L28-L39  
**Benzetme:** Fiş gibi: tarih, oda, kişi, toplam → “Evet” yazın.

### 2.10 Dil tutarlılığı
Misafir hangi dilde başladıysa o dilde devam; misafir istemedikçe dil değiştirme. fileciteturn6file0L39-L40

---

## 3) Mesaj iskeleti (her mesaj için “tek kalıp”)

> Bu bölüm v2 ile eklenmiştir. Amaç: herkes aynı düzenle yazsın.

1) **Selam / kısa giriş**
2) **Durum özeti (1–2 satır)**
3) **Seçenekler veya istenen bilgiler**
4) **Net çağrı (misafirden ne istiyoruz?)**
5) **Kibar kapanış**

---

## 4) Para birimi ve sayı gösterimi (karışıklığı azaltmak)

- Tutarı her zaman “sayı + para birimi” şeklinde yaz: `950 EUR`, `42.000 TRY`, `120 USD`, `95 GBP`, `3.500 RUB`.
- Sembol (€, ₺, $) kullanılabilir ama **karışıklık olmasın** diye mümkünse kodla birlikte ver.

> Not: Para birimi/ödeme konusu açılırsa, içerik kuralı gereği “insan devri” gerekir (error_handling / security kuralları).  
> Bu doküman formatı anlatır; ödeme kararını değil.

---

## 5) 4096’yı aşarsa neyi kesiyoruz? (öncelik sırası)

Mesaj uzarsa, aşağıdaki sırayla “en az önemli” kısımlar kesilir:
1) Ek açıklamalar / uzun notlar
2) Uzun politika metinleri
3) Çok fazla seçenek (ilk 3–5 seçenek kalsın)
4) En sona her zaman **misafirin yapacağı aksiyon** kalsın

---

## 6) Yasaklar (kırmızı çizgiler)

Orijinal yasakların hepsi aynen geçerli: fileciteturn6file0L83-L92
- 4096’yı aşma
- Tek cevapta çok mesaj atma
- WhatsApp mesajında code block / başlık / HTML kullanma
- “sen” dili kullanma
- İç kimlikleri (hold_id, ticket_id vb.) misafire gösterme
- Emoji zinciri kullanma
- Kesin süre verme (“10 dakika içinde”) → “en kısa sürede” de

---

## 7) Validation Checklist (kontrol listesi)

Orijinal liste + v2 ekleri: fileciteturn6file0L93-L102
- [ ] 4096 karakteri geçmiyor
- [ ] Tek mesaj
- [ ] Seçenekler numaralı
- [ ] Emoji en fazla 4
- [ ] Resmî hitap
- [ ] Teknik kelime yok (+ v2: “arka plan” kelimeleri yok)
- [ ] Onay özeti standart formatta
- [ ] Dil tutarlı

---

## Patterns (mühendis notu)

Orijinal kod kalıpları korunur, sadece “kesme mesajı” daha misafir dostu yapılır. fileciteturn6file0L43-L54

### Message formatter (v2 önerisi)
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
