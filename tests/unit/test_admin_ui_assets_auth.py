"""Regression checks for admin panel and Chat Lab inline scripts."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from velox.api.routes.admin_panel_holds_assets import ADMIN_HOLDS_SCRIPT
from velox.api.routes.admin_panel_restaurant_assets import ADMIN_RESTAURANT_SCRIPT
from velox.api.routes.admin_panel_ui import render_admin_panel_html
from velox.api.routes.admin_panel_ui_assets import ADMIN_PANEL_SCRIPT, ADMIN_PANEL_STYLE
from velox.api.routes.test_chat_ui import TEST_CHAT_HTML
from velox.api.routes.test_chat_ui_assets import TEST_CHAT_SCRIPT, TEST_CHAT_STYLE


def _run_admin_panel_script_harness(harness: str) -> dict[str, object]:
    node_path = shutil.which("node")
    assert node_path, "node is required for admin panel runtime harness checks"

    prelude = """
class HTMLElement {
  constructor() {
    this.value = '';
    this.innerHTML = '';
    this.hidden = false;
    this.dataset = {};
    this.className = '';
    this.textContent = '';
    this.checked = false;
    this.disabled = false;
    this.style = {};
    this.classList = { add() {}, remove() {}, contains() { return false; }, toggle() {} };
  }
  addEventListener() {}
  removeEventListener() {}
  setAttribute() {}
  getAttribute() { return ''; }
  hasAttribute() { return false; }
  closest() { return null; }
  querySelectorAll() { return []; }
  querySelector() { return null; }
  focus() {}
  blur() { globalThis.__blurCount = (globalThis.__blurCount || 0) + 1; }
  scrollIntoView() {}
}
class Element extends HTMLElement {}
globalThis.HTMLElement = HTMLElement;
globalThis.Element = Element;
globalThis.MutationObserver = undefined;

const __storage = new Map();
globalThis.window = {
  ADMIN_PANEL_CONFIG: {},
  localStorage: {
    getItem(key) { return __storage.has(key) ? __storage.get(key) : null; },
    setItem(key, value) { __storage.set(key, String(value)); },
    removeItem(key) { __storage.delete(key); },
  },
  location: { hash: '#hotels', href: 'https://test.local/admin#hotels', origin: 'https://test.local' },
  history: { replaceState() {} },
  matchMedia() { return { matches: false }; },
  addEventListener() {},
  removeEventListener() {},
  setInterval,
  clearInterval,
  setTimeout,
  clearTimeout,
  requestAnimationFrame(callback) { return setTimeout(callback, 0); },
  confirm() { return true; },
  prompt() { return ''; },
};
window.parent = window;
globalThis.confirm = window.confirm;
globalThis.navigator = { userAgent: 'node-admin-harness' };
globalThis.document = {
  cookie: '',
  title: 'Admin',
  hidden: false,
  visibilityState: 'visible',
  body: new Element(),
  activeElement: new HTMLElement(),
  addEventListener() {},
  removeEventListener() {},
  getElementById() { return null; },
  querySelectorAll() { return []; },
  querySelector() { return null; },
};
globalThis.FormData = class FormData {
  constructor() {
    this._entries = [];
  }
  entries() {
    return this._entries[Symbol.iterator]();
  }
  get() {
    return null;
  }
};
globalThis.fetch = async () => ({ ok: true, status: 200, text: async () => '', json: async () => ({}) });
"""

    with tempfile.TemporaryDirectory() as tmp_dir:
        script_path = Path(tmp_dir) / "admin_harness.js"
        script_path.write_text(prelude + ADMIN_PANEL_SCRIPT + "\n" + harness, encoding="utf-8")
        result = subprocess.run(
            [node_path, str(script_path)],
            check=True,
            capture_output=True,
        )
    return json.loads(result.stdout.decode("utf-8").strip())


def _run_chat_lab_script_harness(harness: str) -> dict[str, object]:
    node_path = shutil.which("node")
    assert node_path, "node is required for Chat Lab runtime harness checks"

    prelude = """
class SimpleClassList {
  constructor(initial = []) {
    this._classes = new Set(initial.filter(Boolean));
  }
  add(...classes) { classes.filter(Boolean).forEach(item => this._classes.add(item)); }
  remove(...classes) { classes.filter(Boolean).forEach(item => this._classes.delete(item)); }
  contains(item) { return this._classes.has(item); }
  toggle(item, force) {
    if (force === undefined) {
      if (this._classes.has(item)) {
        this._classes.delete(item);
        return false;
      }
      this._classes.add(item);
      return true;
    }
    if (force) this._classes.add(item);
    else this._classes.delete(item);
    return Boolean(force);
  }
  toString() { return Array.from(this._classes).join(' '); }
}

class HTMLElement {
  constructor(id = '') {
    this.id = id;
    this.value = '';
    this.innerHTML = '';
    this.hidden = false;
    this.dataset = {};
    this.textContent = '';
    this.checked = false;
    this.disabled = false;
    this.style = {};
    this.attributes = {};
    this.children = [];
    this.classList = new SimpleClassList();
  }
  addEventListener() {}
  removeEventListener() {}
  setAttribute(name, value) { this.attributes[name] = String(value); }
  getAttribute(name) { return this.attributes[name] || ''; }
  hasAttribute(name) { return Object.prototype.hasOwnProperty.call(this.attributes, name); }
  closest(selector) {
    if (selector === '.hidden' && this.classList.contains('hidden')) return this;
    return null;
  }
  querySelectorAll(selector) {
    if (selector === 'button:not([disabled]),[href],input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex=\"-1\"])') {
      return this.children.filter(child => !child.disabled && !child.classList.contains('hidden'));
    }
    return [];
  }
  querySelector() { return null; }
  focus() { globalThis.document.activeElement = this; }
  blur() {}
  scrollIntoView() {}
  getClientRects() { return this.classList.contains('hidden') ? [] : [1]; }
}

class Element extends HTMLElement {}
globalThis.HTMLElement = HTMLElement;
globalThis.Element = Element;
globalThis.MutationObserver = undefined;

const __storage = new Map();
const __elements = {};
const __tabs = [];
globalThis.window = {
  parent: null,
  ADMIN_PANEL_CONFIG: {},
  localStorage: {
    getItem(key) { return __storage.has(key) ? __storage.get(key) : null; },
    setItem(key, value) { __storage.set(key, String(value)); },
    removeItem(key) { __storage.delete(key); },
  },
  location: { hash: '#chatlab', href: 'https://test.local/admin#chatlab', origin: 'https://test.local' },
  history: { replaceState() {} },
  matchMedia() { return { matches: false }; },
  addEventListener() {},
  removeEventListener() {},
  setInterval,
  clearInterval,
  setTimeout,
  clearTimeout,
  requestAnimationFrame(callback) { callback(); return 1; },
  confirm() { return true; },
  prompt() { return ''; },
};
window.parent = window;
globalThis.confirm = window.confirm;
globalThis.requestAnimationFrame = window.requestAnimationFrame;
globalThis.navigator = { userAgent: 'node-chat-harness' };
globalThis.document = {
  cookie: '',
  title: 'Chat Lab',
  hidden: false,
  visibilityState: 'visible',
  body: new Element('body'),
  activeElement: new HTMLElement('active'),
  addEventListener() {},
  removeEventListener() {},
  contains(node) { return Object.values(__elements).includes(node); },
  getElementById(id) { return __elements[id] || null; },
  querySelector(selector) {
    if (selector === '.app') return __elements.appShell || null;
    if (selector === '#workspace-flyout-tabs .workspace-flyout-tab.is-active') {
      return __tabs.find(tab => tab.classList.contains('is-active')) || null;
    }
    return null;
  },
  querySelectorAll(selector) {
    if (selector === '#workspace-flyout-tabs [data-workspace-tab]') return __tabs;
    return [];
  },
};
globalThis.FormData = class FormData {
  constructor() { this._entries = []; }
  entries() { return this._entries[Symbol.iterator](); }
  get() { return null; }
};
globalThis.fetch = async () => ({ ok: true, status: 200, text: async () => '', json: async () => ({}) });
globalThis.__elements = __elements;
globalThis.__tabs = __tabs;
"""

    with tempfile.TemporaryDirectory() as tmp_dir:
        script_path = Path(tmp_dir) / "chat_harness.js"
        script_path.write_text(prelude + TEST_CHAT_SCRIPT + "\n" + harness, encoding="utf-8")
        result = subprocess.run(
            [node_path, str(script_path)],
            check=True,
            capture_output=True,
        )
    return json.loads(result.stdout.decode("utf-8").strip())


def test_admin_panel_notifications_use_notify_helper() -> None:
    assert "toast(" not in ADMIN_PANEL_SCRIPT
    assert "notify(" in ADMIN_PANEL_SCRIPT


def test_stay_wizard_submit_button_is_not_rendered_disabled() -> None:
    assert 'data-stay-submit-action disabled' not in ADMIN_HOLDS_SCRIPT
    assert 'data-stay-submit-action>' in ADMIN_HOLDS_SCRIPT


def test_chat_lab_boot_no_longer_requires_parent_token() -> None:
    assert "window.parent !== window && !adminToken()) return;" not in TEST_CHAT_SCRIPT


def test_chat_lab_does_not_persist_admin_token_in_localstorage() -> None:
    assert "localStorage.setItem" not in TEST_CHAT_SCRIPT


def test_chat_lab_exposes_reply_action_in_context_menu() -> None:
    assert "Yanıtla" in TEST_CHAT_SCRIPT
    assert "setReplyTarget" in TEST_CHAT_SCRIPT


def test_chat_lab_renders_reply_preview_composer() -> None:
    assert 'id="reply-preview"' in TEST_CHAT_HTML
    assert 'id="reply-preview-clear"' in TEST_CHAT_HTML


def test_chat_lab_renders_workspace_flyout_shell() -> None:
    assert 'id="workspace-panel-toggle"' in TEST_CHAT_HTML
    assert 'id="workspace-diagnostics-toggle"' in TEST_CHAT_HTML
    assert 'class="workspace-utility-nav"' in TEST_CHAT_HTML
    assert 'id="workspace-scrim"' in TEST_CHAT_HTML
    assert 'id="workspace-flyout"' in TEST_CHAT_HTML
    assert 'id="workspace-flyout-sync"' in TEST_CHAT_HTML
    assert 'id="workspace-flyout-tabs"' in TEST_CHAT_HTML
    assert 'id="workspace-settings-panel"' in TEST_CHAT_HTML
    assert 'id="workspace-diagnostics-panel"' in TEST_CHAT_HTML
    assert 'id="workspace-source-summary"' in TEST_CHAT_HTML
    assert 'id="workspace-mode-summary"' in TEST_CHAT_HTML
    assert 'data-workspace-tab="settings"' in TEST_CHAT_HTML
    assert 'data-workspace-tab="diagnostics"' in TEST_CHAT_HTML


def test_chat_lab_workspace_flyout_uses_premium_console_layout() -> None:
    assert 'class="workspace-hero"' in TEST_CHAT_HTML
    assert 'class="workspace-overview-grid"' in TEST_CHAT_HTML
    assert 'workspace-diagnostics-hero' in TEST_CHAT_HTML
    assert 'workspace-signal-grid' in TEST_CHAT_HTML
    assert 'class="workspace-section workspace-section-danger"' in TEST_CHAT_HTML
    assert 'id="workspace-mode-chip"' in TEST_CHAT_HTML
    assert 'id="workspace-open-diagnostics"' in TEST_CHAT_HTML
    assert "Kaynak ve model" in TEST_CHAT_HTML
    assert "Gönderim modu" in TEST_CHAT_HTML
    assert "Araçlar ve çıktı" in TEST_CHAT_HTML
    assert "Riskli işlemler" in TEST_CHAT_HTML
    assert "Tanılama Merkezi" in TEST_CHAT_HTML
    assert "Geri bildirim stüdyosu" in TEST_CHAT_HTML


def test_chat_lab_workspace_flyout_styles_define_console_shell() -> None:
    assert ".workspace-console" in TEST_CHAT_STYLE
    assert ".workspace-flyout{" in TEST_CHAT_STYLE
    assert ".workspace-utility-nav" in TEST_CHAT_STYLE
    assert ".workspace-utility-link.is-active" in TEST_CHAT_STYLE
    assert ".workspace-flyout-topbar" in TEST_CHAT_STYLE
    assert ".workspace-hero" in TEST_CHAT_STYLE
    assert ".workspace-hero-grid" in TEST_CHAT_STYLE
    assert ".workspace-diagnostics-hero" in TEST_CHAT_STYLE
    assert ".workspace-signal-grid" in TEST_CHAT_STYLE
    assert ".workspace-overview-card" in TEST_CHAT_STYLE
    assert ".workspace-section" in TEST_CHAT_STYLE
    assert ".workspace-section-danger" in TEST_CHAT_STYLE
    assert "width:min(640px,96vw)" in TEST_CHAT_STYLE
    assert "linear-gradient(180deg,#13233e 0%,#101d34 14%,#0c1526 100%)" in TEST_CHAT_STYLE


def test_chat_lab_live_feed_inactive_toggle_is_wired() -> None:
    assert 'id="include-inactive-toggle"' in TEST_CHAT_HTML
    assert "const includeInactiveToggle = el('include-inactive-toggle');" in TEST_CHAT_SCRIPT
    assert "include_inactive=true" in TEST_CHAT_SCRIPT


def test_chat_lab_script_has_single_wire_events_definition() -> None:
    assert TEST_CHAT_SCRIPT.count("function wireEvents()") == 1


def test_chat_lab_script_wires_workspace_flyout_keyboard_flow() -> None:
    assert "workspaceFlyoutOpen: false" in TEST_CHAT_SCRIPT
    assert "workspaceFlyoutTab: 'settings'" in TEST_CHAT_SCRIPT
    assert "function renderWorkspaceFlyout()" in TEST_CHAT_SCRIPT
    assert "function toggleWorkspaceFlyout(tab = 'settings')" in TEST_CHAT_SCRIPT
    assert "function toggleWorkspaceDiagnostics(forceOpen = null)" in TEST_CHAT_SCRIPT
    assert "function handleWorkspaceFlyoutTabKeydown(event)" in TEST_CHAT_SCRIPT
    assert "function trapWorkspaceFlyoutFocus(event)" in TEST_CHAT_SCRIPT
    assert "el('workspace-scrim').addEventListener('click', closeWorkspaceFlyout);" in TEST_CHAT_SCRIPT
    assert "el('workspace-flyout').addEventListener('keydown', event => {" in TEST_CHAT_SCRIPT
    assert "el('workspace-diagnostics-toggle').addEventListener('click', () => toggleWorkspaceFlyout('diagnostics'));" in TEST_CHAT_SCRIPT
    assert "el('workspace-open-diagnostics').addEventListener('click', toggleWorkspaceDiagnostics);" in TEST_CHAT_SCRIPT
    assert "panel.setAttribute('aria-modal', String(state.workspaceFlyoutOpen));" in TEST_CHAT_SCRIPT
    assert "handleWorkspaceFlyoutTabKeydown(event);" in TEST_CHAT_SCRIPT
    assert "trapWorkspaceFlyoutFocus(event);" in TEST_CHAT_SCRIPT


def test_chat_lab_script_drops_legacy_debug_panel_names() -> None:
    assert 'id="debug-panel"' not in TEST_CHAT_HTML
    assert "function toggleDebug(" not in TEST_CHAT_SCRIPT
    assert "el('debug-panel')" not in TEST_CHAT_SCRIPT
    assert 'id="toggle-debug"' not in TEST_CHAT_HTML


def test_chat_lab_workspace_flyout_runtime_updates_modal_and_tab_state() -> None:
    harness = """
function register(id, classes = []) {
  const node = new HTMLElement(id);
  node.classList = new SimpleClassList(classes);
  __elements[id] = node;
  return node;
}
const appShell = register('appShell', ['app']);
const panel = register('workspace-flyout', ['workspace-flyout']);
const scrim = register('workspace-scrim', ['workspace-scrim']);
const settingsPanel = register('workspace-settings-panel', ['workspace-tab-panel', 'workspace-console']);
const diagnosticsPanel = register('workspace-diagnostics-panel', ['workspace-tab-panel', 'workspace-console', 'hidden']);
const heading = register('workspace-flyout-heading');
const description = register('workspace-flyout-description');
const toggle = register('workspace-panel-toggle');
const headerDiagnosticsToggle = register('workspace-diagnostics-toggle');
const diagnosticsToggle = register('workspace-open-diagnostics');
const modeIndicator = register('workspace-mode-indicator');
const modeChip = register('workspace-mode-chip');
const sourceSummary = register('workspace-source-summary');
const modeSummary = register('workspace-mode-summary');
const phoneInput = register('phone-input');
phoneInput.value = 'smoke_user';
const tabSettings = register('workspace-tab-settings', ['workspace-flyout-tab']);
tabSettings.dataset.workspaceTab = 'settings';
const tabDiagnostics = register('workspace-tab-diagnostics', ['workspace-flyout-tab']);
tabDiagnostics.dataset.workspaceTab = 'diagnostics';
__tabs.push(tabSettings, tabDiagnostics);

state.operationMode = 'approval';
state.workspaceFlyoutOpen = true;
state.workspaceFlyoutTab = 'diagnostics';
state.sourceType = 'live_test_chat';
state.importFile = '';
renderWorkspaceFlyout();

const openState = {
  panelModal: panel.getAttribute('aria-modal'),
  panelHidden: panel.getAttribute('aria-hidden'),
  appHidden: appShell.getAttribute('aria-hidden'),
  appInert: Boolean(appShell.inert),
  settingsHidden: settingsPanel.classList.contains('hidden'),
  diagnosticsHidden: diagnosticsPanel.classList.contains('hidden'),
  diagnosticsTabSelected: tabDiagnostics.getAttribute('aria-selected'),
  heading: heading.textContent,
  modeIndicatorClasses: modeIndicator.classList.toString(),
  modeChipClasses: modeChip.classList.toString(),
  headerDiagnosticsExpanded: headerDiagnosticsToggle.getAttribute('aria-expanded'),
  diagnosticsExpanded: diagnosticsToggle.getAttribute('aria-expanded'),
};

state.workspaceFlyoutOpen = false;
state.workspaceFlyoutTab = 'settings';
renderWorkspaceFlyout();

const closedState = {
  panelModal: panel.getAttribute('aria-modal'),
  panelHidden: panel.getAttribute('aria-hidden'),
  appHidden: appShell.getAttribute('aria-hidden'),
  appInert: Boolean(appShell.inert),
  panelCollapsed: panel.classList.contains('collapsed'),
  settingsHidden: settingsPanel.classList.contains('hidden'),
  diagnosticsHidden: diagnosticsPanel.classList.contains('hidden'),
  toggleExpanded: toggle.getAttribute('aria-expanded'),
  headerDiagnosticsExpanded: headerDiagnosticsToggle.getAttribute('aria-expanded'),
};

console.log(JSON.stringify({ openState, closedState }));
"""
    result = _run_chat_lab_script_harness(harness)
    assert result["openState"]["panelModal"] == "true"
    assert result["openState"]["panelHidden"] == "false"
    assert result["openState"]["appHidden"] == "true"
    assert result["openState"]["appInert"] is True
    assert result["openState"]["settingsHidden"] is True
    assert result["openState"]["diagnosticsHidden"] is False
    assert result["openState"]["diagnosticsTabSelected"] == "true"
    assert result["openState"]["heading"] == "Tanılama"
    assert "is-mode-approval" in result["openState"]["modeIndicatorClasses"]
    assert "is-mode-approval" in result["openState"]["modeChipClasses"]
    assert result["openState"]["headerDiagnosticsExpanded"] == "true"
    assert result["openState"]["diagnosticsExpanded"] == "true"
    assert result["closedState"]["panelModal"] == "false"
    assert result["closedState"]["panelHidden"] == "true"
    assert result["closedState"]["appHidden"] == "false"
    assert result["closedState"]["appInert"] is False
    assert result["closedState"]["panelCollapsed"] is True
    assert result["closedState"]["settingsHidden"] is False
    assert result["closedState"]["diagnosticsHidden"] is True
    assert result["closedState"]["toggleExpanded"] == "false"
    assert result["closedState"]["headerDiagnosticsExpanded"] == "false"


def test_chat_lab_workspace_flyout_runtime_keyboard_navigation_and_focus_wrap() -> None:
    harness = """
function register(id, classes = []) {
  const node = new HTMLElement(id);
  node.classList = new SimpleClassList(classes);
  __elements[id] = node;
  return node;
}
const appShell = register('appShell', ['app']);
const panel = register('workspace-flyout', ['workspace-flyout', 'collapsed']);
const scrim = register('workspace-scrim', ['workspace-scrim', 'hidden']);
const settingsPanel = register('workspace-settings-panel', ['workspace-tab-panel', 'workspace-console']);
const diagnosticsPanel = register('workspace-diagnostics-panel', ['workspace-tab-panel', 'workspace-console', 'hidden']);
const heading = register('workspace-flyout-heading');
const description = register('workspace-flyout-description');
const toggle = register('workspace-panel-toggle');
const headerDiagnosticsToggle = register('workspace-diagnostics-toggle');
const diagnosticsToggle = register('workspace-open-diagnostics');
const closeButton = register('workspace-flyout-close');
const modeIndicator = register('workspace-mode-indicator');
const modeChip = register('workspace-mode-chip');
const sourceSummary = register('workspace-source-summary');
const modeSummary = register('workspace-mode-summary');
const phoneInput = register('phone-input');
phoneInput.value = 'keyboard_user';
const tabSettings = register('workspace-tab-settings', ['workspace-flyout-tab']);
tabSettings.dataset.workspaceTab = 'settings';
const tabDiagnostics = register('workspace-tab-diagnostics', ['workspace-flyout-tab']);
tabDiagnostics.dataset.workspaceTab = 'diagnostics';
panel.children = [tabSettings, tabDiagnostics, closeButton];
__tabs.push(tabSettings, tabDiagnostics);

document.activeElement = toggle;
state.operationMode = 'ai';
state.sourceType = 'live_test_chat';
openWorkspaceFlyout('settings');

const afterOpen = {
  tab: state.workspaceFlyoutTab,
  activeElement: document.activeElement.id,
  returnFocusStored: Boolean(_workspaceFlyoutReturnFocus && _workspaceFlyoutReturnFocus.id === 'workspace-panel-toggle'),
};

let navPrevented = false;
handleWorkspaceFlyoutTabKeydown({
  key: 'ArrowRight',
  target: { closest() { return tabSettings; } },
  preventDefault() { navPrevented = true; },
});

const afterArrowRight = {
  tab: state.workspaceFlyoutTab,
  activeElement: document.activeElement.id,
  prevented: navPrevented,
};

let wrapForwardPrevented = false;
document.activeElement = closeButton;
trapWorkspaceFlyoutFocus({
  key: 'Tab',
  shiftKey: false,
  preventDefault() { wrapForwardPrevented = true; },
});

const afterWrapForward = {
  activeElement: document.activeElement.id,
  prevented: wrapForwardPrevented,
};

let wrapBackwardPrevented = false;
document.activeElement = tabSettings;
trapWorkspaceFlyoutFocus({
  key: 'Tab',
  shiftKey: true,
  preventDefault() { wrapBackwardPrevented = true; },
});

const afterWrapBackward = {
  activeElement: document.activeElement.id,
  prevented: wrapBackwardPrevented,
};

closeWorkspaceFlyout();

const afterClose = {
  flyoutOpen: state.workspaceFlyoutOpen,
  activeElement: document.activeElement.id,
};

console.log(JSON.stringify({ afterOpen, afterArrowRight, afterWrapForward, afterWrapBackward, afterClose }));
"""
    result = _run_chat_lab_script_harness(harness)
    assert result["afterOpen"]["tab"] == "settings"
    assert result["afterOpen"]["activeElement"] == "workspace-tab-settings"
    assert result["afterOpen"]["returnFocusStored"] is True
    assert result["afterArrowRight"]["tab"] == "diagnostics"
    assert result["afterArrowRight"]["activeElement"] == "workspace-tab-diagnostics"
    assert result["afterArrowRight"]["prevented"] is True
    assert result["afterWrapForward"]["activeElement"] == "workspace-tab-settings"
    assert result["afterWrapForward"]["prevented"] is True
    assert result["afterWrapBackward"]["activeElement"] == "workspace-flyout-close"
    assert result["afterWrapBackward"]["prevented"] is True
    assert result["afterClose"]["flyoutOpen"] is False
    assert result["afterClose"]["activeElement"] == "workspace-panel-toggle"


def test_chat_lab_script_is_valid_javascript() -> None:
    node_path = shutil.which("node")
    assert node_path, "node is required for Chat Lab syntax checks"

    with tempfile.TemporaryDirectory() as tmp_dir:
        script_path = Path(tmp_dir) / "chat_lab.js"
        script_path.write_text(TEST_CHAT_SCRIPT, encoding="utf-8")
        subprocess.run(
            [node_path, "--check", str(script_path)],
            check=True,
            capture_output=True,
        )


def test_admin_panel_shared_label_helper_avoids_broken_regex_escape() -> None:
    assert "findExplicitLabel(" in ADMIN_PANEL_SCRIPT
    assert "label[for]" in ADMIN_PANEL_SCRIPT
    assert "getAttribute('for') === nodeId" in ADMIN_PANEL_SCRIPT
    assert "var safeId =" not in ADMIN_PANEL_SCRIPT


def test_admin_auth_forms_do_not_fallback_to_get_submission() -> None:
    html = render_admin_panel_html()
    assert '<form id="loginForm" class="field-grid" method="post">' in html
    assert '<form id="bootstrapForm" class="field-grid mt-md" method="post">' in html
    assert '<form id="totpRecoveryForm" class="field-grid" method="post">' in html
    assert '<form id="otpVerifyForm" class="field-grid mt-md" method="post" hidden>' in html


def test_admin_hotel_profile_section_exposes_publish_controls() -> None:
    html = render_admin_panel_html()
    assert 'id="publishHotelFacts"' in html
    assert 'id="hotelProfileSections"' in html
    assert 'id="hotelProfileSectionBody"' in html
    assert 'id="applyHotelProfileJson"' in html
    assert 'data-advanced-mode="hotel-profile-json"' in html
    assert 'id="hotelFactsConflict"' in html
    assert 'id="hotelFactsStatus"' in html
    assert 'id="hotelFactsHistory"' in html
    assert 'id="hotelFactsEvents"' in html
    assert 'id="hotelFactsVersionDetail"' in html
    assert "Teknik Düzenleme • Ham JSON" in html
    assert (
        "Taslağı kaydedebilir, ardından değişiklikleri yayına alabilirsiniz. "
        "Misafirler yalnızca yayımlanmış son sürümü görür."
    ) in html


def test_admin_panel_shell_uses_turkish_labels() -> None:
    html = render_admin_panel_html()
    assert "NexlumeAI Yönetim Paneli" in html
    assert "Genel Bakış" in html
    assert "Konuşmalar" in html
    assert "Kapsam" in html
    assert "Yapılandırmayı Yenile" in html
    assert "SSS Kayıtları" in html
    assert "Slot Yönetimi" in html
    assert "Talep Takibi" in html
    assert "Bildirim Numaraları" in html
    assert "Restoran Plan Çizimi" in html
    assert "Masa Ayrıntıları" in html


def test_admin_panel_script_loads_hotel_facts_status_and_publish_actions() -> None:
    assert "HOTEL_PROFILE_SECTIONS" in ADMIN_PANEL_SCRIPT
    assert "renderHotelProfileWorkspace" in ADMIN_PANEL_SCRIPT
    assert "renderHotelProfileGeneralSection" in ADMIN_PANEL_SCRIPT
    assert "renderHotelProfileContactsSection" in ADMIN_PANEL_SCRIPT
    assert "renderHotelProfileRoomsSection" in ADMIN_PANEL_SCRIPT
    assert "renderHotelProfilePricingSection" in ADMIN_PANEL_SCRIPT
    assert "renderHotelProfileTransfersSection" in ADMIN_PANEL_SCRIPT
    assert "renderHotelProfileRestaurantSection" in ADMIN_PANEL_SCRIPT
    assert "renderHotelProfileFaqSection" in ADMIN_PANEL_SCRIPT
    assert "renderHotelProfilePoliciesSection" in ADMIN_PANEL_SCRIPT
    assert "renderHotelProfileAssistantSection" in ADMIN_PANEL_SCRIPT
    assert "renderFaqCard" in ADMIN_PANEL_SCRIPT
    assert "renderMultiCheckboxField" in ADMIN_PANEL_SCRIPT
    assert "renderNearbyPlaceCard" in ADMIN_PANEL_SCRIPT
    assert "renderPolicyCard" in ADMIN_PANEL_SCRIPT
    assert "HIGHLIGHT_OPTIONS" in ADMIN_PANEL_SCRIPT
    assert "CONTACT_ROLE_OPTIONS" in ADMIN_PANEL_SCRIPT
    assert "CONTACT_PRESET_OPTIONS" in ADMIN_PANEL_SCRIPT
    assert "BOARD_TYPE_PRESET_OPTIONS" in ADMIN_PANEL_SCRIPT
    assert "ROOM_TYPE_PRESET_OPTIONS" in ADMIN_PANEL_SCRIPT
    assert "ROOM_AMENITY_OPTIONS" in ADMIN_PANEL_SCRIPT
    assert "ROOM_FEATURE_OPTIONS" in ADMIN_PANEL_SCRIPT
    assert "FAQ_TOPIC_OPTIONS" in ADMIN_PANEL_SCRIPT
    assert "CANCELLATION_RULE_PRESET_OPTIONS" in ADMIN_PANEL_SCRIPT
    assert "CHILD_POLICY_OPTIONS" in ADMIN_PANEL_SCRIPT
    assert "BEDDING_AVAILABILITY_OPTIONS" in ADMIN_PANEL_SCRIPT
    assert "LAUNDRY_TURNAROUND_OPTIONS" in ADMIN_PANEL_SCRIPT


def test_admin_panel_script_tracks_hash_navigation_for_chatlab() -> None:
    assert "window.addEventListener('hashchange'" in ADMIN_PANEL_SCRIPT
    assert "SERVICE_POINT_OPTIONS" in ADMIN_PANEL_SCRIPT
    assert "buildRoomTypeSelectionOptions" in ADMIN_PANEL_SCRIPT
    assert "getActiveHotelProfileFaqIndex" in ADMIN_PANEL_SCRIPT
    assert "buildFaqOptionLabel" in ADMIN_PANEL_SCRIPT
    assert "renderSelectField" in ADMIN_PANEL_SCRIPT
    assert "normalizeProfileFormattedValue" in ADMIN_PANEL_SCRIPT
    assert "isProfileFormattedValueValid" in ADMIN_PANEL_SCRIPT
    assert "applyProfileFieldFormatting" in ADMIN_PANEL_SCRIPT
    assert "onHotelProfileSectionInput" in ADMIN_PANEL_SCRIPT
    assert "getVisibleHotelProfileSections" in ADMIN_PANEL_SCRIPT
    assert "ensureVisibleHotelProfileSection" in ADMIN_PANEL_SCRIPT
    assert "syncHotelProfileAdvancedModeVisibility" in ADMIN_PANEL_SCRIPT
    assert "addContactPresetToDraft" in ADMIN_PANEL_SCRIPT
    assert "addBoardTypePresetToDraft" in ADMIN_PANEL_SCRIPT
    assert "addRoomTypePresetToDraft" in ADMIN_PANEL_SCRIPT
    assert "addCancellationRulePresetToDraft" in ADMIN_PANEL_SCRIPT
    assert "renderStandardRateMappingSummary" in ADMIN_PANEL_SCRIPT
    assert "ensureRateMappingEntryForKey" in ADMIN_PANEL_SCRIPT
    assert "getLinkedProfileMapCollection" in ADMIN_PANEL_SCRIPT
    assert "ensureLinkedProfileMapEntry" in ADMIN_PANEL_SCRIPT
    assert "ensureDraftListByPath" in ADMIN_PANEL_SCRIPT
    assert "createDefaultPathListItem" in ADMIN_PANEL_SCRIPT
    assert "applyHotelProfileSectionSearch" in ADMIN_PANEL_SCRIPT
    assert "onHotelProfileSectionSearchInput" in ADMIN_PANEL_SCRIPT
    assert "onHotelProfileSectionSearchClick" in ADMIN_PANEL_SCRIPT
    assert "scheduleHotelFactsDraftValidation" in ADMIN_PANEL_SCRIPT
    assert "runHotelFactsDraftValidation" in ADMIN_PANEL_SCRIPT
    assert "buildHotelFactsDraftValidationState" in ADMIN_PANEL_SCRIPT
    assert "applyHotelProfileValidationDecorations" in ADMIN_PANEL_SCRIPT
    assert "renderHotelProfileSectionOverview" in ADMIN_PANEL_SCRIPT
    assert "renderHotelProfileOverviewSummary" in ADMIN_PANEL_SCRIPT
    assert "buildHotelProfileSectionOverview" in ADMIN_PANEL_SCRIPT
    assert "buildHotelProfileOverviewSummary" in ADMIN_PANEL_SCRIPT
    assert "getHotelProfileSectionCompletion" in ADMIN_PANEL_SCRIPT
    assert "openHotelProfileOverviewTarget" in ADMIN_PANEL_SCRIPT
    assert "applyHotelProfileSectionIssueBadges" in ADMIN_PANEL_SCRIPT
    assert "applyHotelProfileFieldMarkers" in ADMIN_PANEL_SCRIPT
    assert "renderHotelProfileSectionIssues" in ADMIN_PANEL_SCRIPT
    assert "profile-overview-status" in ADMIN_PANEL_SCRIPT
    assert "profile-progress-fill" in ADMIN_PANEL_SCRIPT
    assert "Bölüm İlerleme Özeti" in ADMIN_PANEL_SCRIPT
    assert "Eksik Alan Özeti" in ADMIN_PANEL_SCRIPT
    assert "data-profile-overview-target" in ADMIN_PANEL_SCRIPT
    assert "data-profile-overview-path" in ADMIN_PANEL_SCRIPT
    assert "profile-overview-metrics" in ADMIN_PANEL_SCRIPT
    assert "focusFirstHotelProfileIssueInSection" in ADMIN_PANEL_SCRIPT
    assert "oda açıklaması" in ADMIN_PANEL_SCRIPT
    assert "fiyat türü / kod kimliği" in ADMIN_PANEL_SCRIPT
    assert "transfer fiyatı (EUR)" in ADMIN_PANEL_SCRIPT
    assert "restoran alan türü" in ADMIN_PANEL_SCRIPT
    assert "data-profile-issue-path" in ADMIN_PANEL_SCRIPT
    assert "/facts/validate" in ADMIN_PANEL_SCRIPT
    assert "data-clear-profile-search" in ADMIN_PANEL_SCRIPT
    assert "data-profile-mode" in ADMIN_PANEL_SCRIPT
    assert "Standart Düzenleme" in ADMIN_PANEL_SCRIPT
    assert "Teknik Ayarlar" in ADMIN_PANEL_SCRIPT
    assert "Ödeme Yöntemleri" in ADMIN_PANEL_SCRIPT
    assert "Ek diller ve alternatif sorular" in ADMIN_PANEL_SCRIPT
    assert "Aramanızla eşleşen alan bulunamadı." in ADMIN_PANEL_SCRIPT
    assert "applyHotelProfileJsonToForm" in ADMIN_PANEL_SCRIPT
    assert "data-hotel-profile-section" in ADMIN_PANEL_SCRIPT
    assert "data-profile-add-list-item" in ADMIN_PANEL_SCRIPT
    assert "data-profile-add-map-entry" in ADMIN_PANEL_SCRIPT
    assert "question_variants_tr" in ADMIN_PANEL_SCRIPT
    assert "data-profile-faq-active" in ADMIN_PANEL_SCRIPT
    assert "Yapay Zekâ Akışı" in ADMIN_PANEL_SCRIPT
    assert "SSS" in ADMIN_PANEL_SCRIPT
    assert "Karşılama" in render_admin_panel_html()
    assert "Taslak" in render_admin_panel_html()
    assert "Çözüldü" in render_admin_panel_html()
    assert "formatTicketStatus" in ADMIN_PANEL_SCRIPT
    assert "formatConversationState" in ADMIN_PANEL_SCRIPT
    assert "formatFaqStatus" in ADMIN_PANEL_SCRIPT
    assert "/facts/status" in ADMIN_PANEL_SCRIPT
    assert "/facts/versions" in ADMIN_PANEL_SCRIPT
    assert "/facts/events" in ADMIN_PANEL_SCRIPT
    assert "/facts/publish" in ADMIN_PANEL_SCRIPT
    assert "/facts/rollback" in ADMIN_PANEL_SCRIPT
    assert "renderHotelFactsStatus" in ADMIN_PANEL_SCRIPT
    assert "renderHotelFactsConflict" in ADMIN_PANEL_SCRIPT
    assert "renderHotelFactsHistory" in ADMIN_PANEL_SCRIPT
    assert "renderHotelFactsEvents" in ADMIN_PANEL_SCRIPT
    assert "renderHotelFactsVersionDetail" in ADMIN_PANEL_SCRIPT
    assert "revealHotelFactsVersionDetail" in ADMIN_PANEL_SCRIPT
    assert "loadHotelFactsVersionDetail" in ADMIN_PANEL_SCRIPT
    assert "rollbackHotelFacts" in ADMIN_PANEL_SCRIPT
    assert "publishHotelFacts" in ADMIN_PANEL_SCRIPT
    assert "restoreHotelFactsConflictDraft" in ADMIN_PANEL_SCRIPT
    assert "dismissHotelFactsConflict" in ADMIN_PANEL_SCRIPT
    assert "summarizeHotelProfileTopLevelDiff" in ADMIN_PANEL_SCRIPT
    assert "diffJsonValues" in ADMIN_PANEL_SCRIPT
    assert "previewDiffValue" in ADMIN_PANEL_SCRIPT
    assert "data-facts-conflict-restore-draft" in ADMIN_PANEL_SCRIPT
    assert "data-facts-conflict-dismiss" in ADMIN_PANEL_SCRIPT
    assert "expected_source_profile_checksum" in ADMIN_PANEL_SCRIPT
    assert "expected_current_version" in ADMIN_PANEL_SCRIPT


def test_admin_panel_save_and_publish_use_loaded_draft_checksum_baseline() -> None:
    assert "hotelProfileLoadedSourceChecksum: null" in ADMIN_PANEL_SCRIPT
    assert "hotelProfileLoadedDraftSnapshot: null" in ADMIN_PANEL_SCRIPT
    assert "hotelProfileHasUnsavedChanges: false" in ADMIN_PANEL_SCRIPT
    assert "hotelProfileMode: 'standard'" in ADMIN_PANEL_SCRIPT
    assert "hotelFactsDraftValidation: null" in ADMIN_PANEL_SCRIPT
    assert (
        "state.hotelProfileLoadedSourceChecksum = state.hotelFactsStatus?.draft_source_profile_checksum || null;"
        in ADMIN_PANEL_SCRIPT
    )
    assert "state.hotelProfileLoadedDraftSnapshot = refs.hotelProfileEditor.value;" in ADMIN_PANEL_SCRIPT
    assert "state.hotelProfileLoadedSourceChecksum = null;" in ADMIN_PANEL_SCRIPT
    assert "state.hotelProfileLoadedDraftSnapshot = null;" in ADMIN_PANEL_SCRIPT
    assert ADMIN_PANEL_SCRIPT.count(
        "expected_source_profile_checksum: state.hotelProfileLoadedSourceChecksum || null"
    ) == 2
    assert 'Kaydedilmemiş değişiklikler var. Önce "Taslağı Kaydet" ile taslağı güncelleyin.' in ADMIN_PANEL_SCRIPT
    assert "Taslak / Canlı Karşılaştırması" in ADMIN_PANEL_SCRIPT
    assert "Yayın Kontrolü" in ADMIN_PANEL_SCRIPT
    assert "buildHotelFactsDraftValidationState" in ADMIN_PANEL_SCRIPT
    assert "buildHotelFactsDraftValidationFromStatus" in ADMIN_PANEL_SCRIPT
    assert "validated_facts_checksum" in ADMIN_PANEL_SCRIPT
    assert "validated_source_profile_checksum" in ADMIN_PANEL_SCRIPT
    assert (
        "refs.publishHotelFacts.disabled = !canPublishHotelFacts(status) || state.hotelProfileHasUnsavedChanges;"
        in ADMIN_PANEL_SCRIPT
    )
    assert "refs.saveHotelProfile.disabled = !state.hotelProfileHasUnsavedChanges;" in ADMIN_PANEL_SCRIPT
    assert "syncHotelProfileDirtyState()" in ADMIN_PANEL_SCRIPT


def test_admin_panel_inline_scripts_are_valid_javascript() -> None:
    node_path = shutil.which("node")
    assert node_path, "node is required for inline script syntax checks"

    html = render_admin_panel_html()
    scripts = html.split("<script>")[1:]
    assert scripts

    with tempfile.TemporaryDirectory() as tmp_dir:
        for index, script_block in enumerate(scripts, start=1):
            script = script_block.split("</script>", 1)[0]
            script_path = Path(tmp_dir) / f"admin_script_{index}.js"
            script_path.write_text(script, encoding="utf-8")
            subprocess.run(  # noqa: S603 - node path comes from shutil.which and script is a temp file we generate
                [node_path, "--check", str(script_path)],
                check=True,
                capture_output=True,
                text=True,
            )


def test_admin_panel_script_handles_structured_detail_messages() -> None:
    assert "typeof payload.detail === 'object'" in ADMIN_PANEL_SCRIPT
    assert "typeof payload.detail.message === 'string'" in ADMIN_PANEL_SCRIPT
    assert "return payload.detail.message.trim();" in ADMIN_PANEL_SCRIPT
    assert "error.status = response.status;" in ADMIN_PANEL_SCRIPT
    assert "if (error?.status === 409)" in ADMIN_PANEL_SCRIPT
    assert "hotel_profile_conflict" in ADMIN_PANEL_SCRIPT
    assert "hotel_facts_publish_conflict" in ADMIN_PANEL_SCRIPT
    assert "hotel_facts_rollback_conflict" in ADMIN_PANEL_SCRIPT
    assert "Liste boyutu farkli" in ADMIN_PANEL_SCRIPT
    assert "Yerel " in ADMIN_PANEL_SCRIPT
    assert "JSON'u Forma Aktar" in render_admin_panel_html()


def test_admin_panel_debug_artifact_ui_includes_preview_and_context_copy() -> None:
    html = render_admin_panel_html()

    assert 'id="debugArtifactPreviewDialog"' in html
    assert "openDebugArtifactPreview(" in ADMIN_PANEL_SCRIPT
    assert "groupDebugArtifacts(" in ADMIN_PANEL_SCRIPT
    assert "Bu run temiz tamamlandı." in ADMIN_PANEL_SCRIPT
    assert ".debug-artifact-summary" in ADMIN_PANEL_STYLE
    assert ".debug-artifact-dialog" in ADMIN_PANEL_STYLE


def test_hold_rows_are_clickable_without_detail_button() -> None:
    """Hold table rows should be directly clickable for selection."""
    assert '.holds-table tbody tr[data-open-hold]{cursor:pointer}' in ADMIN_PANEL_STYLE
    assert 'data-open-hold="' in ADMIN_HOLDS_SCRIPT


def test_restaurant_floor_plan_texts_are_localized() -> None:
    assert "Kayıtlı plan yok" in ADMIN_RESTAURANT_SCRIPT
    assert "Plan seç" in ADMIN_RESTAURANT_SCRIPT
    assert "Plan Adı Girin" in ADMIN_RESTAURANT_SCRIPT
    assert "Aktif plan yok veya bu tarihte masa ataması bulunamadı." in ADMIN_RESTAURANT_SCRIPT


def test_admin_panel_browser_like_harness_blocks_publish_until_saved_then_publishes() -> None:
    result = _run_admin_panel_script_harness(
        """
const apiCalls = [];
const notifications = [];

notify = function(message, tone) {
  notifications.push({ message, tone });
};

renderHotelFactsStatus = function() {};
renderHotelFactsConflict = function() {};
renderHotelFactsHistory = function() {};
renderHotelFactsEvents = function() {};
renderHotelFactsVersionDetail = function() {};

apiFetch = async function(path, options = {}) {
  apiCalls.push({ path, body: options.body || null, method: options.method || 'GET' });
  if (path === '/hotels/21966/profile') {
    return {
      profile_path: 'kassandra.yaml',
      facts_status: { state: 'draft_pending_publish' },
    };
  }
  if (path === '/hotels/21966/facts/publish') {
    return {
      version: 7,
      published: true,
    };
  }
  throw new Error('Unexpected apiFetch path: ' + path);
};

loadHotelProfileSection = async function() {
  state.hotelFactsStatus = { state: 'draft_pending_publish' };
  state.hotelFactsDraftValidation = {
    publishable: true,
    factsChecksum: 'candidate-facts',
    sourceProfileChecksum: 'candidate-source',
    blockers: [],
    warnings: [],
  };
  state.hotelProfileHasUnsavedChanges = false;
  state.hotelProfileLoadedSourceChecksum = 'saved-checksum';
  state.hotelProfileLoadedDraftSnapshot = refs.hotelProfileEditor.value;
};

refs.hotelProfileSelect = new HTMLElement();
refs.hotelProfileSelect.value = '21966';
refs.hotelProfileEditor = new HTMLElement();
refs.hotelProfileEditor.value = JSON.stringify({
  hotel_id: 21966,
  hotel_name: { tr: 'Kassandra', en: 'Kassandra' },
  description: { tr: 'Yeni açıklama', en: 'New description' },
});
refs.hotelProfileMeta = new HTMLElement();
refs.hotelFactsConflict = new HTMLElement();
refs.hotelFactsStatus = new HTMLElement();
refs.hotelFactsHistory = new HTMLElement();
refs.hotelFactsEvents = new HTMLElement();
refs.hotelFactsVersionDetail = new HTMLElement();
refs.publishHotelFacts = new HTMLElement();
refs.saveHotelProfile = new HTMLElement();
refs.hotelProfileSections = new HTMLElement();
refs.hotelProfileSectionBody = new HTMLElement();
refs.toast = new HTMLElement();

state.selectedHotelId = '21966';
state.hotelDetail = { hotel_id: 21966, name_en: 'Kassandra Oludeniz' };
state.hotelFactsStatus = { state: 'in_sync' };
state.hotelFactsDraftValidation = {
  publishable: true,
  factsChecksum: 'candidate-facts',
  sourceProfileChecksum: 'candidate-source',
  blockers: [],
  warnings: [],
};
state.hotelProfileLoadedSourceChecksum = 'loaded-checksum';
state.hotelProfileLoadedDraftSnapshot = JSON.stringify({
  hotel_id: 21966,
  hotel_name: { tr: 'Kassandra', en: 'Kassandra' },
  description: { tr: 'Eski açıklama', en: 'Old description' },
});
state.hotelProfileHasUnsavedChanges = true;

(async () => {
  await publishHotelFacts();
  await saveHotelProfile();
  await publishHotelFacts();
  console.log(JSON.stringify({
    apiCalls,
    notifications,
    loadedChecksum: state.hotelProfileLoadedSourceChecksum,
    hasUnsavedChanges: state.hotelProfileHasUnsavedChanges,
  }));
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
"""
    )

    assert [call["path"] for call in result["apiCalls"]] == [
        "/hotels/21966/profile",
        "/hotels/21966/facts/publish",
    ]
    assert result["apiCalls"][0]["body"]["expected_source_profile_checksum"] == "loaded-checksum"
    assert result["apiCalls"][1]["body"]["expected_source_profile_checksum"] == "saved-checksum"
    assert result["notifications"][0]["message"] == (
        'Kaydedilmemiş değişiklikler var. Önce "Taslağı Kaydet" ile taslağı güncelleyin.'
    )
    assert "Profil kaydedildi" in result["notifications"][1]["message"]
    assert result["notifications"][2]["message"] == "Canlı sürüm güncellendi. Sürüm 7."
    assert result["loadedChecksum"] == "saved-checksum"
    assert result["hasUnsavedChanges"] is False


def test_admin_panel_version_detail_actions_reveal_and_highlight_selected_version() -> None:
    result = _run_admin_panel_script_harness(
        """
const apiCalls = [];
const detailClassNames = new Set();

notify = function() {};
apiFetch = async function(path) {
  apiCalls.push(path);
  if (path === '/hotels/21966/facts/versions/5') {
    return {
      version: 5,
      is_current: false,
      checksum: 'checksum-v5',
      published_by: 'ops_admin',
      published_at: '2026-03-31T20:00:00Z',
      source_profile_checksum: 'source-v5',
      facts: { room_types: [{ code: 'dlx' }], faq_data: [{ faq_id: 'faq-1' }], transfer_routes: [{ route_code: 'apt' }] },
      validation: { blockers: [], warnings: [{ path: 'description', message: 'Eksik açıklama' }] },
    };
  }
  throw new Error('Unexpected apiFetch path: ' + path);
};

refs.hotelProfileSelect = new HTMLElement();
refs.hotelProfileSelect.value = '21966';
refs.hotelFactsVersionDetail = new HTMLElement();
refs.hotelFactsVersionDetail.classList = {
  add(...names) { names.forEach(name => detailClassNames.add(name)); },
  remove(...names) { names.forEach(name => detailClassNames.delete(name)); },
  contains(name) { return detailClassNames.has(name); },
};
refs.hotelFactsVersionDetail.scrollIntoView = function() {
  globalThis.__detailScrollCount = (globalThis.__detailScrollCount || 0) + 1;
};
refs.hotelFactsHistory = new HTMLElement();
refs.hotelFactsEvents = new HTMLElement();

state.selectedHotelId = '21966';
state.hotelFactsVersions = [
  { version: 6, is_current: true, published_by: 'ops_admin', published_at: '2026-03-31T21:00:00Z', blocker_count: 0, warning_count: 1, checksum: 'checksum-v6' },
  { version: 5, is_current: false, published_by: 'ops_admin', published_at: '2026-03-31T20:00:00Z', blocker_count: 0, warning_count: 1, checksum: 'checksum-v5' },
];
state.hotelFactsEvents = [
  { event_type: 'PUBLISH', version: 6, actor: 'ops_admin', occurred_at: '2026-03-31T21:00:00Z', metadata: { source_profile_checksum: 'source-v6' } },
  { event_type: 'PUBLISH', version: 5, actor: 'ops_admin', occurred_at: '2026-03-31T20:00:00Z', metadata: { source_profile_checksum: 'source-v5' } },
];

(async () => {
  await loadHotelFactsVersionDetail(5);
  console.log(JSON.stringify({
    apiCalls,
    scrollCount: globalThis.__detailScrollCount || 0,
    detailHtml: refs.hotelFactsVersionDetail.innerHTML,
    historyHtml: refs.hotelFactsHistory.innerHTML,
    eventsHtml: refs.hotelFactsEvents.innerHTML,
    hasRevealClass: detailClassNames.has('facts-detail-focus'),
  }));
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
"""
    )

    assert result["apiCalls"] == ["/hotels/21966/facts/versions/5"]
    assert result["scrollCount"] == 1
    assert "v5" in result["detailHtml"]
    assert "Arşiv Sürümü" in result["detailHtml"]
    assert "Açık" in result["historyHtml"]
    assert "Açık" in result["eventsHtml"]
    assert result["hasRevealClass"] is True


def test_admin_panel_renders_draft_save_fact_event_label_and_note() -> None:
    result = _run_admin_panel_script_harness(
        """
refs.hotelFactsEvents = new HTMLElement();
state.hotelFactsVersionDetail = { version: 7 };
renderHotelFactsEvents([
  {
    event_type: 'DRAFT_SAVE',
    version: 7,
    actor: 'ops_admin',
    occurred_at: '2026-04-05T10:00:00Z',
    metadata: { draft_facts_checksum: 'draft-checksum-7', source_profile_checksum: 'source-checksum-7' },
  },
]);
console.log(JSON.stringify({ eventsHtml: refs.hotelFactsEvents.innerHTML }));
"""
    )

    assert "Taslak Kaydedildi" in result["eventsHtml"]
    assert "Taslak checksum: draft-checksum-7" in result["eventsHtml"]
    assert "Taslak kaydetme, yayınlama ve geri alma" in result["eventsHtml"]


def test_admin_panel_history_marks_draft_snapshot_rows() -> None:
    result = _run_admin_panel_script_harness(
        """
refs.hotelFactsHistory = new HTMLElement();
state.hotelFactsVersionDetail = null;
renderHotelFactsHistory([
  {
    version: 9,
    is_current: false,
    entry_type: 'DRAFT_SAVE',
    published_by: 'ops_admin',
    published_at: '2026-04-05T11:00:00Z',
    blocker_count: 0,
    warning_count: 1,
    checksum: 'checksum-v9',
  },
]);
console.log(JSON.stringify({ historyHtml: refs.hotelFactsHistory.innerHTML }));
"""
    )

    assert "Taslak" in result["historyHtml"]
    assert "Son 6 sürüm (taslak kaydı + yayın)" in result["historyHtml"]


def test_admin_panel_version_detail_marks_draft_snapshot_type() -> None:
    result = _run_admin_panel_script_harness(
        """
refs.hotelFactsVersionDetail = new HTMLElement();
renderHotelFactsVersionDetail({
  version: 9,
  is_current: false,
  entry_type: 'DRAFT_SAVE',
  published_by: 'ops_admin',
  published_at: '2026-04-05T11:00:00Z',
  checksum: 'checksum-v9',
  source_profile_checksum: 'source-v9',
  facts: { room_types: [], faq_data: [], transfer_routes: [] },
  validation: { blockers: [], warnings: [] },
});
console.log(JSON.stringify({ detailHtml: refs.hotelFactsVersionDetail.innerHTML }));
"""
    )

    assert "Taslak Sürümü" in result["detailHtml"]
    assert "Tür: Taslak Kaydı" in result["detailHtml"]


def test_admin_panel_faq_section_renders_only_selected_item() -> None:
    result = _run_admin_panel_script_harness(
        """
state.hotelProfileDraft = {
  faq_data: [
    { faq_id: 'faq-1', topic: 'room_service', status: 'ACTIVE', question_tr: 'Oda servisi var mı?', answer_tr: 'Hayır' },
    { faq_id: 'faq-2', topic: 'breakfast', status: 'ACTIVE', question_tr: 'Kahvaltı dahil mi?', answer_tr: 'Evet' },
  ],
};
state.hotelProfileFaqActiveIndex = 1;
console.log(JSON.stringify({
  html: renderHotelProfileFaqSection(),
  activeIndex: getActiveHotelProfileFaqIndex(state.hotelProfileDraft.faq_data),
}));
"""
    )

    assert result["activeIndex"] == 1
    assert "SSS Kaydı Seçimi" in result["html"]
    assert "Toplam SSS: 2" in result["html"]
    assert "Açık kayıt: 2" in result["html"]
    assert "SSS 2" in result["html"]
    assert "Kahvaltı dahil mi?" in result["html"]
    assert "Oda servisi var mı?" not in result["html"]
    assert "Hayır" not in result["html"]


def test_admin_panel_cross_field_validation_adds_local_blockers() -> None:
    result = _run_admin_panel_script_harness(
        """
state.hotelProfileDraft = {
  operational: { min_stay: 5, max_stay: 2 },
  restaurant: { capacity_min: 80, capacity_max: 10, max_ai_party_size: 25 },
  contacts: {
    reception: { name: 'Resepsiyon' },
  },
  location: {
    nearby: [
      { name: 'Ölüdeniz Blue Lagoon' },
    ],
  },
  rate_mapping: {
    ONLY_RATE: { rate_type_id: 10, rate_code_id: 20 },
  },
  cancellation_rules: {
    FREE_CANCEL: { prepayment_immediate: true, prepayment_days_before: 5 },
    NON_REFUNDABLE: { refund: false, refund_after_deadline: true, exception_days_before: 21 },
    EXCEPTION_ONLY: { exception_refund: 'total_minus_1_night' },
  },
  board_types: [
    {},
    { breakfast_hours: '08:00-10:30' },
  ],
  faq_data: [
    {},
    { question_tr: 'Check-in saati kaç?' },
  ],
  room_types: [
    { max_pax: 0, size_m2: 0 },
    { max_pax: 2, size_m2: 24, bed_type: 'double', view: 'garden' },
  ],
  transfer_routes: [
    {
      price_eur: 45,
      max_pax: 3,
      duration_min: 70,
      oversize_vehicle: { min_pax: 3 },
    },
    {
      from_location: 'Dalaman Havalimanı',
      price_eur: 55,
      max_pax: 4,
      duration_min: 80,
    },
  ],
};
const validation = buildHotelFactsDraftValidationState({}, { publishable: true, blockers: [], warnings: [] });
console.log(JSON.stringify({
  publishable: validation.publishable,
  blockerCodes: validation.blockers.map(item => item.code),
  blockerPaths: validation.blockers.map(item => item.path),
}));
"""
    )

    assert result["publishable"] is False
    assert "stay_range_invalid" in result["blockerCodes"]
    assert "restaurant_capacity_range_invalid" in result["blockerCodes"]
    assert "restaurant_ai_party_size_invalid" in result["blockerCodes"]
    assert "contact_channel_missing" in result["blockerCodes"]
    assert "nearby_place_incomplete" in result["blockerCodes"]
    assert "cancellation_prepayment_timing_conflict" in result["blockerCodes"]
    assert "cancellation_refund_conflict" in result["blockerCodes"]
    assert "cancellation_exception_refund_missing" in result["blockerCodes"]
    assert "cancellation_exception_days_missing" in result["blockerCodes"]
    assert "rate_mapping_rule_missing" in result["blockerCodes"]
    assert "cancellation_rule_mapping_missing" in result["blockerCodes"]
    assert "board_type_empty_invalid" in result["blockerCodes"]
    assert "board_type_code_missing" in result["blockerCodes"]
    assert "board_type_name_missing" in result["blockerCodes"]
    assert "faq_entry_empty_invalid" in result["blockerCodes"]
    assert "faq_topic_missing" in result["blockerCodes"]
    assert "faq_answer_missing" in result["blockerCodes"]
    assert "room_name_missing" in result["blockerCodes"]
    assert "room_max_pax_invalid" in result["blockerCodes"]
    assert "room_size_invalid" in result["blockerCodes"]
    assert "transfer_oversize_threshold_invalid" in result["blockerCodes"]
    assert "transfer_to_location_missing" in result["blockerCodes"]
    assert "transfer_vehicle_type_missing" in result["blockerCodes"]
    assert "operational.min_stay" in result["blockerPaths"]
    assert "restaurant.capacity_min" in result["blockerPaths"]
    assert "restaurant.max_ai_party_size" in result["blockerPaths"]
    assert "contacts.reception.phone" in result["blockerPaths"]
    assert "location.nearby[0].distance" in result["blockerPaths"]
    assert "cancellation_rules.FREE_CANCEL.prepayment_days_before" in result["blockerPaths"]
    assert "cancellation_rules.NON_REFUNDABLE.refund_after_deadline" in result["blockerPaths"]
    assert "cancellation_rules.NON_REFUNDABLE.exception_refund" in result["blockerPaths"]
    assert "cancellation_rules.EXCEPTION_ONLY.exception_days_before" in result["blockerPaths"]
    assert "rate_mapping.ONLY_RATE" in result["blockerPaths"]
    assert "cancellation_rules.FREE_CANCEL" in result["blockerPaths"]
    assert "board_types[0].code" in result["blockerPaths"]
    assert "board_types[1].code" in result["blockerPaths"]
    assert "board_types[1].name.tr" in result["blockerPaths"]
    assert "faq_data[0].question_tr" in result["blockerPaths"]
    assert "faq_data[1].topic" in result["blockerPaths"]
    assert "faq_data[1].answer_tr" in result["blockerPaths"]
    assert "room_types[0].max_pax" in result["blockerPaths"]
    assert "room_types[0].size_m2" in result["blockerPaths"]
    assert "room_types[1].name.tr" in result["blockerPaths"]
    assert "transfer_routes[0].oversize_vehicle.min_pax" in result["blockerPaths"]
    assert "transfer_routes[1].to_location" in result["blockerPaths"]
    assert "transfer_routes[1].vehicle_type" in result["blockerPaths"]


def test_admin_panel_numeric_field_range_validation_marks_invalid() -> None:
    result = _run_admin_panel_script_harness(
        """
const classes = new Set();
const field = new HTMLElement();
field.value = '0';
field.dataset.numberKind = 'int';
field.dataset.minValue = '1';
field.dataset.maxValue = '365';
field.classList = {
  add(name) { classes.add(name); },
  remove(name) { classes.delete(name); },
  contains(name) { return classes.has(name); },
  toggle(name, force) {
    if (force) classes.add(name);
    else classes.delete(name);
  },
};
applyProfileFieldFormatting(field);
const invalidAfterLow = classes.has('is-invalid');
field.value = '30';
applyProfileFieldFormatting(field);
const invalidAfterValid = classes.has('is-invalid');
field.value = '500';
applyProfileFieldFormatting(field);
console.log(JSON.stringify({ invalidAfterLow, invalidAfterValid, invalidAfterHigh: classes.has('is-invalid') }));
"""
    )

    assert result["invalidAfterLow"] is True
    assert result["invalidAfterValid"] is False
    assert result["invalidAfterHigh"] is True


def test_admin_panel_standard_mode_hides_faq_id_and_structures_policies() -> None:
    result = _run_admin_panel_script_harness(
        """
state.hotelProfileMode = 'standard';
state.hotelProfileDraft = {
  room_types: [
    { name: { tr: 'Deluxe', en: 'Deluxe' } },
    { name: { tr: 'Superior', en: 'Superior' } },
  ],
  faq_data: [
    {
      faq_id: 'faq-1',
      topic: 'check_in',
      status: 'ACTIVE',
      question_tr: 'Check-in saati kaç?',
      answer_tr: '14:00',
      question_en: 'What time is check-in?',
      answer_en: '14:00',
      question_variants_tr: ['Giriş saati kaç?'],
      question_variants_en: ['When can we check in?'],
    },
  ],
  payment: {
    methods: ['BANK_TRANSFER', 'CASH'],
    reply_tr: 'Nakit ve havale kabul edilir.',
    payment_link_handling: 'human_handoff',
    mail_order_handling: 'human_handoff',
  },
  facility_policies: {
    check_in: { time: '14:00', early_checkin: 'availability_handoff', late_arrival_after: '00:00', late_arrival_contact_required: true },
    check_out: { time: '12:00', late_checkout: 'availability_paid_handoff' },
    pets: { allowed: false, reply_tr: 'Evcil hayvan kabul edilmez.' },
    smoking: { rooms: 'non_smoking', allowed_areas: ['balcony'] },
    parking: { hotel_parking: false, street_parking: 'Cadde parkı' },
    pool: { type: 'open', hours: '08:00-19:00', heated: false, hotel_guest: 'free', external_guest: 'paid_handoff' },
    wifi: { available: true, free: true, hours: '24/7' },
    accessibility: { elevator_available: false, accessible_room_types: ['Deluxe'], reply_tr: 'Giriş katta erişilebilir oda var.' },
    wellness: { spa: false, hamam: false, sauna: false, massage: false, offsite_guidance: 'reception' },
    local_services: {
      pharmacy: { distance: '200 metre', location_tr: 'Arka sokakta', details_handling: 'reception' },
      currency_exchange: { available: true, location: 'reception' },
    },
    laundry: { available: true, hours: '24/7', turnaround: '1_day', drop_off: 'reception', pickup: 'reception', expedited_handling: 'reception', pricing_handling: 'human_handoff' },
    children: { policy: 'Tüm yaşlar kabul edilir', extra_bed: 'Ücretli', baby_crib: 'Ücretsiz' },
  },
  operational: {
    no_show_policy: 'human_handoff',
    early_departure_refund: 'human_handoff',
    response_sla_minutes: 15,
  },
};
state.hotelProfileFaqActiveIndex = 0;
console.log(JSON.stringify({
  faqHtml: renderHotelProfileFaqSection(),
  policiesHtml: renderHotelProfilePoliciesSection(),
}));
"""
    )

    assert "SSS Kimliği" not in result["faqHtml"]
    assert "Temel SSS Bilgisi" in result["faqHtml"]
    assert "Ek diller ve alternatif sorular" in result["faqHtml"]
    assert "Bu bölüm isteğe bağlıdır." in result["faqHtml"]
    assert "Odaya saat kaçta yerleşebiliriz?" in result["faqHtml"]
    assert "When can we get into the room?" in result["faqHtml"]
    assert "Ödeme Yöntemleri" in result["policiesHtml"]
    assert "Misafire Gösterilen Ödeme Bilgisi" in result["policiesHtml"]
    assert "EUR Hesap Bilgileri" in result["policiesHtml"]
    assert "TRY Hesap Bilgileri" in result["policiesHtml"]
    assert "Manuel Onay Gerektiren Talepler" in result["policiesHtml"]
    assert "Giriş / Çıkış" in result["policiesHtml"]
    assert "Tesis Politikaları" not in result["policiesHtml"]
    assert "Erişilebilirlik" in result["policiesHtml"]
    assert "Wellness ve Yerel Hizmetler" in result["policiesHtml"]
    assert "Erişilebilir Oda Tipleri" in result["policiesHtml"]
    assert "Döviz Bozdurma Noktası" in result["policiesHtml"]
    assert "Misafire söylenecek yaklaşık mesafeyi yazın." in result["policiesHtml"]
    assert "Hızlı Servis Talepleri" in result["policiesHtml"]
    assert "Fiyat Bilgisi Talepleri" in result["policiesHtml"]
    assert "Teslim noktası seçin" in result["policiesHtml"]
    assert "1 gün" in result["policiesHtml"]
    assert "Örn: 1_day" not in result["policiesHtml"]
    assert "Çocuk politikası seçin" in result["policiesHtml"]
    assert "Ücretsiz" in result["policiesHtml"]
    assert "İlave yatak yalnızca belirli oda tiplerinde sağlanır." in result["policiesHtml"]
    assert "Evcil hayvan kabul edilmez. Rehber köpek için lütfen önceden bilgi verin." in result["policiesHtml"]
    assert "Odalarda sigara içilmez, yalnızca balkonlarda izin verilir." in result["policiesHtml"]
    assert "Otel önünde sınırlı sayıda ücretsiz park alanı vardır." in result["policiesHtml"]
    assert "Asansör mevcuttur ve giriş katta erişilebilir oda seçeneği bulunur." in result["policiesHtml"]
    assert "Şu anda sistemi kontrol edemiyorum, resepsiyon kısa süre içinde size yardımcı olacak." in result["policiesHtml"]
    assert "Örn: 2" in result["policiesHtml"]
    assert "Örn: 14" in result["policiesHtml"]
    assert "Örn: 18" in result["policiesHtml"]
    assert "Örn: 15" in result["policiesHtml"]
    assert 'data-min-value="1"' in result["policiesHtml"]
    assert 'data-max-value="365"' in result["policiesHtml"]


def test_admin_panel_standard_mode_structures_location_and_restaurant_fields() -> None:
    result = _run_admin_panel_script_harness(
        """
state.hotelProfileMode = 'standard';
state.hotelProfileDraft = {
  location: {
    country: 'Türkiye',
    city: 'Muğla',
    district: 'Fethiye',
    address: 'Ölüdeniz Mahallesi',
    nearby: [
      {name: 'Ölüdeniz Blue Lagoon', distance: '300 metre'},
      {name: 'Teleferik', distance: '1 km'},
    ],
  },
  restaurant: {
    name: 'Lounge',
    concept: 'a_la_carte',
    capacity_min: 10,
    capacity_max: 80,
    area_types: ['outdoor'],
    hours: { breakfast: '08:00-10:30', lunch: '12:00-17:00', dinner: '18:00-22:00' },
    breakfast_hotel_guest: 'free',
    breakfast_external_guest: 'paid',
    lunch_dinner: 'paid',
  },
};
console.log(JSON.stringify({
  contactsHtml: renderHotelProfileContactsSection(),
  restaurantHtml: renderHotelProfileRestaurantSection(),
}));
"""
    )

    assert "Yakındaki Yerler" in result["contactsHtml"]
    assert "Yeni Yakın Nokta" in result["contactsHtml"]
    assert "Yer Adı" in result["contactsHtml"]
    assert "Mesafe / Süre" in result["contactsHtml"]
    assert "JSON dizi biçiminde düzenleyin." not in result["contactsHtml"]
    assert "Servis Alanları" in result["restaurantHtml"]
    assert "Açık alan" in result["restaurantHtml"]
    assert "Kapalı alan" in result["restaurantHtml"]
    assert "Genel Restoran Bilgisi" in result["restaurantHtml"]
    assert "Alan ve Kapasite" in result["restaurantHtml"]
    assert "Kahvaltı ve Ücretlendirme" in result["restaurantHtml"]
    assert "Servis Saatleri" in result["restaurantHtml"]
    assert 'data-min-value="0"' in result["restaurantHtml"]
    assert 'data-max-value="1000"' in result["restaurantHtml"]
    assert "Örn: 80" in result["restaurantHtml"]
    assert "Her satıra bir alan türü girin." not in result["restaurantHtml"]


def test_admin_panel_standard_mode_structures_general_and_room_presets() -> None:
    result = _run_admin_panel_script_harness(
        """
state.hotelProfileMode = 'standard';
state.hotelProfileDraft = {
  hotel_type: 'boutique',
  hotel_name: { tr: 'Kassandra', en: 'Kassandra' },
  timezone: 'Europe/Istanbul',
  currency_base: 'EUR',
  season: { open: '04-20', close: '11-10' },
  description: { tr: 'Açıklama', en: 'Description' },
  highlights: ['beachside', 'family_friendly'],
  room_common: {
    smoking: false,
    connecting_rooms: false,
    balcony: true,
    daily_cleaning: true,
    amenities: ['klima', 'kasa'],
  },
  room_types: [
    {
      id: 1,
      pms_room_type_id: 20,
      name: { tr: 'Deluxe', en: 'Deluxe' },
      max_pax: 2,
      size_m2: 24,
      bed_type: 'king',
      view: 'garden',
      features: ['jacuzzi', 'quiet'],
      extra_bed: false,
      baby_crib: false,
      accessible: false,
      description: { tr: 'Açıklama', en: 'Description' },
    },
  ],
};
console.log(JSON.stringify({
  generalHtml: renderHotelProfileGeneralSection(),
  roomsHtml: renderHotelProfileRoomsSection(),
}));
"""
    )

    assert "Öne Çıkan Başlıklar" in result["generalHtml"]
    assert "Plaja yakın" in result["generalHtml"]
    assert "Aile dostu" in result["generalHtml"]
    assert "Ölüdeniz’e yakın, sakin atmosferli butik otelimiz" in result["generalHtml"]
    assert "Our boutique hotel near Oludeniz" in result["generalHtml"]
    assert "Her satıra bir öne çıkan madde girin." not in result["generalHtml"]
    assert "Oda Olanakları" in result["roomsHtml"]
    assert "Klima" in result["roomsHtml"]
    assert "Kasa" in result["roomsHtml"]
    assert "Öne Çıkan Oda Özellikleri" in result["roomsHtml"]
    assert "Jakuzi" in result["roomsHtml"]
    assert "Sessiz" in result["roomsHtml"]
    assert "Bahçe manzaralı, ferah ve sessiz odamız" in result["roomsHtml"]
    assert "Our spacious and quiet garden-view room" in result["roomsHtml"]
    assert 'data-min-value="1"' in result["roomsHtml"]
    assert "Örn: 24" in result["roomsHtml"]
    assert "Her satıra bir olanak girin." not in result["roomsHtml"]


def test_admin_panel_standard_mode_structures_transfer_fields() -> None:
    result = _run_admin_panel_script_harness(
        """
state.hotelProfileMode = 'standard';
state.hotelProfileDraft = {
  transfer_routes: [
    {
      from_location: 'Dalaman Havalimanı',
      to_location: 'Kassandra Ölüdeniz',
      price_eur: 45,
      vehicle_type: 'Sedan',
      max_pax: 3,
      duration_min: 70,
      baby_seat: true,
      oversize_vehicle: {
        type: 'VIP Minibüs',
        price_eur: 70,
        min_pax: 4,
      },
    },
  ],
};
console.log(JSON.stringify({
  transferHtml: renderHotelProfileTransfersSection(),
}));
"""
    )

    assert "Güzergâh Bilgisi" in result["transferHtml"]
    assert "Standart Araç ve Fiyat" in result["transferHtml"]
    assert "Büyük Araç Seçeneği" in result["transferHtml"]
    assert "Örn: Dalaman Havalimanı" in result["transferHtml"]
    assert "Örn: VIP minibüs" in result["transferHtml"]
    assert "Örn: 45" in result["transferHtml"]
    assert "Örn: 70" in result["transferHtml"]
    assert "Tek yön transfer ücretini EUR cinsinden girin." in result["transferHtml"]
    assert "Bu araçta rahat seyahat eden en yüksek kişi sayısını yazın." in result["transferHtml"]
    assert 'data-max-value="10000"' in result["transferHtml"]
    assert 'data-max-value="50"' in result["transferHtml"]
    assert "Güzergâh Kodu" not in result["transferHtml"]


def test_admin_panel_standard_mode_structures_contact_role_and_faq_topic() -> None:
    result = _run_admin_panel_script_harness(
        """
state.hotelProfileMode = 'standard';
state.hotelProfileDraft = {
  contacts: {
    reception: {
      name: 'Ön Büro',
      role: 'RECEPTION',
      phone: '+90 555 000 00 00',
      email: 'frontdesk@example.com',
      hours: '24/7',
    },
  },
  faq_data: [
    {
      faq_id: 'faq-1',
      topic: 'check_in_time',
      status: 'ACTIVE',
      question_tr: 'Check-in saati kaç?',
      answer_tr: '14:00',
    },
  ],
};
state.hotelProfileFaqActiveIndex = 0;
console.log(JSON.stringify({
  contactsHtml: renderHotelProfileContactsSection(),
  faqHtml: renderHotelProfileFaqSection(),
}));
"""
    )

    assert "Resepsiyon Ekle" in result["contactsHtml"]
    assert "Restoran Ekle" in result["contactsHtml"]
    assert "Kat Hizmetleri Ekle" in result["contactsHtml"]
    assert "Yönetici Ekle" in result["contactsHtml"]
    assert "İletişim Türü" in result["contactsHtml"]
    assert "Resepsiyon" in result["contactsHtml"]
    assert "<label>Rol</label>" not in result["contactsHtml"]
    assert "Kategori" in result["faqHtml"]
    assert "Check-in saati" in result["faqHtml"]
    assert "Örn: Check-in saati kaç?" in result["faqHtml"]
    assert "Örn: Standart check-in saatimiz 14:00 itibarıyladır." in result["faqHtml"]
    assert "E.g. What time is check-in?" in result["faqHtml"]
    assert "Örn: check_in_time" not in result["faqHtml"]


def test_admin_panel_multi_checkbox_preserves_hidden_custom_values() -> None:
    result = _run_admin_panel_script_harness(
        """
refs.hotelProfileEditor = { value: '', classList: { add() {}, remove() {}, contains() { return false; } } };
state.hotelProfileMode = 'standard';
state.hotelFactsStatus = null;
state.hotelProfileDraft = {
  highlights: ['beachside', 'custom_spa'],
};
state.hotelProfileLoadedDraftSnapshot = JSON.stringify(state.hotelProfileDraft);
const field = new HTMLElement();
field.dataset.profileMultiField = 'highlights';
field.dataset.profileMultiValue = 'family_friendly';
field.dataset.profileMultiKnownValues = JSON.stringify(['beachside', 'central_location', 'excellent_reviews', 'pool_jacuzzi', 'family_friendly', 'regional_breakfast']);
field.checked = true;
onHotelProfileSectionChange({ target: field });
console.log(JSON.stringify({
  highlights: state.hotelProfileDraft.highlights,
}));
"""
    )

    assert result["highlights"] == ["custom_spa", "beachside", "family_friendly"]


def test_admin_panel_select_field_preserves_hidden_custom_value() -> None:
    result = _run_admin_panel_script_harness(
        """
console.log(JSON.stringify({
  html: renderSelectField('Kategori', 'faq_data[0].topic', 'custom_topic', FAQ_TOPIC_OPTIONS, {help: 'Konu seçin.'}),
}));
"""
    )

    assert "Custom Topic" in result["html"]
    assert "Teknik modda tanımlanmış özel değer korunur." in result["html"]


def test_admin_panel_contact_preset_adds_unique_contact_entry() -> None:
    result = _run_admin_panel_script_harness(
        """
refs.hotelProfileEditor = { value: '', classList: { add() {}, remove() {}, contains() { return false; } } };
state.hotelProfileDraft = {
  contacts: {
    reception: { name: 'Resepsiyon', role: 'RECEPTION', phone: '', email: '', hours: '' },
  },
};
const nextKey = addContactPresetToDraft('RECEPTION');
console.log(JSON.stringify({
  nextKey,
  contacts: state.hotelProfileDraft.contacts,
}));
"""
    )

    assert result["nextKey"] == "reception_2"
    assert result["contacts"]["reception_2"]["role"] == "RECEPTION"
    assert result["contacts"]["reception_2"]["name"] == "Resepsiyon"


def test_admin_panel_standard_mode_renders_cancellation_rule_numeric_guidance() -> None:
    result = _run_admin_panel_script_harness(
        """
state.hotelProfileMode = 'standard';
state.hotelProfileDraft = {
  board_types: [
    {
      code: 'BB',
      name: { tr: 'Oda + Kahvaltı', en: 'Bed & Breakfast' },
      breakfast_hours: '08:00-10:30',
      breakfast_type: 'acik_buyfe',
    },
  ],
  cancellation_rules: {
    FREE_CANCEL: {
      free_cancel_deadline_days: 5,
      prepayment_days_before: 7,
      prepayment_amount: '1_night',
      exception_days_before: 21,
    },
  },
};
console.log(JSON.stringify({
  html: renderHotelProfilePricingSection(),
}));
"""
    )

    assert 'placeholder="Örn: 5"' in result["html"]
    assert 'placeholder="Örn: 7"' in result["html"]
    assert 'placeholder="Örn: 21"' in result["html"]
    assert 'data-min-value="0"' in result["html"]
    assert 'data-max-value="365"' in result["html"]
    assert 'Kural Anahtarı' not in result["html"]


def test_admin_panel_standard_mode_renders_pricing_preset_actions() -> None:
    result = _run_admin_panel_script_harness(
        """
state.hotelProfileMode = 'standard';
state.hotelProfileDraft = {
  board_types: [],
  cancellation_rules: {},
};
console.log(JSON.stringify({
  html: renderHotelProfilePricingSection(),
}));
"""
    )

    assert "Sadece Oda" in result["html"]
    assert "Oda + Kahvaltı" in result["html"]
    assert "Yarım Pansiyon" in result["html"]
    assert "Ücretsiz İptal" in result["html"]
    assert "İadesiz Rezervasyon" in result["html"]
    assert "Yeni Pansiyon Türü" not in result["html"]
    assert "Yeni Kural" not in result["html"]


def test_admin_panel_standard_mode_shows_rate_mapping_summary_without_ids() -> None:
    result = _run_admin_panel_script_harness(
        """
state.hotelProfileMode = 'standard';
state.hotelProfileDraft = {
  board_types: [],
  rate_mapping: {
    FREE_CANCEL: { rate_type_id: 24178, rate_code_id: 183666 },
    NON_REFUNDABLE: { rate_type_id: 0, rate_code_id: 0 },
  },
  cancellation_rules: {
    FREE_CANCEL: { refund: true },
    NON_REFUNDABLE: { refund: false },
  },
};
console.log(JSON.stringify({
  html: renderHotelProfilePricingSection(),
}));
"""
    )

    assert "Rezervasyon Sistemi Eşleştirmeleri" in result["html"]
    assert "Önce misafire sunulan pansiyon paketini ekleyin, ardından uygun iptal kuralını seçin." in result["html"]
    assert "Hazır: 1" in result["html"]
    assert "Bekleyen: 1" in result["html"]
    assert "Ücretsiz iptal" in result["html"]
    assert "İadesiz rezervasyon" in result["html"]
    assert "Teknik eşleştirme bekleniyor" in result["html"]
    assert "Fiyat Türü Kimliği" not in result["html"]
    assert "Fiyat Kodu Kimliği" not in result["html"]
    assert 'data-profile-add-map-entry="rate_mapping"' not in result["html"]


def test_admin_panel_standard_mode_board_card_shows_cancellation_guidance() -> None:
    result = _run_admin_panel_script_harness(
        """
state.hotelProfileMode = 'standard';
state.hotelProfileDraft = {
  board_types: [
    {
      code: 'BB',
      name: { tr: 'Oda + Kahvaltı', en: 'Bed & Breakfast' },
      breakfast_hours: '08:00-10:30',
      breakfast_type: 'acik_buyfe',
    },
  ],
  cancellation_rules: {
    FREE_CANCEL: { refund: true },
  },
};
console.log(JSON.stringify({
  html: renderBoardTypeCard(state.hotelProfileDraft.board_types[0], 0),
}));
"""
    )

    assert "İptal Kuralı İpucu" in result["html"]
    assert "Oda + Kahvaltı için ücretsiz iptal kuralı hazır." in result["html"]
    assert "Ücretsiz İptal hazır" in result["html"]
    assert "İadesiz Rezervasyon yok" in result["html"]


def test_admin_panel_board_type_preset_adds_prefilled_entry() -> None:
    result = _run_admin_panel_script_harness(
        """
refs.hotelProfileEditor = { value: '', classList: { add() {}, remove() {}, contains() { return false; } } };
state.hotelProfileDraft = {
  board_types: [],
};
const nextIndex = addBoardTypePresetToDraft('BB');
console.log(JSON.stringify({
  nextIndex,
  boardTypes: state.hotelProfileDraft.board_types,
}));
"""
    )

    assert result["nextIndex"] == 0
    assert result["boardTypes"][0]["code"] == "BB"
    assert result["boardTypes"][0]["name"]["tr"] == "Oda + Kahvaltı"
    assert result["boardTypes"][0]["name"]["en"] == "Bed & Breakfast"
    assert result["boardTypes"][0]["breakfast_hours"] == "08:00-10:30"
    assert result["boardTypes"][0]["breakfast_type"] == "acik_buyfe"


def test_admin_panel_cancellation_rule_preset_adds_unique_rule_entry() -> None:
    result = _run_admin_panel_script_harness(
        """
refs.hotelProfileEditor = { value: '', classList: { add() {}, remove() {}, contains() { return false; } } };
state.hotelProfileDraft = {
  rate_mapping: {},
  cancellation_rules: {
    FREE_CANCEL: { free_cancel_deadline_days: 3 },
  },
};
const nextKey = addCancellationRulePresetToDraft('FREE_CANCEL');
console.log(JSON.stringify({
  nextKey,
  rules: state.hotelProfileDraft.cancellation_rules,
  mappings: state.hotelProfileDraft.rate_mapping,
  label: formatCancellationRuleKeyLabel(nextKey),
}));
"""
    )

    assert result["nextKey"] == "FREE_CANCEL_2"
    assert result["rules"]["FREE_CANCEL_2"]["free_cancel_deadline_days"] == 5
    assert result["rules"]["FREE_CANCEL_2"]["prepayment_days_before"] == 7
    assert result["rules"]["FREE_CANCEL_2"]["prepayment_amount"] == "1_night"
    assert result["rules"]["FREE_CANCEL_2"]["refund"] is True
    assert result["mappings"]["FREE_CANCEL_2"] == {"rate_type_id": 0, "rate_code_id": 0}
    assert result["label"] == "Ücretsiz iptal 2"


def test_admin_panel_standard_mode_removes_rate_mapping_when_rule_is_deleted() -> None:
    result = _run_admin_panel_script_harness(
        """
syncHotelProfileEditorFromDraft = () => {};
renderHotelProfileWorkspace = () => {};
scheduleHotelFactsDraftValidation = () => {};
state.hotelProfileMode = 'standard';
state.hotelProfileDraft = {
  cancellation_rules: {
    FREE_CANCEL: { refund: true },
    NON_REFUNDABLE: { refund: false },
  },
  rate_mapping: {
    FREE_CANCEL: { rate_type_id: 24178, rate_code_id: 183666 },
    NON_REFUNDABLE: { rate_type_id: 24171, rate_code_id: 183666 },
  },
};
const removeButton = {
  dataset: { profileRemoveMapEntry: 'cancellation_rules', profileMapKeyValue: 'NON_REFUNDABLE' },
};
onHotelProfileSectionClick({
  target: {
    closest(selector) {
      return selector === '[data-profile-remove-map-entry]' ? removeButton : null;
    },
  },
});
console.log(JSON.stringify({
  rules: state.hotelProfileDraft.cancellation_rules,
  mappings: state.hotelProfileDraft.rate_mapping,
}));
"""
    )

    assert "NON_REFUNDABLE" not in result["rules"]
    assert "NON_REFUNDABLE" not in result["mappings"]
    assert "FREE_CANCEL" in result["rules"]
    assert "FREE_CANCEL" in result["mappings"]


def test_admin_panel_rename_cancellation_rule_key_syncs_rate_mapping() -> None:
    result = _run_admin_panel_script_harness(
        """
syncHotelProfileEditorFromDraft = () => {};
renderHotelProfileWorkspace = () => {};
scheduleHotelFactsDraftValidation = () => {};
state.hotelProfileDraft = {
  cancellation_rules: {
    FREE_CANCEL: { refund: true },
  },
  rate_mapping: {
    FREE_CANCEL: { rate_type_id: 24178, rate_code_id: 183666 },
  },
};
const field = {
  dataset: { profileMapKey: 'cancellation_rules', profileMapOldKey: 'FREE_CANCEL' },
  value: 'FREE_FLEX',
};
renameDraftMapKey(field);
console.log(JSON.stringify({
  fieldValue: field.value,
  rules: state.hotelProfileDraft.cancellation_rules,
  mappings: state.hotelProfileDraft.rate_mapping,
}));
"""
    )

    assert result["fieldValue"] == "FREE_FLEX"
    assert "FREE_CANCEL" not in result["rules"]
    assert "FREE_CANCEL" not in result["mappings"]
    assert result["rules"]["FREE_FLEX"] == {"refund": True}
    assert result["mappings"]["FREE_FLEX"] == {"rate_type_id": 24178, "rate_code_id": 183666}


def test_admin_panel_rename_rate_mapping_key_blocks_when_linked_key_conflicts() -> None:
    result = _run_admin_panel_script_harness(
        """
const notices = [];
notify = (message, level) => notices.push({ message, level });
syncHotelProfileEditorFromDraft = () => {};
renderHotelProfileWorkspace = () => {};
scheduleHotelFactsDraftValidation = () => {};
state.hotelProfileDraft = {
  cancellation_rules: {
    FREE_CANCEL: { refund: true },
    NON_REFUNDABLE: { refund: false },
  },
  rate_mapping: {
    FREE_CANCEL: { rate_type_id: 24178, rate_code_id: 183666 },
  },
};
const field = {
  dataset: { profileMapKey: 'rate_mapping', profileMapOldKey: 'FREE_CANCEL' },
  value: 'NON_REFUNDABLE',
};
renameDraftMapKey(field);
console.log(JSON.stringify({
  fieldValue: field.value,
  notices,
  rules: state.hotelProfileDraft.cancellation_rules,
  mappings: state.hotelProfileDraft.rate_mapping,
}));
"""
    )

    assert result["fieldValue"] == "FREE_CANCEL"
    assert result["notices"] == [{"message": "Bağlı teknik anahtar zaten kullanılıyor.", "level": "warn"}]
    assert "FREE_CANCEL" in result["rules"]
    assert "NON_REFUNDABLE" in result["rules"]
    assert "FREE_CANCEL" in result["mappings"]
    assert "NON_REFUNDABLE" not in result["mappings"]


def test_admin_panel_technical_mode_add_rate_mapping_creates_linked_cancellation_rule() -> None:
    result = _run_admin_panel_script_harness(
        """
syncHotelProfileEditorFromDraft = () => {};
renderHotelProfileWorkspace = () => {};
scheduleHotelFactsDraftValidation = () => {};
state.hotelProfileMode = 'technical';
state.hotelProfileDraft = {
  cancellation_rules: {},
  rate_mapping: {},
};
const addButton = {
  dataset: { profileAddMapEntry: 'rate_mapping' },
};
onHotelProfileSectionClick({
  target: {
    closest(selector) {
      return selector === '[data-profile-add-map-entry]' ? addButton : null;
    },
  },
});
console.log(JSON.stringify({
  rules: state.hotelProfileDraft.cancellation_rules,
  mappings: state.hotelProfileDraft.rate_mapping,
}));
"""
    )

    assert result["mappings"]["new_rate_1"] == {"rate_type_id": 0, "rate_code_id": 0}
    assert result["rules"]["new_rate_1"] == {
        "free_cancel_deadline_days": None,
        "prepayment_days_before": None,
        "prepayment_amount": "1_night",
        "prepayment_immediate": False,
        "refund": True,
        "refund_after_deadline": False,
        "exception_days_before": None,
        "exception_refund": "",
    }


def test_admin_panel_technical_mode_add_cancellation_rule_creates_linked_rate_mapping() -> None:
    result = _run_admin_panel_script_harness(
        """
syncHotelProfileEditorFromDraft = () => {};
renderHotelProfileWorkspace = () => {};
scheduleHotelFactsDraftValidation = () => {};
state.hotelProfileMode = 'technical';
state.hotelProfileDraft = {
  cancellation_rules: {},
  rate_mapping: {},
};
const addButton = {
  dataset: { profileAddMapEntry: 'cancellation_rules' },
};
onHotelProfileSectionClick({
  target: {
    closest(selector) {
      return selector === '[data-profile-add-map-entry]' ? addButton : null;
    },
  },
});
console.log(JSON.stringify({
  rules: state.hotelProfileDraft.cancellation_rules,
  mappings: state.hotelProfileDraft.rate_mapping,
}));
"""
    )

    assert result["rules"]["new_rule_1"] == {
        "free_cancel_deadline_days": None,
        "prepayment_days_before": None,
        "prepayment_amount": "1_night",
        "prepayment_immediate": False,
        "refund": True,
        "refund_after_deadline": False,
        "exception_days_before": None,
        "exception_refund": "",
    }
    assert result["mappings"]["new_rule_1"] == {"rate_type_id": 0, "rate_code_id": 0}


def test_admin_panel_technical_mode_pricing_cards_show_linked_status_help() -> None:
    result = _run_admin_panel_script_harness(
        """
state.hotelProfileMode = 'technical';
state.hotelProfileDraft = {
  cancellation_rules: {
    FREE_CANCEL: { refund: true },
  },
  rate_mapping: {
    FREE_CANCEL: { rate_type_id: 24178, rate_code_id: 183666 },
  },
};
console.log(JSON.stringify({
  rateHtml: renderRateMappingCard('FREE_CANCEL', state.hotelProfileDraft.rate_mapping.FREE_CANCEL, 0),
  ruleHtml: renderCancellationRuleCard('FREE_CANCEL', state.hotelProfileDraft.cancellation_rules.FREE_CANCEL, 0),
}));
"""
    )

    assert "Bağlı İptal Kuralı" in result["rateHtml"]
    assert "Ücretsiz iptal için teknik eşleştirme düzenleniyor." in result["rateHtml"]
    assert "Bağlı kural hazır" in result["rateHtml"]
    assert "Kimlikler girildi" in result["rateHtml"]
    assert "PMS tarafındaki fiyat türü kimliğini girin." in result["rateHtml"]
    assert "Örn: 24178" in result["rateHtml"]
    assert "Örn: 183666" in result["rateHtml"]
    assert "Bağlı Teknik Eşleştirme" in result["ruleHtml"]
    assert "Bu kural için bağlı fiyat eşleştirmesi hazır. Kimlikler tamamlanmadıysa yayın öncesi blocker oluşur." in result["ruleHtml"]
    assert "Bağlı eşleştirme hazır" in result["ruleHtml"]
    assert "Kimlikler girildi" in result["ruleHtml"]


def test_admin_panel_technical_mode_rate_mapping_warns_when_pms_ids_are_missing() -> None:
    result = _run_admin_panel_script_harness(
        """
state.hotelProfileMode = 'technical';
state.hotelProfileDraft = {
  cancellation_rules: {
    FREE_CANCEL: { refund: true },
  },
  rate_mapping: {
    FREE_CANCEL: { rate_type_id: 0, rate_code_id: 0 },
  },
};
console.log(JSON.stringify({
  rateHtml: renderRateMappingCard('FREE_CANCEL', state.hotelProfileDraft.rate_mapping.FREE_CANCEL, 0),
}));
"""
    )

    assert "Kimlikler bekleniyor" in result["rateHtml"]
    assert "Kimlikler girilmezse yayın öncesi blocker oluşur." in result["rateHtml"]


def test_admin_panel_standard_mode_renders_room_type_preset_actions() -> None:
    result = _run_admin_panel_script_harness(
        """
state.hotelProfileMode = 'standard';
state.hotelProfileDraft = {
  room_common: {},
  room_types: [],
};
console.log(JSON.stringify({
  html: renderHotelProfileRoomsSection(),
}));
"""
    )

    assert "Standart Oda" in result["html"]
    assert "Superior Oda" in result["html"]
    assert "Aile Odası" in result["html"]
    assert "Suit" in result["html"]
    assert "Yeni Oda Tipi" not in result["html"]


def test_admin_panel_room_type_preset_adds_prefilled_entry() -> None:
    result = _run_admin_panel_script_harness(
        """
refs.hotelProfileEditor = { value: '', classList: { add() {}, remove() {}, contains() { return false; } } };
state.hotelProfileDraft = {
  room_types: [],
};
const nextIndex = addRoomTypePresetToDraft('FAMILY');
console.log(JSON.stringify({
  nextIndex,
  roomTypes: state.hotelProfileDraft.room_types,
}));
"""
    )

    assert result["nextIndex"] == 0
    assert result["roomTypes"][0]["name"]["tr"] == "Aile Odası"
    assert result["roomTypes"][0]["name"]["en"] == "Family Room"
    assert result["roomTypes"][0]["max_pax"] == 4
    assert result["roomTypes"][0]["size_m2"] == 35
    assert result["roomTypes"][0]["bed_type"] == "king"
    assert result["roomTypes"][0]["view"] == "garden"
    assert result["roomTypes"][0]["features"] == ["spacious"]
    assert result["roomTypes"][0]["extra_bed"] is True
    assert result["roomTypes"][0]["baby_crib"] is True
    assert result["roomTypes"][0]["description"] == {"tr": "", "en": ""}


def test_admin_panel_standard_mode_renders_formatted_time_fields() -> None:
    result = _run_admin_panel_script_harness(
        """
state.hotelProfileMode = 'standard';
state.hotelProfileDraft = {
  season: { open: '04-20', close: '11-10' },
  contacts: {
    reception: { name: 'Resepsiyon', role: 'RECEPTION', phone: '', email: '', hours: '08:00-23:00' },
  },
  restaurant: {
    name: 'Lounge',
    concept: 'a_la_carte',
    capacity_min: 10,
    capacity_max: 80,
    area_types: ['outdoor'],
    hours: { breakfast: '08:00-10:30', lunch: '12:00-17:00', dinner: '18:00-22:00' },
    breakfast_hotel_guest: 'free',
    breakfast_external_guest: 'paid',
    lunch_dinner: 'paid',
  },
  facility_policies: {
    check_in: { time: '14:00', late_arrival_after: '00:00' },
    check_out: { time: '12:00' },
    pool: { hours: '08:00-19:00' },
    wifi: { hours: '24/7' },
    laundry: { hours: '09:00-18:00' },
  },
};
console.log(JSON.stringify({
  generalHtml: renderHotelProfileGeneralSection(),
  contactsHtml: renderHotelProfileContactsSection(),
  restaurantHtml: renderHotelProfileRestaurantSection(),
  policiesHtml: renderHotelProfilePoliciesSection(),
}));
"""
    )

    assert 'data-profile-format="month-day"' in result["generalHtml"]
    assert 'data-profile-format="time-range-flex"' in result["contactsHtml"]
    assert 'data-profile-format="time-range"' in result["restaurantHtml"]
    assert 'data-profile-format="time"' in result["policiesHtml"]


def test_admin_panel_format_helpers_normalize_date_and_time_values() -> None:
    result = _run_admin_panel_script_harness(
        """
console.log(JSON.stringify({
  season: normalizeProfileFormattedValue('month-day', '0420'),
  checkin: normalizeProfileFormattedValue('time', '1400'),
  breakfast: normalizeProfileFormattedValue('time-range', '08001030'),
  alwaysOn: normalizeProfileFormattedValue('time-range-flex', '24/7'),
  breakfastValid: isProfileFormattedValueValid('time-range', '08:00-10:30'),
  seasonValid: isProfileFormattedValueValid('month-day', '04-20'),
}));
"""
    )

    assert result["season"] == "04-20"
    assert result["checkin"] == "14:00"
    assert result["breakfast"] == "08:00-10:30"
    assert result["alwaysOn"] == "24/7"
    assert result["breakfastValid"] is True
    assert result["seasonValid"] is True


def test_chat_lab_guest_context_exposes_reservation_actions() -> None:
    assert "guest_info" in TEST_CHAT_SCRIPT
    assert "data-guest-action=\"approve\"" in TEST_CHAT_SCRIPT
    assert "data-guest-action=\"cancel\"" in TEST_CHAT_SCRIPT
    assert "Rezervasyon Onayla" in TEST_CHAT_SCRIPT
    assert "Rezervasyon İptal Et" in TEST_CHAT_SCRIPT
    assert "/api/v1/admin/holds/" in TEST_CHAT_SCRIPT
    assert "/cancel-reservation" in TEST_CHAT_SCRIPT
