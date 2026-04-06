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
.nav-label span{font-size:11px;color:rgba(239,246,255,.62)}
.sidebar-card{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.08);border-radius:20px;padding:16px}
.sidebar-card h2{margin:0 0 8px;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:rgba(239,246,255,.62)}
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
.sidebar-button.danger,.action-button.danger{background:#fde7e5;color:var(--danger)}
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
.profile-overview-metrics span{display:inline-flex;align-items:center;padding:4px 8px;border-radius:999px;background:var(--surface-2);border:1px solid var(--line);font-size:11px;font-weight:700;color:var(--muted)}
.profile-overview-status{display:inline-flex;align-items:center;gap:8px;padding:4px 10px;border-radius:999px;font-size:11px;font-weight:800}
.profile-overview-status.complete{background:#ecfdf3;color:#166534}
.profile-overview-status.incomplete{background:#eef2f7;color:#475569}
.profile-overview-status.warning{background:#fff2dd;color:#92400e}
.profile-overview-status.blocker{background:#fde7e5;color:#991b1b}
.profile-section-badge{display:inline-flex;align-items:center;gap:6px;margin-left:8px;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:800}
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
.chatlab-frame{width:100%;height:calc(100vh - 80px);border:none;border-radius:12px}
.dialog-textarea{min-height:120px}
.inline-flex-center{display:flex;align-items:center;gap:8px}
.pill-closed{background:#e5e7eb;color:#6b7280;font-size:11px}
.pill-warning{display:inline-block;padding:2px 6px;border-radius:8px;font-size:11px;background:#fff4db;color:#7c4b06}
.action-button-sm{font-size:12px;padding:6px 14px}
@media(max-width:1240px){
  .card-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
  .split,.auth-grid{grid-template-columns:1fr}
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
  .field-grid,.dense-form,.status-list,.profile-section-grid,.profile-inline-grid,.profile-overview-grid{grid-template-columns:1fr}
  .topbar{padding:18px 20px;border-radius:24px;flex-direction:column}
  .card-grid{grid-template-columns:1fr}
  .status-strip{grid-template-columns:1fr}
  .hold-summary-grid{grid-template-columns:1fr}
}
"""

ADMIN_PANEL_SCRIPT = UI_SHARED_SCRIPT + """\
const CONFIG = window.ADMIN_PANEL_CONFIG || {};
const API_ROOT = '/api/v1/admin';
const READY_URL = '/api/v1/health/ready';
const HOTEL_KEY = 'velox.admin.hotel';
const CSRF_COOKIE = 'velox_admin_csrf';
const LIVE_REFRESH_INTERVAL_MS = 3000;

const state = {
  me: null,
  bootstrap: null,
  bootstrapPending: null,
  hotels: [],
  selectedHotelId: window.localStorage.getItem(HOTEL_KEY) || '',
  currentView: (window.location.hash || '#dashboard').replace('#', ''),
  dashboard: null,
  conversations: [],
  conversationsTotal: 0,
  conversationDetail: null,
  selectedConversationIds: new Set(),
  stayHolds: [],
  selectedStayHoldId: '',
  restaurantHolds: [],
  selectedRestaurantHoldId: '',
  restaurantDateFrom: '',
  restaurantDateTo: '',
  transferHolds: [],
  selectedTransferHoldId: '',
  activeHoldsTab: 'stay',
  stayStatusFilter: '',
  restaurantStatusFilter: '',
  restaurantMode: 'AI_RESTAURAN',
  transferStatusFilter: '',
  stayDraft: {},
  stayWizardStep: 1,
  stayWizardUseExisting: false,
  stayWizardReprocessHoldId: null,
  stayProfileRoomTypes: [],
  tickets: [],
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
    'ticketFilters','ticketTableBody','hotelProfileSelect','hotelProfileEditor','applyHotelProfileJson','saveHotelProfile',
    'faqFilters','faqTableBody','faqDetail',
    'notifPhoneTableBody','addNotifPhoneForm',
    'hotelProfileMeta','hotelProfileSections','hotelProfileSectionBody','hotelFactsConflict','hotelFactsStatus','hotelFactsHistory','hotelFactsEvents','hotelFactsVersionDetail','publishHotelFacts','slotFilters','slotDisplayInterval','slotTableBody','slotSummaryCards','slotCreateForm','slotDeleteForm','systemChecks','systemMeta',
    'sessionSummary','sessionPreferencesForm','sessionRememberToggle','sessionPreferenceFields',
    'systemVerificationOptions','systemSessionOptions','sessionOtpField','trustedDevicePanel','forgetDeviceButton',
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
    const resNo = new FormData(refs.stayHoldFilters).get('reservation_no');
    if (resNo && resNo.trim()) { lookupStayReservationNo(resNo.trim()); }
    else { loadStayHolds(); }
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
      // Re-obtain a fresh token and send it to the iframe
      await loadChatLab();
    }
    if (event.data && event.data.type === 'chatlab:faq-created') {
      if (state.currentView === 'faq') loadFaqs();
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
        await apiFetch(`/holds/${target.dataset.approveHold}/approve?force=true`, {method: 'POST', body: {notes: ''}});
        notify('Hold onaylandı.', 'success');
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
  await Promise.all([loadDashboard(), loadSystemOverview(), loadSessionPreferences()]);
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

function showAuth() {
  clearLiveRefresh();
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
  state.currentView = view;
  window.location.hash = view;
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
    system: ['Sistem Durumu', 'Sunucu sağlığı, alan adı ve güvenlik ayarlarını kontrol edin.'],
    chatlab: ['Test Paneli', 'Yapay zekâyı canlı test edin, puanlayın ve raporlayın.'],
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
  if (view === 'system') loadSystemOverview();
  if (view === 'chatlab') loadChatLab();
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

async function loadChatLab() {
  const frame = document.getElementById('chatlab-frame');
  if (!frame) return;
  // Obtain a fresh access token and pass it to the iframe via postMessage
  // because iframe fetch may not send httpOnly cookies reliably.
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
