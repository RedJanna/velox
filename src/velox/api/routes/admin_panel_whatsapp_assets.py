"""WhatsApp API admin panel assets."""

# ruff: noqa: E501

ADMIN_WHATSAPP_STYLE = """\
.whatsapp-status-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}
.whatsapp-card{background:#fff;border:1px solid var(--border);border-radius:12px;padding:16px;min-height:120px;display:flex;flex-direction:column;gap:8px}
.whatsapp-card h4{margin:0;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.08em}
.whatsapp-card strong{font-size:22px;color:var(--ink);line-height:1.15}
.whatsapp-card span{color:var(--muted);font-size:13px;line-height:1.35;overflow-wrap:anywhere}
.whatsapp-layout{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(360px,.85fr);gap:18px;align-items:start}
.whatsapp-checklist{display:grid;gap:10px}
.whatsapp-check{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;border:1px solid var(--border);border-radius:10px;padding:12px;background:#fff}
.whatsapp-check strong{display:block;margin-bottom:3px}
.whatsapp-check small{color:var(--muted);line-height:1.35}
.whatsapp-dot{width:12px;height:12px;border-radius:999px;margin-top:4px;flex:0 0 auto;background:#94a3b8}
.whatsapp-dot.ok{background:#16a34a}
.whatsapp-dot.warn{background:#d97706}
.whatsapp-dot.bad{background:#dc2626}
.whatsapp-actions{display:flex;flex-wrap:wrap;gap:10px}
.whatsapp-secret-input{font-family:ui-monospace,SFMono-Regular,Consolas,monospace}
.whatsapp-template-list,.whatsapp-event-list{display:grid;gap:10px}
.whatsapp-list-item{border:1px solid var(--border);border-radius:10px;padding:12px;background:#fff}
.whatsapp-list-item header{display:flex;justify-content:space-between;gap:12px;margin-bottom:8px}
.whatsapp-list-item strong,.whatsapp-list-item span{overflow-wrap:anywhere}
.whatsapp-oauth-step{display:flex;gap:12px;align-items:flex-start;border:1px solid var(--border);border-radius:10px;padding:12px;background:#fff}
.whatsapp-oauth-step span{display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:999px;background:#0f766e;color:#fff;font-weight:800;flex:0 0 auto}
.whatsapp-asset-picker{display:grid;gap:10px;margin-top:14px}
.whatsapp-asset-button{width:100%;text-align:left;border:1px solid var(--border);border-radius:10px;background:#fff;padding:12px;cursor:pointer}
.whatsapp-asset-button:hover{border-color:#0f766e;box-shadow:0 0 0 3px rgba(15,118,110,.12)}
.whatsapp-asset-button strong{display:block;margin-bottom:4px}
.whatsapp-asset-button span{display:block;color:var(--muted);font-size:13px;overflow-wrap:anywhere}
@media (max-width:1100px){.whatsapp-status-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.whatsapp-layout{grid-template-columns:1fr}}
@media (max-width:640px){.whatsapp-status-grid{grid-template-columns:1fr}.whatsapp-actions{flex-direction:column}.whatsapp-actions button{width:100%}}
"""

ADMIN_WHATSAPP_SCRIPT = """\
(function(){
  function normalizeWhatsAppView(view) {
    var normalized = String(view || '').trim().toLowerCase();
    if (normalized === 'whatsappapi' || normalized === 'whatsapp-api' || normalized === 'whatsappapı') {
      return 'whatsappapi';
    }
    return view;
  }

  var refs = {};
  var pollTimer = null;

  function bindWhatsAppRefs() {
    [
      'whatsappStatusCards','whatsappConfigChecklist','whatsappIntegrationMeta','whatsappEvents',
      'whatsappTemplates','whatsappManualForm','whatsappTemplateForm','whatsappConnectButton',
      'whatsappHealthButton','whatsappWebhookSubscribeButton','whatsappTemplateSyncButton',
      'whatsappConnectDialog','whatsappConnectCancel','whatsappConnectLaunch','whatsappConnectStatus',
      'whatsappOauthSteps','whatsappAssets'
    ].forEach(function(id){ refs[id] = document.getElementById(id); });
  }

  function bindWhatsAppEvents() {
    refs.whatsappManualForm?.addEventListener('submit', onManualSave);
    refs.whatsappTemplateForm?.addEventListener('submit', onTemplateDraftSave);
    refs.whatsappConnectButton?.addEventListener('click', openConnectDialog);
    refs.whatsappConnectCancel?.addEventListener('click', closeConnectDialog);
    refs.whatsappConnectLaunch?.addEventListener('click', launchConnectSession);
    refs.whatsappHealthButton?.addEventListener('click', runHealthCheck);
    refs.whatsappWebhookSubscribeButton?.addEventListener('click', subscribeWebhook);
    refs.whatsappTemplateSyncButton?.addEventListener('click', syncTemplates);
    refs.whatsappAssets?.addEventListener('click', onConnectAssetClick);
    window.addEventListener('message', function(event) {
      if (event.origin !== window.location.origin) return;
      if (!event.data || event.data.type !== 'velox:whatsapp-oauth') return;
      notify(event.data.message || 'Meta bağlantısı güncellendi.', event.data.status === 'authorized' ? 'success' : 'warn');
      if (state.whatsappConnectSessionId) {
        pollConnectSession(state.whatsappConnectSessionId);
      }
    });
  }

  function patchSetView() {
    if (typeof setView !== 'function' || window.__veloxWhatsappViewPatched) return;
    window.__veloxWhatsappViewPatched = true;
    var originalSetView = setView;
    setView = function(view) {
      var normalized = normalizeWhatsAppView(view);
      originalSetView(normalized);
      if (normalized === 'whatsappapi') {
        var pageTitle = document.getElementById('pageTitle');
        var pageLead = document.getElementById('pageLead');
        pageTitle && (pageTitle.textContent = 'WhatsApp API');
        pageLead && (pageLead.textContent = 'Meta Cloud API bağlantısı, webhook ve şablon durumlarını yönetin.');
        loadWhatsAppIntegration();
      }
    };
    var initialView = normalizeWhatsAppView(state.currentView || window.location.hash.replace('#', ''));
    if (initialView !== state.currentView) {
      state.currentView = initialView;
      window.location.hash = initialView;
    }
  }

  async function loadWhatsAppIntegration() {
    if (!state.selectedHotelId) {
      renderEmptyWhatsApp('Otel kapsamı seçilmedi.');
      return;
    }
    try {
      var payload = await apiFetch('/hotels/' + encodeURIComponent(state.selectedHotelId) + '/whatsapp/integration');
      state.whatsappIntegrationPayload = payload;
      renderWhatsAppIntegration(payload);
      await loadTemplatesOnly();
    } catch (error) {
      renderEmptyWhatsApp(error.message);
      notify(error.message, 'error');
    }
  }

  function renderEmptyWhatsApp(message) {
    if (refs.whatsappStatusCards) refs.whatsappStatusCards.innerHTML = '<article class="whatsapp-card"><h4>Durum</h4><strong>Bekliyor</strong><span>' + escapeHtml(message) + '</span></article>';
  }

  function renderWhatsAppIntegration(payload) {
    var integration = payload.integration || {};
    var config = payload.config || {};
    var status = integration.connection_status || 'not_connected';
    var webhook = integration.webhook_status || 'unknown';
    var templateSummary = payload.template_summary || {};
    refs.whatsappStatusCards.innerHTML = [
      statusCard('Bağlantı', statusLabel(status), integration.display_phone_number || integration.phone_number_id || 'Numara yok'),
      statusCard('Webhook', statusLabel(webhook), config.webhook_url || '-'),
      statusCard('Token', integration.token_mask || 'not_stored', integration.token_expires_at ? formatDate(integration.token_expires_at) : 'Süre bilgisi yok'),
      statusCard('Şablonlar', String(templateSummary.approved || 0) + ' onaylı', String(templateSummary.total || 0) + ' toplam kayıt')
    ].join('');
    refs.whatsappConfigChecklist.innerHTML = [
      checkRow(config.meta_app_configured, 'Meta App', 'App ID ve App Secret backend tarafında tanımlı.'),
      checkRow(config.embedded_signup_configured, 'Embedded Signup', 'Config ID tanımlıysa bağlantı popup akışı açılır.'),
      checkRow(config.token_encryption_configured, 'Token şifreleme', 'Access token veritabanında şifreli saklanır.'),
      checkRow(config.verify_token_configured && config.app_secret_configured, 'Webhook güvenliği', 'Verify token ve app secret hazır.')
    ].join('');
    refs.whatsappIntegrationMeta.innerHTML = renderIntegrationMeta(payload);
    refs.whatsappEvents.innerHTML = renderEvents(payload.events || []);
    fillManualForm(integration);
  }

  function statusCard(title, value, detail) {
    return '<article class="whatsapp-card"><h4>' + escapeHtml(title) + '</h4><strong>' + escapeHtml(value) + '</strong><span>' + escapeHtml(detail || '-') + '</span></article>';
  }

  function statusLabel(value) {
    var raw = String(value || '').replace(/_/g, ' ');
    return raw ? raw.charAt(0).toUpperCase() + raw.slice(1) : '-';
  }

  function checkRow(ok, title, detail) {
    var tone = ok ? 'ok' : 'bad';
    return '<div class="whatsapp-check"><div><strong>' + escapeHtml(title) + '</strong><small>' + escapeHtml(detail) + '</small></div><span class="whatsapp-dot ' + tone + '"></span></div>';
  }

  function renderIntegrationMeta(payload) {
    var integration = payload.integration || {};
    var config = payload.config || {};
    if (!integration.id) {
      return '<div class="empty-state"><h4>Bağlı numara yok</h4><p>Meta popup akışı veya gelişmiş manuel kayıt ile ilk bağlantıyı oluşturun.</p></div>';
    }
    return '<div class="helper-grid">' +
      helperBox('Business ID', integration.business_id || '-') +
      helperBox('WABA ID', integration.waba_id || '-') +
      helperBox('Phone Number ID', integration.phone_number_id || '-') +
      helperBox('Kalite', integration.quality_rating || '-') +
      helperBox('Webhook URL', config.webhook_url || '-') +
      helperBox('Son kontrol', integration.last_health_check_at ? formatDate(integration.last_health_check_at) : '-') +
    '</div>';
  }

  function helperBox(title, value) {
    return '<div class="helper-box"><strong>' + escapeHtml(title) + '</strong><p class="mono">' + escapeHtml(value) + '</p></div>';
  }

  function renderEvents(events) {
    if (!events.length) return '<div class="empty-state"><p>Henüz bağlantı olayı yok.</p></div>';
    return events.map(function(event) {
      return '<div class="whatsapp-list-item"><header><strong>' + escapeHtml(event.event_type || '-') + '</strong><span>' + escapeHtml(formatDate(event.created_at)) + '</span></header><p class="mono">' + escapeHtml(JSON.stringify(event.safe_payload_json || {})) + '</p></div>';
    }).join('');
  }

  function fillManualForm(integration) {
    if (!refs.whatsappManualForm || !integration) return;
    var form = refs.whatsappManualForm;
    ['business_id','waba_id','phone_number_id','display_phone_number','verified_name','quality_rating','messaging_limit'].forEach(function(name) {
      if (form.elements[name]) form.elements[name].value = integration[name] || '';
    });
    if (form.elements.access_token) form.elements.access_token.value = '';
    if (form.elements.webhook_verify_token) form.elements.webhook_verify_token.value = '';
  }

  async function onManualSave(event) {
    event.preventDefault();
    if (!state.selectedHotelId) return;
    var form = refs.whatsappManualForm;
    var body = formToJson(form);
    body.token_scopes = String(body.token_scopes || '').split(',').map(function(item){ return item.trim(); }).filter(Boolean);
    if (!body.access_token) delete body.access_token;
    if (!body.webhook_verify_token) delete body.webhook_verify_token;
    try {
      await apiFetch('/hotels/' + encodeURIComponent(state.selectedHotelId) + '/whatsapp/integration/manual', {method: 'POST', body: body});
      form.access_token.value = '';
      form.webhook_verify_token.value = '';
      notify('WhatsApp bağlantı kaydı güncellendi.', 'success');
      await loadWhatsAppIntegration();
    } catch (error) {
      notify(error.message, 'error');
    }
  }

  function openConnectDialog() {
    state.whatsappConnectSessionId = '';
    state.whatsappAssetItems = [];
    refs.whatsappConnectStatus.textContent = 'Bağlantı oturumu bekleniyor.';
    if (refs.whatsappAssets) refs.whatsappAssets.innerHTML = '';
    refs.whatsappConnectDialog?.showModal();
  }

  function closeConnectDialog() {
    if (pollTimer) window.clearTimeout(pollTimer);
    pollTimer = null;
    refs.whatsappConnectDialog?.close();
  }

  async function launchConnectSession() {
    try {
      var session = await apiFetch('/hotels/' + encodeURIComponent(state.selectedHotelId) + '/whatsapp/connect-sessions', {method: 'POST', body: {}});
      state.whatsappConnectSessionId = session.session_id;
      refs.whatsappConnectStatus.textContent = 'Meta bağlantı penceresi açıldı. İşlem tamamlanınca bu modal güncellenecek.';
      var popup = window.open(session.auth_url, 'velox_meta_whatsapp_signup', 'width=720,height=760,noopener=false');
      if (!popup) {
        notify('Açılır pencere engellendi. Tarayıcıda popup izni verip tekrar deneyin.', 'warn');
      }
      pollConnectSession(session.session_id);
    } catch (error) {
      refs.whatsappConnectStatus.textContent = error.message;
      notify(error.message, 'error');
    }
  }

  async function pollConnectSession(sessionId) {
    if (!sessionId || !state.selectedHotelId) return;
    try {
      var session = await apiFetch('/hotels/' + encodeURIComponent(state.selectedHotelId) + '/whatsapp/connect-sessions/' + encodeURIComponent(sessionId));
      refs.whatsappConnectStatus.textContent = 'Durum: ' + statusLabel(session.status) + (session.error_message ? ' - ' + session.error_message : '');
      if (session.authorized) {
        await loadConnectAssets(sessionId);
        return;
      }
      if (session.status === 'completed') {
        await loadWhatsAppIntegration();
        return;
      }
      if (session.status === 'error') {
        await loadWhatsAppIntegration();
        return;
      }
      pollTimer = window.setTimeout(function(){ pollConnectSession(sessionId); }, 2500);
    } catch (error) {
      refs.whatsappConnectStatus.textContent = error.message;
    }
  }

  async function loadConnectAssets(sessionId) {
    try {
      refs.whatsappConnectStatus.textContent = 'Meta yetkilendirmesi tamamlandı. Bağlanacak WhatsApp numarasını seçin.';
      var payload = await apiFetch('/hotels/' + encodeURIComponent(state.selectedHotelId) + '/whatsapp/assets?session_id=' + encodeURIComponent(sessionId));
      state.whatsappAssetItems = payload.items || [];
      renderConnectAssets(state.whatsappAssetItems);
    } catch (error) {
      refs.whatsappConnectStatus.textContent = error.message;
      notify(error.message, 'error');
    }
  }

  function renderConnectAssets(items) {
    if (!refs.whatsappAssets) return;
    if (!items.length) {
      refs.whatsappAssets.innerHTML = '<div class="empty-state"><p>Bu Meta hesabında erişilebilir WhatsApp numarası bulunamadı.</p></div>';
      return;
    }
    refs.whatsappAssets.innerHTML = items.map(function(item, index) {
      var title = item.display_phone_number || item.phone_number_id || 'WhatsApp numarası';
      var detail = [item.verified_name, item.waba_name, item.business_name].filter(Boolean).join(' / ');
      return '<button class="whatsapp-asset-button" type="button" data-asset-index="' + index + '">' +
        '<strong>' + escapeHtml(title) + '</strong>' +
        '<span>' + escapeHtml(detail || '-') + '</span>' +
        '<span class="mono">Phone Number ID: ' + escapeHtml(item.phone_number_id || '-') + '</span>' +
      '</button>';
    }).join('');
  }

  async function onConnectAssetClick(event) {
    var button = event.target.closest('[data-asset-index]');
    if (!button) return;
    var item = state.whatsappAssetItems && state.whatsappAssetItems[Number(button.dataset.assetIndex)];
    if (!item || !state.whatsappConnectSessionId) return;
    try {
      refs.whatsappConnectStatus.textContent = 'Numara bağlanıyor...';
      await apiFetch('/hotels/' + encodeURIComponent(state.selectedHotelId) + '/whatsapp/connect-sessions/' + encodeURIComponent(state.whatsappConnectSessionId) + '/complete', {
        method: 'POST',
        body: {
          phone_number_id: item.phone_number_id,
          waba_id: item.waba_id
        }
      });
      notify('WhatsApp numarası bağlandı. Webhook doğrulamasını çalıştırın.', 'success');
      closeConnectDialog();
      await loadWhatsAppIntegration();
    } catch (error) {
      refs.whatsappConnectStatus.textContent = error.message;
      notify(error.message, 'error');
    }
  }

  async function runHealthCheck() {
    try {
      var result = await apiFetch('/hotels/' + encodeURIComponent(state.selectedHotelId) + '/whatsapp/health-check', {method: 'POST', body: {}});
      notify(result.ok ? 'WhatsApp sağlık kontrolü geçti.' : 'Sağlık kontrolünde eksikler var.', result.ok ? 'success' : 'warn');
      await loadWhatsAppIntegration();
    } catch (error) {
      notify(error.message, 'error');
    }
  }

  async function subscribeWebhook() {
    try {
      await apiFetch('/hotels/' + encodeURIComponent(state.selectedHotelId) + '/whatsapp/webhook/subscribe', {method: 'POST', body: {}});
      notify('Webhook aboneliği güncellendi.', 'success');
      await loadWhatsAppIntegration();
    } catch (error) {
      notify(error.message, 'error');
    }
  }

  async function loadTemplatesOnly() {
    if (!refs.whatsappTemplates || !state.selectedHotelId) return;
    try {
      var response = await apiFetch('/hotels/' + encodeURIComponent(state.selectedHotelId) + '/whatsapp/templates');
      renderTemplates(response.items || []);
    } catch (_error) {
      refs.whatsappTemplates.innerHTML = '<div class="empty-state"><p>Şablonlar alınamadı.</p></div>';
    }
  }

  function renderTemplates(items) {
    if (!items.length) {
      refs.whatsappTemplates.innerHTML = '<div class="empty-state"><p>Henüz template kaydı yok.</p></div>';
      return;
    }
    refs.whatsappTemplates.innerHTML = items.map(function(item) {
      return '<div class="whatsapp-list-item"><header><strong>' + escapeHtml(item.name || '-') + '</strong><span>' + escapeHtml(item.status || '-') + '</span></header><p>' + escapeHtml((item.language || '-') + ' / ' + (item.category || '-')) + '</p></div>';
    }).join('');
  }

  async function syncTemplates() {
    try {
      var result = await apiFetch('/hotels/' + encodeURIComponent(state.selectedHotelId) + '/whatsapp/templates/sync', {method: 'POST', body: {}});
      notify(result.count + ' template senkronize edildi.', 'success');
      await loadWhatsAppIntegration();
    } catch (error) {
      notify(error.message, 'error');
    }
  }

  async function onTemplateDraftSave(event) {
    event.preventDefault();
    var body = formToJson(refs.whatsappTemplateForm);
    try {
      body.components = body.components_json ? JSON.parse(body.components_json) : [];
    } catch (_error) {
      notify('Components JSON geçerli değil.', 'error');
      return;
    }
    delete body.components_json;
    try {
      await apiFetch('/hotels/' + encodeURIComponent(state.selectedHotelId) + '/whatsapp/templates', {method: 'POST', body: body});
      refs.whatsappTemplateForm.reset();
      notify('Template taslağı kaydedildi.', 'success');
      await loadTemplatesOnly();
    } catch (error) {
      notify(error.message, 'error');
    }
  }

  document.addEventListener('DOMContentLoaded', function(){
    bindWhatsAppRefs();
    bindWhatsAppEvents();
    patchSetView();
  });
})();
"""
