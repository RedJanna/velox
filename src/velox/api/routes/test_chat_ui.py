"""Static HTML assembly for the Chat Lab web interface."""

# ruff: noqa: E501

from velox.api.routes.test_chat_ui_assets import TEST_CHAT_SCRIPT, TEST_CHAT_STYLE

TEST_CHAT_HTML = (
    """\
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Velox Chat Lab</title>
<style>
"""
    + TEST_CHAT_STYLE
    + """
</style>
</head>
<body>
<div class="app">
  <div class="header">
    <div class="header-brand">
      <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#e7bf5f" stroke-width="1.8">
        <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
      </svg>
      <div class="header-copy">
        <h1>Velox Chat Lab</h1>
        <p>Canli test, feedback kaydi, transcript import ve genel rapor paneli</p>
      </div>
    </div>
    <div class="header-controls">
      <div class="field">
        <label for="model-select">Test modeli</label>
        <select id="model-select" class="header-select header-select-model">
          <option>Yukleniyor...</option>
        </select>
      </div>
      <div class="field">
        <label for="phone-input">Numara / Test Kimliği</label>
        <input type="text" id="phone-input" class="header-input" value="test_user_123">
      </div>
      <div class="field">
        <label for="import-select">Kaynak</label>
        <select id="import-select" class="header-select header-select-import">
          <option value="">Yeni Test</option>
        </select>
      </div>
      <button class="btn btn-ghost" id="refresh-imports" type="button" aria-label="Import listesini yenile">Importlar</button>
      <button class="btn btn-reset" id="reset-btn" type="button" aria-label="Konusmayi sifirla">Reset</button>
      <div class="field">
        <label for="save-format">Export</label>
        <select id="save-format" class="header-select">
          <option value="md">.md</option>
          <option value="txt">.txt</option>
          <option value="json">.json</option>
          <option value="pdf">.pdf</option>
        </select>
      </div>
      <button class="btn btn-save" id="export-btn" type="button" aria-label="Konusma kaydini disa aktar">Disa Aktar</button>
      <button class="btn btn-toggle" id="toggle-debug" type="button" aria-label="Analiz panelini ac veya kapat">Panel</button>
    </div>
  </div>

  <div class="main">
    <div class="chat-panel">
      <div class="messages" id="messages" role="log" aria-live="polite" aria-label="Mesaj akisi"></div>
      <div class="input-bar">
        <textarea id="msg-input" rows="1" placeholder="Mesajinizi yazin..." aria-label="Mesaj girisi"></textarea>
        <button class="btn btn-primary btn-send" id="send-btn" type="button" aria-label="Mesaji gonder">
          <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
        </button>
      </div>
    </div>

    <div class="debug-panel" id="debug-panel">
      <div class="debug-header">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z"/></svg>
        <div>
          <strong>Analiz ve Feedback</strong>
          <span>Kaynak secimi, debug verisi, puanlama ve rapor</span>
        </div>
      </div>
      <div class="debug-body">
        <div class="debug-section">
          <h3>Aktif Kaynak</h3>
          <div class="source-badge" id="source-banner">Canli test gorunumu aktif.</div>
        </div>
        <div class="debug-section">
          <h3>Conversation State</h3>
          <div class="debug-value" id="d-state"><span class="debug-badge badge-state">-</span></div>
        </div>
        <div class="debug-section">
          <h3>Intent</h3>
          <div class="debug-value" id="d-intent"><span class="debug-badge badge-intent">-</span></div>
        </div>
        <div class="debug-section">
          <h3>Language</h3>
          <div class="debug-value" id="d-lang"><span class="debug-badge badge-lang">-</span></div>
        </div>
        <div class="debug-section">
          <h3>Risk Flags</h3>
          <div class="debug-flags" id="d-flags"><span class="feedback-muted">Flag yok</span></div>
        </div>
        <div class="debug-section">
          <h3>Next Step</h3>
          <div class="debug-value" id="d-next">-</div>
        </div>
        <div class="debug-section">
          <h3>Full Internal JSON</h3>
          <div class="debug-json" id="d-full">{}</div>
        </div>
        <div class="debug-section hidden" id="role-mapping-panel">
          <div class="studio-head">
            <div>
              <h3>Role Mapping</h3>
              <p id="role-mapping-note">Import edilen JSON icin rol eslestirmesi gerekiyor.</p>
            </div>
          </div>
          <div id="role-mapping-fields"></div>
          <button class="btn btn-primary btn-block mt-sm" id="role-mapping-submit" type="button">Importu Onayla</button>
        </div>
        <div class="debug-section">
          <div class="studio-head">
            <div>
              <h3>Feedback Studio</h3>
              <p>Asistan mesajini secin, kategori ve etiketleri girin, sonra feedback dosyasini kaydedin.</p>
            </div>
          </div>
          <div id="feedback-empty" class="feedback-muted">Bir asistan mesajinin altindaki 1-5 puan dugmelerinden birini secin.</div>
          <div id="feedback-active" class="hidden">
            <div class="feedback-chip" id="feedback-rating-chip">Puan secilmedi</div>
            <div class="feedback-muted mt-xs" id="feedback-rating-help">-</div>
            <div class="meta-box mt-sm" id="feedback-meta"></div>
            <div class="field-stack">
              <label for="feedback-category">Hata Kategorizasyonu</label>
              <select id="feedback-category" class="debug-select"></select>
              <div class="helper-card" id="feedback-category-help"><strong>Secim Yardimi</strong>Ana problem turunu secin; buna gore etiket onerileri hazirlanir.</div>
            </div>
            <div class="field-stack hidden" id="feedback-custom-category-row">
              <label for="feedback-custom-category">Ozel Kategori</label>
              <input id="feedback-custom-category" class="debug-input" type="text" placeholder="Kategori aciklamasi">
            </div>
            <div class="field-stack">
              <label>Hata Etiketleri</label>
              <div class="tag-toolbar">
                <div class="feedback-muted" id="feedback-tags-note">Kategori secince ilgili etiketler otomatik onerilir.</div>
                <button class="btn btn-ghost btn-mini" id="apply-tag-suggestions" type="button">Onerileri Uygula</button>
              </div>
              <div class="checkbox-grid" id="feedback-tags"></div>
            </div>
            <div class="field-stack">
              <label for="feedback-custom-tags">Ozel Etiketler</label>
              <input id="feedback-custom-tags" class="debug-input" type="text" placeholder="Virgul ile ayirin">
            </div>
            <div class="field-stack">
              <label for="feedback-gold-standard">Altin Standart</label>
              <textarea id="feedback-gold-standard" class="debug-textarea" placeholder="Dogru bilgiyi veya ideal cevabi yazin..."></textarea>
              <div class="inline-note">1-4 puan icin zorunludur.</div>
            </div>
            <div class="field-stack">
              <label for="feedback-notes">Admin Notu</label>
              <textarea id="feedback-notes" class="debug-textarea" placeholder="Opsiyonel not..."></textarea>
            </div>
            <div class="field-stack hidden" id="approved-example-row">
              <label class="check-item">
                <input id="feedback-approved-example" type="checkbox" checked>
                <span class="check-copy"><strong>Onayli Ornek</strong><span>5 puanli cevabi approved_examples havuzuna ekler.</span></span>
              </label>
            </div>
            <button class="btn btn-save btn-block mt-md" id="feedback-submit" type="button">Geri Bildirimi Kaydet</button>
            <div class="meta-box hidden mt-sm" id="feedback-result"></div>
          </div>
        </div>
        <div class="debug-section">
          <div class="studio-head">
            <div>
              <h3>Genel Rapor</h3>
              <p>Bad feedback klasorundeki kayitlari tarih araligina gore cluster edip oneri raporu uretir.</p>
            </div>
          </div>
          <div class="field-stack">
            <label for="report-date-from">Baslangic</label>
            <input id="report-date-from" class="debug-input" type="datetime-local">
          </div>
          <div class="field-stack">
            <label for="report-date-to">Bitis</label>
            <input id="report-date-to" class="debug-input" type="datetime-local">
          </div>
          <button class="btn btn-primary btn-block mt-md" id="report-submit" type="button">Genel Rapor Uret</button>
          <div class="list mt-sm" id="report-result"></div>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
"""
    + TEST_CHAT_SCRIPT
    + """
</script>
</body>
</html>
"""
)
