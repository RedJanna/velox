"""Static assets for the Chat Lab HTML interface."""

# ruff: noqa: E501

TEST_CHAT_STYLE = """\
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --navy:#14213d;--ink:#0f172a;--teal:#14746f;--teal-2:#2a9d8f;--amber:#e9c46a;
  --sand:#f8f5ef;--paper:#ffffff;--line:#d8dee9;--muted:#64748b;--muted-2:#94a3b8;
  --red:#dc2626;--orange:#f59e0b;--green:#22c55e;--shadow:0 18px 36px rgba(15,23,42,.12);
  --radius:18px;--mono:'Cascadia Code','Fira Code',monospace;
}
html,body{height:100%;font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:
radial-gradient(circle at top left,rgba(233,196,106,.24),transparent 30%),
linear-gradient(180deg,#f8f5ef 0%,#eef2f7 100%);color:var(--ink)}
body{overflow:hidden}
.app{display:flex;flex-direction:column;height:100vh}
.header{display:flex;align-items:center;gap:16px;padding:16px 22px;border-bottom:1px solid rgba(20,33,61,.08);
background:rgba(255,255,255,.78);backdrop-filter:blur(16px)}
.header-brand{display:flex;align-items:center;gap:14px}
.header-brand svg{flex-shrink:0}
.header-copy h1{font-size:18px;font-weight:700;letter-spacing:.02em}
.header-copy p{font-size:12px;color:var(--muted);margin-top:2px}
.header-controls{display:flex;align-items:center;gap:10px;margin-left:auto;flex-wrap:wrap}
.header-controls label{font-size:12px;color:var(--muted);font-weight:600}
.header-controls input[type=text],.header-select{height:38px;border:1px solid rgba(20,33,61,.12);border-radius:12px;padding:0 12px;background:rgba(255,255,255,.92);color:var(--ink);outline:none;transition:border-color .2s,box-shadow .2s}
.header-controls input[type=text]:focus,.header-select:focus{border-color:var(--teal);box-shadow:0 0 0 3px rgba(20,116,111,.12)}
.header-select-model{min-width:170px}
.btn{height:38px;border:none;border-radius:12px;padding:0 14px;font-size:13px;font-weight:700;cursor:pointer;transition:transform .15s ease,box-shadow .15s ease,background .15s ease}
.btn:hover{transform:translateY(-1px)}
.btn:disabled{opacity:.45;cursor:not-allowed;transform:none}
.btn-reset{background:#fee2e2;color:#991b1b}
.btn-save{background:var(--amber);color:#553d10}
.btn-toggle{display:none;background:rgba(20,33,61,.08);color:var(--ink)}
.main{display:flex;flex:1;min-height:0}
.chat-panel{flex:1;display:flex;flex-direction:column;min-width:0}
.messages{flex:1;overflow-y:auto;padding:24px 24px 18px;display:flex;flex-direction:column;gap:12px}
.messages::-webkit-scrollbar,.debug-body::-webkit-scrollbar{width:7px}
.messages::-webkit-scrollbar-thumb,.debug-body::-webkit-scrollbar-thumb{background:rgba(100,116,139,.28);border-radius:999px}
.msg{max-width:76%;display:flex;flex-direction:column;gap:8px;padding:14px 16px;border-radius:20px;box-shadow:var(--shadow);animation:fadeIn .24s ease}
.msg-user{align-self:flex-end;background:linear-gradient(135deg,var(--teal),var(--teal-2));color:#fff;border-bottom-right-radius:6px}
.msg-assistant{align-self:flex-start;background:rgba(255,255,255,.96);border:1px solid rgba(20,33,61,.08);border-bottom-left-radius:6px}
.msg-system{align-self:center;max-width:88%;background:rgba(20,33,61,.08);color:var(--muted);box-shadow:none}
.msg-body{font-size:14px;line-height:1.55;word-break:break-word}
.msg-time{font-size:11px;color:inherit;opacity:.65}
.msg-user .msg-time{text-align:right}
.feedback-bar{display:flex;flex-wrap:wrap;align-items:center;gap:8px;padding-top:4px;border-top:1px solid rgba(20,33,61,.08)}
.feedback-label{font-size:11px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:var(--muted)}
.feedback-buttons{display:flex;gap:6px;flex-wrap:wrap}
.feedback-score{width:28px;height:28px;border-radius:999px;border:1px solid rgba(20,33,61,.12);background:#fff;color:var(--ink);font-size:12px;font-weight:700;cursor:pointer;transition:all .15s ease}
.feedback-score:hover{border-color:var(--teal);color:var(--teal)}
.feedback-score.is-active{background:var(--teal);border-color:var(--teal);color:#fff}
.feedback-status{font-size:11px;color:var(--muted)}
.typing{align-self:flex-start;display:flex;gap:5px;padding:13px 16px;background:rgba(255,255,255,.96);border-radius:18px;border:1px solid rgba(20,33,61,.08);box-shadow:var(--shadow)}
.typing span{width:8px;height:8px;border-radius:50%;background:var(--muted-2);animation:bounce .6s infinite alternate}
.typing span:nth-child(2){animation-delay:.2s}.typing span:nth-child(3){animation-delay:.4s}
.input-bar{display:flex;align-items:flex-end;gap:12px;padding:16px 20px;border-top:1px solid rgba(20,33,61,.08);background:rgba(255,255,255,.84)}
.input-bar textarea{flex:1;resize:none;border:1px solid rgba(20,33,61,.12);border-radius:18px;padding:12px 16px;font-size:14px;font-family:inherit;line-height:1.45;max-height:120px;outline:none;transition:border-color .2s,box-shadow .2s;background:#fff}
.input-bar textarea:focus{border-color:var(--teal);box-shadow:0 0 0 3px rgba(20,116,111,.12)}
.btn-send{width:46px;height:46px;border-radius:16px;background:var(--teal);color:#fff;display:flex;align-items:center;justify-content:center}
.btn-send svg{width:20px;height:20px;fill:currentColor}
.debug-panel{width:396px;display:flex;flex-direction:column;background:linear-gradient(180deg,#152238 0%,#0f172a 100%);color:#fff;border-left:1px solid rgba(255,255,255,.06)}
.debug-panel.collapsed{width:0;border:none;overflow:hidden}
.debug-header{display:flex;align-items:center;gap:10px;padding:16px 18px;border-bottom:1px solid rgba(255,255,255,.08)}
.debug-header strong{font-size:14px}
.debug-header span{font-size:12px;color:rgba(255,255,255,.62)}
.debug-body{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:14px}
.debug-section{padding:14px;border-radius:18px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.06)}
.debug-section h3{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:rgba(255,255,255,.62);margin-bottom:8px}
.debug-value{font-size:13px;line-height:1.5}
.debug-json{font-family:var(--mono);font-size:12px;white-space:pre-wrap;word-break:break-word;color:#bfdbfe;background:rgba(2,6,23,.35);border-radius:14px;padding:10px;max-height:220px;overflow:auto}
.debug-badge{display:inline-flex;align-items:center;gap:4px;padding:4px 10px;border-radius:999px;font-size:11px;font-weight:700}
.badge-state{background:rgba(42,157,143,.2);color:#81f7e6}
.badge-intent{background:rgba(233,196,106,.18);color:#ffe49a}
.badge-lang{background:rgba(255,255,255,.12);color:#fff}
.debug-flags{display:flex;flex-wrap:wrap;gap:6px}
.flag{padding:4px 8px;border-radius:999px;font-size:11px;font-weight:700}
.flag-l3{background:#7f1d1d;color:#fecaca}.flag-l2{background:#78350f;color:#fde68a}
.flag-l1{background:#365314;color:#dcfce7}.flag-l0{background:rgba(255,255,255,.12);color:#fff}
.empty-state{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;min-height:100%;color:var(--muted)}
.empty-state svg{width:52px;height:52px;opacity:.35}
.feedback-studio-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}
.feedback-studio-head p{font-size:12px;color:rgba(255,255,255,.62);line-height:1.45}
.feedback-info{display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:999px;background:rgba(255,255,255,.12);font-size:12px;color:#fff;cursor:help}
.feedback-rating-line{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:10px}
.feedback-chip{display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding:6px 10px;background:rgba(20,116,111,.18);color:#a7f3d0;font-size:12px;font-weight:700}
.feedback-form textarea{width:100%;min-height:110px;resize:vertical;border-radius:16px;border:1px solid rgba(255,255,255,.12);background:rgba(2,6,23,.28);color:#fff;padding:12px 14px;font-size:13px;line-height:1.45;outline:none}
.feedback-form textarea:focus{border-color:#5eead4;box-shadow:0 0 0 3px rgba(45,212,191,.12)}
.feedback-form .btn-submit{margin-top:10px;width:100%;background:var(--amber);color:#3b2a04}
.feedback-muted{font-size:12px;color:rgba(255,255,255,.62);line-height:1.5}
.feedback-result{display:flex;flex-direction:column;gap:8px}
.feedback-result .debug-json{max-height:none}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@keyframes bounce{to{opacity:.35;transform:translateY(-4px)}}
@media(max-width:980px){
  .debug-panel{position:fixed;inset:0 0 0 auto;z-index:30;width:min(88vw,396px)}
  .btn-toggle{display:inline-flex;align-items:center;justify-content:center}
  .msg{max-width:90%}
}
"""

TEST_CHAT_SCRIPT = """\
const API = '/api/v1/test';
const messagesEl = document.getElementById('messages');
const inputEl = document.getElementById('msg-input');
const emptyState = document.getElementById('empty-state');
const debugPanel = document.getElementById('debug-panel');
const assistantReplies = new Map();
const feedbackStates = new Map();
let feedbackScale = [
  {rating:1,label:'Kesinlikle Yanlis',tooltip:'Bilgi tamamen yanlis mi? Burayi sec ve dogruyu sisteme ogret.',correction_required:true},
  {rating:2,label:'Hatali Anlatim',tooltip:'Bilgi dogru ama anlatim bozuk mu?',correction_required:true},
  {rating:3,label:'Eksik Bilgi',tooltip:'Cevap yetersiz mi? Eksikleri tamamla.',correction_required:true},
  {rating:4,label:'Gereksiz Ayrinti',tooltip:'Cok mu laf kalabaligi var? Sadelestirilmis halini onayla.',correction_required:true},
  {rating:5,label:'Mukemmel',tooltip:'Yanit tamamen dogruysa bunu secin.',correction_required:false},
];
let selectedFeedback = null;

const L3_FLAGS = ['LEGAL_REQUEST','SECURITY_INCIDENT','THREAT_SELF_HARM','MEDICAL_EMERGENCY'];
const L2_FLAGS = ['PAYMENT_CONFUSION','CHARGEBACK','REFUND_DISPUTE','ANGRY_COMPLAINT','FRAUD_SIGNAL','GROUP_BOOKING','CONTRACT_QUESTION','REPEAT_COMPLAINT','SOCIAL_MEDIA_THREAT','PRICE_MATCH','SYSTEM_ERROR','DOUBLE_CHARGE','TOOL_ERROR_REPEAT','TOOL_UNAVAILABLE'];
const L1_FLAGS = ['VIP_REQUEST','ALLERGY_ALERT','ACCESSIBILITY_NEED','CHILD_SAFETY','CAPACITY_LIMIT','WEATHER_ALERT','SPECIAL_EVENT_FLAG','DIETARY_RESTRICTION'];

function feedbackMeta(rating) {
  return feedbackScale.find(item => item.rating === rating) || feedbackScale[0];
}

function flagLevel(flag) {
  if (L3_FLAGS.includes(flag)) return 'l3';
  if (L2_FLAGS.includes(flag)) return 'l2';
  if (L1_FLAGS.includes(flag)) return 'l1';
  return 'l0';
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function formatMessageHtml(text) {
  return escapeHtml(text).replace(/\\n/g, '<br>');
}

function fmtTime(iso) {
  try { return new Date(iso).toLocaleTimeString('tr-TR', {hour:'2-digit',minute:'2-digit'}); }
  catch { return ''; }
}

function addBubble(role, text, time, messageId = null) {
  if (emptyState) emptyState.style.display = 'none';
  const bubble = document.createElement('div');
  bubble.className = 'msg msg-' + role;
  bubble.dataset.role = role;
  if (messageId) {
    bubble.dataset.messageId = messageId;
  }

  const body = document.createElement('div');
  body.className = 'msg-body';
  body.innerHTML = formatMessageHtml(text);
  bubble.appendChild(body);

  if (time) {
    const stamp = document.createElement('div');
    stamp.className = 'msg-time';
    stamp.textContent = fmtTime(time);
    bubble.appendChild(stamp);
  }

  if (role === 'assistant' && messageId) {
    assistantReplies.set(messageId, text);
    bubble.appendChild(buildFeedbackBar(messageId));
  }

  messagesEl.appendChild(bubble);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function buildFeedbackBar(messageId) {
  const wrapper = document.createElement('div');
  wrapper.className = 'feedback-bar';

  const label = document.createElement('span');
  label.className = 'feedback-label';
  label.textContent = 'Puan';
  wrapper.appendChild(label);

  const buttons = document.createElement('div');
  buttons.className = 'feedback-buttons';
  const state = feedbackStates.get(messageId);

  feedbackScale.forEach(item => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'feedback-score';
    button.textContent = item.rating;
    button.title = item.tooltip;
    const isSelected = selectedFeedback && selectedFeedback.messageId === messageId && selectedFeedback.rating === item.rating;
    if ((state && state.rating === item.rating) || isSelected) {
      button.classList.add('is-active');
    }
    button.addEventListener('click', () => selectFeedback(messageId, item.rating));
    buttons.appendChild(button);
  });
  wrapper.appendChild(buttons);

  const status = document.createElement('span');
  status.className = 'feedback-status';
  status.textContent = state?.status || (selectedFeedback && selectedFeedback.messageId === messageId ? 'Kaydetmeye hazir' : 'Degerlendirme bekliyor');
  wrapper.appendChild(status);
  return wrapper;
}

function refreshFeedbackBars() {
  document.querySelectorAll('.msg[data-role="assistant"]').forEach(bubble => {
    const oldBar = bubble.querySelector('.feedback-bar');
    if (oldBar) oldBar.remove();
    bubble.appendChild(buildFeedbackBar(bubble.dataset.messageId));
  });
}

function showTyping() {
  const el = document.createElement('div');
  el.className = 'typing';
  el.id = 'typing-indicator';
  el.innerHTML = '<span></span><span></span><span></span>';
  messagesEl.appendChild(el);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function hideTyping() {
  const el = document.getElementById('typing-indicator');
  if (el) el.remove();
}

function resetDebugPanel() {
  document.getElementById('d-state').innerHTML = '<span class="debug-badge badge-state">-</span>';
  document.getElementById('d-intent').innerHTML = '<span class="debug-badge badge-intent">-</span>';
  document.getElementById('d-lang').innerHTML = '<span class="debug-badge badge-lang">-</span>';
  document.getElementById('d-flags').innerHTML = '<span class="feedback-muted">Flag yok</span>';
  document.getElementById('d-escalation').textContent = '-';
  document.getElementById('d-entities').textContent = '{}';
  document.getElementById('d-next').textContent = '-';
  document.getElementById('d-full').textContent = '{}';
}

function updateDebug(ij, conv) {
  if (!ij) return;
  document.getElementById('d-state').innerHTML = '<span class="debug-badge badge-state">' + escapeHtml(conv?.state || ij.state || '-') + '</span>';
  document.getElementById('d-intent').innerHTML = '<span class="debug-badge badge-intent">' + escapeHtml(ij.intent || '-') + '</span>';
  document.getElementById('d-lang').innerHTML = '<span class="debug-badge badge-lang">' + escapeHtml(ij.language || '-') + '</span>';

  const flagsEl = document.getElementById('d-flags');
  const allFlags = [...(ij.risk_flags || []), ...(conv?.risk_flags || [])];
  const unique = [...new Set(allFlags)];
  if (unique.length === 0) {
    flagsEl.innerHTML = '<span class="feedback-muted">Flag yok</span>';
  } else {
    flagsEl.innerHTML = unique.map(flag => '<span class="flag flag-' + flagLevel(flag) + '">' + escapeHtml(flag) + '</span>').join('');
  }

  const esc = ij.escalation || {};
  document.getElementById('d-escalation').textContent = 'Level: ' + (esc.level || 'L0') + ' | Role: ' + (esc.route_to_role || 'NONE');
  document.getElementById('d-entities').textContent = JSON.stringify(ij.entities || {}, null, 2);
  document.getElementById('d-next').textContent = ij.next_step || '-';
  document.getElementById('d-full').textContent = JSON.stringify(ij, null, 2);
}

function resetFeedbackStudio() {
  selectedFeedback = null;
  document.getElementById('feedback-empty').hidden = false;
  document.getElementById('feedback-active').hidden = true;
  document.getElementById('feedback-form').hidden = true;
  document.getElementById('feedback-result').hidden = true;
  document.getElementById('feedback-correction').value = '';
  document.getElementById('feedback-rating-chip').textContent = 'Puan secilmedi';
  document.getElementById('feedback-rating-help').textContent = '-';
}

function showFeedbackSelection(messageId, rating) {
  const meta = feedbackMeta(rating);
  selectedFeedback = {messageId: messageId, rating: rating, originalText: assistantReplies.get(messageId) || ''};
  document.getElementById('feedback-empty').hidden = true;
  document.getElementById('feedback-active').hidden = false;
  document.getElementById('feedback-rating-chip').textContent = rating + '/5 - ' + meta.label;
  document.getElementById('feedback-rating-help').textContent = meta.tooltip;
  document.getElementById('feedback-info').title = meta.tooltip;
  document.getElementById('feedback-result').hidden = true;

  const form = document.getElementById('feedback-form');
  const textarea = document.getElementById('feedback-correction');
  if (meta.correction_required) {
    form.hidden = false;
    textarea.placeholder = rating === 4 ? 'Daha kisa ve temiz versiyonu burada duzenleyin...' : 'Dogru bilgiyi veya duzeltilmis cevabi yazin...';
    textarea.value = rating === 4 ? selectedFeedback.originalText : '';
    textarea.focus();
  } else {
    form.hidden = true;
  }
}

async function selectFeedback(messageId, rating) {
  showFeedbackSelection(messageId, rating);
  refreshFeedbackBars();
  if (rating === 5) {
    await submitFeedback();
  }
}

function showFeedbackResult(result) {
  const meta = [];
  meta.push(result.rating + '/5 - ' + result.rating_label);
  if (result.selected_model) meta.push('Model: ' + result.selected_model);
  if (result.scenario_code) meta.push('Senaryo: ' + result.scenario_code);
  if (result.scenario_path) meta.push('Dosya: ' + result.scenario_path);
  document.getElementById('feedback-result-meta').textContent = meta.join(' | ');
  document.getElementById('feedback-corrected-reply').textContent = result.corrected_reply || 'Mukemmel olarak isaretlendi; ek duzeltme uretilmedi.';
  document.getElementById('feedback-result').hidden = false;
}

async function submitFeedback() {
  if (!selectedFeedback) return;

  const meta = feedbackMeta(selectedFeedback.rating);
  const correction = document.getElementById('feedback-correction').value.trim();
  if (meta.correction_required && !correction) {
    document.getElementById('feedback-rating-help').textContent = 'Bu puan icin duzeltme girmelisiniz.';
    return;
  }

  const payload = {
    phone: document.getElementById('phone-input').value.trim() || 'test_user_123',
    assistant_message_id: selectedFeedback.messageId,
    rating: selectedFeedback.rating,
    correction: meta.correction_required ? correction : null,
  };

  const submitButton = document.getElementById('feedback-submit');
  submitButton.disabled = true;
  try {
    const response = await fetch(API + '/chat/feedback', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.detail || 'Geri bildirim kaydedilemedi.');
    }

    const statusText = data.status === 'scenario_created' ? data.scenario_code + ' hazirlandi' : 'Mukemmel olarak kaydedildi';
    feedbackStates.set(selectedFeedback.messageId, {rating: selectedFeedback.rating, status: statusText});
    showFeedbackSelection(selectedFeedback.messageId, selectedFeedback.rating);
    showFeedbackResult(data);
    refreshFeedbackBars();
  } catch (error) {
    document.getElementById('feedback-rating-help').textContent = error.message || 'Geri bildirim kaydedilemedi.';
  } finally {
    submitButton.disabled = false;
  }
}

async function sendMessage() {
  const text = inputEl.value.trim();
  if (!text) return;
  const phone = document.getElementById('phone-input').value.trim() || 'test_user_123';
  inputEl.value = '';
  autoResize();
  addBubble('user', text, new Date().toISOString());
  showTyping();

  try {
    const res = await fetch(API + '/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: text, phone: phone}),
    });
    hideTyping();
    if (!res.ok) {
      const err = await res.json().catch(() => ({detail:'Bilinmeyen hata'}));
      addBubble('system', 'Istek basarisiz: ' + (err.detail || 'Bilinmeyen hata'));
      return;
    }
    const data = await res.json();
    addBubble('assistant', data.reply, data.timestamp, data.assistant_message_id);
    updateDebug(data.internal_json, data.conversation);
  } catch (error) {
    hideTyping();
    addBubble('system', 'Baglanti hatasi: ' + (error.message || 'Bilinmeyen hata'));
  }
}

async function loadHistory() {
  const phone = document.getElementById('phone-input').value.trim() || 'test_user_123';
  try {
    const res = await fetch(API + '/chat/history?phone=' + encodeURIComponent(phone));
    if (!res.ok) return;
    const data = await res.json();
    messagesEl.querySelectorAll('.msg').forEach(el => el.remove());
    assistantReplies.clear();
    feedbackStates.clear();
    if (!data.messages || data.messages.length === 0) {
      if (emptyState) emptyState.style.display = '';
      return;
    }
    data.messages.forEach(message => addBubble(message.role, message.content, message.created_at, message.id));
    const lastAssistant = [...data.messages].reverse().find(message => message.role === 'assistant');
    if (lastAssistant && lastAssistant.internal_json) {
      updateDebug(lastAssistant.internal_json, data.conversation);
    }
  } catch {}
}

async function resetConversation() {
  const phone = document.getElementById('phone-input').value.trim() || 'test_user_123';
  try {
    await fetch(API + '/chat/reset?phone=' + encodeURIComponent(phone), {method:'POST'});
  } catch {}
  messagesEl.querySelectorAll('.msg,.typing').forEach(el => el.remove());
  assistantReplies.clear();
  feedbackStates.clear();
  if (emptyState) emptyState.style.display = '';
  resetDebugPanel();
  resetFeedbackStudio();
  addBubble('system', 'Konusma sifirlandi. Yeni bir mesaj gonderebilirsiniz.');
}

function downloadConversation() {
  const phone = document.getElementById('phone-input').value.trim() || 'test_user_123';
  const format = document.getElementById('save-format').value || 'md';
  const url = API + '/chat/export?phone=' + encodeURIComponent(phone) + '&format=' + encodeURIComponent(format);
  window.open(url, '_blank');
}

function toggleDebug() {
  debugPanel.classList.toggle('collapsed');
}

function handleKey(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
}

function autoResize() {
  inputEl.style.height = 'auto';
  inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + 'px';
}

inputEl.addEventListener('input', autoResize);

async function loadModels() {
  const select = document.getElementById('model-select');
  try {
    const res = await fetch(API + '/models');
    if (!res.ok) return;
    const data = await res.json();
    select.innerHTML = '';
    (data.models || []).forEach(model => {
      const option = document.createElement('option');
      option.value = model;
      option.textContent = model;
      if (model === data.current) option.selected = true;
      select.appendChild(option);
    });
    if (select.options.length === 0) {
      select.innerHTML = '<option>' + (data.current || 'bilinmiyor') + '</option>';
    }
  } catch {
    select.innerHTML = '<option>hata</option>';
  }
}

async function loadFeedbackScale() {
  try {
    const res = await fetch(API + '/chat/feedback-scale');
    if (!res.ok) return;
    const data = await res.json();
    if (Array.isArray(data.items) && data.items.length) {
      feedbackScale = data.items;
    }
  } catch {}
}

async function changeModel(model) {
  try {
    await fetch(API + '/model', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({model: model}),
    });
    addBubble('system', 'Test modeli degisti: ' + model);
  } catch {}
}

Promise.all([loadModels(), loadFeedbackScale()]).finally(() => {
  loadHistory();
  resetFeedbackStudio();
});
"""
