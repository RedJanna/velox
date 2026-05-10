"""Static assets for the admin operations panel."""

# ruff: noqa: E501

from velox.api.routes.admin_panel_ui_tail_assets import ADMIN_PANEL_TAIL_SCRIPT
from velox.api.routes.ui_shared_assets import UI_SHARED_SCRIPT

ADMIN_PANEL_STYLE = """\
*,*::before,*::after{box-sizing:border-box}
:root{
  --bg:#f4f6fb;--bg-2:#e8edf7;--surface:#ffffff;--surface-2:#f7f9fc;--ink:#102033;--muted:#5d6877;
  --line:rgba(16,32,51,.12);--line-strong:rgba(16,32,51,.2);--accent:#192F9A;--accent-2:#2850d9;
  --whatsapp:#128c7e;--ai:#4c1d95;--handoff:#d97706;--warn:#b45309;--danger:#b42318;--danger-2:#7f1d1d;--ok:#166534;--gold:#bb8a2a;--shadow:0 18px 42px rgba(16,32,51,.08);
  --sidebar-bg:#102033;--sidebar-bg-2:#142842;--sidebar-muted:rgba(239,246,255,.72);--sidebar-line:rgba(239,246,255,.12);
  --radius-lg:26px;--radius-md:18px;--radius-sm:12px;--mono:'Cascadia Code','Fira Code',monospace;
  --sans:'Manrope','Segoe UI Variable','Aptos','Segoe UI',system-ui,sans-serif;--serif:'Fraunces','Iowan Old Style','Georgia',serif;
}
html,body{min-height:100%;margin:0;background:
  linear-gradient(180deg,var(--bg) 0%,var(--bg-2) 100%);
  color:var(--ink);font-family:var(--sans)}
body{padding:18px}
button,input,select,textarea{font:inherit}
[hidden]{display:none!important}
.shell{display:grid;grid-template-columns:280px minmax(0,1fr);gap:18px;min-height:calc(100vh - 36px)}
.shell.is-sidebar-collapsed{grid-template-columns:72px minmax(0,1fr)}
.shell:has(> .sidebar[hidden]){grid-template-columns:1fr}
.sidebar{background:var(--sidebar-bg);color:#eff6ff;border-radius:30px;padding:24px;display:flex;flex-direction:column;gap:18px;box-shadow:var(--shadow);min-width:0;transition:width .18s ease,padding .18s ease}
.brand{display:flex;align-items:flex-start;gap:14px}
.brand-mark{width:46px;height:46px;border-radius:16px;background:#e7bf5f;display:grid;place-items:center;color:#4c3506;font-weight:900;letter-spacing:.06em;flex:0 0 auto}
.brand h1{margin:0;font-family:var(--serif);font-size:22px;line-height:1.05}
.brand p{margin:6px 0 0;color:rgba(239,246,255,.72);font-size:13px;line-height:1.45}
.sidebar-collapse-toggle{min-height:40px;border:1px solid var(--sidebar-line);border-radius:14px;background:rgba(255,255,255,.06);color:#eff6ff;padding:9px 10px;display:flex;align-items:center;justify-content:center;gap:8px;font-size:12px;font-weight:800;cursor:pointer;transition:.18s background ease,.18s border-color ease}
.sidebar-collapse-toggle:hover{background:rgba(255,255,255,.1)}
.sidebar-collapse-toggle span{font-size:18px;line-height:1}
.nav{display:flex;flex-direction:column;gap:20px;overflow-y:auto;scrollbar-width:thin;min-height:0}
.nav-group{display:flex;flex-direction:column;gap:6px}
.nav-group-label{padding:0 12px;font-size:11px;font-weight:800;letter-spacing:.04em;text-transform:uppercase;color:var(--sidebar-muted)}
.nav button{position:relative;min-height:44px;border:none;background:transparent;color:#dbeafe;padding:0 12px;border-radius:10px;text-align:left;display:grid;grid-template-columns:24px minmax(0,1fr) auto;align-items:center;gap:10px;cursor:pointer;transition:.18s background ease,.18s color ease}
.nav button:hover{background:rgba(255,255,255,.08);color:#fff}
.nav button.is-active{background:rgba(255,255,255,.12);color:#fff;font-weight:800}
.nav button.is-active::before{content:"";position:absolute;left:0;top:50%;width:2px;height:22px;border-radius:999px;background:var(--accent);transform:translateY(-50%)}
.nav button.is-active .nav-label{font-weight:800}
.nav button.is-active .nav-icon{background:rgba(15,118,110,.35);color:#fff}
.nav-icon{width:24px;height:24px;border-radius:8px;display:grid;place-items:center;color:#eff6ff;background:rgba(255,255,255,.08);font-size:10px;font-weight:900;letter-spacing:0}
.nav-copy{display:flex;flex-direction:column;gap:2px;min-width:0}
.nav-label{font-size:14px;font-weight:700;line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.nav-subtitle{font-size:12px;line-height:1.25;color:var(--sidebar-muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.nav-badge{min-width:24px;height:22px;border-radius:999px;background:#fff2dd;color:#92400e;display:inline-flex;align-items:center;justify-content:center;padding:0 7px;font-size:11px;font-weight:900}
.nav-empty{padding:10px 12px;color:var(--sidebar-muted);font-size:13px;line-height:1.4}
.sidebar.is-collapsed{padding:16px 10px;align-items:center;gap:14px}
.sidebar.is-collapsed .brand{justify-content:center}
.sidebar.is-collapsed .brand > div:not(.brand-mark),.sidebar.is-collapsed .sidebar-card,.sidebar.is-collapsed .sidebar-actions,.sidebar.is-collapsed .sidebar-collapse-toggle strong,.sidebar.is-collapsed .nav-group-label,.sidebar.is-collapsed .nav-copy,.sidebar.is-collapsed .nav-badge{display:none}
.sidebar.is-collapsed .brand-mark{width:44px;height:44px;border-radius:14px}
.sidebar.is-collapsed .sidebar-collapse-toggle{width:44px;height:40px;padding:0}
.sidebar.is-collapsed .sidebar-collapse-toggle span{transform:rotate(180deg)}
.sidebar.is-collapsed .nav{width:100%;overflow:visible}
.sidebar.is-collapsed .nav-group{align-items:center;gap:6px}
.sidebar.is-collapsed .nav button{width:44px;min-width:44px;height:44px;padding:0;display:flex;align-items:center;justify-content:center}
.sidebar.is-collapsed .nav button::after{content:attr(data-tooltip);position:absolute;left:calc(100% + 10px);top:50%;transform:translateY(-50%);z-index:90;min-width:max-content;max-width:220px;padding:7px 9px;border-radius:8px;background:#0b1220;color:#fff;font-size:12px;font-weight:800;box-shadow:0 10px 24px rgba(16,32,51,.18);opacity:0;pointer-events:none;transition:.14s opacity ease}
.sidebar.is-collapsed .nav button:hover::after,.sidebar.is-collapsed .nav button:focus-visible::after{opacity:1}
.sidebar-overlay{position:fixed;inset:0;background:rgba(16,32,51,.42);z-index:65}
.breadcrumb{margin-bottom:8px;color:var(--muted);font-size:12px;font-weight:800;letter-spacing:.04em;text-transform:uppercase}
.sidebar-card{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.08);border-radius:20px;padding:16px}
.sidebar-card h2{margin:0 0 8px;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:rgba(239,246,255,.72)}
.sidebar-card p,.sidebar-card label,.sidebar-card small{color:rgba(239,246,255,.72)}
.sidebar-select,.sidebar-button,.field input,.field select,.field textarea,.toolbar button,.inline-button{
  border:1px solid var(--line);border-radius:14px;background:var(--surface);color:var(--ink);transition:border-color .18s ease,box-shadow .18s ease
}
.sidebar-select{width:100%;padding:11px 12px;background:rgba(255,255,255,.94)}
.sidebar-select:focus,.field input:focus,.field select:focus,.field textarea:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px rgba(15,118,110,.12)}
.sidebar-actions{display:flex;flex-direction:column;gap:10px}
.sidebar-button,.toolbar button,.inline-button,.action-button{border:none;padding:11px 14px;border-radius:14px;font-weight:700;cursor:pointer}
.sidebar-button.secondary,.toolbar button.secondary,.inline-button.secondary{background:rgba(255,255,255,.08);color:#fff;border:1px solid rgba(255,255,255,.1)}
.sidebar-button.primary,.toolbar button.primary,.inline-button.primary,.action-button.primary{background:linear-gradient(135deg,var(--accent),var(--accent-2));color:#fff}
.sidebar-button.warn,.action-button.warn{background:#fff4db;color:#7c4b06}
.sidebar-button.danger,.action-button.danger,.inline-button.danger{background:#fde7e5;color:var(--danger)}
.action-button.secondary{background:#eef2f7;color:#334155;border:1px solid var(--line)}
.action-button.secondary.is-active{background:linear-gradient(135deg,#102033,#1f3554);color:#fff;border-color:#102033}
.action-button:disabled{opacity:.55;cursor:not-allowed}
.workspace{display:flex;flex-direction:column;gap:18px;min-width:0}
.topbar{background:rgba(255,253,248,.9);border-radius:30px;padding:22px 26px;box-shadow:var(--shadow);display:flex;align-items:flex-start;justify-content:space-between;gap:18px;backdrop-filter:blur(18px)}
.topbar h2{margin:0;font-family:var(--serif);font-size:30px;line-height:1}
.topbar p{margin:8px 0 0;color:var(--muted);max-width:760px;line-height:1.55}
.topbar-actions{display:flex;align-items:flex-start;gap:10px}
.topbar-aside{display:flex;flex-wrap:wrap;gap:10px;justify-content:flex-end}
.sidebar-toggle{display:none;border:none;border-radius:12px;padding:10px 14px;background:#13253e;color:#fff;font-weight:800;cursor:pointer}
.sidebar-toggle:focus-visible,.sidebar-collapse-toggle:focus-visible,.nav button:focus-visible,.sidebar-button:focus-visible,.toolbar button:focus-visible,.inline-button:focus-visible,.action-button:focus-visible{
  outline:2px solid rgba(187,138,42,.9);outline-offset:2px
}
.badge{display:inline-flex;align-items:center;gap:8px;padding:8px 12px;border-radius:999px;font-size:12px;font-weight:800;letter-spacing:.03em}
.badge.info{background:#e8eefc;color:#192F9A}.badge.whatsapp{background:#e7f7ef;color:#0f6f5f}.badge.ai{background:#eee9ff;color:#4c1d95}.badge.warn{background:#fff2dd;color:#92400e}.badge.danger{background:#fde7e5;color:#991b1b}.badge.dark{background:#13253e;color:#fff}
.toast{position:fixed;top:24px;right:24px;min-width:260px;max-width:420px;padding:14px 16px;border-radius:18px;box-shadow:var(--shadow);z-index:60;background:#102033;color:#fff;opacity:0;pointer-events:none;transform:translateY(-8px);transition:.18s ease}
.toast.is-visible{opacity:1;pointer-events:auto;transform:none}
.toast.info{background:#102033}.toast.success{background:#115e59}.toast.warn{background:#92400e}.toast.error{background:#991b1b}
.panel{background:rgba(255,253,248,.88);border-radius:30px;padding:22px;box-shadow:var(--shadow);min-width:0}
.auth-grid{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(320px,.9fr);gap:18px}
.auth-card,.overview-card,.queue-card,.module-card{background:var(--surface);border:1px solid var(--line);border-radius:26px;padding:20px;box-shadow:0 10px 28px rgba(16,32,51,.04)}
.auth-card h3,.module-header h3{margin:0;font-family:var(--serif);font-size:26px}
.auth-card p,.module-header p,.empty-state p,.helper{color:var(--muted);line-height:1.55}
.field-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.field{display:flex;flex-direction:column;gap:8px}
.field.full{grid-column:1/-1}
.field label{font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.06em;color:#364152}
.field input,.field select,.field textarea{width:100%;padding:12px 13px;background:var(--surface)}
.field textarea{min-height:260px;resize:vertical;font-family:var(--mono);font-size:12px;line-height:1.55}
.helper-panel{display:flex;flex-direction:column;gap:12px}
.helper-box{padding:14px 16px;border-radius:18px;background:var(--surface-2);border:1px solid var(--line)}
.helper-box strong{display:block;margin-bottom:6px}
.toggle-row{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:14px 16px;border:1px solid var(--line);border-radius:18px;background:var(--surface-2);text-transform:none!important;letter-spacing:0!important}
.toggle-copy{display:flex;flex-direction:column;gap:4px}
.toggle-copy strong{font-size:14px;color:var(--ink)}
.toggle-copy small{font-size:12px;color:var(--muted);line-height:1.45}
.switch{position:relative;display:inline-flex;align-items:center}
.switch input{position:absolute;opacity:0;pointer-events:none}
.switch-track{width:54px;height:32px;border-radius:999px;background:#d7d9dd;display:block;position:relative;transition:.18s background ease}
.switch-thumb{position:absolute;top:4px;left:4px;width:24px;height:24px;border-radius:999px;background:#fff;box-shadow:0 6px 16px rgba(16,32,51,.18);transition:.18s transform ease}
.switch input:checked + .switch-track{background:linear-gradient(135deg,var(--accent),var(--accent-2))}
.switch input:checked + .switch-track .switch-thumb{transform:translateX(22px)}
.session-stack{display:flex;flex-direction:column;gap:14px}
.choice-group{display:flex;flex-wrap:wrap;gap:10px}
.choice-card{cursor:pointer;position:relative}
.choice-card input{position:absolute;opacity:0;pointer-events:none}
.choice-card span{display:inline-flex;align-items:center;justify-content:center;min-height:42px;padding:10px 14px;border-radius:999px;border:1px solid var(--line);background:var(--surface);font-size:13px;font-weight:800;color:var(--muted);transition:.18s ease}
.choice-card input:checked + span{background:linear-gradient(135deg,#102033,#1f3554);border-color:#102033;color:#fff;box-shadow:0 10px 22px rgba(16,32,51,.12)}
.status-strip{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.detail-list{display:flex;flex-direction:column;gap:6px;font-size:13px;color:var(--muted)}
.qr-wrap{display:flex;justify-content:center;padding:10px;border:1px dashed var(--line);border-radius:14px;background:#fff}
.qr-wrap img{width:190px;height:190px;max-width:100%;display:block}
.section-grid{display:grid;grid-template-columns:minmax(0,1fr);gap:18px;min-width:0}
.section-grid > *{min-width:0}
.card-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}
.overview-card h4{margin:0;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.overview-card strong{display:block;margin-top:12px;font-size:34px;font-family:var(--serif);line-height:1}
.overview-card span{display:block;margin-top:8px;color:var(--muted);font-size:13px}
.module-header{display:flex;align-items:flex-start;justify-content:space-between;gap:14px;margin-bottom:16px}
.module-actions{display:flex;flex-wrap:wrap;gap:10px}
.split{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(340px,.8fr);gap:18px}
.sr-only{position:absolute!important;width:1px!important;height:1px!important;padding:0!important;margin:-1px!important;overflow:hidden!important;clip:rect(0,0,0,0)!important;white-space:nowrap!important;border:0!important}
.operation-desk-section{gap:14px}
.operation-mode-strip{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:14px 18px;border:1px solid rgba(25,47,154,.12);border-radius:24px;background:linear-gradient(135deg,#f8fbff 0%,#eef7f3 100%);box-shadow:0 18px 42px rgba(25,47,154,.06)}
.operation-mode-strip strong{display:block;margin-top:4px;font-size:14px;color:var(--ink)}
.mode-pills{display:flex;flex-wrap:wrap;gap:8px;justify-content:flex-end}
.mode-pill{display:inline-flex;align-items:center;border-radius:999px;padding:8px 12px;font-size:12px;font-weight:900;letter-spacing:.02em}
.mode-pill.is-test{background:#e8eefc;color:var(--accent)}
.mode-pill.is-live{background:#e8f7ef;color:#057a55}
.conversation-ops-shell{display:grid;grid-template-columns:minmax(300px,.82fr) minmax(460px,1.42fr) minmax(300px,.86fr);gap:16px;align-items:stretch}
.operation-column{min-width:0;min-height:calc(100vh - 245px)}
.conversation-list-panel,.conversation-thread-panel,.conversation-side-panel{min-width:0}
.conversation-thread-panel{display:flex;flex-direction:column;padding:0;overflow:hidden;background:#f6f1e8}
.conversation-side-panel{position:sticky;top:18px;align-self:start}
.conversation-search{margin-bottom:12px}
.conversation-search input{width:100%;border:1px solid var(--line);border-radius:18px;background:#fff;padding:12px 14px;font-size:14px;color:var(--ink);outline:none}
.conversation-search input:focus{border-color:rgba(25,47,154,.34);box-shadow:0 0 0 4px rgba(25,47,154,.08)}
.conversation-filter-chips{display:flex;gap:8px;overflow:auto;padding-bottom:8px;margin-bottom:10px;scrollbar-width:thin}
.filter-chip{flex:0 0 auto;border:1px solid var(--line);border-radius:999px;background:#fff;color:var(--muted);padding:8px 11px;font-size:12px;font-weight:900;cursor:pointer;transition:.18s ease}
.filter-chip:hover{border-color:rgba(25,47,154,.24);color:var(--accent)}
.filter-chip.is-active{background:var(--accent);border-color:var(--accent);color:#fff;box-shadow:0 10px 20px rgba(25,47,154,.14)}
.conversation-card-list{display:flex;flex-direction:column;gap:10px;max-height:calc(100vh - 405px);overflow:auto;padding-right:3px}
.conversation-card{position:relative;width:100%;border:1px solid transparent;border-radius:20px;background:#fff;padding:12px;text-align:left;color:var(--ink);box-shadow:none;cursor:pointer;transition:.18s ease}
.conversation-card:hover{border-color:rgba(25,47,154,.16);background:#f8fbff;transform:translateY(-1px)}
.conversation-card.is-active{border-color:rgba(25,47,154,.35);background:linear-gradient(135deg,#eef3ff 0%,#ffffff 74%)}
.conversation-card.is-selected{box-shadow:inset 0 0 0 2px rgba(18,140,126,.18)}
.conversation-card-top,.conversation-card-meta,.conversation-card-footer{display:flex;align-items:center;gap:8px}
.conversation-card-top{justify-content:space-between;margin-bottom:6px}
.conversation-card-title{display:flex;align-items:center;gap:8px;min-width:0}
.conversation-card-title strong{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:14px}
.conversation-avatar{width:34px;height:34px;border-radius:50%;display:grid;place-items:center;background:linear-gradient(135deg,#0f8b68,#35c19b);color:#fff;font-weight:900;font-size:12px;flex:0 0 auto}
.conversation-time{font-size:12px;color:var(--muted);white-space:nowrap}
.conversation-preview{margin:0 0 10px 42px;color:#536173;font-size:13px;line-height:1.45;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.conversation-card-meta{justify-content:space-between;margin-left:42px}
.conversation-tags{display:flex;gap:6px;flex-wrap:wrap}
.conversation-tag,.conversation-status-badge,.unread-badge{display:inline-flex;align-items:center;border-radius:999px;font-size:11px;font-weight:900;line-height:1;padding:6px 8px}
.conversation-tag{background:#f1f5f9;color:#475569}
.conversation-status-badge{background:#e8eefc;color:var(--accent)}
.conversation-status-badge.is-handoff{background:#fff4db;color:#b45309}
.conversation-status-badge.is-risk{background:#fee2e2;color:#b91c1c}
.conversation-status-badge.is-approval{background:#fef3c7;color:#92400e}
.unread-badge{background:#0f8b68;color:#fff;min-width:24px;justify-content:center}
.conversation-select-inline{position:absolute;left:10px;top:48px;width:18px;height:18px;accent-color:var(--accent)}
.whatsapp-thread-header{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:14px 16px;background:#fff;border-bottom:1px solid var(--line)}
.thread-guest{display:flex;align-items:center;gap:10px;min-width:0}
.thread-guest strong{display:block;font-size:15px}
.thread-guest span{display:block;color:var(--muted);font-size:12px;margin-top:2px}
.thread-actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap;justify-content:flex-end}
.whatsapp-thread-body{flex:1;overflow:auto;padding:20px 18px;background:radial-gradient(circle at 20% 0%,rgba(18,140,126,.08),transparent 30%),linear-gradient(180deg,#f8f2e8,#f4eadb)}
.message-stream{display:flex;flex-direction:column;gap:12px}
.chat-bubble{max-width:min(76%,680px);border-radius:18px;padding:10px 12px;background:#fff;box-shadow:0 8px 20px rgba(15,23,42,.06)}
.chat-bubble.is-user{align-self:flex-start;border-top-left-radius:6px}
.chat-bubble.is-assistant,.chat-bubble.is-operator{align-self:flex-end;border-top-right-radius:6px;background:#dcf8c6}
.chat-bubble.is-system{align-self:center;max-width:82%;background:rgba(255,255,255,.72);border:1px dashed rgba(83,97,115,.22);box-shadow:none;text-align:center}
.chat-bubble-header{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:6px;color:#64748b;font-size:11px;font-weight:900;text-transform:uppercase;letter-spacing:.04em}
.chat-bubble-content{white-space:pre-wrap;color:#182235;font-size:14px;line-height:1.55}
.message-status{display:flex;justify-content:flex-end;align-items:center;gap:6px;margin-top:7px;color:#64748b;font-size:11px;font-weight:800}
.message-status.is-error{color:#b91c1c}
.message-status.is-read{color:#0f8b68}
.message-status.is-queued{color:#b45309}
.developer-details{margin-top:8px;border-top:1px solid rgba(15,23,42,.08);padding-top:8px}
.developer-details summary{cursor:pointer;color:#536173;font-size:12px;font-weight:900}
.developer-details pre{max-height:220px;overflow:auto;margin:8px 0 0;padding:10px;border-radius:12px;background:#102033;color:#e5edf7;font-size:11px;white-space:pre-wrap}
.message-menu-button{border:none;border-radius:999px;background:rgba(255,255,255,.64);color:#334155;width:28px;height:24px;display:inline-grid;place-items:center;font-weight:900;cursor:pointer}
.message-menu-button:hover,.message-menu-button:focus-visible{background:#fff;outline:2px solid rgba(25,47,154,.22);outline-offset:2px}
.response-context-menu{position:fixed;z-index:120;min-width:190px;padding:8px;border:1px solid var(--line);border-radius:16px;background:#fff;box-shadow:0 24px 54px rgba(16,32,51,.18)}
.response-context-menu button{width:100%;border:none;border-radius:12px;background:transparent;color:#182235;padding:10px 12px;text-align:left;font-size:13px;font-weight:900;cursor:pointer}
.response-context-menu button:hover,.response-context-menu button:focus-visible{background:#eef2ff;color:var(--accent);outline:none}
.response-context-menu button.is-warn:hover,.response-context-menu button.is-warn:focus-visible{background:#fff4db;color:#92400e}
.operation-faq-dialog{max-width:680px;width:min(94vw,680px)}
.operation-faq-dialog .dialog-card{max-height:86vh;overflow:auto}
.thread-composer{padding:14px 16px;background:#fff;border-top:1px solid var(--line);display:grid;gap:10px}
.ai-draft-box{border:1px solid rgba(25,47,154,.16);border-radius:18px;background:#f5f7ff;padding:12px}
.ai-draft-box strong{display:block;color:var(--accent);font-size:13px;margin-bottom:4px}
.ai-draft-box p{margin:0;color:#536173;font-size:13px;line-height:1.45}
.composer-row{display:flex;gap:10px;align-items:flex-end}
.composer-row textarea{flex:1;min-height:48px;resize:vertical;border:1px solid var(--line);border-radius:18px;padding:12px 14px;font:inherit;color:var(--ink)}
.decision-support-panel{display:flex;flex-direction:column;gap:14px}
.decision-section{border:1px solid var(--line);border-radius:20px;background:#fff;padding:14px}
.decision-section h4{margin:0 0 10px;font-size:13px;letter-spacing:.04em;text-transform:uppercase;color:#536173}
.decision-row{display:flex;justify-content:space-between;gap:12px;padding:8px 0;border-bottom:1px solid rgba(15,23,42,.06);font-size:13px}
.decision-row:last-child{border-bottom:none}
.decision-row span{color:#64748b}
.decision-row strong{text-align:right;color:#182235}
.risk-list{display:flex;gap:8px;flex-wrap:wrap}
.risk-chip{border-radius:999px;padding:7px 9px;background:#fee2e2;color:#b91c1c;font-size:12px;font-weight:900}
.risk-chip.is-safe{background:#e8f7ef;color:#057a55}
.quick-actions{display:grid;gap:8px}
.quick-actions .action-button{width:100%;justify-content:center}
.response-review-section{gap:16px}
.response-review-hero{display:flex;align-items:flex-start;justify-content:space-between;gap:18px;border:1px solid rgba(25,47,154,.12);border-radius:26px;background:linear-gradient(135deg,#f8fbff 0%,#fff7ea 100%);padding:20px;box-shadow:0 18px 42px rgba(25,47,154,.06)}
.response-review-hero h3{margin:4px 0 6px;font-family:var(--serif);font-size:28px}
.response-review-hero p{margin:0;max-width:850px;color:var(--muted);line-height:1.55}
.response-review-shell{display:grid;grid-template-columns:minmax(320px,.8fr) minmax(0,1.35fr);gap:16px;align-items:start}
.response-review-list-panel,.response-review-detail-panel{min-width:0}
.response-review-filters{display:grid;grid-template-columns:repeat(3,minmax(0,1fr)) auto;gap:10px;align-items:end;margin-bottom:14px}
.response-review-filters label{display:flex;flex-direction:column;gap:6px;font-size:12px;font-weight:900;color:#536173;text-transform:uppercase;letter-spacing:.04em}
.response-review-filters select{width:100%;border:1px solid var(--line);border-radius:14px;background:#fff;padding:10px;color:var(--ink)}
.response-review-list{display:flex;flex-direction:column;gap:10px;max-height:calc(100vh - 350px);overflow:auto;padding-right:3px}
.response-review-card{border:1px solid var(--line);border-radius:18px;background:#fff;padding:14px;text-align:left;cursor:pointer;transition:.18s ease}
.response-review-card:hover{border-color:rgba(25,47,154,.24);background:#f8fbff}
.response-review-card.is-active{border-color:rgba(25,47,154,.42);box-shadow:inset 0 0 0 2px rgba(25,47,154,.08)}
.response-review-card-top,.response-review-meta,.review-action-row{display:flex;align-items:center;justify-content:space-between;gap:10px}
.response-review-card strong{display:block;line-height:1.35}
.response-review-card p{margin:8px 0 10px;color:#536173;font-size:13px;line-height:1.45;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.review-chip{display:inline-flex;align-items:center;border-radius:999px;padding:6px 8px;font-size:11px;font-weight:900;background:#eef2f7;color:#334155}
.review-chip.open{background:#fff4db;color:#92400e}.review-chip.finalized{background:#e8f7ef;color:#057a55}.review-chip.in_review{background:#e8eefc;color:#192F9A}.review-chip.closed{background:#f1f5f9;color:#64748b}
.review-chip.correct{background:#e8f7ef;color:#057a55}.review-chip.incorrect{background:#fee2e2;color:#b91c1c}.review-chip.needs_revision{background:#fff4db;color:#92400e}
.response-review-detail-grid{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(310px,.9fr);gap:16px}
.review-detail-card{border:1px solid var(--line);border-radius:20px;background:#fff;padding:16px}
.review-detail-card h4{margin:0 0 10px;font-size:13px;text-transform:uppercase;letter-spacing:.05em;color:#536173}
.reported-message-box{border-radius:18px;background:#f8fbff;border:1px solid rgba(25,47,154,.12);padding:14px;white-space:pre-wrap;line-height:1.55}
.review-context-stream{display:flex;flex-direction:column;gap:8px}
.review-context-message{border-radius:14px;padding:10px 12px;background:#f8fafc;border:1px solid rgba(15,23,42,.08)}
.review-context-message.is-target{border-color:rgba(25,47,154,.34);background:#eef3ff}
.review-context-message b{display:flex;justify-content:space-between;gap:10px;margin-bottom:5px;font-size:12px;color:#536173}
.review-form{display:grid;gap:12px}
.review-form label{display:grid;gap:7px;font-size:12px;font-weight:900;color:#536173;text-transform:uppercase;letter-spacing:.04em}
.review-form select,.review-form textarea{border:1px solid var(--line);border-radius:14px;background:#fff;padding:11px 12px;color:var(--ink)}
.review-form textarea{min-height:110px;resize:vertical;line-height:1.5}
.review-history{display:flex;flex-direction:column;gap:8px}
.review-history-item{border-left:3px solid rgba(25,47,154,.32);padding:6px 0 6px 10px;color:#536173;font-size:13px}
.module-header.compact{margin-bottom:12px}
.module-header.compact h3{font-size:18px;font-family:var(--sans)}
.detail-tabs{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px}
.detail-tab{border:1px solid var(--line);border-radius:999px;background:var(--surface-2);color:var(--muted);padding:7px 10px;font-size:12px;font-weight:800;cursor:default}
.detail-tab.is-active{background:#e8eefc;color:var(--accent);border-color:rgba(25,47,154,.22)}
.conversation-side-empty{display:flex;flex-direction:column;gap:8px;border:1px dashed var(--line-strong);border-radius:18px;background:var(--surface-2);padding:14px}
.conversation-side-empty strong{font-size:14px;color:var(--ink)}
.conversation-side-empty p{margin:0;color:var(--muted);font-size:13px;line-height:1.5}
.toolbar{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:14px}
.toolbar input,.toolbar select{padding:10px 12px;border-radius:14px;border:1px solid var(--line);background:var(--surface)}
.toolbar-check{display:flex;align-items:center;gap:6px;font-size:13px;font-weight:500;cursor:pointer;white-space:nowrap}
.toolbar-check input[type=checkbox]{width:16px;height:16px;accent-color:var(--accent,#e7bf5f)}
.bulk-bar{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 14px;border-radius:18px;border:1px dashed var(--line-strong);background:var(--surface-2);margin-bottom:12px}
.bulk-left{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.bulk-count{font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.bulk-actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.bulk-check{padding:6px 10px;border-radius:999px;background:var(--surface);border:1px solid var(--line)}
.table-select{width:52px;text-align:center}
.row-select{width:18px;height:18px;accent-color:var(--accent)}
.action-cell{display:flex;gap:6px;align-items:center}
.pill-closed{display:inline-block;padding:4px 10px;border-radius:10px;font-size:12px;background:#6b7280;color:#fff}
.table-shell{border:1px solid var(--line);border-radius:22px;overflow:hidden;background:var(--surface)}
table{width:100%;border-collapse:collapse}
.holds-table tbody tr.has-special-request td{background:#fff7e6}
.holds-table tbody tr.has-special-request:hover td{background:#ffefc7}
thead th{padding:14px 16px;font-size:12px;letter-spacing:.06em;text-transform:uppercase;background:#f7f2e9;color:#536173;text-align:left;border-bottom:1px solid var(--line)}
tbody td{padding:14px 16px;border-bottom:1px solid var(--line);vertical-align:top;font-size:14px;line-height:1.45}
tbody tr:last-child td{border-bottom:none}
tbody tr:hover{background:#fffcf7}
.table-shell tbody tr.is-selected td{background:#eef8f6}
.holds-table tbody tr.is-selected td{background:#f0f8f7}
.holds-table tbody tr[data-open-hold]{cursor:pointer}
.pill{display:inline-flex;align-items:center;gap:8px;padding:6px 10px;border-radius:999px;font-size:12px;font-weight:800}
.pill.pending{background:#fff2dd;color:#92400e}.pill.open{background:#e8f3f1;color:#115e59}.pill.closed{background:#e5e7eb;color:#374151}.pill.high{background:#fde7e5;color:#991b1b}.pill.medium{background:#eef4ff;color:#1d4ed8}.pill.low{background:#ecfdf3;color:#166534}
.pill.success{background:#ecfdf3;color:#166534}.pill.warn{background:#fff2dd;color:#92400e}.pill.danger{background:#fde7e5;color:#991b1b}.pill.info{background:#e8f3f1;color:#115e59}
.stack{display:flex;flex-direction:column;gap:6px}.muted{color:var(--muted);font-size:13px}
.mono{font-family:var(--mono);font-size:12px}
.hold-action-stack{display:flex;flex-direction:column;gap:8px;min-width:124px}
.holds-table thead th:first-child,.holds-table tbody td:first-child{position:sticky;left:0;background:var(--surface);z-index:2}
.holds-table thead th:first-child{z-index:3}
.hold-summary-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}
.hold-summary-grid span{font-size:12px;color:var(--muted)}
.hold-summary-grid strong{display:block;font-size:13px;color:var(--ink)}
.hold-detail-actions{position:sticky;bottom:0;background:var(--surface);padding-top:12px}
.hold-timeline{display:flex;flex-direction:column;gap:8px}
.hold-timeline-item{display:flex;align-items:flex-start;gap:10px;padding:10px 12px;border-radius:12px;background:var(--surface);border:1px solid var(--line)}
.hold-timeline-item strong{display:block;font-size:13px}
.hold-timeline-item span{font-size:12px;color:var(--muted)}
.hold-timeline-dot{width:10px;height:10px;border-radius:999px;margin-top:5px;background:#d1d5db}
.hold-timeline-dot.done{background:#0f766e}
.hold-timeline-dot.warn{background:#b45309}
.hold-timeline-dot.danger{background:#b42318}
.queue-list{display:flex;flex-direction:column;gap:10px}
.queue-item{padding:14px 16px;border-radius:18px;background:var(--surface-2);border:1px solid var(--line)}
.queue-item strong{display:block}
.empty-state{padding:24px;border:1px dashed var(--line-strong);border-radius:22px;background:#fffaf0;text-align:center}
.timeline{display:flex;flex-direction:column;gap:10px}
.message{padding:14px 16px;border-radius:18px;background:var(--surface-2);border:1px solid var(--line)}
.message.user{border-left:4px solid var(--accent)}
.message.assistant{border-left:4px solid var(--gold)}
.message.system{border-left:4px solid #64748b}
.message header{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:8px}
.message header strong{font-size:13px}
.message pre{white-space:pre-wrap;word-break:break-word;margin:0;font-family:var(--sans)}
.audit-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-bottom:12px}
.audit-grid .helper-box{margin:0}
.audit-row{margin-top:8px;padding-top:8px;border-top:1px dashed var(--line-strong);font-size:12px;line-height:1.45}
.dense-form{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.dense-form .field.full{grid-column:1/-1}
.dialog::backdrop{background:rgba(16,32,51,.42)}
.dialog{border:none;border-radius:24px;padding:0;max-width:520px;width:min(92vw,520px);box-shadow:var(--shadow)}
.dialog-card{padding:22px;background:var(--surface)}
.dialog-head h3{margin:0;font-family:var(--serif);font-size:24px}
.dialog-head p{margin:10px 0 0;color:var(--muted)}
.dialog-actions{display:flex;justify-content:flex-end;gap:10px;margin-top:16px}
.status-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.status-block{padding:16px;border-radius:18px;border:1px solid var(--line);background:var(--surface)}
.status-block h4{margin:0 0 8px;font-size:13px}
.status-block pre{margin:0;font-family:var(--mono);font-size:12px;white-space:pre-wrap}
.profile-section-tabs{display:flex;flex-wrap:wrap;gap:10px}
.profile-section-tab{border:none;padding:10px 14px;border-radius:999px;background:#eef2f7;color:#334155;font-size:13px;font-weight:800;cursor:pointer}
.profile-section-tab.is-active{background:linear-gradient(135deg,var(--accent),var(--accent-2));color:#fff}
.profile-toolbar{display:flex;flex-wrap:wrap;align-items:center;gap:10px;margin-top:14px}
.profile-toolbar .field{flex:1 1 280px;margin:0}
.profile-toolbar-actions{display:flex;align-items:center;gap:8px}
.profile-overview-summary{margin-top:14px}
.profile-overview-header{display:flex;align-items:flex-start;justify-content:space-between;gap:16px}
.profile-overview-header h4{margin:0;font-size:14px}
.profile-overview-header p{margin:6px 0 0;font-size:12px;color:var(--muted)}
.profile-progress-track{position:relative;width:min(240px,100%);height:10px;border-radius:999px;background:#e5e7eb;overflow:hidden}
.profile-progress-fill{position:absolute;inset:0 auto 0 0;height:100%;border-radius:999px;background:linear-gradient(135deg,var(--accent),var(--accent-2))}
.profile-gap-list{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.profile-gap-chip{border:none;padding:8px 10px;border-radius:999px;background:#fff7ed;color:#9a3412;font-size:12px;font-weight:700;cursor:pointer}
.profile-gap-count{display:inline-flex;align-items:center;padding:8px 10px;border-radius:999px;background:var(--surface-2);border:1px solid var(--line);font-size:12px;font-weight:700;color:var(--muted)}
.profile-overview-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:14px}
.profile-overview-card{display:block;width:100%;padding:12px 14px;border-radius:16px;border:1px solid var(--line);background:var(--surface);text-align:left;cursor:pointer}
.profile-overview-card.is-active{border-color:rgba(15,118,110,.32);box-shadow:0 10px 24px rgba(15,118,110,.08)}
.profile-overview-card:hover{border-color:rgba(15,118,110,.24)}
.profile-overview-card h4{margin:0;font-size:13px}
.profile-overview-card p{margin:8px 0 0;font-size:12px;color:var(--muted);line-height:1.45}
.profile-overview-metrics{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.profile-overview-metrics span{display:inline-flex;align-items:center;padding:4px 8px;border-radius:999px;background:var(--surface-2);border:1px solid var(--line);font-size:12px;font-weight:700;color:var(--muted)}
.profile-overview-status{display:inline-flex;align-items:center;gap:8px;padding:4px 10px;border-radius:999px;font-size:12px;font-weight:800}
.profile-overview-status.complete{background:#ecfdf3;color:#166534}
.profile-overview-status.incomplete{background:#eef2f7;color:#475569}
.profile-overview-status.warning{background:#fff2dd;color:#92400e}
.profile-overview-status.blocker{background:#fde7e5;color:#991b1b}
.profile-section-badge{display:inline-flex;align-items:center;gap:6px;margin-left:8px;padding:2px 8px;border-radius:999px;font-size:12px;font-weight:800}
.profile-section-badge.blocker{background:#fde7e5;color:#991b1b}
.profile-section-badge.warning{background:#fff2dd;color:#92400e}
.profile-issue-panel{display:flex;flex-direction:column;gap:10px;margin-top:14px}
.profile-issue-row{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;padding:12px 14px;border-radius:14px;border:1px solid var(--line);background:var(--surface)}
.profile-issue-row.blocker{border-color:rgba(180,35,24,.24);background:#fff4f3}
.profile-issue-row.warning{border-color:rgba(180,83,9,.24);background:#fffaf1}
.profile-field-invalid{border-color:rgba(180,35,24,.22)!important;background:#fff4f3}
.profile-field-warning{border-color:rgba(180,83,9,.22)!important;background:#fffaf1}
.profile-field-invalid label,.profile-field-warning label{color:var(--ink)}
.profile-focus-pulse{animation:profile-focus-pulse 1.2s ease}
@keyframes profile-focus-pulse{0%{box-shadow:0 0 0 0 rgba(15,118,110,.3)}100%{box-shadow:0 0 0 10px rgba(15,118,110,0)}}
.facts-detail-focus{border-radius:22px;box-shadow:0 0 0 3px rgba(15,118,110,.16),0 18px 34px rgba(15,118,110,.12)}
.profile-section-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.profile-section-grid .field.full,.profile-section-grid .helper-box.full{grid-column:1/-1}
.profile-section-stack{display:flex;flex-direction:column;gap:12px}
.profile-card-selector{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
.profile-card-selector .field{min-width:min(320px,100%);flex:1 1 320px}
.profile-card-selector-meta{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.profile-item-card{padding:16px;border-radius:18px;border:1px solid var(--line);background:var(--surface)}
.profile-item-card header{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:12px}
.profile-item-card h4{margin:0;font-size:14px}
.profile-inline-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.profile-inline-grid .field.full{grid-column:1/-1}
.profile-json-textarea,.profile-list-textarea{min-height:140px;font-family:var(--mono);font-size:12px;line-height:1.55}
.profile-json-textarea.is-invalid{border-color:var(--danger);box-shadow:0 0 0 3px rgba(180,35,24,.12)}
.profile-summary-strip{display:flex;flex-wrap:wrap;gap:10px}
.profile-summary-chip{padding:8px 10px;border-radius:999px;background:var(--surface-2);border:1px solid var(--line);font-size:12px;font-weight:700;color:var(--muted)}
.mt-sm{margin-top:10px}.mt-md{margin-top:14px}.mt-lg{margin-top:16px}
.mb-md{margin-bottom:14px}
.min-w-select{min-width:240px}
.checkbox-field{width:20px;height:20px}
.card-grid-3{grid-template-columns:repeat(3,minmax(0,1fr))}
.chatlab-frame{width:100%;height:clamp(560px,calc(100vh - 120px),1000px);min-height:0;border:none;border-radius:12px}
.response-preview-layout{display:grid;grid-template-columns:minmax(320px,.9fr) minmax(360px,1.1fr);gap:18px;align-items:start}
.response-preview-form{display:grid;gap:16px}
.response-preview-form textarea{min-height:230px;resize:vertical;line-height:1.45}
.response-preview-samples{display:flex;gap:8px;flex-wrap:wrap;margin-top:-4px}
.response-preview-samples button{border:1px solid var(--line);background:var(--surface-2);color:var(--ink);border-radius:999px;padding:8px 11px;font-size:12px;font-weight:800;cursor:pointer;transition:border-color .18s ease,box-shadow .18s ease,transform .18s ease}
.response-preview-samples button:hover{border-color:rgba(15,118,110,.36);box-shadow:0 8px 18px rgba(15,118,110,.08);transform:translateY(-1px)}
.response-preview-options{gap:12px}
.response-preview-actions{display:flex;gap:10px;flex-wrap:wrap}
.response-preview-safety{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}
.response-preview-safety span{border:1px solid var(--line);background:#f8fafc;color:var(--muted);border-radius:999px;padding:6px 10px;font-size:12px;font-weight:700}
.response-preview-safety span.success{background:#ecfdf5;color:var(--ok);border-color:rgba(22,101,52,.18)}
.response-preview-safety span.warn{background:#fff7ed;color:var(--warn);border-color:rgba(180,83,9,.18)}
.response-preview-safety span.info{background:#e8f3f1;color:#115e59;border-color:rgba(15,118,110,.18)}
.response-preview-reply{min-height:220px;padding:16px;border:1px solid var(--line);border-radius:10px;background:#fff;white-space:pre-wrap;line-height:1.55}
.response-preview-reply.empty-state{display:flex;align-items:center;justify-content:center;color:var(--muted);background:#f8fafc}
.response-preview-output-actions{display:flex;align-items:center;justify-content:flex-end;gap:10px;flex-wrap:wrap}
.response-preview-translate{background:#fff7ed;color:#92400e;border:1px solid rgba(180,83,9,.26);box-shadow:0 10px 22px rgba(180,83,9,.1)}
.response-preview-translate:hover{background:#ffedd5;border-color:rgba(180,83,9,.42);box-shadow:0 12px 24px rgba(180,83,9,.14)}
.response-preview-translate:disabled{background:#f3f4f6;color:#94a3b8;border-color:#d1d5db;box-shadow:none;cursor:not-allowed}
.response-preview-copy{background:linear-gradient(135deg,#102033,#1f3554);color:#fff;border:1px solid rgba(16,32,51,.88);box-shadow:0 10px 22px rgba(16,32,51,.16)}
.response-preview-copy:hover{background:linear-gradient(135deg,#0f766e,#1d8f86);border-color:#0f766e;box-shadow:0 12px 24px rgba(15,118,110,.2)}
.response-preview-copy:disabled{background:#e5e7eb;color:#94a3b8;border-color:#d1d5db;box-shadow:none;cursor:not-allowed}
.response-preview-diagnostics{display:grid;grid-template-columns:minmax(180px,.7fr) minmax(260px,1fr);gap:14px;margin-top:16px}
.response-preview-diagnostics h4{margin:0 0 8px;font-size:13px}
.response-preview-tool-list{display:flex;flex-wrap:wrap;gap:8px;min-height:38px}
.response-preview-tool-list .pill{max-width:100%;overflow-wrap:anywhere}
.response-preview-diagnostics pre{max-height:280px;overflow:auto;margin:0;padding:12px;border:1px solid var(--line);border-radius:10px;background:#0f172a;color:#e2e8f0;font-size:12px;line-height:1.45}
.voice-lab-summary-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}
.voice-lab-kpi{background:var(--surface);border:1px solid var(--line);border-radius:22px;padding:18px;box-shadow:0 10px 28px rgba(16,32,51,.04)}
.voice-lab-kpi h4{margin:0;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.voice-lab-kpi strong{display:block;margin-top:12px;font-size:32px;font-family:var(--serif);line-height:1}
.voice-lab-kpi span{display:block;margin-top:8px;color:var(--muted);font-size:13px;line-height:1.45}
.voice-lab-layout{display:grid;grid-template-columns:minmax(320px,.9fr) minmax(360px,1.1fr);gap:18px;align-items:start}
.voice-lab-form{display:grid;gap:16px}
.voice-lab-form textarea{min-height:230px;resize:vertical;line-height:1.45}
.voice-lab-sample-list{display:flex;gap:8px;flex-wrap:wrap;margin-top:-4px}
.voice-lab-sample-list button{border:1px solid var(--line);background:var(--surface-2);color:var(--ink);border-radius:999px;padding:8px 11px;font-size:12px;font-weight:800;cursor:pointer;transition:border-color .18s ease,box-shadow .18s ease,transform .18s ease}
.voice-lab-sample-list button:hover{border-color:rgba(15,118,110,.36);box-shadow:0 8px 18px rgba(15,118,110,.08);transform:translateY(-1px)}
.voice-lab-options{gap:12px}
.voice-lab-actions{display:flex;gap:10px;flex-wrap:wrap}
.voice-lab-audio-preview{display:grid;gap:12px;padding:14px 16px;border:1px solid var(--line);border-radius:18px;background:var(--surface-2)}
.voice-lab-realtime-preview{display:grid;gap:12px;padding:14px 16px;border:1px solid rgba(15,118,110,.22);border-radius:18px;background:#f1fbf9}
.voice-lab-elevenlabs-preview{display:grid;gap:12px;padding:14px 16px;border:1px solid rgba(31,53,84,.18);border-radius:18px;background:#f8fafc}
.voice-lab-provider-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}
.voice-lab-audio-copy{display:grid;gap:4px}
.voice-lab-audio-copy strong{font-size:13px;color:var(--ink)}
.voice-lab-audio-copy span{font-size:13px;color:var(--muted);line-height:1.45}
.voice-lab-audio-copy span[data-tone="success"]{color:var(--ok)}
.voice-lab-audio-copy span[data-tone="warn"]{color:var(--warn)}
.voice-lab-audio-copy span[data-tone="error"]{color:var(--danger)}
.voice-lab-tuning-grid{display:grid;grid-template-columns:minmax(180px,1.2fr) minmax(140px,.8fr) minmax(140px,.8fr);gap:12px;align-items:end}
.voice-lab-realtime-grid{display:grid;grid-template-columns:minmax(160px,.75fr) minmax(260px,1fr);gap:12px;align-items:end}
.voice-lab-elevenlabs-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;align-items:end}
.voice-lab-realtime-actions{display:flex;gap:8px;flex-wrap:wrap}
.voice-lab-provider-actions{display:flex;gap:8px;flex-wrap:wrap}
.voice-lab-provider-safety{display:flex;gap:8px;flex-wrap:wrap}
.voice-lab-provider-safety span{border:1px solid var(--line);background:#fff;color:var(--muted);border-radius:999px;padding:6px 10px;font-size:12px;font-weight:700}
.voice-lab-audio-meter{display:grid;gap:10px;padding:12px;border:1px solid rgba(15,118,110,.18);border-radius:16px;background:rgba(255,255,255,.72)}
.voice-lab-meter-head{display:flex;align-items:center;justify-content:space-between;gap:10px}
.voice-lab-meter-head strong{font-size:12px;color:var(--ink)}
.voice-lab-meter-head span{font-size:12px;color:var(--muted);font-weight:800}
.voice-lab-audio-meter.active .voice-lab-meter-head span{color:#115e59}
.voice-lab-meter-bars{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:5px;align-items:end;height:64px}
.voice-lab-meter-bars span{display:block;min-height:8px;height:10px;border-radius:999px;background:linear-gradient(180deg,#0f766e,#7dd3fc);opacity:.45;transition:height .08s linear,opacity .12s ease}
.voice-lab-audio-meter.active .voice-lab-meter-bars span{opacity:.9}
.voice-lab-slider-field label{display:flex;align-items:center;justify-content:space-between;gap:8px}
.voice-lab-slider-field label span{font-size:12px;color:var(--muted);font-weight:800}
.voice-lab-slider-field input[type="range"]{width:100%;min-height:34px;accent-color:var(--accent)}
.voice-lab-slider-field input[type="range"]:disabled{opacity:.55;cursor:not-allowed}
.voice-lab-voice-actions{display:flex;gap:8px;flex-wrap:wrap}
.voice-lab-safety{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}
.voice-lab-safety span{border:1px solid var(--line);background:#f8fafc;color:var(--muted);border-radius:999px;padding:6px 10px;font-size:12px;font-weight:700}
.voice-lab-safety span.success{background:#ecfdf5;color:var(--ok);border-color:rgba(22,101,52,.18)}
.voice-lab-safety span.warn{background:#fff7ed;color:var(--warn);border-color:rgba(180,83,9,.18)}
.voice-lab-safety span.info{background:#e8f3f1;color:#115e59;border-color:rgba(15,118,110,.18)}
.voice-lab-result-panel{min-height:420px}
.voice-lab-result-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-bottom:14px}
.voice-lab-result-block{padding:14px 16px;border-radius:18px;background:var(--surface-2);border:1px solid var(--line)}
.voice-lab-result-block strong{display:block;margin-bottom:6px;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.voice-lab-result-block span{font-weight:800;color:var(--ink);overflow-wrap:anywhere}
.voice-lab-response{padding:16px;border:1px solid var(--line);border-radius:14px;background:#fff;white-space:pre-wrap;line-height:1.55;margin-bottom:14px}
.voice-lab-violations{display:flex;flex-direction:column;gap:8px}
.voice-lab-violation{padding:10px 12px;border-radius:14px;background:#fff4f3;border:1px solid rgba(180,35,24,.18);color:#7f1d1d;font-size:13px;line-height:1.45}
.voice-lab-table-shell table{min-width:760px}
.voice-lab-status-cell{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.response-translation-dialog{max-width:760px;width:min(94vw,760px)}
.response-translation-card{display:grid;gap:16px}
.response-translation-head{display:flex;align-items:flex-start;justify-content:space-between;gap:14px}
.response-translation-body{display:grid;gap:14px}
.response-translation-block{display:grid;gap:8px}
.response-translation-block strong{font-size:13px;color:var(--ink)}
.response-translation-block pre{margin:0;max-height:260px;overflow:auto;white-space:pre-wrap;word-break:break-word;border:1px solid var(--line);border-radius:12px;background:#f8fafc;color:var(--ink);padding:14px;font-family:var(--sans);font-size:14px;line-height:1.55}
.response-translation-block.target pre{background:#fff7ed;border-color:rgba(180,83,9,.22)}
.debug-summary-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
.debug-layout{display:grid;grid-template-columns:minmax(260px,.9fr) minmax(320px,1.1fr) minmax(320px,1fr);gap:18px}
.debug-column{min-height:460px}
.debug-run-list,.debug-finding-list{display:flex;flex-direction:column;gap:10px}
.debug-run-card,.debug-finding-card{border:1px solid var(--line);border-radius:18px;background:var(--surface-2);padding:14px;cursor:pointer;transition:border-color .18s ease,box-shadow .18s ease,transform .18s ease}
.debug-run-card:hover,.debug-finding-card:hover{border-color:rgba(15,118,110,.26);transform:translateY(-1px)}
.debug-run-card.is-active,.debug-finding-card.is-active{border-color:rgba(15,118,110,.38);box-shadow:0 12px 24px rgba(15,118,110,.08);background:#f2fbfa}
.debug-run-card header,.debug-finding-card header{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:8px}
.debug-run-card h4,.debug-finding-card h4{margin:0;font-size:14px}
.debug-card-meta{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}
.debug-card-meta span{display:inline-flex;align-items:center;padding:4px 8px;border-radius:999px;background:var(--surface);border:1px solid var(--line);font-size:12px;color:var(--muted)}
.debug-detail-section{padding:14px 16px;border-radius:18px;background:var(--surface-2);border:1px solid var(--line)}
.debug-detail-section strong{display:block;margin-bottom:8px}
.debug-detail-section pre{margin:0;white-space:pre-wrap;word-break:break-word;font-family:var(--mono);font-size:12px;line-height:1.55}
.debug-detail-grid{display:flex;flex-direction:column;gap:12px}
.debug-artifact-summary{display:flex;flex-direction:column;gap:8px;padding:12px 14px;border-radius:16px;background:#fffaf0;border:1px solid rgba(187,138,42,.18)}
.debug-artifact-summary strong{margin:0;font-size:13px}
.debug-artifact-summary p{margin:0;font-size:12px;line-height:1.55;color:var(--muted)}
.debug-artifact-groups{display:flex;flex-direction:column;gap:12px}
.debug-artifact-group{display:flex;flex-direction:column;gap:10px}
.debug-artifact-group-head{display:flex;align-items:center;justify-content:space-between;gap:12px}
.debug-artifact-group-head strong{margin:0;font-size:13px}
.debug-artifact-group-head span{font-size:12px;color:var(--muted)}
.debug-artifact-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}
.debug-artifact-card{display:flex;flex-direction:column;gap:10px;padding:12px;border-radius:16px;background:var(--surface);border:1px solid var(--line);transition:border-color .18s ease,box-shadow .18s ease,transform .18s ease}
.debug-artifact-card.is-active{border-color:rgba(15,118,110,.34);box-shadow:0 14px 28px rgba(15,118,110,.12);background:#f2fbfa;transform:translateY(-1px)}
.debug-artifact-card strong{margin:0;font-size:13px}
.debug-artifact-card span{font-size:12px;color:var(--muted)}
.debug-artifact-card code{font-family:var(--mono);font-size:11px;color:#475569;word-break:break-all}
.debug-artifact-preview{display:block;width:100%;aspect-ratio:16/10;object-fit:cover;border-radius:12px;border:1px solid var(--line);background:#f3f4f6;cursor:zoom-in}
.debug-artifact-actions{display:flex;flex-wrap:wrap;gap:8px}
.debug-artifact-link{display:inline-flex;align-items:center;justify-content:center;padding:8px 10px;border-radius:12px;background:#eef8f6;border:1px solid rgba(15,118,110,.16);color:#0f766e;font-size:12px;font-weight:800;text-decoration:none;cursor:pointer}
.debug-artifact-link:hover{background:#def3ef}
.debug-artifact-link.secondary{background:#f6f4ee;border-color:var(--line);color:#475569}
.debug-artifact-link.secondary:hover{background:#efe9dc}
.debug-artifact-dialog{max-width:min(96vw,1120px);width:min(96vw,1120px)}
.debug-artifact-dialog-card{display:flex;flex-direction:column;gap:14px}
.debug-artifact-preview-shell{display:grid;place-items:center;min-height:320px;border-radius:18px;background:#f6f1e7;border:1px solid var(--line)}
.debug-artifact-preview-large{display:block;max-width:100%;max-height:min(72vh,820px);border-radius:18px;object-fit:contain}
.debug-artifact-preview-meta{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
.debug-artifact-preview-meta strong{margin:0}
.debug-empty-compact{padding:18px;border:1px dashed var(--line-strong);border-radius:18px;background:#fffaf0}
.debug-empty-compact h4{margin:0 0 8px;font-size:15px}
.debug-toolbar{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.dialog-textarea{min-height:120px}
.inline-flex-center{display:flex;align-items:center;gap:8px}
.pill-closed{background:#e5e7eb;color:#4b5563;font-size:12px}
.pill-warning{display:inline-block;padding:2px 6px;border-radius:8px;font-size:12px;background:#fff4db;color:#7c4b06}
.action-button-sm{font-size:12px;padding:6px 14px}
.access-control-layout,.access-control-main{display:grid;grid-template-columns:minmax(320px,.9fr) minmax(0,1.1fr);gap:18px}
.access-role-grid,.access-user-list,.access-permission-tree{display:flex;flex-direction:column;gap:12px}
.access-role-card,.access-user-card,.access-permission-group{border:1px solid var(--line);border-radius:22px;background:var(--surface-2);padding:16px;transition:border-color .18s ease,box-shadow .18s ease,transform .18s ease}
.access-role-card{cursor:pointer;text-align:left}
.access-role-card:hover,.access-user-card:hover,.access-permission-group:hover{border-color:rgba(15,118,110,.24);box-shadow:0 12px 24px rgba(15,118,110,.06)}
.access-role-card.is-active,.access-user-card.is-selected{border-color:rgba(15,118,110,.38);box-shadow:0 14px 28px rgba(15,118,110,.12);background:#f2fbfa}
.access-role-card header,.access-user-card header,.access-permission-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}
.access-role-card h4,.access-user-card h4,.access-permission-head h4{margin:0;font-size:16px}
.access-role-card p,.access-user-card p,.access-permission-head p{margin:6px 0 0;color:var(--muted);line-height:1.5}
.access-chip-row,.access-user-badges,.access-summary-row{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}
.access-chip{display:inline-flex;align-items:center;padding:6px 10px;border-radius:999px;background:var(--surface);border:1px solid var(--line);font-size:12px;font-weight:800;color:#334155}
.access-chip.role{background:#eef4ff;color:#1d4ed8}
.access-chip.department{background:#e8f8f3;color:#0f766e}
.access-chip.security{background:#fff2dd;color:#92400e}
.access-chip.self{background:#eef2ff;color:#4338ca}
.access-overview-card{display:flex;flex-direction:column;gap:10px}
.access-overview-card h4{margin:0;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.access-overview-card strong{font-size:30px;line-height:1;font-family:var(--serif)}
.access-overview-card span{font-size:13px;color:var(--muted);line-height:1.5}
.access-field-role{background:rgba(238,244,255,.78);border:1px solid rgba(59,130,246,.18);padding:12px;border-radius:18px}
.access-field-department{background:rgba(232,248,243,.86);border:1px solid rgba(15,118,110,.18);padding:12px;border-radius:18px}
.access-field-role label,.access-field-department label{margin-bottom:8px}
.access-field-role small,.access-field-department small{color:var(--muted);line-height:1.45}
.access-toggle-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.access-toggle-locked{opacity:.92}
.access-user-controls{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:14px}
.access-user-controls .field{margin:0}
.access-user-controls .field.full{grid-column:1/-1}
.access-user-card.is-self-locked{background:#fffdf7;border-color:rgba(187,138,42,.32)}
.access-user-card.is-self-locked.is-selected{box-shadow:0 14px 28px rgba(187,138,42,.12);background:#fffaf0}
.access-user-actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px}
.access-user-note{padding:10px 12px;border-radius:14px;background:#fffaf0;border:1px dashed rgba(187,138,42,.28);font-size:12px;color:#7c4b06}
.access-permission-head{margin-bottom:12px}
.access-permission-stats{display:flex;flex-wrap:wrap;gap:8px}
.access-permission-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:12px;align-items:center;padding:14px 0;border-top:1px solid var(--line)}
.access-permission-row:first-of-type{border-top:none}
.access-permission-copy{display:flex;flex-direction:column;gap:6px}
.access-permission-copy strong{font-size:14px}
.access-permission-copy p{margin:0;color:var(--muted);font-size:13px;line-height:1.5}
.access-permission-copy code{font-family:var(--mono);font-size:11px;color:#475569;word-break:break-all}
.access-permission-flags{display:flex;flex-wrap:wrap;gap:6px}
.access-permission-flag{display:inline-flex;align-items:center;padding:4px 8px;border-radius:999px;font-size:11px;font-weight:800}
.access-permission-flag.default{background:#eef4ff;color:#1d4ed8}
.access-permission-flag.override{background:#fff2dd;color:#92400e}
.access-permission-flag.removed{background:#fde7e5;color:#991b1b}
.access-editor-empty{padding:28px;border:1px dashed var(--line-strong);border-radius:22px;background:#fffaf0;text-align:center}
.access-editor-empty h4{margin:0 0 8px;font-size:16px}
.access-editor-empty p{margin:0;color:var(--muted);line-height:1.55}
@media(max-width:1240px){
  .card-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
  .split,.conversation-ops-shell,.auth-grid,.access-control-layout,.access-control-main,.response-review-shell,.response-review-detail-grid{grid-template-columns:1fr}
  .conversation-side-panel{position:static}
  .voice-lab-summary-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
  .voice-lab-layout{grid-template-columns:1fr}
  .voice-lab-table-shell{overflow-x:auto;overflow-y:hidden;-webkit-overflow-scrolling:touch}
}
@media(max-width:980px){
  html,body{overflow-x:hidden}
  body{padding:12px}
  .topbar-actions{width:100%;justify-content:space-between;align-items:center}
  .topbar-aside{justify-content:flex-start}
  .table-shell{overflow-x:auto;overflow-y:hidden;-webkit-overflow-scrolling:touch}
  .table-shell table{min-width:640px}
  .field-grid,.dense-form,.status-list,.profile-section-grid,.profile-inline-grid,.profile-overview-grid,.debug-summary-grid,.debug-layout,.response-preview-layout,.response-preview-diagnostics,.response-review-filters,.voice-lab-summary-grid,.voice-lab-layout,.voice-lab-tuning-grid,.voice-lab-realtime-grid,.voice-lab-elevenlabs-grid,.voice-lab-result-grid,.access-toggle-grid,.access-user-controls{grid-template-columns:1fr}
  .response-review-hero{flex-direction:column}
  .topbar{padding:18px 20px;border-radius:24px;flex-direction:column}
  .card-grid{grid-template-columns:1fr}
  .status-strip{grid-template-columns:1fr}
  .hold-summary-grid{grid-template-columns:1fr}
  .debug-artifact-preview-meta{align-items:flex-start}
  .access-permission-row{grid-template-columns:1fr}
}
@media(min-width:768px) and (max-width:1023px){
  .shell{grid-template-columns:72px minmax(0,1fr)}
  .shell.is-sidebar-expanded{grid-template-columns:280px minmax(0,1fr)}
  .sidebar{position:static;transform:none;width:auto}
  .sidebar-toggle{display:none}
  .sidebar:not(.is-expanded){padding:16px 10px;align-items:center;gap:14px}
  .sidebar:not(.is-expanded) .brand{justify-content:center}
  .sidebar:not(.is-expanded) .brand > div:not(.brand-mark),.sidebar:not(.is-expanded) .sidebar-card,.sidebar:not(.is-expanded) .sidebar-actions,.sidebar:not(.is-expanded) .sidebar-collapse-toggle strong,.sidebar:not(.is-expanded) .nav-group-label,.sidebar:not(.is-expanded) .nav-copy,.sidebar:not(.is-expanded) .nav-badge{display:none}
  .sidebar:not(.is-expanded) .brand-mark{width:44px;height:44px;border-radius:14px}
  .sidebar:not(.is-expanded) .sidebar-collapse-toggle{width:44px;height:40px;padding:0}
  .sidebar:not(.is-expanded) .sidebar-collapse-toggle span{transform:rotate(180deg)}
  .sidebar:not(.is-expanded) .nav{width:100%;overflow:visible}
  .sidebar:not(.is-expanded) .nav-group{align-items:center;gap:6px}
  .sidebar:not(.is-expanded) .nav button{width:44px;min-width:44px;height:44px;padding:0;display:flex;align-items:center;justify-content:center}
}
@media(max-width:767px){
  body{padding:12px}
  body.sidebar-drawer-open{overflow:hidden}
  .shell,.shell.is-sidebar-collapsed,.shell.is-sidebar-expanded{grid-template-columns:1fr}
  .sidebar{position:fixed;left:12px;top:12px;bottom:12px;z-index:70;width:min(88vw,360px);padding:18px;border-radius:24px;transform:translateX(-112%);transition:transform .2s ease;align-items:stretch}
  .sidebar.is-open{transform:translateX(0)}
  .sidebar.is-collapsed{padding:18px;align-items:stretch}
  .sidebar.is-collapsed .brand > div:not(.brand-mark),.sidebar.is-collapsed .sidebar-card,.sidebar.is-collapsed .sidebar-actions,.sidebar.is-collapsed .sidebar-collapse-toggle strong,.sidebar.is-collapsed .nav-group-label,.sidebar.is-collapsed .nav-copy,.sidebar.is-collapsed .nav-badge{display:initial}
  .sidebar.is-collapsed .sidebar-card,.sidebar.is-collapsed .sidebar-actions{display:flex}
  .sidebar.is-collapsed .nav-group-label{display:block}
  .sidebar.is-collapsed .nav-copy{display:flex}
  .sidebar.is-collapsed .nav-badge{display:inline-flex}
  .sidebar.is-collapsed .nav{overflow-y:auto}
  .sidebar.is-collapsed .nav-group{align-items:stretch}
  .sidebar.is-collapsed .nav button{width:100%;height:auto;padding:0 12px;display:grid;grid-template-columns:24px minmax(0,1fr) auto;justify-content:stretch}
  .sidebar-collapse-toggle{display:none}
  .sidebar-toggle{display:inline-flex;align-items:center;justify-content:center}
  .sidebar-overlay:not([hidden]){display:block}
}
"""

ADMIN_PANEL_SCRIPT = UI_SHARED_SCRIPT + """\
const CONFIG = window.ADMIN_PANEL_CONFIG || {};
const API_ROOT = '/api/v1/admin';
const HOTEL_KEY = 'velox.admin.hotel';
const CSRF_COOKIE = 'velox_admin_csrf';
const DEFAULT_VERIFICATION_PRESET = '24_hours';
const DEFAULT_SESSION_PRESET = '8_hours';
const LIVE_REFRESH_INTERVAL_MS = 3000;
const SIDEBAR_STATE_KEY = 'hotel-ai.sidebar.state';
const SIDEBAR_OPEN_GROUPS_KEY = 'hotel-ai.sidebar.openGroups';
const VOICE_LAB_GREETING_TEXT = {
  tr: "Merhaba, Kassandra Ölüdeniz'e hoş geldiniz. Hizmet kalitesi ve talebinizi karşılayabilmemiz için görüşmemiz kayıt altına alınabilir. Size nasıl yardımcı olabilirim?",
  en: "Hello, welcome to Kassandra Oludeniz. For service quality and to assist with your request, this call may be recorded. How may I help you?",
  ru: "Здравствуйте, добро пожаловать в Kassandra Oludeniz. В целях качества обслуживания и помощи с вашим запросом разговор может записываться. Чем могу помочь?",
};
const VOICE_LAB_SPEECH_LANG = {tr: 'tr-TR', en: 'en-US', ru: 'ru-RU'};
const VOICE_LAB_VOICE_KEY = 'velox.voice_lab.voice';
const VOICE_LAB_RATE_KEY = 'velox.voice_lab.rate';
const VOICE_LAB_PITCH_KEY = 'velox.voice_lab.pitch';
const VOICE_LAB_RATE_MIN = 0.78;
const VOICE_LAB_RATE_MAX = 1.03;
const VOICE_LAB_PITCH_MIN = 0.86;
const VOICE_LAB_PITCH_MAX = 1.06;
const VOICE_LAB_DEFAULT_RATE = 0.88;
const VOICE_LAB_DEFAULT_PITCH = 0.96;
const VOICE_LAB_NATURAL_VOICE_HINTS = ['natural','neural','online','premium','enhanced','microsoft','google'];
const VOICE_LAB_REALTIME_VOICE_KEY = 'velox.voice_lab.realtime_voice';
const VOICE_LAB_ELEVENLABS_VOICE_ID_KEY = 'velox.voice_lab.elevenlabs.voice_id';
const VOICE_LAB_ELEVENLABS_PROFILE_KEY = 'velox.voice_lab.elevenlabs.profile';
const VOICE_LAB_ELEVENLABS_STABILITY_KEY = 'velox.voice_lab.elevenlabs.stability';
const VOICE_LAB_ELEVENLABS_SIMILARITY_KEY = 'velox.voice_lab.elevenlabs.similarity';
const VOICE_LAB_ELEVENLABS_STYLE_KEY = 'velox.voice_lab.elevenlabs.style';
const VOICE_LAB_REALTIME_VOICES = [
  {value: 'marin', label: 'Marin (önerilen)'},
  {value: 'cedar', label: 'Cedar (önerilen)'},
  {value: 'alloy', label: 'Alloy'},
  {value: 'ash', label: 'Ash'},
  {value: 'ballad', label: 'Ballad'},
  {value: 'coral', label: 'Coral'},
  {value: 'echo', label: 'Echo'},
  {value: 'sage', label: 'Sage'},
  {value: 'shimmer', label: 'Shimmer'},
  {value: 'verse', label: 'Verse'},
];
const NAVIGATION_GROUPS = [
  {
    id: 'main',
    label: 'Ana Menü',
    items: [
      {
        id: 'conversations',
        label: 'Operasyon Masası',
        subtitle: 'WhatsApp kokpiti',
        icon: 'WA',
        permission: 'conversations:read',
        badgeKey: 'conversations_active',
        title: 'WhatsApp Operasyon Masası',
        lead: 'Misafir konuşmalarını, AI yanıtlarını, riskleri ve insan devri gerektiren işleri tek ekranda yönetin.',
      },
      {
        id: 'responsereview',
        label: 'Yanıt İnceleme',
        subtitle: 'Raporlanan cevaplar',
        icon: 'YR',
        permission: 'response_reviews:read',
        title: 'Yanıt İnceleme ve Raporlama',
        lead: 'Raporlanan AI ve sistem yanıtlarını sınıflandırın, kalite feedback dosyalarına kontrollü aktarın.',
      },
      {
        id: 'holds',
        label: 'Onay Bekleyenler',
        subtitle: 'Rezervasyon ve işlem onayları',
        icon: 'OB',
        permission: 'holds:read',
        badgeKey: 'pending_holds',
        title: 'Onay Bekleyenler',
        lead: 'Konaklama, restoran ve transfer taleplerinde onay bekleyen işlemleri yönetin.',
      },
      {
        id: 'chatlab',
        label: 'Chat Lab',
        subtitle: 'Test stüdyosu',
        icon: 'CL',
        title: 'Chat Lab',
        lead: 'Misafir senaryolarını canlı akıştan ayrı bir test stüdyosunda deneyin ve değerlendirin.',
      },
      {
        id: 'faq',
        label: 'Bilgi Merkezi',
        subtitle: 'Hazır yanıt ve otel bilgisi',
        icon: 'BM',
        permission: 'hotels:read',
        title: 'Bilgi Merkezi',
        lead: 'AI yanıtlarında kullanılacak hazır bilgileri ve sık sorulan soruları sade biçimde yönetin.',
      },
      {
        id: 'whatsappapi',
        label: 'WhatsApp Bağlantısı',
        subtitle: 'Meta bağlantısı ve şablonlar',
        icon: 'WA',
        roles: ['ADMIN'],
        title: 'WhatsApp Bağlantısı',
        lead: 'Meta bağlantısı, telefon varlıkları ve mesaj şablonlarının durumunu kontrol edin.',
      },
      {
        id: 'dashboard',
        label: 'Raporlar',
        subtitle: 'Operasyon özeti',
        icon: 'RP',
        permission: 'dashboard:read',
        title: 'Raporlar',
        lead: 'Aktif konuşmaları, bekleyen onayları ve açık talepleri operasyon raporu olarak görüntüleyin.',
      },
      {
        id: 'system',
        label: 'Ayarlar',
        subtitle: 'Sistem ve panel ayarları',
        icon: 'AY',
        title: 'Ayarlar',
        lead: 'Sistem durumu, güvenlik ve bağlantı ayarlarını kontrol edin.',
      },
    ],
  },
  {
    id: 'advanced',
    label: 'İleri Araçlar',
    items: [
      {
        id: 'tickets',
        label: 'İnsan Devri',
        subtitle: 'Ekibe aktarılan görevler',
        icon: 'İD',
        permission: 'tickets:read',
        badgeKey: 'open_tickets',
        title: 'İnsan Devri',
        lead: 'Ekibe aktarılan görevleri öncelik ve duruma göre takip edin.',
      },
      {
        id: 'restaurant',
        label: 'Restoran Yönetimi',
        subtitle: 'Masa ve kapasite ayarları',
        icon: 'R',
        permission: 'holds:read',
        title: 'Restoran Yönetimi',
        lead: 'Tarih ve saat bazlı masa kapasitelerini ayarlayın.',
      },
      {
        id: 'restaurantai',
        label: 'Restoran Siparişleri',
        subtitle: 'Katalog ve garson akışı',
        icon: 'RS',
        permission: 'restaurant_ai:read',
        title: 'Restoran Siparişleri',
        lead: 'Menü kataloğunu, garson WhatsApp yönlendirmesini, sipariş loglarını ve test konsolunu yönetin.',
      },
      {
        id: 'notifications',
        label: 'Bildirim Ayarları',
        subtitle: 'WhatsApp bildirim numaraları',
        icon: 'B',
        permission: 'notification_phones:read',
        title: 'Bildirim Ayarları',
        lead: 'Rezervasyon onayları için WhatsApp bildirim numaralarını yönetin.',
      },
      {
        id: 'hotels',
        label: 'Otel Bilgileri',
        subtitle: 'Otel profili',
        icon: 'OT',
        permission: 'hotels:read',
        title: 'Otel Bilgileri',
        lead: 'Otel profilini düzenleyin ve değişiklikleri sisteme güvenle uygulayın.',
      },
      {
        id: 'accesscontrol',
        label: 'Rol ve Yetkiler',
        subtitle: 'Kullanıcı ve izin yönetimi',
        icon: 'RY',
        permission: 'access_control:read',
        title: 'Rol ve Yetkiler',
        lead: 'Kullanıcı, rol, departman ve pencere bazlı işlem izinlerini aynı ekranda yönetin.',
      },
      {
        id: 'responsewindow',
        label: 'Yanıt Önizleme',
        subtitle: 'Tek soru testi',
        icon: 'YÖ',
        permission: 'conversations:read',
        title: 'Yanıt Önizleme',
        lead: 'Tek müşteri sorusuna otel verisiyle geçmişsiz yanıt üretin.',
      },
      {
        id: 'voicelab',
        label: 'Voice Lab',
        subtitle: 'Telefon senaryo testleri',
        icon: 'VL',
        permission: 'conversations:read',
        title: 'Voice Lab',
        lead: 'Telefon senaryolarını canlı hatta çıkmadan kaynak, aksiyon ve güvenlik açısından ölçün.',
      },
      {
        id: 'debug',
        label: 'Kontrol Taraması',
        subtitle: 'Panel kalite bulguları',
        icon: 'KT',
        roles: ['ADMIN'],
        title: 'Kontrol Taraması',
        lead: 'Canlı panelde başlatılan yalnızca raporlama amaçlı kontrollerin bulgularını inceleyin.',
      },
    ],
  },
];
const NAVIGATION_ITEMS = NAVIGATION_GROUPS.flatMap(group => group.items);
const VIEW_PERMISSIONS = NAVIGATION_ITEMS.reduce((acc, item) => {
  if (item.permission) acc[item.id] = item.permission;
  return acc;
}, {});

function normalizeAdminViewKey(value) {
  const normalized = String(value || CONFIG.initial_view || 'conversations').replace('#', '').trim().toLowerCase();
  if (normalized === 'access-control') return 'accesscontrol';
  if (normalized === 'voice-lab') return 'voicelab';
  if (normalized === 'response-review' || normalized === 'response_review') return 'responsereview';
  return normalized || 'conversations';
}

const state = {
  me: null,
  bootstrap: null,
  bootstrapPending: null,
  hotels: [],
  selectedHotelId: window.localStorage.getItem(HOTEL_KEY) || '',
  currentView: normalizeAdminViewKey(window.location.hash || CONFIG.initial_view || '#conversations'),
  sidebarCollapsed: false,
  sidebarOpenGroups: new Set(),
  mobileSidebarOpen: false,
  lastDebugSourceView: 'conversations',
  dashboard: null,
  conversations: [],
  conversationsTotal: 0,
  conversationDetail: null,
  conversationFilter: 'all',
  conversationSearch: '',
  selectedConversationIds: new Set(),
  stayHolds: [],
  selectedStayHoldIds: new Set(),
  selectedStayHoldId: '',
  restaurantHolds: [],
  selectedRestaurantHoldId: '',
  restaurantDateFrom: '',
  restaurantDateTo: '',
  transferHolds: [],
  selectedTransferHoldIds: new Set(),
  selectedTransferHoldId: '',
  activeHoldsTab: 'stay',
  stayStatusFilter: '',
  restaurantStatusFilter: '',
  restaurantMode: 'AI_RESTAURAN',
  transferStatusFilter: '',
  confirmationFormType: 'accommodation',
  confirmationLanguage: 'tr',
  confirmationLanguages: [],
  confirmationGeneratedUrl: '',
  stayArchiveMode: false,
  transferArchiveMode: false,
  stayDraft: {},
  stayWizardStep: 1,
  stayWizardUseExisting: false,
  stayWizardReprocessHoldId: null,
  stayProfileRoomTypes: [],
  tickets: [],
  accessControlCatalog: null,
  accessControlUsers: [],
  accessControlSelectedRole: '',
  accessControlSelectedUserId: 0,
  accessControlPreviewRole: '',
  accessControlDraftPermissions: new Set(),
  accessControlUserDrafts: {},
  faqs: [],
  faqDetail: null,
  hotelDetail: null,
  hotelProfileDraft: null,
  hotelProfileLoadedSourceChecksum: null,
  hotelProfileLoadedDraftSnapshot: null,
  hotelProfileHasUnsavedChanges: false,
  hotelProfileMode: 'standard',
  hotelProfileSection: 'general',
  hotelProfileSearch: '',
  hotelProfileFaqActiveIndex: 0,
  hotelFactsDraftValidationHandle: null,
  hotelFactsConflict: null,
  hotelFactsStatus: null,
  hotelFactsDraftValidation: null,
  hotelFactsVersions: [],
  hotelFactsEvents: [],
  hotelFactsVersionDetail: null,
  hotelFactsVersionDetailRevealTimer: null,
  hotelFactsApiUnavailable: false,
  restaurantSlots: [],
  systemOverview: null,
  sessionStatus: null,
  sessionPreferences: null,
  debugRuns: [],
  activeDebugRunId: '',
  activeDebugFindingId: '',
  activeDebugArtifactId: '',
  highlightedDebugArtifactId: '',
  debugRunDetail: null,
  debugFindings: [],
  debugArtifacts: [],
  debugRunArtifacts: [],
  debugArtifactScope: 'run',
  debugPollingHandle: null,
  debugRefreshPromise: null,
  debugWorkerReady: false,
  debugWorkerMessage: '',
  debugBrowserScanAvailable: false,
  debugBrowserScanMessage: '',
  debugBrowserScanMode: '',
  debugBrowserScanTarget: '',
  responsePreviewResult: null,
  responsePreviewLoading: false,
  responseReviewItems: [],
  responseReviewTotal: 0,
  responseReviewDetail: null,
  activeResponseReviewId: '',
  responseContextMenu: null,
  operationFaqMessage: null,
  voiceLabScenarios: [],
  voiceLabResult: null,
  voiceLabMatrixResults: [],
  voiceLabMatrixSummary: null,
  voiceLabLoading: false,
  voiceLabRealtimeActive: false,
  voiceLabRealtimeConnecting: false,
  voiceLabRealtimePeer: null,
  voiceLabRealtimeDataChannel: null,
  voiceLabRealtimeLocalStream: null,
  voiceLabRealtimeAudioElement: null,
  voiceLabRealtimeAudioContext: null,
  voiceLabRealtimeAnalyser: null,
  voiceLabRealtimeMeterSource: null,
  voiceLabRealtimeMeterAnimationFrame: 0,
  refreshPromise: null,
  lastRefreshFailure: null,
  liveRefreshHandle: null,
  _authKeepAliveTimer: null,
  _visibilityBound: false,
};

const refs = {};

document.addEventListener('DOMContentLoaded', () => {
  startInteractiveLabelObserver(document.body);
  bindRefs();
  initializeNavigationState();
  renderNavigation();
  stripSensitiveQueryParams();
  // Prevent native form submission on all auth forms as a safety net
  ['loginForm','bootstrapForm','totpRecoveryForm','otpVerifyForm'].forEach(id => {
    var f = document.getElementById(id);
    if (f) f.addEventListener('submit', function(e){ e.preventDefault(); });
  });
  try { bindEvents(); } catch(e) { console.error('[Velox] bindEvents error:', e); }
  boot();
});

function bindRefs() {
  [
    'sidebar','sidebarToggle','sidebarCollapseToggle','sidebarOverlay','topbar',
    'toast','authView','panelView','loginForm','bootstrapForm','bootstrapCard','bootstrapSummary',
    'totpRecovery','totpRecoveryForm','trustedSessionBanner','loginOtpField','rememberDeviceToggle',
    'loginRememberOptions','loginVerificationOptions','loginSessionOptions',
    'otpSetup','otpSecret','otpUri','otpQrImage','otpVerifyForm','otpVerifyHint','currentUser','currentRole','hotelScope','hotelSelect','nav','pageBreadcrumb','pageTitle','pageLead',
    'dashboardCards','dashboardQueues','conversationFilters','conversationSearchInput','conversationFilterChips','conversationBulkBar','conversationSelectAll','conversationSelectionCount','conversationTableBody','conversationDetail','conversationDecisionPanel',
    'responseReviewFilters','responseReviewStatusFilter','responseReviewClassificationFilter','responseReviewErrorFilter','responseReviewRefresh','responseReviewList','responseReviewDetail',
    'stayHoldFilters','stayHoldTableBody','stayHoldDetail','stayHoldCreatePanel','stayWizardSteps','stayWizardBody','stayStatusChips',
    'restaurantHoldFilters','restaurantHoldTableBody','restaurantHoldDetail','restaurantHoldCreatePanel','restaurantCreateForm','restaurantStatusChips','restaurantDateFrom','restaurantDateTo',
    'transferHoldFilters','transferHoldTableBody','transferHoldDetail','transferHoldCreatePanel','transferCreateForm','transferStatusChips',
    'confirmationLanguageButtons','confirmationTypeButtons','confirmationFields','confirmationPreviewFrame','confirmationPublicUrl','confirmationWhatsappMessage',
    'accessOverviewCards','accessRoleSummary','accessRoleCards','accessCreateUserForm','accessCreateUsername','accessCreateDisplayName',
    'accessCreatePassword','accessCreatePasswordConfirm','accessCreateRole','accessCreateDepartment','accessCreateActive',
    'accessCreateTwoFactor','accessTotpResult','accessTotpResultTitle','accessTotpResultUser','accessTotpQrImage',
    'accessTotpSecret','accessTotpUri','accessUsersList','accessPermissionMeta','accessPermissionTree',
    'accessResetPermissionsButton','accessSavePermissionsButton',
    'ticketFilters','ticketTableBody','hotelProfileSelect','hotelProfileEditor','applyHotelProfileJson','saveHotelProfile',
    'faqFilters','faqTableBody','faqDetail','operationFaqDialog','operationFaqDialogForm','operationFaqDialogClose',
    'operationFaqDialogCancel','operationFaqTopic','operationFaqQuestionTr','operationFaqAnswerTr','operationFaqQuestionEn',
    'operationFaqAnswerEn','operationFaqStatus','operationFaqDialogResult',
    'notifPhoneTableBody','addNotifPhoneForm',
    'hotelProfileMeta','hotelProfileSections','hotelProfileSectionBody','hotelFactsConflict','hotelFactsStatus','hotelFactsHistory','hotelFactsEvents','hotelFactsVersionDetail','publishHotelFacts','slotFilters','slotDisplayInterval','slotTableBody','slotSummaryCards','slotCreateForm','slotDeleteForm','systemChecks','systemMeta',
    'sessionSummary','sessionPreferencesForm','sessionRememberToggle','sessionPreferenceFields',
    'systemVerificationOptions','systemSessionOptions','sessionOtpField','trustedDevicePanel','forgetDeviceButton',
    'debugStartButton','debugTopbarStatus','debugActiveRunStatus','debugActiveRunMeta','debugSummaryFindings','debugSummaryCounts',
    'debugSummaryScope','debugRefreshButton','debugRunList','debugFindingCountBadge','debugFindingList','debugDetailPanel',
    'debugRunDialog','debugRunForm','debugScopeAllPanel','debugScopeCurrentView','debugIncludeChatLab','debugIncludePopups',
    'debugIncludeModals','debugRunCancelButton','debugArtifactPreviewDialog','debugArtifactPreviewTitle',
    'debugArtifactPreviewMeta','debugArtifactPreviewImage','debugArtifactPreviewEmpty','debugArtifactPreviewPath',
    'debugArtifactPreviewLink','debugArtifactPreviewCloseButton',
    'responsePreviewForm','responsePreviewQuestion','responsePreviewSampleList','responsePreviewLanguage',
    'responsePreviewStyle','responsePreviewGenerate','responsePreviewClear',
    'responsePreviewSafety','responsePreviewReply','responsePreviewMeta','responsePreviewTranslate','responsePreviewCopy',
    'responsePreviewToolList','responsePreviewInternalJson','responsePreviewTranslationDialog',
    'responsePreviewTranslationTitle','responsePreviewTranslationMeta','responsePreviewTranslationBody','responsePreviewTranslationClose',
    'voiceLabSummaryCards','voiceLabTotalCount','voiceLabPassedCount','voiceLabFailedCount','voiceLabBlockedCount',
    'voiceLabForm','voiceLabTranscript','voiceLabSampleList','voiceLabScenario','voiceLabLanguage',
    'voiceLabRunButton','voiceLabRunMatrixButton','voiceLabClearButton','voiceLabSafety','voiceLabResultMeta',
    'voiceLabVoiceSelect','voiceLabRate','voiceLabRateValue','voiceLabPitch','voiceLabPitchValue',
    'voiceLabSpeakGreetingButton','voiceLabSpeakReplyButton','voiceLabStopVoiceButton','voiceLabVoiceStatus',
    'voiceLabElevenLabsStatus','voiceLabElevenLabsBadge','voiceLabElevenLabsKeyStatus',
    'voiceLabElevenLabsVoiceId','voiceLabElevenLabsProfile','voiceLabElevenLabsStability',
    'voiceLabElevenLabsStabilityValue','voiceLabElevenLabsSimilarity','voiceLabElevenLabsSimilarityValue',
    'voiceLabElevenLabsStyle','voiceLabElevenLabsStyleValue','voiceLabElevenLabsSaveButton','voiceLabElevenLabsTestButton',
    'voiceLabRealtimeVoice','voiceLabRealtimeStartButton','voiceLabRealtimeStopButton','voiceLabRealtimeStatus',
    'voiceLabRealtimeMeter','voiceLabRealtimeMeterText','voiceLabRealtimeMeterBars',
    'voiceLabResultBadge','voiceLabResultPanel','voiceLabMatrixBadge','voiceLabMatrixBody',
    'logoutButton','reloadButton','decisionDialog','decisionForm','decisionTitle','decisionLead','decisionReason',
    'decisionHoldId','decisionMode'
  ].forEach(id => refs[id] = document.getElementById(id));
  // Bootstrap hotel select uses kebab-case id in HTML; map it to the existing JS key.
  refs.bootstrapHotels = document.getElementById('bootstrap-hotel');
}

function bindEvents() {
  refs.sidebarToggle?.addEventListener('click', toggleSidebar);
  refs.sidebarCollapseToggle?.addEventListener('click', toggleSidebarCollapsed);
  refs.sidebarOverlay?.addEventListener('click', closeSidebar);
  refs.nav?.addEventListener('click', onNavigationClick);
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      closeSidebar();
      closeResponseContextMenu();
    }
  });
  refs.loginForm?.addEventListener('submit', onLogin);
  refs.bootstrapForm?.addEventListener('submit', onBootstrap);
  refs.totpRecoveryForm?.addEventListener('submit', onTotpRecovery);
  refs.otpVerifyForm?.addEventListener('submit', onBootstrapVerify);
  refs.rememberDeviceToggle?.addEventListener('change', toggleLoginRememberOptions);
  refs.hotelSelect?.addEventListener('change', onHotelScopeChange);
  refs.hotelProfileSelect?.addEventListener('change', loadHotelProfileSection);
  refs.publishHotelFacts?.addEventListener('click', publishHotelFacts);
  refs.applyHotelProfileJson?.addEventListener('click', applyHotelProfileJsonToForm);
  refs.slotCreateForm?.addEventListener('submit', onCreateSlot);
  refs.slotDeleteForm?.addEventListener('submit', onDeleteSlots);
  refs.slotDisplayInterval?.addEventListener('change', applySlotDisplayFilter);
  refs.hideSlotsButton?.addEventListener('click', hideRestaurantSlotsView);
  refs.sessionPreferencesForm?.addEventListener('submit', onSessionPreferencesSave);
  refs.sessionRememberToggle?.addEventListener('change', toggleSessionPreferenceState);
  refs.forgetDeviceButton?.addEventListener('click', forgetTrustedDevice);
  refs.debugStartButton?.addEventListener('click', openDebugRunModal);
  refs.debugRunCancelButton?.addEventListener('click', closeDebugRunModal);
  refs.debugRunForm?.addEventListener('submit', onDebugRunSubmit);
  refs.debugRefreshButton?.addEventListener('click', () => {
    loadDebugRunsSafely({preserveSelection: true}, {notifyOnError: true});
  });
  refs.debugRunList?.addEventListener('click', onDebugRunListClick);
  refs.debugFindingList?.addEventListener('click', onDebugFindingListClick);
  refs.debugDetailPanel?.addEventListener('click', onDebugDetailClick);
  refs.debugArtifactPreviewCloseButton?.addEventListener('click', closeDebugArtifactPreview);
  refs.debugArtifactPreviewDialog?.addEventListener('close', () => {
    state.activeDebugArtifactId = '';
  });
  refs.responsePreviewForm?.addEventListener('submit', onResponsePreviewSubmit);
  refs.responsePreviewSampleList?.addEventListener('click', onResponsePreviewSampleClick);
  refs.responsePreviewClear?.addEventListener('click', clearResponsePreview);
  refs.responsePreviewTranslate?.addEventListener('click', openResponsePreviewTranslation);
  refs.responsePreviewTranslationClose?.addEventListener('click', closeResponsePreviewTranslation);
  refs.responsePreviewCopy?.addEventListener('click', copyResponsePreviewReply);
  refs.voiceLabForm?.addEventListener('submit', onVoiceLabSubmit);
  refs.voiceLabSampleList?.addEventListener('click', onVoiceLabSampleClick);
  refs.voiceLabScenario?.addEventListener('change', onVoiceLabScenarioChange);
  refs.voiceLabRunMatrixButton?.addEventListener('click', runVoiceLabMatrix);
  refs.voiceLabClearButton?.addEventListener('click', clearVoiceLab);
  refs.voiceLabVoiceSelect?.addEventListener('change', onVoiceLabVoiceTuningChange);
  refs.voiceLabRate?.addEventListener('input', onVoiceLabVoiceTuningChange);
  refs.voiceLabPitch?.addEventListener('input', onVoiceLabVoiceTuningChange);
  refs.voiceLabSpeakGreetingButton?.addEventListener('click', speakVoiceLabGreeting);
  refs.voiceLabSpeakReplyButton?.addEventListener('click', speakVoiceLabReply);
  refs.voiceLabStopVoiceButton?.addEventListener('click', stopVoiceLabSpeech);
  refs.voiceLabElevenLabsProfile?.addEventListener('change', onVoiceLabElevenLabsChange);
  refs.voiceLabElevenLabsVoiceId?.addEventListener('input', onVoiceLabElevenLabsChange);
  refs.voiceLabElevenLabsStability?.addEventListener('input', onVoiceLabElevenLabsChange);
  refs.voiceLabElevenLabsSimilarity?.addEventListener('input', onVoiceLabElevenLabsChange);
  refs.voiceLabElevenLabsStyle?.addEventListener('input', onVoiceLabElevenLabsChange);
  refs.voiceLabElevenLabsSaveButton?.addEventListener('click', saveVoiceLabElevenLabsSettings);
  refs.voiceLabElevenLabsTestButton?.addEventListener('click', testVoiceLabElevenLabsConnection);
  refs.voiceLabRealtimeVoice?.addEventListener('change', onVoiceLabRealtimeVoiceChange);
  refs.voiceLabRealtimeStartButton?.addEventListener('click', startVoiceLabRealtime);
  refs.voiceLabRealtimeStopButton?.addEventListener('click', stopVoiceLabRealtime);
  refs.voiceLabLanguage?.addEventListener('change', onVoiceLabLanguageChange);
  initializeVoiceLabTuningControls();
  initializeVoiceLabElevenLabsControls();
  initializeVoiceLabRealtimeControls();
  bindVoiceLabSpeechEvents();
  refs.reloadButton?.addEventListener('click', reloadConfig);
  refs.logoutButton?.addEventListener('click', logout);
  refs.conversationFilters?.addEventListener('submit', event => {
    event.preventDefault();
    clearConversationSelection();
    loadConversations();
  });
  refs.conversationSearchInput?.addEventListener('input', event => {
    state.conversationSearch = String(event.target.value || '').trim().toLowerCase();
    renderConversationListFromState();
  });
  refs.conversationFilterChips?.addEventListener('click', event => {
    const button = event.target.closest('[data-conversation-filter]');
    if (!button) return;
    state.conversationFilter = button.dataset.conversationFilter || 'all';
    refs.conversationFilterChips.querySelectorAll('[data-conversation-filter]').forEach(chip => {
      chip.classList.toggle('is-active', chip === button);
    });
    clearConversationSelection();
    renderConversationListFromState();
  });
  refs.conversationTableBody?.addEventListener('change', onConversationSelectionChange);
  refs.conversationSelectAll?.addEventListener('change', onConversationSelectAllChange);
  refs.responseReviewFilters?.addEventListener('submit', event => {
    event.preventDefault();
    loadResponseReviews();
  });
  refs.responseReviewRefresh?.addEventListener('click', () => loadResponseReviews());
  refs.responseReviewList?.addEventListener('click', event => {
    const card = event.target.closest('[data-response-review-id]');
    if (!card) return;
    loadResponseReviewDetail(card.dataset.responseReviewId);
  });
  refs.stayHoldFilters?.addEventListener('submit', event => {
    event.preventDefault();
    loadStayHolds();
  });
  refs.restaurantHoldFilters?.addEventListener('submit', event => {
    event.preventDefault();
    const formData = new FormData(refs.restaurantHoldFilters);
    state.restaurantDateFrom = String(formData.get('date_from') || '').trim();
    state.restaurantDateTo = String(formData.get('date_to') || '').trim();
    loadRestaurantHolds();
  });
  refs.transferHoldFilters?.addEventListener('submit', event => {
    event.preventDefault();
    loadTransferHolds();
  });
  refs.restaurantCreateForm?.addEventListener('submit', event => {
    event.preventDefault();
    submitRestaurantHold();
  });
  refs.transferCreateForm?.addEventListener('submit', event => {
    event.preventDefault();
    submitTransferHold();
  });
  refs.ticketFilters?.addEventListener('submit', event => {
    event.preventDefault();
    loadTickets();
  });
  refs.accessCreateUserForm?.addEventListener('submit', onAccessCreateUser);
  refs.accessCreateRole?.addEventListener('change', onAccessCreateRoleChange);
  refs.accessRoleCards?.addEventListener('click', onAccessRoleCardClick);
  refs.accessUsersList?.addEventListener('click', onAccessUsersListClick);
  refs.accessUsersList?.addEventListener('input', onAccessUsersListInput);
  refs.accessUsersList?.addEventListener('change', onAccessUsersListChange);
  refs.accessPermissionTree?.addEventListener('change', onAccessPermissionTreeChange);
  refs.accessResetPermissionsButton?.addEventListener('click', onAccessResetPermissions);
  refs.accessSavePermissionsButton?.addEventListener('click', onAccessSavePermissions);
  refs.faqFilters?.addEventListener('submit', event => {
    event.preventDefault();
    loadFaqs();
  });
  refs.operationFaqDialogClose?.addEventListener('click', closeOperationFaqDialog);
  refs.operationFaqDialogCancel?.addEventListener('click', closeOperationFaqDialog);
  refs.operationFaqDialogForm?.addEventListener('submit', submitOperationFaqDialog);
  refs.addNotifPhoneForm?.addEventListener('submit', onAddNotifPhone);
  refs.decisionForm?.addEventListener('submit', onDecisionSubmit);
  refs.hotelProfileSections?.addEventListener('click', onHotelProfileSectionNav);
  refs.hotelProfileSections?.addEventListener('input', onHotelProfileSectionSearchInput);
  refs.hotelProfileSections?.addEventListener('click', onHotelProfileSectionSearchClick);
  refs.hotelProfileSectionBody?.addEventListener('click', onHotelProfileSectionClick);
  refs.hotelProfileSectionBody?.addEventListener('input', onHotelProfileSectionInput);
  refs.hotelProfileSectionBody?.addEventListener('change', onHotelProfileSectionChange);
  refs.saveHotelProfile?.addEventListener('click', saveHotelProfile);
  document.getElementById('loadSlotsButton').addEventListener('click', event => {
    event.preventDefault();
    loadRestaurantSlots({syncRestaurantFilters: true});
  });
  document.getElementById('closeDecision').addEventListener('click', () => refs.decisionDialog.close());
  refs.panelView?.addEventListener('contextmenu', onOperationMessageContextMenu);
  document.addEventListener('click', event => {
    if (!event.target.closest?.('.response-context-menu') && !event.target.closest?.('[data-open-message-menu]')) {
      closeResponseContextMenu();
    }
  });
  window.addEventListener('message', async event => {
    if (event.data && event.data.type === 'chatlab:auth-required') {
      await loadChatLab();
    }
    if (event.data && event.data.type === 'chatlab:faq-created') {
      if (state.currentView === 'faq') loadFaqs();
    }
  });
  window.addEventListener('hashchange', () => {
    const newView = normalizeAdminViewKey(window.location.hash || '#conversations');
    if (newView !== state.currentView) {
      setView(newView);
    }
  });
  window.addEventListener('resize', syncSidebarLayout);
  bindDelegatedEvents();
}

function stripSensitiveQueryParams() {
  const url = new URL(window.location.href);
  const sensitiveKeys = ['username', 'password', 'otp_code', 'remember_device'];
  const hadSensitiveParams = sensitiveKeys.some(key => url.searchParams.has(key));
  if (!hadSensitiveParams) {
    return;
  }
  sensitiveKeys.forEach(key => url.searchParams.delete(key));
  const nextUrl = `${url.pathname}${url.search}${url.hash}`;
  window.history.replaceState({}, document.title, nextUrl);
  notify('URL içindeki giriş parametreleri güvenlik için temizlendi. Girişi form üzerinden yapın.', 'warn');
}

function initializeNavigationState() {
  const savedState = readSidebarState();
  state.sidebarCollapsed = typeof savedState.collapsed === 'boolean' ? savedState.collapsed : isTabletLayout();
  state.sidebarOpenGroups = readSidebarOpenGroups();
  syncSidebarLayout();
}

function readSidebarState() {
  try {
    return JSON.parse(window.localStorage.getItem(SIDEBAR_STATE_KEY) || '{}') || {};
  } catch (_error) {
    return {};
  }
}

function readSidebarOpenGroups() {
  try {
    const values = JSON.parse(window.localStorage.getItem(SIDEBAR_OPEN_GROUPS_KEY) || '[]');
    return new Set(Array.isArray(values) ? values.map(String) : []);
  } catch (_error) {
    return new Set();
  }
}

function persistSidebarState() {
  window.localStorage.setItem(SIDEBAR_STATE_KEY, JSON.stringify({collapsed: Boolean(state.sidebarCollapsed)}));
  window.localStorage.setItem(SIDEBAR_OPEN_GROUPS_KEY, JSON.stringify([...state.sidebarOpenGroups]));
}

function getNavigationItem(view) {
  const key = normalizeAdminViewKey(view);
  return NAVIGATION_ITEMS.find(item => item.id === key) || null;
}

function getNavigationGroupForView(view) {
  const key = normalizeAdminViewKey(view);
  return NAVIGATION_GROUPS.find(group => group.items.some(item => item.id === key)) || null;
}

function canAccessNavigationItem(item) {
  if (!state.me) return true;
  if (Array.isArray(item.roles) && item.roles.length && !item.roles.includes(state.me.role)) {
    return false;
  }
  if (item.permission && !hasPermission(item.permission)) {
    return false;
  }
  return true;
}

function getFilteredNavigationGroups() {
  return NAVIGATION_GROUPS
    .map(group => ({
      ...group,
      items: group.items.filter(canAccessNavigationItem),
    }))
    .filter(group => group.items.length > 0);
}

function getNavigationBadgeValue(item) {
  const key = item.badgeKey;
  if (!key || !state.dashboard?.cards) return null;
  return state.dashboard.cards[key];
}

function formatNavBadge(value) {
  if (value === null || value === undefined) return '';
  const count = Number(value);
  if (!Number.isFinite(count) || count <= 0) return '';
  return count > 99 ? '99+' : String(count);
}

function renderNavigation() {
  if (!refs.nav) return;
  const groups = getFilteredNavigationGroups();
  if (!groups.length) {
    refs.nav.innerHTML = '<div class="nav-empty">Bu rol için görünür menü bulunmuyor.</div>';
    return;
  }
  refs.nav.innerHTML = groups.map(group => `
    <section class="nav-group" aria-labelledby="nav-group-${escapeHtml(group.id)}">
      <div id="nav-group-${escapeHtml(group.id)}" class="nav-group-label">${escapeHtml(group.label)}</div>
      ${group.items.map(item => {
        const badge = formatNavBadge(getNavigationBadgeValue(item));
        return `
          <button type="button" data-nav="${escapeHtml(item.id)}" data-tooltip="${escapeHtml(item.label)}" aria-label="${escapeHtml(item.label)}" title="${escapeHtml(item.label)}">
            <span class="nav-icon" aria-hidden="true">${escapeHtml(item.icon || '')}</span>
            <span class="nav-copy">
              <span class="nav-label">${escapeHtml(item.label)}</span>
              <span class="nav-subtitle">${escapeHtml(item.subtitle || '')}</span>
            </span>
            ${badge ? `<span class="nav-badge">${escapeHtml(badge)}</span>` : ''}
          </button>
        `;
      }).join('')}
    </section>
  `).join('');
  updateNavigationState();
}

function updateNavigationState() {
  document.querySelectorAll('[data-nav]').forEach(button => {
    const isActive = button.dataset.nav === state.currentView;
    button.classList.toggle('is-active', isActive);
    if (isActive) {
      button.setAttribute('aria-current', 'page');
    } else {
      button.removeAttribute('aria-current');
    }
  });
}

function onNavigationClick(event) {
  const button = event.target.closest('[data-nav]');
  if (!button) return;
  setView(button.dataset.nav);
  closeSidebar();
}

function isMobileLayout() {
  return window.matchMedia('(max-width: 767px)').matches;
}

function isTabletLayout() {
  return window.matchMedia('(min-width: 768px) and (max-width: 1023px)').matches;
}

function syncSidebarLayout() {
  applySidebarState();
  if (!isMobileLayout()) {
    closeSidebar();
  }
}

function applySidebarState() {
  if (!refs.sidebar) return;
  const shell = refs.sidebar.closest('.shell');
  const useCollapsed = !isMobileLayout() && state.sidebarCollapsed;
  refs.sidebar.classList.toggle('is-collapsed', useCollapsed);
  refs.sidebar.classList.toggle('is-expanded', !useCollapsed && !isMobileLayout());
  shell?.classList.toggle('is-sidebar-collapsed', useCollapsed);
  shell?.classList.toggle('is-sidebar-expanded', !useCollapsed && !isMobileLayout());
  if (refs.sidebarCollapseToggle) {
    refs.sidebarCollapseToggle.hidden = isMobileLayout();
    refs.sidebarCollapseToggle.setAttribute('aria-expanded', useCollapsed ? 'false' : 'true');
    refs.sidebarCollapseToggle.setAttribute('aria-label', useCollapsed ? 'Menüyü genişlet' : 'Menüyü daralt');
    const label = refs.sidebarCollapseToggle.querySelector('strong');
    if (label) label.textContent = useCollapsed ? 'Menüyü Genişlet' : 'Menüyü Daralt';
  }
}

function closeSidebar() {
  if (!refs.sidebar || !refs.sidebarToggle) return;
  refs.sidebar.classList.remove('is-open');
  refs.sidebarToggle.setAttribute('aria-expanded', 'false');
  refs.sidebarOverlay.hidden = true;
  document.body.classList.remove('sidebar-drawer-open');
  state.mobileSidebarOpen = false;
}

function toggleSidebar() {
  if (!refs.sidebar || !refs.sidebarToggle || !isMobileLayout()) return;
  state.mobileSidebarOpen = !refs.sidebar.classList.contains('is-open');
  refs.sidebar.classList.toggle('is-open', state.mobileSidebarOpen);
  refs.sidebarOverlay.hidden = !state.mobileSidebarOpen;
  document.body.classList.toggle('sidebar-drawer-open', state.mobileSidebarOpen);
  refs.sidebarToggle.setAttribute('aria-expanded', state.mobileSidebarOpen ? 'true' : 'false');
}

function toggleSidebarCollapsed() {
  if (isMobileLayout()) return;
  state.sidebarCollapsed = !state.sidebarCollapsed;
  persistSidebarState();
  applySidebarState();
}

function bindDelegatedEvents() {
  // Single delegated click handler on panelView covers all dynamic table actions.
  // This avoids re-binding listeners every time a table is re-rendered.
  refs.panelView.addEventListener('click', async event => {
    // Holds module events (tabs, wizards, filters, create toggles, hold selection)
    if (typeof handleHoldsModuleClick === 'function' && handleHoldsModuleClick(event.target)) return;

    const target = event.target.closest('[data-open-message-menu],[data-report-message],[data-review-classify],[data-bulk-action],[data-open-conversation],[data-deactivate-conversation],[data-approve-message],[data-toggle-human-override],[data-reset-conversation],[data-scroll-composer],[data-approve-hold],[data-reject-hold],[data-restaurant-next-status],[data-restaurant-extend],[data-save-ticket],[data-facts-version-detail],[data-facts-version-rollback],[data-facts-conflict-restore-draft],[data-facts-conflict-dismiss]');
    if (!target) return;

    if (target.dataset.openMessageMenu) {
      const bubble = target.closest('[data-review-message]');
      if (bubble) openResponseContextMenuForBubble(bubble, target.getBoundingClientRect());
      return;
    }

    if (target.dataset.reportMessage) {
      await reportOperationMessage(target.dataset.reportConversation, target.dataset.reportMessage);
      return;
    }

    if (target.dataset.reviewClassify) {
      await submitResponseReviewClassification(target.dataset.reviewClassify);
      return;
    }

    if (target.dataset.bulkAction) {
      runConversationBulkAction(target.dataset.bulkAction);
      return;
    }

    // Conversation detail
    if (target.dataset.openConversation) {
      loadConversationDetail(target.dataset.openConversation);
      return;
    }

    if (target.dataset.approveMessage) {
      const convId = target.dataset.approveConversation;
      const msgId = target.dataset.approveMessage;
      if (!convId || !msgId) return;
      if (!confirm('Bu AI taslağını WhatsApp üzerinden göndermek istediğinize emin misiniz?')) return;
      const originalLabel = target.textContent;
      target.disabled = true;
      target.textContent = 'Gönderiliyor...';
      try {
        await apiFetch(`/conversations/${convId}/messages/${msgId}/send`, {method: 'POST'});
        notify('Yanıt onaylandı ve gönderildi.', 'success');
        await loadConversationDetail(convId);
        await loadConversations();
      } catch (error) {
        target.disabled = false;
        target.textContent = originalLabel;
        notify(error.message || 'Gönderim başarısız.', 'error');
      }
      return;
    }

    if (target.dataset.toggleHumanOverride) {
      const convId = target.dataset.toggleHumanOverride;
      const currentlyEnabled = target.dataset.currentOverride === 'true';
      const newState = !currentlyEnabled;
      const confirmMsg = newState
        ? 'Bu konuşmayı insan devrine almak istediğinize emin misiniz? Yapay zekâ yanıt üretir ancak otomatik gönderim durur.'
        : 'Bu konuşmayı tekrar AI moduna almak istediğinize emin misiniz? Uygun yanıtlar otomatik gönderilebilir.';
      if (!confirm(confirmMsg)) return;
      try {
        await apiFetch(`/conversations/${convId}/human-override?enable=${newState}`, {method: 'POST'});
        notify(newState ? 'İnsan devri aktif. Otomatik gönderim durdu.' : 'AI modu aktif.', 'success');
        await loadConversationDetail(convId);
        await loadConversations();
      } catch (error) {
        notify(error.message || 'Mod değiştirilemedi.', 'error');
      }
      return;
    }

    if (target.dataset.resetConversation) {
      const convId = target.dataset.resetConversation;
      if (!confirm('Bu konuşmayı sıfırlamak istediğinize emin misiniz?')) return;
      try {
        await apiFetch(`/conversations/${convId}/reset`, {method: 'POST'});
        notify('Konuşma sıfırlandı.', 'success');
        state.conversationDetail = null;
        await loadConversations();
      } catch (error) {
        notify(error.message || 'Sıfırlama başarısız.', 'error');
      }
      return;
    }

    if (target.dataset.scrollComposer) {
      refs.conversationDetail?.querySelector('[data-message-composer]')?.focus();
      return;
    }

    // Deactivate conversation
    if (target.dataset.deactivateConversation) {
      const convId = target.dataset.deactivateConversation;
      if (!confirm('Bu konuşmayı pasife almak istediğinize emin misiniz?')) return;
      try {
        await apiFetch(`/conversations/${convId}/deactivate`, {method: 'POST'});
        notify('Konuşma pasife alındı.', 'success');
        loadConversations();
      } catch (error) {
        notify(error.message || 'Pasife alma başarısız.', 'error');
      }
      return;
    }

    // Hold approve
    if (target.dataset.approveHold) {
      const approveButton = target;
      const originalLabel = approveButton.textContent;
      approveButton.disabled = true;
      approveButton.textContent = 'Onaylanıyor...';
      try {
        const result = await apiFetch(`/holds/${target.dataset.approveHold}/approve?force=true`, {method: 'POST', body: {notes: ''}});
        if (result && result.status === 'already_processed') {
          notify('Onay kaydı zaten işlenmiş durumda. Tekrar onay tetiklenmedi.', 'info');
        } else {
          notify('Onay kaydı onaylandı.', 'success');
        }
        const tab = state.activeHoldsTab || 'stay';
        if (tab === 'stay') loadStayHolds();
        else if (tab === 'restaurant') loadRestaurantHolds();
        else loadTransferHolds();
        loadDashboard();
      } catch (error) {
        approveButton.disabled = false;
        approveButton.textContent = originalLabel;
        notify(error.message, 'error');
      }
      return;
    }

    // Hold reject
    if (target.dataset.rejectHold) {
      refs.decisionMode.value = 'reject';
      refs.decisionHoldId.value = target.dataset.rejectHold;
      refs.decisionTitle.textContent = 'Onay kaydını reddet';
      refs.decisionLead.textContent = 'İsterseniz gerekçe yazın; boş bırakarak da reddedebilirsiniz.';
      refs.decisionReason.value = '';
      refs.decisionDialog.showModal();
      return;
    }

    if (target.dataset.restaurantNextStatus) {
      const holdId = target.dataset.restaurantHold || '';
      const nextStatus = target.dataset.restaurantNextStatus || '';
      if (!holdId || !nextStatus) return;
      try {
        await apiFetch(`/holds/restaurant/${encodeURIComponent(holdId)}/status`, {method: 'PUT', body: {status: nextStatus}});
        notify('Restoran rezervasyonu güncellendi.', 'success');
        await loadRestaurantHolds();
        loadDashboard();
      } catch (error) {
        notify(error.message || 'Durum güncellenemedi.', 'error');
      }
      return;
    }

    if (target.dataset.restaurantExtend) {
      const holdId = target.dataset.restaurantExtend || '';
      if (!holdId) return;
      try {
        const result = await apiFetch(`/holds/restaurant/${encodeURIComponent(holdId)}/extend`, {method: 'POST'});
        notify(`Rezervasyon saati ${result.new_time || ''} olarak +15 dk güncellendi.`, 'success');
        await loadRestaurantHolds();
        loadDashboard();
      } catch (error) {
        notify(error.message || 'Uzatma başarısız.', 'error');
      }
      return;
    }

    // Ticket save
    if (target.dataset.saveTicket) {
      const ticketId = target.dataset.saveTicket;
      const statusField = document.querySelector(`[data-ticket-status="${ticketId}"]`);
      try {
        await apiFetch(`/tickets/${ticketId}`, {method: 'PUT', body: {status: statusField.value}});
        notify('Talep güncellendi.', 'success');
        loadTickets();
        loadDashboard();
      } catch (error) {
        notify(error.message, 'error');
      }
      return;
    }

    if (target.dataset.factsVersionDetail && typeof loadHotelFactsVersionDetail === 'function') {
      loadHotelFactsVersionDetail(target.dataset.factsVersionDetail);
      return;
    }

    if (target.dataset.factsVersionRollback && typeof rollbackHotelFacts === 'function') {
      rollbackHotelFacts(target.dataset.factsVersionRollback);
      return;
    }

    if (target.dataset.factsConflictRestoreDraft && typeof restoreHotelFactsConflictDraft === 'function') {
      restoreHotelFactsConflictDraft();
      return;
    }

    if (target.dataset.factsConflictDismiss && typeof dismissHotelFactsConflict === 'function') {
      dismissHotelFactsConflict();
    }
  });
}

async function boot() {
  await Promise.all([loadBootstrapStatus(), loadSessionStatus()]);

  // ── Proactive session recovery ──────────────────────────
  // The access cookie is httpOnly, so the browser UI cannot inspect it.
  // When a remembered session exists, refresh first and let terminal
  // trusted-device failures decide whether the login screen is required.
  const status = state.sessionStatus || {};
  if (status.has_trusted_device && status.session_active) {
    const recovered = await refreshAccessSession({silent: true});
    if (!recovered && isTerminalRefreshFailure(state.lastRefreshFailure)) {
      showAuth();
      return;
    }
  }

  try {
    await hydrateSession();
    if (!isLocalDemoAuth()) {
      startAuthKeepAlive();
    }
    return;
  } catch (error) {
    if (error?.recoverableAuthRefresh) {
      notify(error.message || 'Oturum geri yükleme geçici olarak tamamlanamadı; lütfen biraz sonra tekrar deneyin.', 'warn');
      return;
    }
    if (isTerminalAuthError(error) || !state.me) {
      showAuth();
      return;
    }
    notify(error.message || 'Panel verilerinin bir bölümü yüklenemedi.', 'warn');
  }
}

async function loadBootstrapStatus() {
  state.bootstrap = await apiFetch('/bootstrap/status', {auth: false});
  renderBootstrapState();
}

async function loadSessionStatus() {
  try {
    state.sessionStatus = await apiFetch('/session/status', {auth: false});
  } catch (_error) {
    state.sessionStatus = null;
  }
  renderLoginSessionState();
}

function renderBootstrapState() {
  const info = state.bootstrap || {};
  const hotelOptions = (info.hotel_options || []).map(item => (
    `<option value="${escapeHtml(item.hotel_id)}">${escapeHtml(item.hotel_id)} - ${escapeHtml(item.name)}</option>`
  )).join('');
  refs.bootstrapHotels.innerHTML = hotelOptions || '<option value="">Otel bulunamadı</option>';

  if (!info.bootstrap_required) {
    // Bootstrap already completed — hide the entire setup card.
    // No system metadata (domain, access mode, recovery form) is shown
    // to unauthenticated visitors.
    refs.bootstrapCard.hidden = true;
    refs.bootstrapForm.hidden = true;
    refs.totpRecovery.hidden = true;
    refs.otpVerifyForm.hidden = true;
    refs.otpVerifyHint.hidden = true;
    refs.bootstrapSummary.innerHTML = '';
    return;
  }

  refs.bootstrapForm.hidden = false;
  refs.totpRecovery.hidden = true;
  const accessMode = info.local_bootstrap_allowed
    ? 'Bu cihazdan localhost bootstrap açık.'
    : (info.token_bootstrap_enabled ? 'Bootstrap token gerekli.' : 'Bootstrap için localhost erişimi veya ENV token gerekli.');

  refs.bootstrapSummary.innerHTML = `
    <div class="helper-box">
      <strong>İlk yönetici hesabı gerekli</strong>
      <p>Veritabanında yönetici kullanıcısı yok. İlk hesap oluşturulduktan sonra panel doğrudan 2FA ile çalışacak.</p>
    </div>
    <div class="helper-box">
      <strong>Erişim modu</strong>
      <p>${escapeHtml(accessMode)}</p>
    </div>
  `;
  renderNavigation();
}

function renderLoginSessionState() {
  const status = state.sessionStatus || {};
  const verificationOptions = status.verification_options || [];
  const sessionOptions = status.session_options || [];
  const rememberChecked = refs.rememberDeviceToggle.checked || Boolean(status.has_trusted_device);

  refs.rememberDeviceToggle.checked = rememberChecked;
  renderChoiceGroup(
    refs.loginVerificationOptions,
    'verification_preset',
    verificationOptions,
    status.verification_preset || DEFAULT_VERIFICATION_PRESET,
  );
  renderChoiceGroup(
    refs.loginSessionOptions,
    'session_preset',
    sessionOptions,
    status.session_preset || DEFAULT_SESSION_PRESET,
  );
  toggleLoginRememberOptions();

  if (!status.has_trusted_device) {
    refs.trustedSessionBanner.hidden = true;
    setOtpMode({skipAllowed: false});
    return;
  }

  refs.trustedSessionBanner.hidden = false;
  refs.trustedSessionBanner.innerHTML = `
    <div class="helper-box">
      <strong>${escapeHtml(status.user_label || 'Bu cihaz')}</strong>
      <p>${escapeHtml(status.device_label || 'Tarayıcı cihazı')} için hızlı giriş durumu görünür.</p>
    </div>
    <div class="status-strip">
      <div class="helper-box">
        <strong>OTP tekrar süresi</strong>
        <p>${status.verification_active ? `Aktif · ${escapeHtml(formatDate(status.verification_expires_at))}` : 'Süresi doldu'}</p>
      </div>
      <div class="helper-box">
        <strong>Oturum hatırlama</strong>
        <p>${status.session_active ? `Aktif · ${escapeHtml(formatDate(status.session_expires_at))}` : 'Aktif değil'}</p>
      </div>
    </div>
    ${status.verification_active ? '<button id="loginForceOtpButton" class="inline-button secondary" type="button">Kodu yine de kullan</button>' : ''}
  `;

  setOtpMode({skipAllowed: Boolean(status.verification_active)});
  const forceOtpButton = document.getElementById('loginForceOtpButton');
  if (forceOtpButton) {
    forceOtpButton.addEventListener('click', () => setOtpMode({skipAllowed: false, forced: true}));
  }
}

function toggleLoginRememberOptions() {
  refs.loginRememberOptions.hidden = !refs.rememberDeviceToggle.checked;
}

function setOtpMode({skipAllowed, forced = false}) {
  const otpInput = refs.loginForm.otp_code;
  const shouldHide = skipAllowed && !forced;
  refs.loginOtpField.hidden = shouldHide;
  otpInput.required = !shouldHide;
  if (shouldHide) {
    otpInput.value = '';
  }
}

function renderChoiceGroup(container, name, options, selectedValue) {
  container.innerHTML = (options || []).map(option => `
    <label class="choice-card">
      <input type="radio" name="${escapeHtml(name)}" value="${escapeHtml(option.value)}" ${option.value === selectedValue ? 'checked' : ''}>
      <span>${escapeHtml(option.label)}</span>
    </label>
  `).join('');
}

async function onLogin(event) {
  event.preventDefault();
  const payload = formToJson(refs.loginForm);
  payload.remember_device = refs.rememberDeviceToggle.checked;
  payload.verification_preset = getSelectedChoice(refs.loginForm, 'verification_preset', state.sessionStatus?.verification_preset || DEFAULT_VERIFICATION_PRESET);
  payload.session_preset = getSelectedChoice(refs.loginForm, 'session_preset', state.sessionStatus?.session_preset || DEFAULT_SESSION_PRESET);
  if (!payload.otp_code) {
    delete payload.otp_code;
  }
  try {
    const response = await apiFetch('/login', {method: 'POST', body: payload, auth: false});
    notify(response.authentication_mode === 'trusted_device' ? 'Bu cihaz için OTP adımı atlandı.' : 'Oturum açıldı.', 'success');
    await loadSessionStatus();
    await hydrateSession();
    startAuthKeepAlive();
  } catch (error) {
    notify(error.message, 'error');
  }
}

async function onBootstrap(event) {
  event.preventDefault();
  const payload = formToJson(refs.bootstrapForm);
  payload.hotel_id = Number(payload.hotel_id);
  if (new TextEncoder().encode(String(payload.password || '')).length > 72) {
    notify('Şifre en fazla 72 byte olabilir.', 'warn');
    return;
  }
  try {
    const response = await apiFetch('/bootstrap', {method: 'POST', body: payload, auth: false});
    state.bootstrapPending = {
      username: payload.username,
      password: payload.password,
    };
    refs.otpSetup.hidden = false;
    refs.otpVerifyForm.hidden = false;
    refs.otpVerifyHint.hidden = false;
    refs.otpQrImage.src = response.otpauth_qr_svg_data_uri;
    refs.otpSecret.textContent = response.totp_secret;
    refs.otpUri.textContent = response.otpauth_uri;
    refs.loginForm.username.value = response.username;
    refs.loginForm.password.value = payload.password;
    notify('İlk yönetici hesabı oluşturuldu. QR okutun ve kodu doğrulayın.', 'success');
  } catch (error) {
    notify(error.message, 'error');
  }
}

async function onTotpRecovery(event) {
  event.preventDefault();
  const payload = formToJson(refs.totpRecoveryForm);
  const nextPassword = String(payload.new_password || '');
  if (nextPassword && new TextEncoder().encode(nextPassword).length > 72) {
    notify('Şifre en fazla 72 byte olabilir.', 'warn');
    return;
  }
  try {
    const response = await apiFetch('/bootstrap/recover-totp', {method: 'POST', body: payload, auth: false});
    refs.otpSetup.hidden = false;
    refs.otpVerifyForm.hidden = true;
    refs.otpVerifyHint.hidden = true;
    refs.otpQrImage.src = response.otpauth_qr_svg_data_uri;
    refs.otpSecret.textContent = response.totp_secret;
    refs.otpUri.textContent = response.otpauth_uri;
    refs.loginForm.username.value = response.username;
    if (nextPassword) {
      refs.loginForm.password.value = nextPassword;
      notify('2FA yenilendi. Yeni şifre ve Authenticator kodu ile giriş yapın.', 'success');
    } else {
      notify('2FA yenilendi. Mevcut şifreniz ve yeni Authenticator kodu ile giriş yapın.', 'success');
    }
  } catch (error) {
    notify(error.message, 'error');
  }
}

async function onBootstrapVerify(event) {
  event.preventDefault();
  if (!state.bootstrapPending) {
    notify('Önce ilk yönetici hesabını oluşturun.', 'warn');
    return;
  }
  const payload = formToJson(refs.otpVerifyForm);
  const loginPayload = {
    username: state.bootstrapPending.username,
    password: state.bootstrapPending.password,
    otp_code: payload.otp_code,
  };
  try {
    const response = await apiFetch('/login', {method: 'POST', body: loginPayload, auth: false});
    state.bootstrapPending = null;
    notify('Kurulum doğrulandı, oturum açıldı.', 'success');
    await loadSessionStatus();
    await hydrateSession();
    startAuthKeepAlive();
  } catch (error) {
    notify(error.message, 'error');
  }
}

async function hydrateSession() {
  state.me = await apiFetch('/me');
  state.hotels = await apiFetch('/hotels');
  const preferredHotel = resolvePreferredHotel();
  state.selectedHotelId = preferredHotel ? String(preferredHotel) : '';
  window.localStorage.setItem(HOTEL_KEY, state.selectedHotelId);
  populateHotelSelectors();
  showPanel();
  syncNavigationAccess();
  const hydrationResults = await Promise.allSettled([
    loadDashboard(),
    loadSystemOverview(),
    loadSessionPreferences(),
    loadDebugRunsSafely({preserveSelection: false}, {notifyOnError: false}),
  ]);
  const terminalAuthError = findTerminalHydrationAuthError(hydrationResults);
  if (terminalAuthError) {
    throw terminalAuthError;
  }
  const recoverableError = hydrationResults
    .filter(result => result.status === 'rejected')
    .map(result => result.reason)
    .find(error => error?.recoverableAuthRefresh);
  const firstNonAuthError = hydrationResults
    .filter(result => result.status === 'rejected')
    .map(result => result.reason)
    .find(error => !error?.recoverableAuthRefresh);
  if (recoverableError) {
    notify(recoverableError.message || 'Oturum yenileme geçici olarak tamamlanamadı; panel açık kalacak.', 'warn');
  } else if (firstNonAuthError) {
    notify(firstNonAuthError.message || 'Panel verilerinin bir bölümü yüklenemedi.', 'warn');
  }
  setView(state.currentView || 'conversations');
}

function findTerminalHydrationAuthError(results) {
  return results
    .filter(result => result.status === 'rejected')
    .map(result => result.reason)
    .find(error => isTerminalAuthError(error)) || null;
}

function resolvePreferredHotel() {
  if (state.me?.role !== 'ADMIN') {
    return state.me?.hotel_id || '';
  }
  if (state.selectedHotelId && state.hotels.some(item => String(item.hotel_id) === String(state.selectedHotelId))) {
    return state.selectedHotelId;
  }
  return state.hotels[0]?.hotel_id || '';
}

function populateHotelSelectors() {
  const options = state.hotels.map(item => (
    `<option value="${escapeHtml(item.hotel_id)}">${escapeHtml(item.hotel_id)} - ${escapeHtml(item.name_en || item.name_tr || 'Otel')}</option>`
  )).join('');
  refs.hotelSelect.innerHTML = options;
  refs.hotelProfileSelect.innerHTML = options;
  if (state.selectedHotelId) {
    refs.hotelSelect.value = state.selectedHotelId;
    refs.hotelProfileSelect.value = state.selectedHotelId;
  }
  refs.hotelSelect.disabled = state.me?.role !== 'ADMIN';
}

function hasPermission(permission) {
  const permissions = state.me?.permissions || [];
  if (Array.isArray(permissions)) {
    return permissions.includes(permission);
  }
  if (permissions instanceof Set) {
    return permissions.has(permission);
  }
  return false;
}

function isLocalDemoAuth() {
  return state.me?.auth_source === 'local_demo_bypass';
}

function syncNavigationAccess() {
  renderNavigation();
}

function showAuth() {
  clearLiveRefresh();
  stopDebugPolling();
  stopAuthKeepAlive();
  closeSidebar();
  refs.sidebar.hidden = true;
  refs.topbar.hidden = true;
  refs.authView.hidden = false;
  refs.panelView.hidden = true;
  refs.currentUser.textContent = 'Misafir değil, operasyon';
  refs.currentRole.textContent = 'Panel girişi bekleniyor';
  refs.hotelScope.textContent = CONFIG.public_host || 'nexlumeai.com';
  if (refs.logoutButton) refs.logoutButton.hidden = false;
  renderLoginSessionState();
}

function showPanel() {
  refs.sidebar.hidden = false;
  refs.topbar.hidden = false;
  refs.authView.hidden = true;
  refs.panelView.hidden = false;
  refs.currentUser.textContent = state.me?.display_name || state.me?.username || '-';
  refs.currentRole.textContent = state.me?.role || '-';
  refs.hotelScope.textContent = state.selectedHotelId || '-';
  if (refs.logoutButton) refs.logoutButton.hidden = isLocalDemoAuth();
  applySidebarState();
  renderNavigation();
}

function setView(view) {
  view = normalizeAdminViewKey(view);
  const navItem = getNavigationItem(view);
  if (state.me && navItem && !canAccessNavigationItem(navItem)) {
    notify('Bu bölümü görüntüleme yetkiniz bulunmuyor.', 'warn');
    view = canAccessNavigationItem(getNavigationItem('conversations')) ? 'conversations' : 'dashboard';
  }
  state.currentView = view;
  if (view && view !== 'debug') {
    state.lastDebugSourceView = view;
  }
  window.location.hash = view;
  if (view !== 'debug') {
    stopDebugPolling();
  }
  document.querySelectorAll('[data-view]').forEach(section => {
    section.hidden = section.dataset.view !== view;
  });
  updateNavigationState();

  const activeItem = getNavigationItem(view);
  const activeGroup = getNavigationGroupForView(view);
  const meta = activeItem
    ? [activeItem.title || activeItem.label, activeItem.lead || activeItem.subtitle || 'Yönetim merkezi']
    : ['Yönetim Paneli', 'Yönetim merkezi'];

  refs.pageTitle.textContent = meta[0];
  refs.pageLead.textContent = meta[1];
  if (refs.pageBreadcrumb) {
    refs.pageBreadcrumb.textContent = activeGroup ? `${activeGroup.label} / ${activeItem.label}` : 'Yönetim Paneli';
  }

  if (view === 'dashboard') loadDashboard();
  if (view === 'conversations') loadConversations();
  if (view === 'responsereview') loadResponseReviews({selectFromQuery: true});
  if (view === 'holds') switchHoldsTab(state.activeHoldsTab || 'stay');
  if (view === 'tickets') loadTickets();
  if (view === 'hotels') loadHotelProfileSection();
  if (view === 'faq') loadFaqs();
  if (view === 'restaurant') {
    loadRestaurantSlots();
    if (typeof loadRestaurantHolds === 'function') loadRestaurantHolds();
    if (typeof loadRestaurantSettings === 'function') loadRestaurantSettings();
  }
  if (view === 'restaurantai' && typeof loadRestaurantAiPanel === 'function') loadRestaurantAiPanel();
  if (view === 'notifications') loadNotifPhones();
  if (view === 'accesscontrol') loadAccessControl();
  if (view === 'system') loadSystemOverview();
  if (view === 'responsewindow') loadResponsePreview();
  if (view === 'voicelab') loadVoiceLab();
  if (view === 'chatlab') loadChatLab();
  if (view === 'debug') loadDebugRunsSafely({preserveSelection: true}, {notifyOnError: true});
  scheduleLiveRefresh();
}

function clearLiveRefresh() {
  if (state.liveRefreshHandle) {
    window.clearInterval(state.liveRefreshHandle);
    state.liveRefreshHandle = null;
  }
}

function scheduleLiveRefresh() {
  clearLiveRefresh();
  const refreshers = {
    dashboard: async () => loadDashboard(),
    conversations: async () => loadConversations(),
    holds: async () => {
      const tab = state.activeHoldsTab || 'stay';
      const loader = tab === 'transfer' ? loadTransferHolds : loadStayHolds;
      await Promise.all([loader(), loadDashboard()]);
    },
    restaurant: async () => {
      const tasks = [loadRestaurantSlots()];
      if (typeof loadRestaurantHolds === 'function') tasks.push(loadRestaurantHolds());
      await Promise.all(tasks);
    },
    restaurantai: async () => {
      if (typeof loadRestaurantAiPanel === 'function') await loadRestaurantAiPanel();
    },
  };
  const refresh = refreshers[state.currentView];
  if (!refresh) return;
  state.liveRefreshHandle = window.setInterval(() => {
    if (document.hidden) return;
    refresh().catch(() => {});
  }, LIVE_REFRESH_INTERVAL_MS);
}

function onHotelScopeChange() {
  state.selectedHotelId = refs.hotelSelect.value;
  refs.hotelProfileSelect.value = refs.hotelSelect.value;
  window.localStorage.setItem(HOTEL_KEY, state.selectedHotelId);
  refs.hotelScope.textContent = state.selectedHotelId || '-';
  state.voiceLabResult = null;
  state.voiceLabMatrixResults = [];
  state.voiceLabMatrixSummary = null;
  setView(state.currentView);
}

function openDebugRunModal() {
  if (!refs.debugRunDialog) return;
  if (!state.debugWorkerReady) {
    notify(state.debugWorkerMessage || 'Hata tarama işleyicisi hazır değil.', 'error');
    return;
  }
  if (!state.debugBrowserScanAvailable && state.debugBrowserScanMessage) {
    notify(`${state.debugBrowserScanMessage} HTTP/API taraması yine rapor üretecek.`, 'warn');
  }
  if (refs.debugStartButton?.disabled) {
    notify('Bu otel için zaten aktif bir hata taraması var.', 'warn');
    if (state.currentView !== 'debug') setView('debug');
    return;
  }
  refs.debugScopeAllPanel.checked = true;
  refs.debugScopeCurrentView.checked = false;
  refs.debugIncludeChatLab.checked = true;
  refs.debugIncludePopups.checked = true;
  refs.debugIncludeModals.checked = true;
  refs.debugRunDialog.showModal();
}

function closeDebugRunModal() {
  refs.debugRunDialog?.close();
}

function buildDebugRunPayload() {
  const target = refs.debugScopeCurrentView?.checked ? 'current_view' : 'all_panel';
  const effectiveView = state.currentView || state.lastDebugSourceView || 'conversations';
  return {
    mode: 'aggressive_report_only',
    scope: {
      target,
      target_view: target === 'current_view' ? effectiveView : null,
      include_chatlab_iframe: Boolean(refs.debugIncludeChatLab?.checked),
      include_popups: Boolean(refs.debugIncludePopups?.checked),
      include_modals: Boolean(refs.debugIncludeModals?.checked),
      scan_intensity: 'aggressive',
      report_only: true,
    },
  };
}

async function onDebugRunSubmit(event) {
  event.preventDefault();
  try {
    const run = await apiFetch('/debug/runs', {method: 'POST', body: buildDebugRunPayload()});
    state.activeDebugRunId = run.id;
    state.activeDebugFindingId = '';
    closeDebugRunModal();
    notify('Hata taraması başlatıldı. Bulgular rapor ekranında güncellenecek.', 'success');
    if (state.currentView !== 'debug') {
      setView('debug');
    } else {
      await loadDebugRuns({preserveSelection: false});
    }
  } catch (error) {
    if (error.status === 409) {
      closeDebugRunModal();
      notify(error.message, 'warn');
      if (state.currentView !== 'debug') {
        setView('debug');
      } else {
        await loadDebugRuns({preserveSelection: true});
      }
      return;
    }
    notify(error.message || 'Hata taraması başlatılamadı.', 'error');
  }
}

async function onDebugRunListClick(event) {
  const card = event.target.closest('[data-debug-run-id]');
  if (!card) return;
  const runId = card.dataset.debugRunId;
  if (!runId || runId === state.activeDebugRunId) return;
  state.activeDebugRunId = runId;
  state.activeDebugFindingId = '';
  await Promise.all([loadDebugRunDetail(runId), loadDebugFindings(runId), loadDebugArtifacts(runId)]);
  renderDebugView();
}

async function onDebugFindingListClick(event) {
  const card = event.target.closest('[data-debug-finding-id]');
  if (!card) return;
  state.activeDebugFindingId = card.dataset.debugFindingId || '';
  await loadDebugArtifacts(state.activeDebugRunId, state.activeDebugFindingId || null);
  renderDebugDetailPanel();
}

async function onDebugDetailClick(event) {
  const findingButton = event.target.closest('[data-debug-artifact-finding-id]');
  if (findingButton) {
    await openDebugArtifactFinding(
      findingButton.dataset.debugArtifactFindingId || '',
      findingButton.dataset.debugArtifactId || '',
    );
    return;
  }
  const previewButton = event.target.closest('[data-debug-artifact-preview]');
  if (previewButton) {
    openDebugArtifactPreview(previewButton.dataset.debugArtifactPreview || '');
    return;
  }
  const actionButton = event.target.closest('[data-debug-action]');
  if (!actionButton || !state.activeDebugRunId) return;
  const action = actionButton.dataset.debugAction;
  try {
    if (action === 'cancel') {
      await apiFetch(`/debug/runs/${encodeURIComponent(state.activeDebugRunId)}/cancel`, {method: 'POST', body: {}});
      notify('Hata taraması için iptal isteği işlendi.', 'success');
      await loadDebugRuns({preserveSelection: true});
      return;
    }
    if (action === 'retry') {
      const response = await apiFetch(`/debug/runs/${encodeURIComponent(state.activeDebugRunId)}/retry`, {method: 'POST', body: {}});
      state.activeDebugRunId = response.run?.id || state.activeDebugRunId;
      state.activeDebugFindingId = '';
      notify('Hata taraması yeniden kuyruğa alındı.', 'success');
      await loadDebugRuns({preserveSelection: true});
    }
  } catch (error) {
    notify(error.message || 'Hata taraması işlemi tamamlanamadı.', 'error');
  }
}

async function loadDebugRuns({preserveSelection = true, force = false} = {}) {
  if (state.debugRefreshPromise && !force) {
    return state.debugRefreshPromise;
  }
  const refreshPromise = (async () => {
    await loadDebugStatus();
    const response = await apiFetch('/debug/runs');
    state.debugRuns = Array.isArray(response.items) ? response.items : [];
    const hasSelectedRun = preserveSelection && state.activeDebugRunId && state.debugRuns.some(item => item.id === state.activeDebugRunId);
    if (!hasSelectedRun) {
      const activeRun = state.debugRuns.find(item => item.status === 'running' || item.status === 'queued');
      state.activeDebugRunId = activeRun?.id || state.debugRuns[0]?.id || '';
      state.activeDebugFindingId = '';
    }
    syncDebugTopbarState();
    renderDebugRunList();
    if (!state.activeDebugRunId) {
      state.debugRunDetail = null;
      state.debugFindings = [];
      state.debugArtifacts = [];
      state.debugRunArtifacts = [];
      state.debugArtifactScope = 'run';
      closeDebugArtifactPreview();
      stopDebugPolling();
      renderDebugView();
      return;
    }
    await Promise.all([
      loadDebugRunDetail(state.activeDebugRunId),
      loadDebugFindings(state.activeDebugRunId),
    ]);
    await loadDebugArtifacts(state.activeDebugRunId, state.activeDebugFindingId || null);
    renderDebugView();
  })();
  state.debugRefreshPromise = refreshPromise;
  try {
    return await refreshPromise;
  } finally {
    if (state.debugRefreshPromise === refreshPromise) {
      state.debugRefreshPromise = null;
    }
  }
}

async function loadDebugRunsSafely(options = {}, {notifyOnError = false} = {}) {
  try {
    await loadDebugRuns(options);
  } catch (error) {
    state.debugWorkerReady = false;
    state.debugWorkerMessage = 'Hata taraması verileri alınamadı.';
    syncDebugTopbarState();
    if (state.currentView === 'debug') {
      renderDebugView();
    }
    if (notifyOnError) {
      notify(error.message || 'Hata raporları yüklenemedi.', 'error');
    }
  }
}

async function loadDebugStatus() {
  try {
    const response = await apiFetch('/debug/status');
    state.debugWorkerReady = Boolean(response.worker_ready);
    state.debugWorkerMessage = String(response.active_run_message || '');
    state.debugBrowserScanAvailable = Boolean(response.browser_scan_available);
    state.debugBrowserScanMessage = String(response.browser_scan_reason || '');
    state.debugBrowserScanMode = String(response.browser_scan_mode || '');
    state.debugBrowserScanTarget = String(response.browser_scan_target || '');
  } catch (_error) {
    state.debugWorkerReady = false;
    state.debugWorkerMessage = 'Hata tarama işleyicisi durumu alınamadı.';
    state.debugBrowserScanAvailable = false;
    state.debugBrowserScanMessage = '';
    state.debugBrowserScanMode = '';
    state.debugBrowserScanTarget = '';
  }
}

async function loadDebugRunDetail(runId) {
  state.debugRunDetail = await apiFetch(`/debug/runs/${encodeURIComponent(runId)}`);
  const status = state.debugRunDetail?.status;
  if (status === 'queued' || status === 'running') {
    startDebugPolling(runId);
  } else {
    stopDebugPolling();
  }
}

async function loadDebugFindings(runId) {
  const response = await apiFetch(`/debug/runs/${encodeURIComponent(runId)}/findings`);
  state.debugFindings = Array.isArray(response.items) ? response.items : [];
  if (state.activeDebugFindingId && !state.debugFindings.some(item => item.id === state.activeDebugFindingId)) {
    state.activeDebugFindingId = '';
  }
}

async function fetchDebugArtifacts(runId, findingId = null) {
  const params = new URLSearchParams();
  if (findingId) params.set('finding_id', findingId);
  const query = params.toString();
  const response = await apiFetch(`/debug/runs/${encodeURIComponent(runId)}/artifacts${query ? `?${query}` : ''}`);
  return Array.isArray(response.items) ? response.items : [];
}

async function loadDebugArtifacts(runId, findingId = null) {
  if (!runId) {
    state.debugArtifacts = [];
    state.debugRunArtifacts = [];
    state.debugArtifactScope = 'run';
    closeDebugArtifactPreview();
    return;
  }
  if (!findingId) {
    state.debugRunArtifacts = await fetchDebugArtifacts(runId);
    state.debugArtifacts = [...state.debugRunArtifacts];
    state.debugArtifactScope = 'run';
  } else {
    const [runArtifacts, findingArtifacts] = await Promise.all([
      fetchDebugArtifacts(runId),
      fetchDebugArtifacts(runId, findingId),
    ]);
    state.debugRunArtifacts = runArtifacts;
    if (findingArtifacts.length) {
      state.debugArtifacts = findingArtifacts;
      state.debugArtifactScope = 'finding';
    } else {
      state.debugArtifacts = [...runArtifacts];
      state.debugArtifactScope = 'run_fallback';
    }
  }
  if (!state.debugArtifacts.some(item => item.id === state.activeDebugArtifactId)) {
    closeDebugArtifactPreview();
  }
  if (!state.debugArtifacts.some(item => item.id === state.highlightedDebugArtifactId)) {
    state.highlightedDebugArtifactId = '';
  }
}

function startDebugPolling(runId) {
  stopDebugPolling();
  state.debugPollingHandle = window.setInterval(() => {
    if (document.hidden || state.currentView !== 'debug') return;
    loadDebugRuns({preserveSelection: true}).catch(() => {});
  }, 3000);
}

function stopDebugPolling() {
  if (state.debugPollingHandle) {
    window.clearInterval(state.debugPollingHandle);
    state.debugPollingHandle = null;
  }
}

function describeDebugScope(scope) {
  if (!scope || typeof scope !== 'object') return '-';
  if (scope.target === 'current_view') {
    return `Aktif görünüm · ${scope.target_view || '-'}`;
  }
  return 'Tüm panel';
}

function debugStatusBadgeClass(status) {
  if (status === 'completed') return 'success';
  if (status === 'failed' || status === 'cancelled') return 'danger';
  if (status === 'running') return 'info';
  return 'warn';
}

function formatDebugStatusLabel(status) {
  return {
    queued: 'Kuyrukta',
    running: 'Çalışıyor',
    completed: 'Tamamlandı',
    failed: 'Başarısız',
    cancelled: 'İptal edildi',
  }[String(status || '').toLowerCase()] || String(status || '-');
}

function debugSeverityBadgeClass(severity) {
  if (severity === 'critical' || severity === 'high') return 'danger';
  if (severity === 'medium') return 'warn';
  if (severity === 'low') return 'success';
  return 'info';
}

function formatDebugSeverityLabel(severity) {
  return {
    critical: 'Kritik',
    high: 'Yüksek',
    medium: 'Orta',
    low: 'Düşük',
    info: 'Bilgi',
  }[String(severity || '').toLowerCase()] || String(severity || '-');
}

function formatDebugModeLabel(mode) {
  return {
    aggressive_report_only: 'Yalnızca raporlama',
    report_only: 'Yalnızca raporlama',
  }[String(mode || '').toLowerCase()] || String(mode || '-');
}

function formatDebugArtifactTypeLabel(artifactType) {
  if (artifactType === 'screenshot') return 'Ekran görüntüsü';
  if (artifactType === 'console_log') return 'Konsol kaydı';
  if (artifactType === 'network_log') return 'Ağ kaydı';
  if (artifactType === 'dom_snapshot') return 'DOM anlık görüntüsü';
  if (artifactType === 'trace') return 'İz kaydı';
  return artifactType || 'Kanıt';
}

function getDebugArtifactScreenLabel(item) {
  const screen = item?.metadata?.screen;
  if (screen) return String(screen);
  const storagePath = String(item?.storage_path || '');
  if (storagePath.includes('admin_shell')) return 'Yönetim Paneli';
  if (storagePath.includes('chatlab_shell')) return 'Test Paneli';
  return 'Diğer Kanıtlar';
}

function getDebugArtifactContextNote() {
  const finding = state.debugFindings.find(item => item.id === state.activeDebugFindingId);
  if (finding && state.debugArtifactScope === 'finding') {
    return 'Bu kanıt listesi yalnızca seçili bulguya bağlı kanıtları gösterir.';
  }
  if (finding && state.debugArtifactScope === 'run_fallback') {
    return 'Bu bulguya doğrudan bağlı kanıt yok. Aşağıda tarama seviyesinde kaydedilen kanıtlar gösteriliyor.';
  }
  const findingCount = Number(state.debugRunDetail?.summary?.finding_count || 0);
  if (!finding && findingCount === 0) {
    return 'Bu tarama temiz tamamlandı. Aşağıdaki görseller bulgu değil, taramanın gerçekten hangi ekranlara ulaştığının kanıtıdır.';
  }
  return 'Aşağıdaki kanıtlar tarama sırasında kaydedilen ekran görüntüsü ve teknik kayıtlardır.';
}

function groupDebugArtifacts(items) {
  const groups = [];
  const byScreen = new Map();
  (items || []).forEach(item => {
    const screen = getDebugArtifactScreenLabel(item);
    if (!byScreen.has(screen)) {
      byScreen.set(screen, []);
      groups.push({screen, items: byScreen.get(screen)});
    }
    byScreen.get(screen).push(item);
  });
  return groups;
}

function safeDebugArtifactUrl(rawUrl) {
  const value = String(rawUrl || '').trim();
  if (!value) return '';
  try {
    const url = new URL(value, window.location.origin);
    if (url.origin !== window.location.origin) return '';
    if (!url.pathname.startsWith('/api/v1/admin/debug/runs/')) return '';
    return `${url.pathname}${url.search}${url.hash}`;
  } catch (_error) {
    return '';
  }
}

function isPreviewableDebugArtifact(item) {
  const mimeType = String(item?.mime_type || '');
  return Boolean(mimeType.startsWith('image/') && safeDebugArtifactUrl(item?.content_url));
}

function buildDebugArtifactMetaLine(item) {
  const parts = [
    formatDate(item.created_at) || '-',
    item?.metadata?.target_path || '',
  ].filter(Boolean);
  return parts.join(' · ');
}

function findDebugArtifactById(artifactId, items = state.debugArtifacts) {
  if (!artifactId) return null;
  return (items || []).find(item => item.id === artifactId) || null;
}

function getDebugArtifactRelatedFindingIds(item) {
  const explicitIds = Array.isArray(item?.metadata?.related_finding_ids)
    ? item.metadata.related_finding_ids.map(value => String(value || '').trim()).filter(Boolean)
    : [];
  if (explicitIds.length) return explicitIds;
  if (item?.finding_id) return [String(item.finding_id)];
  return [];
}

function debugFindingSeverityRank(severity) {
  return {
    critical: 5,
    high: 4,
    medium: 3,
    low: 2,
    info: 1,
  }[String(severity || '').toLowerCase()] || 0;
}

function getDebugArtifactRelatedFindings(item) {
  const explicitIds = getDebugArtifactRelatedFindingIds(item);
  const findingById = new Map(state.debugFindings.map(finding => [finding.id, finding]));
  const directMatches = explicitIds.map(id => findingById.get(id)).filter(Boolean);
  if (directMatches.length) return directMatches;
  const artifactScreen = String(item?.metadata?.screen || '');
  const artifactPath = String(item?.metadata?.target_path || '');
  const artifactViewKey = String(item?.metadata?.view_key || '');
  return state.debugFindings
    .map(finding => {
      let score = 0;
      if (artifactScreen && String(finding.screen || '') === artifactScreen) score += 3;
      if (artifactPath && String(finding?.evidence?.path || '') === artifactPath) score += 3;
      if (artifactPath && String(finding.action_label || '').includes(artifactPath)) score += 2;
      if (artifactViewKey && String(finding?.evidence?.target_view || '') === artifactViewKey) score += 1;
      return {finding, score};
    })
    .filter(item => item.score > 0)
    .sort((left, right) => {
      if (right.score !== left.score) return right.score - left.score;
      const severityDelta = debugFindingSeverityRank(right.finding.severity) - debugFindingSeverityRank(left.finding.severity);
      if (severityDelta !== 0) return severityDelta;
      return String(left.finding.created_at || '').localeCompare(String(right.finding.created_at || ''));
    })
    .map(item => item.finding);
}

function getDebugArtifactFindingJumpTarget(item) {
  return getDebugArtifactRelatedFindings(item).find(finding => finding.id !== state.activeDebugFindingId)
    || getDebugArtifactRelatedFindings(item)[0]
    || null;
}

function buildDebugArtifactFindingJumpLabel(item) {
  const relatedCount = getDebugArtifactRelatedFindings(item).length;
  if (relatedCount > 1) return `İlgili Bulgulara Git (${relatedCount})`;
  return 'İlgili Bulguyu Aç';
}

function resolveDebugArtifactHighlight(sourceArtifact, items = state.debugArtifacts) {
  if (!sourceArtifact) return null;
  const exactMatch = findDebugArtifactById(sourceArtifact.id, items);
  if (exactMatch) return exactMatch;
  const sourceRelatedIds = getDebugArtifactRelatedFindingIds(sourceArtifact);
  return (items || [])
    .map(candidate => {
      let score = 0;
      if (candidate.storage_path && candidate.storage_path === sourceArtifact.storage_path) score += 5;
      if (candidate.artifact_type === sourceArtifact.artifact_type) score += 2;
      if (String(candidate?.metadata?.target_key || '') === String(sourceArtifact?.metadata?.target_key || '')) score += 3;
      if (String(candidate?.metadata?.target_path || '') === String(sourceArtifact?.metadata?.target_path || '')) score += 3;
      if (String(candidate?.metadata?.screen || '') === String(sourceArtifact?.metadata?.screen || '')) score += 2;
      if (String(candidate?.metadata?.view_key || '') === String(sourceArtifact?.metadata?.view_key || '')) score += 1;
      if (candidate.finding_id && sourceRelatedIds.includes(String(candidate.finding_id))) score += 4;
      return {candidate, score};
    })
    .filter(item => item.score > 0)
    .sort((left, right) => right.score - left.score)
    .map(item => item.candidate)[0] || null;
}

function scrollActiveDebugFindingIntoView() {
  const cards = Array.from(refs.debugFindingList?.querySelectorAll?.('[data-debug-finding-id]') || []);
  const activeCard = cards.find(card => card?.dataset?.debugFindingId === state.activeDebugFindingId);
  activeCard?.scrollIntoView?.({block: 'nearest', behavior: 'smooth'});
}

function scrollHighlightedDebugArtifactIntoView() {
  const cards = Array.from(refs.debugDetailPanel?.querySelectorAll?.('[data-debug-artifact-id]') || []);
  const activeCard = cards.find(card => card?.dataset?.debugArtifactId === state.highlightedDebugArtifactId);
  activeCard?.scrollIntoView?.({block: 'nearest', behavior: 'smooth'});
}

async function openDebugArtifactFinding(findingId, sourceArtifactId = '') {
  if (!findingId || !state.activeDebugRunId) return;
  if (!state.debugFindings.some(item => item.id === findingId)) {
    notify('İlgili bulgu artık listede bulunmuyor.', 'warn');
    return;
  }
  const sourceArtifact = findDebugArtifactById(sourceArtifactId, state.debugArtifacts);
  state.activeDebugFindingId = findingId;
  await loadDebugArtifacts(state.activeDebugRunId, findingId);
  state.highlightedDebugArtifactId = sourceArtifact
    ? (resolveDebugArtifactHighlight(sourceArtifact)?.id || '')
    : '';
  renderDebugFindingList();
  renderDebugDetailPanel();
  window.requestAnimationFrame(() => {
    scrollActiveDebugFindingIntoView();
    scrollHighlightedDebugArtifactIntoView();
  });
}

function openDebugArtifactPreview(artifactId) {
  const artifact = state.debugArtifacts.find(item => item.id === artifactId);
  if (!artifact || !refs.debugArtifactPreviewDialog) return;
  const contentUrl = safeDebugArtifactUrl(artifact.content_url);
  state.activeDebugArtifactId = artifact.id || '';
  state.highlightedDebugArtifactId = artifact.id || state.highlightedDebugArtifactId;
  refs.debugArtifactPreviewTitle.textContent = `${formatDebugArtifactTypeLabel(artifact.artifact_type)} · ${getDebugArtifactScreenLabel(artifact)}`;
  refs.debugArtifactPreviewMeta.textContent = buildDebugArtifactMetaLine(artifact) || 'Kanıt ayrıntıları';
  refs.debugArtifactPreviewPath.textContent = String(artifact.storage_path || '-');
  if (contentUrl) {
    refs.debugArtifactPreviewLink.hidden = false;
    refs.debugArtifactPreviewLink.href = contentUrl;
  } else {
    refs.debugArtifactPreviewLink.hidden = true;
    refs.debugArtifactPreviewLink.removeAttribute('href');
  }
  if (isPreviewableDebugArtifact(artifact)) {
    refs.debugArtifactPreviewImage.hidden = false;
    refs.debugArtifactPreviewImage.src = contentUrl;
    refs.debugArtifactPreviewImage.alt = refs.debugArtifactPreviewTitle.textContent;
    refs.debugArtifactPreviewEmpty.hidden = true;
  } else {
    refs.debugArtifactPreviewImage.hidden = true;
    refs.debugArtifactPreviewImage.removeAttribute('src');
    refs.debugArtifactPreviewEmpty.hidden = false;
  }
  if (!refs.debugArtifactPreviewDialog.open) {
    refs.debugArtifactPreviewDialog.showModal();
  }
}

function closeDebugArtifactPreview() {
  state.activeDebugArtifactId = '';
  if (refs.debugArtifactPreviewDialog?.open) {
    refs.debugArtifactPreviewDialog.close();
  }
}

function syncDebugTopbarState() {
  const activeRun = state.debugRuns.find(item => item.status === 'running' || item.status === 'queued');
  if (!refs.debugTopbarStatus || !refs.debugStartButton) return;
  refs.debugTopbarStatus.hidden = false;
  if (!state.debugWorkerReady) {
    refs.debugTopbarStatus.textContent = state.debugWorkerMessage || 'İşleyici kapalı';
    refs.debugTopbarStatus.className = 'badge danger';
    refs.debugStartButton.disabled = true;
    return;
  }
  if (!activeRun) {
    if (!state.debugBrowserScanAvailable && state.debugBrowserScanMessage) {
      refs.debugTopbarStatus.textContent = 'HTTP taraması hazır · ekran görüntüsü yok';
      refs.debugTopbarStatus.className = 'badge warn';
    } else {
      refs.debugTopbarStatus.textContent = 'Boşta';
      refs.debugTopbarStatus.className = 'badge info';
    }
    refs.debugStartButton.disabled = false;
    return;
  }
  refs.debugStartButton.disabled = true;
  if (activeRun.status === 'running') {
    refs.debugTopbarStatus.textContent = 'Tarama sürüyor';
    refs.debugTopbarStatus.className = 'badge warn';
    return;
  }
  refs.debugTopbarStatus.textContent = 'Tarama kuyruğa alındı';
  refs.debugTopbarStatus.className = 'badge info';
}

function renderDebugView() {
  renderDebugRunList();
  renderDebugFindingList();
  renderDebugSummary();
  renderDebugDetailPanel();
  syncDebugTopbarState();
}

function renderDebugRunList() {
  if (!refs.debugRunList) return;
  if (!state.debugRuns.length) {
    refs.debugRunList.innerHTML = `
      <div class="empty-state">
        <h4>Henüz hata taraması yok</h4>
        <p>Üst çubuktaki Hata Taraması butonundan yeni bir tarama başlatabilirsiniz.</p>
      </div>
    `;
    return;
  }
  refs.debugRunList.innerHTML = state.debugRuns.map(item => {
    const isActive = item.id === state.activeDebugRunId;
    return `
      <article class="debug-run-card ${isActive ? 'is-active' : ''}" data-debug-run-id="${escapeHtml(item.id)}">
        <header>
          <div>
            <h4>${escapeHtml(describeDebugScope(item.scope))}</h4>
            <div class="muted">${escapeHtml(formatDate(item.queued_at) || '-')}</div>
          </div>
          <span class="pill ${debugStatusBadgeClass(item.status)}">${escapeHtml(formatDebugStatusLabel(item.status))}</span>
        </header>
      <div class="muted">${escapeHtml(item.failure_reason || 'Tarama kaydı oluşturuldu ve işlenmeyi bekliyor.')}</div>
        <div class="debug-card-meta">
          <span>${escapeHtml(formatDebugModeLabel(item.mode))}</span>
          <span>${escapeHtml(String(item.finding_count || 0))} bulgu</span>
        </div>
      </article>
    `;
  }).join('');
}

function renderDebugFindingList() {
  if (!refs.debugFindingList || !refs.debugFindingCountBadge) return;
  refs.debugFindingCountBadge.textContent = `${state.debugFindings.length} kayıt`;
  if (!state.activeDebugRunId) {
    refs.debugFindingList.innerHTML = `
      <div class="empty-state">
        <h4>Tarama seçilmedi</h4>
        <p>Bulguları görmek için soldan bir tarama kaydı seçin.</p>
      </div>
    `;
    return;
  }
  if (!state.debugFindings.length) {
    const waitingText = state.debugRunDetail?.status === 'queued' || state.debugRunDetail?.status === 'running'
      ? 'Tarama sürüyor. Bulgular geldikçe burada listelenecek.'
      : 'Bu tarama için henüz bulgu üretilmedi.';
    refs.debugFindingList.innerHTML = `
      <div class="empty-state">
        <h4>Bulgu bekleniyor</h4>
        <p>${escapeHtml(waitingText)}</p>
      </div>
    `;
    return;
  }
  refs.debugFindingList.innerHTML = state.debugFindings.map(item => `
    <article class="debug-finding-card ${item.id === state.activeDebugFindingId ? 'is-active' : ''}" data-debug-finding-id="${escapeHtml(item.id)}">
      <header>
        <div>
          <h4>${escapeHtml(item.screen || '-')}</h4>
          <div class="muted">${escapeHtml(item.action_label || item.category)}</div>
        </div>
        <span class="pill ${debugSeverityBadgeClass(item.severity)}">${escapeHtml(formatDebugSeverityLabel(item.severity))}</span>
      </header>
      <div>${escapeHtml(item.description || '-')}</div>
      <div class="debug-card-meta">
        <span>${escapeHtml(item.category || '-')}</span>
        <span>${escapeHtml(formatDate(item.created_at) || '-')}</span>
      </div>
    </article>
  `).join('');
}

function renderDebugSummary() {
  if (!refs.debugActiveRunStatus || !refs.debugActiveRunMeta || !refs.debugSummaryFindings || !refs.debugSummaryCounts || !refs.debugSummaryScope) {
    return;
  }
  const run = state.debugRunDetail;
  if (!run) {
    refs.debugActiveRunStatus.textContent = '-';
    refs.debugActiveRunMeta.textContent = 'Henüz tarama başlatılmadı.';
    refs.debugSummaryFindings.textContent = '0';
    refs.debugSummaryCounts.textContent = 'Kritik 0 / Yüksek 0 / Orta 0 / Düşük 0';
    refs.debugSummaryScope.textContent = '-';
    return;
  }
  const summary = run.summary || {};
    refs.debugActiveRunStatus.textContent = formatDebugStatusLabel(run.status);
  refs.debugActiveRunMeta.textContent = run.failure_reason || `${formatDate(run.queued_at) || '-'} · ${describeDebugScope(run.scope)}`;
  refs.debugSummaryFindings.textContent = String(summary.finding_count || state.debugFindings.length || 0);
  refs.debugSummaryCounts.textContent = `Kritik ${summary.critical_count || 0} / Yüksek ${summary.high_count || 0} / Orta ${summary.medium_count || 0} / Düşük ${summary.low_count || 0}`;
  refs.debugSummaryScope.textContent = describeDebugScope(run.scope);
}

function renderDebugDetailPanel() {
  if (!refs.debugDetailPanel) return;
  const finding = state.debugFindings.find(item => item.id === state.activeDebugFindingId);
  const artifactMarkup = renderDebugArtifacts();
  if (finding) {
    refs.debugDetailPanel.innerHTML = `
      <div class="debug-detail-grid">
        <div class="debug-detail-section">
          <strong>Sorun Özeti</strong>
          <div><span class="pill ${debugSeverityBadgeClass(finding.severity)}">${escapeHtml(formatDebugSeverityLabel(finding.severity))}</span></div>
          <p>${escapeHtml(finding.description || '-')}</p>
        </div>
        <div class="debug-detail-section">
          <strong>Tekrar Üretim Adımları</strong>
          <pre>${escapeHtml((finding.steps || []).join('\\n') || 'Adım kaydı yok.')}</pre>
        </div>
        <div class="debug-detail-section">
          <strong>Olası Teknik Neden</strong>
          <pre>${escapeHtml(finding.technical_cause || 'Henüz eklenmedi.')}</pre>
        </div>
        <div class="debug-detail-section">
          <strong>Önerilen Düzeltme</strong>
          <pre>${escapeHtml(finding.suggested_fix || 'Henüz eklenmedi.')}</pre>
        </div>
        <div class="debug-detail-section">
          <strong>Kanıt</strong>
          <pre>${escapeHtml(JSON.stringify(finding.evidence || {}, null, 2) || '{}')}</pre>
        </div>
        <div class="debug-detail-section">
          <strong>Kanıtlar</strong>
          ${artifactMarkup}
        </div>
      </div>
    `;
    return;
  }
  if (!state.debugRunDetail) {
    refs.debugDetailPanel.innerHTML = `
      <div class="empty-state">
        <h4>Seçim bekleniyor</h4>
        <p>Detay görmek için soldan bir tarama veya ortadan bir bulgu seçin.</p>
      </div>
    `;
    return;
  }
  const run = state.debugRunDetail;
  refs.debugDetailPanel.innerHTML = `
    <div class="debug-detail-grid">
      <div class="debug-detail-section">
        <strong>Tarama Durumu</strong>
        <div class="debug-toolbar">
          <span class="pill ${debugStatusBadgeClass(run.status)}">${escapeHtml(formatDebugStatusLabel(run.status))}</span>
          <span class="pill info">${escapeHtml(describeDebugScope(run.scope))}</span>
        </div>
        <p class="muted">${escapeHtml(run.failure_reason || 'Tarama ayrıntıları aşağıda özetleniyor.')}</p>
      </div>
      <div class="debug-detail-section">
        <strong>Zaman Çizelgesi</strong>
        <pre>${escapeHtml([
          `Kuyruğa alındı: ${formatDate(run.queued_at) || '-'}`,
          `Başladı: ${formatDate(run.started_at) || '-'}`,
          `Bitti: ${formatDate(run.finished_at) || '-'}`,
          `Son canlılık sinyali: ${formatDate(run.last_heartbeat_at) || '-'}`,
        ].join('\\n'))}</pre>
      </div>
      <div class="debug-detail-section">
        <strong>Özet</strong>
        <pre>${escapeHtml(JSON.stringify(run.summary || {}, null, 2))}</pre>
      </div>
      <div class="debug-detail-section">
        <strong>İşlemler</strong>
        <div class="debug-toolbar">
          <button class="inline-button secondary" type="button" data-debug-action="cancel"${run.status === 'completed' || run.status === 'failed' || run.status === 'cancelled' ? ' disabled' : ''}>İptal Et</button>
          <button class="inline-button primary" type="button" data-debug-action="retry">Yeniden Çalıştır</button>
        </div>
      </div>
      <div class="debug-detail-section">
        <strong>Kanıtlar</strong>
        ${artifactMarkup}
      </div>
    </div>
  `;
}

function renderDebugArtifacts() {
  if (!state.debugArtifacts.length) {
    return `
      <div class="debug-empty-compact">
        <h4>Kanıt bulunamadı</h4>
        <p>Bu seçim için henüz ekran görüntüsü veya ek kanıt kaydedilmedi.</p>
      </div>
    `;
  }
  const groups = groupDebugArtifacts(state.debugArtifacts);
  const screenCount = groups.length;
  const scopeLabel = state.debugArtifactScope === 'finding'
    ? 'Bulgu kanıtı'
    : (state.debugArtifactScope === 'run_fallback' ? 'Tarama kanıtı (yedek)' : 'Tarama kanıtı');
  return `
    <div class="debug-artifact-groups">
      <section class="debug-artifact-summary">
        <strong>${escapeHtml(scopeLabel)} · ${escapeHtml(String(state.debugArtifacts.length))} kanıt · ${escapeHtml(String(screenCount))} ekran</strong>
        <p>${escapeHtml(getDebugArtifactContextNote())}</p>
      </section>
      ${groups.map(group => `
        <section class="debug-artifact-group">
          <div class="debug-artifact-group-head">
            <strong>${escapeHtml(group.screen)}</strong>
            <span>${escapeHtml(String(group.items.length))} kayıt</span>
          </div>
          <div class="debug-artifact-list">
            ${group.items.map(item => {
              const typeLabel = formatDebugArtifactTypeLabel(item.artifact_type);
              const contentUrl = safeDebugArtifactUrl(item.content_url);
              const preview = isPreviewableDebugArtifact(item)
                ? `<img class="debug-artifact-preview" src="${escapeHtml(contentUrl)}" alt="${escapeHtml(typeLabel)}" data-debug-artifact-preview="${escapeHtml(item.id || '')}">`
                : `<div class="debug-empty-compact"><p>${escapeHtml(item.mime_type || 'İkili dosya')}</p></div>`;
              const findingTarget = getDebugArtifactFindingJumpTarget(item);
              const isHighlighted = item.id === state.highlightedDebugArtifactId;
              const actionButtons = [
                findingTarget && findingTarget.id !== state.activeDebugFindingId
                  ? `<button class="debug-artifact-link secondary" type="button" data-debug-artifact-finding-id="${escapeHtml(findingTarget.id)}" data-debug-artifact-id="${escapeHtml(item.id || '')}">${escapeHtml(buildDebugArtifactFindingJumpLabel(item))}</button>`
                  : '',
                isPreviewableDebugArtifact(item)
                  ? `<button class="debug-artifact-link secondary" type="button" data-debug-artifact-preview="${escapeHtml(item.id || '')}">Önizle</button>`
                  : '',
                contentUrl
                  ? `<a class="debug-artifact-link" href="${escapeHtml(contentUrl)}" target="_blank" rel="noopener noreferrer">Yeni Sekmede Aç</a>`
                  : '',
              ].filter(Boolean).join('');
              return `
                <article class="debug-artifact-card ${isHighlighted ? 'is-active' : ''}" data-debug-artifact-id="${escapeHtml(item.id || '')}">
                  <div>
                    <strong>${escapeHtml(typeLabel)}</strong>
                    <span>${escapeHtml(buildDebugArtifactMetaLine(item) || '-')}</span>
                  </div>
                  ${preview}
                  <code>${escapeHtml(item.storage_path || '-')}</code>
                  <div class="debug-artifact-actions">${actionButtons}</div>
                </article>
              `;
            }).join('')}
          </div>
        </section>
      `).join('')}
    </div>
  `;
}

async function loadVoiceLab() {
  renderVoiceLabSummary();
  renderVoiceLabResult();
  renderVoiceLabMatrix();
  syncVoiceLabSpeechControls();
  syncVoiceLabRealtimeControls();
  if (state.voiceLabScenarios.length) {
    renderVoiceLabScenarioOptions();
    return;
  }
  try {
    const response = await apiFetch('/voice-lab/scenarios');
    state.voiceLabScenarios = Array.isArray(response.items) ? response.items : [];
    renderVoiceLabScenarioOptions();
    renderVoiceLabSummary();
    renderVoiceLabMatrix();
  } catch (error) {
    notify(error.message, 'error');
  }
}

function renderVoiceLabScenarioOptions() {
  if (!refs.voiceLabScenario) return;
  const currentValue = refs.voiceLabScenario.value || '';
  const options = ['<option value="">Otomatik eşleştir</option>'].concat(
    state.voiceLabScenarios.map(item => (
      `<option value="${escapeHtml(item.scenario_id || '')}">${escapeHtml(item.scenario_id || '-')} · ${escapeHtml(item.expected_intent || '-')}</option>`
    ))
  );
  refs.voiceLabScenario.innerHTML = options.join('');
  if (currentValue && state.voiceLabScenarios.some(item => item.scenario_id === currentValue)) {
    refs.voiceLabScenario.value = currentValue;
  }
}

function findVoiceLabScenario(scenarioId) {
  return state.voiceLabScenarios.find(item => item.scenario_id === scenarioId) || null;
}

function onVoiceLabScenarioChange() {
  const scenario = findVoiceLabScenario(refs.voiceLabScenario?.value || '');
  if (!scenario) return;
  if (refs.voiceLabTranscript) {
    refs.voiceLabTranscript.value = scenario.sample_input || '';
    refs.voiceLabTranscript.focus();
  }
  stopVoiceLabSpeech({silent: true});
  syncVoiceLabSpeechControls();
}

function onVoiceLabSampleClick(event) {
  const target = event.target.closest('[data-voice-sample]');
  if (!target || !refs.voiceLabSampleList?.contains(target)) return;
  const scenario = findVoiceLabScenario(target.dataset.voiceSample || '');
  if (!scenario) {
    notify('Senaryo listesi henüz yüklenmedi.', 'warn');
    return;
  }
  if (refs.voiceLabScenario) refs.voiceLabScenario.value = scenario.scenario_id || '';
  if (refs.voiceLabTranscript) {
    refs.voiceLabTranscript.value = scenario.sample_input || '';
    refs.voiceLabTranscript.focus();
  }
  stopVoiceLabSpeech({silent: true});
  state.voiceLabResult = null;
  renderVoiceLabResult();
}

async function onVoiceLabSubmit(event) {
  event.preventDefault();
  stopVoiceLabSpeech({silent: true});
  const transcript = String(refs.voiceLabTranscript?.value || '').trim();
  if (!transcript) {
    notify('Arama transkripti zorunludur.', 'warn');
    return;
  }
  if (!state.selectedHotelId) {
    notify('Lütfen bir otel seçin.', 'warn');
    return;
  }

  setVoiceLabLoading(true);
  try {
    state.voiceLabResult = await apiFetch('/voice-lab/run', {
      method: 'POST',
      body: {
        hotel_id: Number(state.selectedHotelId),
        transcript,
        language: getVoiceLabLanguage(),
        scenario_id: String(refs.voiceLabScenario?.value || '') || null,
      },
    });
    renderVoiceLabResult();
    renderVoiceLabSummary();
    notify('Voice Lab senaryosu çalıştırıldı.', 'success');
  } catch (error) {
    notify(error.message, 'error');
  } finally {
    setVoiceLabLoading(false);
  }
}

async function runVoiceLabMatrix() {
  stopVoiceLabSpeech({silent: true});
  if (!state.selectedHotelId) {
    notify('Lütfen bir otel seçin.', 'warn');
    return;
  }
  setVoiceLabLoading(true);
  try {
    const response = await apiFetch('/voice-lab/run-matrix', {
      method: 'POST',
      body: {
        hotel_id: Number(state.selectedHotelId),
        language: getVoiceLabLanguage(),
      },
    });
    state.voiceLabMatrixSummary = response.summary || null;
    state.voiceLabMatrixResults = Array.isArray(response.items) ? response.items : [];
    state.voiceLabResult = state.voiceLabMatrixResults[0] || state.voiceLabResult;
    renderVoiceLabSummary();
    renderVoiceLabResult();
    renderVoiceLabMatrix();
    notify('Voice Lab matrisi çalıştırıldı.', 'success');
  } catch (error) {
    notify(error.message, 'error');
  } finally {
    setVoiceLabLoading(false);
  }
}

function clearVoiceLab() {
  stopVoiceLabSpeech({silent: true});
  stopVoiceLabRealtime({silent: true});
  if (refs.voiceLabTranscript) refs.voiceLabTranscript.value = '';
  if (refs.voiceLabScenario) refs.voiceLabScenario.value = '';
  state.voiceLabResult = null;
  state.voiceLabMatrixResults = [];
  state.voiceLabMatrixSummary = null;
  renderVoiceLabSummary();
  renderVoiceLabResult();
  renderVoiceLabMatrix();
  if (voiceLabSpeechSupported()) {
    setVoiceLabVoiceStatus('Karşılama veya son yanıt sesini dinleyebilirsiniz.');
  } else {
    syncVoiceLabSpeechControls();
  }
}

function setVoiceLabLoading(isLoading) {
  state.voiceLabLoading = isLoading;
  if (refs.voiceLabRunButton) {
    refs.voiceLabRunButton.disabled = isLoading;
    refs.voiceLabRunButton.textContent = isLoading ? 'Çalıştırılıyor...' : 'Senaryoyu Çalıştır';
  }
  if (refs.voiceLabRunMatrixButton) {
    refs.voiceLabRunMatrixButton.disabled = isLoading;
    refs.voiceLabRunMatrixButton.textContent = isLoading ? 'Matris Çalışıyor...' : 'Tüm Matrisi Çalıştır';
  }
  syncVoiceLabRealtimeControls();
}

function getVoiceLabLanguage() {
  const normalized = String(refs.voiceLabLanguage?.value || 'tr').trim().toLowerCase();
  return ['tr','en','ru'].includes(normalized) ? normalized : 'tr';
}

function getVoiceLabStoredValue(key) {
  try {
    return window.localStorage.getItem(key);
  } catch (_error) {
    return null;
  }
}

function setVoiceLabStoredValue(key, value) {
  try {
    window.localStorage.setItem(key, String(value || ''));
  } catch (_error) {
    // Voice tuning persistence is best-effort only.
  }
}

function getVoiceLabVoiceStorageKey(language) {
  return `${VOICE_LAB_VOICE_KEY}.${language || 'tr'}`;
}

function clampVoiceLabNumber(value, min, max, fallback) {
  const parsed = Number.parseFloat(value);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.min(max, Math.max(min, parsed));
}

function formatVoiceLabRate(value) {
  return `${value.toFixed(2)}x`;
}

function formatVoiceLabPitch(value) {
  return value.toFixed(2);
}

function getVoiceLabSpeechRate() {
  return clampVoiceLabNumber(
    refs.voiceLabRate?.value,
    VOICE_LAB_RATE_MIN,
    VOICE_LAB_RATE_MAX,
    VOICE_LAB_DEFAULT_RATE
  );
}

function getVoiceLabSpeechPitch() {
  return clampVoiceLabNumber(
    refs.voiceLabPitch?.value,
    VOICE_LAB_PITCH_MIN,
    VOICE_LAB_PITCH_MAX,
    VOICE_LAB_DEFAULT_PITCH
  );
}

function updateVoiceLabTuningLabels() {
  const rate = getVoiceLabSpeechRate();
  const pitch = getVoiceLabSpeechPitch();
  if (refs.voiceLabRate) refs.voiceLabRate.value = rate.toFixed(2);
  if (refs.voiceLabPitch) refs.voiceLabPitch.value = pitch.toFixed(2);
  if (refs.voiceLabRateValue) refs.voiceLabRateValue.textContent = formatVoiceLabRate(rate);
  if (refs.voiceLabPitchValue) refs.voiceLabPitchValue.textContent = formatVoiceLabPitch(pitch);
}

function initializeVoiceLabTuningControls() {
  if (refs.voiceLabRate) {
    refs.voiceLabRate.value = clampVoiceLabNumber(
      getVoiceLabStoredValue(VOICE_LAB_RATE_KEY),
      VOICE_LAB_RATE_MIN,
      VOICE_LAB_RATE_MAX,
      VOICE_LAB_DEFAULT_RATE
    ).toFixed(2);
  }
  if (refs.voiceLabPitch) {
    refs.voiceLabPitch.value = clampVoiceLabNumber(
      getVoiceLabStoredValue(VOICE_LAB_PITCH_KEY),
      VOICE_LAB_PITCH_MIN,
      VOICE_LAB_PITCH_MAX,
      VOICE_LAB_DEFAULT_PITCH
    ).toFixed(2);
  }
  updateVoiceLabTuningLabels();
}

function initializeVoiceLabElevenLabsControls() {
  if (refs.voiceLabElevenLabsVoiceId) {
    refs.voiceLabElevenLabsVoiceId.value = getVoiceLabStoredValue(VOICE_LAB_ELEVENLABS_VOICE_ID_KEY) || '';
  }
  if (refs.voiceLabElevenLabsProfile) {
    const profile = getVoiceLabStoredValue(VOICE_LAB_ELEVENLABS_PROFILE_KEY) || 'quality';
    refs.voiceLabElevenLabsProfile.value = ['quality','balanced','low_latency'].includes(profile) ? profile : 'quality';
  }
  if (refs.voiceLabElevenLabsStability) {
    refs.voiceLabElevenLabsStability.value = clampVoiceLabNumber(
      getVoiceLabStoredValue(VOICE_LAB_ELEVENLABS_STABILITY_KEY),
      0,
      1,
      0.5
    ).toFixed(2);
  }
  if (refs.voiceLabElevenLabsSimilarity) {
    refs.voiceLabElevenLabsSimilarity.value = clampVoiceLabNumber(
      getVoiceLabStoredValue(VOICE_LAB_ELEVENLABS_SIMILARITY_KEY),
      0,
      1,
      0.75
    ).toFixed(2);
  }
  if (refs.voiceLabElevenLabsStyle) {
    refs.voiceLabElevenLabsStyle.value = clampVoiceLabNumber(
      getVoiceLabStoredValue(VOICE_LAB_ELEVENLABS_STYLE_KEY),
      0,
      1,
      0.2
    ).toFixed(2);
  }
  updateVoiceLabElevenLabsLabels();
  setVoiceLabElevenLabsStatus('Bağlantı yapılandırması bekleniyor.', 'warn', 'Hazır değil');
}

function updateVoiceLabElevenLabsLabels() {
  if (refs.voiceLabElevenLabsStabilityValue) {
    refs.voiceLabElevenLabsStabilityValue.textContent = clampVoiceLabNumber(
      refs.voiceLabElevenLabsStability?.value,
      0,
      1,
      0.5
    ).toFixed(2);
  }
  if (refs.voiceLabElevenLabsSimilarityValue) {
    refs.voiceLabElevenLabsSimilarityValue.textContent = clampVoiceLabNumber(
      refs.voiceLabElevenLabsSimilarity?.value,
      0,
      1,
      0.75
    ).toFixed(2);
  }
  if (refs.voiceLabElevenLabsStyleValue) {
    refs.voiceLabElevenLabsStyleValue.textContent = clampVoiceLabNumber(
      refs.voiceLabElevenLabsStyle?.value,
      0,
      1,
      0.2
    ).toFixed(2);
  }
}

function setVoiceLabElevenLabsStatus(message, tone = 'info', badge = 'Planlandı') {
  if (refs.voiceLabElevenLabsStatus) {
    refs.voiceLabElevenLabsStatus.textContent = message;
    refs.voiceLabElevenLabsStatus.dataset.tone = tone;
  }
  if (refs.voiceLabElevenLabsBadge) {
    refs.voiceLabElevenLabsBadge.className = `pill ${tone}`;
    refs.voiceLabElevenLabsBadge.textContent = badge;
  }
}

function onVoiceLabElevenLabsChange() {
  updateVoiceLabElevenLabsLabels();
  setVoiceLabElevenLabsStatus('Kaydedilmemiş ElevenLabs ayarı var.', 'info', 'Taslak');
}

function saveVoiceLabElevenLabsSettings() {
  setVoiceLabStoredValue(VOICE_LAB_ELEVENLABS_VOICE_ID_KEY, String(refs.voiceLabElevenLabsVoiceId?.value || '').trim());
  setVoiceLabStoredValue(VOICE_LAB_ELEVENLABS_PROFILE_KEY, String(refs.voiceLabElevenLabsProfile?.value || 'quality'));
  setVoiceLabStoredValue(VOICE_LAB_ELEVENLABS_STABILITY_KEY, clampVoiceLabNumber(refs.voiceLabElevenLabsStability?.value, 0, 1, 0.5).toFixed(2));
  setVoiceLabStoredValue(VOICE_LAB_ELEVENLABS_SIMILARITY_KEY, clampVoiceLabNumber(refs.voiceLabElevenLabsSimilarity?.value, 0, 1, 0.75).toFixed(2));
  setVoiceLabStoredValue(VOICE_LAB_ELEVENLABS_STYLE_KEY, clampVoiceLabNumber(refs.voiceLabElevenLabsStyle?.value, 0, 1, 0.2).toFixed(2));
  setVoiceLabElevenLabsStatus('ElevenLabs panel ayarları kaydedildi. Bağlantı testi için backend endpoint gereklidir.', 'info', 'Taslak');
  notify('ElevenLabs panel ayarları kaydedildi.', 'success');
}

function testVoiceLabElevenLabsConnection() {
  setVoiceLabElevenLabsStatus('ElevenLabs bağlantı testi için backend endpoint ve sunucu ENV bağlantısı sonraki adımdır.', 'warn', 'Bekliyor');
  notify('ElevenLabs bağlantı testi backend entegrasyonundan sonra çalışacak.', 'warn');
}

function initializeVoiceLabRealtimeControls() {
  populateVoiceLabRealtimeVoiceOptions();
  const savedVoice = getVoiceLabStoredValue(VOICE_LAB_REALTIME_VOICE_KEY) || 'marin';
  if (refs.voiceLabRealtimeVoice && VOICE_LAB_REALTIME_VOICES.some(item => item.value === savedVoice)) {
    refs.voiceLabRealtimeVoice.value = savedVoice;
  }
  syncVoiceLabRealtimeControls();
  resetVoiceLabRealtimeMeter();
}

function populateVoiceLabRealtimeVoiceOptions() {
  if (!refs.voiceLabRealtimeVoice) return;
  const currentValue = refs.voiceLabRealtimeVoice.value || getVoiceLabStoredValue(VOICE_LAB_REALTIME_VOICE_KEY) || 'marin';
  refs.voiceLabRealtimeVoice.innerHTML = VOICE_LAB_REALTIME_VOICES.map(item => (
    `<option value="${escapeHtml(item.value)}">${escapeHtml(item.label)}</option>`
  )).join('');
  refs.voiceLabRealtimeVoice.value = VOICE_LAB_REALTIME_VOICES.some(item => item.value === currentValue)
    ? currentValue
    : 'marin';
}

function getVoiceLabRealtimeVoice() {
  const selected = String(refs.voiceLabRealtimeVoice?.value || '').trim().toLowerCase();
  return VOICE_LAB_REALTIME_VOICES.some(item => item.value === selected) ? selected : 'marin';
}

function onVoiceLabRealtimeVoiceChange() {
  setVoiceLabStoredValue(VOICE_LAB_REALTIME_VOICE_KEY, getVoiceLabRealtimeVoice());
  setVoiceLabRealtimeStatus('Realtime ses seçimi güncellendi.', 'info');
}

function voiceLabRealtimeSupported() {
  const nav = typeof navigator !== 'undefined' ? navigator : null;
  return (
    typeof window !== 'undefined' &&
    typeof window.RTCPeerConnection === 'function' &&
    Boolean(nav?.mediaDevices) &&
    typeof nav.mediaDevices.getUserMedia === 'function'
  );
}

function setVoiceLabRealtimeStatus(message, tone = 'info') {
  if (!refs.voiceLabRealtimeStatus) return;
  refs.voiceLabRealtimeStatus.textContent = message;
  refs.voiceLabRealtimeStatus.dataset.tone = tone;
}

function setVoiceLabRealtimeMeter(message, active = false) {
  if (refs.voiceLabRealtimeMeterText) refs.voiceLabRealtimeMeterText.textContent = message;
  if (refs.voiceLabRealtimeMeter) refs.voiceLabRealtimeMeter.classList.toggle('active', Boolean(active));
}

function setVoiceLabRealtimeMeterBars(levels = []) {
  const bars = refs.voiceLabRealtimeMeterBars ? Array.from(refs.voiceLabRealtimeMeterBars.children) : [];
  bars.forEach((bar, index) => {
    const level = Math.max(0.08, Math.min(1, Number(levels[index]) || 0.08));
    bar.style.height = `${Math.round(8 + level * 56)}px`;
  });
}

function resetVoiceLabRealtimeMeter() {
  if (state.voiceLabRealtimeMeterAnimationFrame) {
    window.cancelAnimationFrame(state.voiceLabRealtimeMeterAnimationFrame);
    state.voiceLabRealtimeMeterAnimationFrame = 0;
  }
  try { state.voiceLabRealtimeMeterSource?.disconnect(); } catch (_error) {}
  try { state.voiceLabRealtimeAnalyser?.disconnect(); } catch (_error) {}
  try { state.voiceLabRealtimeAudioContext?.close(); } catch (_error) {}
  state.voiceLabRealtimeMeterSource = null;
  state.voiceLabRealtimeAnalyser = null;
  state.voiceLabRealtimeAudioContext = null;
  setVoiceLabRealtimeMeter('Bekliyor', false);
  setVoiceLabRealtimeMeterBars([]);
}

function startVoiceLabRealtimeMeter(localStream) {
  resetVoiceLabRealtimeMeter();
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextClass || !localStream) {
    setVoiceLabRealtimeMeter('Seviye ölçümü yok', false);
    return;
  }
  try {
    const audioContext = new AudioContextClass();
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;
    analyser.smoothingTimeConstant = 0.72;
    const source = audioContext.createMediaStreamSource(localStream);
    source.connect(analyser);
    state.voiceLabRealtimeAudioContext = audioContext;
    state.voiceLabRealtimeAnalyser = analyser;
    state.voiceLabRealtimeMeterSource = source;
    updateVoiceLabRealtimeMeterFrame();
  } catch (_error) {
    resetVoiceLabRealtimeMeter();
    setVoiceLabRealtimeMeter('Seviye ölçümü başlatılamadı', false);
  }
}

function updateVoiceLabRealtimeMeterFrame() {
  const analyser = state.voiceLabRealtimeAnalyser;
  if (!analyser) return;
  const data = new Uint8Array(analyser.frequencyBinCount);
  analyser.getByteFrequencyData(data);
  const bars = refs.voiceLabRealtimeMeterBars ? Array.from(refs.voiceLabRealtimeMeterBars.children) : [];
  const step = Math.max(1, Math.floor(data.length / Math.max(1, bars.length)));
  const levels = bars.map((_bar, index) => {
    const start = index * step;
    const slice = data.slice(start, start + step);
    const total = slice.reduce((sum, value) => sum + value, 0);
    return Math.max(0.08, total / Math.max(1, slice.length) / 255);
  });
  const peak = Math.max(...levels, 0);
  setVoiceLabRealtimeMeter(peak > 0.16 ? 'Ses algılanıyor' : 'Dinleniyor', true);
  setVoiceLabRealtimeMeterBars(levels);
  state.voiceLabRealtimeMeterAnimationFrame = window.requestAnimationFrame(updateVoiceLabRealtimeMeterFrame);
}

function syncVoiceLabRealtimeControls() {
  const supported = voiceLabRealtimeSupported();
  const busy = Boolean(state.voiceLabLoading || state.voiceLabRealtimeConnecting);
  const active = Boolean(state.voiceLabRealtimeActive);
  if (refs.voiceLabRealtimeVoice) refs.voiceLabRealtimeVoice.disabled = !supported || busy || active;
  if (refs.voiceLabRealtimeStartButton) {
    refs.voiceLabRealtimeStartButton.disabled = !supported || busy || active;
    refs.voiceLabRealtimeStartButton.textContent = state.voiceLabRealtimeConnecting
      ? 'Bağlanıyor...'
      : 'OpenAI Realtime ile Konuş';
  }
  if (refs.voiceLabRealtimeStopButton) refs.voiceLabRealtimeStopButton.disabled = !supported || (!busy && !active);
  if (!supported) {
    setVoiceLabRealtimeStatus('Bu tarayıcı WebRTC mikrofon bağlantısını desteklemiyor.', 'warn');
  } else if (!active && !state.voiceLabRealtimeConnecting) {
    setVoiceLabRealtimeStatus('Mikrofon bağlantısı bekliyor.', 'info');
  }
}

function buildVoiceLabRealtimeClientSecretPath() {
  const query = new URLSearchParams({
    hotel_id: String(Number(state.selectedHotelId)),
    language: getVoiceLabLanguage(),
    voice: getVoiceLabRealtimeVoice(),
  });
  return `/voice-lab/realtime/client-secret?${query.toString()}`;
}

function getVoiceLabRealtimeGreetingInstruction() {
  const language = getVoiceLabLanguage();
  const greeting = VOICE_LAB_GREETING_TEXT[language] || VOICE_LAB_GREETING_TEXT.tr;
  return `Say this greeting naturally and then wait for the caller: ${greeting}`;
}

async function startVoiceLabRealtime() {
  if (!state.selectedHotelId) {
    notify('Lütfen bir otel seçin.', 'warn');
    return;
  }
  if (!voiceLabRealtimeSupported()) {
    setVoiceLabRealtimeStatus('Bu tarayıcı WebRTC mikrofon bağlantısını desteklemiyor.', 'warn');
    notify('Bu tarayıcı WebRTC mikrofon bağlantısını desteklemiyor.', 'warn');
    return;
  }
  stopVoiceLabSpeech({silent: true});
  stopVoiceLabRealtime({silent: true});
  state.voiceLabRealtimeConnecting = true;
  setVoiceLabRealtimeStatus('Mikrofon izni bekleniyor.', 'info');
  syncVoiceLabRealtimeControls();

  let peer = null;
  let dataChannel = null;
  let localStream = null;
  let audioElement = null;
  try {
    peer = new window.RTCPeerConnection();
    audioElement = document.createElement('audio');
    audioElement.autoplay = true;
    audioElement.hidden = true;
    document.body?.appendChild(audioElement);
    peer.ontrack = event => {
      if (event.streams && event.streams[0]) audioElement.srcObject = event.streams[0];
    };
    peer.onconnectionstatechange = () => {
      if (peer.connectionState === 'connected') {
        state.voiceLabRealtimeActive = true;
        setVoiceLabRealtimeStatus('Realtime bağlı. AI sekreter konuşmaya hazır.', 'success');
      }
      if (['failed','disconnected','closed'].includes(peer.connectionState)) {
        stopVoiceLabRealtime({silent: peer.connectionState === 'closed'});
      }
      syncVoiceLabRealtimeControls();
    };

    localStream = await navigator.mediaDevices.getUserMedia({
      audio: {echoCancellation: true, noiseSuppression: true, autoGainControl: true},
    });
    startVoiceLabRealtimeMeter(localStream);
    localStream.getTracks().forEach(track => peer.addTrack(track, localStream));
    dataChannel = peer.createDataChannel('oai-events');
    dataChannel.addEventListener('open', () => {
      state.voiceLabRealtimeActive = true;
      sendVoiceLabRealtimeGreeting(dataChannel);
      setVoiceLabRealtimeStatus('Realtime bağlı. AI sekreter konuşmaya hazır.', 'success');
      syncVoiceLabRealtimeControls();
    });
    dataChannel.addEventListener('message', onVoiceLabRealtimeEvent);
    dataChannel.addEventListener('close', () => {
      if (state.voiceLabRealtimeActive) setVoiceLabRealtimeStatus('Realtime veri kanalı kapandı.', 'warn');
      syncVoiceLabRealtimeControls();
    });

    const offer = await peer.createOffer();
    await peer.setLocalDescription(offer);
    const answerSdp = await requestVoiceLabRealtimeAnswerSdp(offer.sdp);
    await peer.setRemoteDescription({type: 'answer', sdp: answerSdp});

    state.voiceLabRealtimePeer = peer;
    state.voiceLabRealtimeDataChannel = dataChannel;
    state.voiceLabRealtimeLocalStream = localStream;
    state.voiceLabRealtimeAudioElement = audioElement;
    setVoiceLabRealtimeStatus('Realtime bağlantısı kuruluyor.', 'info');
  } catch (error) {
    cleanupVoiceLabRealtimeResources({peer, dataChannel, localStream, audioElement});
    setVoiceLabRealtimeStatus(error.message || 'Realtime bağlantısı başlatılamadı.', 'error');
    notify(error.message || 'Realtime bağlantısı başlatılamadı.', 'error');
  } finally {
    state.voiceLabRealtimeConnecting = false;
    syncVoiceLabRealtimeControls();
  }
}

async function requestVoiceLabRealtimeAnswerSdp(offerSdp) {
  const secretPayload = await apiFetch(buildVoiceLabRealtimeClientSecretPath(), {
    method: 'POST',
    body: {},
  });
  const clientSecret = String(secretPayload?.value || '').trim();
  const callsUrl = String(secretPayload?.realtime_calls_url || 'https://api.openai.com/v1/realtime/calls').trim();
  if (!clientSecret) {
    throw new Error('OpenAI Realtime client secret alınamadı.');
  }
  let response;
  try {
    response = await fetch(callsUrl, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${clientSecret}`,
        'Content-Type': 'application/sdp',
      },
      body: offerSdp,
    });
  } catch (_error) {
    throw new Error('OpenAI Realtime bağlantısına ulaşılamadı.');
  }
  const text = await response.text();
  if (!response.ok) {
    throw new Error('OpenAI Realtime bağlantısı başlatılamadı.');
  }
  const answerSdp = normalizeVoiceLabRealtimeAnswerSdp(text);
  if (!answerSdp.startsWith('v=0')) {
    throw new Error('OpenAI Realtime geçerli SDP cevabı döndürmedi.');
  }
  return answerSdp;
}

function normalizeVoiceLabRealtimeAnswerSdp(value) {
  const sdp = String(value || '').replace(/^\\s+/, '').replace(/\\r?\\n/g, '\\r\\n');
  return sdp.endsWith('\\r\\n') ? sdp : `${sdp}\\r\\n`;
}

function sendVoiceLabRealtimeGreeting(dataChannel) {
  if (!dataChannel || dataChannel.readyState !== 'open') return;
  dataChannel.send(JSON.stringify({
    type: 'response.create',
    response: {
      output_modalities: ['audio'],
      instructions: getVoiceLabRealtimeGreetingInstruction(),
    },
  }));
}

function onVoiceLabRealtimeEvent(event) {
  let payload = null;
  try { payload = JSON.parse(event.data); } catch (_error) { return; }
  if (payload.type === 'output_audio_buffer.started') {
    setVoiceLabRealtimeStatus('AI sekreter konuşuyor.', 'success');
  } else if (payload.type === 'output_audio_buffer.stopped' || payload.type === 'response.done') {
    setVoiceLabRealtimeStatus('AI sekreter dinliyor.', 'info');
  } else if (payload.type === 'error') {
    setVoiceLabRealtimeStatus('Realtime oturumunda hata oluştu.', 'error');
  }
}

function cleanupVoiceLabRealtimeResources(resources = {}) {
  resetVoiceLabRealtimeMeter();
  const dataChannel = resources.dataChannel || state.voiceLabRealtimeDataChannel;
  const localStream = resources.localStream || state.voiceLabRealtimeLocalStream;
  const peer = resources.peer || state.voiceLabRealtimePeer;
  const audioElement = resources.audioElement || state.voiceLabRealtimeAudioElement;
  try { dataChannel?.close(); } catch (_error) {}
  try { localStream?.getTracks().forEach(track => track.stop()); } catch (_error) {}
  try { peer?.close(); } catch (_error) {}
  if (audioElement) {
    try { audioElement.srcObject = null; } catch (_error) {}
    if (typeof audioElement.remove === 'function') audioElement.remove();
  }
}

function stopVoiceLabRealtime(options = {}) {
  cleanupVoiceLabRealtimeResources();
  state.voiceLabRealtimeActive = false;
  state.voiceLabRealtimeConnecting = false;
  state.voiceLabRealtimePeer = null;
  state.voiceLabRealtimeDataChannel = null;
  state.voiceLabRealtimeLocalStream = null;
  state.voiceLabRealtimeAudioElement = null;
  if (!options.silent) setVoiceLabRealtimeStatus('Realtime oturumu kapatıldı.', 'info');
  syncVoiceLabRealtimeControls();
}

function voiceLabSpeechSupported() {
  return (
    typeof window !== 'undefined' &&
    Boolean(window.speechSynthesis) &&
    typeof window.SpeechSynthesisUtterance === 'function'
  );
}

function getVoiceLabAvailableVoices() {
  if (!voiceLabSpeechSupported()) return [];
  if (typeof window.speechSynthesis.getVoices !== 'function') return [];
  const voices = window.speechSynthesis.getVoices();
  return Array.isArray(voices) ? voices : [];
}

function bindVoiceLabSpeechEvents() {
  if (!voiceLabSpeechSupported()) {
    syncVoiceLabSpeechControls();
    return;
  }
  const synth = window.speechSynthesis;
  if (synth.__veloxVoiceLabBound) {
    syncVoiceLabSpeechControls();
    return;
  }
  synth.__veloxVoiceLabBound = true;
  if (typeof synth.addEventListener === 'function') {
    synth.addEventListener('voiceschanged', () => {
      populateVoiceLabVoiceOptions();
      syncVoiceLabSpeechControls();
    });
  } else if ('onvoiceschanged' in synth) {
    synth.onvoiceschanged = () => {
      populateVoiceLabVoiceOptions();
      syncVoiceLabSpeechControls();
    };
  }
  populateVoiceLabVoiceOptions();
  syncVoiceLabSpeechControls();
}

function resolveVoiceLabSpeechLang(language) {
  return VOICE_LAB_SPEECH_LANG[language] || VOICE_LAB_SPEECH_LANG.tr;
}

function getVoiceLabVoiceId(voice) {
  return `${voice?.name || ''}||${voice?.lang || ''}`;
}

function getVoiceLabVoiceLabel(voice) {
  const source = voice?.localService === false ? 'Online' : 'Yerel';
  return `${voice?.name || 'Ses'} · ${voice?.lang || 'Dil yok'} · ${source}`;
}

function scoreVoiceLabSpeechVoice(voice, language) {
  const speechLang = resolveVoiceLabSpeechLang(language).toLowerCase();
  const languagePrefix = String(language || 'tr').toLowerCase();
  const voiceLang = String(voice?.lang || '').toLowerCase();
  const voiceName = String(voice?.name || '').toLowerCase();
  let score = 0;
  if (voiceLang === speechLang) {
    score += 100;
  } else if (voiceLang.startsWith(languagePrefix)) {
    score += 72;
  } else if (language === 'tr' && voiceLang.startsWith('tr')) {
    score += 48;
  }
  if (score === 0) return 0;
  VOICE_LAB_NATURAL_VOICE_HINTS.forEach((hint, index) => {
    if (voiceName.includes(hint)) score += 18 - Math.min(index, 8);
  });
  if (voice?.localService === false) score += 10;
  if (voice?.default) score += 4;
  return score;
}

function getVoiceLabRankedVoices(language) {
  return getVoiceLabAvailableVoices()
    .map(voice => ({voice, score: scoreVoiceLabSpeechVoice(voice, language)}))
    .sort((left, right) => right.score - left.score || getVoiceLabVoiceLabel(left.voice).localeCompare(getVoiceLabVoiceLabel(right.voice)));
}

function populateVoiceLabVoiceOptions() {
  if (!refs.voiceLabVoiceSelect) return;
  if (!voiceLabSpeechSupported()) {
    refs.voiceLabVoiceSelect.innerHTML = '<option value="">Ses desteklenmiyor</option>';
    refs.voiceLabVoiceSelect.disabled = true;
    return;
  }
  const language = getVoiceLabLanguage();
  const voices = getVoiceLabRankedVoices(language);
  if (voices.length === 0) {
    refs.voiceLabVoiceSelect.innerHTML = '<option value="">Tarayıcı sesleri yükleniyor</option>';
    refs.voiceLabVoiceSelect.disabled = true;
    return;
  }
  const displayVoices = voices.some(item => item.score > 0)
    ? voices.filter(item => item.score > 0)
    : voices;
  const savedVoiceId = getVoiceLabStoredValue(getVoiceLabVoiceStorageKey(language)) || '';
  const options = [
    '<option value="">Dile göre en doğal ses</option>',
    ...displayVoices.map(item => {
      const voiceId = getVoiceLabVoiceId(item.voice);
      return `<option value="${escapeHtml(voiceId)}">${escapeHtml(getVoiceLabVoiceLabel(item.voice))}</option>`;
    }),
  ];
  refs.voiceLabVoiceSelect.innerHTML = options.join('');
  refs.voiceLabVoiceSelect.disabled = false;
  if (savedVoiceId && displayVoices.some(item => getVoiceLabVoiceId(item.voice) === savedVoiceId)) {
    refs.voiceLabVoiceSelect.value = savedVoiceId;
  }
}

function findVoiceLabSpeechVoice(language) {
  if (!voiceLabSpeechSupported()) return null;
  const voices = getVoiceLabRankedVoices(language);
  const selectedVoiceId = refs.voiceLabVoiceSelect?.value || getVoiceLabStoredValue(getVoiceLabVoiceStorageKey(language)) || '';
  if (selectedVoiceId) {
    const selected = voices.find(item => getVoiceLabVoiceId(item.voice) === selectedVoiceId);
    if (selected) return selected.voice;
  }
  const matchingVoice = voices.find(item => item.score > 0);
  return matchingVoice?.voice || voices[0]?.voice || null;
}

function onVoiceLabLanguageChange() {
  populateVoiceLabVoiceOptions();
  syncVoiceLabSpeechControls();
  syncVoiceLabRealtimeControls();
}

function onVoiceLabVoiceTuningChange(event) {
  const language = getVoiceLabLanguage();
  if (event?.target === refs.voiceLabVoiceSelect) {
    setVoiceLabStoredValue(getVoiceLabVoiceStorageKey(language), refs.voiceLabVoiceSelect.value || '');
  }
  if (event?.target === refs.voiceLabRate) {
    setVoiceLabStoredValue(VOICE_LAB_RATE_KEY, getVoiceLabSpeechRate().toFixed(2));
  }
  if (event?.target === refs.voiceLabPitch) {
    setVoiceLabStoredValue(VOICE_LAB_PITCH_KEY, getVoiceLabSpeechPitch().toFixed(2));
  }
  updateVoiceLabTuningLabels();
  if (voiceLabSpeechSupported()) {
    setVoiceLabVoiceStatus('Ses ayarı güncellendi. Tekrar dinleyebilirsiniz.', 'info');
  }
}

function setVoiceLabVoiceStatus(message, tone = 'info') {
  if (!refs.voiceLabVoiceStatus) return;
  refs.voiceLabVoiceStatus.textContent = message;
  refs.voiceLabVoiceStatus.dataset.tone = tone;
}

function getVoiceLabReplySpeechText() {
  return String(state.voiceLabResult?.response_text || '').trim();
}

function syncVoiceLabSpeechControls() {
  const supported = voiceLabSpeechSupported();
  const hasReply = Boolean(getVoiceLabReplySpeechText());
  populateVoiceLabVoiceOptions();
  updateVoiceLabTuningLabels();
  if (refs.voiceLabRate) refs.voiceLabRate.disabled = !supported;
  if (refs.voiceLabPitch) refs.voiceLabPitch.disabled = !supported;
  if (refs.voiceLabSpeakGreetingButton) refs.voiceLabSpeakGreetingButton.disabled = !supported;
  if (refs.voiceLabSpeakReplyButton) refs.voiceLabSpeakReplyButton.disabled = !supported || !hasReply;
  if (refs.voiceLabStopVoiceButton) refs.voiceLabStopVoiceButton.disabled = !supported;
  if (!supported) {
    setVoiceLabVoiceStatus('Bu tarayıcı sesli oynatma desteklemiyor.', 'warn');
  } else if (getVoiceLabAvailableVoices().length === 0) {
    setVoiceLabVoiceStatus('Tarayıcı sesleri yükleniyor. Birkaç saniye sonra tekrar deneyebilirsiniz.', 'warn');
  }
}

function speakVoiceLabText(text, label) {
  const speechText = String(text || '').trim();
  if (!speechText) {
    notify('Seslendirilecek metin bulunamadı.', 'warn');
    return;
  }
  if (!voiceLabSpeechSupported()) {
    setVoiceLabVoiceStatus('Bu tarayıcı sesli oynatma desteklemiyor.', 'warn');
    notify('Bu tarayıcı sesli oynatma desteklemiyor.', 'warn');
    return;
  }
  const language = getVoiceLabLanguage();
  const utterance = new window.SpeechSynthesisUtterance(speechText);
  utterance.lang = resolveVoiceLabSpeechLang(language);
  utterance.voice = findVoiceLabSpeechVoice(language);
  utterance.rate = getVoiceLabSpeechRate();
  utterance.pitch = getVoiceLabSpeechPitch();
  utterance.volume = 1;
  utterance.onstart = () => setVoiceLabVoiceStatus(`${label} sesi oynatılıyor.`, 'success');
  utterance.onend = () => setVoiceLabVoiceStatus('Ses önizleme tamamlandı.', 'info');
  utterance.onerror = () => setVoiceLabVoiceStatus('Ses oynatma başlatılamadı.', 'error');
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
}

function speakVoiceLabGreeting() {
  const language = getVoiceLabLanguage();
  speakVoiceLabText(VOICE_LAB_GREETING_TEXT[language] || VOICE_LAB_GREETING_TEXT.tr, 'Karşılama');
}

function speakVoiceLabReply() {
  const speechText = getVoiceLabReplySpeechText();
  if (!speechText) {
    notify('Önce bir Voice Lab senaryosu çalıştırın.', 'warn');
    return;
  }
  speakVoiceLabText(speechText, 'Yanıt');
}

function stopVoiceLabSpeech(options = {}) {
  if (!voiceLabSpeechSupported()) return;
  window.speechSynthesis.cancel();
  if (!options.silent) setVoiceLabVoiceStatus('Ses oynatma durduruldu.', 'info');
}

function renderVoiceLabSummary() {
  const matrixSummary = state.voiceLabMatrixSummary;
  const singleResult = state.voiceLabResult;
  const fallbackTotal = state.voiceLabScenarios.length || 18;
  const summary = matrixSummary || (singleResult ? {
    total: 1,
    passed: singleResult.result === 'PASS' ? 1 : 0,
    failed: singleResult.result === 'FAIL' ? 1 : 0,
    blocked: singleResult.result === 'BLOCKED' ? 1 : 0,
  } : {total: fallbackTotal, passed: 0, failed: 0, blocked: 0});
  if (refs.voiceLabTotalCount) refs.voiceLabTotalCount.textContent = String(summary.total || 0);
  if (refs.voiceLabPassedCount) refs.voiceLabPassedCount.textContent = String(summary.passed || 0);
  if (refs.voiceLabFailedCount) refs.voiceLabFailedCount.textContent = String(summary.failed || 0);
  if (refs.voiceLabBlockedCount) refs.voiceLabBlockedCount.textContent = String(summary.blocked || 0);
  if (refs.voiceLabMatrixBadge) {
    refs.voiceLabMatrixBadge.className = `pill ${voiceLabResultClass((summary.failed || summary.blocked) ? 'FAIL' : (summary.passed ? 'PASS' : 'UNKNOWN'))}`;
    refs.voiceLabMatrixBadge.textContent = matrixSummary ? `${summary.passed || 0}/${summary.total || 0} geçti` : 'Henüz koşulmadı';
  }
}

function renderVoiceLabResult() {
  const result = state.voiceLabResult;
  if (!result) {
    if (refs.voiceLabResultBadge) {
      refs.voiceLabResultBadge.className = 'pill info';
      refs.voiceLabResultBadge.textContent = 'Bekliyor';
    }
    if (refs.voiceLabResultMeta) refs.voiceLabResultMeta.textContent = 'Henüz senaryo çalıştırılmadı.';
    if (refs.voiceLabResultPanel) {
      refs.voiceLabResultPanel.innerHTML = `
        <div class="empty-state">
          <h4>Seçim bekleniyor</h4>
          <p>Bir senaryo çalıştırıldığında kaynak, aksiyon, cevap ve ihlal listesi burada görünür.</p>
        </div>
      `;
    }
    renderVoiceLabSafety(null);
    setVoiceLabLoading(Boolean(state.voiceLabLoading));
    syncVoiceLabSpeechControls();
    return;
  }

  if (refs.voiceLabResultBadge) {
    refs.voiceLabResultBadge.className = `pill ${voiceLabResultClass(result.result)}`;
    refs.voiceLabResultBadge.textContent = formatVoiceLabResult(result.result);
  }
  if (refs.voiceLabResultMeta) {
    refs.voiceLabResultMeta.textContent = [
      result.scenario_id || 'Otomatik',
      `${result.latency_ms?.total || 0} ms`,
      formatVoiceLabSource(result.source_type),
      result.handoff_required ? 'insan devri' : 'self-servis',
    ].join(' · ');
  }
  if (refs.voiceLabResultPanel) {
    const violations = Array.isArray(result.violations) ? result.violations : [];
    refs.voiceLabResultPanel.innerHTML = `
      <div class="voice-lab-result-grid">
        <div class="voice-lab-result-block"><strong>Niyet</strong><span>${escapeHtml(result.intent || '-')}</span></div>
        <div class="voice-lab-result-block"><strong>Kaynak</strong><span>${escapeHtml(formatVoiceLabSource(result.source_type))}</span></div>
        <div class="voice-lab-result-block"><strong>Aksiyon</strong><span>${escapeHtml(formatVoiceLabAction(result.action))}</span></div>
        <div class="voice-lab-result-block"><strong>Araç</strong><span>${escapeHtml(result.tool_name || (result.tool_required ? 'tool gerekli' : '-'))}</span></div>
      </div>
      <div class="voice-lab-response">${escapeHtml(result.response_text || '-')}</div>
      <div class="voice-lab-result-grid">
        <div class="voice-lab-result-block"><strong>Risk Flag</strong><span>${escapeHtml((result.risk_flags || []).join(', ') || '-')}</span></div>
        <div class="voice-lab-result-block"><strong>Kaynak Detayı</strong><span>${escapeHtml(result.source_detail || '-')}</span></div>
      </div>
      ${renderVoiceLabViolations(violations)}
    `;
  }
  renderVoiceLabSafety(result);
  setVoiceLabLoading(Boolean(state.voiceLabLoading));
  syncVoiceLabSpeechControls();
}

function renderVoiceLabViolations(violations) {
  if (!violations.length) {
    return '<div class="voice-lab-violations"><span class="pill success">İhlal yok</span></div>';
  }
  return `
    <div class="voice-lab-violations">
      ${violations.map(item => `<div class="voice-lab-violation">${escapeHtml(item)}</div>`).join('')}
    </div>
  `;
}

function renderVoiceLabMatrix() {
  if (!refs.voiceLabMatrixBody) return;
  const items = state.voiceLabMatrixResults;
  if (!items.length && !state.voiceLabScenarios.length) {
    refs.voiceLabMatrixBody.innerHTML = '<tr><td colspan="6"><div class="empty-state"><p>Matris koşusu bekleniyor.</p></div></td></tr>';
    return;
  }
  if (!items.length) {
    refs.voiceLabMatrixBody.innerHTML = state.voiceLabScenarios.map(item => `
      <tr>
        <td><strong>${escapeHtml(item.scenario_id || '-')}</strong></td>
        <td><span class="pill info">Bekliyor</span></td>
        <td>${escapeHtml(item.expected_intent || '-')}</td>
        <td>${escapeHtml(formatVoiceLabSource(item.expected_source))}</td>
        <td>${escapeHtml(formatVoiceLabAction(item.expected_action))}</td>
        <td><span class="muted">-</span></td>
      </tr>
    `).join('');
    return;
  }
  refs.voiceLabMatrixBody.innerHTML = items.map(item => {
    const violationText = (item.violations || []).join(' | ') || '-';
    return `
      <tr>
        <td><strong>${escapeHtml(item.scenario_id || '-')}</strong></td>
        <td><div class="voice-lab-status-cell"><span class="pill ${voiceLabResultClass(item.result)}">${escapeHtml(formatVoiceLabResult(item.result))}</span></div></td>
        <td>${escapeHtml(item.intent || '-')}</td>
        <td>${escapeHtml(formatVoiceLabSource(item.source_type))}</td>
        <td>${escapeHtml(formatVoiceLabAction(item.action))}</td>
        <td><span class="muted">${escapeHtml(violationText)}</span></td>
      </tr>
    `;
  }).join('');
}

function renderVoiceLabSafety(result) {
  if (!refs.voiceLabSafety) return;
  const badges = result ? [
    {label: result.tool_called ? 'Tool çağrıldı' : (result.tool_required ? 'Tool gerekli' : 'Tool gerekmedi'), cls: result.tool_called ? 'success' : (result.tool_required ? 'warn' : 'info')},
    {label: result.handoff_required ? 'İnsan devri' : 'İnsan devri yok', cls: result.handoff_required ? 'warn' : 'success'},
    {label: 'DB yazımı yok', cls: 'success'},
    {label: 'Yerel ses kaydı yok', cls: 'success'},
    {label: 'Realtime açıkken mikrofon OpenAI’a gider', cls: 'warn'},
    {label: 'ElevenLabs key panelde görünmez', cls: 'success'},
    {label: result.result === 'BLOCKED' ? 'Güvenlik blokladı' : 'Güvenlik kontrolü', cls: result.result === 'BLOCKED' ? 'warn' : 'info'},
  ] : [
    {label: 'Canlı arama yok', cls: 'info'},
    {label: 'Yerel ses kaydı yok', cls: 'success'},
    {label: 'Realtime açıkken mikrofon OpenAI’a gider', cls: 'warn'},
    {label: 'ElevenLabs key panelde görünmez', cls: 'success'},
    {label: 'DB yazımı yok', cls: 'info'},
    {label: 'PMS yazımı yok', cls: 'info'},
  ];
  refs.voiceLabSafety.innerHTML = badges.map(item => `<span class="${escapeHtml(item.cls)}">${escapeHtml(item.label)}</span>`).join('');
}

function voiceLabResultClass(value) {
  if (value === 'PASS') return 'success';
  if (value === 'FAIL') return 'danger';
  if (value === 'BLOCKED') return 'warn';
  return 'info';
}

function formatVoiceLabResult(value) {
  const labels = {PASS: 'Geçti', FAIL: 'Başarısız', BLOCKED: 'Bloke', UNKNOWN: 'Bekliyor'};
  return labels[String(value || 'UNKNOWN').toUpperCase()] || 'Bekliyor';
}

function formatVoiceLabSource(value) {
  const labels = {HOTEL_PROFILE: 'HOTEL_PROFILE', TOOL: 'Tool', HANDOFF: 'İnsan Devri', UNKNOWN: 'Bilinmiyor'};
  return labels[String(value || 'UNKNOWN').toUpperCase()] || String(value || '-');
}

function formatVoiceLabAction(value) {
  const labels = {answer: 'Cevap', tool_required: 'Tool Gerekli', handoff: 'İnsan Devri', clarify: 'Netleştirme'};
  return labels[String(value || '')] || String(value || '-');
}

function loadResponsePreview() {
  renderResponsePreview();
}

function onResponsePreviewSampleClick(event) {
  const target = event.target.closest('[data-response-sample]');
  if (!target || !refs.responsePreviewSampleList?.contains(target)) return;
  if (refs.responsePreviewQuestion) {
    refs.responsePreviewQuestion.value = target.dataset.responseSample || '';
    refs.responsePreviewQuestion.focus();
  }
  state.responsePreviewResult = null;
  renderResponsePreview();
}

async function onResponsePreviewSubmit(event) {
  event.preventDefault();
  const question = String(refs.responsePreviewQuestion?.value || '').trim();
  if (!question) {
    notify('Müşteri sorusu zorunludur.', 'warn');
    return;
  }
  if (!state.selectedHotelId) {
    notify('Lütfen bir otel seçin.', 'warn');
    return;
  }

  setResponsePreviewLoading(true);
  try {
    state.responsePreviewResult = await apiFetch('/response-preview/generate', {
      method: 'POST',
      body: {
        hotel_id: Number(state.selectedHotelId),
        question,
        language: getResponsePreviewLanguage(),
        response_style: getResponsePreviewStyle(),
      },
    });
    renderResponsePreview();
    notify('Yanıt üretildi.', 'success');
  } catch (error) {
    notify(error.message, 'error');
  } finally {
    setResponsePreviewLoading(false);
  }
}

function clearResponsePreview() {
  if (refs.responsePreviewQuestion) refs.responsePreviewQuestion.value = '';
  state.responsePreviewResult = null;
  renderResponsePreview();
}

async function copyResponsePreviewReply() {
  const reply = String(state.responsePreviewResult?.reply || '').trim();
  if (!reply) {
    notify('Kopyalanacak yanıt yok.', 'warn');
    return;
  }
  try {
    await navigator.clipboard.writeText(reply);
    notify('Yanıt kopyalandı.', 'success');
  } catch (_error) {
    notify('Tarayıcı kopyalama izni vermedi.', 'warn');
  }
}

function getResponsePreviewTranslation(result = state.responsePreviewResult) {
  const translation = result?.translation || null;
  const translatedReply = String(translation?.translated_reply || '').trim();
  const sourceLanguage = normalizeResponsePreviewLanguage(translation?.source_language || result?.internal_json?.language || result?.requested_language || 'auto');
  if (!translation?.available || !translatedReply || sourceLanguage === 'tr') return null;
  return {...translation, source_language: sourceLanguage, translated_reply: translatedReply};
}

function openResponsePreviewTranslation() {
  const translation = getResponsePreviewTranslation();
  const result = state.responsePreviewResult || {};
  if (!translation || !refs.responsePreviewTranslationDialog) {
    notify('Çeviri hazır değil.', 'warn');
    return;
  }
  if (refs.responsePreviewTranslationTitle) refs.responsePreviewTranslationTitle.textContent = 'Çeviri';
  if (refs.responsePreviewTranslationMeta) {
    const modelLabel = translation.model ? ` · Model: ${translation.model}` : '';
    refs.responsePreviewTranslationMeta.textContent = `${formatResponsePreviewLanguage(translation.source_language)} → Türkçe${modelLabel}`;
  }
  if (refs.responsePreviewTranslationBody) {
    refs.responsePreviewTranslationBody.innerHTML = `
      <section class="response-translation-block">
        <strong>Orijinal yanıt (${escapeHtml(formatResponsePreviewLanguage(translation.source_language))})</strong>
        <pre>${escapeHtml(result.reply || '-')}</pre>
      </section>
      <section class="response-translation-block target">
        <strong>Türkçe çeviri</strong>
        <pre>${escapeHtml(translation.translated_reply)}</pre>
      </section>
    `;
  }
  if (!refs.responsePreviewTranslationDialog.open) refs.responsePreviewTranslationDialog.showModal();
}

function closeResponsePreviewTranslation() {
  if (refs.responsePreviewTranslationDialog?.open) refs.responsePreviewTranslationDialog.close();
}

function resetResponsePreviewTranslationDialog() {
  if (refs.responsePreviewTranslationMeta) refs.responsePreviewTranslationMeta.textContent = 'Yanıt çevirisi henüz hazır değil.';
  if (refs.responsePreviewTranslationBody) {
    refs.responsePreviewTranslationBody.innerHTML = '<div class="empty-state"><p>Çeviri burada görüntülenir.</p></div>';
  }
}

function setResponsePreviewLoading(isLoading) {
  state.responsePreviewLoading = isLoading;
  const hasReply = Boolean(state.responsePreviewResult?.reply);
  const hasTranslation = Boolean(getResponsePreviewTranslation(state.responsePreviewResult));
  if (refs.responsePreviewGenerate) {
    refs.responsePreviewGenerate.disabled = isLoading;
    refs.responsePreviewGenerate.textContent = isLoading ? 'Üretiliyor...' : (hasReply ? 'Tekrar Üret' : 'Yanıt Üret');
  }
  if (refs.responsePreviewTranslate) {
    refs.responsePreviewTranslate.hidden = isLoading || !hasTranslation;
    refs.responsePreviewTranslate.disabled = isLoading || !hasTranslation;
  }
  if (refs.responsePreviewCopy) {
    refs.responsePreviewCopy.disabled = isLoading || !hasReply;
  }
}

function renderResponsePreview() {
  const result = state.responsePreviewResult;
  if (!result) {
    if (refs.responsePreviewReply) {
      refs.responsePreviewReply.className = 'response-preview-reply empty-state';
      refs.responsePreviewReply.innerHTML = '<p>Yanıt burada görüntülenir.</p>';
    }
    if (refs.responsePreviewMeta) refs.responsePreviewMeta.textContent = 'Henüz yanıt oluşturulmadı.';
    if (refs.responsePreviewToolList) refs.responsePreviewToolList.innerHTML = '<span class="muted">Henüz araç çağrısı yok.</span>';
    if (refs.responsePreviewInternalJson) refs.responsePreviewInternalJson.textContent = '{}';
    closeResponsePreviewTranslation();
    resetResponsePreviewTranslationDialog();
    renderResponsePreviewSafety(null);
    setResponsePreviewLoading(Boolean(state.responsePreviewLoading));
    return;
  }

  if (refs.responsePreviewReply) {
    refs.responsePreviewReply.className = 'response-preview-reply';
    refs.responsePreviewReply.textContent = result.reply || '-';
  }
  const toolCount = (result.tool_calls || []).length;
  if (refs.responsePreviewMeta) {
    refs.responsePreviewMeta.textContent = [
      `Model: ${result.model || '-'}`,
      `${result.duration_ms || 0} ms`,
      `${toolCount} araç`,
      result.history_created ? 'kayıt var' : 'kayıt yok',
      `Dil: ${formatResponsePreviewLanguage(result.requested_language || 'auto')}`,
      `Ton: ${formatResponsePreviewStyle(result.response_style || 'professional')}`,
    ].join(' · ');
  }
  if (refs.responsePreviewToolList) refs.responsePreviewToolList.innerHTML = renderResponsePreviewTools(result.tool_calls || []);
  if (refs.responsePreviewInternalJson) refs.responsePreviewInternalJson.textContent = JSON.stringify(result.internal_json || {}, null, 2);
  renderResponsePreviewSafety(result);
  setResponsePreviewLoading(Boolean(state.responsePreviewLoading));
}

function renderResponsePreviewTools(items) {
  if (!items.length) {
    return '<span class="muted">Araç çağrısı yapılmadı.</span>';
  }
  return items.map(item => {
    const status = item.blocked ? 'blocked' : (item.status || 'ok');
    const badgeClass = item.blocked ? 'warn' : (status === 'ok' ? 'success' : 'closed');
    const reason = item.reason ? ` · ${item.reason}` : '';
    return `<span class="pill ${badgeClass}">${escapeHtml(item.name || 'tool')} · ${escapeHtml(status)}${escapeHtml(reason)}</span>`;
  }).join('');
}

function renderResponsePreviewSafety(result) {
  if (!refs.responsePreviewSafety) return;
  const badges = result ? buildResponsePreviewSafetyBadges(result) : [
    {label: 'Geçmiş kullanılmaz', cls: 'info'},
    {label: 'Kayıt oluşturulmaz', cls: 'info'},
    {label: 'Yanıt gönderilmez', cls: 'info'},
  ];
  refs.responsePreviewSafety.innerHTML = badges.map(item => {
    return `<span class="${escapeHtml(item.cls)}">${escapeHtml(item.label)}</span>`;
  }).join('');
}

function buildResponsePreviewSafetyBadges(result) {
  const toolCalls = result.tool_calls || [];
  const blockedCount = toolCalls.filter(item => item.blocked).length;
  return [
    {label: 'Geçmişsiz', cls: 'success'},
    {label: result.history_created ? 'Kayıt var' : 'Kayıt yok', cls: result.history_created ? 'warn' : 'success'},
    {label: result.persisted ? 'DB yazımı var' : 'DB yazımı yok', cls: result.persisted ? 'warn' : 'success'},
    {label: toolCalls.length ? `${toolCalls.length} read-only araç` : 'Araçsız yanıt', cls: 'info'},
    blockedCount ? {label: `${blockedCount} araç engellendi`, cls: 'warn'} : null,
    getResponsePreviewTranslation(result) ? {label: 'Türkçe çeviri hazır', cls: 'info'} : null,
    {label: `Dil ${formatResponsePreviewLanguage(result.requested_language || 'auto')}`, cls: 'info'},
    {label: `Ton ${formatResponsePreviewStyle(result.response_style || 'professional')}`, cls: 'info'},
  ].filter(Boolean);
}

function getResponsePreviewLanguage() {
  return String(refs.responsePreviewLanguage?.value || 'auto').trim() || 'auto';
}

function getResponsePreviewStyle() {
  return String(refs.responsePreviewStyle?.value || 'professional').trim() || 'professional';
}

function normalizeResponsePreviewLanguage(value) {
  const normalized = String(value || 'auto').trim().toLowerCase();
  return ['auto','tr','en','de','ru','ar','es','fr','zh','hi','pt'].includes(normalized) ? normalized : 'auto';
}

function formatResponsePreviewLanguage(value) {
  const labels = {auto: 'Otomatik', tr: 'Türkçe', en: 'İngilizce (Britanya)', de: 'Deutsch', ru: 'Русский', ar: 'العربية', es: 'Español', fr: 'Français', zh: '中文', hi: 'हिन्दी', pt: 'Português'};
  return labels[String(value || 'auto').toLowerCase()] || 'Otomatik';
}

function formatResponsePreviewStyle(value) {
  const labels = {professional: 'Profesyonel', warm: 'Sıcak', concise: 'Kısa'};
  return labels[String(value || 'professional').toLowerCase()] || 'Profesyonel';
}

async function loadChatLab() {
  const frame = document.getElementById('chatlab-frame');
  if (!frame) return;
  let tokenPayload;
  try {
    tokenPayload = await apiFetch('/session/refresh', {method: 'POST', body: {}, auth: false, allowRefresh: false, logoutOn401: false});
  } catch (_e) {
    try {
      tokenPayload = await apiFetch('/me', {allowRefresh: true});
    } catch (_e2) { return; }
  }
  const token = tokenPayload?.access_token || '';
  const needsLoad = !frame.src || frame.src === 'about:blank' || frame.contentWindow?.location?.href === 'about:blank';
  if (needsLoad) {
    frame.src = '/admin/chat-lab';
  }
  // Send token to iframe once it finishes loading
  const sendToken = () => {
    try { frame.contentWindow.postMessage({type: 'chatlab:token', token, hotelId: state.selectedHotelId}, window.location.origin); } catch(_e) {}
  };
  if (needsLoad) {
    frame.addEventListener('load', sendToken, {once: true});
  } else {
    sendToken();
  }
}

async function loadResponseReviews(options = {}) {
  if (!refs.responseReviewList) return;
  const params = new URLSearchParams();
  if (state.me?.role === 'ADMIN' && state.selectedHotelId) params.set('hotel_id', state.selectedHotelId);
  const statusValue = refs.responseReviewStatusFilter?.value || '';
  const classificationValue = refs.responseReviewClassificationFilter?.value || '';
  const errorValue = refs.responseReviewErrorFilter?.value || '';
  if (statusValue) params.set('status', statusValue);
  if (classificationValue) params.set('classification', classificationValue);
  if (errorValue) params.set('error_type', errorValue);
  params.set('limit', '80');
  try {
    const response = await apiFetch(`/response-reviews?${params.toString()}`);
    state.responseReviewItems = response.items || [];
    state.responseReviewTotal = Number(response.total || 0);
    renderResponseReviewList();
    const requestedId = options.selectFromQuery ? new URLSearchParams(window.location.search).get('review_id') : '';
    const targetId = requestedId || state.activeResponseReviewId || state.responseReviewItems[0]?.id || '';
    if (targetId) await loadResponseReviewDetail(targetId, {silent: true});
    else renderResponseReviewEmptyDetail();
  } catch (error) {
    refs.responseReviewList.innerHTML = `<div class="empty-state"><p>${escapeHtml(error.message || 'Rapor listesi alınamadı.')}</p></div>`;
  }
}

function renderResponseReviewList() {
  if (!refs.responseReviewList) return;
  if (!state.responseReviewItems.length) {
    refs.responseReviewList.innerHTML = '<div class="empty-state"><p>Bu filtrelerle raporlanan yanıt bulunamadı.</p></div>';
    return;
  }
  refs.responseReviewList.innerHTML = state.responseReviewItems.map(item => `
    <button class="response-review-card ${state.activeResponseReviewId === item.id ? 'is-active' : ''}" type="button" data-response-review-id="${escapeHtml(item.id)}">
      <div class="response-review-card-top">
        <strong>${escapeHtml(formatReviewErrorType(item.error_type))}</strong>
        <span class="review-chip ${escapeHtml(item.status)}">${escapeHtml(formatReviewStatus(item.status))}</span>
      </div>
      <p>${escapeHtml(truncateText(item.message_content || '', 180))}</p>
      <div class="response-review-meta">
        <span class="review-chip ${escapeHtml(item.classification)}">${escapeHtml(formatReviewClassification(item.classification))}</span>
        <span class="muted">${escapeHtml(formatDate(item.reported_at))}</span>
      </div>
      <div class="response-review-meta mt-sm">
        <span class="muted">${escapeHtml(item.reported_by_display_name || item.reported_by_username || 'Bilinmiyor')}</span>
        <span class="muted">${escapeHtml(item.included_in_report ? 'Raporda' : 'Rapor dışı')}</span>
      </div>
    </button>
  `).join('');
}

function renderResponseReviewEmptyDetail() {
  if (!refs.responseReviewDetail) return;
  refs.responseReviewDetail.innerHTML = `
    <div class="empty-state">
      <p>Bir rapor seçin veya operasyon masasındaki AI yanıtına sağ tıklayıp <strong>Raporla</strong> aksiyonunu kullanın.</p>
    </div>
  `;
}

async function loadResponseReviewDetail(reviewId, options = {}) {
  if (!reviewId || !refs.responseReviewDetail) return;
  try {
    const params = new URLSearchParams();
    if (state.me?.role === 'ADMIN' && state.selectedHotelId) params.set('hotel_id', state.selectedHotelId);
    const query = params.toString() ? `?${params.toString()}` : '';
    const detail = await apiFetch(`/response-reviews/${encodeURIComponent(reviewId)}${query}`);
    state.activeResponseReviewId = detail.id;
    state.responseReviewDetail = detail;
    renderResponseReviewList();
    renderResponseReviewDetail(detail);
  } catch (error) {
    if (!options.silent) notify(error.message || 'Rapor detayı alınamadı.', 'error');
  }
}

function renderResponseReviewDetail(detail) {
  const contextMessages = Array.isArray(detail.context_messages) ? detail.context_messages : [];
  refs.responseReviewDetail.innerHTML = `
    <div class="module-header compact">
      <div>
        <h3>İnceleme Detayı</h3>
        <p>${escapeHtml(detail.conversation_snapshot?.phone_display || 'Maskeli misafir')} · ${escapeHtml(formatReviewStatus(detail.status))}</p>
      </div>
      <span class="review-chip ${escapeHtml(detail.classification)}">${escapeHtml(formatReviewClassification(detail.classification))}</span>
    </div>
    <div class="response-review-detail-grid">
      <div class="review-detail-card">
        <h4>Raporlanan Yanıt</h4>
        <div class="reported-message-box">${escapeHtml(detail.message_content || '')}</div>
        <div class="decision-row"><span>Konuşma</span><strong>${escapeHtml(detail.conversation_id)}</strong></div>
        <div class="decision-row"><span>Mesaj</span><strong>${escapeHtml(detail.message_id)}</strong></div>
        <div class="decision-row"><span>Raporlayan</span><strong>${escapeHtml(detail.reported_by_display_name || detail.reported_by_username || '-')}</strong></div>
        <div class="decision-row"><span>Rapor zamanı</span><strong>${escapeHtml(formatDate(detail.reported_at))}</strong></div>
        <h4 class="mt-md">Konuşma Bağlamı</h4>
        <div class="review-context-stream">
          ${contextMessages.map(message => renderReviewContextMessage(message, detail.message_id)).join('')}
        </div>
      </div>
      <div class="review-detail-card">
        <h4>Karar ve Feedback</h4>
        <form class="review-form" data-review-form>
          <label>Hata Tipi
            <select name="error_type">
              ${renderReviewErrorOptions(detail.error_type)}
            </select>
          </label>
          <label>Puan
            <select name="rating">
              <option value="5" ${detail.rating === 5 ? 'selected' : ''}>5 · Doğru örnek</option>
              <option value="4" ${detail.rating === 4 ? 'selected' : ''}>4 · Fazla ayrıntı</option>
              <option value="3" ${!detail.rating || detail.rating === 3 ? 'selected' : ''}>3 · Eksik bilgi</option>
              <option value="2" ${detail.rating === 2 ? 'selected' : ''}>2 · Hatalı anlatım</option>
              <option value="1" ${detail.rating === 1 ? 'selected' : ''}>1 · Yanlış bilgi</option>
            </select>
          </label>
          <label>Referans Yanıt
            <textarea name="gold_standard" placeholder="Yanlış veya düzeltilmeli ise olması gereken kısa cevabı yazın.">${escapeHtml(detail.gold_standard || '')}</textarea>
          </label>
          <label>Not
            <textarea name="notes" placeholder="Operasyon veya kalite ekibi için kısa not.">${escapeHtml(detail.notes || '')}</textarea>
          </label>
          <label class="toggle-row">
            <span class="toggle-copy"><strong>Genel rapora dahil et</strong><small>Problemli yanıt final raporlarında kullanılır.</small></span>
            <span class="switch"><input name="included_in_report" type="checkbox" ${detail.included_in_report ? 'checked' : ''}><span class="switch-track"><span class="switch-thumb"></span></span></span>
          </label>
          <div class="review-action-row">
            <button class="action-button primary" type="button" data-review-classify="correct">Doğru</button>
            <button class="action-button warn" type="button" data-review-classify="needs_revision">Düzeltilmeli</button>
            <button class="action-button danger" type="button" data-review-classify="incorrect">Yanlış</button>
          </div>
        </form>
        <h4 class="mt-md">İşlem Geçmişi</h4>
        <div class="review-history">
          ${(detail.actions || []).length ? detail.actions.map(renderReviewHistoryItem).join('') : '<div class="muted">Henüz işlem yok.</div>'}
        </div>
      </div>
    </div>
  `;
}

function renderReviewContextMessage(message, targetId) {
  const isTarget = String(message.id || '') === String(targetId || '');
  const roleLabel = message.role === 'user' ? 'Misafir' : message.role === 'assistant' ? 'AI' : message.role === 'operator' ? 'Operatör' : 'Sistem';
  return `
    <div class="review-context-message ${isTarget ? 'is-target' : ''}">
      <b><span>${escapeHtml(roleLabel)}</span><span>${escapeHtml(formatDate(message.created_at))}</span></b>
      <div>${escapeHtml(message.content || '')}</div>
    </div>
  `;
}

function renderReviewHistoryItem(action) {
  return `
    <div class="review-history-item">
      <strong>${escapeHtml(formatReviewAction(action.action_type))}</strong>
      <span>${escapeHtml(action.actor_username || '-')} · ${escapeHtml(formatDate(action.created_at))}</span>
      ${action.notes ? `<div>${escapeHtml(action.notes)}</div>` : ''}
    </div>
  `;
}

async function submitResponseReviewClassification(classification) {
  const detail = state.responseReviewDetail;
  if (!detail) return;
  const form = refs.responseReviewDetail.querySelector('[data-review-form]');
  if (!form) return;
  const data = new FormData(form);
  const isCorrect = classification === 'correct';
  const payload = {
    classification,
    error_type: isCorrect ? 'not_classified' : String(data.get('error_type') || 'other'),
    rating: isCorrect ? 5 : Number(data.get('rating') || 3),
    gold_standard: isCorrect ? null : String(data.get('gold_standard') || '').trim(),
    notes: String(data.get('notes') || '').trim() || null,
    included_in_report: !isCorrect && Boolean(data.get('included_in_report')),
    finalize: true,
  };
  if (!isCorrect && !payload.gold_standard) {
    notify('Yanlış veya düzeltilmeli kararında referans yanıt zorunludur.', 'warn');
    return;
  }
  if (!isCorrect && payload.error_type === 'not_classified') {
    notify('Yanlış veya düzeltilmeli kararında hata tipi seçilmelidir.', 'warn');
    return;
  }
  try {
    const params = new URLSearchParams();
    if (state.me?.role === 'ADMIN' && state.selectedHotelId) params.set('hotel_id', state.selectedHotelId);
    const query = params.toString() ? `?${params.toString()}` : '';
    const updated = await apiFetch(`/response-reviews/${encodeURIComponent(detail.id)}/classify${query}`, {method: 'POST', body: payload});
    notify('İnceleme kaydedildi ve feedback yapısına aktarıldı.', 'success');
    state.responseReviewDetail = updated;
    await loadResponseReviews();
    await loadResponseReviewDetail(updated.id, {silent: true});
  } catch (error) {
    notify(error.message || 'İnceleme kaydedilemedi.', 'error');
  }
}

function renderReviewErrorOptions(selected) {
  return [
    ['not_classified','Seçilmedi'],
    ['wrong_info','Yanlış bilgi'],
    ['missing_info','Eksik bilgi'],
    ['wrong_intent','Niyet ıskalama'],
    ['source_mismatch','Kaynak uyumsuzluğu'],
    ['unsupported_claim','Kaynaksız iddia'],
    ['policy_risk','Politika riski'],
    ['pii_risk','PII riski'],
    ['tone_or_length','Ton / uzunluk'],
    ['language_issue','Dil sorunu'],
    ['tool_mismatch','Araç sonucu uyumsuz'],
    ['handoff_required','İnsan devri gerekirdi'],
    ['delivery_status_issue','Teslimat durumu'],
    ['other','Diğer'],
  ].map(([value, label]) => `<option value="${escapeHtml(value)}" ${value === selected ? 'selected' : ''}>${escapeHtml(label)}</option>`).join('');
}

function formatReviewStatus(value) {
  return {open: 'Açık', in_review: 'İncelemede', finalized: 'Tamamlandı', closed: 'Kapalı'}[String(value || '')] || 'Açık';
}

function formatReviewClassification(value) {
  return {needs_review: 'İnceleme bekliyor', correct: 'Doğru', incorrect: 'Yanlış', needs_revision: 'Düzeltilmeli'}[String(value || '')] || 'İnceleme bekliyor';
}

function formatReviewErrorType(value) {
  return {
    not_classified: 'Hata tipi seçilmedi',
    wrong_info: 'Yanlış bilgi',
    missing_info: 'Eksik bilgi',
    wrong_intent: 'Niyet ıskalama',
    source_mismatch: 'Kaynak uyumsuzluğu',
    unsupported_claim: 'Kaynaksız iddia',
    policy_risk: 'Politika riski',
    pii_risk: 'PII riski',
    tone_or_length: 'Ton / uzunluk',
    language_issue: 'Dil sorunu',
    tool_mismatch: 'Araç uyumsuzluğu',
    handoff_required: 'İnsan devri gerekirdi',
    delivery_status_issue: 'Teslimat durumu',
    other: 'Diğer',
  }[String(value || '')] || 'Diğer';
}

function formatReviewAction(value) {
  return {reported: 'Raporlandı', classified: 'Sınıflandırıldı'}[String(value || '')] || value || 'İşlem';
}

async function loadDashboard() {
  const query = state.selectedHotelId ? `?hotel_id=${encodeURIComponent(state.selectedHotelId)}` : '';
  state.dashboard = await apiFetch(`/dashboard/overview${query}`);
  renderDashboard();
}

function renderDashboard() {
  if (!state.dashboard) return;
  const cards = [
    ['Aktif Konuşma', state.dashboard.cards.conversations_active, 'Canlı takip gereken oturumlar'],
    ['Bekleyen Onay', state.dashboard.cards.pending_holds, 'Onay akışını tıkayan kayıtlar'],
    ['Açık Talep', state.dashboard.cards.open_tickets, 'Operasyon, satış ve şef kuyrukları'],
    ['Yüksek Öncelik', state.dashboard.cards.high_priority_tickets, 'Gecikirse risk artıran olaylar'],
  ];
  refs.dashboardCards.innerHTML = cards.map(item => `
    <article class="overview-card">
      <h4>${escapeHtml(item[0])}</h4>
      <strong>${escapeHtml(item[1] ?? 0)}</strong>
      <span>${escapeHtml(item[2])}</span>
    </article>
  `).join('');

  refs.dashboardQueues.innerHTML = `
    <div class="queue-card">
      <div class="module-header"><div><h3>Son Konuşmalar</h3><p>Risk ve niyet bağlamıyla son aktivite.</p></div></div>
      ${renderQueue(state.dashboard.recent_conversations, item => `
        <div class="queue-item">
          <strong>${escapeHtml(item.phone_display || 'Maskeli kullanıcı')}</strong>
          <span class="muted">${escapeHtml(formatConversationState(item.current_state || '-'))} · ${escapeHtml(item.current_intent || '-')}</span>
          <div class="muted">${formatDate(item.last_message_at)}</div>
        </div>
      `, 'Konuşma yok')}
    </div>
    <div class="queue-card">
      <div class="module-header"><div><h3>Bekleyen Onaylar</h3><p>Onay bekleyen kararlar burada yoğunlaşır.</p></div></div>
      ${renderQueue(state.dashboard.recent_holds, item => `
        <div class="queue-item">
          <strong>${escapeHtml(item.hold_id)}</strong>
          <span class="muted">${escapeHtml(formatHoldType(item.hold_type))} · ${escapeHtml(formatOperationalStatus(item.status))}</span>
          <div class="muted">${formatDate(item.created_at)}</div>
        </div>
      `, 'Bekleyen onay yok')}
    </div>
    <div class="queue-card">
      <div class="module-header"><div><h3>Açık Talepler</h3><p>Devir kuyruğunda sahiplik ve öncelik takibi.</p></div></div>
      ${renderQueue(state.dashboard.recent_tickets, item => `
        <div class="queue-item">
          <strong>${escapeHtml(item.ticket_id)}</strong>
          <span class="muted">${escapeHtml(item.reason)} · ${escapeHtml(formatPriorityLabel(item.priority))}</span>
          <div class="muted">${formatDate(item.created_at)}</div>
        </div>
      `, 'Açık talep yok')}
    </div>
  `;
  renderNavigation();
}

function renderQueue(items, renderItem, emptyLabel) {
  if (!items || !items.length) {
    return `<div class="empty-state"><p>${escapeHtml(emptyLabel)}</p></div>`;
  }
  return `<div class="queue-list">${items.map(renderItem).join('')}</div>`;
}

async function loadConversations() {
  const params = buildConversationParams();
  const response = await apiFetch(`/conversations?${params.toString()}`);
  state.conversations = response.items || [];
  state.conversationsTotal = Number(response.total || 0);
  syncConversationSelection();
  const visibleItems = getVisibleConversationItems();
  refs.conversationTableBody.innerHTML = renderConversationRows(visibleItems);
  if (visibleItems.length && !state.conversationDetail) {
    loadConversationDetail(visibleItems[0].id);
  } else if (!visibleItems.length) {
    refs.conversationDetail.innerHTML = '<div class="empty-state"><p>Bu filtrede konuşma yok.</p></div>';
    renderDecisionPanel(null, []);
  }
  updateConversationBulkBar();
}

function buildConversationParams() {
  const form = new FormData(refs.conversationFilters);
  const params = new URLSearchParams();
  if (state.me?.role === 'ADMIN' && state.selectedHotelId) params.set('hotel_id', state.selectedHotelId);
  if (form.get('active_only')) params.set('active_only', 'true');
  if (form.get('status')) params.set('status', String(form.get('status')));
  if (form.get('date_from')) params.set('date_from', String(form.get('date_from')));
  if (form.get('date_to')) params.set('date_to', String(form.get('date_to')));
  return params;
}

function renderConversationListFromState() {
  const visibleItems = getVisibleConversationItems();
  syncConversationSelection();
  refs.conversationTableBody.innerHTML = renderConversationRows(visibleItems);
  updateConversationBulkBar();
  const selectedId = String(state.conversationDetail?.conversation?.id || '');
  if (selectedId && !visibleItems.some(item => String(item.id) === selectedId)) {
    refs.conversationDetail.innerHTML = '<div class="empty-state"><p>Seçili konuşma bu filtrede görünmüyor.</p></div>';
    renderDecisionPanel(null, []);
  }
}

function getVisibleConversationItems() {
  const query = String(state.conversationSearch || '').toLowerCase();
  return (state.conversations || []).filter(item => {
    if (!matchesConversationFilter(item, state.conversationFilter)) return false;
    if (!query) return true;
    const haystack = [
      item.phone_display,
      item.id,
      item.current_state,
      item.current_intent,
      conversationPreview(item),
      ...(item.risk_flags || []),
      ...conversationTags(item),
    ].join(' ').toLowerCase();
    return haystack.includes(query);
  });
}

function matchesConversationFilter(item, filter) {
  const key = String(filter || 'all');
  const intent = String(item.current_intent || '').toLowerCase();
  const stateValue = String(item.current_state || '').toLowerCase();
  const risks = item.risk_flags || [];
  if (key === 'all') return true;
  if (key === 'unread') return getConversationUnreadCount(item) > 0;
  if (key === 'handoff') return Boolean(item.human_override) || stateValue.includes('handoff');
  if (key === 'approval') return stateValue.includes('approval') || stateValue.includes('pending');
  if (key === 'reservation') return /reservation|rezervasyon|booking|stay|konaklama|availability/.test(intent);
  if (key === 'restaurant') return /restaurant|restoran|dining|order|siparis|sipariş/.test(intent);
  if (key === 'transfer') return /transfer|airport|havalimani|havalimanı/.test(intent);
  if (key === 'risk') return Array.isArray(risks) && risks.length > 0;
  return true;
}

function getConversationUnreadCount(item) {
  return Number(item.unread_count || item.unread_messages || item.pending_inbound_count || 0);
}

function conversationPreview(item) {
  const internal = asObject(item.last_user_internal_json);
  const candidate = internal.preview || internal.message_preview || internal.last_message || '';
  if (candidate) return String(candidate);
  const intent = resolveConversationIntent(item, []);
  const stateLabel = formatConversationState(item.current_state || '-');
  return intent && intent !== 'intent yok'
    ? `${formatIntentLabel(intent)} talebi · ${stateLabel}`
    : `${stateLabel} · ${Number(item.message_count || 0)} mesaj`;
}

function conversationTags(item) {
  const tags = [];
  const intent = String(resolveConversationIntent(item, []) || '');
  const intentLower = intent.toLowerCase();
  if (/restaurant|restoran|dining|order|siparis|sipariş/.test(intentLower)) tags.push('Restoran');
  else if (/transfer|airport|havalimani|havalimanı/.test(intentLower)) tags.push('Transfer');
  else if (/reservation|rezervasyon|booking|stay|konaklama|availability/.test(intentLower)) tags.push('Rezervasyon');
  else if (intent && intent !== 'intent yok') tags.push(formatIntentLabel(intent));
  if (item.human_override) tags.push('İnsan devri');
  if ((item.risk_flags || []).length) tags.push('Riskli');
  if (String(item.current_state || '').toLowerCase().includes('approval')) tags.push('Onay bekliyor');
  return tags.slice(0, 4);
}

function formatIntentLabel(value) {
  const normalized = String(value || '').replace(/_/g, ' ').trim();
  if (!normalized) return 'Talep';
  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

function getConversationStatusClass(item) {
  const stateValue = String(item.current_state || '').toLowerCase();
  if ((item.risk_flags || []).length) return 'is-risk';
  if (item.human_override || stateValue.includes('handoff')) return 'is-handoff';
  if (stateValue.includes('approval') || stateValue.includes('pending')) return 'is-approval';
  return '';
}

function renderConversationRows(items) {
  if (!items.length) {
    return `<div class="empty-state"><p>Filtreye uygun konuşma bulunamadı.</p></div>`;
  }
  return items.map(item => `
    <div role="button" tabindex="0" class="conversation-card ${state.selectedConversationIds.has(String(item.id)) ? 'is-selected' : ''} ${String(state.conversationDetail?.conversation?.id || '') === String(item.id) ? 'is-active' : ''}" data-open-conversation="${escapeHtml(item.id)}" data-conversation-row="${escapeHtml(item.id)}">
      <input class="conversation-select-inline row-select" type="checkbox" data-select-conversation="${escapeHtml(item.id)}" ${state.selectedConversationIds.has(String(item.id)) ? 'checked' : ''} aria-label="Konuşmayı seç" onclick="event.stopPropagation()">
      <div class="conversation-card-top">
        <div class="conversation-card-title">
          <span class="conversation-avatar" aria-hidden="true">${escapeHtml(getGuestInitials(item.phone_display || 'Misafir'))}</span>
          <strong>${escapeHtml(item.phone_display || 'Maskeli misafir')}</strong>
        </div>
        <span class="conversation-time">${escapeHtml(formatConversationTime(item.updated_at || item.created_at))}</span>
      </div>
      <p class="conversation-preview">${escapeHtml(conversationPreview(item))}</p>
      <div class="conversation-card-meta">
        <div class="conversation-tags">
          <span class="conversation-status-badge ${getConversationStatusClass(item)}">${escapeHtml(formatConversationState(item.current_state || '-'))}</span>
          ${conversationTags(item).map(tag => `<span class="conversation-tag">${escapeHtml(tag)}</span>`).join('')}
        </div>
        ${getConversationUnreadCount(item) ? `<span class="unread-badge">${escapeHtml(getConversationUnreadCount(item))}</span>` : ''}
      </div>
    </div>
  `).join('');
}

function getGuestInitials(value) {
  const text = String(value || 'Misafir').replace(/[^\\p{L}\\p{N}\\s]/gu, ' ').trim();
  const parts = text.split(/\\s+/).filter(Boolean);
  if (!parts.length) return 'M';
  return parts.slice(0, 2).map(part => part[0]).join('').toUpperCase();
}

function formatConversationTime(value) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleTimeString('tr-TR', {hour: '2-digit', minute: '2-digit'});
}

function syncConversationSelection() {
  const allowed = new Set((state.conversations || []).map(item => String(item.id)));
  for (const id of state.selectedConversationIds) {
    if (!allowed.has(id)) state.selectedConversationIds.delete(id);
  }
}

function updateConversationBulkBar() {
  const selectedCount = state.selectedConversationIds.size;
  const visibleItems = getVisibleConversationItems();
  const hasItems = visibleItems.length > 0;
  if (refs.conversationBulkBar) refs.conversationBulkBar.hidden = !hasItems;
  if (refs.conversationSelectionCount) {
    refs.conversationSelectionCount.textContent = `${selectedCount} seçili · görünür ${visibleItems.length} · toplam ${state.conversationsTotal || 0}`;
  }

  if (refs.conversationBulkBar) {
    const disableActions = selectedCount === 0;
    refs.conversationBulkBar.querySelectorAll('button[data-bulk-action]').forEach(button => {
      button.disabled = disableActions;
    });
  }

  if (refs.conversationSelectAll) {
    const total = visibleItems.length;
    if (!total) {
      refs.conversationSelectAll.checked = false;
      refs.conversationSelectAll.indeterminate = false;
      refs.conversationSelectAll.disabled = true;
    } else {
      refs.conversationSelectAll.disabled = false;
      if (selectedCount === 0) {
        refs.conversationSelectAll.checked = false;
        refs.conversationSelectAll.indeterminate = false;
      } else if (selectedCount === total) {
        refs.conversationSelectAll.checked = true;
        refs.conversationSelectAll.indeterminate = false;
      } else {
        refs.conversationSelectAll.checked = false;
        refs.conversationSelectAll.indeterminate = true;
      }
    }
  }
}

function clearConversationSelection() {
  state.selectedConversationIds.clear();
  updateConversationBulkBar();
  if (refs.conversationTableBody) {
    refs.conversationTableBody.querySelectorAll('[data-select-conversation]').forEach(input => {
      input.checked = false;
      const row = input.closest('[data-conversation-row]');
      if (row) row.classList.remove('is-selected');
    });
  }
}

function toggleConversationSelection(conversationId, shouldSelect) {
  if (shouldSelect) state.selectedConversationIds.add(conversationId);
  else state.selectedConversationIds.delete(conversationId);
  updateConversationBulkBar();
}

function onConversationSelectionChange(event) {
  const target = event.target;
  if (!target || !target.matches('[data-select-conversation]')) return;
  const convId = String(target.dataset.selectConversation || '');
  if (!convId) return;
  toggleConversationSelection(convId, target.checked);
  const row = target.closest('[data-conversation-row]');
  if (row) row.classList.toggle('is-selected', target.checked);
  event.stopPropagation();
}

function onConversationSelectAllChange() {
  if (!refs.conversationSelectAll) return;
  const checked = refs.conversationSelectAll.checked;
  const items = getVisibleConversationItems();
  items.forEach(item => {
    const convId = String(item.id);
    if (checked) state.selectedConversationIds.add(convId);
    else state.selectedConversationIds.delete(convId);
  });
  if (refs.conversationTableBody) {
    refs.conversationTableBody.querySelectorAll('[data-select-conversation]').forEach(input => {
      input.checked = checked;
      const row = input.closest('[data-conversation-row]');
      if (row) row.classList.toggle('is-selected', checked);
    });
  }
  updateConversationBulkBar();
}

async function runConversationBulkAction(action) {
  if (action === 'clear') {
    clearConversationSelection();
    return;
  }

  if (action === 'select-filtered') {
    await selectFilteredConversations();
    return;
  }

  const conversationIds = Array.from(state.selectedConversationIds);
  if (!conversationIds.length) {
    notify('Seçili konuşma yok.', 'warn');
    return;
  }

  let confirmMessage = '';
  let endpoint = '';
  let body = null;

  if (action === 'deactivate') {
    confirmMessage = `Seçili ${conversationIds.length} konuşmayı pasife almak istediğinize emin misiniz?`;
    endpoint = '/conversations/bulk/deactivate';
    body = {conversation_ids: conversationIds};
  } else if (action === 'reset') {
    confirmMessage = `Seçili ${conversationIds.length} konuşmayı sıfırlamak istediğinize emin misiniz?`;
    endpoint = '/conversations/bulk/reset';
    body = {conversation_ids: conversationIds};
  } else if (action === 'human-on') {
    confirmMessage = `Seçili ${conversationIds.length} konuşmayı insan devrine almak istediğinize emin misiniz?`;
    endpoint = '/conversations/bulk/human-override';
    body = {conversation_ids: conversationIds, enable: true};
  } else if (action === 'human-off') {
    confirmMessage = `Seçili ${conversationIds.length} konuşmayı yapay zekâ moduna almak istediğinize emin misiniz?`;
    endpoint = '/conversations/bulk/human-override';
    body = {conversation_ids: conversationIds, enable: false};
  }

  if (!endpoint) return;
  if (!confirm(confirmMessage)) return;
  try {
    await apiFetch(endpoint, {method: 'POST', body});
    notify('Toplu işlem tamamlandı.', 'success');
    clearConversationSelection();
    loadConversations();
  } catch (error) {
    notify(error.message || 'Toplu işlem başarısız.', 'error');
  }
}

async function selectFilteredConversations() {
  const params = buildConversationParams();
  params.set('limit', '1000');
  try {
    const response = await apiFetch(`/conversations/ids?${params.toString()}`);
    const ids = response.items || [];
    state.selectedConversationIds = new Set(ids.map(String));
    refs.conversationTableBody?.querySelectorAll('[data-select-conversation]').forEach(input => {
      const convId = String(input.dataset.selectConversation || '');
      const checked = state.selectedConversationIds.has(convId);
      input.checked = checked;
      const row = input.closest('[data-conversation-row]');
      if (row) row.classList.toggle('is-selected', checked);
    });
    updateConversationBulkBar();
    if (response.total > ids.length) {
      notify(`Filtredeki ilk ${ids.length} konuşma seçildi (toplam ${response.total}).`, 'warn');
    } else {
      notify(`Filtredeki ${ids.length} konuşma seçildi.`, 'success');
    }
  } catch (error) {
    notify(error.message || 'Filtrede seçim başarısız.', 'error');
  }
}

// Event delegation: conversation table clicks handled by container listener (see bindDelegatedEvents)

async function loadConversationDetail(conversationId) {
  const response = await apiFetch(`/conversations/${conversationId}`);
  state.conversationDetail = response;
  const resolvedIntent = resolveConversationIntent(response.conversation, response.messages || []);
  const resolvedState = resolveConversationState(response.conversation, response.messages || []);
  const messages = response.messages || [];
  const approvalMessage = findLatestPendingAssistantMessage(messages);
  refs.conversationDetail.innerHTML = `
    <div class="whatsapp-thread-header">
      <div class="thread-guest">
        <span class="conversation-avatar" aria-hidden="true">${escapeHtml(getGuestInitials(response.conversation.phone_display || 'Misafir'))}</span>
        <div>
          <strong>${escapeHtml(response.conversation.phone_display || 'Maskeli misafir')}</strong>
          <span>${escapeHtml(resolvedState)} · ${escapeHtml(formatIntentLabel(resolvedIntent))}</span>
        </div>
      </div>
      <div class="thread-actions">
        <span class="conversation-status-badge ${getConversationStatusClass(response.conversation)}">${escapeHtml(response.conversation.human_override ? 'İnsan devri' : 'AI izliyor')}</span>
        ${response.conversation.is_active ? `
          <button class="action-button ${response.conversation.human_override ? 'primary' : 'warn'} action-button-sm" data-toggle-human-override="${escapeHtml(String(response.conversation.id))}" data-current-override="${response.conversation.human_override ? 'true' : 'false'}">${response.conversation.human_override ? 'AI Moduna Al' : 'İnsan Devrine Al'}</button>
        ` : '<span class="pill pill-closed">Kapalı</span>'}
      </div>
    </div>
    <div class="whatsapp-thread-body">
      <div class="message-stream">
        ${messages.length ? messages.map(renderOperationMessageBubble).join('') : '<div class="empty-state"><p>Henüz mesaj yok.</p></div>'}
      </div>
    </div>
    <div class="thread-composer">
      ${approvalMessage ? renderAiDraftBox(response.conversation, approvalMessage) : `
        <div class="ai-draft-box">
          <strong>AI taslağı</strong>
          <p>Onay bekleyen taslak yok. Yeni yanıt üretimi mevcut backend akışı üzerinden yapılır.</p>
        </div>
      `}
      <div class="composer-row">
        <textarea data-message-composer placeholder="Misafire sorulacak kısa notu yazın" aria-label="Misafire sorulacak mesaj"></textarea>
        <button class="action-button secondary" type="button" data-scroll-composer="true">Düzenle</button>
      </div>
    </div>
  `;
  renderDecisionPanel(response.conversation, messages);
  renderConversationListFromState();
}

function renderOperationMessageBubble(message) {
  const role = String(message.role || 'system').toLowerCase();
  const bubbleClass = role === 'user' ? 'is-user' : role === 'assistant' ? 'is-assistant' : role === 'operator' ? 'is-operator' : 'is-system';
  const roleLabel = role === 'user' ? 'Misafir' : role === 'assistant' ? 'AI' : role === 'operator' ? 'Operatör' : 'Sistem';
  const status = deriveMessageStatus(message);
  const canReport = ['assistant','operator','system'].includes(role) && message.id && state.conversationDetail?.conversation?.id;
  return `
    <article class="chat-bubble ${bubbleClass}" ${canReport ? `tabindex="0" data-review-conversation="${escapeHtml(String(state.conversationDetail.conversation.id))}" data-review-message="${escapeHtml(String(message.id))}" data-review-role="${escapeHtml(role)}"` : ''}>
      <div class="chat-bubble-header">
        <span>${escapeHtml(roleLabel)}</span>
        <span>${escapeHtml(formatDate(message.created_at))}</span>
        ${canReport ? `<button class="message-menu-button" type="button" data-open-message-menu="true" aria-label="Yanıt menüsü">⋯</button>` : ''}
      </div>
      <div class="chat-bubble-content">${escapeHtml(message.content || '')}</div>
      ${role === 'assistant' || role === 'operator' ? `<div class="message-status ${escapeHtml(status.className)}">${escapeHtml(status.label)}</div>` : ''}
      ${renderDeveloperDetails(message)}
    </article>
  `;
}

function deriveMessageStatus(message) {
  const internal = asObject(message.internal_json);
  const providerStatus = String(internal.provider_status || internal.delivery_status || '').toLowerCase();
  if (internal.provider_error || internal.failed_at || providerStatus === 'failed' || providerStatus === 'error') return {label: 'Hata', className: 'is-error'};
  if (internal.send_blocked || internal.approval_pending) return {label: 'Kuyrukta', className: 'is-queued'};
  if (providerStatus === 'read' || internal.read_at) return {label: 'Okundu', className: 'is-read'};
  if (providerStatus === 'delivered' || internal.delivered_at) return {label: 'Teslim edildi', className: ''};
  if (message.whatsapp_message_id || internal.whatsapp_message_id || internal.sent_at || providerStatus === 'sent') return {label: 'Gönderildi', className: ''};
  return {label: 'Kuyrukta', className: 'is-queued'};
}

function renderDeveloperDetails(message) {
  const internal = asObject(message.internal_json);
  const toolCalls = Array.isArray(message.tool_calls) ? message.tool_calls : [];
  if (!Object.keys(internal).length && !toolCalls.length) return '';
  return `
    <details class="developer-details">
      <summary>Geliştirici Detayı</summary>
      <pre>${escapeHtml(JSON.stringify({internal_json: internal, tool_calls: toolCalls}, null, 2))}</pre>
    </details>
  `;
}

function onOperationMessageContextMenu(event) {
  const bubble = event.target.closest?.('[data-review-message]');
  if (!bubble) return;
  event.preventDefault();
  openResponseContextMenuForBubble(bubble, {left: event.clientX, top: event.clientY, width: 0, height: 0});
}

function openResponseContextMenuForBubble(bubble, anchorRect) {
  closeResponseContextMenu();
  const conversationId = bubble.dataset.reviewConversation || '';
  const messageId = bubble.dataset.reviewMessage || '';
  if (!conversationId || !messageId) return;
  const messageText = getOperationMessageText(conversationId, messageId, bubble);
  const menu = document.createElement('div');
  menu.className = 'response-context-menu';
  menu.setAttribute('role', 'menu');
  appendResponseContextMenuButton(menu, 'Raporla', () => reportOperationMessage(conversationId, messageId), {tone: 'warn'});
  if (hasCopyableText(messageText)) {
    appendResponseContextMenuButton(menu, 'Kopyala', () => copyOperationMessage(conversationId, messageId, bubble));
    appendResponseContextMenuButton(menu, "SSS'e Ekle", () => openOperationFaqDialog(conversationId, messageId));
  }
  document.body.appendChild(menu);
  const left = Math.min(anchorRect.left || 0, window.innerWidth - menu.offsetWidth - 12);
  const top = Math.min((anchorRect.top || 0) + (anchorRect.height || 0) + 4, window.innerHeight - menu.offsetHeight - 12);
  menu.style.left = `${Math.max(12, left)}px`;
  menu.style.top = `${Math.max(12, top)}px`;
  state.responseContextMenu = menu;
  menu.querySelector('button')?.focus();
}

function appendResponseContextMenuButton(menu, label, handler, options = {}) {
  const button = document.createElement('button');
  button.type = 'button';
  button.setAttribute('role', 'menuitem');
  button.textContent = label;
  if (options.tone === 'warn') button.classList.add('is-warn');
  button.addEventListener('click', event => {
    event.preventDefault();
    event.stopPropagation();
    handler();
  });
  menu.appendChild(button);
  return button;
}

function closeResponseContextMenu() {
  if (state.responseContextMenu) {
    state.responseContextMenu.remove();
    state.responseContextMenu = null;
  }
}

function normalizeClipboardText(value) {
  return String(value ?? '').replace(/\\r\\n?/g, '\\n');
}

function hasCopyableText(value) {
  return normalizeClipboardText(value).replace(/\\s/g, '').length > 0;
}

function clipboardHtmlForText(text) {
  return `<pre style="margin:0;white-space:pre-wrap;font-family:Cascadia Code,Fira Code,Consolas,monospace;font-size:13px;line-height:1.5">${escapeHtml(normalizeClipboardText(text))}</pre>`;
}

async function writeOperationClipboardText(text) {
  const normalized = normalizeClipboardText(text);
  if (typeof navigator === 'undefined' || !navigator.clipboard) {
    throw new Error('clipboard_unavailable');
  }
  if (typeof ClipboardItem !== 'undefined' && typeof Blob !== 'undefined' && typeof navigator.clipboard.write === 'function') {
    try {
      await navigator.clipboard.write([new ClipboardItem({
        'text/plain': new Blob([normalized], {type: 'text/plain'}),
        'text/html': new Blob([clipboardHtmlForText(normalized)], {type: 'text/html'}),
      })]);
      return;
    } catch (_error) {
      // Some browser permission models only allow writeText; fall through to that safer path.
    }
  }
  await navigator.clipboard.writeText(normalized);
}

function getOperationMessages() {
  return Array.isArray(state.conversationDetail?.messages) ? state.conversationDetail.messages : [];
}

function findOperationMessage(conversationId, messageId) {
  const activeConversationId = String(state.conversationDetail?.conversation?.id || '');
  if (String(conversationId || '') && activeConversationId && String(conversationId) !== activeConversationId) return null;
  return getOperationMessages().find(message => String(message.id || '') === String(messageId || '')) || null;
}

function getOperationMessageText(conversationId, messageId, bubble = null) {
  const message = findOperationMessage(conversationId, messageId);
  const fallbackText = bubble?.querySelector?.('.chat-bubble-content')?.textContent || '';
  return normalizeClipboardText(message?.content || fallbackText).trim();
}

async function copyOperationMessage(conversationId, messageId, bubble = null) {
  const text = getOperationMessageText(conversationId, messageId, bubble);
  closeResponseContextMenu();
  if (!hasCopyableText(text)) {
    notify('Kopyalanacak yanıt yok.', 'warn');
    return;
  }
  try {
    await writeOperationClipboardText(text);
    notify('Yanıt panoya kopyalandı.', 'success');
  } catch (_error) {
    notify('Tarayıcı kopyalama izni vermedi.', 'warn');
  }
}

function extractOperationFaqPair(conversationId, messageId) {
  const messages = getOperationMessages();
  const index = messages.findIndex(message => String(message.id || '') === String(messageId || ''));
  const target = index >= 0 ? messages[index] : findOperationMessage(conversationId, messageId);
  const role = String(target?.role || '').toLowerCase();
  const selectedText = normalizeClipboardText(target?.content || '').trim();
  let question = '';
  let answer = '';
  if (role === 'user') {
    question = selectedText;
    const nextAnswer = messages.slice(index + 1).find(message => ['assistant','operator','system'].includes(String(message.role || '').toLowerCase()));
    answer = normalizeClipboardText(nextAnswer?.content || '').trim();
  } else {
    answer = selectedText;
    const previousQuestion = messages.slice(0, Math.max(0, index)).reverse().find(message => String(message.role || '').toLowerCase() === 'user');
    question = normalizeClipboardText(previousQuestion?.content || '').trim();
  }
  const conversation = state.conversationDetail?.conversation || {};
  const topic = formatIntentLabel(resolveConversationIntent(conversation, messages)) || 'Operasyon yanıtı';
  return {question, answer, topic};
}

function closeOperationFaqDialog() {
  state.operationFaqMessage = null;
  refs.operationFaqDialog?.close?.();
}

function setOperationFaqField(refName, value) {
  if (refs[refName]) refs[refName].value = value || '';
}

function openOperationFaqDialog(conversationId, messageId) {
  closeResponseContextMenu();
  const pair = extractOperationFaqPair(conversationId, messageId);
  if (!refs.operationFaqDialog) {
    notify('SSS penceresi yüklenemedi.', 'error');
    return;
  }
  state.operationFaqMessage = {conversationId: String(conversationId || ''), messageId: String(messageId || '')};
  setOperationFaqField('operationFaqTopic', pair.topic);
  setOperationFaqField('operationFaqQuestionTr', pair.question);
  setOperationFaqField('operationFaqAnswerTr', pair.answer);
  setOperationFaqField('operationFaqQuestionEn', pair.question);
  setOperationFaqField('operationFaqAnswerEn', pair.answer);
  setOperationFaqField('operationFaqStatus', 'ACTIVE');
  if (refs.operationFaqDialogResult) {
    refs.operationFaqDialogResult.hidden = true;
    refs.operationFaqDialogResult.textContent = '';
  }
  refs.operationFaqDialog.showModal();
}

function resolveOperationFaqHotelId() {
  const conversationHotelId = state.conversationDetail?.conversation?.hotel_id;
  return String(state.selectedHotelId || conversationHotelId || state.me?.hotel_id || '');
}

async function submitOperationFaqDialog(event) {
  event.preventDefault();
  const hotelId = resolveOperationFaqHotelId();
  if (!hotelId) {
    notify('SSS eklemek için önce otel seçin.', 'warn');
    return;
  }
  const topic = String(refs.operationFaqTopic?.value || '').trim();
  const questionTr = String(refs.operationFaqQuestionTr?.value || '').trim();
  const answerTr = String(refs.operationFaqAnswerTr?.value || '').trim();
  const questionEn = String(refs.operationFaqQuestionEn?.value || '').trim();
  const answerEn = String(refs.operationFaqAnswerEn?.value || '').trim();
  const status = String(refs.operationFaqStatus?.value || 'ACTIVE').trim();
  if (!topic) { notify('Konu alanı zorunludur.', 'warn'); return; }
  if (!answerTr) { notify('Cevap (TR) alanı zorunludur.', 'warn'); return; }
  if (!answerEn) { notify('Cevap (EN) alanı zorunludur.', 'warn'); return; }

  const submitButton = refs.operationFaqDialogForm?.querySelector('button[type="submit"]');
  const originalLabel = submitButton?.textContent || 'SSS Kaydet';
  if (submitButton) {
    submitButton.disabled = true;
    submitButton.textContent = 'Kaydediliyor...';
  }
  try {
    const payload = {topic, question_tr: questionTr, answer_tr: answerTr, question_en: questionEn, answer_en: answerEn, status};
    await apiFetch(`/hotels/${encodeURIComponent(hotelId)}/faq`, {method: 'POST', body: payload});
    notify('SSS kaydı oluşturuldu.', 'success');
    refs.operationFaqDialog?.close?.();
    state.operationFaqMessage = null;
    if (state.currentView === 'faq') await loadFaqs();
  } catch (error) {
    notify(error.message || 'SSS kaydı oluşturulamadı.', 'error');
    if (refs.operationFaqDialogResult) {
      refs.operationFaqDialogResult.hidden = false;
      refs.operationFaqDialogResult.textContent = error.message || 'SSS kaydı oluşturulamadı.';
    }
  } finally {
    if (submitButton) {
      submitButton.disabled = false;
      submitButton.textContent = originalLabel;
    }
  }
}

async function reportOperationMessage(conversationId, messageId) {
  closeResponseContextMenu();
  try {
    const body = {
      conversation_id: String(conversationId || ''),
      message_id: String(messageId || ''),
      reason: 'Operasyon masasından raporlandı.',
      error_type: 'not_classified',
    };
    if (state.me?.role === 'ADMIN' && state.selectedHotelId) body.hotel_id = Number(state.selectedHotelId);
    const review = await apiFetch('/response-reviews', {
      method: 'POST',
      body,
    });
    notify('Yanıt inceleme kuyruğuna alındı.', 'success');
    const reviewId = encodeURIComponent(review.id || '');
    window.location.href = `/admin/response-review?review_id=${reviewId}`;
  } catch (error) {
    notify(error.message || 'Yanıt raporlanamadı.', 'error');
  }
}

function findLatestPendingAssistantMessage(messages) {
  return [...(messages || [])].reverse().find(message => {
    if (message.role !== 'assistant') return false;
    const internal = asObject(message.internal_json);
    return Boolean(internal.send_blocked || internal.approval_pending);
  }) || null;
}

function renderAiDraftBox(conversation, message) {
  return `
    <div class="ai-draft-box">
      <strong>AI taslağı onay bekliyor</strong>
      <p>${escapeHtml(truncateText(message.content || '', 220))}</p>
      <div class="module-actions mt-sm">
        <button class="action-button primary action-button-sm" data-approve-conversation="${escapeHtml(String(conversation.id))}" data-approve-message="${escapeHtml(String(message.id))}">Onayla ve Gönder</button>
        <button class="action-button secondary action-button-sm" data-scroll-composer="true">Düzenle</button>
      </div>
    </div>
  `;
}

function renderDecisionPanel(conversation, messages) {
  if (!refs.conversationDecisionPanel) return;
  if (!conversation) {
    refs.conversationDecisionPanel.innerHTML = `
      <div class="module-header compact"><div><h3>Karar Desteği</h3><p>Konuşma seçilince aksiyon önerisi burada görünür.</p></div></div>
      <div class="conversation-side-empty"><strong>Konuşma seçimi bekleniyor</strong><p>Misafir özeti, AI’nin anladığı konu, risk ve hızlı aksiyonlar burada toplanır.</p></div>
    `;
    return;
  }
  const latestAssistant = [...(messages || [])].reverse().find(message => message.role === 'assistant');
  const latestUser = [...(messages || [])].reverse().find(message => message.role === 'user');
  const assistantInternal = asObject(latestAssistant?.internal_json);
  const pendingMessage = findLatestPendingAssistantMessage(messages || []);
  const risks = conversation.risk_flags || assistantInternal.risk_flags || [];
  refs.conversationDecisionPanel.innerHTML = `
    <div class="module-header compact">
      <div><h3>Karar Desteği</h3><p>Şimdi ne yapılmalı?</p></div>
    </div>
    <section class="decision-section">
      <h4>Misafir Özeti</h4>
      <div class="decision-row"><span>Misafir</span><strong>${escapeHtml(conversation.phone_display || 'Maskeli misafir')}</strong></div>
      <div class="decision-row"><span>Ne istiyor?</span><strong>${escapeHtml(formatIntentLabel(resolveConversationIntent(conversation, messages || [])))}</strong></div>
      <div class="decision-row"><span>Durum</span><strong>${escapeHtml(resolveConversationState(conversation, messages || []))}</strong></div>
      <div class="decision-row"><span>Son mesaj</span><strong>${escapeHtml(truncateText(latestUser?.content || 'Yok', 72))}</strong></div>
    </section>
    <section class="decision-section">
      <h4>AI Ne Yaptı?</h4>
      <div class="decision-row"><span>Taslak</span><strong>${escapeHtml(pendingMessage ? 'Onay bekliyor' : latestAssistant ? 'Yanıt oluşturdu' : 'Henüz yok')}</strong></div>
      <div class="decision-row"><span>Kaynak</span><strong>${escapeHtml(resolveAssistantSource(assistantInternal))}</strong></div>
      <div class="decision-row"><span>Eksik bilgi</span><strong>${escapeHtml(resolveMissingInfo(assistantInternal))}</strong></div>
      <div class="decision-row"><span>İnsan devri</span><strong>${escapeHtml(conversation.human_override ? 'Aktif' : 'Gerekmiyor')}</strong></div>
    </section>
    <section class="decision-section">
      <h4>Risk</h4>
      <div class="risk-list">
        ${Array.isArray(risks) && risks.length ? risks.map(risk => `<span class="risk-chip">${escapeHtml(risk)}</span>`).join('') : '<span class="risk-chip is-safe">Risk yok</span>'}
      </div>
    </section>
    <section class="decision-section">
      <h4>Hızlı Aksiyonlar</h4>
      <div class="quick-actions">
        <button class="action-button primary" ${pendingMessage ? '' : 'disabled'} data-approve-conversation="${escapeHtml(String(conversation.id))}" data-approve-message="${escapeHtml(String(pendingMessage?.id || ''))}">Onayla ve Gönder</button>
        <button class="action-button secondary" data-scroll-composer="true">Düzenle</button>
        <button class="action-button secondary" type="button" disabled>Reddet</button>
        <button class="action-button secondary" data-scroll-composer="true">Misafire Sor</button>
        <button class="action-button warn" data-toggle-human-override="${escapeHtml(String(conversation.id))}" data-current-override="${conversation.human_override ? 'true' : 'false'}">${conversation.human_override ? 'AI Moduna Al' : 'İnsan Devrine Al'}</button>
        <button class="action-button danger" data-reset-conversation="${escapeHtml(String(conversation.id))}">Sıfırla</button>
      </div>
    </section>
  `;
}

function resolveAssistantSource(internal) {
  const source = internal.source || internal.source_name || internal.knowledge_source || internal.tool_name;
  if (source) return String(source);
  const toolCalls = Array.isArray(internal.tool_calls) ? internal.tool_calls : [];
  if (toolCalls.length) return 'Araç sonucu';
  return 'Kaynak bilgisi yok';
}

function resolveMissingInfo(internal) {
  const missing = internal.missing_fields || internal.missing_info || internal.required_fields_missing;
  if (Array.isArray(missing) && missing.length) return missing.join(', ');
  if (typeof missing === 'string' && missing.trim()) return missing;
  return 'Yok';
}

function truncateText(value, maxLength) {
  const text = String(value || '').replace(/\\s+/g, ' ').trim();
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength - 1)}…`;
}

// Hold functions moved to admin_panel_holds_assets.py

async function onDecisionSubmit(event) {
  event.preventDefault();
  const holdId = refs.decisionHoldId.value;
  const reason = refs.decisionReason.value.trim();
  try {
    if (!String(holdId || '').startsWith('R_HOLD_') && !reason) {
      notify('Reddetme gerekçesi zorunludur.', 'warn');
      return;
    }
    if (String(holdId || '').startsWith('R_HOLD_')) {
      const restaurantHold = (state.restaurantHolds || []).find(item => String(item.hold_id) === String(holdId));
      if (String(restaurantHold?.status || '').toUpperCase() === 'PENDING_APPROVAL') {
        await apiFetch(`/holds/${encodeURIComponent(holdId)}/reject`, {method: 'POST', body: {reason: reason || 'Admin reddi'}});
      } else {
        await apiFetch(`/holds/restaurant/${encodeURIComponent(holdId)}/status`, {method: 'PUT', body: {status: 'IPTAL', reason: reason || null}});
      }
    } else {
      await apiFetch(`/holds/${holdId}/reject`, {method: 'POST', body: {reason}});
    }
    refs.decisionDialog.close();
    notify('Hold reddedildi.', 'success');
    const tab = state.activeHoldsTab || 'stay';
    if (tab === 'stay') loadStayHolds();
    else if (tab === 'restaurant') loadRestaurantHolds();
    else loadTransferHolds();
    loadDashboard();
  } catch (error) {
    notify(error.message, 'error');
  }
}

async function loadAccessControl() {
  if (!hasPermission('access_control:read')) {
    renderAccessControlUnavailable('Bu bölümü görüntüleme yetkiniz bulunmuyor.');
    return;
  }
  const [catalogResponse, usersResponse] = await Promise.all([
    state.accessControlCatalog ? Promise.resolve(state.accessControlCatalog) : apiFetch('/access-control/catalog'),
    apiFetch('/users'),
  ]);
  state.accessControlCatalog = catalogResponse;
  state.accessControlUsers = Array.isArray(usersResponse.items) ? usersResponse.items : [];
  state.accessControlUserDrafts = {};
  ensureAccessControlSelection();
  const previewRole = getAccessRoleByCode(state.accessControlPreviewRole);
  const selectedUser = getAccessSelectedUser();
  if (previewRole) {
    state.accessControlDraftPermissions = buildAccessRoleDefaultSet(previewRole.code);
  } else if (selectedUser) {
    state.accessControlDraftPermissions = new Set(selectedUser.permissions || []);
  }
  renderAccessControl();
}

function ensureAccessControlSelection() {
  const roles = state.accessControlCatalog?.roles || [];
  if (!roles.length) {
    state.accessControlSelectedRole = '';
    state.accessControlSelectedUserId = 0;
    state.accessControlPreviewRole = '';
    state.accessControlDraftPermissions = new Set();
    return;
  }
  if (!roles.some(item => String(item.code) === String(state.accessControlSelectedRole))) {
    state.accessControlSelectedRole = String(roles[0].code);
  }
  if (
    state.accessControlPreviewRole &&
    !roles.some(item => String(item.code) === String(state.accessControlPreviewRole))
  ) {
    state.accessControlPreviewRole = '';
  }
  if (
    state.accessControlSelectedUserId &&
    !state.accessControlUsers.some(item => Number(item.user_id) === Number(state.accessControlSelectedUserId))
  ) {
    state.accessControlSelectedUserId = 0;
    state.accessControlDraftPermissions = new Set();
  }
  if (!state.accessControlSelectedUserId) {
    const editableUser = state.accessControlUsers.find(
      item => Number(item.user_id) !== Number(state.me?.user_id || 0),
    );
    state.accessControlSelectedUserId = Number(
      editableUser?.user_id || state.accessControlUsers[0]?.user_id || 0,
    );
  }
}

function renderAccessControlUnavailable(message) {
  refs.accessOverviewCards.innerHTML = '';
  refs.accessRoleSummary.innerHTML = `<div class="helper-box"><strong>Erişim kapalı</strong><p>${escapeHtml(message)}</p></div>`;
  refs.accessRoleCards.innerHTML = '';
  refs.accessUsersList.innerHTML = `<div class="access-editor-empty"><h4>Erişim yok</h4><p>${escapeHtml(message)}</p></div>`;
  refs.accessPermissionMeta.innerHTML = `<div class="helper-box"><strong>İzin düzenleyici</strong><p>${escapeHtml(message)}</p></div>`;
  refs.accessPermissionTree.innerHTML = '';
}

function renderAccessControl() {
  renderAccessOverviewCards();
  renderAccessRoleSummary();
  renderAccessRoleCards();
  renderAccessCreateOptions();
  renderAccessUsersList();
  renderAccessPermissionEditor();
  syncAccessCreateFormState();
}

function renderAccessOverviewCards() {
  const roles = state.accessControlCatalog?.roles || [];
  const departments = state.accessControlCatalog?.departments || [];
  const users = state.accessControlUsers || [];
  const totpReadyCount = users.filter(item => item.totp_enrolled).length;
  refs.accessOverviewCards.innerHTML = [
    {
      title: 'Yetki Şablonları',
      value: roles.length,
      note: `${departments.length} otel birimi ile eşleştirilmiş rol kataloğu`,
    },
    {
      title: 'Yönetici Kullanıcıları',
      value: users.length,
      note: `${users.filter(item => item.is_active).length} aktif hesap şu anda panele erişebilir`,
    },
    {
      title: '2FA Hazır',
      value: totpReadyCount,
      note: `${Math.max(users.length - totpReadyCount, 0)} hesap için yeni Authenticator uygulaması kurulumu gerekebilir`,
    },
  ].map(item => `
    <article class="overview-card access-overview-card">
      <h4>${escapeHtml(item.title)}</h4>
      <strong>${escapeHtml(item.value)}</strong>
      <span>${escapeHtml(item.note)}</span>
    </article>
  `).join('');
}

function renderAccessRoleSummary() {
  const role = getAccessRoleByCode(state.accessControlSelectedRole);
  if (!role) {
    refs.accessRoleSummary.innerHTML = '<div class="helper-box"><strong>Rol seçilmedi</strong><p>Soldaki kartlardan bir rol seçin.</p></div>';
    return;
  }
  const department = getAccessDepartmentByCode(role.default_department_code);
  const assignedUserCount = state.accessControlUsers.filter(item => item.role === role.code).length;
  refs.accessRoleSummary.innerHTML = `
    <div class="helper-box">
      <strong>${escapeHtml(role.label)}</strong>
      <p>${escapeHtml(role.description || 'Bu rol için açıklama bulunmuyor.')}</p>
      <div class="access-summary-row">
        <span class="access-chip role">${escapeHtml((role.default_permissions || []).length)} varsayılan izin</span>
        <span class="access-chip department">${escapeHtml(department?.label || role.default_department_code || '-')}</span>
        <span class="access-chip security">${escapeHtml(assignedUserCount)} kullanıcı bu rolde</span>
      </div>
    </div>
  `;
}

function renderAccessRoleCards() {
  const roles = state.accessControlCatalog?.roles || [];
  refs.accessRoleCards.innerHTML = roles.map(role => {
    const department = getAccessDepartmentByCode(role.default_department_code);
    const assignedUserCount = state.accessControlUsers.filter(item => item.role === role.code).length;
    return `
      <button
        class="access-role-card ${String(role.code) === String(state.accessControlSelectedRole) ? 'is-active' : ''}"
        type="button"
        data-access-role="${escapeHtml(role.code)}"
        aria-label="${escapeHtml(role.label)} rolünü görüntüle"
      >
        <header>
          <div>
            <h4>${escapeHtml(role.label)}</h4>
            <p>${escapeHtml(role.description || '')}</p>
          </div>
          <span class="pill info">${escapeHtml(assignedUserCount)} kullanıcı</span>
        </header>
        <div class="access-chip-row">
          <span class="access-chip role">${escapeHtml((role.default_permissions || []).length)} izin</span>
          <span class="access-chip department">${escapeHtml(department?.label || role.default_department_code || '-')}</span>
        </div>
      </button>
    `;
  }).join('');
}

function renderAccessCreateOptions() {
  const roles = state.accessControlCatalog?.roles || [];
  const departments = state.accessControlCatalog?.departments || [];
  const currentRole = refs.accessCreateRole?.value || state.accessControlSelectedRole || String(roles[0]?.code || '');
  refs.accessCreateRole.innerHTML = roles.map(role => `
    <option value="${escapeHtml(role.code)}">${escapeHtml(role.label)}</option>
  `).join('');
  if (roles.some(item => String(item.code) === String(currentRole))) {
    refs.accessCreateRole.value = currentRole;
  }
  const fallbackDepartment = getAccessRoleByCode(refs.accessCreateRole.value)?.default_department_code || String(departments[0]?.code || '');
  const currentDepartment = refs.accessCreateDepartment?.value || fallbackDepartment;
  refs.accessCreateDepartment.innerHTML = departments.map(item => `
    <option value="${escapeHtml(item.code)}">${escapeHtml(item.label)}</option>
  `).join('');
  if (departments.some(item => String(item.code) === String(currentDepartment))) {
    refs.accessCreateDepartment.value = currentDepartment;
  } else if (fallbackDepartment) {
    refs.accessCreateDepartment.value = fallbackDepartment;
  }
}

function syncAccessCreateFormState() {
  const canWrite = hasPermission('access_control:write');
  refs.accessCreateUserForm?.querySelectorAll('input, select, button').forEach(element => {
    if (element.id === 'accessCreateTwoFactor') {
      element.disabled = true;
      return;
    }
    element.disabled = !canWrite;
  });
}

function renderAccessUsersList() {
  const users = state.accessControlUsers || [];
  const hasWritePermission = hasPermission('access_control:write');
  if (!users.length) {
    refs.accessUsersList.innerHTML = '<div class="access-editor-empty"><h4>Kayıtlı kullanıcı yok</h4><p>Bu otel kapsamında henüz ek yönetim kullanıcısı bulunmuyor.</p></div>';
    return;
  }
  refs.accessUsersList.innerHTML = users.map(user => {
    const isSelf = Number(user.user_id) === Number(state.me?.user_id || 0);
    const selected = !state.accessControlPreviewRole && Number(user.user_id) === Number(state.accessControlSelectedUserId || 0);
    const draft = getAccessUserDraft(user.user_id);
    const draftRole = draft.role || user.role;
    const draftDepartment = draft.department_code || user.department_code;
    const draftIsActive = typeof draft.is_active === 'boolean' ? draft.is_active : user.is_active;
    const draftDisplayName = Object.prototype.hasOwnProperty.call(draft, 'display_name') ? draft.display_name : (user.display_name || '');
    const draftDepartmentLabel = getAccessDepartmentByCode(draftDepartment)?.label || user.department_label || draftDepartment || '-';
    const draftRoleLabel = getAccessRoleByCode(draftRole)?.label || user.role_label || draftRole;
    const overrideCount = Object.keys(user.permission_overrides || {}).length;
    const canEditRole = hasWritePermission && !isSelf && !user.is_super_admin;
    const activeLockedReason = !hasWritePermission
      ? 'Aktiflik durumunu değiştirme yetkiniz bulunmuyor.'
      : isSelf
        ? 'Giriş yaptığınız hesabı aynı oturumdan pasife alamazsınız.'
        : user.is_super_admin
          ? 'Korunan süper yönetici hesabı pasife alınamaz.'
          : '';
    const twoFactorLockedReason = 'Zorunlu 2FA güvenlik politikası gereği kapatılamaz; gerekiyorsa 2FA QR yenileme butonunu kullanın.';
    const roleHelpText = isSelf
      ? 'Giriş yaptığınız hesabın rolü güvenlik nedeniyle bu karttan değiştirilemez. Rol değişikliği için başka bir yönetici hesabı ile bu kullanıcıyı düzenleyin.'
      : user.is_super_admin
        ? 'Korunan süper yönetici hesabının rolü düşürülemez; tüm izinleri açık kalır.'
        : hasWritePermission
        ? 'Rol, hangi pencere ve işlem ailelerine erişileceğini belirler.'
        : 'Rol değiştirme yetkiniz bulunmuyor.';
    const departmentHelpText = isSelf
      ? 'Bu hesapta departman bilgisi güncellenebilir; ancak rol, aktiflik ve izin kümesi kilitli tutulur.'
      : 'Departman, kullanıcının oteldeki organizasyon konumunu tanımlar.';
    return `
      <article class="access-user-card ${selected ? 'is-selected' : ''} ${isSelf ? 'is-self-locked' : ''}">
        <header>
          <div>
            <h4>${escapeHtml(user.display_name || user.username)}</h4>
            <p>${escapeHtml(user.username)} hesabının rol, departman, aktiflik ve güvenlik akışlarını bu karttan yönetin.</p>
            <div class="access-user-badges">
              <span class="access-chip role">${escapeHtml(draftRoleLabel)}</span>
              <span class="access-chip department">${escapeHtml(draftDepartmentLabel)}</span>
              <span class="access-chip security">${escapeHtml((user.permissions || []).length)} etkin izin</span>
              <span class="access-chip">${escapeHtml(overrideCount)} özel izin farkı</span>
              ${isSelf ? '<span class="access-chip self">Giriş yaptığınız hesap</span>' : ''}
            </div>
          </div>
          <div class="stack">
            <span class="pill ${draftIsActive ? 'success' : 'closed'}">${escapeHtml(draftIsActive ? 'Aktif' : 'Pasif')}</span>
            <span class="pill ${user.totp_enrolled ? 'info' : 'warn'}">${escapeHtml(user.totp_enrolled ? '2FA kayıtlı' : '2FA kurulacak')}</span>
          </div>
        </header>
        <div class="access-user-controls">
          <div class="field">
            <label for="accessDisplayName-${escapeHtml(user.user_id)}">Görünen ad</label>
            <input id="accessDisplayName-${escapeHtml(user.user_id)}" data-user-display="${escapeHtml(user.user_id)}" maxlength="100" value="${escapeHtml(draftDisplayName || '')}" ${!hasWritePermission ? 'disabled' : ''}>
          </div>
          <div class="field">
            <label for="accessPassword-${escapeHtml(user.user_id)}">Yeni geçici şifre</label>
            <input id="accessPassword-${escapeHtml(user.user_id)}" data-user-password="${escapeHtml(user.user_id)}" type="password" minlength="12" maxlength="72" placeholder="Boş bırakırsanız değişmez" ${!hasWritePermission ? 'disabled' : ''}>
          </div>
          <div class="field access-field-role">
            <label for="accessRole-${escapeHtml(user.user_id)}">Rol (Yetki şablonu)</label>
            <select id="accessRole-${escapeHtml(user.user_id)}" data-user-role="${escapeHtml(user.user_id)}" ${canEditRole ? '' : 'disabled'}>
              ${renderAccessRoleOptions(draftRole)}
            </select>
            <small>${escapeHtml(roleHelpText)}</small>
          </div>
          <div class="field access-field-department">
            <label for="accessDepartment-${escapeHtml(user.user_id)}">Departman (Otel birimi)</label>
            <select id="accessDepartment-${escapeHtml(user.user_id)}" data-user-department="${escapeHtml(user.user_id)}" ${!hasWritePermission ? 'disabled' : ''}>
              ${renderAccessDepartmentOptions(draftDepartment)}
            </select>
            <small>${escapeHtml(departmentHelpText)}</small>
          </div>
          <div class="field full access-toggle-grid">
            <label class="toggle-row ${activeLockedReason ? 'access-toggle-locked' : ''}" for="accessActive-${escapeHtml(user.user_id)}" ${activeLockedReason ? `data-access-locked-toggle="${escapeHtml(activeLockedReason)}"` : ''}>
              <span class="toggle-copy">
                <strong>Hesap aktif</strong>
                <small>Pasif kullanıcı giriş yapamaz.</small>
              </span>
              <span class="switch">
                <input id="accessActive-${escapeHtml(user.user_id)}" data-user-active="${escapeHtml(user.user_id)}" type="checkbox" ${draftIsActive ? 'checked' : ''} ${activeLockedReason ? 'disabled' : ''}>
                <span class="switch-track"><span class="switch-thumb"></span></span>
              </span>
            </label>
            <label class="toggle-row access-toggle-locked" for="accessTwoFactor-${escapeHtml(user.user_id)}" data-access-locked-toggle="${escapeHtml(twoFactorLockedReason)}">
              <span class="toggle-copy">
                <strong>Zorunlu 2FA</strong>
                <small>Politika gereği açık tutulur; gerekirse QR yenilenir.</small>
              </span>
              <span class="switch">
                <input id="accessTwoFactor-${escapeHtml(user.user_id)}" type="checkbox" checked disabled>
                <span class="switch-track"><span class="switch-thumb"></span></span>
              </span>
            </label>
          </div>
          ${isSelf ? '<div class="field full"><div class="access-user-note">Bu kayıt şu an giriş yaptığınız yönetici hesabı. Güvenlik nedeniyle kendi rolünüzü, aktiflik durumunuzu ve izin kümenizi bu akıştan değiştiremezsiniz. Gerekirse departman, görünen ad veya şifreyi güncelleyin; rol değişikliği için önce ikinci bir yönetici hesabı oluşturup bu kullanıcıyı onunla düzenleyin.</div></div>' : ''}
        </div>
        <div class="access-user-actions">
          <button class="action-button secondary ${selected ? 'is-active' : ''}" type="button" data-access-edit-permissions="${escapeHtml(user.user_id)}">${isSelf ? 'İzinleri Görüntüle' : 'İzinleri Düzenle'}</button>
          <button class="action-button primary" type="button" data-access-save-user="${escapeHtml(user.user_id)}" ${!hasWritePermission ? 'disabled' : ''}>Değişiklikleri Kaydet</button>
          <button class="action-button warn" type="button" data-access-rotate-totp="${escapeHtml(user.user_id)}" ${!hasWritePermission ? 'disabled' : ''}>2FA QR Yenile</button>
        </div>
      </article>
    `;
  }).join('');
}

function renderAccessPermissionEditor() {
  const previewRole = getAccessRoleByCode(state.accessControlPreviewRole);
  if (previewRole) {
    const rolePermissions = buildAccessRoleDefaultSet(previewRole.code);
    const department = getAccessDepartmentByCode(previewRole.default_department_code);
    state.accessControlDraftPermissions = rolePermissions;
    refs.accessResetPermissionsButton.disabled = true;
    refs.accessSavePermissionsButton.disabled = true;
    refs.accessPermissionMeta.innerHTML = `
      <div class="helper-box">
        <strong>${escapeHtml(previewRole.label)} rol şablonu</strong>
        <p>${escapeHtml(previewRole.description || 'Bu rol için açıklama bulunmuyor.')} Bu görünüm rolün varsayılan izinlerini gösterir; kullanıcıya uygulamak için kullanıcı kartındaki rol alanını seçip değişiklikleri kaydedin.</p>
        <div class="access-summary-row">
          <span class="access-chip role">${escapeHtml(rolePermissions.size)} varsayılan izin</span>
          <span class="access-chip department">${escapeHtml(department?.label || previewRole.default_department_code || '-')}</span>
          <span class="access-chip security">Önizleme modu</span>
        </div>
      </div>
      <div class="helper-box"><strong>Rol önizlemesi</strong><p>Rol şablonları katalogtan gelir; bu ekranda doğrudan düzenlenmez. Değişiklik için ilgili kullanıcıya rol atayın veya kullanıcı bazlı izinleri kullanıcı kartından açın.</p></div>
    `;
    refs.accessPermissionTree.innerHTML = renderAccessPermissionGroups(rolePermissions, rolePermissions, false);
    return;
  }
  const user = getAccessSelectedUser();
  if (!user) {
    refs.accessResetPermissionsButton.disabled = true;
    refs.accessSavePermissionsButton.disabled = true;
    refs.accessPermissionMeta.innerHTML = '<div class="helper-box"><strong>Kullanıcı seçin</strong><p>İzin ağacını açmak için soldaki kartlardan bir kullanıcı seçin.</p></div>';
    refs.accessPermissionTree.innerHTML = '<div class="access-editor-empty"><h4>Henüz kullanıcı seçilmedi</h4><p>Bir kullanıcı seçtiğinizde pencere erişimleri ve işlem izinleri burada anahtar menüsü ile açılır.</p></div>';
    return;
  }
  if (!(state.accessControlDraftPermissions instanceof Set)) {
    state.accessControlDraftPermissions = new Set(user.permissions || []);
  }
  const isSelf = Number(user.user_id) === Number(state.me?.user_id || 0);
  const draft = getAccessUserDraft(user.user_id);
  const effectiveRole = draft.role || user.role;
  const effectiveDepartment = draft.department_code || user.department_code;
  const effectiveRoleLabel = getAccessRoleByCode(effectiveRole)?.label || user.role_label || effectiveRole;
  const effectiveDepartmentLabel = getAccessDepartmentByCode(effectiveDepartment)?.label || user.department_label || effectiveDepartment || '-';
  const roleDefaults = buildAccessRoleDefaultSet(effectiveRole);
  const hasWritePermission = hasPermission('access_control:write');
  const canWrite = hasWritePermission && !isSelf && !user.is_super_admin;
  const overrideCount = Object.keys(user.permission_overrides || {}).length;
  refs.accessResetPermissionsButton.disabled = !canWrite;
  refs.accessSavePermissionsButton.disabled = !canWrite;
  const lockMessage = isSelf
    ? 'Bu kayıt şu an giriş yaptığınız yönetici hesabı. Güvenlik nedeniyle kendi rolünüz, aktifliğiniz ve izin kümeniz bu ekrandan değiştirilemez. Başka bir yönetici hesabı oluşturup bu kullanıcıyı onunla düzenleyin.'
    : user.is_super_admin
      ? 'Korunan süper yönetici hesabının izin kümesi azaltılamaz; tüm izinleri açık kalır.'
    : !hasWritePermission
      ? 'Bu kullanıcı için izin değişikliği yapma yetkiniz bulunmuyor.'
      : '';
  refs.accessPermissionMeta.innerHTML = `
      <div class="helper-box">
        <strong>${escapeHtml(user.display_name || user.username)}</strong>
        <p>${escapeHtml(effectiveRoleLabel)} rolündeki kullanıcının etkin izinleri düzenleniyor. Kaydedilen farklar rol varsayılanının üzerine kullanıcı bazlı özel izin farkı olarak işlenir.</p>
        <div class="access-summary-row">
        <span class="access-chip role">${escapeHtml(effectiveRoleLabel)}</span>
        <span class="access-chip department">${escapeHtml(effectiveDepartmentLabel)}</span>
        <span class="access-chip security">${escapeHtml(state.accessControlDraftPermissions.size)} seçili izin</span>
        <span class="access-chip">${escapeHtml(overrideCount)} kayıtlı özel izin farkı</span>
      </div>
    </div>
    ${!canWrite ? `<div class="helper-box"><strong>Değişiklik kilitli</strong><p>${escapeHtml(lockMessage)}</p></div>` : ''}
  `;
  refs.accessPermissionTree.innerHTML = renderAccessPermissionGroups(
    state.accessControlDraftPermissions,
    roleDefaults,
    canWrite,
  );
}

function renderAccessPermissionGroups(permissionSet, roleDefaults, canWrite) {
  return (state.accessControlCatalog?.permission_groups || []).map(group => {
    const items = Array.isArray(group.items) ? group.items : [];
    const activeCount = items.filter(item => permissionSet.has(item.key)).length;
    return `
      <section class="access-permission-group" aria-labelledby="permission-group-${escapeHtml(group.group)}">
        <div class="access-permission-head">
          <div>
            <h4 id="permission-group-${escapeHtml(group.group)}">${escapeHtml(group.group_label || group.group)}</h4>
            <p>${escapeHtml(activeCount)} / ${escapeHtml(items.length)} izin seçili</p>
          </div>
          <div class="access-permission-stats">
            <span class="pill info">${escapeHtml(items.length)} anahtar</span>
            <span class="pill ${activeCount === items.length ? 'success' : 'warn'}">${escapeHtml(activeCount)} aktif</span>
          </div>
        </div>
        ${items.map(item => {
          const enabled = permissionSet.has(item.key);
          const roleDefaultEnabled = roleDefaults.has(item.key);
          const flags = [];
          if (roleDefaultEnabled) {
            flags.push('<span class="access-permission-flag default">Rol varsayılanı</span>');
          }
          if (enabled !== roleDefaultEnabled) {
            flags.push(`<span class="access-permission-flag ${enabled ? 'override' : 'removed'}">${enabled ? 'Ek yetki' : 'Varsayılandan kaldırıldı'}</span>`);
          }
          if (item.is_sensitive) {
            flags.push('<span class="access-permission-flag removed">Kritik</span>');
          }
          return `
            <div class="access-permission-row">
              <div class="access-permission-copy">
                <strong>${escapeHtml(item.label || item.key)}</strong>
                <p>${escapeHtml(item.description || '')}</p>
                <code>${escapeHtml(item.key)}</code>
                <div class="access-permission-flags">${flags.join('')}</div>
              </div>
              <label class="switch" aria-label="${escapeHtml(item.label || item.key)} iznini aç veya kapat">
                <input type="checkbox" data-access-permission="${escapeHtml(item.key)}" ${enabled ? 'checked' : ''} ${canWrite ? '' : 'disabled'}>
                <span class="switch-track"><span class="switch-thumb"></span></span>
              </label>
            </div>
          `;
        }).join('')}
      </section>
    `;
  }).join('');
}

function renderAccessRoleOptions(selectedRole) {
  return (state.accessControlCatalog?.roles || []).map(role => `
    <option value="${escapeHtml(role.code)}" ${String(role.code) === String(selectedRole) ? 'selected' : ''}>${escapeHtml(role.label)}</option>
  `).join('');
}

function renderAccessDepartmentOptions(selectedDepartmentCode) {
  return (state.accessControlCatalog?.departments || []).map(item => `
    <option value="${escapeHtml(item.code)}" ${String(item.code) === String(selectedDepartmentCode) ? 'selected' : ''}>${escapeHtml(item.label)}</option>
  `).join('');
}

function getAccessRoleByCode(roleCode) {
  return (state.accessControlCatalog?.roles || []).find(item => String(item.code) === String(roleCode)) || null;
}

function getAccessDepartmentByCode(departmentCode) {
  return (state.accessControlCatalog?.departments || []).find(item => String(item.code) === String(departmentCode)) || null;
}

function getAccessUserById(userId) {
  return (state.accessControlUsers || []).find(item => Number(item.user_id) === Number(userId)) || null;
}

function getAccessUserDraft(userId) {
  return state.accessControlUserDrafts?.[String(userId)] || {};
}

function setAccessUserDraftValue(userId, key, value) {
  const userKey = String(userId || '');
  if (!userKey) {
    return;
  }
  state.accessControlUserDrafts = state.accessControlUserDrafts || {};
  state.accessControlUserDrafts[userKey] = {
    ...(state.accessControlUserDrafts[userKey] || {}),
    [key]: value,
  };
}

function getAccessSelectedUser() {
  return getAccessUserById(state.accessControlSelectedUserId);
}

function buildAccessRoleDefaultSet(roleCode) {
  return new Set(getAccessRoleByCode(roleCode)?.default_permissions || []);
}

function syncAccessCreateDepartment(roleCode) {
  const nextDepartmentCode = getAccessRoleByCode(roleCode)?.default_department_code;
  if (nextDepartmentCode && refs.accessCreateDepartment) {
    refs.accessCreateDepartment.value = nextDepartmentCode;
  }
}

function onAccessRoleCardClick(event) {
  const button = event.target.closest('[data-access-role]');
  if (!button) {
    return;
  }
  state.accessControlSelectedRole = String(button.dataset.accessRole || '');
  state.accessControlPreviewRole = state.accessControlSelectedRole;
  state.accessControlDraftPermissions = buildAccessRoleDefaultSet(state.accessControlSelectedRole);
  if (refs.accessCreateRole) {
    refs.accessCreateRole.value = state.accessControlSelectedRole;
    syncAccessCreateDepartment(state.accessControlSelectedRole);
  }
  renderAccessRoleSummary();
  renderAccessRoleCards();
  renderAccessUsersList();
  renderAccessPermissionEditor();
}

function onAccessCreateRoleChange() {
  state.accessControlSelectedRole = refs.accessCreateRole.value;
  state.accessControlPreviewRole = state.accessControlSelectedRole;
  state.accessControlDraftPermissions = buildAccessRoleDefaultSet(state.accessControlSelectedRole);
  syncAccessCreateDepartment(state.accessControlSelectedRole);
  renderAccessRoleSummary();
  renderAccessRoleCards();
  renderAccessUsersList();
  renderAccessPermissionEditor();
}

async function onAccessCreateUser(event) {
  event.preventDefault();
  if (!hasPermission('access_control:write')) {
    notify('Yeni kullanıcı oluşturma yetkiniz bulunmuyor.', 'warn');
    return;
  }
  const username = refs.accessCreateUsername.value.trim();
  const displayName = refs.accessCreateDisplayName.value.trim();
  const password = refs.accessCreatePassword.value;
  const passwordConfirm = refs.accessCreatePasswordConfirm.value;
  const roleCode = refs.accessCreateRole.value;
  const departmentCode = refs.accessCreateDepartment.value;
  if (!username || username.length < 3) {
    notify('Kullanıcı adı en az 3 karakter olmalıdır.', 'warn');
    return;
  }
  if (!password || password.length < 12) {
    notify('Geçici şifre en az 12 karakter olmalıdır.', 'warn');
    return;
  }
  if (new TextEncoder().encode(password).length > 72) {
    notify('Şifre en fazla 72 byte olabilir.', 'warn');
    return;
  }
  if (password !== passwordConfirm) {
    notify('Şifre tekrarı eşleşmiyor.', 'warn');
    return;
  }
  const role = getAccessRoleByCode(roleCode);
  const department = getAccessDepartmentByCode(departmentCode);
  if (!role || !department) {
    notify('Rol veya departman seçimi geçersiz.', 'warn');
    return;
  }
  try {
    const response = await apiFetch('/users', {
      method: 'POST',
      body: {
        username,
        display_name: displayName || null,
        password,
        role: role.code,
        department_code: department.code,
        permissions: Array.from(buildAccessRoleDefaultSet(role.code)).sort(),
        is_active: refs.accessCreateActive.checked,
      },
    });
    state.accessControlSelectedUserId = Number(response.user?.user_id || 0);
    state.accessControlPreviewRole = '';
    state.accessControlDraftPermissions = new Set(response.user?.permissions || []);
    refs.accessCreateUserForm.reset();
    refs.accessCreateActive.checked = true;
    refs.accessCreateTwoFactor.checked = true;
    refs.accessCreateRole.value = role.code;
    syncAccessCreateDepartment(role.code);
    showAccessTotpResult(response, 'Yeni kullanıcı için Authenticator uygulaması kurulumu');
    await loadAccessControl();
    notify(`${username} kullanıcısı oluşturuldu.`, 'success');
  } catch (error) {
    notify(error.message, 'error');
  }
}

function showAccessTotpResult(response, title) {
  if (!refs.accessTotpResult) {
    return;
  }
  if (!response?.otpauth_qr_svg_data_uri) {
    refs.accessTotpResult.hidden = true;
    return;
  }
  refs.accessTotpResult.hidden = false;
  refs.accessTotpResultTitle.textContent = title;
  refs.accessTotpResultUser.textContent = `${response.user?.username || '-'} hesabı için QR kodu aşağıdadır.`;
  refs.accessTotpQrImage.src = response.otpauth_qr_svg_data_uri;
  refs.accessTotpSecret.textContent = response.totp_secret || '-';
  refs.accessTotpUri.textContent = response.otpauth_uri || '-';
}

function onAccessUsersListClick(event) {
  const permissionsButton = event.target.closest('[data-access-edit-permissions]');
  if (permissionsButton) {
    const userId = Number(permissionsButton.dataset.accessEditPermissions || 0);
    const user = getAccessUserById(userId);
    if (!user) {
      return;
    }
    state.accessControlPreviewRole = '';
    state.accessControlSelectedUserId = userId;
    state.accessControlSelectedRole = String(user.role || state.accessControlSelectedRole);
    state.accessControlDraftPermissions = new Set(user.permissions || []);
    renderAccessRoleSummary();
    renderAccessRoleCards();
    renderAccessUsersList();
    renderAccessPermissionEditor();
    return;
  }
  const lockedToggle = event.target.closest('[data-access-locked-toggle]');
  if (lockedToggle) {
    notify(lockedToggle.dataset.accessLockedToggle || 'Bu ayar güvenlik nedeniyle kilitli.', 'warn');
    return;
  }
  const saveButton = event.target.closest('[data-access-save-user]');
  if (saveButton) {
    void saveAccessUser(Number(saveButton.dataset.accessSaveUser || 0));
    return;
  }
  const rotateButton = event.target.closest('[data-access-rotate-totp]');
  if (rotateButton) {
    void rotateAccessUserTotp(Number(rotateButton.dataset.accessRotateTotp || 0));
  }
}

function onAccessUsersListInput(event) {
  const displayNameInput = event.target.closest('[data-user-display]');
  if (!displayNameInput) {
    return;
  }
  setAccessUserDraftValue(
    Number(displayNameInput.dataset.userDisplay || 0),
    'display_name',
    displayNameInput.value,
  );
}

function onAccessUsersListChange(event) {
  const roleSelect = event.target.closest('[data-user-role]');
  if (roleSelect) {
    const userId = Number(roleSelect.dataset.userRole || 0);
    const role = getAccessRoleByCode(roleSelect.value);
    if (!userId || !role) {
      return;
    }
    const departmentSelect = refs.accessUsersList.querySelector(`[data-user-department="${userId}"]`);
    setAccessUserDraftValue(userId, 'role', role.code);
    if (departmentSelect && !departmentSelect.disabled && role.default_department_code) {
      departmentSelect.value = role.default_department_code;
      setAccessUserDraftValue(userId, 'department_code', role.default_department_code);
    }
    state.accessControlSelectedUserId = userId;
    state.accessControlSelectedRole = String(role.code);
    state.accessControlPreviewRole = String(role.code);
    state.accessControlDraftPermissions = buildAccessRoleDefaultSet(role.code);
    renderAccessRoleSummary();
    renderAccessRoleCards();
    renderAccessPermissionEditor();
    notify('Rol şablonu önizlendi. Uygulamak için Değişiklikleri Kaydet butonunu kullanın.', 'success');
    return;
  }
  const departmentSelect = event.target.closest('[data-user-department]');
  if (departmentSelect) {
    const userId = Number(departmentSelect.dataset.userDepartment || 0);
    setAccessUserDraftValue(userId, 'department_code', departmentSelect.value);
    state.accessControlSelectedUserId = userId;
    state.accessControlPreviewRole = '';
    renderAccessPermissionEditor();
    notify('Departman seçimi güncellendi. Kalıcı yapmak için Değişiklikleri Kaydet butonunu kullanın.', 'success');
    return;
  }
  const activeInput = event.target.closest('[data-user-active]');
  if (activeInput) {
    const userId = Number(activeInput.dataset.userActive || 0);
    setAccessUserDraftValue(userId, 'is_active', Boolean(activeInput.checked));
    state.accessControlSelectedUserId = userId;
    state.accessControlPreviewRole = '';
    notify('Aktiflik durumu değiştirildi. Kalıcı yapmak için Değişiklikleri Kaydet butonunu kullanın.', 'success');
  }
}

async function saveAccessUser(userId) {
  if (!hasPermission('access_control:write')) {
    notify('Bu kullanıcıyı güncelleme yetkiniz bulunmuyor.', 'warn');
    return;
  }
  const user = getAccessUserById(userId);
  if (!user) {
    notify('Kullanıcı bulunamadı.', 'error');
    return;
  }
  const userKey = String(userId);
  const displayNameInput = refs.accessUsersList.querySelector(`[data-user-display="${userKey}"]`);
  const passwordInput = refs.accessUsersList.querySelector(`[data-user-password="${userKey}"]`);
  const roleSelect = refs.accessUsersList.querySelector(`[data-user-role="${userKey}"]`);
  const departmentSelect = refs.accessUsersList.querySelector(`[data-user-department="${userKey}"]`);
  const activeInput = refs.accessUsersList.querySelector(`[data-user-active="${userKey}"]`);
  const payload = {
    display_name: displayNameInput ? displayNameInput.value.trim() : user.display_name || '',
  };
  const nextPassword = passwordInput ? String(passwordInput.value || '') : '';
  if (nextPassword) {
    if (nextPassword.length < 12) {
      notify('Yeni geçici şifre en az 12 karakter olmalıdır.', 'warn');
      return;
    }
    if (new TextEncoder().encode(nextPassword).length > 72) {
      notify('Şifre en fazla 72 byte olabilir.', 'warn');
      return;
    }
    payload.new_password = nextPassword;
  }
  if (Number(userId) !== Number(state.me?.user_id || 0)) {
    payload.role = roleSelect ? roleSelect.value : user.role;
    payload.department_code = departmentSelect ? departmentSelect.value : user.department_code;
    payload.is_active = Boolean(activeInput?.checked);
  } else {
    payload.department_code = departmentSelect ? departmentSelect.value : user.department_code;
  }
  try {
    const response = await apiFetch(`/users/${encodeURIComponent(userId)}`, {method: 'PUT', body: payload});
    state.accessControlSelectedUserId = userId;
    state.accessControlPreviewRole = '';
    state.accessControlSelectedRole = String(response.user?.role || state.accessControlSelectedRole);
    state.accessControlDraftPermissions = new Set(response.user?.permissions || []);
    await loadAccessControl();
    notify(`${user.username} kullanıcısı güncellendi.`, 'success');
  } catch (error) {
    notify(error.message, 'error');
  }
}

async function rotateAccessUserTotp(userId) {
  if (!hasPermission('access_control:write')) {
    notify('2FA yenileme yetkiniz bulunmuyor.', 'warn');
    return;
  }
  const user = getAccessUserById(userId);
  if (!user) {
    notify('Kullanıcı bulunamadı.', 'error');
    return;
  }
  if (!confirm(`${user.username} kullanıcısı için Authenticator uygulaması kurulumunu yenilemek istiyor musunuz?`)) {
    return;
  }
  try {
    const response = await apiFetch(`/users/${encodeURIComponent(userId)}/rotate-totp`, {method: 'POST', body: {}});
    state.accessControlSelectedUserId = userId;
    state.accessControlPreviewRole = '';
    state.accessControlDraftPermissions = new Set(response.user?.permissions || []);
    showAccessTotpResult(response, 'Authenticator uygulaması kurulumu yenilendi');
    await loadAccessControl();
    notify(`${user.username} için 2FA kurulumu yenilendi.`, 'success');
  } catch (error) {
    notify(error.message, 'error');
  }
}

function onAccessPermissionTreeChange(event) {
  const input = event.target.closest('[data-access-permission]');
  if (!input) {
    return;
  }
  const permissionKey = String(input.dataset.accessPermission || '');
  if (!permissionKey) {
    return;
  }
  if (state.accessControlPreviewRole) {
    notify('Rol şablonu önizleme modunda doğrudan düzenlenemez.', 'warn');
    renderAccessPermissionEditor();
    return;
  }
  if (!(state.accessControlDraftPermissions instanceof Set)) {
    state.accessControlDraftPermissions = new Set();
  }
  if (input.checked) {
    state.accessControlDraftPermissions.add(permissionKey);
  } else {
    state.accessControlDraftPermissions.delete(permissionKey);
  }
  renderAccessPermissionEditor();
}

function onAccessResetPermissions() {
  const user = getAccessSelectedUser();
  if (!user) {
    notify('Önce bir kullanıcı seçin.', 'warn');
    return;
  }
  if (!hasPermission('access_control:write') || Number(user.user_id) === Number(state.me?.user_id || 0)) {
    notify('Bu kullanıcı için izin sıfırlama yetkiniz bulunmuyor.', 'warn');
    return;
  }
  state.accessControlDraftPermissions = buildAccessRoleDefaultSet(user.role);
  renderAccessPermissionEditor();
  notify('Rol varsayılan izinleri yüklendi. Kaydetmek için butonu kullanın.', 'success');
}

async function onAccessSavePermissions() {
  const user = getAccessSelectedUser();
  if (!user) {
    notify('Önce bir kullanıcı seçin.', 'warn');
    return;
  }
  if (!hasPermission('access_control:write') || Number(user.user_id) === Number(state.me?.user_id || 0)) {
    notify('Bu kullanıcı için izin güncelleme yetkiniz bulunmuyor.', 'warn');
    return;
  }
  try {
    const response = await apiFetch(`/users/${encodeURIComponent(user.user_id)}/permissions`, {
      method: 'PUT',
      body: {
        permissions: Array.from(state.accessControlDraftPermissions || []).sort(),
      },
    });
    state.accessControlSelectedUserId = Number(user.user_id);
    state.accessControlPreviewRole = '';
    state.accessControlDraftPermissions = new Set(response.user?.permissions || []);
    await loadAccessControl();
    notify(`${user.username} için izinler kaydedildi.`, 'success');
  } catch (error) {
    notify(error.message, 'error');
  }
}

async function loadTickets() {
  const form = new FormData(refs.ticketFilters);
  const params = new URLSearchParams();
  if (state.me?.role === 'ADMIN' && state.selectedHotelId) params.set('hotel_id', state.selectedHotelId);
  if (form.get('status')) params.set('status', String(form.get('status')));
  if (form.get('priority')) params.set('priority', String(form.get('priority')));
  const response = await apiFetch(`/tickets?${params.toString()}`);
  state.tickets = response.items || [];
  refs.ticketTableBody.innerHTML = renderTicketRows(state.tickets);
}

function renderTicketRows(items) {
  if (!items.length) {
    return `<tr><td colspan="7"><div class="empty-state"><p>Açık talep bulunamadı.</p></div></td></tr>`;
  }
  return items.map(item => `
    <tr>
      <td><div class="stack"><strong>${escapeHtml(item.ticket_id)}</strong><span class="muted">${escapeHtml(item.reason)}</span></div></td>
      <td><span class="pill ${escapeHtml((item.priority || 'low').toLowerCase())}">${escapeHtml(formatPriorityLabel(item.priority))}</span></td>
      <td>${escapeHtml(formatTicketStatus(item.status))}</td>
      <td>${escapeHtml(item.assigned_to_role || '-')}</td>
      <td>${formatDate(item.created_at)}</td>
      <td><div class="muted">${escapeHtml(item.transcript_summary || '').slice(0, 180)}</div></td>
      <td>
        <div class="stack">
          <select data-ticket-status="${escapeHtml(item.ticket_id)}" aria-label="${escapeHtml(item.ticket_id + ' talep durumu')}">
            ${['OPEN','IN_PROGRESS','RESOLVED','CLOSED'].map(status => `<option value="${status}" ${item.status === status ? 'selected' : ''}>${escapeHtml(formatTicketStatus(status))}</option>`).join('')}
          </select>
          <button class="action-button primary" data-save-ticket="${escapeHtml(item.ticket_id)}" aria-label="${escapeHtml(item.ticket_id + ' talebini kaydet')}">Kaydet</button>
        </div>
      </td>
    </tr>
  `).join('');
}

// Ticket actions handled by delegated event listener (see bindDelegatedEvents)
""" + ADMIN_PANEL_TAIL_SCRIPT
