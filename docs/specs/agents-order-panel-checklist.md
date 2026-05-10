# Agents Checklist: Velox Customer Ordering Panel Redesign

Use this checklist during development and review. Do not mark an item complete unless it has been tested in the running app.

## 1. Scope Control

- [ ] Only `/order` customer-facing ordering experience was redesigned.
- [ ] `/admin#restaurantai` was changed only for logo/restaurant identity requirements.
- [ ] No unrelated admin navigation or business logic was reorganized.
- [ ] No new frontend framework or heavy dependency was added unless already used and allowed by AGENTS.md.
- [ ] Existing QR/table/session behavior was preserved.
- [ ] Backend order submission contract was not broken.

## 2. UI/UX Quality Control

- [ ] The interface feels premium, clean, modern, and customer-friendly.
- [ ] The design clearly reflects the reference style without becoming a poster-like layout.
- [ ] Header, category rail, product cards, cart bar, and checkout/review areas have consistent spacing.
- [ ] Main actions are visually obvious.
- [ ] Decorative details do not reduce readability.
- [ ] Empty, loading, unavailable, error, and success states are polished.
- [ ] Product prices are easy to scan.
- [ ] Add-to-cart interaction is immediate and clear.
- [ ] Quantity editing is understandable.
- [ ] Order confirmation gives the user confidence that the order was received.

## 3. Responsive Design Checks

- [ ] Tested at 360px mobile width.
- [ ] Tested at 390px mobile width.
- [ ] Tested at 430px mobile width.
- [ ] Tested at 768px tablet width.
- [ ] Tested at 1024px desktop width.
- [ ] Tested at 1280px+ desktop width.
- [ ] Sticky category rail does not cover content incorrectly.
- [ ] Sticky cart bar respects mobile safe-area inset.
- [ ] Product cards do not overflow horizontally.
- [ ] Long product names wrap cleanly.
- [ ] Long category names remain usable.
- [ ] Desktop layout does not look like a stretched mobile screen.

## 4. Color and Typography Consistency

- [ ] `#192f9a` is used as a primary color.
- [ ] All order UI colors are centralized as CSS variables/design tokens.
- [ ] Cream, blue, terracotta, olive, and gold accents are used consistently.
- [ ] Low-contrast gold/terracotta is not used for small body text.
- [ ] White-on-blue and blue-on-cream primary text/actions pass contrast expectations.
- [ ] Aviano Sans Black is used only where readable and appropriate.
- [ ] Body, product descriptions, inputs, and buttons use a readable UI font.
- [ ] Font fallbacks are defined.
- [ ] No unlicensed font files were added.

## 5. Logo Upload and Update Behavior

- [ ] Logo appears in the `/order` header.
- [ ] Logo uses `object-fit: contain` and preserves aspect ratio.
- [ ] Missing logo fallback looks professional.
- [ ] Logo has meaningful alt text.
- [ ] `/admin#restaurantai` includes logo upload.
- [ ] Admin can preview current logo.
- [ ] Admin can replace logo.
- [ ] Admin can remove/reset logo.
- [ ] Upload validates file type.
- [ ] Upload validates file size.
- [ ] SVG upload is disabled unless secure sanitization exists.
- [ ] Logo URL is cache-busted after update.
- [ ] Customer page reflects new logo after upload.
- [ ] Upload failure shows a clear admin-facing error.

## 6. Menu Category Structure Alignment

- [ ] UI supports menu groups such as A La Carte, Snack, Drinks, and Wine.
- [ ] UI supports nested categories.
- [ ] UI supports many categories without becoming unusable.
- [ ] Product model supports bilingual names/descriptions.
- [ ] Product model supports prices and price variants.
- [ ] Product model supports unavailable state.
- [ ] Product model supports tags such as vegan, signature, spicy, alcohol.
- [ ] Product model supports future product images.
- [ ] Product model supports modifiers/add-ons.
- [ ] Current menu data remains backward-compatible.

## 7. Ordering Flow Usability

- [ ] User can browse categories without losing context.
- [ ] User can search products.
- [ ] User can add a simple product quickly.
- [ ] Product with variants opens a clear modifier sheet/modal.
- [ ] Required modifiers block add-to-cart until complete.
- [ ] User can edit quantity from product card or cart.
- [ ] User can remove an item from cart.
- [ ] User can add item-level notes if supported.
- [ ] User can add general order note if supported.
- [ ] Cart summary shows item count and total.
- [ ] Submit button prevents double submission.
- [ ] Order success state includes confirmation/order number if available.
- [ ] Order failure state allows retry without losing cart.

## 8. Accessibility Checks

- [ ] Interactive targets are comfortably tappable on mobile.
- [ ] Keyboard focus is visible.
- [ ] Sticky headers/bottom bars do not hide focused elements.
- [ ] Category rail is keyboard accessible.
- [ ] Product buttons have accessible names.
- [ ] Quantity controls have accessible names.
- [ ] Cart updates are announced with `aria-live` where possible.
- [ ] Modal/bottom sheet traps focus.
- [ ] Focus returns to the triggering element after modal close.
- [ ] UI does not rely on color alone.
- [ ] Reduced motion preference is respected.
- [ ] Images have appropriate alt text or empty alt if decorative.

## 9. Performance Checks

- [ ] No large dependency was added unnecessarily.
- [ ] Product images are lazy-loaded where applicable.
- [ ] Logo is optimized.
- [ ] Layout does not shift heavily during loading.
- [ ] Add-to-cart update feels instant.
- [ ] Search input is debounced.
- [ ] Long menus do not cause scroll jank.
- [ ] CSS/JS changes are scoped and not bloated.

## 10. Admin Panel Integration Checks

- [ ] Admin logo upload uses existing auth/session patterns.
- [ ] Admin upload uses existing media storage patterns where possible.
- [ ] Public config endpoint exposes only safe public fields.
- [ ] Backend stores logo metadata.
- [ ] Deleting logo does not delete unrelated assets.
- [ ] Admin preview matches customer header behavior.
- [ ] Errors are logged server-side without leaking sensitive details to the user.

## 11. End-User Experience Testing

- [ ] Test as a first-time customer on mobile.
- [ ] Test a long browsing session with multiple categories.
- [ ] Test adding multiple items from different categories.
- [ ] Test editing cart before submit.
- [ ] Test order submission success.
- [ ] Test network/order submission failure.
- [ ] Test unavailable item display.
- [ ] Test very long product name and description.
- [ ] Test no-logo fallback.
- [ ] Test logo replacement immediately before opening `/order`.

## 12. Stop Conditions

Stop and report before continuing if:

- [ ] The current architecture conflicts with this brief.
- [ ] AGENTS.md forbids a proposed change.
- [ ] Logo upload requires a new storage provider or major media refactor.
- [ ] Current menu schema cannot support categories without migration risk.
- [ ] Order submission depends on hidden pricing/business logic.
- [ ] A change risks breaking admin authentication or order operations.

