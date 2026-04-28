"""CSS and JS assets for the restaurant floor plan editor, daily view, and settings."""

# ruff: noqa: E501

ADMIN_RESTAURANT_STYLE = """
/* ── Floor plan workspace ───────────────────────────── */
.floor-plan-workspace{display:flex;gap:1rem;align-items:stretch;min-height:1600px}
.floor-plan-toolbox{width:180px;flex-shrink:0;display:flex;flex-direction:column;gap:.35rem;padding:.75rem;background:var(--bg-2);border-radius:var(--radius);border:1px solid var(--border);max-height:1700px;overflow-y:auto;position:sticky;top:1rem;align-self:flex-start}
#floorPlanEditorCard>.module-header{display:flex;flex-wrap:wrap;align-items:flex-start;gap:.5rem}
.floor-plan-controls{display:flex;align-items:flex-end;gap:.5rem;flex-wrap:wrap;flex:1 1 100%;margin-top:.75rem;padding:.75rem;background:var(--bg-2);border:1px solid var(--border);border-radius:var(--radius)}
.fp-plan-name-field{min-width:200px;max-width:300px;margin:0}
.fp-plan-list-field{min-width:200px;max-width:280px;margin:0}
.fp-plan-name-field span,.fp-plan-list-field span{display:block;font-size:.68rem;color:var(--muted);margin-bottom:.2rem}
.fp-plan-dirty-indicator{display:inline-block;width:8px;height:8px;border-radius:50%;background:#f59e0b;margin-left:6px;vertical-align:middle;opacity:0;transition:opacity .2s}
.fp-plan-dirty-indicator.visible{opacity:1}
.fp-plan-status{font-size:.72rem;color:var(--muted);align-self:center;margin-left:auto;display:flex;align-items:center;gap:.3rem}
.fp-plan-status .fp-plan-id-badge{font-size:.65rem;background:var(--bg-2);border:1px solid var(--border);border-radius:var(--radius);padding:.1rem .4rem}
.fp-plan-info-bar{display:flex;align-items:center;gap:.6rem;flex-wrap:wrap;font-size:.75rem;color:var(--muted);padding:.5rem .75rem;background:var(--bg-2);border:1px solid var(--border);border-radius:var(--radius);margin-bottom:.5rem}
.fp-plan-info-bar .fp-plan-badge{display:inline-flex;align-items:center;gap:.25rem;background:var(--accent-bg);color:var(--accent);border-radius:999px;padding:.15rem .55rem;font-weight:600;font-size:.7rem}
.fp-plan-info-bar .fp-plan-badge.is-new{background:#fef3c7;color:#92400e}
.fp-plan-info-bar .fp-plan-date{color:var(--muted)}
.fp-name-prompt-overlay{position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center}
.fp-name-prompt-box{background:var(--bg-1);border:1px solid var(--border);border-radius:var(--radius);padding:1.5rem;width:min(400px,90vw);box-shadow:0 8px 30px rgba(0,0,0,.35)}
.fp-name-prompt-box h4{margin:0 0 .75rem;font-size:.95rem}
.fp-name-prompt-box input{width:100%;padding:.5rem .6rem;font-size:.88rem;border:1px solid var(--border);border-radius:var(--radius);background:var(--bg-2);color:var(--fg);outline:none;margin-bottom:.75rem}
.fp-name-prompt-box input:focus{border-color:var(--accent)}
.fp-name-prompt-actions{display:flex;justify-content:flex-end;gap:.5rem}
.fp-delete-btn{background:none;border:1px solid var(--danger,#ef4444);color:var(--danger,#ef4444);border-radius:var(--radius);padding:.3rem .6rem;font-size:.72rem;cursor:pointer;transition:all .15s}
.fp-delete-btn:hover{background:var(--danger,#ef4444);color:#fff}
.fp-activate-btn{background:none;border:1px solid var(--accent);color:var(--accent);border-radius:var(--radius);padding:.3rem .6rem;font-size:.72rem;cursor:pointer;transition:all .15s}
.fp-activate-btn:hover{background:var(--accent);color:#fff}
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
.floor-plan-canvas{flex:1;position:relative;background:var(--floor-base,var(--bg-1));background-image:var(--floor-texture,none);background-size:var(--floor-size,auto);background-position:center;border:2px dashed var(--border);border-radius:var(--radius);min-height:1600px;aspect-ratio:1/1;max-height:none;overflow:hidden}
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
.service-mode-dialog{border:none;width:100vw;height:100vh;max-width:none;max-height:none;padding:0;background:var(--bg-0,#0f172a);color:var(--fg,#f8fafc);z-index:2147483000}
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
.service-mode-canvas{width:100%;height:100%;min-height:560px;overflow:hidden;touch-action:none;position:relative}
.service-canvas-scaler{position:absolute;top:0;left:0;transform-origin:0 0}
.service-mode-canvas .canvas-table{touch-action:none;cursor:grab}
.service-mode-canvas .canvas-table:active{cursor:grabbing}
.service-mode-side{display:flex;flex-direction:column;gap:10px;min-height:0;overflow:auto}
.service-list{display:flex;flex-direction:column;gap:6px;max-height:220px;overflow:auto}
.service-reservation-card{background:var(--bg-2);border:1px solid var(--border);border-radius:var(--radius);padding:.7rem;cursor:grab;touch-action:none}
.service-reservation-card small{display:block;color:var(--muted)}
.service-table-drop{outline:2px dashed var(--accent);outline-offset:6px}
.service-shape-locked{pointer-events:none;opacity:.72;filter:saturate(.7)}

/* Service mode toolbox */
.service-toolbox{display:flex;flex-wrap:wrap;gap:6px;padding:4px 0}
.service-toolbox-item{display:flex;align-items:center;gap:4px;padding:4px 8px;border-radius:var(--radius);background:var(--bg-1);border:1px solid var(--border);cursor:grab;font-size:.72rem;user-select:none;transition:background .15s}
.service-toolbox-item:hover{background:var(--accent-bg);border-color:var(--accent)}
.service-toolbox-item svg{width:28px;height:28px}

/* Service mode table tooltip */
.service-table-tooltip{position:absolute;z-index:100;background:var(--bg-0,#1e293b);color:#f8fafc;border:1px solid var(--border);border-radius:var(--radius);padding:8px 10px;font-size:.72rem;line-height:1.4;pointer-events:none;white-space:nowrap;box-shadow:0 4px 12px rgba(0,0,0,.4);transform:translateX(-50%);left:50%;bottom:calc(100% + 8px)}
.service-table-tooltip::after{content:'';position:absolute;top:100%;left:50%;transform:translateX(-50%);border:5px solid transparent;border-top-color:var(--bg-0,#1e293b)}

/* Service Mode V2 layout */
.service-mode-v2{padding:10px 12px}
.service-mode-grid-v2{display:grid;grid-template-columns:320px minmax(0,1fr) 340px;gap:10px;min-height:0;flex:1}
.service-col{min-height:0;display:flex;flex-direction:column;gap:10px}
.service-panel{background:var(--bg-2);border:1px solid var(--border);border-radius:var(--radius);padding:10px}
.service-col-left .service-panel{flex:1;min-height:180px;overflow:auto}
.service-col-center .service-canvas-panel{display:flex;flex-direction:column;height:100%;min-height:620px}
.service-col-center .service-canvas-panel .service-mode-canvas{flex:1}
.service-col-right .service-panel{height:100%;overflow:auto}
.service-meta-row{font-size:.85rem;color:var(--muted);margin:.3rem 0}
.service-mode-bottom-v2{display:grid;grid-template-columns:1fr 1.2fr 1fr 1fr;gap:10px}
.service-bottom-block{background:var(--bg-2);border:1px solid var(--border);border-radius:var(--radius);padding:10px;min-height:120px}
.service-bottom-block h5{margin:0 0 8px 0;font-size:.82rem;color:var(--muted)}
.service-table-legend{position:absolute;bottom:10px;right:10px;z-index:20;background:rgba(255,255,255,.92);border:1px solid var(--border);border-radius:var(--radius);padding:8px 10px;font-size:.72rem;line-height:1;display:flex;flex-direction:column;gap:5px}
.service-table-legend h6{margin:0 0 2px 0;font-size:.7rem;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.service-legend-row{display:flex;align-items:center;gap:6px;cursor:grab;padding:3px 4px;border-radius:4px;transition:background .15s}
.service-legend-row:hover{background:rgba(0,0,0,.06)}
.service-legend-row:active{cursor:grabbing}
.service-legend-row svg{width:28px;height:20px;flex-shrink:0;pointer-events:none}
.service-legend-row span{color:var(--fg);white-space:nowrap;pointer-events:none}

/* ── Service mode context menu ──────────────────── */
.svc-ctx-menu{position:fixed;z-index:2147483010;min-width:200px;background:var(--bg-1,#1e293b);border:1px solid var(--border,#334155);border-radius:10px;box-shadow:0 12px 40px rgba(0,0,0,.45),0 2px 8px rgba(0,0,0,.2);padding:5px 0;opacity:0;transform:scale(.92) translateY(-4px);transition:opacity .12s ease,transform .12s ease;pointer-events:none;font-family:inherit}
.svc-ctx-menu.is-visible{opacity:1;transform:scale(1) translateY(0);pointer-events:auto}
.svc-ctx-menu-header{padding:8px 14px 6px;font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--muted,#94a3b8);user-select:none;border-bottom:1px solid var(--border,#334155);margin-bottom:2px}
.svc-ctx-item{display:flex;align-items:center;gap:10px;padding:9px 14px;font-size:.82rem;color:var(--fg,#f1f5f9);cursor:pointer;transition:background .1s;border-radius:0;user-select:none;border:none;background:none;width:100%;text-align:left;font-family:inherit}
.svc-ctx-item:hover{background:var(--accent-bg,rgba(99,102,241,.12))}
.svc-ctx-item:active{background:var(--accent-bg,rgba(99,102,241,.2))}
.svc-ctx-item .ctx-icon{width:18px;height:18px;display:flex;align-items:center;justify-content:center;border-radius:5px;font-size:.72rem;flex-shrink:0}
.svc-ctx-item .ctx-icon.icon-remove{background:rgba(239,68,68,.15);color:#f87171}
.svc-ctx-item .ctx-icon.icon-swap{background:rgba(99,102,241,.15);color:#818cf8}
.svc-ctx-item .ctx-icon.icon-edit{background:rgba(34,197,94,.15);color:#4ade80}
.svc-ctx-item .ctx-icon.icon-cancel{background:rgba(251,191,36,.15);color:#fbbf24}
.svc-ctx-item .ctx-label{display:flex;flex-direction:column;gap:1px}
.svc-ctx-item .ctx-label small{font-size:.66rem;color:var(--muted,#94a3b8);font-weight:400}
.svc-ctx-sep{height:1px;background:var(--border,#334155);margin:3px 10px}
.svc-ctx-item.ctx-danger:hover{background:rgba(239,68,68,.12)}
.svc-ctx-item.ctx-danger .ctx-label,.svc-ctx-item.ctx-danger .ctx-label small{color:#f87171}

/* ── Service mode confirm modal ─────────────────── */
.svc-confirm-backdrop{position:fixed;inset:0;z-index:2147483020;background:rgba(0,0,0,.55);display:flex;align-items:center;justify-content:center;opacity:0;transition:opacity .15s;pointer-events:none}
.svc-confirm-backdrop.is-visible{opacity:1;pointer-events:auto}
.svc-confirm-box{background:var(--bg-1,#1e293b);border:1px solid var(--border,#334155);border-radius:14px;box-shadow:0 20px 60px rgba(0,0,0,.5);width:min(420px,92vw);padding:0;transform:scale(.94);transition:transform .15s;overflow:hidden}
.svc-confirm-backdrop.is-visible .svc-confirm-box{transform:scale(1)}
.svc-confirm-head{padding:16px 20px 12px;border-bottom:1px solid var(--border,#334155)}
.svc-confirm-head h4{margin:0;font-size:.95rem;font-weight:600;color:var(--fg,#f1f5f9)}
.svc-confirm-head p{margin:6px 0 0;font-size:.78rem;color:var(--muted,#94a3b8);line-height:1.45}
.svc-confirm-body{padding:14px 20px;display:flex;flex-direction:column;gap:10px}
.svc-confirm-option{display:flex;align-items:center;gap:12px;padding:12px 14px;border:1px solid var(--border,#334155);border-radius:10px;background:var(--bg-2,#0f172a);cursor:pointer;transition:border-color .12s,background .12s}
.svc-confirm-option:hover{border-color:var(--accent,#6366f1);background:rgba(99,102,241,.06)}
.svc-confirm-option .opt-icon{width:34px;height:34px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:1rem;flex-shrink:0}
.svc-confirm-option .opt-icon.opt-remove{background:rgba(239,68,68,.15);color:#f87171}
.svc-confirm-option .opt-icon.opt-move{background:rgba(99,102,241,.15);color:#818cf8}
.svc-confirm-option .opt-text{display:flex;flex-direction:column;gap:2px}
.svc-confirm-option .opt-text strong{font-size:.84rem;color:var(--fg,#f1f5f9);font-weight:600}
.svc-confirm-option .opt-text span{font-size:.72rem;color:var(--muted,#94a3b8)}
.svc-confirm-foot{padding:10px 20px 14px;display:flex;justify-content:flex-end}
.svc-confirm-foot .svc-cancel-btn{background:none;border:1px solid var(--border,#334155);border-radius:8px;padding:7px 18px;font-size:.78rem;color:var(--muted,#94a3b8);cursor:pointer;transition:border-color .12s,color .12s;font-family:inherit}
.svc-confirm-foot .svc-cancel-btn:hover{border-color:var(--fg,#f1f5f9);color:var(--fg,#f1f5f9)}

/* Move-to-table input modal */
.svc-move-input-group{display:flex;gap:8px;align-items:stretch}
.svc-move-input{flex:1;background:var(--bg-2,#0f172a);border:1px solid var(--border,#334155);border-radius:8px;padding:10px 12px;font-size:.88rem;color:var(--fg,#f1f5f9);outline:none;transition:border-color .12s;font-family:inherit}
.svc-move-input:focus{border-color:var(--accent,#6366f1)}
.svc-move-input.has-error{border-color:#ef4444}
.svc-move-submit{background:var(--accent,#6366f1);color:#fff;border:none;border-radius:8px;padding:10px 20px;font-size:.82rem;font-weight:600;cursor:pointer;transition:opacity .12s;font-family:inherit;white-space:nowrap}
.svc-move-submit:hover{opacity:.88}
.svc-move-submit:disabled{opacity:.4;cursor:not-allowed}
.svc-move-error{font-size:.72rem;color:#f87171;margin-top:2px;min-height:16px}

@media(max-width:1400px){
  .service-mode-grid-v2{grid-template-columns:280px minmax(0,1fr) 300px}
}

@media(max-width:980px){
  .floor-plan-workspace{flex-direction:column;min-height:0}
  .floor-plan-controls{justify-content:stretch}
  .fp-plan-name-field,.fp-plan-list-field{min-width:100%;max-width:none}
  .floor-plan-toolbox{width:100%;flex-direction:row;flex-wrap:wrap;min-height:auto;max-height:none}
  .floor-plan-canvas{min-height:900px;max-height:none}
  .fp-toolbar{justify-content:center}
  .service-mode-shell{padding:8px}
  .service-mode-actions .inline-button,.service-mode-toolbar .filter-chip{min-height:42px;padding:.45rem .8rem}
  .service-mode-body{grid-template-columns:1fr;grid-template-rows:minmax(0,1fr) auto}
  .service-mode-side{max-height:45vh}
  .service-mode-grid-v2{grid-template-columns:1fr}
  .service-mode-bottom-v2{grid-template-columns:1fr}
  .service-col-center .service-canvas-panel{min-height:420px}
}
"""

ADMIN_RESTAURANT_SCRIPT = """
/* ═══════════════════════════════════════════════════════
   Restaurant Floor Plan Editor, Daily View, Settings
   - Realistic SVG tables with chairs, advanced tools
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
const FLOOR_PLAN_EMPTY_OPTION_LABEL = 'Kayıtlı plan yok';
const FLOOR_PLAN_SELECT_PROMPT = 'Plan seç';
const FLOOR_PLAN_NAME_PROMPT_TITLE = 'Plan Adı Girin';
const FLOOR_PLAN_NAME_PLACEHOLDER = 'Örn. Ana Salon Akşam Düzeni';
const DAILY_VIEW_EMPTY_MESSAGE = 'Aktif plan yok veya bu tarihte masa ataması bulunamadı.';
let fpState = {tables:[],shapes:[],planId:null,planName:'Ana Plan',counter:0,floorTheme:DEFAULT_FLOOR_THEME};
let floorPlanCollection = [];
let selectedEl = null;
let activeShapeEditId = null;
let undoStack = [];
const MAX_UNDO = 30;
let clickPlaceMode = null; // null or {type, capacity} or {shape}
let showGrid = true;
let floorPlanAutoSaveTimer = null;
const FLOOR_PLAN_AUTOSAVE_DELAY_MS = 1500;

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
    var input = window.prompt('Masa numarası zorunlu. Örnek: A1, 12, H-07', fallback);
    if(input === null) return null;
    var candidate = normalizeTableId(input);
    if(!candidate){
      notify('Masa numarası boş bırakılamaz.', 'warn');
      fallback = candidate;
      continue;
    }
    if(hasTableId(candidate, excludeId)){
      notify('Bu masa numarası zaten kullanılıyor.', 'warn');
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
function applyThemeClassToCanvas(canvas, themeKey){
  if(!canvas) return;
  Object.keys(FLOOR_THEMES).forEach(function(key){ canvas.classList.remove(FLOOR_THEMES[key]); });
  var resolved = FLOOR_THEMES[themeKey] ? themeKey : DEFAULT_FLOOR_THEME;
  canvas.classList.add(FLOOR_THEMES[resolved]);
}

function applyFloorTheme(themeKey){
  var canvas = document.getElementById('floorPlanCanvas');
  if(!canvas) return;
  var resolved = FLOOR_THEMES[themeKey] ? themeKey : DEFAULT_FLOOR_THEME;
  applyThemeClassToCanvas(canvas, resolved);
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

function getFloorPlanNameInputValue(){
  var input = document.getElementById('floorPlanNameInput');
  var raw = input ? String(input.value || '').trim() : '';
  if(!raw) raw = fpState.planName || 'Ana Plan';
  return raw.slice(0, 80);
}

function syncFloorPlanHeaderFields(){
  var input = document.getElementById('floorPlanNameInput');
  if(input) input.value = fpState.planName || 'Ana Plan';
  var select = document.getElementById('floorPlanSelect');
  if(select && fpState.planId){
    select.value = String(fpState.planId);
  }
  updateDirtyIndicator();
}

function renderFloorPlanSelect(){
  var select = document.getElementById('floorPlanSelect');
  if(!select) return;
  if(!floorPlanCollection.length){
    select.innerHTML = '<option value="">' + FLOOR_PLAN_EMPTY_OPTION_LABEL + '</option>';
    select.disabled = true;
    return;
  }
  select.disabled = false;
  var opts = '<option value="">-- ' + FLOOR_PLAN_SELECT_PROMPT + ' (' + floorPlanCollection.length + ' kayıtlı) --</option>';
  opts += floorPlanCollection.map(function(plan){
    var pid = String(plan.id || '');
    var activeTag = plan.is_active ? ' ★ Aktif' : '';
    var tableCount = (plan.layout_data && plan.layout_data.tables) ? plan.layout_data.tables.length : 0;
    var shapeCount = (plan.layout_data && plan.layout_data.shapes) ? plan.layout_data.shapes.length : 0;
    var suffix = '';
    if(tableCount > 0 || shapeCount > 0) suffix = ' (' + tableCount + ' masa, ' + shapeCount + ' şekil)';
    var dateInfo = plan.updated_at ? ' - ' + String(plan.updated_at).slice(0,10) : '';
    return '<option value="' + escapeHtml(pid) + '">' + escapeHtml((plan.name || 'Adsız Plan') + activeTag + suffix + dateInfo) + '</option>';
  }).join('');
  select.innerHTML = opts;
  if(fpState.planId){
    select.value = String(fpState.planId);
  }
}

function scheduleFloorPlanAutoSave(){
  if(floorPlanAutoSaveTimer){
    window.clearTimeout(floorPlanAutoSaveTimer);
  }
  floorPlanAutoSaveTimer = window.setTimeout(function(){
    saveFloorPlan({silent:true, fromAutoSave:true});
  }, FLOOR_PLAN_AUTOSAVE_DELAY_MS);
}

function updateDirtyIndicator(){
  var dot = document.getElementById('fpDirtyDot');
  if(dot) dot.classList.toggle('visible', !!fpState._dirty);
  var badge = document.getElementById('fpPlanIdBadge');
  if(badge){
    if(fpState.planId){
      badge.textContent = 'ID: ' + String(fpState.planId).slice(0,8);
      badge.title = 'Plan kimliği: ' + String(fpState.planId);
    } else {
      badge.textContent = 'Yeni';
      badge.title = 'Henüz kaydedilmemiş yeni plan';
    }
  }
  updatePlanInfoBar();
}

function updatePlanInfoBar(){
  var bar = document.getElementById('fpPlanInfoBar');
  if(!bar) return;
  var badgeEl = document.getElementById('fpPlanBadge');
  var dateEl = document.getElementById('fpPlanDate');
  var countEl = document.getElementById('fpPlanTableCount');
  if(badgeEl){
    if(fpState.planId){
      var currentPlan = floorPlanCollection.find(function(p){ return String(p.id) === String(fpState.planId); });
      var isActive = currentPlan && currentPlan.is_active;
      badgeEl.textContent = isActive ? '\u2605 Aktif Plan' : 'Kayıtlı Plan';
      badgeEl.className = 'fp-plan-badge' + (isActive ? '' : ' is-new');
    } else {
      badgeEl.textContent = 'Yeni Plan';
      badgeEl.className = 'fp-plan-badge is-new';
    }
  }
  if(dateEl){
    var plan = floorPlanCollection.find(function(p){ return fpState.planId && String(p.id) === String(fpState.planId); });
    dateEl.textContent = plan && plan.updated_at ? 'Son güncelleme: ' + String(plan.updated_at).slice(0,16).replace('T',' ') : '';
  }
  if(countEl){
    var tc = fpState.tables.length;
    var sc = fpState.shapes.length;
    countEl.textContent = tc + ' masa, ' + sc + ' şekil';
  }
  // Toggle delete & activate button visibility
  var delBtn = document.getElementById('deleteFloorPlanBtn');
  var actBtn = document.getElementById('activateFloorPlanBtn');
  if(delBtn) delBtn.style.display = fpState.planId ? '' : 'none';
  if(actBtn){
    var activePlan = floorPlanCollection.find(function(p){ return fpState.planId && String(p.id) === String(fpState.planId); });
    actBtn.style.display = (fpState.planId && !(activePlan && activePlan.is_active)) ? '' : 'none';
  }
}

function markFloorPlanChanged(){
  fpState.planName = getFloorPlanNameInputValue();
  fpState._dirty = true;
  syncFloorPlanHeaderFields();
  updateDirtyIndicator();
  scheduleFloorPlanAutoSave();
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
  markFloorPlanChanged();
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
    editBtn.setAttribute('title', isEditing ? 'Şekil düzenlemeyi kapat' : 'Şekil düzenle');
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
  if(saveBtn) saveBtn.addEventListener('click', function(){ saveFloorPlan({silent:false}); });
  var resetBtn = document.getElementById('resetFloorPlanBtn');
  if(resetBtn) resetBtn.addEventListener('click', loadFloorPlan);

  var planNameInput = document.getElementById('floorPlanNameInput');
  if(planNameInput && planNameInput.dataset.bound !== '1'){
    planNameInput.addEventListener('input', function(){
      fpState.planName = getFloorPlanNameInputValue();
      fpState._dirty = true;
      updateDirtyIndicator();
      scheduleFloorPlanAutoSave();
    });
    planNameInput.dataset.bound = '1';
  }

  var planSelect = document.getElementById('floorPlanSelect');
  if(planSelect && planSelect.dataset.bound !== '1'){
    planSelect.addEventListener('change', async function(){
      var selectedPlanId = planSelect.value;
      if(!selectedPlanId) return;
      // Don't reload if already on this plan
      if(fpState.planId && String(fpState.planId) === String(selectedPlanId) && !fpState._dirty) return;
      if(fpState._dirty){
    var shouldSave = window.confirm('Mevcut planda kaydedilmemiş değişiklikler var. Kaydetmek ister misiniz?');
        if(shouldSave) await saveFloorPlan({silent:true});
      }
      // Cancel pending auto-save
      if(floorPlanAutoSaveTimer){ window.clearTimeout(floorPlanAutoSaveTimer); floorPlanAutoSaveTimer = null; }
      var hid = state.hotelId || state.selectedHotelId;
      try{
        // Always fetch fresh data from API to avoid stale plan content
        var res = await apiFetch('/hotels/' + hid + '/restaurant/floor-plans?include_all=true');
        floorPlanCollection = res.plans || [];
        renderFloorPlanSelect();
        var freshPlan = floorPlanCollection.find(function(item){ return String(item.id) === String(selectedPlanId); });
        if(freshPlan){
          loadFloorPlanFromPayload(freshPlan);
        } else {
          notify('Seçilen plan bulunamadı.', 'warn');
        }
      }catch(e){
        // Fallback to cached version
        var cached = floorPlanCollection.find(function(item){ return String(item.id) === String(selectedPlanId); });
        if(cached) loadFloorPlanFromPayload(cached);
        else notify('Plan yüklenemedi.', 'error');
      }
    });
    planSelect.dataset.bound = '1';
  }

  var newPlanBtn = document.getElementById('createNewFloorPlanBtn');
  if(newPlanBtn && newPlanBtn.dataset.bound !== '1'){
    newPlanBtn.addEventListener('click', async function(){
      // Ask for plan name upfront via inline prompt
      var planName = await showPlanNamePrompt('');
      if(planName === null) return; // cancelled
      // Save current dirty plan before switching
      if(fpState._dirty){
        var shouldSave = window.confirm('Mevcut planda kaydedilmemiş değişiklikler var. Kaydetmek ister misiniz?');
        if(shouldSave) await saveFloorPlan({silent:true});
      }
      // Cancel pending auto-save to prevent stale writes
      if(floorPlanAutoSaveTimer){ window.clearTimeout(floorPlanAutoSaveTimer); floorPlanAutoSaveTimer = null; }
      // Completely fresh state - zero data from previous plan
      fpState = {tables:[],shapes:[],planId:null,planName:planName,counter:0,floorTheme:DEFAULT_FLOOR_THEME,_dirty:false};
      activeShapeEditId = null;
      selectedEl = null;
      undoStack = [];
      applyFloorTheme(DEFAULT_FLOOR_THEME);
      rerenderCanvas();
      syncFloorPlanHeaderFields();
      updateDirtyIndicator();
      var nameInput = document.getElementById('floorPlanNameInput');
      if(nameInput){ nameInput.value = planName; nameInput.focus(); }
      // Deselect in plan list
      var select = document.getElementById('floorPlanSelect');
      if(select) select.value = '';
      notify('Yeni plan "' + escapeHtml(planName) + '" oluşturuldu. Çizime başlayın; değişiklikler otomatik kaydedilir.', 'info');
    });
    newPlanBtn.dataset.bound = '1';
  }

  // Delete plan button
  var delPlanBtn = document.getElementById('deleteFloorPlanBtn');
  if(delPlanBtn && delPlanBtn.dataset.bound !== '1'){
    delPlanBtn.addEventListener('click', async function(){
      if(!fpState.planId){ notify('Silinecek kayıtlı plan yok.','warn'); return; }
      if(!confirm('Bu planı kalıcı olarak silmek istediğinizden emin misiniz? Plan: ' + (fpState.planName || '-'))) return;
      var hid = state.hotelId || state.selectedHotelId;
      try{
        await apiFetch('/hotels/' + hid + '/restaurant/floor-plans/' + fpState.planId, {method:'DELETE'});
        notify('Plan "' + escapeHtml(fpState.planName) + '" silindi.','success');
        fpState = {tables:[],shapes:[],planId:null,planName:'Ana Plan',counter:0,floorTheme:DEFAULT_FLOOR_THEME,_dirty:false};
        activeShapeEditId = null; selectedEl = null; undoStack = [];
        rerenderCanvas();
        await loadFloorPlan();
        await syncFloorPlanToServiceMode();
      }catch(e){
        notify('Plan silinemedi: ' + (e.message||'Bilinmeyen hata'),'error');
      }
    });
    delPlanBtn.dataset.bound = '1';
  }

  // Activate plan button
  var actPlanBtn = document.getElementById('activateFloorPlanBtn');
  if(actPlanBtn && actPlanBtn.dataset.bound !== '1'){
    actPlanBtn.addEventListener('click', async function(){
      if(!fpState.planId){ notify('Aktif yapılacak kayıtlı plan yok.','warn'); return; }
      var hid = state.hotelId || state.selectedHotelId;
      try{
        await apiFetch('/hotels/' + hid + '/restaurant/floor-plans/' + fpState.planId + '/activate', {method:'POST'});
        notify('Plan "' + escapeHtml(fpState.planName) + '" aktif yapıldı.','success');
        await loadFloorPlan();
        await syncFloorPlanToServiceMode();
      }catch(e){
        notify('Plan aktif yapılamadı.','error');
      }
    });
    actPlanBtn.dataset.bound = '1';
  }

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
    if(!confirm('Tüm masaları ve şekilleri silmek istediğinizden emin misiniz?')) return;
    pushUndo();
    fpState.tables = [];
    fpState.shapes = [];
    rerenderCanvas();
    markFloorPlanChanged();
  });

  var floorThemeSelect = document.getElementById('fpFloorTheme');
  if(floorThemeSelect){
    floorThemeSelect.value = fpState.floorTheme || DEFAULT_FLOOR_THEME;
    floorThemeSelect.addEventListener('change', function(){
      pushUndo();
      applyFloorTheme(floorThemeSelect.value || DEFAULT_FLOOR_THEME);
      markFloorPlanChanged();
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
  markFloorPlanChanged();
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
  html += '<button class="tbl-act-btn rot" title="Döndür" aria-label="Döndür">&#x21BB;</button>';
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
  el.innerHTML = '<div class="shape-body" aria-hidden="true"></div><div class="shape-actions"><button class="shape-act-btn edit" title="Şekil düzenle" aria-label="Şekil düzenle" aria-pressed="false">&#x25C8;</button><button class="shape-act-btn rot" title="Döndür" aria-label="Döndür">&#x21BB;</button><button class="shape-act-btn del" title="Sil" aria-label="Sil">&times;</button></div><button class="shape-resize-handle" type="button" aria-label="Boyutlandır"></button>';
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
    markFloorPlanChanged();
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
      markFloorPlanChanged();
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
      markFloorPlanChanged();
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

function loadFloorPlanFromPayload(plan){
  var canvas = document.getElementById('floorPlanCanvas');
  if(!canvas) return;
  // Cancel any pending auto-save before switching plans
  if(floorPlanAutoSaveTimer){ window.clearTimeout(floorPlanAutoSaveTimer); floorPlanAutoSaveTimer = null; }
  canvas.querySelectorAll('.canvas-table,.canvas-shape').forEach(function(el){el.remove();});
  fpState = {tables:[],shapes:[],planId:null,planName:'Ana Plan',counter:0,floorTheme:DEFAULT_FLOOR_THEME,_dirty:false};
  activeShapeEditId = null;
  selectedEl = null;
  undoStack = [];
  applyFloorTheme(DEFAULT_FLOOR_THEME);

  if(!plan || !plan.layout_data){
    syncFloorPlanHeaderFields();
    updateDirtyIndicator();
    return;
  }

  fpState.planId = plan.id || null;
  fpState.planName = String(plan.name || 'Ana Plan');
  fpState._dirty = false;
  var ld = plan.layout_data;
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
  syncFloorPlanHeaderFields();
  updateDirtyIndicator();
}

async function loadFloorPlan(){
  var hid = state.hotelId || state.selectedHotelId;
  if(!hid) return;

  // Remember current plan ID so we can restore it after reload
  var previousPlanId = fpState.planId ? String(fpState.planId) : null;

  try{
    var res = await apiFetch('/hotels/' + hid + '/restaurant/floor-plans?include_all=true');
    floorPlanCollection = res.plans || (res.plan ? [res.plan] : []);
    renderFloorPlanSelect();

    // If we had a plan loaded, try to reload that same plan (preserves editing context)
    if(previousPlanId){
      var samePlan = floorPlanCollection.find(function(p){ return String(p.id) === previousPlanId; });
      if(samePlan){
        loadFloorPlanFromPayload(samePlan);
        return;
      }
    }
    // Otherwise load active plan or first plan
    if(res.plan){
      loadFloorPlanFromPayload(res.plan);
    } else if(floorPlanCollection.length){
      loadFloorPlanFromPayload(floorPlanCollection[0]);
    } else {
      loadFloorPlanFromPayload(null);
    }
  }catch(e){
    loadFloorPlanFromPayload(null);
  }
}

function showPlanNamePrompt(defaultName){
  return new Promise(function(resolve){
    var overlay = document.createElement('div');
    overlay.className = 'fp-name-prompt-overlay';
    overlay.innerHTML = '<div class="fp-name-prompt-box">'
      + '<h4>' + FLOOR_PLAN_NAME_PROMPT_TITLE + '</h4>'
      + '<input type="text" id="fpNamePromptInput" maxlength="80" placeholder="' + FLOOR_PLAN_NAME_PLACEHOLDER + '" value="' + escapeHtml(defaultName || '') + '" autofocus>'
      + '<div class="fp-name-prompt-actions">'
      + '<button class="inline-button secondary" id="fpNamePromptCancel" type="button">İptal</button>'
      + '<button class="inline-button primary" id="fpNamePromptOk" type="button">Kaydet</button>'
      + '</div></div>';
    document.body.appendChild(overlay);
    var input = document.getElementById('fpNamePromptInput');
    if(input) input.focus();
    function cleanup(val){
      if(overlay.parentNode) overlay.parentNode.removeChild(overlay);
      resolve(val);
    }
    document.getElementById('fpNamePromptCancel').addEventListener('click', function(){ cleanup(null); });
    document.getElementById('fpNamePromptOk').addEventListener('click', function(){
      var v = input ? input.value.trim().slice(0,80) : '';
      if(!v){ input.style.borderColor = '#ef4444'; return; }
      cleanup(v);
    });
    if(input) input.addEventListener('keydown', function(e){
      if(e.key === 'Enter'){ e.preventDefault(); document.getElementById('fpNamePromptOk').click(); }
      if(e.key === 'Escape'){ cleanup(null); }
    });
    overlay.addEventListener('click', function(e){ if(e.target === overlay) cleanup(null); });
  });
}

async function saveFloorPlan(options){
  var opts = options || {};
  var hid = state.hotelId || state.selectedHotelId;
  if(!hid){ if(!opts.silent) notify('Otel seçilmedi','error'); return false; }
  // Block auto-save for unnamed new plans to prevent accidental "Ana Plan" entries
  if(opts.fromAutoSave && !fpState.planId && (!fpState.planName || fpState.planName === 'Ana Plan' || fpState.planName === '')){
    return false;
  }

  fpState.planName = getFloorPlanNameInputValue();
  if(!fpState.planName || fpState.planName === 'Ana Plan'){
    // If it's a new plan (no ID) and still has default name, require naming via inline prompt
    if(!fpState.planId && !opts.fromAutoSave){
      var prompted = await showPlanNamePrompt(fpState.planName === 'Ana Plan' ? '' : fpState.planName);
      if(prompted === null) return false;
      fpState.planName = prompted;
      var ni = document.getElementById('floorPlanNameInput');
      if(ni) ni.value = prompted;
    }
  }
  var layout = {
    canvas_width: 1400,
    canvas_height: 1400,
    floor_theme: fpState.floorTheme || DEFAULT_FLOOR_THEME,
    tables: fpState.tables,
    shapes: fpState.shapes
  };

  try{
    var res;
    if(fpState.planId){
      res = await apiFetch('/hotels/' + hid + '/restaurant/floor-plans/' + fpState.planId, {
        method:'PUT',
        body:({name:fpState.planName,layout_data:layout})
      });
    } else {
      res = await apiFetch('/hotels/' + hid + '/restaurant/floor-plans', {
        method:'POST',
        body:({name:fpState.planName || 'Ana Plan',layout_data:layout})
      });
    }
    var data = res;
    if(data.plan){
      fpState.planId = data.plan.id;
      fpState.planName = data.plan.name || fpState.planName;
    }
    fpState._dirty = false;
    floorPlanAutoSaveTimer = null;
    updateDirtyIndicator();
    // Reload full plan list so select dropdown is current
    await loadFloorPlan();
    // Always sync to service mode after save so live view reflects changes
    await syncFloorPlanToServiceMode();
    if(!opts.silent){
      notify('Plan "' + escapeHtml(fpState.planName) + '" kaydedildi','success');
    }
    return true;
  }catch(e){
    floorPlanAutoSaveTimer = null;
    if(!opts.silent){
      notify('Plan kaydedilemedi','error');
    }
    return false;
  }
}

/* ── Service Mode Sync ────────────────────── */

let _syncInProgress = false;

async function syncFloorPlanToServiceMode(){
  // Debounce concurrent calls
  if(_syncInProgress) return;
  _syncInProgress = true;
  try{
    // Always refresh plans cache from API so service mode uses latest version
    var hid = state.hotelId || state.selectedHotelId;
    if(hid){
      var freshRes = await apiFetch('/hotels/' + hid + '/restaurant/floor-plans?include_all=true');
      var freshPlans = freshRes.plans || (freshRes.plan ? [freshRes.plan] : []);
      // Update shared plan collection for editor select
      floorPlanCollection = freshPlans;
      // Update service state plans with deep copy to prevent cross-mutation
      serviceState.plans = JSON.parse(JSON.stringify(freshPlans));
    }
    if(serviceState.open){
      await loadServiceModePlans();
      await loadServiceModeHolds();
      renderServiceMode();
    }
  }catch(e){ /* non-critical: service mode will refresh on next open/poll */ }
  finally{ _syncInProgress = false; }
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
  if(!hid){ notify('Otel seçilmedi','error'); return; }

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
      canvas.innerHTML = '<div class="empty-state">' + DAILY_VIEW_EMPTY_MESSAGE + '</div>';
    }
  }catch(e){
    notify('Günlük görünüm yüklenemedi','error');
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
    if(!hold){ notify('Rezervasyon bulunamadı','error'); return; }

    document.getElementById('tableDetailTitle').textContent = 'Masa Detayı - ' + escapeHtml(holdId);
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
    notify('Detay yüklenemedi','error');
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

      notify('Rezervasyon güncellendi','success');
      dialog.close();
      loadDailyView();
    }catch(e){
      notify('Güncelleme başarısız','error');
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
      var errMsg = e.message || 'Uzatma başarısız';
      notify(errMsg,'error');
    }
  });

  var cancelBtn = document.getElementById('tdCancelBtn');
  if(cancelBtn) cancelBtn.addEventListener('click', async function(){
    var holdId = dialog.dataset.holdId;
    if(!holdId) return;
    if(!confirm('Bu rezervasyonu iptal etmek istediğinizden emin misiniz?')) return;
    try{
      await apiFetch('/holds/restaurant/' + encodeURIComponent(holdId) + '/status', {
        method:'PUT',
        body:({status:'IPTAL',reason:'Yönetici tarafından iptal'})
      });
      notify('Rezervasyon iptal edildi','success');
      dialog.close();
      loadDailyView();
    }catch(e){
      notify('İptal başarısız','error');
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
    createBtn.title = normalized === 'MANUEL' ? 'Manuel modda panelden rezervasyon oluşturma kapalı.' : '';
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
    if(!hid){ notify('Otel seçilmedi','error'); return; }

    var enabled = document.getElementById('dailyCapToggle').checked;
    var count = parseInt(document.getElementById('dailyCapCount').value,10);
    var dailyPartyEnabled = document.getElementById('dailyPartyCapToggle').checked;
    var dailyPartyCount = parseInt(document.getElementById('dailyPartyCapCount').value,10);
    var minParty = parseInt(document.getElementById('restaurantMinPartySize').value,10);
    var maxParty = parseInt(document.getElementById('restaurantMaxPartySize').value,10);
    var chefPhoneEl = document.getElementById('restaurantChefPhone');
    var chefPhone = chefPhoneEl ? chefPhoneEl.value.trim() : '';
    if(isNaN(count) || count < 1){ notify('Geçerli bir günlük rezervasyon sayısı girin','error'); return; }
    if(isNaN(dailyPartyCount) || dailyPartyCount < 1){ notify('Geçerli bir günlük toplam kişi sayısı girin','error'); return; }
    if(isNaN(minParty) || minParty < 1 || isNaN(maxParty) || maxParty < minParty){ notify('Geçerli bir kişi aralığı girin','error'); return; }

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
      notify('Kapasite ayarları kaydedildi','success');
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
  breakfast: {label:'Kahvaltı', start:'08:00', end:'10:30'},
  lunch: {label:'Öğle', start:'12:00', end:'17:00'},
  dinner: {label:'Akşam', start:'18:00', end:'22:00'}
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

function formatLocalDateISO(d){
  var y = d.getFullYear();
  var m = String(d.getMonth() + 1).padStart(2, '0');
  var day = String(d.getDate()).padStart(2, '0');
  return y + '-' + m + '-' + day;
}

function isHoldInMeal(hold, mealKey){
  var meal = resolveMealHours()[mealKey] || SERVICE_MEALS.dinner;
  var holdMins = parseTimeMinutes(hold.time);
  var start = parseTimeMinutes(meal.start);
  var end = parseTimeMinutes(meal.end);
  return holdMins >= start && holdMins <= end;
}

function ensureServiceModeDialogScaffold(){
  var dialog = document.getElementById('serviceModeDialog');
  if(!dialog) return null;
  if(dialog.querySelector('#serviceModeCanvas')) return dialog;

  dialog.classList.add('service-mode-dialog');
  dialog.innerHTML = ''
    + '<div class="service-mode-shell service-mode-v2">'
    + '  <header class="service-mode-header">'
    + '    <div><h3>Servis Modu</h3><p>Operasyon planı (V2 yerleşim)</p></div>'
    + '    <div class="service-mode-actions">'
    + '      <button type="button" id="serviceModePrevDay" class="inline-button secondary" title="Onceki gun (Alt+Sol)">←</button>'
    + '      <input type="date" id="serviceModeDate" aria-label="Servis modu tarihi">'
    + '      <button type="button" id="serviceModeNextDay" class="inline-button secondary" title="Sonraki gun (Alt+Sag)">→</button>'
    + '      <button type="button" id="serviceModeCloseBtn" class="inline-button" aria-label="Servis modunu kapat">Kapat</button>'
    + '    </div>'
    + '  </header>'
    + '  <div class="service-mode-grid-v2">'
    + '    <aside class="service-col service-col-left">'
    + '      <article class="module-card service-panel"><h4>Onaylanan</h4><div id="serviceModeApprovedList" class="service-list"></div></article>'
    + '      <article class="module-card service-panel"><h4>Onay Bekleyen</h4><div id="serviceModePendingList" class="service-list"></div></article>'
    + '      <article class="module-card service-panel service-meta-panel"><h4>Guncel Bilgi</h4><div class="service-meta-row"><strong>Tarih:</strong> <span id="serviceMetaDate">-</span></div><div class="service-meta-row"><strong>Saat:</strong> <span id="serviceMetaTime">-</span></div><div class="service-meta-row"><strong>Chef:</strong> <span id="serviceMetaChef">-</span></div></article>'
    + '    </aside>'
    + '    <section class="service-col service-col-center">'
    + '      <div class="service-mode-canvas-wrap service-panel service-canvas-panel"><div id="serviceModeCanvas" class="floor-plan-canvas service-mode-canvas" aria-label="Servis modu masa planı"></div></div>'
    + '    </section>'
    + '    <aside class="service-col service-col-right">'
    + '      <article class="module-card service-panel">'
    + '        <h4>Yeni Rezervasyon Oluştur</h4>'
    + '        <form id="serviceModeQuickCreateForm" class="dense-form">'
    + '          <div class="field full"><label>Misafir Adı</label><input type="text" placeholder="Ad Soyad"></div>'
    + '          <div class="field"><label>Kişi</label><input type="number" min="1" placeholder="2"></div>'
    + '          <div class="field"><label>Saat</label><input type="time"></div>'
    + '          <div class="field full"><label>Telefon</label><input type="tel" placeholder="+90..."></div>'
    + '          <div class="field full"><label>Not</label><textarea rows="3" placeholder="Opsiyonel not"></textarea></div>'
    + '          <div class="field full"><button type="button" class="inline-button primary">Oluştur (yakında)</button></div>'
    + '        </form>'
    + '      </article>'
    + '    </aside>'
    + '  </div>'
    + '  <div class="service-mode-bottom-v2">'
    + '    <div class="service-bottom-block"><h5>Öğün Seçimi</h5><div class="filter-chips" id="serviceModeMealChips" aria-label="Öğün seçimi"><button type="button" class="filter-chip" data-service-meal="breakfast" title="Kahvaltı (1)">Kahvaltı</button><button type="button" class="filter-chip" data-service-meal="lunch" title="Öğle (2)">Öğle</button><button type="button" class="filter-chip is-active" data-service-meal="dinner" title="Akşam (3)">Akşam</button></div></div>'
    + '    <div class="service-bottom-block"><h5>Diğer Durumlar (Reddedilen / Gelmeyen)</h5><div id="serviceModeOtherList" class="service-list"></div></div>'
    + '    <div class="service-bottom-block"><h5>Plan ve Alan</h5><div class="filter-chips" id="serviceModeAreaChips" aria-label="Alan seçimi"><button type="button" class="filter-chip is-active" data-service-area="main">Ana Mekân</button><button type="button" class="filter-chip" data-service-area="pool">Havuz</button></div><div class="stack" style="gap:8px;align-items:flex-start;margin-top:8px;"><label style="font-size:.78rem;color:var(--muted);">Plan:</label><select id="serviceModePlanSelect" aria-label="Servis modu plan seçimi"></select></div></div>'
    + '    <div class="service-bottom-block"><h5>Masa Ekle (Sürükle)</h5><div id="serviceModeToolbox" class="service-toolbox"></div></div>'
    + '  </div>'
    + '</div>';

  if(typeof bindServiceModeEvents === 'function') bindServiceModeEvents();
  return dialog;
}

async function openServiceMode(){
  var dialog = ensureServiceModeDialogScaffold();
  if(!dialog) return;
  var hid = state.selectedHotelId || state.hotelId;
  if(!hid){ notify('Otel seçin.', 'warn'); return; }

  serviceState.open = true;
  serviceState.date = getOperationalTodayIso();
  serviceState.meal = 'dinner';
  serviceState.area = 'main';
  serviceState.dirty = false;

  var dateInput = document.getElementById('serviceModeDate');
  if(dateInput) dateInput.value = serviceState.date;

  // Open modal immediately; load data in background so API hiccups do not block UI opening.
  // Force a visible fallback for environments where <dialog> behaves inconsistently.
  try{
    if(typeof dialog.showModal === 'function') dialog.showModal();
    else dialog.setAttribute('open', 'open');
  }catch(_err){
    dialog.setAttribute('open', 'open');
  }
  dialog.setAttribute('open', 'open');
  dialog.style.display = 'block';
  dialog.style.position = 'fixed';
  dialog.style.left = '0';
  dialog.style.top = '0';
  dialog.style.right = '0';
  dialog.style.bottom = '0';
  dialog.style.width = '100vw';
  dialog.style.height = '100vh';
  dialog.style.maxWidth = 'none';
  dialog.style.maxHeight = 'none';
  dialog.style.margin = '0';
  dialog.style.padding = '0';
  dialog.style.border = 'none';
  dialog.style.zIndex = '2147483647';

  try{
    await loadServiceModePlans();
    await loadServiceModeHolds();
    renderServiceMode();
    startServiceModePolling();
  }catch(error){
    notify(error.message || 'Servis modu verileri yüklenemedi.', 'error');
    renderServiceMode();
  }
}

async function closeServiceMode(){
  var dialog = document.getElementById('serviceModeDialog');
  if(serviceState.dirty){
    var shouldSave = window.confirm('Kaydedilmemiş plan seçimi var. Kapatmadan önce kaydedilsin mi?');
    if(shouldSave){
      await saveServiceModePlanPrefs();
    }
  }
  stopServiceModePolling();
  serviceState.open = false;
  if(dialog){
    if(dialog.open) dialog.close();
    dialog.style.display = '';
    dialog.style.position = '';
    dialog.style.left = '';
    dialog.style.top = '';
    dialog.style.right = '';
    dialog.style.bottom = '';
    dialog.style.width = '';
    dialog.style.height = '';
    dialog.style.maxWidth = '';
    dialog.style.maxHeight = '';
    dialog.style.margin = '';
    dialog.style.padding = '';
    dialog.style.border = '';
    dialog.style.zIndex = '';
  }
}

function startServiceModePolling(){
  stopServiceModePolling();
  serviceState.pollTimer = window.setInterval(async function(){
    if(!serviceState.open) return;
    await Promise.all([loadServiceModeHolds(), loadServiceModePlans()]);
    renderServiceMode();
  }, 10000);
}

function stopServiceModePolling(){
  if(serviceState.pollTimer){
    window.clearInterval(serviceState.pollTimer);
    serviceState.pollTimer = null;
  }
}

async function loadServiceModePlans(){
  var hid = state.selectedHotelId || state.hotelId;
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
  var hid = state.selectedHotelId || state.hotelId;
  var params = new URLSearchParams();
  params.set('hotel_id', String(hid));
  params.set('date_from', serviceState.date);
  params.set('date_to', serviceState.date);
  params.set('per_page', '100');
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
  var md = document.getElementById('serviceMetaDate');
  var mt = document.getElementById('serviceMetaTime');
  var mc = document.getElementById('serviceMetaChef');
  if(md) md.textContent = serviceState.date || '-';
  if(mt) mt.textContent = new Date().toLocaleTimeString('tr-TR', {hour:'2-digit', minute:'2-digit'});
  if(mc) mc.textContent = (state.restaurantSettings && state.restaurantSettings.chef_phone) ? String(state.restaurantSettings.chef_phone) : '-';
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
    canvas.innerHTML = '<div class="empty-state"><p>Bu alan için plan seçilmedi. Lütfen plan seçin.</p></div>';
    return;
  }
  applyThemeClassToCanvas(canvas, (plan.layout_data && plan.layout_data.floor_theme) || DEFAULT_FLOOR_THEME);
  var tables = (plan.layout_data.tables || []);
  var shapes = (plan.layout_data.shapes || []);
  if(!tables.length && !shapes.length){
    canvas.innerHTML = '<div class="empty-state"><p>Plan boş; henüz masa veya şekil eklenmemiş.</p></div>';
    return;
  }

  /* ── 1. Compute content bounding box ── */
  var minX = Infinity, minY = Infinity, maxX = 0, maxY = 0;
  tables.forEach(function(t){
    var d = TABLE_DIMS[t.type] || {w:72,h:72};
    var x = t.x || 0, y = t.y || 0;
    if(x < minX) minX = x;
    if(y < minY) minY = y;
    if(x + d.w > maxX) maxX = x + d.w;
    if(y + d.h + 18 > maxY) maxY = y + d.h + 18; // +18 for table label
  });
  shapes.forEach(function(s){
    var x = s.x || 0, y = s.y || 0;
    if(x < minX) minX = x;
    if(y < minY) minY = y;
    if(x + (s.width||40) > maxX) maxX = x + (s.width||40);
    if(y + (s.height||40) > maxY) maxY = y + (s.height||40);
  });
  if(minX === Infinity){ minX = 0; minY = 0; maxX = 400; maxY = 400; }
  var PAD = 16;
  var ox = minX - PAD;  // origin offset X
  var oy = minY - PAD;  // origin offset Y
  var contentW = (maxX - minX) + PAD * 2;
  var contentH = (maxY - minY) + PAD * 2;

  /* ── 2. Measure visible viewport ── */
  var rect = canvas.getBoundingClientRect();
  var viewW = rect.width  || canvas.clientWidth  || canvas.offsetWidth  || 600;
  var viewH = rect.height || canvas.clientHeight || canvas.offsetHeight || 560;

  /* ── 3. Calculate scale to fit ── */
  var scale = Math.min(viewW / contentW, viewH / contentH);
  var scaledW = contentW * scale;
  var scaledH = contentH * scale;

  /* ── 4. Create scaler wrapper - centered in viewport ── */
  var scaler = document.createElement('div');
  scaler.className = 'service-canvas-scaler';
  scaler.style.width  = contentW + 'px';
  scaler.style.height = contentH + 'px';
  scaler.style.transform = 'scale(' + scale.toFixed(4) + ')';
  scaler.style.left = Math.round((viewW - scaledW) / 2) + 'px';
  scaler.style.top  = Math.round((viewH - scaledH) / 2) + 'px';

  /* ── 5. Build hold lookup ── */
  var occupiedByTable = {};
  serviceState.holds.filter(function(h){
    return !!h.table_id && isHoldInMeal(h, serviceState.meal) && String(h.date) === serviceState.date;
  }).forEach(function(h){ occupiedByTable[String(h.table_id)] = h; });

  /* ── 6. Render shapes (offset from origin) ── */
  shapes.forEach(function(s){
    var el = document.createElement('div');
    el.className = 'canvas-shape service-shape-locked';
    el.dataset.shape = s.type;
    el.style.left   = ((s.x || 0) - ox) + 'px';
    el.style.top    = ((s.y || 0) - oy) + 'px';
    el.style.width  = (s.width || 40) + 'px';
    el.style.height = (s.height || 40) + 'px';
    el.style.setProperty('--rot', getRotation(s) + 'deg');
    el.innerHTML = '<div class="shape-body" aria-hidden="true"></div>';
    scaler.appendChild(el);
  });

  /* ── 7. Render tables (offset from origin) ── */
  tables.forEach(function(t){
    var svgData = getTableSvg(t.type);
    var el = document.createElement('div');
    el.className = 'canvas-table';
    el.dataset.tableId = t.table_id;
    el.style.left   = ((t.x || 0) - ox) + 'px';
    el.style.top    = ((t.y || 0) - oy) + 'px';
    el.style.width  = svgData.w + 'px';
    el.style.height = svgData.h + 'px';
    el.style.setProperty('--rot', getRotation(t) + 'deg');
    var hold = occupiedByTable[String(t.table_id)];
    if(hold) el.classList.add('st-' + hold.status);
    var html = svgData.svg + '<span class="table-label">' + escapeHtml(t.table_id) + '</span>';
    if(hold){
      html += '<div class="guest-overlay"><div>' + escapeHtml(hold.guest_name || '-') + '</div><div class="guest-time">' + escapeHtml(hold.time || '') + '</div></div>';
    }
    el.innerHTML = html;

    // Hover tooltip with reservation details
    el.addEventListener('mouseenter', function(){
      var existing = el.querySelector('.service-table-tooltip');
      if(existing) existing.remove();
      var tip = document.createElement('div');
      tip.className = 'service-table-tooltip';
      if(hold){
        tip.innerHTML = '<strong>' + escapeHtml(hold.guest_name || '-') + '</strong><br>'
          + escapeHtml(hold.time || '-') + ' · ' + escapeHtml(String(hold.party_size || '-')) + ' kişi<br>'
          + 'Durum: ' + escapeHtml(hold.status || '-')
          + (hold.notes ? '<br>Not: ' + escapeHtml(String(hold.notes).slice(0,60)) : '');
      } else {
        tip.innerHTML = '<strong>' + escapeHtml(t.table_id) + '</strong> - ' + escapeHtml(t.type) + '<br>Boş masa (' + (TABLE_DIMS[t.type]||{}).w + 'px)';
      }
      el.appendChild(tip);
    });
    el.addEventListener('mouseleave', function(){
      var existing = el.querySelector('.service-table-tooltip');
      if(existing) existing.remove();
    });

    // ── Pointer-based drag to move table in service mode ──
    (function(tableEl, tableData, currentScale, originX, originY){
      var isDragging = false;
      var startPX, startPY, origLeft, origTop;
      tableEl.addEventListener('pointerdown', function(e){
        if(e.button === 2) return; // right-click handled by contextmenu
        if(e.target.closest('.tbl-act-btn') || e.target.closest('.service-table-tooltip')) return;
        e.preventDefault();
        isDragging = false;
        startPX = e.clientX; startPY = e.clientY;
        origLeft = parseInt(tableEl.style.left, 10) || 0;
        origTop  = parseInt(tableEl.style.top, 10) || 0;
        tableEl.setPointerCapture(e.pointerId);

        function onMove(ev){
          var dx = (ev.clientX - startPX) / currentScale;
          var dy = (ev.clientY - startPY) / currentScale;
          if(!isDragging && (Math.abs(dx) > 3 || Math.abs(dy) > 3)) isDragging = true;
          if(!isDragging) return;
          // Remove tooltip while dragging
          var tip = tableEl.querySelector('.service-table-tooltip');
          if(tip) tip.remove();
          var nx = Math.max(0, Math.round((origLeft + dx) / 20) * 20);
          var ny = Math.max(0, Math.round((origTop + dy) / 20) * 20);
          tableEl.style.left = nx + 'px';
          tableEl.style.top  = ny + 'px';
        }
        function onUp(ev){
          tableEl.releasePointerCapture(ev.pointerId);
          tableEl.removeEventListener('pointermove', onMove);
          tableEl.removeEventListener('pointerup', onUp);
          if(!isDragging) return; // was a click, not a drag
          var finalLeft = parseInt(tableEl.style.left, 10) || 0;
          var finalTop  = parseInt(tableEl.style.top, 10) || 0;
          // Convert back to plan coordinates (add origin offset)
          var newX = finalLeft + originX;
          var newY = finalTop + originY;
          saveServiceTablePosition(tableData.table_id, newX, newY);
        }
        tableEl.addEventListener('pointermove', onMove);
        tableEl.addEventListener('pointerup', onUp);
      });
    })(el, t, scale, ox, oy);

    // Right-click context menu (all tables - with or without hold)
    (function(tableEl, tableData, tableHold){
      tableEl.addEventListener('contextmenu', function(e){
        openSvcTableContextMenu(e, tableData, tableHold || null);
      });
      // Left-click on occupied table also opens context menu for quick actions
      if(tableHold){
        tableEl.addEventListener('click', function(e){
          if(e.target.closest('.tbl-act-btn') || e.target.closest('.service-table-tooltip')) return;
          openSvcTableContextMenu(e, tableData, tableHold);
        });
      }
    })(el, t, hold);
    el.addEventListener('dragover', function(ev){ ev.preventDefault(); el.classList.add('service-table-drop'); });
    el.addEventListener('dragleave', function(){ el.classList.remove('service-table-drop'); });
    el.addEventListener('drop', async function(ev){
      ev.preventDefault();
      ev.stopPropagation();
      el.classList.remove('service-table-drop');
      var holdId = ev.dataTransfer.getData('text/plain');
      if(!holdId) return;
      await assignHoldToServiceTable(holdId, t);
    });
    scaler.appendChild(el);
  });

  /* ── 8. Append scaler to canvas ── */
  canvas.appendChild(scaler);

  /* ── 8b. Table type legend overlay (bottom-right, draggable) ── */
  var legend = document.createElement('div');
  legend.className = 'service-table-legend';
  legend.innerHTML = '<h6>Masa Tipleri</h6>';
  var legendTypes = [
    {type:'TABLE_2', capacity:2, label:'2 Kişilik', svg:miniSvg2()},
    {type:'TABLE_4', capacity:4, label:'4 Kişilik', svg:miniSvg4()},
    {type:'TABLE_6', capacity:6, label:'6 Kişilik', svg:miniSvg6()},
    {type:'TABLE_8', capacity:8, label:'8 Kişilik', svg:miniSvg8()},
    {type:'TABLE_10', capacity:10, label:'10 Kişilik', svg:miniSvg10()}
  ];
  legendTypes.forEach(function(lt){
    var row = document.createElement('div');
    row.className = 'service-legend-row';
    row.draggable = true;
    row.setAttribute('aria-label', lt.label + ' masa sürükle');
    row.innerHTML = lt.svg + '<span>' + escapeHtml(lt.label) + '</span>';
    row.addEventListener('dragstart', function(ev){
      ev.dataTransfer.setData('application/velox-table', JSON.stringify({type:lt.type, capacity:lt.capacity}));
      ev.dataTransfer.setData('text/plain', '');
    });
    legend.appendChild(row);
  });
  canvas.appendChild(legend);

  /* ── 9. Canvas-level drop: toolbox tables + reservation fallback ── */
  canvas.ondragover = function(ev){ ev.preventDefault(); };
  canvas.ondrop = async function(ev){
    ev.preventDefault();

    /* ── 9a. Toolbox table drop (new table onto canvas) ── */
    var tableData = ev.dataTransfer.getData('application/velox-table');
    if(tableData){
      var info;
      try{ info = JSON.parse(tableData); }catch{ return; }
      var canvasRect2 = canvas.getBoundingClientRect();
      var dropX = (ev.clientX - canvasRect2.left - parseFloat(scaler.style.left || 0)) / scale + ox;
      var dropY = (ev.clientY - canvasRect2.top - parseFloat(scaler.style.top || 0)) / scale + oy;
      dropX = Math.round(dropX / 20) * 20;
      dropY = Math.round(dropY / 20) * 20;
      var tableId = window.prompt('Masa numarası girin:', 'T' + info.capacity + '-' + Math.floor(Math.random()*100));
      if(!tableId) return;
      var activePlan = getServiceActivePlan();
      if(!activePlan || !activePlan.id) return;
      var hid = state.selectedHotelId || state.hotelId;
      var newTable = {table_id:tableId.trim().toUpperCase(), type:info.type, capacity:info.capacity, x:dropX, y:dropY, rotation:0, label:tableId.trim().toUpperCase()};
      var updatedTables = (activePlan.layout_data.tables || []).concat([newTable]);
      var updatedLayout = Object.assign({}, activePlan.layout_data, {tables:updatedTables});
      try{
        await apiFetch('/hotels/' + hid + '/restaurant/floor-plans/' + activePlan.id, {method:'PUT', body:{layout_data:updatedLayout}});
        notify('Masa ' + tableId + ' plana eklendi.', 'success');
        await loadServiceModePlans();
        renderServiceMode();
      }catch(e){ notify(e.message || 'Masa eklenemedi.', 'error'); }
      return;
    }

    /* ── 9b. Reservation hold drop - fallback when per-table handler missed
             (CSS transform scale can shift hit-test areas in some browsers) ── */
    var holdId = ev.dataTransfer.getData('text/plain');
    if(!holdId) return;
    var canvasRect3 = canvas.getBoundingClientRect();
    var scalerLeft = parseFloat(scaler.style.left || 0);
    var scalerTop  = parseFloat(scaler.style.top || 0);
    var planX = (ev.clientX - canvasRect3.left - scalerLeft) / scale + ox;
    var planY = (ev.clientY - canvasRect3.top - scalerTop) / scale + oy;
    // Find closest table within hit tolerance
    var hitTable = null;
    var hitDist  = Infinity;
    var HIT_PAD  = 20; // px tolerance around table edges
    tables.forEach(function(t){
      var d = TABLE_DIMS[t.type] || {w:72,h:72};
      var tx = t.x || 0, ty = t.y || 0;
      if(planX >= tx - HIT_PAD && planX <= tx + d.w + HIT_PAD && planY >= ty - HIT_PAD && planY <= ty + d.h + HIT_PAD){
        var cx = tx + d.w / 2, cy = ty + d.h / 2;
        var dist = Math.abs(planX - cx) + Math.abs(planY - cy);
        if(dist < hitDist){ hitDist = dist; hitTable = t; }
      }
    });
    if(hitTable){
      await assignHoldToServiceTable(holdId, hitTable);
    } else {
      notify('Lütfen rezervasyonu bir masanın üzerine bırakın.', 'warn');
    }
  };
}

function renderServiceReservationLists(){
  var approved = document.getElementById('serviceModeApprovedList');
  var pending = document.getElementById('serviceModePendingList');
  var other = document.getElementById('serviceModeOtherList');
  if(!approved || !pending || !other) return;
  var rows = (serviceState.holds || []).filter(function(item){
    return String(item.date) === serviceState.date && isHoldInMeal(item, serviceState.meal);
  });
  // Approved items that are already assigned to a table don't show in the list (they appear on canvas)
  var approvedRows = rows.filter(function(item){ return item.status === 'ONAYLANDI' && !item.table_id; });
  var pendingRows = rows.filter(function(item){ return item.status === 'BEKLEMEDE' || item.status === 'PENDING_APPROVAL'; });
  var otherRows = rows.filter(function(item){ return item.status !== 'ONAYLANDI' && item.status !== 'BEKLEMEDE' && item.status !== 'PENDING_APPROVAL'; });
  approved.innerHTML = renderServiceHoldCards(approvedRows, true);
  pending.innerHTML = renderServiceHoldCards(pendingRows, true);
  other.innerHTML = renderServiceHoldCards(otherRows, false);
}

function renderServiceHoldCards(items, draggable){
  if(!items.length) return '<div class="empty-state"><p>Kayıt yok.</p></div>';
  return items.map(function(item){
    return '<article class="service-reservation-card" draggable="' + (draggable ? 'true' : 'false') + '" data-service-hold-id="' + escapeHtml(item.hold_id) + '">'
      + '<strong>' + escapeHtml(item.guest_name || item.hold_id) + '</strong>'
      + '<small>' + escapeHtml(item.time || '-') + ' · ' + escapeHtml(item.party_size || '-') + ' kişi</small>'
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
    notify('Rezervasyon masaya atandı.', 'success');
    await loadServiceModeHolds();
    renderServiceMode();
  }catch(error){
    notify(error.message || 'Masa ataması başarısız.', 'error');
  }
}

async function saveServiceTablePosition(tableId, newX, newY){
  var activePlan = getServiceActivePlan();
  if(!activePlan || !activePlan.id || !activePlan.layout_data) return;
  var hid = state.selectedHotelId || state.hotelId;
  var tables = (activePlan.layout_data.tables || []).map(function(t){
    if(t.table_id === tableId) return Object.assign({}, t, {x: newX, y: newY});
    return t;
  });
  var updatedLayout = Object.assign({}, activePlan.layout_data, {tables: tables});
  try{
    await apiFetch('/hotels/' + hid + '/restaurant/floor-plans/' + activePlan.id, {method:'PUT', body:{layout_data: updatedLayout}});
    // Update local cache so next render uses new position
    activePlan.layout_data = updatedLayout;
  }catch(e){ notify(e.message || 'Masa konumu kaydedilemedi.', 'error'); }
}

/* ═══════════════════════════════════════════════════════
   Service Mode - Context Menu + Confirm Modals
   ═══════════════════════════════════════════════════════ */

// ── Singleton DOM helpers ──────────────────────────────
function getOrCreateCtxMenu(){
  var el = document.getElementById('svcCtxMenu');
  if(el) return el;
  el = document.createElement('div');
  el.id = 'svcCtxMenu';
  el.className = 'svc-ctx-menu';
  el.setAttribute('role', 'menu');
  el.setAttribute('aria-label', 'Masa işlemleri');
  document.body.appendChild(el);
  return el;
}

function getOrCreateConfirm(){
  var el = document.getElementById('svcConfirmBackdrop');
  if(el) return el;
  el = document.createElement('div');
  el.id = 'svcConfirmBackdrop';
  el.className = 'svc-confirm-backdrop';
  document.body.appendChild(el);
  return el;
}

// ── Close context menu ─────────────────────────────────
function closeSvcCtxMenu(){
  var m = document.getElementById('svcCtxMenu');
  if(m) m.classList.remove('is-visible');
}

function closeSvcConfirm(){
  var b = document.getElementById('svcConfirmBackdrop');
  if(b){ b.classList.remove('is-visible'); b.innerHTML = ''; }
}

// Global click-away & Escape
if(!window.__svcCtxGlobalBound){
  window.__svcCtxGlobalBound = true;
  document.addEventListener('pointerdown', function(ev){
    var m = document.getElementById('svcCtxMenu');
    if(m && m.classList.contains('is-visible') && !m.contains(ev.target)) closeSvcCtxMenu();
  });
  document.addEventListener('keydown', function(ev){
    if(ev.key === 'Escape'){
      closeSvcCtxMenu();
      closeSvcConfirm();
    }
  });
  document.addEventListener('scroll', closeSvcCtxMenu, true);
}

// ── Validate target table ID ───────────────────────────
function validateMoveTarget(targetId, currentTableId){
  var id = String(targetId || '').trim().toUpperCase();
  if(!id) return {ok:false, error:'Masa numarası boş bırakılamaz.'};
  if(id === String(currentTableId || '').trim().toUpperCase()) return {ok:false, error:'Aynı masa numarası; farklı bir masa seçin.'};
  var plan = getServiceActivePlan();
  if(!plan || !plan.layout_data) return {ok:false, error:'Aktif plan bulunamadı.'};
  var found = (plan.layout_data.tables || []).find(function(t){ return String(t.table_id || '').trim().toUpperCase() === id; });
  if(!found) return {ok:false, error:'Planda "' + id + '" numaralı masa bulunamadı.'};
  // Check if target table already has a hold for this meal/date
  var occupied = (serviceState.holds || []).find(function(h){
    return String(h.table_id || '').trim().toUpperCase() === id
      && String(h.date) === serviceState.date
      && isHoldInMeal(h, serviceState.meal)
      && h.status !== 'IPTAL' && h.status !== 'GELMEDI';
  });
  if(occupied) return {ok:false, error:'Masa "' + id + '" bu öğün için zaten dolu (' + escapeHtml(occupied.guest_name || occupied.hold_id) + ').'};
  return {ok:true, tableData:found, cleanId:id};
}

// ── Remove table from plan ─────────────────────────────
async function removeTableFromPlan(tableId){
  var plan = getServiceActivePlan();
  if(!plan || !plan.id || !plan.layout_data) return;
  var hid = state.selectedHotelId || state.hotelId;
  var updated = (plan.layout_data.tables || []).filter(function(t){ return t.table_id !== tableId; });
  var layout = Object.assign({}, plan.layout_data, {tables:updated});
  await apiFetch('/hotels/' + hid + '/restaurant/floor-plans/' + plan.id, {method:'PUT', body:{layout_data:layout}});
  plan.layout_data = layout;
}

// ── Move reservation to another table ──────────────────
async function moveHoldToTable(holdId, targetTableData){
  await apiFetch('/holds/restaurant/' + encodeURIComponent(holdId), {
    method:'PUT',
    body:{table_id:String(targetTableData.table_id), table_type:String(targetTableData.type || '')}
  });
}

// ── Show confirm modal: reservation exists on table ────
function showRemoveTableConfirm(hold, table){
  var backdrop = getOrCreateConfirm();
  backdrop.innerHTML = ''
    + '<div class="svc-confirm-box">'
    + '  <div class="svc-confirm-head">'
    + '    <h4>Masa ' + escapeHtml(table.table_id) + ' \u2014 Aktif Rezervasyon</h4>'
    + '    <p><strong>' + escapeHtml(hold.guest_name || hold.hold_id) + '</strong> için '
    + escapeHtml(hold.time || '-') + ' saatinde ' + escapeHtml(String(hold.party_size || '-'))
    + ' kişilik aktif rezervasyon mevcut. Masayı kaldırmadan önce ne yapmak istiyorsunuz?</p>'
    + '  </div>'
    + '  <div class="svc-confirm-body">'
    + '    <div class="svc-confirm-option" data-action="remove-hold" tabindex="0" role="button">'
    + '      <div class="opt-icon opt-remove">\u2716</div>'
    + '      <div class="opt-text"><strong>Rezervasyonu kaldır</strong><span>Rezervasyon iptal edilir ve masa plandan kaldırılır</span></div>'
    + '    </div>'
    + '    <div class="svc-confirm-option" data-action="move-hold" tabindex="0" role="button">'
    + '      <div class="opt-icon opt-move">\u21C4</div>'
    + '      <div class="opt-text"><strong>Başka masaya taşı</strong><span>Rezervasyon yeni masaya aktarılır, bu masa plandan kaldırılır</span></div>'
    + '    </div>'
    + '  </div>'
    + '  <div class="svc-confirm-foot">'
    + '    <button type="button" class="svc-cancel-btn" data-action="cancel">Vazgeç</button>'
    + '  </div>'
    + '</div>';

  backdrop.classList.add('is-visible');

  backdrop.addEventListener('click', async function handler(ev){
    var opt = ev.target.closest('[data-action]');
    if(!opt) return;
    var act = opt.dataset.action;

    if(act === 'cancel'){
      closeSvcConfirm();
      backdrop.removeEventListener('click', handler);
      return;
    }

    if(act === 'remove-hold'){
      closeSvcConfirm();
      backdrop.removeEventListener('click', handler);
      try{
        await apiFetch('/holds/restaurant/' + encodeURIComponent(hold.hold_id) + '/status', {
          method:'PUT', body:{status:'IPTAL', reason:'Servis modu - masa kaldırıldı, rezervasyon iptal'}
        });
        await removeTableFromPlan(table.table_id);
        notify('Rezervasyon iptal edildi, masa plandan kaldırıldı.', 'success');
        await loadServiceModeHolds();
        await loadServiceModePlans();
        renderServiceMode();
      }catch(e){ notify(e.message || 'İşlem başarısız.', 'error'); }
      return;
    }

    if(act === 'move-hold'){
      closeSvcConfirm();
      backdrop.removeEventListener('click', handler);
      showMoveHoldModal(hold, table, true); // removeAfterMove = true
      return;
    }
  });
}

// ── Show move-to-table modal ───────────────────────────
function showMoveHoldModal(hold, currentTable, removeAfterMove){
  var backdrop = getOrCreateConfirm();
  var title = removeAfterMove
    ? 'Rezervasyonu Taşı ve Masayı Kaldır'
    : 'Rezervasyonu Başka Masaya Taşı';
  var desc = '<strong>' + escapeHtml(hold.guest_name || hold.hold_id) + '</strong> - '
    + escapeHtml(hold.time || '-') + ', ' + escapeHtml(String(hold.party_size || '-')) + ' kişi';

  backdrop.innerHTML = ''
    + '<div class="svc-confirm-box">'
    + '  <div class="svc-confirm-head">'
    + '    <h4>' + title + '</h4>'
    + '    <p>' + desc + '</p>'
    + '  </div>'
    + '  <div class="svc-confirm-body">'
    + '    <label style="font-size:.76rem;color:var(--muted);">Hedef masa numarası</label>'
    + '    <div class="svc-move-input-group">'
    + '      <input type="text" class="svc-move-input" id="svcMoveTargetInput" placeholder="Örnek: A3, T4-12" autocomplete="off" spellcheck="false">'
    + '      <button type="button" class="svc-move-submit" id="svcMoveSubmitBtn">Taşı</button>'
    + '    </div>'
    + '    <div class="svc-move-error" id="svcMoveError"></div>'
    + '  </div>'
    + '  <div class="svc-confirm-foot">'
    + '    <button type="button" class="svc-cancel-btn" id="svcMoveCancelBtn">Vazgeç</button>'
    + '  </div>'
    + '</div>';

  backdrop.classList.add('is-visible');

  var input = document.getElementById('svcMoveTargetInput');
  var submitBtn = document.getElementById('svcMoveSubmitBtn');
  var errorEl = document.getElementById('svcMoveError');
  var cancelBtn = document.getElementById('svcMoveCancelBtn');

  setTimeout(function(){ if(input) input.focus(); }, 80);

  async function doMove(){
    if(!input || !submitBtn) return;
    var val = input.value;
    var v = validateMoveTarget(val, currentTable.table_id);
    if(!v.ok){
      errorEl.textContent = v.error;
      input.classList.add('has-error');
      input.focus();
      return;
    }
    input.classList.remove('has-error');
    errorEl.textContent = '';
    submitBtn.disabled = true;
    submitBtn.textContent = 'Taşınıyor...';
    try{
      await moveHoldToTable(hold.hold_id, v.tableData);
      if(removeAfterMove){
        await removeTableFromPlan(currentTable.table_id);
        notify('Rezervasyon ' + v.cleanId + ' masasına taşındı, eski masa kaldırıldı.', 'success');
        await loadServiceModePlans();
      } else {
        notify('Rezervasyon ' + v.cleanId + ' masasına taşındı.', 'success');
      }
      closeSvcConfirm();
      await loadServiceModeHolds();
      renderServiceMode();
    }catch(e){
      submitBtn.disabled = false;
      submitBtn.textContent = 'Taşı';
      errorEl.textContent = e.message || 'Taşıma başarısız.';
    }
  }

  submitBtn.addEventListener('click', doMove);
  input.addEventListener('keydown', function(ev){
    if(ev.key === 'Enter'){ ev.preventDefault(); doMove(); }
  });
  input.addEventListener('input', function(){
    input.classList.remove('has-error');
    errorEl.textContent = '';
  });
  cancelBtn.addEventListener('click', function(){ closeSvcConfirm(); });
}

// ── Open context menu on a service mode table ──────────
function openSvcTableContextMenu(ev, table, hold){
  ev.preventDefault();
  ev.stopPropagation();
  closeSvcCtxMenu(); // close any existing

  var menu = getOrCreateCtxMenu();
  var headerLabel = escapeHtml(table.table_id) + (hold ? (' \u2014 ' + escapeHtml(hold.guest_name || hold.hold_id)) : ' \u2014 Boş');

  var items = '';

  if(hold){
    items += ''
      + '<button class="svc-ctx-item" data-ctx="swap" role="menuitem">'
      + '  <span class="ctx-icon icon-swap">\u21C4</span>'
      + '  <span class="ctx-label">Değiştir<small>Rezervasyonu başka masaya taşı</small></span>'
      + '</button>'
      + '<button class="svc-ctx-item" data-ctx="unassign" role="menuitem">'
      + '  <span class="ctx-icon icon-remove">\u2716</span>'
      + '  <span class="ctx-label">Masa Atamasını Kaldır<small>Rezervasyon listeye döner</small></span>'
      + '</button>'
      + '<div class="svc-ctx-sep"></div>'
      + '<button class="svc-ctx-item ctx-danger" data-ctx="cancel-hold" role="menuitem">'
      + '  <span class="ctx-icon icon-cancel">\u26A0</span>'
      + '  <span class="ctx-label">Rezervasyonu İptal Et<small>Tamamen iptal edilir</small></span>'
      + '</button>';
  }

  items += '<div class="svc-ctx-sep"></div>'
    + '<button class="svc-ctx-item ctx-danger" data-ctx="remove-table" role="menuitem">'
    + '  <span class="ctx-icon icon-remove">\u2716</span>'
    + '  <span class="ctx-label">Masayı Plandan Kaldır<small>Masa kalıcı olarak silinir</small></span>'
    + '</button>';

  menu.innerHTML = '<div class="svc-ctx-menu-header">' + headerLabel + '</div>' + items;

  // Position menu at cursor, keep within viewport
  var mx = ev.clientX, my = ev.clientY;
  menu.style.left = '0px';
  menu.style.top = '0px';
  menu.classList.add('is-visible');
  var rect = menu.getBoundingClientRect();
  var vw = window.innerWidth, vh = window.innerHeight;
  if(mx + rect.width > vw - 8) mx = vw - rect.width - 8;
  if(my + rect.height > vh - 8) my = vh - rect.height - 8;
  if(mx < 4) mx = 4;
  if(my < 4) my = 4;
  menu.style.left = mx + 'px';
  menu.style.top  = my + 'px';

  // Handle menu item click
  menu.addEventListener('click', async function handler(clickEv){
    var btn = clickEv.target.closest('[data-ctx]');
    if(!btn) return;
    var action = btn.dataset.ctx;
    closeSvcCtxMenu();
    menu.removeEventListener('click', handler);

    try{
      if(action === 'swap' && hold){
        showMoveHoldModal(hold, table, false);

      } else if(action === 'unassign' && hold){
        await apiFetch('/holds/restaurant/' + encodeURIComponent(hold.hold_id), {
          method:'PUT', body:{table_id:''}
        });
        notify('Masa ataması kaldırıldı; rezervasyon listeye döndü.', 'success');
        await loadServiceModeHolds();
        renderServiceMode();

      } else if(action === 'cancel-hold' && hold){
        await apiFetch('/holds/restaurant/' + encodeURIComponent(hold.hold_id) + '/status', {
          method:'PUT', body:{status:'IPTAL', reason:'Servis modu bağlam menüsü - iptal'}
        });
        notify('Rezervasyon iptal edildi.', 'success');
        await loadServiceModeHolds();
        renderServiceMode();

      } else if(action === 'remove-table'){
        if(hold){
          showRemoveTableConfirm(hold, table);
        } else {
          await removeTableFromPlan(table.table_id);
          notify('Masa "' + table.table_id + '" plandan kaldırıldı.', 'success');
          await loadServiceModePlans();
          renderServiceMode();
        }
      }
    }catch(e){ notify(e.message || 'İşlem başarısız.', 'error'); }
  });
}

async function saveServiceModePlanPrefs(){
  var hid = state.selectedHotelId || state.hotelId;
  if(!hid) return;
  try{
    await apiFetch('/hotels/' + hid + '/restaurant/settings', {
      method:'PUT',
      body:({
        service_mode_main_plan_id: serviceState.selectedPlanByArea.main || null,
        service_mode_pool_plan_id: serviceState.selectedPlanByArea.pool || null
      })
    });
    serviceState.dirty = false;
    notify('Servis modu plan seçimleri kaydedildi.', 'success');
  }catch(error){
    notify(error.message || 'Plan seçimi kaydedilemedi.', 'error');
  }
}

function bindServiceModeEvents(){
  var openBtn = document.getElementById('openServiceModeBtn');
  if(openBtn && openBtn.dataset.serviceModeBound !== '1'){
    openBtn.addEventListener('click', openServiceMode);
    openBtn.dataset.serviceModeBound = '1';
  }
  var closeBtn = document.getElementById('serviceModeCloseBtn');
  if(closeBtn){
    closeBtn.onclick = closeServiceMode;
  }

  var dateInput = document.getElementById('serviceModeDate');
  if(dateInput){
    dateInput.onchange = async function(){
      serviceState.date = dateInput.value || getOperationalTodayIso();
      await loadServiceModeHolds();
      renderServiceMode();
    };
  }

  var prevDay = document.getElementById('serviceModePrevDay');
  if(prevDay){
    prevDay.onclick = async function(){
      var d = new Date(serviceState.date + 'T00:00:00');
      d.setDate(d.getDate() - 1);
      serviceState.date = formatLocalDateISO(d);
      if(dateInput) dateInput.value = serviceState.date;
      await loadServiceModeHolds();
      renderServiceMode();
    };
  }
  var nextDay = document.getElementById('serviceModeNextDay');
  if(nextDay){
    nextDay.onclick = async function(){
      var d = new Date(serviceState.date + 'T00:00:00');
      d.setDate(d.getDate() + 1);
      serviceState.date = formatLocalDateISO(d);
      if(dateInput) dateInput.value = serviceState.date;
      await loadServiceModeHolds();
      renderServiceMode();
    };
  }

  document.querySelectorAll('#serviceModeMealChips [data-service-meal]').forEach(function(btn){
    if(btn.dataset.serviceModeBound === '1') return;
    btn.addEventListener('click', function(){ serviceState.meal = btn.dataset.serviceMeal; renderServiceMode(); });
    btn.dataset.serviceModeBound = '1';
  });
  document.querySelectorAll('#serviceModeAreaChips [data-service-area]').forEach(function(btn){
    if(btn.dataset.serviceModeBound === '1') return;
    btn.addEventListener('click', async function(){
      if(serviceState.dirty){
        var shouldSave = window.confirm('Plan seçimi değişti. Alan değiştirmeden önce kaydedilsin mi?');
        if(shouldSave){
          await saveServiceModePlanPrefs();
        }
      }
      serviceState.area = btn.dataset.serviceArea;
      renderServiceMode();
    });
    btn.dataset.serviceModeBound = '1';
  });

  var planSelect = document.getElementById('serviceModePlanSelect');
  if(planSelect && planSelect.dataset.serviceModeBound !== '1'){
    planSelect.addEventListener('change', async function(){
      serviceState.selectedPlanByArea[serviceState.area] = planSelect.value;
      serviceState.dirty = true;
      await saveServiceModePlanPrefs();
      renderServiceMode();
    });
    planSelect.dataset.serviceModeBound = '1';
  }

  // Render service mode toolbox (draggable table types)
  var toolboxEl = document.getElementById('serviceModeToolbox');
  if(toolboxEl && !toolboxEl.dataset.bound){
    toolboxEl.dataset.bound = '1';
    var tableTypes = [
      {type:'TABLE_2', capacity:2, label:'2 Kişilik', svg:miniSvg2()},
      {type:'TABLE_4', capacity:4, label:'4 Kişilik', svg:miniSvg4()},
      {type:'TABLE_6', capacity:6, label:'6 Kişilik', svg:miniSvg6()},
      {type:'TABLE_8', capacity:8, label:'8 Kişilik', svg:miniSvg8()},
      {type:'TABLE_10', capacity:10, label:'10 Kişilik', svg:miniSvg10()}
    ];
    tableTypes.forEach(function(tt){
      var item = document.createElement('div');
      item.className = 'service-toolbox-item';
      item.draggable = true;
      item.innerHTML = '<span class="toolbox-preview">' + tt.svg + '</span> ' + escapeHtml(tt.label);
      item.addEventListener('dragstart', function(ev){
        ev.dataTransfer.setData('application/velox-table', JSON.stringify({type:tt.type, capacity:tt.capacity}));
        ev.dataTransfer.setData('text/plain', '');
      });
      toolboxEl.appendChild(item);
    });
  }

  if(!window.__veloxServiceModeDocBound){
    window.__veloxServiceModeDocBound = true;

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
      serviceState.date = formatLocalDateISO(d1);
      var di1 = document.getElementById('serviceModeDate');
      if(di1) di1.value = serviceState.date;
      await loadServiceModeHolds();
      renderServiceMode();
    }
    if(ev.altKey && ev.key === 'ArrowRight'){
      ev.preventDefault();
      var d2 = new Date(serviceState.date + 'T00:00:00');
      d2.setDate(d2.getDate() + 1);
      serviceState.date = formatLocalDateISO(d2);
      var di2 = document.getElementById('serviceModeDate');
      if(di2) di2.value = serviceState.date;
      await loadServiceModeHolds();
      renderServiceMode();
    }
    });
  }
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
function _safeInitOnReady(){
  try{
    _initOnReady();
  }catch(err){
    console.error('[Velox] restaurant init error:', err);
  }
}
if(document.readyState === 'loading'){
  document.addEventListener('DOMContentLoaded', _safeInitOnReady);
} else {
  _safeInitOnReady();
}

// Global fallback: even if module init order changes, button click still opens service mode.
document.addEventListener('click', function(e){
  var btn = e.target && e.target.closest ? e.target.closest('#openServiceModeBtn') : null;
  if(!btn) return;
  e.preventDefault();
  openServiceMode();
});
window.__veloxOpenServiceMode = openServiceMode;

})();
"""
