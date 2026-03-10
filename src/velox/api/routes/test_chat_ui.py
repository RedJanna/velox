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
      <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#e9c46a" stroke-width="1.8">
        <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
      </svg>
      <div class="header-copy">
        <h1>Velox Chat Lab</h1>
        <p>Canli geri bildirim, duzeltme ve senaryo uretim paneli</p>
      </div>
    </div>
    <div class="header-controls">
      <label for="model-select">Test modeli</label>
      <select id="model-select" class="header-select header-select-model" onchange="changeModel(this.value)">
        <option>Yukleniyor...</option>
      </select>
      <label for="phone-input">Phone</label>
      <input type="text" id="phone-input" value="test_user_123">
      <button class="btn btn-reset" onclick="resetConversation()">Reset</button>
      <label for="save-format">Export</label>
      <select id="save-format" class="header-select">
        <option value="md">.md</option>
        <option value="txt">.txt</option>
        <option value="json">.json</option>
        <option value="pdf">.pdf</option>
      </select>
      <button class="btn btn-save" onclick="downloadConversation()">Disa Aktar</button>
      <button class="btn btn-toggle" id="toggle-debug" onclick="toggleDebug()">Panel</button>
    </div>
  </div>

  <div class="main">
    <div class="chat-panel">
      <div class="messages" id="messages">
        <div class="empty-state" id="empty-state">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/></svg>
          <p>Mesaj gonderin, yaniti puanlayin ve gerekiyorsa yeni senaryo uretin.</p>
        </div>
      </div>
      <div class="input-bar">
        <textarea id="msg-input" rows="1" placeholder="Mesajinizi yazin..." onkeydown="handleKey(event)"></textarea>
        <button class="btn btn-send" onclick="sendMessage()">
          <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
        </button>
      </div>
    </div>

    <div class="debug-panel" id="debug-panel">
      <div class="debug-header">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z"/></svg>
        <div>
          <strong>Analiz ve Feedback</strong>
          <span>Debug durumu + duzeltme akisi</span>
        </div>
      </div>
      <div class="debug-body" id="debug-body">
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
          <h3>Escalation</h3>
          <div class="debug-value" id="d-escalation">-</div>
        </div>
        <div class="debug-section">
          <h3>Entities</h3>
          <div class="debug-json" id="d-entities">{}</div>
        </div>
        <div class="debug-section">
          <h3>Next Step</h3>
          <div class="debug-value" id="d-next">-</div>
        </div>
        <div class="debug-section">
          <h3>Full Internal JSON</h3>
          <div class="debug-json" id="d-full">{}</div>
        </div>
        <div class="debug-section">
          <div class="feedback-studio-head">
            <div>
              <h3>Feedback Studio</h3>
              <p>Her asistan yanitinin altindan puan secin. 1-4 icin duzeltme girildiginde sistem yeni senaryo dosyasi uretir.</p>
            </div>
            <span class="feedback-info" id="feedback-info" title="Puan secildiginde duzeltme alani burada acilir.">i</span>
          </div>
          <div id="feedback-empty" class="feedback-muted">Bir yaniti secmek icin 1-5 puan dugmelerinden birine basin.</div>
          <div id="feedback-active" hidden>
            <div class="feedback-rating-line">
              <span class="feedback-chip" id="feedback-rating-chip">Puan secilmedi</span>
              <span class="feedback-muted" id="feedback-rating-help">-</span>
            </div>
            <div class="feedback-form" id="feedback-form" hidden>
              <textarea id="feedback-correction" placeholder="Dogru bilgiyi veya duzeltilmis cevabi yazin..."></textarea>
              <button class="btn btn-submit" id="feedback-submit" onclick="submitFeedback()">Duzelt ve Senaryo Uret</button>
            </div>
            <div class="feedback-result" id="feedback-result" hidden>
              <div class="feedback-muted" id="feedback-result-meta"></div>
              <div class="debug-json" id="feedback-corrected-reply"></div>
            </div>
          </div>
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
