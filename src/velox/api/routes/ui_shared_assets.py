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
  if (payload && typeof payload.detail === 'object' && !Array.isArray(payload.detail)) {
    if (typeof payload.detail.message === 'string') {
      return payload.detail.message.trim();
    }
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

function findExplicitLabel(scope, nodeId) {
  var labels = Array.from((scope || document).querySelectorAll('label[for]'));
  return labels.find(function(label) {
    return label.getAttribute('for') === nodeId;
  }) || null;
}

function findLabelText(node, root) {
  if (!node) return '';
  var scope = root || document;
  var text = '';
  if (node.id) {
    var explicitLabel = findExplicitLabel(scope, node.id) || (scope !== document ? findExplicitLabel(document, node.id) : null);
    text = explicitLabel ? explicitLabel.textContent : '';
  }
  if (!text) {
    var wrappingLabel = node.closest('label');
    text = wrappingLabel ? wrappingLabel.textContent : '';
  }
  if (!text && node.tagName === 'BUTTON') {
    text = node.textContent || node.title || '';
  }
  if (!text) {
    text = node.getAttribute('placeholder') || node.getAttribute('name') || '';
  }
  return String(text || '').replace(/\\s+/g, ' ').trim();
}

function ensureInteractiveLabels(root) {
  var scope = root || document;
  scope.querySelectorAll('button, input, select, textarea').forEach(function(node) {
    if (node.type === 'hidden') return;
    if (node.hasAttribute('aria-label') || node.hasAttribute('aria-labelledby')) return;
    var label = findLabelText(node, scope);
    if (label) {
      node.setAttribute('aria-label', label);
    }
  });
}

var _interactiveLabelObserverStarted = false;

function startInteractiveLabelObserver(root) {
  var scope = root || document.body;
  ensureInteractiveLabels(document);
  if (_interactiveLabelObserverStarted || typeof MutationObserver === 'undefined' || !scope) return;
  _interactiveLabelObserverStarted = true;
  var observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      mutation.addedNodes.forEach(function(node) {
        if (!(node instanceof Element)) return;
        ensureInteractiveLabels(node);
      });
    });
  });
  observer.observe(scope, {childList: true, subtree: true});
}
"""
