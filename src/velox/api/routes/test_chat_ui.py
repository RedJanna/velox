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
<div id="conv-detail-overlay" class="conv-modal-overlay hidden" role="dialog" aria-modal="true" aria-label="Konuşma detayı">
  <div class="conv-modal">
    <div class="conv-modal-header">
      <strong>Konuşma Detayı</strong>
      <button class="conv-modal-close" id="conv-modal-close" type="button" aria-label="Kapat">&times;</button>
    </div>
    <div class="conv-modal-meta" id="conv-modal-meta"></div>
    <div class="conv-modal-messages" id="conv-modal-messages"></div>
    <div class="conv-modal-json-toggle">
      <button class="btn btn-ghost btn-mini" id="conv-modal-json-btn" type="button">Sistem Detayları (JSON)</button>
    </div>
    <div class="conv-modal-json hidden" id="conv-modal-json"></div>
    <div class="conv-modal-feedback hidden" id="conv-modal-feedback">
      <div class="conv-modal-feedback-title">Olumsuz Geri Bildirim</div>
      <div class="field-stack">
        <label for="conv-fb-category">Kategori</label>
        <select id="conv-fb-category" class="debug-select"></select>
      </div>
      <div class="field-stack">
        <label for="conv-fb-gold">Doğru yanıt ne olmalı?</label>
        <textarea id="conv-fb-gold" class="debug-textarea" rows="3" placeholder="İdeal yanıtı yazın..."></textarea>
      </div>
      <div class="field-stack">
        <label for="conv-fb-notes">Yönetici Notu (isteğe bağlı)</label>
        <textarea id="conv-fb-notes" class="debug-textarea" rows="2" placeholder="Ek not yazın..."></textarea>
      </div>
      <button class="btn btn-save btn-block mt-sm" id="conv-fb-submit" type="button">Geri Bildirimi Kaydet</button>
      <div class="feedback-muted mt-xs" id="conv-fb-result"></div>
    </div>
    <div class="conv-modal-send" id="conv-modal-send">
      <textarea id="conv-modal-msg-input" rows="1" placeholder="Mesaj yazın..."></textarea>
      <button class="btn btn-primary" id="conv-modal-send-btn" type="button">Gönder</button>
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
        <input id="faq-topic" class="debug-input" type="text" required maxlength="120" placeholder="Örneğin: Odada ütü var mı?">
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
          <option value="DRAFT">Taslak</option>
          <option value="ACTIVE" selected>Aktif</option>
        </select>
      </div>
      <button class="btn btn-save btn-block mt-md" type="submit">SSS Kaydet</button>
    </form>
    <div id="faq-dialog-result" class="meta-box hidden mt-sm"></div>
  </div>
</dialog>
<dialog id="shortcut-dialog" class="faq-dialog shortcut-dialog">
  <div class="faq-dialog-card">
    <div class="faq-dialog-head">
      <h3>Klavye Kısayolları</h3>
      <button id="shortcut-dialog-close" type="button" aria-label="Kapat">&times;</button>
    </div>
    <div class="shortcut-list" aria-label="Chat Lab kısayolları">
      <div class="shortcut-row"><span class="shortcut-key">J / ↓</span><span>Sonraki konuşmaya geç</span></div>
      <div class="shortcut-row"><span class="shortcut-key">K / ↑</span><span>Önceki konuşmaya geç</span></div>
      <div class="shortcut-row"><span class="shortcut-key">R</span><span>Yanıt moduna geç</span></div>
      <div class="shortcut-row"><span class="shortcut-key">N</span><span>İç not moduna geç</span></div>
      <div class="shortcut-row"><span class="shortcut-key">T</span><span>Şablon moduna geç</span></div>
      <div class="shortcut-row"><span class="shortcut-key">Ctrl/Cmd + K</span><span>Konuşma aramasına odaklan</span></div>
      <div class="shortcut-row"><span class="shortcut-key">D</span><span>Tanılama panelini aç / kapat</span></div>
      <div class="shortcut-row"><span class="shortcut-key">G / O / L / A</span><span>Misafir, Operasyon, Teslimat ve Denetim İzi sekmeleri</span></div>
      <div class="shortcut-row"><span class="shortcut-key">Enter</span><span>Seçili konuşmayı aç</span></div>
      <div class="shortcut-row"><span class="shortcut-key">Esc</span><span>Açık paneli veya önizlemeyi kapat</span></div>
      <div class="shortcut-row"><span class="shortcut-key">?</span><span>Bu yardımı aç / kapat</span></div>
      <div class="shortcut-row"><span class="shortcut-key">Shift + Enter</span><span>Satır atla</span></div>
      <div class="shortcut-row"><span class="shortcut-key">Enter</span><span>Yazı alanında mesajı gönder</span></div>
    </div>
    <div class="feedback-muted">Yazı alanı veya iletişim kutusu açıkken kısayollar devre dışı kalır.</div>
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
        <p>WhatsApp benzeri operasyon akışı, canlı kuyruk ve inceleme arayüzü</p>
      </div>
      <div class="source-badge" id="source-banner">Canlı kuyruk hazır.</div>
    </div>
    <div class="header-controls">
      <div class="field field-stack-sm">
        <label for="model-select">Test modeli</label>
        <select id="model-select" class="header-select header-select-model">
          <option>Yükleniyor...</option>
        </select>
      </div>
      <div class="field field-stack-sm">
        <label for="phone-input">Test kimliği</label>
        <input type="text" id="phone-input" class="header-input" value="test_user_123">
      </div>
      <div class="field field-stack-sm">
        <label for="import-select">Kaynak</label>
        <select id="import-select" class="header-select header-select-import">
          <option value="">Yeni test</option>
        </select>
      </div>
      <div class="field field-stack-sm">
        <label>Mod</label>
        <div class="mode-switch" id="mode-switch">
          <button class="mode-btn" data-mode="test" type="button" title="Test: mesaj alınır, yapay zekâ yanıt üretir ama göndermez">Test</button>
          <button class="mode-btn" data-mode="ai" type="button" title="Otomatik: mesaj alınır, yapay zekâ yanıt üretir ve gönderir">Otomatik</button>
          <button class="mode-btn" data-mode="approval" type="button" title="Onay: yapay zekâ yanıt üretir, yönetici onaylayana kadar göndermez">Onay</button>
          <button class="mode-btn" data-mode="off" type="button" title="Kapalı: sadece veri kaydedilir, yanıt üretilmez">Kapalı</button>
        </div>
      </div>
      <button class="btn btn-ghost" id="refresh-imports" type="button" aria-label="İçe aktarım listesini yenile">İçe Aktarımlar</button>
      <button class="btn btn-reset" id="reset-btn" type="button" aria-label="Konuşmayı sıfırla">Sıfırla</button>
      <div class="field field-stack-sm">
        <label for="save-format">Dışa Aktarım</label>
        <select id="save-format" class="header-select">
          <option value="md">.md</option>
          <option value="txt">.txt</option>
          <option value="json">.json</option>
          <option value="pdf">.pdf</option>
        </select>
      </div>
      <button class="btn btn-save" id="export-btn" type="button" aria-label="Konuşma kaydını dışa aktar">Dışa Aktar</button>
      <button class="btn btn-toggle" id="toggle-debug" type="button" aria-label="Tanılama panelini aç veya kapat">Tanılama</button>
    </div>
  </div>

  <div class="main">
    <aside class="queue-panel">
      <div class="queue-panel-head">
        <div>
          <h2>Konuşmalar</h2>
          <p>Canlı kuyruk, onay bekleyen yanıtlar ve dikkat gerektiren konuşmalar</p>
        </div>
        <div class="queue-panel-actions">
          <button class="btn btn-ghost btn-mini" id="shortcut-help-btn" type="button" aria-label="Klavye kısayollarını göster">Kısayollar</button>
          <button class="btn btn-ghost btn-mini" id="live-feed-refresh" type="button">Yenile</button>
        </div>
      </div>
      <div class="queue-toolbar">
        <div class="queue-tabs" id="queue-tabs">
          <button class="queue-tab is-active" type="button" data-queue-filter="all">Tümü</button>
          <button class="queue-tab" type="button" data-queue-filter="approval">Onay</button>
          <button class="queue-tab" type="button" data-queue-filter="human">Temsilci</button>
          <button class="queue-tab" type="button" data-queue-filter="attention">Sorunlu</button>
        </div>
        <input id="queue-search" class="header-input queue-search" type="text" placeholder="Numara, durum veya mesaj ara" aria-label="Konuşma ara">
        <div id="queue-summary" class="queue-summary" aria-live="polite"></div>
      </div>
      <div id="live-feed-container" class="queue-list">
        <div class="feedback-muted">Kuyruk yükleniyor...</div>
      </div>
    </aside>

    <section class="chat-panel">
      <div id="thread-header" class="thread-header">
        <div class="thread-header-copy">
          <h2>Konuşma seçin</h2>
          <p>Soldaki kuyruktan bir konuşma açın veya test kimliği ile yeni bir test başlatın.</p>
        </div>
        <div class="thread-header-actions">
          <span class="thread-chip thread-chip-muted">Hazir</span>
        </div>
      </div>
      <div id="session-strip" class="session-strip"></div>
      <div class="messages" id="messages" role="log" aria-live="polite" aria-label="Mesaj akisi"></div>
      <div class="input-bar">
        <div class="composer-modebar" id="composer-modebar">
          <button class="composer-mode-btn is-active" type="button" data-composer-mode="reply">Yanıt</button>
          <button class="composer-mode-btn" type="button" data-composer-mode="internal_note">İç Not</button>
          <button class="composer-mode-btn" type="button" data-composer-mode="template">Şablon</button>
          <button class="composer-mode-btn" type="button" data-composer-mode="ai_draft">Yapay Zekâ Taslağı</button>
        </div>
        <div id="composer-helper" class="composer-helper hidden" aria-live="polite"></div>
        <div id="reply-preview" class="reply-preview hidden" aria-live="polite">
          <div class="reply-preview-copy">
            <span class="reply-preview-label" id="reply-preview-label">Yanıtlanıyor</span>
            <div class="reply-preview-text" id="reply-preview-text"></div>
          </div>
          <button id="reply-preview-clear" class="reply-preview-clear" type="button" aria-label="Yanıtı iptal et">&times;</button>
        </div>
        <div id="composer-attachments" class="composer-attachments hidden" aria-live="polite"></div>
        <div id="template-panel" class="template-panel hidden">
          <div class="template-panel-head">
            <div class="template-panel-copy">
              <strong>Şablon modu</strong>
              <p>Servis penceresi kapalıysa aşağıdaki şablon önerilerini inceleyin. Gerçek gönderimde ise onaylı Meta pencere açma şablonu kullanılır.</p>
            </div>
            <span class="template-panel-badge">Salt okunur</span>
          </div>
          <input id="template-search" class="header-input template-search" type="text" placeholder="Şablon ara" aria-label="Şablon ara">
          <div id="template-list" class="template-list">
            <div class="feedback-muted">Şablonlar yükleniyor...</div>
          </div>
          <div id="template-preview" class="template-preview">
            <strong>Önizleme</strong>
            <p>Bir şablon seçtiğinizde içerik burada görünecek.</p>
          </div>
        </div>
        <input id="attachment-input" type="file" class="hidden" multiple accept=".jpg,.jpeg,.png,.webp,.pdf,.docx,.txt,.ogg,.mp3,.m4a,.mp4,.webm" aria-label="Dosya seç">
        <div class="input-row">
          <button class="btn btn-ghost btn-attach" id="attach-btn" type="button" aria-label="Dosya ekle">
            <svg viewBox="0 0 24 24"><path d="M16.5 6.5l-7.6 7.6a2.5 2.5 0 103.5 3.5l7.1-7.1a4.5 4.5 0 10-6.4-6.4L5.3 12a6 6 0 008.5 8.5l6.3-6.3-1.4-1.4-6.3 6.3a4 4 0 11-5.7-5.7l7.8-7.8a2.5 2.5 0 113.5 3.5l-7.1 7.1a.5.5 0 11-.7-.7l6.4-6.4-1.4-1.4-6.4 6.4a2.5 2.5 0 003.5 3.5l7.1-7.1a4.5 4.5 0 10-6.4-6.4z"/></svg>
          </button>
          <button class="btn btn-ghost btn-voice" id="voice-btn" type="button" aria-label="Ses kaydını başlat">
            <svg viewBox="0 0 24 24"><path d="M12 14a3 3 0 003-3V6a3 3 0 10-6 0v5a3 3 0 003 3zm5-3a1 1 0 10-2 0 3 3 0 01-6 0 1 1 0 10-2 0 5 5 0 004 4.9V20H8a1 1 0 100 2h8a1 1 0 100-2h-3v-1.1A5 5 0 0017 11z"/></svg>
          </button>
          <textarea id="msg-input" rows="1" placeholder="Mesajınızı yazın..." aria-label="Mesaj girişi"></textarea>
          <button class="btn btn-primary btn-send" id="send-btn" type="button" aria-label="Mesajı gönder">
            <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
          </button>
        </div>
      </div>
    </section>

    <aside class="context-panel">
      <div class="context-panel-head">
        <div>
          <h2>Bağlam</h2>
          <p>Misafir, operasyon modu, teslimat durumu ve denetim izi</p>
        </div>
      </div>
      <div class="context-tabs" id="context-tabs">
        <button class="context-tab is-active" type="button" data-context-tab="guest">Misafir</button>
        <button class="context-tab" type="button" data-context-tab="operations">Operasyon</button>
        <button class="context-tab" type="button" data-context-tab="delivery">Teslimat</button>
        <button class="context-tab" type="button" data-context-tab="audit">Denetim İzi</button>
      </div>
      <div id="context-body" class="context-body">
        <div class="context-empty">
          <strong>Bağlam hazır değil</strong>
          <p>Bir konuşma açıldığında misafir ve teslimat özeti burada görünecek.</p>
        </div>
      </div>
    </aside>
  </div>
</div>

<div class="debug-panel collapsed" id="debug-panel">
  <div class="debug-header">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z"/></svg>
    <div>
      <strong>Tanılama</strong>
      <span>Chat Lab hata ayıklama, geri bildirim, metrik ve rapor alanları</span>
    </div>
  </div>
  <div class="debug-body">
    <div class="debug-section">
      <h3>Konuşma durumu</h3>
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
      <h3>Risk işaretleri</h3>
      <div class="debug-flags" id="d-flags"><span class="feedback-muted">Risk işareti yok</span></div>
    </div>
    <div class="debug-section">
      <h3>Sonraki adım</h3>
      <div class="debug-value" id="d-next">-</div>
    </div>
    <div class="debug-section">
      <h3>İç veri (tam JSON)</h3>
      <div class="debug-json" id="d-full">{}</div>
    </div>
    <div class="debug-section hidden" id="role-mapping-panel">
      <div class="studio-head">
        <div>
          <h3>Rol eşleştirme</h3>
          <p id="role-mapping-note">İçe aktarılan JSON için rol eşleştirmesi gerekiyor.</p>
        </div>
      </div>
      <div id="role-mapping-fields"></div>
      <button class="btn btn-primary btn-block mt-sm" id="role-mapping-submit" type="button">İçe Aktarmayı Onayla</button>
    </div>
    <div class="debug-section">
      <div class="studio-head">
        <div>
          <h3>Geri Bildirim Alanı</h3>
          <p>Asistan mesajını seçin, kategori ve etiketleri girin, ardından geri bildirimi kaydedin.</p>
        </div>
      </div>
      <div id="feedback-empty" class="feedback-muted">Bir asistan mesajının altındaki 1-5 puan düğmelerinden birini seçin.</div>
      <div id="feedback-active" class="hidden">
        <div class="feedback-chip" id="feedback-rating-chip">Puan seçilmedi</div>
        <div class="feedback-muted mt-xs" id="feedback-rating-help">-</div>
        <div class="meta-box mt-sm" id="feedback-meta"></div>
        <div class="field-stack">
          <label for="feedback-category" id="lbl-category">Hata kategorisi</label>
          <select id="feedback-category" class="debug-select"></select>
          <div class="helper-card" id="feedback-category-help"><strong>Seçim yardımı</strong>Ana problem türünü seçin; buna göre etiket önerileri hazırlanır.</div>
        </div>
        <div class="field-stack hidden" id="feedback-custom-category-row">
          <label for="feedback-custom-category">Özel kategori</label>
          <input id="feedback-custom-category" class="debug-input" type="text" placeholder="Kategori açıklaması">
        </div>
        <div class="field-stack">
          <label id="lbl-tags">Hata etiketleri</label>
          <div class="tag-toolbar">
            <div class="feedback-muted" id="feedback-tags-note">Kategori seçildiğinde ilgili etiketler otomatik önerilir.</div>
            <button class="btn btn-ghost btn-mini" id="apply-tag-suggestions" type="button">Önerileri Uygula</button>
          </div>
          <div class="checkbox-grid" id="feedback-tags"></div>
        </div>
        <div class="field-stack">
          <label for="feedback-custom-tags">Özel etiketler</label>
          <input id="feedback-custom-tags" class="debug-input" type="text" placeholder="Virgülle ayırın">
        </div>
        <div class="field-stack">
          <label for="feedback-gold-standard" id="lbl-gold">Referans yanıt</label>
          <textarea id="feedback-gold-standard" class="debug-textarea" placeholder="Doğru bilgiyi veya ideal yanıtı yazın..."></textarea>
          <div class="inline-note">1-4 puan için zorunludur.</div>
        </div>
        <div class="field-stack">
          <label for="feedback-notes">Yönetici notu</label>
          <textarea id="feedback-notes" class="debug-textarea" placeholder="İsteğe bağlı not..."></textarea>
        </div>
        <div class="field-stack hidden" id="approved-example-row">
          <label class="check-item">
            <input id="feedback-approved-example" type="checkbox" checked>
            <span class="check-copy"><strong>Onaylı örnek</strong><span>5 puanlı yanıtı onaylı örnek havuzuna ekler.</span></span>
          </label>
        </div>
        <button class="btn btn-save btn-block mt-md" id="feedback-submit" type="button">Geri Bildirimi Kaydet</button>
        <div class="meta-box hidden mt-sm" id="feedback-result" aria-live="polite"></div>
      </div>
    </div>
    <div class="debug-section">
      <div class="studio-head">
        <div>
          <h3>Geri Bildirim Metrikleri</h3>
          <p>Toplam geri bildirim, puan dağılımı, kategori ve dil bazlı özet istatistikler.</p>
        </div>
        <button class="btn btn-ghost btn-mini" id="metrics-refresh" type="button">Yenile</button>
      </div>
      <div id="metrics-container">
        <div class="feedback-muted">Metrikler yükleniyor...</div>
      </div>
    </div>
    <div class="debug-section">
      <div class="studio-head">
        <div>
          <h3>Genel Rapor</h3>
          <p>Olumsuz geri bildirim kayıtlarını tarih aralığına göre gruplayıp öneri raporu oluşturur.</p>
        </div>
      </div>
      <div class="field-stack">
        <label for="report-date-from">Başlangıç</label>
        <input id="report-date-from" class="debug-input" type="datetime-local">
      </div>
      <div class="field-stack">
        <label for="report-date-to">Bitiş</label>
        <input id="report-date-to" class="debug-input" type="datetime-local">
      </div>
      <button class="btn btn-primary btn-block mt-md" id="report-submit" type="button">Genel Rapor Oluştur</button>
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
