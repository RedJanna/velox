# Feature Brief: Velox Customer Ordering Panel Mobile Revision

**Target URL:** `https://velox.nexlumeai.com/order`  
**Project:** Velox / Nexlume customer-facing ordering page  
**Prepared for:** Codex implementation planning  
**Language of this brief:** Turkish  
**Current phase:** Planning / technical preparation  
**Important instruction:** Do not modify backend, frontend, database schema, routes, or production behavior until the implementation phase is explicitly approved.

---

## 1. Objective

Bu çalışmanın amacı, Velox müşteri sipariş sayfasını özellikle **mobil telefon kullanımı** için daha kullanılabilir, daha hızlı anlaşılır, daha profesyonel, daha modern ve daha güvenilir bir sipariş deneyimine dönüştürmektir.

Ana hedef yalnızca görsel güzelleştirme değildir. Asıl hedef şudur:

> Kullanıcı telefondan 10–20 saniye içinde ürünü bulabilmeli, anlayabilmeli, seçenekleri görebilmeli ve siparişe ekleyebilmelidir.

Bu nedenle çalışma; mobil UX, kategori mimarisi, ürün kartı yapısı, dil tutarlılığı, renk/kontrast sistemi, sepet deneyimi, veri yapısı ve ileride ölçeklenebilir menü yönetimi açısından ele alınmalıdır.

---

## 2. Primary Focus

İlk öncelik müşteri tarafındaki sipariş panelidir:

- URL: `/order`
- Dil seçimi
- Menü seçimi
- Kategori gezintisi
- Ürün listeleme
- Ürün kartları
- Ürün detayları
- Sepete ekleme deneyimi
- Mobil görünüm
- Dokunmatik kullanım
- Okunabilirlik
- Sepet / devam etme akışı

Admin panel, restoran yönetim paneli, WhatsApp entegrasyonları, ödeme altyapısı, kullanıcı hesap sistemi ve backend iş mantığı bu çalışmanın ilk odağı değildir. Ancak sipariş panelinin frontend ihtiyaçları backend veri yapısına bağlıysa, bu alanlar yalnızca analiz edilmeli ve öneri olarak raporlanmalıdır.

---

## 3. Current State Summary

Mevcut `/order` sayfası temel olarak çalışan bir sipariş akışına sahiptir. Kullanıcı önce siparişe devam eder, ardından dil seçer, sonra kahvaltı / öğle / akşam gibi menü seçeneklerinden birini seçerek ürünleri görüntüler.

Ancak mevcut yapı mobil kullanım için yeterince rafine değildir. Akış fazla adımlı hissediyor, kategori gezintisi mobilde güçlü değil, bazı ürün/kategori içerikleri PDF’ye yönleniyor, dil seçimi sonrası farklı diller karışabiliyor ve ürün kartları küçük ekranlarda fazla yoğun görünüyor.

Mevcut sayfa teknik olarak çalışsa da, premium ve hızlı bir mobil sipariş deneyimi için yeniden organize edilmelidir.

---

## 4. Core Problems

### 4.1 Mobile Navigation Problems

Mevcut kategori yapısı mobilde yeterince rahat değildir. Kategoriler yatay dizildiğinde kullanıcı kaydırmak zorunda kalır. Küçük ekranda bu durum kategori keşfini zayıflatır.

Beklenen iyileştirme:

- Kategoriler mobilde daha kolay seçilebilir olmalı.
- Kategori alanı gerektiğinde sticky davranabilmeli.
- Uzun kategori listeleri dropdown, bottom sheet veya sade yatay chip sistemiyle çözülebilmeli.
- Kullanıcı hangi kategoride olduğunu net anlayabilmeli.

---

### 4.2 Product Card Density

Ürün kartları aynı anda çok fazla bilgi göstermeye çalışıyor. Mobilde ürün adı, açıklama, içerik, fiyat/onay bilgisi ve butonların aynı alanda sıkışması karar vermeyi zorlaştırır.

Beklenen iyileştirme:

- İlk bakışta ürün adı, kısa açıklama, fiyat ve “Ekle” butonu görünmeli.
- Uzun içerikler detay alanına alınmalı.
- Alerjen, içerik ve seçenek bilgileri sade etiketlerle gösterilmeli.
- Ürün kartları tek elle kullanım için yeterli dokunma alanına sahip olmalı.

---

### 4.3 Language Consistency Problems

Dil seçimi yapıldıktan sonra aynı dil kapsamında tutarlılık sağlanmalıdır. İngilizce seçildiğinde Türkçe ifadeler görünmemeli; Türkçe seçildiğinde de İngilizce sistem metinleri gereksiz şekilde kalmamalıdır.

Tespit edilen problem örnekleri:

- `Tümü`
- `2 seçenek`
- `İçindekiler`
- Türkçe ve İngilizce kategori/ürün adlarının karışması
- Bazı kategori adlarında büyük/küçük harf tutarsızlığı
- Ürün açıklamalarında eksik veya zayıf çeviri

Beklenen iyileştirme:

- Tüm UI metinleri localization sistemine bağlanmalı.
- Her dil için eksiksiz label seti olmalı.
- Ürün adı, kategori adı, açıklama, alerjen bilgisi, fiyat mesajı ve boş durum mesajları aynı dilde olmalı.
- Geçici placeholder metinler profesyonel dile dönüştürülmeli.

---

### 4.4 PDF Menu Problem

Bazı kategorilerin PDF menüye yönlendirilmesi mobil sipariş deneyimini kırar.

PDF sorunları:

- Mobilde yeni sekme / indirme davranışı yaratabilir.
- Yakınlaştırma gerektirebilir.
- Sepete ekleme akışıyla entegre değildir.
- Erişilebilirlik ve çeviri yönetimi zayıftır.
- Ürün verisi sistem içinde yönetilemez.

Beklenen iyileştirme:

- PDF’ye bağlı menüler kademeli olarak yapılandırılmış ürün verisine dönüştürülmeli.
- Tüm ürünler uygulama içinde listelenmeli.
- PDF gerekiyorsa yalnızca ikincil “Menüyü PDF olarak görüntüle” seçeneği olmalı; ana sipariş deneyimi PDF’ye bağlı olmamalıdır.

---

### 4.5 Typography and Contrast Problems

Mevcut tipografi ve renk kontrastı mobilde daha güçlü hale getirilmelidir.

Beklenen iyileştirme:

- Body text minimum 16px hedeflenmeli.
- Ürün adları medium/semi-bold olmalı.
- Fiyatlar daha net ayrışmalı.
- Kategori başlıkları ürün adlarından belirgin şekilde farklı olmalı.
- Normal metinlerde WCAG AA düzeyinde yeterli kontrast hedeflenmeli.
- Açık bej zemin üzerinde zayıf gri metinlerden kaçınılmalı.

---

## 5. Target UX Principles

Yeni deneyim aşağıdaki prensiplerle tasarlanmalıdır:

1. **Mobile-first:** Önce mobil ekran çözülmeli, sonra tablet/desktop uyarlanmalıdır.
2. **Fast decision-making:** Kullanıcı ürünü hızlıca bulup karar verebilmelidir.
3. **Clear hierarchy:** Ürün adı, fiyat ve işlem butonu net ayrışmalıdır.
4. **Minimal friction:** Gereksiz adım, gereksiz scroll ve gereksiz PDF yönlendirmesi azaltılmalıdır.
5. **Consistent language:** Seçilen dil tüm arayüzde eksiksiz uygulanmalıdır.
6. **Structured data:** Menü içeriği mümkün olduğunca frontend içinde hard-coded olmamalıdır.
7. **Accessible by default:** Renk, kontrast, dokunma alanı ve font boyutu erişilebilirlik odaklı olmalıdır.
8. **Premium but usable:** Tasarım modern ve premium görünmeli fakat okunabilirlikten ödün vermemelidir.

---

## 6. Proposed Revision Phases

Aşağıdaki fazlar sıralı ilerlemelidir. Codex her faz sonunda yapılanları özetlemeli, riskleri belirtmeli ve bir sonraki faza geçmeden önce onay istemelidir.

---

# Phase 0 — Codebase Inspection and Mapping

## Purpose

Mevcut projenin `/order` sayfasını nasıl ürettiğini, hangi dosyalara bağlı olduğunu, hangi verinin nereden geldiğini ve frontend/backend sınırlarının nerede olduğunu netleştirmek.

## Allowed Actions

- Dosya yapısını incele.
- `/order` route’unu bul.
- İlgili frontend componentlerini veya template dosyalarını tespit et.
- Ürün/kategori/dil verisinin nereden geldiğini incele.
- PDF menü linklerinin nerede tanımlandığını bul.
- Çeviri dosyaları veya localization mantığı varsa haritala.
- Sepet akışını ve state management yapısını incele.
- Mobil CSS / responsive breakpoint kullanımını incele.

## Not Allowed

- Kod değiştirme.
- Dosya silme.
- Yeni dependency ekleme.
- Backend endpoint değiştirme.
- Database migration oluşturma.
- Üretim verisine müdahale etme.

## Output Required

Codex şu başlıklarla kısa ama net bir rapor üretmelidir:

```md
## Phase 0 Inspection Report

### Relevant Files
- ...

### Current /order Flow
- ...

### Data Sources
- ...

### Localization Structure
- ...

### PDF Menu Usage
- ...

### Frontend Architecture Notes
- ...

### Backend Architecture Notes
- ...

### Risks
- ...

### Recommended Next Step
- ...
```

## Stop Condition

Phase 0 tamamlandıktan sonra dur. Kod değişikliği yapma. Uygulama fazına geçmeden önce onay bekle.

---

# Phase 1 — UX Architecture and Menu Structure Planning

## Purpose

Mevcut sipariş akışını mobil-first mantıkla yeniden planlamak.

## Tasks

- Mevcut adım sayısını değerlendir.
- Dil seçimi, menü seçimi ve ürün listeleme akışını sadeleştir.
- Kategori mimarisini yeniden öner.
- Breakfast / Lunch / Dinner ayrımının korunup korunmayacağını değerlendir.
- PDF kategorilerinin uygulama içi kategoriye nasıl dönüştürüleceğini planla.
- Ürün kartı bilgi hiyerarşisini tanımla.
- Sepet görünürlüğünü ve mobil CTA davranışını planla.

## Recommended Target Flow

Önerilen mobil akış:

1. Kullanıcı `/order` sayfasına gelir.
2. Üst alanda restoran/oda/masa bilgisi görünür.
3. Dil seçimi küçük ama erişilebilir bir kontrol olarak kalır.
4. Arama alanı görünür veya sticky hale gelir.
5. Kategori seçimi kullanıcıyı yormadan sunulur.
6. Ürün kartları sade şekilde listelenir.
7. Sepet alt barda sabit görünür.
8. Kullanıcı sepete gidip siparişi onaylar.

## Suggested Menu Structure

```md
Breakfast
- Breakfast Plates
- Hot Breakfast Items
- Eggs
- Bakery
- Hot Drinks
- Cold Drinks

Food
- Starters
- Hot Starters
- Salads
- Main Courses
- Seafood
- Meat & Chicken
- Vegetarian
- Burgers & Sandwiches
- Desserts

Drinks
- Hot Drinks
- Cold Drinks
- Cocktails
- Wine
- Non-Alcoholic Specials
```

Not: Gerçek kategori isimleri mevcut ürünlere göre uyarlanmalıdır. Codex önce mevcut ürün verisini incelemeli, sonra uygulanabilir kategori önerisi çıkarmalıdır.

## Output Required

```md
## Phase 1 UX Architecture Proposal

### Recommended User Flow
- ...

### Recommended Category Structure
- ...

### Product Card Information Hierarchy
- ...

### Mobile Navigation Model
- ...

### Cart / CTA Behavior
- ...

### Open Questions
- ...
```

## Stop Condition

Bu faz sonunda kod yazma. Yeni akış onaylanmadan uygulama yapma.

---

# Phase 2 — Localization and Content Consistency Plan

## Purpose

Dil karışıklığını ortadan kaldırmak ve tüm arayüz metinlerini seçilen dile göre tutarlı hale getirmek.

## Tasks

- Tüm UI stringlerini listele.
- Türkçe kalan İngilizce ekran metinlerini tespit et.
- İngilizce kalan Türkçe ekran metinlerini tespit et.
- Kategori adlarını standardize et.
- Ürün adlarında hangi terimlerin çevrileceğini, hangilerinin korunacağını belirle.
- Placeholder metinleri profesyonelleştir.
- “Price confirmed by staff” gibi ifadeleri kullanıcı güvenini zedelemeyecek şekilde yeniden ele al.
- İçerik, alerjen, opsiyon ve fiyat mesajları için dil dosyası mantığını netleştir.

## Required Localization Rules

- English selected → no Turkish UI labels.
- Turkish selected → no unnecessary English UI labels.
- Category casing must be consistent.
- Same concept must use the same translation everywhere.
- Product descriptions must be short, clear and appetizing.
- Ingredient and allergen labels must be consistent.
- Empty states and error messages must also be localized.

## Example Translation Corrections

```md
Tümü → All
2 seçenek → 2 options
İçindekiler → Ingredients
Sepete Ekle → Add to cart
Devam → Continue
Geri → Back
Fiyat personel onayı ile → Ask staff for current price
```

## Output Required

```md
## Phase 2 Localization Plan

### Current Mixed-Language Issues
- ...

### Required Translation Keys
- ...

### Suggested TR Labels
- ...

### Suggested EN Labels
- ...

### Product Naming Rules
- ...

### Content Risks
- ...
```

## Stop Condition

Bu fazda yalnızca plan oluştur. Dil dosyalarını değiştirme.

---

# Phase 3 — UI Design System and Mobile Component Specification

## Purpose

Mobil sipariş deneyimi için uygulanabilir UI kuralları, component yapıları ve görsel tasarım sistemi tanımlamak.

## Target Components

- Order page header
- Language selector
- Meal/category selector
- Search input
- Category chips / dropdown / bottom sheet
- Product card
- Product detail expansion
- Quantity stepper
- Add-to-cart button
- Sticky cart bar
- Empty state
- Loading state
- Error state
- PDF fallback notice, if still required

## Product Card Target Structure

Önerilen ürün kartı yapısı:

```md
[Product Name]                         [Price]
Short description, max 1–2 lines.

[Dietary tags / allergen indicators]

[-] [quantity] [+]     [Add]
```

Detay alanı:

```md
Ingredients
Allergens
Options
Preparation note
```

## Visual Rules

- Background: warm off-white or light stone tone.
- Card background: near-white, slightly warm.
- Text: dark charcoal / dark brown.
- Secondary text: medium neutral tone, not too pale.
- CTA: one strong primary color.
- Accent colors: limited and consistent.
- Avoid multiple competing gradients.
- Avoid low-contrast text on beige backgrounds.
- Avoid decorative typography for body text.

## Typography Rules

- Body: minimum 16px.
- Product name: 16–18px, medium/semi-bold.
- Price: 16–18px, bold.
- Category title: 20–24px.
- Secondary text: 14–15px, but must remain readable.
- Buttons: 15–16px, medium/semi-bold.

## Touch Target Rules

- Primary buttons should be at least 44px high.
- Category chips should be easy to tap.
- Quantity controls should not be too close together.
- Sticky cart bar should not cover content.

## Output Required

```md
## Phase 3 UI Component Specification

### Design Tokens
- ...

### Component Specs
- ...

### Mobile Breakpoints
- ...

### Interaction States
- ...

### Accessibility Notes
- ...

### Risks
- ...
```

## Stop Condition

Bu faz sonunda yalnızca teknik UI planı üret. Henüz componentleri değiştirme.

---

# Phase 4 — Data Model and Backend Readiness Assessment

## Purpose

Mevcut backend/veri yapısının mobil-first sipariş deneyimini destekleyip desteklemediğini değerlendirmek.

## Tasks

- Ürünlerin frontend içinde hard-coded olup olmadığını incele.
- Ürün, kategori, fiyat, açıklama, çeviri ve PDF linklerinin nerede tutulduğunu belirle.
- Backend API varsa endpointleri haritala.
- Ürün bulunabilirlik / stok / fiyat güncelleme mantığını incele.
- Çok dilli ürün verisi destekleniyor mu kontrol et.
- PDF’ye bağlı alanların structured data’ya dönüştürülmesi için öneri hazırla.

## Suggested Product Schema

```json
{
  "product_id": "string",
  "category_id": "string",
  "meal_period": "breakfast | lunch | dinner | all_day",
  "name": {
    "tr": "string",
    "en": "string"
  },
  "description": {
    "tr": "string",
    "en": "string"
  },
  "ingredients": {
    "tr": ["string"],
    "en": ["string"]
  },
  "allergens": ["gluten", "milk", "nuts"],
  "dietary_tags": ["vegetarian", "vegan", "gluten_free"],
  "price": 0,
  "currency": "TRY",
  "image_url": "string",
  "is_available": true,
  "sort_order": 0
}
```

## Backend Decision Rules

- Eğer mevcut backend ürün/kategori/dil verisini destekliyorsa, korunmalı ve iyileştirilmelidir.
- Eğer ürünler hard-coded ise, structured data yapısına geçiş planı çıkarılmalıdır.
- Eğer PDF ana veri kaynağıysa, bu yapı uzun vadede refactor edilmelidir.
- Backend tamamen silinmemelidir; önce mevcut yapı analiz edilmelidir.

## Output Required

```md
## Phase 4 Backend Readiness Report

### Current Data Flow
- ...

### Current Product Source
- ...

### Current Category Source
- ...

### Current Localization Source
- ...

### PDF Dependencies
- ...

### Recommended Data Model
- ...

### Refactor Level
- Light / Medium / Heavy

### Risks
- ...
```

## Stop Condition

Bu fazda backend değiştirme. Sadece değerlendirme ve plan üret.

---

# Phase 5 — Implementation Plan

## Purpose

Onaylanan UX, UI, localization ve data kararlarına göre uygulama planı hazırlamak.

## Important

Bu faza yalnızca Phase 0–4 raporları onaylandıktan sonra geçilmelidir.

## Implementation Order

1. Localization cleanup
2. Category navigation refactor
3. Product card redesign
4. Sticky mobile cart bar
5. Search/filter improvement
6. PDF fallback reduction
7. Accessibility improvements
8. Responsive breakpoint cleanup
9. Testing and QA

## Implementation Rules

- Küçük ve geri alınabilir commit mantığıyla ilerle.
- Her değişiklikten sonra ilgili sayfayı test et.
- Eski işlevselliği kırma.
- Sepete ekleme, ürün seçme, dil değiştirme gibi kritik akışları her adımda kontrol et.
- Yeni dependency ekleme gerekiyorsa önce gerekçe sun.
- Backend değişikliği gerekiyorsa önce migration riskini açıkla.
- Production data veya secrets dosyalarına dokunma.

## Output Required Before Coding

```md
## Phase 5 Implementation Plan

### Files to Change
- ...

### Components to Refactor
- ...

### Data/Localization Changes
- ...

### Risk Level
- Low / Medium / High

### Test Plan
- ...

### Rollback Plan
- ...
```

---

# Phase 6 — QA and Acceptance Testing

## Purpose

Yapılan değişikliklerin mobil kullanım, erişilebilirlik, dil tutarlılığı ve sipariş akışı açısından doğru çalıştığını doğrulamak.

## Required Manual Tests

### Mobile Device Tests

- iPhone Safari
- Android Chrome
- 360px width viewport
- 390px width viewport
- 430px width viewport
- Tablet breakpoint
- Desktop breakpoint

### User Flow Tests

- `/order` açılır.
- Dil seçilir.
- Kategori seçilir.
- Ürün aranır.
- Ürün sepete eklenir.
- Ürün adedi değiştirilir.
- Ürün çıkarılır.
- Sepete gidilir.
- Geri dönülür.
- Dil değiştirildiğinde içerik doğru güncellenir.

### Localization Tests

- English seçildiğinde Türkçe UI label kalmamalı.
- Türkçe seçildiğinde gereksiz İngilizce label kalmamalı.
- Kategori adları tutarlı olmalı.
- Ürün açıklamaları aynı dilde görünmeli.
- Hata ve boş durum mesajları çevrilmiş olmalı.

### Accessibility Tests

- Text contrast yeterli olmalı.
- Button tap area yeterli olmalı.
- Focus state görünür olmalı.
- Görseller varsa alt text bulunmalı.
- Renk tek başına bilgi taşımamalı.
- Fontlar mobilde okunabilir olmalı.

### Performance Tests

- İlk yükleme hızlı olmalı.
- Büyük ürün listelerinde scroll takılmamalı.
- PDF veya büyük asset kullanımı azaltılmalı.
- Görseller varsa lazy load uygulanmalı.

## Acceptance Criteria

Bu çalışma ancak aşağıdaki koşullar sağlandığında tamamlanmış kabul edilir:

- Mobilde kategori seçimi rahat ve anlaşılır.
- Ürün kartları okunabilir ve hızlı taranabilir.
- Sepet / devam et aksiyonu her zaman net.
- İngilizce ve Türkçe arayüzler tamamen tutarlı.
- PDF ana sipariş akışının parçası değil.
- Normal ürün metinleri yeterli kontrasta sahip.
- Kullanıcı bir ürünü hızlıca bulup sepete ekleyebiliyor.
- Desktop görünüm bozulmamış.
- Mevcut sipariş işlevi kırılmamış.

---

## 7. Out of Scope

Aşağıdakiler bu çalışmanın kapsamı dışında tutulmalıdır:

- Admin panelin komple yeniden tasarımı
- WhatsApp API akışlarının değiştirilmesi
- Ödeme sistemi eklenmesi
- Kullanıcı üyelik sistemi eklenmesi
- Masa QR mantığının değiştirilmesi
- Restaurant operasyon paneli refactor’u
- Tam CMS geliştirme, eğer ayrıca onaylanmadıysa
- Veritabanı migration işlemi, eğer ayrıca onaylanmadıysa
- Production deployment, eğer ayrıca onaylanmadıysa

---

## 8. Technical Guardrails for Codex

Codex aşağıdaki kurallara uymalıdır:

1. Önce inceleme yap, sonra plan öner.
2. Onay almadan kod değiştirme.
3. Mevcut mimariyi varsayma; dosyalardan doğrula.
4. Yeni framework veya dependency ekleme.
5. Backend’i silme veya yeniden yazma önerisi yapmadan önce mevcut yapıyı raporla.
6. PDF bağımlılıklarını tespit et ama hemen kaldırma.
7. Localization yapısını tespit etmeden metinleri hard-code etme.
8. Responsive düzeltmeleri yalnızca ilgili component kapsamıyla sınırla.
9. Sepet, dil seçimi ve ürün ekleme akışlarını kırma.
10. Her faz sonunda dur ve rapor üret.

---

## 9. Questions Codex Should Answer Before Implementation

Codex uygulamaya başlamadan önce şu soruları cevaplamalıdır:

1. `/order` sayfası hangi dosyalardan oluşuyor?
2. Ürün verileri nereden geliyor?
3. Kategori verileri nereden geliyor?
4. Çeviri sistemi var mı?
5. PDF menüler hangi dosyalarda veya veri kaynaklarında tanımlı?
6. Sepet state’i nerede yönetiliyor?
7. Mobil responsive kuralları nerede yazılmış?
8. Hangi dosyalar güvenli şekilde değiştirilebilir?
9. Backend değişikliği gerekiyor mu, yoksa frontend refactor yeterli mi?
10. En düşük riskli ilk uygulama adımı nedir?

---

## 10. Recommended First Command / Prompt for Codex

Aşağıdaki metin Codex’e ilk mesaj olarak verilebilir:

```md
Read this brief fully before making any changes.

We are improving the customer-facing `/order` page for Velox/Nexlume with a mobile-first UX focus. In this first step, do not modify any code. Inspect the codebase and produce the Phase 0 Inspection Report requested in this brief.

Focus on:
- relevant files for `/order`
- frontend architecture
- data source for products/categories
- localization structure
- PDF menu dependencies
- cart state and order flow
- responsive/mobile CSS
- technical risks

Stop after the report. Do not edit files, do not refactor, do not add dependencies, and do not change backend behavior.
```

---

## 11. Final Direction

Bu çalışma, yalnızca arayüzü “daha güzel” yapmak için değil, sipariş deneyimini gerçek mobil kullanıcı davranışına göre yeniden düzenlemek için yapılmalıdır.

Başarı ölçütü:

> Kullanıcı, küçük telefon ekranında menüyü rahatça gezebilmeli, seçtiği dili tutarlı şekilde görmeli, ürünü hızlıca anlamalı ve siparişe güvenle devam edebilmelidir.
