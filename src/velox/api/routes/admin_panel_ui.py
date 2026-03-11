"""HTML route for the unified admin operations panel."""

from __future__ import annotations

# ruff: noqa: E501
import json

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from velox.api.routes.admin_panel_ui_assets import ADMIN_PANEL_SCRIPT, ADMIN_PANEL_STYLE
from velox.config.settings import settings

router = APIRouter(tags=["admin-panel-ui"])


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
  <div id="toast" class="toast info"></div>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">NX</div>
        <div>
          <h1>NexlumeAI<br>Admin</h1>
          <p>Tek domain, tek operasyon yuzeyi. Konusma, onay, ticket ve konfigurasyon ayni merkezde.</p>
        </div>
      </div>

      <nav id="nav" class="nav" aria-label="Admin navigasyon">
        <button data-nav="dashboard"><span class="nav-label"><strong>Dashboard</strong><span>Durum farkindaligi</span></span><span>01</span></button>
        <button data-nav="conversations"><span class="nav-label"><strong>Konusmalar</strong><span>Baglam ve risk takibi</span></span><span>02</span></button>
        <button data-nav="holds"><span class="nav-label"><strong>Holdlar</strong><span>Onay ve red aksiyonlari</span></span><span>03</span></button>
        <button data-nav="tickets"><span class="nav-label"><strong>Ticketlar</strong><span>Handoff ve sahiplik</span></span><span>04</span></button>
        <button data-nav="hotels"><span class="nav-label"><strong>Hotel Profile</strong><span>Dinamik bilgi yonetimi</span></span><span>05</span></button>
        <button data-nav="restaurant"><span class="nav-label"><strong>Restoran Slotlari</strong><span>Kapasite ve zamanlama</span></span><span>06</span></button>
        <button data-nav="system"><span class="nav-label"><strong>Sistem</strong><span>Domain, readiness, reload</span></span><span>07</span></button>
      </nav>

      <section class="sidebar-card">
        <h2>Kimlik</h2>
        <p id="currentUser">Panel girisi bekleniyor</p>
        <small id="currentRole">-</small>
      </section>

      <section class="sidebar-card">
        <h2>Scope</h2>
        <label for="hotelSelect">Hotel</label>
        <select id="hotelSelect" class="sidebar-select"></select>
        <p style="margin-top:10px">Aktif scope: <strong id="hotelScope">-</strong></p>
      </section>

      <section class="sidebar-card">
        <h2>Kontroller</h2>
        <div class="sidebar-actions">
          <button id="reloadButton" class="sidebar-button warn" type="button">Config Reload</button>
          <button id="logoutButton" class="sidebar-button secondary" type="button">Cikis Yap</button>
        </div>
      </section>
    </aside>

    <main class="workspace">
      <header class="topbar">
        <div>
          <div class="badge dark">nexlumeai.com operasyon alani</div>
          <h2 id="pageTitle">Operasyon Ozeti</h2>
          <p id="pageLead">Admin paneli kokpit mantigiyla calisir: kritik sinyali gizlemez, aksiyonu merkezde tutar.</p>
        </div>
        <div class="topbar-aside">
          <div class="badge info">Tek merkezli kontrol</div>
          <div class="badge warn">Riskli aksiyonlar gorunur</div>
        </div>
      </header>

      <section id="authView" class="panel">
        <div class="auth-grid">
          <article class="auth-card">
            <h3>Panel Girisi</h3>
            <p>Sistem acik oldugunda giris yalnizca kullanici adi, sifre ve Google Authenticator kodu ile tamamlanir.</p>
            <form id="loginForm" class="field-grid">
              <div class="field">
                <label for="login-username">Kullanici adi</label>
                <input id="login-username" name="username" autocomplete="username" required>
              </div>
              <div class="field">
                <label for="login-password">Sifre</label>
                <input id="login-password" name="password" type="password" autocomplete="current-password" required>
              </div>
              <div class="field full">
                <label for="login-otp">Google Authenticator kodu</label>
                <input id="login-otp" name="otp_code" inputmode="numeric" pattern="[0-9]*" placeholder="6 haneli kod" required>
              </div>
              <div class="field full">
                <button class="sidebar-button primary" type="submit">Oturum Ac</button>
              </div>
            </form>
          </article>

          <article id="bootstrapCard" class="auth-card">
            <h3>Ilk Kurulum</h3>
            <p>Yonetici kaydi yoksa panel kilitli kalmaz; ilk hesap guvenli bootstrap akisiyla uretilir.</p>
            <div id="bootstrapSummary" class="helper-panel"></div>
            <form id="bootstrapForm" class="field-grid" style="margin-top:14px">
              <div class="field">
                <label for="bootstrap-hotel">Hotel</label>
                <select id="bootstrap-hotel" name="hotel_id" required></select>
              </div>
              <div class="field">
                <label for="bootstrap-username">Kullanici adi</label>
                <input id="bootstrap-username" name="username" required>
              </div>
              <div class="field">
                <label for="bootstrap-display-name">Gorunen ad</label>
                <input id="bootstrap-display-name" name="display_name">
              </div>
              <div class="field">
                <label for="bootstrap-password">Gecici sifre</label>
                <input id="bootstrap-password" name="password" type="password" minlength="12" required>
              </div>
              <div class="field full">
                <label for="bootstrap-token">Bootstrap token</label>
                <input id="bootstrap-token" name="bootstrap_token" placeholder="ENV ile acildiysa gerekli olabilir">
              </div>
              <div class="field full">
                <button class="sidebar-button primary" type="submit">Ilk Admin Hesabini Olustur</button>
              </div>
            </form>
            <div id="otpSetup" class="helper-panel" hidden>
              <div class="helper-box">
                <strong>Authenticator Secret</strong>
                <p id="otpSecret" class="mono"></p>
              </div>
              <div class="helper-box">
                <strong>otpauth URI</strong>
                <p id="otpUri" class="mono"></p>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section id="panelView" class="panel" hidden>
        <section data-view="dashboard" class="section-grid">
          <div id="dashboardCards" class="card-grid"></div>
          <div id="dashboardQueues" class="card-grid" style="grid-template-columns:repeat(3,minmax(0,1fr))"></div>
        </section>

        <section data-view="conversations" class="section-grid" hidden>
          <div class="split">
            <article class="module-card">
              <div class="module-header">
                <div><h3>Konusma Listesi</h3><p>Filtreleri sade tut, riskli olanlari hizla ac.</p></div>
              </div>
              <form id="conversationFilters" class="toolbar">
                <select name="status">
                  <option value="">Tum durumlar</option>
                  <option value="GREETING">GREETING</option>
                  <option value="PENDING_APPROVAL">PENDING_APPROVAL</option>
                  <option value="CONFIRMED">CONFIRMED</option>
                  <option value="HANDOFF">HANDOFF</option>
                </select>
                <input name="date_from" type="date">
                <input name="date_to" type="date">
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
              <div class="empty-state"><p>Detay icin soldan bir konusma secin.</p></div>
            </article>
          </div>
        </section>

        <section data-view="holds" class="section-grid" hidden>
          <article class="module-card">
            <div class="module-header">
              <div><h3>Birlesik Hold Masasi</h3><p>Konaklama, restoran ve transfer taleplerini tek kurgu ile yonetin.</p></div>
            </div>
            <form id="holdFilters" class="toolbar">
              <select name="hold_type">
                <option value="">Tum tipler</option>
                <option value="stay">Stay</option>
                <option value="restaurant">Restaurant</option>
                <option value="transfer">Transfer</option>
              </select>
              <select name="status">
                <option value="">Tum statuler</option>
                <option value="PENDING_APPROVAL">PENDING_APPROVAL</option>
                <option value="APPROVED">APPROVED</option>
                <option value="REJECTED">REJECTED</option>
              </select>
              <button class="primary" type="submit">Filtrele</button>
            </form>
            <div class="table-shell">
              <table>
                <thead><tr><th>Hold</th><th>Hotel</th><th>Durum</th><th>Draft</th><th>Zaman</th><th>Aksiyon</th></tr></thead>
                <tbody id="holdTableBody"></tbody>
              </table>
            </div>
          </article>
        </section>

        <section data-view="tickets" class="section-grid" hidden>
          <article class="module-card">
            <div class="module-header">
              <div><h3>Ticket Takibi</h3><p>Sahiplik ve kapanis durumunu kaybetmeden ekip akisina mudahale edin.</p></div>
            </div>
            <form id="ticketFilters" class="toolbar">
              <select name="status">
                <option value="">Tum statuler</option>
                <option value="OPEN">OPEN</option>
                <option value="IN_PROGRESS">IN_PROGRESS</option>
                <option value="RESOLVED">RESOLVED</option>
                <option value="CLOSED">CLOSED</option>
              </select>
              <select name="priority">
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
                <select id="hotelProfileSelect" class="sidebar-select" style="min-width:240px"></select>
                <button id="saveHotelProfile" class="inline-button primary" type="button">Profile Kaydet</button>
              </div>
            </div>
            <div id="hotelProfileMeta" class="helper-panel" style="margin-bottom:14px"></div>
            <div class="field full">
              <label for="hotelProfileEditor">profile_json</label>
              <textarea id="hotelProfileEditor"></textarea>
            </div>
          </article>
        </section>

        <section data-view="restaurant" class="section-grid" hidden>
          <article class="module-card">
            <div class="module-header">
              <div><h3>Slot Yonetimi</h3><p>Kapasiteyi tarih ve saat bazli tut, dar ekranda bile kritik kolonlari kaybetme.</p></div>
            </div>
            <form id="slotFilters" class="toolbar">
              <input name="date_from" type="date">
              <input name="date_to" type="date">
              <button id="loadSlotsButton" class="primary" type="button">Slotlari Getir</button>
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
              <div class="field"><label>Tarih baslangic</label><input name="date_from" type="date" required></div>
              <div class="field"><label>Tarih bitis</label><input name="date_to" type="date" required></div>
              <div class="field"><label>Saat</label><input name="time" type="time" required></div>
              <div class="field"><label>Alan</label><select name="area"><option value="outdoor">outdoor</option><option value="indoor">indoor</option></select></div>
              <div class="field"><label>Toplam kapasite</label><input name="total_capacity" type="number" min="1" required></div>
              <div class="field"><label>Aktif</label><input name="is_active" type="checkbox" checked style="width:20px;height:20px"></div>
              <div class="field full"><button class="inline-button primary" type="submit">Slot Araligi Olustur</button></div>
            </form>
          </article>
        </section>

        <section data-view="system" class="section-grid" hidden>
          <article class="module-card">
            <div class="module-header">
              <div><h3>Sistem Kontrolleri</h3><p>Readiness, domain ve bootstrap guvenlik durumu ayni ekranda gorunur kalir.</p></div>
            </div>
            <div id="systemMeta" class="helper-panel" style="margin-bottom:14px"></div>
            <div id="systemChecks" class="status-list"></div>
          </article>
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
        <textarea id="decisionReason" required style="min-height:120px"></textarea>
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


@router.get("/admin", response_class=HTMLResponse)
async def admin_panel_ui() -> HTMLResponse:
    """Serve the standalone admin panel HTML."""
    return HTMLResponse(content=render_admin_panel_html())
