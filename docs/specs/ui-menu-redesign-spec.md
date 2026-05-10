````md
# Feature Brief: Admin Panel Menu Redesign

## 1. Objective

Bu çalışmanın amacı, otel AI resepsiyon yönetim panelindeki menü ve navigasyon yapısını daha net, daha hızlı taranabilir, daha düzenli ve daha operasyonel hale getirmektir.

Codex, bu brief’i uygularken admin panelin sidebar, menü grupları, aktif durumları, rol bazlı görünürlük, responsive davranış ve erişilebilirlik kurallarını iyileştirmelidir.

Bu çalışma görsel olarak premium, sakin, profesyonel ve işlevsel bir admin panel navigasyonu üretmelidir.

---

## 2. Scope

Codex aşağıdaki alanlarda değişiklik yapabilir:

- Sidebar / navigation component’leri
- Menü grupları
- Menü item sıralaması
- Menü item etiketleri
- Menü aktif / hover / disabled durumları
- Menü ikon kullanımı
- Sidebar collapse / expand davranışı
- Mobile drawer / sheet navigation davranışı
- Rol bazlı menü görünürlüğü
- Breadcrumb ile menü ilişkisi
- Menü badge gösterimi
- Menü erişilebilirliği
- Menü config dosyası
- Menü route aktifliği helper fonksiyonları
- Sidebar state yönetimi
- Tailwind class düzenlemeleri
- shadcn/ui tabanlı navigation component kullanımı

Codex aşağıdaki dosya yapısını oluşturabilir veya mevcut yapıya uygun şekilde güncelleyebilir:

```txt
src/
  config/
    navigation.ts
  components/
    layout/
      app-shell.tsx
      app-sidebar.tsx
      app-topbar.tsx
      app-breadcrumb.tsx
    navigation/
      nav-group.tsx
      nav-item.tsx
      nav-badge.tsx
      nav-collapse-toggle.tsx
      command-menu.tsx
  hooks/
    use-current-role.ts
    use-sidebar-state.ts
    use-active-route.ts
  lib/
    navigation/
      filter-navigation-by-role.ts
      get-active-navigation-item.ts
      format-nav-badge.ts
````

---

## 3. Out of Scope

Codex aşağıdaki alanlara dokunmamalıdır:

* Backend authorization sistemi
* Authentication akışı
* Login / register ekranları
* Database schema
* Database migration
* API endpoint yapısı
* Business logic
* Reservation, guest, sales veya AI modüllerinin iç işleyişi
* Sayfa içi form yapıları
* Dashboard grafiklerinin veri mantığı
* Yeni sayfa oluşturma
* Yeni backend servisi yazma
* Yeni dependency ekleme
* Mevcut route permission sistemini değiştirme
* Kullanıcı rolleri veri modelini değiştirme

Codex yalnızca navigasyon ve menü arayüzünü düzenlemelidir.

---

## 4. Current Problems

Mevcut admin panel menülerinde aşağıdaki problemler vardır:

* Menü yapısı karışık.
* Kullanıcı hangi sayfada olduğunu hızlı anlayamıyor.
* Görsel hiyerarşi zayıf.
* Aktif menü durumu yeterince belirgin değil.
* Menü grupları görev mantığına göre ayrılmamış.
* Menü item’ları günlük kullanım önceliğine göre sıralanmamış.
* Rol bazlı sadeleşme yetersiz.
* Sidebar gereğinden kalabalık görünüyor.
* İkon kullanımı tutarsız olabilir.
* Mobil kullanım yeterince net değil.
* Hover, active ve disabled durumları standart değil.
* Menü arayüzü premium ve operasyonel görünümden uzak olabilir.

---

## 5. Target UX Behavior

Yeni navigasyon yapısı aşağıdaki davranışları sağlamalıdır:

* Kullanıcı ana görevlerine en fazla 2 tıklama ile ulaşabilmelidir.
* Kullanıcı bulunduğu sayfayı sidebar, breadcrumb ve page title üzerinden net anlayabilmelidir.
* Menü grupları teknik yapıya göre değil, kullanıcı görevlerine göre düzenlenmelidir.
* Admin, operasyon, satış ve destek kullanıcıları yalnızca kendi işleriyle ilgili menüleri görmelidir.
* Ana operasyonel sayfalar dropdown içine saklanmamalıdır.
* Menü, kullanıcının günlük çalışma akışını hızlandırmalıdır.
* Menüde aynı anda gereksiz seçenekler gösterilmemelidir.
* Kritik aksiyon gerektiren işler badge ile gösterilmelidir.
* Badge yalnızca kullanıcı aksiyonu gerektiren durumlarda kullanılmalıdır.
* Kullanıcı collapsed sidebar kullanıyorsa menü item’larını tooltip ile anlayabilmelidir.
* Mobilde menü drawer olarak açılmalı ve seçim sonrası kapanmalıdır.

---

## 6. Target UI Rules

Arayüz aşağıdaki kurallara uymalıdır:

* UI MUST clean, premium, calm ve operational dashboard hissi vermelidir.
* UI MUST modern fakat trend odaklı veya dekoratif görünmemelidir.
* UI MUST günlük operasyon kullanımı için hızlı taranabilir olmalıdır.
* UI MUST güçlü görsel hiyerarşi sağlamalıdır.
* UI MUST düşük görsel gürültüye sahip olmalıdır.
* UI MUST tutarlı spacing kullanmalıdır.
* UI MUST sade renk sistemi kullanmalıdır.
* UI MUST text, icon ve badge arasında net öncelik kurmalıdır.

### Visual Style Rules

* Sidebar arka planı ana içerikten hafif ayrışmalıdır.
* Menü item’ları kart gibi görünmemelidir.
* Heavy shadow kullanılmamalıdır.
* Gradient kullanılmamalıdır.
* Glassmorphism kullanılmamalıdır.
* Çok renkli ikon kullanılmamalıdır.
* Ana navigasyon metni düşük kontrast olmamalıdır.
* Menü item yüksekliği tutarlı olmalıdır.
* Aktif item görsel olarak açıkça ayrışmalıdır.

### Suggested Visual Measurements

```txt
Expanded sidebar width: 280px
Collapsed sidebar width: 72px
Menu item height: 40px minimum
Recommended primary item height: 44px
Icon size: 18px
Menu text size: 14px
Group label size: 11px
Group label letter spacing: 0.04em
Horizontal item padding: 12px
Group vertical spacing: 20px
Item gap: 6px
```

### Typography Rules

* Menu item text MUST use `text-sm font-medium`.
* Active menu item MUST use stronger weight, such as `font-semibold`.
* Group labels MUST use `text-[11px] font-semibold uppercase tracking-wide`.
* Secondary text MUST use `text-xs text-muted-foreground`.
* Disabled item MUST use `opacity-50 cursor-not-allowed`.

---

## 7. Navigation / Menu Rules

### Main Menu Groups

Menü grupları aşağıdaki sırayla kullanılmalıdır:

1. Genel Bakış
2. Resepsiyon
3. Rezervasyonlar
4. Misafirler
5. Operasyon
6. Satış
7. AI Yönetimi
8. Raporlar
9. Ayarlar

### Suggested Navigation Structure

```txt
Genel Bakış
  - Dashboard

Resepsiyon
  - Canlı Konuşmalar
  - AI Devralmaları
  - Gelen Talepler

Rezervasyonlar
  - Tüm Rezervasyonlar
  - Bugünkü Girişler
  - Bugünkü Çıkışlar

Misafirler
  - Misafir Profilleri
  - Segmentler

Operasyon
  - Görevler
  - Oda Durumu
  - Bakım Talepleri

Satış
  - Leadler
  - Teklifler
  - Kampanyalar

AI Yönetimi
  - Bilgi Bankası
  - Yanıt Kuralları
  - Otomasyonlar

Raporlar
  - Operasyon Raporları
  - Satış Raporları
  - AI Performansı

Ayarlar
  - Otel Ayarları
  - Kullanıcılar ve Roller
  - Entegrasyonlar
```

### Route Rules

Aşağıdaki route yapısı kullanılabilir. Mevcut projede farklı route varsa Codex mevcut route’lara uyarlama yapmalıdır; yeni route üretmeden önce mevcut route yapısını kontrol etmelidir.

```txt
/dashboard

/reception/conversations
/reception/handoffs
/reception/requests

/reservations
/reservations/check-ins
/reservations/check-outs

/guests
/guests/segments

/operations/tasks
/operations/rooms
/operations/maintenance

/sales/leads
/sales/offers
/sales/campaigns

/ai/knowledge-base
/ai/response-rules
/ai/automations

/reports/operations
/reports/sales
/reports/ai-performance

/settings/property
/settings/users
/settings/integrations
```

### Role Visibility Rules

```txt
admin:
  MUST see all navigation groups.

operations:
  MUST see Genel Bakış, Resepsiyon, Rezervasyonlar, Misafirler, Operasyon, Raporlar.
  MUST NOT see Satış unless already allowed by existing product permissions.
  MUST NOT see AI Yönetimi.
  MUST NOT see Ayarlar.

sales:
  MUST see Genel Bakış, Rezervasyonlar, Misafirler, Satış, Raporlar.
  MUST NOT see Operasyon maintenance pages unless already allowed.
  MUST NOT see AI Yönetimi.
  MUST NOT see Ayarlar.

support:
  MUST see Genel Bakış, Resepsiyon, Misafirler.
  MUST NOT see Satış.
  MUST NOT see AI Yönetimi.
  MUST NOT see Ayarlar.
```

### Menu Config Rules

Navigation data MUST be centralized.

Recommended file:

```txt
src/config/navigation.ts
```

Recommended type structure:

```ts
type UserRole = "admin" | "operations" | "sales" | "support";

type NavigationItem = {
  id: string;
  label: string;
  href: string;
  icon?: string;
  group: string;
  order: number;
  roles: UserRole[];
  badge?: {
    type: "count" | "status";
    sourceKey: string;
  };
  children?: NavigationItem[];
  exactMatch?: boolean;
};
```

### Active State Rules

Active menu item MUST include:

* Visible background state
* Stronger text color
* Stronger font weight
* Left 2px accent indicator
* Active icon color
* `aria-current="page"`

Suggested active style:

```txt
bg-muted text-foreground font-semibold before:absolute before:left-0 before:h-5 before:w-[2px] before:rounded-full before:bg-primary
```

### Hover Rules

Hover state SHOULD be subtle.

Suggested hover style:

```txt
hover:bg-muted/60 hover:text-foreground
```

Hover state MUST NOT use:

* Scale animation
* Heavy shadow
* Gradient
* Layout-shifting border
* Overly colorful background

### Collapse / Expand Rules

Desktop sidebar MUST support:

* Expanded state
* Collapsed state
* LocalStorage persistence
* Tooltip in collapsed mode
* Icon-only display in collapsed mode

Collapsed sidebar MUST:

* Show icons only
* Keep item hit area minimum 44px
* Show tooltip on hover/focus
* Preserve active state visibility

Expanded sidebar MUST:

* Show group labels
* Show item labels
* Show badges where applicable
* Show collapsible child items where applicable

### Nested Menu Rules

* Sidebar MUST NOT use 3rd-level nested menus.
* Sidebar MAY use 2nd-level children.
* Active route parent group MUST open automatically.
* User manually opened groups SHOULD stay open across route changes.
* Empty groups after role filtering MUST NOT render.

### Badge Rules

Badge SHOULD only be used for actionable operational counts.

Allowed badge locations:

* Canlı Konuşmalar
* AI Devralmaları
* Gelen Talepler
* Bugünkü Girişler
* Görevler
* Bakım Talepleri

Badge rules:

* Badge MUST NOT render when value is `0`.
* Badge MUST show `99+` if value is greater than `99`.
* Badge MUST NOT fetch data inside `NavItem`.
* Badge data SHOULD come from parent layout, provider, or existing state.
* Badge color MUST be semantically meaningful.
* Badge MUST NOT use random colors.

### Icon Rules

* Each menu item SHOULD use one icon maximum.
* Icons MUST be visually consistent.
* Icons SHOULD be outline style.
* Icon size SHOULD be 18px.
* Decorative icons MUST use `aria-hidden="true"`.
* Random icons MUST NOT be used.
* Multi-color icons MUST NOT be used.

---

## 8. Responsive Rules

### Breakpoints

```txt
< 768px:
  Use mobile drawer navigation.

768px - 1023px:
  Use collapsed sidebar by default.

>= 1024px:
  Use expanded sidebar by default.
```

### Desktop Rules

* Sidebar MUST be visible.
* Sidebar MUST support expanded and collapsed states.
* Sidebar SHOULD remain fixed or layout-stable.
* Main content MUST align correctly with sidebar width.
* Sidebar content SHOULD scroll independently if needed.
* Topbar SHOULD align with main content area.

### Tablet Rules

* Sidebar SHOULD start collapsed.
* Tooltip SHOULD be available on hover-capable devices.
* Touch target MUST be at least 44px.
* Collapsed sidebar MUST remain usable without text labels.

### Mobile Rules

* Sidebar MUST NOT be permanently visible.
* Navigation MUST open as drawer / sheet.
* Drawer trigger MUST be placed in the top bar.
* Drawer width SHOULD be `min(88vw, 360px)`.
* Drawer MUST close when user selects a menu item.
* Drawer MUST close with ESC.
* Drawer MUST close when overlay is clicked.
* Body scroll SHOULD be locked while drawer is open.
* Mobile MUST NOT use icon-only collapsed sidebar.
* Mobile menu MUST preserve group labels.

---

## 9. Accessibility Rules

### Semantic Navigation

Sidebar MUST use semantic navigation:

```tsx
<nav aria-label="Main navigation">
```

Active item MUST use:

```tsx
aria-current="page"
```

Collapsible trigger MUST use:

```tsx
aria-expanded={isOpen}
aria-controls="menu-group-id"
```

### Keyboard Rules

* All menu items MUST be reachable with Tab.
* Enter MUST activate navigation links.
* Space MUST toggle collapsible menu groups.
* ESC MUST close mobile drawer.
* Focus state MUST be visible.
* Disabled items MUST NOT be focusable unless there is a clear reason.

### Focus State

Suggested focus style:

```txt
focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2
```

### Contrast Rules

* Main menu text MUST meet WCAG AA contrast.
* Low contrast muted text MUST NOT be used for primary menu labels.
* Disabled state MUST use both visual and semantic indication.
* Disabled items SHOULD use `aria-disabled`.
* Critical badge meaning MUST NOT rely on color alone.

### Hit Area Rules

```txt
Desktop minimum hit area: 40px
Touch minimum hit area: 44px
Collapsed icon button minimum width: 44px
```

---

## 10. Technical Implementation Notes

### Component Responsibilities

#### `app-shell.tsx`

MUST:

* Compose sidebar, topbar and main content layout.
* Apply responsive layout structure.
* Keep main content aligned with sidebar state.

MUST NOT:

* Hard-code navigation items.
* Perform role filtering inline.
* Contain route matching logic.

#### `app-sidebar.tsx`

MUST:

* Render navigation groups.
* Support expanded and collapsed states.
* Render desktop navigation.
* Use filtered navigation data.

MUST NOT:

* Fetch badge data directly.
* Manage backend permissions.
* Hide unauthorized items with CSS only.

#### `nav-item.tsx`

MUST:

* Render a single navigation item.
* Apply active, hover, disabled and badge states.
* Apply `aria-current` when active.
* Render tooltip in collapsed mode.

MUST NOT:

* Filter roles.
* Own navigation config.
* Fetch data.
* Contain business logic.

#### `filter-navigation-by-role.ts`

MUST:

* Filter navigation items by current role.
* Filter child items recursively.
* Remove empty groups.

MUST NOT:

* Generate UI classes.
* Perform API calls.
* Change route permissions.

#### `get-active-navigation-item.ts`

MUST:

* Determine active item from pathname.
* Support exact and prefix matching.
* Return active group and active item when possible.

Suggested route active helper:

```ts
function isRouteActive(pathname: string, href: string, exactMatch?: boolean) {
  if (exactMatch) return pathname === href;
  return pathname === href || pathname.startsWith(`${href}/`);
}
```

#### `format-nav-badge.ts`

MUST:

* Hide `0`, `null` and `undefined`.
* Convert values greater than `99` to `99+`.
* Return display-safe badge text.

### State Management

Sidebar state SHOULD include:

```txt
expanded
collapsed
mobileOpen
openGroups
```

Persisted state:

```txt
sidebar collapsed / expanded
manually opened groups
```

Non-persisted state:

```txt
mobile drawer open
hover state
temporary command menu query
```

Suggested localStorage keys:

```txt
hotel-ai.sidebar.state
hotel-ai.sidebar.openGroups
```

### shadcn/ui Usage

Codex MAY use:

* `Button`
* `Sheet`
* `Tooltip`
* `Collapsible`
* `Badge`
* `Separator`
* `ScrollArea`
* `Command`
* `DropdownMenu`

Codex MUST keep shadcn usage simple and consistent.

Codex MUST NOT create a separate design system.

### Tailwind Rules

Codex SHOULD use semantic tokens:

```txt
bg-background
bg-muted
text-foreground
text-muted-foreground
border-border
ring-ring
bg-primary
text-primary-foreground
```

Codex MUST avoid unnecessary hard-coded colors.

Codex SHOULD centralize repeated navigation class logic.

---

## 11. Do Not Implement

Codex MUST NOT implement the following:

* 3rd-level nested sidebar menus
* New backend authorization logic
* New database migration
* New API endpoints
* New dependency
* New route permission model
* New authentication flow
* Placeholder pages for missing routes
* Large dashboard redesign
* Business logic refactor
* Heavy gradients
* Glassmorphism navigation
* Excessive shadows
* Decorative animations
* Hover scale animation
* Random icon selection
* Multi-color icon sets
* Menu items hidden only with CSS
* Low contrast primary menu text
* Multiple CTA buttons inside one menu row
* Technical endpoint names in UI
* Backend model names in UI
* Duplicate links to the same route from multiple menu items
* Settings group placed near the top
* Reports placed above daily operational tasks

---

## 12. Acceptance Criteria

### Navigation Architecture

* [ ] Navigation data is centralized in one config file.
* [ ] Sidebar does not hard-code menu items.
* [ ] Menu groups follow the approved order.
* [ ] Dashboard appears first.
* [ ] Settings appears last.
* [ ] No 3rd-level nested menu exists.
* [ ] Empty groups are not rendered.

### Role-Based Visibility

* [ ] Admin can see all approved groups.
* [ ] Operations user does not see irrelevant sales/admin-only areas.
* [ ] Sales user does not see irrelevant operations/admin-only areas.
* [ ] Support user sees only support-relevant areas.
* [ ] Unauthorized items are filtered before render.
* [ ] CSS-only hiding is not used for permission-based navigation visibility.

### Active State

* [ ] Active item is visually clear.
* [ ] Active item uses `aria-current="page"`.
* [ ] Active item has background, stronger text and left accent indicator.
* [ ] Parent group opens automatically when child route is active.
* [ ] Breadcrumb and page title remain consistent with active navigation.

### Responsive

* [ ] Desktop sidebar supports expanded mode.
* [ ] Desktop sidebar supports collapsed mode.
* [ ] Tablet defaults to collapsed sidebar.
* [ ] Mobile uses drawer / sheet navigation.
* [ ] Mobile drawer closes after item selection.
* [ ] Mobile drawer closes on ESC.
* [ ] Mobile drawer closes on overlay click.
* [ ] Touch targets are at least 44px.

### Interaction

* [ ] Sidebar expanded/collapsed state persists.
* [ ] Manually opened groups persist.
* [ ] Collapsed sidebar shows tooltips.
* [ ] Badge does not render for zero values.
* [ ] Badge values over 99 render as `99+`.
* [ ] NavItem does not fetch badge data directly.

### Accessibility

* [ ] Sidebar uses `<nav aria-label="Main navigation">`.
* [ ] Collapsible triggers use `aria-expanded`.
* [ ] Keyboard navigation works.
* [ ] Focus state is visible.
* [ ] Disabled items use semantic disabled state.
* [ ] Primary menu labels meet contrast requirements.

### Code Quality

* [ ] Role filtering is handled outside UI components.
* [ ] Active route logic is handled by helper function.
* [ ] Badge formatting is handled by helper function.
* [ ] No new dependency is added.
* [ ] Backend logic is not changed.
* [ ] Existing route permission system is preserved.

---

## 13. Needs Human Decision

Codex MUST pause and ask for human decision if any of the following situations occur:

* Existing project route names do not match the proposed route names.
* Required menu item does not have an existing page or route.
* Current role names are different from `admin`, `operations`, `sales`, `support`.
* Existing authorization system conflicts with proposed role visibility.
* Existing design tokens do not include required semantic colors.
* Badge data source is not available.
* There is no reliable way to determine current user role.
* There is no existing layout structure compatible with sidebar changes.
* A requested menu item requires backend changes.
* A requested change requires database migration.
* A requested change requires adding a new dependency.
* A proposed route would create a broken link.
* Existing product terminology conflicts with the proposed Turkish labels.

Codex MUST NOT guess in these situations.

---

## 14. Codex Instructions

Codex, implement this feature as a navigation and menu redesign only.

You MUST:

1. Read the existing layout and navigation structure before editing.
2. Identify current sidebar, topbar, breadcrumb and navigation config files.
3. Create or update a centralized `navigation.ts` config.
4. Move hard-coded navigation items into the centralized config where possible.
5. Implement role-based navigation filtering before render.
6. Preserve existing backend authorization behavior.
7. Preserve existing routes unless a route mapping is clearly available.
8. Implement active route detection with a helper function.
9. Implement expanded and collapsed desktop sidebar states.
10. Persist desktop sidebar collapsed/expanded state in localStorage.
11. Implement mobile navigation using shadcn `Sheet` or existing equivalent.
12. Close mobile navigation after item click.
13. Add accessible labels, focus states and aria attributes.
14. Use semantic Tailwind tokens.
15. Keep UI calm, premium, structured and operational.
16. Avoid decorative visual effects.
17. Avoid new dependencies.
18. Stop when a required decision falls under `Needs Human Decision`.

You SHOULD:

1. Keep components small and responsibility-based.
2. Prefer existing project conventions.
3. Reuse existing shadcn/ui components.
4. Keep menu labels short.
5. Keep spacing consistent.
6. Keep sidebar visually quiet.
7. Use badge only for actionable counts.
8. Keep icons consistent and minimal.
9. Make the active state obvious but not visually heavy.
10. Make the mobile drawer simple and fast to use.

You MUST NOT:

1. Change backend authorization.
2. Change database schema.
3. Add new dependencies.
4. Create placeholder pages.
5. Add 3rd-level nested menus.
6. Hide unauthorized items using only CSS.
7. Use heavy gradients, glassmorphism or decorative animations.
8. Refactor unrelated business logic.
9. Rename routes without a clear mapping.
10. Guess missing product decisions.

Implementation is complete only when all applicable acceptance criteria pass.

```
```
