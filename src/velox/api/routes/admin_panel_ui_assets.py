"""Static assets for the admin operations panel."""

# ruff: noqa: E501

from velox.api.routes.admin_panel_ui_tail_assets import ADMIN_PANEL_TAIL_SCRIPT
from velox.api.routes.ui_shared_assets import UI_SHARED_SCRIPT

ADMIN_PANEL_STYLE = """\
*,*::before,*::after{box-sizing:border-box}
:root{
  --bg:#f4efe6;--bg-2:#ebe4d8;--surface:#fffdf8;--surface-2:#f8f4ec;--ink:#102033;--muted:#5d6877;
  --line:rgba(16,32,51,.12);--line-strong:rgba(16,32,51,.2);--accent:#0f766e;--accent-2:#1d8f86;
  --warn:#b45309;--danger:#b42318;--danger-2:#7f1d1d;--ok:#166534;--gold:#bb8a2a;--shadow:0 18px 42px rgba(16,32,51,.08);
  --radius-lg:26px;--radius-md:18px;--radius-sm:12px;--mono:'Cascadia Code','Fira Code',monospace;
  --sans:'Manrope','Segoe UI Variable','Aptos','Segoe UI',system-ui,sans-serif;--serif:'Fraunces','Iowan Old Style','Georgia',serif;
}
html,body{min-height:100%;margin:0;background:
  radial-gradient(circle at top left,rgba(187,138,42,.18),transparent 24%),
  radial-gradient(circle at bottom right,rgba(15,118,110,.12),transparent 22%),
  linear-gradient(180deg,var(--bg) 0%,var(--bg-2) 100%);
  color:var(--ink);font-family:var(--sans)}
body{padding:18px}
button,input,select,textarea{font:inherit}
[hidden]{display:none!important}
.shell{display:grid;grid-template-columns:280px minmax(0,1fr);gap:18px;min-height:calc(100vh - 36px)}
.shell:has(> .sidebar[hidden]){grid-template-columns:1fr}
.sidebar{background:linear-gradient(180deg,#11223a 0%,#0a1525 100%);color:#eff6ff;border-radius:30px;padding:24px;display:flex;flex-direction:column;gap:22px;box-shadow:var(--shadow)}
.brand{display:flex;align-items:flex-start;gap:14px}
.brand-mark{width:46px;height:46px;border-radius:16px;background:linear-gradient(135deg,var(--gold),#f2ca72);display:grid;place-items:center;color:#4c3506;font-weight:900;letter-spacing:.06em}
.brand h1{margin:0;font-family:var(--serif);font-size:22px;line-height:1.05}
.brand p{margin:6px 0 0;color:rgba(239,246,255,.72);font-size:13px;line-height:1.45}
.nav{display:flex;flex-direction:column;gap:8px}
.nav button{border:none;background:transparent;color:inherit;padding:12px 14px;border-radius:16px;text-align:left;display:flex;align-items:center;justify-content:space-between;gap:12px;cursor:pointer;transition:.18s background ease,.18s transform ease}
.nav button:hover{background:rgba(255,255,255,.08);transform:translateX(2px)}
.nav button.is-active{background:linear-gradient(135deg,rgba(29,143,134,.24),rgba(187,138,42,.18));box-shadow:inset 0 0 0 1px rgba(255,255,255,.08)}
.nav-label{display:flex;flex-direction:column;gap:3px}
.nav-label strong{font-size:14px}
.nav-label span{font-size:12px;color:rgba(239,246,255,.72)}
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
.sidebar-toggle:focus-visible,.nav button:focus-visible,.sidebar-button:focus-visible,.toolbar button:focus-visible,.inline-button:focus-visible,.action-button:focus-visible{
  outline:2px solid rgba(187,138,42,.9);outline-offset:2px
}
.badge{display:inline-flex;align-items:center;gap:8px;padding:8px 12px;border-radius:999px;font-size:12px;font-weight:800;letter-spacing:.03em}
.badge.info{background:#e8f3f1;color:#115e59}.badge.warn{background:#fff2dd;color:#92400e}.badge.danger{background:#fde7e5;color:#991b1b}.badge.dark{background:#13253e;color:#fff}
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
.section-grid{display:grid;gap:18px}
.card-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}
.overview-card h4{margin:0;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.overview-card strong{display:block;margin-top:12px;font-size:34px;font-family:var(--serif);line-height:1}
.overview-card span{display:block;margin-top:8px;color:var(--muted);font-size:13px}
.module-header{display:flex;align-items:flex-start;justify-content:space-between;gap:14px;margin-bottom:16px}
.module-actions{display:flex;flex-wrap:wrap;gap:10px}
.split{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(340px,.8fr);gap:18px}
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
  .split,.auth-grid,.access-control-layout,.access-control-main{grid-template-columns:1fr}
}
@media(max-width:980px){
  body{padding:12px}.shell{grid-template-columns:1fr}
  .sidebar{position:fixed;left:12px;top:12px;bottom:12px;z-index:70;width:min(86vw,320px);padding:18px;border-radius:24px;transform:translateX(-112%);transition:transform .2s ease}
  .sidebar.is-open{transform:translateX(0)}
  .sidebar-toggle{display:inline-flex;align-items:center;justify-content:center}
  .topbar-actions{width:100%;justify-content:space-between;align-items:center}
  .topbar-aside{justify-content:flex-start}
  .table-shell{overflow-x:auto;overflow-y:hidden;-webkit-overflow-scrolling:touch}
  .table-shell table{min-width:640px}
  .field-grid,.dense-form,.status-list,.profile-section-grid,.profile-inline-grid,.profile-overview-grid,.debug-summary-grid,.debug-layout,.access-toggle-grid,.access-user-controls{grid-template-columns:1fr}
  .topbar{padding:18px 20px;border-radius:24px;flex-direction:column}
  .card-grid{grid-template-columns:1fr}
  .status-strip{grid-template-columns:1fr}
  .hold-summary-grid{grid-template-columns:1fr}
  .debug-artifact-preview-meta{align-items:flex-start}
  .access-permission-row{grid-template-columns:1fr}
}
"""

ADMIN_PANEL_SCRIPT = UI_SHARED_SCRIPT + """\
const CONFIG = window.ADMIN_PANEL_CONFIG || {};
const API_ROOT = '/api/v1/admin';
const HOTEL_KEY = 'velox.admin.hotel';
const CSRF_COOKIE = 'velox_admin_csrf';
const LIVE_REFRESH_INTERVAL_MS = 3000;
const VIEW_PERMISSIONS = {
  accesscontrol: 'access_control:read',
};

const state = {
  me: null,
  bootstrap: null,
  bootstrapPending: null,
  hotels: [],
  selectedHotelId: window.localStorage.getItem(HOTEL_KEY) || '',
  currentView: ((window.location.hash || '#dashboard').replace('#', '').toLowerCase() === 'access-control'
    ? 'accesscontrol'
    : (window.location.hash || '#dashboard').replace('#', '')),
  lastDebugSourceView: 'dashboard',
  dashboard: null,
  conversations: [],
  conversationsTotal: 0,
  conversationDetail: null,
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
  accessControlDraftPermissions: new Set(),
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
  refreshPromise: null,
  liveRefreshHandle: null,
  _authKeepAliveTimer: null,
  _visibilityBound: false,
};

const refs = {};

document.addEventListener('DOMContentLoaded', () => {
  startInteractiveLabelObserver(document.body);
  bindRefs();
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
    'sidebar','sidebarToggle','topbar',
    'toast','authView','panelView','loginForm','bootstrapForm','bootstrapCard','bootstrapSummary',
    'totpRecovery','totpRecoveryForm','trustedSessionBanner','loginOtpField','rememberDeviceToggle',
    'loginRememberOptions','loginVerificationOptions','loginSessionOptions',
    'otpSetup','otpSecret','otpUri','otpQrImage','otpVerifyForm','otpVerifyHint','currentUser','currentRole','hotelScope','hotelSelect','nav','pageTitle','pageLead',
    'dashboardCards','dashboardQueues','conversationFilters','conversationBulkBar','conversationSelectAll','conversationSelectionCount','conversationTableBody','conversationDetail',
    'stayHoldFilters','stayHoldTableBody','stayHoldDetail','stayHoldCreatePanel','stayWizardSteps','stayWizardBody','stayStatusChips',
    'restaurantHoldFilters','restaurantHoldTableBody','restaurantHoldDetail','restaurantHoldCreatePanel','restaurantCreateForm','restaurantStatusChips','restaurantDateFrom','restaurantDateTo',
    'transferHoldFilters','transferHoldTableBody','transferHoldDetail','transferHoldCreatePanel','transferCreateForm','transferStatusChips',
    'accessOverviewCards','accessRoleSummary','accessRoleCards','accessCreateUserForm','accessCreateUsername','accessCreateDisplayName',
    'accessCreatePassword','accessCreatePasswordConfirm','accessCreateRole','accessCreateDepartment','accessCreateActive',
    'accessCreateTwoFactor','accessTotpResult','accessTotpResultTitle','accessTotpResultUser','accessTotpQrImage',
    'accessTotpSecret','accessTotpUri','accessUsersList','accessPermissionMeta','accessPermissionTree',
    'accessResetPermissionsButton','accessSavePermissionsButton',
    'ticketFilters','ticketTableBody','hotelProfileSelect','hotelProfileEditor','applyHotelProfileJson','saveHotelProfile',
    'faqFilters','faqTableBody','faqDetail',
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
    'logoutButton','reloadButton','decisionDialog','decisionForm','decisionTitle','decisionLead','decisionReason',
    'decisionHoldId','decisionMode'
  ].forEach(id => refs[id] = document.getElementById(id));
  // Bootstrap hotel select uses kebab-case id in HTML; map it to the existing JS key.
  refs.bootstrapHotels = document.getElementById('bootstrap-hotel');
}

function bindEvents() {
  refs.sidebarToggle?.addEventListener('click', toggleSidebar);
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
  refs.reloadButton?.addEventListener('click', reloadConfig);
  refs.logoutButton?.addEventListener('click', logout);
  refs.conversationFilters?.addEventListener('submit', event => {
    event.preventDefault();
    clearConversationSelection();
    loadConversations();
  });
  refs.conversationTableBody?.addEventListener('change', onConversationSelectionChange);
  refs.conversationSelectAll?.addEventListener('change', onConversationSelectAllChange);
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
  refs.accessPermissionTree?.addEventListener('change', onAccessPermissionTreeChange);
  refs.accessResetPermissionsButton?.addEventListener('click', onAccessResetPermissions);
  refs.accessSavePermissionsButton?.addEventListener('click', onAccessSavePermissions);
  refs.faqFilters?.addEventListener('submit', event => {
    event.preventDefault();
    loadFaqs();
  });
  refs.addNotifPhoneForm?.addEventListener('submit', onAddNotifPhone);
  refs.decisionForm?.addEventListener('submit', onDecisionSubmit);
  refs.hotelProfileSections?.addEventListener('click', onHotelProfileSectionNav);
  refs.hotelProfileSections?.addEventListener('input', onHotelProfileSectionSearchInput);
  refs.hotelProfileSections?.addEventListener('click', onHotelProfileSectionSearchClick);
  refs.hotelProfileSectionBody?.addEventListener('click', onHotelProfileSectionClick);
  refs.hotelProfileSectionBody?.addEventListener('input', onHotelProfileSectionInput);
  refs.hotelProfileSectionBody?.addEventListener('change', onHotelProfileSectionChange);
  document.querySelectorAll('[data-nav]').forEach(button => {
    const label = button.querySelector('.nav-label strong')?.textContent || 'Navigasyon';
    button.setAttribute('aria-label', label.trim());
    button.addEventListener('click', () => {
      setView(button.dataset.nav);
      closeSidebar();
    });
  });
  refs.saveHotelProfile?.addEventListener('click', saveHotelProfile);
  document.getElementById('loadSlotsButton').addEventListener('click', event => {
    event.preventDefault();
    loadRestaurantSlots({syncRestaurantFilters: true});
  });
  document.getElementById('closeDecision').addEventListener('click', () => refs.decisionDialog.close());
  window.addEventListener('message', async event => {
    if (event.data && event.data.type === 'chatlab:auth-required') {
      await loadChatLab();
    }
    if (event.data && event.data.type === 'chatlab:faq-created') {
      if (state.currentView === 'faq') loadFaqs();
    }
  });
  window.addEventListener('hashchange', () => {
    const rawView = window.location.hash.replace('#', '') || 'dashboard';
    const newView = String(rawView).toLowerCase() === 'access-control' ? 'accesscontrol' : rawView;
    if (newView !== state.currentView) {
      setView(newView);
    }
  });
  window.addEventListener('resize', closeSidebar);
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

function isMobileLayout() {
  return window.matchMedia('(max-width: 980px)').matches;
}

function closeSidebar() {
  if (!refs.sidebar || !refs.sidebarToggle) return;
  refs.sidebar.classList.remove('is-open');
  refs.sidebarToggle.setAttribute('aria-expanded', 'false');
}

function toggleSidebar() {
  if (!refs.sidebar || !refs.sidebarToggle || !isMobileLayout()) return;
  refs.sidebar.classList.toggle('is-open');
  refs.sidebarToggle.setAttribute('aria-expanded', refs.sidebar.classList.contains('is-open') ? 'true' : 'false');
}

function bindDelegatedEvents() {
  // Single delegated click handler on panelView covers all dynamic table actions.
  // This avoids re-binding listeners every time a table is re-rendered.
  refs.panelView.addEventListener('click', async event => {
    // Holds module events (tabs, wizards, filters, create toggles, hold selection)
    if (typeof handleHoldsModuleClick === 'function' && handleHoldsModuleClick(event.target)) return;

    const target = event.target.closest('[data-bulk-action],[data-open-conversation],[data-deactivate-conversation],[data-approve-hold],[data-reject-hold],[data-save-ticket],[data-facts-version-detail],[data-facts-version-rollback],[data-facts-conflict-restore-draft],[data-facts-conflict-dismiss]');
    if (!target) return;

    if (target.dataset.bulkAction) {
      runConversationBulkAction(target.dataset.bulkAction);
      return;
    }

    // Conversation detail
    if (target.dataset.openConversation) {
      loadConversationDetail(target.dataset.openConversation);
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
      approveButton.textContent = 'Onaylaniyor...';
      try {
        const result = await apiFetch(`/holds/${target.dataset.approveHold}/approve?force=true`, {method: 'POST', body: {notes: ''}});
        if (result && result.status === 'already_processed') {
          notify('Hold zaten islenmis durumda. Tekrar onay tetiklenmedi.', 'info');
        } else {
          notify('Hold onaylandı.', 'success');
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
      refs.decisionTitle.textContent = 'Hold reddet';
      refs.decisionLead.textContent = 'İsterseniz gerekçe yazın; boş bırakarak da reddedebilirsiniz.';
      refs.decisionReason.value = '';
      refs.decisionDialog.showModal();
      return;
    }

    if (target.dataset.restaurantStatus) {
      const holdId = target.dataset.restaurantHold || '';
      const nextStatus = target.dataset.restaurantStatus || '';
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
  // If access cookie is gone but a trusted device session exists,
  // try a silent refresh BEFORE hydrateSession so we avoid the
  // 401 → refresh → retry round-trip that sometimes loses the race
  // against concurrent requests.
  const hasAccess = Boolean(readCookie('velox_admin_access'));
  const status = state.sessionStatus || {};
  if (!hasAccess && status.has_trusted_device && status.session_active) {
    const recovered = await refreshAccessSession({silent: true});
    if (!recovered) {
      showAuth();
      return;
    }
  }

  try {
    await hydrateSession();
    startAuthKeepAlive();
    return;
  } catch (_error) {
    showAuth();
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
      <p>Veritabanında admin kullanıcısı yok. İlk hesap oluşturulduktan sonra panel doğrudan 2FA ile çalışacak.</p>
    </div>
    <div class="helper-box">
      <strong>Erişim modu</strong>
      <p>${escapeHtml(accessMode)}</p>
    </div>
  `;
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
    status.verification_preset || '7_days',
  );
  renderChoiceGroup(
    refs.loginSessionOptions,
    'session_preset',
    sessionOptions,
    status.session_preset || '24_hours',
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
  payload.verification_preset = getSelectedChoice(refs.loginForm, 'verification_preset', state.sessionStatus?.verification_preset || '7_days');
  payload.session_preset = getSelectedChoice(refs.loginForm, 'session_preset', state.sessionStatus?.session_preset || '24_hours');
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
    notify('İlk admin hesabı oluşturuldu. QR okutun ve kodu doğrulayın.', 'success');
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
    notify('Önce ilk admin hesabını oluşturun.', 'warn');
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
  await Promise.all([
    loadDashboard(),
    loadSystemOverview(),
    loadSessionPreferences(),
    loadDebugRunsSafely({preserveSelection: false}, {notifyOnError: false}),
  ]);
  setView(state.currentView || 'dashboard');
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

function syncNavigationAccess() {
  document.querySelectorAll('[data-nav]').forEach(button => {
    const requiredPermission = VIEW_PERMISSIONS[button.dataset.nav];
    button.hidden = Boolean(requiredPermission) && !hasPermission(requiredPermission);
  });
}

function showAuth() {
  clearLiveRefresh();
  stopDebugPolling();
  stopAuthKeepAlive();
  refs.sidebar.hidden = true;
  refs.topbar.hidden = true;
  refs.authView.hidden = false;
  refs.panelView.hidden = true;
  refs.currentUser.textContent = 'Misafir değil, operasyon';
  refs.currentRole.textContent = 'Panel girişi bekleniyor';
  refs.hotelScope.textContent = CONFIG.public_host || 'nexlumeai.com';
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
}

function setView(view) {
  if (state.me && VIEW_PERMISSIONS[view] && !hasPermission(VIEW_PERMISSIONS[view])) {
    notify('Bu bölümü görüntüleme yetkiniz bulunmuyor.', 'warn');
    view = 'dashboard';
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
  document.querySelectorAll('[data-nav]').forEach(button => {
    button.classList.toggle('is-active', button.dataset.nav === view);
  });

  const meta = {
    dashboard: ['Genel Bakış', 'Aktif konuşmaları, bekleyen onayları ve açık talepleri tek ekranda görüntüleyin.'],
    conversations: ['Konuşmalar', 'Misafir mesajlarını, durumlarını ve geçmişini inceleyin.'],
    holds: ['Onay Bekleyenler', 'Konaklama, restoran ve transfer taleplerini onaylayın veya reddedin.'],
    tickets: ['Destek Talepleri', 'Ekibe aktarılan görevleri öncelik ve duruma göre takip edin.'],
    hotels: ['Otel Bilgileri', 'Otel profilini düzenleyin ve değişiklikleri sisteme güvenle uygulayın.'],
    faq: ['Sık Sorulan Sorular', 'Hazır yanıtları yönetin, uygunsuz içerikleri hızlıca kaldırın.'],
    restaurant: ['Restoran Yönetimi', 'Tarih ve saat bazlı masa kapasitelerini ayarlayın.'],
    notifications: ['Bildirim Ayarları', 'Rezervasyon onayları için WhatsApp bildirim numaralarını yönetin.'],
    accesscontrol: ['Rol ve Yetkiler', 'Kullanıcı, rol, departman ve pencere bazlı işlem izinlerini aynı ekranda yönetin.'],
    system: ['Sistem Durumu', 'Sunucu sağlığı, alan adı ve güvenlik ayarlarını kontrol edin.'],
    chatlab: ['Test Paneli', 'Yapay zekâyı canlı test edin, puanlayın ve raporlayın.'],
    debug: ['Hata Raporları', 'Canlı panelde başlatılan report-only taramaların bulgularını inceleyin.'],
  }[view] || ['Yönetim Paneli', 'Yönetim merkezi'];

  refs.pageTitle.textContent = meta[0];
  refs.pageLead.textContent = meta[1];

  if (view === 'dashboard') loadDashboard();
  if (view === 'conversations') loadConversations();
  if (view === 'holds') switchHoldsTab(state.activeHoldsTab || 'stay');
  if (view === 'tickets') loadTickets();
  if (view === 'hotels') loadHotelProfileSection();
  if (view === 'faq') loadFaqs();
  if (view === 'restaurant') {
    loadRestaurantSlots();
    if (typeof loadRestaurantHolds === 'function') loadRestaurantHolds();
    if (typeof loadRestaurantSettings === 'function') loadRestaurantSettings();
  }
  if (view === 'notifications') loadNotifPhones();
  if (view === 'accesscontrol') loadAccessControl();
  if (view === 'system') loadSystemOverview();
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
  setView(state.currentView);
}

function openDebugRunModal() {
  if (!refs.debugRunDialog) return;
  if (!state.debugWorkerReady) {
    notify(state.debugWorkerMessage || 'Debug worker hazır değil.', 'error');
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
  const effectiveView = state.currentView || state.lastDebugSourceView || 'dashboard';
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
      notify('Debug run için iptal isteği işlendi.', 'success');
      await loadDebugRuns({preserveSelection: true});
      return;
    }
    if (action === 'retry') {
      const response = await apiFetch(`/debug/runs/${encodeURIComponent(state.activeDebugRunId)}/retry`, {method: 'POST', body: {}});
      state.activeDebugRunId = response.run?.id || state.activeDebugRunId;
      state.activeDebugFindingId = '';
      notify('Debug run yeniden kuyruğa alındı.', 'success');
      await loadDebugRuns({preserveSelection: true});
    }
  } catch (error) {
    notify(error.message || 'Debug aksiyonu tamamlanamadı.', 'error');
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
    state.debugWorkerMessage = 'Debug verileri alınamadı.';
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
    state.debugWorkerMessage = 'Debug worker durumu alınamadı.';
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

function debugSeverityBadgeClass(severity) {
  if (severity === 'critical' || severity === 'high') return 'danger';
  if (severity === 'medium') return 'warn';
  if (severity === 'low') return 'success';
  return 'info';
}

function formatDebugArtifactTypeLabel(artifactType) {
  if (artifactType === 'screenshot') return 'Ekran görüntüsü';
  if (artifactType === 'console_log') return 'Konsol kaydı';
  if (artifactType === 'network_log') return 'Ağ kaydı';
  if (artifactType === 'dom_snapshot') return 'DOM snapshot';
  if (artifactType === 'trace') return 'Trace';
  return artifactType || 'Artifact';
}

function getDebugArtifactScreenLabel(item) {
  const screen = item?.metadata?.screen;
  if (screen) return String(screen);
  const storagePath = String(item?.storage_path || '');
  if (storagePath.includes('admin_shell')) return 'Admin Panel';
  if (storagePath.includes('chatlab_shell')) return 'Chat Lab';
  return 'Diğer Kanıtlar';
}

function getDebugArtifactContextNote() {
  const finding = state.debugFindings.find(item => item.id === state.activeDebugFindingId);
  if (finding && state.debugArtifactScope === 'finding') {
    return 'Bu artifact listesi yalnız seçili bulguya bağlı kanıtları gösterir.';
  }
  if (finding && state.debugArtifactScope === 'run_fallback') {
    return 'Bu bulguya doğrudan bağlı artifact yok. Aşağıda run seviyesinde kaydedilen kanıtlar gösteriliyor.';
  }
  const findingCount = Number(state.debugRunDetail?.summary?.finding_count || 0);
  if (!finding && findingCount === 0) {
    return 'Bu run temiz tamamlandı. Aşağıdaki görseller bulgu değil, taramanın gerçekten hangi ekranlara ulaştığının kanıtıdır.';
  }
  return 'Aşağıdaki artifactlar tarama sırasında kaydedilen ekran görüntüsü ve teknik kanıtlardır.';
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
  refs.debugArtifactPreviewMeta.textContent = buildDebugArtifactMetaLine(artifact) || 'Artifact ayrıntıları';
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
    refs.debugTopbarStatus.textContent = state.debugWorkerMessage || 'Worker kapalı';
    refs.debugTopbarStatus.className = 'badge danger';
    refs.debugStartButton.disabled = true;
    return;
  }
  if (!activeRun) {
    if (!state.debugBrowserScanAvailable && state.debugBrowserScanMessage) {
      refs.debugTopbarStatus.textContent = 'HTTP tarama hazır · screenshot yok';
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
        <p>Topbardaki Hata Taraması butonundan yeni bir run başlatabilirsiniz.</p>
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
          <span class="pill ${debugStatusBadgeClass(item.status)}">${escapeHtml(item.status)}</span>
        </header>
        <div class="muted">${escapeHtml(item.failure_reason || 'Run kaydı oluşturuldu ve işlenmeyi bekliyor.')}</div>
        <div class="debug-card-meta">
          <span>${escapeHtml(item.mode || '-')}</span>
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
        <h4>Run seçilmedi</h4>
        <p>Bulguları görmek için soldan bir tarama kaydı seçin.</p>
      </div>
    `;
    return;
  }
  if (!state.debugFindings.length) {
    const waitingText = state.debugRunDetail?.status === 'queued' || state.debugRunDetail?.status === 'running'
      ? 'Tarama sürüyor. Bulgular geldikçe burada listelenecek.'
      : 'Bu run için henüz bulgu üretilmedi.';
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
        <span class="pill ${debugSeverityBadgeClass(item.severity)}">${escapeHtml(item.severity)}</span>
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
    refs.debugSummaryCounts.textContent = 'Critical 0 / High 0 / Medium 0 / Low 0';
    refs.debugSummaryScope.textContent = '-';
    return;
  }
  const summary = run.summary || {};
  refs.debugActiveRunStatus.textContent = run.status || '-';
  refs.debugActiveRunMeta.textContent = run.failure_reason || `${formatDate(run.queued_at) || '-'} · ${describeDebugScope(run.scope)}`;
  refs.debugSummaryFindings.textContent = String(summary.finding_count || state.debugFindings.length || 0);
  refs.debugSummaryCounts.textContent = `Critical ${summary.critical_count || 0} / High ${summary.high_count || 0} / Medium ${summary.medium_count || 0} / Low ${summary.low_count || 0}`;
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
          <div><span class="pill ${debugSeverityBadgeClass(finding.severity)}">${escapeHtml(finding.severity)}</span></div>
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
          <strong>Artifact'lar ve Kanıtlar</strong>
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
        <p>Detay görmek için soldan bir run veya ortadan bir bulgu seçin.</p>
      </div>
    `;
    return;
  }
  const run = state.debugRunDetail;
  refs.debugDetailPanel.innerHTML = `
    <div class="debug-detail-grid">
      <div class="debug-detail-section">
        <strong>Run Durumu</strong>
        <div class="debug-toolbar">
          <span class="pill ${debugStatusBadgeClass(run.status)}">${escapeHtml(run.status || '-')}</span>
          <span class="pill info">${escapeHtml(describeDebugScope(run.scope))}</span>
        </div>
        <p class="muted">${escapeHtml(run.failure_reason || 'Run detayları aşağıda özetleniyor.')}</p>
      </div>
      <div class="debug-detail-section">
        <strong>Zaman Çizelgesi</strong>
        <pre>${escapeHtml([
          `Kuyruğa alındı: ${formatDate(run.queued_at) || '-'}`,
          `Başladı: ${formatDate(run.started_at) || '-'}`,
          `Bitti: ${formatDate(run.finished_at) || '-'}`,
          `Heartbeat: ${formatDate(run.last_heartbeat_at) || '-'}`,
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
        <strong>Artifact'lar ve Kanıtlar</strong>
        ${artifactMarkup}
      </div>
    </div>
  `;
}

function renderDebugArtifacts() {
  if (!state.debugArtifacts.length) {
    return `
      <div class="debug-empty-compact">
        <h4>Artifact bulunamadı</h4>
        <p>Bu seçim için henüz ekran görüntüsü veya ek kanıt kaydedilmedi.</p>
      </div>
    `;
  }
  const groups = groupDebugArtifacts(state.debugArtifacts);
  const screenCount = groups.length;
  const scopeLabel = state.debugArtifactScope === 'finding'
    ? 'Bulgu kanıtı'
    : (state.debugArtifactScope === 'run_fallback' ? 'Run kanıtı (yedek)' : 'Run kanıtı');
  return `
    <div class="debug-artifact-groups">
      <section class="debug-artifact-summary">
        <strong>${escapeHtml(scopeLabel)} · ${escapeHtml(String(state.debugArtifacts.length))} artifact · ${escapeHtml(String(screenCount))} ekran</strong>
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
  refs.conversationTableBody.innerHTML = renderConversationRows(state.conversations);
  if (state.conversations.length && !state.conversationDetail) {
    loadConversationDetail(state.conversations[0].id);
  } else if (!state.conversations.length) {
    refs.conversationDetail.innerHTML = '<div class="empty-state"><p>Seçili konuşma yok.</p></div>';
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

function renderConversationRows(items) {
  if (!items.length) {
    return `<tr><td colspan="7"><div class="empty-state"><p>Filtreye uygun konuşma bulunamadı.</p></div></td></tr>`;
  }
  return items.map(item => `
    <tr class="${state.selectedConversationIds.has(String(item.id)) ? 'is-selected' : ''}" data-conversation-row="${escapeHtml(item.id)}">
      <td class="table-select"><input class="row-select" type="checkbox" data-select-conversation="${escapeHtml(item.id)}" ${state.selectedConversationIds.has(String(item.id)) ? 'checked' : ''} aria-label="Konuşmayı seç"></td>
      <td><div class="stack"><strong>${escapeHtml(item.phone_display || 'Maskeli kullanıcı')}</strong><span class="muted mono">${escapeHtml(item.id)}</span></div></td>
      <td><span class="pill open">${escapeHtml(formatConversationState(item.current_state || '-'))}</span>${item.human_override ? ' <span class="pill pill-warning" title="İnsan devri aktif">👤</span>' : ''}</td>
      <td>${escapeHtml(resolveConversationIntent(item, []))}</td>
      <td>${escapeHtml((item.risk_flags || []).join(', ') || 'Yok')}</td>
      <td>${escapeHtml(item.message_count || 0)}</td>
      <td class="action-cell">
        <button class="inline-button primary" data-open-conversation="${escapeHtml(item.id)}">Detay</button>
        ${item.is_active ? `<button class="inline-button danger" data-deactivate-conversation="${escapeHtml(item.id)}">Pasife Al</button>` : '<span class="pill pill-closed">Pasif</span>'}
      </td>
    </tr>
  `).join('');
}

function syncConversationSelection() {
  const allowed = new Set((state.conversations || []).map(item => String(item.id)));
  for (const id of state.selectedConversationIds) {
    if (!allowed.has(id)) state.selectedConversationIds.delete(id);
  }
}

function updateConversationBulkBar() {
  const selectedCount = state.selectedConversationIds.size;
  const hasItems = (state.conversations || []).length > 0;
  if (refs.conversationBulkBar) refs.conversationBulkBar.hidden = !hasItems;
  if (refs.conversationSelectionCount) {
    refs.conversationSelectionCount.textContent = `${selectedCount} seçili · bu sayfa ${state.conversations.length} · filtre toplamı ${state.conversationsTotal || 0}`;
  }

  if (refs.conversationBulkBar) {
    const disableActions = selectedCount === 0;
    refs.conversationBulkBar.querySelectorAll('button[data-bulk-action]').forEach(button => {
      button.disabled = disableActions;
    });
  }

  if (refs.conversationSelectAll) {
    const total = (state.conversations || []).length;
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
      const row = input.closest('tr');
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
  const row = target.closest('tr');
  if (row) row.classList.toggle('is-selected', target.checked);
}

function onConversationSelectAllChange() {
  if (!refs.conversationSelectAll) return;
  const checked = refs.conversationSelectAll.checked;
  const items = state.conversations || [];
  items.forEach(item => {
    const convId = String(item.id);
    if (checked) state.selectedConversationIds.add(convId);
    else state.selectedConversationIds.delete(convId);
  });
  if (refs.conversationTableBody) {
    refs.conversationTableBody.querySelectorAll('[data-select-conversation]').forEach(input => {
      input.checked = checked;
      const row = input.closest('tr');
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
      const row = input.closest('tr');
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
  const audit = extractLatestUserAudit(response.messages || []);
  refs.conversationDetail.innerHTML = `
    <div class="module-header">
      <div>
        <h3>Konuşma Detayı</h3>
        <p>${escapeHtml(response.conversation.phone_display || 'Maskeli kullanıcı')} · ${escapeHtml(resolvedState)}</p>
      </div>
      <div class="inline-flex-center">
        <div class="badge dark">${escapeHtml(resolvedIntent)}</div>
        ${response.conversation.is_active ? `
          <button class="action-button ${response.conversation.human_override ? 'primary' : 'warn'} action-button-sm" data-toggle-human-override="${escapeHtml(String(response.conversation.id))}" data-current-override="${response.conversation.human_override ? 'true' : 'false'}" aria-label="İnsan devri / yapay zekâ modu değiştir">${response.conversation.human_override ? 'Yapay Zekâ Moduna Al' : 'İnsan Devrine Al'}</button>
          <button class="action-button danger action-button-sm" data-reset-conversation="${escapeHtml(String(response.conversation.id))}" aria-label="Seçili konuşmayı sıfırla">Sıfırla</button>
        ` : '<span class="pill pill-closed">Kapalı</span>'}
      </div>
    </div>
    ${renderUserAuditSection(audit)}
    <div class="timeline">
      ${(response.messages || []).map(message => `
        <article class="message ${escapeHtml(message.role || 'system')}">
          <header><strong>${escapeHtml(message.role || 'system')}</strong><span class="muted">${formatDate(message.created_at)}</span></header>
          <pre>${escapeHtml(message.content || '')}</pre>
          ${renderMessageAuditRow(message)}
        </article>
      `).join('')}
    </div>
  `;
  const overrideBtn = refs.conversationDetail.querySelector('[data-toggle-human-override]');
  if (overrideBtn) {
    overrideBtn.addEventListener('click', async () => {
      const convId = overrideBtn.dataset.toggleHumanOverride;
      const currentlyEnabled = overrideBtn.dataset.currentOverride === 'true';
      const newState = !currentlyEnabled;
      const confirmMsg = newState
        ? 'Bu konuşmayı İNSAN DEVRİNE almak istediğinize emin misiniz? Yapay zekâ yanıt üretmeye devam edecek ancak mesajlar WhatsApp üzerinden GÖNDERİLMEYECEK.'
        : 'Bu konuşmayı tekrar YAPAY ZEKÂ MODUNA almak istediğinize emin misiniz? Mesajlar otomatik olarak gönderilmeye başlanacak.';
      if (!confirm(confirmMsg)) return;
      try {
        await apiFetch(`/conversations/${convId}/human-override?enable=${newState}`, {method: 'POST'});
        notify(newState ? 'İnsan devri aktif — mesajlar gönderilmeyecek.' : 'Yapay zekâ modu aktif — mesajlar otomatik gönderilecek.', 'success');
        loadConversationDetail(convId);
        loadConversations();
      } catch (error) {
        notify(error.message, 'error');
      }
    });
  }
  const resetBtn = refs.conversationDetail.querySelector('[data-reset-conversation]');
  if (resetBtn) {
    resetBtn.addEventListener('click', async () => {
      if (!confirm('Bu konuşmayı sıfırlamak istediğinize emin misiniz? Kullanıcının bir sonraki mesajı yeni bir konuşma başlatacaktır.')) return;
      try {
        await apiFetch(`/conversations/${resetBtn.dataset.resetConversation}/reset`, {method: 'POST'});
        notify('Konuşma sıfırlandı.', 'success');
        loadConversations();
      } catch (error) {
        notify(error.message, 'error');
      }
    });
  }
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
      await apiFetch(`/holds/restaurant/${encodeURIComponent(holdId)}/status`, {method: 'PUT', body: {status: 'IPTAL', reason: reason || null}});
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
  ensureAccessControlSelection();
  const selectedUser = getAccessSelectedUser();
  if (selectedUser) {
    state.accessControlDraftPermissions = new Set(selectedUser.permissions || []);
  }
  renderAccessControl();
}

function ensureAccessControlSelection() {
  const roles = state.accessControlCatalog?.roles || [];
  if (!roles.length) {
    state.accessControlSelectedRole = '';
    state.accessControlSelectedUserId = 0;
    state.accessControlDraftPermissions = new Set();
    return;
  }
  if (!roles.some(item => String(item.code) === String(state.accessControlSelectedRole))) {
    state.accessControlSelectedRole = String(roles[0].code);
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
      title: 'Admin Kullanıcıları',
      value: users.length,
      note: `${users.filter(item => item.is_active).length} aktif hesap şu anda panele erişebilir`,
    },
    {
      title: '2FA Hazır',
      value: totpReadyCount,
      note: `${Math.max(users.length - totpReadyCount, 0)} hesap için yeni Authenticator kurulumu gerekebilir`,
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
    const selected = Number(user.user_id) === Number(state.accessControlSelectedUserId || 0);
    const overrideCount = Object.keys(user.permission_overrides || {}).length;
    const canEditRole = hasWritePermission && !isSelf;
    const roleHelpText = isSelf
      ? 'Giriş yaptığınız hesabın rolü güvenlik nedeniyle bu karttan değiştirilemez. Rol değişikliği için başka bir admin hesabı ile bu kullanıcıyı düzenleyin.'
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
              <span class="access-chip role">${escapeHtml(user.role_label || user.role)}</span>
              <span class="access-chip department">${escapeHtml(user.department_label || user.department_code || '-')}</span>
              <span class="access-chip security">${escapeHtml((user.permissions || []).length)} etkin izin</span>
              <span class="access-chip">${escapeHtml(overrideCount)} özel izin farkı</span>
              ${isSelf ? '<span class="access-chip self">Giriş yaptığınız hesap</span>' : ''}
            </div>
          </div>
          <div class="stack">
            <span class="pill ${user.is_active ? 'success' : 'closed'}">${escapeHtml(user.is_active ? 'Aktif' : 'Pasif')}</span>
            <span class="pill ${user.totp_enrolled ? 'info' : 'warn'}">${escapeHtml(user.totp_enrolled ? '2FA kayıtlı' : '2FA kurulacak')}</span>
          </div>
        </header>
        <div class="access-user-controls">
          <div class="field">
            <label for="accessDisplayName-${escapeHtml(user.user_id)}">Görünen ad</label>
            <input id="accessDisplayName-${escapeHtml(user.user_id)}" data-user-display="${escapeHtml(user.user_id)}" maxlength="100" value="${escapeHtml(user.display_name || '')}" ${!hasWritePermission ? 'disabled' : ''}>
          </div>
          <div class="field">
            <label for="accessPassword-${escapeHtml(user.user_id)}">Yeni geçici şifre</label>
            <input id="accessPassword-${escapeHtml(user.user_id)}" data-user-password="${escapeHtml(user.user_id)}" type="password" minlength="12" maxlength="72" placeholder="Boş bırakırsanız değişmez" ${!hasWritePermission ? 'disabled' : ''}>
          </div>
          <div class="field access-field-role">
            <label for="accessRole-${escapeHtml(user.user_id)}">Rol (Yetki şablonu)</label>
            <select id="accessRole-${escapeHtml(user.user_id)}" data-user-role="${escapeHtml(user.user_id)}" ${canEditRole ? '' : 'disabled'}>
              ${renderAccessRoleOptions(user.role)}
            </select>
            <small>${escapeHtml(roleHelpText)}</small>
          </div>
          <div class="field access-field-department">
            <label for="accessDepartment-${escapeHtml(user.user_id)}">Departman (Otel birimi)</label>
            <select id="accessDepartment-${escapeHtml(user.user_id)}" data-user-department="${escapeHtml(user.user_id)}" ${!hasWritePermission ? 'disabled' : ''}>
              ${renderAccessDepartmentOptions(user.department_code)}
            </select>
            <small>${escapeHtml(departmentHelpText)}</small>
          </div>
          <div class="field full access-toggle-grid">
            <label class="toggle-row" for="accessActive-${escapeHtml(user.user_id)}">
              <span class="toggle-copy">
                <strong>Hesap aktif</strong>
                <small>Pasif kullanıcı giriş yapamaz.</small>
              </span>
              <span class="switch">
                <input id="accessActive-${escapeHtml(user.user_id)}" data-user-active="${escapeHtml(user.user_id)}" type="checkbox" ${user.is_active ? 'checked' : ''} ${!hasWritePermission || isSelf ? 'disabled' : ''}>
                <span class="switch-track"><span class="switch-thumb"></span></span>
              </span>
            </label>
            <label class="toggle-row access-toggle-locked" for="accessTwoFactor-${escapeHtml(user.user_id)}">
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
          ${isSelf ? '<div class="field full"><div class="access-user-note">Bu kayıt şu an giriş yaptığınız admin hesabı. Güvenlik nedeniyle kendi rolünüzü, aktiflik durumunuzu ve izin kümenizi bu akıştan değiştiremezsiniz. Gerekirse departman, görünen ad veya şifreyi güncelleyin; rol değişikliği için önce ikinci bir admin hesabı oluşturup bu kullanıcıyı onunla düzenleyin.</div></div>' : ''}
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
  const user = getAccessSelectedUser();
  if (!user) {
    refs.accessResetPermissionsButton.disabled = true;
    refs.accessSavePermissionsButton.disabled = true;
    refs.accessPermissionMeta.innerHTML = '<div class="helper-box"><strong>Kullanıcı seçin</strong><p>İzin ağacını açmak için soldaki kartlardan bir kullanıcı seçin.</p></div>';
    refs.accessPermissionTree.innerHTML = '<div class="access-editor-empty"><h4>Henüz kullanıcı seçilmedi</h4><p>Bir kullanıcı seçtiğinizde pencere erişimleri ve işlem izinleri burada toggle menüsü ile açılır.</p></div>';
    return;
  }
  if (!(state.accessControlDraftPermissions instanceof Set)) {
    state.accessControlDraftPermissions = new Set(user.permissions || []);
  }
  const isSelf = Number(user.user_id) === Number(state.me?.user_id || 0);
  const roleDefaults = buildAccessRoleDefaultSet(user.role);
  const hasWritePermission = hasPermission('access_control:write');
  const canWrite = hasWritePermission && !isSelf;
  const overrideCount = Object.keys(user.permission_overrides || {}).length;
  refs.accessResetPermissionsButton.disabled = !canWrite;
  refs.accessSavePermissionsButton.disabled = !canWrite;
  const lockMessage = isSelf
    ? 'Bu kayıt şu an giriş yaptığınız admin hesabı. Güvenlik nedeniyle kendi rolünüz, aktifliğiniz ve izin kümeniz bu ekrandan değiştirilemez. Başka bir admin hesabı oluşturup bu kullanıcıyı onunla düzenleyin.'
    : !hasWritePermission
      ? 'Bu kullanıcı için izin değişikliği yapma yetkiniz bulunmuyor.'
      : '';
  refs.accessPermissionMeta.innerHTML = `
    <div class="helper-box">
      <strong>${escapeHtml(user.display_name || user.username)}</strong>
      <p>${escapeHtml(user.role_label || user.role)} rolündeki kullanıcının etkin izinleri düzenleniyor. Kaydedilen farklar rol varsayılanının üzerine kullanıcı bazlı override olarak işlenir.</p>
      <div class="access-summary-row">
        <span class="access-chip role">${escapeHtml((user.role_label || user.role))}</span>
        <span class="access-chip department">${escapeHtml(user.department_label || user.department_code || '-')}</span>
        <span class="access-chip security">${escapeHtml(state.accessControlDraftPermissions.size)} seçili izin</span>
        <span class="access-chip">${escapeHtml(overrideCount)} kayıtlı override</span>
      </div>
    </div>
    ${!canWrite ? `<div class="helper-box"><strong>Değişiklik kilitli</strong><p>${escapeHtml(lockMessage)}</p></div>` : ''}
  `;
  refs.accessPermissionTree.innerHTML = (state.accessControlCatalog?.permission_groups || []).map(group => {
    const items = Array.isArray(group.items) ? group.items : [];
    const activeCount = items.filter(item => state.accessControlDraftPermissions.has(item.key)).length;
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
          const enabled = state.accessControlDraftPermissions.has(item.key);
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
  if (refs.accessCreateRole) {
    refs.accessCreateRole.value = state.accessControlSelectedRole;
    syncAccessCreateDepartment(state.accessControlSelectedRole);
  }
  renderAccessRoleSummary();
  renderAccessRoleCards();
}

function onAccessCreateRoleChange() {
  state.accessControlSelectedRole = refs.accessCreateRole.value;
  syncAccessCreateDepartment(state.accessControlSelectedRole);
  renderAccessRoleSummary();
  renderAccessRoleCards();
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
    state.accessControlDraftPermissions = new Set(response.user?.permissions || []);
    refs.accessCreateUserForm.reset();
    refs.accessCreateActive.checked = true;
    refs.accessCreateTwoFactor.checked = true;
    refs.accessCreateRole.value = role.code;
    syncAccessCreateDepartment(role.code);
    showAccessTotpResult(response, 'Yeni kullanıcı için Authenticator kurulumu');
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
    state.accessControlSelectedUserId = userId;
    state.accessControlDraftPermissions = new Set(user.permissions || []);
    renderAccessUsersList();
    renderAccessPermissionEditor();
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
  if (!confirm(`${user.username} kullanıcısı için Authenticator kurulumunu yenilemek istiyor musunuz?`)) {
    return;
  }
  try {
    const response = await apiFetch(`/users/${encodeURIComponent(userId)}/rotate-totp`, {method: 'POST', body: {}});
    state.accessControlSelectedUserId = userId;
    state.accessControlDraftPermissions = new Set(response.user?.permissions || []);
    showAccessTotpResult(response, 'Authenticator kurulumu yenilendi');
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
