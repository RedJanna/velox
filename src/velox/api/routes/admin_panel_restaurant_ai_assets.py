"""Static assets for the Restaurant AI admin panel module."""

# ruff: noqa: E501

ADMIN_RESTAURANT_AI_STYLE = """\
.restaurant-ai-panel .module-card textarea{min-height:112px}
.restaurant-ai-hero{border-color:rgba(15,118,110,.24);background:linear-gradient(180deg,#fffdf8 0%,#f4fbf9 100%)}
.restaurant-ai-summary{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-top:16px}
.restaurant-ai-stat{border:1px solid var(--line);border-radius:16px;background:rgba(255,255,255,.78);padding:14px}
.restaurant-ai-stat strong{display:block;font-size:22px;line-height:1;color:var(--ink)}
.restaurant-ai-stat span{display:block;margin-top:6px;color:var(--muted);font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.05em}
.restaurant-ai-toolbar{grid-template-columns:1.3fr repeat(4,minmax(120px,.75fr)) auto}
.restaurant-ai-table table{min-width:1080px}
.restaurant-ai-tags{display:flex;flex-wrap:wrap;gap:5px;max-width:220px}
.restaurant-ai-tag{display:inline-flex;align-items:center;min-height:22px;border-radius:999px;background:#e8f3f1;color:#115e59;padding:3px 8px;font-size:11px;font-weight:800}
.restaurant-ai-state{display:inline-flex;align-items:center;min-height:24px;border-radius:999px;padding:3px 9px;font-size:11px;font-weight:900}
.restaurant-ai-state.active,.restaurant-ai-state.sent,.restaurant-ai-state.confirmed,.restaurant-ai-state.sent_to_waiter,.restaurant-ai-state.passed,.restaurant-ai-state.accepted_by_staff,.restaurant-ai-state.completed{background:#e7f7ed;color:#166534}
.restaurant-ai-state.passive,.restaurant-ai-state.cancelled,.restaurant-ai-state.not_sent{background:#eef2f7;color:#475569}
.restaurant-ai-state.pending_approval,.restaurant-ai-state.pending_confirmation,.restaurant-ai-state.partial,.restaurant-ai-state.pending_staff_approval,.restaurant-ai-state.preparing,.restaurant-ai-state.customer_confirmed_twice,.restaurant-ai-state.sent_to_staff{background:#fff2dd;color:#92400e}
.restaurant-ai-state.failed,.restaurant-ai-state.approval_required,.restaurant-ai-state.rejected_by_staff{background:#fde7e5;color:#991b1b}
.restaurant-ai-conflict{border:1px solid var(--line);border-radius:16px;padding:14px;background:var(--surface-2)}
.restaurant-ai-conflict strong{display:block;margin-bottom:6px}
.restaurant-ai-conflict ul{margin:8px 0 0;padding-left:18px;color:var(--muted)}
.restaurant-ai-test-result{margin-top:16px;display:grid;gap:12px}
.restaurant-ai-result-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.restaurant-ai-result-box{border:1px solid var(--line);border-radius:16px;background:var(--surface-2);padding:14px;min-width:0}
.restaurant-ai-result-box h4{margin:0 0 8px;font-size:13px;text-transform:uppercase;letter-spacing:.05em;color:#364152}
.restaurant-ai-result-box pre{margin:0;white-space:pre-wrap;font-family:var(--mono);font-size:12px;line-height:1.5;color:var(--ink)}
.restaurant-ai-mini-actions{display:flex;gap:6px;flex-wrap:wrap}
.restaurant-ai-mini-actions button{min-height:30px;border:1px solid var(--line);border-radius:10px;background:#fff;color:var(--ink);font-size:12px;font-weight:800;padding:5px 8px;cursor:pointer}
.restaurant-ai-panel .action-button.secondary[aria-expanded="true"]{background:linear-gradient(135deg,#102033,#1f3554);color:#fff;border-color:#102033}
@media (max-width:1100px){.restaurant-ai-summary,.restaurant-ai-result-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.restaurant-ai-toolbar{grid-template-columns:1fr 1fr}}
@media (max-width:720px){.restaurant-ai-summary,.restaurant-ai-result-grid,.restaurant-ai-toolbar{grid-template-columns:1fr}}
"""


ADMIN_RESTAURANT_AI_SCRIPT = """\
const restaurantAiState = {
  catalog: [],
  categories: [],
  venues: [],
  menuTypes: [],
  conflicts: [],
  waiters: [],
  orders: [],
  offMenu: [],
  settings: null,
  source: 'missing',
  loaded: false,
};

function restaurantAiEl(id) {
  return document.getElementById(id);
}

function restaurantAiHotelId() {
  return Number(state.selectedHotelId || state.me?.hotel_id || 0);
}

function restaurantAiText(value, fallback = '-') {
  const text = value === null || value === undefined ? '' : String(value);
  return text.trim() || fallback;
}

function restaurantAiMoney(value) {
  if (value === null || value === undefined || value === '') return '-';
  const numberValue = Number(value);
  if (!Number.isFinite(numberValue)) return escapeHtml(String(value));
  return `${new Intl.NumberFormat('tr-TR', {maximumFractionDigits: 2}).format(numberValue)} TL`;
}

function restaurantAiDate(value) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return escapeHtml(String(value));
  return new Intl.DateTimeFormat('tr-TR', {dateStyle: 'short', timeStyle: 'short'}).format(date);
}

function restaurantAiStatePill(value) {
  const safe = restaurantAiText(value, '-');
  return `<span class="restaurant-ai-state ${escapeHtml(safe)}">${escapeHtml(safe)}</span>`;
}

function restaurantAiTags(tags) {
  const list = Array.isArray(tags) ? tags.filter(Boolean).slice(0, 5) : [];
  if (!list.length) return '<span class="muted">-</span>';
  return `<div class="restaurant-ai-tags">${list.map(tag => `<span class="restaurant-ai-tag">${escapeHtml(tag)}</span>`).join('')}</div>`;
}

function restaurantAiIngredients(ingredients) {
  const list = Array.isArray(ingredients) ? ingredients.filter(Boolean).slice(0, 8) : [];
  if (!list.length) return '<span class="muted">İçerik eksik</span>';
  return `<div class="restaurant-ai-tags">${list.map(item => `<span class="restaurant-ai-tag">${escapeHtml(item)}</span>`).join('')}</div>`;
}

function restaurantAiQueryFromForm(form) {
  const params = new URLSearchParams();
  const hotelId = restaurantAiHotelId();
  if (hotelId) params.set('hotel_id', String(hotelId));
  if (!form) return params;
  const data = new FormData(form);
  for (const [key, value] of data.entries()) {
    const text = String(value || '').trim();
    if (text) params.set(key, text);
  }
  return params;
}

async function loadRestaurantAiPanel() {
  const hotelId = restaurantAiHotelId();
  if (!hotelId) {
    notify('Lütfen bir otel seçin.', 'warn');
    return;
  }
  try {
    await Promise.all([
      loadRestaurantAiCatalog(),
      loadRestaurantAiConflicts(),
      loadRestaurantAiWaiters(),
      loadRestaurantAiOrders(),
      loadRestaurantAiOffMenu(),
      loadRestaurantAiSettings(),
    ]);
    restaurantAiState.loaded = true;
    renderRestaurantAiSummary();
  } catch (error) {
    notify(error.message || 'Restaurant AI paneli yüklenemedi.', 'error');
  }
}

async function loadRestaurantAiCatalog() {
  const params = restaurantAiQueryFromForm(restaurantAiEl('restaurantAiCatalogFilters'));
  const payload = await apiFetch(`/restaurant-ai/catalog?${params.toString()}`);
  restaurantAiState.catalog = Array.isArray(payload.items) ? payload.items : [];
  restaurantAiState.categories = Array.isArray(payload.categories) ? payload.categories : [];
  restaurantAiState.venues = Array.isArray(payload.venues) ? payload.venues : [];
  restaurantAiState.menuTypes = Array.isArray(payload.menu_types) ? payload.menu_types : [];
  restaurantAiState.source = payload.source || 'missing';
  restaurantAiState.latestVersion = payload.latest_version || null;
  restaurantAiState.safeSaveMode = payload.safe_save_mode || '';
  renderRestaurantAiCatalogFilters();
  renderRestaurantAiCatalog();
}

async function loadRestaurantAiConflicts() {
  const hotelId = restaurantAiHotelId();
  const payload = await apiFetch(`/restaurant-ai/catalog/conflicts?hotel_id=${encodeURIComponent(hotelId)}`);
  restaurantAiState.conflicts = Array.isArray(payload.items) ? payload.items : [];
  renderRestaurantAiConflicts();
}

async function loadRestaurantAiWaiters() {
  const hotelId = restaurantAiHotelId();
  const payload = await apiFetch(`/restaurant-ai/waiters?hotel_id=${encodeURIComponent(hotelId)}`);
  restaurantAiState.waiters = Array.isArray(payload.items) ? payload.items : [];
  renderRestaurantAiWaiters();
}

async function loadRestaurantAiOrders() {
  const params = new URLSearchParams();
  const hotelId = restaurantAiHotelId();
  if (hotelId) params.set('hotel_id', String(hotelId));
  const status = restaurantAiEl('restaurantAiOrderStatusFilter')?.value || '';
  if (status) params.set('status', status);
  const payload = await apiFetch(`/restaurant-ai/orders?${params.toString()}`);
  restaurantAiState.orders = Array.isArray(payload.items) ? payload.items : [];
  renderRestaurantAiOrders();
}

async function loadRestaurantAiOffMenu() {
  const hotelId = restaurantAiHotelId();
  const payload = await apiFetch(`/restaurant-ai/off-menu-requests?hotel_id=${encodeURIComponent(hotelId)}`);
  restaurantAiState.offMenu = Array.isArray(payload.items) ? payload.items : [];
  renderRestaurantAiOffMenu();
}

async function loadRestaurantAiSettings() {
  const hotelId = restaurantAiHotelId();
  const payload = await apiFetch(`/restaurant-ai/settings?hotel_id=${encodeURIComponent(hotelId)}`);
  restaurantAiState.settings = payload.settings || null;
  renderRestaurantAiSettings();
}

function renderRestaurantAiSummary() {
  const target = restaurantAiEl('restaurantAiSummary');
  if (!target) return;
  const activeCount = restaurantAiState.catalog.filter(item => item.status === 'active').length;
  const manualCount = restaurantAiState.catalog.filter(item => item.manual_status === 'approval_required').length;
  const version = restaurantAiState.latestVersion?.version ? `v${restaurantAiState.latestVersion.version}` : restaurantAiState.source;
  target.innerHTML = [
    ['Katalog', restaurantAiState.catalog.length, version],
    ['Aktif Ürün', activeCount, 'asistanın kullanabileceği kayıt'],
    ['Fiyat Çakışması', restaurantAiState.conflicts.length, 'venue + menü tipi bazında'],
    ['Onay Gerekli', manualCount, 'manuel ürün talepleri'],
  ].map(([label, value, hint]) => `<div class="restaurant-ai-stat"><strong>${escapeHtml(value)}</strong><span>${escapeHtml(label)}</span><small class="muted">${escapeHtml(hint)}</small></div>`).join('');
}

function renderRestaurantAiCatalogFilters() {
  renderRestaurantAiSelect('restaurantAiCategoryFilter', restaurantAiState.categories, 'Tüm kategoriler');
  renderRestaurantAiSelect('restaurantAiVenueFilter', restaurantAiState.venues, 'Tüm venue');
  renderRestaurantAiSelect('restaurantAiMenuTypeFilter', restaurantAiState.menuTypes, 'Tüm menü tipleri');
}

function renderRestaurantAiSelect(id, options, placeholder) {
  const select = restaurantAiEl(id);
  if (!select) return;
  const current = select.value;
  select.innerHTML = `<option value="">${escapeHtml(placeholder)}</option>` + options.map(item => `<option value="${escapeHtml(item)}">${escapeHtml(item)}</option>`).join('');
  select.value = options.includes(current) ? current : '';
}

function renderRestaurantAiCatalog() {
  const target = restaurantAiEl('restaurantAiCatalogTableBody');
  if (!target) return;
  if (!restaurantAiState.catalog.length) {
    target.innerHTML = '<tr><td colspan="10" class="empty-state">Katalog kaydı bulunamadı.</td></tr>';
    renderRestaurantAiSummary();
    return;
  }
  target.innerHTML = restaurantAiState.catalog.map(item => {
    const primaryName = item.name_tr || item.name_en || '-';
    const secondaryName = item.name_tr && item.name_en ? `<br><small>${escapeHtml(item.name_en)}</small>` : '';
    const description = item.description_tr || item.description_en || item.notes || '-';
    return `<tr>
      <td><strong>${escapeHtml(primaryName)}</strong>${secondaryName}<br><small class="mono">${escapeHtml(item.menu_item_id || '')}</small></td>
      <td>${escapeHtml(item.category || '-')}</td>
      <td>${escapeHtml(item.menu_type || '-')}</td>
      <td>${escapeHtml(item.venue || '-')}</td>
      <td>${restaurantAiMoney(item.price_try)}</td>
      <td>${escapeHtml(description)}</td>
      <td>${restaurantAiIngredients(item.ingredients)}</td>
      <td>${restaurantAiTags(item.tags)}</td>
      <td>${restaurantAiStatePill(item.manual_status === 'approval_required' ? 'approval_required' : item.status)}</td>
      <td><div class="restaurant-ai-mini-actions">
        <button type="button" data-restaurant-ai-item-content="${escapeHtml(item.menu_item_id || '')}" data-ingredients="${escapeHtml((item.ingredients || []).join(', '))}">İçerik</button>
        <button type="button" data-restaurant-ai-item-status="${escapeHtml(item.menu_item_id || '')}" data-status="${item.status === 'active' ? 'passive' : 'active'}">${item.status === 'active' ? 'Pasifleştir' : 'Aktifleştir'}</button>
      </div></td>
    </tr>`;
  }).join('');
  renderRestaurantAiSummary();
}

function renderRestaurantAiConflicts() {
  const target = restaurantAiEl('restaurantAiConflictList');
  if (!target) return;
  if (!restaurantAiState.conflicts.length) {
    target.innerHTML = '<div class="empty-state"><p>Fiyat çakışması görünmüyor.</p></div>';
    renderRestaurantAiSummary();
    return;
  }
  target.innerHTML = restaurantAiState.conflicts.map(conflict => `
    <div class="restaurant-ai-conflict">
      <strong>${escapeHtml(conflict.name || '-')}</strong>
      <span class="muted">${escapeHtml(conflict.venue || '-')} / ${escapeHtml(conflict.menu_type || '-')}</span>
      <ul>${(conflict.items || []).map(item => `<li>${escapeHtml(item.category || '-')} - ${restaurantAiMoney(item.price_try)} <span class="mono">${escapeHtml(item.menu_item_id || '')}</span></li>`).join('')}</ul>
    </div>
  `).join('');
  renderRestaurantAiSummary();
}

function renderRestaurantAiWaiters() {
  const target = restaurantAiEl('restaurantAiWaiterTableBody');
  if (!target) return;
  if (!restaurantAiState.waiters.length) {
    target.innerHTML = '<tr><td colspan="7" class="empty-state">Garson numarası yok.</td></tr>';
    return;
  }
  target.innerHTML = restaurantAiState.waiters.map(item => `
    <tr>
      <td><strong>${escapeHtml(item.waiter_name || '-')}</strong></td>
      <td>${escapeHtml(item.whatsapp_display || '-')}</td>
      <td>${escapeHtml(item.role || '-')}</td>
      <td>${escapeHtml(item.venue || '-')}</td>
      <td>${restaurantAiStatePill(item.active ? 'active' : 'passive')}</td>
      <td>${restaurantAiStatePill(item.receives_order_notifications ? 'active' : 'passive')}</td>
      <td><div class="restaurant-ai-mini-actions">
        <button type="button" data-restaurant-ai-waiter-toggle="${escapeHtml(item.id)}" data-field="active" data-value="${item.active ? 'false' : 'true'}">${item.active ? 'Pasifleştir' : 'Aktifleştir'}</button>
        <button type="button" data-restaurant-ai-waiter-toggle="${escapeHtml(item.id)}" data-field="receives_order_notifications" data-value="${item.receives_order_notifications ? 'false' : 'true'}">${item.receives_order_notifications ? 'Bildirim kapat' : 'Bildirim aç'}</button>
      </div></td>
    </tr>
  `).join('');
}

function renderRestaurantAiOrders() {
  const target = restaurantAiEl('restaurantAiOrderTableBody');
  if (!target) return;
  if (!restaurantAiState.orders.length) {
    target.innerHTML = '<tr><td colspan="9" class="empty-state">Sipariş logu bulunamadı.</td></tr>';
    return;
  }
  target.innerHTML = restaurantAiState.orders.map(item => {
    const details = (item.items || []).map(orderItem => {
      const name = orderItem.name_tr || orderItem.name_en || orderItem.name || orderItem.menu_item_id || '-';
      const quantity = orderItem.quantity || 1;
      return `${quantity}x ${name}`;
    }).join(', ') || '-';
    return `<tr>
      <td><strong>${escapeHtml(item.order_id || '-')}</strong><br><small>${restaurantAiDate(item.created_at)}</small></td>
      <td>${escapeHtml(item.table_or_room || '-')}</td>
      <td>${escapeHtml(item.guest_name || '-')}</td>
      <td>${escapeHtml(details)}</td>
      <td>${restaurantAiMoney(item.total_try)}</td>
      <td>${escapeHtml(item.customer_note || '-')}</td>
      <td>${escapeHtml(item.allergy_note || '-')}</td>
      <td>${restaurantAiStatePill(item.confirmation_status)}${renderRestaurantAiOrderActions(item)}</td>
      <td>${restaurantAiStatePill(item.whatsapp_send_status)}</td>
    </tr>`;
  }).join('');
}

function renderRestaurantAiOrderActions(item) {
  const status = item.confirmation_status || '';
  if (status === 'pending_staff_approval') {
    return `<div class="restaurant-ai-mini-actions mt-sm">
      <button type="button" data-restaurant-ai-order-status="${escapeHtml(item.order_id || '')}" data-status="accepted_by_staff">Kabul Et</button>
      <button type="button" data-restaurant-ai-order-status="${escapeHtml(item.order_id || '')}" data-status="rejected_by_staff">Reddet</button>
    </div>`;
  }
  if (status === 'accepted_by_staff') {
    return `<div class="restaurant-ai-mini-actions mt-sm">
      <button type="button" data-restaurant-ai-order-status="${escapeHtml(item.order_id || '')}" data-status="preparing">Hazırlanıyor</button>
      <button type="button" data-restaurant-ai-order-status="${escapeHtml(item.order_id || '')}" data-status="completed">Tamamlandı</button>
    </div>`;
  }
  if (status === 'preparing') {
    return `<div class="restaurant-ai-mini-actions mt-sm">
      <button type="button" data-restaurant-ai-order-status="${escapeHtml(item.order_id || '')}" data-status="completed">Tamamlandı</button>
    </div>`;
  }
  return '';
}

function renderRestaurantAiOffMenu() {
  const target = restaurantAiEl('restaurantAiOffMenuTableBody');
  if (!target) return;
  if (!restaurantAiState.offMenu.length) {
    target.innerHTML = '<tr><td colspan="5" class="empty-state">Menü dışı talep logu yok.</td></tr>';
    return;
  }
  target.innerHTML = restaurantAiState.offMenu.map(item => `
    <tr>
      <td><strong>${escapeHtml(item.requested_text || '-')}</strong><br><small class="mono">${escapeHtml(item.normalized_request || '')}</small></td>
      <td>${escapeHtml(item.detected_intent || '-')}</td>
      <td>${escapeHtml(item.venue || '-')}</td>
      <td>${item.added_to_catalog ? restaurantAiStatePill('failed') : restaurantAiStatePill('passive')}</td>
      <td>${restaurantAiDate(item.created_at)}</td>
    </tr>
  `).join('');
}

function renderRestaurantAiSettings() {
  const form = restaurantAiEl('restaurantAiSettingsForm');
  const settings = restaurantAiState.settings;
  if (!form || !settings) return;
  form.off_menu_response.value = settings.off_menu_response || '';
  form.order_confirmation_message.value = settings.order_confirmation_message || '';
  form.whatsapp_notification_template.value = settings.whatsapp_notification_template || '';
  form.allergy_warning_text.value = settings.allergy_warning_text || '';
}

function setRestaurantAiCatalogExpanded(expanded) {
  const content = restaurantAiEl('restaurantAiCatalogContent');
  const button = restaurantAiEl('restaurantAiCatalogToggle');
  if (!content || !button) return;
  content.hidden = !expanded;
  button.setAttribute('aria-expanded', expanded ? 'true' : 'false');
  button.textContent = expanded ? 'Kataloğu Kapat' : 'Kataloğu Aç';
}

function renderRestaurantAiTestResult(result) {
  const target = restaurantAiEl('restaurantAiTestResult');
  if (!target) return;
  if (!result) {
    target.innerHTML = '';
    return;
  }
  const matches = (result.matched_menu_items || []).map(item => `${item.name_tr || item.name_en} - ${restaurantAiMoney(item.price_try)}`).join('\\n') || '-';
  target.innerHTML = `<div class="restaurant-ai-result-grid">
    <div class="restaurant-ai-result-box"><h4>Algılanan niyet</h4><pre>${escapeHtml(result.detected_intent || '-')}</pre></div>
    <div class="restaurant-ai-result-box"><h4>Menü dışı risk</h4><pre>${result.off_menu_risk ? 'Var' : 'Yok'}</pre></div>
    <div class="restaurant-ai-result-box"><h4>Eşleşen ürünler</h4><pre>${escapeHtml(matches)}</pre></div>
    <div class="restaurant-ai-result-box"><h4>Validator sonucu</h4><pre>${escapeHtml(JSON.stringify(result.validator || {}, null, 2))}</pre></div>
    <div class="restaurant-ai-result-box" style="grid-column:1/-1"><h4>Üretilen cevap</h4><pre>${escapeHtml(result.generated_answer || '-')}</pre></div>
  </div>`;
}

async function onRestaurantAiImportCatalog() {
  const hotelId = restaurantAiHotelId();
  if (!hotelId) return notify('Lütfen bir otel seçin.', 'warn');
  if (!confirm('menu_catalog.json DB kataloğuna yeni versiyon olarak aktarılsın mı?')) return;
  try {
    const result = await apiFetch(`/restaurant-ai/catalog/import-default?hotel_id=${encodeURIComponent(hotelId)}`, {method: 'POST', body: {}});
    notify(`Katalog v${result.version} olarak içe aktarıldı.`, 'success');
    await loadRestaurantAiPanel();
  } catch (error) {
    notify(error.message || 'Katalog import edilemedi.', 'error');
  }
}

async function onRestaurantAiManualItem(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  const body = {
    hotel_id: restaurantAiHotelId(),
    venue: String(data.get('venue') || '').trim(),
    menu_type: String(data.get('menu_type') || '').trim(),
    category: String(data.get('category') || '').trim(),
    name_en: String(data.get('name_en') || '').trim(),
    name_tr: String(data.get('name_tr') || '').trim() || null,
    price_try: data.get('price_try') ? Number(data.get('price_try')) : null,
    description_tr: String(data.get('description_tr') || '').trim() || null,
    ingredients: String(data.get('ingredients') || '').split(',').map(item => item.trim()).filter(Boolean),
    tags: String(data.get('tags') || '').split(',').map(item => item.trim()).filter(Boolean),
    notes: String(data.get('notes') || '').trim() || null,
  };
  try {
    await apiFetch('/restaurant-ai/catalog/manual-items', {method: 'POST', body});
    notify('Manuel ürün onay gerekli olarak kaydedildi.', 'success');
    form.reset();
    await loadRestaurantAiCatalog();
  } catch (error) {
    notify(error.message || 'Manuel ürün kaydedilemedi.', 'error');
  }
}

async function onRestaurantAiWaiterCreate(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  const body = {
    hotel_id: restaurantAiHotelId(),
    waiter_name: String(data.get('waiter_name') || '').trim(),
    whatsapp_number: String(data.get('whatsapp_number') || '').trim(),
    role: String(data.get('role') || '').trim() || null,
    venue: String(data.get('venue') || '').trim() || null,
    active: Boolean(data.get('active')),
    receives_order_notifications: Boolean(data.get('receives_order_notifications')),
  };
  try {
    await apiFetch('/restaurant-ai/waiters', {method: 'POST', body});
    notify('Garson numarası eklendi.', 'success');
    form.reset();
    form.active.checked = true;
    form.receives_order_notifications.checked = true;
    await loadRestaurantAiWaiters();
  } catch (error) {
    notify(error.message || 'Garson numarası eklenemedi.', 'error');
  }
}

async function onRestaurantAiQrCreate(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  const body = {
    hotel_id: restaurantAiHotelId(),
    venue: String(data.get('venue') || '').trim(),
    table_no: String(data.get('table_no') || '').trim(),
  };
  try {
    const result = await apiFetch('/restaurant-ai/table-order-link', {method: 'POST', body});
    const target = restaurantAiEl('restaurantAiQrResult');
    if (target) {
      target.innerHTML = `<p><strong>Public sipariş linki</strong></p><p><a href="${escapeHtml(result.order_url)}" target="_blank" rel="noopener">${escapeHtml(result.order_url)}</a></p><p class="muted">Bu bağlantı masa numarasını imzalı token ile taşır; müşteri masa numarasını değiştiremez.</p>`;
    }
    notify('QR sipariş linki üretildi.', 'success');
  } catch (error) {
    notify(error.message || 'QR linki üretilemedi.', 'error');
  }
}

async function onRestaurantAiOffMenuCreate(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  const body = {
    hotel_id: restaurantAiHotelId(),
    requested_text: String(data.get('requested_text') || '').trim(),
    detected_intent: String(data.get('detected_intent') || '').trim() || null,
    venue: String(data.get('venue') || '').trim() || null,
    guest_context: {},
  };
  try {
    await apiFetch('/restaurant-ai/off-menu-requests', {method: 'POST', body});
    notify('Menü dışı talep loglandı; kataloğa eklenmedi.', 'success');
    form.reset();
    await loadRestaurantAiOffMenu();
  } catch (error) {
    notify(error.message || 'Menü dışı talep kaydedilemedi.', 'error');
  }
}

async function onRestaurantAiTest(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  const body = {
    hotel_id: restaurantAiHotelId(),
    question: String(data.get('question') || '').trim(),
    venue: String(data.get('venue') || '').trim() || null,
    menu_type: String(data.get('menu_type') || '').trim() || null,
  };
  try {
    const result = await apiFetch('/restaurant-ai/test-console', {method: 'POST', body});
    renderRestaurantAiTestResult(result);
    notify('Test konsolu çalıştı.', 'success');
  } catch (error) {
    notify(error.message || 'Test çalıştırılamadı.', 'error');
  }
}

async function onRestaurantAiSettingsSave(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const hotelId = restaurantAiHotelId();
  const body = {
    off_menu_response: form.off_menu_response.value.trim(),
    order_confirmation_message: form.order_confirmation_message.value.trim(),
    whatsapp_notification_template: form.whatsapp_notification_template.value.trim(),
    allergy_warning_text: form.allergy_warning_text.value.trim(),
  };
  try {
    await apiFetch(`/restaurant-ai/settings?hotel_id=${encodeURIComponent(hotelId)}`, {method: 'PUT', body});
    notify('Restaurant AI mesajları kaydedildi.', 'success');
    await loadRestaurantAiSettings();
  } catch (error) {
    notify(error.message || 'Mesaj ayarları kaydedilemedi.', 'error');
  }
}

async function onRestaurantAiPanelClick(event) {
  const waiterButton = event.target.closest('[data-restaurant-ai-waiter-toggle]');
  if (waiterButton) {
    const waiterId = waiterButton.dataset.restaurantAiWaiterToggle;
    const field = waiterButton.dataset.field;
    const value = waiterButton.dataset.value === 'true';
    if (!waiterId || !field) return;
    try {
      await apiFetch(`/restaurant-ai/waiters/${encodeURIComponent(waiterId)}?hotel_id=${encodeURIComponent(restaurantAiHotelId())}`, {
        method: 'PATCH',
        body: {[field]: value},
      });
      await loadRestaurantAiWaiters();
      notify('Garson yönlendirmesi güncellendi.', 'success');
    } catch (error) {
      notify(error.message || 'Garson yönlendirmesi güncellenemedi.', 'error');
    }
    return;
  }
  const contentButton = event.target.closest('[data-restaurant-ai-item-content]');
  if (contentButton) {
    const menuItemId = contentButton.dataset.restaurantAiItemContent;
    if (!menuItemId) return;
    const current = contentButton.dataset.ingredients || '';
    const value = window.prompt('İçindekileri virgülle ayırarak girin.', current);
    if (value === null) return;
    const ingredients = String(value || '').split(',').map(item => item.trim()).filter(Boolean);
    try {
      await apiFetch(`/restaurant-ai/catalog/items/${encodeURIComponent(menuItemId)}/content?hotel_id=${encodeURIComponent(restaurantAiHotelId())}`, {
        method: 'PATCH',
        body: {ingredients},
      });
      await loadRestaurantAiCatalog();
      notify('Ürün içeriği güncellendi.', 'success');
    } catch (error) {
      notify(error.message || 'Ürün içeriği güncellenemedi.', 'error');
    }
    return;
  }
  const itemStatusButton = event.target.closest('[data-restaurant-ai-item-status]');
  if (itemStatusButton) {
    const menuItemId = itemStatusButton.dataset.restaurantAiItemStatus;
    const status = itemStatusButton.dataset.status;
    try {
      await apiFetch(`/restaurant-ai/catalog/items/${encodeURIComponent(menuItemId)}/status?hotel_id=${encodeURIComponent(restaurantAiHotelId())}`, {
        method: 'PATCH',
        body: {status},
      });
      await loadRestaurantAiCatalog();
      notify('Ürün durumu güncellendi.', 'success');
    } catch (error) {
      notify(error.message || 'Ürün durumu güncellenemedi.', 'error');
    }
    return;
  }
  const orderStatusButton = event.target.closest('[data-restaurant-ai-order-status]');
  if (orderStatusButton) {
    const orderId = orderStatusButton.dataset.restaurantAiOrderStatus;
    const status = orderStatusButton.dataset.status;
    try {
      await apiFetch(`/restaurant-ai/orders/${encodeURIComponent(orderId)}?hotel_id=${encodeURIComponent(restaurantAiHotelId())}`, {
        method: 'PATCH',
        body: {confirmation_status: status},
      });
      await loadRestaurantAiOrders();
      notify('Sipariş durumu güncellendi.', 'success');
    } catch (error) {
      notify(error.message || 'Sipariş durumu güncellenemedi.', 'error');
    }
  }
}

function initRestaurantAiPanel() {
  restaurantAiEl('restaurantAiImportCatalog')?.addEventListener('click', onRestaurantAiImportCatalog);
  restaurantAiEl('restaurantAiCatalogToggle')?.addEventListener('click', event => {
    const expanded = event.currentTarget.getAttribute('aria-expanded') === 'true';
    setRestaurantAiCatalogExpanded(!expanded);
  });
  restaurantAiEl('restaurantAiCatalogFilters')?.addEventListener('submit', event => {
    event.preventDefault();
    loadRestaurantAiCatalog();
  });
  restaurantAiEl('restaurantAiManualItemForm')?.addEventListener('submit', onRestaurantAiManualItem);
  restaurantAiEl('restaurantAiQrForm')?.addEventListener('submit', onRestaurantAiQrCreate);
  restaurantAiEl('restaurantAiWaiterForm')?.addEventListener('submit', onRestaurantAiWaiterCreate);
  restaurantAiEl('restaurantAiOffMenuForm')?.addEventListener('submit', onRestaurantAiOffMenuCreate);
  restaurantAiEl('restaurantAiOrderFilters')?.addEventListener('submit', event => {
    event.preventDefault();
    loadRestaurantAiOrders();
  });
  restaurantAiEl('restaurantAiTestForm')?.addEventListener('submit', onRestaurantAiTest);
  restaurantAiEl('restaurantAiSettingsForm')?.addEventListener('submit', onRestaurantAiSettingsSave);
  document.querySelector('[data-view="restaurantai"]')?.addEventListener('click', onRestaurantAiPanelClick);
}

window.loadRestaurantAiPanel = loadRestaurantAiPanel;
initRestaurantAiPanel();
"""
