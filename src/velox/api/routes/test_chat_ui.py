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
<div id="toast" class="toast info" role="status" aria-live="polite"></div>
<div id="conv-detail-overlay" class="conv-modal-overlay hidden" role="dialog" aria-modal="true" aria-label="Konusma detayi">
  <div class="conv-modal">
    <div class="conv-modal-header">
      <strong>Konusma Detayi</strong>
      <button class="conv-modal-close" id="conv-modal-close" type="button" aria-label="Kapat">&times;</button>
    </div>
    <div class="conv-modal-meta" id="conv-modal-meta"></div>
    <div class="conv-modal-messages" id="conv-modal-messages"></div>
    <div class="conv-modal-json-toggle">
      <button class="btn btn-ghost btn-mini" id="conv-modal-json-btn" type="button">Sistem Detaylari (JSON)</button>
    </div>
    <div class="conv-modal-json hidden" id="conv-modal-json"></div>
    <div class="conv-modal-feedback hidden" id="conv-modal-feedback">
      <div class="conv-modal-feedback-title">Olumsuz Geri Bildirim</div>
      <div class="field-stack">
        <label for="conv-fb-category">Kategori</label>
        <select id="conv-fb-category" class="debug-select"></select>
      </div>
      <div class="field-stack">
        <label for="conv-fb-gold">Dogru yanit ne olmali?</label>
        <textarea id="conv-fb-gold" class="debug-textarea" rows="3" placeholder="Ideal cevabi yazin..."></textarea>
      </div>
      <div class="field-stack">
        <label for="conv-fb-notes">Admin Notu (opsiyonel)</label>
        <textarea id="conv-fb-notes" class="debug-textarea" rows="2" placeholder="Ek not..."></textarea>
      </div>
      <button class="btn btn-save btn-block mt-sm" id="conv-fb-submit" type="button">Geri Bildirimi Kaydet</button>
      <div class="feedback-muted mt-xs" id="conv-fb-result"></div>
    </div>
    <div class="conv-modal-send" id="conv-modal-send">
      <textarea id="conv-modal-msg-input" rows="1" placeholder="Mesaj yazin..."></textarea>
      <button class="btn btn-primary" id="conv-modal-send-btn" type="button">Gonder</button>
    </div>
    <div class="conv-modal-actions" id="conv-modal-actions"></div>
  </div>
</div>
<dialog id="faq-dialog" class="faq-dialog">
  <div class="faq-dialog-card">
    <div class="faq-dialog-head">
      <h3>SSS'e Ekle</h3>
      <button id="faq-dialog-close" type="button" aria-label="Kapat">&times;</button>
    </div>
    <form id="faq-dialog-form">
      <div class="field-stack">
        <label for="faq-topic">Konu</label>
        <input id="faq-topic" class="debug-input" type="text" required maxlength="120" placeholder="Ornegin: Odada utu var mi?">
      </div>
      <div class="field-stack">
        <label for="faq-question-tr">Soru (TR)</label>
        <textarea id="faq-question-tr" class="debug-textarea" rows="3" maxlength="500"></textarea>
      </div>
      <div class="field-stack">
        <label for="faq-answer-tr">Cevap (TR)</label>
        <textarea id="faq-answer-tr" class="debug-textarea" rows="4" required maxlength="4000"></textarea>
      </div>
      <div class="field-stack">
        <label for="faq-question-en">Soru (EN)</label>
        <textarea id="faq-question-en" class="debug-textarea" rows="3" maxlength="500"></textarea>
      </div>
      <div class="field-stack">
        <label for="faq-answer-en">Cevap (EN)</label>
        <textarea id="faq-answer-en" class="debug-textarea" rows="4" required maxlength="4000"></textarea>
      </div>
      <div class="field-stack">
        <label for="faq-status">Durum</label>
        <select id="faq-status" class="debug-select">
          <option value="DRAFT">Taslak (DRAFT)</option>
          <option value="ACTIVE" selected>Aktif (ACTIVE)</option>
        </select>
      </div>
      <button class="btn btn-save btn-block mt-md" type="submit">SSS Kaydet</button>
    </form>
    <div id="faq-dialog-result" class="meta-box hidden mt-sm"></div>
  </div>
</dialog>
<div class="app">
  <div class="header header--workspace">
    <div class="header-brand">
      <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#e7bf5f" stroke-width="1.8">
        <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
      </svg>
      <div class="header-copy">
        <h1>Velox Chat Lab</h1>
        <p>WhatsApp benzeri operasyon akisi, canli kuyruk ve inceleme arayuzu</p>
      </div>
      <div class="source-badge" id="source-banner">Canli kuyruk hazir.</div>
    </div>
    <div class="header-controls">
      <div class="field field-stack-sm">
        <label for="model-select">Test modeli</label>
        <select id="model-select" class="header-select header-select-model">
          <option>Yukleniyor...</option>
        </select>
      </div>
      <div class="field field-stack-sm">
        <label for="phone-input">Test Kimligi</label>
        <input type="text" id="phone-input" class="header-input" value="test_user_123">
      </div>
      <div class="field field-stack-sm">
        <label for="import-select">Kaynak</label>
        <select id="import-select" class="header-select header-select-import">
          <option value="">Yeni Test</option>
        </select>
      </div>
      <div class="field field-stack-sm">
        <label>Mod</label>
        <div class="mode-switch" id="mode-switch">
          <button class="mode-btn" data-mode="test" type="button" title="Test: mesaj alinir, AI cevap uretir ama gondermez">Test</button>
          <button class="mode-btn" data-mode="ai" type="button" title="AI: mesaj alinir, AI cevap uretir ve gonderir">AI</button>
          <button class="mode-btn" data-mode="approval" type="button" title="Onay: AI cevap uretir, admin onaylayana kadar gondermez">Onay</button>
          <button class="mode-btn" data-mode="off" type="button" title="Off: sadece veri kaydedilir, cevap uretilmez">Off</button>
        </div>
      </div>
      <button class="btn btn-ghost" id="refresh-imports" type="button" aria-label="Import listesini yenile">Importlar</button>
      <button class="btn btn-reset" id="reset-btn" type="button" aria-label="Konusmayi sifirla">Reset</button>
      <div class="field field-stack-sm">
        <label for="save-format">Export</label>
        <select id="save-format" class="header-select">
          <option value="md">.md</option>
          <option value="txt">.txt</option>
          <option value="json">.json</option>
          <option value="pdf">.pdf</option>
        </select>
      </div>
      <button class="btn btn-save" id="export-btn" type="button" aria-label="Konusma kaydini disa aktar">Disa Aktar</button>
      <button class="btn btn-toggle" id="toggle-debug" type="button" aria-label="Analiz panelini ac veya kapat">Diagnostics</button>
    </div>
  </div>

  <div class="main">
    <aside class="queue-panel">
      <div class="queue-panel-head">
        <div>
          <h2>Konusmalar</h2>
          <p>Canli kuyruk, onay bekleyen yanitlar ve dikkat gerektiren konusmalar</p>
        </div>
        <button class="btn btn-ghost btn-mini" id="live-feed-refresh" type="button">Yenile</button>
      </div>
      <div class="queue-toolbar">
        <div class="queue-tabs" id="queue-tabs">
          <button class="queue-tab is-active" type="button" data-queue-filter="all">Tum</button>
          <button class="queue-tab" type="button" data-queue-filter="approval">Onay</button>
          <button class="queue-tab" type="button" data-queue-filter="human">Insan</button>
          <button class="queue-tab" type="button" data-queue-filter="attention">Sorunlu</button>
        </div>
        <input id="queue-search" class="header-input queue-search" type="text" placeholder="Numara, durum veya mesaj ara" aria-label="Konusma ara">
      </div>
      <div id="live-feed-container" class="queue-list">
        <div class="feedback-muted">Kuyruk yukleniyor...</div>
      </div>
    </aside>

    <section class="chat-panel">
      <div id="thread-header" class="thread-header">
        <div class="thread-header-copy">
          <h2>Konusma secin</h2>
          <p>Soldaki kuyruktan bir konusma acin veya test kimligi ile yeni bir test baslatin.</p>
        </div>
        <div class="thread-header-actions">
          <span class="thread-chip thread-chip-muted">Hazir</span>
        </div>
      </div>
      <div id="session-strip" class="session-strip"></div>
      <div class="messages" id="messages" role="log" aria-live="polite" aria-label="Mesaj akisi"></div>
      <div class="input-bar">
        <div class="composer-modebar" id="composer-modebar">
          <button class="composer-mode-btn is-active" type="button" data-composer-mode="reply">Yanit</button>
          <button class="composer-mode-btn" type="button" data-composer-mode="internal_note">Ic Not</button>
          <button class="composer-mode-btn" type="button" data-composer-mode="template">Sablon</button>
          <button class="composer-mode-btn" type="button" data-composer-mode="ai_draft">AI Taslak</button>
        </div>
        <div id="composer-helper" class="composer-helper hidden" aria-live="polite"></div>
        <div id="reply-preview" class="reply-preview hidden" aria-live="polite">
          <div class="reply-preview-copy">
            <span class="reply-preview-label" id="reply-preview-label">Yanitlaniyor</span>
            <div class="reply-preview-text" id="reply-preview-text"></div>
          </div>
          <button id="reply-preview-clear" class="reply-preview-clear" type="button" aria-label="Yaniti iptal et">&times;</button>
        </div>
        <div id="composer-attachments" class="composer-attachments hidden" aria-live="polite"></div>
        <div id="template-panel" class="template-panel hidden">
          <div class="template-panel-copy">
            <strong>Sablon modu</strong>
            <p>Bu P0 asamasinda sablon gonderimi hazirlik durumunda. Serbest mesaj yerine uygun sablon secimi gerektiginde bu alan genisletilecek.</p>
          </div>
        </div>
        <input id="attachment-input" type="file" class="hidden" multiple accept=".jpg,.jpeg,.png,.webp,.pdf,.docx,.txt,.ogg,.mp3,.m4a,.mp4,.webm" aria-label="Dosya sec">
        <div class="input-row">
          <button class="btn btn-ghost btn-attach" id="attach-btn" type="button" aria-label="Dosya ekle">
            <svg viewBox="0 0 24 24"><path d="M16.5 6.5l-7.6 7.6a2.5 2.5 0 103.5 3.5l7.1-7.1a4.5 4.5 0 10-6.4-6.4L5.3 12a6 6 0 008.5 8.5l6.3-6.3-1.4-1.4-6.3 6.3a4 4 0 11-5.7-5.7l7.8-7.8a2.5 2.5 0 113.5 3.5l-7.1 7.1a.5.5 0 11-.7-.7l6.4-6.4-1.4-1.4-6.4 6.4a2.5 2.5 0 003.5 3.5l7.1-7.1a4.5 4.5 0 10-6.4-6.4z"/></svg>
          </button>
          <button class="btn btn-ghost btn-voice" id="voice-btn" type="button" aria-label="Ses kaydi baslat">
            <svg viewBox="0 0 24 24"><path d="M12 14a3 3 0 003-3V6a3 3 0 10-6 0v5a3 3 0 003 3zm5-3a1 1 0 10-2 0 3 3 0 01-6 0 1 1 0 10-2 0 5 5 0 004 4.9V20H8a1 1 0 100 2h8a1 1 0 100-2h-3v-1.1A5 5 0 0017 11z"/></svg>
          </button>
          <textarea id="msg-input" rows="1" placeholder="Mesajinizi yazin..." aria-label="Mesaj girisi"></textarea>
          <button class="btn btn-primary btn-send" id="send-btn" type="button" aria-label="Mesaji gonder">
            <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
          </button>
        </div>
      </div>
    </section>

    <aside class="context-panel">
      <div class="context-panel-head">
        <div>
          <h2>Baglam</h2>
          <p>Misafir, operasyon modu ve teslimat sagligi</p>
        </div>
      </div>
      <div class="context-tabs" id="context-tabs">
        <button class="context-tab is-active" type="button" data-context-tab="guest">Misafir</button>
        <button class="context-tab" type="button" data-context-tab="operations">Operasyon</button>
        <button class="context-tab" type="button" data-context-tab="delivery">Teslimat</button>
      </div>
      <div id="context-body" class="context-body">
        <div class="context-empty">
          <strong>Baglam hazir degil</strong>
          <p>Bir konusma acildiginda misafir ve teslimat ozeti burada gorunecek.</p>
        </div>
      </div>
    </aside>
  </div>
</div>

<div class="debug-panel collapsed" id="debug-panel">
  <div class="debug-header">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z"/></svg>
    <div>
      <strong>Diagnostics</strong>
      <span>Chat Lab debug, feedback, metrik ve rapor alanlari</span>
    </div>
  </div>
  <div class="debug-body">
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
          <label for="feedback-category" id="lbl-category">Hata Kategorizasyonu</label>
          <select id="feedback-category" class="debug-select"></select>
          <div class="helper-card" id="feedback-category-help"><strong>Secim Yardimi</strong>Ana problem turunu secin; buna gore etiket onerileri hazirlanir.</div>
        </div>
        <div class="field-stack hidden" id="feedback-custom-category-row">
          <label for="feedback-custom-category">Ozel Kategori</label>
          <input id="feedback-custom-category" class="debug-input" type="text" placeholder="Kategori aciklamasi">
        </div>
        <div class="field-stack">
          <label id="lbl-tags">Hata Etiketleri</label>
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
          <label for="feedback-gold-standard" id="lbl-gold">Altin Standart</label>
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
        <div class="meta-box hidden mt-sm" id="feedback-result" aria-live="polite"></div>
      </div>
    </div>
    <div class="debug-section">
      <div class="studio-head">
        <div>
          <h3>Feedback Metrikleri</h3>
          <p>Toplam geri bildirim, puan dagilimi, kategori ve dil bazli ozet istatistikler.</p>
        </div>
        <button class="btn btn-ghost btn-mini" id="metrics-refresh" type="button">Yenile</button>
      </div>
      <div id="metrics-container">
        <div class="feedback-muted">Metrikler yukleniyor...</div>
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
      <div class="list mt-sm" id="report-result" aria-live="polite"></div>
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
