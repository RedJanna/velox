"""Static assets for the Chat Lab HTML interface."""

# ruff: noqa: E501

TEST_CHAT_STYLE = """\
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --navy:#12213b;--ink:#0f172a;--muted:#64748b;--muted-2:#9aa7b8;--paper:#fff;
  --sand:#f6f2e8;--line:#d6dce8;--teal:#15756f;--teal-2:#2a9d8f;--amber:#e7bf5f;
  --red:#dc2626;--shadow:0 18px 36px rgba(15,23,42,.12);--mono:'Cascadia Code','Fira Code',monospace;
}
html,body{height:100%;font-family:'Segoe UI',system-ui,sans-serif;background:
radial-gradient(circle at top left,rgba(231,191,95,.22),transparent 28%),
linear-gradient(180deg,#f8f6f0 0%,#edf2f7 100%);color:var(--ink)}
body{overflow:hidden}
.app{display:flex;flex-direction:column;height:100vh}
.header{display:flex;align-items:center;gap:16px;padding:14px 22px;border-bottom:1px solid rgba(18,33,59,.08);background:rgba(255,255,255,.84);backdrop-filter:blur(18px)}
.header-brand{display:flex;align-items:center;gap:14px}
.header-copy h1{font-size:18px;font-weight:700;letter-spacing:.02em}
.header-copy p{font-size:12px;color:var(--muted);margin-top:2px}
.header-controls{margin-left:auto;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.field{display:flex;align-items:center;gap:8px}
.field label{font-size:12px;font-weight:700;color:var(--muted)}
.header-select,.header-input,.input-bar textarea,.debug-input,.debug-select,.debug-textarea{
  border:1px solid rgba(18,33,59,.12);border-radius:14px;background:rgba(255,255,255,.94);color:var(--ink);outline:none;
  transition:border-color .18s ease,box-shadow .18s ease
}
.header-select,.header-input{height:38px;padding:0 12px}
.header-select:focus,.header-input:focus,.input-bar textarea:focus,.debug-input:focus,.debug-select:focus,.debug-textarea:focus{
  border-color:var(--teal);box-shadow:0 0 0 3px rgba(21,117,111,.12)
}
.header-select-model{min-width:170px}.header-select-import{min-width:220px}.header-input{width:150px}
.btn{height:38px;border:none;border-radius:12px;padding:0 14px;font-size:13px;font-weight:700;cursor:pointer;transition:transform .15s ease,opacity .15s ease}
.btn:hover{transform:translateY(-1px)}.btn:disabled{opacity:.5;cursor:not-allowed;transform:none}
.btn-reset{background:#fee2e2;color:#991b1b}.btn-save{background:var(--amber);color:#4a3405}.btn-ghost{background:rgba(18,33,59,.08);color:var(--ink)}.btn-primary{background:var(--teal);color:#fff}
.btn-toggle{display:none}
.main{display:flex;flex:1;min-height:0}
.chat-panel{flex:1;display:flex;flex-direction:column;min-width:0}
.messages{flex:1;overflow-y:auto;padding:24px;display:flex;flex-direction:column;gap:12px}
.messages::-webkit-scrollbar,.debug-body::-webkit-scrollbar{width:7px}
.messages::-webkit-scrollbar-thumb,.debug-body::-webkit-scrollbar-thumb{background:rgba(100,116,139,.28);border-radius:999px}
.msg{max-width:76%;display:flex;flex-direction:column;gap:8px;padding:14px 16px;border-radius:20px;box-shadow:var(--shadow);animation:fadeIn .22s ease}
.msg-user{align-self:flex-end;background:linear-gradient(135deg,var(--teal),var(--teal-2));color:#fff;border-bottom-right-radius:6px}
.msg-assistant{align-self:flex-start;background:rgba(255,255,255,.96);border:1px solid rgba(18,33,59,.08);border-bottom-left-radius:6px}
.msg-system{align-self:center;max-width:88%;background:rgba(18,33,59,.08);color:var(--muted);box-shadow:none}
.msg-body{font-size:14px;line-height:1.55;word-break:break-word}
.msg-time{font-size:11px;opacity:.66}.msg-user .msg-time{text-align:right}
.feedback-bar{display:flex;flex-wrap:wrap;align-items:center;gap:8px;padding-top:6px;border-top:1px solid rgba(18,33,59,.08)}
.feedback-label{font-size:11px;font-weight:800;letter-spacing:.04em;text-transform:uppercase;color:var(--muted)}
.feedback-buttons{display:flex;gap:6px;flex-wrap:wrap}
.feedback-score{width:28px;height:28px;border-radius:999px;border:1px solid rgba(18,33,59,.14);background:#fff;color:var(--ink);font-size:12px;font-weight:700;cursor:pointer}
.feedback-score:hover{border-color:var(--teal);color:var(--teal)}.feedback-score.is-active{background:var(--teal);border-color:var(--teal);color:#fff}
.feedback-status{font-size:11px;color:var(--muted)}
.typing{align-self:flex-start;display:flex;gap:5px;padding:13px 16px;background:rgba(255,255,255,.96);border-radius:18px;border:1px solid rgba(18,33,59,.08);box-shadow:var(--shadow)}
.typing span{width:8px;height:8px;border-radius:50%;background:var(--muted-2);animation:bounce .6s infinite alternate}
.typing span:nth-child(2){animation-delay:.2s}.typing span:nth-child(3){animation-delay:.4s}
.empty-state{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;min-height:100%;color:var(--muted)}
.empty-state svg{width:52px;height:52px;opacity:.35}
.input-bar{display:flex;align-items:flex-end;gap:12px;padding:16px 20px;border-top:1px solid rgba(18,33,59,.08);background:rgba(255,255,255,.86)}
.input-bar textarea{flex:1;resize:none;padding:12px 16px;font-size:14px;line-height:1.45;max-height:130px}
.btn-send{width:46px;height:46px;border-radius:16px;display:flex;align-items:center;justify-content:center}
.btn-send svg{width:20px;height:20px;fill:currentColor}
.debug-panel{width:410px;display:flex;flex-direction:column;background:linear-gradient(180deg,#152238 0%,#0f172a 100%);color:#fff;border-left:1px solid rgba(255,255,255,.06)}
.debug-panel.collapsed{width:0;border:none;overflow:hidden}
.debug-header{display:flex;align-items:center;gap:10px;padding:16px 18px;border-bottom:1px solid rgba(255,255,255,.08)}
.debug-header strong{font-size:14px}.debug-header span{font-size:12px;color:rgba(255,255,255,.62)}
.debug-body{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:14px}
.debug-section{padding:14px;border-radius:18px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.06)}
.debug-section h3{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:rgba(255,255,255,.62);margin-bottom:8px}
.debug-value{font-size:13px;line-height:1.55}
.debug-json,.meta-box{font-family:var(--mono);font-size:12px;white-space:pre-wrap;word-break:break-word;color:#bfdbfe;background:rgba(2,6,23,.35);border-radius:14px;padding:10px;max-height:220px;overflow:auto}
.meta-box{color:#e2e8f0}
.debug-badge{display:inline-flex;align-items:center;gap:4px;padding:4px 10px;border-radius:999px;font-size:11px;font-weight:700}
.badge-state{background:rgba(42,157,143,.2);color:#8df7e8}.badge-intent{background:rgba(233,196,106,.18);color:#ffe49a}.badge-lang{background:rgba(255,255,255,.14);color:#fff}
.debug-flags{display:flex;flex-wrap:wrap;gap:6px}.flag{padding:4px 8px;border-radius:999px;font-size:11px;font-weight:700}
.flag-l3{background:#7f1d1d;color:#fecaca}.flag-l2{background:#78350f;color:#fde68a}.flag-l1{background:#365314;color:#dcfce7}.flag-l0{background:rgba(255,255,255,.12);color:#fff}
.studio-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}
.studio-head p,.feedback-muted,.report-muted{font-size:12px;color:rgba(255,255,255,.64);line-height:1.5}
.feedback-chip{display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding:6px 10px;background:rgba(21,117,111,.18);color:#a7f3d0;font-size:12px;font-weight:700}
.debug-input,.debug-select,.debug-textarea{width:100%;padding:10px 12px;background:rgba(255,255,255,.92)}
.debug-textarea{min-height:96px;resize:vertical}
.field-stack{display:flex;flex-direction:column;gap:6px;margin-top:10px}
.field-stack label{font-size:12px;font-weight:700;color:rgba(255,255,255,.8)}
.helper-card{padding:10px 12px;border-radius:14px;background:rgba(2,6,23,.24);border:1px solid rgba(255,255,255,.08);font-size:12px;line-height:1.5;color:rgba(255,255,255,.72)}
.helper-card strong{display:block;color:#fff;margin-bottom:3px}
.tag-toolbar{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:8px}
.tag-toolbar .feedback-muted{flex:1}
.btn-mini{height:30px;padding:0 12px;font-size:12px;border-radius:10px}
.checkbox-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px}
.check-item{display:flex;align-items:flex-start;gap:8px;padding:8px 10px;border-radius:14px;background:rgba(2,6,23,.24);border:1px solid rgba(255,255,255,.08)}
.check-item input{margin-top:2px}.check-copy strong{display:block;font-size:12px;color:#fff}.check-copy span{display:block;font-size:11px;color:rgba(255,255,255,.6);margin-top:2px}
.inline-note{font-size:11px;color:#fcd34d}
.hidden{display:none!important}
.source-badge{display:inline-flex;align-items:center;gap:6px;padding:6px 10px;border-radius:999px;background:rgba(233,191,95,.16);color:#ffe49a;font-size:12px;font-weight:700}
.list{display:flex;flex-direction:column;gap:8px}
.list-item{padding:10px 12px;border-radius:14px;background:rgba(2,6,23,.24);border:1px solid rgba(255,255,255,.08)}
.list-item strong{display:block;font-size:12px}.list-item span{display:block;font-size:11px;color:rgba(255,255,255,.64);margin-top:3px}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@keyframes bounce{to{opacity:.35;transform:translateY(-4px)}}
@media(max-width:1040px){
  .debug-panel{position:fixed;inset:0 0 0 auto;z-index:30;width:min(90vw,410px)}
  .btn-toggle{display:inline-flex;align-items:center;justify-content:center}
  .msg{max-width:90%}
}
"""

TEST_CHAT_SCRIPT = """\
const API = '/api/v1/test';
const DEFAULT_FEEDBACK_SCALES = [
  {rating: 1, label: 'Kesinlikle Yanlis', summary: 'Yanit tamamen hatali.', tooltip: 'Bilgi tamamen yanlis mi? Burayi sec ve dogruyu sisteme ogret.', correction_required: true},
  {rating: 2, label: 'Hatali Anlatim', summary: 'Bilgi ozunde dogru ama anlatim bozuk.', tooltip: 'Bilgi dogru ama anlatim bozuk mu?', correction_required: true},
  {rating: 3, label: 'Eksik Bilgi', summary: 'Temel cevap dogru ama kritik detay eksik.', tooltip: 'Cevap yetersiz mi? Eksikleri tamamla.', correction_required: true},
  {rating: 4, label: 'Gereksiz Ayrinti', summary: 'Bilgi dogru ama fazla uzun.', tooltip: 'Cok mu laf kalabaligi var? Sadelestirilmis halini onayla.', correction_required: true},
  {rating: 5, label: 'Mukemmel', summary: 'Yanit dogru ve onayli ornek olmaya uygun.', tooltip: 'Yanit dogruysa bunu secin; onayli ornek havuzuna eklenir.', correction_required: false},
];
const DEFAULT_FEEDBACK_CATEGORIES = [
  {key: 'yanlis_bilgi', label: 'Yanlis Bilgi', description: 'Net olarak yanlis bilgi verilmesi.', tooltip: 'Ornek: EUR yerine USD yazmak.'},
  {key: 'eksik_bilgi', label: 'Eksik Bilgi', description: 'Temel cevap dogru ama kritik detaylar eksik.', tooltip: 'Cevap yarim kaliyor veya gerekli bilgi tamamlanmiyor.'},
  {key: 'alakasiz_yanit', label: 'Alakasiz Yanit', description: 'Sorudan kopuk veya konu disi cevap.', tooltip: 'Kullanici niyetini kaciran cevaplar.'},
  {key: 'baglam_kopuklugu', label: 'Baglam Kopuklugu', description: 'Sohbet akisina uyumsuz cevap.', tooltip: 'Hafiza kaybi gibi davranan cevaplar.'},
  {key: 'uydurma_bilgi', label: 'Asiri Ozyguvenli Uydurma', description: 'Kaynaksiz bilgi uydurulmasi.', tooltip: 'Bilmiyorum demek yerine uydurma bilgi verilmesi.'},
  {key: 'gevezelik', label: 'Gevezelik / Uzunluk', description: 'Gereksiz uzun veya daginik cevap.', tooltip: 'Kisa istek icin asiri uzun mesaj.'},
  {key: 'intent_iskalama', label: 'Intent Iskalama', description: 'Asil talebi kaciran cevap.', tooltip: 'Kelimeyi anlayip amaci gormeyen cevap.'},
  {key: 'format_ihlali', label: 'Format Ihlali', description: 'Istenen sunum bicimine uymayan cevap.', tooltip: 'Liste yerine duz metin gibi.'},
  {key: 'mantik_celiskisi', label: 'Eksik / Celiskili Mantik', description: 'Tutarsiz veya eksik mantik.', tooltip: 'Bir adim digerini bozuyor.'},
  {key: 'ton_politika_ihlali', label: 'Ton / Politika Ihlali', description: 'Uslup veya politika ihlali.', tooltip: 'Kaba uslup ya da yetkisiz taahhut.'},
  {key: 'ozel_kategori', label: 'Ozel Kategori', description: 'Hazir listeye sigmayan durum.', tooltip: 'Aciklamayi admin manuel yazar.'},
];
const DEFAULT_FEEDBACK_TAGS = [
  {key: 'yanlis_bilgi', label: 'Yanlis Bilgi', description: 'Net bilgi hatasi.'},
  {key: 'eksik_bilgi', label: 'Eksik Bilgi', description: 'Kritik detay eksik.'},
  {key: 'alakasiz_yanit', label: 'Alakasiz Yanit', description: 'Sorudan kopuk cevap.'},
  {key: 'baglam_kopuklugu', label: 'Baglam Kopuklugu', description: 'Onceki konusma unutuluyor.'},
  {key: 'niyet_iskalama', label: 'Niyet Iskalama', description: 'Asil amac anlasilmiyor.'},
  {key: 'asiri_uzun_yanit', label: 'Asiri Uzun Yanit', description: 'Gereksiz uzun mesaj.'},
  {key: 'asiri_kisa_yanit', label: 'Asiri Kisa Yanit', description: 'Eksik aciklama iceren kisa cevap.'},
  {key: 'tekrar_loop', label: 'Tekrar / Loop', description: 'Ayni kalip tekrar ediyor.'},
  {key: 'format_ihlali', label: 'Format Ihlali', description: 'Istenen format bozuluyor.'},
  {key: 'ton_uyumsuzlugu', label: 'Ton Uyumsuzlugu', description: 'Duruma uygun olmayan uslup.'},
  {key: 'kaba_uslup', label: 'Kaba Uslup', description: 'Premium sicak ton bozuluyor.'},
  {key: 'politika_ihlali', label: 'Politika Ihlali', description: 'Kurallarin disina cikiliyor.'},
  {key: 'uydurma_bilgi', label: 'Uydurma Bilgi', description: 'Kaynaksiz bilgi uyduruluyor.'},
  {key: 'guncel_olmayan_bilgi', label: 'Guncel Olmayan Bilgi', description: 'Eski bilgi kullaniliyor.'},
  {key: 'hotel_profile_celiskisi', label: 'Hotel Profile Celiskisi', description: 'Hotel profile ile uyumsuz cevap.'},
  {key: 'tool_output_celiskisi', label: 'Tool Output Celiskisi', description: 'Tool sonucu ile uyumsuz cevap.'},
  {key: 'mantik_celiskisi', label: 'Mantik Celiskisi', description: 'Cevap kendi icinde tutarsiz.'},
  {key: 'eksik_dogrulama_sorusu', label: 'Eksik Dogrulama Sorusu', description: 'Gerekli netlestirme sorusu yok.'},
  {key: 'gereksiz_pii_talebi', label: 'Gereksiz PII Talebi', description: 'Gereksiz kisisel veri istendi.'},
  {key: 'gereksiz_escalation', label: 'Gereksiz Escalation', description: 'Gereksiz insan devri yapildi.'},
];

const state = {
  sourceType: 'live_test_chat',
  importFile: '',
  roleMapping: {},
  messages: [],
  conversation: null,
  importMetadata: {},
  catalog: {
    scales: DEFAULT_FEEDBACK_SCALES,
    categories: DEFAULT_FEEDBACK_CATEGORIES,
    tags: DEFAULT_FEEDBACK_TAGS,
    default_report_start: null,
    default_report_end: null,
  },
  feedbackStates: new Map(),
  selectedFeedback: null,
  manualTagTouched: false,
};
const CATEGORY_PRIORITY = ['yanlis_bilgi', 'eksik_bilgi', 'baglam_kopuklugu', 'intent_iskalama', 'mantik_celiskisi', 'format_ihlali', 'gevezelik', 'alakasiz_yanit', 'uydurma_bilgi', 'ton_politika_ihlali', 'ozel_kategori'];
const CATEGORY_TAG_SUGGESTIONS = {
  yanlis_bilgi: ['yanlis_bilgi', 'tool_output_celiskisi'],
  eksik_bilgi: ['eksik_bilgi', 'eksik_dogrulama_sorusu'],
  alakasiz_yanit: ['alakasiz_yanit', 'niyet_iskalama'],
  baglam_kopuklugu: ['baglam_kopuklugu', 'mantik_celiskisi'],
  uydurma_bilgi: ['uydurma_bilgi', 'guncel_olmayan_bilgi'],
  gevezelik: ['asiri_uzun_yanit'],
  intent_iskalama: ['niyet_iskalama', 'eksik_dogrulama_sorusu'],
  format_ihlali: ['format_ihlali'],
  mantik_celiskisi: ['mantik_celiskisi'],
  ton_politika_ihlali: ['ton_uyumsuzlugu', 'politika_ihlali'],
};

const L3_FLAGS = ['LEGAL_REQUEST','SECURITY_INCIDENT','THREAT_SELF_HARM','MEDICAL_EMERGENCY'];
const L2_FLAGS = ['PAYMENT_CONFUSION','CHARGEBACK','REFUND_DISPUTE','ANGRY_COMPLAINT','FRAUD_SIGNAL','GROUP_BOOKING','CONTRACT_QUESTION','REPEAT_COMPLAINT','SOCIAL_MEDIA_THREAT','PRICE_MATCH','SYSTEM_ERROR','DOUBLE_CHARGE','TOOL_ERROR_REPEAT','TOOL_UNAVAILABLE'];
const L1_FLAGS = ['VIP_REQUEST','ALLERGY_ALERT','ACCESSIBILITY_NEED','CHILD_SAFETY','CAPACITY_LIMIT','WEATHER_ALERT','SPECIAL_EVENT_FLAG','DIETARY_RESTRICTION'];

const el = id => document.getElementById(id);

function escapeHtml(value) {
  return String(value ?? '')
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
  try { return new Date(iso).toLocaleTimeString('tr-TR', {hour:'2-digit', minute:'2-digit'}); }
  catch { return ''; }
}

function flagLevel(flag) {
  if (L3_FLAGS.includes(flag)) return 'l3';
  if (L2_FLAGS.includes(flag)) return 'l2';
  if (L1_FLAGS.includes(flag)) return 'l1';
  return 'l0';
}

function feedbackMeta(rating) {
  return state.catalog.scales.find(item => item.rating === rating) || null;
}

function categoryMeta(categoryKey) {
  return state.catalog.categories.find(item => item.key === categoryKey) || null;
}

function sortedCategories() {
  return [...state.catalog.categories].sort((left, right) => {
    const leftPriority = CATEGORY_PRIORITY.indexOf(left.key);
    const rightPriority = CATEGORY_PRIORITY.indexOf(right.key);
    const normalizedLeft = leftPriority === -1 ? 999 : leftPriority;
    const normalizedRight = rightPriority === -1 ? 999 : rightPriority;
    if (normalizedLeft !== normalizedRight) return normalizedLeft - normalizedRight;
    return String(left.label || '').localeCompare(String(right.label || ''), 'tr');
  });
}

function selectedTagKeys() {
  return Array.from(document.querySelectorAll('#feedback-tags input[type=checkbox]:checked')).map(input => input.value);
}

function setCheckedTags(tagKeys) {
  const tagSet = new Set(tagKeys);
  document.querySelectorAll('#feedback-tags input[type=checkbox]').forEach(input => {
    input.checked = tagSet.has(input.value);
  });
}

function updateCategoryGuidance() {
  const selectedCategory = el('feedback-category').value;
  const helper = el('feedback-category-help');
  const recommendation = el('feedback-tags-note');
  const recommendedTags = CATEGORY_TAG_SUGGESTIONS[selectedCategory] || [];
  const meta = categoryMeta(selectedCategory);

  if (!selectedCategory) {
    helper.innerHTML = '<strong>Secim Yardimi</strong>Ana problem turunu secin; buna gore etiket onerileri hazirlanir.';
    recommendation.textContent = 'Kategori secince ilgili etiketler otomatik onerilir.';
    return;
  }

  const tooltip = meta?.tooltip ? ` ${meta.tooltip}` : '';
  helper.innerHTML = `<strong>${escapeHtml(meta?.label || selectedCategory)}</strong>${escapeHtml((meta?.description || '') + tooltip)}`;
  if (!recommendedTags.length) {
    recommendation.textContent = 'Bu kategori icin hazir etiket onerisi yok.';
    return;
  }

  const recommendationText = recommendedTags
    .map(tagKey => state.catalog.tags.find(item => item.key === tagKey)?.label || tagKey)
    .join(', ');
  recommendation.textContent = state.manualTagTouched
    ? `Onerilen etiketler: ${recommendationText}. Mevcut manuel secim korunuyor.`
    : `Onerilen etiketler otomatik uygulandi: ${recommendationText}.`;
}

function applyCategorySuggestions(force = false) {
  const selectedCategory = el('feedback-category').value;
  const recommendedTags = CATEGORY_TAG_SUGGESTIONS[selectedCategory] || [];
  if (!selectedCategory || !recommendedTags.length) {
    updateCategoryGuidance();
    return;
  }
  if (!force && state.manualTagTouched) {
    updateCategoryGuidance();
    return;
  }
  setCheckedTags(recommendedTags);
  state.manualTagTouched = false;
  updateCategoryGuidance();
}

async function apiFetch(path, options = {}) {
  const response = await fetch(API + path, options);
  let data = null;
  let rawText = '';
  try {
    data = await response.json();
  } catch {
    try {
      rawText = await response.text();
    } catch {
      rawText = '';
    }
  }
  if (!response.ok) {
    throw new Error(extractApiErrorMessage(data, rawText));
  }
  return data || {};
}

function extractApiErrorMessage(data, rawText) {
  if (typeof data?.detail === 'string' && data.detail.trim()) {
    return data.detail.trim();
  }
  if (Array.isArray(data?.detail) && data.detail.length) {
    return data.detail
      .map(item => {
        if (typeof item === 'string') return item;
        const location = Array.isArray(item?.loc) ? item.loc.join(' > ') : 'field';
        const message = item?.msg || JSON.stringify(item);
        return `${location}: ${message}`;
      })
      .join(' | ');
  }
  if (rawText && rawText.trim()) {
    return rawText.trim().slice(0, 400);
  }
  return 'Islem tamamlanamadi.';
}

function showTyping() {
  const typing = document.createElement('div');
  typing.className = 'typing';
  typing.id = 'typing-indicator';
  typing.innerHTML = '<span></span><span></span><span></span>';
  el('messages').appendChild(typing);
  el('messages').scrollTop = el('messages').scrollHeight;
}

function hideTyping() {
  const typing = el('typing-indicator');
  if (typing) typing.remove();
}

function renderMessages() {
  const container = el('messages');
  container.innerHTML = '';
  if (state.messages.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/></svg>
        <p>Canli test veya import kaydi secin; sonra asistan mesajlarini puanlayin.</p>
      </div>`;
    return;
  }

  state.messages.forEach(message => {
    const bubble = document.createElement('div');
    bubble.className = 'msg msg-' + message.role;
    bubble.dataset.role = message.role;
    bubble.dataset.messageId = message.id || '';

    const body = document.createElement('div');
    body.className = 'msg-body';
    body.innerHTML = formatMessageHtml(message.content || '');
    bubble.appendChild(body);

    const stamp = document.createElement('div');
    stamp.className = 'msg-time';
    stamp.textContent = fmtTime(message.created_at);
    bubble.appendChild(stamp);

    if (message.role === 'assistant' && message.id) {
      bubble.appendChild(buildFeedbackBar(message.id));
    }
    container.appendChild(bubble);
  });
  container.scrollTop = container.scrollHeight;
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
  const saved = state.feedbackStates.get(messageId);
  state.catalog.scales.forEach(item => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'feedback-score';
    button.textContent = item.rating;
    button.title = item.tooltip;
    const selected = state.selectedFeedback && state.selectedFeedback.messageId === messageId && state.selectedFeedback.rating === item.rating;
    if ((saved && saved.rating === item.rating) || selected) button.classList.add('is-active');
    button.addEventListener('click', () => selectFeedback(messageId, item.rating));
    buttons.appendChild(button);
  });
  wrapper.appendChild(buttons);

  const status = document.createElement('span');
  status.className = 'feedback-status';
  status.textContent = saved?.status || 'Puan secin';
  wrapper.appendChild(status);
  return wrapper;
}

function findMessage(messageId) {
  return state.messages.find(message => String(message.id) === String(messageId)) || null;
}

function buildFeedbackContext(messageId) {
  const index = state.messages.findIndex(message => String(message.id) === String(messageId));
  if (index < 0) return null;
  const message = state.messages[index];
  let inputText = '';
  for (let cursor = index - 1; cursor >= 0; cursor -= 1) {
    if (state.messages[cursor].role === 'user') {
      inputText = state.messages[cursor].content || '';
      break;
    }
  }
  const internal = message.internal_json || {};
  const toolCalls = Array.isArray(internal.tool_calls)
    ? internal.tool_calls.map(item => item.name || item.function?.name).filter(Boolean)
    : [];
  return {
    input: inputText,
    output: message.content || '',
    conversationId: state.conversation?.id || state.importMetadata.conversation_id || '-',
    assistantMessageId: String(message.id || ''),
    timestamp: message.created_at || '',
    language: state.conversation?.language || state.importMetadata.language || internal.language || '-',
    intent: internal.intent || state.conversation?.intent || state.importMetadata.intent || '-',
    currentState: internal.state || state.conversation?.state || state.importMetadata.state || '-',
    riskFlags: internal.risk_flags || state.conversation?.risk_flags || state.importMetadata.risk_flags || [],
    toolCalls: toolCalls,
    model: message.model || state.importMetadata.model || el('model-select').value || '-',
    sourceType: state.sourceType,
  };
}

function renderFeedbackStudio() {
  const empty = el('feedback-empty');
  const active = el('feedback-active');
  const result = el('feedback-result');
  const approvedRow = el('approved-example-row');
  const customCategory = el('feedback-custom-category-row');
  result.classList.add('hidden');

  if (!state.selectedFeedback) {
    empty.classList.remove('hidden');
    active.classList.add('hidden');
    el('feedback-meta').textContent = '';
    return;
  }

  const ctx = buildFeedbackContext(state.selectedFeedback.messageId);
  const meta = feedbackMeta(state.selectedFeedback.rating);
  empty.classList.add('hidden');
  active.classList.remove('hidden');
  el('feedback-rating-chip').textContent = `${state.selectedFeedback.rating}/5 - ${meta ? meta.label : '-'}`;
  el('feedback-rating-help').textContent = meta ? meta.tooltip : '-';
  el('feedback-meta').textContent = [
    `input: ${ctx?.input || '-'}`,
    `output: ${ctx?.output || '-'}`,
    `conversation_id: ${ctx?.conversationId || '-'}`,
    `assistant_message_id: ${ctx?.assistantMessageId || '-'}`,
    `timestamp: ${ctx?.timestamp || '-'}`,
    `language: ${ctx?.language || '-'}`,
    `intent: ${ctx?.intent || '-'}`,
    `state: ${ctx?.currentState || '-'}`,
    `risk_flags: ${(ctx?.riskFlags || []).join(', ') || '-'}`,
    `tool_calls: ${(ctx?.toolCalls || []).join(', ') || '-'}`,
    `model: ${ctx?.model || '-'}`,
    `source_type: ${ctx?.sourceType || '-'}`,
  ].join('\\n');

  approvedRow.classList.toggle('hidden', state.selectedFeedback.rating !== 5);
  el('feedback-gold-standard').placeholder = state.selectedFeedback.rating === 4
    ? 'Daha sade ve kisa onayli cevabi yazin...'
    : 'Dogru bilgiyi veya Altin Standart cevabi yazin...';
  customCategory.classList.toggle('hidden', el('feedback-category').value !== 'ozel_kategori');
  updateCategoryGuidance();
}

function renderCategoryOptions() {
  const selectedValue = el('feedback-category').value;
  el('feedback-category').innerHTML = '<option value="">Kategori secin</option>' +
    sortedCategories().map(item => `<option value="${escapeHtml(item.key)}">${escapeHtml(item.label)}</option>`).join('');
  el('feedback-category').value = selectedValue || '';
  updateCategoryGuidance();
}

function renderTagOptions() {
  const checkedValues = selectedTagKeys();
  el('feedback-tags').innerHTML = state.catalog.tags.map(item => `
    <label class="check-item">
      <input type="checkbox" value="${escapeHtml(item.key)}">
      <span class="check-copy"><strong>${escapeHtml(item.label)}</strong><span>${escapeHtml(item.description)}</span></span>
    </label>`).join('');
  if (checkedValues.length) setCheckedTags(checkedValues);
  updateCategoryGuidance();
}

function renderImportOptions(items) {
  const select = el('import-select');
  const selected = state.importFile;
  select.innerHTML = '<option value="">New Test</option>' + items.map(item => `
    <option value="${escapeHtml(item.filename)}">${escapeHtml(item.filename)}</option>`).join('');
  select.value = selected || '';
}

function renderRoleMappingPanel(response) {
  const panel = el('role-mapping-panel');
  const fields = el('role-mapping-fields');
  if (!response || response.status !== 'role_mapping_required') {
    panel.classList.add('hidden');
    fields.innerHTML = '';
    return;
  }

  panel.classList.remove('hidden');
  el('role-mapping-note').textContent = 'JSON icindeki roller net degil. Eslesmeyi tamamlayin ve importu onaylayin.';
  fields.innerHTML = (response.participants || []).map(item => `
    <div class="field-stack">
      <label>${escapeHtml(item.label || item.phone)}</label>
      <select class="debug-select role-mapping-select" data-phone="${escapeHtml(item.phone)}">
        <option value="user" ${item.suggested_role === 'user' ? 'selected' : ''}>Musteri</option>
        <option value="assistant" ${item.suggested_role === 'assistant' ? 'selected' : ''}>Asistan</option>
        <option value="system" ${item.suggested_role === 'system' ? 'selected' : ''}>Sistem</option>
        <option value="other" ${item.suggested_role === 'other' ? 'selected' : ''}>Diger</option>
      </select>
    </div>`).join('');
}

function currentRoleMapping() {
  const mapping = {};
  document.querySelectorAll('.role-mapping-select').forEach(select => {
    mapping[select.dataset.phone] = select.value;
  });
  return mapping;
}

function setComposerMode(isLive) {
  el('msg-input').disabled = !isLive;
  el('send-btn').disabled = !isLive;
  el('export-btn').disabled = !isLive;
  el('msg-input').placeholder = isLive
    ? 'Mesajinizi yazin...'
    : 'Import gorunumu salt okunur. Yeni mesaj icin New Test secin.';
  const sourceLabel = isLive
    ? 'Canli test gorunumu aktif.'
    : `Import gorunumu aktif: ${state.importFile || '-'}`;
  el('source-banner').textContent = sourceLabel;
}

function updateDebug(message = null) {
  const internal = message?.internal_json || {};
  const conversation = state.conversation || {};
  el('d-state').innerHTML = `<span class="debug-badge badge-state">${escapeHtml(conversation.state || internal.state || '-')}</span>`;
  el('d-intent').innerHTML = `<span class="debug-badge badge-intent">${escapeHtml(conversation.intent || internal.intent || '-')}</span>`;
  el('d-lang').innerHTML = `<span class="debug-badge badge-lang">${escapeHtml(conversation.language || state.importMetadata.language || internal.language || '-')}</span>`;

  const flags = [...new Set([...(conversation.risk_flags || []), ...(internal.risk_flags || []), ...(state.importMetadata.risk_flags || [])])];
  el('d-flags').innerHTML = flags.length
    ? flags.map(flag => `<span class="flag flag-${flagLevel(flag)}">${escapeHtml(flag)}</span>`).join('')
    : '<span class="feedback-muted">Flag yok</span>';
  el('d-next').textContent = internal.next_step || '-';
  el('d-full').textContent = JSON.stringify(internal || {}, null, 2);
}

function refreshDebugFromLatestAssistant() {
  const latestAssistant = [...state.messages].reverse().find(message => message.role === 'assistant') || null;
  updateDebug(latestAssistant);
}

async function loadHistory() {
  if (state.sourceType !== 'live_test_chat') return;
  const phone = encodeURIComponent(el('phone-input').value.trim() || 'test_user_123');
  const data = await apiFetch(`/chat/history?phone=${phone}`);
  state.messages = data.messages || [];
  state.conversation = data.conversation || null;
  renderMessages();
  refreshDebugFromLatestAssistant();
}

async function sendMessage() {
  if (state.sourceType !== 'live_test_chat') return;
  const message = el('msg-input').value.trim();
  if (!message) return;

  showTyping();
  try {
    const payload = {message: message, phone: el('phone-input').value.trim() || 'test_user_123'};
    const data = await apiFetch('/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload),
    });
    state.messages.push(
      {
        id: `user_${Date.now()}`,
        role: 'user',
        content: message,
        created_at: data.timestamp,
        internal_json: null,
      },
      {
        id: data.assistant_message_id,
        role: 'assistant',
        content: data.reply,
        created_at: data.timestamp,
        internal_json: data.internal_json,
        model: el('model-select').value || '',
      },
    );
    state.conversation = data.conversation || null;
    el('msg-input').value = '';
    renderMessages();
    updateDebug(state.messages[state.messages.length - 1]);
  } catch (error) {
    el('source-banner').textContent = error.message || 'Mesaj gonderilemedi.';
  } finally {
    hideTyping();
  }
}

async function resetConversation() {
  if (state.sourceType !== 'live_test_chat') {
    el('import-select').value = '';
    state.importFile = '';
    state.sourceType = 'live_test_chat';
    state.importMetadata = {};
    state.roleMapping = {};
    setComposerMode(true);
    renderRoleMappingPanel(null);
    await loadHistory();
    return;
  }

  const phone = encodeURIComponent(el('phone-input').value.trim() || 'test_user_123');
  await apiFetch(`/chat/reset?phone=${phone}`, {method: 'POST'});
  state.messages = [];
  state.conversation = null;
  state.feedbackStates.clear();
  state.selectedFeedback = null;
  renderMessages();
  renderFeedbackStudio();
  updateDebug(null);
}

async function downloadConversation() {
  if (state.sourceType !== 'live_test_chat') return;
  const phone = encodeURIComponent(el('phone-input').value.trim() || 'test_user_123');
  const format = encodeURIComponent(el('save-format').value);
  window.location.href = `${API}/chat/export?phone=${phone}&format=${format}`;
}

async function refreshImportFiles() {
  const data = await apiFetch('/chat/import-files');
  renderImportOptions(data.items || []);
}

async function loadSelectedImport(roleMapping = {}) {
  const filename = el('import-select').value;
  if (!filename) {
    state.sourceType = 'live_test_chat';
    state.importFile = '';
    state.importMetadata = {};
    state.roleMapping = {};
    setComposerMode(true);
    renderRoleMappingPanel(null);
    await loadHistory();
    return;
  }

  const data = await apiFetch('/chat/import-load', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({filename: filename, role_mapping: roleMapping}),
  });
  state.sourceType = data.source_type;
  state.importFile = data.file_name;
  state.importMetadata = {...(data.metadata || {}), conversation_id: data.conversation_id, source_label: data.source_label};
  state.roleMapping = roleMapping;

  if (data.status === 'role_mapping_required') {
    state.messages = [];
    renderMessages();
    renderRoleMappingPanel(data);
    setComposerMode(false);
    updateDebug(null);
    return;
  }

  renderRoleMappingPanel(null);
  state.messages = data.messages || [];
  state.conversation = {
    id: data.conversation_id || data.file_name,
    language: data.metadata?.language || '-',
    state: data.metadata?.state || '-',
    intent: data.metadata?.intent || '-',
    risk_flags: data.metadata?.risk_flags || [],
  };
  setComposerMode(false);
  renderMessages();
  refreshDebugFromLatestAssistant();
}

function selectFeedback(messageId, rating) {
  state.selectedFeedback = {messageId: String(messageId), rating: rating};
  state.manualTagTouched = false;
  const defaultApproved = el('feedback-approved-example');
  defaultApproved.checked = true;
  el('feedback-gold-standard').value = '';
  el('feedback-notes').value = '';
  el('feedback-custom-tags').value = '';
  el('feedback-category').value = '';
  el('feedback-custom-category').value = '';
  document.querySelectorAll('#feedback-tags input[type=checkbox]').forEach(input => { input.checked = false; });
  renderMessages();
  renderFeedbackStudio();
}

async function submitFeedback() {
  if (!state.selectedFeedback) return;
  const category = el('feedback-category').value || null;
  const customCategory = (el('feedback-custom-category').value || '').trim() || null;
  const tags = Array.from(document.querySelectorAll('#feedback-tags input[type=checkbox]:checked')).map(input => input.value);
  const customTags = (el('feedback-custom-tags').value || '')
    .split(',')
    .map(item => item.trim())
    .filter(Boolean);
  const goldStandard = (el('feedback-gold-standard').value || '').trim() || null;
  const notes = (el('feedback-notes').value || '').trim() || null;
  const approvedExample = state.selectedFeedback.rating === 5 ? el('feedback-approved-example').checked : false;

  try {
    const payload = {
      source_type: state.sourceType,
      phone: el('phone-input').value.trim() || 'test_user_123',
      assistant_message_id: state.selectedFeedback.messageId,
      rating: state.selectedFeedback.rating,
      category: category,
      custom_category: customCategory,
      tags: tags,
      custom_tags: customTags,
      gold_standard: goldStandard,
      notes: notes,
      approved_example: approvedExample,
      import_file: state.importFile || null,
      role_mapping: state.roleMapping,
    };
    const data = await apiFetch('/chat/feedback', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload),
    });
    state.feedbackStates.set(state.selectedFeedback.messageId, {
      rating: data.rating,
      status: data.approved_example ? 'Onayli ornek olarak kaydedildi' : 'Geri bildirim kaydedildi',
    });
    renderMessages();
    el('feedback-result').classList.remove('hidden');
    el('feedback-result').textContent = `Kayit: ${data.storage_path}`;
  } catch (error) {
    el('feedback-result').classList.remove('hidden');
    el('feedback-result').textContent = error.message || 'Geri bildirim kaydedilemedi.';
  }
}

async function generateReport() {
  const fromValue = el('report-date-from').value;
  const toValue = el('report-date-to').value;
  const payload = {
    date_from: fromValue ? new Date(fromValue).toISOString() : state.catalog.default_report_start,
    date_to: toValue ? new Date(toValue).toISOString() : state.catalog.default_report_end,
  };
  try {
    const data = await apiFetch('/chat/report', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload),
    });
    if (data.status === 'no_feedback') {
      el('report-result').textContent = data.summary;
      return;
    }
    const items = (data.recommendations || []).map(item => `
      <div class="list-item">
        <strong>${escapeHtml(item.target_file)}</strong>
        <span>${escapeHtml(item.reason)}</span>
        <span>Risk: ${escapeHtml(item.risk)}</span>
        <span>Test: ${escapeHtml(item.test_suggestion)}</span>
      </div>`).join('');
    el('report-result').innerHTML = `
      <div class="list-item">
        <strong>${escapeHtml(data.selected_model || '-')} | ${escapeHtml(data.report_path || '-')}</strong>
        <span>${escapeHtml(data.summary || '-')}</span>
      </div>${items}`;
  } catch (error) {
    el('report-result').textContent = error.message || 'Rapor olusturulamadi.';
  }
}

async function loadCatalog() {
  try {
    const data = await apiFetch('/chat/feedback-catalog');
    state.catalog = {
      ...data,
      scales: Array.isArray(data.scales) && data.scales.length ? data.scales : DEFAULT_FEEDBACK_SCALES,
      categories: Array.isArray(data.categories) && data.categories.length ? data.categories : DEFAULT_FEEDBACK_CATEGORIES,
      tags: Array.isArray(data.tags) && data.tags.length ? data.tags : DEFAULT_FEEDBACK_TAGS,
    };
    el('report-date-from').value = isoToLocalInput(data.default_report_start);
    el('report-date-to').value = isoToLocalInput(data.default_report_end);
  } catch (error) {
    state.catalog = {
      ...state.catalog,
      scales: DEFAULT_FEEDBACK_SCALES,
      categories: DEFAULT_FEEDBACK_CATEGORIES,
      tags: DEFAULT_FEEDBACK_TAGS,
    };
    el('source-banner').textContent = error.message || 'Feedback katalogu alinamadi; varsayilan puanlar kullaniliyor.';
  }
  renderCategoryOptions();
  renderTagOptions();
  renderMessages();
  renderFeedbackStudio();
}

async function loadModels() {
  const data = await apiFetch('/models');
  el('model-select').innerHTML = (data.models || []).map(model => `
    <option value="${escapeHtml(model)}">${escapeHtml(model)}</option>`).join('');
  if (data.current) el('model-select').value = data.current;
}

async function changeModel() {
  const model = el('model-select').value;
  await apiFetch('/model', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({model: model}),
  });
}

function isoToLocalInput(value) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  const pad = part => String(part).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function toggleDebug() {
  el('debug-panel').classList.toggle('collapsed');
}

function wireEvents() {
  el('send-btn').addEventListener('click', sendMessage);
  el('msg-input').addEventListener('keydown', event => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  });
  el('reset-btn').addEventListener('click', resetConversation);
  el('export-btn').addEventListener('click', downloadConversation);
  el('refresh-imports').addEventListener('click', refreshImportFiles);
  el('import-select').addEventListener('change', () => loadSelectedImport());
  el('role-mapping-submit').addEventListener('click', () => loadSelectedImport(currentRoleMapping()));
  el('feedback-category').addEventListener('change', () => {
    if (!state.manualTagTouched) applyCategorySuggestions(true);
    renderFeedbackStudio();
  });
  el('feedback-tags').addEventListener('change', () => {
    state.manualTagTouched = true;
    updateCategoryGuidance();
  });
  el('apply-tag-suggestions').addEventListener('click', () => applyCategorySuggestions(true));
  el('feedback-submit').addEventListener('click', submitFeedback);
  el('report-submit').addEventListener('click', generateReport);
  el('model-select').addEventListener('change', changeModel);
  el('phone-input').addEventListener('change', () => {
    if (state.sourceType === 'live_test_chat') loadHistory();
  });
  el('toggle-debug').addEventListener('click', toggleDebug);
}

async function boot() {
  wireEvents();
  renderCategoryOptions();
  renderTagOptions();
  await Promise.all([loadCatalog(), loadModels(), refreshImportFiles()]);
  setComposerMode(true);
  await loadHistory();
}

window.addEventListener('load', boot);
"""
