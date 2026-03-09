"""Test chat endpoints and web UI — disabled in production."""

from datetime import UTC, datetime
from typing import Annotated, Any

import structlog
from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from velox.adapters.whatsapp.formatter import WhatsAppFormatter
from velox.api.routes.test_chat_export import (
    ConversationExportPayload,
    ExportFormat,
    build_export_file_content,
    build_export_filename,
)

# Cross-module imports for reusing core pipeline logic (no WhatsApp API calls).
from velox.api.routes.whatsapp_webhook import (
    _hash_phone,
    _mask_phone,
    _normalize_text,
    _run_message_pipeline,
)
from velox.config.settings import settings
from velox.db.repositories.conversation import ConversationRepository
from velox.llm.client import get_llm_client
from velox.models.conversation import Conversation, Message

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/test", tags=["test-chat"])
ui_router = APIRouter(tags=["test-chat-ui"])
formatter = WhatsAppFormatter()

TEST_PHONE_PREFIX = "test_"


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class TestChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4096)
    phone: str = Field(default="test_user_123")


class TestChatResponse(BaseModel):
    reply: str
    internal_json: dict
    conversation: dict
    timestamp: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ensure_test_phone(phone: str) -> str:
    if phone.startswith(TEST_PHONE_PREFIX):
        return phone
    return f"{TEST_PHONE_PREFIX}{phone}"


def _serialize_message(message: Message) -> dict[str, Any]:
    return {
        "id": str(message.id),
        "role": message.role,
        "content": message.content,
        "internal_json": message.internal_json,
        "created_at": message.created_at.isoformat(),
    }


def _conversation_state_value(conversation: Conversation) -> str:
    if hasattr(conversation.current_state, "value"):
        return str(conversation.current_state.value)
    return str(conversation.current_state)


def _conversation_intent_value(conversation: Conversation) -> str | None:
    if conversation.current_intent is None:
        return None
    if hasattr(conversation.current_intent, "value"):
        return str(conversation.current_intent.value)
    return str(conversation.current_intent)


def _serialize_conversation(conversation: Conversation) -> dict[str, Any]:
    return {
        "id": str(conversation.id),
        "state": _conversation_state_value(conversation),
        "intent": _conversation_intent_value(conversation),
        "language": conversation.language,
        "entities": conversation.entities_json,
        "risk_flags": conversation.risk_flags,
        "is_active": conversation.is_active,
    }


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=TestChatResponse)
async def test_chat(body: TestChatRequest, request: Request) -> TestChatResponse:
    """Process a test message synchronously and return the bot reply."""
    phone = _ensure_test_phone(body.phone)
    db_pool = getattr(request.app.state, "db_pool", None)
    if db_pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    repo = ConversationRepository()
    phone_hash = _hash_phone(phone)

    conversation = await repo.get_active_by_phone(settings.elektra_hotel_id, phone_hash)
    if conversation is None:
        conversation = Conversation(
            hotel_id=settings.elektra_hotel_id,
            phone_hash=phone_hash,
            phone_display=_mask_phone(phone),
            language="tr",
        )
        conversation = await repo.create(conversation)

    normalized = _normalize_text(body.message)

    user_msg = Message(conversation_id=conversation.id, role="user", content=normalized)
    await repo.add_message(user_msg)
    conversation.messages.append(user_msg)

    recent = await repo.get_recent_messages(conversation.id, count=20)
    conversation.messages = recent

    llm_response = await _run_message_pipeline(
        conversation=conversation,
        normalized_text=normalized,
        dispatcher=getattr(request.app.state, "tool_dispatcher", None),
    )
    reply_text = formatter.truncate(llm_response.user_message)

    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=reply_text,
        internal_json=llm_response.internal_json.model_dump(mode="json"),
    )
    await repo.add_message(assistant_msg)

    return TestChatResponse(
        reply=reply_text,
        internal_json=llm_response.internal_json.model_dump(mode="json"),
        conversation=_serialize_conversation(conversation),
        timestamp=datetime.now().isoformat(),
    )


@router.get("/chat/history")
async def test_chat_history(request: Request, phone: str = "test_user_123") -> dict:
    """Load conversation history for a test phone number."""
    phone = _ensure_test_phone(phone)
    db_pool = getattr(request.app.state, "db_pool", None)
    if db_pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    repo = ConversationRepository()
    phone_hash = _hash_phone(phone)
    conversation = await repo.get_active_by_phone(settings.elektra_hotel_id, phone_hash)

    if conversation is None:
        return {"messages": [], "conversation": None}

    messages = await repo.get_messages(conversation.id, limit=100, offset=0)
    return {
        "messages": [_serialize_message(message) for message in messages],
        "conversation": _serialize_conversation(conversation),
    }


@router.post("/chat/reset")
async def test_chat_reset(request: Request, phone: str = "test_user_123") -> dict:
    """Close the active conversation for a test phone so the next message starts fresh."""
    phone = _ensure_test_phone(phone)
    db_pool = getattr(request.app.state, "db_pool", None)
    if db_pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    repo = ConversationRepository()
    phone_hash = _hash_phone(phone)
    conversation = await repo.get_active_by_phone(settings.elektra_hotel_id, phone_hash)

    if conversation is None:
        return {"status": "no_active_conversation"}

    await repo.close(conversation.id)
    return {"status": "reset", "closed_conversation_id": str(conversation.id)}


@router.get("/chat/export")
async def test_chat_export(
    request: Request,
    phone: str = "test_user_123",
    export_format: Annotated[ExportFormat, Query(alias="format")] = "md",
) -> Response:
    """Export active test conversation as json/pdf/md/txt."""
    phone = _ensure_test_phone(phone)
    db_pool = getattr(request.app.state, "db_pool", None)
    if db_pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    repository = ConversationRepository()
    phone_hash = _hash_phone(phone)
    conversation = await repository.get_active_by_phone(settings.elektra_hotel_id, phone_hash)
    if conversation is None:
        raise HTTPException(status_code=404, detail="No active conversation for this phone")

    messages = await repository.get_messages(conversation.id, limit=500, offset=0)
    exported_at = datetime.now(UTC)
    payload = ConversationExportPayload(
        phone=phone,
        conversation=_serialize_conversation(conversation),
        messages=[_serialize_message(message) for message in messages],
        exported_at=exported_at,
    )
    content, media_type, extension = build_export_file_content(export_format, payload)
    filename = build_export_filename(phone=phone, extension=extension, exported_at=exported_at)
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=content, media_type=media_type, headers=headers)


# ---------------------------------------------------------------------------
# Model management
# ---------------------------------------------------------------------------

class SetModelRequest(BaseModel):
    model: str = Field(min_length=1)


@router.get("/models")
async def list_models() -> dict:
    """List available OpenAI GPT models and the currently active one."""
    client = get_llm_client()
    try:
        models_page = await client.client.models.list()
        gpt_models = sorted(
            [m.id for m in models_page.data if "gpt" in m.id],
            reverse=True,
        )
    except Exception:
        gpt_models = []
    return {"models": gpt_models, "current": client.primary_model}


@router.post("/model")
async def set_model(body: SetModelRequest) -> dict:
    """Change the active LLM model at runtime (test only)."""
    client = get_llm_client()
    client.primary_model = body.model
    return {"status": "ok", "model": body.model}


# ---------------------------------------------------------------------------
# HTML Chat UI
# ---------------------------------------------------------------------------

TEST_CHAT_HTML = """\
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Velox Test Chat</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --navy:#1a1a2e;--navy-light:#16213e;--teal:#0d7377;--teal-light:#14a3a8;
  --gold:#e2b340;--bg:#f4f5f7;--white:#fff;--gray-100:#f0f0f3;
  --gray-200:#e2e4e8;--gray-400:#9ca3af;--gray-600:#4b5563;--gray-800:#1f2937;
  --red:#ef4444;--orange:#f59e0b;--yellow:#fbbf24;--green:#22c55e;
  --radius:12px;--shadow:0 2px 12px rgba(0,0,0,.08);
}
html,body{height:100%;font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--gray-800)}
/* ---- LAYOUT ---- */
.app{display:flex;flex-direction:column;height:100vh}
.header{background:linear-gradient(135deg,var(--navy),var(--navy-light));color:var(--white);padding:14px 24px;display:flex;align-items:center;gap:16px;flex-shrink:0;box-shadow:0 2px 8px rgba(0,0,0,.2)}
.header h1{font-size:18px;font-weight:600;letter-spacing:.5px}
.header .subtitle{font-size:12px;color:var(--gray-400);margin-left:-8px}
.header-controls{display:flex;align-items:center;gap:10px;margin-left:auto}
.header-controls label{font-size:12px;color:var(--gray-400)}
.header-controls input[type=text]{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.15);border-radius:6px;color:var(--white);padding:6px 10px;font-size:13px;width:140px;outline:none;transition:border .2s}
.header-controls input[type=text]:focus{border-color:var(--teal-light)}
.btn{border:none;border-radius:8px;padding:8px 16px;font-size:13px;font-weight:500;cursor:pointer;transition:all .15s}
.btn-reset{background:var(--red);color:var(--white)}
.btn-reset:hover{background:#dc2626}
.btn-save{background:var(--gold);color:var(--navy)}
.btn-save:hover{background:#d1a238}
.btn-toggle{background:rgba(255,255,255,.12);color:var(--white);display:none}
.btn-toggle:hover{background:rgba(255,255,255,.2)}

.main{display:flex;flex:1;min-height:0}

/* ---- CHAT PANEL ---- */
.chat-panel{flex:1;display:flex;flex-direction:column;min-width:0}
.messages{flex:1;overflow-y:auto;padding:20px 24px;display:flex;flex-direction:column;gap:8px}
.messages::-webkit-scrollbar{width:6px}
.messages::-webkit-scrollbar-thumb{background:var(--gray-200);border-radius:3px}

.msg{max-width:75%;padding:10px 14px;border-radius:var(--radius);font-size:14px;line-height:1.55;word-wrap:break-word;position:relative;animation:fadeIn .25s ease}
@keyframes fadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.msg-user{align-self:flex-end;background:var(--teal);color:var(--white);border-bottom-right-radius:4px}
.msg-assistant{align-self:flex-start;background:var(--white);color:var(--gray-800);border:1px solid var(--gray-200);border-bottom-left-radius:4px;box-shadow:var(--shadow)}
.msg-system{align-self:center;background:var(--gray-100);color:var(--gray-600);font-size:12px;border-radius:20px;padding:6px 14px}
.msg-time{font-size:10px;margin-top:4px;opacity:.6}
.msg-user .msg-time{text-align:right}

/* typing indicator */
.typing{align-self:flex-start;display:flex;align-items:center;gap:4px;padding:12px 16px;background:var(--white);border:1px solid var(--gray-200);border-radius:var(--radius);box-shadow:var(--shadow)}
.typing span{width:7px;height:7px;background:var(--gray-400);border-radius:50%;animation:bounce .6s infinite alternate}
.typing span:nth-child(2){animation-delay:.2s}
.typing span:nth-child(3){animation-delay:.4s}
@keyframes bounce{to{opacity:.3;transform:translateY(-4px)}}

/* input bar */
.input-bar{display:flex;align-items:flex-end;gap:10px;padding:14px 20px;background:var(--white);border-top:1px solid var(--gray-200)}
.input-bar textarea{flex:1;resize:none;border:1px solid var(--gray-200);border-radius:var(--radius);padding:10px 14px;font-size:14px;font-family:inherit;line-height:1.4;max-height:120px;outline:none;transition:border .2s}
.input-bar textarea:focus{border-color:var(--teal)}
.btn-send{background:var(--teal);color:var(--white);border-radius:50%;width:42px;height:42px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.btn-send:hover{background:var(--teal-light)}
.btn-send svg{width:20px;height:20px;fill:var(--white)}

/* ---- DEBUG PANEL ---- */
.debug-panel{width:380px;background:var(--navy);color:var(--white);display:flex;flex-direction:column;flex-shrink:0;border-left:1px solid rgba(255,255,255,.06);overflow:hidden;transition:width .3s}
.debug-panel.collapsed{width:0;border:none}
.debug-header{padding:14px 18px;font-size:14px;font-weight:600;color:var(--gold);border-bottom:1px solid rgba(255,255,255,.08);display:flex;align-items:center;gap:8px;flex-shrink:0}
.debug-header svg{width:16px;height:16px;fill:var(--gold)}
.debug-body{flex:1;overflow-y:auto;padding:14px 18px;display:flex;flex-direction:column;gap:12px}
.debug-body::-webkit-scrollbar{width:5px}
.debug-body::-webkit-scrollbar-thumb{background:rgba(255,255,255,.15);border-radius:3px}

.debug-section{background:rgba(255,255,255,.05);border-radius:8px;padding:10px 12px}
.debug-section h3{font-size:11px;text-transform:uppercase;letter-spacing:.8px;color:var(--gray-400);margin-bottom:6px}
.debug-value{font-size:13px;font-family:'Cascadia Code','Fira Code',monospace;color:var(--gray-100);word-break:break-all}
.debug-badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600}
.badge-state{background:var(--teal);color:var(--white)}
.badge-intent{background:var(--gold);color:var(--navy)}
.badge-lang{background:rgba(255,255,255,.15);color:var(--white)}

.debug-flags{display:flex;flex-wrap:wrap;gap:4px}
.flag{padding:2px 7px;border-radius:4px;font-size:11px;font-weight:500}
.flag-l3{background:var(--red);color:var(--white)}
.flag-l2{background:var(--orange);color:var(--navy)}
.flag-l1{background:var(--yellow);color:var(--navy)}
.flag-l0{background:var(--gray-400);color:var(--white)}

.debug-json{background:rgba(0,0,0,.2);border-radius:6px;padding:8px 10px;font-size:12px;font-family:'Cascadia Code','Fira Code',monospace;color:#93c5fd;max-height:200px;overflow-y:auto;white-space:pre-wrap;word-break:break-all}

.empty-state{text-align:center;color:var(--gray-400);padding:60px 20px}
.empty-state svg{width:48px;height:48px;fill:var(--gray-200);margin-bottom:12px}
.empty-state p{font-size:14px}

/* ---- RESPONSIVE ---- */
@media(max-width:768px){
  .debug-panel{position:fixed;right:0;top:0;bottom:0;z-index:100;width:320px}
  .debug-panel.collapsed{width:0}
  .btn-toggle{display:flex;align-items:center;gap:4px}
  .msg{max-width:88%}
}
</style>
</head>
<body>
<div class="app">
  <div class="header">
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#e2b340" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
    <div>
      <h1>Velox Test Chat</h1>
      <div class="subtitle">WhatsApp Simulator &mdash; Development Mode</div>
    </div>
    <div class="header-controls">
      <label>Model</label>
      <select id="model-select" onchange="changeModel(this.value)" style="background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.15);border-radius:6px;color:#fff;padding:6px 8px;font-size:12px;min-width:160px;outline:none;cursor:pointer">
        <option>Loading...</option>
      </select>
      <label>Phone</label>
      <input type="text" id="phone-input" value="test_user_123">
      <button class="btn btn-reset" onclick="resetConversation()">Reset</button>
      <label>Save</label>
      <select id="save-format" style="background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.15);border-radius:6px;color:#fff;padding:6px 8px;font-size:12px;outline:none;cursor:pointer">
        <option value="md">.md</option>
        <option value="txt">.txt</option>
        <option value="json">.json</option>
        <option value="pdf">.pdf</option>
      </select>
      <button class="btn btn-save" onclick="downloadConversation()">Farkli Kaydet</button>
      <button class="btn btn-toggle" id="toggle-debug" onclick="toggleDebug()">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M20 4H4a2 2 0 00-2 2v12a2 2 0 002 2h16a2 2 0 002-2V6a2 2 0 00-2-2zm0 14H4V6h16v12z"/></svg>
        Debug
      </button>
    </div>
  </div>

  <div class="main">
    <div class="chat-panel">
      <div class="messages" id="messages">
        <div class="empty-state" id="empty-state">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/></svg>
          <p>Mesaj gondererek test konusmasini baslatin.</p>
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
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z"/></svg>
        Debug Panel
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
          <div class="debug-flags" id="d-flags"><span style="color:var(--gray-400);font-size:12px">No flags</span></div>
        </div>
        <div class="debug-section">
          <h3>Escalation</h3>
          <div class="debug-value" id="d-escalation" style="font-size:12px;color:var(--gray-400)">-</div>
        </div>
        <div class="debug-section">
          <h3>Entities</h3>
          <div class="debug-json" id="d-entities">{}</div>
        </div>
        <div class="debug-section">
          <h3>Next Step</h3>
          <div class="debug-value" id="d-next" style="font-size:12px;color:var(--gray-400)">-</div>
        </div>
        <div class="debug-section">
          <h3>Full Internal JSON</h3>
          <div class="debug-json" id="d-full">{}</div>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
const API = '/api/v1/test';
const messagesEl = document.getElementById('messages');
const inputEl = document.getElementById('msg-input');
const emptyState = document.getElementById('empty-state');
const debugPanel = document.getElementById('debug-panel');

const L3_FLAGS = ['LEGAL_REQUEST','SECURITY_INCIDENT','THREAT_SELF_HARM','MEDICAL_EMERGENCY'];
const L2_FLAGS = ['PAYMENT_CONFUSION','CHARGEBACK','REFUND_DISPUTE','ANGRY_COMPLAINT','FRAUD_SIGNAL','GROUP_BOOKING','CONTRACT_QUESTION','REPEAT_COMPLAINT','SOCIAL_MEDIA_THREAT','PRICE_MATCH','SYSTEM_ERROR','DOUBLE_CHARGE'];
const L1_FLAGS = ['VIP_REQUEST','ALLERGY_ALERT','ACCESSIBILITY_NEED','CHILD_SAFETY','CAPACITY_LIMIT','WEATHER_ALERT','SPECIAL_EVENT_FLAG','DIETARY_RESTRICTION'];

function flagLevel(f) {
  if (L3_FLAGS.includes(f)) return 'l3';
  if (L2_FLAGS.includes(f)) return 'l2';
  if (L1_FLAGS.includes(f)) return 'l1';
  return 'l0';
}

function fmtTime(iso) {
  try { return new Date(iso).toLocaleTimeString('tr-TR', {hour:'2-digit',minute:'2-digit'}); }
  catch { return ''; }
}

function addBubble(role, text, time) {
  if (emptyState) emptyState.style.display = 'none';
  const div = document.createElement('div');
  div.className = 'msg msg-' + role;
  div.innerHTML = text.replace(/\\n/g,'<br>') +
    (time ? '<div class="msg-time">' + fmtTime(time) + '</div>' : '');
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
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

function updateDebug(ij, conv) {
  if (!ij) return;
  document.getElementById('d-state').innerHTML =
    '<span class="debug-badge badge-state">' + (conv?.state || ij.state || '-') + '</span>';
  document.getElementById('d-intent').innerHTML =
    '<span class="debug-badge badge-intent">' + (ij.intent || '-') + '</span>';
  document.getElementById('d-lang').innerHTML =
    '<span class="debug-badge badge-lang">' + (ij.language || '-') + '</span>';

  const flagsEl = document.getElementById('d-flags');
  const allFlags = [...(ij.risk_flags||[]), ...(conv?.risk_flags||[])];
  const unique = [...new Set(allFlags)];
  if (unique.length === 0) {
    flagsEl.innerHTML = '<span style="color:var(--gray-400);font-size:12px">No flags</span>';
  } else {
    flagsEl.innerHTML = unique.map(f => '<span class="flag flag-' + flagLevel(f) + '">' + f + '</span>').join('');
  }

  const esc = ij.escalation || {};
  document.getElementById('d-escalation').textContent =
    'Level: ' + (esc.level||'L0') + '  |  Role: ' + (esc.route_to_role||'NONE');
  document.getElementById('d-entities').textContent = JSON.stringify(ij.entities||{}, null, 2);
  document.getElementById('d-next').textContent = ij.next_step || '-';
  document.getElementById('d-full').textContent = JSON.stringify(ij, null, 2);
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
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({message: text, phone: phone}),
    });
    hideTyping();
    if (!res.ok) {
      const err = await res.json().catch(() => ({detail:'Unknown error'}));
      addBubble('system', 'Error ' + res.status + ': ' + (err.detail||JSON.stringify(err)));
      return;
    }
    const data = await res.json();
    addBubble('assistant', data.reply, data.timestamp);
    updateDebug(data.internal_json, data.conversation);
  } catch (e) {
    hideTyping();
    addBubble('system', 'Network error: ' + e.message);
  }
}

async function loadHistory() {
  const phone = document.getElementById('phone-input').value.trim() || 'test_user_123';
  try {
    const res = await fetch(API + '/chat/history?phone=' + encodeURIComponent(phone));
    if (!res.ok) return;
    const data = await res.json();
    if (data.messages && data.messages.length > 0) {
      // clear existing bubbles except empty state
      messagesEl.querySelectorAll('.msg').forEach(el => el.remove());
      data.messages.forEach(m => addBubble(m.role, m.content, m.created_at));
      // update debug with last assistant message's internal_json
      const lastAssistant = [...data.messages].reverse().find(m => m.role === 'assistant');
      if (lastAssistant && lastAssistant.internal_json) {
        updateDebug(lastAssistant.internal_json, data.conversation);
      }
    }
  } catch {}
}

async function resetConversation() {
  const phone = document.getElementById('phone-input').value.trim() || 'test_user_123';
  try {
    await fetch(API + '/chat/reset?phone=' + encodeURIComponent(phone), {method:'POST'});
  } catch {}
  // clear UI
  messagesEl.querySelectorAll('.msg,.typing').forEach(el => el.remove());
  if (emptyState) emptyState.style.display = '';
  // reset debug
  document.getElementById('d-state').innerHTML = '<span class="debug-badge badge-state">-</span>';
  document.getElementById('d-intent').innerHTML = '<span class="debug-badge badge-intent">-</span>';
  document.getElementById('d-lang').innerHTML = '<span class="debug-badge badge-lang">-</span>';
  document.getElementById('d-flags').innerHTML = '<span style="color:var(--gray-400);font-size:12px">No flags</span>';
  document.getElementById('d-escalation').textContent = '-';
  document.getElementById('d-entities').textContent = '{}';
  document.getElementById('d-next').textContent = '-';
  document.getElementById('d-full').textContent = '{}';
  addBubble('system', 'Konusma sifirlandi. Yeni bir mesaj gonderin.');
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

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

function autoResize() {
  inputEl.style.height = 'auto';
  inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + 'px';
}
inputEl.addEventListener('input', autoResize);

// --- Model selector ---
async function loadModels() {
  const sel = document.getElementById('model-select');
  try {
    const res = await fetch(API + '/models');
    if (!res.ok) return;
    const data = await res.json();
    sel.innerHTML = '';
    (data.models || []).forEach(m => {
      const opt = document.createElement('option');
      opt.value = m; opt.textContent = m;
      if (m === data.current) opt.selected = true;
      sel.appendChild(opt);
    });
    if (sel.options.length === 0) {
      sel.innerHTML = '<option>' + (data.current || 'unknown') + '</option>';
    }
  } catch {
    sel.innerHTML = '<option>error</option>';
  }
}

async function changeModel(model) {
  try {
    await fetch(API + '/model', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({model: model}),
    });
    addBubble('system', 'Model degistirildi: ' + model);
  } catch {}
}

// Load on startup
loadModels();
loadHistory();
</script>
</body>
</html>
"""


@ui_router.get("/test-chat", response_class=HTMLResponse)
async def test_chat_ui() -> HTMLResponse:
    """Serve the test chat web interface."""
    return HTMLResponse(content=TEST_CHAT_HTML)
