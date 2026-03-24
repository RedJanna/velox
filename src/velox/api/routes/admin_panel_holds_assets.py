"""Hold module assets — CSS & JS for Konaklama, Restoran, Transfer tabs."""

# ruff: noqa: E501

ADMIN_HOLDS_STYLE = """\
.holds-tabs{display:flex;gap:4px;margin-bottom:16px}
.holds-tab{padding:10px 22px;border-radius:var(--radius-sm) var(--radius-sm) 0 0;background:var(--surface-2);border:1px solid var(--line);border-bottom:none;cursor:pointer;font-weight:700;font-size:14px;color:var(--muted);transition:background .18s,color .18s,box-shadow .18s}
.holds-tab:hover{background:var(--surface);color:var(--ink)}
.holds-tab.is-active{background:var(--surface);color:var(--ink);box-shadow:0 -2px 0 var(--accent) inset}
.holds-panel{animation:holdsFadeIn .15s ease}
@keyframes holdsFadeIn{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
.filter-chips{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.filter-chip{padding:6px 14px;border-radius:999px;border:1px solid var(--line);background:var(--surface);cursor:pointer;font-size:13px;font-weight:600;color:var(--muted);transition:all .15s}
.filter-chip:hover{border-color:var(--accent);color:var(--accent)}
.filter-chip.is-active{background:linear-gradient(135deg,var(--accent),var(--accent-2));color:#fff;border-color:var(--accent)}
.rez-no-cell{font-family:var(--mono);font-size:13px;font-weight:700;color:var(--accent);letter-spacing:.02em}
.rez-no-hero{font-family:var(--mono);font-size:18px;font-weight:800;color:var(--accent);margin-top:4px}
.wizard-steps{display:flex;gap:0;margin-bottom:20px;border:1px solid var(--line);border-radius:var(--radius-sm);overflow:hidden}
.wizard-step{flex:1;padding:12px 14px;text-align:center;font-size:13px;font-weight:700;border-right:1px solid var(--line);color:var(--muted);background:var(--surface-2);cursor:pointer;transition:all .15s}
.wizard-step:last-child{border-right:none}
.wizard-step.is-active{background:var(--surface);color:var(--accent);box-shadow:0 -3px 0 var(--accent) inset}
.wizard-step.is-done{background:var(--surface);color:var(--ok)}
.wizard-body .field-grid{margin-top:14px}
.wizard-nav{display:flex;justify-content:space-between;gap:10px;margin-top:18px}
.creation-header{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:14px}
.toggle-mode{display:flex;align-items:center;gap:10px;padding:12px 16px;border-radius:var(--radius-sm);border:1px solid var(--line);background:var(--surface-2);margin-bottom:14px}
.toggle-mode label{font-size:13px;font-weight:600;color:var(--ink);cursor:pointer;display:flex;align-items:center;gap:8px}
.wizard-loading{display:flex;align-items:center;justify-content:center;gap:10px;padding:40px 20px;color:var(--muted);font-size:14px;font-weight:600}
.wizard-loading::before{content:'';width:20px;height:20px;border:3px solid var(--line);border-top-color:var(--accent);border-radius:50%;animation:wizSpin .7s linear infinite}
@keyframes wizSpin{to{transform:rotate(360deg)}}
.wizard-error{padding:18px;border-radius:var(--radius-sm);background:rgba(180,35,24,.06);border:1px solid rgba(180,35,24,.18);color:var(--danger);font-size:13px;font-weight:600}
.summary-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:14px}
.summary-card{border:1px solid var(--line);border-radius:var(--radius-sm);padding:16px;background:var(--surface)}
.summary-card h4{font-size:13px;font-weight:800;color:var(--accent);text-transform:uppercase;letter-spacing:.04em;margin:0 0 10px 0}
.summary-card .row{display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid var(--line);font-size:13px}
.summary-card .row:last-child{border-bottom:none}
.summary-card .row .label{color:var(--muted);font-weight:600}
.summary-card .row .value{font-weight:700;color:var(--ink)}
.summary-total{margin-top:14px;padding:14px 18px;border-radius:var(--radius-sm);background:linear-gradient(135deg,var(--accent),var(--accent-2));color:#fff;display:flex;justify-content:space-between;align-items:center}
.summary-total .total-label{font-size:14px;font-weight:700}
.summary-total .total-value{font-family:var(--mono);font-size:22px;font-weight:900}
@media(max-width:980px){.summary-grid{grid-template-columns:1fr}.room-card-grid{grid-template-columns:1fr}}
"""

ADMIN_HOLDS_SCRIPT = """\
// ---------------------------------------------------------------------------
// Hold Module — Shared Constants & Status Labels
// ---------------------------------------------------------------------------
const STATUS_LABELS_TR = {
  '': 'Tumu',
  'PENDING_APPROVAL': 'Onay Bekliyor',
  'PMS_PENDING': 'PMS Isleniyor',
  'PMS_CREATED': 'PMS Olusturuldu',
  'PAYMENT_PENDING': 'Odeme Bekliyor',
  'PAYMENT_EXPIRED': 'Odeme Suresi Doldu',
  'MANUAL_REVIEW': 'Inceleme Gerekli',
  'PMS_FAILED': 'PMS Hatasi',
  'APPROVED': 'Onaylandi',
  'CONFIRMED': 'Tamamlandi',
  'REJECTED': 'Reddedildi',
  'BEKLEMEDE': 'Onay Bekliyor',
  'ONAYLANDI': 'Onaylandi',
  'GELDI': 'Geldi',
  'GELMEDI': 'Gelmedi',
  'IPTAL': 'Iptal',
  'DEGISIKLIK_UYGULA': 'Degisiklik Uygula',
};
const STAY_STATUS_KEYS = ['', 'PENDING_APPROVAL', 'PMS_PENDING', 'PMS_CREATED', 'PAYMENT_PENDING', 'PAYMENT_EXPIRED', 'MANUAL_REVIEW', 'PMS_FAILED', 'APPROVED', 'CONFIRMED', 'REJECTED'];
const SIMPLE_STATUS_KEYS = ['', 'PENDING_APPROVAL', 'APPROVED', 'CONFIRMED', 'REJECTED'];
const RESTAURANT_STATUS_KEYS = ['', 'BEKLEMEDE', 'ONAYLANDI', 'GELDI', 'GELMEDI', 'IPTAL', 'DEGISIKLIK_UYGULA'];

function holdStatusLabel(status) {
  return STATUS_LABELS_TR[String(status || '').toUpperCase()] || String(status || '-');
}

// ---------------------------------------------------------------------------
// Hold Module — Shared Utility Functions (moved from main assets)
// ---------------------------------------------------------------------------
function holdStatusClass(status) {
  const n = String(status || '').toUpperCase();
  if (['PMS_FAILED', 'MANUAL_REVIEW', 'REJECTED', 'IPTAL', 'GELMEDI'].includes(n)) return 'danger';
  if (['PENDING_APPROVAL', 'PMS_PENDING', 'PAYMENT_PENDING', 'BEKLEMEDE', 'DEGISIKLIK_UYGULA'].includes(n)) return 'warn';
  if (['PMS_CREATED', 'CONFIRMED', 'ONAYLANDI', 'GELDI'].includes(n)) return 'success';
  if (['PAYMENT_EXPIRED', 'APPROVED'].includes(n)) return 'info';
  return 'pending';
}

function holdDraftField(item, key, fallback) {
  const draft = item && item.draft_json && typeof item.draft_json === 'object' ? item.draft_json : {};
  const v = draft[key];
  if (v === null || v === undefined || v === '') return String(fallback);
  return String(v);
}

function holdChildrenCount(item) {
  const draft = item && item.draft_json && typeof item.draft_json === 'object' ? item.draft_json : {};
  return Array.isArray(draft.chd_ages) ? draft.chd_ages.length : 0;
}

function formatHoldSummaryDetailCell(label, value) {
  return '<div><span>' + escapeHtml(label) + '</span><strong>' + escapeHtml(String(value)) + '</strong></div>';
}

function holdHasPersistedReservation(item) {
  return Boolean(item && (item.pms_reservation_id || item.voucher_no));
}

function holdNeedsManualReviewIntervention(item) {
  const reason = String(item?.manual_review_reason || '');
  if (holdHasPersistedReservation(item)) return true;
  return ['create_missing_identifiers', 'create_unverified_after_readback'].includes(reason);
}

function isHoldApproveActionable(item) {
  const holdType = String(item?.type || '').toLowerCase();
  const status = String(item?.status || '').toUpperCase();
  if (holdType === 'stay') {
    if (status === 'MANUAL_REVIEW' && holdNeedsManualReviewIntervention(item)) return false;
    return ['PENDING_APPROVAL', 'APPROVED', 'MANUAL_REVIEW', 'PMS_FAILED'].includes(status);
  }
  return status === 'PENDING_APPROVAL';
}

function holdApproveButtonLabel(item) {
  const status = String(item?.status || '').toUpperCase();
  if (status === 'MANUAL_REVIEW' && holdNeedsManualReviewIntervention(item)) return 'Inceleme Gerekli';
  if (['APPROVED', 'MANUAL_REVIEW', 'PMS_FAILED'].includes(status)) return 'Yeniden Dene';
  return 'Onayla';
}

function mapFailedTool(toolName) {
  const n = String(toolName || '').trim();
  if (!n) return '-';
  if (n === 'booking_create_reservation') return 'PMS rezervasyon olusturma';
  if (n === 'booking_get_reservation') return 'PMS readback dogrulamasi';
  if (n === 'payment_request_prepayment') return 'Odeme talebi olusturma';
  return n;
}

function mapManualReviewReason(reason) {
  const n = String(reason || '').trim();
  if (!n) return '-';
  if (n === 'create_missing_identifiers') return 'PMS create yanitinda reservation id/voucher gelmedi.';
  if (n === 'create_unverified_after_readback') return 'Create sonrasi readback dogrulamasi basarisiz.';
  if (n.startsWith('create_failed:')) {
    const parts = n.split(':');
    return 'PMS create hatasi (' + (parts[1] || 'UnknownError') + '), aksiyon: ' + (parts[2] || 'manual_review') + '.';
  }
  return n;
}

function formatHoldTechnicalState(item) {
  const workflowState = item.workflow_state ? String(item.workflow_state) : '-';
  const reservationId = item.pms_reservation_id ? String(item.pms_reservation_id) : '-';
  const voucherNo = item.voucher_no ? String(item.voucher_no) : '-';
  const manualReason = mapManualReviewReason(item.manual_review_reason);
  const failedTool = mapFailedTool(item.last_failed_tool);
  const failedErrorType = item.last_failed_error_type ? String(item.last_failed_error_type) : '-';
  return '<div class="stack">'
    + '<span class="muted">Workflow: <strong>' + escapeHtml(workflowState) + '</strong></span>'
    + '<span class="muted">PMS ID: <strong>' + escapeHtml(reservationId) + '</strong></span>'
    + '<span class="muted">Voucher: <strong>' + escapeHtml(voucherNo) + '</strong></span>'
    + '<span class="muted">Son hata araci: <strong>' + escapeHtml(failedTool) + '</strong></span>'
    + '<span class="muted">Hata tipi: <strong>' + escapeHtml(failedErrorType) + '</strong></span>'
    + '<span class="muted">Not: <strong>' + escapeHtml(manualReason) + '</strong></span>'
    + '</div>';
}

function holdTimelineLevel(item) {
  const s = String(item.status || '').toUpperCase();
  if (['MANUAL_REVIEW', 'PMS_FAILED', 'REJECTED'].includes(s)) return 'danger';
  if (['PMS_PENDING', 'PENDING_APPROVAL', 'PAYMENT_PENDING'].includes(s)) return 'warn';
  return 'done';
}

function formatHoldTimeline(item) {
  const approvalTs = item.approval_decided_at || item.approved_at || null;
  const rows = [
    {label: 'Hold olusturuldu', value: item.created_at ? formatDate(item.created_at) : '-', level: 'done'},
    {label: 'Admin onayi', value: approvalTs ? formatDate(approvalTs) : 'Bekleniyor', level: approvalTs ? 'done' : 'warn'},
    {label: 'PMS create basladi', value: item.pms_create_started_at ? formatDate(item.pms_create_started_at) : 'Baslamadi', level: item.pms_create_started_at ? 'done' : 'warn'},
    {label: 'PMS create tamamlandi', value: item.pms_create_completed_at ? formatDate(item.pms_create_completed_at) : 'Tamamlanmadi', level: item.pms_create_completed_at ? 'done' : 'warn'},
    {label: 'Odeme talebi', value: item.payment_requested_at ? formatDate(item.payment_requested_at) : 'Olusturulmadi', level: item.payment_requested_at ? 'done' : 'warn'},
    {label: 'Mevcut workflow', value: String(item.workflow_state || item.status || '-'), level: holdTimelineLevel(item)},
  ];
  return '<div class="hold-timeline">' + rows.map(function(row) {
    return '<div class="hold-timeline-item"><span class="hold-timeline-dot ' + escapeHtml(row.level) + '"></span><div><strong>' + escapeHtml(row.label) + '</strong><span>' + escapeHtml(row.value) + '</span></div></div>';
  }).join('') + '</div>';
}

function formatHoldSummary(item) {
  const checkin = holdDraftField(item, 'checkin_date', '-');
  const checkout = holdDraftField(item, 'checkout_date', '-');
  const guest = holdDraftField(item, 'guest_name', '-');
  const adults = Number(holdDraftField(item, 'adults', '0') || 0);
  const children = holdChildrenCount(item);
  const total = escapeHtml(holdDraftField(item, 'total_price_eur', '-')) + ' EUR';
  const cancelPolicy = holdDraftField(item, 'cancel_policy_type', '-');
  return '<div class="hold-summary-grid">'
    + '<div><span>Misafir</span><strong>' + escapeHtml(guest) + '</strong></div>'
    + '<div><span>Tarih</span><strong>' + escapeHtml(checkin) + ' → ' + escapeHtml(checkout) + '</strong></div>'
    + '<div><span>Kisi</span><strong>' + escapeHtml(String(adults)) + 'Y / ' + escapeHtml(String(children)) + 'C</strong></div>'
    + '<div><span>Tutar</span><strong>' + total + '</strong></div>'
    + '<div><span>Politika</span><strong>' + escapeHtml(cancelPolicy) + '</strong></div>'
    + '<div><span>Tip</span><strong>' + escapeHtml(String(item.type || '-').toUpperCase()) + '</strong></div>'
    + '</div>';
}

// ---------------------------------------------------------------------------
// Tab Management
// ---------------------------------------------------------------------------
function switchHoldsTab(tab) {
  state.activeHoldsTab = tab === 'restaurant' ? 'stay' : tab;
  document.querySelectorAll('[data-holds-tab]').forEach(function(btn) {
    btn.classList.toggle('is-active', btn.dataset.holdsTab === state.activeHoldsTab);
  });
  document.querySelectorAll('[data-holds-panel]').forEach(function(panel) {
    panel.hidden = panel.dataset.holdsPanel !== state.activeHoldsTab;
  });
  if (state.activeHoldsTab === 'stay') loadStayHolds();
  if (state.activeHoldsTab === 'transfer') loadTransferHolds();
}

// ---------------------------------------------------------------------------
// KONAKLAMA MODULE
// ---------------------------------------------------------------------------
function renderStatusChips(containerId, keys, currentFilter, dataPrefix) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = keys.map(function(key) {
    return '<button type="button" class="filter-chip ' + (key === currentFilter ? 'is-active' : '') + '" data-' + dataPrefix + '-status="' + escapeHtml(key) + '" aria-label="' + escapeHtml(holdStatusLabel(key) + ' filtresi') + '">' + escapeHtml(holdStatusLabel(key)) + '</button>';
  }).join('');
}

async function loadStayHolds() {
  const hotelId = state.selectedHotelId;
  const params = new URLSearchParams();
  if (state.me?.role === 'ADMIN' && hotelId) params.set('hotel_id', hotelId);
  if (state.stayStatusFilter) params.set('status', state.stayStatusFilter);

  const resNoInput = document.querySelector('#stayHoldFilters input[name="reservation_no"]');
  const resNoValue = resNoInput ? resNoInput.value.trim() : '';
  if (resNoValue) params.set('reservation_no', resNoValue);

  const response = await apiFetch('/holds/stay?' + params.toString());
  state.stayHolds = response.items || [];
  const selectedExists = state.stayHolds.some(function(i) { return String(i.hold_id) === String(state.selectedStayHoldId); });
  if (!selectedExists) state.selectedStayHoldId = state.stayHolds.length ? String(state.stayHolds[0].hold_id) : '';
  state.selectedStayHold = state.stayHolds.find(function(i) { return String(i.hold_id) === String(state.selectedStayHoldId); }) || null;
  renderStatusChips('stayStatusChips', STAY_STATUS_KEYS, state.stayStatusFilter, 'stay');
  refs.stayHoldTableBody.innerHTML = renderStayHoldRows(state.stayHolds);
  renderStayHoldDetail(state.selectedStayHold);
}

function renderStayHoldRows(items) {
  if (!items.length) return '<tr><td colspan="7"><div class="empty-state"><p>Konaklama kaydı bulunamadı.</p></div></td></tr>';
  return items.map(function(item) {
    var isSelected = String(item.hold_id) === String(state.selectedStayHoldId);
    return '<tr class="' + (isSelected ? 'is-selected' : '') + '" data-open-hold="' + escapeHtml(item.hold_id) + '">'
      + '<td><button class="inline-button secondary" data-open-hold="' + escapeHtml(item.hold_id) + '" aria-label="' + escapeHtml(item.hold_id + ' detayini ac') + '">Detay</button></td>'
      + '<td><span class="rez-no-cell">' + escapeHtml(item.reservation_no || '-') + '</span></td>'
      + '<td><div class="stack"><strong>' + escapeHtml(item.hold_id) + '</strong><span class="muted">Hotel ' + escapeHtml(String(item.hotel_id)) + '</span></div></td>'
      + '<td><span class="pill ' + holdStatusClass(item.status) + '">' + escapeHtml(holdStatusLabel(item.status)) + '</span></td>'
      + '<td>' + escapeHtml(holdDraftField(item, 'guest_name', '-')) + '</td>'
      + '<td><span class="muted">' + escapeHtml(holdDraftField(item, 'checkin_date', '-')) + ' → ' + escapeHtml(holdDraftField(item, 'checkout_date', '-')) + '</span></td>'
      + '<td><strong>' + escapeHtml(holdDraftField(item, 'total_price_eur', '-')) + ' EUR</strong></td>'
      + '</tr>';
  }).join('');
}

function selectStayHold(holdId) {
  state.selectedStayHoldId = String(holdId || '');
  state.selectedStayHold = state.stayHolds.find(function(i) { return String(i.hold_id) === state.selectedStayHoldId; }) || null;
  refs.stayHoldTableBody.innerHTML = renderStayHoldRows(state.stayHolds);
  renderStayHoldDetail(state.selectedStayHold);
}

function renderStayHoldDetail(item) {
  if (!item) {
    refs.stayHoldDetail.innerHTML = '<div class="empty-state"><p>Detay icin listeden bir kayit secin.</p></div>';
    return;
  }
  refs.stayHoldDetail.innerHTML = '<div class="module-header"><div>'
    + '<h3>' + escapeHtml(String(item.hold_id || 'Hold')) + '</h3>'
    + '<p class="rez-no-hero">' + escapeHtml(item.reservation_no || '-') + '</p>'
    + '<p class="muted">KONAKLAMA · Hotel ' + escapeHtml(String(item.hotel_id || '-')) + '</p>'
    + '</div><span class="pill ' + holdStatusClass(item.status) + '">' + escapeHtml(holdStatusLabel(item.status)) + '</span></div>'
    + '<div class="hold-summary-grid mb-md">'
    + formatHoldSummaryDetailCell('Misafir', holdDraftField(item, 'guest_name', '-'))
    + formatHoldSummaryDetailCell('Tarih', holdDraftField(item, 'checkin_date', '-') + ' → ' + holdDraftField(item, 'checkout_date', '-'))
    + formatHoldSummaryDetailCell('Kisi', holdDraftField(item, 'adults', '0') + 'Y / ' + holdChildrenCount(item) + 'C')
    + formatHoldSummaryDetailCell('Toplam', holdDraftField(item, 'total_price_eur', '-') + ' EUR')
    + formatHoldSummaryDetailCell('Politika', holdDraftField(item, 'cancel_policy_type', '-'))
    + formatHoldSummaryDetailCell('Telefon', holdDraftField(item, 'phone', '-'))
    + '</div>'
    + '<div class="helper-box"><strong>Teknik Durum</strong>' + formatHoldTechnicalState(item) + '</div>'
    + '<div class="helper-box mt-md"><strong>Islem Zaman Cizelgesi</strong>' + formatHoldTimeline(item) + '</div>'
    + '<div class="dialog-actions hold-detail-actions mt-lg">'
    + '<button class="action-button primary" data-approve-hold="' + escapeHtml(item.hold_id) + '" aria-label="' + escapeHtml(item.hold_id + ' holdunu onayla') + '" ' + (isHoldApproveActionable(item) ? '' : 'disabled') + '>' + escapeHtml(holdApproveButtonLabel(item)) + '</button>'
    + '<button class="action-button danger" data-reject-hold="' + escapeHtml(item.hold_id) + '" aria-label="' + escapeHtml(item.hold_id + ' holdunu reddet') + '">Reddet</button>'
    + '</div>';
}

// Stay creation wizard — 3-step direct flow (no availability query)
var STAY_WIZARD_LABELS = ['Misafir', 'Detay', 'Ozet'];

function toggleStayCreatePanel() {
  var panel = document.getElementById('stayHoldCreatePanel');
  if (!panel) return;
  panel.hidden = !panel.hidden;
  if (!panel.hidden) {
    state.stayWizardStep = 1;
    state.stayWizardUseExisting = false;
    state.stayDraft = {};
    state.stayProfileRoomTypes = [];
    state.stayWizardReprocessHoldId = null;
    loadStayProfileRoomTypes();
    renderStayWizardStep();
  }
}

// Load room types from hotel profile (cached per hotel)
async function loadStayProfileRoomTypes() {
  try {
    var resp = await apiFetch('/elektraweb/room-types?hotel_id=' + encodeURIComponent(state.selectedHotelId));
    state.stayProfileRoomTypes = (resp.room_types || []).map(function(r) {
      return {
        pms_room_type_id: r.pms_room_type_id,
        name: (r.name && r.name.tr) || r.name || 'Oda',
        max_pax: r.max_pax || 0,
      };
    });
  } catch (e) {
    state.stayProfileRoomTypes = [];
  }
}

function renderStayWizardStep() {
  var stepsEl = document.getElementById('stayWizardSteps');
  var bodyEl = document.getElementById('stayWizardBody');
  if (!stepsEl || !bodyEl) return;
  var step = state.stayWizardStep || 1;
  stepsEl.innerHTML = STAY_WIZARD_LABELS.map(function(l, i) {
    var cls = (i + 1) === step ? 'is-active' : ((i + 1) < step ? 'is-done' : '');
    return '<div class="wizard-step ' + cls + '" data-stay-wizard-step="' + (i + 1) + '">' + escapeHtml((i + 1) + '. ' + l) + '</div>';
  }).join('');

  if (step === 1) renderStayWizardGuest(bodyEl);
  else if (step === 2) renderStayWizardDetails(bodyEl);
  else if (step === 3) renderStayWizardSummary(bodyEl);
}

// Step 1 — Misafir bilgileri
function renderStayWizardGuest(bodyEl) {
  var d = state.stayDraft || {};
  bodyEl.innerHTML = '<div class="toggle-mode"><label><input type="checkbox" id="stayUseExisting" ' + (state.stayWizardUseExisting ? 'checked' : '') + '> Mevcut rezervasyonu kullan</label></div>'
    + '<div class="field-grid">'
    + (state.stayWizardUseExisting
      ? '<div class="field full"><label>Rezervasyon Numarasi</label><input id="stayLookupResNo" placeholder="VLX-21966-..." aria-label="Mevcut rezervasyon numarasi"></div>'
      : '<div class="field"><label>Misafir Adi *</label><input id="stayGuestName" value="' + escapeHtml(d.guest_name || '') + '" aria-label="Misafir adi"></div>'
        + '<div class="field"><label>Telefon *</label><input id="stayPhone" value="' + escapeHtml(d.phone || '') + '" placeholder="+905..." aria-label="Telefon"></div>'
        + '<div class="field"><label>E-posta</label><input id="stayEmail" type="email" value="' + escapeHtml(d.email || '') + '" placeholder="misafir@ornek.com" aria-label="E-posta"></div>'
        + '<div class="field"><label>Uyruk</label><select id="stayNationality" aria-label="Uyruk"><option value="TR"' + ((d.nationality || 'TR') === 'TR' ? ' selected' : '') + '>TR - Turkiye</option><option value="GB"' + (d.nationality === 'GB' ? ' selected' : '') + '>GB - Ingiltere</option><option value="DE"' + (d.nationality === 'DE' ? ' selected' : '') + '>DE - Almanya</option><option value="RU"' + (d.nationality === 'RU' ? ' selected' : '') + '>RU - Rusya</option><option value="NL"' + (d.nationality === 'NL' ? ' selected' : '') + '>NL - Hollanda</option><option value="US"' + (d.nationality === 'US' ? ' selected' : '') + '>US - ABD</option><option value="OTHER"' + (d.nationality === 'OTHER' ? ' selected' : '') + '>Diger</option></select></div>')
    + '</div>'
    + '<div class="wizard-nav">'
    + (state.stayWizardUseExisting
      ? '<button class="inline-button primary" type="button" data-stay-lookup-action aria-label="Rezervasyon ara">Rezervasyonu Ara</button>'
      : '<span></span><button class="inline-button primary" type="button" data-stay-wizard-next aria-label="Sonraki adim">Sonraki</button>')
    + '</div>';
}

// Step 2 — Detay: tarih, kisi, oda tipi, pansiyon, fiyat, iptal politikasi
function renderStayWizardDetails(bodyEl) {
  var d = state.stayDraft || {};
  var today = new Date().toISOString().split('T')[0];
  var rooms = state.stayProfileRoomTypes || [];
  var roomOpts = '<option value="">-- Oda tipi secin --</option>' + rooms.map(function(r) {
    var sel = String(d.room_type_id) === String(r.pms_room_type_id) ? ' selected' : '';
    return '<option value="' + escapeHtml(String(r.pms_room_type_id)) + '"' + sel + '>' + escapeHtml(r.name) + ' (max ' + escapeHtml(String(r.max_pax)) + ')</option>';
  }).join('');
  var boardOpts = '<option value="BB"' + ((d.board_type || 'BB') === 'BB' ? ' selected' : '') + '>Oda Kahvalti (BB)</option>'
    + '<option value="HB"' + (d.board_type === 'HB' ? ' selected' : '') + '>Yarim Pansiyon (HB)</option>'
    + '<option value="FB"' + (d.board_type === 'FB' ? ' selected' : '') + '>Tam Pansiyon (FB)</option>'
    + '<option value="AI"' + (d.board_type === 'AI' ? ' selected' : '') + '>Her Sey Dahil (AI)</option>'
    + '<option value="RO"' + (d.board_type === 'RO' ? ' selected' : '') + '>Sadece Oda (RO)</option>';
  var cancelOpts = '<option value="FREE_CANCEL"' + ((d.cancel_policy_type || 'FREE_CANCEL') === 'FREE_CANCEL' ? ' selected' : '') + '>Ucretsiz Iptal</option>'
    + '<option value="NON_REFUNDABLE"' + (d.cancel_policy_type === 'NON_REFUNDABLE' ? ' selected' : '') + '>Iade Edilmez</option>';
  bodyEl.innerHTML = '<div class="field-grid">'
    + '<div class="field"><label>Giris Tarihi *</label><input id="stayCheckin" type="date" min="' + escapeHtml(today) + '" value="' + escapeHtml(d.checkin_date || '') + '" aria-label="Giris tarihi"></div>'
    + '<div class="field"><label>Cikis Tarihi *</label><input id="stayCheckout" type="date" min="' + escapeHtml(today) + '" value="' + escapeHtml(d.checkout_date || '') + '" aria-label="Cikis tarihi"></div>'
    + '<div class="field"><label>Yetiskin *</label><input id="stayAdults" type="number" min="1" max="6" value="' + escapeHtml(String(d.adults || 1)) + '" aria-label="Yetiskin sayisi"></div>'
    + '<div class="field"><label>Cocuk Yaslari (virgul ile)</label><input id="stayChdAges" value="' + escapeHtml((d.chd_ages || []).join(',')) + '" placeholder="4,8" aria-label="Cocuk yaslari"></div>'
    + '<div class="field"><label>Oda Tipi *</label><select id="stayRoomType" aria-label="Oda tipi">' + roomOpts + '</select></div>'
    + '<div class="field"><label>Pansiyon Tipi</label><select id="stayBoardType" aria-label="Pansiyon tipi">' + boardOpts + '</select></div>'
    + '<div class="field"><label>Iptal Politikasi</label><select id="stayCancelPolicy" aria-label="Iptal politikasi">' + cancelOpts + '</select></div>'
    + '<div class="field"><label>Toplam Fiyat (EUR) *</label><input id="stayTotalPrice" type="number" min="0" step="0.01" value="' + escapeHtml(String(d.total_price_eur || '')) + '" placeholder="0.00" aria-label="Toplam fiyat EUR"></div>'
    + '</div>'
    + '<div class="wizard-nav"><button class="inline-button secondary" type="button" data-stay-wizard-prev aria-label="Onceki adim">Geri</button><button class="inline-button primary" type="button" data-stay-wizard-next aria-label="Ozete git">Ozet</button></div>';
}

// Step 3 — Ozet & olustur
function renderStayWizardSummary(bodyEl) {
  var d = state.stayDraft || {};
  var rooms = state.stayProfileRoomTypes || [];
  var selectedRoom = rooms.find(function(r) { return String(r.pms_room_type_id) === String(d.room_type_id); });
  var roomName = selectedRoom ? selectedRoom.name : '-';
  var boardLabels = {BB: 'Oda Kahvalti', HB: 'Yarim Pansiyon', FB: 'Tam Pansiyon', AI: 'Her Sey Dahil', RO: 'Sadece Oda'};
  var cancelLabels = {FREE_CANCEL: 'Ucretsiz Iptal', NON_REFUNDABLE: 'Iade Edilmez'};

  function sRow(label, value) {
    return '<div class="row"><span class="label">' + escapeHtml(label) + '</span><span class="value">' + escapeHtml(String(value || '-')) + '</span></div>';
  }

  bodyEl.innerHTML = '<div class="summary-grid">'
    + '<div class="summary-card"><h4>Misafir</h4>'
    + sRow('Ad Soyad', d.guest_name)
    + sRow('Telefon', d.phone)
    + sRow('E-posta', d.email || '-')
    + sRow('Uyruk', d.nationality || 'TR')
    + '</div>'
    + '<div class="summary-card"><h4>Konaklama</h4>'
    + sRow('Giris', d.checkin_date)
    + sRow('Cikis', d.checkout_date)
    + sRow('Yetiskin', d.adults || 1)
    + sRow('Cocuk', d.chd_ages && d.chd_ages.length ? d.chd_ages.join(', ') + ' yas' : 'Yok')
    + '</div>'
    + '<div class="summary-card"><h4>Oda</h4>'
    + sRow('Oda Tipi', roomName)
    + sRow('Pansiyon', boardLabels[d.board_type] || d.board_type || '-')
    + sRow('Iptal Politikasi', cancelLabels[d.cancel_policy_type] || d.cancel_policy_type || '-')
    + '</div>'
    + '<div class="summary-card"><h4>Notlar</h4>'
    + '<div class="field full" style="margin-top:4px"><textarea id="stayNotes" rows="3" aria-label="Notlar" style="width:100%;font-size:13px;border:1px solid var(--line);border-radius:8px;padding:8px">' + escapeHtml(d.notes || '') + '</textarea></div>'
    + '</div>'
    + '</div>'
    + '<div class="summary-total"><span class="total-label">Toplam Tutar</span><span class="total-value">' + escapeHtml(String(d.total_price_eur || 0)) + ' EUR</span></div>'
    + '<div class="wizard-nav"><button class="inline-button secondary" type="button" data-stay-wizard-prev>Geri</button>'
    + '<button class="inline-button primary" type="button" data-stay-submit-action>' + (state.stayWizardUseExisting ? 'Yeniden Islem Baslat' : 'Rezervasyon Olustur') + '</button></div>';
}

function collectStayDraftFromStep(step) {
  if (!state.stayDraft) state.stayDraft = {};
  if (step === 1 && !state.stayWizardUseExisting) {
    var nameEl = document.getElementById('stayGuestName');
    var phoneEl = document.getElementById('stayPhone');
    var emailEl = document.getElementById('stayEmail');
    var natEl = document.getElementById('stayNationality');
    if (nameEl) state.stayDraft.guest_name = nameEl.value.trim();
    if (phoneEl) state.stayDraft.phone = phoneEl.value.trim();
    if (emailEl) state.stayDraft.email = emailEl.value.trim();
    if (natEl) state.stayDraft.nationality = natEl.value;
  } else if (step === 2) {
    var ciEl = document.getElementById('stayCheckin');
    var coEl = document.getElementById('stayCheckout');
    var adEl = document.getElementById('stayAdults');
    var chEl = document.getElementById('stayChdAges');
    var rtEl = document.getElementById('stayRoomType');
    var btEl = document.getElementById('stayBoardType');
    var cpEl = document.getElementById('stayCancelPolicy');
    var prEl = document.getElementById('stayTotalPrice');
    if (ciEl) state.stayDraft.checkin_date = ciEl.value;
    if (coEl) state.stayDraft.checkout_date = coEl.value;
    if (adEl) state.stayDraft.adults = Number(adEl.value) || 1;
    if (chEl) state.stayDraft.chd_ages = chEl.value.split(',').map(function(v) { return parseInt(v.trim(), 10); }).filter(function(v) { return !isNaN(v); });
    if (rtEl) state.stayDraft.room_type_id = rtEl.value;
    if (btEl) state.stayDraft.board_type = btEl.value;
    if (cpEl) state.stayDraft.cancel_policy_type = cpEl.value;
    if (prEl) state.stayDraft.total_price_eur = Number(prEl.value) || 0;
    // Resolve room type name for payload
    var rooms = state.stayProfileRoomTypes || [];
    var matchedRoom = rooms.find(function(r) { return String(r.pms_room_type_id) === String(state.stayDraft.room_type_id); });
    state.stayDraft.room_type_name = matchedRoom ? matchedRoom.name : '';
  } else if (step === 3) {
    var notesEl = document.getElementById('stayNotes');
    if (notesEl) state.stayDraft.notes = notesEl.value.trim();
  }
}

async function lookupStayReservationNo() {
  var resNoEl = document.getElementById('stayLookupResNo');
  if (!resNoEl || !resNoEl.value.trim()) {
    notify('Rezervasyon numarasi girin.', 'warn');
    return;
  }
  try {
    var result = await apiFetch('/holds/stay/by-reservation-no/' + encodeURIComponent(resNoEl.value.trim()));
    state.stayDraft = result.draft_json || {};
    state.stayDraft.guest_name = state.stayDraft.guest_name || '';
    state.stayDraft.phone = state.stayDraft.phone || '';
    state.stayWizardReprocessHoldId = result.hold_id;
    notify('Rezervasyon bulundu. Bilgileri kontrol edip devam edin.', 'success');
    state.stayWizardStep = 2;
    renderStayWizardStep();
  } catch (error) {
    notify(error.message || 'Bu rezervasyon numarasiyla kayit bulunamadi.', 'warn');
  }
}

async function submitStayHold() {
  collectStayDraftFromStep(3);
  var draft = state.stayDraft || {};
  if (!draft.guest_name) { notify('Misafir adi zorunlu.', 'warn'); return; }
  if (!draft.checkin_date || !draft.checkout_date) { notify('Tarih alanlari zorunlu.', 'warn'); return; }

  if (state.stayWizardUseExisting && state.stayWizardReprocessHoldId) {
    try {
      await apiFetch('/holds/' + encodeURIComponent(state.stayWizardReprocessHoldId) + '/approve?force=true', {method: 'POST', body: {notes: ''}});
      notify('Hold yeniden isleme alindi.', 'success');
      toggleStayCreatePanel();
      loadStayHolds();
      loadDashboard();
    } catch (error) {
      notify(error.message, 'error');
    }
    return;
  }

  var totalPrice = Number(draft.total_price_eur || 0);
  if (!totalPrice || totalPrice <= 0) { notify('Gecerli bir fiyat girin.', 'warn'); return; }
  if (!draft.room_type_id) { notify('Oda tipi secin.', 'warn'); return; }

  // Resolve rate mapping from cancel policy
  var rateMapping = {FREE_CANCEL: {rate_type_id: 24178, rate_code_id: 183666}, NON_REFUNDABLE: {rate_type_id: 24171, rate_code_id: 183659}};
  var selectedRate = rateMapping[draft.cancel_policy_type] || rateMapping.FREE_CANCEL;

  try {
    var payload = {
      hotel_id: Number(state.selectedHotelId),
      guest_name: draft.guest_name,
      phone: draft.phone || '',
      email: draft.email || '',
      nationality: draft.nationality || 'TR',
      checkin_date: draft.checkin_date,
      checkout_date: draft.checkout_date,
      adults: draft.adults || 1,
      chd_ages: draft.chd_ages || [],
      total_price_eur: totalPrice,
      room_type_id: Number(draft.room_type_id) || 0,
      board_type_id: 2,
      rate_type_id: selectedRate.rate_type_id,
      rate_code_id: selectedRate.rate_code_id,
      price_agency_id: null,
      cancel_policy_type: draft.cancel_policy_type || 'FREE_CANCEL',
      room_type_name: draft.room_type_name || '',
      board_type_name: draft.board_type || 'BB',
      notes: draft.notes || '',
    };
    var result = await apiFetch('/holds/stay/create', {method: 'POST', body: payload});
    notify('Konaklama rezervasyonu olusturuldu: ' + (result.reservation_no || result.hold_id), 'success');
    state.stayDraft = {};
    toggleStayCreatePanel();
    loadStayHolds();
    loadDashboard();
  } catch (error) {
    notify(error.message, 'error');
  }
}

// ---------------------------------------------------------------------------
// RESTORAN MODULE
// ---------------------------------------------------------------------------
function normalizeSpecialRequestText(value) {
  return String(value || '')
    .toLocaleLowerCase('tr-TR')
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[\\s\\.,!?:;\\-_/\\\\"'`~()\\[\\]{}]+/g, ' ')
    .replace(/\\s+/g, ' ')
    .trim();
}

function hasMeaningfulSpecialRequest(value) {
  var normalized = normalizeSpecialRequestText(value);
  if (!normalized) return false;

  var exactNoRequestValues = new Set([
    'yok', 'yoktur', 'yoktu', 'hayir', 'hayirdir', 'istemiyor', 'istek yok', 'ozel istek yok', 'ozel talep yok', 'herhangi bir istek yok', 'ozel bir istek yok',
    'none', 'no', 'nope', 'n a', 'na', 'nil', 'null', 'nothing', 'nothing special', 'no special request', 'no special requests', 'no request', 'no requests', 'no preference', 'no preferences', 'not applicable', 'nothing to add',
    'aucun', 'aucune', 'aucune demande', 'aucune demande speciale', 'pas de demande', 'pas de demande speciale',
    'ninguno', 'ninguna', 'sin solicitud', 'sin solicitudes', 'sin peticiones', 'sin peticion especial', 'ninguna solicitud especial',
    'keine', 'keiner', 'keine anfrage', 'keine anfragen', 'keine besonderen wunsche', 'kein besonderer wunsch',
    'nessuno', 'nessuna', 'nessuna richiesta', 'nessuna richiesta speciale',
    'nenhum', 'nenhuma', 'sem pedido', 'sem pedidos', 'sem solicitacao especial', 'nenhuma solicitacao especial',
    'niks', 'geen', 'geen verzoek', 'geen speciale verzoeken',
    'net', 'nic', 'brak', 'brak prosby', 'brak specjalnych zyczen',
    'nyet', 'niet', 'bez prosby', 'bez osobych pozhelaniy',
    'لا يوجد', 'لا', 'لا طلب', 'لا توجد طلبات', 'لا يوجد طلب خاص',
    '无', '没有', '没有要求', '没有特殊要求', '无特殊要求',
    'なし', 'ありません', '特になし', '特別な要望なし',
    '없음', '없어요', '특이사항 없음', '특별 요청 없음',
    'nahi', 'koi nahi', 'koi request nahi', 'koi khas darkhast nahi',
    'yok hocam', 'ozel istek bulunmuyor', 'misafirin ozel istegi yok'
  ]);
  if (exactNoRequestValues.has(normalized)) return false;

  var noRequestPatterns = [
    /\bozel( bir)? istek yok\b/,
    /\bozel talep yok\b/,
    /\bherhangi bir istek yok\b/,
    /\bherhangi bir ozel istek yok\b/,
    /\bmisafirin ozel istegi yok\b/,
    /\bistek bulunmuyor\b/,
    /\bno special request(s)?\b/,
    /\bno request(s)?\b/,
    /\bno preference(s)?\b/,
    /\bnothing special\b/,
    /\bnothing to add\b/,
    /\bwithout special request(s)?\b/,
    /\baucune? demande( speciale)?\b/,
    /\bpas de demande( speciale)?\b/,
    /\bsin (solicitud|solicitudes|peticion|peticiones)( especial(es)?)?\b/,
    /\bninguna solicitud especial\b/,
    /\bkein(e|er)? besondere(n)? wunsch(e)?\b/,
    /\bkeine anfrage(n)?\b/,
    /\bnessuna richiesta( speciale)?\b/,
    /\bsem (pedido|pedidos|solicitacao especial)\b/,
    /\bnenhuma solicitacao especial\b/,
    /\bgeen speciale verzoek(en)?\b/,
    /\bbrak specjalnych zyczen\b/,
    /\bbez osobych pozhelaniy\b/,
    /لا يوجد طلب( خاص)?/,
    /没有(特殊)?要求/,
    /特に?なし/,
    /特別な要望なし/,
    /특별 요청 없음/,
    /특이사항 없음/,
    /koi (request|khas darkhast) nahi/
  ];

  return !noRequestPatterns.some(function(pattern) { return pattern.test(normalized); });
}

function detectSpecialRequestTags(value) {
  var normalized = normalizeSpecialRequestText(value);
  if (!hasMeaningfulSpecialRequest(normalized)) return [];

  var tagRules = [
    { label: 'Alerji', patterns: [/alerji/, /allerg/, /allergie/, /allergia/, /حساسي/, /过敏/, /アレルギ/, /알레르기/] },
    { label: 'Vegan/Vejetaryen', patterns: [/vegan/, /vegetarian/, /vejetaryen/, /glutensiz/, /gluten free/, /helal/, /halal/, /kosher/] },
    { label: 'Çocuk', patterns: [/cocuk/, /çocuk/, /bebek/, /baby/, /high chair/, /mama sandalyesi/, /kids?/, /stroller/] },
    { label: 'Pencere Kenarı', patterns: [/pencere/, /window/, /cam kenari/, /window side/, /vista/, /view/] },
    { label: 'Dış/İç Alan', patterns: [/outdoor/, /indoor/, /teras/, /terrace/, /bahce/, /garden/, /patio/, /dis mekan/, /ic mekan/] },
    { label: 'Doğum Günü/Kutlama', patterns: [/dogum gunu/, /doğum günü/, /birthday/, /anniversary/, /honeymoon/, /balayi/, /balayı/, /celebrat/, /romantic/, /romantik/] },
    { label: 'Erişilebilirlik', patterns: [/wheelchair/, /tekerlekli sandalye/, /accessible/, /disabled/, /engelli/, /accessibility/] },
    { label: 'Geç Saat', patterns: [/late/, /gec/, /geç/, /delay/, /delayed/, /gecik/, /late arrival/] },
    { label: 'Masa Tercihi', patterns: [/masa/, /table/, /corner/, /kose/, /köşe/, /quiet/, /sessiz/, /near music/, /uzak/] }
  ];

  return tagRules
    .filter(function(rule) { return rule.patterns.some(function(pattern) { return pattern.test(normalized); }); })
    .map(function(rule) { return rule.label; })
    .slice(0, 3);
}

async function loadRestaurantHolds() {
  var hotelId = state.selectedHotelId;
  var params = new URLSearchParams();
  if (state.me?.role === 'ADMIN' && hotelId) params.set('hotel_id', hotelId);
  if (state.restaurantStatusFilter) params.set('status', state.restaurantStatusFilter);
  if (state.restaurantDateFrom) params.set('date_from', state.restaurantDateFrom);
  if (state.restaurantDateTo) params.set('date_to', state.restaurantDateTo);
  if (refs.restaurantDateFrom) refs.restaurantDateFrom.value = state.restaurantDateFrom || '';
  if (refs.restaurantDateTo) refs.restaurantDateTo.value = state.restaurantDateTo || '';
  var response = await apiFetch('/holds/restaurant?' + params.toString());
  state.restaurantHolds = response.items || [];
  var selectedExists = state.restaurantHolds.some(function(i) { return String(i.hold_id) === String(state.selectedRestaurantHoldId); });
  if (!selectedExists) state.selectedRestaurantHoldId = state.restaurantHolds.length ? String(state.restaurantHolds[0].hold_id) : '';
  state.selectedRestaurantHold = state.restaurantHolds.find(function(i) { return String(i.hold_id) === String(state.selectedRestaurantHoldId); }) || null;
  renderStatusChips('restaurantStatusChips', RESTAURANT_STATUS_KEYS, state.restaurantStatusFilter, 'restaurant');
  refs.restaurantHoldTableBody.innerHTML = renderRestaurantHoldRows(state.restaurantHolds);
  renderRestaurantHoldDetail(state.selectedRestaurantHold);
}

function renderRestaurantHoldRows(items) {
  if (!items.length) return '<tr><td colspan="6"><div class="empty-state"><p>Restoran kaydı bulunamadı.</p></div></td></tr>';
  return items.map(function(item) {
    var isSelected = String(item.hold_id) === String(state.selectedRestaurantHoldId);
    var hasSpecialRequest = hasMeaningfulSpecialRequest(item.notes);
    var requestTags = detectSpecialRequestTags(item.notes);
    var requestTagHtml = requestTags.length ? '<div class="inline-flex-center" style="flex-wrap:wrap">' + requestTags.map(function(tag){ return '<span class="pill info">' + escapeHtml(tag) + '</span>'; }).join('') + '</div>' : '';
    return '<tr class="' + (isSelected ? 'is-selected ' : '') + (hasSpecialRequest ? 'has-special-request' : '') + '" data-open-hold="' + escapeHtml(item.hold_id) + '">'
      + '<td><button class="inline-button secondary" data-open-hold="' + escapeHtml(item.hold_id) + '" aria-label="' + escapeHtml(item.hold_id + ' detayini ac') + '">Detay</button></td>'
      + '<td><div class="stack"><strong>' + escapeHtml(item.hold_id) + '</strong><span class="muted">Hotel ' + escapeHtml(String(item.hotel_id)) + '</span>' + (hasSpecialRequest ? '<span class="pill warn">Ozel Istek Var</span>' : '') + requestTagHtml + '</div></td>'
      + '<td><span class="pill ' + holdStatusClass(item.status) + '">' + escapeHtml(holdStatusLabel(item.status)) + '</span></td>'
      + '<td>' + escapeHtml(item.guest_name || '-') + '</td>'
      + '<td><span class="muted">' + escapeHtml(item.date || '-') + ' ' + escapeHtml(item.time || '') + '</span>'
      + (item.created_at ? '<br><small class="muted">Olusturma: ' + escapeHtml(formatDate(item.created_at)) + '</small>' : '') + '</td>'
      + '<td>' + escapeHtml(String(item.party_size || '-')) + ' kisi' + (hasSpecialRequest ? '<br><small style="color:#92400e;font-weight:700">' + escapeHtml((item.notes || '').trim().slice(0, 60)) + '</small>' : '') + '</td>'
      + '</tr>';
  }).join('');
}

function selectRestaurantHold(holdId) {
  state.selectedRestaurantHoldId = String(holdId || '');
  state.selectedRestaurantHold = state.restaurantHolds.find(function(i) { return String(i.hold_id) === state.selectedRestaurantHoldId; }) || null;
  refs.restaurantHoldTableBody.innerHTML = renderRestaurantHoldRows(state.restaurantHolds);
  renderRestaurantHoldDetail(state.selectedRestaurantHold);
}

function renderRestaurantHoldDetail(item) {
  if (!item) {
    refs.restaurantHoldDetail.innerHTML = '<div class="empty-state"><p>Detay icin listeden bir kayit secin.</p></div>';
    return;
  }
  var status = String(item.status || '').toUpperCase();
  var canApprove = status === 'BEKLEMEDE' || status === 'DEGISIKLIK_UYGULA';
  var canMarkArrived = status === 'ONAYLANDI';
  var canMarkNoShow = status === 'ONAYLANDI';
  var canExtend = status === 'ONAYLANDI';
  var hasSpecialRequest = hasMeaningfulSpecialRequest(item.notes);
  var requestTags = detectSpecialRequestTags(item.notes);
  var requestTagHtml = requestTags.length ? '<div class="inline-flex-center" style="flex-wrap:wrap;justify-content:flex-end">' + requestTags.map(function(tag){ return '<span class="pill info">' + escapeHtml(tag) + '</span>'; }).join('') + '</div>' : '';
  refs.restaurantHoldDetail.innerHTML = '<div class="module-header"><div>'
    + '<h3>' + escapeHtml(String(item.hold_id || 'Hold')) + '</h3>'
    + '<p class="muted">RESTORAN · Hotel ' + escapeHtml(String(item.hotel_id || '-')) + '</p>'
    + '</div><div class="stack" style="align-items:flex-end"><span class="pill ' + holdStatusClass(item.status) + '">' + escapeHtml(holdStatusLabel(item.status)) + '</span>' + (String(item.approved_by || '').toUpperCase() === 'AI_RESTAURAN' ? '<span class="pill info">AI Restoran</span>' : '') + (hasSpecialRequest ? '<span class="pill warn">Ozel Istek</span>' : '') + requestTagHtml + '</div></div>'
    + '<div class="hold-summary-grid mb-md">'
    + formatHoldSummaryDetailCell('Misafir', item.guest_name || '-')
    + formatHoldSummaryDetailCell('Tarih', (item.date || '-') + ' ' + (item.time || ''))
    + formatHoldSummaryDetailCell('Kisi Sayisi', String(item.party_size || '-'))
    + formatHoldSummaryDetailCell('Alan', item.area || '-')
    + formatHoldSummaryDetailCell('Telefon', item.phone || '-')
    + formatHoldSummaryDetailCell('Notlar', hasSpecialRequest ? (item.notes || '-') : '-')
    + '</div>'
    + '<div class="dialog-actions hold-detail-actions mt-lg">'
    + '<button class="action-button primary" data-restaurant-hold="' + escapeHtml(item.hold_id) + '" data-restaurant-status="ONAYLANDI" ' + (canApprove ? '' : 'disabled') + '>Onayla</button>'
    + '<button class="action-button danger" data-reject-hold="' + escapeHtml(item.hold_id) + '">Reddet</button>'
    + '<button class="action-button primary" data-restaurant-hold="' + escapeHtml(item.hold_id) + '" data-restaurant-status="GELDI" ' + (canMarkArrived ? '' : 'disabled') + '>Geldi</button>'
    + '<button class="action-button warn" data-restaurant-hold="' + escapeHtml(item.hold_id) + '" data-restaurant-status="GELMEDI" ' + (canMarkNoShow ? '' : 'disabled') + '>Gelmedi</button>'
    + '<button class="action-button secondary" data-restaurant-extend="' + escapeHtml(item.hold_id) + '" ' + (canExtend ? '' : 'disabled') + '>+15 Dakika</button>'
    + '</div>';
}

function toggleRestaurantCreatePanel() {
  var panel = document.getElementById('restaurantHoldCreatePanel');
  if (!panel) return;
  panel.hidden = !panel.hidden;
}

async function submitRestaurantHold(event) {
  event.preventDefault();
  var form = document.getElementById('restaurantCreateForm');
  if (!form) return;
  var payload = {
    hotel_id: Number(state.selectedHotelId),
    slot_id: Number(form.slot_id.value),
    party_size: Number(form.party_size.value) || 1,
    guest_name: form.guest_name.value.trim(),
    phone: form.phone.value.trim(),
    notes: form.notes ? form.notes.value.trim() : '',
  };
  if (!payload.guest_name) { notify('Misafir adi zorunlu.', 'warn'); return; }
  if (!payload.slot_id) { notify('Slot ID zorunlu.', 'warn'); return; }
  try {
    await apiFetch('/holds/restaurant/create', {method: 'POST', body: payload});
    notify('Restoran rezervasyonu olusturuldu.', 'success');
    form.reset();
    toggleRestaurantCreatePanel();
    loadRestaurantHolds();
    loadDashboard();
  } catch (error) {
    notify(error.message, 'error');
  }
}

// ---------------------------------------------------------------------------
// TRANSFER MODULE
// ---------------------------------------------------------------------------
async function loadTransferHolds() {
  var hotelId = state.selectedHotelId;
  var params = new URLSearchParams();
  if (state.me?.role === 'ADMIN' && hotelId) params.set('hotel_id', hotelId);
  if (state.transferStatusFilter) params.set('status', state.transferStatusFilter);
  var response = await apiFetch('/holds/transfer?' + params.toString());
  state.transferHolds = response.items || [];
  var selectedExists = state.transferHolds.some(function(i) { return String(i.hold_id) === String(state.selectedTransferHoldId); });
  if (!selectedExists) state.selectedTransferHoldId = state.transferHolds.length ? String(state.transferHolds[0].hold_id) : '';
  state.selectedTransferHold = state.transferHolds.find(function(i) { return String(i.hold_id) === String(state.selectedTransferHoldId); }) || null;
  renderStatusChips('transferStatusChips', SIMPLE_STATUS_KEYS, state.transferStatusFilter, 'transfer');
  refs.transferHoldTableBody.innerHTML = renderTransferHoldRows(state.transferHolds);
  renderTransferHoldDetail(state.selectedTransferHold);
}

function renderTransferHoldRows(items) {
  if (!items.length) return '<tr><td colspan="6"><div class="empty-state"><p>Transfer kaydı bulunamadı.</p></div></td></tr>';
  return items.map(function(item) {
    var isSelected = String(item.hold_id) === String(state.selectedTransferHoldId);
    return '<tr class="' + (isSelected ? 'is-selected' : '') + '" data-open-hold="' + escapeHtml(item.hold_id) + '">'
      + '<td><button class="inline-button secondary" data-open-hold="' + escapeHtml(item.hold_id) + '" aria-label="' + escapeHtml(item.hold_id + ' detayini ac') + '">Detay</button></td>'
      + '<td><div class="stack"><strong>' + escapeHtml(item.hold_id) + '</strong><span class="muted">Hotel ' + escapeHtml(String(item.hotel_id)) + '</span></div></td>'
      + '<td><span class="pill ' + holdStatusClass(item.status) + '">' + escapeHtml(holdStatusLabel(item.status)) + '</span></td>'
      + '<td>' + escapeHtml(item.guest_name || '-') + '</td>'
      + '<td><span class="muted">' + escapeHtml(item.route || '-') + ' · ' + escapeHtml(item.date || '-') + '</span></td>'
      + '<td>' + escapeHtml(String(item.pax_count || '-')) + ' kisi</td>'
      + '</tr>';
  }).join('');
}

function selectTransferHold(holdId) {
  state.selectedTransferHoldId = String(holdId || '');
  state.selectedTransferHold = state.transferHolds.find(function(i) { return String(i.hold_id) === state.selectedTransferHoldId; }) || null;
  refs.transferHoldTableBody.innerHTML = renderTransferHoldRows(state.transferHolds);
  renderTransferHoldDetail(state.selectedTransferHold);
}

function renderTransferHoldDetail(item) {
  if (!item) {
    refs.transferHoldDetail.innerHTML = '<div class="empty-state"><p>Detay icin listeden bir kayit secin.</p></div>';
    return;
  }
  refs.transferHoldDetail.innerHTML = '<div class="module-header"><div>'
    + '<h3>' + escapeHtml(String(item.hold_id || 'Hold')) + '</h3>'
    + '<p class="muted">TRANSFER · Hotel ' + escapeHtml(String(item.hotel_id || '-')) + '</p>'
    + '</div><span class="pill ' + holdStatusClass(item.status) + '">' + escapeHtml(holdStatusLabel(item.status)) + '</span></div>'
    + '<div class="hold-summary-grid mb-md">'
    + formatHoldSummaryDetailCell('Misafir', item.guest_name || '-')
    + formatHoldSummaryDetailCell('Guzergah', item.route || '-')
    + formatHoldSummaryDetailCell('Tarih', (item.date || '-') + ' ' + (item.time || ''))
    + formatHoldSummaryDetailCell('Kisi', String(item.pax_count || '-'))
    + formatHoldSummaryDetailCell('Ucus', item.flight_no || '-')
    + formatHoldSummaryDetailCell('Arac', item.vehicle_type || '-')
    + formatHoldSummaryDetailCell('Fiyat', (item.price_eur ? item.price_eur + ' EUR' : '-'))
    + formatHoldSummaryDetailCell('Telefon', item.phone || '-')
    + '</div>'
    + '<div class="dialog-actions hold-detail-actions mt-lg">'
    + '<button class="action-button primary" data-approve-hold="' + escapeHtml(item.hold_id) + '" ' + (String(item.status).toUpperCase() === 'PENDING_APPROVAL' ? '' : 'disabled') + '>Onayla</button>'
    + '<button class="action-button danger" data-reject-hold="' + escapeHtml(item.hold_id) + '">Reddet</button>'
    + '</div>';
}

function toggleTransferCreatePanel() {
  var panel = document.getElementById('transferHoldCreatePanel');
  if (!panel) return;
  panel.hidden = !panel.hidden;
}

async function submitTransferHold(event) {
  event.preventDefault();
  var form = document.getElementById('transferCreateForm');
  if (!form) return;
  var payload = {
    hotel_id: Number(state.selectedHotelId),
    route: form.route.value.trim(),
    date: form.date.value,
    time: form.time ? form.time.value : null,
    pax_count: Number(form.pax_count.value) || 1,
    guest_name: form.guest_name.value.trim(),
    phone: form.phone ? form.phone.value.trim() : '',
    flight_no: form.flight_no ? form.flight_no.value.trim() : null,
    vehicle_type: form.vehicle_type ? form.vehicle_type.value : null,
    price_eur: form.price_eur ? Number(form.price_eur.value) || null : null,
    notes: form.notes ? form.notes.value.trim() : '',
  };
  if (!payload.guest_name) { notify('Misafir adi zorunlu.', 'warn'); return; }
  if (!payload.route) { notify('Guzergah zorunlu.', 'warn'); return; }
  if (!payload.date) { notify('Tarih zorunlu.', 'warn'); return; }
  try {
    await apiFetch('/holds/transfer/create', {method: 'POST', body: payload});
    notify('Transfer rezervasyonu olusturuldu.', 'success');
    form.reset();
    toggleTransferCreatePanel();
    loadTransferHolds();
    loadDashboard();
  } catch (error) {
    notify(error.message, 'error');
  }
}

// ---------------------------------------------------------------------------
// Delegated events for hold modules (called from main bindDelegatedEvents)
// ---------------------------------------------------------------------------
function handleHoldsModuleClick(target) {
  // Tab switching
  if (target.dataset.holdsTab) {
    switchHoldsTab(target.dataset.holdsTab);
    return true;
  }
  // Stay create toggle
  if (target.hasAttribute('data-stay-toggle-create')) {
    toggleStayCreatePanel();
    return true;
  }
  // Stay wizard steps
  if (target.dataset.stayWizardStep) {
    var targetStep = Number(target.dataset.stayWizardStep);
    if (targetStep < (state.stayWizardStep || 1)) {
      collectStayDraftFromStep(state.stayWizardStep);
      state.stayWizardStep = targetStep;
      renderStayWizardStep();
    }
    return true;
  }
  if (target.hasAttribute('data-stay-wizard-next')) {
    var curStep = state.stayWizardStep || 1;
    collectStayDraftFromStep(curStep);
    var d = state.stayDraft || {};
    if (curStep === 1 && !state.stayWizardUseExisting) {
      if (!d.guest_name) { notify('Misafir adi zorunlu.', 'warn'); return true; }
      if (!d.phone) { notify('Telefon numarasi zorunlu.', 'warn'); return true; }
    }
    if (curStep === 2) {
      if (!d.checkin_date || !d.checkout_date) { notify('Giris ve cikis tarihlerini girin.', 'warn'); return true; }
      if (d.checkout_date <= d.checkin_date) { notify('Cikis tarihi giris tarihinden sonra olmali.', 'warn'); return true; }
      if (!d.room_type_id) { notify('Oda tipi secin.', 'warn'); return true; }
      if (!d.total_price_eur || d.total_price_eur <= 0) { notify('Gecerli bir fiyat girin.', 'warn'); return true; }
    }
    state.stayWizardStep = curStep + 1;
    renderStayWizardStep();
    return true;
  }
  if (target.hasAttribute('data-stay-wizard-prev')) {
    collectStayDraftFromStep(state.stayWizardStep || 1);
    state.stayWizardStep = Math.max(1, (state.stayWizardStep || 1) - 1);
    renderStayWizardStep();
    return true;
  }
  if (target.hasAttribute('data-stay-lookup-action')) {
    lookupStayReservationNo();
    return true;
  }
  if (target.hasAttribute('data-stay-submit-action')) {
    submitStayHold();
    return true;
  }
  // UseExisting toggle
  if (target.id === 'stayUseExisting') {
    state.stayWizardUseExisting = target.checked;
    state.stayDraft = {};
    state.stayWizardReprocessHoldId = null;
    renderStayWizardStep();
    return true;
  }
  // Status chip clicks
  if (target.dataset.stayStatus !== undefined) {
    state.stayStatusFilter = target.dataset.stayStatus;
    loadStayHolds();
    return true;
  }
  if (target.dataset.restaurantStatus !== undefined) {
    state.restaurantStatusFilter = target.dataset.restaurantStatus;
    loadRestaurantHolds();
    return true;
  }
  if (target.dataset.transferStatus !== undefined) {
    state.transferStatusFilter = target.dataset.transferStatus;
    loadTransferHolds();
    return true;
  }
  // Restaurant/Transfer create toggles
  if (target.hasAttribute('data-restaurant-toggle-create')) {
    toggleRestaurantCreatePanel();
    return true;
  }
  if (target.hasAttribute('data-transfer-toggle-create')) {
    toggleTransferCreatePanel();
    return true;
  }
  // Hold selection (route to correct module based on prefix)
  if (target.dataset.openHold) {
    var hid = target.dataset.openHold;
    if (hid.startsWith('S_HOLD_')) selectStayHold(hid);
    else if (hid.startsWith('R_HOLD_')) selectRestaurantHold(hid);
    else if (hid.startsWith('TR_HOLD_')) selectTransferHold(hid);
    return true;
  }
  return false;
}
"""
