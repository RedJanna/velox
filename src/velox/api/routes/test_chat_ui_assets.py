"""Static assets for the Chat Lab HTML interface."""

# ruff: noqa: E501, S608

from velox.api.routes.ui_shared_assets import UI_SHARED_SCRIPT

TEST_CHAT_STYLE = """\
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --navy:#12213b;--ink:#0f172a;--muted:#64748b;--muted-2:#9aa7b8;--paper:#fff;
  --paper-soft:#f8fafc;--sand:#f6f2e8;--line:#d6dce8;--teal:#15756f;--teal-2:#2a9d8f;--amber:#e7bf5f;
  --red:#dc2626;--shadow:0 18px 36px rgba(15,23,42,.12);--mono:'Cascadia Code','Fira Code',monospace;
  --text-xs:12px;--text-sm:13px;--text-md:15px;--text-lg:17px;--text-xl:20px;
  --space-1:4px;--space-2:8px;--space-3:12px;--space-4:16px;--space-5:20px;--space-6:24px;--space-7:30px;
  --control-h:44px;--chip-h:34px;
}
html,body{height:100%;font-size:16px;font-family:'Segoe UI Variable','Aptos','Segoe UI',system-ui,sans-serif;background:
radial-gradient(circle at top left,rgba(231,191,95,.18),transparent 24%),
radial-gradient(circle at right top,rgba(21,117,111,.07),transparent 22%),
linear-gradient(180deg,#f7f4ec 0%,#eef3f8 100%);color:var(--ink)}
body{overflow:hidden}
.app{display:flex;flex-direction:column;height:100dvh;min-height:0}
.app.is-workspace-dimmed{filter:saturate(.94) brightness(.985);transition:filter .18s ease}
.header{display:flex;align-items:flex-start;gap:var(--space-5);padding:18px 24px;border-bottom:1px solid rgba(18,33,59,.08);background:rgba(255,255,255,.78);backdrop-filter:blur(18px)}
.header-brand{display:grid;grid-template-columns:auto 1fr;grid-template-areas:'icon copy' '. badge';gap:12px 14px}
.header-brand > svg{grid-area:icon}
.header-copy{grid-area:copy}
.header-copy h1{font-size:var(--text-xl);font-weight:800;letter-spacing:.01em;line-height:1.2}
.header-copy p{font-size:13px;line-height:1.55;color:var(--muted);margin-top:4px;max-width:46ch}
.field{display:flex;align-items:center;gap:8px}
.field label{font-size:11px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.header-select,.header-input,.input-bar textarea,.debug-input,.debug-select,.debug-textarea{
  border:1px solid rgba(18,33,59,.12);border-radius:16px;background:rgba(255,255,255,.97);color:var(--ink);outline:none;
  transition:border-color .18s ease,box-shadow .18s ease
}
.header-select,.header-input{height:var(--control-h);padding:0 14px;font-size:13px}
.header-select:focus,.header-input:focus,.input-bar textarea:focus,.debug-input:focus,.debug-select:focus,.debug-textarea:focus{
  border-color:var(--teal);box-shadow:0 0 0 3px rgba(21,117,111,.12)
}
.btn:focus-visible,.header-select:focus-visible,.header-input:focus-visible,.input-bar textarea:focus-visible,.debug-input:focus-visible,.debug-select:focus-visible,.debug-textarea:focus-visible{
  outline:2px solid rgba(231,191,95,.9);outline-offset:2px
}
.header-select-model,.header-select-import,.header-input{width:100%}
.btn{height:var(--control-h);border:none;border-radius:14px;padding:0 14px;font-size:13px;font-weight:800;cursor:pointer;transition:transform .15s ease,opacity .15s ease,box-shadow .15s ease;display:inline-flex;align-items:center;justify-content:center}
.btn:hover{transform:translateY(-1px)}.btn:disabled{opacity:.5;cursor:not-allowed;transform:none}
.btn-reset{background:#fee2e2;color:#991b1b}.btn-save{background:var(--amber);color:#4a3405}.btn-ghost{background:rgba(18,33,59,.08);color:var(--ink)}.btn-primary{background:var(--teal);color:#fff;box-shadow:0 10px 20px rgba(21,117,111,.18)}
.btn-toggle{display:inline-flex}
.toast{position:fixed;top:18px;right:18px;min-width:240px;max-width:360px;padding:12px 14px;border-radius:16px;box-shadow:var(--shadow);z-index:60;background:var(--navy);color:#fff;opacity:0;pointer-events:none;transform:translateY(-8px);transition:.18s ease}
.toast.is-visible{opacity:1;transform:none}
.toast.info{background:var(--navy)}.toast.success{background:var(--teal)}.toast.warn{background:#92400e}.toast.error{background:#991b1b}
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
.msg-attachments{display:flex;flex-direction:column;gap:8px}
.msg-attachment{display:flex;align-items:center;gap:8px;padding:8px 10px;border-radius:12px;background:rgba(18,33,59,.08);border:1px solid rgba(18,33,59,.12)}
.msg-user .msg-attachment{background:rgba(255,255,255,.12);border-color:rgba(255,255,255,.22)}
.msg-attachment-meta{display:flex;flex-direction:column;gap:2px;min-width:0}
.msg-attachment-name{font-size:12px;font-weight:700;line-height:1.3;word-break:break-word}
.msg-attachment-kind{font-size:12px;color:var(--muted)}
.msg-attachment-audio{width:100%}
.msg-attachment-image{max-width:260px;max-height:220px;border-radius:10px;border:1px solid rgba(18,33,59,.16);background:#fff}
.msg-time{font-size:13px;color:#526274;font-weight:600}.msg-user .msg-time{text-align:right}
.msg-sending{opacity:.6}
.msg-sending .msg-time::after{content:' \u2022 gönderiliyor...';font-style:italic;color:var(--muted-2)}
.msg-error{border:1px solid var(--red)!important}
.msg-error .msg-time::after{content:' \u2022 gönderilemedi';color:var(--red);font-weight:700}
.msg-retry-btn{margin-top:6px;padding:4px 12px;border:1px solid var(--red);border-radius:10px;background:rgba(220,38,38,.08);color:var(--red);font-size:12px;font-weight:700;cursor:pointer;transition:background .15s ease}
.msg-retry-btn:hover{background:rgba(220,38,38,.16)}
.feedback-bar{display:flex;flex-wrap:wrap;align-items:center;gap:8px;padding-top:6px;border-top:1px solid rgba(18,33,59,.08)}
.feedback-label{font-size:12px;font-weight:800;letter-spacing:.04em;text-transform:uppercase;color:var(--muted)}
.feedback-buttons{display:flex;gap:6px;flex-wrap:wrap}
.feedback-score{width:28px;height:28px;border-radius:999px;border:1px solid rgba(18,33,59,.14);background:#fff;color:var(--ink);font-size:12px;font-weight:700;cursor:pointer}
.feedback-score:hover{border-color:var(--teal);color:var(--teal)}.feedback-score.is-active{background:var(--teal);border-color:var(--teal);color:#fff}
.feedback-status{font-size:12px;color:var(--muted)}
.typing{align-self:flex-start;display:flex;gap:5px;padding:13px 16px;background:rgba(255,255,255,.96);border-radius:18px;border:1px solid rgba(18,33,59,.08);box-shadow:var(--shadow)}
.typing span{width:8px;height:8px;border-radius:50%;background:var(--muted-2);animation:bounce .6s infinite alternate}
.typing span:nth-child(2){animation-delay:.2s}.typing span:nth-child(3){animation-delay:.4s}
.empty-state{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;min-height:100%;color:var(--muted)}
.empty-state svg{width:52px;height:52px;opacity:.35}
.empty-card{display:flex;flex-direction:column;gap:12px;max-width:420px;padding:20px 22px;border-radius:20px;background:rgba(255,255,255,.96);border:1px solid rgba(18,33,59,.08);box-shadow:0 12px 32px rgba(15,23,42,.06);text-align:left}
.empty-card strong{font-size:15px;color:var(--ink)}
.empty-card p{font-size:13px;line-height:1.6;color:var(--muted)}
.empty-actions{display:flex;flex-wrap:wrap;gap:8px}
.empty-hints{display:flex;flex-wrap:wrap;gap:8px}
.empty-hint{display:inline-flex;align-items:center;padding:5px 10px;border-radius:999px;background:rgba(18,33,59,.06);font-size:12px;font-weight:700;color:var(--muted)}
.msg-reply{padding:10px 12px;border-radius:14px;border-left:3px solid var(--amber);background:rgba(18,33,59,.06);font-size:12px;line-height:1.45}
.msg-reply-label{display:block;font-weight:800;font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);margin-bottom:4px}
.msg-reply-text{color:inherit;opacity:.82}
.input-bar{display:flex;flex-direction:column;align-items:stretch;gap:var(--space-3);padding:var(--space-3) var(--space-4) var(--space-4);border-top:1px solid rgba(18,33,59,.08);background:rgba(255,255,255,.86)}
.input-row{display:flex;align-items:flex-end;gap:12px}
.composer-attachments{display:flex;flex-wrap:wrap;gap:8px}
.composer-chip{display:flex;align-items:center;gap:8px;max-width:320px;padding:7px 10px;border-radius:12px;background:rgba(18,33,59,.08);border:1px solid rgba(18,33,59,.14)}
.composer-chip-main{display:flex;flex-direction:column;gap:2px;min-width:0;flex:1}
.composer-chip-name{font-size:var(--text-xs);font-weight:700;line-height:1.35;white-space:normal;overflow:visible;text-overflow:clip;overflow-wrap:anywhere}
.composer-chip-meta{font-size:12px;color:var(--muted)}
.composer-chip-progress{width:100%;height:4px;border-radius:999px;background:rgba(18,33,59,.12);overflow:hidden;margin-top:2px}
.composer-chip-progress-fill{height:100%;background:var(--teal);transition:width .2s ease}
.composer-chip.error .composer-chip-progress-fill{background:var(--red)}
.composer-chip-remove{width:24px;height:24px;border:none;border-radius:8px;background:rgba(18,33,59,.12);cursor:pointer;font-size:14px;line-height:1;color:var(--ink)}
.composer-chip-remove:hover{background:rgba(18,33,59,.2)}
.reply-preview{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;padding:10px 12px;border-radius:16px;border:1px solid rgba(18,33,59,.1);background:rgba(18,33,59,.05)}
.reply-preview-copy{min-width:0}
.reply-preview-label{display:block;font-size:12px;font-weight:800;letter-spacing:.05em;text-transform:uppercase;color:var(--teal)}
.reply-preview-text{margin-top:4px;font-size:13px;line-height:1.45;color:var(--ink);word-break:break-word}
.reply-preview-clear{width:32px;height:32px;border:none;border-radius:10px;background:rgba(18,33,59,.08);color:var(--ink);font-size:20px;line-height:1;cursor:pointer}
.reply-preview-clear:hover{background:rgba(18,33,59,.14)}
.input-bar textarea{flex:1;resize:none;padding:11px 14px;font-size:14px;line-height:1.45;max-height:130px}
.btn-attach,.btn-voice{width:40px;height:40px;padding:0;border-radius:12px;display:flex;align-items:center;justify-content:center}
.btn-attach svg,.btn-voice svg{width:20px;height:20px;fill:currentColor}
.btn-voice.is-recording{background:#fee2e2;color:#991b1b}
.btn-send{width:40px;height:40px;border-radius:12px;display:flex;align-items:center;justify-content:center}
.btn-send svg{width:20px;height:20px;fill:currentColor}
.debug-header{display:flex;align-items:center;gap:10px;padding:16px 18px;border-bottom:1px solid rgba(255,255,255,.08)}
.debug-header strong{font-size:14px}.debug-header span{font-size:12px;color:rgba(255,255,255,.82)}
.debug-body{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:14px}
.debug-section{padding:14px;border-radius:18px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.06)}
.debug-section h3{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:rgba(255,255,255,.82);margin-bottom:8px}
.debug-value{font-size:13px;line-height:1.55}
.debug-json,.meta-box{font-family:var(--mono);font-size:12px;white-space:pre-wrap;word-break:break-word;color:#bfdbfe;background:rgba(2,6,23,.35);border-radius:14px;padding:10px;max-height:220px;overflow:auto}
.meta-box{color:#e2e8f0}
.debug-badge{display:inline-flex;align-items:center;gap:4px;padding:4px 10px;border-radius:999px;font-size:12px;font-weight:700}
.badge-state{background:rgba(42,157,143,.2);color:#8df7e8}.badge-intent{background:rgba(233,196,106,.18);color:#ffe49a}.badge-lang{background:rgba(255,255,255,.14);color:#fff}
.debug-flags{display:flex;flex-wrap:wrap;gap:6px}.flag{padding:4px 8px;border-radius:999px;font-size:12px;font-weight:700}
.flag-l3{background:#7f1d1d;color:#fecaca}.flag-l2{background:#78350f;color:#fde68a}.flag-l1{background:#365314;color:#dcfce7}.flag-l0{background:rgba(255,255,255,.12);color:#fff}
.studio-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}
.studio-head p,.feedback-muted,.report-muted{font-size:12px;color:rgba(255,255,255,.82);line-height:1.5}
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
.check-item input{margin-top:2px}.check-copy strong{display:block;font-size:12px;color:#fff}.check-copy span{display:block;font-size:12px;color:rgba(255,255,255,.78);margin-top:2px}
.inline-note{font-size:12px;color:#fcd34d}
.required-mark{color:#f87171;font-weight:800;margin-left:3px}
.hidden{display:none!important}
.source-badge{grid-area:badge;justify-self:start;display:inline-flex;align-items:center;gap:6px;padding:8px 12px;border-radius:999px;background:#f6df9a;color:#6f4300;border:1px solid rgba(180,131,24,.34);box-shadow:0 4px 12px rgba(180,131,24,.12);font-size:12px;font-weight:800;line-height:1.35}
.list{display:flex;flex-direction:column;gap:8px}
.list-item{padding:10px 12px;border-radius:14px;background:rgba(2,6,23,.24);border:1px solid rgba(255,255,255,.08)}
.list-item strong{display:block;font-size:12px}.list-item span{display:block;font-size:12px;color:rgba(255,255,255,.82);margin-top:3px}
.mt-xs{margin-top:8px}.mt-sm{margin-top:10px}.mt-md{margin-top:12px}
.btn-block{width:100%}
.ctx-menu{position:fixed;z-index:1100;min-width:140px;padding:6px 0;background:var(--paper);border:1px solid var(--line);border-radius:12px;box-shadow:var(--shadow);animation:fadeIn .12s ease}
.ctx-menu-item{display:flex;align-items:center;gap:8px;width:100%;padding:8px 14px;border:none;background:none;color:var(--ink);font-size:13px;font-weight:600;cursor:pointer;transition:background .12s ease}
.ctx-menu-item:hover{background:rgba(21,117,111,.08)}
.ctx-menu-item svg{width:15px;height:15px;fill:currentColor;opacity:.7}
.metrics-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px}
.metric-card{padding:10px 12px;border-radius:14px;background:rgba(2,6,23,.24);border:1px solid rgba(255,255,255,.08)}
.metric-card .metric-value{font-size:20px;font-weight:800;color:#ffe49a;line-height:1.2}
.metric-card .metric-label{font-size:12px;color:rgba(255,255,255,.82);margin-top:2px}
.metric-bar-group{margin-top:8px}
.metric-bar-title{font-size:12px;color:rgba(255,255,255,.82)}
.metric-bar-row{display:flex;align-items:center;gap:8px;margin-top:4px}
.metric-bar-label{font-size:12px;color:rgba(255,255,255,.82);min-width:90px;text-align:right}
.metric-bar-track{flex:1;height:8px;background:rgba(255,255,255,.08);border-radius:4px;overflow:hidden}
.metric-bar-fill{height:100%;border-radius:4px;transition:width .3s ease}
.metric-bar-count{font-size:12px;color:rgba(255,255,255,.78);min-width:28px}
.mode-switch{display:flex;gap:0;border-radius:16px;overflow:hidden;border:1px solid rgba(18,33,59,.12);min-height:var(--control-h);background:#fff}
.mode-btn{flex:1;min-height:var(--control-h);padding:0 14px;font-size:12px;font-weight:800;border:none;cursor:pointer;background:rgba(18,33,59,.04);color:var(--muted);transition:all .15s ease}
.mode-btn:hover{background:rgba(18,33,59,.12)}
.mode-btn.is-active-mode[data-mode="test"]{background:#fef3c7;color:#92400e}
.mode-btn.is-active-mode[data-mode="ai"]{background:#dcfce7;color:#166534}
.mode-btn.is-active-mode[data-mode="approval"]{background:#e0e7ff;color:#3730a3}
.mode-btn.is-active-mode[data-mode="off"]{background:#fee2e2;color:#991b1b}
.live-feed-card{padding:10px 12px;border-radius:14px;background:rgba(2,6,23,.24);border:1px solid rgba(255,255,255,.08);margin-top:6px;cursor:pointer;transition:border-color .15s ease}
.live-feed-card:hover{border-color:rgba(255,255,255,.2)}
.live-feed-card:focus-visible{outline:2px solid rgba(99,102,241,.45);outline-offset:2px}
.live-feed-head{display:flex;align-items:center;justify-content:space-between;gap:8px}
.live-feed-phone{font-size:12px;font-weight:700;color:#ffe49a}
.live-feed-time{font-size:12px;color:rgba(255,255,255,.78)}
.live-feed-msgs{margin-top:6px;font-size:13px;line-height:1.6}
.live-feed-user,.live-feed-assistant{white-space:pre-wrap;word-break:break-word;display:block;overflow:visible}
.live-feed-user{color:rgba(255,255,255,.7)}
.live-feed-assistant{color:rgba(42,157,143,.8)}
#live-feed-container{min-height:320px;max-height:60vh;overflow-y:auto;padding-right:4px}
#live-feed-container::-webkit-scrollbar{width:5px}
#live-feed-container::-webkit-scrollbar-thumb{background:rgba(255,255,255,.15);border-radius:999px}
.live-feed-blocked{display:inline-flex;align-items:center;gap:3px;padding:2px 7px;border-radius:6px;font-size:12px;font-weight:800;background:rgba(234,179,8,.2);color:#fbbf24}
.live-feed-sent{display:inline-flex;align-items:center;gap:3px;padding:2px 7px;border-radius:6px;font-size:12px;font-weight:800;background:rgba(34,197,94,.25);color:#4ade80}
.live-feed-badges{display:flex;align-items:center;gap:6px;margin-top:4px;flex-wrap:wrap}
.live-feed-badge{padding:2px 6px;border-radius:6px;font-size:12px;font-weight:700;background:rgba(255,255,255,.1);color:rgba(255,255,255,.82)}
.live-feed-badge-active{color:#86efac}
.live-feed-badge-inactive{color:#fca5a5}
.live-feed-head-meta{display:flex;align-items:center;gap:8px;flex-wrap:wrap;justify-content:flex-end}
.live-feed-approve-btn{padding:2px 8px;border-radius:6px;font-size:12px;font-weight:800;background:rgba(99,102,241,.3);color:#c7d2fe;border:1px solid rgba(99,102,241,.5);cursor:pointer;transition:all .15s ease}
.live-feed-approve-btn:hover{background:rgba(99,102,241,.5);color:#fff}
.live-feed-reject-btn{padding:2px 8px;border-radius:6px;font-size:12px;font-weight:800;background:rgba(239,68,68,.25);color:#fca5a5;border:1px solid rgba(239,68,68,.45);cursor:pointer;transition:all .15s ease}
.live-feed-reject-btn:hover{background:rgba(239,68,68,.45);color:#fff}
.live-feed-reject-btn.confirm-state{background:rgba(239,68,68,.55);color:#fff;animation:pulse .6s infinite alternate}
.live-feed-rejected{display:inline-flex;align-items:center;gap:3px;padding:2px 7px;border-radius:6px;font-size:12px;font-weight:800;background:rgba(239,68,68,.35);color:#fca5a5}
.live-feed-card[draggable="true"]{cursor:grab}.live-feed-card[draggable="true"]:active{cursor:grabbing}
.live-feed-card.is-dragging{opacity:.4}
.chat-panel.drop-active{outline:2px dashed var(--teal);outline-offset:-4px;background:rgba(21,117,111,.05)}
.chat-panel.drop-active .messages::after{content:'Konuşmayı buraya bırakın';position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:700;color:var(--teal);background:rgba(21,117,111,.06);border-radius:18px;pointer-events:none}
.messages{position:relative}
.conv-modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:1000;display:flex;align-items:center;justify-content:center;animation:fadeIn .15s ease}
.conv-modal-overlay.hidden{display:none!important}
.conv-modal{width:min(720px,95vw);max-height:85vh;background:linear-gradient(180deg,#1a2740,#0f172a);color:#fff;border-radius:18px;box-shadow:0 24px 48px rgba(0,0,0,.4);display:flex;flex-direction:column;overflow:hidden}
.conv-modal-header{display:flex;align-items:center;justify-content:space-between;padding:16px 20px;border-bottom:1px solid rgba(255,255,255,.08)}
.conv-modal-header strong{font-size:15px}
.conv-modal-close{background:none;border:none;color:rgba(255,255,255,.82);font-size:24px;cursor:pointer;padding:0 4px;line-height:1}
.conv-modal-close:hover{color:#fff}
.conv-modal-meta{display:flex;flex-wrap:wrap;gap:8px;padding:12px 20px;border-bottom:1px solid rgba(255,255,255,.06)}
.conv-modal-meta-item{padding:3px 8px;border-radius:8px;font-size:12px;font-weight:700;background:rgba(255,255,255,.1);color:rgba(255,255,255,.85)}
.conv-modal-meta-item.highlight{background:rgba(42,157,143,.2);color:#8df7e8}
.conv-modal-messages{flex:1;overflow-y:auto;padding:16px 20px;display:flex;flex-direction:column;gap:10px}
.conv-modal-messages::-webkit-scrollbar{width:5px}
.conv-modal-messages::-webkit-scrollbar-thumb{background:rgba(255,255,255,.15);border-radius:999px}
.conv-msg{padding:10px 14px;border-radius:14px;max-width:88%}
.conv-msg-user{align-self:flex-end;background:rgba(42,157,143,.18);border:1px solid rgba(42,157,143,.25)}
.conv-msg-assistant{align-self:flex-start;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.08)}
.conv-msg-system{align-self:center;background:rgba(255,255,255,.05);color:rgba(255,255,255,.78);font-size:12px;max-width:95%}
.conv-msg-role{font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px}
.conv-msg-user .conv-msg-role{color:#86efac}
.conv-msg-assistant .conv-msg-role{color:#93c5fd}
.conv-msg-body{font-size:13px;line-height:1.6;white-space:pre-wrap;word-break:break-word}
.conv-msg-time{font-size:12px;color:rgba(255,255,255,.78);margin-top:4px}
.conv-msg-status{display:inline-flex;padding:1px 6px;border-radius:6px;font-size:12px;font-weight:800;margin-left:6px}
.conv-msg-status.sent{background:rgba(34,197,94,.25);color:#4ade80}
.conv-msg-status.pending{background:rgba(234,179,8,.25);color:#fbbf24}
.conv-msg-status.rejected{background:rgba(239,68,68,.3);color:#f87171}
.conv-modal-json-toggle{padding:8px 20px;border-top:1px solid rgba(255,255,255,.06)}
.conv-modal-json{padding:0 20px 12px;max-height:200px;overflow:auto}
.conv-modal-json pre{font-family:var(--mono);font-size:12px;white-space:pre-wrap;word-break:break-word;color:#bfdbfe;background:rgba(2,6,23,.4);border-radius:12px;padding:10px}
.conv-modal-actions{display:flex;gap:8px;padding:14px 20px;border-top:1px solid rgba(255,255,255,.08);justify-content:flex-end}
.conv-modal-actions .btn{height:34px;font-size:12px}
.conv-modal-feedback{padding:14px 20px;border-top:1px solid rgba(255,255,255,.08);background:rgba(239,68,68,.06)}
.conv-modal-feedback.hidden{display:none!important}
.conv-modal-feedback-title{font-size:13px;font-weight:800;color:#fca5a5;margin-bottom:10px}
.conv-modal-feedback .debug-select,.conv-modal-feedback .debug-textarea{background:#1e293b;color:#e2e8f0;border:1px solid rgba(255,255,255,.18);border-radius:10px}
.conv-modal-feedback .debug-select option{background:#1e293b;color:#e2e8f0}
.conv-modal-feedback .field-stack label{color:rgba(255,255,255,.7)}
.conv-modal-send{padding:12px 20px;border-top:1px solid rgba(255,255,255,.06);display:flex;gap:8px;align-items:flex-end}
.conv-modal-send textarea{flex:1;min-height:38px;max-height:100px;resize:vertical;padding:8px 12px;font-size:13px;line-height:1.4;background:#1e293b;color:#e2e8f0;border:1px solid rgba(255,255,255,.15);border-radius:10px;outline:none;font-family:inherit}
.conv-modal-send textarea:focus{border-color:var(--teal)}
.conv-modal-send .btn{height:38px;flex-shrink:0}
.faq-dialog{border:none;border-radius:18px;padding:0;background:transparent;max-width:520px;width:92vw}
.faq-dialog::backdrop{background:rgba(0,0,0,.45)}
.faq-dialog-card{background:var(--paper);border-radius:18px;box-shadow:var(--shadow);padding:24px;display:flex;flex-direction:column;gap:14px}
.faq-dialog-head{display:flex;align-items:center;justify-content:space-between}
.faq-dialog-head h3{font-size:16px;font-weight:700;color:var(--ink)}
.faq-dialog-head button{background:none;border:none;font-size:22px;color:var(--muted);cursor:pointer;padding:0 4px;line-height:1}
.faq-dialog-head button:hover{color:var(--ink)}
.faq-dialog .field-stack{margin-top:0}
.faq-dialog .field-stack label{color:var(--ink)}
.faq-dialog .debug-input,.faq-dialog .debug-textarea,.faq-dialog .debug-select{background:rgba(255,255,255,.94);color:var(--ink)}
.shortcut-list{display:flex;flex-direction:column;gap:10px}
.shortcut-row{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:10px 12px;border-radius:12px;background:rgba(18,33,59,.04);font-size:13px;color:var(--ink)}
.shortcut-key{display:inline-flex;align-items:center;justify-content:center;min-width:110px;padding:6px 10px;border-radius:10px;background:rgba(18,33,59,.08);font-family:var(--mono);font-size:12px;font-weight:700;color:var(--ink)}
.field-stack-sm{flex-direction:column;align-items:flex-start;gap:6px}
.header--workspace{display:grid;grid-template-columns:minmax(0,1fr) auto auto;gap:18px;align-items:center;justify-content:space-between}
.header--workspace .header-brand{align-items:flex-start;min-width:0}
.header-status{display:flex;align-items:center;justify-content:flex-end;gap:10px;flex-wrap:wrap}
.header-status-pill{display:inline-flex;align-items:center;padding:8px 12px;border-radius:999px;background:rgba(18,33,59,.06);border:1px solid rgba(18,33,59,.08);font-size:12px;font-weight:800;color:#415269;white-space:nowrap}
.header-status-pill.is-mode-test{background:rgba(245,158,11,.12);border-color:rgba(245,158,11,.18);color:#9a6700}
.header-status-pill.is-mode-ai{background:rgba(16,185,129,.12);border-color:rgba(16,185,129,.18);color:#0f766e}
.header-status-pill.is-mode-approval{background:rgba(99,102,241,.14);border-color:rgba(129,140,248,.22);color:#4338ca}
.header-status-pill.is-mode-off{background:rgba(239,68,68,.1);border-color:rgba(248,113,113,.16);color:#b91c1c}
.header-utility{display:flex;align-items:center;justify-content:flex-end;gap:10px}
.workspace-panel-toggle{white-space:nowrap;background:linear-gradient(180deg,#fff,#f4f7fb);border:1px solid rgba(18,33,59,.08);box-shadow:0 12px 24px rgba(15,23,42,.08)}
.control-cluster{
  display:flex;flex-direction:column;gap:12px;padding:15px 16px;border-radius:20px;
  background:rgba(255,255,255,.74);border:1px solid rgba(18,33,59,.08);box-shadow:0 12px 28px rgba(15,23,42,.05);min-width:0
}
.control-cluster-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}
.control-cluster-head strong{display:block;font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#314155}
.control-cluster-head p{margin-top:4px;font-size:12px;line-height:1.55;color:var(--muted)}
.control-cluster-core{grid-column:1 / -1}
.control-cluster-grid{display:grid;gap:12px;align-items:end}
.control-cluster-grid-core{grid-template-columns:minmax(0,1.2fr) minmax(0,.9fr) minmax(0,1fr)}
.control-cluster-grid-actions{grid-template-columns:repeat(6,minmax(0,1fr))}
.control-model,.control-source,.control-id,.control-mode,.control-export-format{min-width:0}
.control-mode{width:100%}
.control-action{width:100%}
.control-imports{grid-column:span 2}
.control-reset,.control-export-format,.control-export,.control-diagnostics{grid-column:span 1}
.main{
  display:grid;grid-template-columns:minmax(312px,360px) minmax(720px,1fr) minmax(308px,360px);
  gap:16px;padding:16px 18px 18px;min-height:0;
  background:linear-gradient(180deg,rgba(255,255,255,.28),rgba(255,255,255,0));align-items:stretch
}
.queue-panel,.chat-panel,.context-panel{
  min-height:0;background:rgba(255,255,255,.88);border:1px solid rgba(18,33,59,.08);
  border-radius:24px;box-shadow:0 18px 36px rgba(15,23,42,.08)
}
.queue-panel,.context-panel{display:flex;flex-direction:column;overflow:hidden}
.queue-panel-head,.context-panel-head{
  display:flex;flex-direction:column;align-items:stretch;gap:12px;padding:18px 18px 14px;
  border-bottom:1px solid rgba(18,33,59,.08);background:linear-gradient(180deg,rgba(248,250,252,.92),rgba(255,255,255,.72))
}
.queue-panel-head h2,.context-panel-head h2{font-size:18px;font-weight:800;letter-spacing:.01em;line-height:1.2}
.queue-panel-head p,.context-panel-head p{font-size:13px;line-height:1.55;color:var(--muted);margin-top:4px}
.queue-panel-actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.queue-toggle{display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:700;color:var(--muted);cursor:pointer;white-space:nowrap}
.queue-toggle input{accent-color:var(--teal)}
.queue-toolbar{display:flex;flex-direction:column;gap:12px;padding:14px 18px;border-bottom:1px solid rgba(18,33,59,.08);background:rgba(248,250,252,.74)}
.queue-tabs,.context-tabs,.composer-modebar{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.queue-tab,.context-tab,.composer-mode-btn{
  height:var(--chip-h);border:1px solid rgba(18,33,59,.1);border-radius:999px;background:rgba(255,255,255,.92);
  padding:0 14px;font-size:12px;font-weight:800;color:var(--muted);cursor:pointer;transition:all .16s ease
}
.queue-tab:hover,.context-tab:hover,.composer-mode-btn:hover{border-color:rgba(21,117,111,.34);color:var(--teal)}
.queue-tab.is-active,.context-tab.is-active,.composer-mode-btn.is-active{
  background:rgba(21,117,111,.1);border-color:rgba(21,117,111,.34);color:var(--teal);box-shadow:inset 0 0 0 1px rgba(21,117,111,.08)
}
.queue-search{width:100%}
.queue-summary{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.queue-summary-chip{display:inline-flex;align-items:center;gap:6px;padding:6px 10px;border-radius:999px;background:rgba(18,33,59,.06);color:var(--muted);font-size:12px;font-weight:700}
.queue-summary-chip-warning{color:#b45309;background:rgba(245,158,11,.16)}
.queue-list{flex:1;overflow:auto;padding:14px}
.queue-list::-webkit-scrollbar,.context-body::-webkit-scrollbar{width:7px}
.queue-list::-webkit-scrollbar-thumb,.context-body::-webkit-scrollbar-thumb{background:rgba(100,116,139,.28);border-radius:999px}
.live-feed-card{
  position:relative;margin:0 0 10px;padding:14px;border-radius:20px;background:#fff;border:1px solid rgba(18,33,59,.08);
  box-shadow:0 10px 24px rgba(15,23,42,.045);cursor:pointer;transition:border-color .15s ease,transform .15s ease,box-shadow .15s ease
}
.live-feed-card:hover{border-color:rgba(21,117,111,.22);transform:translateY(-1px)}
.live-feed-card.is-active{border-color:rgba(21,117,111,.45);box-shadow:0 14px 28px rgba(21,117,111,.12), inset 3px 0 0 rgba(21,117,111,.75)}
.live-feed-card.is-attention{border-color:rgba(245,158,11,.28);box-shadow:0 12px 26px rgba(245,158,11,.08)}
.live-feed-card.is-attention.is-active{box-shadow:0 14px 28px rgba(245,158,11,.12), inset 3px 0 0 rgba(245,158,11,.85)}
.live-feed-card.is-human{background:linear-gradient(180deg,rgba(255,251,235,.96),#fff)}
.live-feed-card.has-draft{border-style:dashed}
.live-feed-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}
.live-feed-title-stack{display:flex;flex-direction:column;gap:3px;min-width:0}
.live-feed-phone{font-size:14px;line-height:1.35;font-weight:800;color:var(--ink);word-break:break-word}
.live-feed-subline{font-size:12px;line-height:1.45;color:var(--muted)}
.live-feed-head-meta{display:flex;align-items:center;gap:8px;flex-wrap:wrap;justify-content:flex-end}
.live-feed-time{font-size:12px;color:var(--muted);white-space:nowrap}
.live-feed-priority{display:inline-flex;align-items:center;padding:4px 9px;border-radius:999px;background:rgba(18,33,59,.06);font-size:12px;font-weight:800;color:var(--muted);white-space:nowrap}
.live-feed-priority.is-attention{background:rgba(245,158,11,.18);color:#b45309}
.live-feed-priority.is-human{background:rgba(253,230,138,.3);color:#854d0e}
.live-feed-priority.is-draft{background:rgba(196,181,253,.22);color:#6d28d9}
.live-feed-preview{display:grid;gap:8px;margin-top:12px}
.live-feed-preview-block{display:flex;flex-direction:column;gap:4px;padding:10px 12px;border-radius:16px;background:rgba(18,33,59,.04);border:1px solid rgba(18,33,59,.05)}
.live-feed-preview-label{font-size:11px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#516173}
.live-feed-user,.live-feed-assistant{font-size:13px;line-height:1.55;word-break:break-word}
.live-feed-user{color:var(--ink)}
.live-feed-assistant{color:#44576d}
.live-feed-status-row{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:12px}
.live-feed-badges{display:flex;align-items:center;gap:6px;row-gap:8px;flex-wrap:wrap;margin-top:12px}
.live-feed-badge{background:rgba(18,33,59,.06);color:var(--muted);border-radius:999px;padding:4px 8px;font-size:12px}
.live-feed-blocked,.live-feed-sent,.live-feed-rejected{display:inline-flex;align-items:center;border-radius:999px;padding:5px 9px;font-size:12px}
.chat-panel{display:flex;flex-direction:column;overflow:hidden}
.thread-header{
  display:flex;align-items:flex-start;justify-content:space-between;gap:14px;padding:18px 20px 14px;
  border-bottom:1px solid rgba(18,33,59,.08);background:linear-gradient(180deg,rgba(248,250,252,.94),rgba(255,255,255,.86))
}
.thread-header-copy h2{font-size:20px;font-weight:800;letter-spacing:.01em;line-height:1.2}
.thread-header-copy p{font-size:13px;line-height:1.6;color:var(--muted);margin-top:6px;max-width:60ch}
.thread-header-actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap;justify-content:flex-end}
.thread-chip{display:inline-flex;align-items:center;gap:6px;padding:7px 11px;border-radius:999px;font-size:12px;font-weight:800;background:rgba(21,117,111,.1);color:var(--teal);border:1px solid rgba(21,117,111,.16)}
.thread-chip-muted{background:rgba(18,33,59,.06);color:#435468;border-color:rgba(18,33,59,.08)}
.session-strip{
  display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:12px 20px;border-bottom:1px solid rgba(18,33,59,.06);
  background:rgba(248,250,252,.78);min-height:64px
}
.session-pill{display:inline-flex;align-items:center;gap:6px;padding:7px 11px;border-radius:999px;background:#fff;border:1px solid rgba(18,33,59,.1);font-size:12px;font-weight:700;color:#223247}
.session-pill.is-warning{background:rgba(231,191,95,.16);border-color:rgba(231,191,95,.4);color:#7c5800}
.session-pill.is-danger{background:rgba(220,38,38,.1);border-color:rgba(220,38,38,.24);color:#991b1b}
.messages{gap:14px;padding:18px 20px 14px;background:linear-gradient(180deg,rgba(248,250,252,.72),rgba(255,255,255,.86))}
.msg{max-width:78%;border:1px solid transparent;box-shadow:0 14px 30px rgba(15,23,42,.07);padding:16px 18px;border-radius:22px;gap:10px}
.msg-user{align-self:flex-start;background:#fff;border-color:rgba(18,33,59,.08);color:var(--ink);border-bottom-left-radius:8px}
.msg-assistant{align-self:flex-end;background:linear-gradient(135deg,var(--teal),var(--teal-2));color:#fff;border-bottom-right-radius:8px}
.msg-system{align-self:center;max-width:92%;background:rgba(18,33,59,.06);color:var(--muted);border:1px solid rgba(18,33,59,.06)}
.msg.msg-ai-draft{align-self:flex-end;max-width:82%;background:linear-gradient(180deg,#fff8e8,#fff);border:1px dashed rgba(231,191,95,.85);color:var(--ink)}
.msg.msg-internal-note{align-self:center;max-width:88%;background:rgba(15,23,42,.92);color:#e2e8f0;border:1px solid rgba(15,23,42,.92)}
.msg-body{font-size:14px;line-height:1.65}
.msg-role{display:flex;align-items:center;gap:8px;font-size:12px;font-weight:800;letter-spacing:.04em;text-transform:uppercase;opacity:.95}
.msg-status-row{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.msg-status-pill{display:inline-flex;align-items:center;padding:4px 8px;border-radius:999px;font-size:12px;font-weight:800;background:rgba(18,33,59,.1);color:#34475c;border:1px solid rgba(18,33,59,.1)}
.msg-status-pill.is-warning{background:rgba(231,191,95,.18);color:#7c5800}
.msg-status-pill.is-danger{background:rgba(220,38,38,.12);color:#991b1b}
.msg-status-pill.is-success{background:rgba(21,117,111,.14);color:var(--teal)}
.msg-actions{display:flex;gap:8px;flex-wrap:wrap;padding-top:6px}
.msg-action{height:34px;border-radius:999px;border:1px solid rgba(18,33,59,.12);background:#fff;padding:0 12px;font-size:12px;font-weight:800;color:var(--ink);cursor:pointer}
.msg-action:hover{border-color:rgba(21,117,111,.34);color:var(--teal)}
.msg-assistant .msg-action{background:rgba(255,255,255,.92)}
.msg-assistant .msg-reply{background:rgba(8,61,58,.18);border:1px solid rgba(255,255,255,.18);border-left:3px solid rgba(255,255,255,.92)}
.msg-assistant .msg-reply-label{color:#f8fafc}
.msg-assistant .msg-reply-text{color:#ffffff;opacity:1}
.msg-assistant .msg-time{color:#f8fafc;font-weight:700}
.msg-assistant .msg-status-pill{background:rgba(8,61,58,.24);border:1px solid rgba(255,255,255,.22);color:#ffffff}
.msg-assistant .msg-status-pill.is-success{background:rgba(8,61,58,.28);color:#ffffff}
.msg-assistant .msg-status-pill.is-warning{background:rgba(124,88,0,.28);color:#fff7dd}
.msg-assistant .msg-status-pill.is-danger{background:rgba(127,29,29,.28);color:#ffe2e2}
.msg-internal-note .msg-action{background:rgba(255,255,255,.1);border-color:rgba(255,255,255,.12);color:#fff}
.feedback-bar{display:none}
.input-bar{gap:12px;padding:14px 18px 18px;background:rgba(255,255,255,.94);border-top:1px solid rgba(18,33,59,.08)}
.composer-helper,.template-panel{padding:16px 18px;border-radius:20px;background:rgba(18,33,59,.05);border:1px solid rgba(18,33,59,.08);font-size:13px;line-height:1.65;color:#47586c}
.composer-helper.hidden,.template-panel.hidden{display:none!important}
.template-panel{display:flex;flex-direction:column;gap:14px;background:linear-gradient(180deg,rgba(248,250,252,.9),rgba(255,255,255,.84))}
.template-panel-copy strong{display:block;font-size:15px;font-weight:800;color:var(--ink);margin-bottom:6px}
.template-panel-copy p{font-size:13px;line-height:1.6;color:var(--muted)}
.template-panel-head{display:flex;align-items:flex-start;justify-content:space-between;gap:14px}
.template-panel-actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap;justify-content:flex-end}
.template-panel-badge{display:inline-flex;align-items:center;padding:5px 9px;border-radius:999px;background:rgba(18,33,59,.08);font-size:12px;font-weight:800;color:var(--muted);white-space:nowrap}
.template-panel-grid{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(260px,.95fr);gap:14px;align-items:start}
.template-panel-rail,.template-panel-preview-stack{display:flex;flex-direction:column;gap:12px;min-width:0}
.template-search{margin-top:0}
.template-list{display:flex;flex-direction:column;gap:10px;max-height:312px;overflow:auto;padding-right:6px}
.template-card{padding:14px;border-radius:16px;background:#fff;border:1px solid rgba(18,33,59,.08);cursor:pointer;transition:border-color .16s ease,transform .16s ease,box-shadow .16s ease}
.template-card:hover{border-color:rgba(21,117,111,.24);transform:translateY(-1px)}
.template-card.is-selected{border-color:rgba(21,117,111,.42);box-shadow:0 12px 24px rgba(21,117,111,.08)}
.template-card-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}
.template-card-title{font-size:13px;font-weight:800;color:var(--ink);line-height:1.4}
.template-card-meta{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.template-pill{display:inline-flex;align-items:center;padding:4px 8px;border-radius:999px;background:rgba(18,33,59,.06);font-size:12px;font-weight:700;color:var(--muted)}
.template-pill.is-recommended{background:rgba(21,117,111,.12);color:var(--teal)}
.template-card-preview{margin-top:9px;font-size:12px;line-height:1.55;color:var(--muted)}
.template-preview{padding:14px 16px;border-radius:18px;background:#fff;border:1px solid rgba(18,33,59,.08);white-space:pre-wrap;min-height:220px;line-height:1.65}
.template-preview strong{display:block;font-size:14px;font-weight:800;color:var(--ink);margin-bottom:8px}
.template-preview small{display:block;margin-top:10px;color:var(--muted)}
.input-row{display:flex;align-items:flex-end;gap:10px}
.input-bar textarea{flex:1;resize:none;padding:13px 16px;font-size:14px;line-height:1.55;max-height:140px;min-height:52px}
.btn-attach,.btn-voice,.btn-send{width:44px;height:44px;padding:0;border-radius:14px;display:flex;align-items:center;justify-content:center}
.context-panel .context-tabs{padding:0 18px 14px;border-bottom:1px solid rgba(18,33,59,.08);background:rgba(248,250,252,.76)}
.context-body{flex:1;overflow:auto;padding:16px;background:linear-gradient(180deg,rgba(248,250,252,.72),rgba(255,255,255,.9))}
.context-empty{padding:16px 8px;color:var(--muted);line-height:1.6}
.context-empty strong{display:block;color:var(--ink);margin-bottom:6px}
.context-card{display:flex;flex-direction:column;gap:12px;padding:14px 15px;border-radius:18px;background:#fff;border:1px solid rgba(18,33,59,.08);box-shadow:0 8px 18px rgba(15,23,42,.04)}
.context-card + .context-card{margin-top:12px}
.context-card h3{font-size:13px;font-weight:800;letter-spacing:.02em}
.context-list{display:flex;flex-direction:column;gap:10px}
.context-row{display:grid;grid-template-columns:minmax(96px,116px) minmax(0,1fr);align-items:start;gap:6px 12px;font-size:12px;line-height:1.55}
.context-row span:first-child{color:#53667a;font-weight:700}
.context-row span:last-child{color:#13253e;text-align:left;font-weight:600;word-break:break-word}
.context-tag-row{display:flex;flex-wrap:wrap;gap:8px}
.context-tag{display:inline-flex;align-items:center;padding:6px 10px;border-radius:999px;background:rgba(18,33,59,.06);font-size:12px;font-weight:700;color:var(--muted)}
.guest-card-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}
.guest-card-title{display:flex;flex-direction:column;gap:4px}
.guest-card-title strong{font-size:15px;color:var(--ink)}
.guest-card-title span{font-size:12px;line-height:1.6;color:var(--muted)}
.guest-status-badge{display:inline-flex;align-items:center;justify-content:center;padding:6px 10px;border-radius:999px;font-size:11px;font-weight:800;letter-spacing:.04em;text-transform:uppercase;white-space:nowrap}
.guest-status-badge.is-success{background:rgba(34,197,94,.14);color:#166534}
.guest-status-badge.is-warning{background:rgba(245,158,11,.16);color:#b45309}
.guest-status-badge.is-danger{background:rgba(239,68,68,.12);color:#b91c1c}
.guest-status-badge.is-info{background:rgba(37,99,235,.12);color:#1d4ed8}
.guest-status-badge.is-muted{background:rgba(18,33,59,.08);color:var(--muted)}
.guest-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.guest-field{display:flex;flex-direction:column;gap:5px;padding:12px 13px;border-radius:16px;border:1px solid rgba(18,33,59,.08);background:rgba(18,33,59,.03);min-width:0}
.guest-field.full{grid-column:1 / -1}
.guest-field span{font-size:11px;font-weight:800;letter-spacing:.05em;text-transform:uppercase;color:var(--muted)}
.guest-field strong{font-size:13px;line-height:1.55;color:var(--ink);word-break:break-word}
.guest-actions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.guest-action-btn{height:40px;border-radius:14px;border:1px solid rgba(18,33,59,.12);padding:0 12px;font-size:12px;font-weight:800;cursor:pointer;transition:transform .15s ease,opacity .15s ease}
.guest-action-btn:hover{transform:translateY(-1px)}
.guest-action-btn.primary{background:var(--teal);border-color:var(--teal);color:#fff}
.guest-action-btn.danger{background:#fff1f2;border-color:rgba(220,38,38,.18);color:#b91c1c}
.guest-action-btn:disabled{opacity:.55;cursor:not-allowed;transform:none}
.guest-action-note{font-size:12px;line-height:1.5;color:var(--muted)}
.audit-timeline{display:flex;flex-direction:column;gap:10px}
.audit-item{padding:12px;border-radius:14px;border:1px solid rgba(18,33,59,.08);background:rgba(248,250,252,.9)}
.audit-item.is-success{border-color:rgba(21,117,111,.22);background:rgba(21,117,111,.06)}
.audit-item.is-warning{border-color:rgba(231,191,95,.42);background:rgba(231,191,95,.12)}
.audit-item.is-danger{border-color:rgba(220,38,38,.24);background:rgba(220,38,38,.08)}
.audit-item.is-muted{border-color:rgba(100,116,139,.16);background:rgba(15,23,42,.03)}
.audit-item-main{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}
.audit-item-title{font-size:12px;font-weight:800;color:var(--ink)}
.audit-item-time{font-size:12px;color:#526274;white-space:nowrap}
.audit-item-detail{margin-top:6px;font-size:12px;line-height:1.5;color:#526274}
.workspace-scrim{position:fixed;inset:0;z-index:72;background:rgba(6,12,24,.48);backdrop-filter:blur(10px)}
.workspace-flyout{position:fixed;top:0;right:0;bottom:0;z-index:80;width:min(580px,96vw);display:flex;flex-direction:column;background:linear-gradient(180deg,#13233e 0%,#101d34 14%,#0c1526 100%);color:#fff;border-left:1px solid rgba(255,255,255,.08);transform:translateX(0);transition:transform .22s ease,opacity .22s ease;box-shadow:-28px 0 56px rgba(4,10,20,.36)}
.workspace-flyout.collapsed{transform:translateX(100%);opacity:0;pointer-events:none;overflow:hidden}
.workspace-flyout-header{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;padding:24px 24px 18px}
.workspace-flyout-title{display:flex;flex-direction:column;gap:6px;min-width:0}
.workspace-flyout-title strong{font-size:19px;font-weight:800;letter-spacing:.01em;color:#fff}
.workspace-flyout-title span{font-size:13px;line-height:1.6;color:rgba(255,255,255,.68)}
.workspace-flyout-close{width:40px;height:40px;border:none;border-radius:14px;background:rgba(255,255,255,.08);color:#fff;font-size:22px;line-height:1;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0;box-shadow:inset 0 1px 0 rgba(255,255,255,.05);transition:background .18s ease,transform .18s ease}
.workspace-flyout-close:hover{background:rgba(255,255,255,.16);transform:translateY(-1px)}
.workspace-flyout-tabs{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;padding:0 24px 18px;border-bottom:1px solid rgba(255,255,255,.08)}
.workspace-flyout-tab{height:42px;border:none;border-radius:16px;background:rgba(255,255,255,.08);padding:0 16px;font-size:13px;font-weight:800;color:rgba(255,255,255,.72);cursor:pointer;transition:all .18s ease;box-shadow:inset 0 1px 0 rgba(255,255,255,.03)}
.workspace-flyout-tab:hover{background:rgba(255,255,255,.14);color:#fff}
.workspace-flyout-tab.is-active{background:linear-gradient(135deg,rgba(231,191,95,.28),rgba(42,157,143,.22));color:#fff;box-shadow:inset 0 0 0 1px rgba(255,255,255,.12),0 12px 24px rgba(15,23,42,.18)}
.workspace-flyout-body{flex:1;min-height:0;overflow:hidden}
.workspace-tab-panel{height:100%;min-height:0}
#workspace-settings-panel,#workspace-diagnostics-panel{padding:0 24px 24px;display:flex;flex-direction:column;gap:18px;overflow:auto}
.workspace-console{scrollbar-width:thin}
.workspace-hero{display:flex;flex-direction:column;gap:18px;padding:24px;border-radius:28px;background:
linear-gradient(145deg,rgba(231,191,95,.2),rgba(42,157,143,.15) 42%,rgba(255,255,255,.08)),
linear-gradient(180deg,rgba(255,255,255,.06),rgba(255,255,255,.03));border:1px solid rgba(255,255,255,.14);box-shadow:0 24px 48px rgba(4,10,20,.22),inset 0 1px 0 rgba(255,255,255,.05)}
.workspace-diagnostics-hero{background:
linear-gradient(145deg,rgba(64,145,255,.18),rgba(42,157,143,.14) 48%,rgba(255,255,255,.08)),
linear-gradient(180deg,rgba(255,255,255,.06),rgba(255,255,255,.03))}
.workspace-hero-top{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
.workspace-hero-kicker{display:inline-flex;align-items:center;gap:8px;padding:7px 12px;border-radius:999px;background:rgba(7,18,36,.34);border:1px solid rgba(255,255,255,.08);font-size:11px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:#c8d5e6}
.workspace-status-chip{display:inline-flex;align-items:center;padding:8px 14px;border-radius:999px;background:rgba(255,255,255,.95);font-size:12px;font-weight:800;color:#243449;box-shadow:0 10px 24px rgba(4,10,20,.18)}
.workspace-status-chip.is-mode-test{background:#fff6db;color:#8a5b00}
.workspace-status-chip.is-mode-ai{background:#d9fbef;color:#0f766e}
.workspace-status-chip.is-mode-approval{background:#e1e7ff;color:#3730a3}
.workspace-status-chip.is-mode-off{background:#ffe2e2;color:#991b1b}
.workspace-status-chip-diagnostics{background:#dce8ff;color:#213a7a}
.workspace-hero-copy h2{font-size:28px;font-weight:800;line-height:1.08;letter-spacing:-.02em;color:#fff;max-width:12ch}
.workspace-hero-copy p{margin-top:10px;font-size:14px;line-height:1.7;color:rgba(255,255,255,.78);max-width:48ch}
.workspace-overview-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.workspace-overview-card{display:flex;flex-direction:column;gap:8px;padding:16px 18px;border-radius:22px;background:rgba(7,18,36,.28);border:1px solid rgba(255,255,255,.08)}
.workspace-overview-label{font-size:11px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:#c0ccdb}
.workspace-overview-value{font-size:15px;font-weight:800;line-height:1.5;color:#fff}
.workspace-overview-note{font-size:12px;line-height:1.55;color:rgba(255,255,255,.62)}
.workspace-section{display:flex;flex-direction:column;gap:16px;padding:20px;border-radius:26px;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.08);box-shadow:0 18px 38px rgba(4,10,20,.14)}
.workspace-section-head{display:flex;align-items:flex-start;gap:14px}
.workspace-section-index{display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:14px;background:rgba(255,255,255,.12);font-size:12px;font-weight:800;letter-spacing:.08em;color:#fff;flex-shrink:0}
.workspace-section-copy{min-width:0}
.workspace-section-title{display:block;font-size:16px;font-weight:800;letter-spacing:.01em;color:#fff}
.workspace-section-text{margin-top:5px;font-size:13px;line-height:1.65;color:rgba(255,255,255,.72);max-width:48ch}
.workspace-fields{display:grid;gap:14px}
.workspace-fields-split{grid-template-columns:repeat(2,minmax(0,1fr))}
.workspace-field{display:flex;flex-direction:column;gap:8px;min-width:0}
.workspace-field-span{grid-column:1 / -1}
.workspace-field label{font-size:11px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:#c0ccdb}
#workspace-settings-panel .header-select,#workspace-settings-panel .header-input{height:48px;border-radius:16px;border:1px solid rgba(255,255,255,.14);background:rgba(255,255,255,.94);box-shadow:0 12px 24px rgba(4,10,20,.14)}
#workspace-settings-panel .header-select:focus,#workspace-settings-panel .header-input:focus{box-shadow:0 0 0 3px rgba(231,191,95,.18),0 12px 24px rgba(4,10,20,.18)}
.workspace-mode-shell{display:flex;flex-direction:column;gap:14px}
.workspace-mode-note{display:flex;flex-direction:column;gap:5px;padding:14px 16px;border-radius:18px;background:rgba(7,18,36,.28);border:1px solid rgba(255,255,255,.08)}
.workspace-mode-note strong{font-size:13px;font-weight:800;color:#fff}
.workspace-mode-note span{font-size:12px;line-height:1.6;color:rgba(255,255,255,.7)}
#workspace-settings-panel .workspace-mode-switch{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;border:none;background:transparent;min-height:0}
#workspace-settings-panel .workspace-mode-switch .mode-btn{min-height:50px;border-radius:18px;border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.08);color:rgba(255,255,255,.74);box-shadow:inset 0 1px 0 rgba(255,255,255,.03)}
#workspace-settings-panel .workspace-mode-switch .mode-btn:hover{background:rgba(255,255,255,.16);color:#fff}
#workspace-settings-panel .workspace-mode-switch .mode-btn.is-active-mode[data-mode="test"]{background:rgba(245,158,11,.22);border-color:rgba(245,158,11,.34);color:#fde68a}
#workspace-settings-panel .workspace-mode-switch .mode-btn.is-active-mode[data-mode="ai"]{background:rgba(16,185,129,.24);border-color:rgba(16,185,129,.34);color:#bbf7d0}
#workspace-settings-panel .workspace-mode-switch .mode-btn.is-active-mode[data-mode="approval"]{background:rgba(99,102,241,.24);border-color:rgba(129,140,248,.36);color:#c7d2fe}
#workspace-settings-panel .workspace-mode-switch .mode-btn.is-active-mode[data-mode="off"]{background:rgba(239,68,68,.24);border-color:rgba(248,113,113,.34);color:#fecaca}
.workspace-action-stack{display:grid;gap:12px}
.workspace-action-card,.workspace-danger-card{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:16px 18px;border-radius:22px;background:rgba(7,18,36,.24);border:1px solid rgba(255,255,255,.08)}
.workspace-action-copy{min-width:0;display:flex;flex-direction:column;gap:4px}
.workspace-action-copy strong{font-size:14px;font-weight:800;line-height:1.4;color:#fff}
.workspace-action-copy span{font-size:12px;line-height:1.6;color:rgba(255,255,255,.68)}
.workspace-action-card .btn,.workspace-danger-card .btn{min-width:144px;height:48px;border-radius:16px}
.workspace-action-footer{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:12px;align-items:end}
#workspace-settings-panel .workspace-action-card .btn-ghost{background:rgba(255,255,255,.95);color:#1f3048}
#workspace-settings-panel .workspace-action-card .btn-toggle{background:rgba(255,255,255,.12);color:#fff}
#workspace-settings-panel .workspace-action-footer .btn-save{min-width:188px}
.workspace-section-danger{background:linear-gradient(180deg,rgba(127,29,29,.24),rgba(69,10,10,.18));border-color:rgba(248,113,113,.18)}
.workspace-danger-card{background:rgba(127,29,29,.16);border-color:rgba(248,113,113,.12)}
#workspace-settings-panel .workspace-danger-card .btn-reset{background:#fff;color:#991b1b;box-shadow:0 14px 26px rgba(69,10,10,.18)}
.workspace-signal-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.workspace-signal-card{display:flex;flex-direction:column;gap:8px;padding:16px 18px;border-radius:22px;background:rgba(7,18,36,.28);border:1px solid rgba(255,255,255,.08)}
.workspace-signal-card-wide{grid-column:1 / -1}
.workspace-signal-card-accent{background:linear-gradient(135deg,rgba(99,102,241,.18),rgba(42,157,143,.16));border-color:rgba(191,219,254,.16)}
.workspace-signal-label{font-size:11px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:#c0ccdb}
.workspace-signal-value{font-size:15px;font-weight:800;line-height:1.5;color:#fff;min-height:24px}
.workspace-signal-value .debug-badge{font-size:12px}
.workspace-signal-note{font-size:12px;line-height:1.55;color:rgba(255,255,255,.62)}
.workspace-signal-flags{display:flex;flex-wrap:wrap;gap:6px}
.workspace-diagnostics-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.workspace-diagnostics-card{display:flex;flex-direction:column;gap:14px;padding:18px;border-radius:22px;background:rgba(7,18,36,.24);border:1px solid rgba(255,255,255,.08);min-width:0}
.workspace-diagnostics-card-tall{min-height:240px}
.workspace-card-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}
.workspace-card-head strong{display:block;font-size:14px;font-weight:800;color:#fff}
.workspace-card-head span{display:block;margin-top:4px;font-size:12px;line-height:1.55;color:rgba(255,255,255,.66)}
.workspace-mono-box{font-family:var(--mono);font-size:12px;white-space:pre-wrap;word-break:break-word;color:#bfdbfe;background:rgba(2,6,23,.35);border-radius:16px;padding:14px;max-height:320px;min-height:176px;overflow:auto}
.workspace-studio-shell{display:flex;flex-direction:column;gap:14px}
.workspace-feedback-stack{display:flex;flex-direction:column;gap:14px}
.workspace-empty-note{padding:14px 16px;border-radius:18px;background:rgba(7,18,36,.2);border:1px dashed rgba(255,255,255,.14);font-size:12px;line-height:1.65;color:rgba(255,255,255,.72)}
.workspace-inline-note{font-size:12px;line-height:1.55;color:rgba(255,255,255,.72)}
.workspace-report-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.workspace-section-head-wide{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}
.workspace-section-head-main{display:flex;align-items:flex-start;gap:14px;min-width:0}
.workspace-section-head-wide .btn{flex-shrink:0}
.btn-toggle{display:inline-flex;align-items:center;justify-content:center}
@keyframes pulse{from{opacity:.8}to{opacity:1}}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@keyframes bounce{to{opacity:.35;transform:translateY(-4px)}}
@media(max-width:1500px){
  .main{grid-template-columns:minmax(300px,340px) minmax(0,1fr) minmax(292px,332px)}
}
@media(max-width:1240px){
  .header{padding:14px 18px}
  .header--workspace{grid-template-columns:1fr}
  .header--workspace .header-brand{max-width:none}
  .header-status,.header-utility{justify-content:flex-start}
  .main{grid-template-columns:minmax(296px,336px) minmax(0,1fr)}
  .context-panel{display:none}
  .template-panel-grid{grid-template-columns:1fr}
  .msg{max-width:86%}
  .workspace-overview-grid,.workspace-fields-split,.workspace-action-footer,.workspace-signal-grid,.workspace-diagnostics-grid,.workspace-report-grid{grid-template-columns:1fr}
  .workspace-action-card,.workspace-danger-card{flex-direction:column;align-items:stretch}
  .workspace-section-head-wide{flex-direction:column;align-items:stretch}
  .workspace-action-card .btn,.workspace-danger-card .btn,#workspace-settings-panel .workspace-action-footer .btn-save{width:100%;min-width:0}
}
@media(max-width:980px){
  body{overflow:auto}
  .app{height:auto;min-height:100vh}
  .header{gap:12px}
  .header--workspace .header-brand{min-width:0}
  .header-status,.header-utility{width:100%}
  .workspace-flyout-header,.workspace-flyout-tabs{padding-left:18px;padding-right:18px}
  #workspace-settings-panel,#workspace-diagnostics-panel{padding-left:18px;padding-right:18px}
  .workspace-hero,.workspace-section{padding:18px}
  .workspace-hero-copy h2{font-size:24px;max-width:none}
  .workspace-overview-grid,.workspace-fields-split,.workspace-action-footer,.workspace-signal-grid,.workspace-diagnostics-grid,.workspace-report-grid,#workspace-settings-panel .workspace-mode-switch{grid-template-columns:1fr}
  .header-select,.header-input{width:100%}
  .main{grid-template-columns:1fr;min-height:calc(100vh - 170px);padding:12px}
  .queue-panel{max-height:clamp(38vh,50vh,60vh)}
  .context-panel{display:flex}
  .queue-panel-head,.context-panel-head,.thread-header,.session-strip,.messages,.input-bar,.queue-toolbar,.context-panel .context-tabs{padding-left:16px;padding-right:16px}
  .live-feed-head{flex-direction:column;align-items:flex-start}
  .live-feed-head-meta{justify-content:flex-start}
  .msg{max-width:90%}
  .template-panel-head{flex-direction:column;align-items:flex-start}
  .template-panel-actions{justify-content:flex-start}
  .composer-chip{max-width:100%}
  .context-row{grid-template-columns:1fr}
  .guest-grid,.guest-actions{grid-template-columns:minmax(0,1fr)}
}
"""

TEST_CHAT_SCRIPT = UI_SHARED_SCRIPT + """\
const API = '/api/v1/test';
const ADMIN_ENTRY_PATH = '/admin';
const CSRF_COOKIE = 'velox_admin_csrf';
const TOAST_TIMEOUT_MS = 2800;
const DEFAULT_FEEDBACK_SCALES = [
  {rating: 1, label: 'Kesinlikle Yanlış', summary: 'Yanıt tamamen hatalı.', tooltip: 'Bilgi tamamen yanlışsa bunu seçin ve doğru bilgiyi sisteme öğretin.', correction_required: true},
  {rating: 2, label: 'Hatalı Anlatım', summary: 'Bilgi özünde doğru ama anlatım bozuk.', tooltip: 'Bilgi doğru ama anlatımı bozuksa bunu seçin.', correction_required: true},
  {rating: 3, label: 'Eksik Bilgi', summary: 'Temel cevap doğru ama kritik detay eksik.', tooltip: 'Cevap yetersizse eksikleri tamamlayın.', correction_required: true},
  {rating: 4, label: 'Gereksiz Ayrıntı', summary: 'Bilgi doğru ama fazla uzun.', tooltip: 'Gereksiz uzunsa daha sade bir sürümü onaylayın.', correction_required: true},
  {rating: 5, label: 'Mükemmel', summary: 'Yanıt doğru ve onaylı örnek olmaya uygun.', tooltip: 'Yanıt doğruysa bunu seçin; onaylı örnek havuzuna eklenir.', correction_required: false},
];
const DEFAULT_FEEDBACK_CATEGORIES = [
  {key: 'yanlis_bilgi', label: 'Yanlış Bilgi', description: 'Net olarak yanlış bilgi verilmesi.', tooltip: 'Örnek: EUR yerine USD yazmak.'},
  {key: 'eksik_bilgi', label: 'Eksik Bilgi', description: 'Temel cevap doğru ama kritik detaylar eksik.', tooltip: 'Cevap yarım kalıyor veya gerekli bilgi tamamlanmıyor.'},
  {key: 'alakasiz_yanit', label: 'Alakasız Yanıt', description: 'Sorudan kopuk veya konu dışı cevap.', tooltip: 'Kullanıcı niyetini kaçıran cevaplar.'},
  {key: 'baglam_kopuklugu', label: 'Bağlam Kopukluğu', description: 'Sohbet akışına uyumsuz cevap.', tooltip: 'Hafıza kaybı varmış gibi davranan cevaplar.'},
  {key: 'uydurma_bilgi', label: 'Aşırı Özgüvenli Uydurma', description: 'Kaynaksız bilgi uydurulması.', tooltip: 'Bilmiyorum demek yerine uydurma bilgi verilmesi.'},
  {key: 'gevezelik', label: 'Gevezelik / Uzunluk', description: 'Gereksiz uzun veya dağınık cevap.', tooltip: 'Kısa bir istek için aşırı uzun mesaj.'},
  {key: 'intent_iskalama', label: 'Niyet Kaçırma', description: 'Asıl talebi kaçıran cevap.', tooltip: 'Kelimeyi anlayıp amacı göremeyen cevap.'},
  {key: 'format_ihlali', label: 'Format İhlali', description: 'İstenen sunum biçimine uymayan cevap.', tooltip: 'Liste yerine düz metin kullanılması gibi.'},
  {key: 'mantik_celiskisi', label: 'Eksik / Çelişkili Mantık', description: 'Tutarsız veya eksik mantık.', tooltip: 'Bir adımın diğerini bozduğu durumlar.'},
  {key: 'ton_politika_ihlali', label: 'Ton / Politika İhlali', description: 'Üslup veya politika ihlali.', tooltip: 'Kaba üslup ya da yetkisiz taahhüt.'},
  {key: 'ozel_kategori', label: 'Özel Kategori', description: 'Hazır listeye sığmayan durum.', tooltip: 'Açıklamayı yönetici manuel olarak yazar.'},
];
const DEFAULT_FEEDBACK_TAGS = [
  {key: 'yanlis_bilgi', label: 'Yanlış Bilgi', description: 'Net bilgi hatası.'},
  {key: 'eksik_bilgi', label: 'Eksik Bilgi', description: 'Kritik detay eksik.'},
  {key: 'alakasiz_yanit', label: 'Alakasız Yanıt', description: 'Sorudan kopuk cevap.'},
  {key: 'baglam_kopuklugu', label: 'Bağlam Kopukluğu', description: 'Önceki konuşma unutuluyor.'},
  {key: 'niyet_iskalama', label: 'Niyet Kaçırma', description: 'Asıl amaç anlaşılmıyor.'},
  {key: 'asiri_uzun_yanit', label: 'Aşırı Uzun Yanıt', description: 'Gereksiz uzun mesaj.'},
  {key: 'asiri_kisa_yanit', label: 'Aşırı Kısa Yanıt', description: 'Eksik açıklama içeren kısa cevap.'},
  {key: 'tekrar_loop', label: 'Tekrar / Döngü', description: 'Aynı kalıp tekrar ediyor.'},
  {key: 'format_ihlali', label: 'Format İhlali', description: 'İstenen format bozuluyor.'},
  {key: 'ton_uyumsuzlugu', label: 'Ton Uyumsuzluğu', description: 'Duruma uygun olmayan üslup.'},
  {key: 'kaba_uslup', label: 'Kaba Üslup', description: 'Beklenen sıcak ve profesyonel ton bozuluyor.'},
  {key: 'politika_ihlali', label: 'Politika İhlali', description: 'Kuralların dışına çıkılıyor.'},
  {key: 'uydurma_bilgi', label: 'Uydurma Bilgi', description: 'Kaynaksız bilgi uyduruluyor.'},
  {key: 'guncel_olmayan_bilgi', label: 'Güncel Olmayan Bilgi', description: 'Eski bilgi kullanılıyor.'},
  {key: 'hotel_profile_celiskisi', label: 'Otel Profili Çelişkisi', description: 'Otel profili ile uyumsuz cevap.'},
  {key: 'tool_output_celiskisi', label: 'Araç Çıktısı Çelişkisi', description: 'Araç sonucu ile uyumsuz cevap.'},
  {key: 'mantik_celiskisi', label: 'Mantık Çelişkisi', description: 'Cevap kendi içinde tutarsız.'},
  {key: 'eksik_dogrulama_sorusu', label: 'Eksik Doğrulama Sorusu', description: 'Gerekli netleştirme sorusu yok.'},
  {key: 'gereksiz_pii_talebi', label: 'Gereksiz Kişisel Veri Talebi', description: 'Gereksiz kişisel veri istendi.'},
  {key: 'gereksiz_escalation', label: 'Gereksiz İnsan Devri', description: 'Gereksiz insan devri yapıldı.'},
];

const state = {
  adminToken: '',
  hotelId: '',
  sourceType: 'live_test_chat',
  importFile: '',
  roleMapping: {},
  messages: [],
  inflightMessages: new Map(),
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
  refreshPromise: null,
  operationMode: 'test',
  liveConversations: [],
  importItems: [],
  activeConversationId: null,
  queueFilter: 'all',
  queueSearch: '',
  replyTarget: null,
  composerAttachments: [],
  uploadInProgress: 0,
  mediaRecorder: null,
  mediaChunks: [],
  isRecordingVoice: false,
  composerMode: 'reply',
  composerDrafts: new Map(),
  contextTab: 'guest',
  templateTemplates: [],
  templateSearch: '',
  selectedTemplateId: null,
  renderedMessagesSignature: '',
  renderedThreadHeaderSignature: '',
  renderedSessionStripSignature: '',
  renderedContextRailSignature: '',
  liveConversationRequest: null,
  liveConversationRequestId: '',
  sync: {
    lastPanelRefreshAt: null,
    lastConversationRefreshAt: null,
    connectionState: 'idle',
  },
  workspaceFlyoutOpen: false,
  workspaceFlyoutTab: 'settings',
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
const WORKSPACE_FLYOUT_FOCUSABLE = 'button:not([disabled]),[href],input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])';

const el = id => document.getElementById(id);
let _workspaceFlyoutReturnFocus = null;

// escapeHtml, formatMessageHtml, formatTime provided by UI_SHARED_SCRIPT
const fmtTime = formatTime;

function currentConversationKey() {
  if (state.sourceType === 'live_conversation' && state.activeConversationId) return `live:${state.activeConversationId}`;
  return `test:${(el('phone-input')?.value || 'test_user_123').trim() || 'test_user_123'}`;
}

function clearComposerDraft(key = currentConversationKey()) {
  state.composerDrafts.delete(key);
  rerenderQueueRail();
}

function buildMessagesRenderSignature() {
  return JSON.stringify({
    sourceType: state.sourceType,
    activeConversationId: state.activeConversationId || '',
    messageCount: state.messages.length,
    messages: state.messages.map(message => ({
      id: message.id || '',
      role: message.role || '',
      content: message.content || '',
      created_at: message.created_at || '',
      status: message.status || '',
      local_status: message.local_status || '',
      provider_status: message.provider_status || '',
      send_blocked: Boolean(message.send_blocked),
      approval_pending: Boolean(message.approval_pending),
      rejected: Boolean(message.rejected),
      internal_note: Boolean(message.internal_note),
      whatsapp_message_id: message.whatsapp_message_id || '',
      attachment_count: Array.isArray(message.attachments) ? message.attachments.length : 0,
    })),
  });
}

function buildThreadHeaderSignature() {
  return JSON.stringify({
    sourceType: state.sourceType,
    operationMode: state.operationMode || '',
    conversation: state.conversation || null,
  });
}

function buildSessionStripSignature() {
  return JSON.stringify({
    sourceType: state.sourceType,
    operationMode: state.operationMode || '',
    conversation: state.conversation || null,
    delivery: latestDeliverySummary(),
    sync: getSyncSnapshot(),
  });
}

function buildContextRailSignature() {
  return JSON.stringify({
    contextTab: state.contextTab,
    operationMode: state.operationMode || '',
    conversation: state.conversation || null,
    delivery: latestDeliverySummary(),
    messageCount: state.messages.length,
    messages: state.messages.map(message => ({
      id: message.id || '',
      role: message.role || '',
      created_at: message.created_at || '',
      content: message.content || '',
      internal_note: Boolean(message.internal_note),
      internal_json: message.internal_json || null,
      send_blocked: Boolean(message.send_blocked),
      approval_pending: Boolean(message.approval_pending),
      rejected: Boolean(message.rejected),
    })),
  });
}

function conversationRequiresTemplate() {
  return state.sourceType === 'live_conversation' && String(state.conversation?.window_state || '') === 'closed';
}

function normalizeComposerMode() {
  if (conversationRequiresTemplate() && state.composerMode !== 'internal_note' && state.composerMode !== 'template') {
    state.composerMode = 'template';
  }
}

function applyComposerMode(requestedMode = 'reply', options = {}) {
  const {
    warnOnTemplateGate = false,
    focusInput = false,
  } = options;
  saveComposerDraft();
  if (conversationRequiresTemplate() && requestedMode !== 'template' && requestedMode !== 'internal_note') {
    state.composerMode = 'template';
    if (warnOnTemplateGate) {
      notify('Bu konuşmada servis penceresi kapalı. Misafire serbest mesaj yerine şablon kullanılmalıdır.', 'warn');
    }
  } else {
    state.composerMode = requestedMode;
  }
  renderComposerModeBar();
  renderComposerHelper();
  setComposerMode(state.sourceType === 'live_test_chat' || state.sourceType === 'live_conversation');
  saveComposerDraft();
  if (focusInput && !el('msg-input')?.disabled) {
    el('msg-input').focus();
  }
}

function saveComposerDraft() {
  const key = currentConversationKey();
  state.composerDrafts.set(key, {
    mode: state.composerMode,
    text: el('msg-input')?.value || '',
    replyTarget: state.replyTarget ? {...state.replyTarget} : null,
  });
  rerenderQueueRail();
}

function rerenderQueueRail() {
  const container = el('live-feed-container');
  if (!container) return;
  renderLiveFeed(container, {conversations: state.liveConversations});
  const activeCard = container.querySelector('.live-feed-card.is-active');
  if (activeCard) activeCard.scrollIntoView({block: 'nearest'});
}

function queueDraftForConversation(conversationId) {
  if (!conversationId) return null;
  return state.composerDrafts.get(`live:${conversationId}`) || null;
}

function queueDraftLabel(conversationId) {
  const draft = queueDraftForConversation(conversationId);
  if (!draft || !String(draft.text || '').trim()) return '';
  if (draft.mode === 'internal_note') return 'not taslağı';
  if (draft.mode === 'template') return 'şablon taslağı';
  if (draft.mode === 'ai_draft') return 'yapay zekâ taslağı';
  return 'taslak var';
}

function queueHumanOverrideActive(conversation = {}) {
  return Boolean(conversation.human_override)
    || String(conversation.state || '').toLowerCase().includes('handoff')
    || String(conversation.state || '').toLowerCase().includes('human');
}

function queueNeedsAttention(conversation = {}) {
  const blocked = conversation.send_blocked === 'true'
    || conversation.send_blocked === true
    || conversation.approval_pending === 'true'
    || conversation.approval_pending === true;
  const rejected = conversation.rejected === 'true' || conversation.rejected === true;
  return blocked
    || rejected
    || String(conversation.delivery_state || '').includes('failed')
    || String(conversation.window_state || '') === 'closing_soon'
    || String(conversation.window_state || '') === 'closed';
}

function queueSessionReopenLabel(conversation = {}) {
  if (!conversation.session_reopen_template_sent) return '';
  return conversation.session_reopen_template_name || 'reopen sablonu';
}

function queueDeliveryTone(value = '') {
  const normalized = String(value || '').toLowerCase();
  if (normalized.includes('fail') || normalized.includes('error') || normalized.includes('reject')) return 'danger';
  if (normalized === 'read' || normalized === 'delivered' || normalized === 'accepted') return 'success';
  if (normalized === 'sent') return 'info';
  if (normalized.includes('pending') || normalized.includes('approval')) return 'warning';
  return 'muted';
}

function queueBadgeHtml(label, tone = 'muted') {
  const styles = {
    success: 'color:#166534;background:rgba(34,197,94,.12)',
    warning: 'color:#b45309;background:rgba(245,158,11,.16)',
    danger: 'color:#991b1b;background:rgba(239,68,68,.14)',
    info: 'color:#075985;background:rgba(56,189,248,.14)',
    accent: 'color:#6d28d9;background:rgba(196,181,253,.18)',
    handoff: 'color:#854d0e;background:rgba(253,230,138,.28)',
  };
  const style = styles[tone] || '';
  return '<span class="live-feed-badge"' + (style ? ' style="' + style + '"' : '') + '>' + escapeHtml(label) + '</span>';
}

function getVisibleQueueConversations(rawConversations = state.liveConversations) {
  const rawConvs = rawConversations || [];
  const queueSearch = String(state.queueSearch || '').trim().toLowerCase();
  return rawConvs.filter(c => {
    const blocked = c.send_blocked === 'true' || c.send_blocked === true || c.approval_pending === 'true' || c.approval_pending === true;
    const human = queueHumanOverrideActive(c);
    const attention = queueNeedsAttention(c);
    if (state.queueFilter === 'approval' && !blocked) return false;
    if (state.queueFilter === 'human' && !human) return false;
    if (state.queueFilter === 'attention' && !attention) return false;
    if (!queueSearch) return true;
    const draftLabel = queueDraftLabel(c.id);
    const reopenLabel = queueSessionReopenLabel(c);
    const haystack = [c.phone_display, c.last_user_msg, c.last_assistant_msg, c.intent, c.state, c.provider_status, draftLabel, reopenLabel, human ? 'insan devri human override manual' : '', ...(c.risk_flags || [])].join(' ').toLowerCase();
    return haystack.includes(queueSearch);
  });
}

function activeQueueIndex(visibleConversations = getVisibleQueueConversations()) {
  return visibleConversations.findIndex(conversation => String(conversation.id) === String(state.activeConversationId));
}

function activeQueueConversationFiltered(rawConversations = state.liveConversations, visibleConversations = getVisibleQueueConversations(rawConversations)) {
  if (!state.activeConversationId) return false;
  const activeInRaw = rawConversations.some(conversation => String(conversation.id) === String(state.activeConversationId));
  if (!activeInRaw) return false;
  return !visibleConversations.some(conversation => String(conversation.id) === String(state.activeConversationId));
}

async function moveQueueSelection(step = 1) {
  const visibleConversations = getVisibleQueueConversations();
  if (!visibleConversations.length) return;
  const currentIndex = activeQueueIndex(visibleConversations);
  const nextIndex = currentIndex < 0
    ? (step > 0 ? 0 : visibleConversations.length - 1)
    : Math.min(Math.max(currentIndex + step, 0), visibleConversations.length - 1);
  const nextConversation = visibleConversations[nextIndex];
  if (!nextConversation) return;
  await loadLiveConversation(nextConversation.id);
}

function renderQueueSummary(rawConversations = [], visibleConversations = rawConversations) {
  const container = el('queue-summary');
  if (!container) return;
  const allCount = rawConversations.length;
  const approvalCount = rawConversations.filter(conversation =>
    conversation.send_blocked === 'true'
    || conversation.send_blocked === true
    || conversation.approval_pending === 'true'
    || conversation.approval_pending === true,
  ).length;
  const humanCount = rawConversations.filter(queueHumanOverrideActive).length;
  const attentionCount = rawConversations.filter(queueNeedsAttention).length;
  const draftCount = rawConversations.filter(conversation => Boolean(queueDraftLabel(conversation.id))).length;
  const reopenCount = rawConversations.filter(conversation => Boolean(queueSessionReopenLabel(conversation))).length;
  const visibleCount = visibleConversations.length;
  const chips = [
    `<span class="queue-summary-chip">Gorunen ${visibleCount}/${allCount}</span>`,
    `<span class="queue-summary-chip">Onay ${approvalCount}</span>`,
    `<span class="queue-summary-chip">Insan ${humanCount}</span>`,
    `<span class="queue-summary-chip">Dikkat Gerektiren ${attentionCount}</span>`,
    `<span class="queue-summary-chip">Taslak ${draftCount}</span>`,
    `<span class="queue-summary-chip">Reopen ${reopenCount}</span>`,
    '<span class="queue-summary-chip">J/K ile gez</span>',
  ];
  if (activeQueueConversationFiltered(rawConversations, visibleConversations)) {
    chips.push('<span class="queue-summary-chip queue-summary-chip-warning">Aktif konusma filtre disinda</span>');
  }
  container.innerHTML = chips.join('');
}

function restoreComposerDraft() {
  const key = currentConversationKey();
  const draft = state.composerDrafts.get(key);
  if (!draft) {
    state.composerMode = 'reply';
    normalizeComposerMode();
    state.replyTarget = null;
    if (el('msg-input')) el('msg-input').value = '';
    renderComposerModeBar();
    renderReplyPreview();
    renderComposerHelper();
    return;
  }
  state.composerMode = draft.mode || 'reply';
  normalizeComposerMode();
  state.replyTarget = draft.replyTarget ? {...draft.replyTarget} : null;
  if (el('msg-input')) el('msg-input').value = draft.text || '';
  renderComposerModeBar();
  renderReplyPreview();
  renderComposerHelper();
}

function formatRelativeTime(value) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  const diff = Math.max(0, Date.now() - date.getTime());
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'şimdi';
  if (mins < 60) return `${mins} dk`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} sa`;
  const days = Math.floor(hours / 24);
  return `${days} g`;
}

function formatWindowBadge(conversation = {}) {
  const stateValue = String(conversation.window_state || 'unknown');
  const remainingSeconds = Number(conversation.window_remaining_seconds || 0);
  if (stateValue === 'open') {
    const hours = Math.floor(remainingSeconds / 3600);
    const mins = Math.floor((remainingSeconds % 3600) / 60);
    return {label: `Pencere açık ${hours}s ${mins}dk`, tone: 'success'};
  }
  if (stateValue === 'closing_soon') {
    const mins = Math.floor(remainingSeconds / 60);
    return {label: `Pencere kapanıyor ${mins}dk`, tone: 'warning'};
  }
  if (stateValue === 'closed') {
    return {label: 'Pencere kapalı · şablon gerekli', tone: 'danger'};
  }
  return {label: 'Pencere durumu bilinmiyor', tone: 'muted'};
}

function getConversationDisplayTitle(conversation = null) {
  if (!conversation) return 'Konuşma seçin';
  return conversation.phone_display || conversation.display_name || 'Maskeli kullanıcı';
}

function getConversationSubtitle(conversation = null) {
  if (!conversation) return 'Soldaki kuyruktan bir konuşma açın veya test kimliği ile yeni bir test başlatın.';
  const parts = [
    conversation.language ? `Dil: ${conversation.language}` : null,
    conversation.intent ? `Niyet: ${conversation.intent}` : null,
    conversation.state ? `Durum: ${conversation.state}` : null,
    conversation.human_override ? 'İnsan devri aktif' : null,
  ].filter(Boolean);
  return parts.join(' · ') || 'Konuşma özeti hazır.';
}

function guestToneClass(tone = 'muted') {
  const normalized = String(tone || 'muted').toLowerCase();
  if (['success', 'warning', 'danger', 'info'].includes(normalized)) return `is-${normalized}`;
  return 'is-muted';
}

function guestStatusBadgeHtml(label, tone = 'muted') {
  return `<span class="guest-status-badge ${guestToneClass(tone)}">${escapeHtml(label || '-')}</span>`;
}

function renderGuestField(label, value, {full = false} = {}) {
  return `<div class="guest-field${full ? ' full' : ''}"><span>${escapeHtml(label || '-')}</span><strong>${escapeHtml(value || '-')}</strong></div>`;
}

function formatGuestParty(guestInfo = {}) {
  const adults = Number(guestInfo.adults || 0);
  const children = Number(guestInfo.children || 0);
  if (!adults && !children) return '-';
  return `${adults} yetişkin${children ? ` • ${children} çocuk` : ''}`;
}

function renderGuestContext(conversation, tags) {
  const guestInfo = conversation?.guest_info || {};
  const guestName = guestInfo.guest_name || getConversationDisplayTitle(conversation);
  const infoStatus = guestInfo.info_status_label || 'Misafir bilgi durumu: veri bekleniyor';
  const infoTone = guestInfo.info_status_tone || 'muted';
  const holdStatusLabel = guestInfo.hold_status_label || 'Rezervasyon Kaydı Yok';
  const holdStatusTone = guestInfo.hold_status_tone || 'muted';
  const reservationReference = guestInfo.reservation_reference || guestInfo.voucher_no || guestInfo.pms_reservation_id || '-';
  const actionNote = guestInfo.status_detail || guestInfo.cancel_reason || guestInfo.approve_reason || 'Rezervasyon aksiyonları için uygun veri bekleniyor.';
  const approveDisabled = !guestInfo.approve_enabled || !guestInfo.hold_id;
  const cancelDisabled = !guestInfo.cancel_enabled || !guestInfo.hold_id;
  const approveReason = approveDisabled ? (guestInfo.approve_reason || 'Onay aksiyonu kullanılamıyor.') : 'Rezervasyon onay akışı başlatılacak.';
  const cancelReason = cancelDisabled ? (guestInfo.cancel_reason || 'İptal aksiyonu kullanılamıyor.') : (guestInfo.cancel_action === 'cancel_reservation' ? 'Elektra PMS üzerinde iptal çağrısı yapılacak.' : 'PMS kaydı oluşmadan önce hold iptal edilecek.');
  return `
    <div class="context-card">
      <div class="guest-card-head">
        <div class="guest-card-title">
          <strong>${escapeHtml(guestName || '-')}</strong>
          <span>${escapeHtml(infoStatus)}</span>
        </div>
        ${guestStatusBadgeHtml(holdStatusLabel, holdStatusTone || infoTone)}
      </div>
      <div class="guest-grid">
        ${renderGuestField('Telefon', guestInfo.phone || conversation.phone_display || '-')}
        ${renderGuestField('E-posta', guestInfo.email || '-')}
        ${renderGuestField('Dil', guestInfo.language || conversation.language || '-')}
        ${renderGuestField('Uyruk', guestInfo.nationality || '-')}
      </div>
    </div>
    <div class="context-card">
      <div class="guest-card-head">
        <div class="guest-card-title">
          <strong>Rezervasyon Detayları</strong>
          <span>${escapeHtml(guestInfo.available ? 'Stay hold ve PMS referansları konuşma ile eşlendi.' : 'Konuşma için bağlı stay hold bulunamadı.')}</span>
        </div>
        ${guestStatusBadgeHtml(infoStatus, infoTone)}
      </div>
      <div class="guest-grid">
        ${renderGuestField('Tarih', `${guestInfo.checkin_date || '-'} → ${guestInfo.checkout_date || '-'}`)}
        ${renderGuestField('Konaklama', guestInfo.nights ? `${guestInfo.nights} gece` : '-')}
        ${renderGuestField('Kişi', formatGuestParty(guestInfo))}
        ${renderGuestField('Toplam', guestInfo.total_price_display || '-')}
        ${renderGuestField('Oda', guestInfo.room_label || '-')}
        ${renderGuestField('Pansiyon', guestInfo.board_label || '-')}
        ${renderGuestField('Referans', reservationReference, {full: true})}
      </div>
    </div>
    <div class="context-card">
      <div class="guest-card-head">
        <div class="guest-card-title">
          <strong>Rezervasyon Aksiyonları</strong>
          <span>${escapeHtml(actionNote)}</span>
        </div>
        ${guestInfo.hold_id ? guestStatusBadgeHtml(guestInfo.hold_id, 'info') : guestStatusBadgeHtml('Hold Yok', 'muted')}
      </div>
      <div class="guest-actions">
        <button class="guest-action-btn primary" type="button" data-guest-action="approve" data-hold-id="${escapeHtml(guestInfo.hold_id || '')}" ${approveDisabled ? 'disabled' : ''}>Rezervasyon Onayla</button>
        <button class="guest-action-btn danger" type="button" data-guest-action="cancel" data-hold-id="${escapeHtml(guestInfo.hold_id || '')}" ${cancelDisabled ? 'disabled' : ''}>Rezervasyon İptal Et</button>
      </div>
      <div class="guest-grid mt-xs">
        ${renderGuestField('Onay Durumu', approveReason, {full: true})}
        ${renderGuestField('İptal Durumu', cancelReason, {full: true})}
      </div>
    </div>
    <div class="context-card">
      <h3>Etiketler</h3>
      <div class="context-tag-row">${tags.length ? tags.map(tag => `<span class="context-tag">${escapeHtml(tag)}</span>`).join('') : '<span class="context-tag">Etiket yok</span>'}</div>
    </div>`;
}

function renderEmptyCard({title, body, actions = [], hints = []} = {}) {
  return `
    <div class="empty-state">
      <svg viewBox="0 0 24 24" fill="currentColor"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/></svg>
      <div class="empty-card">
        <strong>${escapeHtml(title || 'Hazır')}</strong>
        <p>${escapeHtml(body || '')}</p>
        ${actions.length ? `<div class="empty-actions">${actions.map(action => `<button class="btn btn-ghost btn-mini" type="button" data-empty-action="${escapeHtml(action.action)}">${escapeHtml(action.label)}</button>`).join('')}</div>` : ''}
        ${hints.length ? `<div class="empty-hints">${hints.map(hint => `<span class="empty-hint">${escapeHtml(hint)}</span>`).join('')}</div>` : ''}
      </div>
    </div>`;
}

function latestDeliverySummary() {
  const assistant = [...state.messages].reverse().find(message => message.role === 'assistant' && !message.internal_note);
  if (!assistant) return null;
  return {
    localStatus: assistant.local_status || assistant.status || 'unknown',
    providerStatus: assistant.provider_status || 'unknown',
    providerStatusUpdatedAt: assistant.provider_status_updated_at || '',
    whatsappMessageId: assistant.whatsapp_message_id || assistant.internal_json?.whatsapp_message_id || '',
    approvedAt: assistant.internal_json?.approved_at || '',
    sentAt: assistant.internal_json?.sent_at || '',
    providerSentAt: assistant.provider_sent_at || '',
    deliveredAt: assistant.delivered_at || '',
    readAt: assistant.read_at || '',
    failedAt: assistant.failed_at || '',
    providerError: assistant.provider_error || null,
    providerEvents: Array.isArray(assistant.provider_events) ? assistant.provider_events : [],
    sessionReopenTemplateSent: Boolean(assistant.session_reopen_template_sent),
    sessionReopenTemplateName: assistant.session_reopen_template_name || '',
    sessionReopenTemplateSentAt: assistant.session_reopen_template_sent_at || '',
  };
}

function markSyncSuccess(scope = 'panel') {
  const now = new Date().toISOString();
  if (scope === 'conversation') state.sync.lastConversationRefreshAt = now;
  state.sync.lastPanelRefreshAt = now;
  state.sync.connectionState = 'online';
}

function markSyncFailure() {
  state.sync.connectionState = 'degraded';
}

function getSyncSnapshot() {
  const lastRefresh = state.sourceType === 'live_conversation'
    ? state.sync.lastConversationRefreshAt || state.sync.lastPanelRefreshAt
    : state.sync.lastPanelRefreshAt;
  if (!lastRefresh) {
    return {label: 'Panel senkronu bekleniyor', tone: 'muted'};
  }
  const diffMs = Math.max(0, Date.now() - new Date(lastRefresh).getTime());
  const stale = diffMs > 8000 || state.sync.connectionState === 'degraded';
  if (stale) {
    return {label: `Senkron gecikti · ${Math.floor(diffMs / 1000)} sn`, tone: 'warning'};
  }
  return {label: `Son yenileme ${formatRelativeTime(lastRefresh)}`, tone: 'muted'};
}

function isDialogOpen() {
  return Array.from(document.querySelectorAll('dialog')).some(dialog => dialog.open);
}

function toggleShortcutDialog(forceOpen = null) {
  const dialog = el('shortcut-dialog');
  if (!dialog) return;
  const shouldOpen = forceOpen === null ? !dialog.open : Boolean(forceOpen);
  if (shouldOpen) {
    if (!dialog.open) dialog.showModal();
    return;
  }
  if (dialog.open) dialog.close();
}

function renderWorkspaceSummary() {
  const modeClassMap = ['is-mode-test', 'is-mode-ai', 'is-mode-approval', 'is-mode-off'];
  const modeLabels = {
    test: 'Mod: Test',
    ai: 'Mod: Otomatik',
    approval: 'Mod: Onay',
    off: 'Mod: Kapalı',
  };
  const modeChipLabels = {
    test: 'Test modu',
    ai: 'Otomatik mod',
    approval: 'Onay modu',
    off: 'Kapalı mod',
  };
  const modeDescriptions = {
    test: 'Test modunda yanıt üretilir ancak gerçek misafire gönderilmez.',
    ai: 'Otomatik modda uygun yanıtlar canlı konuşmaya doğrudan gönderilir.',
    approval: 'Onay modunda yanıt önce operatör onayına düşer, sonra gönderilir.',
    off: 'Kapalı modda sistem konuşmayı izler ancak yeni yanıt üretmez.',
  };
  const modeIndicator = el('workspace-mode-indicator');
  if (modeIndicator) {
    modeIndicator.textContent = modeLabels[state.operationMode] || ('Mod: ' + String(state.operationMode || '-'));
    modeIndicator.classList.remove(...modeClassMap);
    modeIndicator.classList.add(`is-mode-${state.operationMode || 'test'}`);
  }
  const modeChip = el('workspace-mode-chip');
  if (modeChip) {
    modeChip.textContent = modeChipLabels[state.operationMode] || 'Çalışma modu';
    modeChip.classList.remove(...modeClassMap);
    modeChip.classList.add(`is-mode-${state.operationMode || 'test'}`);
  }
  const sourceSummary = el('workspace-source-summary');
  if (sourceSummary) {
    if (state.sourceType === 'live_conversation') {
      const sourceLabel = state.conversation?.phone_display || state.activeConversationId || 'canlı konuşma';
      sourceSummary.textContent = sourceLabel + ' canlı konuşması';
    } else if (state.importFile) {
      sourceSummary.textContent = 'İçe aktarılan kayıt · ' + state.importFile;
    } else {
      sourceSummary.textContent = 'Yeni test oturumu · ' + ((el('phone-input')?.value || 'test_user_123').trim() || 'test_user_123');
    }
  }
  const modeSummary = el('workspace-mode-summary');
  if (modeSummary) {
    modeSummary.textContent = modeDescriptions[state.operationMode] || 'Seçili mod davranışı burada özetlenir.';
  }
  const diagnosticsOpen = state.workspaceFlyoutOpen && state.workspaceFlyoutTab === 'diagnostics';
  el('workspace-panel-toggle')?.setAttribute('aria-expanded', String(state.workspaceFlyoutOpen));
  el('workspace-open-diagnostics')?.setAttribute('aria-expanded', String(diagnosticsOpen));
}

function getVisibleWorkspaceFlyoutElements() {
  const panel = el('workspace-flyout');
  if (!panel || panel.classList.contains('collapsed')) return [];
  return Array.from(panel.querySelectorAll(WORKSPACE_FLYOUT_FOCUSABLE)).filter(node => {
    if (!(node instanceof HTMLElement)) return false;
    if (node.closest('.hidden')) return false;
    return node.getClientRects().length > 0;
  });
}

function focusWorkspaceFlyoutTab(tab = state.workspaceFlyoutTab) {
  const target = document.querySelector(`#workspace-flyout-tabs [data-workspace-tab="${tab === 'diagnostics' ? 'diagnostics' : 'settings'}"]`);
  target?.focus?.();
}

function handleWorkspaceFlyoutTabKeydown(event) {
  const currentTab = event.target.closest?.('#workspace-flyout-tabs [data-workspace-tab]');
  if (!currentTab) return;
  const tabs = Array.from(document.querySelectorAll('#workspace-flyout-tabs [data-workspace-tab]'));
  if (!tabs.length) return;
  const currentIndex = tabs.indexOf(currentTab);
  if (currentIndex < 0) return;
  let nextIndex = currentIndex;
  if (event.key === 'ArrowRight') nextIndex = (currentIndex + 1) % tabs.length;
  else if (event.key === 'ArrowLeft') nextIndex = (currentIndex - 1 + tabs.length) % tabs.length;
  else if (event.key === 'Home') nextIndex = 0;
  else if (event.key === 'End') nextIndex = tabs.length - 1;
  else return;
  event.preventDefault();
  const nextTab = tabs[nextIndex];
  setWorkspaceFlyoutTab(nextTab.dataset.workspaceTab || 'settings');
  nextTab.focus();
}

function trapWorkspaceFlyoutFocus(event) {
  if (event.key !== 'Tab' || !state.workspaceFlyoutOpen) return;
  const focusable = getVisibleWorkspaceFlyoutElements();
  if (!focusable.length) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
    return;
  }
  if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}

function renderWorkspaceFlyout() {
  const panel = el('workspace-flyout');
  if (!panel) return;
  const normalizedTab = state.workspaceFlyoutTab === 'diagnostics' ? 'diagnostics' : 'settings';
  const isDiagnostics = normalizedTab === 'diagnostics';
  state.workspaceFlyoutTab = normalizedTab;
  panel.classList.toggle('collapsed', !state.workspaceFlyoutOpen);
  panel.setAttribute('aria-hidden', String(!state.workspaceFlyoutOpen));
  panel.setAttribute('aria-modal', String(state.workspaceFlyoutOpen));
  panel.dataset.workspaceTab = normalizedTab;
  el('workspace-scrim')?.classList.toggle('hidden', !state.workspaceFlyoutOpen);
  el('workspace-scrim')?.setAttribute('aria-hidden', String(!state.workspaceFlyoutOpen));
  const appShell = document.querySelector('.app');
  appShell?.classList.toggle('is-workspace-dimmed', state.workspaceFlyoutOpen);
  if (appShell) {
    appShell.setAttribute('aria-hidden', String(state.workspaceFlyoutOpen));
    try {
      appShell.inert = state.workspaceFlyoutOpen;
    } catch (_) {
      // `inert` is best-effort; aria-hidden + focus trap still apply.
    }
  }
  document.querySelectorAll('#workspace-flyout-tabs [data-workspace-tab]').forEach(btn => {
    const isActive = btn.dataset.workspaceTab === normalizedTab;
    btn.classList.toggle('is-active', isActive);
    btn.setAttribute('aria-selected', String(isActive));
    btn.setAttribute('tabindex', isActive ? '0' : '-1');
  });
  el('workspace-settings-panel')?.classList.toggle('hidden', isDiagnostics);
  el('workspace-settings-panel')?.classList.toggle('is-active', !isDiagnostics);
  el('workspace-diagnostics-panel')?.classList.toggle('hidden', !isDiagnostics);
  el('workspace-diagnostics-panel')?.classList.toggle('is-active', isDiagnostics);
  if (el('workspace-flyout-heading')) {
    el('workspace-flyout-heading').textContent = isDiagnostics ? 'Tanılama' : 'Çalışma Ayarları';
  }
  if (el('workspace-flyout-description')) {
    el('workspace-flyout-description').textContent = isDiagnostics
      ? 'Teknik durum, geri bildirim ve metrik görünümü'
      : 'Ortam kontrolleri ve teknik araçlar';
  }
  renderWorkspaceSummary();
}

function setWorkspaceFlyoutTab(tab = 'settings') {
  state.workspaceFlyoutTab = tab === 'diagnostics' ? 'diagnostics' : 'settings';
  renderWorkspaceFlyout();
}

function openWorkspaceFlyout(tab = 'settings') {
  if (!state.workspaceFlyoutOpen) {
    _workspaceFlyoutReturnFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  }
  state.workspaceFlyoutOpen = true;
  state.workspaceFlyoutTab = tab === 'diagnostics' ? 'diagnostics' : 'settings';
  renderWorkspaceFlyout();
  requestAnimationFrame(() => {
    const focusTarget = document.querySelector('#workspace-flyout-tabs .workspace-flyout-tab.is-active') || getVisibleWorkspaceFlyoutElements()[0] || el('workspace-flyout-close');
    focusTarget?.focus?.();
  });
}

function closeWorkspaceFlyout() {
  if (!state.workspaceFlyoutOpen) return;
  state.workspaceFlyoutOpen = false;
  renderWorkspaceFlyout();
  const returnTarget = _workspaceFlyoutReturnFocus && document.contains(_workspaceFlyoutReturnFocus)
    ? _workspaceFlyoutReturnFocus
    : el('workspace-panel-toggle');
  _workspaceFlyoutReturnFocus = null;
  returnTarget?.focus?.();
}

function toggleWorkspaceFlyout(tab = 'settings') {
  const normalizedTab = tab === 'diagnostics' ? 'diagnostics' : 'settings';
  if (state.workspaceFlyoutOpen && state.workspaceFlyoutTab === normalizedTab) {
    closeWorkspaceFlyout();
    return;
  }
  openWorkspaceFlyout(normalizedTab);
}

function handleEscapeShortcut() {
  if (el('shortcut-dialog')?.open) {
    toggleShortcutDialog(false);
    return true;
  }
  if (el('faq-dialog')?.open) {
    el('faq-dialog').close();
    return true;
  }
  if (!el('conv-detail-overlay')?.classList.contains('hidden')) {
    closeConvModal();
    return true;
  }
  if (state.workspaceFlyoutOpen) {
    closeWorkspaceFlyout();
    return true;
  }
  if (state.replyTarget) {
    clearReplyTarget();
    saveComposerDraft();
    return true;
  }
  return false;
}

function focusQueueSearch() {
  const input = el('queue-search');
  if (!input) return;
  input.focus();
  input.select?.();
}

function applyContextTab(tab = 'guest') {
  state.contextTab = tab;
  renderContextRail();
}

function applyQueueFilter(filter = 'all') {
  state.queueFilter = filter;
  document.querySelectorAll('.queue-tab').forEach(item => {
    item.classList.toggle('is-active', item.dataset.queueFilter === filter);
  });
}

function clearQueueSearch() {
  state.queueSearch = '';
  if (el('queue-search')) el('queue-search').value = '';
}

function activeTemplateCandidate() {
  if (!state.templateTemplates.length) return null;
  return state.templateTemplates.find(item => item.id === state.selectedTemplateId)
    || state.templateTemplates.find(item => item.recommended)
    || state.templateTemplates[0];
}

function buildTemplateQuery() {
  const params = new URLSearchParams();
  if (state.sourceType === 'live_conversation' && state.activeConversationId) {
    params.set('conversation_id', state.activeConversationId);
    return params.toString();
  }
  if (state.conversation?.intent) params.set('intent', state.conversation.intent);
  if (state.conversation?.state) params.set('state', state.conversation.state);
  if (state.conversation?.language) params.set('language', state.conversation.language);
  return params.toString();
}

async function loadTemplateCandidates() {
  if (!state.conversation) {
    state.templateTemplates = [];
    state.selectedTemplateId = null;
    renderTemplatePanel();
    return;
  }
  const query = buildTemplateQuery();
  try {
    const data = await apiFetch('/chat/templates' + (query ? `?${query}` : ''));
    state.templateTemplates = data.templates || [];
    const selectedExists = state.templateTemplates.some(item => item.id === state.selectedTemplateId);
    if (!selectedExists) {
      state.selectedTemplateId = (state.templateTemplates.find(item => item.recommended) || state.templateTemplates[0] || {}).id || null;
    }
    renderTemplatePanel();
  } catch (error) {
    state.templateTemplates = [];
    state.selectedTemplateId = null;
    renderTemplatePanel(error.message || 'Şablonlar yüklenemedi.');
  }
}

function renderComposerModeBar() {
  document.querySelectorAll('.composer-mode-btn').forEach(btn => {
    btn.classList.toggle('is-active', btn.dataset.composerMode === state.composerMode);
  });
  const templatePanel = el('template-panel');
  if (!templatePanel) return;
  templatePanel.classList.toggle('hidden', state.composerMode !== 'template');
  renderTemplatePanel();
}

function renderComposerHelper() {
  const helper = el('composer-helper');
  if (!helper) return;
  let text = '';
  if (conversationRequiresTemplate() && state.composerMode === 'template') {
    text = 'Servis penceresi kapalı. Seçili şablon gönderilir; Meta pencere kapalıysa önce onaylı pencere açma şablonu devreye girer.';
  } else if (state.composerMode === 'internal_note') {
    text = 'İç not olarak kaydedilir; misafire gönderilmez.';
  } else if (state.composerMode === 'template') {
    text = 'Şablon modunda listeden başlığa göre seçim yapıp seçili şablonu misafire gönderebilirsiniz.';
  } else if (state.composerMode === 'ai_draft') {
    text = 'Yapay zekâ taslağı bu modda düzenlenir; göndermeden önce son kontrol sizde kalır.';
  }
  helper.textContent = text;
  helper.classList.toggle('hidden', !text);
}

function renderThreadHeader() {
  const container = el('thread-header');
  if (!container) return;
  const nextSignature = buildThreadHeaderSignature();
  if (state.renderedThreadHeaderSignature === nextSignature) {
    return;
  }
  state.renderedThreadHeaderSignature = nextSignature;
  const title = state.sourceType === 'live_test_chat'
    ? `Test: ${(el('phone-input')?.value || 'test_user_123').trim() || 'test_user_123'}`
    : getConversationDisplayTitle(state.conversation);
  const subtitle = state.sourceType === 'live_test_chat'
    ? 'Test akışı · istem ve davranış denemeleri için canlı alan'
    : getConversationSubtitle(state.conversation);
  const modeLabel = state.sourceType === 'live_conversation' ? 'Canlı' : 'Test';
  const windowBadge = formatWindowBadge(state.conversation || {});
  const handoffChip = state.conversation?.human_override
    ? '<span class="thread-chip thread-chip-muted">Insan devri</span>'
    : '';
  container.innerHTML = `
    <div class="thread-header-copy">
      <h2>${escapeHtml(title)}</h2>
      <p>${escapeHtml(subtitle)}</p>
    </div>
    <div class="thread-header-actions">
      <span class="thread-chip thread-chip-muted">${escapeHtml(modeLabel)}</span>
      ${handoffChip}
      <span class="thread-chip ${windowBadge.tone === 'warning' ? 'thread-chip-muted' : ''}">${escapeHtml(windowBadge.label)}</span>
    </div>
  `;
}

function renderSessionStrip() {
  const container = el('session-strip');
  if (!container) return;
  const nextSignature = buildSessionStripSignature();
  if (state.renderedSessionStripSignature === nextSignature) {
    return;
  }
  state.renderedSessionStripSignature = nextSignature;
  const conversation = state.conversation || {};
  if (!conversation || (!conversation.id && state.sourceType !== 'live_test_chat')) {
    container.innerHTML = '<span class="session-pill">Konuşma seçildiğinde oturum durumu burada görünecek.</span>';
    return;
  }
  const windowBadge = formatWindowBadge(conversation);
  const delivery = latestDeliverySummary();
  const sync = getSyncSnapshot();
  const pills = [
    `<span class="session-pill ${windowBadge.tone === 'warning' ? 'is-warning' : windowBadge.tone === 'danger' ? 'is-danger' : ''}">${escapeHtml(windowBadge.label)}</span>`,
  ];
  if (conversation.last_inbound_at || conversation.last_message_at) {
    pills.push(`<span class="session-pill">Son gelen: ${escapeHtml(formatRelativeTime(conversation.last_inbound_at || conversation.last_message_at))}</span>`);
  }
  if (conversation.last_outbound_at) {
    pills.push(`<span class="session-pill">Son çıkış: ${escapeHtml(formatRelativeTime(conversation.last_outbound_at))}</span>`);
  }
  if (conversation.human_override) {
    pills.push('<span class="session-pill is-warning">İnsan devri aktif</span>');
  }
  if (delivery) {
    pills.push(`<span class="session-pill">${escapeHtml('Teslimat: ' + delivery.localStatus)}</span>`);
    if (delivery.providerStatus && delivery.providerStatus !== 'unknown') {
      pills.push(`<span class="session-pill">${escapeHtml('Sağlayıcı: ' + delivery.providerStatus)}</span>`);
    }
  }
  if (conversation.last_webhook_at || delivery?.providerStatusUpdatedAt) {
    pills.push(`<span class="session-pill">Son webhook: ${escapeHtml(formatRelativeTime(conversation.last_webhook_at || delivery?.providerStatusUpdatedAt))}</span>`);
  }
  if (state.operationMode) {
    pills.push(`<span class="session-pill">Mod: ${escapeHtml(String(state.operationMode).toUpperCase())}</span>`);
  }
  pills.push(`<span class="session-pill ${sync.tone === 'warning' ? 'is-warning' : ''}">${escapeHtml(sync.label)}</span>`);
  container.innerHTML = pills.join('');
}

function renderContextRail() {
  const container = el('context-body');
  if (!container) return;
  const nextSignature = buildContextRailSignature();
  if (state.renderedContextRailSignature === nextSignature) {
    return;
  }
  state.renderedContextRailSignature = nextSignature;
  document.querySelectorAll('.context-tab').forEach(btn => {
    btn.classList.toggle('is-active', btn.dataset.contextTab === state.contextTab);
  });
  const conversation = state.conversation;
  if (!conversation) {
    container.innerHTML = `
      <div class="context-empty">
        <strong>Bağlam hazır değil</strong>
        <p>Bir konuşma açıldığında misafir, operasyon ve teslimat özeti burada görünecek.</p>
        <div class="empty-hints">
          <span class="empty-hint">G / O / L / A ile sekmeler</span>
          <span class="empty-hint">D ile tanılama</span>
        </div>
      </div>`;
    return;
  }
  const tags = [...new Set([...(conversation.risk_flags || []), conversation.intent || '', conversation.state || ''])].filter(Boolean);
  const delivery = latestDeliverySummary();
  if (state.contextTab === 'guest') {
    container.innerHTML = renderGuestContext(conversation, tags);
    return;
  }
  if (state.contextTab === 'operations') {
    container.innerHTML = `
      <div class="context-card">
        <h3>Operasyon Modu</h3>
        <div class="context-list">
          <div class="context-row"><span>Çalışma modu</span><span>${escapeHtml(String(state.operationMode || '-').toUpperCase())}</span></div>
          <div class="context-row"><span>Niyet</span><span>${escapeHtml(conversation.intent || '-')}</span></div>
          <div class="context-row"><span>Durum</span><span>${escapeHtml(conversation.state || '-')}</span></div>
          <div class="context-row"><span>İnsan devri</span><span>${conversation.human_override ? 'Aktif' : 'Kapalı'}</span></div>
          <div class="context-row"><span>Pencere</span><span>${escapeHtml(formatWindowBadge(conversation).label)}</span></div>
        </div>
      </div>
      <div class="context-card">
        <h3>Risk ve Notlar</h3>
        <div class="context-tag-row">${(conversation.risk_flags || []).length ? conversation.risk_flags.map(flag => `<span class="context-tag">${escapeHtml(flag)}</span>`).join('') : '<span class="context-tag">Risk işareti yok</span>'}</div>
      </div>`;
    return;
  }
  if (state.contextTab === 'audit') {
    const entries = buildAuditEntries();
    container.innerHTML = `
      <div class="context-card">
        <h3>Denetim Geçmişi</h3>
        <div class="audit-timeline">
          ${
            entries.length
              ? entries.map(entry => `
                <div class="audit-item ${entry.tone ? `is-${entry.tone}` : ''}">
                  <div class="audit-item-main">
                    <div class="audit-item-title">${escapeHtml(entry.title)}</div>
                    <div class="audit-item-time">${escapeHtml(entry.timestamp ? fmtTime(entry.timestamp) : '-')}</div>
                  </div>
                  ${entry.detail ? `<div class="audit-item-detail">${escapeHtml(entry.detail)}</div>` : ''}
                </div>
              `).join('')
              : '<div class="context-empty"><strong>Denetim olayı yok</strong><p>Bu konuşma için henüz izlenebilir bir olay kaydı oluşmadı.</p></div>'
          }
        </div>
      </div>`;
    return;
  }
  container.innerHTML = `
    <div class="context-card">
      <h3>Teslimat Durumu</h3>
      <div class="context-list">
        <div class="context-row"><span>Mesaj durumu</span><span>${escapeHtml(delivery?.localStatus || conversation.delivery_state || 'unknown')}</span></div>
        <div class="context-row"><span>Sağlayıcı durumu</span><span>${escapeHtml(delivery?.providerStatus || 'unknown')}</span></div>
        <div class="context-row"><span>WhatsApp mesaj kimliği</span><span>${escapeHtml(delivery?.whatsappMessageId || '-')}</span></div>
        <div class="context-row"><span>Onaylanma zamanı</span><span>${escapeHtml(delivery?.approvedAt ? fmtTime(delivery.approvedAt) : '-')}</span></div>
        <div class="context-row"><span>Gönderim zamanı</span><span>${escapeHtml(delivery?.sentAt ? fmtTime(delivery.sentAt) : '-')}</span></div>
        <div class="context-row"><span>İletim zamanı</span><span>${escapeHtml(delivery?.deliveredAt ? fmtTime(delivery.deliveredAt) : '-')}</span></div>
        <div class="context-row"><span>Okunma zamanı</span><span>${escapeHtml(delivery?.readAt ? fmtTime(delivery.readAt) : '-')}</span></div>
        <div class="context-row"><span>Hata zamanı</span><span>${escapeHtml(delivery?.failedAt ? fmtTime(delivery.failedAt) : '-')}</span></div>
        <div class="context-row"><span>Oturum açma şablonu</span><span>${escapeHtml(delivery?.sessionReopenTemplateSent ? (delivery.sessionReopenTemplateName || 'hello_world') : '-')}</span></div>
        <div class="context-row"><span>Şablon gönderim zamanı</span><span>${escapeHtml(delivery?.sessionReopenTemplateSentAt ? fmtTime(delivery.sessionReopenTemplateSentAt) : '-')}</span></div>
        <div class="context-row"><span>Son webhook</span><span>${escapeHtml((conversation.last_webhook_at || delivery?.providerStatusUpdatedAt) ? fmtTime(conversation.last_webhook_at || delivery?.providerStatusUpdatedAt) : '-')}</span></div>
        <div class="context-row"><span>Panel eşitleme durumu</span><span>${escapeHtml(getSyncSnapshot().label)}</span></div>
      </div>
    </div>
    <div class="context-card">
      <h3>Sağlayıcı Olay Geçmişi</h3>
      <div class="context-list">
        ${
          (delivery?.providerEvents || []).length
            ? delivery.providerEvents.slice().reverse().map(event => `
              <div class="context-row">
                <span>${escapeHtml(String(event.status || '-'))}</span>
                <span>${escapeHtml(event.timestamp ? fmtTime(event.timestamp) : '-')}</span>
              </div>
            `).join('')
            : '<div class="context-row"><span>Olay</span><span>Henüz yok</span></div>'
        }
      </div>
      ${
        delivery?.providerError
          ? `<div class="context-row"><span>Son hata</span><span>${escapeHtml([delivery.providerError.title, delivery.providerError.code].filter(Boolean).join(' · ') || '-')}</span></div>`
          : ''
      }
    </div>
    <div class="context-card">
      <h3>Oturum Durumu</h3>
      <div class="context-list">
        <div class="context-row"><span>Pencere</span><span>${escapeHtml(formatWindowBadge(conversation).label)}</span></div>
        <div class="context-row"><span>Son gelen</span><span>${escapeHtml(formatRelativeTime(conversation.last_inbound_at || conversation.last_message_at))}</span></div>
        <div class="context-row"><span>Son çıkış</span><span>${escapeHtml(formatRelativeTime(conversation.last_outbound_at))}</span></div>
      </div>
    </div>`;
}

function buildAuditEntries() {
  const entries = [];
  state.messages.forEach(message => {
    const internal = message.internal_json || {};
    const createdAt = message.created_at || '';
    if (message.role === 'user') {
      entries.push({
        timestamp: createdAt,
        tone: 'muted',
        title: 'Misafir mesajı alındı',
        detail: truncateReplyPreview(message.content || ''),
      });
    }
    if (message.internal_note || internal.internal_note) {
      entries.push({
        timestamp: internal.created_at || createdAt,
        tone: 'muted',
        title: 'İç not kaydedildi',
        detail: truncateReplyPreview(message.content || ''),
      });
    }
    if (message.role === 'assistant' && (message.send_blocked || message.approval_pending) && !message.rejected) {
      entries.push({
        timestamp: createdAt,
        tone: 'warning',
        title: 'Yapay zekâ taslağı onay bekliyor',
        detail: truncateReplyPreview(message.content || ''),
      });
    }
    if (internal.regenerated_at) {
      entries.push({
        timestamp: internal.regenerated_at,
        tone: 'warning',
        title: 'Yapay zekâ taslağı yeniden oluşturuldu',
        detail: truncateReplyPreview(message.content || ''),
      });
    }
    if (message.rejected || internal.rejected_at) {
      entries.push({
        timestamp: internal.rejected_at || createdAt,
        tone: 'danger',
        title: 'Yapay zekâ taslağı reddedildi',
        detail: truncateReplyPreview(message.content || ''),
      });
    }
    if (internal.approved_at) {
      entries.push({
        timestamp: internal.approved_at,
        tone: 'success',
        title: 'Mesaj onaylandı',
        detail: truncateReplyPreview(message.content || ''),
      });
    }
    if (internal.manual_send) {
      entries.push({
        timestamp: internal.sent_at || createdAt,
        tone: 'success',
        title: 'Yönetici manuel mesaj gönderdi',
        detail: truncateReplyPreview(message.content || ''),
      });
    }
    if (message.session_reopen_template_sent || internal.session_reopen_template_sent) {
      entries.push({
        timestamp: message.session_reopen_template_sent_at || internal.session_reopen_template_sent_at || createdAt,
        tone: 'warning',
        title: 'Oturumu yeniden açma şablonu gönderildi',
        detail: internal.session_reopen_template_name || message.session_reopen_template_name || 'hello_world',
      });
    }
    const providerEvents = Array.isArray(message.provider_events) ? message.provider_events : [];
    providerEvents.forEach(event => {
      entries.push({
        timestamp: event.timestamp || createdAt,
        tone: String(event.status || '') === 'failed' ? 'danger' : String(event.status || '') === 'read' ? 'success' : 'muted',
        title: `Sağlayıcı olayı: ${String(event.status || '-').replaceAll('_', ' ')}`,
        detail: [event.error_title, event.error_code].filter(Boolean).join(' · '),
      });
    });
  });
  return entries.sort((a, b) => String(b.timestamp || '').localeCompare(String(a.timestamp || '')));
}

function renderTemplatePanel(errorMessage = '') {
  const listEl = el('template-list');
  const previewEl = el('template-preview');
  const searchEl = el('template-search');
  const sendBtn = el('template-send-btn');
  if (!listEl || !previewEl) return;
  if (searchEl && searchEl.value !== state.templateSearch) searchEl.value = state.templateSearch;
  if (state.composerMode !== 'template') return;
  const needle = String(state.templateSearch || '').trim().toLowerCase();
  const items = state.templateTemplates.filter(item => {
    if (!needle) return true;
    const haystack = [item.id, item.title, item.intent, item.state, item.language, item.preview, ...(item.fields || [])].join(' ').toLowerCase();
    return haystack.includes(needle);
  });
  if (errorMessage) {
    listEl.innerHTML = `<div class="feedback-muted">${escapeHtml(errorMessage)}</div>`;
    previewEl.innerHTML = '<strong>Önizleme</strong><p>Şablonlar şu anda getirilemedi.</p>';
    if (sendBtn) sendBtn.disabled = true;
    return;
  }
  if (!items.length) {
    const emptyText = conversationRequiresTemplate()
      ? 'Bu konuşma için uygun şablon bulunamadı. Meta şablon kataloğu bağlantısını tamamlamak gerekiyor.'
      : 'Bu filtreyle eşleşen şablon bulunamadı.';
    listEl.innerHTML = `<div class="feedback-muted">${escapeHtml(emptyText)}</div>`;
    previewEl.innerHTML = '<strong>Önizleme</strong><p>Görüntülenecek şablon yok.</p>';
    if (sendBtn) sendBtn.disabled = true;
    return;
  }
  const selected = items.find(item => item.id === state.selectedTemplateId) || items[0];
  if (sendBtn) sendBtn.disabled = !(state.sourceType === 'live_conversation' && state.activeConversationId && selected?.id);
  listEl.innerHTML = items.map(item => `
    <div class="template-card ${item.id === selected.id ? 'is-selected' : ''}" data-template-id="${escapeHtml(item.id)}">
      <div class="template-card-head">
        <div class="template-card-title">${escapeHtml(item.title || item.id)}</div>
        ${item.recommended ? '<span class="template-pill is-recommended">önerilen</span>' : ''}
      </div>
      <div class="template-card-meta">
        <span class="template-pill">${escapeHtml(item.language)}</span>
        <span class="template-pill">${escapeHtml(item.intent || '-')}</span>
        <span class="template-pill">${escapeHtml(item.state || '-')}</span>
      </div>
      <div class="template-card-preview">${escapeHtml(String(item.preview || '').slice(0, 180))}</div>
    </div>
  `).join('');
  previewEl.innerHTML = `
    <strong>${escapeHtml(selected.title || selected.id)}</strong>
    <div>${escapeHtml(selected.preview || selected.body || '-')}</div>
    <small>Alanlar: ${escapeHtml((selected.fields || []).length ? selected.fields.join(', ') : 'değişken yok')} · Kimlik: ${escapeHtml(selected.id)}</small>
  `;
}

function openTemplateDialog() {
  el('template-title').value = '';
  el('template-id').value = '';
  el('template-intent').value = state.conversation?.intent || '';
  el('template-state').value = state.conversation?.state || '';
  el('template-language').value = state.conversation?.language || 'tr';
  el('template-body').value = '';
  el('template-dialog-result').classList.add('hidden');
  el('template-dialog-result').textContent = '';
  el('template-dialog').showModal();
}

async function onTemplateSubmit(event) {
  event.preventDefault();
  const payload = {
    title: el('template-title').value.trim(),
    template_id: el('template-id').value.trim() || null,
    intent: el('template-intent').value.trim(),
    state: el('template-state').value.trim(),
    language: el('template-language').value,
    template: el('template-body').value.trim(),
  };
  const submitBtn = el('template-dialog-form').querySelector('button[type="submit"]');
  submitBtn.disabled = true;
  submitBtn.textContent = 'Kaydediliyor...';
  try {
    const response = await apiFetch('/chat/templates', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload),
    });
    state.selectedTemplateId = response.template?.id || null;
    await loadTemplateCandidates();
    notify('Yeni şablon kaydedildi.', 'success');
    el('template-dialog').close();
  } catch (error) {
    el('template-dialog-result').classList.remove('hidden');
    el('template-dialog-result').textContent = error.message || 'Şablon kaydedilemedi.';
    notify(error.message || 'Şablon kaydedilemedi.', 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Şablonu Kaydet';
  }
}

async function sendSelectedTemplate() {
  if (state.sourceType !== 'live_conversation' || !state.activeConversationId) {
    notify('Şablon gönderimi yalnızca canlı konuşmalarda kullanılabilir.', 'warn');
    return;
  }
  const selected = activeTemplateCandidate();
  if (!selected?.id) {
    notify('Önce bir şablon seçin.', 'warn');
    return;
  }
  await sendLiveConversationMessage('', [], selected.id);
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
    helper.innerHTML = '<strong>Seçim Yardımı</strong>Ana problem türünü seçin; buna göre etiket önerileri hazırlanır.';
    recommendation.textContent = 'Kategori seçildiğinde ilgili etiketler otomatik önerilir.';
    return;
  }

  const tooltip = meta?.tooltip ? ` ${meta.tooltip}` : '';
  helper.innerHTML = `<strong>${escapeHtml(meta?.label || selectedCategory)}</strong>${escapeHtml((meta?.description || '') + tooltip)}`;
  if (!recommendedTags.length) {
    recommendation.textContent = 'Bu kategori için hazır etiket önerisi yok.';
    return;
  }

  const recommendationText = recommendedTags
    .map(tagKey => state.catalog.tags.find(item => item.key === tagKey)?.label || tagKey)
    .join(', ');
  recommendation.textContent = state.manualTagTouched
    ? `Önerilen etiketler: ${recommendationText}. Mevcut manuel seçim korunuyor.`
    : `Önerilen etiketler otomatik uygulandı: ${recommendationText}.`;
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

function adminToken() {
  return state.adminToken || '';
}

let _refreshResolver = null;
let _refreshTimer = null;

function notify(message, tone = 'info') {
  const toast = el('toast');
  if (!toast || !message) return;
  toast.textContent = message;
  toast.className = `toast ${tone} is-visible`;
  window.clearTimeout(notify.timer);
  notify.timer = window.setTimeout(() => {
    toast.className = `toast ${tone}`;
  }, TOAST_TIMEOUT_MS);
}

function finishParentRefresh(success) {
  if (_refreshTimer) {
    window.clearTimeout(_refreshTimer);
    _refreshTimer = null;
  }
  if (_refreshResolver) {
    _refreshResolver(Boolean(success));
    _refreshResolver = null;
  }
  state.refreshPromise = null;
}

function requestParentSessionRefresh() {
  if (window.parent === window) return Promise.resolve(false);
  if (state.refreshPromise) return state.refreshPromise;
  state.refreshPromise = new Promise(resolve => {
    _refreshResolver = resolve;
    _refreshTimer = window.setTimeout(() => finishParentRefresh(false), 4000);
    window.parent.postMessage({type: 'chatlab:auth-required'}, window.location.origin);
  });
  return state.refreshPromise;
}

function ensureAdminSession() {
  // Access control is enforced by backend (cookie or bearer).
  // Do not require a bearer token on page load; cookie-only sessions are valid.
  return true;
}

async function apiFetch(path, options = {}) {
  const headers = {...(options.headers || {})};
  const allowRefresh = options.allowRefresh !== false;
  const method = String(options.method || 'GET').toUpperCase();
  if (!isSafeMethod(method)) {
    const csrfToken = readCookie(CSRF_COOKIE);
    if (csrfToken && !headers['X-CSRF-Token']) {
      headers['X-CSRF-Token'] = csrfToken;
    }
  }
  const token = adminToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  let response;
  try {
    response = await fetch((path.startsWith('/api/') ? path : API + path), {
      ...options,
      headers,
      credentials: 'same-origin',
    });
  } catch (_error) {
    throw new Error('Bağlantı sorunu. Lütfen tekrar deneyin.');
  }
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
    if (response.status === 401 && allowRefresh) {
      const refreshed = await requestParentSessionRefresh();
      if (refreshed) {
        return apiFetch(path, {...options, allowRefresh: false});
      }
    }
    if (response.status === 401) {
      if (window.parent !== window) {
        window.parent.postMessage({type: 'chatlab:auth-required'}, window.location.origin);
      } else {
        window.location.href = ADMIN_ENTRY_PATH;
      }
      throw new Error('Oturum süresi doldu. Lütfen yeniden giriş yapın.');
    }
    if (response.status === 403) {
      throw new Error('Chat Lab erişimi için yönetici yetkisi gerekiyor.');
    }
    throw new Error(extractApiErrorMessage(data, rawText));
  }
  return data || {};
}

// extractApiErrorMessage wraps shared extractErrorDetail
function extractApiErrorMessage(data, rawText) {
  return extractErrorDetail(data, rawText);
}

function formatBytes(size) {
  const value = Number(size || 0);
  if (!Number.isFinite(value) || value <= 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  let idx = 0;
  let current = value;
  while (current >= 1024 && idx < units.length - 1) {
    current /= 1024;
    idx += 1;
  }
  const digits = idx === 0 ? 0 : 1;
  return `${current.toFixed(digits)} ${units[idx]}`;
}

function attachmentKindLabel(kind) {
  if (kind === 'image') return 'Görsel';
  if (kind === 'audio') return 'Ses';
  if (kind === 'document') return 'Belge';
  return 'Dosya';
}

function normalizeAttachments(rawAttachments) {
  if (!Array.isArray(rawAttachments)) return [];
  return rawAttachments
    .filter(item => item && typeof item === 'object')
    .map(item => ({
      asset_id: String(item.asset_id || ''),
      kind: String(item.kind || 'document'),
      mime_type: String(item.mime_type || ''),
      file_name: String(item.file_name || 'dosya'),
      size_bytes: Number(item.size_bytes || 0),
      content_url: String(item.content_url || ''),
    }))
    .filter(item => item.asset_id);
}

function updateComposerControls() {
  const sendDisabled = state.sourceType !== 'live_test_chat' || state.uploadInProgress > 0;
  const sendBtn = el('send-btn');
  const attachBtn = el('attach-btn');
  const voiceBtn = el('voice-btn');
  if (sendBtn) sendBtn.disabled = sendDisabled;
  if (attachBtn) attachBtn.disabled = state.sourceType !== 'live_test_chat' || state.uploadInProgress > 0;
  if (voiceBtn) voiceBtn.disabled = state.sourceType !== 'live_test_chat' || state.uploadInProgress > 0;
}

function renderComposerAttachments() {
  const container = el('composer-attachments');
  if (!container) return;
  if (!state.composerAttachments.length) {
    container.classList.add('hidden');
    container.innerHTML = '';
    updateComposerControls();
    return;
  }

  container.classList.remove('hidden');
  container.innerHTML = state.composerAttachments.map(item => {
    const pct = Math.max(0, Math.min(100, Number(item.progress || 0)));
    const status = item.status === 'uploading'
      ? `Yükleniyor (%${pct})`
      : item.status === 'error'
        ? (item.error || 'Hata')
        : item.status === 'uploaded'
          ? 'Hazır'
          : 'Bekliyor';
    const chipClass = item.status === 'error' ? 'composer-chip error' : 'composer-chip';
    return `
      <div class="${chipClass}">
        <div class="composer-chip-main">
          <div class="composer-chip-name" title="${escapeHtml(item.file_name || 'dosya')}">${escapeHtml(item.file_name || 'dosya')}</div>
          <div class="composer-chip-meta">${escapeHtml(attachmentKindLabel(item.kind))} • ${escapeHtml(formatBytes(item.size_bytes))} • ${escapeHtml(status)}</div>
          <div class="composer-chip-progress">
            <div class="composer-chip-progress-fill" style="width:${pct}%"></div>
          </div>
        </div>
        <button class="composer-chip-remove" type="button" data-remove-attachment="${escapeHtml(item.local_id)}" aria-label="Eki kaldır">&times;</button>
      </div>`;
  }).join('');
  updateComposerControls();
}

async function removeComposerAttachment(localId) {
  const index = state.composerAttachments.findIndex(item => item.local_id === localId);
  if (index < 0) return;
  const item = state.composerAttachments[index];
  state.composerAttachments.splice(index, 1);
  renderComposerAttachments();
  if (item.asset_id && item.status === 'uploaded') {
    try {
      await apiFetch('/chat/upload-asset/' + encodeURIComponent(item.asset_id), {method: 'DELETE'});
    } catch (_error) {
      // Best effort cleanup only.
    }
  }
}

function buildMessageAttachments(message) {
  const direct = normalizeAttachments(message.attachments);
  if (direct.length) return direct;
  const internal = message && message.internal_json && typeof message.internal_json === 'object'
    ? message.internal_json
    : {};
  return normalizeAttachments(internal.attachments);
}

function renderMessageAttachments(message) {
  const attachments = buildMessageAttachments(message);
  if (!attachments.length) return '';
  return '<div class="msg-attachments">' + attachments.map(item => {
    const safeName = escapeHtml(item.file_name || 'dosya');
    const safeLabel = escapeHtml(attachmentKindLabel(item.kind));
    const safeSize = escapeHtml(formatBytes(item.size_bytes));
    const safeUrl = escapeHtml(item.content_url || '');
    if (item.kind === 'image' && safeUrl) {
      return `
        <div class="msg-attachment">
          <img src="${safeUrl}" alt="${safeName}" class="msg-attachment-image" loading="lazy">
          <div class="msg-attachment-meta">
            <span class="msg-attachment-name">${safeName}</span>
            <span class="msg-attachment-kind">${safeLabel} • ${safeSize}</span>
          </div>
        </div>`;
    }
    if (item.kind === 'audio' && safeUrl) {
      return `
        <div class="msg-attachment">
          <audio controls preload="none" class="msg-attachment-audio" src="${safeUrl}"></audio>
          <div class="msg-attachment-meta">
            <span class="msg-attachment-name">${safeName}</span>
            <span class="msg-attachment-kind">${safeLabel} • ${safeSize}</span>
          </div>
        </div>`;
    }
    if (safeUrl) {
      return `
        <a class="msg-attachment" href="${safeUrl}" target="_blank" rel="noopener noreferrer">
          <div class="msg-attachment-meta">
            <span class="msg-attachment-name">${safeName}</span>
            <span class="msg-attachment-kind">${safeLabel} • ${safeSize}</span>
          </div>
        </a>`;
    }
    return `
      <div class="msg-attachment">
        <div class="msg-attachment-meta">
          <span class="msg-attachment-name">${safeName}</span>
          <span class="msg-attachment-kind">${safeLabel} • ${safeSize}</span>
        </div>
      </div>`;
  }).join('') + '</div>';
}

function guessAttachmentKindByMime(mime) {
  const normalized = String(mime || '').toLowerCase();
  if (normalized.startsWith('image/')) return 'image';
  if (normalized.startsWith('audio/')) return 'audio';
  return 'document';
}

async function uploadComposerFile(file) {
  if (!file) return;
  const localId = `asset_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
  const kind = guessAttachmentKindByMime(file.type);
  const item = {
    local_id: localId,
    asset_id: '',
    kind,
    mime_type: file.type || '',
    file_name: file.name || 'dosya',
    size_bytes: Number(file.size || 0),
    content_url: '',
    status: 'uploading',
    progress: 15,
    error: '',
  };
  state.composerAttachments.push(item);
  state.uploadInProgress += 1;
  renderComposerAttachments();

  try {
    const formData = new FormData();
    formData.append('file', file);
    item.progress = 45;
    renderComposerAttachments();
    const data = await apiFetch('/chat/upload-asset', {
      method: 'POST',
      body: formData,
      headers: {},
    });
    const asset = data.asset || {};
    item.asset_id = String(asset.asset_id || '');
    item.kind = String(asset.kind || item.kind);
    item.mime_type = String(asset.mime_type || item.mime_type || '');
    item.file_name = String(asset.file_name || item.file_name);
    item.size_bytes = Number(asset.size_bytes || item.size_bytes || 0);
    item.content_url = String(asset.content_url || '');
    item.status = 'uploaded';
    item.progress = 100;
    item.error = '';
  } catch (error) {
    item.status = 'error';
    item.progress = 100;
    item.error = error.message || 'Yükleme başarısız.';
    notify(item.error, 'error');
  } finally {
    state.uploadInProgress = Math.max(0, state.uploadInProgress - 1);
    renderComposerAttachments();
  }
}

async function handleAttachmentFiles(fileList) {
  const files = Array.from(fileList || []);
  if (!files.length) return;
  for (const file of files) {
    if (state.composerAttachments.length >= 5) {
      notify('Tek mesajda en fazla 5 dosya gönderebilirsiniz.', 'warn');
      break;
    }
    await uploadComposerFile(file);
  }
}

function openAttachmentPicker() {
  if (state.sourceType !== 'live_test_chat') return;
  const input = el('attachment-input');
  if (!input) return;
  input.value = '';
  input.click();
}

async function startVoiceRecording() {
  if (state.isRecordingVoice) return;
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    notify('Tarayıcı ses kaydını desteklemiyor.', 'error');
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({audio: true});
    const recorderOptions = (window.MediaRecorder && MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported('audio/webm'))
      ? {mimeType: 'audio/webm'}
      : undefined;
    const recorder = recorderOptions ? new MediaRecorder(stream, recorderOptions) : new MediaRecorder(stream);
    state.mediaChunks = [];
    state.mediaRecorder = recorder;
    state.isRecordingVoice = true;
    const voiceBtn = el('voice-btn');
    if (voiceBtn) voiceBtn.classList.add('is-recording');

    recorder.addEventListener('dataavailable', event => {
      if (event.data && event.data.size > 0) state.mediaChunks.push(event.data);
    });
    recorder.addEventListener('stop', async () => {
      stream.getTracks().forEach(track => track.stop());
      const blob = new Blob(state.mediaChunks, {type: 'audio/webm'});
      state.mediaChunks = [];
      state.mediaRecorder = null;
      state.isRecordingVoice = false;
      const voiceBtnStop = el('voice-btn');
      if (voiceBtnStop) voiceBtnStop.classList.remove('is-recording');
      if (!blob.size) return;
      const file = new File([blob], `voice_${Date.now()}.webm`, {type: 'audio/webm'});
      await handleAttachmentFiles([file]);
    });
    recorder.start();
    notify('Ses kaydı başladı. Durdurmak için mikrofon simgesine tekrar basın.', 'info');
  } catch (_error) {
    state.isRecordingVoice = false;
    notify('Mikrofon izni olmadan ses kaydı başlatılamaz.', 'error');
  }
}

function stopVoiceRecording() {
  const recorder = state.mediaRecorder;
  if (!recorder || recorder.state === 'inactive') return;
  recorder.stop();
  notify('Ses kaydı durduruldu.', 'success');
}

function toggleVoiceRecording() {
  if (state.sourceType !== 'live_test_chat') return;
  if (state.isRecordingVoice) {
    stopVoiceRecording();
    return;
  }
  startVoiceRecording();
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
  const nextSignature = buildMessagesRenderSignature();
  if (state.renderedMessagesSignature === nextSignature) {
    return;
  }
  state.renderedMessagesSignature = nextSignature;
  container.innerHTML = '';
  if (state.messages.length === 0) {
    const visibleConversations = getVisibleQueueConversations();
    if (state.sourceType === 'live_conversation') {
      container.innerHTML = renderEmptyCard({
        title: 'Bu konuşmada henüz mesaj yok',
        body: 'Misafir veya temsilci mesajı geldiğinde akış burada görünecek. Oturum ve teslimat durumu üst şeritte izlenmeye devam eder.',
        hints: ['R ile yanıt', 'N ile iç not', 'T ile şablon', 'D ile tanılama'],
      });
    } else if (visibleConversations.length) {
      container.innerHTML = renderEmptyCard({
        title: 'Bir konuşma seçin',
        body: 'Soldaki kuyruktan bir konuşma açın veya klavye ile gezin. Aktif akış seçildiğinde mesajlar burada görünecek.',
        actions: [
          {label: 'İlk görünür konuşmayı aç', action: 'open-first-visible-conversation'},
          {label: 'Aramayı odakla', action: 'focus-queue-search'},
        ],
        hints: ['J/K ile gezin', 'Enter ile aç', 'Ctrl/Cmd + K ile ara'],
      });
    } else {
      container.innerHTML = renderEmptyCard({
        title: 'Kuyruk şu an boş',
        body: 'Canlı bir konuşma geldiğinde bu alan mesaj akışı olarak kullanılacak. Filtre veya arama aktifse önce kuyruğu temizleyin.',
        actions: [
          {label: 'Aramayı temizle', action: 'clear-queue-search'},
          {label: 'Filtreleri sıfırla', action: 'reset-queue-filter'},
        ],
        hints: ['Yenile ile kuyruğu güncelle', 'Ctrl/Cmd + K ile ara'],
      });
    }
    renderThreadHeader();
    renderSessionStrip();
    renderContextRail();
    return;
  }

  state.messages.forEach(message => {
    const bubble = document.createElement('div');
    const isInternalNote = Boolean(message.internal_note || message.internal_json?.internal_note);
    const isAIDraft = message.role === 'assistant' && (message.send_blocked || message.approval_pending || message.rejected);
    const bubbleRole = isInternalNote
      ? 'system'
      : message.role === 'user'
        ? 'user'
        : message.role === 'assistant' && !isAIDraft
          ? 'assistant'
          : 'system';
    bubble.className = 'msg msg-' + bubbleRole;
    if (isAIDraft) bubble.classList.add('msg-ai-draft');
    if (isInternalNote) bubble.classList.add('msg-internal-note');
    bubble.dataset.role = message.role;
    bubble.dataset.messageId = message.id || '';
    bubble.dataset.status = message.status || '';
    if (message.status === 'sending') bubble.classList.add('msg-sending');
    if (message.status === 'error') bubble.classList.add('msg-error');

    const roleRow = document.createElement('div');
    roleRow.className = 'msg-role';
    let roleLabel = 'Sistem';
    if (isInternalNote) roleLabel = 'İç Not';
    else if (isAIDraft) roleLabel = 'Yapay zekâ önerisi';
    else if (message.role === 'user') roleLabel = 'Misafir';
    else if (message.role === 'assistant') roleLabel = 'Gönderilen Yanıt';
    roleRow.textContent = roleLabel;
    bubble.appendChild(roleRow);

    const replySnippet = buildReplySnippet(message);
    if (replySnippet) {
      const replyBlock = document.createElement('div');
      replyBlock.className = 'msg-reply';

      const replyLabel = document.createElement('span');
      replyLabel.className = 'msg-reply-label';
      replyLabel.textContent = replySnippet.label;
      replyBlock.appendChild(replyLabel);

      const replyText = document.createElement('div');
      replyText.className = 'msg-reply-text';
      replyText.textContent = replySnippet.text;
      replyBlock.appendChild(replyText);

      bubble.appendChild(replyBlock);
    }

    const body = document.createElement('div');
    body.className = 'msg-body';
    body.innerHTML = formatMessageHtml(message.content || '');
    const attachmentsHtml = renderMessageAttachments(message);
    if (attachmentsHtml) {
      body.innerHTML += attachmentsHtml;
    }
    bubble.appendChild(body);

    const stamp = document.createElement('div');
    stamp.className = 'msg-time';
    stamp.textContent = fmtTime(message.created_at);
    bubble.appendChild(stamp);

    const statusRow = document.createElement('div');
    statusRow.className = 'msg-status-row';
    const localStatus = message.local_status || message.status || '';
    if (localStatus) {
      const pill = document.createElement('span');
      pill.className = 'msg-status-pill';
      if (localStatus.includes('failed') || localStatus === 'error') pill.classList.add('is-danger');
      else if (localStatus.includes('pending')) pill.classList.add('is-warning');
      else if (localStatus === 'accepted' || localStatus === 'delivered') pill.classList.add('is-success');
      pill.textContent = localStatus.replaceAll('_', ' ');
      statusRow.appendChild(pill);
    }
    if (message.provider_status && message.provider_status !== 'unknown' && message.provider_status !== localStatus) {
      const providerPill = document.createElement('span');
      providerPill.className = 'msg-status-pill';
      providerPill.textContent = 'sağlayıcı: ' + String(message.provider_status).replaceAll('_', ' ');
      statusRow.appendChild(providerPill);
    }
    if (message.whatsapp_message_id) {
      const idPill = document.createElement('span');
      idPill.className = 'msg-status-pill';
      idPill.textContent = 'WhatsApp mesaj kimliği var';
      statusRow.appendChild(idPill);
    }
    if (statusRow.children.length > 0) bubble.appendChild(statusRow);

    if (message.status === 'error' && message._retryPayload) {
      const retryBtn = document.createElement('button');
      retryBtn.type = 'button';
      retryBtn.className = 'msg-retry-btn';
      retryBtn.textContent = 'Tekrar Dene';
      retryBtn.setAttribute('aria-label', 'Mesajı tekrar gönder');
      const msgId = message.id;
      retryBtn.addEventListener('click', () => retryMessage(msgId));
      bubble.appendChild(retryBtn);
    }

    if (isAIDraft && message.id) {
      const actions = document.createElement('div');
      actions.className = 'msg-actions';
      if (!message.rejected) {
        actions.innerHTML += `<button class="msg-action" type="button" data-msg-action="approve" data-message-id="${escapeHtml(String(message.id))}">Onayla ve Gönder</button>`;
        actions.innerHTML += `<button class="msg-action" type="button" data-msg-action="reject" data-message-id="${escapeHtml(String(message.id))}">Reddet</button>`;
      }
      actions.innerHTML += `<button class="msg-action" type="button" data-msg-action="regenerate" data-message-id="${escapeHtml(String(message.id))}">Yeniden Oluştur</button>`;
      if (message.rejected) {
        actions.innerHTML += `<button class="msg-action" type="button" data-msg-action="feedback" data-message-id="${escapeHtml(String(message.id))}">Geri Bildirim</button>`;
      }
      bubble.appendChild(actions);
    }

    if (message.role === 'assistant' && message.id && state.sourceType !== 'live_conversation' && !isAIDraft) {
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
    button.setAttribute('aria-label', `Mesaj puani ${item.rating}: ${item.label}`);
    const selected = state.selectedFeedback && state.selectedFeedback.messageId === messageId && state.selectedFeedback.rating === item.rating;
    if ((saved && saved.rating === item.rating) || selected) button.classList.add('is-active');
    button.addEventListener('click', () => selectFeedback(messageId, item.rating));
    buttons.appendChild(button);
  });
  wrapper.appendChild(buttons);

  const status = document.createElement('span');
  status.className = 'feedback-status';
  status.textContent = saved?.status || 'Puan seçin';
  wrapper.appendChild(status);
  return wrapper;
}

function findMessage(messageId) {
  return state.messages.find(message => String(message.id) === String(messageId)) || null;
}

function truncateReplyPreview(text, maxLength = 180) {
  const normalized = String(text || '').replace(/\\s+/g, ' ').trim();
  if (!normalized) return '-';
  if (normalized.length <= maxLength) return normalized;
  return normalized.slice(0, maxLength - 3) + '...';
}

function replyRoleLabel(role) {
  if (role === 'assistant') return 'Yapay zekâ mesajına yanıt';
  if (role === 'user') return 'Misafir mesajına yanıt';
  if (role === 'system') return 'Sistem mesajına yanıt';
  return 'Mesaja yanıt';
}

function buildReplyTargetFromMessage(message) {
  if (!message || !message.id) return null;
  return {
    messageId: String(message.id),
    role: String(message.role || 'assistant'),
    preview: truncateReplyPreview(message.content || ''),
  };
}

function clearReplyTarget() {
  state.replyTarget = null;
  renderReplyPreview();
}

function setReplyTarget(messageId) {
  const message = findMessage(messageId);
  const target = buildReplyTargetFromMessage(message);
  if (!target) return;
  state.replyTarget = target;
  renderReplyPreview();
  el('msg-input').focus();
}

function renderReplyPreview() {
  const wrapper = el('reply-preview');
  const label = el('reply-preview-label');
  const text = el('reply-preview-text');
  if (!wrapper || !label || !text) return;
  if (!state.replyTarget || state.sourceType !== 'live_test_chat') {
    wrapper.classList.add('hidden');
    text.textContent = '';
    return;
  }
  label.textContent = replyRoleLabel(state.replyTarget.role);
  text.textContent = state.replyTarget.preview || '-';
  wrapper.classList.remove('hidden');
}

function buildReplySnippet(message) {
  const internal = message?.internal_json || {};
  const replyContext = internal.reply_context;
  if (!replyContext || !replyContext.present) return null;
  const role = replyContext.target_role || 'assistant';
  const label = replyContext.resolved ? replyRoleLabel(role) : 'Mesaja yanıt';
  const text = replyContext.resolved
    ? truncateReplyPreview(replyContext.target_content || '')
    : 'Hedef mesaj artık çözümlenemiyor.';
  return {label, text};
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
    ? 'Daha sade ve kısa onaylı yanıtı yazın...'
    : 'Doğru bilgiyi veya referans yanıtı yazın...';
  customCategory.classList.toggle('hidden', el('feedback-category').value !== 'ozel_kategori');

  const r = state.selectedFeedback.rating;
  const mark = '<span class="required-mark">*</span>';
  const lblCat = el('lbl-category');
  const lblTags = el('lbl-tags');
  const lblGold = el('lbl-gold');
  if (lblCat) lblCat.innerHTML = 'Hata kategorisi' + (r <= 4 ? mark : '');
  if (lblTags) lblTags.innerHTML = 'Hata etiketleri' + (r <= 3 ? mark : '');
  if (lblGold) lblGold.innerHTML = 'Referans yanıt' + (r <= 4 ? mark : '');

  updateCategoryGuidance();
}

function renderCategoryOptions() {
  const selectedValue = el('feedback-category').value;
  el('feedback-category').innerHTML = '<option value="">Kategori seçin</option>' +
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

function renderImportOptions(items, liveConvs) {
  const select = el('import-select');
  const prev = select.value || state.importFile || '';
  let html = '<option value="">Yeni test</option>';
  if (liveConvs && liveConvs.length) {
    html += '<optgroup label="Aktif Konuşmalar">' + liveConvs.map(c => {
      const label = (c.phone_display || '***') + ' (' + c.msg_count + ' mesaj)';
      return '<option value="conv:' + escapeHtml(c.id) + '">' + escapeHtml(label) + '</option>';
    }).join('') + '</optgroup>';
  }
  if (items && items.length) {
    html += '<optgroup label="İçe Aktarılan Dosyalar">' + items.map(item =>
      '<option value="' + escapeHtml(item.filename) + '">' + escapeHtml(item.label || item.filename) + '</option>'
    ).join('') + '</optgroup>';
  }
  select.innerHTML = html;
  select.value = prev;
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
  el('role-mapping-note').textContent = 'JSON içindeki roller net değil. Eşleştirmeyi tamamlayıp içe aktarmayı onaylayın.';
  fields.innerHTML = (response.participants || []).map(item => `
    <div class="field-stack">
      <label>${escapeHtml(item.label || item.phone)}</label>
      <select class="debug-select role-mapping-select" data-phone="${escapeHtml(item.phone)}" aria-label="${escapeHtml((item.label || item.phone) + ' rol seçimi')}">
        <option value="user" ${item.suggested_role === 'user' ? 'selected' : ''}>Misafir</option>
        <option value="assistant" ${item.suggested_role === 'assistant' ? 'selected' : ''}>Asistan</option>
        <option value="system" ${item.suggested_role === 'system' ? 'selected' : ''}>Sistem</option>
        <option value="other" ${item.suggested_role === 'other' ? 'selected' : ''}>Diğer</option>
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
  normalizeComposerMode();
  const composerEnabled = isLive || state.sourceType === 'live_conversation';
  const messageInput = el('msg-input');
  const sendBtn = el('send-btn');
  const attachBtn = el('attach-btn');
  const voiceBtn = el('voice-btn');
  const exportBtn = el('export-btn');
  const templateTextEnabled = false;
  messageInput.disabled = !composerEnabled || (state.composerMode === 'template' && !templateTextEnabled);
  sendBtn.disabled = !composerEnabled;
  attachBtn.disabled = !composerEnabled || state.composerMode === 'template';
  voiceBtn.disabled = !composerEnabled || state.sourceType !== 'live_test_chat' || state.composerMode !== 'reply';
  exportBtn.disabled = state.sourceType !== 'live_test_chat';
  if (!composerEnabled) {
    clearReplyTarget();
    state.composerAttachments = [];
    if (state.isRecordingVoice) stopVoiceRecording();
  }
  if (state.sourceType === 'live_conversation') {
    messageInput.placeholder = state.composerMode === 'internal_note'
      ? 'Konuşma için ekip içi not yazın...'
      : state.composerMode === 'template'
        ? 'Seçili şablon doğrudan gönderilir.'
        : 'Canlı konuşmaya mesaj yazın...';
    el('source-banner').textContent = 'Canlı kuyruk konuşması açık.';
  } else if (isLive) {
    messageInput.placeholder = state.composerMode === 'internal_note'
      ? 'Test akışı için yerel not yazın...'
      : state.composerMode === 'template'
        ? 'Şablon modu seçili.'
        : 'Mesajınızı yazın...';
    el('source-banner').textContent = 'Canlı test görünümü aktif.';
  } else {
    messageInput.placeholder = 'İçe aktarılan kayıt görünümü salt okunurdur. Yeni mesaj için "Yeni test" seçin.';
    el('source-banner').textContent = 'İçe aktarılan kayıt açık: ' + (state.importFile || '-');
  }
  renderWorkspaceSummary();
  renderComposerModeBar();
  renderComposerHelper();
  renderReplyPreview();
  renderComposerAttachments();
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
    : '<span class="feedback-muted">Risk işareti yok</span>';
  el('d-next').textContent = internal.next_step || '-';
  el('d-full').textContent = JSON.stringify(internal || {}, null, 2);
}

function refreshDebugFromLatestAssistant() {
  const latestAssistant = [...state.messages].reverse().find(message => message.role === 'assistant') || null;
  updateDebug(latestAssistant);
}

async function loadHistory() {
  if (state.sourceType !== 'live_test_chat') return;
  saveComposerDraft();
  state.activeConversationId = null;
  state.templateSearch = '';
  clearReplyTarget();
  const phone = encodeURIComponent(el('phone-input').value.trim() || 'test_user_123');
  try {
    const data = await apiFetch(`/chat/history?phone=${phone}`);
    markSyncSuccess('conversation');
    state.messages = data.messages || [];
    state.conversation = data.conversation ? {
      ...data.conversation,
      phone_display: (el('phone-input')?.value || 'test_user_123').trim() || 'test_user_123',
      window_state: data.window_state,
      window_expires_at: data.window_expires_at,
      window_remaining_seconds: data.window_remaining_seconds,
      last_message_at: state.messages.length ? state.messages[state.messages.length - 1].created_at : null,
    } : null;
    renderMessages();
    renderThreadHeader();
    renderSessionStrip();
    renderContextRail();
    refreshDebugFromLatestAssistant();
    restoreComposerDraft();
    await loadTemplateCandidates();
  } catch (error) {
    markSyncFailure();
    renderSessionStrip();
    renderContextRail();
    notify(error.message || 'Konuşma geçmişi yüklenemedi.', 'error');
  }
}

function updateTypingIndicator() {
  state.inflightMessages.size > 0 ? showTyping() : hideTyping();
}

function sendMessage() {
  if (state.composerMode === 'template') {
    if (state.sourceType !== 'live_conversation' || !state.activeConversationId) {
      notify('Şablon modu yalnızca canlı konuşmalarda kullanılabilir.', 'warn');
      return;
    }
    sendSelectedTemplate();
    return;
  }
  const message = el('msg-input').value.trim();
  const attachments = state.composerAttachments
    .filter(item => item.status === 'uploaded' && item.asset_id)
    .map(item => ({
      asset_id: item.asset_id,
      kind: item.kind,
      mime_type: item.mime_type,
      file_name: item.file_name,
      size_bytes: item.size_bytes,
      content_url: item.content_url,
    }));
  if (!message && attachments.length === 0) return;
  if (state.uploadInProgress > 0) {
    notify('Dosya yüklemesi tamamlanmadan mesaj gönderilemez.', 'warn');
    return;
  }
  saveComposerDraft();
  if (state.composerMode === 'internal_note') {
    if (state.sourceType !== 'live_conversation' || !state.activeConversationId) {
      notify('İç not yalnızca canlı konuşma seçiliyken kaydedilebilir.', 'warn');
      return;
    }
    persistInternalNote(message);
    return;
  }
  if (state.sourceType === 'live_conversation' && state.activeConversationId) {
    sendLiveConversationMessage(message, attachments);
    return;
  }
  if (state.sourceType !== 'live_test_chat') return;
  const replyTarget = state.replyTarget ? {...state.replyTarget} : null;
  const clientMsgId = `cl_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
  const visibleText = message || (attachments.length ? `Ek gönderildi (${attachments.length})` : '');

  const userMsg = {
    id: `user_${Date.now()}`,
    role: 'user',
    content: visibleText,
    attachments: attachments,
    created_at: new Date().toISOString(),
    internal_json: replyTarget ? {
      reply_to_message_id: replyTarget.messageId,
      reply_context: {
        present: true,
        resolved: true,
        reply_to_message_id: replyTarget.messageId,
        target_role: replyTarget.role,
        target_content: replyTarget.preview,
      },
    } : null,
    status: 'sending',
  };
  state.messages.push(userMsg);
  el('msg-input').value = '';
  state.composerAttachments = [];
  clearReplyTarget();
  renderComposerAttachments();
  renderMessages();

  state.inflightMessages.set(clientMsgId, { userMsg });
  updateTypingIndicator();

  _fireSend(clientMsgId, userMsg, message, attachments, replyTarget);
}

async function persistInternalNote(message) {
  const payload = {
    conversation_id: state.activeConversationId,
    note: message,
  };
  const input = el('msg-input');
  const sendBtn = el('send-btn');
  sendBtn.disabled = true;
  try {
    await apiFetch('/chat/note-to-conversation', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload),
    });
    input.value = '';
    clearComposerDraft();
    notify('İç not kaydedildi.', 'success');
    await loadLiveConversation(state.activeConversationId);
  } catch (error) {
    notify(error.message || 'İç not kaydedilemedi.', 'error');
  } finally {
    sendBtn.disabled = false;
  }
}

async function sendLiveConversationMessage(message, attachments, templateId = null) {
  const payload = {
    conversation_id: state.activeConversationId,
    message: message,
    attachments: attachments.map(item => ({asset_id: item.asset_id})),
  };
  if (templateId) payload.template_id = templateId;
  const input = el('msg-input');
  const sendBtn = el('send-btn');
  sendBtn.disabled = true;
  try {
    const data = await apiFetch('/chat/send-to-conversation', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload),
    });
    input.value = '';
    state.composerAttachments = [];
    renderComposerAttachments();
    clearReplyTarget();
    clearComposerDraft();
    if (data?.session_reopen_template_sent) {
      notify(`Meta pencere açma şablonu (${data.session_reopen_template_name || 'hello_world'}) gönderildi, ardından mesaj iletildi.`, 'success');
    } else if (data?.template_title) {
      notify(`Şablon gönderildi: ${data.template_title}`, 'success');
    } else {
      notify('Mesaj canlı konuşmaya gönderildi.', 'success');
    }
    await loadLiveConversation(state.activeConversationId);
    await loadLiveFeed();
  } catch (error) {
    notify(error.message || 'Canlı konuşmaya mesaj gönderilemedi.', 'error');
  } finally {
    sendBtn.disabled = false;
  }
}

async function _fireSend(clientMsgId, userMsg, message, attachments, replyTarget) {
  try {
    const payload = {
      message: message,
      phone: el('phone-input').value.trim() || 'test_user_123',
      client_message_id: clientMsgId,
      reply_to_message_id: replyTarget?.messageId || null,
      attachments: attachments.map(item => ({asset_id: item.asset_id})),
    };
    const data = await apiFetch('/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload),
    });
    userMsg.id = data.user_message_id || userMsg.id;
    userMsg.created_at = data.timestamp;
    userMsg.status = 'delivered';
    if (data.blocked) {
      state.conversation = data.conversation || null;
      clearComposerDraft();
      renderMessages();
      renderThreadHeader();
      renderSessionStrip();
      renderContextRail();
      refreshDebugFromLatestAssistant();
      notify('Bu konuşma insan temsilci devrinde. Yapay zekâ yanıtı durduruldu.', 'warn');
      return;
    }
    state.messages.push(
      {
        id: data.assistant_message_id,
        role: 'assistant',
        content: data.reply,
        created_at: data.timestamp,
        internal_json: data.internal_json,
        model: el('model-select').value || '',
        send_blocked: Boolean(data.internal_json?.send_blocked),
        approval_pending: Boolean(data.internal_json?.approval_pending),
        rejected: Boolean(data.internal_json?.rejected),
        internal_note: false,
        whatsapp_message_id: data.internal_json?.whatsapp_message_id || null,
        local_status: data.internal_json?.approval_pending || data.internal_json?.send_blocked ? 'pending_approval' : 'accepted',
        provider_status: 'unknown',
      },
    );
    state.conversation = data.conversation || null;
    clearComposerDraft();
    renderMessages();
    renderThreadHeader();
    renderSessionStrip();
    renderContextRail();
    updateDebug(state.messages[state.messages.length - 1]);
  } catch (error) {
    userMsg.status = 'error';
    userMsg.errorMessage = error.message || 'Mesaj gönderilemedi.';
    userMsg._retryPayload = { clientMsgId, message, attachments, replyTarget };
    renderMessages();
    renderThreadHeader();
    renderSessionStrip();
    renderContextRail();
    notify(error.message || 'Mesaj gönderilemedi.', 'error');
  } finally {
    state.inflightMessages.delete(clientMsgId);
    updateTypingIndicator();
  }
}

function retryMessage(messageId) {
  const msg = state.messages.find(m => m.id === messageId);
  if (!msg || !msg._retryPayload) return;
  const { clientMsgId, message, attachments, replyTarget } = msg._retryPayload;
  msg.status = 'sending';
  msg.errorMessage = undefined;
  msg._retryPayload = undefined;
  renderMessages();
  state.inflightMessages.set(clientMsgId, { userMsg: msg });
  updateTypingIndicator();
  _fireSend(clientMsgId, msg, message, attachments || [], replyTarget);
}

async function resetConversation() {
  if (state.sourceType !== 'live_test_chat') {
    el('import-select').value = '';
    state.importFile = '';
    state.sourceType = 'live_test_chat';
    state.importMetadata = {};
    state.roleMapping = {};
    state.inflightMessages.clear();
    state.composerAttachments = [];
    updateTypingIndicator();
    clearReplyTarget();
    setComposerMode(true);
    renderRoleMappingPanel(null);
    await loadHistory();
    return;
  }

  const phone = encodeURIComponent(el('phone-input').value.trim() || 'test_user_123');
  try {
    await apiFetch(`/chat/reset?phone=${phone}`, {method: 'POST'});
    state.messages = [];
    state.conversation = null;
    state.templateTemplates = [];
    state.selectedTemplateId = null;
    state.feedbackStates.clear();
    state.selectedFeedback = null;
    state.inflightMessages.clear();
    state.composerAttachments = [];
    updateTypingIndicator();
    clearReplyTarget();
    renderComposerAttachments();
    renderMessages();
    renderThreadHeader();
    renderSessionStrip();
    renderContextRail();
    renderTemplatePanel();
    renderFeedbackStudio();
    updateDebug(null);
    notify('Konuşma sıfırlandı.', 'success');
  } catch (error) {
    notify(error.message || 'Konuşma sıfırlanamadı.', 'error');
  }
}

async function downloadConversation() {
  if (state.sourceType !== 'live_test_chat') return;
  const phone = encodeURIComponent(el('phone-input').value.trim() || 'test_user_123');
  const format = encodeURIComponent(el('save-format').value);
  window.location.href = `${API}/chat/export?phone=${phone}&format=${format}`;
}

async function refreshImportFiles() {
  try {
    const data = await apiFetch('/chat/import-files');
    state.importItems = data.items || [];
    renderImportOptions(state.importItems, state.liveConversations);
  } catch (error) {
    notify(error.message || 'İçe aktarım listesi yüklenemedi.', 'error');
  }
}

async function loadLiveConversation(convId) {
  const conversationId = String(convId || '').trim();
  if (!conversationId) return;
  if (state.liveConversationRequest && state.liveConversationRequestId === conversationId) {
    return state.liveConversationRequest;
  }
  const request = (async () => {
    saveComposerDraft();
    state.sourceType = 'live_conversation';
    state.activeConversationId = conversationId;
    state.templateSearch = '';
    state.importFile = '';
    state.importMetadata = {};
    state.roleMapping = {};
    clearReplyTarget();
    setComposerMode(true);
    renderRoleMappingPanel(null);
    el('source-banner').textContent = 'Canlı konuşma görüntüleniyor.';
    renderWorkspaceSummary();
    try {
      const data = await apiFetch('/chat/conversation/' + encodeURIComponent(conversationId));
      if (String(state.activeConversationId || '') !== conversationId) {
        return;
      }
      markSyncSuccess('conversation');
      state.messages = (data.messages || []).map(m => ({
        id: m.id,
        role: m.role,
        content: m.content,
        created_at: m.created_at,
        internal_json: m.internal_json || null,
        attachments: Array.isArray(m.attachments) ? m.attachments : [],
        model: m.model || null,
        send_blocked: m.send_blocked || false,
        approval_pending: m.approval_pending || false,
        rejected: m.rejected || false,
        internal_note: m.internal_note || false,
        whatsapp_message_id: m.whatsapp_message_id || null,
        local_status: m.local_status || 'unknown',
        provider_status: m.provider_status || 'unknown',
        provider_status_updated_at: m.provider_status_updated_at || null,
        provider_sent_at: m.provider_sent_at || null,
        delivered_at: m.delivered_at || null,
        read_at: m.read_at || null,
        failed_at: m.failed_at || null,
        provider_error: m.provider_error || null,
        provider_events: Array.isArray(m.provider_events) ? m.provider_events : [],
        session_reopen_template_sent: m.session_reopen_template_sent || false,
        session_reopen_template_name: m.session_reopen_template_name || null,
        session_reopen_template_sent_at: m.session_reopen_template_sent_at || null,
      }));
      state.conversation = {
        id: data.id,
        phone_display: data.phone_display || '***',
        language: data.language || '-',
        state: data.state || '-',
        intent: data.intent || '-',
        risk_flags: data.risk_flags || [],
        is_active: Boolean(data.is_active),
        human_override: Boolean(data.human_override),
        last_message_at: data.last_message_at || null,
        last_inbound_at: data.last_inbound_at || null,
        last_outbound_at: data.last_outbound_at || null,
        delivery_state: data.delivery_state || 'unknown',
        last_webhook_at: data.last_webhook_at || null,
        window_state: data.window_state || 'unknown',
        window_expires_at: data.window_expires_at || null,
        window_remaining_seconds: data.window_remaining_seconds || 0,
        guest_info: data.guest_info || null,
      };
      renderMessages();
      renderThreadHeader();
      renderSessionStrip();
      renderContextRail();
      refreshDebugFromLatestAssistant();
      restoreComposerDraft();
      await loadTemplateCandidates();
    } catch (error) {
      if (String(state.activeConversationId || '') !== conversationId) {
        return;
      }
      markSyncFailure();
      renderSessionStrip();
      renderContextRail();
      notify(error.message || 'Konuşma yüklenemedi.', 'error');
    }
  })();
  state.liveConversationRequest = request;
  state.liveConversationRequestId = conversationId;
  try {
    await request;
  } finally {
    if (state.liveConversationRequest === request) {
      state.liveConversationRequest = null;
      state.liveConversationRequestId = '';
    }
  }
}

async function loadSelectedImport(roleMapping = {}) {
  const filename = el('import-select').value;
  if (!filename) {
    state.sourceType = 'live_test_chat';
    state.templateSearch = '';
    state.importFile = '';
    state.importMetadata = {};
    state.roleMapping = {};
    state.activeConversationId = null;
    clearReplyTarget();
    setComposerMode(true);
    renderRoleMappingPanel(null);
    await loadHistory();
    return;
  }

  // Handle active conversation selection
  if (filename.startsWith('conv:')) {
    const convId = filename.slice(5);
    await loadLiveConversation(convId);
    return;
  }

  let data;
  try {
    data = await apiFetch('/chat/import-load', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({filename: filename, role_mapping: roleMapping}),
    });
  } catch (error) {
    notify(error.message || 'İçe aktarma yüklenemedi.', 'error');
    return;
  }
  state.sourceType = data.source_type;
  state.templateSearch = '';
  state.importFile = data.file_name;
  state.importMetadata = {...(data.metadata || {}), conversation_id: data.conversation_id, source_label: data.source_label};
  state.roleMapping = roleMapping;

  if (data.status === 'role_mapping_required') {
    state.messages = [];
    renderMessages();
    renderRoleMappingPanel(data);
    setComposerMode(false);
    renderThreadHeader();
    renderSessionStrip();
    renderContextRail();
    updateDebug(null);
    return;
  }

  renderRoleMappingPanel(null);
  state.messages = data.messages || [];
  state.conversation = {
    id: data.conversation_id || data.file_name,
    phone_display: data.source_label || data.file_name,
    language: data.metadata?.language || '-',
    state: data.metadata?.state || '-',
    intent: data.metadata?.intent || '-',
    risk_flags: data.metadata?.risk_flags || [],
  };
  setComposerMode(false);
  renderMessages();
  renderThreadHeader();
  renderSessionStrip();
  renderContextRail();
  refreshDebugFromLatestAssistant();
  await loadTemplateCandidates();
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

  const rating = state.selectedFeedback.rating;
  const errors = [];
  if (rating <= 4 && !goldStandard) errors.push('Referans yanıt / doğru cevap alanı zorunludur.');
  if (rating <= 4 && !category && !customCategory) errors.push('Kategori seçimi zorunludur.');
  if (rating <= 3 && !tags.length && !customTags.length) errors.push('En az bir etiket seçimi zorunludur.');
  if (errors.length) {
    notify(errors[0], 'error');
    return;
  }

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
      conversation_id: state.activeConversationId || null,
    };
    const data = await apiFetch('/chat/feedback', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload),
    });
    state.feedbackStates.set(state.selectedFeedback.messageId, {
      rating: data.rating,
      status: data.approved_example ? 'Onaylı örnek olarak kaydedildi' : 'Geri bildirim kaydedildi',
    });
    renderMessages();
    el('feedback-result').classList.remove('hidden');
    el('feedback-result').textContent = `Kayıt: ${data.storage_path}`;
    notify('Geri bildirim kaydedildi.', 'success');
    loadMetrics();
  } catch (error) {
    el('feedback-result').classList.remove('hidden');
    el('feedback-result').textContent = error.message || 'Geri bildirim kaydedilemedi.';
    notify(error.message || 'Geri bildirim kaydedilemedi.', 'error');
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
    notify('Rapor oluşturuldu.', 'success');
  } catch (error) {
    el('report-result').textContent = error.message || 'Rapor oluşturulamadı.';
    notify(error.message || 'Rapor oluşturulamadı.', 'error');
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
    notify(error.message || 'Geri bildirim kataloğu alınamadı; varsayılan puanlar kullanılıyor.', 'warn');
  }
  renderCategoryOptions();
  renderTagOptions();
  renderMessages();
  renderFeedbackStudio();
}

async function loadModels() {
  try {
    const data = await apiFetch('/models');
    el('model-select').innerHTML = (data.models || []).map(model => `
      <option value="${escapeHtml(model)}">${escapeHtml(model)}</option>`).join('');
    if (data.current) el('model-select').value = data.current;
  } catch (error) {
    notify(error.message || 'Model listesi yüklenemedi.', 'error');
  }
}

async function changeModel() {
  const model = el('model-select').value;
  try {
    await apiFetch('/model', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({model: model}),
    });
    notify('Model güncellendi.', 'success');
  } catch (error) {
    notify(error.message || 'Model güncellenemedi.', 'error');
  }
}

// isoToLocalInput provided by UI_SHARED_SCRIPT

function toggleWorkspaceDiagnostics(forceOpen = null) {
  const shouldOpen = forceOpen === null
    ? !(state.workspaceFlyoutOpen && state.workspaceFlyoutTab === 'diagnostics')
    : Boolean(forceOpen);
  if (!shouldOpen) {
    closeWorkspaceFlyout();
    return;
  }
  openWorkspaceFlyout('diagnostics');
}

function removeCtxMenu() {
  const prev = document.querySelector('.ctx-menu');
  if (prev) prev.remove();
}

function showCtxMenu(event, text, bubble) {
  event.preventDefault();
  removeCtxMenu();
  const menu = document.createElement('div');
  menu.className = 'ctx-menu';
  menu.setAttribute('role', 'menu');
  const canReply = Boolean(
    bubble &&
    state.sourceType === 'live_test_chat' &&
    bubble.dataset.messageId &&
    bubble.dataset.status !== 'sending' && bubble.dataset.status !== 'error',
  );
  if (canReply) {
    const replyBtn = document.createElement('button');
    replyBtn.type = 'button';
    replyBtn.className = 'ctx-menu-item';
    replyBtn.setAttribute('role', 'menuitem');
    replyBtn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M10 9V5l-7 7 7 7v-4.1c5 0 8.5 1.6 11 5.1-.9-5-4-10-11-11z"/></svg>Yanıtla';
    replyBtn.addEventListener('click', () => {
      setReplyTarget(bubble.dataset.messageId);
      removeCtxMenu();
    });
    menu.appendChild(replyBtn);
  }
  const copyBtn = document.createElement('button');
  copyBtn.type = 'button';
  copyBtn.className = 'ctx-menu-item';
  copyBtn.setAttribute('role', 'menuitem');
  copyBtn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>Kopyala';
  copyBtn.addEventListener('click', () => {
    navigator.clipboard.writeText(text).then(() => notify('Panoya kopyalandı.', 'success')).catch(() => notify('Kopyalanamadı.', 'error'));
    removeCtxMenu();
  });
  menu.appendChild(copyBtn);
  if (bubble) {
    const faqBtn = document.createElement('button');
    faqBtn.type = 'button';
    faqBtn.className = 'ctx-menu-item';
    faqBtn.setAttribute('role', 'menuitem');
    faqBtn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M17 3H7c-1.1 0-2 .9-2 2v16l7-3 7 3V5c0-1.1-.9-2-2-2zm0 15l-5-2.18L7 18V5h10v13z"/></svg>SSS&#39;e Ekle';
    faqBtn.addEventListener('click', () => {
      removeCtxMenu();
      openFaqDialog(bubble);
    });
    menu.appendChild(faqBtn);
  }
  document.body.appendChild(menu);
  const vw = window.innerWidth;
  const vh = window.innerHeight;
  let x = event.clientX;
  let y = event.clientY;
  if (x + menu.offsetWidth > vw) x = vw - menu.offsetWidth - 4;
  if (y + menu.offsetHeight > vh) y = vh - menu.offsetHeight - 4;
  menu.style.left = x + 'px';
  menu.style.top = y + 'px';
}

function extractFaqPair(bubble) {
  const role = bubble.dataset.role;
  const text = (bubble.querySelector('.msg-body') || {}).textContent || '';
  let question = '';
  let answer = '';
  if (role === 'user') {
    question = text;
    let sibling = bubble.nextElementSibling;
    while (sibling) {
      if (sibling.dataset.role === 'assistant') {
        answer = (sibling.querySelector('.msg-body') || {}).textContent || '';
        break;
      }
      sibling = sibling.nextElementSibling;
    }
  } else if (role === 'assistant') {
    answer = text;
    let sibling = bubble.previousElementSibling;
    while (sibling) {
      if (sibling.dataset.role === 'user') {
        question = (sibling.querySelector('.msg-body') || {}).textContent || '';
        break;
      }
      sibling = sibling.previousElementSibling;
    }
  }
  return {question, answer};
}

function openFaqDialog(bubble) {
  const pair = extractFaqPair(bubble);
  el('faq-topic').value = '';
  el('faq-question-tr').value = pair.question;
  el('faq-answer-tr').value = pair.answer;
  el('faq-question-en').value = pair.question;
  el('faq-answer-en').value = pair.answer;
  el('faq-status').value = 'ACTIVE';
  el('faq-dialog-result').classList.add('hidden');
  el('faq-dialog-result').textContent = '';
  el('faq-dialog').showModal();
}

async function onFaqSubmit(event) {
  event.preventDefault();
  if (!state.hotelId) {
    notify('Otel bilgisi eksik. Lütfen yönetim panelinden otel seçin.', 'error');
    return;
  }
  const topic = el('faq-topic').value.trim();
  const questionTr = el('faq-question-tr').value.trim();
  const answerTr = el('faq-answer-tr').value.trim();
  const questionEn = el('faq-question-en').value.trim();
  const answerEn = el('faq-answer-en').value.trim();
  const status = el('faq-status').value;
  if (!topic) { notify('Konu alani zorunludur.', 'warn'); return; }
  if (!answerTr) { notify('Cevap (TR) alani zorunludur.', 'warn'); return; }
  if (!answerEn) { notify('Cevap (EN) alani zorunludur.', 'warn'); return; }
  const submitBtn = el('faq-dialog-form').querySelector('button[type="submit"]');
  submitBtn.disabled = true;
  submitBtn.textContent = 'Kaydediliyor...';
  try {
    const payload = {topic, question_tr: questionTr, answer_tr: answerTr, question_en: questionEn, answer_en: answerEn, status};
    await apiFetch('/api/v1/admin/hotels/' + encodeURIComponent(state.hotelId) + '/faq', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)});
    notify('SSS kaydı oluşturuldu.', 'success');
    el('faq-dialog').close();
    if (window.parent !== window) {
      try { window.parent.postMessage({type: 'chatlab:faq-created'}, window.location.origin); } catch(_e) {}
    }
  } catch (error) {
    notify(error.message || 'SSS kaydı oluşturulamadı.', 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'SSS Kaydet';
  }
}

async function loadMode() {
  try {
    const data = await apiFetch('/chat/mode');
    updateModeUI(data.mode);
  } catch (error) {
    notify('Mod bilgisi alınamadı.', 'error');
  }
}

function updateModeUI(mode) {
  state.operationMode = mode;
  document.querySelectorAll('.mode-btn').forEach(btn => {
    btn.classList.toggle('is-active-mode', btn.dataset.mode === mode);
  });
  renderWorkspaceSummary();
}

async function changeMode(newMode) {
  if (newMode === 'ai') {
    if (!confirm('Otomatik moda geçmek gerçek misafirlere mesaj gönderimini etkinleştirir. Emin misiniz?')) return;
  }
  try {
    const data = await apiFetch('/chat/mode', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({mode: newMode}),
    });
    updateModeUI(data.mode);
    const modeLabels = {test: 'Test', ai: 'Otomatik', approval: 'Onay', off: 'Kapalı'};
    notify('Mod değiştirildi: ' + (modeLabels[data.mode] || String(data.mode || '').toUpperCase()), 'success');
  } catch (error) {
    notify(error.message || 'Mod değiştirilemedi.', 'error');
  }
}

// ── Conversation Detail Modal ──────────────────────────────────
let _modalRefreshTimer = null;
function openConvModal() {
  el('conv-detail-overlay').classList.remove('hidden');
  _startModalAutoRefresh();
}
function closeConvModal() {
  el('conv-detail-overlay').classList.add('hidden');
  _modalConvId = null;
  _stopModalAutoRefresh();
}
function _startModalAutoRefresh() {
  _stopModalAutoRefresh();
  _modalRefreshTimer = setInterval(() => {
    if (_modalConvId) _silentRefreshModal(_modalConvId);
  }, 3000);
}
function _stopModalAutoRefresh() {
  if (_modalRefreshTimer) { clearInterval(_modalRefreshTimer); _modalRefreshTimer = null; }
}
async function _silentRefreshModal(convId) {
  // Skip refresh if feedback form is open or user is typing
  if (!el('conv-modal-feedback').classList.contains('hidden')) return;
  const input = document.getElementById('conv-modal-msg-input');
  if (input && input.value.trim()) return;
  try {
    const data = await apiFetch('/chat/conversation/' + encodeURIComponent(convId));
    if (_modalConvId === convId) renderConvModal(data);
  } catch (_) { /* silent fail — next tick will retry */ }
}

async function showConversationDetail(convId) {
  _modalConvId = convId;
  openConvModal();
  el('conv-modal-meta').innerHTML = '<span class="feedback-muted">Yükleniyor...</span>';
  el('conv-modal-messages').innerHTML = '';
  el('conv-modal-json').classList.add('hidden');
  el('conv-modal-json').innerHTML = '';
  el('conv-modal-feedback').classList.add('hidden');
  el('conv-modal-actions').innerHTML = '';
  document.getElementById('conv-modal-msg-input').value = '';
  try {
    const data = await apiFetch('/chat/conversation/' + encodeURIComponent(convId));
    renderConvModal(data);
  } catch (error) {
    el('conv-modal-meta').innerHTML = '<span class="feedback-muted">Hata: ' + escapeHtml(error.message || '') + '</span>';
  }
}

function renderConvModal(data) {
  // Meta badges
  const metaItems = [
    {label: data.phone_display, highlight: true},
    {label: 'Dil: ' + data.language},
    {label: 'Durum: ' + data.state},
    {label: 'Niyet: ' + data.intent},
    {label: data.is_active ? 'Aktif' : 'Kapalı', highlight: data.is_active},
  ];
  if (data.hotel_id) metaItems.push({label: 'Otel: ' + data.hotel_id});
  const flags = data.risk_flags || [];
  flags.forEach(f => metaItems.push({label: 'Risk: ' + f}));
  el('conv-modal-meta').innerHTML = metaItems.map(m =>
    '<span class="conv-modal-meta-item' + (m.highlight ? ' highlight' : '') + '">' + escapeHtml(m.label) + '</span>'
  ).join('');

  // Messages
  const msgs = data.messages || [];
  let lastAssistantMsg = null;
  const msgHtml = msgs.map(m => {
    const roleClass = m.role === 'user' ? 'conv-msg-user' : m.role === 'assistant' ? 'conv-msg-assistant' : 'conv-msg-system';
    const roleName = m.role === 'user' ? 'Misafir' : m.role === 'assistant' ? 'Yapay zekâ önerisi' : 'Sistem';
    const timeStr = m.created_at ? formatTime(m.created_at) : '';
    let statusHtml = '';
    if (m.role === 'assistant') {
      lastAssistantMsg = m;
      const hasInternalFlags = m.internal_json && Object.keys(m.internal_json).length > 0;
      if (m.rejected) {
        statusHtml = '<span class="conv-msg-status rejected">REDDEDİLDİ</span>';
      } else if (m.send_blocked) {
        statusHtml = '<span class="conv-msg-status pending">BEKLİYOR</span>';
      } else if (!hasInternalFlags && state.operationMode !== 'ai') {
        // No flags recorded — treat as pending in non-ai modes (legacy data safety)
        statusHtml = '<span class="conv-msg-status pending">BEKLİYOR</span>';
        m.send_blocked = true;
      } else {
        statusHtml = '<span class="conv-msg-status sent">GÖNDERİLDİ</span>';
      }
    }
    return '<div class="conv-msg ' + roleClass + '">' +
      '<div class="conv-msg-role">' + roleName + statusHtml + '</div>' +
      '<div class="conv-msg-body">' + escapeHtml(m.content) + '</div>' +
      '<div class="conv-msg-time">' + escapeHtml(timeStr) + '</div>' +
    '</div>';
  }).join('');
  el('conv-modal-messages').innerHTML = msgHtml || '<div class="feedback-muted">Mesaj bulunamadı.</div>';

  // JSON toggle content (last assistant internal_json)
  if (lastAssistantMsg && lastAssistantMsg.internal_json) {
    el('conv-modal-json').innerHTML = '<pre>' + escapeHtml(JSON.stringify(lastAssistantMsg.internal_json, null, 2)) + '</pre>';
  } else {
    el('conv-modal-json').innerHTML = '<pre>{}</pre>';
  }

  // Action buttons
  let actionsHtml = '';
  if (lastAssistantMsg) {
    if (!lastAssistantMsg.rejected && lastAssistantMsg.send_blocked) {
      actionsHtml += '<button class="btn btn-primary" id="conv-modal-approve" data-conv="' + escapeHtml(data.id) + '" data-msg="' + escapeHtml(lastAssistantMsg.id) + '">Onayla ve Gönder</button>';
      actionsHtml += '<button class="btn btn-reset" id="conv-modal-reject" data-conv="' + escapeHtml(data.id) + '" data-msg="' + escapeHtml(lastAssistantMsg.id) + '">Reddet</button>';
    }
    // Henüz gönderilmemiş mesajlar için yeniden oluşturma aksiyonunu göster.
    if (lastAssistantMsg.send_blocked || lastAssistantMsg.rejected) {
      actionsHtml += '<button class="btn btn-save" id="conv-modal-regenerate" data-conv="' + escapeHtml(data.id) + '">Yeniden Oluştur</button>';
    }
    // Show feedback button for rejected messages that were closed without feedback
    if (lastAssistantMsg.rejected) {
      actionsHtml += '<button class="btn btn-reset" id="conv-modal-show-feedback" data-conv="' + escapeHtml(data.id) + '" data-msg="' + escapeHtml(lastAssistantMsg.id) + '">Geri Bildirim Ver</button>';
    }
  }
  actionsHtml += '<button class="btn btn-ghost" id="conv-modal-close-bottom">Kapat</button>';
  el('conv-modal-actions').innerHTML = actionsHtml;

  // Wire modal action buttons
  const approveBtn = document.getElementById('conv-modal-approve');
  if (approveBtn) {
    approveBtn.addEventListener('click', async () => {
      approveBtn.disabled = true;
      approveBtn.textContent = 'Gönderiliyor...';
      try {
        await apiFetch('/chat/approve-message', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({conversation_id: approveBtn.dataset.conv, message_id: approveBtn.dataset.msg})});
        notify('Mesaj onaylandı ve gönderildi.', 'success');
        loadLiveFeed();
        showConversationDetail(approveBtn.dataset.conv);
      } catch (err) {
        notify(err.message || 'Onay gönderilemedi.', 'error');
        approveBtn.disabled = false;
        approveBtn.textContent = 'Onayla ve Gönder';
      }
    });
  }
  const rejectBtn = document.getElementById('conv-modal-reject');
  if (rejectBtn) {
    rejectBtn.addEventListener('click', async () => {
      if (!confirm('Bu mesajı reddetmek istediğinize emin misiniz?')) return;
      rejectBtn.disabled = true;
      rejectBtn.textContent = 'Reddediliyor...';
      try {
        await apiFetch('/chat/reject-message', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({conversation_id: rejectBtn.dataset.conv, message_id: rejectBtn.dataset.msg})});
        notify('Mesaj reddedildi.', 'success');
        loadLiveFeed();
        // Show inline negative feedback form
        showModalFeedbackForm(rejectBtn.dataset.conv, rejectBtn.dataset.msg);
        rejectBtn.disabled = true;
        rejectBtn.textContent = 'Reddedildi';
        if (approveBtn) approveBtn.remove();
      } catch (err) {
        notify(err.message || 'Reddetme başarısız.', 'error');
        rejectBtn.disabled = false;
        rejectBtn.textContent = 'Reddet';
      }
    });
  }
  // Regenerate button
  const regenBtn = document.getElementById('conv-modal-regenerate');
  if (regenBtn) {
    regenBtn.addEventListener('click', async () => {
      if (!confirm('Yapay zekâ mesajı yeniden oluşturulacak. Önceki öneri silinecek. Emin misiniz?')) return;
      regenBtn.disabled = true;
      regenBtn.textContent = 'Oluşturuluyor...';
      try {
        await apiFetch('/chat/regenerate', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({conversation_id: regenBtn.dataset.conv})});
        notify('Mesaj yeniden oluşturuldu.', 'success');
        loadLiveFeed();
        showConversationDetail(regenBtn.dataset.conv);
      } catch (err) {
        notify(err.message || 'Yeniden oluşturma başarısız.', 'error');
        regenBtn.disabled = false;
        regenBtn.textContent = 'Yeniden Oluştur';
      }
    });
  }
  // Show feedback for already-rejected messages
  const showFbBtn = document.getElementById('conv-modal-show-feedback');
  if (showFbBtn) {
    showFbBtn.addEventListener('click', () => {
      showModalFeedbackForm(showFbBtn.dataset.conv, showFbBtn.dataset.msg);
    });
  }
  const closeBottom = document.getElementById('conv-modal-close-bottom');
  if (closeBottom) closeBottom.addEventListener('click', closeConvModal);
}

function showModalFeedbackForm(convId, msgId) {
  const fbPanel = el('conv-modal-feedback');
  fbPanel.classList.remove('hidden');
  // Populate categories
  const catSelect = document.getElementById('conv-fb-category');
  const cats = state.feedbackCategories || DEFAULT_FEEDBACK_CATEGORIES;
  catSelect.innerHTML = '<option value="">Kategori seçin...</option>' +
    cats.map(c => '<option value="' + escapeHtml(c.key) + '">' + escapeHtml(c.label) + '</option>').join('');
  document.getElementById('conv-fb-gold').value = '';
  document.getElementById('conv-fb-notes').value = '';
  document.getElementById('conv-fb-result').textContent = '';

  const submitBtn = document.getElementById('conv-fb-submit');
  // Remove old listeners by replacing node
  const freshBtn = submitBtn.cloneNode(true);
  submitBtn.parentNode.replaceChild(freshBtn, submitBtn);
  freshBtn.addEventListener('click', async () => {
    const category = catSelect.value;
    const gold = document.getElementById('conv-fb-gold').value.trim();
    const notes = document.getElementById('conv-fb-notes').value.trim();
    if (!category) { notify('Kategori seçin.', 'warn'); return; }
    if (!gold) { notify('Doğru yanıt alanını doldurun.', 'warn'); return; }
    freshBtn.disabled = true;
    freshBtn.textContent = 'Kaydediliyor...';
    try {
      await apiFetch('/chat/feedback', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          source_type: 'live_conversation',
          phone: 'admin_reject',
          assistant_message_id: msgId,
          rating: 1,
          category: category,
          tags: ['reddedilen_mesaj'],
          custom_tags: [],
          gold_standard: gold,
          notes: notes || null,
          approved_example: false,
          conversation_id: convId || null,
        }),
      });
      document.getElementById('conv-fb-result').textContent = 'Geri bildirim kaydedildi.';
      document.getElementById('conv-fb-result').style.color = '#86efac';
      notify('Olumsuz geri bildirim kaydedildi.', 'success');
      freshBtn.textContent = 'Kaydedildi';
    } catch (err) {
      document.getElementById('conv-fb-result').textContent = 'Hata: ' + (err.message || '');
      document.getElementById('conv-fb-result').style.color = '#fca5a5';
      freshBtn.disabled = false;
      freshBtn.textContent = 'Geri Bildirimi Kaydet';
    }
  });

  // Scroll feedback form into view
  fbPanel.scrollIntoView({behavior: 'smooth', block: 'nearest'});
}

// Track current modal conversation ID for send
let _modalConvId = null;

async function sendModalMessage() {
  const input = document.getElementById('conv-modal-msg-input');
  const text = (input.value || '').trim();
  if (!text || !_modalConvId) return;
  const btn = document.getElementById('conv-modal-send-btn');
  btn.disabled = true;
  btn.textContent = 'Gönderiliyor...';
  input.disabled = true;
  try {
    await apiFetch('/chat/send-to-conversation', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({conversation_id: _modalConvId, message: text}),
    });
    input.value = '';
    notify('Mesaj gönderildi.', 'success');
    loadLiveFeed();
    showConversationDetail(_modalConvId);
  } catch (err) {
    notify(err.message || 'Mesaj gönderilemedi.', 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Gönder';
    input.disabled = false;
    input.focus();
  }
}

async function loadLiveFeed() {
  const container = el('live-feed-container');
  const includeInactiveToggle = el('include-inactive-toggle');
  const includeInactive = includeInactiveToggle?.checked ? true : false;
  const query = includeInactive ? '&include_inactive=true' : '';
  try {
    const data = await apiFetch('/chat/live-feed?limit=15' + query);
    markSyncSuccess('panel');
    state.liveConversations = data.conversations || [];
    renderLiveFeed(container, data);
    renderImportOptions(state.importItems, state.liveConversations);
    renderSessionStrip();
    renderContextRail();
  } catch (error) {
    markSyncFailure();
    renderSessionStrip();
    renderContextRail();
    container.innerHTML = '<div class="feedback-muted">Canlı akış yüklenemedi: ' + escapeHtml(error.message || '') + '</div>';
  }
}

function renderLiveFeed(container, data) {
  const rawConvs = data.conversations || [];
  const convs = getVisibleQueueConversations(rawConvs);
  renderQueueSummary(rawConvs, convs);
  if (!convs.length) {
    const activeFiltered = activeQueueConversationFiltered(rawConvs, convs);
    const searchActive = Boolean(String(state.queueSearch || '').trim());
    const filterActive = state.queueFilter !== 'all';
    let title = 'Bu filtreyle eşleşen konuşma yok';
    let body = 'Filtre veya arama sonucunda görünen kuyruk şu an boş.';
    if (!rawConvs.length) {
      title = 'Canlı kuyrukta henüz konuşma yok';
      body = 'Yeni mesajlar geldiğinde konuşmalar burada listelenecek.';
    } else if (activeFiltered) {
      body += ' Aktif konuşma filtre dışında kalıyor.';
    }
    const actions = [];
    if (searchActive) actions.push({label: 'Aramayı temizle', action: 'clear-queue-search'});
    if (filterActive) actions.push({label: 'Filtreleri sıfırla', action: 'reset-queue-filter'});
    actions.push({label: 'Yenile', action: 'refresh-queue'});
    container.innerHTML = renderEmptyCard({
      title,
      body,
      actions,
      hints: ['Ctrl/Cmd + K ile ara', 'J/K ile gezin'],
    });
    return;
  }

  container.innerHTML = convs.map(c => {
    const timeStr = c.last_message_at ? formatTime(c.last_message_at) : '-';
    const userSnippet = c.last_user_msg ? escapeHtml(c.last_user_msg.slice(0, 300)) : '-';
    const assistantSnippet = c.last_assistant_msg ? escapeHtml(c.last_assistant_msg.slice(0, 300)) : '-';
    const blocked = c.send_blocked === 'true' || c.send_blocked === true || c.approval_pending === 'true' || c.approval_pending === true;
    const rejected = c.rejected === 'true' || c.rejected === true;
    const human = queueHumanOverrideActive(c);
    const attention = queueNeedsAttention(c);
    const draftLabel = queueDraftLabel(c.id);
    const hasDraft = Boolean(draftLabel);
    const reopenLabel = queueSessionReopenLabel(c);
    let statusTag;
    if (rejected) {
      statusTag = '<span class="live-feed-rejected">REDDEDİLDİ</span>';
    } else if (blocked && c.last_assistant_msg_id) {
      statusTag = '<span class="live-feed-blocked">BEKLİYOR</span> ' +
        '<button class="live-feed-approve-btn" data-approve-conv="' + escapeHtml(c.id) + '" data-approve-msg="' + escapeHtml(String(c.last_assistant_msg_id)) + '">Onayla</button>' +
        ' <button class="live-feed-reject-btn" data-reject-conv="' + escapeHtml(c.id) + '" data-reject-msg="' + escapeHtml(String(c.last_assistant_msg_id)) + '">Reddet</button>';
    } else if (blocked) {
      statusTag = '<span class="live-feed-blocked">BEKLİYOR</span>';
    } else if (String(c.delivery_state || '') === 'failed') {
      statusTag = '<span class="live-feed-rejected">HATA</span>';
    } else {
      statusTag = '<span class="live-feed-sent">' + escapeHtml(String(c.delivery_state || 'accepted').replaceAll('_', ' ').toUpperCase()) + '</span>';
    }

    const flags = (c.risk_flags || []).map(f => '<span class="live-feed-badge">' + escapeHtml(f) + '</span>').join('');

    const windowBadge = c.window_state === 'closed'
      ? queueBadgeHtml('pencere kapalı', 'danger')
      : c.window_state === 'closing_soon'
        ? queueBadgeHtml('pencere kapanıyor', 'warning')
        : queueBadgeHtml('pencere açık', 'success');
    const deliveryBadge = c.delivery_state ? queueBadgeHtml(String(c.delivery_state).replaceAll('_', ' '), queueDeliveryTone(c.delivery_state)) : '';
    const providerBadge = c.provider_status && c.provider_status !== 'unknown'
      ? queueBadgeHtml('sağlayıcı ' + String(c.provider_status).replaceAll('_', ' '), queueDeliveryTone(c.provider_status))
      : '';
    const webhookBadge = c.provider_status_updated_at ? queueBadgeHtml('webhook ' + formatRelativeTime(c.provider_status_updated_at), 'info') : '';
    const draftBadge = draftLabel ? queueBadgeHtml(draftLabel, 'accent') : '';
    const handoffBadge = human ? queueBadgeHtml('insan devri', 'handoff') : '';
    const reopenBadge = reopenLabel ? queueBadgeHtml('yeniden açma ' + reopenLabel, 'info') : '';
    let priorityBadge = '';
    if (attention) {
      priorityBadge = '<span class="live-feed-priority is-attention">Dikkat Gerektiriyor</span>';
    } else if (human) {
      priorityBadge = '<span class="live-feed-priority is-human">Temsilci</span>';
    } else if (hasDraft) {
      priorityBadge = '<span class="live-feed-priority is-draft">Taslak</span>';
    }
    const cardClasses = ['live-feed-card'];
    if (state.activeConversationId === c.id) cardClasses.push('is-active');
    if (attention) cardClasses.push('is-attention');
    if (human) cardClasses.push('is-human');
    if (hasDraft) cardClasses.push('has-draft');

    return '<div class="' + cardClasses.join(' ') + '" draggable="true" tabindex="0" aria-label="' + escapeHtml(`${c.phone_display || 'Konuşma'} kuyruk kartı`) + '" data-conv-id="' + escapeHtml(c.id) + '">' +
      '<div class="live-feed-head">' +
        '<div class="live-feed-title-stack">' +
          '<span class="live-feed-phone">' + escapeHtml(c.phone_display) + '</span>' +
          '<span class="live-feed-subline">' + escapeHtml(c.msg_count + ' mesaj') + '</span>' +
        '</div>' +
        '<div class="live-feed-head-meta">' + priorityBadge + '<span class="live-feed-time">' + timeStr + '</span></div>' +
      '</div>' +
      '<div class="live-feed-preview">' +
        '<div class="live-feed-preview-block">' +
          '<span class="live-feed-preview-label">Misafir</span>' +
          '<div class="live-feed-user">' + userSnippet + '</div>' +
        '</div>' +
        '<div class="live-feed-preview-block">' +
          '<span class="live-feed-preview-label">Son çıkış</span>' +
          '<div class="live-feed-assistant">' + assistantSnippet + '</div>' +
        '</div>' +
      '</div>' +
      '<div class="live-feed-status-row">' + statusTag + '</div>' +
      '<div class="live-feed-badges">' +
        '<span class="live-feed-badge">' + escapeHtml(c.language || '-') + '</span>' +
        '<span class="live-feed-badge">' + escapeHtml(c.state || '-') + '</span>' +
        (c.intent && c.intent !== '-' ? '<span class="live-feed-badge">' + escapeHtml(c.intent) + '</span>' : '') +
        (c.is_active ? '<span class="live-feed-badge live-feed-badge-active">aktif</span>' : '<span class="live-feed-badge live-feed-badge-inactive">kapalı</span>') +
        handoffBadge +
        draftBadge +
        reopenBadge +
        windowBadge +
        deliveryBadge +
        providerBadge +
        webhookBadge +
        flags +
      '</div>' +
    '</div>';
  }).join('');
}

async function loadMetrics() {
  const container = el('metrics-container');
  try {
    const data = await apiFetch('/chat/metrics');
    renderMetrics(container, data);
  } catch (error) {
    container.innerHTML = '<div class="feedback-muted">Metrik yüklenemedi: ' + escapeHtml(error.message || 'Bilinmeyen hata') + '</div>';
  }
}

function renderMetrics(container, m) {
  if (!m || m.total_feedbacks === 0) {
    container.innerHTML = '<div class="feedback-muted">Henüz geri bildirim kaydedilmemiş.</div>';
    return;
  }
  const pct = (n) => m.total_feedbacks ? Math.round(n / m.total_feedbacks * 100) : 0;
  const barColors = {'1':'#ef4444','2':'#f97316','3':'#eab308','4':'#22d3ee','5':'#22c55e'};

  let ratingBars = '';
  for (let r = 5; r >= 1; r--) {
    const count = (m.rating_distribution || {})[String(r)] || 0;
    const w = pct(count);
    const color = barColors[r] || '#888';
    ratingBars += '<div class="metric-bar-row">' +
      '<span class="metric-bar-label">' + r + ' Puan</span>' +
      '<div class="metric-bar-track"><div class="metric-bar-fill" style="width:' + w + '%;background:' + color + '"></div></div>' +
      '<span class="metric-bar-count">' + count + '</span></div>';
  }

  let catBars = '';
  const cats = Object.entries(m.category_distribution || {}).sort((a, b) => b[1] - a[1]).slice(0, 5);
  cats.forEach(([key, count]) => {
    const w = pct(count);
    catBars += '<div class="metric-bar-row">' +
      '<span class="metric-bar-label">' + escapeHtml(key) + '</span>' +
      '<div class="metric-bar-track"><div class="metric-bar-fill" style="width:' + w + '%;background:var(--amber)"></div></div>' +
      '<span class="metric-bar-count">' + count + '</span></div>';
  });

  let langBars = '';
  const langs = Object.entries(m.language_distribution || {}).sort((a, b) => b[1] - a[1]);
  langs.forEach(([key, count]) => {
    const w = pct(count);
    langBars += '<div class="metric-bar-row">' +
      '<span class="metric-bar-label">' + escapeHtml(key.toUpperCase()) + '</span>' +
      '<div class="metric-bar-track"><div class="metric-bar-fill" style="width:' + w + '%;background:var(--teal-2)"></div></div>' +
      '<span class="metric-bar-count">' + count + '</span></div>';
  });

  container.innerHTML =
    '<div class="metrics-grid">' +
      '<div class="metric-card"><div class="metric-value">' + m.total_feedbacks + '</div><div class="metric-label">Toplam Geri Bildirim</div></div>' +
      '<div class="metric-card"><div class="metric-value">' + (m.avg_rating || 0).toFixed(1) + '</div><div class="metric-label">Ortalama Puan</div></div>' +
      '<div class="metric-card"><div class="metric-value">' + (m.good_count || 0) + '</div><div class="metric-label">İyi (4-5)</div></div>' +
      '<div class="metric-card"><div class="metric-value">' + (m.bad_count || 0) + '</div><div class="metric-label">Kötü (1-3)</div></div>' +
    '</div>' +
    '<div class="metric-bar-group"><strong class="metric-bar-title">Puan Dağılımı</strong>' + ratingBars + '</div>' +
    (catBars ? '<div class="metric-bar-group mt-sm"><strong class="metric-bar-title">Kategori Dağılımı (İlk 5)</strong>' + catBars + '</div>' : '') +
    (langBars ? '<div class="metric-bar-group mt-sm"><strong class="metric-bar-title">Dil Dağılımı</strong>' + langBars + '</div>' : '');
}

function wireEvents() {
  if (_eventsBound) return;
  _eventsBound = true;
  document.addEventListener('click', removeCtxMenu);
  el('faq-dialog-close').addEventListener('click', () => el('faq-dialog').close());
  el('template-dialog-close').addEventListener('click', () => el('template-dialog').close());
  el('shortcut-dialog-close').addEventListener('click', () => toggleShortcutDialog(false));
  el('shortcut-help-btn').addEventListener('click', () => toggleShortcutDialog(true));
  el('workspace-panel-toggle').addEventListener('click', () => toggleWorkspaceFlyout('settings'));
  el('workspace-flyout-close').addEventListener('click', closeWorkspaceFlyout);
  el('workspace-scrim').addEventListener('click', closeWorkspaceFlyout);
  el('workspace-flyout').addEventListener('keydown', event => {
    handleWorkspaceFlyoutTabKeydown(event);
    trapWorkspaceFlyoutFocus(event);
  });
  el('workspace-flyout-tabs').addEventListener('click', event => {
    const btn = event.target.closest('[data-workspace-tab]');
    if (!btn) return;
    setWorkspaceFlyoutTab(btn.dataset.workspaceTab || 'settings');
  });
  el('faq-dialog-form').addEventListener('submit', onFaqSubmit);
  el('template-dialog-form').addEventListener('submit', onTemplateSubmit);
  el('template-create-btn').addEventListener('click', openTemplateDialog);
  el('template-send-btn').addEventListener('click', sendSelectedTemplate);
  el('messages').addEventListener('contextmenu', event => {
    const bubble = event.target.closest('.msg');
    if (!bubble) return;
    const body = bubble.querySelector('.msg-body');
    if (!body) return;
    showCtxMenu(event, body.textContent, bubble);
  });
  el('messages').addEventListener('click', async event => {
    const emptyActionBtn = event.target.closest('[data-empty-action]');
    if (emptyActionBtn) {
      const action = emptyActionBtn.dataset.emptyAction;
      if (action === 'open-first-visible-conversation') {
        const firstConversation = getVisibleQueueConversations()[0];
        if (firstConversation?.id) await loadLiveConversation(firstConversation.id);
      } else if (action === 'focus-queue-search') {
        focusQueueSearch();
      } else if (action === 'clear-queue-search') {
        clearQueueSearch();
        renderLiveFeed(el('live-feed-container'), {conversations: state.liveConversations});
      } else if (action === 'reset-queue-filter') {
        applyQueueFilter('all');
        renderLiveFeed(el('live-feed-container'), {conversations: state.liveConversations});
      }
      return;
    }
    const actionBtn = event.target.closest('[data-msg-action]');
    if (!actionBtn) return;
    const action = actionBtn.dataset.msgAction;
    const messageId = actionBtn.dataset.messageId;
    if (!state.activeConversationId || !messageId) return;
    actionBtn.disabled = true;
    try {
      if (action === 'approve') {
        const data = await apiFetch('/chat/approve-message', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({conversation_id: state.activeConversationId, message_id: messageId})});
        if (data?.session_reopen_template_sent) {
          notify(`Mesaj onaylandı. Meta pencere açma şablonu (${data.session_reopen_template_name || 'hello_world'}) kullanılarak gönderildi.`, 'success');
        } else {
          notify('Mesaj onaylandı ve gönderildi.', 'success');
        }
      } else if (action === 'reject') {
        await apiFetch('/chat/reject-message', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({conversation_id: state.activeConversationId, message_id: messageId})});
        notify('Mesaj reddedildi.', 'success');
      } else if (action === 'regenerate') {
        await apiFetch('/chat/regenerate', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({conversation_id: state.activeConversationId})});
        notify('Mesaj yeniden oluşturuldu.', 'success');
      } else if (action === 'feedback') {
        showConversationDetail(state.activeConversationId).then(() => showModalFeedbackForm(state.activeConversationId, messageId));
      }
      await loadLiveFeed();
      await loadLiveConversation(state.activeConversationId);
    } catch (error) {
      notify(error.message || 'Mesaj işlemi başarısız.', 'error');
      actionBtn.disabled = false;
    }
  });
  el('send-btn').addEventListener('click', sendMessage);
  el('attach-btn').addEventListener('click', openAttachmentPicker);
  el('voice-btn').addEventListener('click', toggleVoiceRecording);
  el('attachment-input').addEventListener('change', event => {
    handleAttachmentFiles(event.target.files);
  });
  el('composer-attachments').addEventListener('click', event => {
    const removeBtn = event.target.closest('[data-remove-attachment]');
    if (!removeBtn) return;
    removeComposerAttachment(removeBtn.dataset.removeAttachment);
  });
  el('reply-preview-clear').addEventListener('click', clearReplyTarget);
  el('composer-modebar').addEventListener('click', event => {
    const btn = event.target.closest('.composer-mode-btn');
    if (!btn) return;
    applyComposerMode(btn.dataset.composerMode || 'reply', {warnOnTemplateGate: true});
  });
  el('msg-input').addEventListener('keydown', event => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  });
  document.addEventListener('keydown', async event => {
    const target = event.target;
    const tagName = String(target?.tagName || '').toLowerCase();
    const editable = Boolean(target?.isContentEditable);
    const shortcutDialogOpen = Boolean(el('shortcut-dialog')?.open);
    const typingContext = editable
      || ['input', 'textarea', 'select', 'button'].includes(tagName)
      || target?.closest?.('.feedback-studio')
      || target?.closest?.('.template-panel')
      || target?.closest?.('.conv-modal')
      || target?.closest?.('.workspace-flyout');
    if (event.key === '?') {
      if (typingContext && !shortcutDialogOpen) return;
      event.preventDefault();
      toggleShortcutDialog(!shortcutDialogOpen);
      return;
    }
    if (event.key === 'Escape') {
      if (handleEscapeShortcut()) {
        event.preventDefault();
      }
      return;
    }
    if ((event.metaKey || event.ctrlKey) && (event.key === 'k' || event.key === 'K')) {
      if (!isDialogOpen()) {
        event.preventDefault();
        focusQueueSearch();
      }
      return;
    }
    if (typingContext || isDialogOpen()) return;

    if (event.key === 'r' || event.key === 'R') {
      event.preventDefault();
      applyComposerMode('reply', {warnOnTemplateGate: true, focusInput: true});
      return;
    }
    if (event.key === 'n' || event.key === 'N') {
      event.preventDefault();
      applyComposerMode('internal_note', {focusInput: true});
      return;
    }
    if (event.key === 't' || event.key === 'T') {
      event.preventDefault();
      applyComposerMode('template', {focusInput: true});
      return;
    }
    if (event.key === 'd' || event.key === 'D') {
      event.preventDefault();
      toggleWorkspaceDiagnostics();
      return;
    }
    if (event.key === 'g' || event.key === 'G') {
      event.preventDefault();
      applyContextTab('guest');
      return;
    }
    if (event.key === 'o' || event.key === 'O') {
      event.preventDefault();
      applyContextTab('operations');
      return;
    }
    if (event.key === 'l' || event.key === 'L') {
      event.preventDefault();
      applyContextTab('delivery');
      return;
    }
    if (event.key === 'a' || event.key === 'A') {
      event.preventDefault();
      applyContextTab('audit');
      return;
    }

    if (event.key === 'j' || event.key === 'ArrowDown') {
      event.preventDefault();
      await moveQueueSelection(1);
      return;
    }
    if (event.key === 'k' || event.key === 'ArrowUp') {
      event.preventDefault();
      await moveQueueSelection(-1);
      return;
    }
    if (event.key === 'Enter' && !state.activeConversationId) {
      event.preventDefault();
      await moveQueueSelection(1);
    }
  });
  el('msg-input').addEventListener('input', () => saveComposerDraft());
  el('reset-btn').addEventListener('click', resetConversation);
  el('export-btn').addEventListener('click', downloadConversation);
  el('refresh-imports').addEventListener('click', refreshImportFiles);
  el('import-select').addEventListener('change', () => loadSelectedImport());
  el('queue-tabs').addEventListener('click', event => {
    const btn = event.target.closest('.queue-tab');
    if (!btn) return;
    applyQueueFilter(btn.dataset.queueFilter || 'all');
    renderLiveFeed(el('live-feed-container'), {conversations: state.liveConversations});
  });
  el('queue-search').addEventListener('input', event => {
    state.queueSearch = event.target.value || '';
    renderLiveFeed(el('live-feed-container'), {conversations: state.liveConversations});
  });
  el('template-search').addEventListener('input', event => {
    state.templateSearch = event.target.value || '';
    renderTemplatePanel();
  });
  el('template-list').addEventListener('click', event => {
    const card = event.target.closest('[data-template-id]');
    if (!card) return;
    state.selectedTemplateId = card.dataset.templateId || null;
    renderTemplatePanel();
  });
  el('context-tabs').addEventListener('click', event => {
    const btn = event.target.closest('.context-tab');
    if (!btn) return;
    applyContextTab(btn.dataset.contextTab || 'guest');
  });
  el('context-body').addEventListener('click', async event => {
    const actionBtn = event.target.closest('[data-guest-action]');
    if (!actionBtn) return;
    const conversationId = state.activeConversationId;
    const guestInfo = state.conversation?.guest_info || {};
    const holdId = actionBtn.dataset.holdId || guestInfo.hold_id || '';
    if (!conversationId || !holdId) return;

    const action = actionBtn.dataset.guestAction || '';
    let path = '';
    let payload = null;
    let confirmMessage = '';
    let successMessage = '';

    if (action === 'approve') {
      if (!guestInfo.approve_enabled) {
        notify(guestInfo.approve_reason || 'Rezervasyon onay akışı şu an kapalı.', 'warn');
        return;
      }
      path = '/api/v1/admin/holds/' + encodeURIComponent(holdId) + '/approve';
      payload = {notes: 'chat_lab_guest_info_approve'};
      confirmMessage = 'Bu rezervasyon için onay akışını başlatmak istiyor musunuz?';
      successMessage = 'Rezervasyon onay akışı başlatıldı.';
    } else if (action === 'cancel') {
      if (!guestInfo.cancel_enabled) {
        notify(guestInfo.cancel_reason || 'Rezervasyon iptal akışı şu an kapalı.', 'warn');
        return;
      }
      if (guestInfo.cancel_action === 'cancel_reservation') {
        path = '/api/v1/admin/holds/' + encodeURIComponent(holdId) + '/cancel-reservation';
        payload = {reason: 'chat_lab_guest_info_cancel'};
        confirmMessage = 'Bu rezervasyon Elektra PMS üzerinden iptal edilecek. Devam edilsin mi?';
        successMessage = 'Rezervasyon Elektra üzerinden iptal edildi.';
      } else if (guestInfo.cancel_action === 'reject_hold') {
        path = '/api/v1/admin/holds/' + encodeURIComponent(holdId) + '/reject';
        payload = {reason: 'chat_lab_guest_info_cancel'};
        confirmMessage = 'Bu hold PMS kaydı oluşmadan iptal edilecek. Devam edilsin mi?';
        successMessage = 'Rezervasyon talebi iptal edildi.';
      } else {
        notify(guestInfo.cancel_reason || 'Rezervasyon iptal akışı şu an kapalı.', 'warn');
        return;
      }
    } else {
      return;
    }

    if (typeof window.confirm === 'function' && !window.confirm(confirmMessage)) {
      return;
    }

    const originalLabel = actionBtn.textContent;
    actionBtn.disabled = true;
    actionBtn.textContent = action === 'approve' ? 'İşleniyor...' : 'İptal Ediliyor...';
    try {
      const data = await apiFetch(path, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload),
      });
      if (data?.status === 'already_processed') {
        notify(data?.result?.message || 'Rezervasyon zaten işlenmiş durumda.', 'warn');
      } else {
        notify(successMessage, 'success');
      }
      await loadLiveFeed();
      await loadLiveConversation(conversationId);
    } catch (error) {
      notify(error.message || 'Rezervasyon aksiyonu başarısız.', 'error');
      actionBtn.disabled = false;
      actionBtn.textContent = originalLabel;
    }
  });
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
  el('metrics-refresh').addEventListener('click', loadMetrics);
  el('live-feed-refresh').addEventListener('click', loadLiveFeed);
  const includeInactiveToggle = el('include-inactive-toggle');
  if (includeInactiveToggle) includeInactiveToggle.addEventListener('change', loadLiveFeed);
  el('live-feed-container').addEventListener('click', async event => {
    const emptyActionBtn = event.target.closest('[data-empty-action]');
    if (emptyActionBtn) {
      const action = emptyActionBtn.dataset.emptyAction;
      if (action === 'clear-queue-search') {
        clearQueueSearch();
        renderLiveFeed(el('live-feed-container'), {conversations: state.liveConversations});
      } else if (action === 'reset-queue-filter') {
        applyQueueFilter('all');
        renderLiveFeed(el('live-feed-container'), {conversations: state.liveConversations});
      } else if (action === 'refresh-queue') {
        await loadLiveFeed();
      }
      return;
    }
    // Approve button
    const approveBtn = event.target.closest('.live-feed-approve-btn');
    if (approveBtn) {
      event.stopPropagation();
      const convId = approveBtn.dataset.approveConv;
      const msgId = approveBtn.dataset.approveMsg;
      if (!convId || !msgId) return;
      approveBtn.disabled = true;
      approveBtn.textContent = 'Gönderiliyor...';
      try {
        const data = await apiFetch('/chat/approve-message', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({conversation_id: convId, message_id: msgId})});
        if (data?.session_reopen_template_sent) {
          notify(`Mesaj onaylandı. Meta pencere açma şablonu (${data.session_reopen_template_name || 'hello_world'}) kullanılarak gönderildi.`, 'success');
        } else {
          notify('Mesaj onaylandı ve gönderildi.', 'success');
        }
        await loadLiveFeed();
        await loadLiveConversation(convId);
      } catch (error) {
        notify(error.message || 'Onay gönderilemedi.', 'error');
        approveBtn.disabled = false;
        approveBtn.textContent = 'Onayla ve Gönder';
      }
      return;
    }
    // Reject button with confirm state
    const rejectBtn = event.target.closest('.live-feed-reject-btn');
    if (rejectBtn) {
      event.stopPropagation();
      if (!rejectBtn.classList.contains('confirm-state')) {
        rejectBtn.classList.add('confirm-state');
        rejectBtn.textContent = 'Emin misiniz?';
        setTimeout(() => { rejectBtn.classList.remove('confirm-state'); rejectBtn.textContent = 'Reddet'; }, 3000);
        return;
      }
      const convId = rejectBtn.dataset.rejectConv;
      const msgId = rejectBtn.dataset.rejectMsg;
      if (!convId || !msgId) return;
      rejectBtn.disabled = true;
      rejectBtn.textContent = 'Reddediliyor...';
      try {
        await apiFetch('/chat/reject-message', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({conversation_id: convId, message_id: msgId})});
        notify('Mesaj reddedildi.', 'success');
        await loadLiveFeed();
        await loadLiveConversation(convId);
        // Open modal with feedback form for the rejected message
        showConversationDetail(convId).then(() => {
          showModalFeedbackForm(convId, msgId);
        });
      } catch (error) {
        notify(error.message || 'Reddetme başarısız.', 'error');
        rejectBtn.disabled = false;
        rejectBtn.textContent = 'Reddet';
        rejectBtn.classList.remove('confirm-state');
      }
      return;
    }
    // Card click → open modal
    const card = event.target.closest('.live-feed-card');
    if (card && card.dataset.convId) {
      loadLiveConversation(card.dataset.convId);
    }
  });
  el('live-feed-container').addEventListener('keydown', async event => {
    const card = event.target.closest('.live-feed-card');
    if (!card || !card.dataset.convId) return;
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      await loadLiveConversation(card.dataset.convId);
    }
  });
  // Right-click copy on live feed messages
  el('live-feed-container').addEventListener('contextmenu', event => {
    // Find the closest message text element or fall back to the card itself
    let msgEl = event.target.closest('.live-feed-user') || event.target.closest('.live-feed-assistant');
    const card = event.target.closest('.live-feed-card');
    if (!msgEl && card) {
      // User right-clicked elsewhere on the card — pick the assistant (AI response) text
      msgEl = card.querySelector('.live-feed-assistant');
    }
    if (!msgEl) return;
    event.preventDefault();
    // Clone node and remove status badges so copied text is clean
    const clone = msgEl.cloneNode(true);
    clone.querySelectorAll('.live-feed-blocked,.live-feed-sent,.live-feed-rejected,.live-feed-approve-btn,.live-feed-reject-btn').forEach(n => n.remove());
    const raw = clone.textContent.replace(/^(Misafir|Yapay Zekâ|Son çıkış):\\s*/, '').trim();
    if (raw) showCtxMenu(event, raw);
  });
  // Drag-and-drop: live feed card → chat panel
  el('live-feed-container').addEventListener('dragstart', event => {
    const card = event.target.closest('.live-feed-card');
    if (!card || !card.dataset.convId) { event.preventDefault(); return; }
    event.dataTransfer.setData('text/plain', card.dataset.convId);
    event.dataTransfer.effectAllowed = 'copy';
    card.classList.add('is-dragging');
    requestAnimationFrame(() => document.querySelector('.chat-panel').classList.add('drop-active'));
  });
  el('live-feed-container').addEventListener('dragend', event => {
    const card = event.target.closest('.live-feed-card');
    if (card) card.classList.remove('is-dragging');
    document.querySelector('.chat-panel').classList.remove('drop-active');
  });
  const chatPanel = document.querySelector('.chat-panel');
  chatPanel.addEventListener('dragover', event => {
    if (!event.dataTransfer.types.includes('text/plain')) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = 'copy';
    chatPanel.classList.add('drop-active');
  });
  chatPanel.addEventListener('dragleave', event => {
    if (!chatPanel.contains(event.relatedTarget)) chatPanel.classList.remove('drop-active');
  });
  chatPanel.addEventListener('drop', event => {
    event.preventDefault();
    chatPanel.classList.remove('drop-active');
    const convId = event.dataTransfer.getData('text/plain');
    if (!convId) return;
    // Update dropdown selection to match
    const selectVal = 'conv:' + convId;
    const select = el('import-select');
    if (select.querySelector('option[value="' + selectVal.replace(/"/g, '\\"') + '"]')) {
      select.value = selectVal;
    }
    loadLiveConversation(convId);
  });
  // Modal close handlers
  el('conv-modal-close').addEventListener('click', closeConvModal);
  el('conv-detail-overlay').addEventListener('click', event => {
    if (event.target === el('conv-detail-overlay')) closeConvModal();
  });
  el('conv-modal-json-btn').addEventListener('click', () => {
    el('conv-modal-json').classList.toggle('hidden');
  });
  // Right-click copy on modal messages
  el('conv-modal-messages').addEventListener('contextmenu', event => {
    const msgEl = event.target.closest('.conv-msg');
    if (!msgEl) return;
    const body = msgEl.querySelector('.conv-msg-body');
    if (!body) return;
    showCtxMenu(event, body.textContent);
  });
  // Send message from modal
  el('conv-modal-send-btn').addEventListener('click', sendModalMessage);
  el('conv-modal-msg-input').addEventListener('keydown', event => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendModalMessage();
    }
  });
  el('mode-switch').addEventListener('click', event => {
    const btn = event.target.closest('.mode-btn');
    if (btn && btn.dataset.mode) changeMode(btn.dataset.mode);
  });
  el('report-submit').addEventListener('click', generateReport);
  el('model-select').addEventListener('change', changeModel);
  el('phone-input').addEventListener('change', () => {
    if (state.sourceType === 'live_test_chat') {
      saveComposerDraft();
      loadHistory();
    }
  });
  el('workspace-open-diagnostics').addEventListener('click', toggleWorkspaceDiagnostics);
}

async function boot() {
  if (_booted) return;
  _booted = true;
  startInteractiveLabelObserver(document.body);
  wireEvents();
  renderWorkspaceFlyout();
  renderWorkspaceSummary();
  renderCategoryOptions();
  renderTagOptions();
  renderThreadHeader();
  renderSessionStrip();
  renderContextRail();
  renderComposerModeBar();
  renderComposerHelper();
  renderReplyPreview();
  try {
    await Promise.all([loadCatalog(), loadModels(), refreshImportFiles(), loadMetrics(), loadMode(), loadLiveFeed()]);
  } catch (error) {
    notify(error.message || 'Panel başlatılamadı. Lütfen tekrar deneyin.', 'error');
    _booted = false;
    return;
  }
  setComposerMode(true);
  if (state.liveConversations.length) {
    await loadLiveConversation(state.liveConversations[0].id);
  } else {
    await loadHistory();
  }
  // Auto-refresh live feed and mode every 3 seconds
  setInterval(async () => {
    await loadLiveFeed();
    await loadMode();
    if (state.sourceType === 'live_conversation' && state.activeConversationId) {
      await loadLiveConversation(state.activeConversationId);
    }
  }, 3000);
}

let _eventsBound = false;
let _booted = false;

window.addEventListener('load', boot);

// Accept auth token from parent admin panel when running inside an iframe.
window.addEventListener('message', event => {
  if (event.origin !== window.location.origin) return;
  if (event.data && event.data.type === 'chatlab:token') {
    state.adminToken = String(event.data.token || '');
    state.hotelId = String(event.data.hotelId || '');
    finishParentRefresh(Boolean(state.adminToken));
    if (state.adminToken) {
      boot();
    }
  }
});
"""
