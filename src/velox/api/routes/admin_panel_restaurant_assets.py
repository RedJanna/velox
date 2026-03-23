"""CSS and JS assets for the restaurant floor plan editor, daily view, and settings."""

# ruff: noqa: E501

ADMIN_RESTAURANT_STYLE = """
/* ── Floor plan workspace ───────────────────────────── */
.floor-plan-workspace{display:flex;gap:1rem;min-height:560px}
.floor-plan-toolbox{width:180px;flex-shrink:0;display:flex;flex-direction:column;gap:.35rem;padding:.75rem;background:var(--bg-2);border-radius:var(--radius);border:1px solid var(--border);max-height:620px;overflow-y:auto}
.toolbox-title{font-size:.65rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin:.6rem 0 .15rem;font-weight:700}
.toolbox-item{display:flex;align-items:center;gap:.5rem;padding:.45rem .6rem;border-radius:var(--radius);background:var(--bg-1);border:1px solid var(--border);cursor:grab;font-size:.78rem;transition:background .15s,border-color .15s}
.toolbox-item:hover{background:var(--accent-bg);border-color:var(--accent)}
.toolbox-item.active-tool{background:var(--accent);color:#fff;border-color:var(--accent)}
.toolbox-item[draggable]{user-select:none}

/* Toolbox mini previews */
.toolbox-preview{width:36px;height:36px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.toolbox-preview svg{width:100%;height:100%}

/* Toolbar buttons */
.fp-toolbar{display:flex;gap:.35rem;flex-wrap:wrap;margin-bottom:.5rem}
.fp-toolbar .fp-tool-btn{display:inline-flex;align-items:center;gap:.3rem;padding:.3rem .55rem;border-radius:var(--radius);background:var(--bg-2);border:1px solid var(--border);cursor:pointer;font-size:.72rem;color:var(--fg);transition:all .15s}
.fp-toolbar .fp-tool-btn:hover{background:var(--accent-bg);border-color:var(--accent)}
.fp-toolbar .fp-tool-btn.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.fp-toolbar .fp-tool-btn.danger{color:var(--danger,#ef4444)}
.fp-toolbar .fp-tool-btn.danger:hover{background:#fef2f2;border-color:var(--danger,#ef4444)}
.fp-toolbar .fp-sep{width:1px;height:22px;background:var(--border);margin:0 .15rem;align-self:center}

/* Canvas */
.floor-plan-canvas{flex:1;position:relative;background:var(--floor-base,var(--bg-1));background-image:var(--floor-texture,none);background-size:var(--floor-size,auto);background-position:center;border:2px dashed var(--border);border-radius:var(--radius);min-height:560px;overflow:hidden}
.floor-plan-canvas.show-grid{background-image:var(--floor-texture,none),radial-gradient(circle,var(--border,#d1cdc4) 1px,transparent 1px);background-size:var(--floor-size,auto),20px 20px;background-position:center,0 0}
.floor-plan-canvas.drag-over{border-color:var(--accent);background-color:var(--accent-bg)}
.floor-plan-canvas.click-place-mode{cursor:crosshair}
.floor-plan-canvas.floor-cream-marble-classic{--floor-base:#f4ecdf;--floor-texture:linear-gradient(135deg,rgba(255,255,255,.35),rgba(255,255,255,0) 38%),radial-gradient(circle at 18% 22%,rgba(201,179,150,.18) 0 2px,transparent 3px),radial-gradient(circle at 72% 68%,rgba(181,157,128,.14) 0 2px,transparent 3px),linear-gradient(115deg,transparent 0 28%,rgba(181,157,128,.16) 29% 31%,transparent 32% 58%,rgba(214,198,175,.18) 59% 61%,transparent 62% 100%),linear-gradient(25deg,transparent 0 18%,rgba(196,171,141,.12) 19% 20%,transparent 21% 100%);--floor-size:100% 100%,160px 160px,220px 220px,260px 260px,210px 210px}
.floor-plan-canvas.floor-cream-marble-warm{--floor-base:#efe2d2;--floor-texture:linear-gradient(140deg,rgba(255,255,255,.3),rgba(255,255,255,0) 42%),linear-gradient(90deg,transparent 0 22%,rgba(196,161,128,.16) 23% 24%,transparent 25% 55%,rgba(224,204,184,.22) 56% 58%,transparent 59% 100%),linear-gradient(25deg,transparent 0 35%,rgba(182,150,118,.14) 36% 37%,transparent 38% 100%),radial-gradient(circle at 24% 30%,rgba(255,248,240,.34) 0 20%,transparent 21% 100%);--floor-size:100% 100%,240px 240px,220px 220px,180px 180px}
.floor-plan-canvas.floor-cream-marble-soft{--floor-base:#f7f1e8;--floor-texture:linear-gradient(135deg,rgba(255,255,255,.42),rgba(255,255,255,0) 44%),linear-gradient(115deg,transparent 0 30%,rgba(221,209,191,.18) 31% 33%,transparent 34% 64%,rgba(205,188,167,.14) 65% 67%,transparent 68% 100%),linear-gradient(35deg,transparent 0 18%,rgba(188,172,153,.1) 19% 20%,transparent 21% 100%);--floor-size:100% 100%,280px 280px,220px 220px}
.fp-floor-select{min-width:220px;max-width:280px}

/* Snap guide lines */
.snap-guide{position:absolute;z-index:50;pointer-events:none}
.snap-guide.horizontal{left:0;right:0;height:1px;background:var(--accent);opacity:.5}
.snap-guide.vertical{top:0;bottom:0;width:1px;background:var(--accent);opacity:.5}

/* ── SVG-based canvas table elements ─────────────── */
.canvas-table{position:absolute;cursor:move;z-index:2;user-select:none;transition:filter .15s}
.canvas-table:hover{filter:brightness(1.08) drop-shadow(0 2px 6px rgba(0,0,0,.18))}
.canvas-table.selected{filter:drop-shadow(0 0 0 3px var(--accent)) drop-shadow(0 0 8px rgba(99,102,241,.4))}

/* Canvas table label */
.canvas-table .table-label{position:absolute;bottom:-16px;left:50%;transform:translateX(-50%);font-size:.65rem;font-weight:600;color:var(--fg);white-space:nowrap;pointer-events:none;text-shadow:0 1px 2px rgba(255,255,255,.8)}

/* Canvas table action buttons */
.canvas-table .table-actions,.canvas-shape .shape-actions{position:absolute;display:none;gap:2px;z-index:6}
.canvas-table .table-actions{top:-8px;right:-8px}
.canvas-shape .shape-actions{top:-30px;right:0}
.canvas-table:hover .table-actions,.canvas-shape:hover .shape-actions,.canvas-table.selected .table-actions,.canvas-shape.selected .shape-actions{display:flex}
.table-actions .tbl-act-btn,.shape-actions .shape-act-btn{width:18px;height:18px;border-radius:50%;border:none;font-size:.55rem;cursor:pointer;display:flex;align-items:center;justify-content:center;line-height:1;transition:transform .1s;pointer-events:auto}
.table-actions .tbl-act-btn:hover,.shape-actions .shape-act-btn:hover{transform:scale(1.15)}
.tbl-act-btn.del{background:var(--danger,#ef4444);color:#fff}
.tbl-act-btn.dup{background:#3b82f6;color:#fff}
.tbl-act-btn.rot{background:#8b5cf6;color:#fff}

/* Canvas shapes */
.canvas-shape{position:absolute;z-index:1;cursor:move;border-radius:2px;transform-origin:center center}
.canvas-shape.selected{outline:2px solid var(--accent);outline-offset:8px;z-index:3}
.canvas-shape .shape-body{position:absolute;inset:0}
.canvas-shape[data-shape="HORIZONTAL_DIVIDER"] .shape-body{background:var(--muted);height:3px;width:100%;top:50%;transform:translateY(-50%)}
.canvas-shape[data-shape="VERTICAL_DIVIDER"] .shape-body{background:var(--muted);width:3px;height:100%;left:50%;transform:translateX(-50%)}
.canvas-shape[data-shape="WALL"] .shape-body{background:#64748b;border-radius:2px}
.canvas-shape[data-shape="CURVED_WALL"] .shape-body{border:8px solid #64748b;border-right-color:transparent;border-bottom-color:transparent;border-radius:999px;background:transparent;box-sizing:border-box}
.canvas-shape[data-shape="TREE"] .shape-body{background:radial-gradient(circle at 35% 35%,#86efac 0 28%,#22c55e 28% 72%,#15803d 72% 100%);border-radius:50%;box-shadow:inset 0 -10px 0 rgba(21,128,61,.15)}
.canvas-shape[data-shape="TREE"]::after{content:'';position:absolute;left:50%;bottom:-8px;width:10px;height:16px;background:#92400e;border-radius:999px;transform:translateX(-50%)}
.canvas-shape[data-shape="BUSH"] .shape-body{background:radial-gradient(circle at 30% 30%,#bbf7d0 0 24%,#4ade80 24% 68%,#15803d 68% 100%);border-radius:999px}
.shape-actions .shape-act-btn:hover,.table-actions .tbl-act-btn:hover{transform:scale(1.15)}
.shape-act-btn.del{background:var(--danger,#ef4444);color:#fff}
.shape-act-btn.rot{background:#8b5cf6;color:#fff}
.shape-act-btn.edit{background:#0f766e;color:#fff}
.canvas-shape.shape-editing{outline-offset:10px;z-index:4}
.canvas-shape.shape-editing .shape-actions,.canvas-shape.shape-compact .shape-actions,.canvas-shape.shape-editing .shape-resize-handle,.canvas-shape.shape-compact .shape-resize-handle{display:flex}
.canvas-shape.shape-compact .shape-actions{top:calc(100% + 10px);right:auto;left:50%;transform:translateX(-50%)}
.shape-resize-handle{position:absolute;right:-14px;bottom:-14px;width:24px;height:24px;border-radius:999px;background:#fff;border:2px solid var(--accent);cursor:nwse-resize;display:none;align-items:center;justify-content:center;z-index:7;box-shadow:0 4px 12px rgba(15,23,42,.24);pointer-events:auto;touch-action:none}
.shape-resize-handle::before{content:'';position:absolute;inset:-10px;border-radius:999px}
.shape-resize-handle::after{content:'';width:10px;height:10px;border-radius:999px;background:var(--accent);box-shadow:0 0 0 2px #fff}
.canvas-shape:hover .shape-resize-handle,.canvas-shape.selected .shape-resize-handle{display:flex}
.canvas-shape[data-shape="HORIZONTAL_DIVIDER"] .shape-resize-handle,.canvas-shape[data-shape="VERTICAL_DIVIDER"] .shape-resize-handle,.canvas-shape[data-shape="WALL"] .shape-resize-handle{right:-12px;bottom:-12px}
.canvas-shape[data-shape="HORIZONTAL_DIVIDER"].shape-editing .shape-resize-handle,.canvas-shape[data-shape="WALL"].shape-editing .shape-resize-handle,.canvas-shape[data-shape="HORIZONTAL_DIVIDER"].shape-compact .shape-resize-handle,.canvas-shape[data-shape="WALL"].shape-compact .shape-resize-handle{right:-6px;bottom:50%;transform:translateY(50%)}
.canvas-shape[data-shape="VERTICAL_DIVIDER"].shape-editing .shape-resize-handle,.canvas-shape[data-shape="VERTICAL_DIVIDER"].shape-compact .shape-resize-handle{right:50%;bottom:-8px;transform:translateX(50%)}

/* Rotation transforms */
.canvas-table,.canvas-shape{transform:rotate(var(--rot,0deg))}

/* ── Daily view ───────────────────────────────────── */
.daily-view-canvas{min-height:400px}
.daily-view-canvas .canvas-table{cursor:pointer}

/* Status colors for daily view */
.canvas-table.st-BEKLEMEDE svg .table-surface{fill:#FEF3C7;stroke:#F59E0B}
.canvas-table.st-ONAYLANDI svg .table-surface{fill:#D1FAE5;stroke:#10B981}
.canvas-table.st-GELDI svg .table-surface{fill:#A7F3D0;stroke:#059669}
.canvas-table.st-GELMEDI svg .table-surface{fill:#FEE2E2;stroke:#EF4444}
.canvas-table.st-IPTAL svg .table-surface{fill:#E5E7EB;stroke:#6B7280}
.canvas-table.st-IPTAL .table-label{text-decoration:line-through}
.canvas-table.st-DEGISIKLIK_UYGULA svg .table-surface{fill:#EDE9FE;stroke:#8B5CF6}

/* Daily view guest info overlay */
.canvas-table .guest-overlay{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;pointer-events:none;font-size:.6rem;line-height:1.2;color:#1e293b;font-weight:500;max-width:90%}
.canvas-table .guest-overlay .guest-time{font-size:.55rem;color:#64748b}

/* ── Table detail dialog ──────────────────────────── */
.table-detail-dialog{border:none;border-radius:var(--radius);padding:0;width:min(440px,90vw);background:var(--bg-1);color:var(--fg);box-shadow:0 8px 30px rgba(0,0,0,.35)}
.table-detail-dialog::backdrop{background:rgba(0,0,0,.5)}
.dialog-header{display:flex;justify-content:space-between;align-items:center;padding:.8rem 1rem;border-bottom:1px solid var(--border)}
.dialog-header h3{margin:0;font-size:1rem}
.close-dialog-btn{background:none;border:none;font-size:1.4rem;cursor:pointer;color:var(--muted);padding:0 .3rem}
.dialog-body{padding:1rem;display:grid;grid-template-columns:1fr 1fr;gap:.75rem}
.dialog-body .field.full{grid-column:1/-1}
.dialog-body .readonly-info{grid-column:1/-1;font-size:.75rem;color:var(--muted);border-top:1px solid var(--border);padding-top:.5rem;display:flex;flex-direction:column;gap:.2rem}
.dialog-body .readonly-field{font-size:.85rem;color:var(--muted);padding:.3rem 0}
.dialog-footer{display:flex;justify-content:flex-end;gap:.5rem;padding:.8rem 1rem;border-top:1px solid var(--border)}
.inline-button.danger{background:var(--danger,#ef4444);color:#fff}

/* ── Toggle switch ──────────────────────────────── */
.toggle-switch{position:relative;display:inline-block;width:42px;height:22px}
.toggle-switch input{opacity:0;width:0;height:0}
.toggle-slider{position:absolute;cursor:pointer;inset:0;background:var(--border);border-radius:22px;transition:.2s}
.toggle-slider::before{content:'';position:absolute;height:16px;width:16px;left:3px;bottom:3px;background:#fff;border-radius:50%;transition:.2s}
.toggle-switch input:checked+.toggle-slider{background:var(--accent)}
.toggle-switch input:checked+.toggle-slider::before{transform:translateX(20px)}

/* ── Slot summary / capacity graph ───────────────── */
#slotSummaryCards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:.75rem;margin:.75rem 0 1rem}
.slot-summary-card{background:var(--bg-2);border:1px solid var(--border);border-radius:var(--radius);padding:.85rem}
.slot-summary-card h4{margin:0 0 .35rem;font-size:.85rem}
.slot-summary-value{font-size:1.35rem;font-weight:700;margin-bottom:.3rem}
.slot-summary-meta{font-size:.75rem;color:var(--muted)}
.slot-progress{height:10px;background:rgba(148,163,184,.18);border-radius:999px;overflow:hidden;margin:.55rem 0 .4rem}
.slot-progress-bar{height:100%;border-radius:999px;background:linear-gradient(90deg,#22c55e,#f59e0b,#ef4444)}
.slot-chip-row{display:flex;flex-wrap:wrap;gap:.4rem;margin-top:.45rem}
.slot-chip{display:inline-flex;align-items:center;gap:.25rem;border-radius:999px;padding:.18rem .5rem;font-size:.72rem;background:var(--bg-1);border:1px solid var(--border)}

/* ── Service mode ───────────────────────────────────── */
.service-mode-dialog{border:none;width:100vw;height:100vh;max-width:none;max-height:none;padding:0;background:var(--bg-0,#0f172a);color:var(--fg,#f8fafc)}
.service-mode-dialog::backdrop{background:rgba(2,6,23,.72)}
.service-mode-shell{height:100vh;display:flex;flex-direction:column;padding:12px;gap:10px}
.service-mode-header{display:flex;justify-content:space-between;align-items:center;gap:12px}
.service-mode-header h3{margin:0;font-size:1.1rem}
.service-mode-header p{margin:.2rem 0 0;font-size:.8rem;color:var(--muted)}
.service-mode-actions{display:flex;gap:8px;align-items:center}
.service-mode-toolbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.service-mode-shortcuts{display:flex;gap:8px;flex-wrap:wrap;font-size:.72rem;color:var(--muted)}
.service-shortcut-chip{border:1px solid var(--border);border-radius:999px;padding:.12rem .5rem;background:var(--bg-2)}
.service-mode-body{display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:10px;min-height:0;flex:1}
.service-mode-canvas-wrap{background:var(--bg-2);border:1px solid var(--border);border-radius:var(--radius);padding:8px;min-height:0}
.service-mode-canvas{height:100%;min-height:560px;overflow:auto;touch-action:manipulation}
.service-mode-side{display:flex;flex-direction:column;gap:10px;min-height:0;overflow:auto}
.service-list{display:flex;flex-direction:column;gap:6px;max-height:220px;overflow:auto}
.service-reservation-card{background:var(--bg-2);border:1px solid var(--border);border-radius:var(--radius);padding:.7rem;cursor:grab;touch-action:none}
.service-reservation-card small{display:block;color:var(--muted)}
.service-table-drop{outline:2px dashed var(--accent);outline-offset:6px}
.service-shape-locked{pointer-events:none;opacity:.72;filter:saturate(.7)}

@media(max-width:980px){
  .floor-plan-workspace{flex-direction:column}
  .floor-plan-toolbox{width:100%;flex-direction:row;flex-wrap:wrap;min-height:auto;max-height:none}
  .fp-toolbar{justify-content:center}
  .service-mode-shell{padding:8px}
  .service-mode-actions .inline-button,.service-mode-toolbar .filter-chip{min-height:42px;padding:.45rem .8rem}
  .service-mode-body{grid-template-columns:1fr;grid-template-rows:minmax(0,1fr) auto}
  .service-mode-side{max-height:45vh}
}
"""

ADMIN_RESTAURANT_SCRIPT = """
/* ═══════════════════════════════════════════════════════
   Restaurant Floor Plan Editor, Daily View, Settings
   — Realistic SVG tables with chairs, advanced tools
   ═══════════════════════════════════════════════════════ */
(function(){
'use strict';

const GRID = 20;
const FLOOR_THEMES = {
  CREAM_MARBLE_CLASSIC: 'floor-cream-marble-classic',
  CREAM_MARBLE_WARM: 'floor-cream-marble-warm',
  CREAM_MARBLE_SOFT: 'floor-cream-marble-soft'
};
const DEFAULT_FLOOR_THEME = 'CREAM_MARBLE_CLASSIC';
let fpState = {tables:[],shapes:[],planId:null,counter:0,floorTheme:DEFAULT_FLOOR_THEME};
let selectedEl = null;
let activeShapeEditId = null;
let undoStack = [];
const MAX_UNDO = 30;
let clickPlaceMode = null; // null or {type, capacity} or {shape}
let showGrid = true;

/* ── SVG Table Generators ────────────────────── */

function chairCircle(cx, cy){
  return '<circle cx="'+cx+'" cy="'+cy+'" r="5" fill="#78716c" stroke="#57534e" stroke-width="1"/>';
}

function svgTable2(w,h){
  // Round 2-person bistro table
  w=w||52; h=h||52;
  var cx=w/2, cy=h/2;
  var svg = '<svg xmlns="http://www.w3.org/2000/svg" width="'+w+'" height="'+h+'" viewBox="0 0 '+w+' '+h+'">';
  // Chairs: top and bottom
  svg += chairCircle(cx, 4);
  svg += chairCircle(cx, h-4);
  // Table surface (circle)
  svg += '<circle class="table-surface" cx="'+cx+'" cy="'+cy+'" r="14" fill="#d4a574" stroke="#92400e" stroke-width="2"/>';
  // Table highlight
  svg += '<circle cx="'+cx+'" cy="'+cy+'" r="10" fill="none" stroke="#e8c89e" stroke-width="0.5" opacity="0.5"/>';
  svg += '</svg>';
  return {svg:svg, w:w, h:h};
}

function svgTable4(w,h){
  w=w||72; h=h||72;
  var cx=w/2, cy=h/2, tw=24, th=24;
  var svg = '<svg xmlns="http://www.w3.org/2000/svg" width="'+w+'" height="'+h+'" viewBox="0 0 '+w+' '+h+'">';
  // 4 chairs: top, bottom, left, right
  svg += chairCircle(cx, 5);
  svg += chairCircle(cx, h-5);
  svg += chairCircle(5, cy);
  svg += chairCircle(w-5, cy);
  // Table surface (rounded rect)
  svg += '<rect class="table-surface" x="'+(cx-tw/2)+'" y="'+(cy-th/2)+'" width="'+tw+'" height="'+th+'" rx="4" fill="#d4a574" stroke="#92400e" stroke-width="2"/>';
  svg += '<rect x="'+(cx-tw/2+3)+'" y="'+(cy-th/2+3)+'" width="'+(tw-6)+'" height="'+(th-6)+'" rx="2" fill="none" stroke="#e8c89e" stroke-width="0.5" opacity="0.5"/>';
  svg += '</svg>';
  return {svg:svg, w:w, h:h};
}

function svgTable6(w,h){
  w=w||110; h=h||72;
  var cx=w/2, cy=h/2, tw=60, th=26;
  var svg = '<svg xmlns="http://www.w3.org/2000/svg" width="'+w+'" height="'+h+'" viewBox="0 0 '+w+' '+h+'">';
  // 6 chairs: 3 top, 3 bottom
  svg += chairCircle(cx-20, 5);
  svg += chairCircle(cx, 5);
  svg += chairCircle(cx+20, 5);
  svg += chairCircle(cx-20, h-5);
  svg += chairCircle(cx, h-5);
  svg += chairCircle(cx+20, h-5);
  // Table surface (rounded rect)
  svg += '<rect class="table-surface" x="'+(cx-tw/2)+'" y="'+(cy-th/2)+'" width="'+tw+'" height="'+th+'" rx="5" fill="#d4a574" stroke="#92400e" stroke-width="2"/>';
  svg += '<rect x="'+(cx-tw/2+3)+'" y="'+(cy-th/2+3)+'" width="'+(tw-6)+'" height="'+(th-6)+'" rx="3" fill="none" stroke="#e8c89e" stroke-width="0.5" opacity="0.5"/>';
  svg += '</svg>';
  return {svg:svg, w:w, h:h};
}

function svgTable8(w,h){
  w=w||130; h=h||80;
  var cx=w/2, cy=h/2, tw=76, th=30;
  var svg = '<svg xmlns="http://www.w3.org/2000/svg" width="'+w+'" height="'+h+'" viewBox="0 0 '+w+' '+h+'">';
  // 8 chairs: 3 top, 3 bottom, 1 left, 1 right
  svg += chairCircle(cx-22, 5);
  svg += chairCircle(cx, 5);
  svg += chairCircle(cx+22, 5);
  svg += chairCircle(cx-22, h-5);
  svg += chairCircle(cx, h-5);
  svg += chairCircle(cx+22, h-5);
  svg += chairCircle(8, cy);
  svg += chairCircle(w-8, cy);
  // Table surface
  svg += '<rect class="table-surface" x="'+(cx-tw/2)+'" y="'+(cy-th/2)+'" width="'+tw+'" height="'+th+'" rx="6" fill="#d4a574" stroke="#92400e" stroke-width="2"/>';
  svg += '<rect x="'+(cx-tw/2+3)+'" y="'+(cy-th/2+3)+'" width="'+(tw-6)+'" height="'+(th-6)+'" rx="4" fill="none" stroke="#e8c89e" stroke-width="0.5" opacity="0.5"/>';
  svg += '</svg>';
  return {svg:svg, w:w, h:h};
}

function svgTable10(w,h){
  w=w||156; h=h||84;
  var cx=w/2, cy=h/2, tw=96, th=32;
  var svg = '<svg xmlns="http://www.w3.org/2000/svg" width="'+w+'" height="'+h+'" viewBox="0 0 '+w+' '+h+'">';
  // 10 chairs: 4 top, 4 bottom, 1 left, 1 right
  svg += chairCircle(cx-30, 5);
  svg += chairCircle(cx-10, 5);
  svg += chairCircle(cx+10, 5);
  svg += chairCircle(cx+30, 5);
  svg += chairCircle(cx-30, h-5);
  svg += chairCircle(cx-10, h-5);
  svg += chairCircle(cx+10, h-5);
  svg += chairCircle(cx+30, h-5);
  svg += chairCircle(8, cy);
  svg += chairCircle(w-8, cy);
  // Table surface
  svg += '<rect class="table-surface" x="'+(cx-tw/2)+'" y="'+(cy-th/2)+'" width="'+tw+'" height="'+th+'" rx="6" fill="#d4a574" stroke="#92400e" stroke-width="2"/>';
  svg += '<rect x="'+(cx-tw/2+3)+'" y="'+(cy-th/2+3)+'" width="'+(tw-6)+'" height="'+(th-6)+'" rx="4" fill="none" stroke="#e8c89e" stroke-width="0.5" opacity="0.5"/>';
  svg += '</svg>';
  return {svg:svg, w:w, h:h};
}

var TABLE_SVG_MAP = {
  TABLE_2: svgTable2,
  TABLE_4: svgTable4,
  TABLE_6: svgTable6,
  TABLE_8: svgTable8,
  TABLE_10: svgTable10
};

var TABLE_DIMS = {
  TABLE_2: {w:52,h:52},
  TABLE_4: {w:72,h:72},
  TABLE_6: {w:110,h:72},
  TABLE_8: {w:130,h:80},
  TABLE_10: {w:156,h:84}
};

function getTableSvg(type){
  var fn = TABLE_SVG_MAP[type];
  if(!fn) return {svg:'<div style="width:50px;height:50px;background:#ccc;border-radius:6px"></div>',w:50,h:50};
  var dims = TABLE_DIMS[type] || {w:72,h:72};
  return fn(dims.w, dims.h);
}

/* Mini preview SVGs for toolbox */
function miniSvg2(){
  return '<svg viewBox="0 0 36 36"><circle cx="18" cy="3" r="3" fill="#78716c"/><circle cx="18" cy="33" r="3" fill="#78716c"/><circle cx="18" cy="18" r="10" fill="#d4a574" stroke="#92400e" stroke-width="1.5"/></svg>';
}
function miniSvg4(){
  return '<svg viewBox="0 0 36 36"><circle cx="18" cy="3" r="3" fill="#78716c"/><circle cx="18" cy="33" r="3" fill="#78716c"/><circle cx="3" cy="18" r="3" fill="#78716c"/><circle cx="33" cy="18" r="3" fill="#78716c"/><rect x="10" y="10" width="16" height="16" rx="3" fill="#d4a574" stroke="#92400e" stroke-width="1.5"/></svg>';
}
function miniSvg6(){
  return '<svg viewBox="0 0 44 36"><circle cx="12" cy="3" r="3" fill="#78716c"/><circle cx="22" cy="3" r="3" fill="#78716c"/><circle cx="32" cy="3" r="3" fill="#78716c"/><circle cx="12" cy="33" r="3" fill="#78716c"/><circle cx="22" cy="33" r="3" fill="#78716c"/><circle cx="32" cy="33" r="3" fill="#78716c"/><rect x="6" y="10" width="32" height="16" rx="4" fill="#d4a574" stroke="#92400e" stroke-width="1.5"/></svg>';
}
function miniSvg8(){
  return '<svg viewBox="0 0 48 36"><circle cx="12" cy="3" r="2.5" fill="#78716c"/><circle cx="24" cy="3" r="2.5" fill="#78716c"/><circle cx="36" cy="3" r="2.5" fill="#78716c"/><circle cx="12" cy="33" r="2.5" fill="#78716c"/><circle cx="24" cy="33" r="2.5" fill="#78716c"/><circle cx="36" cy="33" r="2.5" fill="#78716c"/><circle cx="3" cy="18" r="2.5" fill="#78716c"/><circle cx="45" cy="18" r="2.5" fill="#78716c"/><rect x="8" y="9" width="32" height="18" rx="4" fill="#d4a574" stroke="#92400e" stroke-width="1.5"/></svg>';
}
function miniSvg10(){
  return '<svg viewBox="0 0 52 36"><circle cx="10" cy="3" r="2.5" fill="#78716c"/><circle cx="20" cy="3" r="2.5" fill="#78716c"/><circle cx="30" cy="3" r="2.5" fill="#78716c"/><circle cx="40" cy="3" r="2.5" fill="#78716c"/><circle cx="10" cy="33" r="2.5" fill="#78716c"/><circle cx="20" cy="33" r="2.5" fill="#78716c"/><circle cx="30" cy="33" r="2.5" fill="#78716c"/><circle cx="40" cy="33" r="2.5" fill="#78716c"/><circle cx="3" cy="18" r="2.5" fill="#78716c"/><circle cx="49" cy="18" r="2.5" fill="#78716c"/><rect x="7" y="9" width="38" height="18" rx="4" fill="#d4a574" stroke="#92400e" stroke-width="1.5"/></svg>';
}

/* ── Helpers ──────────────────────────────── */

function snap(v){ return Math.round(v/GRID)*GRID; }
function nextId(prefix){ fpState.counter++; return prefix + fpState.counter; }
function normalizeTableId(raw){ return String(raw || '').trim().toUpperCase(); }
function hasTableId(tableId, excludeId){
  var wanted = normalizeTableId(tableId);
  return fpState.tables.some(function(item){
    if(excludeId && item.table_id === excludeId) return false;
    return normalizeTableId(item.table_id) === wanted;
  });
}
function askTableId(defaultValue, excludeId){
  var fallback = normalizeTableId(defaultValue || '');
  while(true){
    var input = window.prompt('Masa numarasi zorunlu. Ornek: A1, 12, H-07', fallback);
    if(input === null) return null;
    var candidate = normalizeTableId(input);
    if(!candidate){
      notify('Masa numarasi bos birakilamaz.', 'warn');
      fallback = candidate;
      continue;
    }
    if(hasTableId(candidate, excludeId)){
      notify('Bu masa numarasi zaten kullaniliyor.', 'warn');
      fallback = candidate;
      continue;
    }
    return candidate;
  }
}
function getRotation(item){ return parseInt(item.rotation || 0, 10) || 0; }
function getNormalizedRotation(item){
  var raw = getRotation(item) % 360;
  return raw < 0 ? raw + 360 : raw;
}
function clampSize(value, min, max){ return Math.max(min, Math.min(max, snap(value))); }
function isWallShape(type){ return type === 'WALL' || type === 'CURVED_WALL'; }
function applyFloorTheme(themeKey){
  var canvas = document.getElementById('floorPlanCanvas');
  if(!canvas) return;
  Object.keys(FLOOR_THEMES).forEach(function(key){ canvas.classList.remove(FLOOR_THEMES[key]); });
  var resolved = FLOOR_THEMES[themeKey] ? themeKey : DEFAULT_FLOOR_THEME;
  canvas.classList.add(FLOOR_THEMES[resolved]);
  fpState.floorTheme = resolved;
  var select = document.getElementById('fpFloorTheme');
  if(select && select.value !== resolved) select.value = resolved;
}
function getShapeDefaults(type){
  switch(type){
    case 'HORIZONTAL_DIVIDER': return {width:120,height:12};
    case 'VERTICAL_DIVIDER': return {width:12,height:120};
    case 'WALL': return {width:160,height:12};
    case 'CURVED_WALL': return {width:120,height:120};
    case 'TREE': return {width:56,height:56};
    case 'BUSH': return {width:72,height:44};
    default: return {width:40,height:40};
  }
}

function pushUndo(){
  undoStack.push(JSON.stringify({tables:fpState.tables,shapes:fpState.shapes}));
  if(undoStack.length > MAX_UNDO) undoStack.shift();
}

function popUndo(){
  if(undoStack.length === 0) return false;
  var snap = JSON.parse(undoStack.pop());
  fpState.tables = snap.tables;
  fpState.shapes = snap.shapes;
  rerenderCanvas();
  return true;
}

function rerenderCanvas(){
  var canvas = document.getElementById('floorPlanCanvas');
  if(!canvas) return;
  selectedEl = null;
  // Keep only non-table/shape children (like snap guides)
  canvas.querySelectorAll('.canvas-table,.canvas-shape').forEach(function(el){el.remove();});
  fpState.tables.forEach(function(t){ renderCanvasTable(canvas,t); });
  fpState.shapes.forEach(function(s){ renderCanvasShape(canvas,s); });
}

function setSelectedElement(nextEl){
  if(selectedEl && selectedEl !== nextEl) selectedEl.classList.remove('selected');
  selectedEl = nextEl || null;
  if(selectedEl) selectedEl.classList.add('selected');
}

function isCompactShape(shape){
  var width = shape.width || 0;
  var height = shape.height || 0;
  return width <= 72 || height <= 40 || Math.min(width, height) <= 32;
}

function syncShapeEditState(el, shape){
  if(!el || !shape) return;
  var isEditing = activeShapeEditId === shape.shape_id;
  var compact = isCompactShape(shape);
  el.classList.toggle('shape-editing', isEditing);
  el.classList.toggle('shape-compact', compact);
  var editBtn = el.querySelector('.shape-act-btn.edit');
  if(editBtn){
    editBtn.classList.toggle('active', isEditing);
    editBtn.setAttribute('aria-pressed', isEditing ? 'true' : 'false');
    editBtn.setAttribute('title', isEditing ? 'Sekil duzenlemeyi kapat' : 'Sekil duzenle');
  }
  var resizeHandle = el.querySelector('.shape-resize-handle');
  if(resizeHandle){
    resizeHandle.setAttribute('aria-hidden', isEditing || compact ? 'false' : 'true');
  }
}

function setActiveShapeEdit(shapeId){
  activeShapeEditId = shapeId || null;
  document.querySelectorAll('.canvas-shape').forEach(function(node){
    var shape = fpState.shapes.find(function(item){ return item.shape_id === node.dataset.shapeId; });
    if(shape) syncShapeEditState(node, shape);
  });
}

/* ── Floor Plan Editor ────────────────────── */

function initFloorPlanEditor(){
  var canvas = document.getElementById('floorPlanCanvas');
  var toolbox = document.getElementById('floorPlanToolbox');
  if(!canvas||!toolbox) return;

  // Show grid by default
  if(showGrid) canvas.classList.add('show-grid');
  applyFloorTheme(fpState.floorTheme || DEFAULT_FLOOR_THEME);

  // Drag from toolbox
  toolbox.addEventListener('dragstart', function(e){
    var item = e.target.closest('.toolbox-item');
    if(!item) return;
    var tt = item.dataset.tableType;
    var st = item.dataset.shapeType;
    if(tt) e.dataTransfer.setData('text/plain', JSON.stringify({action:'add_table',type:tt,capacity:parseInt(item.dataset.capacity,10)}));
    else if(st) e.dataTransfer.setData('text/plain', JSON.stringify({action:'add_shape',type:st}));
  });

  canvas.addEventListener('dragover', function(e){ e.preventDefault(); canvas.classList.add('drag-over'); });
  canvas.addEventListener('dragleave', function(){ canvas.classList.remove('drag-over'); });

  canvas.addEventListener('drop', function(e){
    e.preventDefault();
    canvas.classList.remove('drag-over');
    var data;
    try{ data = JSON.parse(e.dataTransfer.getData('text/plain')); }catch{ return; }
    var rect = canvas.getBoundingClientRect();
    var x = snap(e.clientX - rect.left);
    var y = snap(e.clientY - rect.top);
    placeItem(data, x, y);
  });

  // Click-to-place on canvas
  canvas.addEventListener('click', function(e){
    if(!clickPlaceMode) return;
    if(e.target.closest('.canvas-table') || e.target.closest('.canvas-shape')) return;
    var rect = canvas.getBoundingClientRect();
    var x = snap(e.clientX - rect.left);
    var y = snap(e.clientY - rect.top);
    placeItem(clickPlaceMode, x, y);
  });

  canvas.addEventListener('pointerdown', function(e){
    if(e.target === canvas) setSelectedElement(null);
  });

  // Keyboard shortcuts
  document.addEventListener('keydown', function(e){
    if(e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;
    if(e.key === 'Escape'){
      exitClickPlaceMode();
    }
    if((e.ctrlKey || e.metaKey) && e.key === 'z'){
      e.preventDefault();
      popUndo();
    }
  });

  // Save & Reset buttons
  var saveBtn = document.getElementById('saveFloorPlanBtn');
  if(saveBtn) saveBtn.addEventListener('click', saveFloorPlan);
  var resetBtn = document.getElementById('resetFloorPlanBtn');
  if(resetBtn) resetBtn.addEventListener('click', loadFloorPlan);

  // Toolbar buttons
  var undoBtn = document.getElementById('fpUndoBtn');
  if(undoBtn) undoBtn.addEventListener('click', function(){ popUndo(); });

  var gridBtn = document.getElementById('fpGridBtn');
  if(gridBtn) gridBtn.addEventListener('click', function(){
    showGrid = !showGrid;
    canvas.classList.toggle('show-grid', showGrid);
    gridBtn.classList.toggle('active', showGrid);
  });

  var clearBtn = document.getElementById('fpClearBtn');
  if(clearBtn) clearBtn.addEventListener('click', function(){
    if(!confirm('Tum masalari ve sekilleri silmek istediginizden emin misiniz?')) return;
    pushUndo();
    fpState.tables = [];
    fpState.shapes = [];
    rerenderCanvas();
  });

  var floorThemeSelect = document.getElementById('fpFloorTheme');
  if(floorThemeSelect){
    floorThemeSelect.value = fpState.floorTheme || DEFAULT_FLOOR_THEME;
    floorThemeSelect.addEventListener('change', function(){
      pushUndo();
      applyFloorTheme(floorThemeSelect.value || DEFAULT_FLOOR_THEME);
    });
  }

  // Make toolbox items clickable for click-to-place mode
  toolbox.querySelectorAll('.toolbox-item').forEach(function(item){
    item.addEventListener('click', function(e){
      // Don't activate click-place if user is starting a drag
      if(e.detail === 0) return; // programmatic
      var tt = item.dataset.tableType;
      var st = item.dataset.shapeType;
      if(tt){
        setClickPlaceMode({action:'add_table',type:tt,capacity:parseInt(item.dataset.capacity,10)}, item);
      } else if(st){
        setClickPlaceMode({action:'add_shape',type:st}, item);
      }
    });
  });

  loadFloorPlan();
}

function setClickPlaceMode(data, activeItem){
  var canvas = document.getElementById('floorPlanCanvas');
  var toolbox = document.getElementById('floorPlanToolbox');
  // Toggle off if same tool clicked again
  if(clickPlaceMode && clickPlaceMode.type === data.type && clickPlaceMode.action === data.action){
    exitClickPlaceMode();
    return;
  }
  clickPlaceMode = data;
  if(canvas) canvas.classList.add('click-place-mode');
  toolbox.querySelectorAll('.toolbox-item').forEach(function(i){ i.classList.remove('active-tool'); });
  if(activeItem) activeItem.classList.add('active-tool');
}

function exitClickPlaceMode(){
  clickPlaceMode = null;
  var canvas = document.getElementById('floorPlanCanvas');
  if(canvas) canvas.classList.remove('click-place-mode');
  var toolbox = document.getElementById('floorPlanToolbox');
  if(toolbox) toolbox.querySelectorAll('.toolbox-item').forEach(function(i){ i.classList.remove('active-tool'); });
}

function placeItem(data, x, y){
  var canvas = document.getElementById('floorPlanCanvas');
  if(!canvas) return;
  pushUndo();

  if(data.action === 'add_table'){
    var dims = TABLE_DIMS[data.type] || {w:72,h:72};
    // Center on click point
    x = snap(Math.max(0, x - dims.w/2));
    y = snap(Math.max(0, y - dims.h/2));
    var suggestedId = nextId('T' + data.capacity + '-');
    var tableId = askTableId(suggestedId);
    if(!tableId) return;
    var t = {table_id:tableId,type:data.type,capacity:data.capacity,x:x,y:y,rotation:0,label:tableId};
    fpState.tables.push(t);
    renderCanvasTable(canvas,t);
  } else if(data.action === 'add_shape'){
    var shapeId = nextId('S-');
    var dims = getShapeDefaults(data.type);
    var s = {shape_id:shapeId,type:data.type,x:x,y:y,width:dims.width,height:dims.height,rotation:0};
    fpState.shapes.push(s);
    renderCanvasShape(canvas,s);
  }
}

function renderCanvasTable(canvas, t){
  var svgData = getTableSvg(t.type);
  var el = document.createElement('div');
  el.className = 'canvas-table';
  el.dataset.type = t.type;
  el.dataset.tableId = t.table_id;
  el.dataset.rot = getRotation(t);
  el.style.setProperty('--rot', getRotation(t) + 'deg');
  el.style.left = t.x + 'px';
  el.style.top = t.y + 'px';
  el.style.width = svgData.w + 'px';
  el.style.height = svgData.h + 'px';

  var html = svgData.svg;
  html += '<span class="table-label">' + escapeHtml(t.label||t.table_id) + '</span>';
  html += '<div class="table-actions">';
  html += '<button class="tbl-act-btn rot" title="Dondur" aria-label="Dondur">&#x21BB;</button>';
  html += '<button class="tbl-act-btn dup" title="Kopyala" aria-label="Kopyala">&#x2398;</button>';
  html += '<button class="tbl-act-btn del" title="Sil" aria-label="Sil">&times;</button>';
  html += '</div>';
  el.innerHTML = html;

  makeDraggable(el, canvas, function(nx,ny){
    t.x = nx; t.y = ny;
  });
  el.addEventListener('pointerdown', function(){
    setSelectedElement(el);
  });

  // Delete
  el.querySelector('.tbl-act-btn.del').addEventListener('click', function(ev){
    ev.stopPropagation();
    pushUndo();
    fpState.tables = fpState.tables.filter(function(tt){return tt.table_id !== t.table_id;});
    el.remove();
  });

  // Duplicate
  el.querySelector('.tbl-act-btn.dup').addEventListener('click', function(ev){
    ev.stopPropagation();
    var suggestedId = nextId('T' + t.capacity + '-');
    var newId = askTableId(suggestedId);
    if(!newId) return;
    pushUndo();
    var nt = {table_id:newId,type:t.type,capacity:t.capacity,x:t.x+GRID*2,y:t.y+GRID*2,rotation:t.rotation||0,label:newId};
    fpState.tables.push(nt);
    renderCanvasTable(canvas,nt);
  });

  // Rotate
  el.querySelector('.tbl-act-btn.rot').addEventListener('click', function(ev){
    ev.stopPropagation();
    pushUndo();
    var r = (getRotation(t) + 90) % 360;
    t.rotation = r;
    el.dataset.rot = r;
    el.style.setProperty('--rot', r + 'deg');
  });

  canvas.appendChild(el);
}

function renderCanvasShape(canvas, s){
  if(typeof s.rotation === 'undefined') s.rotation = 0;
  var el = document.createElement('div');
  el.className = 'canvas-shape';
  el.dataset.shape = s.type;
  el.dataset.shapeId = s.shape_id;
  el.style.left = s.x + 'px';
  el.style.top = s.y + 'px';
  el.style.width = s.width + 'px';
  el.style.height = s.height + 'px';
  el.style.setProperty('--rot', getRotation(s) + 'deg');
  el.innerHTML = '<div class="shape-body" aria-hidden="true"></div><div class="shape-actions"><button class="shape-act-btn edit" title="Sekil duzenle" aria-label="Sekil duzenle" aria-pressed="false">&#x25C8;</button><button class="shape-act-btn rot" title="Dondur" aria-label="Dondur">&#x21BB;</button><button class="shape-act-btn del" title="Sil" aria-label="Sil">&times;</button></div><button class="shape-resize-handle" type="button" aria-label="Boyutlandir"></button>';
  makeDraggable(el, canvas, function(nx,ny){
    s.x = nx; s.y = ny;
  });
  el.addEventListener('pointerdown', function(){
    setSelectedElement(el);
  });
  el.querySelector('.shape-act-btn.edit').addEventListener('click', function(ev){
    ev.stopPropagation();
    setSelectedElement(el);
    setActiveShapeEdit(activeShapeEditId === s.shape_id ? null : s.shape_id);
  });
  el.querySelector('.shape-act-btn.del').addEventListener('click', function(ev){
    ev.stopPropagation();
    pushUndo();
    fpState.shapes = fpState.shapes.filter(function(ss){return ss.shape_id !== s.shape_id;});
    if(activeShapeEditId === s.shape_id) setActiveShapeEdit(null);
    el.remove();
  });
  el.querySelector('.shape-act-btn.rot').addEventListener('click', function(ev){
    ev.stopPropagation();
    pushUndo();
    var r = (getRotation(s) + 90) % 360;
    s.rotation = r;
    el.style.setProperty('--rot', r + 'deg');
    setSelectedElement(el);
    setActiveShapeEdit(s.shape_id);
  });
  var resizeHandle = el.querySelector('.shape-resize-handle');
  if(resizeHandle){
    makeShapeResizable(resizeHandle, el, s);
  }
  syncShapeEditState(el, s);
  canvas.appendChild(el);
}

function makeShapeResizable(handle, el, shape){
  handle.addEventListener('pointerdown', function(e){
    e.preventDefault();
    e.stopPropagation();
    pushUndo();
    setSelectedElement(el);
    setActiveShapeEdit(shape.shape_id);
    var startX = e.clientX;
    var startY = e.clientY;
    var startWidth = shape.width || parseInt(el.style.width,10) || 0;
    var startHeight = shape.height || parseInt(el.style.height,10) || 0;
    handle.setPointerCapture(e.pointerId);

    function onPointerMove(ev){
      var deltaX = ev.clientX - startX;
      var deltaY = ev.clientY - startY;
      var nextWidth = clampSize(startWidth + deltaX, 40, 480);
      var nextHeight = clampSize(startHeight + deltaY, 12, 480);
      var normalizedRotation = getNormalizedRotation(shape);
      if(shape.type === 'HORIZONTAL_DIVIDER'){
        nextWidth = clampSize(startWidth + deltaX, 40, 480);
        nextHeight = clampSize(startHeight, 12, 24);
      }
      if(shape.type === 'VERTICAL_DIVIDER'){
        nextWidth = clampSize(startWidth, 12, 24);
        nextHeight = clampSize(startHeight + deltaY, 40, 480);
      }
      if(shape.type === 'WALL'){
        var isVerticalWall = normalizedRotation === 90 || normalizedRotation === 270;
        if(isVerticalWall){
          nextWidth = clampSize(startWidth, 12, 32);
          nextHeight = clampSize(startHeight + deltaY, 40, 480);
        } else {
          nextWidth = clampSize(startWidth + deltaX, 40, 480);
          nextHeight = clampSize(startHeight, 12, 32);
        }
      }
      if(shape.type === 'CURVED_WALL' || shape.type === 'TREE'){
        var size = clampSize(Math.max(nextWidth, nextHeight), 60, 320);
        nextWidth = size;
        nextHeight = size;
      }
      if(shape.type === 'BUSH'){
        nextHeight = clampSize(nextHeight, 24, 200);
      }
      shape.width = nextWidth;
      shape.height = nextHeight;
      el.style.width = nextWidth + 'px';
      el.style.height = nextHeight + 'px';
      syncShapeEditState(el, shape);
    }

    function onPointerUp(ev){
      handle.releasePointerCapture(ev.pointerId);
      handle.removeEventListener('pointermove', onPointerMove);
      handle.removeEventListener('pointerup', onPointerUp);
      syncShapeEditState(el, shape);
    }

    handle.addEventListener('pointermove', onPointerMove);
    handle.addEventListener('pointerup', onPointerUp);
  });
}

function makeDraggable(el, canvas, onMove){
  var startX, startY, origX, origY;
  el.addEventListener('pointerdown', function(e){
    if(e.target.closest('.tbl-act-btn') || e.target.closest('.shape-act-btn') || e.target.closest('.shape-resize-handle') || e.target.closest('.del-btn')) return;
    e.preventDefault();
    startX = e.clientX; startY = e.clientY;
    origX = parseInt(el.style.left,10)||0;
    origY = parseInt(el.style.top,10)||0;
    el.setPointerCapture(e.pointerId);
    if(el.classList.contains('canvas-shape')) setSelectedElement(el);

    function onPointerMove(ev){
      var nx = snap(origX + ev.clientX - startX);
      var ny = snap(origY + ev.clientY - startY);
      el.style.left = Math.max(0,nx) + 'px';
      el.style.top = Math.max(0,ny) + 'px';
    }
    function onPointerUp(ev){
      el.releasePointerCapture(ev.pointerId);
      el.removeEventListener('pointermove', onPointerMove);
      el.removeEventListener('pointerup', onPointerUp);
      var nx = parseInt(el.style.left,10)||0;
      var ny = parseInt(el.style.top,10)||0;
      if(onMove) onMove(nx,ny);
      if(el.classList.contains('canvas-shape')){
        var shapeId = el.dataset.shapeId;
        var shape = fpState.shapes.find(function(item){ return item.shape_id === shapeId; });
        if(shape) syncShapeEditState(el, shape);
      }
    }
    el.addEventListener('pointermove', onPointerMove);
    el.addEventListener('pointerup', onPointerUp);
  });
}

async function loadFloorPlan(){
  var canvas = document.getElementById('floorPlanCanvas');
  if(!canvas) return;
  canvas.querySelectorAll('.canvas-table,.canvas-shape').forEach(function(el){el.remove();});
  fpState = {tables:[],shapes:[],planId:null,counter:0,floorTheme:DEFAULT_FLOOR_THEME};
  activeShapeEditId = null;
  undoStack = [];
  applyFloorTheme(DEFAULT_FLOOR_THEME);

  try{
    var hid = state.hotelId || state.selectedHotelId;
    if(!hid) return;
    var res = await apiFetch('/hotels/' + hid + '/restaurant/floor-plans');
    var data = res;
    if(data.plan && data.plan.layout_data){
      fpState.planId = data.plan.id;
      var ld = data.plan.layout_data;
      applyFloorTheme(ld.floor_theme || DEFAULT_FLOOR_THEME);
      (ld.tables||[]).forEach(function(t){
        fpState.tables.push(t);
        fpState.counter = Math.max(fpState.counter, parseInt((t.table_id.match(/\\d+$/)||['0'])[0],10));
        renderCanvasTable(canvas,t);
      });
      (ld.shapes||[]).forEach(function(s){
        fpState.shapes.push(s);
        fpState.counter = Math.max(fpState.counter, parseInt((s.shape_id.match(/\\d+$/)||['0'])[0],10));
        renderCanvasShape(canvas,s);
      });
    }
  }catch(e){ /* fresh canvas */ }
}

async function saveFloorPlan(){
  var hid = state.hotelId || state.selectedHotelId;
  if(!hid){ notify('Otel secilmedi','error'); return; }

  var layout = {
    canvas_width: 1200,
    canvas_height: 800,
    floor_theme: fpState.floorTheme || DEFAULT_FLOOR_THEME,
    tables: fpState.tables,
    shapes: fpState.shapes
  };

  try{
    var res;
    if(fpState.planId){
      res = await apiFetch('/hotels/' + hid + '/restaurant/floor-plans/' + fpState.planId, {
        method:'PUT',
        body:({layout_data:layout})
      });
    } else {
      res = await apiFetch('/hotels/' + hid + '/restaurant/floor-plans', {
        method:'POST',
        body:({name:'Ana Plan',layout_data:layout})
      });
    }
    var data = res;
    if(data.plan) fpState.planId = data.plan.id;
    notify('Plan kaydedildi','success');
  }catch(e){
    notify('Plan kaydedilemedi','error');
  }
}

/* ── Daily View ───────────────────────────── */

function initDailyView(){
  var btn = document.getElementById('loadDailyViewBtn');
  var dateInput = document.getElementById('dailyViewDate');
  if(!btn||!dateInput) return;
  dateInput.value = new Date().toISOString().slice(0,10);
  btn.addEventListener('click', loadDailyView);
}

async function loadDailyView(){
  var canvas = document.getElementById('dailyViewCanvas');
  var dateInput = document.getElementById('dailyViewDate');
  if(!canvas||!dateInput) return;
  canvas.innerHTML = '';

  var hid = state.hotelId || state.selectedHotelId;
  if(!hid){ notify('Otel secilmedi','error'); return; }

  try{
    var res = await apiFetch('/hotels/' + hid + '/restaurant/tables/daily-view?target_date=' + encodeURIComponent(dateInput.value));
    var data = res;
    (data.items||[]).forEach(function(item){
      var svgData = getTableSvg(item.table_type);
      var el = document.createElement('div');
      el.className = 'canvas-table' + (item.status ? ' st-' + item.status : '');
      el.dataset.type = item.table_type;
      el.style.left = item.x + 'px';
      el.style.top = item.y + 'px';
      el.style.width = svgData.w + 'px';
      el.style.height = svgData.h + 'px';
      el.style.setProperty('--rot', getRotation(item) + 'deg');

      var html = svgData.svg;
      html += '<span class="table-label">' + escapeHtml(item.table_id) + '</span>';

      if(item.status && item.hold_id){
        html += '<div class="guest-overlay">';
        html += '<div>' + escapeHtml(item.guest_name||'') + '</div>';
        if(item.reservation_time) html += '<div class="guest-time">' + escapeHtml(item.reservation_time) + '</div>';
        html += '</div>';
      }

      el.innerHTML = html;
      if(item.hold_id){
        el.style.cursor = 'pointer';
        el.addEventListener('click', function(){ openTableDetail(item.hold_id); });
      }
      canvas.appendChild(el);
    });
    if(!data.items || data.items.length === 0){
      canvas.innerHTML = '<div class="empty-state">Aktif plan yok veya bu tarihte masa atamasi bulunamadi.</div>';
    }
  }catch(e){
    notify('Gunluk gorunum yuklenemedi','error');
  }
}

/* ── Table Detail Dialog ──────────────────── */

async function openTableDetail(holdId){
  var dialog = document.getElementById('tableDetailDialog');
  if(!dialog) return;

  try{
    var hid = state.hotelId || state.selectedHotelId;
    var listRes = await apiFetch('/holds/restaurant?hotel_id=' + hid + '&per_page=100');
    var listData = listRes;
    var hold = (listData.items||[]).find(function(h){ return h.hold_id === holdId; });
    if(!hold){ notify('Rezervasyon bulunamadi','error'); return; }

    document.getElementById('tableDetailTitle').textContent = 'Masa Detayi - ' + escapeHtml(holdId);
    document.getElementById('tdGuestName').value = hold.guest_name || '';
    document.getElementById('tdPhone').textContent = hold.phone ? ('***' + (hold.phone||'').slice(-4)) : '-';
    document.getElementById('tdPartySize').value = hold.party_size || '';
    document.getElementById('tdTime').value = hold.time || '';
    var tdArea = document.getElementById('tdArea');
    if(tdArea) tdArea.value = hold.area || 'outdoor';
    document.getElementById('tdNotes').value = hold.notes || '';
    var tdStatus = document.getElementById('tdStatus');
    if(tdStatus) tdStatus.value = hold.status || 'BEKLEMEDE';
    document.getElementById('tdHoldId').textContent = holdId;
    document.getElementById('tdCreatedAt').textContent = hold.created_at || '-';
    document.getElementById('tdApprovedBy').textContent = hold.approved_by || '-';

    dialog.dataset.holdId = holdId;
    dialog.showModal();
  }catch(e){
    notify('Detay yuklenemedi','error');
  }
}

function initTableDetailDialog(){
  var dialog = document.getElementById('tableDetailDialog');
  if(!dialog) return;

  var closeBtn = dialog.querySelector('[data-close-table-dialog]');
  if(closeBtn) closeBtn.addEventListener('click', function(){ dialog.close(); });

  var form = document.getElementById('tableDetailForm');
  if(form) form.addEventListener('submit', async function(e){
    e.preventDefault();
    var holdId = dialog.dataset.holdId;
    if(!holdId) return;

    var updateBody = {};
    var gn = document.getElementById('tdGuestName').value.trim();
    var ps = parseInt(document.getElementById('tdPartySize').value,10);
    var tm = document.getElementById('tdTime').value;
    var nt = document.getElementById('tdNotes').value.trim();
    if(gn) updateBody.guest_name = gn;
    if(ps > 0) updateBody.party_size = ps;
    if(tm) updateBody.time = tm;
    if(nt !== undefined) updateBody.notes = nt;

    try{
      if(Object.keys(updateBody).length > 0){
        await apiFetch('/holds/restaurant/' + encodeURIComponent(holdId), {
          method:'PUT',
          body:(updateBody)
        });
      }

      var newStatus = document.getElementById('tdStatus').value;
      if(newStatus){
        try{
          await apiFetch('/holds/restaurant/' + encodeURIComponent(holdId) + '/status', {
            method:'PUT',
            body:({status:newStatus})
          });
        }catch(statusErr){}
      }

      notify('Rezervasyon guncellendi','success');
      dialog.close();
      loadDailyView();
    }catch(e){
      notify('Guncelleme basarisiz','error');
    }
  });

  var extendBtn = document.getElementById('tdExtendBtn');
  if(extendBtn) extendBtn.addEventListener('click', async function(){
    var holdId = dialog.dataset.holdId;
    if(!holdId) return;
    try{
      var res = await apiFetch('/holds/restaurant/' + encodeURIComponent(holdId) + '/extend', {method:'POST'});
      var data = res;
      notify('+15 dakika eklendi (toplam: ' + data.total_extended_minutes + ' dk)','success');
      document.getElementById('tdTime').value = data.new_time || '';
    }catch(e){
      var errMsg = e.message || 'Uzatma basarisiz';
      notify(errMsg,'error');
    }
  });

  var cancelBtn = document.getElementById('tdCancelBtn');
  if(cancelBtn) cancelBtn.addEventListener('click', async function(){
    var holdId = dialog.dataset.holdId;
    if(!holdId) return;
    if(!confirm('Bu rezervasyonu iptal etmek istediginizden emin misiniz?')) return;
    try{
      await apiFetch('/holds/restaurant/' + encodeURIComponent(holdId) + '/status', {
        method:'PUT',
        body:({status:'IPTAL',reason:'Admin tarafindan iptal'})
      });
      notify('Rezervasyon iptal edildi','success');
      dialog.close();
      loadDailyView();
    }catch(e){
      notify('Iptal basarisiz','error');
    }
  });
}

/* ── Restaurant Settings ──────────────────── */

function applyRestaurantModeUI(mode){
  var normalized = String(mode || 'AI_RESTAURAN').toUpperCase();
  var aiBtn = document.getElementById('restaurantModeAi');
  var manualBtn = document.getElementById('restaurantModeManual');
  if(aiBtn) aiBtn.classList.toggle('is-active', normalized === 'AI_RESTAURAN');
  if(manualBtn) manualBtn.classList.toggle('is-active', normalized === 'MANUEL');
  state.restaurantMode = normalized;

  var panel = document.getElementById('restaurantHoldCreatePanel');
  var createButtons = Array.from(document.querySelectorAll('[data-action="toggle-restaurant-create"]'));
  if(panel){
    panel.hidden = normalized === 'MANUEL' ? true : panel.hidden;
  }
  createButtons.forEach(function(createBtn){
    createBtn.disabled = normalized === 'MANUEL';
    createBtn.title = normalized === 'MANUEL' ? 'Manuel modda panelden rezervasyon olusturma kapali.' : '';
  });
}

function initRestaurantSettings(){
  var form = document.getElementById('restaurantSettingsForm');
  if(!form) return;

  var aiBtn = document.getElementById('restaurantModeAi');
  var manualBtn = document.getElementById('restaurantModeManual');
  if(aiBtn){
    aiBtn.addEventListener('click', function(){ applyRestaurantModeUI('AI_RESTAURAN'); });
  }
  if(manualBtn){
    manualBtn.addEventListener('click', function(){ applyRestaurantModeUI('MANUEL'); });
  }

  form.addEventListener('submit', async function(e){
    e.preventDefault();
    var hid = state.hotelId || state.selectedHotelId;
    if(!hid){ notify('Otel secilmedi','error'); return; }

    var enabled = document.getElementById('dailyCapToggle').checked;
    var count = parseInt(document.getElementById('dailyCapCount').value,10);
    var dailyPartyEnabled = document.getElementById('dailyPartyCapToggle').checked;
    var dailyPartyCount = parseInt(document.getElementById('dailyPartyCapCount').value,10);
    var minParty = parseInt(document.getElementById('restaurantMinPartySize').value,10);
    var maxParty = parseInt(document.getElementById('restaurantMaxPartySize').value,10);
    var chefPhoneEl = document.getElementById('restaurantChefPhone');
    var chefPhone = chefPhoneEl ? chefPhoneEl.value.trim() : '';
    if(isNaN(count) || count < 1){ notify('Gecerli bir gunluk rezervasyon sayisi girin','error'); return; }
    if(isNaN(dailyPartyCount) || dailyPartyCount < 1){ notify('Gecerli bir gunluk toplam kisi sayisi girin','error'); return; }
    if(isNaN(minParty) || minParty < 1 || isNaN(maxParty) || maxParty < minParty){ notify('Gecerli bir kisi araligi girin','error'); return; }

    try{
      await apiFetch('/hotels/' + hid + '/restaurant/settings', {
        method:'PUT',
        body:({
          daily_max_reservations_enabled:enabled,
          daily_max_reservations_count:count,
          daily_max_party_size_enabled:dailyPartyEnabled,
          daily_max_party_size_count:dailyPartyCount,
          reservation_mode: state.restaurantMode || 'AI_RESTAURAN',
          min_party_size:minParty,
          max_party_size:maxParty,
          chef_phone:chefPhone
        })
      });
      notify('Kapasite ayarlari kaydedildi','success');
    }catch(e){
      notify('Ayarlar kaydedilemedi','error');
    }
  });
}

async function loadRestaurantSettings(){
  var hid = state.hotelId || state.selectedHotelId;
  if(!hid) return;
  try{
    var res = await apiFetch('/hotels/' + hid + '/restaurant/settings');
    var data = res;
    if(data.settings){
      var toggle = document.getElementById('dailyCapToggle');
      var count = document.getElementById('dailyCapCount');
      var dailyPartyToggle = document.getElementById('dailyPartyCapToggle');
      var dailyPartyCount = document.getElementById('dailyPartyCapCount');
      var minParty = document.getElementById('restaurantMinPartySize');
      var maxParty = document.getElementById('restaurantMaxPartySize');
      var chefPhone = document.getElementById('restaurantChefPhone');
      applyRestaurantModeUI(data.settings.reservation_mode || 'AI_RESTAURAN');
      if(toggle) toggle.checked = !!data.settings.daily_max_reservations_enabled;
      if(count) count.value = data.settings.daily_max_reservations_count || 50;
      if(dailyPartyToggle) dailyPartyToggle.checked = !!data.settings.daily_max_party_size_enabled;
      if(dailyPartyCount) dailyPartyCount.value = data.settings.daily_max_party_size_count || 200;
      if(minParty) minParty.value = data.settings.min_party_size || 1;
      if(maxParty) maxParty.value = data.settings.max_party_size || 8;
      if(chefPhone) chefPhone.value = data.settings.chef_phone || '';
    }
  }catch(e){ /* defaults */ }
}

/* ── Service Mode ─────────────────────────── */

const SERVICE_MEALS = {
  breakfast: {label:'Kahvalti', start:'08:00', end:'10:30'},
  lunch: {label:'Ogle', start:'12:00', end:'17:00'},
  dinner: {label:'Aksam', start:'18:00', end:'22:00'}
};

let serviceState = {
  open:false,
  date:'',
  meal:'dinner',
  area:'main',
  plans:[],
  selectedPlanByArea:{main:null,pool:null},
  holds:[],
  pollTimer:null,
  dirty:false
};

function getOperationalTodayIso(){
  var now = new Date();
  var shifted = new Date(now.getTime() - (5 * 60 * 60 * 1000));
  return shifted.toISOString().slice(0,10);
}

function resolveMealHours(){
  var mealHours = state.hotelProfile && state.hotelProfile.restaurant && state.hotelProfile.restaurant.meal_hours;
  if(!mealHours) return SERVICE_MEALS;
  function parseWindow(raw, fallback){
    var text = String(raw || fallback || '').trim();
    var parts = text.split('-');
    if(parts.length !== 2) return fallback;
    return {label:fallback.label,start:parts[0],end:parts[1]};
  }
  return {
    breakfast: parseWindow(mealHours.breakfast, SERVICE_MEALS.breakfast),
    lunch: parseWindow(mealHours.lunch, SERVICE_MEALS.lunch),
    dinner: parseWindow(mealHours.dinner, SERVICE_MEALS.dinner)
  };
}

function parseTimeMinutes(value){
  var txt = String(value || '00:00');
  var p = txt.split(':');
  return (Number(p[0]) || 0) * 60 + (Number(p[1]) || 0);
}

function isHoldInMeal(hold, mealKey){
  var meal = resolveMealHours()[mealKey] || SERVICE_MEALS.dinner;
  var holdMins = parseTimeMinutes(hold.time);
  var start = parseTimeMinutes(meal.start);
  var end = parseTimeMinutes(meal.end);
  return holdMins >= start && holdMins <= end;
}

async function openServiceMode(){
  var dialog = document.getElementById('serviceModeDialog');
  if(!dialog) return;
  if(!state.selectedHotelId){ notify('Hotel secin.', 'warn'); return; }
  serviceState.open = true;
  serviceState.date = getOperationalTodayIso();
  serviceState.meal = 'dinner';
  serviceState.area = 'main';
  serviceState.dirty = false;
  var dateInput = document.getElementById('serviceModeDate');
  if(dateInput) dateInput.value = serviceState.date;
  await loadServiceModePlans();
  await loadServiceModeHolds();
  renderServiceMode();
  if(typeof dialog.showModal === 'function') dialog.showModal();
  startServiceModePolling();
}

async function closeServiceMode(){
  var dialog = document.getElementById('serviceModeDialog');
  if(serviceState.dirty){
    var shouldSave = window.confirm('Kaydedilmemis plan secimi var. Kapatmadan once kaydedilsin mi?');
    if(shouldSave){
      await saveServiceModePlanPrefs();
    }
  }
  stopServiceModePolling();
  serviceState.open = false;
  if(dialog && dialog.open) dialog.close();
}

function startServiceModePolling(){
  stopServiceModePolling();
  serviceState.pollTimer = window.setInterval(async function(){
    if(!serviceState.open) return;
    await loadServiceModeHolds();
    renderServiceReservationLists();
  }, 10000);
}

function stopServiceModePolling(){
  if(serviceState.pollTimer){
    window.clearInterval(serviceState.pollTimer);
    serviceState.pollTimer = null;
  }
}

async function loadServiceModePlans(){
  var hid = state.selectedHotelId;
  var pair = await Promise.all([
    apiFetch('/hotels/' + hid + '/restaurant/floor-plans?include_all=true'),
    apiFetch('/hotels/' + hid + '/restaurant/settings')
  ]);
  var res = pair[0];
  var settings = (pair[1] && pair[1].settings) ? pair[1].settings : {};
  serviceState.plans = res.plans || (res.plan ? [res.plan] : []);
  if(settings.service_mode_main_plan_id){
    serviceState.selectedPlanByArea.main = String(settings.service_mode_main_plan_id);
  }
  if(settings.service_mode_pool_plan_id){
    serviceState.selectedPlanByArea.pool = String(settings.service_mode_pool_plan_id);
  }
  if(!serviceState.selectedPlanByArea.main && res.plan){
    serviceState.selectedPlanByArea.main = String(res.plan.id || '');
  }
  if(!serviceState.selectedPlanByArea.pool){
    serviceState.selectedPlanByArea.pool = serviceState.selectedPlanByArea.main;
  }
  renderServicePlanSelect();
}

async function loadServiceModeHolds(){
  var hid = state.selectedHotelId;
  var params = new URLSearchParams();
  params.set('hotel_id', String(hid));
  params.set('date_from', serviceState.date);
  params.set('date_to', serviceState.date);
  params.set('per_page', '500');
  var response = await apiFetch('/holds/restaurant?' + params.toString());
  serviceState.holds = response.items || [];
}

function getServiceActivePlan(){
  var planId = serviceState.selectedPlanByArea[serviceState.area];
  return serviceState.plans.find(function(item){ return String(item.id) === String(planId); }) || null;
}

function renderServicePlanSelect(){
  var select = document.getElementById('serviceModePlanSelect');
  if(!select) return;
  var selected = serviceState.selectedPlanByArea[serviceState.area];
  select.innerHTML = serviceState.plans.map(function(plan){
    var sid = String(plan.id || '');
    var isSel = String(selected) === sid ? 'selected' : '';
    return '<option value="' + escapeHtml(sid) + '" ' + isSel + '>' + escapeHtml(plan.name || ('Plan ' + sid.slice(0,8))) + '</option>';
  }).join('');
}

function renderServiceMode(){
  renderServicePlanSelect();
  renderServiceCanvas();
  renderServiceReservationLists();
  renderServiceChipStates();
}

function renderServiceChipStates(){
  document.querySelectorAll('#serviceModeMealChips [data-service-meal]').forEach(function(btn){
    btn.classList.toggle('is-active', btn.dataset.serviceMeal === serviceState.meal);
  });
  document.querySelectorAll('#serviceModeAreaChips [data-service-area]').forEach(function(btn){
    btn.classList.toggle('is-active', btn.dataset.serviceArea === serviceState.area);
  });
}

function renderServiceCanvas(){
  var canvas = document.getElementById('serviceModeCanvas');
  if(!canvas) return;
  canvas.innerHTML = '';
  var plan = getServiceActivePlan();
  if(!plan || !plan.layout_data){
    canvas.innerHTML = '<div class="empty-state"><p>Bu alan icin plan secilmedi. Lutfen plan secin.</p></div>';
    return;
  }
  applyFloorTheme((plan.layout_data && plan.layout_data.floor_theme) || DEFAULT_FLOOR_THEME);
  var tables = (plan.layout_data.tables || []);
  var shapes = (plan.layout_data.shapes || []);
  var occupiedByTable = {};
  serviceState.holds.filter(function(h){
    return !!h.table_id && isHoldInMeal(h, serviceState.meal) && String(h.date) === serviceState.date;
  }).forEach(function(h){ occupiedByTable[String(h.table_id)] = h; });

  shapes.forEach(function(s){
    var shape = document.createElement('div');
    shape.className = 'canvas-shape service-shape-locked';
    shape.dataset.shape = s.type;
    shape.style.left = (s.x || 0) + 'px';
    shape.style.top = (s.y || 0) + 'px';
    shape.style.width = (s.width || 40) + 'px';
    shape.style.height = (s.height || 40) + 'px';
    shape.style.setProperty('--rot', getRotation(s) + 'deg');
    shape.innerHTML = '<div class="shape-body" aria-hidden="true"></div>';
    canvas.appendChild(shape);
  });

  tables.forEach(function(t){
    var svgData = getTableSvg(t.type);
    var el = document.createElement('div');
    el.className = 'canvas-table';
    el.dataset.tableId = t.table_id;
    el.style.left = (t.x || 0) + 'px';
    el.style.top = (t.y || 0) + 'px';
    el.style.width = svgData.w + 'px';
    el.style.height = svgData.h + 'px';
    el.style.setProperty('--rot', getRotation(t) + 'deg');
    var hold = occupiedByTable[String(t.table_id)];
    if(hold) el.classList.add('st-' + hold.status);
    var html = svgData.svg + '<span class="table-label">' + escapeHtml(t.table_id) + '</span>';
    if(hold){
      html += '<div class="guest-overlay"><div>' + escapeHtml(hold.guest_name || '-') + '</div><div class="guest-time">' + escapeHtml(hold.time || '') + '</div></div>';
      el.title = 'Dolu: ' + (hold.guest_name || '-') + ' | ' + (hold.party_size || '-') + ' kisi';
    } else {
      el.title = 'Bos masa: ' + t.table_id;
    }
    el.innerHTML = html;
    if(hold){
      el.addEventListener('click', function(){ openServiceHoldActions(hold, t); });
    }
    el.addEventListener('dragover', function(ev){ ev.preventDefault(); el.classList.add('service-table-drop'); });
    el.addEventListener('dragleave', function(){ el.classList.remove('service-table-drop'); });
    el.addEventListener('drop', async function(ev){
      ev.preventDefault();
      el.classList.remove('service-table-drop');
      var holdId = ev.dataTransfer.getData('text/plain');
      if(!holdId) return;
      await assignHoldToServiceTable(holdId, t);
    });
    canvas.appendChild(el);
  });
}

function renderServiceReservationLists(){
  var approved = document.getElementById('serviceModeApprovedList');
  var pending = document.getElementById('serviceModePendingList');
  var other = document.getElementById('serviceModeOtherList');
  if(!approved || !pending || !other) return;
  var rows = (serviceState.holds || []).filter(function(item){
    return String(item.date) === serviceState.date && isHoldInMeal(item, serviceState.meal);
  });
  var approvedRows = rows.filter(function(item){ return item.status === 'ONAYLANDI'; });
  var pendingRows = rows.filter(function(item){ return item.status === 'BEKLEMEDE' || item.status === 'PENDING_APPROVAL'; });
  var otherRows = rows.filter(function(item){ return item.status !== 'ONAYLANDI' && item.status !== 'BEKLEMEDE' && item.status !== 'PENDING_APPROVAL'; });
  approved.innerHTML = renderServiceHoldCards(approvedRows, true);
  pending.innerHTML = renderServiceHoldCards(pendingRows, true);
  other.innerHTML = renderServiceHoldCards(otherRows, false);
}

function renderServiceHoldCards(items, draggable){
  if(!items.length) return '<div class="empty-state"><p>Kayit yok.</p></div>';
  return items.map(function(item){
    return '<article class="service-reservation-card" draggable="' + (draggable ? 'true' : 'false') + '" data-service-hold-id="' + escapeHtml(item.hold_id) + '">'
      + '<strong>' + escapeHtml(item.guest_name || item.hold_id) + '</strong>'
      + '<small>' + escapeHtml(item.time || '-') + ' · ' + escapeHtml(item.party_size || '-') + ' kisi</small>'
      + '<small>Durum: ' + escapeHtml(item.status || '-') + '</small>'
      + '</article>';
  }).join('');
}

async function assignHoldToServiceTable(holdId, table){
  try{
    var hold = (serviceState.holds || []).find(function(item){ return item.hold_id === holdId; });
    if(hold && (hold.status === 'BEKLEMEDE' || hold.status === 'PENDING_APPROVAL')){
      await apiFetch('/holds/restaurant/' + encodeURIComponent(holdId) + '/status', {
        method:'PUT',
        body:({status:'ONAYLANDI', reason:'Servis Modu onay + masa atama'})
      });
    }
    await apiFetch('/holds/restaurant/' + encodeURIComponent(holdId), {
      method:'PUT',
      body:({table_id:String(table.table_id || ''), table_type:String(table.type || '')})
    });
    notify('Rezervasyon masaya atandi.', 'success');
    await loadServiceModeHolds();
    renderServiceMode();
  }catch(error){
    notify(error.message || 'Masa atamasi basarisiz.', 'error');
  }
}

async function openServiceHoldActions(hold, table){
  var action = window.prompt('Aksiyon secin: DEGISTIR / KALDIR / GUNCELLE / IPTAL', 'GUNCELLE');
  if(!action) return;
  var normalized = String(action || '').trim().toUpperCase();
  try{
    if(normalized === 'DEGISTIR'){
      var nextTable = window.prompt('Yeni masa numarasi girin', String(table.table_id || hold.table_id || ''));
      if(!nextTable) return;
      await apiFetch('/holds/restaurant/' + encodeURIComponent(hold.hold_id), {
        method:'PUT',
        body:({table_id:String(nextTable).trim(), table_type:hold.table_type || table.type || null})
      });
      notify('Masa degistirildi.', 'success');
    } else if(normalized === 'KALDIR'){
      await apiFetch('/holds/restaurant/' + encodeURIComponent(hold.hold_id), {
        method:'PUT',
        body:({table_id:''})
      });
      notify('Masa atamasi kaldirildi.', 'success');
    } else if(normalized === 'IPTAL'){
      await apiFetch('/holds/restaurant/' + encodeURIComponent(hold.hold_id) + '/status', {
        method:'PUT',
        body:({status:'IPTAL', reason:'Servis Modu iptal islemi'})
      });
      notify('Rezervasyon iptal edildi.', 'success');
    } else {
      var guestName = window.prompt('Misafir adi', hold.guest_name || '') || hold.guest_name;
      var partySizeText = window.prompt('Kisi sayisi', String(hold.party_size || '')) || String(hold.party_size || '');
      var timeText = window.prompt('Saat (HH:MM)', String(hold.time || '')) || String(hold.time || '');
      var notesText = window.prompt('Notlar', hold.notes || '') || hold.notes || '';
      await apiFetch('/holds/restaurant/' + encodeURIComponent(hold.hold_id), {
        method:'PUT',
        body:({guest_name:guestName, party_size:Number(partySizeText), time:timeText, notes:notesText})
      });
      notify('Rezervasyon guncellendi.', 'success');
    }
    await loadServiceModeHolds();
    renderServiceMode();
  }catch(error){
    notify(error.message || 'Islem basarisiz.', 'error');
  }
}

async function saveServiceModePlanPrefs(){
  if(!state.selectedHotelId) return;
  try{
    await apiFetch('/hotels/' + state.selectedHotelId + '/restaurant/settings', {
      method:'PUT',
      body:({
        service_mode_main_plan_id: serviceState.selectedPlanByArea.main || null,
        service_mode_pool_plan_id: serviceState.selectedPlanByArea.pool || null
      })
    });
    serviceState.dirty = false;
    notify('Servis modu plan secimleri kaydedildi.', 'success');
  }catch(error){
    notify(error.message || 'Plan secimi kaydedilemedi.', 'error');
  }
}

function bindServiceModeEvents(){
  var openBtn = document.getElementById('openServiceModeBtn');
  if(openBtn) openBtn.addEventListener('click', openServiceMode);
  var closeBtn = document.getElementById('serviceModeCloseBtn');
  if(closeBtn) closeBtn.addEventListener('click', closeServiceMode);

  var dateInput = document.getElementById('serviceModeDate');
  if(dateInput){
    dateInput.addEventListener('change', async function(){
      serviceState.date = dateInput.value || getOperationalTodayIso();
      await loadServiceModeHolds();
      renderServiceMode();
    });
  }

  var prevDay = document.getElementById('serviceModePrevDay');
  if(prevDay){
    prevDay.addEventListener('click', async function(){
      var d = new Date(serviceState.date + 'T00:00:00');
      d.setDate(d.getDate() - 1);
      serviceState.date = d.toISOString().slice(0,10);
      if(dateInput) dateInput.value = serviceState.date;
      await loadServiceModeHolds();
      renderServiceMode();
    });
  }
  var nextDay = document.getElementById('serviceModeNextDay');
  if(nextDay){
    nextDay.addEventListener('click', async function(){
      var d = new Date(serviceState.date + 'T00:00:00');
      d.setDate(d.getDate() + 1);
      serviceState.date = d.toISOString().slice(0,10);
      if(dateInput) dateInput.value = serviceState.date;
      await loadServiceModeHolds();
      renderServiceMode();
    });
  }

  document.querySelectorAll('#serviceModeMealChips [data-service-meal]').forEach(function(btn){
    btn.addEventListener('click', function(){ serviceState.meal = btn.dataset.serviceMeal; renderServiceMode(); });
  });
  document.querySelectorAll('#serviceModeAreaChips [data-service-area]').forEach(function(btn){
    btn.addEventListener('click', async function(){
      if(serviceState.dirty){
        var shouldSave = window.confirm('Plan secimi degisti. Alan degistirmeden once kaydedilsin mi?');
        if(shouldSave){
          await saveServiceModePlanPrefs();
        }
      }
      serviceState.area = btn.dataset.serviceArea;
      renderServiceMode();
    });
  });

  var planSelect = document.getElementById('serviceModePlanSelect');
  if(planSelect){
    planSelect.addEventListener('change', async function(){
      serviceState.selectedPlanByArea[serviceState.area] = planSelect.value;
      serviceState.dirty = true;
      await saveServiceModePlanPrefs();
      renderServiceMode();
    });
  }

  document.addEventListener('dragstart', function(ev){
    var card = ev.target.closest('[data-service-hold-id]');
    if(!card || card.getAttribute('draggable') !== 'true') return;
    ev.dataTransfer.setData('text/plain', card.dataset.serviceHoldId || '');
  });

  document.addEventListener('keydown', async function(ev){
    if(!serviceState.open) return;
    if(ev.key === '1'){ serviceState.meal = 'breakfast'; renderServiceMode(); }
    if(ev.key === '2'){ serviceState.meal = 'lunch'; renderServiceMode(); }
    if(ev.key === '3'){ serviceState.meal = 'dinner'; renderServiceMode(); }
    if(ev.altKey && ev.key === 'ArrowLeft'){
      ev.preventDefault();
      var d1 = new Date(serviceState.date + 'T00:00:00');
      d1.setDate(d1.getDate() - 1);
      serviceState.date = d1.toISOString().slice(0,10);
      var di1 = document.getElementById('serviceModeDate');
      if(di1) di1.value = serviceState.date;
      await loadServiceModeHolds();
      renderServiceMode();
    }
    if(ev.altKey && ev.key === 'ArrowRight'){
      ev.preventDefault();
      var d2 = new Date(serviceState.date + 'T00:00:00');
      d2.setDate(d2.getDate() + 1);
      serviceState.date = d2.toISOString().slice(0,10);
      var di2 = document.getElementById('serviceModeDate');
      if(di2) di2.value = serviceState.date;
      await loadServiceModeHolds();
      renderServiceMode();
    }
  });
}

/* ── Init ─────────────────────────────────── */

function initRestaurantModule(){
  initFloorPlanEditor();
  initDailyView();
  initTableDetailDialog();
  initRestaurantSettings();
  bindServiceModeEvents();
  applyRestaurantModeUI('AI_RESTAURAN');
}

// Hook into navigation
let _restaurantInited = false;
function _onRestaurantView(){
  if(!_restaurantInited){ initRestaurantModule(); _restaurantInited = true; }
  loadFloorPlan();
  loadDailyView();
  loadRestaurantSettings();
  if(typeof loadRestaurantHolds === 'function') loadRestaurantHolds();
}

window.addEventListener('hashchange', function(){
  if(window.location.hash === '#restaurant') _onRestaurantView();
});
document.addEventListener('click', function(e){
  if(e.target.closest('[data-nav="restaurant"]')){
    setTimeout(_onRestaurantView, 50);
  }
});

function _initOnReady(){
  initRestaurantModule();
  _restaurantInited = true;
  if(window.location.hash === '#restaurant') _onRestaurantView();
}
if(document.readyState === 'loading'){
  document.addEventListener('DOMContentLoaded', _initOnReady);
} else {
  _initOnReady();
}

})();
"""
