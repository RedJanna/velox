# Skill: Frontend Standards (Admin Panel & Chat Lab)

> **Hiyerarsi:** Bu dosya `system_prompt_velox.md` hiyerarsisinde **Oncelik 3** seviyesindedir.
> Guvenlik (`security_privacy.md`) ve kaynak dogrulama (`anti_hallucination.md`) kurallari bu dosyadan once gelir.

> Kod bilmeyen biri icin benzetme: Bu dokuman, admin panelinin **"ic mimar kilavuzu"**dur.
> Her ekran ayni stilde, ayni malzemeyle, ayni duzenle yapilsin diye kurallar koyar.
> Amac: Panelin tutarli, bakimi kolay ve guvenli olmasi.

---

## 0) Bu dokumanin kapsami

- **Kapsam:** Velox Admin Panel (`/admin`) ve Chat Lab (`/admin/chat-lab`) web arayuzleri
- **Kapsam disi:** Backend API, WhatsApp mesaj formati, LLM prompt kurallari
- **Iliskili dosyalar:** `coding_standards.md` (backend), `security_privacy.md` (veri guvenligi)

---

## 1) Mevcut Mimari

Velox frontend'i **Python icine gomulu (embedded) HTML/CSS/JS** mimarisi kullanir.
Bagimsiz bir frontend build pipeline'i yoktur; tum UI kodu FastAPI uygulamasinin parcasidir.

### 1.1 Tech Stack (Mevcut)

| Katman | Teknoloji | Not |
|--------|-----------|-----|
| Render | FastAPI `HTMLResponse` | Python f-string ile HTML assembly |
| Dil | Vanilla JavaScript (ES2020+) | TypeScript yok, tip kontrolu yok |
| Stil | Ozel CSS (CSS custom properties) | Tailwind yok, inline `<style>` bloklari |
| Component | Yok (DOM manipulasyonu) | `innerHTML` template literal ile render |
| State | Global `state` objesi | Framework yok, dogrudan mutation |
| HTTP Client | Native `fetch` + wrapper (`apiFetch`) | Merkezi client, CSRF ve auth destekli |
| Build | Yok | Minification, bundling, tree-shaking mevcut degil |

### 1.2 Dosya Yapisi (Mevcut)

```
src/velox/api/routes/
  admin_panel_ui.py          # Admin panel HTML iskeleti (~510 satir)
  admin_panel_ui_assets.py   # Admin panel CSS + JS (~1620 satir)
  test_chat_ui.py            # Chat Lab HTML iskeleti (~207 satir)
  test_chat_ui_assets.py     # Chat Lab CSS + JS (~966 satir)
```

### 1.3 Mimari Kisitlar

Bu gomulu mimari bilerek secilmistir: tek container, sifir npm bagimliligi, deployment basitligi.
Ancak su kisitlamalari tasir:

- Frontend kodu Python string literal'i icinde yasadigi icin IDE destegi (autocomplete, lint, format) zayiftir.
- JS fonksiyonlari izole degildir; unit test yazmak zordur.
- Dosya boyutlari buyudukce bakimi zorlasir.

---

## 2) Temel Kurallar

### 2.1 XSS Korumasi (KRITIK)

- Kullanicidan veya API'den gelen **her** degisken `escapeHtml()` fonksiyonu ile sanitize edilmelidir.
- `innerHTML` ile render yaparken template literal icindeki **tum** degiskenler `escapeHtml()` ile sarilmalidir.
- **Inline event handler yasaktir** (`onclick="fn()"` gibi). Tum event'ler `addEventListener` ile baglanmalidir.
- URL parametreleri DOM'a yazilmadan once `encodeURIComponent` ile encode edilmelidir.

**Benzetme:** Her musluktan gelen su filtrelenir — kaynagi ne olursa olsun.

### 2.2 `escapeHtml` Kullanim Kurali

```javascript
// DOGRU: Her degisken escaped
`<td>${escapeHtml(item.name)}</td>`

// YANLIS: Degisken dogrudan yazilmis
`<td>${item.name}</td>`

// YASAK: Inline event handler
`<button onclick="doSomething('${value}')">Tikla</button>`

// DOGRU: Event delegation veya addEventListener
button.addEventListener('click', () => doSomething(value));
```

### 2.3 State Yonetimi

- Her UI'nin tek bir `state` objesi vardir. Bu obje global scope'ta tanimlidir.
- State degisiklikleri yalnizca ilgili `load*` veya `on*` fonksiyonlari icerisinde yapilir.
- State'ten okuma yapan render fonksiyonlari (`render*`) state'i **degistirmez**, yalnizca DOM'u gunceller.
- Yeni state alani eklendiginde `clearClientSession()` fonksiyonuna da eklenmesi gerekir.

### 2.4 API Client Kurallari

- Tum API cagrilari merkezi `apiFetch()` fonksiyonu uzerinden yapilir.
- `apiFetch()` otomatik olarak:
  - CSRF token ekler (unsafe method'larda)
  - 401 durumunda token refresh dener
  - Basarisiz refresh'te login ekranina yonlendirir
- Dogrudan `fetch()` cagrisi **yasaktir** (tek istisna: `apiFetchFromAbsolute` gibi acikca tanimlanmis wrapper'lar).
- Hata durumlarinda kullaniciya `notify()` ile toast gosterilir, teknik detay gosterilmez.

### 2.5 Event Yonetimi

- **Event delegation tercih edilir:** Tablo satirlarindaki butonlar icin her satirda ayri listener yerine, ust container'a tek listener baglanmalidir.
- **Listener temizligi:** `bind*Actions()` fonksiyonlari her cagrildiginda eski listener'lar temizlenmelidir. `innerHTML` ile yeniden render edilen alanlarda listener zaten kaybolur, ancak `addEventListener` ile baglanan durable listener'lar icin dikkatli olunmalidir.
- **Inline handler yasak:** `onclick`, `onchange` gibi HTML attribute event handler'lari kullanilmaz.

### 2.6 Isimlendirme

| Oge | Kural | Ornek |
|-----|-------|-------|
| JS fonksiyon | camelCase | `loadConversations`, `renderHoldRows` |
| JS sabit | UPPER_SNAKE_CASE | `API_ROOT`, `CSRF_COOKIE` |
| CSS class | kebab-case | `module-card`, `empty-state` |
| CSS degisken | `--` prefix, kebab-case | `--accent`, `--bg-2` |
| HTML id | camelCase | `conversationTableBody`, `holdFilters` |
| data attribute | kebab-case | `data-nav`, `data-approve-hold` |
| Python fonksiyon | snake_case | `render_admin_panel_html` |

### 2.7 Dosya Boyutu

- **Hedef:** Assets dosyalari 1200 satiri asmamali.
- **Asilarsa:** Ortak yardimci fonksiyonlari ayri bir shared module'e tasi.
- **HTML iskeleti:** 600 satiri asmamali. Asilarsa section'lari ayri fonksiyonlara bol.

---

## 3) Tasarim Felsefesi: "Bilinçli Minimalizm"

- **Anti-Jenerik:** Standart "bootstrap" gorunumunu reddet. Template gibi gorunuyorsa yanlistir.
- **Ozgunluk:** Bespoke layout, asimetri ve ayirt edici tipografi hedefle.
- **"Neden" Faktoru:** Her elementi yerlestirmeden once amacini hesapla. Amaci yoksa sil.
- **Minimalizm:** Azaltma en yuksek zarafettir.
- **Micro-interactions:** Hover, focus, transition efektleri kaliteli olsun.
- **Spacing:** Tutarli spacing scale (CSS custom properties ile).

---

## 4) CSS Kurallari

### 4.1 Custom Properties (Zorunlu)

- Tum renkler, olculer ve font'lar `:root` degiskenleri ile tanimlanir.
- Yeni renk veya spacing eklerken once mevcut degiskenleri kontrol et; gereksiz yeni degisken olusturma.
- Admin Panel ve Chat Lab **ayni degisken isimlerini kullanmalidir** (uyumluluk hedefi).

### 4.2 Inline Style Yasagi

- `style="..."` HTML attribute'u **yalnizca** dinamik degerler icin (JS ile hesaplanan degerler) kullanilabilir.
- Sabit gorunum degerleri (`margin-top:14px`, `min-width:240px` gibi) CSS class'i olarak tanimlanmalidir.
- Yeni sabit gorunum ihtiyaci varsa, mevcut utility class'lari kontrol et veya yeni class ekle.

### 4.3 Responsive Tasarim

- En az uc breakpoint tanimli olmalidir: desktop (varsayilan), tablet (~1240px), mobil (~980px).
- Tablolar dar ekranda yatay scroll veya kart gorunumune gecmelidir.
- Sidebar mobilde collapse olmali, toggle butonu ile acilmalidir.

### 4.4 `!important` Yasagi

- `!important` yalnizca `[hidden]` ve `.hidden` gibi framework-level override'lar icin kullanilabilir.
- Diger tum durumlarda spesifiklik ile cozum uretilmelidir.

---

## 5) Guvenlik (Frontend Ozel)

### 5.1 XSS Korumasi
- `innerHTML` kullanilan her yerde tum degiskenler `escapeHtml()` ile sanitize edilir.
- Inline event handler (`onclick`, `onchange`) **yasaktir** — `addEventListener` kullanilir.
- URL parametreleri DOM'a yazilmadan once sanitize edilir.

### 5.2 Auth & Route Korumasi
- Admin panel JWT token'i `httpOnly` cookie'de saklanir (localStorage'da **degil**).
- Token suresi dolunca otomatik refresh denenir; basarisizsa login ekranina yonlendirilir.
- CSRF token her unsafe request'e (`POST`, `PUT`, `DELETE`) otomatik eklenir.
- Chat Lab iframe icinde calistiginda, token `postMessage` ile gonderilir; origin kontrolu zorunludur.

### 5.3 Hassas Veri Gosterimi
- Telefon numaralari admin panelde **maskelenmis** gosterilir (`phone_display` alani).
- Kart/CVV/OTP bilgisi admin panelde **asla** gosterilmez.
- `console.log`'da hassas veri yazdirmak **yasaktir**.

### 5.4 API Iletisimi
- Tum API cagrilari merkezi `apiFetch()` uzerinden yapilir.
- Hata durumlarinda kullaniciya toast/notification gosterilir, teknik detay gosterilmez.
- API hata mesajlari `extractErrorMessage()` ile parse edilir; ham JSON kullaniciya yansitilmaz.

---

## 6) Erisilebilirlik (a11y)

- Tum interactive elementlerde `aria-label` veya `aria-labelledby` olmalidir.
- Navigasyon icin `<nav>` elementi `aria-label` ile etiketlenmelidir.
- Keyboard navigation calismalidir (Tab sirasi mantikli).
- Renk kontrasti WCAG AA minimum (4.5:1 normal metin, 3:1 buyuk metin).
- Focus ring gorunur olmalidir (CSS `outline` veya `box-shadow` ile).
- Form hata mesajlari `aria-describedby` ile input'a baglanmalidir.
- Dialog/modal elemanlari `<dialog>` HTML elementi ile uygulanmalidir (mevcut durum uygun).

---

## 7) Hata Yonetimi (Frontend)

- API hata durumlari:
  - `401` -> Token refresh dene, basarisizsa login ekranina yonlendir
  - `403` -> "Yetkiniz yok" toast mesaji
  - `404` -> "Bulunamadi" empty state
  - `500` -> "Bir sorun olustu, lutfen tekrar deneyin" (teknik detay yok)
- Network hatasi -> "Baglanti sorunu" toast mesaji
- Form validation hatalari `notify()` ile gosterilir; gerekce net ve Turkce olmalidir.
- JSON parse hatalari icin kullaniciya anlasilir mesaj gosterilir (`Profile JSON parse edilemedi` gibi).

---

## 8) Dil ve Metin Tutarliligi

### 8.1 Temel Kural
- UI metinleri **Turkce** olarak yazilir.
- Teknik terimler (Dashboard, Hold, Ticket, FAQ, Chat Lab) Turkce karsiliklarinin yaygin olmadigi durumlarda Ingilizce kalabilir, ancak **ayni terim her yerde ayni sekilde yazilir**.

### 8.2 Karakter Kurali
- HTML icindeki Turkce metinlerde ozel karakter (`i`, `s`, `g`, `u`, `o`, `c`) kullanilir.
- Ancak **CSS class isimleri ve JS degisken isimleri** ASCII ile sinirli kalir.

### 8.3 Tutarlilik Tablosu

| Terim | Dogru Kullanim | Yanlis Kullanim |
|-------|---------------|----------------|
| Konusmalar | Konusmalar | Conversations |
| Holdlar | Holdlar | Holds / Bekleyen Onaylar (karisik) |
| Ticketlar | Ticketlar | Tickets / Talepler (karisik) |
| Durum | Durum | Status (UI metninde) |
| Aksiyon | Aksiyon | Action (UI metninde) |

---

## 9) Kesin Yasaklar (Kirmizi Cizgiler)

1. `innerHTML` icinde `escapeHtml()` olmadan degisken yazmak -> **XSS riski**
2. Inline event handler (`onclick`, `onchange`) kullanmak -> **addEventListener kullan**
3. JWT token'i localStorage'da tutmak -> **httpOnly cookie**
4. `console.log`'da hassas veri yazdirmak
5. Dogrudan `fetch()` cagrisi yapmak (`apiFetch()` wrapper'i yerine)
6. Ayni yardimci fonksiyonu birden fazla dosyada tekrar tanimlamak -> **shared module'e tasi**
7. Backend URL'yi koda gommek -> `CONFIG` objesi veya env variable kullan
8. `postMessage` gonderirken `'*'` origin kullanmak -> **`window.location.origin` kullan**
9. CSS'de sabit deger icin inline `style="..."` kullanmak -> **CSS class tanimla**
10. Event listener'lari temizlemeden yeniden bind etmek -> **delegation veya cleanup**

---

## 10) Validation Checklist

Her frontend degisikligi sonrasi asagidaki kontrol uygulanir:

- [ ] Tum `innerHTML` template'lerinde degiskenler `escapeHtml()` ile sarili
- [ ] Inline event handler yok (onclick, onchange vb.)
- [ ] API cagrilari `apiFetch()` uzerinden
- [ ] JWT httpOnly cookie'de, localStorage'da degil
- [ ] CSRF token unsafe method'larda gonderiliyor
- [ ] Hassas veri maskelenmis gosteriliyor
- [ ] `console.log`'da hassas veri yok
- [ ] CSS custom properties kullaniliyor, hardcoded renk/font yok
- [ ] Inline style yalnizca dinamik degerler icin (sabit degerler class'ta)
- [ ] Event listener'lar temiz (delegation veya innerHTML ile yeniden render)
- [ ] Toast mesajlari Turkce ve anlasilir
- [ ] Empty state tasarimi mevcut (bos tablo, bos liste)
- [ ] Responsive breakpoint'lar calisiyor (1240px, 980px)
- [ ] `aria-label` interactive elementlerde mevcut
- [ ] Yardimci fonksiyonlar tekrar tanimlanmamis (shared module'den import)

---

## 11) Gelecek Mimari Hedefi (Referans)

Proje buyudukce asagidaki stack'e gecis planlanmaktadir.
Bu bolum **mevcut kurallari gecersiz kilmaz**; yalnizca yol haritasi referansidir.

| Katman | Hedef Teknoloji | Not |
|--------|----------------|-----|
| Framework | React 18+ / Next.js | SPA veya SSR |
| Dil | TypeScript (strict mode) | `any` tipi yasak |
| Stil | Tailwind CSS | Ozel CSS minimumda |
| Component Library | Shadcn UI (Radix primitives) | Mevcut kutuphaneden faydalanilir |
| State Management | React Context / Zustand | Basit state Context, karmasik state Zustand |
| HTTP Client | Axios veya fetch + wrapper | Merkezi client |
| Form | React Hook Form + Zod | Validasyon Zod ile |
| Tablo | TanStack Table | Sayfalama, siralama, filtreleme |

**Gecis kosullari:**
- Frontend dosya boyutlari 2000+ satiri astiginda
- Birden fazla bagimsiz frontend gelistirici calistiginda
- Karmasik form akislari ve client-side routing ihtiyaci dogdugunda

Bu gecis gerceklestiginde bu bolum "Mevcut Mimari" bolumunun yerine tasinir ve eski kurallar kaldirilir.
