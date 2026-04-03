"""HTML route for the unified admin operations panel."""

from __future__ import annotations

# ruff: noqa: E501
import json

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse

from velox.api.routes.admin_panel_holds_assets import ADMIN_HOLDS_SCRIPT, ADMIN_HOLDS_STYLE
from velox.api.routes.admin_panel_restaurant_assets import ADMIN_RESTAURANT_SCRIPT, ADMIN_RESTAURANT_STYLE
from velox.api.routes.admin_panel_ui_assets import ADMIN_PANEL_SCRIPT, ADMIN_PANEL_STYLE
from velox.config.settings import settings

router = APIRouter(tags=["admin-panel-ui"])
ADMIN_PANEL_ROUTE = settings.admin_panel_path if settings.admin_panel_path.startswith("/") else f"/{settings.admin_panel_path}"
ADMIN_UI_NO_STORE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}


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
  <title>NexlumeAI Yönetim Paneli</title>
  <style>{ADMIN_PANEL_STYLE}
{ADMIN_HOLDS_STYLE}
{ADMIN_RESTAURANT_STYLE}</style>
</head>
<body>
  <div id="toast" class="toast info" role="status" aria-live="polite"></div>
  <div class="shell">
    <aside id="sidebar" class="sidebar" hidden>
      <div class="brand">
        <div class="brand-mark">NX</div>
        <div>
          <h1>NexlumeAI<br>Admin</h1>
          <p>Misafir konuşmaları, onaylar ve otel ayarları tek yerden yönetilir.</p>
        </div>
      </div>

      <nav id="nav" class="nav" aria-label="Yönetim paneli gezinmesi">
        <button data-nav="dashboard"><span class="nav-label"><strong>Genel Bakış</strong><span>Anlık durum özeti</span></span><span>01</span></button>
        <button data-nav="conversations"><span class="nav-label"><strong>Konuşmalar</strong><span>Misafir mesajları ve geçmiş</span></span><span>02</span></button>
        <button data-nav="holds"><span class="nav-label"><strong>Onay Bekleyenler</strong><span>Rezervasyon onay ve red islemleri</span></span><span>03</span></button>
        <button data-nav="tickets"><span class="nav-label"><strong>Destek Talepleri</strong><span>Ekibe aktarılan görevler</span></span><span>04</span></button>
        <button data-nav="hotels"><span class="nav-label"><strong>Otel Bilgileri</strong><span>Otel profili ve ayarları</span></span><span>05</span></button>
        <button data-nav="faq"><span class="nav-label"><strong>Sık Sorulan Sorular</strong><span>Hazır yanıt yönetimi</span></span><span>06</span></button>
        <button data-nav="restaurant"><span class="nav-label"><strong>Restoran Yönetimi</strong><span>Masa ve kapasite ayarları</span></span><span>07</span></button>
        <button data-nav="notifications"><span class="nav-label"><strong>Bildirim Ayarları</strong><span>WhatsApp bildirim numaraları</span></span><span>08</span></button>
        <button data-nav="system"><span class="nav-label"><strong>Sistem Durumu</strong><span>Sunucu ve bağlantı kontrolleri</span></span><span>09</span></button>
        <button data-nav="chatlab"><span class="nav-label"><strong>Test Paneli</strong><span>Canlı test ve değerlendirme</span></span><span>10</span></button>
      </nav>

      <section class="sidebar-card">
        <h2>Kimlik</h2>
        <p id="currentUser">Panel girişi bekleniyor</p>
        <small id="currentRole">-</small>
      </section>

      <section class="sidebar-card">
        <h2>Kapsam</h2>
        <label for="hotelSelect">Otel</label>
        <select id="hotelSelect" class="sidebar-select"></select>
        <p class="mt-sm">Aktif kapsam: <strong id="hotelScope">-</strong></p>
      </section>

      <section class="sidebar-card">
        <h2>Kontroller</h2>
        <div class="sidebar-actions">
          <button id="reloadButton" class="sidebar-button warn" type="button">Yapılandırmayı Yenile</button>
          <button id="logoutButton" class="sidebar-button secondary" type="button">Çıkış Yap</button>
        </div>
      </section>
    </aside>

    <main class="workspace">
      <header id="topbar" class="topbar" hidden>
        <div>
          <div class="badge dark">NexlumeAI Yönetim Paneli</div>
          <h2 id="pageTitle">Genel Bakış</h2>
          <p id="pageLead">Aktif konuşmaları, bekleyen onayları ve açık talepleri tek ekranda görüntüleyin.</p>
        </div>
        <div class="topbar-actions">
          <button id="sidebarToggle" class="sidebar-toggle" type="button" aria-label="Gezinme menüsü" aria-expanded="false">Menü</button>
          <div class="topbar-aside">
            <div class="badge info">Merkezi yönetim</div>
            <div class="badge warn">Onay gerektiren işlemler görünür</div>
          </div>
        </div>
      </header>

      <section id="authView" class="panel">
        <div class="auth-grid">
          <article class="auth-card">
            <h3>Panel Girişi</h3>
            <p>Kullanıcı adı, şifre ve Google Authenticator kodu ile giriş yapın. Tanımlı cihazlarda kod adımı atlanabilir.</p>
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
                    <strong>Bu cihazı hatırla</strong>
                    <small>Aynı cihazda tekrar girişlerde Google doğrulamasını azaltır.</small>
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
                    <label>Doğrulama tekrarı</label>
                    <div id="loginVerificationOptions" class="choice-group"></div>
                  </div>
                  <div>
                    <label>Oturum hatırlama</label>
                    <div id="loginSessionOptions" class="choice-group"></div>
                  </div>
                  <p class="helper">Paylaşılan cihazlarda bu seçeneği kapalı tutun.</p>
                </div>
              </div>
              <div class="field full">
                <button class="sidebar-button primary" type="submit">Oturum Aç</button>
              </div>
            </form>
          </article>

          <article id="bootstrapCard" class="auth-card">
            <h3>İlk Kurulum</h3>
            <p>Henüz yönetici hesabı yoksa buradan ilk hesabı oluşturun ve Google Authenticator'ı bağlayın.</p>
            <div id="bootstrapSummary" class="helper-panel"></div>
            <form id="bootstrapForm" class="field-grid mt-md" method="post">
              <div class="field">
                <label for="bootstrap-hotel">Otel</label>
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
                <p>Hesap var ancak Google Authenticator kurulumu kaybolduysa, kurulum anahtarı ile yeni QR kodu üretebilirsiniz.</p>
              </div>
              <form id="totpRecoveryForm" class="field-grid" method="post">
                <div class="field">
                  <label for="recovery-username">Kullanıcı adı</label>
                  <input id="recovery-username" name="username" required>
                </div>
                <div class="field">
                  <label for="recovery-token">Bootstrap token</label>
                  <input id="recovery-token" name="bootstrap_token" required>
                </div>
                <div class="field full">
                <label for="recovery-password">Yeni şifre (isteğe bağlı)</label>
                  <input id="recovery-password" name="new_password" type="password" minlength="12" maxlength="72" placeholder="Boş bırakırsanız mevcut şifre korunur">
                </div>
                <div class="field full">
                  <button class="sidebar-button warn" type="submit">2FA QR Kodunu Yenile</button>
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
                <label class="toolbar-check"><input name="active_only" type="checkbox" checked> Sadece aktif</label>
                <select name="status" aria-label="Konuşma durumu">
                  <option value="">Tüm durumlar</option>
                  <option value="GREETING">Karşılama</option>
                  <option value="PENDING_APPROVAL">Onay Bekliyor</option>
                  <option value="CONFIRMED">Onaylandı</option>
                  <option value="HANDOFF">İnsan Devrinde</option>
                </select>
                <input name="date_from" type="date" aria-label="Başlangıç tarihi">
                <input name="date_to" type="date" aria-label="Bitiş tarihi">
                <button class="primary" type="submit">Filtrele</button>
              </form>
              <div class="table-shell">
                <table>
                  <thead><tr><th>Kullanıcı</th><th>Durum</th><th>Niyet</th><th>Risk</th><th>Mesaj</th><th>İşlem</th></tr></thead>
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
          <div class="holds-tabs">
            <button class="holds-tab is-active" data-holds-tab="stay">Konaklama</button>
            <button class="holds-tab" data-holds-tab="transfer">Transfer</button>
          </div>

          <div data-holds-panel="stay" class="holds-panel">
            <div class="split">
              <article class="module-card">
                <div class="module-header">
                  <div><h3>Konaklama Talepleri</h3><p>Otel rezervasyon onay, red ve takip işlemleri.</p></div>
                  <button class="inline-button primary" data-stay-toggle-create aria-label="Yeni konaklama rezervasyonu oluştur">Yeni Rezervasyon</button>
                </div>
                <form id="stayHoldFilters" class="toolbar">
                  <div class="filter-chips" id="stayStatusChips"></div>
                  <input name="reservation_no" placeholder="Rez. No ile ara" aria-label="Rezervasyon numarası araması">
                  <button class="primary" type="submit">Ara</button>
                </form>
                <div class="table-shell">
                  <table class="holds-table"><thead><tr>
                    <th>Aç</th><th>Rez. No</th><th>Hold</th><th>Durum</th><th>Misafir</th><th>Tarih</th><th>Tutar</th>
                  </tr></thead><tbody id="stayHoldTableBody"></tbody></table>
                </div>
              </article>
              <article id="stayHoldDetail" class="module-card">
                <div class="empty-state"><p>Ayrıntıları görmek için listeden bir kayıt seçin.</p></div>
              </article>
            </div>
            <article id="stayHoldCreatePanel" class="module-card" hidden>
              <div class="module-header">
                <div><h3>Konaklama Rezervasyonu Oluştur</h3><p>Bilgileri adım adım girin.</p></div>
                <button class="inline-button secondary" data-stay-toggle-create>Kapat</button>
              </div>
              <div class="wizard-steps" id="stayWizardSteps"></div>
              <div id="stayWizardBody" class="wizard-body"></div>
            </article>
          </div>

          <div data-holds-panel="restaurant" class="holds-panel" hidden>
            <div class="split">
              <article class="module-card">
                <div class="module-header">
                  <div><h3>Restoran Talepleri</h3><p>Restoran rezervasyon onay ve red işlemleri.</p></div>
                  <div class="stack" style="align-items:flex-end;gap:8px;">
                    <div class="filter-chips" aria-label="Restoran mod seçimi">
                      <button class="filter-chip is-active" id="restaurantModeAiLegacy" type="button">Yapay Zekâ Restoran</button>
                      <button class="filter-chip" id="restaurantModeManualLegacy" type="button">Manuel</button>
                    </div>
                    <button class="inline-button primary" data-action="toggle-restaurant-create" data-restaurant-toggle-create aria-label="Yeni restoran rezervasyonu oluştur">Yeni Rezervasyon</button>
                  </div>
                </div>
                <form id="restaurantHoldFiltersLegacy" class="toolbar">
                  <div class="filter-chips" id="restaurantStatusChipsLegacy"></div>
                  <button class="primary" type="submit">Filtrele</button>
                </form>
                <div class="table-shell">
                  <table class="holds-table"><thead><tr>
                    <th>Aç</th><th>Hold</th><th>Durum</th><th>Misafir</th><th>Tarih/Saat</th><th>Kişi</th>
                  </tr></thead><tbody id="restaurantHoldTableBodyLegacy"></tbody></table>
                </div>
              </article>
              <article id="restaurantHoldDetailLegacy" class="module-card">
                <div class="empty-state"><p>Ayrıntıları görmek için listeden bir kayıt seçin.</p></div>
              </article>
            </div>
            <article id="restaurantHoldCreatePanelLegacy" class="module-card" hidden>
              <div class="module-header">
                <div><h3>Restoran Rezervasyonu Oluştur</h3><p>Bilgileri girin.</p></div>
                <button class="inline-button secondary" data-restaurant-toggle-create>Kapat</button>
              </div>
              <form id="restaurantCreateFormLegacy" class="field-grid">
                <div class="field"><label for="rc-date">Tarih</label><input id="rc-date" name="date" type="date" required></div>
                <div class="field"><label for="rc-time">Saat</label><input id="rc-time" name="time" type="time" required></div>
                <div class="field"><label for="rc-guest">Misafir Adı</label><input id="rc-guest" name="guest_name" required></div>
                <div class="field"><label for="rc-pax">Kişi Sayısı</label><input id="rc-pax" name="pax" type="number" min="1" required></div>
                <div class="field"><label for="rc-phone">Telefon</label><input id="rc-phone" name="phone" placeholder="+905XXXXXXXXX" required></div>
                <div class="field"><label for="rc-area">Alan</label><select id="rc-area" name="area"><option value="outdoor">Dış Mekân</option><option value="indoor">İç Mekân</option></select></div>
                <div class="field full"><label for="rc-notes">Notlar</label><textarea id="rc-notes" name="notes" style="min-height:80px"></textarea></div>
                <div class="field full"><button class="inline-button primary" type="submit">Restoran Rezervasyonu Oluştur</button></div>
              </form>
            </article>
          </div>

          <div data-holds-panel="transfer" class="holds-panel" hidden>
            <div class="split">
              <article class="module-card">
                <div class="module-header">
                  <div><h3>Transfer Talepleri</h3><p>Transfer onay ve red işlemleri.</p></div>
                  <button class="inline-button primary" data-transfer-toggle-create aria-label="Yeni transfer talebi oluştur">Yeni Transfer</button>
                </div>
                <form id="transferHoldFilters" class="toolbar">
                  <div class="filter-chips" id="transferStatusChips"></div>
                  <button class="primary" type="submit">Filtrele</button>
                </form>
                <div class="table-shell">
                  <table class="holds-table"><thead><tr>
                    <th>Aç</th><th>Hold</th><th>Durum</th><th>Misafir</th><th>Güzergâh</th><th>Tarih</th>
                  </tr></thead><tbody id="transferHoldTableBody"></tbody></table>
                </div>
              </article>
              <article id="transferHoldDetail" class="module-card">
                <div class="empty-state"><p>Ayrıntıları görmek için listeden bir kayıt seçin.</p></div>
              </article>
            </div>
            <article id="transferHoldCreatePanel" class="module-card" hidden>
              <div class="module-header">
                <div><h3>Transfer Talebi Oluştur</h3><p>Bilgileri girin.</p></div>
                <button class="inline-button secondary" data-transfer-toggle-create>Kapat</button>
              </div>
              <form id="transferCreateForm" class="field-grid">
                <div class="field"><label for="tc-date">Tarih</label><input id="tc-date" name="date" type="date" required></div>
                <div class="field"><label for="tc-time">Saat</label><input id="tc-time" name="time" type="time" required></div>
                <div class="field"><label for="tc-guest">Misafir Adı</label><input id="tc-guest" name="guest_name" required></div>
                <div class="field"><label for="tc-pax">Kişi Sayısı</label><input id="tc-pax" name="pax" type="number" min="1" required></div>
                <div class="field"><label for="tc-phone">Telefon</label><input id="tc-phone" name="phone" placeholder="+905XXXXXXXXX" required></div>
                <div class="field"><label for="tc-from">Kalkış</label><input id="tc-from" name="pickup_location" required></div>
                <div class="field"><label for="tc-to">Varış</label><input id="tc-to" name="dropoff_location" required></div>
                <div class="field full"><label for="tc-notes">Notlar</label><textarea id="tc-notes" name="notes" style="min-height:80px"></textarea></div>
                <div class="field full"><button class="inline-button primary" type="submit">Transfer Talebi Oluştur</button></div>
              </form>
            </article>
          </div>
        </section>

        <section data-view="tickets" class="section-grid" hidden>
          <article class="module-card">
            <div class="module-header">
              <div><h3>Talep Takibi</h3><p>Sahiplik ve kapanış durumunu kaybetmeden ekip akışına müdahale edin.</p></div>
            </div>
            <form id="ticketFilters" class="toolbar">
              <select name="status" aria-label="Talep durumu">
                <option value="">Tüm statüler</option>
                <option value="OPEN">Açık</option>
                <option value="IN_PROGRESS">İşlemde</option>
                <option value="RESOLVED">Çözüldü</option>
                <option value="CLOSED">Kapalı</option>
              </select>
              <select name="priority" aria-label="Talep önceliği">
                <option value="">Tüm öncelikler</option>
                <option value="high">Yüksek</option>
                <option value="medium">Orta</option>
                <option value="low">Düşük</option>
              </select>
              <button class="primary" type="submit">Filtrele</button>
            </form>
            <div class="table-shell">
              <table>
                <thead><tr><th>Talep</th><th>Öncelik</th><th>Durum</th><th>Sahiplik</th><th>Zaman</th><th>Özet</th><th>İşlem</th></tr></thead>
                <tbody id="ticketTableBody"></tbody>
              </table>
            </div>
          </article>
        </section>

        <section data-view="hotels" class="section-grid" hidden>
          <article class="module-card">
            <div class="module-header">
              <div><h3>Otel Profil Düzenleyicisi</h3><p>Taslağı kaydedebilir, ardından değişiklikleri yayına alabilirsiniz. Misafirler yalnızca yayımlanmış son sürümü görür.</p></div>
              <div class="module-actions">
                <select id="hotelProfileSelect" class="sidebar-select min-w-select" aria-label="Otel profili seçimi"></select>
                <button id="saveHotelProfile" class="inline-button primary" type="button">Taslağı Kaydet</button>
                <button id="publishHotelFacts" class="inline-button secondary" type="button">Değişiklikleri Yayına Al</button>
              </div>
            </div>
            <div id="hotelProfileMeta" class="helper-panel mb-md"></div>
            <div id="hotelFactsConflict" class="helper-panel mb-md"></div>
            <div id="hotelFactsStatus" class="helper-panel mb-md"></div>
            <div id="hotelFactsHistory" class="helper-panel mb-md"></div>
            <div id="hotelFactsEvents" class="helper-panel mb-md"></div>
            <div id="hotelFactsVersionDetail" class="helper-panel mb-md"></div>
            <div id="hotelProfileSections" class="helper-panel mb-md"></div>
            <div id="hotelProfileSectionBody" class="helper-panel mb-md"></div>
            <details class="helper-box" data-advanced-mode="hotel-profile-json">
              <summary><strong>Teknik Düzenleme • Ham JSON</strong></summary>
              <p class="muted mt-sm">Bu panel varsayılan olarak kapalıdır. Teknik eşleştirme, geri kazanım ve ileri düzey düzenlemeler için kullanılır; günlük kullanımda bölüm sekmelerini tercih edin.</p>
              <div class="module-actions mt-sm">
                <button id="applyHotelProfileJson" class="action-button secondary" type="button">JSON'u Forma Aktar</button>
              </div>
              <div class="field full mt-md">
                <label for="hotelProfileEditor">Profil JSON'u</label>
                <textarea id="hotelProfileEditor"></textarea>
              </div>
            </details>
          </article>
        </section>

        <section data-view="faq" class="section-grid" hidden>
          <div class="split">
            <article class="module-card">
              <div class="module-header">
                <div><h3>SSS Kayıtları</h3><p>Yalnızca aktif kayıtlar yanıt motorunda kullanılır. Uygunsuz içerikleri hemen kaldırın.</p></div>
              </div>
              <form id="faqFilters" class="toolbar">
                <select name="status" aria-label="SSS durumu">
                  <option value="">Tüm durumlar</option>
                  <option value="DRAFT">Taslak</option>
                  <option value="ACTIVE">Aktif</option>
                  <option value="PAUSED">Duraklatıldı</option>
                  <option value="REMOVED">Kaldırıldı</option>
                </select>
                <input name="q" placeholder="Konu, soru veya cevap ara" aria-label="SSS arama metni">
                <button class="primary" type="submit">Filtrele</button>
              </form>
              <div class="table-shell">
                <table>
                  <thead><tr><th>Konu</th><th>Durum</th><th>Soru Özeti</th><th>Cevap Özeti</th><th>İşlem</th></tr></thead>
                  <tbody id="faqTableBody"></tbody>
                </table>
              </div>
            </article>
            <article id="faqDetail" class="module-card">
              <div class="empty-state"><p>Ayrıntıları görmek için listeden bir SSS kaydı seçin.</p></div>
            </article>
          </div>
        </section>

        <section data-view="restaurant" class="section-grid" hidden>
          <article class="module-card">
            <div class="module-header">
              <div><h3>Slot Yönetimi</h3><p>Kapasiteyi tarih ve rezervasyon saati bazında takip edin, kalan kapasiteyi görsel olarak izleyin.</p></div>
              <div class="stack" style="align-items:flex-end;gap:8px;">
                <button id="openServiceModeBtn" class="inline-button primary" type="button" aria-label="Servis modunu aç" onclick="window.__veloxOpenServiceMode && window.__veloxOpenServiceMode()">Servis Modu</button>
              </div>
            </div>
            <form id="slotFilters" class="toolbar">
              <input name="date_from" type="date" aria-label="Slot başlangıç tarihi">
              <input name="date_to" type="date" aria-label="Slot bitiş tarihi">
              <select name="display_interval" id="slotDisplayInterval" aria-label="Slot gösterim aralığı">
                <option value="1m">Her 1 dakika</option>
                <option value="1h">Her 1 saat</option>
                <option value="2h">Her 2 saat</option>
                <option value="1d" selected>Her gün</option>
                <option value="3d">Her 3 gün</option>
                <option value="1w">Her hafta</option>
                <option value="15d">Her 15 gün</option>
                <option value="30d">Her 30 gün</option>
                <option value="2mo">Her 2 ay</option>
              </select>
              <button id="loadSlotsButton" class="primary" type="button" aria-label="Slotları getir">Slotları Getir</button>
            </form>
            <div class="toolbar" style="margin-top:-4px">
              <button id="hideSlotsButton" class="inline-button secondary" type="button" aria-label="Slotları kapat">Slotları Kapat</button>
            </div>
            <div id="slotSummaryCards" class="split"></div>
            <div class="table-shell">
              <table>
                <thead><tr><th>ID</th><th>Tarih</th><th>Rezervasyon Saati</th><th>Alan</th><th>Kalan Slot</th><th>Durum</th><th>İşlem</th></tr></thead>
                <tbody id="slotTableBody"></tbody>
              </table>
            </div>
          </article>

          <article class="module-card">
            <div class="module-header">
              <div><h3>Toplu Slot Temizleme</h3><p>Seçilen tarih ve saat aralığındaki slot kayıtlarını tek seferde silin. Başlangıç ve bitiş saatine denk gelen slotlar da dahildir.</p></div>
            </div>
            <form id="slotDeleteForm" class="dense-form">
              <div class="field"><label>Tarih başlangıcı</label><input name="date_from" type="date" required aria-label="Silme başlangıç tarihi"></div>
              <div class="field"><label>Tarih bitişi</label><input name="date_to" type="date" required aria-label="Silme bitiş tarihi"></div>
              <div class="field"><label>Başlangıç saati</label><input name="start_time" type="time" required aria-label="Silme başlangıç saati"></div>
              <div class="field"><label>Bitiş saati</label><input name="end_time" type="time" required aria-label="Silme bitiş saati"></div>
              <div class="field full">
                <label>Haftanın günleri</label>
                <div class="checkbox-group" id="slotDeleteWeekdays">
                  <label><input type="checkbox" name="weekdays" value="0"> Pzt</label>
                  <label><input type="checkbox" name="weekdays" value="1"> Sal</label>
                  <label><input type="checkbox" name="weekdays" value="2"> Çar</label>
                  <label><input type="checkbox" name="weekdays" value="3"> Per</label>
                  <label><input type="checkbox" name="weekdays" value="4"> Cum</label>
                  <label><input type="checkbox" name="weekdays" value="5"> Cmt</label>
                  <label><input type="checkbox" name="weekdays" value="6"> Paz</label>
                </div>
                <small>Seçmezseniz tüm günlerde uygular.</small>
              </div>
              <div class="field full"><button class="inline-button danger" type="submit">Seçili Aralıktaki Slotları Temizle</button></div>
            </form>
          </article>

          <article class="module-card">
            <div class="module-header">
              <div><h3>Tarihler Arası Kapasite</h3><p>Seçilen tarih aralığında başlangıç ve bitiş saatleri arasındaki tüm dakikalar için rezervasyon kapasitesi oluşturur.</p></div>
            </div>
            <form id="slotCreateForm" class="dense-form">
              <div class="field"><label>Tarih başlangıcı</label><input name="date_from" type="date" required aria-label="Kapasite başlangıç tarihi"></div>
              <div class="field"><label>Tarih bitişi</label><input name="date_to" type="date" required aria-label="Kapasite bitiş tarihi"></div>
              <div class="field"><label>Başlangıç saati</label><input name="start_time" type="time" required aria-label="Kapasite başlangıç saati"></div>
              <div class="field"><label>Bitiş saati</label><input name="end_time" type="time" required aria-label="Kapasite bitiş saati"></div>
              <div class="field"><label>Toplam rezervasyon sayısı</label><input name="reservation_limit" type="number" min="1" required aria-label="Pencere toplam rezervasyon limiti"></div>
              <div class="field"><label>Toplam kişi sayısı limiti</label><input name="total_party_size_limit" type="number" min="1" required aria-label="Pencere toplam kişi sayısı limiti"></div>
              <div class="field"><label>Min. kişi sayısı</label><input name="min_party_size" type="number" min="1" value="1" required aria-label="Minimum kişi sayısı"></div>
              <div class="field"><label>Maks. kişi sayısı</label><input name="max_party_size" type="number" min="1" value="8" required aria-label="Maksimum kişi sayısı"></div>
              <div class="field"><label>Misafire açık mı?</label><input name="is_active" type="checkbox" checked class="checkbox-field" aria-label="Slot aktif mi"></div>
              <div class="field full"><button class="inline-button primary" type="submit">Tarihler Arası Kapasite Oluştur</button></div>
            </form>
          </article>

          <article class="module-card" id="restaurantSettingsCard">
            <div class="module-header">
              <div><h3>Kapasite Ayarları</h3><p>Günlük maksimum rezervasyon sayısını ve kabul edilen kişi aralığını yönetin.</p></div>
            </div>
            <form id="restaurantSettingsForm" class="dense-form">
              <div class="field">
                <label>Günlük limit aktif</label>
                <label class="toggle-switch"><input type="checkbox" id="dailyCapToggle" name="daily_max_reservations_enabled" aria-label="Günlük kapasite limiti"><span class="toggle-slider"></span></label>
              </div>
              <div class="field">
                <label>Maks. günlük rezervasyon</label>
                <input name="daily_max_reservations_count" type="number" min="1" value="50" id="dailyCapCount" aria-label="Günlük maksimum rezervasyon sayısı">
              </div>
              <div class="field">
                <label>Günlük kişi limiti aktif</label>
                <label class="toggle-switch"><input type="checkbox" id="dailyPartyCapToggle" name="daily_max_party_size_enabled" aria-label="Günlük kişi limiti"><span class="toggle-slider"></span></label>
              </div>
              <div class="field">
                <label>Maks. günlük toplam kişi</label>
                <input name="daily_max_party_size_count" type="number" min="1" value="200" id="dailyPartyCapCount" aria-label="Günlük maksimum toplam kişi sayısı">
              </div>
              <div class="field">
                <label>Min. kişi sayısı</label>
                <input name="min_party_size" type="number" min="1" value="1" id="restaurantMinPartySize" aria-label="Genel minimum kişi sayısı">
              </div>
              <div class="field">
                <label>Maks. kişi sayısı</label>
                <input name="max_party_size" type="number" min="1" value="8" id="restaurantMaxPartySize" aria-label="Genel maksimum kişi sayısı">
              </div>
              <div class="field">
                <label>Restoran şef numarası</label>
                <input name="chef_phone" type="tel" id="restaurantChefPhone" placeholder="+905XXXXXXXXX" aria-label="Restoran şef numarası">
              </div>
              <div class="field full"><button class="inline-button primary" type="submit">Kaydet</button></div>
            </form>
          </article>

          <div class="split">
            <article class="module-card">
              <div class="module-header">
                <div><h3>Restoran Talepleri</h3><p>Restoran rezervasyon onay, red ve manuel oluşturma işlemleri.</p></div>
                <div class="stack" style="align-items:flex-end;gap:8px;">
                  <div class="filter-chips" aria-label="Restoran mod seçimi">
                      <button class="filter-chip is-active" id="restaurantModeAi" type="button">Yapay Zekâ Restoran</button>
                    <button class="filter-chip" id="restaurantModeManual" type="button">Manuel</button>
                  </div>
                  <button class="inline-button primary" data-action="toggle-restaurant-create" data-restaurant-toggle-create aria-label="Yeni restoran rezervasyonu oluştur">Yeni Rezervasyon</button>
                </div>
              </div>
              <form id="restaurantHoldFilters" class="toolbar">
                <div class="filter-chips" id="restaurantStatusChips"></div>
                <input id="restaurantDateFrom" name="date_from" type="date" aria-label="Restoran talebi başlangıç tarihi">
                <input id="restaurantDateTo" name="date_to" type="date" aria-label="Restoran talebi bitiş tarihi">
                <button class="primary" type="submit">Filtrele</button>
              </form>
              <div class="table-shell">
                <table class="holds-table"><thead><tr>
                  <th>Aç</th><th>Hold</th><th>Durum</th><th>Misafir</th><th>Tarih/Saat</th><th>Kişi</th>
                </tr></thead><tbody id="restaurantHoldTableBody"></tbody></table>
              </div>
            </article>
            <article id="restaurantHoldDetail" class="module-card">
              <div class="empty-state"><p>Ayrıntıları görmek için listeden bir kayıt seçin.</p></div>
            </article>
          </div>
          <article id="restaurantHoldCreatePanel" class="module-card" hidden>
            <div class="module-header">
              <div><h3>Restoran Rezervasyonu Oluştur</h3><p>Bilgileri girin.</p></div>
              <button class="inline-button secondary" data-restaurant-toggle-create>Kapat</button>
            </div>
            <form id="restaurantCreateForm" class="field-grid">
              <div class="field"><label for="rc-date">Tarih</label><input id="rc-date" name="date" type="date" required></div>
              <div class="field"><label for="rc-time">Saat</label><input id="rc-time" name="time" type="time" required></div>
              <div class="field"><label for="rc-guest">Misafir Adı</label><input id="rc-guest" name="guest_name" required></div>
              <div class="field"><label for="rc-pax">Kişi Sayısı</label><input id="rc-pax" name="pax" type="number" min="1" required></div>
              <div class="field"><label for="rc-phone">Telefon</label><input id="rc-phone" name="phone" placeholder="+905XXXXXXXXX" required></div>
              <div class="field"><label for="rc-area">Alan</label><select id="rc-area" name="area"><option value="outdoor">Dış Mekân</option><option value="indoor">İç Mekân</option></select></div>
              <div class="field full"><label for="rc-notes">Notlar</label><textarea id="rc-notes" name="notes" style="min-height:80px"></textarea></div>
              <div class="field full"><button class="inline-button primary" type="submit">Restoran Rezervasyonu Oluştur</button></div>
            </form>
          </article>

          <article class="module-card" id="floorPlanEditorCard">
            <div class="module-header">
              <div data-ascii-hint="Duvarlari uzatip kisaltabilir"><h3>Restoran Plan Çizimi</h3><p>Masaları ve şekilleri sürükleyip bırakarak veya tıklayarak yerleştirin. Duvarları uzatıp kısaltabilir, tüm araçları döndürebilir, kopyalayabilir ve silebilirsiniz.</p></div>
              <div class="floor-plan-controls">
                <label class="field fp-plan-name-field" for="floorPlanNameInput">
                  <span>Plan Adı</span>
                  <input id="floorPlanNameInput" type="text" maxlength="80" placeholder="Örn. Ana Salon Akşam Düzeni" aria-label="Plan adı">
                </label>
                <label class="field fp-plan-list-field" for="floorPlanSelect">
                  <span>Kayıtlı Planlar</span>
                  <select id="floorPlanSelect" aria-label="Kayıtlı planlar"></select>
                </label>
                <button class="inline-button accent" id="createNewFloorPlanBtn" type="button" aria-label="Yeni plan oluştur">+ Yeni Plan</button>
                <button class="inline-button primary" id="saveFloorPlanBtn" type="button" aria-label="Planı kaydet">Kaydet</button>
                <button class="inline-button secondary" id="resetFloorPlanBtn" type="button" aria-label="Son kaydedilen hale dön">Sıfırla</button>
                <button class="fp-activate-btn" id="activateFloorPlanBtn" type="button" aria-label="Planı aktif yap" title="Bu planı aktif plan olarak ayarla">&#9733; Aktif Yap</button>
                <button class="fp-delete-btn" id="deleteFloorPlanBtn" type="button" aria-label="Planı sil" title="Kayıtlı planı sil">&#10005; Sil</button>
                <span class="fp-plan-status"><span class="fp-plan-dirty-indicator" id="fpDirtyDot" title="Kaydedilmemiş değişiklik var"></span><span id="fpPlanIdBadge" class="fp-plan-id-badge"></span></span>
              </div>
            </div>
            <div class="fp-plan-info-bar" id="fpPlanInfoBar">
              <span class="fp-plan-badge is-new" id="fpPlanBadge">Yeni Plan</span>
              <span class="fp-plan-date" id="fpPlanDate"></span>
              <span id="fpPlanTableCount"></span>
            </div>
            <div class="fp-toolbar">
              <button class="fp-tool-btn active" id="fpGridBtn" type="button" title="Izgarayı göster/gizle">&#9638; Izgara</button>
              <button class="fp-tool-btn" id="fpUndoBtn" type="button" title="Geri al (Ctrl+Z)">&#8630; Geri Al</button>
              <span class="fp-sep"></span>
              <label class="field fp-floor-select" style="margin:0">
                <span style="display:block;font-size:.68rem;color:var(--muted);margin-bottom:.2rem">Zemin</span>
                <select id="fpFloorTheme" aria-label="Restoran zemin seçimi">
                  <option value="CREAM_MARBLE_CLASSIC">Krem Mermer - Klasik</option>
                  <option value="CREAM_MARBLE_WARM" data-ascii-label="Krem Mermer - Sicak Ton">Krem Mermer - Sıcak Ton</option>
                  <option value="CREAM_MARBLE_SOFT" data-ascii-label="Krem Mermer - Yumusayak Doku">Krem Mermer - Yumuşak Doku</option>
                </select>
              </label>
              <span class="fp-sep"></span>
              <button class="fp-tool-btn danger" id="fpClearBtn" type="button" title="Tüm elemanları temizle">&#10005; Temizle</button>
              <span class="fp-sep"></span>
              <span style="font-size:.7rem;color:var(--muted);align-self:center">İpucu: Aracınızı seçin, ardından tuvale tıklayın veya sürükleyin. ESC ile modu iptal edin.</span>
            </div>
            <div class="floor-plan-workspace">
              <div class="floor-plan-toolbox" id="floorPlanToolbox">
                <p class="toolbox-title">Masalar</p>
                <div class="toolbox-item" draggable="true" data-table-type="TABLE_2" data-capacity="2" aria-label="2 kişilik masa ekle">
                  <span class="toolbox-preview"><svg viewBox="0 0 36 36"><circle cx="18" cy="3" r="3" fill="#78716c"/><circle cx="18" cy="33" r="3" fill="#78716c"/><circle cx="18" cy="18" r="10" fill="#d4a574" stroke="#92400e" stroke-width="1.5"/></svg></span> 2 Kişilik
                </div>
                <div class="toolbox-item" draggable="true" data-table-type="TABLE_4" data-capacity="4" aria-label="4 kişilik masa ekle">
                  <span class="toolbox-preview"><svg viewBox="0 0 36 36"><circle cx="18" cy="3" r="3" fill="#78716c"/><circle cx="18" cy="33" r="3" fill="#78716c"/><circle cx="3" cy="18" r="3" fill="#78716c"/><circle cx="33" cy="18" r="3" fill="#78716c"/><rect x="10" y="10" width="16" height="16" rx="3" fill="#d4a574" stroke="#92400e" stroke-width="1.5"/></svg></span> 4 Kişilik
                </div>
                <div class="toolbox-item" draggable="true" data-table-type="TABLE_6" data-capacity="6" aria-label="6 kişilik masa ekle">
                  <span class="toolbox-preview"><svg viewBox="0 0 44 36"><circle cx="12" cy="3" r="3" fill="#78716c"/><circle cx="22" cy="3" r="3" fill="#78716c"/><circle cx="32" cy="3" r="3" fill="#78716c"/><circle cx="12" cy="33" r="3" fill="#78716c"/><circle cx="22" cy="33" r="3" fill="#78716c"/><circle cx="32" cy="33" r="3" fill="#78716c"/><rect x="6" y="10" width="32" height="16" rx="4" fill="#d4a574" stroke="#92400e" stroke-width="1.5"/></svg></span> 6 Kişilik
                </div>
                <div class="toolbox-item" draggable="true" data-table-type="TABLE_8" data-capacity="8" aria-label="8 kişilik masa ekle">
                  <span class="toolbox-preview"><svg viewBox="0 0 48 36"><circle cx="12" cy="3" r="2.5" fill="#78716c"/><circle cx="24" cy="3" r="2.5" fill="#78716c"/><circle cx="36" cy="3" r="2.5" fill="#78716c"/><circle cx="12" cy="33" r="2.5" fill="#78716c"/><circle cx="24" cy="33" r="2.5" fill="#78716c"/><circle cx="36" cy="33" r="2.5" fill="#78716c"/><circle cx="3" cy="18" r="2.5" fill="#78716c"/><circle cx="45" cy="18" r="2.5" fill="#78716c"/><rect x="8" y="9" width="32" height="18" rx="4" fill="#d4a574" stroke="#92400e" stroke-width="1.5"/></svg></span> 8 Kişilik
                </div>
                <div class="toolbox-item" draggable="true" data-table-type="TABLE_10" data-capacity="10" aria-label="10 kişilik masa ekle">
                  <span class="toolbox-preview"><svg viewBox="0 0 52 36"><circle cx="10" cy="3" r="2.5" fill="#78716c"/><circle cx="20" cy="3" r="2.5" fill="#78716c"/><circle cx="30" cy="3" r="2.5" fill="#78716c"/><circle cx="40" cy="3" r="2.5" fill="#78716c"/><circle cx="10" cy="33" r="2.5" fill="#78716c"/><circle cx="20" cy="33" r="2.5" fill="#78716c"/><circle cx="30" cy="33" r="2.5" fill="#78716c"/><circle cx="40" cy="33" r="2.5" fill="#78716c"/><circle cx="3" cy="18" r="2.5" fill="#78716c"/><circle cx="49" cy="18" r="2.5" fill="#78716c"/><rect x="7" y="9" width="38" height="18" rx="4" fill="#d4a574" stroke="#92400e" stroke-width="1.5"/></svg></span> 10 Kişilik
                </div>
                <p class="toolbox-title">Sekiller</p>
                <div class="toolbox-item" draggable="true" data-shape-type="HORIZONTAL_DIVIDER" aria-label="Yatay ayırıcı ekle">━ Yatay Ayırıcı</div>
                <div class="toolbox-item" draggable="true" data-shape-type="VERTICAL_DIVIDER" aria-label="Dikey ayırıcı ekle">┃ Dikey Ayırıcı</div>
                <div class="toolbox-item" draggable="true" data-shape-type="WALL" aria-label="Duvar ekle">&#9632; Duvar</div>
                <div class="toolbox-item" draggable="true" data-shape-type="CURVED_WALL" aria-label="Yuvarlak duvar ekle">&#9681; Yuvarlak Duvar</div>
                <div class="toolbox-item" draggable="true" data-shape-type="TREE" data-ascii-label="Agac" aria-label="Ağaç ekle">&#127794; Ağaç</div>
                <div class="toolbox-item" draggable="true" data-shape-type="BUSH" data-ascii-label="Cali" aria-label="Çalı ekle">&#127807; Çalı</div>
              </div>
              <div class="floor-plan-canvas show-grid" id="floorPlanCanvas" aria-label="Restoran plan çizim alanı"></div>
            </div>
          </article>

          <article class="module-card" id="dailyViewCard">
            <div class="module-header">
              <div><h3>Günlük Görünüm</h3><p>Masaların doluluk durumunu görün, masaya tıklayarak ayrıntıları inceleyin.</p></div>
            </div>
            <div class="toolbar">
              <input type="date" id="dailyViewDate" aria-label="Günlük görünüm tarihi">
              <button class="primary" id="loadDailyViewBtn" type="button" aria-label="Günlük görünümü getir">Görüntüle</button>
            </div>
            <div class="floor-plan-canvas daily-view-canvas" id="dailyViewCanvas" aria-label="Günlük masa görünümü"></div>
          </article>

          <dialog id="tableDetailDialog" class="table-detail-dialog" aria-label="Masa detay penceresi">
            <form id="tableDetailForm" method="dialog">
              <div class="dialog-header">
                <h3 id="tableDetailTitle">Masa Ayrıntıları</h3>
                <button type="button" class="close-dialog-btn" aria-label="Kapat" data-close-table-dialog>&times;</button>
              </div>
              <div class="dialog-body">
                <div class="field"><label>Durum</label><select id="tdStatus" name="status" aria-label="Rezervasyon durumu">
                  <option value="BEKLEMEDE">Beklemede</option>
                  <option value="ONAYLANDI">Onaylandı</option>
                  <option value="GELDI">Geldi</option>
                  <option value="GELMEDI">Gelmedi</option>
                  <option value="IPTAL">İptal</option>
                  <option value="DEGISIKLIK_UYGULA">Değişikliği Uygula</option>
                </select></div>
                <div class="field"><label>Misafir Adı</label><input id="tdGuestName" name="guest_name" type="text" maxlength="100" aria-label="Misafir adı"></div>
                <div class="field"><label>Telefon</label><span id="tdPhone" class="readonly-field"></span></div>
                <div class="field"><label>Kişi Sayısı</label><input id="tdPartySize" name="party_size" type="number" min="1" aria-label="Kişi sayısı"></div>
                <div class="field"><label>Saat</label><input id="tdTime" name="time" type="time" aria-label="Rezervasyon saati"></div>
                <div class="field full"><label>Notlar</label><textarea id="tdNotes" name="notes" maxlength="500" rows="2" aria-label="Notlar"></textarea></div>
                <div class="readonly-info">
                  <p>Hold ID: <span id="tdHoldId"></span></p>
                  <p>Oluşturulma: <span id="tdCreatedAt"></span></p>
                  <p>Onaylayan: <span id="tdApprovedBy"></span></p>
                </div>
              </div>
              <div class="dialog-footer">
                <button type="button" class="inline-button secondary" id="tdExtendBtn" aria-label="15 dakika uzat">+15 Dk Ver</button>
                <button type="button" class="inline-button danger" id="tdCancelBtn" aria-label="İptal et">İptal</button>
                <button type="submit" class="inline-button primary" aria-label="Kaydet">Kaydet</button>
              </div>
            </form>
          </dialog>
        </section>

        <section data-view="notifications" class="section-grid" hidden>
          <article class="module-card">
            <div class="module-header">
              <div><h3>Bildirim Numaraları</h3><p>Rezervasyon onay talebi oluşturulduğunda WhatsApp mesajı gönderilecek yönetici numaraları. Varsayılan numara kaldırılamaz.</p></div>
            </div>
            <div class="table-shell">
              <table>
                <thead><tr><th>Telefon</th><th>Etiket</th><th>Varsayılan</th><th>İşlem</th></tr></thead>
                <tbody id="notifPhoneTableBody"></tbody>
              </table>
            </div>
            <form id="addNotifPhoneForm" class="dense-form mt-lg">
              <div class="field"><label>Telefon numarası</label><input name="phone" placeholder="+905XXXXXXXXX" required aria-label="Bildirim telefon numarası"></div>
              <div class="field"><label>Etiket (isteğe bağlı)</label><input name="label" placeholder="Örn: Satış müdürü" aria-label="Bildirim etiketi"></div>
              <div class="field full"><button class="inline-button primary" type="submit">Numara Ekle</button></div>
            </form>
          </article>
        </section>

        <section data-view="system" class="section-grid" hidden>
          <div class="split">
            <article class="module-card">
              <div class="module-header">
                <div><h3>Sistem Kontrolleri</h3><p>Hazırlık durumu, alan adı ve kurulum güvenliği aynı ekranda görünür kalır.</p></div>
              </div>
              <div id="systemMeta" class="helper-panel mb-md"></div>
              <div id="systemChecks" class="status-list"></div>
            </article>

            <article class="module-card">
              <div class="module-header">
                <div><h3>Güvenlik ve Oturum</h3><p>Sık giriş yapan ekipler için doğrulama tekrarı ve cihaz hatırlama süresini buradan yönetin.</p></div>
              </div>
              <div id="sessionSummary" class="helper-panel mb-md"></div>
              <form id="sessionPreferencesForm" class="field-grid">
                <div class="field full">
                  <label class="toggle-row" for="sessionRememberToggle">
                    <span class="toggle-copy">
                      <strong>Bu cihazı panel için hatırla</strong>
                      <small>Kayıtlı cihazlarda giriş adımlarını kısaltır; ayar değişikliği için 6 haneli kod gerekir.</small>
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
                      <label>Google doğrulama tekrarı</label>
                      <div id="systemVerificationOptions" class="choice-group"></div>
                    </div>
                    <div>
                      <label>Oturum / hatırlama süresi</label>
                      <div id="systemSessionOptions" class="choice-group"></div>
                    </div>
                  </div>
                </div>
                <div id="sessionOtpField" class="field full">
                  <label for="session-otp-code">Google Authenticator kodu</label>
                  <input id="session-otp-code" name="otp_code" inputmode="numeric" pattern="[0-9]*" placeholder="Tercihleri kaydetmek için 6 haneli kod">
                </div>
                <div class="field full">
                  <button class="inline-button primary" type="submit">Oturum Tercihlerini Kaydet</button>
                </div>
              </form>
              <div id="trustedDevicePanel" class="helper-panel mt-md"></div>
              <div class="module-actions mt-md">
                <button id="forgetDeviceButton" class="inline-button danger" type="button">Bu Cihazı Unut</button>
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

  <dialog id="serviceModeDialog" class="service-mode-dialog" aria-label="Servis Modu">
    <div class="service-mode-shell service-mode-v2">
      <header class="service-mode-header">
        <div>
          <h3>Servis Modu</h3>
          <p>Operasyon planı (V2 yerleşim)</p>
        </div>
        <div class="service-mode-actions">
          <button type="button" id="serviceModePrevDay" class="inline-button secondary" title="Önceki gün (Alt+Sol)">←</button>
          <input type="date" id="serviceModeDate" aria-label="Servis modu tarihi">
          <button type="button" id="serviceModeNextDay" class="inline-button secondary" title="Sonraki gün (Alt+Sağ)">→</button>
          <button type="button" id="serviceModeCloseBtn" class="inline-button" aria-label="Servis modunu kapat">Kapat</button>
        </div>
      </header>

      <div class="service-mode-grid-v2">
        <aside class="service-col service-col-left">
          <article class="module-card service-panel"><h4>Onaylanan</h4><div id="serviceModeApprovedList" class="service-list"></div></article>
          <article class="module-card service-panel"><h4>Onay Bekleyen</h4><div id="serviceModePendingList" class="service-list"></div></article>
          <article class="module-card service-panel service-meta-panel">
            <h4>Güncel Bilgi</h4>
            <div class="service-meta-row"><strong>Tarih:</strong> <span id="serviceMetaDate">-</span></div>
            <div class="service-meta-row"><strong>Saat:</strong> <span id="serviceMetaTime">-</span></div>
            <div class="service-meta-row"><strong>Şef:</strong> <span id="serviceMetaChef">-</span></div>
          </article>
        </aside>

        <section class="service-col service-col-center">
          <div class="service-mode-canvas-wrap service-panel service-canvas-panel">
            <div id="serviceModeCanvas" class="floor-plan-canvas service-mode-canvas" aria-label="Servis modu masa plani"></div>
          </div>
        </section>

        <aside class="service-col service-col-right">
          <article class="module-card service-panel">
            <h4>Yeni Rezervasyon Oluştur</h4>
            <form id="serviceModeQuickCreateForm" class="dense-form">
              <div class="field full"><label>Misafir Adı</label><input type="text" placeholder="Ad Soyad"></div>
              <div class="field"><label>Kişi</label><input type="number" min="1" placeholder="2"></div>
              <div class="field"><label>Saat</label><input type="time"></div>
              <div class="field full"><label>Telefon</label><input type="tel" placeholder="+90..."></div>
              <div class="field full"><label>Not</label><textarea rows="3" placeholder="Opsiyonel not"></textarea></div>
              <div class="field full"><button type="button" class="inline-button primary">Oluştur (yakında)</button></div>
            </form>
          </article>
        </aside>
      </div>

      <div class="service-mode-bottom-v2">
        <div class="service-bottom-block">
          <h5>Öğün Seçimi</h5>
          <div class="filter-chips" id="serviceModeMealChips" aria-label="Öğün seçimi">
            <button type="button" class="filter-chip" data-service-meal="breakfast" title="Kahvaltı (1)">Kahvaltı</button>
            <button type="button" class="filter-chip" data-service-meal="lunch" title="Öğle (2)">Öğle</button>
            <button type="button" class="filter-chip is-active" data-service-meal="dinner" title="Akşam (3)">Akşam</button>
          </div>
        </div>
        <div class="service-bottom-block">
          <h5>Diğer Durumlar (Reddedilen / Gelmeyen)</h5>
          <div id="serviceModeOtherList" class="service-list"></div>
        </div>
        <div class="service-bottom-block">
          <h5>Plan ve Alan</h5>
          <div class="filter-chips" id="serviceModeAreaChips" aria-label="Alan seçimi">
            <button type="button" class="filter-chip is-active" data-service-area="main">Ana Mekân</button>
            <button type="button" class="filter-chip" data-service-area="pool">Havuz</button>
          </div>
          <div class="stack" style="gap:8px;align-items:flex-start;margin-top:8px;">
            <label style="font-size:.78rem;color:var(--muted);">Plan:</label>
            <select id="serviceModePlanSelect" aria-label="Servis modu plan seçimi"></select>
          </div>
        </div>
      </div>
    </div>
  </dialog>

  <dialog id="decisionDialog" class="dialog">
    <div class="dialog-card">
      <div class="dialog-head">
        <h3 id="decisionTitle">İşlem</h3>
        <p id="decisionLead">Gerekçe girin.</p>
      </div>
      <form id="decisionForm" class="field">
        <input id="decisionHoldId" type="hidden">
        <input id="decisionMode" type="hidden">
        <label for="decisionReason">Gerekçe</label>
        <textarea id="decisionReason" class="dialog-textarea" aria-label="Red gerekçesi"></textarea>
        <div class="dialog-actions">
          <button id="closeDecision" class="inline-button secondary" type="button">Vazgeç</button>
          <button class="inline-button danger" type="submit">Reddi Uygula</button>
        </div>
      </form>
    </div>
  </dialog>

  <script>window.ADMIN_PANEL_CONFIG = {config_json};</script>
  <script>{ADMIN_PANEL_SCRIPT}</script>
  <script>{ADMIN_HOLDS_SCRIPT}</script>
  <script>{ADMIN_RESTAURANT_SCRIPT}</script>
</body>
</html>
"""


if ADMIN_PANEL_ROUTE == "/admin":

    @router.get("/admin", response_class=HTMLResponse)
    async def admin_panel_ui() -> HTMLResponse:
        """Serve the standalone admin panel HTML."""
        return HTMLResponse(content=render_admin_panel_html(), headers=ADMIN_UI_NO_STORE_HEADERS)

else:

    @router.get(ADMIN_PANEL_ROUTE, response_class=HTMLResponse)
    async def admin_panel_ui() -> HTMLResponse:
        """Serve the standalone admin panel HTML using configured path."""
        return HTMLResponse(content=render_admin_panel_html(), headers=ADMIN_UI_NO_STORE_HEADERS)

    @router.get("/admin", response_class=HTMLResponse, include_in_schema=False)
    async def admin_panel_ui_legacy() -> HTMLResponse:
        """Serve admin UI on legacy path for compatibility during cutover."""
        return HTMLResponse(content=render_admin_panel_html(), headers=ADMIN_UI_NO_STORE_HEADERS)


# ── POST fallback: prevent 405 when JS fails and browser submits the login
# form natively to the current URL (POST /admin). Redirect back to GET /admin
# so the user sees the panel page instead of a raw JSON error. ──


@router.post("/admin", response_class=RedirectResponse, include_in_schema=False)
async def admin_panel_post_fallback() -> RedirectResponse:
    """Catch accidental native form POST to /admin and redirect to GET."""
    return RedirectResponse(url="/admin", status_code=303)


if ADMIN_PANEL_ROUTE != "/admin":

    @router.post(ADMIN_PANEL_ROUTE, response_class=RedirectResponse, include_in_schema=False)
    async def admin_panel_post_fallback_custom() -> RedirectResponse:
        """Catch accidental native form POST to custom admin path and redirect."""
        return RedirectResponse(url=ADMIN_PANEL_ROUTE, status_code=303)
