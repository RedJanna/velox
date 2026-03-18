# Skill: Frontend Standards (Admin Panel & Chat Lab)

> **Hiyerarşi:** Bu dosya `SKILL.md` kural hiyerarşisinde **Öncelik 3** seviyesindedir.
> `security_privacy.md` ve `anti_hallucination.md` kuralları bu dosyadan önce gelir; `system_prompt_velox.md` ise bu skill'den sonra gelir.

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
| Stil | Özel CSS (CSS cüstom properties) | Tailwind yok, inline `<style>` blokları |
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

**Benzetme:** Her musluktan gelen şu filtrelenir — kaynağı ne olursa olsun.

### 2.2 `escapeHtml` Kullanım Kuralı

```javascript
// DOĞRU: Her değişken escaped
`<td>${escapeHtml(item.name)}</td>`

// YANLIŞ: Değişken doğrudan yazılmış
`<td>${item.name}</td>`

// YASAK: Inline event handler
`<button onclick="doSomething('${value}')">Tıkla</button>`

// DOGRU: Event delegation veya addEventListener
button.addEventListener('click', () => doSomething(value));
```

### 2.3 State Yönetimi

- Her UI'nin tek bir `state` objesi vardır. Bu obje global scope'ta tanımlıdır.
- State değişiklikleri yalnızca ilgili `load*` veya `on*` fonksiyonları icerisinde yapılır.
- State'ten okuma yapan render fonksiyonları (`render*`) state'i **değiştirmez**, yalnızca DOM'u günceller.
- Yeni state alani eklendiginde `clearClientSession()` fonksiyonuna da eklenmesi gerekir.

### 2.4 API Client Kuralları

- Tum API cagrilari merkezi `apiFetch()` fonksiyonu uzerinden yapılır.
- `apiFetch()` otomatik olarak:
  - CSRF token ekler (unsafe method'larda)
  - 401 durumunda token refresh dener
  - Basarisiz refresh'te login ekranina yonlendirir
- Dogrudan `fetch()` cagrisi **yasaktir** (tek istisna: `apiFetchFromAbsolute` gibi acikca tanımlanmis wrapper'lar).
- Hata durumlarinda kullanıcıya `notify()` ile toast gösterilir, teknik detay gosterilmez.

### 2.5 Event Yönetimi

- **Event delegation tercih edilir:** Tablo satırlarındaki butonlar için her satırda ayrı listener yerine, üst container'a tek listener bağlanmalıdır.
- **Listener temizliği:** `bind*Actions()` fonksiyonları her çağrıldığında eski listener'lar temizlenmelidir. `innerHTML` ile yeniden render edilen alanlarda listener zaten kaybolur, ancak `addEventListener` ile baglanan durable listener'lar için dikkatli olunmalidir.
- **Inline handler yasak:** `onclick`, `onchange` gibi HTML attribute event handler'lari kullanilmaz.

### 2.6 İsimlendirme

| Oge | Kural | Ornek |
|-----|-------|-------|
| JS fonksiyon | camelCase | `loadConversations`, `renderHoldRows` |
| JS sabit | UPPER_SNAKE_CASE | `API_ROOT`, `CSRF_COOKIE` |
| CSS class | kebab-case | `module-card`, `empty-state` |
| CSS değişken | `--` prefix, kebab-case | `--accent`, `--bg-2` |
| HTML id | camelCase | `conversationTableBody`, `holdFilters` |
| data attribute | kebab-case | `data-nav`, `data-approve-hold` |
| Python fonksiyon | snake_case | `render_admin_panel_html` |

### 2.7 Dosya Boyutu

- **Hedef:** Assets dosyalari 1200 satıri asmamali.
- **Asilarsa:** Ortak yardimci fonksiyonları ayrı bir shared module'e tasi.
- **HTML iskeleti:** 600 satıri asmamali. Asilarsa section'lari ayrı fonksiyonlara bol.

---

## 3) Tasarım Felsefesi: "Bilinçli Minimalizm"

- **Anti-Jenerik:** Standart "bootstrap" gorunumunu reddet. Template gibi gorunuyorsa yanlistir.
- **Ozgunluk:** Bespoke layout, asimetri ve ayirt edici tipografi hedefle.
- **"Neden" Faktoru:** Her elementi yerlestirmeden once amacini hesapla. Amaci yoksa sil.
- **Minimalizm:** Azaltma en yuksek zarafettir.
- **Micro-interactions:** Hover, focus, transition efektleri kaliteli olsun.
- **Spacing:** Tutarli spacing scale (CSS cüstom properties ile).

---

## 4) CSS Kuralları

### 4.1 Cüstom Properties (Zorunlu)

- Tum renkler, olculer ve font'lar `:root` değişkenleri ile tanımlanir.
- Yeni renk veya spacing eklerken once mevcut değişkenleri kontrol et; gereksiz yeni değişken olüsturma.
- Admin Panel ve Chat Lab **ayni değişken isimlerini kullanmalidir** (uyumluluk hedefi).

### 4.2 Inline Style Yasağı

- `style="..."` HTML attribute'u **yalnızca** dinamik değerler için (JS ile hesaplanan değerler) kullanılabilir.
- Sabit gorunum değerleri (`margin-top:14px`, `min-width:240px` gibi) CSS class'i olarak tanımlanmalidir.
- Yeni sabit gorunum ihtiyaci varsa, mevcut utility class'lari kontrol et veya yeni class ekle.

### 4.3 Responsive Tasarım

- En az uc breakpoint tanimli olmalidir: desktop (varsayilan), tablet (~1240px), mobil (~980px).
- Tablolar dar ekranda yatay scroll veya kart gorunumune gecmelidir.
- Sidebar mobilde collapse olmali, toggle butonu ile acilmalidir.

### 4.4 `!important` Yasağı

- `!important` yalnızca `[hidden]` ve `.hidden` gibi framework-level override'lar için kullanılabilir.
- Diger tüm durumlarda spesifiklik ile cozum uretilmelidir.

---

## 5) Güvenlik (Frontend Özel)

### 5.1 XSS Koruması
- `innerHTML` kullanilan her yerde tüm değişkenler `escapeHtml()` ile sanitize edilir.
- Inline event handler (`onclick`, `onchange`) **yasaktir** — `addEventListener` kullanilir.
- URL parametreleri DOM'a yazilmadan once sanitize edilir.

### 5.2 Auth & Route Koruması
- Admin panel JWT token'i `httpOnly` cookie'de saklanir (localStorage'da **degil**).
- Token şuresi dolunca otomatik refresh denenir; basarisizsa login ekranina yonlendirilir.
- CSRF token her unsafe request'e (`POST`, `PUT`, `DELETE`) otomatik eklenir.
- Chat Lab iframe içinde calistiginda, token `postMessage` ile gonderilir; origin kontrolu zorunludur.

### 5.3 Hassas Veri Gosterimi
- Telefon numaralari admin panelde **maskelenmis** gösterilir (`phone_display` alani).
- Kart/CVV/OTP bilgisi admin panelde **asla** gosterilmez.
- `console.log`'da hassas veri yazdirmak **yasaktir**.

### 5.4 API Iletisimi
- Tum API cagrilari merkezi `apiFetch()` uzerinden yapılır.
- Hata durumlarinda kullanıcıya toast/notification gösterilir, teknik detay gosterilmez.
- API hata mesajlari `extractErrorMessage()` ile parse edilir; ham JSON kullanıcıya yansitilmaz.

---

## 6) Erişilebilirlik (a11y)

- Tum interactive elementlerde `aria-label` veya `aria-labelledby` olmalidir.
- Navigasyon için `<nav>` elementi `aria-label` ile etiketlenmelidir.
- Keyboard navigation calismalidir (Tab sirasi mantikli).
- Renk kontrasti WCAG AA minimum (4.5:1 normal metin, 3:1 buyuk metin).
- Focus ring gorunur olmalidir (CSS `outline` veya `box-shadow` ile).
- Form hata mesajlari `aria-describedby` ile input'a bağlanmalıdır.
- Dialog/modal elemanlari `<dialog>` HTML elementi ile uygulanmalidir (mevcut durum uygun).

---

## 7) Hata Yönetimi (Frontend)

- API hata durumlari:
  - `401` -> Token refresh dene, basarisizsa login ekranina yonlendir
  - `403` -> "Yetkiniz yok" toast mesaji
  - `404` -> "Bulunamadi" empty state
  - `500` -> "Bir sorun olüstu, lutfen tekrar deneyin" (teknik detay yok)
- Network hatasi -> "Baglanti sorunu" toast mesaji
- Form validation hatalari `notify()` ile gösterilir; gerekce net ve Turkce olmalidir.
- JSON parse hatalari için kullanıcıya anlaşılır mesaj gösterilir (`Profile JSON parse edilemedi` gibi).

---

## 8) Dil ve Metin Tutarlılığı

### 8.1 Temel Kural
- UI metinleri **Turkce** olarak yazilir.
- Teknik terimler (Dashboard, Hold, Ticket, FAQ, Chat Lab) Turkce karsiliklarinin yaygin olmadigi durumlarda Ingilizce kalabilir, ancak **ayni terim her yerde ayni sekilde yazilir**.

### 8.2 Karakter Kuralı
- HTML içindeki Turkce metinlerde ozel karakter (`i`, `s`, `g`, `u`, `o`, `c`) kullanilir.
- Ancak **CSS class isimleri ve JS değişken isimleri** ASCII ile sinirli kalir.

### 8.3 Tutarlılık Tabloşu

| Terim | Dogru Kullanım | Yanlis Kullanım |
|-------|---------------|----------------|
| Konusmalar | Konusmalar | Conversations |
| Holdlar | Holdlar | Holds / Bekleyen Onaylar (karisik) |
| Ticketlar | Ticketlar | Tickets / Talepler (karisik) |
| Durum | Durum | Status (UI metninde) |
| Aksiyon | Aksiyon | Action (UI metninde) |

---

## 9) Kesin Yasaklar (Kırmızı Çizgiler)

1. `innerHTML` içinde `escapeHtml()` olmadan değişken yazmak -> **XSS riski**
2. Inline event handler (`onclick`, `onchange`) kullanmak -> **addEventListener kullan**
3. JWT token'i localStorage'da tutmak -> **httpOnly cookie**
4. `console.log`'da hassas veri yazdirmak
5. Dogrudan `fetch()` cagrisi yapmak (`apiFetch()` wrapper'i yerine)
6. Ayni yardimci fonksiyonu birden fazla dosyada tekrar tanımlamak -> **shared module'e tasi**
7. Backend URL'yi koda gommek -> `CONFIG` objesi veya env variable kullan
8. `postMessage` gonderirken `'*'` origin kullanmak -> **`window.location.origin` kullan**
9. CSS'de sabit deger için inline `style="..."` kullanmak -> **CSS class tanımla**
10. Event listener'lari temizlemeden yeniden bind etmek -> **delegation veya cleanup**

---

## 10) Kontrol Listesi

Her frontend degisikligi sonrasi asagidaki kontrol uygulanir:

- [ ] Tum `innerHTML` template'lerinde değişkenler `escapeHtml()` ile sarili
- [ ] Inline event handler yok (onclick, onchange vb.)
- [ ] API cagrilari `apiFetch()` uzerinden
- [ ] JWT httpOnly cookie'de, localStorage'da degil
- [ ] CSRF token unsafe method'larda gonderiliyor
- [ ] Hassas veri maskelenmis gosteriliyor
- [ ] `console.log`'da hassas veri yok
- [ ] CSS cüstom properties kullaniliyor, hardcoded renk/font yok
- [ ] Inline style yalnızca dinamik değerler için (sabit değerler class'ta)
- [ ] Event listener'lar temiz (delegation veya innerHTML ile yeniden render)
- [ ] Toast mesajlari Turkce ve anlaşılır
- [ ] Empty state tasarimi mevcut (bos tablo, bos liste)
- [ ] Responsive breakpoint'lar calisiyor (1240px, 980px)
- [ ] `aria-label` interactive elementlerde mevcut
- [ ] Yardimci fonksiyonlar tekrar tanımlanmamis (shared module'den import)

---

## 11) Gelecek Mimari Hedefi (Referans)

Proje büyüdükçe asagidaki stack'e gecis planlanmaktadir.
Bu bolum **mevcut kurallari gecersiz kilmaz**; yalnızca yol haritasi referansidir.

| Katman | Hedef Teknoloji | Not |
|--------|----------------|-----|
| Framework | React 18+ / Next.js | SPA veya SSR |
| Dil | TypeScript (strict mode) | `any` tipi yasak |
| Stil | Tailwind CSS | Özel CSS minimumda |
| Component Library | Shadcn UI (Radix primitives) | Mevcut kutuphaneden faydalanilir |
| State Management | React Context / Züstand | Basit state Context, karmasik state Züstand |
| HTTP Client | Axios veya fetch + wrapper | Merkezi client |
| Form | React Hook Form + Zod | Validasyon Zod ile |
| Tablo | TanStack Table | Sayfalama, siralama, filtreleme |

**Gecis koşullari:**
- Frontend dosya boyutları 2000+ satıri astiginda
- Birden fazla bagimsiz frontend gelistirici calistiginda
- Karmasik form akislari ve client-side routing ihtiyaci dogdugunda

Bu gecis gerceklestiginde bu bolum "Mevcut Mimari" bolumunun yerine tasinir ve eski kurallar kaldirilir.
