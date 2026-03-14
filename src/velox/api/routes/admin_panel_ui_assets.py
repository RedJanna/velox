"""Static assets for the admin operations panel."""

# ruff: noqa: E501

from velox.api.routes.ui_shared_assets import UI_SHARED_SCRIPT

ADMIN_PANEL_STYLE = """\
*,*::before,*::after{box-sizing:border-box}
:root{
  --bg:#f4efe6;--bg-2:#ebe4d8;--surface:#fffdf8;--surface-2:#f8f4ec;--ink:#102033;--muted:#5d6877;
  --line:rgba(16,32,51,.12);--line-strong:rgba(16,32,51,.2);--accent:#0f766e;--accent-2:#1d8f86;
  --warn:#b45309;--danger:#b42318;--danger-2:#7f1d1d;--ok:#166534;--gold:#bb8a2a;--shadow:0 18px 42px rgba(16,32,51,.08);
  --radius-lg:26px;--radius-md:18px;--radius-sm:12px;--mono:'Cascadia Code','Fira Code',monospace;
  --sans:'Manrope','Segoe UI Variable','Aptos','Segoe UI',system-ui,sans-serif;--serif:'Fraunces','Iowan Old Style','Georgia',serif;
}
html,body{min-height:100%;margin:0;background:
  radial-gradient(circle at top left,rgba(187,138,42,.18),transparent 24%),
  radial-gradient(circle at bottom right,rgba(15,118,110,.12),transparent 22%),
  linear-gradient(180deg,var(--bg) 0%,var(--bg-2) 100%);
  color:var(--ink);font-family:var(--sans)}
body{padding:18px}
button,input,select,textarea{font:inherit}
[hidden]{display:none!important}
.shell{display:grid;grid-template-columns:280px minmax(0,1fr);gap:18px;min-height:calc(100vh - 36px)}
.sidebar{background:linear-gradient(180deg,#11223a 0%,#0a1525 100%);color:#eff6ff;border-radius:30px;padding:24px;display:flex;flex-direction:column;gap:22px;box-shadow:var(--shadow)}
.brand{display:flex;align-items:flex-start;gap:14px}
.brand-mark{width:46px;height:46px;border-radius:16px;background:linear-gradient(135deg,var(--gold),#f2ca72);display:grid;place-items:center;color:#4c3506;font-weight:900;letter-spacing:.06em}
.brand h1{margin:0;font-family:var(--serif);font-size:22px;line-height:1.05}
.brand p{margin:6px 0 0;color:rgba(239,246,255,.72);font-size:13px;line-height:1.45}
.nav{display:flex;flex-direction:column;gap:8px}
.nav button{border:none;background:transparent;color:inherit;padding:12px 14px;border-radius:16px;text-align:left;display:flex;align-items:center;justify-content:space-between;gap:12px;cursor:pointer;transition:.18s background ease,.18s transform ease}
.nav button:hover{background:rgba(255,255,255,.08);transform:translateX(2px)}
.nav button.is-active{background:linear-gradient(135deg,rgba(29,143,134,.24),rgba(187,138,42,.18));box-shadow:inset 0 0 0 1px rgba(255,255,255,.08)}
.nav-label{display:flex;flex-direction:column;gap:3px}
.nav-label strong{font-size:14px}
.nav-label span{font-size:11px;color:rgba(239,246,255,.62)}
.sidebar-card{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.08);border-radius:20px;padding:16px}
.sidebar-card h2{margin:0 0 8px;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:rgba(239,246,255,.62)}
.sidebar-card p,.sidebar-card label,.sidebar-card small{color:rgba(239,246,255,.72)}
.sidebar-select,.sidebar-button,.field input,.field select,.field textarea,.toolbar button,.inline-button{
  border:1px solid var(--line);border-radius:14px;background:var(--surface);color:var(--ink);transition:border-color .18s ease,box-shadow .18s ease
}
.sidebar-select{width:100%;padding:11px 12px;background:rgba(255,255,255,.94)}
.sidebar-select:focus,.field input:focus,.field select:focus,.field textarea:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px rgba(15,118,110,.12)}
.sidebar-actions{display:flex;flex-direction:column;gap:10px}
.sidebar-button,.toolbar button,.inline-button,.action-button{border:none;padding:11px 14px;border-radius:14px;font-weight:700;cursor:pointer}
.sidebar-button.secondary,.toolbar button.secondary,.inline-button.secondary{background:rgba(255,255,255,.08);color:#fff;border:1px solid rgba(255,255,255,.1)}
.sidebar-button.primary,.toolbar button.primary,.inline-button.primary,.action-button.primary{background:linear-gradient(135deg,var(--accent),var(--accent-2));color:#fff}
.sidebar-button.warn,.action-button.warn{background:#fff4db;color:#7c4b06}
.sidebar-button.danger,.action-button.danger{background:#fde7e5;color:var(--danger)}
.workspace{display:flex;flex-direction:column;gap:18px;min-width:0}
.topbar{background:rgba(255,253,248,.9);border-radius:30px;padding:22px 26px;box-shadow:var(--shadow);display:flex;align-items:flex-start;justify-content:space-between;gap:18px;backdrop-filter:blur(18px)}
.topbar h2{margin:0;font-family:var(--serif);font-size:30px;line-height:1}
.topbar p{margin:8px 0 0;color:var(--muted);max-width:760px;line-height:1.55}
.topbar-actions{display:flex;align-items:flex-start;gap:10px}
.topbar-aside{display:flex;flex-wrap:wrap;gap:10px;justify-content:flex-end}
.sidebar-toggle{display:none;border:none;border-radius:12px;padding:10px 14px;background:#13253e;color:#fff;font-weight:800;cursor:pointer}
.sidebar-toggle:focus-visible,.nav button:focus-visible,.sidebar-button:focus-visible,.toolbar button:focus-visible,.inline-button:focus-visible,.action-button:focus-visible{
  outline:2px solid rgba(187,138,42,.9);outline-offset:2px
}
.badge{display:inline-flex;align-items:center;gap:8px;padding:8px 12px;border-radius:999px;font-size:12px;font-weight:800;letter-spacing:.03em}
.badge.info{background:#e8f3f1;color:#115e59}.badge.warn{background:#fff2dd;color:#92400e}.badge.danger{background:#fde7e5;color:#991b1b}.badge.dark{background:#13253e;color:#fff}
.toast{position:fixed;top:24px;right:24px;min-width:260px;max-width:420px;padding:14px 16px;border-radius:18px;box-shadow:var(--shadow);z-index:60;background:#102033;color:#fff;opacity:0;pointer-events:none;transform:translateY(-8px);transition:.18s ease}
.toast.is-visible{opacity:1;pointer-events:auto;transform:none}
.toast.info{background:#102033}.toast.success{background:#115e59}.toast.warn{background:#92400e}.toast.error{background:#991b1b}
.panel{background:rgba(255,253,248,.88);border-radius:30px;padding:22px;box-shadow:var(--shadow);min-width:0}
.auth-grid{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(320px,.9fr);gap:18px}
.auth-card,.overview-card,.queue-card,.module-card{background:var(--surface);border:1px solid var(--line);border-radius:26px;padding:20px;box-shadow:0 10px 28px rgba(16,32,51,.04)}
.auth-card h3,.module-header h3{margin:0;font-family:var(--serif);font-size:26px}
.auth-card p,.module-header p,.empty-state p,.helper{color:var(--muted);line-height:1.55}
.field-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.field{display:flex;flex-direction:column;gap:8px}
.field.full{grid-column:1/-1}
.field label{font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.06em;color:#364152}
.field input,.field select,.field textarea{width:100%;padding:12px 13px;background:var(--surface)}
.field textarea{min-height:260px;resize:vertical;font-family:var(--mono);font-size:12px;line-height:1.55}
.helper-panel{display:flex;flex-direction:column;gap:12px}
.helper-box{padding:14px 16px;border-radius:18px;background:var(--surface-2);border:1px solid var(--line)}
.helper-box strong{display:block;margin-bottom:6px}
.toggle-row{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:14px 16px;border:1px solid var(--line);border-radius:18px;background:var(--surface-2);text-transform:none!important;letter-spacing:0!important}
.toggle-copy{display:flex;flex-direction:column;gap:4px}
.toggle-copy strong{font-size:14px;color:var(--ink)}
.toggle-copy small{font-size:12px;color:var(--muted);line-height:1.45}
.switch{position:relative;display:inline-flex;align-items:center}
.switch input{position:absolute;opacity:0;pointer-events:none}
.switch-track{width:54px;height:32px;border-radius:999px;background:#d7d9dd;display:block;position:relative;transition:.18s background ease}
.switch-thumb{position:absolute;top:4px;left:4px;width:24px;height:24px;border-radius:999px;background:#fff;box-shadow:0 6px 16px rgba(16,32,51,.18);transition:.18s transform ease}
.switch input:checked + .switch-track{background:linear-gradient(135deg,var(--accent),var(--accent-2))}
.switch input:checked + .switch-track .switch-thumb{transform:translateX(22px)}
.session-stack{display:flex;flex-direction:column;gap:14px}
.choice-group{display:flex;flex-wrap:wrap;gap:10px}
.choice-card{cursor:pointer;position:relative}
.choice-card input{position:absolute;opacity:0;pointer-events:none}
.choice-card span{display:inline-flex;align-items:center;justify-content:center;min-height:42px;padding:10px 14px;border-radius:999px;border:1px solid var(--line);background:var(--surface);font-size:13px;font-weight:800;color:var(--muted);transition:.18s ease}
.choice-card input:checked + span{background:linear-gradient(135deg,#102033,#1f3554);border-color:#102033;color:#fff;box-shadow:0 10px 22px rgba(16,32,51,.12)}
.status-strip{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.detail-list{display:flex;flex-direction:column;gap:6px;font-size:13px;color:var(--muted)}
.qr-wrap{display:flex;justify-content:center;padding:10px;border:1px dashed var(--line);border-radius:14px;background:#fff}
.qr-wrap img{width:190px;height:190px;max-width:100%;display:block}
.section-grid{display:grid;gap:18px}
.card-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}
.overview-card h4{margin:0;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.overview-card strong{display:block;margin-top:12px;font-size:34px;font-family:var(--serif);line-height:1}
.overview-card span{display:block;margin-top:8px;color:var(--muted);font-size:13px}
.module-header{display:flex;align-items:flex-start;justify-content:space-between;gap:14px;margin-bottom:16px}
.module-actions{display:flex;flex-wrap:wrap;gap:10px}
.split{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(340px,.8fr);gap:18px}
.toolbar{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:14px}
.toolbar input,.toolbar select{padding:10px 12px;border-radius:14px;border:1px solid var(--line);background:var(--surface)}
.table-shell{border:1px solid var(--line);border-radius:22px;overflow:hidden;background:var(--surface)}
table{width:100%;border-collapse:collapse}
thead th{padding:14px 16px;font-size:12px;letter-spacing:.06em;text-transform:uppercase;background:#f7f2e9;color:#536173;text-align:left;border-bottom:1px solid var(--line)}
tbody td{padding:14px 16px;border-bottom:1px solid var(--line);vertical-align:top;font-size:14px;line-height:1.45}
tbody tr:last-child td{border-bottom:none}
tbody tr:hover{background:#fffcf7}
.pill{display:inline-flex;align-items:center;gap:8px;padding:6px 10px;border-radius:999px;font-size:12px;font-weight:800}
.pill.pending{background:#fff2dd;color:#92400e}.pill.open{background:#e8f3f1;color:#115e59}.pill.closed{background:#e5e7eb;color:#374151}.pill.high{background:#fde7e5;color:#991b1b}.pill.medium{background:#eef4ff;color:#1d4ed8}.pill.low{background:#ecfdf3;color:#166534}
.stack{display:flex;flex-direction:column;gap:6px}.muted{color:var(--muted);font-size:13px}
.mono{font-family:var(--mono);font-size:12px}
.queue-list{display:flex;flex-direction:column;gap:10px}
.queue-item{padding:14px 16px;border-radius:18px;background:var(--surface-2);border:1px solid var(--line)}
.queue-item strong{display:block}
.empty-state{padding:24px;border:1px dashed var(--line-strong);border-radius:22px;background:#fffaf0;text-align:center}
.timeline{display:flex;flex-direction:column;gap:10px}
.message{padding:14px 16px;border-radius:18px;background:var(--surface-2);border:1px solid var(--line)}
.message.user{border-left:4px solid var(--accent)}
.message.assistant{border-left:4px solid var(--gold)}
.message.system{border-left:4px solid #64748b}
.message header{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:8px}
.message header strong{font-size:13px}
.message pre{white-space:pre-wrap;word-break:break-word;margin:0;font-family:var(--sans)}
.audit-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-bottom:12px}
.audit-grid .helper-box{margin:0}
.audit-row{margin-top:8px;padding-top:8px;border-top:1px dashed var(--line-strong);font-size:12px;line-height:1.45}
.dense-form{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.dense-form .field.full{grid-column:1/-1}
.dialog::backdrop{background:rgba(16,32,51,.42)}
.dialog{border:none;border-radius:24px;padding:0;max-width:520px;width:min(92vw,520px);box-shadow:var(--shadow)}
.dialog-card{padding:22px;background:var(--surface)}
.dialog-head h3{margin:0;font-family:var(--serif);font-size:24px}
.dialog-head p{margin:10px 0 0;color:var(--muted)}
.dialog-actions{display:flex;justify-content:flex-end;gap:10px;margin-top:16px}
.status-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.status-block{padding:16px;border-radius:18px;border:1px solid var(--line);background:var(--surface)}
.status-block h4{margin:0 0 8px;font-size:13px}
.status-block pre{margin:0;font-family:var(--mono);font-size:12px;white-space:pre-wrap}
.mt-sm{margin-top:10px}.mt-md{margin-top:14px}.mt-lg{margin-top:16px}
.mb-md{margin-bottom:14px}
.min-w-select{min-width:240px}
.checkbox-field{width:20px;height:20px}
.card-grid-3{grid-template-columns:repeat(3,minmax(0,1fr))}
.chatlab-frame{width:100%;height:calc(100vh - 80px);border:none;border-radius:12px}
.dialog-textarea{min-height:120px}
.inline-flex-center{display:flex;align-items:center;gap:8px}
.pill-closed{background:#e5e7eb;color:#6b7280;font-size:11px}
.action-button-sm{font-size:12px;padding:6px 14px}
@media(max-width:1240px){
  .card-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
  .split,.auth-grid{grid-template-columns:1fr}
}
@media(max-width:980px){
  body{padding:12px}.shell{grid-template-columns:1fr}
  .sidebar{position:fixed;left:12px;top:12px;bottom:12px;z-index:70;width:min(86vw,320px);padding:18px;border-radius:24px;transform:translateX(-112%);transition:transform .2s ease}
  .sidebar.is-open{transform:translateX(0)}
  .sidebar-toggle{display:inline-flex;align-items:center;justify-content:center}
  .topbar-actions{width:100%;justify-content:space-between;align-items:center}
  .topbar-aside{justify-content:flex-start}
  .field-grid,.dense-form,.status-list{grid-template-columns:1fr}
  .topbar{padding:18px 20px;border-radius:24px;flex-direction:column}
  .card-grid{grid-template-columns:1fr}
  .status-strip{grid-template-columns:1fr}
}
"""

ADMIN_PANEL_SCRIPT = UI_SHARED_SCRIPT + """\
const CONFIG = window.ADMIN_PANEL_CONFIG || {};
const API_ROOT = '/api/v1/admin';
const READY_URL = '/api/v1/health/ready';
const HOTEL_KEY = 'velox.admin.hotel';
const CSRF_COOKIE = 'velox_admin_csrf';

const state = {
  me: null,
  bootstrap: null,
  bootstrapPending: null,
  hotels: [],
  selectedHotelId: window.localStorage.getItem(HOTEL_KEY) || '',
  currentView: (window.location.hash || '#dashboard').replace('#', ''),
  dashboard: null,
  conversations: [],
  conversationDetail: null,
  holds: [],
  tickets: [],
  faqs: [],
  faqDetail: null,
  hotelDetail: null,
  restaurantSlots: [],
  systemOverview: null,
  sessionStatus: null,
  sessionPreferences: null,
  refreshPromise: null,
};

const refs = {};

document.addEventListener('DOMContentLoaded', () => {
  bindRefs();
  bindEvents();
  boot();
});

function bindRefs() {
  [
    'sidebar','sidebarToggle',
    'toast','authView','panelView','loginForm','bootstrapForm','bootstrapCard','bootstrapSummary',
    'totpRecovery','totpRecoveryForm','trustedSessionBanner','loginOtpField','rememberDeviceToggle',
    'loginRememberOptions','loginVerificationOptions','loginSessionOptions',
    'otpSetup','otpSecret','otpUri','otpQrImage','otpVerifyForm','otpVerifyHint','currentUser','currentRole','hotelScope','hotelSelect','nav','pageTitle','pageLead',
    'dashboardCards','dashboardQueues','conversationFilters','conversationTableBody','conversationDetail',
    'holdFilters','holdTableBody','ticketFilters','ticketTableBody','hotelProfileSelect','hotelProfileEditor',
    'faqFilters','faqTableBody','faqDetail',
    'notifPhoneTableBody','addNotifPhoneForm',
    'hotelProfileMeta','slotFilters','slotTableBody','slotCreateForm','systemChecks','systemMeta',
    'sessionSummary','sessionPreferencesForm','sessionRememberToggle','sessionPreferenceFields',
    'systemVerificationOptions','systemSessionOptions','sessionOtpField','trustedDevicePanel','forgetDeviceButton',
    'logoutButton','reloadButton','decisionDialog','decisionForm','decisionTitle','decisionLead','decisionReason',
    'decisionHoldId','decisionMode'
  ].forEach(id => refs[id] = document.getElementById(id));
  // Bootstrap hotel select uses kebab-case id in HTML; map it to the existing JS key.
  refs.bootstrapHotels = document.getElementById('bootstrap-hotel');
}

function bindEvents() {
  refs.sidebarToggle?.addEventListener('click', toggleSidebar);
  refs.loginForm.addEventListener('submit', onLogin);
  refs.bootstrapForm.addEventListener('submit', onBootstrap);
  refs.totpRecoveryForm.addEventListener('submit', onTotpRecovery);
  refs.otpVerifyForm.addEventListener('submit', onBootstrapVerify);
  refs.rememberDeviceToggle.addEventListener('change', toggleLoginRememberOptions);
  refs.hotelSelect.addEventListener('change', onHotelScopeChange);
  refs.hotelProfileSelect.addEventListener('change', loadHotelProfileSection);
  refs.slotCreateForm.addEventListener('submit', onCreateSlot);
  refs.sessionPreferencesForm.addEventListener('submit', onSessionPreferencesSave);
  refs.sessionRememberToggle.addEventListener('change', toggleSessionPreferenceState);
  refs.forgetDeviceButton.addEventListener('click', forgetTrustedDevice);
  refs.reloadButton.addEventListener('click', reloadConfig);
  refs.logoutButton.addEventListener('click', logout);
  refs.conversationFilters.addEventListener('submit', event => {
    event.preventDefault();
    loadConversations();
  });
  refs.holdFilters.addEventListener('submit', event => {
    event.preventDefault();
    loadHolds();
  });
  refs.ticketFilters.addEventListener('submit', event => {
    event.preventDefault();
    loadTickets();
  });
  refs.faqFilters.addEventListener('submit', event => {
    event.preventDefault();
    loadFaqs();
  });
  refs.addNotifPhoneForm.addEventListener('submit', onAddNotifPhone);
  refs.decisionForm.addEventListener('submit', onDecisionSubmit);
  document.querySelectorAll('[data-nav]').forEach(button => {
    const label = button.querySelector('.nav-label strong')?.textContent || 'Navigasyon';
    button.setAttribute('aria-label', label.trim());
    button.addEventListener('click', () => {
      setView(button.dataset.nav);
      closeSidebar();
    });
  });
  document.getElementById('saveHotelProfile').addEventListener('click', saveHotelProfile);
  document.getElementById('loadSlotsButton').addEventListener('click', event => {
    event.preventDefault();
    loadRestaurantSlots();
  });
  document.getElementById('closeDecision').addEventListener('click', () => refs.decisionDialog.close());
  window.addEventListener('message', async event => {
    if (event.data && event.data.type === 'chatlab:auth-required') {
      // Re-obtain a fresh token and send it to the iframe
      await loadChatLab();
    }
  });
  window.addEventListener('resize', closeSidebar);
  bindDelegatedEvents();
}

function isMobileLayout() {
  return window.matchMedia('(max-width: 980px)').matches;
}

function closeSidebar() {
  if (!refs.sidebar || !refs.sidebarToggle) return;
  refs.sidebar.classList.remove('is-open');
  refs.sidebarToggle.setAttribute('aria-expanded', 'false');
}

function toggleSidebar() {
  if (!refs.sidebar || !refs.sidebarToggle || !isMobileLayout()) return;
  refs.sidebar.classList.toggle('is-open');
  refs.sidebarToggle.setAttribute('aria-expanded', refs.sidebar.classList.contains('is-open') ? 'true' : 'false');
}

function bindDelegatedEvents() {
  // Single delegated click handler on panelView covers all dynamic table actions.
  // This avoids re-binding listeners every time a table is re-rendered.
  refs.panelView.addEventListener('click', async event => {
    const target = event.target.closest('[data-open-conversation],[data-approve-hold],[data-reject-hold],[data-save-ticket]');
    if (!target) return;

    // Conversation detail
    if (target.dataset.openConversation) {
      loadConversationDetail(target.dataset.openConversation);
      return;
    }

    // Hold approve
    if (target.dataset.approveHold) {
      try {
        await apiFetch(`/holds/${target.dataset.approveHold}/approve`, {method: 'POST', body: {notes: ''}});
        notify('Hold onaylandi.', 'success');
        loadHolds();
        loadDashboard();
      } catch (error) {
        notify(error.message, 'error');
      }
      return;
    }

    // Hold reject
    if (target.dataset.rejectHold) {
      refs.decisionMode.value = 'reject';
      refs.decisionHoldId.value = target.dataset.rejectHold;
      refs.decisionTitle.textContent = 'Hold reddet';
      refs.decisionLead.textContent = 'Bu islem misafir akisina olumsuz yansir. Nedeni acik yazin.';
      refs.decisionReason.value = '';
      refs.decisionDialog.showModal();
      return;
    }

    // Ticket save
    if (target.dataset.saveTicket) {
      const ticketId = target.dataset.saveTicket;
      const statusField = document.querySelector(`[data-ticket-status="${ticketId}"]`);
      try {
        await apiFetch(`/tickets/${ticketId}`, {method: 'PUT', body: {status: statusField.value}});
        notify('Ticket guncellendi.', 'success');
        loadTickets();
        loadDashboard();
      } catch (error) {
        notify(error.message, 'error');
      }
    }
  });
}

async function boot() {
  await Promise.all([loadBootstrapStatus(), loadSessionStatus()]);
  try {
    await hydrateSession();
    return;
  } catch (_error) {
    showAuth();
  }
}

async function loadBootstrapStatus() {
  state.bootstrap = await apiFetch('/bootstrap/status', {auth: false});
  renderBootstrapState();
}

async function loadSessionStatus() {
  try {
    state.sessionStatus = await apiFetch('/session/status', {auth: false});
  } catch (_error) {
    state.sessionStatus = null;
  }
  renderLoginSessionState();
}

function renderBootstrapState() {
  const info = state.bootstrap || {};
  const hotelOptions = (info.hotel_options || []).map(item => (
    `<option value="${escapeHtml(item.hotel_id)}">${escapeHtml(item.hotel_id)} - ${escapeHtml(item.name)}</option>`
  )).join('');
  refs.bootstrapHotels.innerHTML = hotelOptions || '<option value="">Hotel yok</option>';

  if (!info.bootstrap_required) {
    refs.bootstrapForm.hidden = true;
    refs.totpRecovery.hidden = false;
    refs.otpVerifyForm.hidden = true;
    refs.otpVerifyHint.hidden = true;
    refs.bootstrapSummary.innerHTML = `
      <div class="helper-box">
        <strong>Kurulum tamam</strong>
        <p>Panel girişi aktif. Google Authenticator kodunuz ile oturum açabilirsiniz.</p>
      </div>
      <div class="helper-box">
        <strong>Alan adı</strong>
        <p>${escapeHtml(info.panel_url || CONFIG.panel_url || '/admin')}</p>
      </div>
    `;
    return;
  }

  refs.bootstrapForm.hidden = false;
  refs.totpRecovery.hidden = true;
  const accessMode = info.local_bootstrap_allowed
    ? 'Bu cihazdan localhost bootstrap açık.'
    : (info.token_bootstrap_enabled ? 'Bootstrap token gerekli.' : 'Bootstrap için localhost erişimi veya ENV token gerekli.');

  refs.bootstrapSummary.innerHTML = `
    <div class="helper-box">
      <strong>İlk yönetici hesabı gerekli</strong>
      <p>Veritabanında admin kullanıcısı yok. İlk hesap oluşturulduktan sonra panel doğrudan 2FA ile çalışacak.</p>
    </div>
    <div class="helper-box">
      <strong>Erişim modu</strong>
      <p>${escapeHtml(accessMode)}</p>
    </div>
  `;
}

function renderLoginSessionState() {
  const status = state.sessionStatus || {};
  const verificationOptions = status.verification_options || [];
  const sessionOptions = status.session_options || [];
  const rememberChecked = refs.rememberDeviceToggle.checked || Boolean(status.has_trusted_device);

  refs.rememberDeviceToggle.checked = rememberChecked;
  renderChoiceGroup(
    refs.loginVerificationOptions,
    'verification_preset',
    verificationOptions,
    status.verification_preset || '24_hours',
  );
  renderChoiceGroup(
    refs.loginSessionOptions,
    'session_preset',
    sessionOptions,
    status.session_preset || '8_hours',
  );
  toggleLoginRememberOptions();

  if (!status.has_trusted_device) {
    refs.trustedSessionBanner.hidden = true;
    setOtpMode({skipAllowed: false});
    return;
  }

  refs.trustedSessionBanner.hidden = false;
  refs.trustedSessionBanner.innerHTML = `
    <div class="helper-box">
      <strong>${escapeHtml(status.user_label || 'Bu cihaz')}</strong>
      <p>${escapeHtml(status.device_label || 'Tarayici cihazi')} icin hizli giris durumu gorunur.</p>
    </div>
    <div class="status-strip">
      <div class="helper-box">
        <strong>OTP tekrar suresi</strong>
        <p>${status.verification_active ? `Aktif · ${escapeHtml(formatDate(status.verification_expires_at))}` : 'Suresi doldu'}</p>
      </div>
      <div class="helper-box">
        <strong>Oturum hatirlama</strong>
        <p>${status.session_active ? `Aktif · ${escapeHtml(formatDate(status.session_expires_at))}` : 'Aktif degil'}</p>
      </div>
    </div>
    ${status.verification_active ? '<button id="loginForceOtpButton" class="inline-button secondary" type="button">Kodu yine de kullan</button>' : ''}
  `;

  setOtpMode({skipAllowed: Boolean(status.verification_active)});
  const forceOtpButton = document.getElementById('loginForceOtpButton');
  if (forceOtpButton) {
    forceOtpButton.addEventListener('click', () => setOtpMode({skipAllowed: false, forced: true}));
  }
}

function toggleLoginRememberOptions() {
  refs.loginRememberOptions.hidden = !refs.rememberDeviceToggle.checked;
}

function setOtpMode({skipAllowed, forced = false}) {
  const otpInput = refs.loginForm.otp_code;
  const shouldHide = skipAllowed && !forced;
  refs.loginOtpField.hidden = shouldHide;
  otpInput.required = !shouldHide;
  if (shouldHide) {
    otpInput.value = '';
  }
}

function renderChoiceGroup(container, name, options, selectedValue) {
  container.innerHTML = (options || []).map(option => `
    <label class="choice-card">
      <input type="radio" name="${escapeHtml(name)}" value="${escapeHtml(option.value)}" ${option.value === selectedValue ? 'checked' : ''}>
      <span>${escapeHtml(option.label)}</span>
    </label>
  `).join('');
}

async function onLogin(event) {
  event.preventDefault();
  const payload = formToJson(refs.loginForm);
  payload.remember_device = refs.rememberDeviceToggle.checked;
  payload.verification_preset = getSelectedChoice(refs.loginForm, 'verification_preset', state.sessionStatus?.verification_preset || '24_hours');
  payload.session_preset = getSelectedChoice(refs.loginForm, 'session_preset', state.sessionStatus?.session_preset || '8_hours');
  if (!payload.otp_code) {
    delete payload.otp_code;
  }
  try {
    const response = await apiFetch('/login', {method: 'POST', body: payload, auth: false});
    notify(response.authentication_mode === 'trusted_device' ? 'Bu cihaz icin OTP adimi atlandi.' : 'Oturum acildi.', 'success');
    await loadSessionStatus();
    await hydrateSession();
  } catch (error) {
    notify(error.message, 'error');
  }
}

async function onBootstrap(event) {
  event.preventDefault();
  const payload = formToJson(refs.bootstrapForm);
  payload.hotel_id = Number(payload.hotel_id);
  if (new TextEncoder().encode(String(payload.password || '')).length > 72) {
    notify('Şifre en fazla 72 byte olabilir.', 'warn');
    return;
  }
  try {
    const response = await apiFetch('/bootstrap', {method: 'POST', body: payload, auth: false});
    state.bootstrapPending = {
      username: payload.username,
      password: payload.password,
    };
    refs.otpSetup.hidden = false;
    refs.otpVerifyForm.hidden = false;
    refs.otpVerifyHint.hidden = false;
    refs.otpQrImage.src = response.otpauth_qr_svg_data_uri;
    refs.otpSecret.textContent = response.totp_secret;
    refs.otpUri.textContent = response.otpauth_uri;
    refs.loginForm.username.value = response.username;
    refs.loginForm.password.value = payload.password;
    notify('İlk admin hesabı oluşturuldu. QR okutun ve kodu doğrulayın.', 'success');
  } catch (error) {
    notify(error.message, 'error');
  }
}

async function onTotpRecovery(event) {
  event.preventDefault();
  const payload = formToJson(refs.totpRecoveryForm);
  const nextPassword = String(payload.new_password || '');
  if (nextPassword && new TextEncoder().encode(nextPassword).length > 72) {
    notify('Şifre en fazla 72 byte olabilir.', 'warn');
    return;
  }
  try {
    const response = await apiFetch('/bootstrap/recover-totp', {method: 'POST', body: payload, auth: false});
    refs.otpSetup.hidden = false;
    refs.otpVerifyForm.hidden = true;
    refs.otpVerifyHint.hidden = true;
    refs.otpQrImage.src = response.otpauth_qr_svg_data_uri;
    refs.otpSecret.textContent = response.totp_secret;
    refs.otpUri.textContent = response.otpauth_uri;
    refs.loginForm.username.value = response.username;
    if (nextPassword) {
      refs.loginForm.password.value = nextPassword;
      notify('2FA yenilendi. Yeni şifre ve Authenticator kodu ile giriş yapın.', 'success');
    } else {
      notify('2FA yenilendi. Mevcut şifreniz ve yeni Authenticator kodu ile giriş yapın.', 'success');
    }
  } catch (error) {
    notify(error.message, 'error');
  }
}

async function onBootstrapVerify(event) {
  event.preventDefault();
  if (!state.bootstrapPending) {
    notify('Önce ilk admin hesabını oluşturun.', 'warn');
    return;
  }
  const payload = formToJson(refs.otpVerifyForm);
  const loginPayload = {
    username: state.bootstrapPending.username,
    password: state.bootstrapPending.password,
    otp_code: payload.otp_code,
  };
  try {
    const response = await apiFetch('/login', {method: 'POST', body: loginPayload, auth: false});
    state.bootstrapPending = null;
    notify('Kurulum dogrulandi, oturum acildi.', 'success');
    await loadSessionStatus();
    await hydrateSession();
  } catch (error) {
    notify(error.message, 'error');
  }
}

async function hydrateSession() {
  state.me = await apiFetch('/me');
  state.hotels = await apiFetch('/hotels');
  const preferredHotel = resolvePreferredHotel();
  state.selectedHotelId = preferredHotel ? String(preferredHotel) : '';
  window.localStorage.setItem(HOTEL_KEY, state.selectedHotelId);
  populateHotelSelectors();
  showPanel();
  await Promise.all([loadDashboard(), loadSystemOverview(), loadSessionPreferences()]);
  setView(state.currentView || 'dashboard');
}

function resolvePreferredHotel() {
  if (state.me?.role !== 'ADMIN') {
    return state.me?.hotel_id || '';
  }
  if (state.selectedHotelId && state.hotels.some(item => String(item.hotel_id) === String(state.selectedHotelId))) {
    return state.selectedHotelId;
  }
  return state.hotels[0]?.hotel_id || '';
}

function populateHotelSelectors() {
  const options = state.hotels.map(item => (
    `<option value="${escapeHtml(item.hotel_id)}">${escapeHtml(item.hotel_id)} - ${escapeHtml(item.name_en || item.name_tr || 'Hotel')}</option>`
  )).join('');
  refs.hotelSelect.innerHTML = options;
  refs.hotelProfileSelect.innerHTML = options;
  if (state.selectedHotelId) {
    refs.hotelSelect.value = state.selectedHotelId;
    refs.hotelProfileSelect.value = state.selectedHotelId;
  }
  refs.hotelSelect.disabled = state.me?.role !== 'ADMIN';
}

function showAuth() {
  refs.authView.hidden = false;
  refs.panelView.hidden = true;
  refs.currentUser.textContent = 'Misafir değil, operasyon';
  refs.currentRole.textContent = 'Panel girişi bekleniyor';
  refs.hotelScope.textContent = CONFIG.public_host || 'nexlumeai.com';
  renderLoginSessionState();
}

function showPanel() {
  refs.authView.hidden = true;
  refs.panelView.hidden = false;
  refs.currentUser.textContent = state.me?.display_name || state.me?.username || '-';
  refs.currentRole.textContent = state.me?.role || '-';
  refs.hotelScope.textContent = state.selectedHotelId || '-';
}

function setView(view) {
  state.currentView = view;
  window.location.hash = view;
  document.querySelectorAll('[data-view]').forEach(section => {
    section.hidden = section.dataset.view !== view;
  });
  document.querySelectorAll('[data-nav]').forEach(button => {
    button.classList.toggle('is-active', button.dataset.nav === view);
  });

  const meta = {
    dashboard: ['Genel Bakis', 'Aktif konusmalar, bekleyen onaylar ve acik talepleri tek ekranda gorun.'],
    conversations: ['Konusmalar', 'Misafir mesajlarini, durumlarini ve gecmisini inceleyin.'],
    holds: ['Onay Bekleyenler', 'Konaklama, restoran ve transfer taleplerini onaylayin veya reddedin.'],
    tickets: ['Destek Talepleri', 'Ekibe aktarilan gorevleri oncelik ve duruma gore takip edin.'],
    hotels: ['Otel Bilgileri', 'Otel profilini duzenleyin ve degisiklikleri sisteme uygulatin.'],
    faq: ['Sik Sorulan Sorular', 'Hazir yanitlari yonetin, uygunsuz icerigi hizlica kaldirin.'],
    restaurant: ['Restoran Yonetimi', 'Tarih ve saat bazli masa kapasitelerini ayarlayin.'],
    notifications: ['Bildirim Ayarlari', 'Rezervasyon onaylari icin WhatsApp bildirim numaralarini yonetin.'],
    system: ['Sistem Durumu', 'Sunucu sagligi, alan adi ve guvenlik ayarlarini kontrol edin.'],
    chatlab: ['Test Paneli', 'Yapay zekayi canli test edin, puanlayin ve raporlayin.'],
  }[view] || ['Admin Panel', 'Yonetim merkezi'];

  refs.pageTitle.textContent = meta[0];
  refs.pageLead.textContent = meta[1];

  if (view === 'dashboard') loadDashboard();
  if (view === 'conversations') loadConversations();
  if (view === 'holds') loadHolds();
  if (view === 'tickets') loadTickets();
  if (view === 'hotels') loadHotelProfileSection();
  if (view === 'faq') loadFaqs();
  if (view === 'restaurant') loadRestaurantSlots();
  if (view === 'notifications') loadNotifPhones();
  if (view === 'system') loadSystemOverview();
  if (view === 'chatlab') loadChatLab();
}

function onHotelScopeChange() {
  state.selectedHotelId = refs.hotelSelect.value;
  refs.hotelProfileSelect.value = refs.hotelSelect.value;
  window.localStorage.setItem(HOTEL_KEY, state.selectedHotelId);
  refs.hotelScope.textContent = state.selectedHotelId || '-';
  setView(state.currentView);
}

async function loadChatLab() {
  const frame = document.getElementById('chatlab-frame');
  if (!frame) return;
  // Obtain a fresh access token and pass it to the iframe via postMessage
  // because iframe fetch may not send httpOnly cookies reliably.
  let tokenPayload;
  try {
    tokenPayload = await apiFetch('/session/refresh', {method: 'POST', body: {}, auth: false, allowRefresh: false, logoutOn401: false});
  } catch (_e) {
    try {
      tokenPayload = await apiFetch('/me', {allowRefresh: true});
    } catch (_e2) { return; }
  }
  const token = tokenPayload?.access_token || '';
  const needsLoad = !frame.src || frame.src === 'about:blank' || frame.contentWindow?.location?.href === 'about:blank';
  if (needsLoad) {
    frame.src = '/admin/chat-lab';
  }
  // Send token to iframe once it finishes loading
  const sendToken = () => {
    try { frame.contentWindow.postMessage({type: 'chatlab:token', token}, window.location.origin); } catch(_e) {}
  };
  if (needsLoad) {
    frame.addEventListener('load', sendToken, {once: true});
  } else {
    sendToken();
  }
}

async function loadDashboard() {
  const query = state.selectedHotelId ? `?hotel_id=${encodeURIComponent(state.selectedHotelId)}` : '';
  state.dashboard = await apiFetch(`/dashboard/overview${query}`);
  renderDashboard();
}

function renderDashboard() {
  if (!state.dashboard) return;
  const cards = [
    ['Aktif Konusma', state.dashboard.cards.conversations_active, 'Canli takip gereken oturumlar'],
    ['Bekleyen Hold', state.dashboard.cards.pending_holds, 'Onay akisini tikayan kayitlar'],
    ['Acik Ticket', state.dashboard.cards.open_tickets, 'Ops, sales ve chef kuyruklari'],
    ['Yuksek Oncelik', state.dashboard.cards.high_priority_tickets, 'Gecikirse risk artiran olaylar'],
  ];
  refs.dashboardCards.innerHTML = cards.map(item => `
    <article class="overview-card">
      <h4>${escapeHtml(item[0])}</h4>
      <strong>${escapeHtml(item[1] ?? 0)}</strong>
      <span>${escapeHtml(item[2])}</span>
    </article>
  `).join('');

  refs.dashboardQueues.innerHTML = `
    <div class="queue-card">
      <div class="module-header"><div><h3>Son Konusmalar</h3><p>Risk ve intent baglamiyla son aktivite.</p></div></div>
      ${renderQueue(state.dashboard.recent_conversations, item => `
        <div class="queue-item">
          <strong>${escapeHtml(item.phone_display || 'Maskeli kullanici')}</strong>
          <span class="muted">${escapeHtml(item.current_state || '-')} · ${escapeHtml(item.current_intent || '-')}</span>
          <div class="muted">${formatDate(item.last_message_at)}</div>
        </div>
      `, 'Konuşma yok')}
    </div>
    <div class="queue-card">
      <div class="module-header"><div><h3>Bekleyen Holdlar</h3><p>Onay bekleyen kararlar burada yoğunlaşır.</p></div></div>
      ${renderQueue(state.dashboard.recent_holds, item => `
        <div class="queue-item">
          <strong>${escapeHtml(item.hold_id)}</strong>
          <span class="muted">${escapeHtml(item.hold_type)} · ${escapeHtml(item.status)}</span>
          <div class="muted">${formatDate(item.created_at)}</div>
        </div>
      `, 'Bekleyen hold yok')}
    </div>
    <div class="queue-card">
      <div class="module-header"><div><h3>Açık Ticketlar</h3><p>Handoff kuyruğunda sahiplik ve öncelik takibi.</p></div></div>
      ${renderQueue(state.dashboard.recent_tickets, item => `
        <div class="queue-item">
          <strong>${escapeHtml(item.ticket_id)}</strong>
          <span class="muted">${escapeHtml(item.reason)} · ${escapeHtml(item.priority)}</span>
          <div class="muted">${formatDate(item.created_at)}</div>
        </div>
      `, 'Açık ticket yok')}
    </div>
  `;
}

function renderQueue(items, renderItem, emptyLabel) {
  if (!items || !items.length) {
    return `<div class="empty-state"><p>${escapeHtml(emptyLabel)}</p></div>`;
  }
  return `<div class="queue-list">${items.map(renderItem).join('')}</div>`;
}

async function loadConversations() {
  const form = new FormData(refs.conversationFilters);
  const params = new URLSearchParams();
  if (state.me?.role === 'ADMIN' && state.selectedHotelId) params.set('hotel_id', state.selectedHotelId);
  if (form.get('status')) params.set('status', String(form.get('status')));
  if (form.get('date_from')) params.set('date_from', String(form.get('date_from')));
  if (form.get('date_to')) params.set('date_to', String(form.get('date_to')));
  const response = await apiFetch(`/conversations?${params.toString()}`);
  state.conversations = response.items || [];
  refs.conversationTableBody.innerHTML = renderConversationRows(state.conversations);
  if (state.conversations.length && !state.conversationDetail) {
    loadConversationDetail(state.conversations[0].id);
  } else if (!state.conversations.length) {
    refs.conversationDetail.innerHTML = '<div class="empty-state"><p>Seçili konuşma yok.</p></div>';
  }
}

function renderConversationRows(items) {
  if (!items.length) {
    return `<tr><td colspan="6"><div class="empty-state"><p>Filtreye uygun konuşma bulunamadı.</p></div></td></tr>`;
  }
  return items.map(item => `
    <tr>
      <td><div class="stack"><strong>${escapeHtml(item.phone_display || 'Maskeli kullanici')}</strong><span class="muted mono">${escapeHtml(item.id)}</span></div></td>
      <td><span class="pill open">${escapeHtml(item.current_state || '-')}</span></td>
      <td>${escapeHtml(resolveConversationIntent(item, []))}</td>
      <td>${escapeHtml((item.risk_flags || []).join(', ') || 'Yok')}</td>
      <td>${escapeHtml(item.message_count || 0)}</td>
      <td><button class="inline-button primary" data-open-conversation="${escapeHtml(item.id)}">Detay</button></td>
    </tr>
  `).join('');
}

// Event delegation: conversation table clicks handled by container listener (see bindDelegatedEvents)

async function loadConversationDetail(conversationId) {
  const response = await apiFetch(`/conversations/${conversationId}`);
  state.conversationDetail = response;
  const resolvedIntent = resolveConversationIntent(response.conversation, response.messages || []);
  const resolvedState = resolveConversationState(response.conversation, response.messages || []);
  const audit = extractLatestUserAudit(response.messages || []);
  refs.conversationDetail.innerHTML = `
    <div class="module-header">
      <div>
        <h3>Konuşma Detayı</h3>
        <p>${escapeHtml(response.conversation.phone_display || 'Maskeli kullanici')} · ${escapeHtml(resolvedState)}</p>
      </div>
      <div class="inline-flex-center">
        <div class="badge dark">${escapeHtml(resolvedIntent)}</div>
        ${response.conversation.is_active ? `<button class="action-button danger action-button-sm" data-reset-conversation="${escapeHtml(String(response.conversation.id))}">Sifirla</button>` : '<span class="pill pill-closed">Kapali</span>'}
      </div>
    </div>
    ${renderUserAuditSection(audit)}
    <div class="timeline">
      ${(response.messages || []).map(message => `
        <article class="message ${escapeHtml(message.role || 'system')}">
          <header><strong>${escapeHtml(message.role || 'system')}</strong><span class="muted">${formatDate(message.created_at)}</span></header>
          <pre>${escapeHtml(message.content || '')}</pre>
          ${renderMessageAuditRow(message)}
        </article>
      `).join('')}
    </div>
  `;
  const resetBtn = refs.conversationDetail.querySelector('[data-reset-conversation]');
  if (resetBtn) {
    resetBtn.addEventListener('click', async () => {
      if (!confirm('Bu konuşmayı sıfırlamak istediğinize emin misiniz? Kullanıcının bir sonraki mesajı yeni bir konuşma başlatacaktır.')) return;
      try {
        await apiFetch(`/conversations/${resetBtn.dataset.resetConversation}/reset`, {method: 'POST'});
        notify('Konuşma sıfırlandı.', 'success');
        loadConversations();
      } catch (error) {
        notify(error.message, 'error');
      }
    });
  }
}

async function loadHolds() {
  const form = new FormData(refs.holdFilters);
  const params = new URLSearchParams();
  if (state.me?.role === 'ADMIN' && state.selectedHotelId) params.set('hotel_id', state.selectedHotelId);
  if (form.get('hold_type')) params.set('hold_type', String(form.get('hold_type')));
  if (form.get('status')) params.set('status', String(form.get('status')));
  const response = await apiFetch(`/holds?${params.toString()}`);
  state.holds = response.items || [];
  refs.holdTableBody.innerHTML = renderHoldRows(state.holds);
}

function renderHoldRows(items) {
  if (!items.length) {
    return `<tr><td colspan="6"><div class="empty-state"><p>Onay akışında kayıt yok.</p></div></td></tr>`;
  }
  return items.map(item => `
    <tr>
      <td><div class="stack"><strong>${escapeHtml(item.hold_id)}</strong><span class="muted">${escapeHtml(item.type)}</span></div></td>
      <td>${escapeHtml(item.hotel_id)}</td>
      <td><span class="pill pending">${escapeHtml(item.status)}</span></td>
      <td><pre class="mono">${escapeHtml(JSON.stringify(item.draft_json || {}, null, 2))}</pre></td>
      <td>${formatDate(item.created_at)}</td>
      <td>
        <div class="stack">
          <button class="action-button primary" data-approve-hold="${escapeHtml(item.hold_id)}">Onayla</button>
          <button class="action-button danger" data-reject-hold="${escapeHtml(item.hold_id)}">Reddet</button>
        </div>
      </td>
    </tr>
  `).join('');
}

// Hold actions handled by delegated event listener (see bindDelegatedEvents)

async function onDecisionSubmit(event) {
  event.preventDefault();
  const holdId = refs.decisionHoldId.value;
  const reason = refs.decisionReason.value.trim();
  if (!reason) {
    notify('Red gerekçesi zorunlu.', 'warn');
    return;
  }
  try {
    await apiFetch(`/holds/${holdId}/reject`, {method: 'POST', body: {reason}});
    refs.decisionDialog.close();
    notify('Hold reddedildi.', 'success');
    loadHolds();
    loadDashboard();
  } catch (error) {
    notify(error.message, 'error');
  }
}

async function loadTickets() {
  const form = new FormData(refs.ticketFilters);
  const params = new URLSearchParams();
  if (state.me?.role === 'ADMIN' && state.selectedHotelId) params.set('hotel_id', state.selectedHotelId);
  if (form.get('status')) params.set('status', String(form.get('status')));
  if (form.get('priority')) params.set('priority', String(form.get('priority')));
  const response = await apiFetch(`/tickets?${params.toString()}`);
  state.tickets = response.items || [];
  refs.ticketTableBody.innerHTML = renderTicketRows(state.tickets);
}

function renderTicketRows(items) {
  if (!items.length) {
    return `<tr><td colspan="7"><div class="empty-state"><p>Açık ticket bulunamadı.</p></div></td></tr>`;
  }
  return items.map(item => `
    <tr>
      <td><div class="stack"><strong>${escapeHtml(item.ticket_id)}</strong><span class="muted">${escapeHtml(item.reason)}</span></div></td>
      <td><span class="pill ${escapeHtml((item.priority || 'low').toLowerCase())}">${escapeHtml(item.priority)}</span></td>
      <td>${escapeHtml(item.status)}</td>
      <td>${escapeHtml(item.assigned_to_role || '-')}</td>
      <td>${formatDate(item.created_at)}</td>
      <td><div class="muted">${escapeHtml(item.transcript_summary || '').slice(0, 180)}</div></td>
      <td>
        <div class="stack">
          <select data-ticket-status="${escapeHtml(item.ticket_id)}">
            ${['OPEN','IN_PROGRESS','RESOLVED','CLOSED'].map(status => `<option value="${status}" ${item.status === status ? 'selected' : ''}>${status}</option>`).join('')}
          </select>
          <button class="action-button primary" data-save-ticket="${escapeHtml(item.ticket_id)}">Kaydet</button>
        </div>
      </td>
    </tr>
  `).join('');
}

// Ticket actions handled by delegated event listener (see bindDelegatedEvents)

async function loadFaqs() {
  const hotelId = state.selectedHotelId;
  if (!hotelId) {
    refs.faqTableBody.innerHTML = '<tr><td colspan="5"><div class="empty-state"><p>Hotel seçin.</p></div></td></tr>';
    refs.faqDetail.innerHTML = '<div class="empty-state"><p>Detay için listeden bir FAQ kaydı seçin.</p></div>';
    state.faqs = [];
    state.faqDetail = null;
    return;
  }
  const form = new FormData(refs.faqFilters);
  const params = new URLSearchParams();
  if (form.get('status')) params.set('status', String(form.get('status')));
  if (form.get('q')) params.set('q', String(form.get('q')));
  const response = await apiFetch(`/hotels/${hotelId}/faq?${params.toString()}`);
  state.faqs = response.items || [];
  refs.faqTableBody.innerHTML = renderFaqRows(state.faqs);
  bindFaqActions();
  if (!state.faqDetail || !state.faqs.find(item => item.faq_id === state.faqDetail.faq_id)) {
    state.faqDetail = null;
    refs.faqDetail.innerHTML = '<div class="empty-state"><p>Detay için listeden bir FAQ kaydı seçin.</p></div>';
  } else {
    renderFaqDetail(state.faqDetail);
  }
}

function renderFaqRows(items) {
  if (!items.length) {
    return '<tr><td colspan="5"><div class="empty-state"><p>Filtreye uyan FAQ kaydı bulunamadı.</p></div></td></tr>';
  }
  return items.map(item => {
    const pillClass = item.status === 'ACTIVE' ? 'open' : (item.status === 'REMOVED' ? 'closed' : 'pending');
    const questionPreview = `${item.question?.tr || '-'} / ${item.question?.en || '-'}`;
    const answerPreview = `${item.answer?.tr || '-'} / ${item.answer?.en || '-'}`;
    return `
      <tr>
        <td><strong>${escapeHtml(item.topic || '-')}</strong></td>
        <td><span class="pill ${pillClass}">${escapeHtml(item.status || '-')}</span></td>
        <td><span class="muted">${escapeHtml(questionPreview).slice(0, 180)}</span></td>
        <td><span class="muted">${escapeHtml(answerPreview).slice(0, 180)}</span></td>
        <td>
          <div class="stack">
            <button class="action-button primary" data-faq-open="${escapeHtml(item.faq_id)}">Detay</button>
            ${item.status === 'ACTIVE'
              ? `<button class="action-button warn" data-faq-status="${escapeHtml(item.faq_id)}" data-next-status="PAUSED">Pasife Al</button>`
              : ''}
            ${(item.status === 'PAUSED' || item.status === 'DRAFT')
              ? `<button class="action-button primary" data-faq-status="${escapeHtml(item.faq_id)}" data-next-status="ACTIVE">Aktif Et</button>`
              : ''}
            ${item.status !== 'REMOVED'
              ? `<button class="action-button danger" data-faq-remove="${escapeHtml(item.faq_id)}">Kaldir</button>`
              : ''}
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function bindFaqActions() {
  document.querySelectorAll('[data-faq-open]').forEach(button => {
    button.addEventListener('click', () => {
      const item = state.faqs.find(entry => entry.faq_id === button.dataset.faqOpen);
      if (!item) return;
      state.faqDetail = item;
      renderFaqDetail(item);
    });
  });

  document.querySelectorAll('[data-faq-status]').forEach(button => {
    button.addEventListener('click', async () => {
      const faqId = button.dataset.faqStatus;
      const nextStatus = button.dataset.nextStatus;
      try {
        await apiFetch(`/hotels/${state.selectedHotelId}/faq/${faqId}/status`, {
          method: 'POST',
          body: {status: nextStatus},
        });
        notify(`FAQ durumu ${nextStatus} olarak guncellendi.`, 'success');
        await loadFaqs();
      } catch (error) {
        notify(error.message, 'error');
      }
    });
  });

  document.querySelectorAll('[data-faq-remove]').forEach(button => {
    button.addEventListener('click', async () => {
      const faqId = button.dataset.faqRemove;
      const reason = window.prompt('Kaldırma gerekçesi yazın:');
      if (!reason || !reason.trim()) {
        notify('Kaldırma gerekçesi zorunlu.', 'warn');
        return;
      }
      try {
        await apiFetch(`/hotels/${state.selectedHotelId}/faq/${faqId}`, {
          method: 'DELETE',
          body: {reason: reason.trim()},
        });
        notify('FAQ kaydi aninda kaldirildi.', 'success');
        await loadFaqs();
      } catch (error) {
        notify(error.message, 'error');
      }
    });
  });
}

function renderFaqDetail(item) {
  if (!item) {
    refs.faqDetail.innerHTML = '<div class="empty-state"><p>Detay için listeden bir FAQ kaydı seçin.</p></div>';
    return;
  }
  const variants = item.question_variants || {};
  refs.faqDetail.innerHTML = `
    <div class="module-header">
      <div>
        <h3>${escapeHtml(item.topic || 'FAQ Detay')}</h3>
        <p>Soru ve cevap aynı panelde incelenir. Durum değişikliği ve kaldırma aksiyonu anında uygulanır.</p>
      </div>
      <span class="pill ${item.status === 'ACTIVE' ? 'open' : (item.status === 'REMOVED' ? 'closed' : 'pending')}">${escapeHtml(item.status || '-')}</span>
    </div>
    <div class="status-list">
      <div class="status-block">
        <h4>Soru (TR)</h4>
        <pre>${escapeHtml(item.question?.tr || '-')}</pre>
      </div>
      <div class="status-block">
        <h4>Soru (EN)</h4>
        <pre>${escapeHtml(item.question?.en || '-')}</pre>
      </div>
      <div class="status-block">
        <h4>Cevap (TR)</h4>
        <pre>${escapeHtml(item.answer?.tr || '-')}</pre>
      </div>
      <div class="status-block">
        <h4>Cevap (EN)</h4>
        <pre>${escapeHtml(item.answer?.en || '-')}</pre>
      </div>
    </div>
    <div class="helper-panel mt-md">
      <div class="helper-box">
        <strong>Varyantlar</strong>
        <p class="mono">TR: ${escapeHtml((variants.tr || []).join(' | ') || '-')}</p>
        <p class="mono">EN: ${escapeHtml((variants.en || []).join(' | ') || '-')}</p>
      </div>
      <div class="helper-box">
        <strong>Yonetim Bilgisi</strong>
        <p class="mono">Guncelleyen: ${escapeHtml(item.updated_by || '-')} · ${escapeHtml(formatDate(item.updated_at) || '-')}</p>
        <p class="mono">Kaldirma: ${escapeHtml(item.removed_reason || '-')}</p>
      </div>
    </div>
  `;
}

async function loadHotelProfileSection() {
  const hotelId = refs.hotelProfileSelect.value || state.selectedHotelId;
  if (!hotelId) {
    refs.hotelProfileEditor.value = '';
    refs.hotelProfileMeta.innerHTML = '<div class="empty-state"><p>Hotel seçin.</p></div>';
    return;
  }
  state.hotelDetail = await apiFetch(`/hotels/${hotelId}`);
  refs.hotelProfileEditor.value = JSON.stringify(state.hotelDetail.profile_json || {}, null, 2);
  refs.hotelProfileMeta.innerHTML = `
    <div class="helper-box">
      <strong>${escapeHtml(state.hotelDetail.name_en || state.hotelDetail.name_tr || 'Hotel')}</strong>
      <p>Dosya kaynağı YAML olarak güncellenir ve runtime cache yenilenir. Bu alan riskli konfigürasyondur.</p>
    </div>
  `;
}

async function saveHotelProfile() {
  const hotelId = refs.hotelProfileSelect.value || state.selectedHotelId;
  if (!hotelId) {
    notify('Hotel seçin.', 'warn');
    return;
  }
  let profileJson;
  try {
    profileJson = JSON.parse(refs.hotelProfileEditor.value);
  } catch (_error) {
    notify('Profile JSON parse edilemedi.', 'error');
    return;
  }
  try {
    const response = await apiFetch(`/hotels/${hotelId}/profile`, {method: 'PUT', body: {profile_json: profileJson}});
    notify(`Profile kaydedildi (${response.profile_path}).`, 'success');
    loadHotelProfileSection();
  } catch (error) {
    notify(error.message, 'error');
  }
}

async function loadRestaurantSlots() {
  const hotelId = state.selectedHotelId;
  if (!hotelId) {
    refs.slotTableBody.innerHTML = '<tr><td colspan="7"><div class="empty-state"><p>Hotel seçin.</p></div></td></tr>';
    return;
  }
  const form = new FormData(refs.slotFilters);
  const params = new URLSearchParams();
  params.set('date_from', String(form.get('date_from') || defaultDate()));
  params.set('date_to', String(form.get('date_to') || defaultDate(7)));
  const response = await apiFetch(`/hotels/${hotelId}/restaurant/slots?${params.toString()}`);
  state.restaurantSlots = response.items || [];
  refs.slotTableBody.innerHTML = renderSlotRows(state.restaurantSlots);
  bindSlotActions();
}

function renderSlotRows(items) {
  if (!items.length) {
    return `<tr><td colspan="7"><div class="empty-state"><p>Seçili aralıkta slot yok.</p></div></td></tr>`;
  }
  return items.map(item => `
    <tr>
      <td>${escapeHtml(item.slot_id)}</td>
      <td>${escapeHtml(item.date)}</td>
      <td>${escapeHtml(item.time)}</td>
      <td>${escapeHtml(item.area)}</td>
      <td>${escapeHtml(item.capacity_left)} / ${escapeHtml(item.total_capacity)}</td>
      <td>${item.is_active ? '<span class="pill open">AKTIF</span>' : '<span class="pill closed">PASIF</span>'}</td>
      <td>
        <div class="stack">
          <input type="number" min="1" value="${escapeHtml(item.total_capacity)}" data-slot-capacity="${escapeHtml(item.slot_id)}">
          <select data-slot-active="${escapeHtml(item.slot_id)}">
            <option value="true" ${item.is_active ? 'selected' : ''}>Aktif</option>
            <option value="false" ${!item.is_active ? 'selected' : ''}>Pasif</option>
          </select>
          <button class="action-button primary" data-save-slot="${escapeHtml(item.slot_id)}">Güncelle</button>
        </div>
      </td>
    </tr>
  `).join('');
}

function bindSlotActions() {
  document.querySelectorAll('[data-save-slot]').forEach(button => {
    button.addEventListener('click', async () => {
      const slotId = button.dataset.saveSlot;
      const capacity = document.querySelector(`[data-slot-capacity="${slotId}"]`).value;
      const isActive = document.querySelector(`[data-slot-active="${slotId}"]`).value === 'true';
      try {
        await apiFetch(`/hotels/${state.selectedHotelId}/restaurant/slots/${slotId}`, {
          method: 'PUT',
          body: {total_capacity: Number(capacity), is_active: isActive},
        });
        notify('Slot güncellendi.', 'success');
        loadRestaurantSlots();
      } catch (error) {
        notify(error.message, 'error');
      }
    });
  });
}

async function onCreateSlot(event) {
  event.preventDefault();
  if (!state.selectedHotelId) {
    notify('Hotel seçin.', 'warn');
    return;
  }
  const payload = formToJson(refs.slotCreateForm);
  payload.total_capacity = Number(payload.total_capacity);
  payload.is_active = payload.is_active === 'on';
  try {
    await apiFetch(`/hotels/${state.selectedHotelId}/restaurant/slots`, {method: 'POST', body: [payload]});
    notify('Yeni slot aralığı oluşturuldu.', 'success');
    refs.slotCreateForm.reset();
    loadRestaurantSlots();
  } catch (error) {
    notify(error.message, 'error');
  }
}

async function loadSystemOverview() {
  const [systemOverview, readyState] = await Promise.all([
    apiFetch('/system/overview'),
    apiFetchFromAbsolute(READY_URL),
  ]);
  state.systemOverview = {systemOverview, readyState};
  renderSystemOverview();
}

function renderSystemOverview() {
  if (!state.systemOverview) return;
  const {systemOverview, readyState} = state.systemOverview;
  refs.systemChecks.innerHTML = Object.entries(systemOverview.checks || {}).map(([key, value]) => `
    <div class="status-block">
      <h4>${escapeHtml(key)}</h4>
      <pre>${escapeHtml(JSON.stringify(value, null, 2))}</pre>
    </div>
  `).join('');
  refs.systemMeta.innerHTML = `
    <div class="helper-box">
      <strong>Panel Domain</strong>
      <p>${escapeHtml(systemOverview.panel_url)}</p>
    </div>
    <div class="helper-box">
      <strong>Trusted Hosts</strong>
      <p>${escapeHtml((systemOverview.trusted_hosts || []).join(', '))}</p>
    </div>
    <div class="helper-box">
      <strong>Readiness</strong>
      <p>${escapeHtml(readyState.status || '-')}</p>
    </div>
  `;
}

async function loadSessionPreferences() {
  state.sessionPreferences = await apiFetch('/session/preferences');
  state.sessionStatus = state.sessionPreferences;
  renderSessionPreferences();
  renderLoginSessionState();
}

function renderSessionPreferences() {
  const prefs = state.sessionPreferences || state.sessionStatus;
  if (!prefs) return;

  refs.sessionRememberToggle.checked = Boolean(prefs.has_trusted_device);
  renderChoiceGroup(
    refs.systemVerificationOptions,
    'verification_preset',
    prefs.verification_options || [],
    prefs.verification_preset || '24_hours',
  );
  renderChoiceGroup(
    refs.systemSessionOptions,
    'session_preset',
    prefs.session_options || [],
    prefs.session_preset || '8_hours',
  );
  refs.sessionSummary.innerHTML = `
    <div class="helper-box">
      <strong>Giris hizlandirma</strong>
      <p>${prefs.has_trusted_device ? 'Bu cihaz tanimli. OTP tekrari ve oturum suresi secimleri aktif.' : 'Bu cihaz icin hizli giris kapali. Etkinlestirmek icin switchi acin ve 6 haneli kodu girin.'}</p>
    </div>
    <div class="status-strip">
      <div class="helper-box">
        <strong>Dogrulama tekrar suresi</strong>
        <p>${prefs.has_trusted_device ? escapeHtml(formatDate(prefs.verification_expires_at)) : '-'}</p>
      </div>
      <div class="helper-box">
        <strong>Oturum hatirlama</strong>
        <p>${prefs.has_trusted_device ? escapeHtml(formatDate(prefs.session_expires_at)) : '-'}</p>
      </div>
    </div>
  `;
  refs.trustedDevicePanel.innerHTML = prefs.has_trusted_device ? `
    <div class="helper-box">
      <strong>${escapeHtml(prefs.device_label || 'Tarayici cihazi')}</strong>
      <p>${escapeHtml(prefs.user_label || 'Aktif kullanici')} icin tanimli.</p>
      <div class="detail-list">
        <span>OTP atlama: ${prefs.verification_active ? 'Acik' : 'Kapali'}</span>
        <span>Session restore: ${prefs.session_active ? 'Acik' : 'Kapali'}</span>
        <span>Son dogrulama: ${escapeHtml(formatDate(prefs.last_verified_at))}</span>
      </div>
    </div>
  ` : '<div class="empty-state"><p>Bu cihaz icin kayitli hizli giris bulunmuyor.</p></div>';
  refs.forgetDeviceButton.hidden = !prefs.has_trusted_device;
  toggleSessionPreferenceState();
}

function toggleSessionPreferenceState() {
  const rememberEnabled = refs.sessionRememberToggle.checked;
  refs.sessionOtpField.hidden = !rememberEnabled;
  refs.sessionPreferencesForm.otp_code.required = rememberEnabled;
}

async function onSessionPreferencesSave(event) {
  event.preventDefault();
  const payload = {
    remember_device: refs.sessionRememberToggle.checked,
    verification_preset: getSelectedChoice(refs.sessionPreferencesForm, 'verification_preset', state.sessionPreferences?.verification_preset || '24_hours'),
    session_preset: getSelectedChoice(refs.sessionPreferencesForm, 'session_preset', state.sessionPreferences?.session_preset || '8_hours'),
  };
  const otpCode = String(refs.sessionPreferencesForm.otp_code.value || '').trim();
  if (payload.remember_device) {
    if (!otpCode) {
      notify('Tercihleri kaydetmek icin 6 haneli kod gerekli.', 'warn');
      return;
    }
    payload.otp_code = otpCode;
  }

  try {
    state.sessionPreferences = await apiFetch('/session/preferences', {method: 'PUT', body: payload});
    state.sessionStatus = state.sessionPreferences;
    refs.sessionPreferencesForm.otp_code.value = '';
    renderSessionPreferences();
    renderLoginSessionState();
    notify(payload.remember_device ? 'Cihaz tercihleri kaydedildi.' : 'Bu cihaz icin hizli giris kapatildi.', 'success');
  } catch (error) {
    notify(error.message, 'error');
  }
}

async function forgetTrustedDevice() {
  try {
    state.sessionPreferences = await apiFetch('/session/forget-device', {method: 'POST', body: {}});
    state.sessionStatus = state.sessionPreferences;
    refs.sessionPreferencesForm.otp_code.value = '';
    renderSessionPreferences();
    renderLoginSessionState();
    notify('Bu cihaz artik hatirlanmayacak.', 'success');
  } catch (error) {
    notify(error.message, 'error');
  }
}

function resolveConversationIntent(conversation, messages) {
  if (conversation?.current_intent) return String(conversation.current_intent);
  const assistant = [...(messages || [])].reverse().find(message => message.role === 'assistant');
  const internal = asObject(assistant?.internal_json);
  return String(internal.intent || 'intent yok');
}

function resolveConversationState(conversation, messages) {
  if (conversation?.current_state) return String(conversation.current_state);
  const assistant = [...(messages || [])].reverse().find(message => message.role === 'assistant');
  const internal = asObject(assistant?.internal_json);
  return String(internal.state || '-');
}

function extractLatestUserAudit(messages) {
  const userMessage = [...(messages || [])].reverse().find(message => message.role === 'user');
  const internal = asObject(userMessage?.internal_json);
  const routeAudit = asObject(internal.route_audit);
  return {
    senderProfileName: internal.sender_profile_name || '-',
    waIdMasked: internal.wa_id_masked || '-',
    waMessageId: internal.message_id || '-',
    route: routeAudit.route || '-',
    webhookIp: routeAudit.webhook_ip || '-',
    receivedAt: routeAudit.received_at || '-',
  };
}

function renderUserAuditSection(audit) {
  if (!audit) return '';
  return `
    <div class="audit-grid">
      <div class="helper-box"><strong>Gönderen Profil Adı</strong><p>${escapeHtml(audit.senderProfileName)}</p></div>
      <div class="helper-box"><strong>WA ID (maskeli)</strong><p>${escapeHtml(audit.waIdMasked)}</p></div>
      <div class="helper-box"><strong>WA Message ID</strong><p class="mono">${escapeHtml(audit.waMessageId)}</p></div>
      <div class="helper-box"><strong>Route Audit</strong><p class="mono">${escapeHtml(`${audit.route} | ${audit.webhookIp}`)}</p><p class="muted">${escapeHtml(formatDate(audit.receivedAt))}</p></div>
    </div>
  `;
}

function renderMessageAuditRow(message) {
  if (message.role !== 'user') return '';
  const internal = asObject(message.internal_json);
  if (!internal.message_id && !internal.route_audit) return '';
  const routeAudit = asObject(internal.route_audit);
  return `
    <div class="audit-row muted mono">
      profil=${escapeHtml(internal.sender_profile_name || '-')}
      | wa_id=${escapeHtml(internal.wa_id_masked || '-')}
      | msg_id=${escapeHtml(internal.message_id || '-')}
      | route=${escapeHtml(routeAudit.route || '-')}
      | ip=${escapeHtml(routeAudit.webhook_ip || '-')}
    </div>
  `;
}

async function reloadConfig() {
  try {
    await apiFetch('/reload-config', {method: 'POST', body: {}});
    notify('Konfigürasyon yeniden yüklendi.', 'success');
    loadSystemOverview();
    if (state.currentView === 'hotels') loadHotelProfileSection();
    if (state.currentView === 'faq') loadFaqs();
  } catch (error) {
    notify(error.message, 'error');
  }
}

async function logout() {
  try {
    await apiFetch('/logout', {method: 'POST', body: {}, allowRefresh: false});
  } catch (_error) {
    // UI logout should still continue even if the backend cookie already expired.
  }
  clearClientSession();
  await loadSessionStatus();
  renderLoginSessionState();
  notify('Oturum kapatildi.', 'info');
  showAuth();
}

function clearClientSession() {
  state.me = null;
  state.bootstrapPending = null;
  state.dashboard = null;
  state.conversationDetail = null;
  state.faqs = [];
  state.faqDetail = null;
  state.sessionPreferences = null;
}

async function apiFetch(path, {method = 'GET', body = null, auth = true, allowRefresh = true, logoutOn401 = true} = {}) {
  const headers = {'Content-Type': 'application/json'};
  if (auth && !isSafeMethod(method)) {
    const csrfToken = readCookie(CSRF_COOKIE);
    if (csrfToken) {
      headers['X-CSRF-Token'] = csrfToken;
    }
  }
  const response = await fetch(`${API_ROOT}${path}`, {
    method,
    credentials: 'same-origin',
    headers,
    body: body ? JSON.stringify(body) : null,
  });
  return handleResponse(response, {auth, allowRefresh, logoutOn401, request: {path, method, body}});
}

async function apiFetchFromAbsolute(path) {
  const response = await fetch(path, {credentials: 'same-origin'});
  return handleResponse(response, {auth: false, allowRefresh: false, logoutOn401: false, request: null});
}

async function handleResponse(response, options) {
  let payload = {};
  try {
    payload = await response.json();
  } catch (_error) {
    payload = {};
  }
  if (!response.ok) {
    if (options.auth && response.status === 401 && options.allowRefresh) {
      const refreshed = await refreshAccessSession({silent: true});
      if (refreshed && options.request) {
        return apiFetch(options.request.path, {
          method: options.request.method,
          body: options.request.body,
          auth: true,
          allowRefresh: false,
          logoutOn401: options.logoutOn401,
        });
      }
    }
    if (options.auth && response.status === 401 && options.logoutOn401) {
      clearClientSession();
      await loadSessionStatus();
      showAuth();
    }
    throw new Error(extractErrorMessage(payload));
  }
  return payload;
}

async function refreshAccessSession({silent = false} = {}) {
  if (state.refreshPromise) {
    return state.refreshPromise;
  }
  state.refreshPromise = (async () => {
    try {
      await apiFetch('/session/refresh', {method: 'POST', body: {}, auth: false, allowRefresh: false, logoutOn401: false});
      await loadSessionStatus();
      return true;
    } catch (error) {
      if (!silent) {
        notify(error.message, 'warn');
      }
      await loadSessionStatus();
      return false;
    } finally {
      state.refreshPromise = null;
    }
  })();
  return state.refreshPromise;
}

// extractErrorMessage wraps shared extractErrorDetail for admin panel compat
function extractErrorMessage(payload) {
  return extractErrorDetail(payload, '');
}

function getSelectedChoice(form, name, fallback) {
  const field = form.querySelector(`input[name="${name}"]:checked`);
  return field ? field.value : fallback;
}

function notify(message, tone = 'info') {
  refs.toast.textContent = message;
  refs.toast.className = `toast ${tone} is-visible`;
  window.clearTimeout(notify.timer);
  notify.timer = window.setTimeout(() => refs.toast.className = `toast ${tone}`, 2800);
}

// ---------------------------------------------------------------------------
// Notification phones
// ---------------------------------------------------------------------------

async function loadNotifPhones() {
  try {
    const phones = await apiFetch('/notification-phones');
    renderNotifPhones(phones);
  } catch (err) {
    notify('Bildirim numaralari yuklenemedi: ' + (err.message || err), 'error');
  }
}

function renderNotifPhones(phones) {
  if (!refs.notifPhoneTableBody) return;
  if (!phones || !phones.length) {
    refs.notifPhoneTableBody.innerHTML = '<tr><td colspan="4"><div class="empty-state"><p>Kayit yok</p></div></td></tr>';
    return;
  }
  refs.notifPhoneTableBody.innerHTML = phones.map(p => {
    const isDefault = p.is_default;
    const removeBtn = isDefault
      ? '<span class="badge dark">Varsayilan</span>'
      : `<button class="inline-button danger" data-remove-phone="${escapeHtml(p.phone)}">Kaldir</button>`;
    return `<tr>
      <td><code>${escapeHtml(p.phone)}</code></td>
      <td>${escapeHtml(p.label || '-')}</td>
      <td>${isDefault ? 'Evet' : 'Hayir'}</td>
      <td>${removeBtn}</td>
    </tr>`;
  }).join('');
  bindNotifPhoneActions();
}

function bindNotifPhoneActions() {
  document.querySelectorAll('[data-remove-phone]').forEach(button => {
    button.addEventListener('click', () => removeNotifPhone(button.dataset.removePhone));
  });
}

async function onAddNotifPhone(event) {
  event.preventDefault();
  const form = refs.addNotifPhoneForm;
  const phone = form.phone.value.trim();
  const label = form.label.value.trim();
  if (!phone) return;
  try {
    await apiFetch('/notification-phones', {method: 'POST', body: {phone, label}});
    notify('Numara eklendi', 'success');
    form.reset();
    await loadNotifPhones();
  } catch (err) {
    notify('Numara eklenemedi: ' + (err.message || err), 'error');
  }
}

async function removeNotifPhone(phone) {
  if (!confirm('Bu numarayi kaldirmak istediginize emin misiniz?')) return;
  const encoded = phone.replace('+', '_');
  try {
    await apiFetch('/notification-phones/' + encoded, {method: 'DELETE'});
    notify('Numara kaldirildi', 'success');
    await loadNotifPhones();
  } catch (err) {
    notify('Numara kaldirilamadi: ' + (err.message || err), 'error');
  }
}
"""
