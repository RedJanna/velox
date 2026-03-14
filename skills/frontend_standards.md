# Skill: Frontend Standards (Admin Panel)

> **Hiyerarşi:** Bu dosya `system_prompt_velox.md §0` hiyerarşisinde **Öncelik 3** seviyesindedir.
> Güvenlik (`security_privacy.md`) ve kaynak doğrulama (`anti_hallucination.md`) kuralları bu dosyadan önce gelir.

> Kod bilmeyen biri için benzetme: Bu doküman, admin panelinin **"iç mimar kılavuzu"**dur.
> Her ekran aynı stilde, aynı malzemeyle, aynı düzenle yapılsın diye kurallar koyar.
> Amaç: Panelin tutarlı, bakımı kolay ve güvenli olması.

---

## 0) Bu dokümanın kapsamı

- **Kapsam:** Velox Admin Panel (React/Next.js tabanlı web arayüzü)
- **Kapsam dışı:** Backend API, WhatsApp mesaj formatı, LLM prompt kuralları
- **İlişkili dosyalar:** `coding_standards.md` (backend), `security_privacy.md` (veri güvenliği)

---

## 1) Tech Stack

| Katman | Teknoloji | Not |
|--------|-----------|-----|
| Framework | React 18+ / Next.js | SPA veya SSR — proje kararına göre |
| Dil | TypeScript (strict mode) | `any` tipi yasak |
| Stil | Tailwind CSS | Ek özel CSS minimumda tutulur |
| Component Library | Shadcn UI (Radix primitives) | Mevcut kütüphane varsa **onu kullan** |
| State Management | React Context / Zustand | Basit state Context, karmaşık state Zustand |
| HTTP Client | Axios veya fetch + wrapper | Backend API iletişimi |
| Form | React Hook Form + Zod | Validasyon şeması Zod ile |
| Tablo | TanStack Table | Sayfalama, sıralama, filtreleme |

---

## 2) Temel Kurallar

### 2.1 Kütüphane Disiplini (KRİTİK)
Projede bir UI kütüphanesi (Shadcn UI, Radix, MUI vb.) aktifse **onu kullanmak zorunludur**.

- Kütüphane sağlıyorsa modal, dropdown, button gibi bileşenleri **sıfırdan yazma**.
- Gereksiz CSS ile kütüphane bileşenlerini **çoğaltma**.
- **İstisna:** Kütüphane bileşenini sarmalayıp (wrap) stil verebilirsin, ama alttaki primitive kütüphaneden gelmeli.

**Benzetme:** Otel zaten hazır form kullanıyorsa, aynı bilgiyi toplayan ikinci bir form icat etme.

### 2.2 TypeScript Strict
- `tsconfig.json`'da `strict: true` aktif olmalı.
- `any` tipi **yasak** — `unknown` veya doğru tip kullan.
- API response'ları Zod schema ile parse et, ham JSON'a güvenme.

**Benzetme:** Etiket olmadan kablo çekmek yasak — her kablonun tipi belli olmalı.

### 2.3 Component Yapısı
```
src/
├── components/
│   ├── ui/              # Shadcn UI primitives (Button, Dialog, Input...)
│   ├── layout/          # Header, Sidebar, PageLayout
│   ├── features/        # İş mantığı bileşenleri (ReservationTable, GuestCard...)
│   └── shared/          # Ortak (LoadingSpinner, ErrorBoundary, EmptyState...)
├── pages/ veya app/     # Route bazlı sayfalar
├── hooks/               # Custom hooks (useAuth, useHotelProfile...)
├── lib/                 # Utility fonksiyonlar, API client
├── types/               # TypeScript type tanımları
└── stores/              # Zustand store'ları (gerekirse)
```

### 2.4 İsimlendirme

| Öğe | Kural | Örnek |
|-----|-------|-------|
| Component dosyası | PascalCase | `ReservationTable.tsx` |
| Component adı | PascalCase | `ReservationTable` |
| Hook | camelCase, `use` prefix | `useReservations` |
| Utility fonksiyon | camelCase | `formatCurrency` |
| Sabitler | UPPER_SNAKE_CASE | `MAX_PAGE_SIZE` |
| CSS class (Tailwind) | kebab-case | `bg-primary text-sm` |
| API endpoint path | kebab-case | `/api/admin/hotel-profile` |

### 2.5 Dosya Boyutu
- Hedef: **300 satır/component dosyası** (backend'in 600 satır hedefinden farklı)
- Aşılırsa: Alt bileşenlere böl, custom hook'a çıkar
- **İstisna:** Büyük form bileşenleri (10+ alan) 400 satıra kadar tolere edilir

### 2.6 Prop Drilling Yasak
- 3+ seviye prop geçirme yerine Context veya Zustand kullan
- Her Context provider'ın kendi dosyası olsun (`AuthProvider.tsx`, `HotelProvider.tsx`)

---

## 3) Tasarım Felsefesi: "Bilinçli Minimalizm"

- **Anti-Jenerik:** Standart "bootstrap" görünümünü reddet. Template gibi görünüyorsa yanlıştır.
- **Özgünlük:** Bespoke layout, asimetri ve ayırt edici tipografi hedefle.
- **"Neden" Faktörü:** Her elementi yerleştirmeden önce amacını hesapla. Amacı yoksa sil.
- **Minimalizm:** Azaltma en yüksek zarafettir.
- **Micro-interactions:** Hover, focus, transition efektleri kaliteli olsun.
- **Spacing:** Tutarlı spacing scale (Tailwind'in spacing sistemi).

---

## 4) Güvenlik (Frontend Özel)

### 4.1 XSS Koruması
- Kullanıcıdan gelen metni `dangerouslySetInnerHTML` ile **asla** render etme
- Gerekli HTML render için DOMPurify kullan
- URL parametrelerini doğrudan DOM'a yazmadan önce sanitize et

### 4.2 Auth & Route Koruması
- Admin panel rotaları `ProtectedRoute` wrapper ile korunsun
- JWT token'ı `httpOnly` cookie'de saklanmalı (localStorage'da **değil**)
- Token süresi dolunca kullanıcıyı login'e yönlendir
- CSRF token backend'den alınıp isteklere eklensin

### 4.3 Hassas Veri Gösterimi
- Telefon numaraları admin panelde **maskelenmiş** gösterilir (son 4 hane hariç)
- "Tam göster" butonu ile geçici olarak açılabilir (audit log'a düşmeli)
- Kart/CVV/OTP bilgisi admin panelde **asla** gösterilmez
- Console.log'da hassas veri yazdırmak **yasak** (production build'de log temizlenir)

### 4.4 API İletişimi
- Tüm API çağrıları merkezi bir client üzerinden yapılır (interceptor ile auth header eklenir)
- Hata durumlarında kullanıcıya toast/notification gösterilir, teknik detay gösterilmez
- Request/response interceptor'da hassas veri loglanmaz

---

## 5) Erişilebilirlik (a11y)

- Tüm interactive elementlerde `aria-label` veya `aria-labelledby` olmalı
- Keyboard navigation çalışmalı (Tab sırası mantıklı)
- Renk kontrastı WCAG AA minimum (4.5:1 normal metin, 3:1 büyük metin)
- Focus ring görünür olmalı (Tailwind `focus-visible:ring-2`)
- Form hata mesajları `aria-describedby` ile input'a bağlanmalı

---

## 6) Performans

- **Lazy loading:** Route-level code splitting (`React.lazy` / Next.js dynamic import)
- **Memoization:** Pahalı hesaplamalar `useMemo`, callback'ler `useCallback` ile sarılır
- **Re-render kontrolü:** React DevTools Profiler ile gereksiz render tespit edilir
- **Image optimization:** Next.js `Image` component veya lazy load
- **Bundle size:** Gereksiz kütüphane ekleme — her yeni bağımlılık PR'da gerekçelendirilmeli

---

## 7) Hata Yönetimi (Frontend)

- Her sayfa/route `ErrorBoundary` ile sarılmalı
- API hata durumları:
  - `401` → Login sayfasına yönlendir
  - `403` → "Yetkiniz yok" mesajı
  - `404` → "Bulunamadı" sayfası
  - `500` → "Bir sorun oluştu, lütfen tekrar deneyin" (teknik detay yok)
- Network hatası → "Bağlantı sorunu" toast mesajı
- Form validation hataları inline gösterilmeli (submit sonrası değil, yazarken)

---

## 8) Kesin Yasaklar (Kırmızı Çizgiler)

- `any` tipi kullanma → doğru TypeScript tipi yaz
- `dangerouslySetInnerHTML` direkt kullanma → sanitize et veya kaçın
- JWT token'ı localStorage'da tutma → httpOnly cookie
- Console.log'da hassas veri yazdırma
- Kütüphane varken custom component yazma (modal, dropdown, tooltip, button)
- Inline style kullanma (Tailwind varken)
- `!important` kullanma (istisna: 3rd party override zorunluysa)
- Prop drilling (3+ seviye)
- Backend URL'yi koda gömme → env variable kullan
- Tarihleri `new Date()` ile parse etme → `date-fns` veya `dayjs` kullan

---

## 9) Validation Checklist

- [ ] TypeScript strict mode aktif, `any` yok
- [ ] Tüm API çağrıları merkezi client üzerinden
- [ ] Route koruması var (ProtectedRoute / auth guard)
- [ ] JWT httpOnly cookie'de, localStorage'da değil
- [ ] XSS koruması var (dangerouslySetInnerHTML yok veya sanitized)
- [ ] CSRF token uygulanıyor
- [ ] Hassas veri maskelenmiş gösteriliyor
- [ ] Console.log'da hassas veri yok
- [ ] ErrorBoundary her route'ta var
- [ ] Component dosyaları hedef 300 satır altında
- [ ] Erişilebilirlik: aria-label, keyboard nav, kontrast
- [ ] Tailwind kullanılıyor, inline style yok
- [ ] Kütüphane bileşenleri kullanılıyor (custom component gereksiz yere yok)
- [ ] Lazy loading / code splitting aktif
- [ ] Backend URL env variable'dan geliyor
