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
};
const STAY_STATUS_KEYS = ['', 'PENDING_APPROVAL', 'PMS_PENDING', 'PMS_CREATED', 'PAYMENT_PENDING', 'PAYMENT_EXPIRED', 'MANUAL_REVIEW', 'PMS_FAILED', 'APPROVED', 'CONFIRMED', 'REJECTED'];
const SIMPLE_STATUS_KEYS = ['', 'PENDING_APPROVAL', 'APPROVED', 'CONFIRMED', 'REJECTED'];

function holdStatusLabel(status) {
  return STATUS_LABELS_TR[String(status || '').toUpperCase()] || String(status || '-');
}

// ---------------------------------------------------------------------------
// Hold Module — Shared Utility Functions (moved from main assets)
// ---------------------------------------------------------------------------
function holdStatusClass(status) {
  const n = String(status || '').toUpperCase();
  if (['PMS_FAILED', 'MANUAL_REVIEW', 'REJECTED'].includes(n)) return 'danger';
  if (['PENDING_APPROVAL', 'PMS_PENDING', 'PAYMENT_PENDING'].includes(n)) return 'warn';
  if (['PMS_CREATED', 'CONFIRMED'].includes(n)) return 'success';
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
  state.activeHoldsTab = tab;
  document.querySelectorAll('[data-holds-tab]').forEach(function(btn) {
    btn.classList.toggle('is-active', btn.dataset.holdsTab === tab);
  });
  document.querySelectorAll('[data-holds-panel]').forEach(function(panel) {
    panel.hidden = panel.dataset.holdsPanel !== tab;
  });
  if (tab === 'stay') loadStayHolds();
  if (tab === 'restaurant') loadRestaurantHolds();
  if (tab === 'transfer') loadTransferHolds();
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

// Stay creation wizard
function toggleStayCreatePanel() {
  var panel = document.getElementById('stayHoldCreatePanel');
  if (!panel) return;
  panel.hidden = !panel.hidden;
  if (!panel.hidden) {
    state.stayWizardStep = 1;
    state.stayWizardUseExisting = false;
    renderStayWizardStep();
  }
}

function renderStayWizardStep() {
  var stepsEl = document.getElementById('stayWizardSteps');
  var bodyEl = document.getElementById('stayWizardBody');
  if (!stepsEl || !bodyEl) return;
  var step = state.stayWizardStep || 1;
  var labels = ['Misafir', 'Detay', 'Fiyat'];
  stepsEl.innerHTML = labels.map(function(l, i) {
    var cls = (i + 1) === step ? 'is-active' : ((i + 1) < step ? 'is-done' : '');
    return '<div class="wizard-step ' + cls + '" data-stay-wizard-step="' + (i + 1) + '">' + escapeHtml((i + 1) + '. ' + l) + '</div>';
  }).join('');

  if (step === 1) {
    bodyEl.innerHTML = '<div class="toggle-mode"><label><input type="checkbox" id="stayUseExisting" ' + (state.stayWizardUseExisting ? 'checked' : '') + '> Mevcut rezervasyonu kullan</label></div>'
      + '<div class="field-grid">'
      + (state.stayWizardUseExisting
        ? '<div class="field full"><label>Rezervasyon Numarasi</label><input id="stayLookupResNo" placeholder="VLX-..." aria-label="Mevcut rezervasyon numarasi"></div>'
        : '<div class="field"><label>Misafir Adi</label><input id="stayGuestName" value="' + escapeHtml(state.stayDraft?.guest_name || '') + '" aria-label="Misafir adi"></div>'
          + '<div class="field"><label>Telefon</label><input id="stayPhone" value="' + escapeHtml(state.stayDraft?.phone || '') + '" placeholder="+905..." aria-label="Telefon"></div>')
      + '</div>'
      + '<div class="wizard-nav">'
      + (state.stayWizardUseExisting
        ? '<button class="inline-button primary" type="button" data-stay-lookup-action aria-label="Rezervasyon ara">Rezervasyonu Ara</button>'
        : '<span></span><button class="inline-button primary" type="button" data-stay-wizard-next aria-label="Sonraki adim">Sonraki</button>')
      + '</div>';
  } else if (step === 2) {
    bodyEl.innerHTML = '<div class="field-grid">'
      + '<div class="field"><label>Giris Tarihi</label><input id="stayCheckin" type="date" value="' + escapeHtml(state.stayDraft?.checkin_date || '') + '" aria-label="Giris tarihi"></div>'
      + '<div class="field"><label>Cikis Tarihi</label><input id="stayCheckout" type="date" value="' + escapeHtml(state.stayDraft?.checkout_date || '') + '" aria-label="Cikis tarihi"></div>'
      + '<div class="field"><label>Yetiskin</label><input id="stayAdults" type="number" min="1" value="' + escapeHtml(String(state.stayDraft?.adults || 1)) + '" aria-label="Yetiskin sayisi"></div>'
      + '<div class="field"><label>Cocuk Yaslari (virgul ile)</label><input id="stayChdAges" value="' + escapeHtml((state.stayDraft?.chd_ages || []).join(',')) + '" placeholder="4,8" aria-label="Cocuk yaslari"></div>'
      + '</div>'
      + '<div class="wizard-nav"><button class="inline-button secondary" type="button" data-stay-wizard-prev aria-label="Onceki adim">Geri</button><button class="inline-button primary" type="button" data-stay-wizard-next aria-label="Sonraki adim">Sonraki</button></div>';
  } else if (step === 3) {
    bodyEl.innerHTML = '<div class="field-grid">'
      + '<div class="field"><label>Toplam Fiyat (EUR)</label><input id="stayPrice" type="number" step="0.01" min="0" value="' + escapeHtml(String(state.stayDraft?.total_price_eur || '')) + '" aria-label="Toplam fiyat"></div>'
      + '<div class="field"><label>Iptal Politikasi</label><select id="stayCancelPolicy" aria-label="Iptal politikasi"><option value="FREE_CANCEL" ' + (state.stayDraft?.cancel_policy_type === 'FREE_CANCEL' ? 'selected' : '') + '>Ucretsiz Iptal</option><option value="NON_REFUNDABLE" ' + (state.stayDraft?.cancel_policy_type === 'NON_REFUNDABLE' ? 'selected' : '') + '>Iade Edilmez</option></select></div>'
      + '<div class="field full"><label>Notlar</label><textarea id="stayNotes" rows="2" aria-label="Notlar">' + escapeHtml(state.stayDraft?.notes || '') + '</textarea></div>'
      + '</div>'
      + '<div class="wizard-nav"><button class="inline-button secondary" type="button" data-stay-wizard-prev aria-label="Onceki adim">Geri</button><button class="inline-button primary" type="button" data-stay-submit-action aria-label="Rezervasyon olustur">' + (state.stayWizardUseExisting ? 'Yeniden Islem Baslat' : 'Rezervasyon Olustur') + '</button></div>';
  }
}

function collectStayDraftFromStep(step) {
  if (!state.stayDraft) state.stayDraft = {};
  if (step === 1 && !state.stayWizardUseExisting) {
    var nameEl = document.getElementById('stayGuestName');
    var phoneEl = document.getElementById('stayPhone');
    if (nameEl) state.stayDraft.guest_name = nameEl.value.trim();
    if (phoneEl) state.stayDraft.phone = phoneEl.value.trim();
  } else if (step === 2) {
    var ciEl = document.getElementById('stayCheckin');
    var coEl = document.getElementById('stayCheckout');
    var adEl = document.getElementById('stayAdults');
    var chEl = document.getElementById('stayChdAges');
    if (ciEl) state.stayDraft.checkin_date = ciEl.value;
    if (coEl) state.stayDraft.checkout_date = coEl.value;
    if (adEl) state.stayDraft.adults = Number(adEl.value) || 1;
    if (chEl) state.stayDraft.chd_ages = chEl.value.split(',').map(function(v) { return parseInt(v.trim(), 10); }).filter(function(v) { return !isNaN(v); });
  } else if (step === 3) {
    var priceEl = document.getElementById('stayPrice');
    var policyEl = document.getElementById('stayCancelPolicy');
    var notesEl = document.getElementById('stayNotes');
    if (priceEl) state.stayDraft.total_price_eur = Number(priceEl.value) || 0;
    if (policyEl) state.stayDraft.cancel_policy_type = policyEl.value;
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
  if (!draft.total_price_eur || draft.total_price_eur <= 0) { notify('Gecerli bir fiyat girin.', 'warn'); return; }

  if (state.stayWizardUseExisting && state.stayWizardReprocessHoldId) {
    try {
      await apiFetch('/holds/' + encodeURIComponent(state.stayWizardReprocessHoldId) + '/approve', {method: 'POST', body: {notes: ''}});
      notify('Hold yeniden isleme alindi.', 'success');
      toggleStayCreatePanel();
      loadStayHolds();
      loadDashboard();
    } catch (error) {
      notify(error.message, 'error');
    }
    return;
  }

  try {
    var payload = {
      hotel_id: Number(state.selectedHotelId),
      guest_name: draft.guest_name,
      phone: draft.phone || '',
      checkin_date: draft.checkin_date,
      checkout_date: draft.checkout_date,
      adults: draft.adults || 1,
      chd_ages: draft.chd_ages || [],
      total_price_eur: draft.total_price_eur,
      cancel_policy_type: draft.cancel_policy_type || 'FREE_CANCEL',
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
async function loadRestaurantHolds() {
  var hotelId = state.selectedHotelId;
  var params = new URLSearchParams();
  if (state.me?.role === 'ADMIN' && hotelId) params.set('hotel_id', hotelId);
  if (state.restaurantStatusFilter) params.set('status', state.restaurantStatusFilter);
  var response = await apiFetch('/holds/restaurant?' + params.toString());
  state.restaurantHolds = response.items || [];
  var selectedExists = state.restaurantHolds.some(function(i) { return String(i.hold_id) === String(state.selectedRestaurantHoldId); });
  if (!selectedExists) state.selectedRestaurantHoldId = state.restaurantHolds.length ? String(state.restaurantHolds[0].hold_id) : '';
  state.selectedRestaurantHold = state.restaurantHolds.find(function(i) { return String(i.hold_id) === String(state.selectedRestaurantHoldId); }) || null;
  renderStatusChips('restaurantStatusChips', SIMPLE_STATUS_KEYS, state.restaurantStatusFilter, 'restaurant');
  refs.restaurantHoldTableBody.innerHTML = renderRestaurantHoldRows(state.restaurantHolds);
  renderRestaurantHoldDetail(state.selectedRestaurantHold);
}

function renderRestaurantHoldRows(items) {
  if (!items.length) return '<tr><td colspan="6"><div class="empty-state"><p>Restoran kaydı bulunamadı.</p></div></td></tr>';
  return items.map(function(item) {
    var isSelected = String(item.hold_id) === String(state.selectedRestaurantHoldId);
    return '<tr class="' + (isSelected ? 'is-selected' : '') + '" data-open-hold="' + escapeHtml(item.hold_id) + '">'
      + '<td><button class="inline-button secondary" data-open-hold="' + escapeHtml(item.hold_id) + '" aria-label="' + escapeHtml(item.hold_id + ' detayini ac') + '">Detay</button></td>'
      + '<td><div class="stack"><strong>' + escapeHtml(item.hold_id) + '</strong><span class="muted">Hotel ' + escapeHtml(String(item.hotel_id)) + '</span></div></td>'
      + '<td><span class="pill ' + holdStatusClass(item.status) + '">' + escapeHtml(holdStatusLabel(item.status)) + '</span></td>'
      + '<td>' + escapeHtml(item.guest_name || '-') + '</td>'
      + '<td><span class="muted">' + escapeHtml(item.date || '-') + ' ' + escapeHtml(item.time || '') + '</span></td>'
      + '<td>' + escapeHtml(String(item.party_size || '-')) + ' kisi</td>'
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
  refs.restaurantHoldDetail.innerHTML = '<div class="module-header"><div>'
    + '<h3>' + escapeHtml(String(item.hold_id || 'Hold')) + '</h3>'
    + '<p class="muted">RESTORAN · Hotel ' + escapeHtml(String(item.hotel_id || '-')) + '</p>'
    + '</div><span class="pill ' + holdStatusClass(item.status) + '">' + escapeHtml(holdStatusLabel(item.status)) + '</span></div>'
    + '<div class="hold-summary-grid mb-md">'
    + formatHoldSummaryDetailCell('Misafir', item.guest_name || '-')
    + formatHoldSummaryDetailCell('Tarih', (item.date || '-') + ' ' + (item.time || ''))
    + formatHoldSummaryDetailCell('Kisi Sayisi', String(item.party_size || '-'))
    + formatHoldSummaryDetailCell('Alan', item.area || '-')
    + formatHoldSummaryDetailCell('Telefon', item.phone || '-')
    + formatHoldSummaryDetailCell('Notlar', item.notes || '-')
    + '</div>'
    + '<div class="dialog-actions hold-detail-actions mt-lg">'
    + '<button class="action-button primary" data-approve-hold="' + escapeHtml(item.hold_id) + '" ' + (String(item.status).toUpperCase() === 'PENDING_APPROVAL' ? '' : 'disabled') + '>Onayla</button>'
    + '<button class="action-button danger" data-reject-hold="' + escapeHtml(item.hold_id) + '">Reddet</button>'
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
    area: form.area ? form.area.value : '',
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
    collectStayDraftFromStep(state.stayWizardStep || 1);
    state.stayWizardStep = (state.stayWizardStep || 1) + 1;
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
