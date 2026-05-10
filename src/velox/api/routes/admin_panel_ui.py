"""HTML route for the unified admin operations panel."""

from __future__ import annotations

# ruff: noqa: E501
import json

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse

from velox.api.routes.admin_panel_holds_assets import ADMIN_HOLDS_SCRIPT, ADMIN_HOLDS_STYLE
from velox.api.routes.admin_panel_restaurant_ai_assets import (
    ADMIN_RESTAURANT_AI_SCRIPT,
    ADMIN_RESTAURANT_AI_STYLE,
)
from velox.api.routes.admin_panel_restaurant_assets import ADMIN_RESTAURANT_SCRIPT, ADMIN_RESTAURANT_STYLE
from velox.api.routes.admin_panel_ui_assets import ADMIN_PANEL_SCRIPT, ADMIN_PANEL_STYLE
from velox.api.routes.admin_panel_whatsapp_assets import ADMIN_WHATSAPP_SCRIPT, ADMIN_WHATSAPP_STYLE
from velox.config.settings import settings

router = APIRouter(tags=["admin-panel-ui"])
ADMIN_PANEL_ROUTE = settings.admin_panel_path if settings.admin_panel_path.startswith("/") else f"/{settings.admin_panel_path}"
ADMIN_UI_NO_STORE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}


def render_admin_panel_html(initial_view: str | None = None) -> str:
    """Assemble the standalone admin panel HTML document."""
    config_json = json.dumps(
        {
            "panel_url": settings.admin_panel_url,
            "public_host": settings.public_host,
            "initial_view": initial_view,
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
{ADMIN_RESTAURANT_STYLE}
{ADMIN_RESTAURANT_AI_STYLE}
{ADMIN_WHATSAPP_STYLE}</style>
</head>
<body>
  <div id="toast" class="toast info" role="status" aria-live="polite"></div>
  <div class="shell">
    <aside id="sidebar" class="sidebar" hidden>
      <div class="brand">
        <div class="brand-mark">NX</div>
        <div>
          <h1>NexlumeAI<br>Yönetim</h1>
          <p>Misafir konuşmaları, onaylar ve otel ayarları tek yerden yönetilir.</p>
        </div>
      </div>
      <button id="sidebarCollapseToggle" class="sidebar-collapse-toggle" type="button" aria-label="Menüyü daralt" aria-expanded="true">
        <span aria-hidden="true">‹</span>
        <strong>Menüyü Daralt</strong>
      </button>

      <nav id="nav" class="nav" aria-label="Ana navigasyon"></nav>

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
    <div id="sidebarOverlay" class="sidebar-overlay" hidden></div>

    <main class="workspace">
      <header id="topbar" class="topbar" hidden>
        <div>
          <nav id="pageBreadcrumb" class="breadcrumb" aria-label="Sayfa yolu">Genel Bakış</nav>
          <h2 id="pageTitle">Genel Bakış</h2>
          <p id="pageLead">Aktif konuşmaları, bekleyen onayları ve açık talepleri tek ekranda görüntüleyin.</p>
        </div>
        <div class="topbar-actions">
          <button id="sidebarToggle" class="sidebar-toggle" type="button" aria-label="Gezinme menüsü" aria-expanded="false">Menü</button>
          <button id="debugStartButton" class="action-button secondary" type="button">Kontrol Taraması</button>
          <div id="debugTopbarStatus" class="badge info" hidden>Boşta</div>
          <div class="topbar-aside">
            <div class="badge info">Otel kapsamı seçili</div>
            <div class="badge whatsapp">WhatsApp bağlantısı</div>
            <div class="badge ai">Yanıt modu izleniyor</div>
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
                <label for="bootstrap-token">İlk kurulum anahtarı</label>
                <input id="bootstrap-token" name="bootstrap_token" placeholder="Ortam değişkeniyle etkinleştirildiyse gerekli olabilir">
              </div>
              <div class="field full">
                <button class="sidebar-button primary" type="submit">İlk Yönetici Hesabını Oluştur</button>
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
                  <label for="recovery-token">İlk kurulum anahtarı</label>
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
                <strong>Google Authenticator QR Kodu</strong>
                <div class="qr-wrap">
                  <img id="otpQrImage" alt="Google Authenticator QR">
                </div>
              </div>
              <div class="helper-box">
                <strong>Authenticator Gizli Anahtarı</strong>
                <p id="otpSecret" class="mono"></p>
              </div>
              <div class="helper-box">
                <strong>otpauth Adresi</strong>
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

        <section data-view="conversations" class="section-grid operation-desk-section" hidden>
          <div class="operation-mode-strip" aria-label="Çalışma modu özeti">
            <div>
              <span class="eyebrow">WhatsApp Operasyon Masası</span>
              <strong>Test ve canlı gönderim ayrımı bu ekranda görünür tutulur.</strong>
            </div>
            <div class="mode-pills">
              <span class="mode-pill is-test">Test modu</span>
              <span class="mode-pill is-live">Canlı gönderim kontrollü</span>
            </div>
          </div>
          <div class="conversation-ops-shell operation-desk-shell">
            <article class="module-card conversation-list-panel operation-column">
              <div class="module-header compact">
                <div><h3>Konuşmalar</h3><p>Kim yazdı, ne istiyor ve müdahale gerekiyor mu?</p></div>
              </div>
              <div class="conversation-search">
                <label class="sr-only" for="conversationSearchInput">Konuşma ara</label>
                <input id="conversationSearchInput" type="search" placeholder="Misafir, durum veya niyet ara">
              </div>
              <div id="conversationFilterChips" class="conversation-filter-chips" aria-label="Konuşma filtreleri">
                <button class="filter-chip is-active" type="button" data-conversation-filter="all">Tümü</button>
                <button class="filter-chip" type="button" data-conversation-filter="unread">Okunmamış</button>
                <button class="filter-chip" type="button" data-conversation-filter="handoff">İnsan Devri</button>
                <button class="filter-chip" type="button" data-conversation-filter="approval">Onay Bekleyen</button>
                <button class="filter-chip" type="button" data-conversation-filter="reservation">Rezervasyon</button>
                <button class="filter-chip" type="button" data-conversation-filter="restaurant">Restoran</button>
                <button class="filter-chip" type="button" data-conversation-filter="transfer">Transfer</button>
                <button class="filter-chip" type="button" data-conversation-filter="risk">Riskli</button>
              </div>
              <form id="conversationFilters" class="sr-only" aria-hidden="true">
                <input name="active_only" type="checkbox" checked>
                <select name="status" aria-label="Konuşma durumu">
                  <option value="">Tüm durumlar</option>
                  <option value="GREETING">Karşılama</option>
                  <option value="PENDING_APPROVAL">Onay Bekliyor</option>
                  <option value="CONFIRMED">Onaylandı</option>
                  <option value="HANDOFF">İnsan Devrinde</option>
                </select>
                <input name="date_from" type="date" aria-label="Başlangıç tarihi">
                <input name="date_to" type="date" aria-label="Bitiş tarihi">
              </form>
              <div id="conversationBulkBar" class="bulk-bar" hidden>
                <div class="bulk-left">
                  <label class="toolbar-check bulk-check">
                    <input id="conversationSelectAll" type="checkbox" aria-label="Tüm konuşmaları seç">
                    Bu listeyi seç
                  </label>
                  <span id="conversationSelectionCount" class="bulk-count">0 seçili</span>
                </div>
                <div class="bulk-actions">
                  <button class="action-button danger action-button-sm" data-bulk-action="deactivate">Pasife Al</button>
                  <button class="action-button warn action-button-sm" data-bulk-action="reset">Sıfırla</button>
                  <button class="action-button secondary action-button-sm" data-bulk-action="human-on">İnsan Devrine Al</button>
                  <button class="action-button secondary action-button-sm" data-bulk-action="human-off">Yapay Zekâ Moduna Al</button>
                  <button class="action-button secondary action-button-sm" data-bulk-action="select-filtered">Filtredeki Tümünü Seç</button>
                  <button class="action-button secondary action-button-sm" data-bulk-action="clear">Seçimi Temizle</button>
                </div>
              </div>
              <div id="conversationTableBody" class="conversation-card-list" aria-live="polite"></div>
            </article>
            <article id="conversationDetail" class="module-card conversation-thread-panel whatsapp-thread-panel operation-column">
              <div class="empty-state"><p>Detay için soldan bir konuşma seçin.</p></div>
            </article>
            <aside id="conversationDecisionPanel" class="module-card conversation-side-panel decision-support-panel operation-column" aria-label="Karar destek paneli">
              <div class="module-header compact">
                <div><h3>Karar Desteği</h3><p>Konuşma seçilince aksiyon önerisi burada görünür.</p></div>
              </div>
              <div class="conversation-side-empty">
                <strong>Konuşma seçimi bekleniyor</strong>
                <p>Misafir özeti, AI’nin anladığı konu, risk ve hızlı aksiyonlar burada toplanır.</p>
              </div>
            </aside>
          </div>
        </section>

        <section data-view="responsereview" class="section-grid response-review-section" hidden>
          <div class="response-review-hero" aria-label="Yanıt inceleme özeti">
            <div>
              <span class="eyebrow">Response Review</span>
              <h3>Yanıt İnceleme ve Raporlama</h3>
              <p>Operasyon masasından raporlanan AI, operatör ve sistem yanıtlarını sınıflandırın; doğru örnekleri ve problemli yanıtları kontrollü feedback yapısına aktarın.</p>
            </div>
            <div class="mode-pills">
              <span class="mode-pill is-test">Audit izli</span>
              <span class="mode-pill is-live">Feedback kontrollü</span>
            </div>
          </div>
          <div class="response-review-shell">
            <article class="module-card response-review-list-panel">
              <div class="module-header compact">
                <div><h3>Raporlanan Yanıtlar</h3><p>Dikey kuyruk, durum ve hata tipine göre filtrelenir.</p></div>
                <button id="responseReviewRefresh" class="action-button secondary action-button-sm" type="button">Yenile</button>
              </div>
              <form id="responseReviewFilters" class="response-review-filters">
                <label>
                  <span>Durum</span>
                  <select id="responseReviewStatusFilter" name="status">
                    <option value="">Tümü</option>
                    <option value="open">Açık</option>
                    <option value="in_review">İncelemede</option>
                    <option value="finalized">Tamamlandı</option>
                    <option value="closed">Kapalı</option>
                  </select>
                </label>
                <label>
                  <span>Karar</span>
                  <select id="responseReviewClassificationFilter" name="classification">
                    <option value="">Tümü</option>
                    <option value="needs_review">İnceleme bekliyor</option>
                    <option value="correct">Doğru</option>
                    <option value="incorrect">Yanlış</option>
                    <option value="needs_revision">Düzeltilmeli</option>
                  </select>
                </label>
                <label>
                  <span>Hata Tipi</span>
                  <select id="responseReviewErrorFilter" name="error_type">
                    <option value="">Tümü</option>
                    <option value="wrong_info">Yanlış bilgi</option>
                    <option value="missing_info">Eksik bilgi</option>
                    <option value="wrong_intent">Niyet ıskalama</option>
                    <option value="source_mismatch">Kaynak uyumsuzluğu</option>
                    <option value="unsupported_claim">Kaynaksız iddia</option>
                    <option value="policy_risk">Politika riski</option>
                    <option value="pii_risk">PII riski</option>
                    <option value="tone_or_length">Ton / uzunluk</option>
                    <option value="language_issue">Dil sorunu</option>
                    <option value="tool_mismatch">Araç sonucu uyumsuz</option>
                    <option value="handoff_required">İnsan devri gerekirdi</option>
                    <option value="delivery_status_issue">Teslimat durumu</option>
                    <option value="other">Diğer</option>
                  </select>
                </label>
                <button class="action-button primary action-button-sm" type="submit">Kontrol Et</button>
              </form>
              <div id="responseReviewList" class="response-review-list" aria-live="polite"></div>
            </article>
            <article id="responseReviewDetail" class="module-card response-review-detail-panel">
              <div class="empty-state">
                <p>Bir rapor seçin veya operasyon masasındaki AI yanıtına sağ tıklayıp <strong>Raporla</strong> aksiyonunu kullanın.</p>
              </div>
            </article>
          </div>
        </section>

        <section data-view="holds" class="section-grid" hidden>
          <article class="module-card confirmation-form-panel">
            <div class="module-header">
              <div><h3>Onay Formları</h3><p>Konaklama, restoran ve transfer onay formlarını müşteri dilinde oluşturun.</p></div>
              <div id="confirmationTypeButtons" class="confirmation-type-row" aria-label="Onay formu tipi">
                <button class="action-button secondary is-active" type="button" data-confirmation-type="accommodation">Konaklama Formu</button>
                <button class="action-button secondary" type="button" data-confirmation-type="restaurant">Restoran Formu</button>
                <button class="action-button secondary" type="button" data-confirmation-type="transfer">Transfer Formu</button>
              </div>
            </div>
            <div class="confirmation-workspace">
              <div class="confirmation-editor">
                <div id="confirmationLanguageButtons" class="filter-chips confirmation-language-row" aria-label="Form dili"></div>
                <div class="confirmation-actions-row">
                  <button class="inline-button secondary" type="button" data-confirmation-fill-selected>Seçili Kayıttan Doldur</button>
                  <button class="inline-button primary" type="button" data-confirmation-preview>Önizleme</button>
                  <button class="inline-button secondary" type="button" data-confirmation-generate>Güvenli Link Oluştur</button>
                  <button class="inline-button primary" type="button" data-confirmation-send>Oluştur ve Gönder</button>
                </div>
                <div id="confirmationFields" class="field-grid confirmation-fields"></div>
                <div id="confirmationPublicUrl" class="confirmation-public-url" hidden></div>
                <textarea id="confirmationWhatsappMessage" class="confirmation-message-preview" readonly aria-label="WhatsApp onay mesajı"></textarea>
              </div>
              <div class="confirmation-preview-shell">
                <iframe id="confirmationPreviewFrame" class="confirmation-preview-frame" title="Onay formu HTML önizlemesi"></iframe>
              </div>
            </div>
          </article>

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
                  <div class="filter-chips" id="stayArchiveChips">
                    <button class="filter-chip is-active" type="button" data-stay-archive="active" aria-label="Aktif konaklama kayıtları">Aktif</button>
                    <button class="filter-chip" type="button" data-stay-archive="archived" aria-label="Arşiv konaklama kayıtları">Arşiv</button>
                  </div>
                  <div class="filter-chips" id="stayStatusChips"></div>
                  <button class="inline-button secondary" type="button" data-stay-select-all aria-label="Tüm görünen konaklama kayıtlarını seç">Seç</button>
                  <button class="inline-button danger" type="button" data-stay-bulk-archive aria-label="Seçili konaklama kayıtlarını arşive taşı">Toplu Temizle</button>
                  <input name="reservation_no" placeholder="Rez. No ile ara" aria-label="Rezervasyon numarası araması">
                  <button class="primary" type="submit">Ara</button>
                </form>
                <div class="table-shell">
                  <table class="holds-table"><thead><tr>
                    <th class="table-select">Seç</th><th>Aç</th><th>Rez. No</th><th>Onay Kaydı</th><th>Durum</th><th>Misafir</th><th>Tarih</th><th>Tutar</th>
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
                    <th>Aç</th><th>Onay Kaydı</th><th>Durum</th><th>Misafir</th><th>Tarih/Saat</th><th>Kişi</th>
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
                  <div class="filter-chips" id="transferArchiveChips">
                    <button class="filter-chip is-active" type="button" data-transfer-archive="active" aria-label="Aktif transfer kayıtları">Aktif</button>
                    <button class="filter-chip" type="button" data-transfer-archive="archived" aria-label="Arşiv transfer kayıtları">Arşiv</button>
                  </div>
                  <div class="filter-chips" id="transferStatusChips"></div>
                  <button class="inline-button secondary" type="button" data-transfer-select-all aria-label="Tüm görünen transfer kayıtlarını seç">Seç</button>
                  <button class="inline-button danger" type="button" data-transfer-bulk-archive aria-label="Seçili transfer kayıtlarını arşive taşı">Toplu Temizle</button>
                  <button class="primary" type="submit">Filtrele</button>
                </form>
                <div class="table-shell">
                  <table class="holds-table"><thead><tr>
                    <th class="table-select">Seç</th><th>Aç</th><th>Onay Kaydı</th><th>Durum</th><th>Misafir</th><th>Güzergâh</th><th>Tarih</th>
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
              <div><h3>Kapasite Aralığı Yönetimi</h3><p>Kapasiteyi tarih ve rezervasyon saati bazında takip edin, kalan kapasiteyi görsel olarak izleyin.</p></div>
              <div class="stack" style="align-items:flex-end;gap:8px;">
                <button id="openServiceModeBtn" class="inline-button primary" type="button" aria-label="Servis modunu aç" onclick="window.__veloxOpenServiceMode && window.__veloxOpenServiceMode()">Servis Modu</button>
              </div>
            </div>
            <form id="slotFilters" class="toolbar">
              <input name="date_from" type="date" aria-label="Kapasite aralığı başlangıç tarihi">
              <input name="date_to" type="date" aria-label="Kapasite aralığı bitiş tarihi">
              <select name="display_interval" id="slotDisplayInterval" aria-label="Kapasite aralığı gösterim aralığı">
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
              <button id="loadSlotsButton" class="primary" type="button" aria-label="Kapasite aralıklarını getir">Kapasite Aralıklarını Getir</button>
            </form>
            <div class="toolbar" style="margin-top:-4px">
              <button id="hideSlotsButton" class="inline-button secondary" type="button" aria-label="Kapasite aralıklarını kapat">Kapasite Aralıklarını Kapat</button>
            </div>
            <div id="slotSummaryCards" class="split"></div>
            <div class="table-shell">
              <table>
                <thead><tr><th>ID</th><th>Tarih</th><th>Rezervasyon Saati</th><th>Alan</th><th>Kalan Kapasite</th><th>Durum</th><th>İşlem</th></tr></thead>
                <tbody id="slotTableBody"></tbody>
              </table>
            </div>
          </article>

          <article class="module-card">
            <div class="module-header">
              <div><h3>Toplu Kapasite Aralığı Temizleme</h3><p>Seçilen tarih ve saat aralığındaki kapasite kayıtlarını tek seferde silin. Başlangıç ve bitiş saatine denk gelen kayıtlar da dahildir.</p></div>
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
              <div class="field full"><button class="inline-button danger" type="submit">Seçili Aralıktaki Kapasite Kayıtlarını Temizle</button></div>
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
              <div class="field"><label>Misafire açık mı?</label><input name="is_active" type="checkbox" checked class="checkbox-field" aria-label="Kapasite aralığı aktif mi"></div>
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
                  <th>Aç</th><th>Onay Kaydı</th><th>Durum</th><th>Misafir</th><th>Tarih/Saat</th><th>Kişi</th>
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
                <p class="toolbox-title">Şekiller</p>
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
                  <option value="PENDING_APPROVAL">Onay Bekliyor</option>
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
                  <p>Onay Kaydı ID: <span id="tdHoldId"></span></p>
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

        <section data-view="restaurantai" class="section-grid restaurant-ai-panel" hidden>
          <article class="module-card restaurant-ai-hero">
            <div class="module-header">
              <div>
                <h3>Restaurant AI / Menü Asistanı</h3>
                <p>Menü kataloğu, garson WhatsApp yönlendirmesi, sipariş logları, menü dışı talepler ve deterministik test konsolu.</p>
              </div>
              <div class="module-actions">
                <button id="restaurantAiImportCatalog" class="inline-button primary" type="button">JSON Kataloğu Versiyonlu İçe Aktar</button>
              </div>
            </div>
            <div id="restaurantAiSummary" class="restaurant-ai-summary"></div>
          </article>

          <article class="module-card">
            <div class="module-header">
              <div><h3>Public Sipariş / QR Yönetimi</h3><p>Masa QR kodları için değiştirilemez, imzalı /order bağlantısı üretin. Müşteri adı ve oda numarası kalıcı sipariş loguna yazılmaz.</p></div>
            </div>
            <form id="restaurantAiQrForm" class="dense-form">
              <div class="field"><label>Venue</label><input name="venue" required value="Kassandra Restaurant"></div>
              <div class="field"><label>Masa no</label><input name="table_no" required placeholder="12"></div>
              <div class="field full"><button class="inline-button primary" type="submit">QR Linki Üret</button></div>
            </form>
            <div id="restaurantAiQrResult" class="helper-panel mt-md"></div>
          </article>

          <article class="module-card">
            <div class="module-header">
              <div><h3>Menü Kataloğu Yönetimi</h3><p>menu_catalog.json veya versiyonlu DB kataloğunu görüntüleyin; manuel ürünler otomatik aktif olmaz.</p></div>
              <div class="module-actions">
                <button id="restaurantAiCatalogToggle" class="action-button secondary" type="button" aria-expanded="false" aria-controls="restaurantAiCatalogContent">Kataloğu Aç</button>
              </div>
            </div>
            <div id="restaurantAiCatalogContent" hidden>
              <form id="restaurantAiCatalogFilters" class="toolbar restaurant-ai-toolbar">
                <input id="restaurantAiCatalogSearch" name="search" placeholder="Ürün, etiket veya açıklama ara" aria-label="Menü kataloğu arama">
                <select id="restaurantAiCategoryFilter" name="category" aria-label="Kategori filtresi"><option value="">Tüm kategoriler</option></select>
                <select id="restaurantAiVenueFilter" name="venue" aria-label="Venue filtresi"><option value="">Tüm venue</option></select>
                <select id="restaurantAiMenuTypeFilter" name="menu_type" aria-label="Menü tipi filtresi"><option value="">Tüm menü tipleri</option></select>
                <select id="restaurantAiStatusFilter" name="status" aria-label="Durum filtresi">
                  <option value="">Tüm durumlar</option>
                  <option value="active">Aktif</option>
                  <option value="passive">Pasif</option>
                  <option value="pending_approval">Onay gerekli</option>
                </select>
                <button class="primary" type="submit">Filtrele</button>
              </form>
              <div class="table-shell restaurant-ai-table">
                <table>
                  <thead><tr><th>Ürün</th><th>Kategori</th><th>Menü</th><th>Venue</th><th>Fiyat</th><th>Açıklama</th><th>İçerik</th><th>Etiketler</th><th>Durum</th><th>İşlem</th></tr></thead>
                  <tbody id="restaurantAiCatalogTableBody"></tbody>
                </table>
              </div>
            </div>
          </article>

          <div class="split">
            <article class="module-card">
              <div class="module-header">
                <div><h3>Fiyat Çakışmaları</h3><p>Aynı venue + menü tipinde aynı ürün farklı fiyatla görünürse burada ayrılır.</p></div>
              </div>
              <div id="restaurantAiConflictList" class="helper-panel"></div>
            </article>
            <article class="module-card">
              <div class="module-header">
                <div><h3>Manuel Ürün Talebi</h3><p>Menü dışı veya elle eklenen ürün varsayılan olarak “onay gerekli” statüsünde kalır.</p></div>
              </div>
              <form id="restaurantAiManualItemForm" class="dense-form">
                <div class="field"><label>Venue</label><input name="venue" required value="Kassandra Restaurant"></div>
                <div class="field"><label>Menü tipi</label><input name="menu_type" required placeholder="Snack Menu"></div>
                <div class="field"><label>Kategori</label><input name="category" required placeholder="Pizzas"></div>
                <div class="field"><label>Ürün adı</label><input name="name_en" required placeholder="Menu item name"></div>
                <div class="field"><label>Türkçe ad</label><input name="name_tr" placeholder="Türkçe ürün adı"></div>
                <div class="field"><label>Fiyat TRY</label><input name="price_try" type="number" min="0" step="0.01"></div>
                <div class="field full"><label>Açıklama</label><textarea name="description_tr" placeholder="Kısa açıklama"></textarea></div>
                <div class="field full"><label>İçindekiler</label><input name="ingredients" placeholder="domates, mozzarella, fesleğen"></div>
                <div class="field full"><label>Etiketler</label><input name="tags" placeholder="vegan, seafood, light_candidate"></div>
                <div class="field full"><label>Not</label><input name="notes" placeholder="Neden eklenmek istendi?"></div>
                <div class="field full"><button class="inline-button primary" type="submit">Onay Gerekli Olarak Kaydet</button></div>
              </form>
            </article>
          </div>

          <div class="split">
            <article class="module-card">
              <div class="module-header">
                <div><h3>Garson WhatsApp Numaraları</h3><p>Sipariş bildirimlerinin gideceği aktif garsonları yönetin.</p></div>
              </div>
              <form id="restaurantAiWaiterForm" class="dense-form">
                <div class="field"><label>Garson adı</label><input name="waiter_name" required></div>
                <div class="field"><label>WhatsApp numarası</label><input name="whatsapp_number" required placeholder="+905XXXXXXXXX"></div>
                <div class="field"><label>Rol</label><input name="role" placeholder="Garson / Şef / Bar"></div>
                <div class="field"><label>Venue</label><input name="venue" placeholder="Kassandra Restaurant"></div>
                <div class="field"><label>Aktif</label><input name="active" type="checkbox" class="checkbox-field" checked></div>
                <div class="field"><label>Sipariş bildirimi</label><input name="receives_order_notifications" type="checkbox" class="checkbox-field" checked></div>
                <div class="field full"><button class="inline-button primary" type="submit">Garson Numarası Ekle</button></div>
              </form>
              <div class="table-shell mt-md">
                <table>
                  <thead><tr><th>Garson</th><th>Numara</th><th>Rol</th><th>Venue</th><th>Aktif</th><th>Bildirim</th><th>İşlem</th></tr></thead>
                  <tbody id="restaurantAiWaiterTableBody"></tbody>
                </table>
              </div>
            </article>
            <article class="module-card">
              <div class="module-header">
                <div><h3>Menü Dışı Talep Logları</h3><p>Sushi, margarita cocktail veya lahmacun gibi katalog dışı talepler analiz için saklanır; öneri sistemine otomatik eklenmez.</p></div>
              </div>
              <form id="restaurantAiOffMenuForm" class="dense-form">
                <div class="field"><label>Talep</label><input name="requested_text" required placeholder="sushi"></div>
                <div class="field"><label>Niyet</label><input name="detected_intent" placeholder="off_menu_request"></div>
                <div class="field"><label>Venue</label><input name="venue" placeholder="Kassandra Restaurant"></div>
                <div class="field full"><button class="inline-button secondary" type="submit">Log Olarak Kaydet</button></div>
              </form>
              <div class="table-shell mt-md">
                <table>
                  <thead><tr><th>Talep</th><th>Niyet</th><th>Venue</th><th>Katalog</th><th>Tarih</th></tr></thead>
                  <tbody id="restaurantAiOffMenuTableBody"></tbody>
                </table>
              </div>
            </article>
          </div>

          <article class="module-card">
            <div class="module-header">
              <div><h3>Sipariş Logları</h3><p>AI üzerinden alınan siparişlerin onay ve WhatsApp gönderim durumlarını izleyin.</p></div>
            </div>
            <form id="restaurantAiOrderFilters" class="toolbar">
              <select id="restaurantAiOrderStatusFilter" name="status" aria-label="Sipariş durumu">
                <option value="">Tüm durumlar</option>
                <option value="pending_staff_approval">pending_staff_approval</option>
                <option value="accepted_by_staff">accepted_by_staff</option>
                <option value="rejected_by_staff">rejected_by_staff</option>
                <option value="preparing">preparing</option>
                <option value="completed">completed</option>
                <option value="pending_confirmation">pending_confirmation</option>
                <option value="confirmed">confirmed</option>
                <option value="sent_to_waiter">sent_to_waiter</option>
                <option value="failed">failed</option>
                <option value="cancelled">cancelled</option>
              </select>
              <button class="primary" type="submit">Siparişleri Getir</button>
            </form>
            <div class="table-shell restaurant-ai-table">
              <table>
                <thead><tr><th>Sipariş</th><th>Masa/Oda</th><th>Misafir</th><th>Detay</th><th>Toplam</th><th>Not</th><th>Alerji</th><th>Onay</th><th>WhatsApp</th></tr></thead>
                <tbody id="restaurantAiOrderTableBody"></tbody>
              </table>
            </div>
          </article>

          <div class="split">
            <article class="module-card">
              <div class="module-header">
                <div><h3>Test Konsolu</h3><p>Örnek müşteri sorusunu katalog doğrulamalı test edin.</p></div>
              </div>
              <form id="restaurantAiTestForm" class="dense-form">
                <div class="field full"><label>Müşteri sorusu</label><textarea name="question" required placeholder="Sushi var mı?"></textarea></div>
                <div class="field"><label>Venue</label><input name="venue" placeholder="Kassandra Restaurant"></div>
                <div class="field"><label>Menü tipi</label><input name="menu_type" placeholder="Snack Menu"></div>
                <div class="field full"><button class="inline-button primary" type="submit">Testi Çalıştır</button></div>
              </form>
              <div id="restaurantAiTestResult" class="restaurant-ai-test-result"></div>
            </article>
            <article class="module-card">
              <div class="module-header">
                <div><h3>Sistem Ayarları</h3><p>Menü dışı öneri engeli her zaman açık kalır; yalnızca mesaj metinleri düzenlenir.</p></div>
              </div>
              <div class="helper-box mb-md"><strong>Menü dışı öneri engeli: HER ZAMAN AÇIK</strong><p>Bu ayar panelden kapatılamaz.</p></div>
              <form id="restaurantAiSettingsForm" class="dense-form">
                <div class="field full"><label>Menü dışı ürün cevabı</label><textarea name="off_menu_response" required></textarea></div>
                <div class="field full"><label>Sipariş onay mesajı</label><textarea name="order_confirmation_message" required></textarea></div>
                <div class="field full"><label>WhatsApp bildirim şablonu</label><textarea name="whatsapp_notification_template" required></textarea></div>
                <div class="field full"><label>Alerji uyarı metni</label><textarea name="allergy_warning_text" required></textarea></div>
                <div class="field full"><button class="inline-button primary" type="submit">Mesajları Kaydet</button></div>
              </form>
            </article>
          </div>
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

        <section data-view="accesscontrol" class="section-grid" hidden>
          <div id="accessOverviewCards" class="card-grid card-grid-3"></div>

          <div class="access-control-layout">
            <article class="module-card">
              <div class="module-header">
                <div><h3>Rol Şablonları</h3><p>Otel operasyonunda kullanılan yetki şablonlarını, varsayılan departmanlarını ve erişim yoğunluğunu inceleyin.</p></div>
                <div class="badge info">Rol = yetki şablonu</div>
              </div>
              <div id="accessRoleSummary" class="helper-panel mb-md"></div>
              <div id="accessRoleCards" class="access-role-grid"></div>
            </article>

            <article class="module-card">
              <div class="module-header">
                <div><h3>Yeni Yönetici Kullanıcısı</h3><p>Kullanıcı adı, geçici şifre, rol, departman ve zorunlu 2FA bilgilerini tek akışta tanımlayın.</p></div>
                <div class="badge warn">2FA zorunlu</div>
              </div>
              <form id="accessCreateUserForm" class="field-grid">
                <div class="field">
                  <label for="accessCreateUsername">Kullanıcı adı</label>
                  <input id="accessCreateUsername" name="username" autocomplete="off" minlength="3" maxlength="100" required>
                </div>
                <div class="field">
                  <label for="accessCreateDisplayName">Görünen ad</label>
                  <input id="accessCreateDisplayName" name="display_name" maxlength="100" placeholder="Örn. Ayşe Demir">
                </div>
                <div class="field">
                  <label for="accessCreatePassword">Geçici şifre</label>
                  <input id="accessCreatePassword" name="password" type="password" autocomplete="new-password" minlength="12" maxlength="72" required>
                </div>
                <div class="field">
                  <label for="accessCreatePasswordConfirm">Şifre tekrarı</label>
                  <input id="accessCreatePasswordConfirm" name="password_confirm" type="password" autocomplete="new-password" minlength="12" maxlength="72" required>
                </div>
                <div class="field access-field-role">
                  <label for="accessCreateRole">Rol (Yetki şablonu)</label>
                  <select id="accessCreateRole" name="role" required></select>
                  <small>Panelde hangi ekranlara ve hangi işlemlere erişeceğini belirler.</small>
                </div>
                <div class="field access-field-department">
                  <label for="accessCreateDepartment">Departman (Otel birimi)</label>
                  <select id="accessCreateDepartment" name="department_code" required></select>
                  <small>Kullanıcının otel organizasyonunda hangi ekibe bağlı olduğunu tanımlar.</small>
                </div>
                <div class="field full access-toggle-grid">
                  <label class="toggle-row" for="accessCreateActive">
                    <span class="toggle-copy">
                      <strong>Hesap aktif</strong>
                      <small>Pasif kullanıcı panele giriş yapamaz.</small>
                    </span>
                    <span class="switch">
                      <input id="accessCreateActive" name="is_active" type="checkbox" checked>
                      <span class="switch-track"><span class="switch-thumb"></span></span>
                    </span>
                  </label>
                  <label class="toggle-row access-toggle-locked" for="accessCreateTwoFactor">
                    <span class="toggle-copy">
                      <strong>Zorunlu 2FA</strong>
                      <small>Güvenlik politikası gereği kapatılamaz; kullanıcı ilk girişte Authenticator kurulumu yapar.</small>
                    </span>
                    <span class="switch">
                      <input id="accessCreateTwoFactor" name="two_factor_required" type="checkbox" checked disabled>
                      <span class="switch-track"><span class="switch-thumb"></span></span>
                    </span>
                  </label>
                </div>
                <div class="field full">
                  <button class="inline-button primary" type="submit">Kullanıcı Oluştur ve Rol Ata</button>
                </div>
              </form>

              <div id="accessTotpResult" class="helper-panel mt-md" hidden>
                <div class="helper-box">
                  <strong id="accessTotpResultTitle">Authenticator Kurulumu</strong>
                  <p id="accessTotpResultUser" class="muted"></p>
                </div>
                <div class="qr-wrap">
                  <img id="accessTotpQrImage" alt="Authenticator QR kodu">
                </div>
                <div class="helper-box">
                  <strong>Authenticator Gizli Anahtarı</strong>
                  <p id="accessTotpSecret" class="mono"></p>
                </div>
                <div class="helper-box">
                  <strong>otpauth Adresi</strong>
                  <p id="accessTotpUri" class="mono"></p>
                </div>
              </div>
            </article>
          </div>

          <div class="access-control-main">
            <article class="module-card">
              <div class="module-header">
                <div><h3>Kullanıcılar ve Rol Değişikliği</h3><p>Mevcut kullanıcıların rolü, departmanı, aktiflik durumu ve 2FA kayıtları kontrollü şekilde yönetilir.</p></div>
                <div class="badge dark">Departman = organizasyon birimi</div>
              </div>
              <div id="accessUsersList" class="access-user-list"></div>
            </article>

            <article class="module-card">
              <div class="module-header">
                <div><h3>İzin Düzenleyici</h3><p>Seçili kullanıcının ekran ve işlem izinlerini anahtar yapısı ile güncelleyin. Rol varsayılanına dönme seçeneği korunur.</p></div>
                <div class="module-actions">
                  <button id="accessResetPermissionsButton" class="inline-button secondary" type="button">Rol Varsayılana Dön</button>
                  <button id="accessSavePermissionsButton" class="inline-button primary" type="button">İzinleri Kaydet</button>
                </div>
              </div>
              <div id="accessPermissionMeta" class="helper-panel mb-md"></div>
              <div id="accessPermissionTree" class="access-permission-tree"></div>
            </article>
          </div>
        </section>

        <section data-view="whatsappapi" class="section-grid" hidden>
          <article class="module-card whatsapp-guide-card">
            <div class="module-header">
              <div><h3>WhatsApp Cloud API Kurulum Rehberi</h3><p>Meta hesabından doğru bilgileri alıp bu sisteme hatasız bağlamak için önce rehberi açın, sonra bağlantı adımlarını sırayla tamamlayın.</p></div>
              <button id="whatsappGuideButton" class="inline-button primary" type="button" aria-label="WhatsApp Cloud API detaylı kurulum rehberini aç">Detaylı Rehberi Aç</button>
            </div>
            <div class="whatsapp-guide-highlights">
              <div class="whatsapp-guide-highlight"><b>1</b><span>Başlamadan önce Meta Business, WABA, telefon ve HTTPS webhook hazırlığını kontrol edin.</span></div>
              <div class="whatsapp-guide-highlight"><b>2</b><span>Önerilen yol olarak Meta ile Bağlan akışını kullanın; manuel kayıt sadece yedek yoldur.</span></div>
              <div class="whatsapp-guide-highlight"><b>3</b><span>Webhook Abone Et, Sağlık Kontrolü ve Meta'dan Senkronize Et adımlarını tamamlayın.</span></div>
              <div class="whatsapp-guide-highlight"><b>4</b><span>24 saatlik pencere dışındaki mesajlar için onaylı şablon hazırlayın.</span></div>
            </div>
            <div class="whatsapp-meta-resource-shell" aria-label="Meta bilgi ve dokümantasyon bağlantıları">
              <div class="whatsapp-meta-resource-head">
                <div>
                  <h4>Meta Bilgi Merkezi</h4>
                  <p>Kurulum sırasına göre gruplanmış resmi Meta dokümantasyonları ve operasyon ekranları. Hızlı bağlantı seçimi ilgili kaynağı doğrudan yeni sekmede açar.</p>
                </div>
                <div class="whatsapp-meta-resource-select">
                  <label for="whatsappMetaResourceSelect">Hızlı bağlantı</label>
                  <select id="whatsappMetaResourceSelect" aria-label="Meta dokümantasyon veya bilgi bağlantısı seç">
                    <option value="">Meta kaynağı seçin</option>
                  </select>
                </div>
              </div>
              <div id="whatsappMetaResourceToggles" class="whatsapp-meta-resource-toggles"></div>
            </div>
          </article>
          <div id="whatsappStatusCards" class="whatsapp-status-grid"></div>
          <div class="whatsapp-layout">
            <article class="module-card">
              <div class="module-header">
                <div><h3>Meta Bağlantısı</h3><p>Cloud API numarası, webhook ve token durumu bu ekranda izlenir.</p></div>
                <div class="whatsapp-actions">
                  <button id="whatsappConnectButton" class="inline-button primary" type="button">Meta ile Bağlan</button>
                  <button id="whatsappHealthButton" class="inline-button secondary" type="button">Sağlık Kontrolü</button>
                  <button id="whatsappWebhookSubscribeButton" class="inline-button secondary" type="button">Webhook Abone Et</button>
                </div>
              </div>
              <div id="whatsappIntegrationMeta" class="helper-panel mb-md"></div>
              <div id="whatsappConfigChecklist" class="whatsapp-checklist"></div>
            </article>

            <article class="module-card">
              <div class="module-header">
                <div><h3>Gelişmiş Manuel Kayıt</h3><p>Meta açılır pencere akışı kullanılamadığında teknik bilgiler buradan kaydedilir.</p></div>
              </div>
              <form id="whatsappManualForm" class="dense-form">
                <div class="field"><label>İşletme Kimliği</label><input name="business_id" autocomplete="off"></div>
                <div class="field"><label>WABA Kimliği</label><input name="waba_id" autocomplete="off"></div>
                <div class="field"><label>Telefon Numarası Kimliği</label><input name="phone_number_id" autocomplete="off" required></div>
                <div class="field"><label>Görünen numara</label><input name="display_phone_number" autocomplete="off"></div>
                <div class="field"><label>Doğrulanmış ad</label><input name="verified_name" autocomplete="off"></div>
                <div class="field"><label>Kalite</label><input name="quality_rating" autocomplete="off"></div>
                <div class="field"><label>Mesaj limiti</label><input name="messaging_limit" autocomplete="off"></div>
                <div class="field"><label>Token izin kapsamı</label><input name="token_scopes" placeholder="izin1,izin2" autocomplete="off"></div>
                <div class="field full"><label>Erişim token'ı</label><input class="whatsapp-secret-input" name="access_token" type="password" autocomplete="off" placeholder="Boş bırakırsanız mevcut token korunur"></div>
                <div class="field full"><label>Webhook doğrulama token'ı</label><input class="whatsapp-secret-input" name="webhook_verify_token" type="password" autocomplete="off" placeholder="Boş bırakırsanız mevcut değer korunur"></div>
                <div class="field full"><button class="inline-button primary" type="submit">Bağlantıyı Kaydet</button></div>
              </form>
            </article>
          </div>

          <div class="split">
            <article class="module-card">
              <div class="module-header">
                <div><h3>Şablon Mesajları</h3><p>24 saat penceresi kapalı konuşmalar için onaylı şablon gerekir.</p></div>
                <button id="whatsappTemplateSyncButton" class="inline-button secondary" type="button">Meta'dan Senkronize Et</button>
              </div>
              <div id="whatsappTemplates" class="whatsapp-template-list"></div>
              <form id="whatsappTemplateForm" class="field-grid mt-lg">
                <div class="field"><label>Şablon adı</label><input name="name" required></div>
                <div class="field"><label>Dil</label><input name="language" placeholder="tr" required></div>
                <div class="field"><label>Kategori</label><input name="category" placeholder="UTILITY"></div>
                <div class="field full"><label>Bileşenler JSON'u</label><textarea name="components_json" class="whatsapp-secret-input" style="min-height:90px" placeholder="[]"></textarea></div>
                <div class="field full"><button class="inline-button primary" type="submit">Yerel Taslak Kaydet</button></div>
              </form>
            </article>

            <article class="module-card">
              <div class="module-header">
                <div><h3>Bağlantı Günlüğü</h3><p>Gizli anahtar içermeyen bağlantı olayları.</p></div>
              </div>
              <div id="whatsappEvents" class="whatsapp-event-list"></div>
            </article>
          </div>
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

        <section data-view="debug" class="section-grid" hidden>
          <div class="debug-summary-grid">
            <article class="overview-card">
              <h4>Aktif Tarama</h4>
              <strong id="debugActiveRunStatus">-</strong>
              <span id="debugActiveRunMeta">Henüz tarama başlatılmadı.</span>
            </article>
            <article class="overview-card">
              <h4>Toplam Bulgu</h4>
              <strong id="debugSummaryFindings">0</strong>
              <span id="debugSummaryCounts">Kritik 0 / Yüksek 0 / Orta 0 / Düşük 0</span>
            </article>
            <article class="overview-card">
              <h4>Kapsam</h4>
              <strong id="debugSummaryScope">-</strong>
              <span id="debugSummaryScopeMeta">Aktif tarama seçildiğinde kapsam burada görünür.</span>
            </article>
          </div>

          <div class="debug-layout">
            <article class="module-card debug-column">
              <div class="module-header">
                <div><h3>Tarama Listesi</h3><p>Kuyruktaki ve tamamlanan taramaları bu panelden takip edin.</p></div>
                <div class="module-actions">
                  <button id="debugRefreshButton" class="inline-button secondary" type="button">Yenile</button>
                </div>
              </div>
              <div id="debugRunList" class="debug-run-list">
                <div class="empty-state">
                  <h4>Henüz hata taraması yok</h4>
                  <p>Üst çubuktaki Hata Taraması butonundan yeni bir tarama başlatabilirsiniz.</p>
                </div>
              </div>
            </article>

            <article class="module-card debug-column">
              <div class="module-header">
                <div><h3>Bulgular</h3><p>Seçili tarama için tespit edilen bulgu kayıtları burada listelenir.</p></div>
                <div class="module-actions">
                  <span id="debugFindingCountBadge" class="pill info">0 kayıt</span>
                </div>
              </div>
              <div id="debugFindingList" class="debug-finding-list">
                <div class="empty-state">
                  <h4>Bulgu bekleniyor</h4>
                  <p>Bu tarama için henüz bulgu üretilmedi.</p>
                </div>
              </div>
            </article>

            <article class="module-card debug-column">
              <div class="module-header">
                <div><h3>Detay</h3><p>Tarama veya bulgu seçildiğinde teknik özet ve önerilen düzeltme burada görünür.</p></div>
              </div>
              <div id="debugDetailPanel" class="helper-panel">
                <div class="empty-state">
                  <h4>Seçim bekleniyor</h4>
                  <p>Detay görmek için soldan bir tarama veya ortadan bir bulgu seçin.</p>
                </div>
              </div>
            </article>
          </div>
        </section>

        <section data-view="responsewindow" class="section-grid" hidden>
          <div class="response-preview-layout">
            <article class="module-card response-preview-input">
              <div class="module-header">
                <div>
                  <h3>Yanıt Penceresi</h3>
                  <p>Tek müşteri sorusu için bağımsız AI yanıtı üretin.</p>
                </div>
                <span class="pill info">Geçmişsiz</span>
              </div>
              <form id="responsePreviewForm" class="response-preview-form">
                <div class="field">
                  <label for="responsePreviewQuestion">Müşteri sorusu</label>
                  <textarea id="responsePreviewQuestion" name="question" rows="9" maxlength="4000" placeholder="Örn. Havalimanı transfer ücretiniz nedir?"></textarea>
                </div>
                <div class="response-preview-samples" id="responsePreviewSampleList" aria-label="Hızlı test soruları">
                  <button type="button" data-response-sample="Havalimanı transfer ücretiniz nedir?">Transfer</button>
                  <button type="button" data-response-sample="Kahvaltı dahil mi ve saat kaçta başlıyor?">Kahvaltı</button>
                  <button type="button" data-response-sample="Check-in ve check-out saatleriniz nedir?">Check-in</button>
                  <button type="button" data-response-sample="Evcil hayvan kabul ediyor musunuz?">Evcil Hayvan</button>
                </div>
                <div class="field-grid response-preview-options">
                  <div class="field">
                    <label for="responsePreviewLanguage">Yanıt dili</label>
                    <select id="responsePreviewLanguage" name="language" aria-label="Yanıt dili">
                      <option value="auto">Otomatik</option>
                      <option value="tr">Türkçe</option>
                      <option value="en">İngilizce (Britanya)</option>
                      <option value="de">Deutsch</option>
                      <option value="ru">Русский</option>
                    </select>
                  </div>
                  <div class="field">
                    <label for="responsePreviewStyle">Yanıt tonu</label>
                    <select id="responsePreviewStyle" name="response_style" aria-label="Yanıt tonu">
                      <option value="professional">Profesyonel</option>
                      <option value="warm">Sıcak</option>
                      <option value="concise">Kısa</option>
                    </select>
                  </div>
                </div>
                <div class="response-preview-actions">
                  <button id="responsePreviewGenerate" class="action-button primary" type="submit">Yanıt Üret</button>
                  <button id="responsePreviewClear" class="action-button secondary" type="button">Temizle</button>
                </div>
              </form>
              <div id="responsePreviewSafety" class="response-preview-safety">
                <span>Geçmiş kullanılmaz</span>
                <span>Kayıt oluşturulmaz</span>
                <span>Yanıt gönderilmez</span>
              </div>
            </article>

            <article class="module-card response-preview-output">
              <div class="module-header">
                <div>
                  <h3>Üretilen Yanıt</h3>
                  <p id="responsePreviewMeta">Henüz yanıt oluşturulmadı.</p>
                </div>
                <div class="response-preview-output-actions">
                  <button id="responsePreviewTranslate" class="inline-button response-preview-translate" type="button" hidden disabled>Çeviriyi Aç</button>
                  <button id="responsePreviewCopy" class="inline-button response-preview-copy" type="button" disabled>Kopyala</button>
                </div>
              </div>
              <div id="responsePreviewReply" class="response-preview-reply empty-state">
                <p>Yanıt burada görüntülenir.</p>
              </div>
              <div class="response-preview-diagnostics">
                <div>
                  <h4>Araç İzleri</h4>
                  <div id="responsePreviewToolList" class="response-preview-tool-list">
                    <span class="muted">Henüz araç çağrısı yok.</span>
                  </div>
                </div>
                <div>
                  <h4>INTERNAL_JSON</h4>
                  <pre id="responsePreviewInternalJson">{{}}</pre>
                </div>
              </div>
            </article>
          </div>
        </section>

        <section data-view="voicelab" class="section-grid" hidden>
          <div class="voice-lab-summary-grid" id="voiceLabSummaryCards" aria-live="polite">
            <article class="voice-lab-kpi"><h4>Toplam Senaryo</h4><strong id="voiceLabTotalCount">18</strong><span>V001-V018 matrisi</span></article>
            <article class="voice-lab-kpi"><h4>Geçen</h4><strong id="voiceLabPassedCount">0</strong><span>Son koşu sonucu</span></article>
            <article class="voice-lab-kpi"><h4>Başarısız</h4><strong id="voiceLabFailedCount">0</strong><span>Kaynak veya aksiyon ihlali</span></article>
            <article class="voice-lab-kpi"><h4>Bloke</h4><strong id="voiceLabBlockedCount">0</strong><span>Güvenlik veya kapsam dışı</span></article>
          </div>

          <div class="voice-lab-layout">
            <article class="module-card voice-lab-input-card">
              <div class="module-header">
                <div>
                  <h3>Telefon Senaryosu</h3>
                  <p>Canlı hatta çıkmadan önce metin transkriptiyle kaynak, aksiyon ve güvenlik davranışını ölçün.</p>
                </div>
                <span class="pill info">Mock + Realtime</span>
              </div>
              <form id="voiceLabForm" class="voice-lab-form">
                <div class="field full">
                  <label for="voiceLabTranscript">Arama transkripti</label>
                  <textarea id="voiceLabTranscript" name="transcript" rows="9" maxlength="4000" placeholder="Örn. Kredi kartı için taksitlendirme uyguluyor musunuz?"></textarea>
                </div>
                <div class="voice-lab-sample-list" id="voiceLabSampleList" aria-label="Voice Lab hızlı senaryolar">
                  <button type="button" data-voice-sample="V001">Fiyat</button>
                  <button type="button" data-voice-sample="V005">Müsaitlik</button>
                  <button type="button" data-voice-sample="V009">Taksit</button>
                  <button type="button" data-voice-sample="V011">Otopark</button>
                  <button type="button" data-voice-sample="V018">Ölüdeniz</button>
                </div>
                <div class="field-grid voice-lab-options">
                  <div class="field">
                    <label for="voiceLabScenario">Senaryo</label>
                    <select id="voiceLabScenario" name="scenario_id">
                      <option value="">Otomatik eşleştir</option>
                    </select>
                  </div>
                  <div class="field">
                    <label for="voiceLabLanguage">Dil</label>
                    <select id="voiceLabLanguage" name="language">
                      <option value="tr">Türkçe</option>
                      <option value="en">İngilizce</option>
                      <option value="ru">Rusça</option>
                    </select>
                  </div>
                </div>
                <div class="voice-lab-actions">
                  <button id="voiceLabRunButton" class="action-button primary" type="submit">Senaryoyu Çalıştır</button>
                  <button id="voiceLabRunMatrixButton" class="action-button secondary" type="button">Tüm Matrisi Çalıştır</button>
                  <button id="voiceLabClearButton" class="action-button secondary" type="button">Temizle</button>
                </div>
                <div class="voice-lab-audio-preview">
                  <div class="voice-lab-audio-copy">
                    <strong>Ses Önizleme</strong>
                    <span id="voiceLabVoiceStatus" aria-live="polite">Karşılama veya son yanıt sesini dinleyebilirsiniz.</span>
                  </div>
                  <div class="voice-lab-tuning-grid" role="group" aria-label="Ses ayarları">
                    <div class="field">
                      <label for="voiceLabVoiceSelect">Ses tipi</label>
                      <select id="voiceLabVoiceSelect" name="voice_name">
                        <option value="">Dile göre en doğal ses</option>
                      </select>
                    </div>
                    <div class="field voice-lab-slider-field">
                      <label for="voiceLabRate">Konuşma hızı <span id="voiceLabRateValue">0.88x</span></label>
                      <input id="voiceLabRate" name="speech_rate" type="range" min="0.78" max="1.03" step="0.01" value="0.88" aria-label="Konuşma hızı">
                    </div>
                    <div class="field voice-lab-slider-field">
                      <label for="voiceLabPitch">Ses tonu <span id="voiceLabPitchValue">0.96</span></label>
                      <input id="voiceLabPitch" name="speech_pitch" type="range" min="0.86" max="1.06" step="0.01" value="0.96" aria-label="Ses tonu">
                    </div>
                  </div>
                  <div class="voice-lab-voice-actions">
                    <button id="voiceLabSpeakGreetingButton" class="action-button secondary" type="button" aria-label="Karşılama metnini seslendir">Karşılamayı Dinle</button>
                    <button id="voiceLabSpeakReplyButton" class="action-button secondary" type="button" aria-label="Son Voice Lab yanıtını seslendir" disabled>Yanıtı Dinle</button>
                    <button id="voiceLabStopVoiceButton" class="action-button secondary" type="button" aria-label="Sesli oynatmayı durdur">Durdur</button>
                  </div>
                </div>
                <div class="voice-lab-elevenlabs-preview">
                  <div class="voice-lab-provider-head">
                    <div class="voice-lab-audio-copy">
                      <strong>ElevenLabs Entegrasyonu</strong>
                      <span id="voiceLabElevenLabsStatus" aria-live="polite">Bağlantı yapılandırması bekleniyor.</span>
                    </div>
                    <span id="voiceLabElevenLabsBadge" class="pill warn">Hazır değil</span>
                  </div>
                  <div class="voice-lab-elevenlabs-grid" role="group" aria-label="ElevenLabs ayarları">
                    <div class="field">
                      <label for="voiceLabElevenLabsKeyStatus">API anahtarı</label>
                      <input id="voiceLabElevenLabsKeyStatus" type="text" value="Sunucu ENV üzerinde tutulur" disabled aria-label="ElevenLabs API anahtarı durumu">
                    </div>
                    <div class="field">
                      <label for="voiceLabElevenLabsVoiceId">Voice ID / preset</label>
                      <input id="voiceLabElevenLabsVoiceId" name="elevenlabs_voice_id" type="text" maxlength="120" placeholder="Voice ID veya otel preset adı">
                    </div>
                    <div class="field">
                      <label for="voiceLabElevenLabsProfile">Model profili</label>
                      <select id="voiceLabElevenLabsProfile" name="elevenlabs_profile">
                        <option value="quality">Kalite öncelikli</option>
                        <option value="balanced">Dengeli</option>
                        <option value="low_latency">Düşük gecikme</option>
                      </select>
                    </div>
                    <div class="field voice-lab-slider-field">
                      <label for="voiceLabElevenLabsStability">Stabilite <span id="voiceLabElevenLabsStabilityValue">0.50</span></label>
                      <input id="voiceLabElevenLabsStability" name="elevenlabs_stability" type="range" min="0" max="1" step="0.01" value="0.50" aria-label="ElevenLabs stabilite">
                    </div>
                    <div class="field voice-lab-slider-field">
                      <label for="voiceLabElevenLabsSimilarity">Benzerlik <span id="voiceLabElevenLabsSimilarityValue">0.75</span></label>
                      <input id="voiceLabElevenLabsSimilarity" name="elevenlabs_similarity" type="range" min="0" max="1" step="0.01" value="0.75" aria-label="ElevenLabs ses benzerliği">
                    </div>
                    <div class="field voice-lab-slider-field">
                      <label for="voiceLabElevenLabsStyle">Stil <span id="voiceLabElevenLabsStyleValue">0.20</span></label>
                      <input id="voiceLabElevenLabsStyle" name="elevenlabs_style" type="range" min="0" max="1" step="0.01" value="0.20" aria-label="ElevenLabs stil ayarı">
                    </div>
                  </div>
                  <div class="voice-lab-provider-actions">
                    <button id="voiceLabElevenLabsSaveButton" class="action-button secondary" type="button">Ayarları Kaydet</button>
                    <button id="voiceLabElevenLabsTestButton" class="action-button secondary" type="button">Bağlantıyı Test Et</button>
                  </div>
                  <div class="voice-lab-provider-safety">
                    <span>API key panelde görünmez</span>
                    <span>Backend endpoint bekliyor</span>
                    <span>Canlı çağrı yapılmaz</span>
                  </div>
                </div>
                <div class="voice-lab-realtime-preview">
                  <div class="voice-lab-audio-copy">
                    <strong>OpenAI Realtime</strong>
                    <span id="voiceLabRealtimeStatus" aria-live="polite">Mikrofon bağlantısı bekliyor.</span>
                  </div>
                  <div class="voice-lab-realtime-grid">
                    <div class="field">
                      <label for="voiceLabRealtimeVoice">Realtime ses</label>
                      <select id="voiceLabRealtimeVoice" name="realtime_voice">
                        <option value="marin">Marin (önerilen)</option>
                        <option value="cedar">Cedar (önerilen)</option>
                        <option value="alloy">Alloy</option>
                        <option value="ash">Ash</option>
                        <option value="ballad">Ballad</option>
                        <option value="coral">Coral</option>
                        <option value="echo">Echo</option>
                        <option value="sage">Sage</option>
                        <option value="shimmer">Shimmer</option>
                        <option value="verse">Verse</option>
                      </select>
                    </div>
                    <div class="voice-lab-realtime-actions">
                      <button id="voiceLabRealtimeStartButton" class="action-button primary" type="button">OpenAI Realtime ile Konuş</button>
                      <button id="voiceLabRealtimeStopButton" class="action-button secondary" type="button" disabled>Realtime Durdur</button>
                    </div>
                  </div>
                  <div id="voiceLabRealtimeMeter" class="voice-lab-audio-meter" aria-label="Canlı mikrofon seviyesi">
                    <div class="voice-lab-meter-head">
                      <strong>Canlı ses seviyesi</strong>
                      <span id="voiceLabRealtimeMeterText" aria-live="polite">Bekliyor</span>
                    </div>
                    <div id="voiceLabRealtimeMeterBars" class="voice-lab-meter-bars" aria-hidden="true">
                      <span></span><span></span><span></span><span></span><span></span><span></span>
                      <span></span><span></span><span></span><span></span><span></span><span></span>
                    </div>
                  </div>
                </div>
              </form>
              <div id="voiceLabSafety" class="voice-lab-safety">
                <span>Canlı arama yok</span>
                <span>Yerel ses kaydı yok</span>
                <span>Realtime açıkken mikrofon OpenAI'a gider</span>
                <span>ElevenLabs key panelde görünmez</span>
                <span>DB yazımı yok</span>
                <span>PMS yazımı yok</span>
              </div>
            </article>

            <article class="module-card voice-lab-result-card">
              <div class="module-header">
                <div>
                  <h3>Koşu Sonucu</h3>
                  <p id="voiceLabResultMeta">Henüz senaryo çalıştırılmadı.</p>
                </div>
                <span id="voiceLabResultBadge" class="pill info">Bekliyor</span>
              </div>
              <div id="voiceLabResultPanel" class="voice-lab-result-panel" aria-live="polite">
                <div class="empty-state">
                  <h4>Seçim bekleniyor</h4>
                  <p>Bir senaryo çalıştırıldığında kaynak, aksiyon, cevap ve ihlal listesi burada görünür.</p>
                </div>
              </div>
            </article>
          </div>

          <article class="module-card voice-lab-matrix-card">
            <div class="module-header">
              <div>
                <h3>Senaryo Matrisi</h3>
                <p>V001-V018 koşularının son durumu, kaynak/aksiyon ve hata ayrıntıları.</p>
              </div>
              <span id="voiceLabMatrixBadge" class="pill info">Henüz koşulmadı</span>
            </div>
            <div class="table-shell voice-lab-table-shell">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Durum</th>
                    <th>Niyet</th>
                    <th>Kaynak</th>
                    <th>Aksiyon</th>
                    <th>İhlal</th>
                  </tr>
                </thead>
                <tbody id="voiceLabMatrixBody">
                  <tr><td colspan="6"><div class="empty-state"><p>Matris koşusu bekleniyor.</p></div></td></tr>
                </tbody>
              </table>
            </div>
          </article>
        </section>

        <section data-view="chatlab" class="section-grid" hidden>
          <iframe id="chatlab-frame" class="chatlab-frame"></iframe>
        </section>
      </section>
    </main>
  </div>

  <dialog id="responsePreviewTranslationDialog" class="dialog response-translation-dialog" aria-labelledby="responsePreviewTranslationTitle">
    <div class="dialog-card response-translation-card">
      <div class="dialog-head response-translation-head">
        <div>
          <h3 id="responsePreviewTranslationTitle">Çeviri</h3>
          <p id="responsePreviewTranslationMeta">Yanıt çevirisi henüz hazır değil.</p>
        </div>
        <button id="responsePreviewTranslationClose" class="inline-button secondary" type="button" aria-label="Çeviri penceresini kapat">Kapat</button>
      </div>
      <div id="responsePreviewTranslationBody" class="response-translation-body">
        <div class="empty-state">
          <p>Çeviri burada görüntülenir.</p>
        </div>
      </div>
    </div>
  </dialog>

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
            <div id="serviceModeCanvas" class="floor-plan-canvas service-mode-canvas" aria-label="Servis modu masa planı"></div>
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

  <dialog id="whatsappConnectDialog" class="dialog" aria-label="WhatsApp Meta bağlantısı">
    <div class="dialog-card">
      <div class="dialog-head">
        <h3>Meta ile Bağlan</h3>
        <p id="whatsappConnectStatus">Bağlantı oturumu bekleniyor.</p>
      </div>
      <div id="whatsappOauthSteps" class="field-grid">
        <div class="whatsapp-oauth-step"><span>1</span><div><strong>Oturum oluştur</strong><p>Backend kısa süreli ve CSRF durumu içeren bağlantı oturumu üretir.</p></div></div>
        <div class="whatsapp-oauth-step"><span>2</span><div><strong>Meta açılır penceresi</strong><p>Yetkilendirme ayrı açılır pencerede tamamlanır; token frontend'e dönmez.</p></div></div>
        <div class="whatsapp-oauth-step"><span>3</span><div><strong>Numara seçimi</strong><p>Yetki sonrası erişilebilir WhatsApp numaraları backend'den alınır ve seçilen numara aktif bağlantıya dönüştürülür.</p></div></div>
      </div>
      <div id="whatsappAssets" class="whatsapp-asset-picker"></div>
      <div class="dialog-actions">
        <button id="whatsappConnectCancel" class="inline-button secondary" type="button">Kapat</button>
        <button id="whatsappConnectLaunch" class="inline-button primary" type="button">Meta Penceresini Aç</button>
      </div>
    </div>
  </dialog>

  <dialog id="whatsappGuideDialog" class="dialog whatsapp-guide-dialog" aria-label="WhatsApp Cloud API kurulum rehberi">
    <div class="dialog-card">
      <div class="dialog-head">
        <h3>WhatsApp Meta Cloud API Kurulum Rehberi</h3>
        <p>Bu rehber, teknik bilgisi sınırlı kullanıcıların Meta tarafında doğru bilgileri bulup Velox'a güvenli ve eksiksiz bağlaması için hazırlanmıştır.</p>
      </div>
      <div class="whatsapp-guide-body mt-md">
        <div class="whatsapp-guide-intro">
          <section class="whatsapp-guide-panel">
            <span class="whatsapp-guide-kicker">Önerilen yol</span>
            <h4>Önce Meta ile Bağlan akışını deneyin</h4>
            <p>Bu ekrandaki <strong>Meta ile Bağlan</strong> düğmesi kullanıcıyı mümkün olduğunca Velox içinde tutar. Meta oturumu güvenli açılır pencerede tamamlanır, token frontend'e yazılmaz, yetki sonrası erişilebilir WhatsApp numaraları burada listelenir.</p>
            <ul class="whatsapp-guide-safe-list">
              <li>Açılır pencere açılırsa manuel formu doldurmanız gerekmez.</li>
              <li>Token şifreli saklanır ve ekranda geri gösterilmez.</li>
              <li>Bağlantıdan sonra webhook, sağlık kontrolü ve şablon senkronizasyonu bu ekrandan yapılır.</li>
            </ul>
          </section>
          <section class="whatsapp-guide-mini-screen" aria-label="Meta kurulum ekranı örneği">
            <div class="whatsapp-guide-mini-top"><span class="whatsapp-guide-mini-dot"></span><span class="whatsapp-guide-mini-dot"></span><span class="whatsapp-guide-mini-dot"></span></div>
            <div class="whatsapp-guide-mini-body">
              <div class="whatsapp-guide-mini-row"><strong>İşletme Ayarları</strong><span>İşletme Kimliği</span></div>
              <div class="whatsapp-guide-mini-row"><strong>WhatsApp Yöneticisi</strong><span>WABA Kimliği</span></div>
              <div class="whatsapp-guide-mini-row"><strong>API Kurulumu</strong><span>Telefon Numarası Kimliği</span></div>
              <div class="whatsapp-guide-mini-row"><strong>Webhook'lar</strong><span>Geri Çağrı URL'si + Doğrulama Token'ı</span></div>
              <div class="whatsapp-guide-mini-row"><strong>Şablonlar</strong><span>24 saat dışı mesajlar</span></div>
            </div>
          </section>
        </div>

        <section class="whatsapp-guide-result" aria-label="Kurulum sonucunda beklenen durum">
          <div><strong>Bağlantı</strong><span>Doğru WhatsApp numarası Velox'a bağlı görünür.</span></div>
          <div><strong>Webhook</strong><span>Meta gelen mesajları herkese açık HTTPS uç noktasına gönderir.</span></div>
          <div><strong>Token</strong><span>Gerekli izinlere sahip, canlı kullanım için uygun token saklanır.</span></div>
          <div><strong>Şablon</strong><span>24 saatlik pencere kapalıyken kullanılacak onaylı mesajlar hazırdır.</span></div>
        </section>

        <section class="whatsapp-guide-panel">
          <span class="whatsapp-guide-kicker">Ön kontrol</span>
          <h4>Başlamadan önce 5 dakikalık kontrol</h4>
          <p>Bu maddeler hazır değilse kurulum sırasında numara görünmeme, webhook doğrulanmama veya mesaj gönderememe hataları oluşur.</p>
          <div class="whatsapp-guide-checklist">
            <div class="whatsapp-guide-checkitem"><b>✓</b><span>Meta Business portföyünde yönetici yetkiniz var.</span></div>
            <div class="whatsapp-guide-checkitem"><b>✓</b><span>Bağlanacak telefon numarası SMS veya sesli arama ile doğrulama alabiliyor.</span></div>
            <div class="whatsapp-guide-checkitem"><b>✓</b><span>Velox webhook adresi herkese açık HTTPS üzerinden erişilebilir. Localhost veya HTTP kullanılmaz.</span></div>
            <div class="whatsapp-guide-checkitem"><b>✓</b><span>Meta uygulaması tarafında WhatsApp ve Webhook ürünleri yapılandırılmış.</span></div>
            <div class="whatsapp-guide-checkitem"><b>✓</b><span>Canlı kullanım için kısa süreli test token yerine sistem kullanıcısı veya uzun ömürlü uygun token planlandı.</span></div>
            <div class="whatsapp-guide-checkitem"><b>✓</b><span>İlk giden mesajlar için en az bir onaylı yardımcı işlem şablonu hazırlamayı planladınız.</span></div>
          </div>
        </section>

        <section class="whatsapp-guide-panel">
          <span class="whatsapp-guide-kicker">Yol seçimi</span>
          <h4>Hangi yolu seçmeliyim?</h4>
          <div class="whatsapp-guide-path-grid">
            <div class="whatsapp-guide-path-card recommended">
              <strong>Meta ile Bağlan</strong>
              <span class="whatsapp-guide-badge">Önerilen</span>
              <p>Yeni kullanıcılar için en güvenli akıştır. Açılır pencere içinde Meta izni alınır, Velox erişilebilir WABA ve numaraları backend üzerinden listeler.</p>
              <ul>
                <li>Token tarayıcıda görünmez.</li>
                <li>ID karıştırma riski azalır.</li>
                <li>Numara seçimi Velox içinde tamamlanır.</li>
              </ul>
            </div>
            <div class="whatsapp-guide-path-card">
              <strong>Gelişmiş Manuel Kayıt</strong>
              <span class="whatsapp-guide-badge">Yedek yol</span>
              <p>Sadece açılır pencere akışı çalışmıyorsa veya teknik ekip Meta bilgilerini ayrıca verdiyse kullanın. Her alanı Meta'daki doğru kaynaktan kopyalamak gerekir.</p>
              <ul>
                <li>İşletme Kimliği, WABA Kimliği ve Telefon Numarası Kimliği karıştırılmamalı.</li>
                <li>Erişim token'ı izinleri manuel kontrol edilmeli.</li>
                <li>Webhook doğrulama token'ı backend değeriyle aynı olmalı.</li>
              </ul>
            </div>
          </div>
        </section>

        <section class="whatsapp-guide-flow" aria-label="Kurulum adımları">
          <div class="whatsapp-guide-step">
            <b>1</b>
            <div>
              <h4>Meta Business hesabını hazırlayın</h4>
              <p>Kurulumu yapacak kişinin Meta Business portföyünde yönetici veya gerekli varlık yetkilerine sahip olması gerekir. İşletme adı, web sitesi, ülke ve iletişim bilgileri doğru olmalıdır.</p>
              <ul>
                <li>İşletme Ayarları ekranında doğru işletme portföyünü seçin.</li>
                <li>WhatsApp hesabı ve telefon numarası aynı işletme altında veya size paylaşılmış varlık olarak görünmeli.</li>
                <li>İşletme doğrulaması her kurulumda ilk dakika şartı olmayabilir, fakat canlı kullanım, limit ve güvenilirlik için eksik bırakılmamalıdır.</li>
              </ul>
            </div>
          </div>

          <div class="whatsapp-guide-step">
            <b>2</b>
            <div>
              <h4>İşletme Kimliği, WABA Kimliği ve Telefon Numarası Kimliği ayrımını netleştirin</h4>
              <p>Meta tarafında üç farklı kimlik vardır. Bunlar aynı şey değildir ve yanlış alana yazılırsa bağlantı başarısız olur.</p>
              <ul>
                <li><strong>İşletme Kimliği</strong>: Meta Business portföyünün kimliğidir.</li>
                <li><strong>WABA Kimliği</strong>: WhatsApp İşletme Hesabı kimliğidir.</li>
                <li><strong>Telefon Numarası Kimliği</strong>: Mesaj gönderecek telefonun API kimliğidir. Telefon Numarası Kimliği, görünen telefon numarası değildir.</li>
              </ul>
            </div>
          </div>

          <div class="whatsapp-guide-step">
            <b>3</b>
            <div>
              <h4>Telefon numarasını Cloud API için hazır edin</h4>
              <p>Meta, telefon numarasının WABA altında görünmesini ve Cloud API için kayıtlı olmasını bekler. Kayıt sırasında 6 haneli iki adımlı doğrulama PIN'i belirlenebilir.</p>
              <ul>
                <li>Numara WhatsApp Business uygulamasında aktifse taşıma veya bağlantı kısıtlarını kontrol edin.</li>
                <li>Gömülü kayıt akışıyla bağlanan numaranın kayıt adımı geciktirilmemelidir; Meta tarafında süre sınırı olabilir.</li>
                <li>PIN'i kaybederseniz ileride numara yönetimi zorlaşır; güvenli yerde saklayın, chat içinde paylaşmayın.</li>
              </ul>
            </div>
          </div>

          <div class="whatsapp-guide-step">
            <b>4</b>
            <div>
              <h4>Velox'ta Meta ile Bağlan akışını çalıştırın</h4>
              <p>Bu sayfada <strong>Meta ile Bağlan</strong> düğmesine basın, ardından <strong>Meta Penceresini Aç</strong> ile yetkilendirmeyi tamamlayın. Meta ekranı güvenlik nedeniyle iframe içinde açılamazsa açılır pencere kullanılır.</p>
              <ul>
                <li>Açılır pencere engellenirse tarayıcı adres çubuğundan bu site için açılır pencere izni verin.</li>
                <li>Meta girişinden sonra doğru işletme ve doğru WhatsApp numarasını seçin.</li>
                <li>Velox'a döndüğünüzde listelenen numaradan gerçek otel numarasını seçin.</li>
              </ul>
            </div>
          </div>

          <div class="whatsapp-guide-step">
            <b>5</b>
            <div>
              <h4>Webhook'u doğrulayın ve WABA'ya abone edin</h4>
              <p>Meta'nın gelen mesajları Velox'a göndermesi için Webhook ürünü, geri çağrı URL'si, doğrulama token'ı ve WABA aboneliği tamamlanmalıdır.</p>
              <ul>
                <li>Webhook URL'si herkese açık HTTPS olmalı ve bu sistemde <code>/api/v1/webhook/whatsapp</code> yoluna gitmelidir.</li>
                <li>Doğrulama token'ı değeri backend tarafındaki <code>WHATSAPP_VERIFY_TOKEN</code> ile aynı olmalıdır.</li>
                <li>Bu ekrandaki <strong>Webhook Abone Et</strong> düğmesi WABA aboneliğini tamamlamaya çalışır.</li>
              </ul>
            </div>
          </div>

          <div class="whatsapp-guide-step">
            <b>6</b>
            <div>
              <h4>Erişim token'ı izinlerini kontrol edin</h4>
              <p>Token, mesaj göndermek ve WABA varlıklarını yönetmek için doğru izinlere sahip olmalıdır. Erişim token'ı, uygulama gizli anahtarı veya doğrulama token'ı değildir.</p>
              <ul>
                <li>Mesaj göndermek için <code>whatsapp_business_messaging</code> gerekir.</li>
                <li>WABA, numara, şablon ve webhook yönetimi için <code>whatsapp_business_management</code> gerekir.</li>
                <li>Bazı varlık listeleme ve katılım akışlarında <code>business_management</code> gerekebilir.</li>
              </ul>
            </div>
          </div>

          <div class="whatsapp-guide-step">
            <b>7</b>
            <div>
              <h4>Sağlık kontrolünü çalıştırın</h4>
              <p><strong>Sağlık Kontrolü</strong> düğmesi token, Telefon Numarası Kimliği, WABA eşleşmesi ve webhook durumunu doğrulamak için kullanılır. Kartlarda kırmızı veya uyarı durumu varsa canlı kullanıma geçmeyin.</p>
              <ul>
                <li>Bağlantı kartında doğru görünen numara olmalı.</li>
                <li>Webhook kartında doğru herkese açık URL görünmeli.</li>
                <li>Token kartı kayıtlı token olduğunu göstermeli, ham token görünmemeli.</li>
              </ul>
            </div>
          </div>

          <div class="whatsapp-guide-step">
            <b>8</b>
            <div>
              <h4>Şablon mesajlarını hazırlayın</h4>
              <p>Misafir size son 24 saat içinde yazdıysa serbest yanıt gönderebilirsiniz. 24 saatlik pencere kapandıysa, yeni mesaj başlatmak için Meta tarafından onaylı şablon gerekir.</p>
              <ul>
                <li>Meta'da şablon adı, dil, kategori ve değişken örneklerini girip onaya gönderin.</li>
                <li>Otel hatırlatmaları için genelde yardımcı işlem şablonu kullanılır; pazarlama içeriklerini ayrıca değerlendirin.</li>
                <li>Onaylandıktan sonra bu ekrandan <strong>Meta'dan Senkronize Et</strong> ile Velox listesini güncelleyin.</li>
              </ul>
            </div>
          </div>

          <div class="whatsapp-guide-step">
            <b>9</b>
            <div>
              <h4>Canlı test yapın</h4>
              <p>Kurulum bittiğinde gerçek kullanıcı verisi kullanmadan test numarasıyla uçtan uca kontrol yapın. Önce test numarasından WhatsApp mesajı gönderin, sonra Velox'un cevap verebildiğini doğrulayın.</p>
              <ul>
                <li>Gelen mesaj bağlantı günlüğünde veya ilgili sohbet akışında görünmeli.</li>
                <li>İçeriden gönderilen test mesajı WhatsApp'a ulaşmalı.</li>
                <li>24 saat dışı senaryo için onaylı şablon ile ayrıca deneme yapılmalı.</li>
              </ul>
            </div>
          </div>
        </section>

        <section class="whatsapp-guide-panel">
          <span class="whatsapp-guide-kicker">Manuel form</span>
          <h4>Her alanı nereden bulurum ve neyle karıştırmamalıyım?</h4>
          <div class="whatsapp-field-grid">
            <div class="whatsapp-field-card"><strong>İşletme Kimliği</strong><p>Meta Business portföyünün kimliğidir. İşletme Ayarları ekranında veya URL'deki <code>business_id</code> değerinde görülür.</p><small>WABA kimliği değildir.</small></div>
            <div class="whatsapp-field-card"><strong>WABA Kimliği</strong><p>WhatsApp İşletme Hesabı kimliğidir. WhatsApp Yöneticisi veya İşletme Ayarları içindeki WhatsApp hesabı detayından alınır.</p><small>Bir işletmede birden fazla WABA olabilir.</small></div>
            <div class="whatsapp-field-card"><strong>Telefon Numarası Kimliği</strong><p>Mesaj gönderecek telefonun API kimliğidir. WABA altındaki telefon numaraları veya API Kurulumu ekranında görünür.</p><small>+90 ile başlayan görünen telefon numarası değildir.</small></div>
            <div class="whatsapp-field-card"><strong>Görünen numara</strong><p>Kullanıcının WhatsApp'ta gördüğü numaradır. Kontrol amaçlıdır; API çağrılarında Telefon Numarası Kimliği kullanılır.</p><small>Yanlış numara seçimini fark etmek için doldurun.</small></div>
            <div class="whatsapp-field-card"><strong>Token izin kapsamı</strong><p>Token'ın sahip olduğu izinleri virgülle yazabilirsiniz: <code>whatsapp_business_messaging,whatsapp_business_management</code>.</p><small>Eksik izin kapsamı mesaj veya webhook hatası üretir.</small></div>
            <div class="whatsapp-field-card"><strong>Erişim token'ı</strong><p>Meta Graph API'ye erişim anahtarıdır. Yalnızca şifre alanına girilir, kayıttan sonra geri gösterilmez.</p><small>Erişim token'ı, uygulama gizli anahtarı veya doğrulama token'ı değildir.</small></div>
            <div class="whatsapp-field-card"><strong>Webhook doğrulama token'ı</strong><p>Meta webhook doğrulamasında sizin belirlediğiniz gizli metindir. Backend'deki <code>WHATSAPP_VERIFY_TOKEN</code> ile birebir aynı olmalıdır.</p><small>Erişim token'ı yerine yazılmaz.</small></div>
            <div class="whatsapp-field-card"><strong>Webhook URL'si</strong><p>Meta'nın gelen mesajları göndereceği herkese açık HTTPS adresidir. Bu sistemde <code>/api/v1/webhook/whatsapp</code> yoluna gider.</p><small>HTTP, localhost veya erişilemeyen intranet adresi kullanmayın.</small></div>
          </div>
        </section>

        <section class="whatsapp-guide-panel">
          <span class="whatsapp-guide-kicker">Sorun çözme</span>
          <h4>Takılırsanız hızlı teşhis tablosu</h4>
          <div class="whatsapp-guide-troubleshoot">
            <div class="whatsapp-trouble-card"><strong>Açılır pencere açılmıyor</strong><p>Tarayıcı açılır pencereyi engelliyor olabilir. Adres çubuğundaki uyarıdan <code>velox.nexlumeai.com</code> için izin verin ve Meta Penceresini Aç düğmesine tekrar basın.</p></div>
            <div class="whatsapp-trouble-card"><strong>Meta'da numara görünmüyor</strong><p>Yanlış işletme seçilmiş, WABA size paylaşılmamış veya token izinleri eksik olabilir. İşletme Kimliği, WABA erişimi ve <code>whatsapp_business_management</code> iznini kontrol edin.</p></div>
            <div class="whatsapp-trouble-card"><strong>Sağlık kontrolü başarısız</strong><p>Token süresi dolmuş, Telefon Numarası Kimliği yanlış, numara kayıtlı değil veya token bu WABA'ya yetkili değil olabilir. Önce kimlik eşleşmesini, sonra token izin kapsamı listesini kontrol edin.</p></div>
            <div class="whatsapp-trouble-card"><strong>Webhook abone edilemiyor</strong><p>Meta uygulaması içinde Webhook ürünü eksik, geri çağrı URL'si doğrulanmamış veya WABA aboneliği için yönetim izni eksik olabilir. Doğrulama token'ı eşleşmesini ve herkese açık HTTPS erişimini kontrol edin.</p></div>
            <div class="whatsapp-trouble-card"><strong>Gelen mesaj Velox'a düşmüyor</strong><p>WABA aboneliği yapılmamış, webhook mesajlar alanı aktif değil, geri çağrı URL'si yanlış veya uygulama gizli anahtarıyla imza doğrulaması başarısız olabilir. Bağlantı Günlüğü ve webhook durum kartını kontrol edin.</p></div>
            <div class="whatsapp-trouble-card"><strong>24 saat sonrası mesaj gitmiyor</strong><p>Serbest metin yalnızca açık müşteri hizmeti penceresinde gönderilebilir. Pencere kapalıysa onaylı şablon seçin veya şablonu Meta'da onaya gönderin.</p></div>
          </div>
        </section>

        <section class="whatsapp-guide-warning danger">
          <h4>En sık yapılan hatalar</h4>
          <ul>
            <li>Görünen telefon numarasını Telefon Numarası Kimliği alanına yazmak.</li>
            <li>WABA Kimliği yerine İşletme Kimliği girmek veya tam tersini yapmak.</li>
            <li>Erişim token'ı, uygulama gizli anahtarı veya doğrulama token'ı değerlerini birbirinin yerine kullanmak.</li>
            <li>24 saat süresi dolmuş kullanıcıya onaysız serbest mesaj göndermeye çalışmak.</li>
            <li>Test ekranındaki kısa süreli token ile canlı kullanıma geçmek.</li>
            <li>Webhook URL'sini HTTP veya localhost olarak ayarlamak; Meta için herkese açık HTTPS gerekir.</li>
            <li>Telefon numarası kayıt/iki adımlı doğrulama PIN adımını tamamlamadan mesaj göndermeyi denemek.</li>
          </ul>
        </section>

        <section class="whatsapp-guide-warning">
          <h4>Bittiğini nasıl anlarım?</h4>
          <ul>
            <li>Bağlantı durum kartında doğru WhatsApp numarası ve Telefon Numarası Kimliği görünüyor.</li>
            <li>Webhook durumu doğrulandı veya <strong>Webhook Abone Et</strong> işlemi başarılı oldu.</li>
            <li><strong>Sağlık Kontrolü</strong> token, WABA ve Telefon Numarası Kimliği eşleşmesini onayladı.</li>
            <li>En az bir onaylı şablon <strong>Meta'dan Senkronize Et</strong> ile Velox listesine geldi.</li>
            <li>Test numarasından gelen mesaj Velox'a düştü ve Velox'tan gönderilen yanıt WhatsApp'a ulaştı.</li>
            <li>24 saatlik pencere dışında serbest metin yerine onaylı şablon kullanıldığını test ettiniz.</li>
          </ul>
        </section>
      </div>
      <div class="dialog-actions">
        <button id="whatsappGuideClose" class="inline-button primary" type="button">Rehberi Kapat</button>
      </div>
    </div>
  </dialog>

  <dialog id="debugRunDialog" class="dialog" aria-label="Canlı hata taraması">
    <div class="dialog-card">
      <div class="dialog-head">
        <h3>Canlı Hata Taraması</h3>
        <p>Bu işlem canlı veriyi değiştirmez. Sadece hata ve kalite raporu üretir.</p>
      </div>
      <form id="debugRunForm" class="field-grid" method="dialog">
        <div class="field full">
          <label>Kapsam</label>
          <div class="choice-group">
            <label class="choice-card">
              <input id="debugScopeAllPanel" name="debug_scope_target" type="radio" value="all_panel" checked>
              <span>Tüm panel</span>
            </label>
            <label class="choice-card">
              <input id="debugScopeCurrentView" name="debug_scope_target" type="radio" value="current_view">
              <span>Aktif görünüm</span>
            </label>
          </div>
        </div>
        <div class="field full">
          <label class="toggle-row" for="debugIncludeChatLab">
            <span class="toggle-copy">
              <strong>Test paneli iframe'i dahil</strong>
              <small>Tarama sırasında test paneli iframe içeriğini de tarar.</small>
            </span>
            <span class="switch">
              <input id="debugIncludeChatLab" name="include_chatlab_iframe" type="checkbox" checked>
              <span class="switch-track"><span class="switch-thumb"></span></span>
            </span>
          </label>
        </div>
        <div class="field full">
          <label class="toggle-row" for="debugIncludePopups">
            <span class="toggle-copy">
              <strong>Açılır pencere ve yeni pencereleri izle</strong>
              <small>Yeni sekme, açılır pencere ve dialog yüzeyleri varsa rapora dahil edilir.</small>
            </span>
            <span class="switch">
              <input id="debugIncludePopups" name="include_popups" type="checkbox" checked>
              <span class="switch-track"><span class="switch-thumb"></span></span>
            </span>
          </label>
        </div>
        <div class="field full">
          <label class="toggle-row" for="debugIncludeModals">
            <span class="toggle-copy">
              <strong>Modal ve açılır panel davranışlarını dahil et</strong>
              <small>Katman, çekmece ve panel açma/kapama akışları güvenli modda test edilir.</small>
            </span>
            <span class="switch">
              <input id="debugIncludeModals" name="include_modals" type="checkbox" checked>
              <span class="switch-track"><span class="switch-thumb"></span></span>
            </span>
          </label>
        </div>
        <div class="field full">
          <div class="helper-box">
            <strong>Yalnızca raporlama koruması açık</strong>
            <p>Kaydetme, gönderme, onaylama ve silme gibi canlı veriyi etkileyen adımlar hata ayıklama oturumunda engellenecektir.</p>
          </div>
        </div>
        <div class="field full dialog-actions">
          <button id="debugRunCancelButton" class="inline-button secondary" type="button">İptal</button>
          <button class="inline-button primary" type="submit">Taramayı Başlat</button>
        </div>
      </form>
    </div>
  </dialog>

  <dialog id="debugArtifactPreviewDialog" class="dialog debug-artifact-dialog" aria-label="Kanıt önizleme">
    <div class="dialog-card debug-artifact-dialog-card">
      <div class="dialog-head">
        <h3 id="debugArtifactPreviewTitle">Kanıt önizleme</h3>
        <p id="debugArtifactPreviewMeta">Seçili kanıtın ayrıntıları burada görünür.</p>
      </div>
      <div class="debug-artifact-preview-shell">
        <img id="debugArtifactPreviewImage" class="debug-artifact-preview-large" alt="Kanıt önizleme" hidden>
        <div id="debugArtifactPreviewEmpty" class="debug-empty-compact" hidden>
          <h4>Önizleme yok</h4>
          <p>Bu kanıt görsel önizlemeyi desteklemiyor. Dosyayı yeni sekmede açabilirsiniz.</p>
        </div>
      </div>
      <div class="debug-artifact-preview-meta">
        <strong id="debugArtifactPreviewPath" class="mono">-</strong>
        <div class="debug-artifact-actions">
          <a id="debugArtifactPreviewLink" class="debug-artifact-link" href="#" target="_blank" rel="noopener noreferrer">Yeni Sekmede Aç</a>
        </div>
      </div>
      <div class="dialog-actions">
        <button id="debugArtifactPreviewCloseButton" class="inline-button secondary" type="button">Kapat</button>
      </div>
    </div>
  </dialog>

  <script>window.ADMIN_PANEL_CONFIG = {config_json};</script>
  <script>{ADMIN_PANEL_SCRIPT}</script>
  <script>{ADMIN_HOLDS_SCRIPT}</script>
  <script>{ADMIN_RESTAURANT_SCRIPT}</script>
  <script>{ADMIN_RESTAURANT_AI_SCRIPT}</script>
  <script>{ADMIN_WHATSAPP_SCRIPT}</script>
</body>
</html>
"""


if ADMIN_PANEL_ROUTE == "/admin":

    @router.get("/admin", response_class=HTMLResponse)
    async def admin_panel_ui() -> HTMLResponse:
        """Serve the standalone admin panel HTML."""
        return HTMLResponse(content=render_admin_panel_html(), headers=ADMIN_UI_NO_STORE_HEADERS)

    @router.get("/admin/response-review", response_class=HTMLResponse)
    async def response_review_ui() -> HTMLResponse:
        """Serve the response review flow under a separate admin URL."""
        return HTMLResponse(content=render_admin_panel_html(initial_view="responsereview"), headers=ADMIN_UI_NO_STORE_HEADERS)

else:

    @router.get(ADMIN_PANEL_ROUTE, response_class=HTMLResponse)
    async def admin_panel_ui() -> HTMLResponse:
        """Serve the standalone admin panel HTML using configured path."""
        return HTMLResponse(content=render_admin_panel_html(), headers=ADMIN_UI_NO_STORE_HEADERS)

    @router.get(f"{ADMIN_PANEL_ROUTE.rstrip('/')}/response-review", response_class=HTMLResponse)
    async def response_review_ui() -> HTMLResponse:
        """Serve the response review flow under the configured admin URL."""
        return HTMLResponse(content=render_admin_panel_html(initial_view="responsereview"), headers=ADMIN_UI_NO_STORE_HEADERS)

    @router.get("/admin", response_class=HTMLResponse, include_in_schema=False)
    async def admin_panel_ui_legacy() -> HTMLResponse:
        """Serve admin UI on legacy path for compatibility during cutover."""
        return HTMLResponse(content=render_admin_panel_html(), headers=ADMIN_UI_NO_STORE_HEADERS)

    @router.get("/admin/response-review", response_class=HTMLResponse, include_in_schema=False)
    async def response_review_ui_legacy() -> HTMLResponse:
        """Serve response review UI on legacy admin path for compatibility."""
        return HTMLResponse(content=render_admin_panel_html(initial_view="responsereview"), headers=ADMIN_UI_NO_STORE_HEADERS)


# ── POST fallback: prevent 405 when JS fails and browser submits the login
# form natively to the current URL (POST /admin). Redirect back to GET /admin
# so the user sees the panel page instead of a raw JSON error. ──


@router.post("/admin", response_class=RedirectResponse, include_in_schema=False)
async def admin_panel_post_fallback() -> RedirectResponse:
    """Catch accidental native form POST to /admin and redirect to GET."""
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/admin/response-review", response_class=RedirectResponse, include_in_schema=False)
async def response_review_post_fallback() -> RedirectResponse:
    """Catch accidental native form POST to response review and redirect to GET."""
    return RedirectResponse(url="/admin/response-review", status_code=303)


if ADMIN_PANEL_ROUTE != "/admin":

    @router.post(ADMIN_PANEL_ROUTE, response_class=RedirectResponse, include_in_schema=False)
    async def admin_panel_post_fallback_custom() -> RedirectResponse:
        """Catch accidental native form POST to custom admin path and redirect."""
        return RedirectResponse(url=ADMIN_PANEL_ROUTE, status_code=303)

    @router.post(f"{ADMIN_PANEL_ROUTE.rstrip('/')}/response-review", response_class=RedirectResponse, include_in_schema=False)
    async def response_review_post_fallback_custom() -> RedirectResponse:
        """Catch accidental native form POST to custom response review and redirect."""
        return RedirectResponse(url=f"{ADMIN_PANEL_ROUTE.rstrip('/')}/response-review", status_code=303)
