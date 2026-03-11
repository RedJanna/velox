"""Static assets for the admin operations panel."""

# ruff: noqa: E501

ADMIN_PANEL_STYLE = """\
*,*::before,*::after{box-sizing:border-box}
:root{
  --bg:#f4efe6;--bg-2:#ebe4d8;--surface:#fffdf8;--surface-2:#f8f4ec;--ink:#102033;--muted:#5d6877;
  --line:rgba(16,32,51,.12);--line-strong:rgba(16,32,51,.2);--accent:#0f766e;--accent-2:#1d8f86;
  --warn:#b45309;--danger:#b42318;--danger-2:#7f1d1d;--ok:#166534;--gold:#bb8a2a;--shadow:0 18px 42px rgba(16,32,51,.08);
  --radius-lg:26px;--radius-md:18px;--radius-sm:12px;--mono:'Cascadia Code','Fira Code',monospace;
  --sans:'Segoe UI Variable','Aptos','Segoe UI',system-ui,sans-serif;--serif:'Iowan Old Style','Georgia',serif;
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
.topbar-aside{display:flex;flex-wrap:wrap;gap:10px;justify-content:flex-end}
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
@media(max-width:1240px){
  .card-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
  .split,.auth-grid{grid-template-columns:1fr}
}
@media(max-width:980px){
  body{padding:12px}.shell{grid-template-columns:1fr}
  .sidebar{padding:18px;border-radius:24px}
  .field-grid,.dense-form,.status-list{grid-template-columns:1fr}
  .topbar{padding:18px 20px;border-radius:24px;flex-direction:column}
  .card-grid{grid-template-columns:1fr}
}
"""

ADMIN_PANEL_SCRIPT = """\
const CONFIG = window.ADMIN_PANEL_CONFIG || {};
const API_ROOT = '/api/v1/admin';
const READY_URL = '/api/v1/health/ready';
const TOKEN_KEY = 'velox.admin.token';
const HOTEL_KEY = 'velox.admin.hotel';

const state = {
  token: window.localStorage.getItem(TOKEN_KEY) || '',
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
  hotelDetail: null,
  restaurantSlots: [],
  systemOverview: null,
};

const refs = {};

document.addEventListener('DOMContentLoaded', () => {
  bindRefs();
  bindEvents();
  boot();
});

function bindRefs() {
  [
    'toast','authView','panelView','loginForm','bootstrapForm','bootstrapCard','bootstrapSummary',
    'totpRecovery','totpRecoveryForm',
    'otpSetup','otpSecret','otpUri','otpQrImage','otpVerifyForm','otpVerifyHint','currentUser','currentRole','hotelScope','hotelSelect','nav','pageTitle','pageLead',
    'dashboardCards','dashboardQueues','conversationFilters','conversationTableBody','conversationDetail',
    'holdFilters','holdTableBody','ticketFilters','ticketTableBody','hotelProfileSelect','hotelProfileEditor',
    'hotelProfileMeta','slotFilters','slotTableBody','slotCreateForm','systemChecks','systemMeta',
    'logoutButton','reloadButton','decisionDialog','decisionForm','decisionTitle','decisionLead','decisionReason',
    'decisionHoldId','decisionMode'
  ].forEach(id => refs[id] = document.getElementById(id));
  // Bootstrap hotel select uses kebab-case id in HTML; map it to the existing JS key.
  refs.bootstrapHotels = document.getElementById('bootstrap-hotel');
}

function bindEvents() {
  refs.loginForm.addEventListener('submit', onLogin);
  refs.bootstrapForm.addEventListener('submit', onBootstrap);
  refs.totpRecoveryForm.addEventListener('submit', onTotpRecovery);
  refs.otpVerifyForm.addEventListener('submit', onBootstrapVerify);
  refs.hotelSelect.addEventListener('change', onHotelScopeChange);
  refs.hotelProfileSelect.addEventListener('change', loadHotelProfileSection);
  refs.slotCreateForm.addEventListener('submit', onCreateSlot);
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
  refs.decisionForm.addEventListener('submit', onDecisionSubmit);
  document.querySelectorAll('[data-nav]').forEach(button => {
    button.addEventListener('click', () => setView(button.dataset.nav));
  });
  document.getElementById('saveHotelProfile').addEventListener('click', saveHotelProfile);
  document.getElementById('loadSlotsButton').addEventListener('click', event => {
    event.preventDefault();
    loadRestaurantSlots();
  });
  document.getElementById('closeDecision').addEventListener('click', () => refs.decisionDialog.close());
}

async function boot() {
  await loadBootstrapStatus();
  if (state.token) {
    try {
      await hydrateSession();
      return;
    } catch (error) {
      console.error(error);
    }
  }
  showAuth();
}

async function loadBootstrapStatus() {
  state.bootstrap = await apiFetch('/bootstrap/status', {auth: false});
  renderBootstrapState();
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
        <p>Panel girisi aktif. Google Authenticator kodunuz ile oturum acabilirsiniz.</p>
      </div>
      <div class="helper-box">
        <strong>Alan adi</strong>
        <p>${escapeHtml(info.panel_url || CONFIG.panel_url || '/admin')}</p>
      </div>
    `;
    return;
  }

  refs.bootstrapForm.hidden = false;
  refs.totpRecovery.hidden = true;
  const accessMode = info.local_bootstrap_allowed
    ? 'Bu cihazdan localhost bootstrap acik.'
    : (info.token_bootstrap_enabled ? 'Bootstrap token gerekli.' : 'Bootstrap icin localhost erisimi veya ENV token gerekli.');

  refs.bootstrapSummary.innerHTML = `
    <div class="helper-box">
      <strong>Ilk yonetici hesabi gerekli</strong>
      <p>Veritabaninda admin kullanicisi yok. Ilk hesap olusturulduktan sonra panel dogrudan 2FA ile calisacak.</p>
    </div>
    <div class="helper-box">
      <strong>Erisim modu</strong>
      <p>${escapeHtml(accessMode)}</p>
    </div>
  `;
}

async function onLogin(event) {
  event.preventDefault();
  const payload = formToJson(refs.loginForm);
  try {
    const response = await apiFetch('/login', {method: 'POST', body: payload, auth: false});
    state.token = response.access_token;
    window.localStorage.setItem(TOKEN_KEY, state.token);
    notify('Oturum acildi.', 'success');
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
    notify('Sifre en fazla 72 byte olabilir.', 'warn');
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
    notify('Ilk admin hesabi olusturuldu. QR okutun ve kodu dogrulayin.', 'success');
  } catch (error) {
    notify(error.message, 'error');
  }
}

async function onTotpRecovery(event) {
  event.preventDefault();
  const payload = formToJson(refs.totpRecoveryForm);
  const nextPassword = String(payload.new_password || '');
  if (nextPassword && new TextEncoder().encode(nextPassword).length > 72) {
    notify('Sifre en fazla 72 byte olabilir.', 'warn');
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
      notify('2FA yenilendi. Yeni sifre ve Authenticator kodu ile giris yapin.', 'success');
    } else {
      notify('2FA yenilendi. Mevcut sifreniz ve yeni Authenticator kodu ile giris yapin.', 'success');
    }
  } catch (error) {
    notify(error.message, 'error');
  }
}

async function onBootstrapVerify(event) {
  event.preventDefault();
  if (!state.bootstrapPending) {
    notify('Once ilk admin hesabini olusturun.', 'warn');
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
    state.token = response.access_token;
    state.bootstrapPending = null;
    window.localStorage.setItem(TOKEN_KEY, state.token);
    notify('Kurulum dogrulandi, oturum acildi.', 'success');
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
  await Promise.all([loadDashboard(), loadSystemOverview()]);
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
  refs.currentUser.textContent = 'Misafir degil, operasyon';
  refs.currentRole.textContent = 'Panel girisi bekleniyor';
  refs.hotelScope.textContent = CONFIG.public_host || 'nexlumeai.com';
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
    dashboard: ['Operasyon Ozeti', 'Tek bakista ne normal, ne riskli ve siradaki aksiyon ne sorularina cevap verir.'],
    conversations: ['Konusmalar', 'Mesaj akisini, risk flaglerini ve karar baglamini ayni yerde toplar.'],
    holds: ['Onay Bekleyen Kayitlar', 'Konaklama, restoran ve transfer taleplerini tek kararla yonetin.'],
    tickets: ['Handoff ve Takip', 'Acilik, sahiplik ve kapanis durumlarini kaybetmeden ekip yonetin.'],
    hotels: ['Hotel Profile', 'Dinamik hotel verisini panelden duzenleyip runtime cache ile esitleyin.'],
    restaurant: ['Restoran Slotlari', 'Kapasite, alan ve tarih bazli slot yonetimini kontrol edin.'],
    system: ['Sistem ve Domain', 'Alan adi, readiness, konfig reload ve panel guven katmanlarini izleyin.'],
  }[view] || ['Admin Panel', 'Operasyon merkezi'];

  refs.pageTitle.textContent = meta[0];
  refs.pageLead.textContent = meta[1];

  if (view === 'dashboard') loadDashboard();
  if (view === 'conversations') loadConversations();
  if (view === 'holds') loadHolds();
  if (view === 'tickets') loadTickets();
  if (view === 'hotels') loadHotelProfileSection();
  if (view === 'restaurant') loadRestaurantSlots();
  if (view === 'system') loadSystemOverview();
}

function onHotelScopeChange() {
  state.selectedHotelId = refs.hotelSelect.value;
  refs.hotelProfileSelect.value = refs.hotelSelect.value;
  window.localStorage.setItem(HOTEL_KEY, state.selectedHotelId);
  refs.hotelScope.textContent = state.selectedHotelId || '-';
  setView(state.currentView);
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
      `, 'Konusma yok')}
    </div>
    <div class="queue-card">
      <div class="module-header"><div><h3>Bekleyen Holdlar</h3><p>Onay bekleyen kararlar burada yogunlasir.</p></div></div>
      ${renderQueue(state.dashboard.recent_holds, item => `
        <div class="queue-item">
          <strong>${escapeHtml(item.hold_id)}</strong>
          <span class="muted">${escapeHtml(item.hold_type)} · ${escapeHtml(item.status)}</span>
          <div class="muted">${formatDate(item.created_at)}</div>
        </div>
      `, 'Bekleyen hold yok')}
    </div>
    <div class="queue-card">
      <div class="module-header"><div><h3>Acik Ticketlar</h3><p>Handoff kuyrugunda sahiplik ve oncelik takibi.</p></div></div>
      ${renderQueue(state.dashboard.recent_tickets, item => `
        <div class="queue-item">
          <strong>${escapeHtml(item.ticket_id)}</strong>
          <span class="muted">${escapeHtml(item.reason)} · ${escapeHtml(item.priority)}</span>
          <div class="muted">${formatDate(item.created_at)}</div>
        </div>
      `, 'Acik ticket yok')}
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
  bindConversationActions();
  if (state.conversations.length && !state.conversationDetail) {
    loadConversationDetail(state.conversations[0].id);
  } else if (!state.conversations.length) {
    refs.conversationDetail.innerHTML = '<div class="empty-state"><p>Secili konusma yok.</p></div>';
  }
}

function renderConversationRows(items) {
  if (!items.length) {
    return `<tr><td colspan="6"><div class="empty-state"><p>Filtreye uygun konusma bulunamadi.</p></div></td></tr>`;
  }
  return items.map(item => `
    <tr>
      <td><div class="stack"><strong>${escapeHtml(item.phone_display || 'Maskeli kullanici')}</strong><span class="muted mono">${escapeHtml(item.id)}</span></div></td>
      <td><span class="pill open">${escapeHtml(item.current_state || '-')}</span></td>
      <td>${escapeHtml(item.current_intent || '-')}</td>
      <td>${escapeHtml((item.risk_flags || []).join(', ') || 'Yok')}</td>
      <td>${escapeHtml(item.message_count || 0)}</td>
      <td><button class="inline-button primary" data-open-conversation="${escapeHtml(item.id)}">Detay</button></td>
    </tr>
  `).join('');
}

function bindConversationActions() {
  document.querySelectorAll('[data-open-conversation]').forEach(button => {
    button.addEventListener('click', () => loadConversationDetail(button.dataset.openConversation));
  });
}

async function loadConversationDetail(conversationId) {
  const response = await apiFetch(`/conversations/${conversationId}`);
  state.conversationDetail = response;
  refs.conversationDetail.innerHTML = `
    <div class="module-header">
      <div>
        <h3>Konusma Detayi</h3>
        <p>${escapeHtml(response.conversation.phone_display || 'Maskeli kullanici')} · ${escapeHtml(response.conversation.current_state || '-')}</p>
      </div>
      <div class="badge dark">${escapeHtml(response.conversation.current_intent || 'intent yok')}</div>
    </div>
    <div class="timeline">
      ${(response.messages || []).map(message => `
        <article class="message ${escapeHtml(message.role || 'system')}">
          <header><strong>${escapeHtml(message.role || 'system')}</strong><span class="muted">${formatDate(message.created_at)}</span></header>
          <pre>${escapeHtml(message.content || '')}</pre>
        </article>
      `).join('')}
    </div>
  `;
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
  bindHoldActions();
}

function renderHoldRows(items) {
  if (!items.length) {
    return `<tr><td colspan="6"><div class="empty-state"><p>Onay akisinda kayit yok.</p></div></td></tr>`;
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

function bindHoldActions() {
  document.querySelectorAll('[data-approve-hold]').forEach(button => {
    button.addEventListener('click', async () => {
      try {
        await apiFetch(`/holds/${button.dataset.approveHold}/approve`, {method: 'POST', body: {notes: ''}});
        notify('Hold onaylandi.', 'success');
        loadHolds();
        loadDashboard();
      } catch (error) {
        notify(error.message, 'error');
      }
    });
  });
  document.querySelectorAll('[data-reject-hold]').forEach(button => {
    button.addEventListener('click', () => {
      refs.decisionMode.value = 'reject';
      refs.decisionHoldId.value = button.dataset.rejectHold;
      refs.decisionTitle.textContent = 'Hold reddet';
      refs.decisionLead.textContent = 'Bu islem misafir akisina olumsuz yansir. Nedeni acik yazin.';
      refs.decisionReason.value = '';
      refs.decisionDialog.showModal();
    });
  });
}

async function onDecisionSubmit(event) {
  event.preventDefault();
  const holdId = refs.decisionHoldId.value;
  const reason = refs.decisionReason.value.trim();
  if (!reason) {
    notify('Red gerekcesi zorunlu.', 'warn');
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
  bindTicketActions();
}

function renderTicketRows(items) {
  if (!items.length) {
    return `<tr><td colspan="7"><div class="empty-state"><p>Acik ticket bulunamadi.</p></div></td></tr>`;
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

function bindTicketActions() {
  document.querySelectorAll('[data-save-ticket]').forEach(button => {
    button.addEventListener('click', async () => {
      const ticketId = button.dataset.saveTicket;
      const statusField = document.querySelector(`[data-ticket-status="${ticketId}"]`);
      try {
        await apiFetch(`/tickets/${ticketId}`, {method: 'PUT', body: {status: statusField.value}});
        notify('Ticket guncellendi.', 'success');
        loadTickets();
        loadDashboard();
      } catch (error) {
        notify(error.message, 'error');
      }
    });
  });
}

async function loadHotelProfileSection() {
  const hotelId = refs.hotelProfileSelect.value || state.selectedHotelId;
  if (!hotelId) {
    refs.hotelProfileEditor.value = '';
    refs.hotelProfileMeta.innerHTML = '<div class="empty-state"><p>Hotel secin.</p></div>';
    return;
  }
  state.hotelDetail = await apiFetch(`/hotels/${hotelId}`);
  refs.hotelProfileEditor.value = JSON.stringify(state.hotelDetail.profile_json || {}, null, 2);
  refs.hotelProfileMeta.innerHTML = `
    <div class="helper-box">
      <strong>${escapeHtml(state.hotelDetail.name_en || state.hotelDetail.name_tr || 'Hotel')}</strong>
      <p>Dosya kaynagi YAML olarak guncellenir ve runtime cache yenilenir. Bu alan riskli konfigurasyondur.</p>
    </div>
  `;
}

async function saveHotelProfile() {
  const hotelId = refs.hotelProfileSelect.value || state.selectedHotelId;
  if (!hotelId) {
    notify('Hotel secin.', 'warn');
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
    refs.slotTableBody.innerHTML = '<tr><td colspan="7"><div class="empty-state"><p>Hotel secin.</p></div></td></tr>';
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
    return `<tr><td colspan="7"><div class="empty-state"><p>Secili aralikta slot yok.</p></div></td></tr>`;
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
          <button class="action-button primary" data-save-slot="${escapeHtml(item.slot_id)}">Guncelle</button>
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
        notify('Slot guncellendi.', 'success');
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
    notify('Hotel secin.', 'warn');
    return;
  }
  const payload = formToJson(refs.slotCreateForm);
  payload.total_capacity = Number(payload.total_capacity);
  payload.is_active = payload.is_active === 'on';
  try {
    await apiFetch(`/hotels/${state.selectedHotelId}/restaurant/slots`, {method: 'POST', body: [payload]});
    notify('Yeni slot araligi olusturuldu.', 'success');
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

async function reloadConfig() {
  try {
    await apiFetch('/reload-config', {method: 'POST', body: {}});
    notify('Konfigurasyon yeniden yuklendi.', 'success');
    loadSystemOverview();
    if (state.currentView === 'hotels') loadHotelProfileSection();
  } catch (error) {
    notify(error.message, 'error');
  }
}

function logout() {
  state.token = '';
  state.me = null;
  state.bootstrapPending = null;
  window.localStorage.removeItem(TOKEN_KEY);
  notify('Oturum kapatildi.', 'info');
  showAuth();
}

async function apiFetch(path, {method = 'GET', body = null, auth = true} = {}) {
  const headers = {'Content-Type': 'application/json'};
  if (auth && state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }
  const response = await fetch(`${API_ROOT}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : null,
  });
  return handleResponse(response, auth);
}

async function apiFetchFromAbsolute(path) {
  const response = await fetch(path);
  return handleResponse(response, false);
}

async function handleResponse(response, auth) {
  let payload = {};
  try {
    payload = await response.json();
  } catch (_error) {
    payload = {};
  }
  if (!response.ok) {
    if (auth && response.status === 401) {
      logout();
    }
    throw new Error(extractErrorMessage(payload));
  }
  return payload;
}

function extractErrorMessage(payload) {
  if (typeof payload?.detail === 'string' && payload.detail.trim()) {
    return payload.detail;
  }
  if (Array.isArray(payload?.detail) && payload.detail.length > 0) {
    const messages = payload.detail.map(item => {
      if (typeof item === 'string') return item;
      if (item && typeof item.msg === 'string') return item.msg;
      return '';
    }).filter(Boolean);
    if (messages.length > 0) {
      return messages.join(' | ');
    }
  }
  if (typeof payload?.message === 'string' && payload.message.trim()) {
    return payload.message;
  }
  return 'Beklenmeyen panel hatasi.';
}

function formToJson(form) {
  return Object.fromEntries(new FormData(form).entries());
}

function notify(message, tone = 'info') {
  refs.toast.textContent = message;
  refs.toast.className = `toast ${tone} is-visible`;
  window.clearTimeout(notify.timer);
  notify.timer = window.setTimeout(() => refs.toast.className = `toast ${tone}`, 2800);
}

function formatDate(value) {
  if (!value) return '-';
  try {
    return new Date(value).toLocaleString('tr-TR', {dateStyle: 'short', timeStyle: 'short'});
  } catch (_error) {
    return String(value);
  }
}

function defaultDate(offsetDays = 0) {
  const date = new Date();
  date.setDate(date.getDate() + offsetDays);
  return date.toISOString().slice(0, 10);
}

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
"""
