# Skill: Frontend Standards (Admin Panel & Chat Lab)

> **Hiyerarşi:** Bu dosya `SKILL.md` kural hiyerarşisinde **Öncelik 3** seviyesindedir.
> `security_privacy.md` ve `anti_hallüçination.md` kuralları bu dosyadan önce gelir; `system_prompt_velox.md` ise bu skill'den sonra gelir.

> Kod bilmeyen biri için benzetme: Bu doküman, admin panelinin **"iç mimar kılavuzu"**dur.
> Her ekran aynı stilde, aynı malzemeyle, aynı düzenle yapılsın diye kurallar koyar.
> Amaç: Panelin tutarlı, bakımı kolay ve güvenli olması.

---

## 0) Kapsam ve çalışma notları

- **Kapsam:** Velox Admin Panel (`/admin`) ve Chat Lab (`/chat-lab`) web arayüzleri
- **Kapsam dışı:** Backend API, WhatsApp mesaj formatı, LLM prompt kuralları
- **İlişkili dosyalar:** `coding_standards.md`, `security_privacy.md`, `whatsapp_format.md`
- **Temel ilke:** Frontend, bozuk backend davranışını gizleyen kalıcı bir yama katmanı olarak kullanılmaz

---

## 1) Mevcut Mimari

Velox frontend'i **Python içine gömülü (embedded) HTML/CSS/JS** mimarisi kullanır.
Bağımsız bir frontend build pipeline'ı yoktur; tüm UI kodu FastAPI uygulamasının parçasıdır.

### 1.1 Teknoloji Yığını (Mevcut)

| Katman | Teknoloji | Not |
|--------|-----------|-----|
| Render | FastAPI `HTMLResponse` | Python f-string ile HTML assembly |
| Dil | Vanilla JavaScript (ES2020+) | TypeScript yok, tip kontrolü yok |
| Stil | Özel CSS (CSS custom properties) | Tailwind yok, inline `<style>` blokları |
| Component | Yok (DOM manipülasyonu) | `innerHTML` template literal ile render |
| State | Global `state` objesi | Framework yok, doğrudan mutation |
| HTTP Client | Native `fetch` + wrapper (`apiFetch`) | Merkezi client, CSRF ve auth destekli |
| Build | Yok | Minification, bundling, tree-shaking mevcut değil |

### 1.2 Dosya Yapısı (Mevcut)

```
src/velox/api/routes/
  admin_panel_ui.py          # Admin panel HTML iskeleti (~510 satır)
  admin_panel_ui_assets.py   # Admin panel CSS + JS (~1620 satır)
  test_chat_ui.py            # Chat Lab HTML iskeleti (~207 satır)
  test_chat_ui_assets.py     # Chat Lab CSS + JS (~966 satır)
```

### 1.3 Mimari Kısıtlar

Bu gömülü mimari bilerek seçilmiştir: tek container, sıfır npm bağımlılığı, deployment basitliği.
Ancak şu kısıtlamaları taşır:

- Frontend kodu Python string literal'i içinde yaşadığı için IDE desteği (autocomplete, lint, format) zayıftır.
- JS fonksiyonları izole değildir; unit test yazmak zordur.
- Dosya boyutları büyüdükçe bakımı zorlaşır.

---

## 2) Temel Kurallar

### 2.1 XSS Koruması (KRİTİK)

- Kullanıcıdan veya API'den gelen **her** değişken `escapeHtml()` fonksiyonu ile sanitize edilmelidir.
- `innerHTML` ile render yaparken template literal içindeki **tüm** değişkenler `escapeHtml()` ile sarılmalıdır.
- **Inline event handler yasaktır** (`onclick="fn()"` gibi). Tüm event'ler `addEventListener` ile bağlanmalıdır.
- URL parametreleri DOM'a yazılmadan önce `encodeURIComponent` ile encode edilmelidir.

**Benzetme:** Her musluktan gelen su filtrelenir — kaynağı ne olursa olsun.

### 2.2 `escapeHtml` Kullanım Kuralı

```javascript
// DOĞRU: Her değişken escaped
`<td>${escapeHtml(item.name)}</td>`

// YANLIŞ: Değişken doğrudan yazılmış
`<td>${item.name}</td>`

// YASAK: Inline event handler
`<button onclick="doSomething('${value}')">Tıkla</button>`

// DOĞRU: Event delegation veya addEventListener
button.addEventListener('click', () => doSomething(value));
```

### 2.3 State Yönetimi

- Her UI'nin tek bir `state` objesi vardır. Bu obje global scope'ta tanımlıdır.
- State değişiklikleri yalnızca ilgili `load*` veya `on*` fonksiyonları içerisinde yapılır.
- State'ten okuma yapan render fonksiyonları (`render*`) state'i **değiştirmez**, yalnızca DOM'u günceller.
- Yeni state alanı eklendiğinde `clearClientSession()` fonksiyonuna da eklenmesi gerekir.

### 2.4 API Client Kuralları

- Tüm API çağrıları merkezi `apiFetch()` fonksiyonu üzerinden yapılır.
- `apiFetch()` otomatik olarak:
  - CSRF token ekler (unsafe method'larda)
  - 401 durumunda token refresh dener
  - Başarısız refresh'te login ekranına yönlendirir
- Doğrudan `fetch()` çağrısı **yasaktır** (tek istisna: `apiFetchFromAbsolute` gibi açıkça tanımlanmış wrapper'lar).
- Hata durumlarında kullanıcıya `notify()` ile toast gösterilir, teknik detay gösterilmez.

### 2.5 Event Yönetimi

- **Event delegation tercih edilir:** Tablo satırlarındaki butonlar için her satırda ayrı listener yerine, üst container'a tek listener bağlanmalıdır.
- **Listener temizliği:** `bind*Actions()` fonksiyonları her çağrıldığında eski listener'lar temizlenmelidir. `innerHTML` ile yeniden render edilen alanlarda listener zaten kaybölur, ancak `addEventListener` ile bağlanan durable listener'lar için dikkatli olunmalıdır.
- **Inline handler yasak:** `onclick`, `onchange` gibi HTML attribute event handler'lari kullanılmaz.

### 2.6 İsimlendirme

| Öğe | Kural | Örnek |
|-----|-------|-------|
| JS fonksiyon | camelCase | `loadConversations`, `renderHoldRows` |
| JS sabit | UPPER_SNAKE_CASE | `API_ROOT`, `CSRF_COOKIE` |
| CSS class | kebab-case | `module-card`, `empty-state` |
| CSS değişken | `--` prefix, kebab-case | `--accent`, `--bg-2` |
| HTML id | camelCase | `conversationTableBody`, `holdFilters` |
| data attribute | kebab-case | `data-nav`, `data-approve-hold` |
| Python fonksiyon | snake_case | `render_admin_panel_html` |

### 2.7 Dosya Boyutu

- **Hedef:** Assets dosyaları 1200 satırı aşmamalı.
- **Aşılırsa:** Ortak yardımcı fonksiyonları ayrı bir shared module'e taşı.
- **HTML iskeleti:** 600 satırı aşmamalı. Aşılırsa section'lari ayrı fonksiyonlara böl.

---

## 3) Tasarım Felsefesi: "Bilinçli Minimalizm"

- **Anti-Jenerik:** Standart "bootstrap" görünümünü reddet. Template gibi görünüyorsa yanlıştır.
- **Özgünlük:** Bespoke layout, asimetri ve ayırt edici tipografi hedefle.
- **"Neden" Faktörü:** Her elementi yerleştirmeden önce amacını hesapla. Amacı yoksa sil.
- **Minimalizm:** Azaltma en yuksek zarafettir.
- **Micro-interactions:** Hover, focus, transition efektleri kaliteli olsun.
- **Spacing:** Tutarlı spacing scale (CSS custom properties ile).

---

## 4) CSS Kuralları

### 4.1 Custom Properties (Zorunlu)

- Tüm renkler, ölçüler ve font'lar `:root` değişkenleri ile tanımlanır.
- Yeni renk veya spacing eklerken önce mevcut değişkenleri kontrol et; gereksiz yeni değişken oluşturma.
- Admin Panel ve Chat Lab **aynı değişken isimlerini kullanmalıdır** (uyumluluk hedefi).

### 4.2 Inline Style Yasağı

- `style="..."` HTML attribute'u **yalnızca** dinamik değerler için (JS ile hesaplanan değerler) kullanılabilir.
- Sabit görünüm değerleri (`margin-top:14px`, `min-width:240px` gibi) CSS class'i olarak tanımlanmalıdır.
- Yeni sabit görünüm ihtiyacı varsa, mevcut utility class'lari kontrol et veya yeni class ekle.

### 4.3 Responsive Tasarım

- En az üç breakpoint tanımlı olmalıdır: desktop (varsayılan), tablet (~1240px), mobil (~980px).
- Tablolar dar ekranda yatay scroll veya kart görünümune geçmelidir.
- Sidebar mobilde collapse olmalı, toggle butonu ile açılmalıdır.

### 4.4 `!important` Yasağı

- `!important` yalnızca `[hidden]` ve `.hidden` gibi framework-level override'lar için kullanılabilir.
- Diğer tüm durumlarda spesifiklik ile çözüm üretilmelidir.

---

## 5) Güvenlik (Frontend Özel)

### 5.1 XSS Koruması
- `innerHTML` kullanılan her yerde tüm değişkenler `escapeHtml()` ile sanitize edilir.
- Inline event handler (`onclick`, `onchange`) **yasaktır** — `addEventListener` kullanılır.
- URL parametreleri DOM'a yazılmadan önce sanitize edilir.

### 5.2 Auth & Route Koruması
- Admin panel JWT token'i `httpOnly` cookie'de saklanır (localStorage'da **değil**).
- Token süresi dolunca otomatik refresh denenir; başarısızsa login ekranına yonlendirilir.
- CSRF token her unsafe request'e (`POST`, `PUT`, `DELETE`) otomatik eklenir.
- Chat Lab iframe içinde çalıştığında, token `postMessage` ile gönderilir; origin kontrolü zorunludur.

### 5.3 Hassas Veri Gösterimi
- Telefon numaraları admin panelde **maskelenmiş** gösterilir (`phone_display` alanı).
- Kart/CVV/OTP bilgisi admin panelde **asla** gösterilmez.
- `console.log`'da hassas veri yazdırmak **yasaktır**.

### 5.4 API İletişimi
- Tüm API çağrıları merkezi `apiFetch()` üzerinden yapılır.
- Hata durumlarında kullanıcıya toast/notification gösterilir, teknik detay gösterilmez.
- API hata mesajları `extractErrorMessage()` ile parse edilir; ham JSON kullanıcıya yansıtılmaz.

---

## 6) Erişilebilirlik (a11y)

- Tüm interactive elementlerde `aria-label` veya `aria-labelledby` olmalıdır.
- Navigasyon için `<nav>` elementi `aria-label` ile etiketlenmelidir.
- Keyboard navigation çalışmalıdır (Tab sırası mantıklı).
- Renk kontrastı WCAG AA minimum (4.5:1 normal metin, 3:1 büyük metin).
- Focus ring görünür olmalıdır (CSS `outline` veya `box-shadow` ile).
- Form hata mesajları `aria-describedby` ile input'a bağlanmalıdır.
- Dialog/modal elemanları `<dialog>` HTML elementi ile uygulanmalıdır (mevcut durum uygun).

---

## 7) Hata Yönetimi (Frontend)

- API hata durumları:
  - `401` -> Token refresh dene, başarısızsa login ekranına yönlendir
  - `403` -> "Yetkiniz yok" toast mesajı
  - `404` -> "Bulunamadı" empty state
  - `500` -> "Bir sorun oluştu, lütfen tekrar deneyin" (teknik detay yok)
- Network hatası -> "Bağlantı sorunu" toast mesajı
- Form validation hataları `notify()` ile gösterilir; gerekçe net ve Türkçe olmalıdır.
- JSON parse hataları için kullanıcıya anlaşılır mesaj gösterilir (`Profile JSON parse edilemedi` gibi).

---

## 8) Dil ve Metin Tutarlılığı

### 8.1 Temel Kural
- UI metinleri **Türkçe** olarak yazılır.
- Teknik terimler (Dashboard, Hold, Ticket, FAQ, Chat Lab) Türkçe karşılıklarının yaygın olmadığı durumlarda İngilizce kalabilir, ancak **aynı terim her yerde aynı şekilde yazılır**.

### 8.2 Karakter Kuralı
- HTML içindeki Türkçe metinlerde özel karakter (`i`, `s`, `g`, `u`, `o`, `c`) kullanılır.
- Ancak **CSS class isimleri ve JS değişken isimleri** ASCII ile sınırlı kalır.

### 8.3 Tutarlılık Tablosu

| Terim | Doğru Kullanım | Yanlış Kullanım |
|-------|---------------|----------------|
| Konuşmalar | Konuşmalar | Conversations |
| Holdlar | Holdlar | Holds / Bekleyen Onaylar (karışık) |
| Ticketlar | Ticketlar | Tickets / Talepler (karışık) |
| Durum | Durum | Status (UI metninde) |
| Aksiyon | Aksiyon | Action (UI metninde) |

---

## 9) Kesin Yasaklar (Kırmızı Çizgiler)

1. `innerHTML` içinde `escapeHtml()` olmadan değişken yazmak -> **XSS riski**
2. Inline event handler (`onclick`, `onchange`) kullanmak -> **addEventListener kullan**
3. JWT token'i localStorage'da tutmak -> **httpOnly cookie**
4. `console.log`'da hassas veri yazdırmak
5. Doğrudan `fetch()` çağrısı yapmak (`apiFetch()` wrapper'i yerine)
6. Ayni yardımcı fonksiyonu birden fazla dosyada tekrar tanımlamak -> **shared module'e taşı**
7. Backend URL'yi koda gommek -> `CONFIG` objesi veya env variable kullan
8. `postMessage` gonderirken `'*'` origin kullanmak -> **`window.location.origin` kullan**
9. CSS'de sabit değer için inline `style="..."` kullanmak -> **CSS class tanımla**
10. Event listener'lari temizlemeden yeniden bind etmek -> **delegation veya cleanup**

---

## 10) Kontrol Listesi

Her frontend değişikliği sonrası aşağıdaki kontrol uygulanır:

- [ ] Tüm `innerHTML` template'lerinde değişkenler `escapeHtml()` ile sarılı
- [ ] Inline event handler yok (onclick, onchange vb.)
- [ ] API çağrıları `apiFetch()` üzerinden
- [ ] JWT httpOnly cookie'de, localStorage'da değil
- [ ] CSRF token unsafe method'larda gönderiliyor
- [ ] Hassas veri maskelenmiş gösteriliyor
- [ ] `console.log`'da hassas veri yok
- [ ] CSS custom properties kullanılıyor, hardcoded renk/font yok
- [ ] Inline style yalnızca dinamik değerler için (sabit değerler class'ta)
- [ ] Event listener'lar temiz (delegation veya innerHTML ile yeniden render)
- [ ] Toast mesajları Türkçe ve anlaşılır
- [ ] Empty state tasarımı mevcut (boş tablo, boş liste)
- [ ] Responsive breakpoint'lar çalışıyor (1240px, 980px)
- [ ] `aria-label` interactive elementlerde mevcut
- [ ] Yardımcı fonksiyonlar tekrar tanımlanmamış (shared module'den import)

---

## 11) Gelecek Mimari Hedefi (Referans)

Proje büyüdükçe aşağıdaki stack'e geçiş planlanmaktadır.
Bu bölüm **mevcut kuralları geçersiz kılmaz**; yalnızca yol haritası referansıdır.

| Katman | Hedef Teknoloji | Not |
|--------|----------------|-----|
| Framework | React 18+ / Next.js | SPA veya SSR |
| Dil | TypeScript (strict mode) | `any` tipi yasak |
| Stil | Tailwind CSS | Özel CSS minimumda |
| Component Library | Shadcn UI (Radix primitives) | Mevcut kütüphaneden faydalanılır |
| State Management | React Context / Zustand | Basit state Context, karmaşık state Zustand |
| HTTP Client | Axios veya fetch + wrapper | Merkezi client |
| Form | React Hook Form + Zod | Validasyon Zod ile |
| Tablo | TanStack Table | Sayfalama, sıralama, filtreleme |

**Geçiş koşulları:**
- Frontend dosya boyutları 2000+ satırı aştığında
- Birden fazla bağımsız frontend geliştirici çalıştığında
- Karmaşık form akışları ve client-side routing ihtiyacı doğduğunda

Bu geçiş gerçekleştiğinde bu bölüm "Mevcut Mimari" bölümünün yerine taşınır ve eski kurallar kaldırılır.
