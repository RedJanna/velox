"""Shared JavaScript utilities used by both Admin Panel and Chat Lab UIs.

This module eliminates duplicate helper functions across admin_panel_ui_assets
and test_chat_ui_assets.  Both modules import UI_SHARED_SCRIPT and embed it
before their own page-specific script block.
"""

# ruff: noqa: E501

UI_SHARED_SCRIPT = """\
/* ── Velox Shared UI Utilities ───────────────────────────────── */

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function formatDate(value) {
  if (!value) return '-';
  try {
    return new Date(value).toLocaleString('tr-TR', {dateStyle: 'short', timeStyle: 'short'});
  } catch (_error) {
    return String(value);
  }
}

function formatTime(iso) {
  try {
    return new Date(iso).toLocaleTimeString('tr-TR', {hour: '2-digit', minute: '2-digit'});
  } catch (_error) {
    return '';
  }
}

function formatMessageHtml(text) {
  return escapeHtml(text).replace(/\\n/g, '<br>');
}

function defaultDate(offsetDays = 0) {
  const date = new Date();
  date.setDate(date.getDate() + offsetDays);
  return date.toISOString().slice(0, 10);
}

function formToJson(form) {
  return Object.fromEntries(new FormData(form).entries());
}

function readCookie(name) {
  const encoded = name + '=';
  return document.cookie.split(';').map(function(item) { return item.trim(); }).find(function(item) { return item.startsWith(encoded); })?.slice(encoded.length) || '';
}

function isSafeMethod(method) {
  return ['GET', 'HEAD', 'OPTIONS'].includes(String(method || 'GET').toUpperCase());
}

function asObject(value) {
  if (value && typeof value === 'object') return value;
  if (typeof value === 'string') {
    try {
      var parsed = JSON.parse(value);
      if (parsed && typeof parsed === 'object') return parsed;
    } catch (_error) {
      return {};
    }
  }
  return {};
}

function extractErrorDetail(payload, rawText) {
  if (typeof payload?.detail === 'string' && payload.detail.trim()) {
    return payload.detail.trim();
  }
  if (Array.isArray(payload?.detail) && payload.detail.length) {
    var messages = payload.detail.map(function(item) {
      if (typeof item === 'string') return item;
      if (item && typeof item.msg === 'string') {
        var location = Array.isArray(item.loc) ? item.loc.join(' > ') : 'field';
        return location + ': ' + item.msg;
      }
      return '';
    }).filter(Boolean);
    if (messages.length) return messages.join(' | ');
  }
  if (typeof payload?.message === 'string' && payload.message.trim()) {
    return payload.message.trim();
  }
  if (typeof rawText === 'string' && rawText.trim()) {
    return rawText.trim().slice(0, 400);
  }
  return 'Islem tamamlanamadi.';
}

function isoToLocalInput(value) {
  if (!value) return '';
  var date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  var pad = function(part) { return String(part).padStart(2, '0'); };
  return date.getFullYear() + '-' + pad(date.getMonth() + 1) + '-' + pad(date.getDate()) + 'T' + pad(date.getHours()) + ':' + pad(date.getMinutes());
}
"""
