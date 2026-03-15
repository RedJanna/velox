"""HTML route for the unified admin operations panel."""

from __future__ import annotations

# ruff: noqa: E501
import json

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from velox.api.routes.admin_panel_ui_assets import ADMIN_PANEL_SCRIPT, ADMIN_PANEL_STYLE
from velox.config.settings import settings

router = APIRouter(tags=["admin-panel-ui"])
ADMIN_PANEL_ROUTE = settings.admin_panel_path if settings.admin_panel_path.startswith("/") else f"/{settings.admin_panel_path}"


def render_admin_panel_html() -> str:
    """Assemble the standalone admin panel HTML document."""
    config_json = json.dumps(
        {
            "panel_url": settings.admin_panel_url,
            "public_host": settings.public_host,
        },
        ensure_ascii=False,
    )
    return f"""\
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>NexlumeAI Admin Panel</title>
  <style>{ADMIN_PANEL_STYLE}</style>
</head>
<body>
  <div id="toast" class="toast info" role="status" aria-live="polite"></div>
  <div class="shell">
    <aside id="sidebar" class="sidebar">
      <div class="brand">
        <div class="brand-mark">NX</div>
        <div>
          <h1>NexlumeAI<br>Admin</h1>
          <p>Misafir konusmalari, onaylar ve otel ayarlari tek yerden yonetilir.</p>
        </div>
      </div>

      <nav id="nav" class="nav" aria-label="Admin navigasyon">
        <button data-nav="dashboard"><span class="nav-label"><strong>Genel Bakis</strong><span>Anlık durum ozeti</span></span><span>01</span></button>
        <button data-nav="conversations"><span class="nav-label"><strong>Konusmalar</strong><span>Misafir mesajlari ve gecmis</span></span><span>02</span></button>
        <button data-nav="holds"><span class="nav-label"><strong>Onay Bekleyenler</strong><span>Rezervasyon onay ve red islemleri</span></span><span>03</span></button>
        <button data-nav="tickets"><span class="nav-label"><strong>Destek Talepleri</strong><span>Ekibe aktarilan gorevler</span></span><span>04</span></button>
        <button data-nav="hotels"><span class="nav-label"><strong>Otel Bilgileri</strong><span>Otel profil ve ayarlari</span></span><span>05</span></button>
        <button data-nav="faq"><span class="nav-label"><strong>Sik Sorulan Sorular</strong><span>Hazir yanit yonetimi</span></span><span>06</span></button>
        <button data-nav="restaurant"><span class="nav-label"><strong>Restoran Yonetimi</strong><span>Masa ve kapasite ayarlari</span></span><span>07</span></button>
        <button data-nav="notifications"><span class="nav-label"><strong>Bildirim Ayarlari</strong><span>WhatsApp bildirim numaralari</span></span><span>08</span></button>
        <button data-nav="system"><span class="nav-label"><strong>Sistem Durumu</strong><span>Sunucu ve baglanti kontrolleri</span></span><span>09</span></button>
        <button data-nav="chatlab"><span class="nav-label"><strong>Test Paneli</strong><span>Canli test ve degerlendirme</span></span><span>10</span></button>
      </nav>

      <section class="sidebar-card">
        <h2>Kimlik</h2>
        <p id="currentUser">Panel girişi bekleniyor</p>
        <small id="currentRole">-</small>
      </section>

      <section class="sidebar-card">
        <h2>Scope</h2>
        <label for="hotelSelect">Hotel</label>
        <select id="hotelSelect" class="sidebar-select"></select>
        <p class="mt-sm">Aktif scope: <strong id="hotelScope">-</strong></p>
      </section>

      <section class="sidebar-card">
        <h2>Kontroller</h2>
        <div class="sidebar-actions">
          <button id="reloadButton" class="sidebar-button warn" type="button">Config Reload</button>
          <button id="logoutButton" class="sidebar-button secondary" type="button">Çıkış Yap</button>
        </div>
      </section>
    </aside>

    <main class="workspace">
      <header class="topbar">
        <div>
          <div class="badge dark">NexlumeAI Yonetim Paneli</div>
          <h2 id="pageTitle">Genel Bakis</h2>
          <p id="pageLead">Aktif konusmalar, bekleyen onaylar ve acik talepleri tek ekranda gorun.</p>
        </div>
        <div class="topbar-actions">
          <button id="sidebarToggle" class="sidebar-toggle" type="button" aria-label="Navigasyon menusu" aria-expanded="false">Menü</button>
          <div class="topbar-aside">
            <div class="badge info">Merkezi yonetim</div>
            <div class="badge warn">Onay gerektiren islemler gorunur</div>
          </div>
        </div>
      </header>

      <section id="authView" class="panel">
        <div class="auth-grid">
          <article class="auth-card">
            <h3>Panel Girisi</h3>
            <p>Kullanici adi, sifre ve Google Authenticator kodu ile giris yapin. Tanimli cihazlarda kod adimi atlanabilir.</p>
            <div id="trustedSessionBanner" class="helper-panel mb-md" hidden></div>
            <form id="loginForm" class="field-grid" method="post">
              <div class="field">
                <label for="login-username">Kullanıcı adı</label>
                <input id="login-username" name="username" autocomplete="username" required>
              </div>
              <div class="field">
                <label for="login-password">Şifre</label>
                <input id="login-password" name="password" type="password" autocomplete="current-password" maxlength="72" required>
              </div>
              <div id="loginOtpField" class="field full">
                <label for="login-otp">Google Authenticator kodu</label>
                <input id="login-otp" name="otp_code" inputmode="numeric" pattern="[0-9]*" placeholder="6 haneli kod" required>
              </div>
              <div class="field full">
                <label class="toggle-row" for="rememberDeviceToggle">
                  <span class="toggle-copy">
                    <strong>Bu cihazi hatirla</strong>
                    <small>Ayni cihazda tekrar girislerde Google dogrulamasini azaltir.</small>
                  </span>
                  <span class="switch">
                    <input id="rememberDeviceToggle" name="remember_device" type="checkbox">
                    <span class="switch-track"><span class="switch-thumb"></span></span>
                  </span>
                </label>
              </div>
              <div id="loginRememberOptions" class="field full" hidden>
                <div class="session-stack">
                  <div>
                    <label>Dogrulama tekrari</label>
                    <div id="loginVerificationOptions" class="choice-group"></div>
                  </div>
                  <div>
                    <label>Oturum hatirlama</label>
                    <div id="loginSessionOptions" class="choice-group"></div>
                  </div>
                  <p class="helper">Paylasilan cihazlarda bu secenegi kapali tutun.</p>
                </div>
              </div>
              <div class="field full">
                <button class="sidebar-button primary" type="submit">Oturum Aç</button>
              </div>
            </form>
          </article>

          <article id="bootstrapCard" class="auth-card">
            <h3>İlk Kurulum</h3>
            <p>Henuz yonetici hesabi yoksa buradan ilk hesabi olusturun ve Google Authenticator'i baglatin.</p>
            <div id="bootstrapSummary" class="helper-panel"></div>
            <form id="bootstrapForm" class="field-grid mt-md" method="post">
              <div class="field">
                <label for="bootstrap-hotel">Hotel</label>
                <select id="bootstrap-hotel" name="hotel_id" required></select>
              </div>
              <div class="field">
                <label for="bootstrap-username">Kullanıcı adı</label>
                <input id="bootstrap-username" name="username" required>
              </div>
              <div class="field">
                <label for="bootstrap-display-name">Görünen ad</label>
                <input id="bootstrap-display-name" name="display_name">
              </div>
              <div class="field">
                <label for="bootstrap-password">Geçici şifre</label>
                <input id="bootstrap-password" name="password" type="password" minlength="12" maxlength="72" required>
              </div>
              <div class="field full">
                <label for="bootstrap-token">Bootstrap token</label>
                <input id="bootstrap-token" name="bootstrap_token" placeholder="ENV ile açıldıysa gerekli olabilir">
              </div>
              <div class="field full">
                <button class="sidebar-button primary" type="submit">İlk Admin Hesabını Oluştur</button>
              </div>
            </form>
            <section id="totpRecovery" class="helper-panel mt-md" hidden>
              <div class="helper-box">
                <strong>2FA Kurtarma</strong>
                <p>Hesap var ama Google Authenticator kurulumu kaybolduysa, bootstrap token ile yeni QR uretebilirsiniz.</p>
              </div>
              <form id="totpRecoveryForm" class="field-grid" method="post">
                <div class="field">
                  <label for="recovery-username">Kullanici adi</label>
                  <input id="recovery-username" name="username" required>
                </div>
                <div class="field">
                  <label for="recovery-token">Bootstrap token</label>
                  <input id="recovery-token" name="bootstrap_token" required>
                </div>
                <div class="field full">
                <label for="recovery-password">Yeni sifre (opsiyonel)</label>
                  <input id="recovery-password" name="new_password" type="password" minlength="12" maxlength="72" placeholder="Boş bırakırsanız mevcut şifre korunur">
                </div>
                <div class="field full">
                  <button class="sidebar-button warn" type="submit">2FA QR Yenile</button>
                </div>
              </form>
            </section>
            <div id="otpSetup" class="helper-panel" hidden>
              <div class="helper-box">
                <strong>Google Authenticator QR</strong>
                <div class="qr-wrap">
                  <img id="otpQrImage" alt="Google Authenticator QR">
                </div>
              </div>
              <div class="helper-box">
                <strong>Authenticator Secret</strong>
                <p id="otpSecret" class="mono"></p>
              </div>
              <div class="helper-box">
                <strong>otpauth URI</strong>
                <p id="otpUri" class="mono"></p>
              </div>
            </div>
            <form id="otpVerifyForm" class="field-grid mt-md" method="post" hidden>
              <div class="field full">
                <label for="otp-verify-code">Google Authenticator kodu</label>
                <input id="otp-verify-code" name="otp_code" inputmode="numeric" pattern="[0-9]*" placeholder="6 haneli kod" required>
              </div>
              <div class="field full">
                <button class="sidebar-button primary" type="submit">Kurulumu Doğrula ve Oturum Aç</button>
              </div>
            </form>
            <p id="otpVerifyHint" class="helper" hidden>QR okutulduktan sonra uygulamadaki 6 haneli kodu girin.</p>
          </article>
        </div>
      </section>

      <section id="panelView" class="panel" hidden>
        <section data-view="dashboard" class="section-grid">
          <div id="dashboardCards" class="card-grid"></div>
          <div id="dashboardQueues" class="card-grid card-grid-3"></div>
        </section>

        <section data-view="conversations" class="section-grid" hidden>
          <div class="split">
            <article class="module-card">
              <div class="module-header">
                <div><h3>Konuşma Listesi</h3><p>Filtreleri sade tutun, riskli olanları hızlıca açın.</p></div>
              </div>
              <form id="conversationFilters" class="toolbar">
                <select name="status" aria-label="Konusma durumu">
                  <option value="">Tum durumlar</option>
                  <option value="GREETING">GREETING</option>
                  <option value="PENDING_APPROVAL">PENDING_APPROVAL</option>
                  <option value="CONFIRMED">CONFIRMED</option>
                  <option value="HANDOFF">HANDOFF</option>
                </select>
                <input name="date_from" type="date" aria-label="Başlangıç tarihi">
                <input name="date_to" type="date" aria-label="Bitiş tarihi">
                <button class="primary" type="submit">Filtrele</button>
              </form>
              <div class="table-shell">
                <table>
                  <thead><tr><th>Kullanici</th><th>Durum</th><th>Intent</th><th>Risk</th><th>Mesaj</th><th></th></tr></thead>
                  <tbody id="conversationTableBody"></tbody>
                </table>
              </div>
            </article>
            <article id="conversationDetail" class="module-card">
              <div class="empty-state"><p>Detay için soldan bir konuşma seçin.</p></div>
            </article>
          </div>
        </section>

        <section data-view="holds" class="section-grid" hidden>
          <div class="split">
            <article class="module-card">
              <div class="module-header">
                <div><h3>Birleşik Hold Masası</h3><p>Konaklama, restoran ve transfer taleplerini tek kurgu ile yönetin.</p></div>
              </div>
              <form id="holdFilters" class="toolbar">
                <select name="hold_type" aria-label="Hold tipi">
                  <option value="">Tum tipler</option>
                  <option value="stay">Stay</option>
                  <option value="restaurant">Restaurant</option>
                  <option value="transfer">Transfer</option>
                </select>
                <select name="status" aria-label="Hold durumu">
                  <option value="">Tum statuler</option>
                  <option value="PENDING_APPROVAL">PENDING_APPROVAL</option>
                  <option value="PMS_PENDING">PMS_PENDING</option>
                  <option value="PMS_CREATED">PMS_CREATED</option>
                  <option value="PAYMENT_PENDING">PAYMENT_PENDING</option>
                  <option value="PAYMENT_EXPIRED">PAYMENT_EXPIRED</option>
                  <option value="MANUAL_REVIEW">MANUAL_REVIEW</option>
                  <option value="PMS_FAILED">PMS_FAILED</option>
                  <option value="APPROVED">APPROVED</option>
                  <option value="CONFIRMED">CONFIRMED</option>
                  <option value="REJECTED">REJECTED</option>
                </select>
                <button class="primary" type="submit">Filtrele</button>
              </form>
              <div class="table-shell">
                <table class="holds-table">
                  <thead><tr><th>Ac</th><th>Hold</th><th>Durum</th><th>Rezervasyon Ozeti</th><th>Zaman</th><th>Teknik Durum</th></tr></thead>
                  <tbody id="holdTableBody"></tbody>
                </table>
              </div>
            </article>
            <article id="holdDetail" class="module-card">
              <div class="empty-state"><p>Detay ve aksiyonlar icin listeden bir hold secin.</p></div>
            </article>
          </div>
        </section>

        <section data-view="tickets" class="section-grid" hidden>
          <article class="module-card">
            <div class="module-header">
              <div><h3>Ticket Takibi</h3><p>Sahiplik ve kapanış durumunu kaybetmeden ekip akışına müdahale edin.</p></div>
            </div>
            <form id="ticketFilters" class="toolbar">
              <select name="status" aria-label="Ticket durumu">
                <option value="">Tum statuler</option>
                <option value="OPEN">OPEN</option>
                <option value="IN_PROGRESS">IN_PROGRESS</option>
                <option value="RESOLVED">RESOLVED</option>
                <option value="CLOSED">CLOSED</option>
              </select>
              <select name="priority" aria-label="Ticket onceligi">
                <option value="">Tum oncelikler</option>
                <option value="high">high</option>
                <option value="medium">medium</option>
                <option value="low">low</option>
              </select>
              <button class="primary" type="submit">Filtrele</button>
            </form>
            <div class="table-shell">
              <table>
                <thead><tr><th>Ticket</th><th>Oncelik</th><th>Durum</th><th>Sahiplik</th><th>Zaman</th><th>Ozet</th><th>Aksiyon</th></tr></thead>
                <tbody id="ticketTableBody"></tbody>
              </table>
            </div>
          </article>
        </section>

        <section data-view="hotels" class="section-grid" hidden>
          <article class="module-card">
            <div class="module-header">
              <div><h3>Hotel Profile Editor</h3><p>Panelden guncellenen veri YAML kaynagina yazilir ve runtime cache yenilenir.</p></div>
              <div class="module-actions">
                <select id="hotelProfileSelect" class="sidebar-select min-w-select" aria-label="Hotel profile secimi"></select>
                <button id="saveHotelProfile" class="inline-button primary" type="button">Profile Kaydet</button>
              </div>
            </div>
            <div id="hotelProfileMeta" class="helper-panel mb-md"></div>
            <div class="field full">
              <label for="hotelProfileEditor">profile_json</label>
              <textarea id="hotelProfileEditor"></textarea>
            </div>
          </article>
        </section>

        <section data-view="faq" class="section-grid" hidden>
          <div class="split">
            <article class="module-card">
              <div class="module-header">
                <div><h3>FAQ Kayitlari</h3><p>Sadece aktif kayitlar cevap motorunda kullanilir. Uygunsuz icerikleri aninda kaldirin.</p></div>
              </div>
              <form id="faqFilters" class="toolbar">
                <select name="status" aria-label="FAQ durumu">
                  <option value="">Tum durumlar</option>
                  <option value="DRAFT">DRAFT</option>
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="PAUSED">PAUSED</option>
                  <option value="REMOVED">REMOVED</option>
                </select>
                <input name="q" placeholder="Konu, soru veya cevap ara" aria-label="FAQ arama metni">
                <button class="primary" type="submit">Filtrele</button>
              </form>
              <div class="table-shell">
                <table>
                  <thead><tr><th>Konu</th><th>Durum</th><th>Soru/Ozet</th><th>Cevap/Ozet</th><th>Aksiyon</th></tr></thead>
                  <tbody id="faqTableBody"></tbody>
                </table>
              </div>
            </article>
            <article id="faqDetail" class="module-card">
              <div class="empty-state"><p>Detay için listeden bir FAQ kaydı seçin.</p></div>
            </article>
          </div>
        </section>

        <section data-view="restaurant" class="section-grid" hidden>
          <article class="module-card">
            <div class="module-header">
              <div><h3>Slot Yonetimi</h3><p>Kapasiteyi tarih ve saat bazli tut, dar ekranda bile kritik kolonlari kaybetme.</p></div>
            </div>
            <form id="slotFilters" class="toolbar">
              <input name="date_from" type="date" aria-label="Slot baslangic tarihi">
              <input name="date_to" type="date" aria-label="Slot bitis tarihi">
              <button id="loadSlotsButton" class="primary" type="button" aria-label="Slotlari getir">Slotlari Getir</button>
            </form>
            <div class="table-shell">
              <table>
                <thead><tr><th>ID</th><th>Tarih</th><th>Saat</th><th>Alan</th><th>Kapasite</th><th>Durum</th><th>Aksiyon</th></tr></thead>
                <tbody id="slotTableBody"></tbody>
              </table>
            </div>
          </article>

          <article class="module-card">
            <div class="module-header">
              <div><h3>Yeni Slot Araligi</h3><p>Toplu kapasite acmak icin tarih araligini tek formdan olusturun.</p></div>
            </div>
            <form id="slotCreateForm" class="dense-form">
              <div class="field"><label>Tarih baslangic</label><input name="date_from" type="date" required aria-label="Yeni slot baslangic tarihi"></div>
              <div class="field"><label>Tarih bitis</label><input name="date_to" type="date" required aria-label="Yeni slot bitis tarihi"></div>
              <div class="field"><label>Saat</label><input name="time" type="time" required aria-label="Yeni slot saati"></div>
              <div class="field"><label>Alan</label><select name="area" aria-label="Yeni slot alani"><option value="outdoor">outdoor</option><option value="indoor">indoor</option></select></div>
              <div class="field"><label>Toplam kapasite</label><input name="total_capacity" type="number" min="1" required aria-label="Yeni slot toplam kapasitesi"></div>
              <div class="field"><label>Aktif</label><input name="is_active" type="checkbox" checked class="checkbox-field" aria-label="Yeni slot aktif mi"></div>
              <div class="field full"><button class="inline-button primary" type="submit">Slot Araligi Olustur</button></div>
            </form>
          </article>
        </section>

        <section data-view="notifications" class="section-grid" hidden>
          <article class="module-card">
            <div class="module-header">
              <div><h3>Bildirim Numaralari</h3><p>Rezervasyon onay talebi olusturuldugunda WhatsApp mesaji gonderilecek admin numaralari. Varsayilan numara kaldirilAmaz.</p></div>
            </div>
            <div class="table-shell">
              <table>
                <thead><tr><th>Telefon</th><th>Etiket</th><th>Varsayilan</th><th>Aksiyon</th></tr></thead>
                <tbody id="notifPhoneTableBody"></tbody>
              </table>
            </div>
            <form id="addNotifPhoneForm" class="dense-form mt-lg">
              <div class="field"><label>Telefon numarasi</label><input name="phone" placeholder="+905XXXXXXXXX" required aria-label="Bildirim telefon numarasi"></div>
              <div class="field"><label>Etiket (opsiyonel)</label><input name="label" placeholder="Orn: Satis muduru" aria-label="Bildirim etiketi"></div>
              <div class="field full"><button class="inline-button primary" type="submit">Numara Ekle</button></div>
            </form>
          </article>
        </section>

        <section data-view="system" class="section-grid" hidden>
          <div class="split">
            <article class="module-card">
              <div class="module-header">
                <div><h3>Sistem Kontrolleri</h3><p>Readiness, domain ve bootstrap guvenlik durumu ayni ekranda gorunur kalir.</p></div>
              </div>
              <div id="systemMeta" class="helper-panel mb-md"></div>
              <div id="systemChecks" class="status-list"></div>
            </article>

            <article class="module-card">
              <div class="module-header">
                <div><h3>Guvenlik ve Oturum</h3><p>Sik giris yapan ekipler icin dogrulama tekrari ve cihaz hatirlama suresini buradan yonetin.</p></div>
              </div>
              <div id="sessionSummary" class="helper-panel mb-md"></div>
              <form id="sessionPreferencesForm" class="field-grid">
                <div class="field full">
                  <label class="toggle-row" for="sessionRememberToggle">
                    <span class="toggle-copy">
                      <strong>Bu cihazi panel icin hatirla</strong>
                      <small>Kayitli cihazlarda giris adimlarini kisaltir; ayar degisikligi icin 6 haneli kod gerekir.</small>
                    </span>
                    <span class="switch">
                      <input id="sessionRememberToggle" name="remember_device" type="checkbox">
                      <span class="switch-track"><span class="switch-thumb"></span></span>
                    </span>
                  </label>
                </div>
                <div id="sessionPreferenceFields" class="field full">
                  <div class="session-stack">
                    <div>
                      <label>Google dogrulama tekrari</label>
                      <div id="systemVerificationOptions" class="choice-group"></div>
                    </div>
                    <div>
                      <label>Oturum / hatirlama suresi</label>
                      <div id="systemSessionOptions" class="choice-group"></div>
                    </div>
                  </div>
                </div>
                <div id="sessionOtpField" class="field full">
                  <label for="session-otp-code">Google Authenticator kodu</label>
                  <input id="session-otp-code" name="otp_code" inputmode="numeric" pattern="[0-9]*" placeholder="Tercihleri kaydetmek icin 6 haneli kod">
                </div>
                <div class="field full">
                  <button class="inline-button primary" type="submit">Oturum Tercihlerini Kaydet</button>
                </div>
              </form>
              <div id="trustedDevicePanel" class="helper-panel mt-md"></div>
              <div class="module-actions mt-md">
                <button id="forgetDeviceButton" class="inline-button danger" type="button">Bu Cihazi Unut</button>
              </div>
            </article>
          </div>
        </section>

        <section data-view="chatlab" class="section-grid" hidden>
          <iframe id="chatlab-frame" class="chatlab-frame"></iframe>
        </section>
      </section>
    </main>
  </div>

  <dialog id="decisionDialog" class="dialog">
    <div class="dialog-card">
      <div class="dialog-head">
        <h3 id="decisionTitle">Aksiyon</h3>
        <p id="decisionLead">Gerekce girin.</p>
      </div>
      <form id="decisionForm" class="field">
        <input id="decisionHoldId" type="hidden">
        <input id="decisionMode" type="hidden">
        <label for="decisionReason">Gerekce</label>
        <textarea id="decisionReason" required class="dialog-textarea" aria-label="Red gerekcesi"></textarea>
        <div class="dialog-actions">
          <button id="closeDecision" class="inline-button secondary" type="button">Vazgec</button>
          <button class="inline-button danger" type="submit">Reddi Uygula</button>
        </div>
      </form>
    </div>
  </dialog>

  <script>window.ADMIN_PANEL_CONFIG = {config_json};</script>
  <script>{ADMIN_PANEL_SCRIPT}</script>
</body>
</html>
"""


if ADMIN_PANEL_ROUTE == "/admin":

    @router.get("/admin", response_class=HTMLResponse)
    async def admin_panel_ui() -> HTMLResponse:
        """Serve the standalone admin panel HTML."""
        return HTMLResponse(content=render_admin_panel_html())

else:

    @router.get(ADMIN_PANEL_ROUTE, response_class=HTMLResponse)
    async def admin_panel_ui() -> HTMLResponse:
        """Serve the standalone admin panel HTML using configured path."""
        return HTMLResponse(content=render_admin_panel_html())

    @router.get("/admin", response_class=HTMLResponse, include_in_schema=False)
    async def admin_panel_ui_legacy() -> HTMLResponse:
        """Serve admin UI on legacy path for compatibility during cutover."""
        return HTMLResponse(content=render_admin_panel_html())
