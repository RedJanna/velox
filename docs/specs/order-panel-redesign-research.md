# Feature Brief: Velox Customer Ordering Panel Redesign

## 0. Implementation Context

Primary target page: `/order` / `https://velox.nexlumeai.com/order`.

Primary admin dependency: `/admin#restaurantai` for restaurant identity, logo upload, and menu-related settings.

Main priority: customer-facing ordering experience only. Do not reorganize unrelated admin menu structures in this phase unless required to support the order panel logo/menu data.

Design reference: the uploaded Rovena hospitality poster. Translate it into UI, not into a literal poster. Use the poster’s cream surface, deep royal blue, terracotta, olive/green, muted gold, elegant line icons, refined border language, generous spacing, geometric Mediterranean atmosphere, and premium editorial hierarchy.

Important technical guardrail: preserve the project’s existing architecture. If the current app is FastAPI-rendered HTML + CSS + vanilla JS, implement with the current stack. Do not introduce React, Tailwind, shadcn, or a new frontend build system unless the repository already uses them and AGENTS.md allows it.

---

## 1. Objective

Redesign the customer-facing ordering panel so it feels:

- easier to browse on mobile,
- visually more premium and modern,
- clearer for category navigation,
- faster to add/edit items,
- flexible enough for a large restaurant menu,
- consistent with the Mediterranean premium visual language in the reference image,
- maintainable for future PDF/category-based menu organization.

The user should immediately understand where they are, what categories are available, how to add an item, how to review the cart, and how to complete the order.

---

## 2. Source Inputs Used

### Visual Design Reference

The uploaded Rovena poster uses a premium hospitality illustration style: cream background, deep blue typography, terracotta/orange geometry, olive/green accents, muted gold details, line icons, border ornaments, rounded Mediterranean arches, and a calm dining/hospitality atmosphere. This should inform the order panel’s tokens, spacing, icon style, category cards, and CTA language.

### Menu Structure Inputs

The 3 uploaded PDFs indicate that the ordering system must support more than a flat product list:

- A La Carte: starters, hot starters, salads, mains, pastas, kids menu, desserts, signature cocktails, classic cocktails, beer, gin, vodka, whiskey, liqueurs, rakı, soft drinks, hot drinks.
- Snack: light bites & sandwiches, salads, power bowls, shareables, pizzas, burgers & wraps, pastas & pans, hearty plates, kids menu, desserts, cocktails, alcoholic drinks, beers, soft drinks, local & natural drinks, hot drinks.
- Wine: white wines, red wines, rosé wines, champagnes.

Therefore the order panel must support menu groups, nested categories, product metadata, descriptions, prices, variants, item modifiers, availability states, and future visual/media enrichment.

---

## 3. Scope

Codex may change:

- `/order` customer UI templates, CSS, and JavaScript.
- Shared frontend assets only if used by `/order` and not breaking admin pages.
- Backend endpoints/data serialization required for `/order` to load restaurant branding, logo, categories, products, prices, variants, and order submission.
- `/admin#restaurantai` only for logo upload/update/delete/preview and related restaurant identity settings.
- Existing menu/category models only if the migration is backward-compatible and does not delete current menu data.

Codex must not change:

- unrelated admin navigation,
- unrelated WhatsApp/restaurant AI workflows,
- authentication/session logic unless required for secure logo upload,
- QR/table routing behavior unless currently broken,
- payment/accounting logic,
- database schema destructively.

---

## 4. Design Direction

### 4.1 Visual Personality

The interface should feel like “premium Mediterranean hospitality + modern ordering technology.” Avoid a generic SaaS dashboard look. Avoid basic food-delivery styling.

Design cues:

- warm cream background,
- deep royal blue structural elements,
- fine line borders,
- restrained terracotta and olive accents,
- soft card elevation,
- rounded geometry inspired by arches,
- thin icon strokes,
- calm, high-end spacing,
- clear hierarchy and strong mobile usability.

### 4.2 UI Translation of the Reference Poster

Use the poster style this way:

- Blue becomes the primary action/navigation color.
- Cream becomes the page surface.
- Terracotta and gold are accents, not heavy text colors.
- Olive/green supports “natural / premium / food” category accents.
- Decorative line motifs may be used in headers, dividers, or empty states, but never at the cost of readability.
- Border ornaments should become subtle UI borders, dividers, focus rings, and card frames.

Do not create a poster-like interface. The result must remain practical, fast, and accessible.

---

## 5. Recommended Design Tokens

Implement as CSS variables. Keep all colors centralized.

```css
:root {
  --color-primary: #192f9a;
  --color-primary-700: #0f1f70;
  --color-primary-600: #192f9a;
  --color-primary-500: #243fb4;
  --color-primary-50: #edf1ff;

  --color-surface: #f6efe5;
  --color-surface-soft: #fffaf0;
  --color-surface-elevated: #ffffff;
  --color-border: rgba(25, 47, 154, 0.18);

  --color-ink: #111827;
  --color-muted: #6f5e4e;
  --color-muted-2: #8b7a67;

  --color-olive: #193d36;
  --color-olive-soft: #e6eee8;

  --color-terracotta: #c87045;
  --color-terracotta-accessible: #9a4b2e;
  --color-terracotta-soft: #f7dcc8;

  --color-gold: #d7a844;
  --color-gold-accessible: #7a5805;
  --color-gold-soft: #fbefd0;

  --radius-sm: 10px;
  --radius-md: 16px;
  --radius-lg: 22px;
  --radius-xl: 28px;

  --shadow-card: 0 12px 34px rgba(17, 24, 39, 0.08);
  --shadow-floating: 0 18px 45px rgba(17, 24, 39, 0.16);

  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
}
```

### 5.1 Accessibility Notes for Palette

- `#192f9a` on `#f6efe5` is strong enough for normal text and key controls.
- White text on `#192f9a` is strong enough for primary buttons.
- `#c87045` is acceptable mainly as a decorative accent or large bold label; use `#9a4b2e` for normal terracotta text.
- `#d7a844` should not be used as small text on light surfaces; use `#7a5805` for readable gold/brown text.
- Never rely on color alone for selected, unavailable, error, allergy, or order status states.

---

## 6. Typography Recommendation

### 6.1 Aviano Sans Black

Use Aviano Sans Black as a brand/display font, not as the only UI font. It can work well for:

- restaurant name,
- category hero titles,
- selected promotional labels,
- large section headings,
- short uppercase chips.

Do not use Aviano Sans Black for long descriptions, item details, notes, helper text, or dense product lists. Black-weight display fonts reduce readability in small sizes and long passages.

### 6.2 Recommended UI Pairing

Use a highly readable UI font for body and controls:

Preferred stack:

```css
--font-display: "Aviano Sans", "Cinzel", "Trajan Pro", serif;
--font-ui: "Inter", "Manrope", "Aptos", "Segoe UI", system-ui, sans-serif;
```

If Aviano is not licensed/available in the project, do not bundle unlicensed font files. Use the existing licensed font or a safe fallback.

### 6.3 Type Scale

```css
--text-xs: 12px;
--text-sm: 14px;
--text-base: 16px;
--text-md: 18px;
--text-lg: 22px;
--text-xl: 28px;
--text-display: clamp(30px, 7vw, 52px);
```

Rules:

- Product names: 15–17px, 650–750 weight.
- Descriptions: 13–15px, relaxed line-height.
- Prices: 15–17px, strong weight, clear right alignment.
- Primary CTA: 16px+, strong weight.
- Avoid all-caps for long text.

---

## 7. Target Customer Flow

### 7.1 Recommended Flow

1. Customer opens `/order` from QR or direct link.
2. Header shows restaurant logo, restaurant name, optional table/room number, and language toggle.
3. Customer sees search + horizontal category rail.
4. Customer browses categories and product cards.
5. Customer taps product or `+`.
6. If product has variants/modifiers, open bottom sheet/product modal.
7. Customer selects variation, quantity, optional note, and adds to cart.
8. Sticky bottom cart summary appears after first item.
9. Customer reviews cart, edits quantities/notes.
10. Customer confirms order.
11. System shows success state with order number/status.

### 7.2 Flow Principles

- Keep browsing and adding items fast.
- Do not force users into a full product detail page for simple products.
- Use bottom sheets on mobile for variants/notes.
- Keep total visible once cart has items.
- Allow cart editing without losing category position.
- Preserve table/QR context as read-only if available.
- Show clear unavailable states without deleting products.

---

## 8. Page Layout Requirements

### 8.1 Mobile First Layout

Mobile is the main experience.

Structure:

1. `OrderShell`
2. `BrandHeader`
3. `SearchAndQuickFilters`
4. `StickyCategoryRail`
5. `CategorySection`
6. `ProductCard`
7. `StickyCartBar`
8. `CartReviewSheet`
9. `ProductModifierSheet`
10. `OrderSuccessState`

### 8.2 Desktop Layout

Desktop should not simply stretch mobile cards.

Recommended desktop layout:

- Max content width: 1180–1280px.
- Left or top category navigation depending on available code constraints.
- Product grid: 2–3 columns.
- Cart summary as right-side sticky panel if viewport >= 1024px.
- Keep logo/header compact and premium.

### 8.3 Breakpoints

```css
@media (max-width: 480px) { /* compact mobile */ }
@media (min-width: 481px) and (max-width: 767px) { /* large mobile */ }
@media (min-width: 768px) and (max-width: 1023px) { /* tablet */ }
@media (min-width: 1024px) { /* desktop */ }
```

---

## 9. Logo Area Requirements

### 9.1 Customer-Facing Logo Area

The order window must include a professional logo area:

- Position: top header area.
- Mobile size: 56–72px visual height depending on logo ratio.
- Desktop size: 72–96px max visual height.
- Use `object-fit: contain`.
- Preserve aspect ratio.
- Provide safe fallback if logo missing.
- Add alt text: restaurant name + “logo”.
- Avoid cropping unless admin explicitly crops.
- Background should be calm: cream/white glass card with blue border.

Recommended structure:

```html
<header class="order-brand-header">
  <div class="restaurant-logo-frame">
    <img src="..." alt="Kassandra Restaurant logo" loading="eager" />
  </div>
  <div class="restaurant-meta">
    <p class="eyebrow">Order Experience</p>
    <h1>Restaurant Name</h1>
    <p class="table-context">Masa 12</p>
  </div>
</header>
```

### 9.2 Admin Upload Requirements

Add/update in `/admin#restaurantai`:

- Upload logo file.
- Preview current logo.
- Replace logo.
- Remove logo / reset fallback.
- Show recommended dimensions and file constraints.
- Store alt text or derive from restaurant name.
- Show how the logo will look on mobile order header.

Accepted formats:

- PNG, JPG/JPEG, WebP.
- SVG only if the app already sanitizes SVG securely; otherwise disable SVG upload.

Recommended validation:

- Max file size: 2 MB.
- Convert raster uploads to optimized WebP if backend has an existing image-processing path.
- Reject executable or mismatched MIME files.
- Store original only if current media policy allows it.
- Generate hashed filename for cache busting.

Suggested DB fields:

```text
restaurant_logo_url
restaurant_logo_alt
restaurant_logo_updated_at
restaurant_logo_width
restaurant_logo_height
restaurant_logo_fit_mode   // contain | cover, default contain
```

Suggested API behavior:

- `GET /api/restaurant/public-config` returns logo URL, restaurant name, color theme, table context if applicable.
- `POST /api/admin/restaurant/logo` uploads/replaces logo.
- `DELETE /api/admin/restaurant/logo` removes logo and resets fallback.
- Frontend must use cache-busted logo URL or version query based on `restaurant_logo_updated_at`.

---

## 10. Flexible Menu Architecture

Do not hard-code only the current PDF categories. Build a structure that can support future divisions.

### 10.1 Data Model Recommendation

```json
{
  "menuGroups": [
    {
      "id": "a-la-carte",
      "title_tr": "A La Carte",
      "title_en": "A La Carte",
      "displayOrder": 10,
      "isActive": true,
      "categories": [
        {
          "id": "starters",
          "title_tr": "Başlangıçlar",
          "title_en": "Starters",
          "icon": "leaf",
          "displayOrder": 10,
          "isActive": true,
          "products": []
        }
      ]
    }
  ]
}
```

### 10.2 Product Model Recommendation

```json
{
  "id": "product-id",
  "categoryId": "starters",
  "name_tr": "Avokado Humus",
  "name_en": "Avocado Hummus",
  "description_tr": "...",
  "description_en": "...",
  "price": 440,
  "currency": "TRY",
  "imageUrl": null,
  "isAvailable": true,
  "isFeatured": false,
  "tags": ["vegan", "signature"],
  "allergens": ["sesame"],
  "variantGroups": [
    {
      "id": "size",
      "title_tr": "Porsiyon",
      "title_en": "Size",
      "required": true,
      "minSelect": 1,
      "maxSelect": 1,
      "options": [
        { "id": "small", "title_tr": "Küçük", "priceDelta": 0 },
        { "id": "large", "title_tr": "Büyük", "priceDelta": 120 }
      ]
    }
  ],
  "modifierGroups": [
    {
      "id": "sauce",
      "title_tr": "Sos Seçimi",
      "required": false,
      "minSelect": 0,
      "maxSelect": 2,
      "options": []
    }
  ],
  "displayOrder": 10
}
```

### 10.3 Category Mapping from PDFs

Recommended top-level groups:

1. A La Carte
2. Snack Menu
3. Drinks
4. Wine List
5. Kids
6. Desserts

Recommended nested categories:

- Starters / Başlangıçlar
- Hot Starters / Ara Sıcaklar
- Salads / Salatalar
- Main Courses / Ana Yemekler
- Pastas / Makarnalar
- Light Bites & Sandwiches
- Power Bowls
- Shareables
- Pizzas
- Burgers & Wraps
- Hearty Plates
- Kids Menu
- Desserts
- Signature Cocktails
- Classic Cocktails
- Non-Alcoholic Cocktails
- Soft Drinks
- Local & Natural
- Hot Drinks
- Beers
- Spirits
- White Wines
- Red Wines
- Rosé Wines
- Champagnes

The UI must allow either one flat category rail or a two-level menu-group/category navigation.

---

## 11. Component Requirements

### 11.1 Brand Header

Must include:

- logo,
- restaurant name,
- table/room context if available,
- optional “Order Experience” label,
- language switch if app supports multilingual content.

Visual style:

- elevated cream/white card,
- thin blue border,
- subtle ornamental divider,
- no clutter.

### 11.2 Category Rail

Mobile:

- sticky under header/search,
- horizontal scroll chips,
- active category clearly indicated,
- no tiny tap targets,
- include “All” and major groups if needed.

Desktop:

- visible navigation, not hidden behind hamburger if space allows.
- can be left rail or top rail.

### 11.3 Product Card

Each card must show:

- product name,
- short description if available,
- price,
- tags such as Vegan / Signature / Spicy / Alcohol,
- availability state,
- image if available,
- clear add button,
- quantity stepper after item is added.

Card style:

- cream/white elevated card,
- 16–22px radius,
- 1px blue-tinted border,
- strong spacing,
- price and CTA easy to scan.

### 11.4 Product Modifier Sheet

Open only when needed:

- variants,
- add-ons,
- sauce selection,
- cooking preference,
- item note.

Rules:

- Required choices must be clearly marked.
- Disable add-to-cart until required selections are valid.
- Price updates live.
- Sheet must be dismissible but not accidentally destructive.

### 11.5 Sticky Cart Bar

Mobile:

- appears after first item,
- fixed bottom,
- shows item count + total + primary CTA,
- respects safe-area inset.

Desktop:

- right sticky cart panel if enough space.

### 11.6 Cart Review

Must support:

- edit quantities,
- remove item,
- edit item modifiers/notes,
- general order note,
- table/room context review,
- clear submit button,
- loading and success state.

### 11.7 Empty, Loading, Error States

Implement polished states:

- loading skeletons, not layout jumps,
- empty category message,
- network error with retry,
- order submission error with non-technical explanation,
- unavailable product state.

---

## 12. UI/UX Improvement Recommendations

1. Add search at top for large menus.
2. Use sticky category navigation to reduce scrolling friction.
3. Keep product cards compact but premium.
4. Make `+` / quantity stepper obvious and thumb-friendly.
5. Use a bottom cart bar so users never lose the path to checkout.
6. Use bottom sheets for product customization on mobile.
7. Keep the order flow linear: browse → add → review → confirm → success.
8. Avoid hiding categories behind a hamburger on desktop.
9. Keep menu data bilingual-ready.
10. Use availability states instead of deleting items from the menu.
11. Keep animations short and subtle.
12. Do not overuse decorative motifs in dense product areas.

---

## 13. Accessibility Requirements

Target WCAG 2.2 AA where practical.

Required:

- All interactive controls must have accessible labels.
- Focus styles must be visible and not hidden by sticky headers or bottom bars.
- Touch targets should be at least 44px high for comfort; do not go below WCAG target-size expectations.
- Text contrast must pass normal text contrast requirements.
- Cart quantity updates should be announced with `aria-live="polite"` where possible.
- Buttons must not depend on color alone.
- Category rail must be keyboard navigable.
- Modals/bottom sheets must trap focus and restore focus on close.
- Product images need useful alt text or empty alt when decorative.
- Respect `prefers-reduced-motion`.
- Do not use drag-only interactions.

---

## 14. Animation Requirements

Motion should feel premium, not flashy.

Recommended:

- 150–220ms transitions,
- ease-out for entry,
- subtle card hover/lift on desktop,
- bottom sheet slide-up with opacity,
- category active indicator transition,
- cart bar slide/fade.

Avoid:

- long intro animations,
- parallax in the ordering flow,
- animation that delays add-to-cart,
- infinite decorative motion.

Implement reduced motion:

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

---

## 15. Technical Implementation Notes

### 15.1 Recommended File Strategy

Codex should first inspect the repository and identify the existing `/order` implementation.

Likely implementation zones:

- order template / route handler,
- customer order CSS asset,
- customer order JS asset,
- public restaurant config API,
- order submission API,
- admin restaurant settings/logo upload code.

Do not create duplicate route systems. Refactor existing files where possible.

### 15.2 CSS Strategy

- Introduce `order-design-tokens.css` or equivalent block in existing CSS.
- Use BEM-like or prefixed classes: `.order-*` to avoid leaking styles to admin.
- Do not globally change `button`, `input`, `body` styles in a way that affects admin unexpectedly.
- Keep responsive rules near order-specific components.

### 15.3 JavaScript Strategy

- Keep state minimal and predictable.
- Centralize cart state in one object/store.
- Use event delegation for product cards if rendering server-side HTML.
- Debounce search input.
- Persist cart to session/local storage only if this is already expected and safe.
- Clear cart after successful order submission.
- Prevent double-submit.

Suggested client state shape:

```js
const orderState = {
  restaurant: {},
  menuGroups: [],
  activeCategoryId: null,
  searchQuery: "",
  filters: [],
  cart: [],
  isSubmitting: false,
  error: null
};
```

### 15.4 Order Submission

Order payload should include:

```json
{
  "restaurantId": "...",
  "tableId": "...",
  "items": [
    {
      "productId": "...",
      "quantity": 2,
      "unitPrice": 440,
      "selectedVariants": [],
      "selectedModifiers": [],
      "note": "..."
    }
  ],
  "orderNote": "...",
  "clientTimestamp": "..."
}
```

Backend must calculate final trusted prices. Frontend totals are for display only.

### 15.5 Security

- Sanitize and validate upload MIME types.
- Do not allow SVG unless sanitized.
- Do not trust client prices.
- Rate-limit order submissions if existing infrastructure supports it.
- Prevent double-order by disabling submit and/or using idempotency key.
- Keep public config endpoint limited to safe public fields.

---

## 16. Performance Requirements

- First content should render quickly on mobile.
- Avoid huge full-menu images as primary content.
- Lazy-load product images below first viewport.
- Use skeleton loading for menu data.
- Use compressed WebP/AVIF where existing pipeline supports it.
- Keep CSS/JS bundle small.
- Avoid adding large icon libraries if current stack does not use them.
- Use CSS icons or inline SVG sprites for a small curated icon set.

Targets:

- Product list interaction should feel immediate.
- Add-to-cart should update UI within 100ms after user tap.
- Category navigation should not jank on long menus.

---

## 17. Prioritized Development Plan

### Phase 0 — Repository Audit

- Find current `/order` route/template/assets.
- Find existing restaurant/admin settings model.
- Find existing upload/media storage patterns.
- Identify how menu items are currently loaded.
- Identify current order submission contract.
- Stop if assumptions conflict with AGENTS.md.

### Phase 1 — Design Tokens and Visual Shell

- Add order-specific tokens.
- Create premium page background.
- Build refined brand header.
- Add logo rendering fallback.
- Add base responsive layout.

### Phase 2 — Menu Browsing UX

- Add sticky category rail.
- Add search/filter UI.
- Redesign product cards.
- Add availability and tag states.
- Add empty/loading/error states.

### Phase 3 — Cart and Order Flow

- Add bottom cart bar.
- Add cart review sheet/panel.
- Add quantity editing and item notes.
- Add product modifier sheet if item has variants.
- Add success and failure states.

### Phase 4 — Admin Logo Integration

- Add logo upload/replace/delete in `/admin#restaurantai`.
- Add preview and validation.
- Add public config output.
- Add cache busting.
- Confirm customer page updates logo after upload.

### Phase 5 — Menu Architecture Readiness

- Prepare support for menu groups and nested categories.
- Preserve current data compatibility.
- Do not complete full PDF import unless explicitly asked.
- Ensure UI can display A La Carte, Snack, Drinks, and Wine structures later.

### Phase 6 — QA and Polish

- Mobile testing at 360px, 390px, 430px.
- Tablet and desktop testing.
- Keyboard navigation.
- Screen reader basics.
- Contrast checks.
- Slow network checks.
- Admin upload checks.

---

## 18. Risks and Gaps

1. Current live order page could not be fully visually audited from this brief alone. Codex must inspect the repository implementation and run the page locally.
2. Aviano Sans Black may not be licensed for web embedding. Use only if already licensed/available.
3. Uploaded PDFs include duplicate/overlapping categories and inconsistent product naming/price formats. Do not build a one-off parser without a normalization plan.
4. Alcohol categories may require local legal/operational handling. Do not add age verification unless requested, but keep alcohol tagging supported.
5. Logo upload security is a risk if SVG or unsanitized files are allowed.
6. New design tokens must be scoped to `/order` to avoid breaking admin UI.
7. Backend must calculate trusted order totals; frontend totals are not authoritative.
8. If product images are introduced later, image performance and aspect-ratio handling must be planned.

---

## 19. Acceptance Criteria

The task is complete when:

- `/order` has a premium, clean, modern customer-facing UI based on the reference visual language.
- The page works well on mobile first.
- Logo appears in a professional header area.
- Logo can be updated through `/admin#restaurantai` and reflected on `/order`.
- Categories and product cards are easier to browse.
- Cart/add/review/submit flow is clear and linear.
- UI supports future nested menu categories.
- Colors and typography are centralized in tokens.
- Accessibility basics are addressed.
- No unrelated admin/menu sections are broken.
- Code follows AGENTS.md and existing project architecture.

