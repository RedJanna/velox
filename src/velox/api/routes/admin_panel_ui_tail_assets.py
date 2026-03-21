"""Tail script sections for the admin operations panel."""

# ruff: noqa: E501

ADMIN_PANEL_TAIL_SCRIPT = """\
async function loadFaqs() {
  const hotelId = state.selectedHotelId;
  if (!hotelId) {
    refs.faqTableBody.innerHTML = '<tr><td colspan="5"><div class="empty-state"><p>Hotel seçin.</p></div></td></tr>';
    refs.faqDetail.innerHTML = '<div class="empty-state"><p>Detay için listeden bir FAQ kaydı seçin.</p></div>';
    state.faqs = [];
    state.faqDetail = null;
    return;
  }
  const form = new FormData(refs.faqFilters);
  const params = new URLSearchParams();
  if (form.get('status')) params.set('status', String(form.get('status')));
  if (form.get('q')) params.set('q', String(form.get('q')));
  const response = await apiFetch(`/hotels/${hotelId}/faq?${params.toString()}`);
  state.faqs = response.items || [];
  refs.faqTableBody.innerHTML = renderFaqRows(state.faqs);
  bindFaqActions();
  if (!state.faqDetail || !state.faqs.find(item => item.faq_id === state.faqDetail.faq_id)) {
    state.faqDetail = null;
    refs.faqDetail.innerHTML = '<div class="empty-state"><p>Detay için listeden bir FAQ kaydı seçin.</p></div>';
  } else {
    renderFaqDetail(state.faqDetail);
  }
}

function renderFaqRows(items) {
  if (!items.length) {
    return '<tr><td colspan="5"><div class="empty-state"><p>Filtreye uyan FAQ kaydı bulunamadı.</p></div></td></tr>';
  }
  return items.map(item => {
    const pillClass = item.status === 'ACTIVE' ? 'open' : (item.status === 'REMOVED' ? 'closed' : 'pending');
    const questionPreview = `${item.question?.tr || '-'} / ${item.question?.en || '-'}`;
    const answerPreview = `${item.answer?.tr || '-'} / ${item.answer?.en || '-'}`;
    return `
      <tr>
        <td><strong>${escapeHtml(item.topic || '-')}</strong></td>
        <td><span class="pill ${pillClass}">${escapeHtml(item.status || '-')}</span></td>
        <td><span class="muted">${escapeHtml(questionPreview).slice(0, 180)}</span></td>
        <td><span class="muted">${escapeHtml(answerPreview).slice(0, 180)}</span></td>
        <td>
          <div class="stack">
            <button class="action-button primary" data-faq-open="${escapeHtml(item.faq_id)}" aria-label="${escapeHtml((item.topic || 'FAQ') + ' detayini ac')}">Detay</button>
            ${item.status === 'ACTIVE'
              ? `<button class="action-button warn" data-faq-status="${escapeHtml(item.faq_id)}" data-next-status="PAUSED" aria-label="${escapeHtml((item.topic || 'FAQ') + ' kaydini pasife al')}">Pasife Al</button>`
              : ''}
            ${(item.status === 'PAUSED' || item.status === 'DRAFT')
              ? `<button class="action-button primary" data-faq-status="${escapeHtml(item.faq_id)}" data-next-status="ACTIVE" aria-label="${escapeHtml((item.topic || 'FAQ') + ' kaydini aktif et')}">Aktif Et</button>`
              : ''}
            ${item.status !== 'REMOVED'
              ? `<button class="action-button danger" data-faq-remove="${escapeHtml(item.faq_id)}" aria-label="${escapeHtml((item.topic || 'FAQ') + ' kaydini kaldir')}">Kaldir</button>`
              : ''}
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function bindFaqActions() {
  document.querySelectorAll('[data-faq-open]').forEach(button => {
    button.addEventListener('click', () => {
      const item = state.faqs.find(entry => entry.faq_id === button.dataset.faqOpen);
      if (!item) return;
      state.faqDetail = item;
      renderFaqDetail(item);
    });
  });

  document.querySelectorAll('[data-faq-status]').forEach(button => {
    button.addEventListener('click', async () => {
      const faqId = button.dataset.faqStatus;
      const nextStatus = button.dataset.nextStatus;
      try {
        await apiFetch(`/hotels/${state.selectedHotelId}/faq/${faqId}/status`, {
          method: 'POST',
          body: {status: nextStatus},
        });
        notify(`FAQ durumu ${nextStatus} olarak guncellendi.`, 'success');
        await loadFaqs();
      } catch (error) {
        notify(error.message, 'error');
      }
    });
  });

  document.querySelectorAll('[data-faq-remove]').forEach(button => {
    button.addEventListener('click', async () => {
      const faqId = button.dataset.faqRemove;
      const reason = window.prompt('Kaldırma gerekçesi yazın:');
      if (!reason || !reason.trim()) {
        notify('Kaldırma gerekçesi zorunlu.', 'warn');
        return;
      }
      try {
        await apiFetch(`/hotels/${state.selectedHotelId}/faq/${faqId}`, {
          method: 'DELETE',
          body: {reason: reason.trim()},
        });
        notify('FAQ kaydi aninda kaldirildi.', 'success');
        await loadFaqs();
      } catch (error) {
        notify(error.message, 'error');
      }
    });
  });
}

function renderFaqDetail(item) {
  if (!item) {
    refs.faqDetail.innerHTML = '<div class="empty-state"><p>Detay için listeden bir FAQ kaydı seçin.</p></div>';
    return;
  }
  const variants = item.question_variants || {};
  refs.faqDetail.innerHTML = `
    <div class="module-header">
      <div>
        <h3>${escapeHtml(item.topic || 'FAQ Detay')}</h3>
        <p>Soru ve cevap aynı panelde incelenir. Durum değişikliği ve kaldırma aksiyonu anında uygulanır.</p>
      </div>
      <span class="pill ${item.status === 'ACTIVE' ? 'open' : (item.status === 'REMOVED' ? 'closed' : 'pending')}">${escapeHtml(item.status || '-')}</span>
    </div>
    <div class="status-list">
      <div class="status-block">
        <h4>Soru (TR)</h4>
        <pre>${escapeHtml(item.question?.tr || '-')}</pre>
      </div>
      <div class="status-block">
        <h4>Soru (EN)</h4>
        <pre>${escapeHtml(item.question?.en || '-')}</pre>
      </div>
      <div class="status-block">
        <h4>Cevap (TR)</h4>
        <pre>${escapeHtml(item.answer?.tr || '-')}</pre>
      </div>
      <div class="status-block">
        <h4>Cevap (EN)</h4>
        <pre>${escapeHtml(item.answer?.en || '-')}</pre>
      </div>
    </div>
    <div class="helper-panel mt-md">
      <div class="helper-box">
        <strong>Varyantlar</strong>
        <p class="mono">TR: ${escapeHtml((variants.tr || []).join(' | ') || '-')}</p>
        <p class="mono">EN: ${escapeHtml((variants.en || []).join(' | ') || '-')}</p>
      </div>
      <div class="helper-box">
        <strong>Yonetim Bilgisi</strong>
        <p class="mono">Guncelleyen: ${escapeHtml(item.updated_by || '-')} · ${escapeHtml(formatDate(item.updated_at) || '-')}</p>
        <p class="mono">Kaldirma: ${escapeHtml(item.removed_reason || '-')}</p>
      </div>
    </div>
  `;
}

async function loadHotelProfileSection() {
  const hotelId = refs.hotelProfileSelect.value || state.selectedHotelId;
  if (!hotelId) {
    refs.hotelProfileEditor.value = '';
    refs.hotelProfileMeta.innerHTML = '<div class="empty-state"><p>Hotel seçin.</p></div>';
    return;
  }
  state.hotelDetail = await apiFetch(`/hotels/${hotelId}`);
  refs.hotelProfileEditor.value = JSON.stringify(state.hotelDetail.profile_json || {}, null, 2);
  refs.hotelProfileMeta.innerHTML = `
    <div class="helper-box">
      <strong>${escapeHtml(state.hotelDetail.name_en || state.hotelDetail.name_tr || 'Hotel')}</strong>
      <p>Dosya kaynağı YAML olarak güncellenir ve runtime cache yenilenir. Bu alan riskli konfigürasyondur.</p>
    </div>
  `;
}

async function saveHotelProfile() {
  const hotelId = refs.hotelProfileSelect.value || state.selectedHotelId;
  if (!hotelId) {
    notify('Hotel seçin.', 'warn');
    return;
  }
  let profileJson;
  try {
    profileJson = JSON.parse(refs.hotelProfileEditor.value);
  } catch (_error) {
    notify('Profile JSON parse edilemedi.', 'error');
    return;
  }
  try {
    const response = await apiFetch(`/hotels/${hotelId}/profile`, {method: 'PUT', body: {profile_json: profileJson}});
    notify(`Profile kaydedildi (${response.profile_path}).`, 'success');
    loadHotelProfileSection();
  } catch (error) {
    notify(error.message, 'error');
  }
}

async function loadRestaurantSlots() {
  const hotelId = state.selectedHotelId;
  if (!hotelId) {
    refs.slotTableBody.innerHTML = '<tr><td colspan="7"><div class="empty-state"><p>Hotel seçin.</p></div></td></tr>';
    if (refs.slotSummaryCards) refs.slotSummaryCards.innerHTML = '';
    return;
  }
  const form = new FormData(refs.slotFilters);
  const params = new URLSearchParams();
  params.set('date_from', String(form.get('date_from') || defaultDate()));
  params.set('date_to', String(form.get('date_to') || defaultDate(7)));
  const response = await apiFetch(`/hotels/${hotelId}/restaurant/slots?${params.toString()}`);
  state.restaurantSlots = response.items || [];
  refs.slotTableBody.innerHTML = renderSlotRows(state.restaurantSlots);
  if (refs.slotSummaryCards) refs.slotSummaryCards.innerHTML = renderSlotSummaryCards(state.restaurantSlots);
  bindSlotActions();
}

function renderSlotSummaryCards(items) {
  if (!items.length) {
    return '<div class="module-card"><div class="empty-state"><p>Grafik için önce slot oluşturun veya filtreyle yükleyin.</p></div></div>';
  }
  const totalCapacity = items.reduce((sum, item) => sum + Number(item.total_capacity || 0), 0);
  const totalBooked = items.reduce((sum, item) => sum + Number(item.booked_count || 0), 0);
  const totalLeft = items.reduce((sum, item) => sum + Number(item.capacity_left || 0), 0);
  const activeCount = items.filter(item => item.is_active).length;
  const passiveCount = items.length - activeCount;
  const firstTime = items.map(item => String(item.time || '')).sort()[0] || '-';
  const lastTime = items.map(item => String(item.time || '')).sort().slice(-1)[0] || '-';
  const usagePct = totalCapacity > 0 ? Math.min(100, Math.round((totalBooked / totalCapacity) * 100)) : 0;
  const freePct = totalCapacity > 0 ? Math.max(0, 100 - usagePct) : 0;
  return `
    <article class="slot-summary-card">
      <h4>Kapasite Grafiği</h4>
      <div class="slot-summary-value">${escapeHtml(String(totalLeft))} boş / ${escapeHtml(String(totalCapacity))}</div>
      <div class="slot-progress" aria-label="Kapasite kullanım grafiği"><div class="slot-progress-bar" style="width:${escapeHtml(String(usagePct))}%"></div></div>
      <div class="slot-summary-meta">Dolu: ${escapeHtml(String(totalBooked))} • Boş yüzdesi: ${escapeHtml(String(freePct))}%</div>
    </article>
    <article class="slot-summary-card">
      <h4>Ne kadar slot kaldı?</h4>
      <div class="slot-summary-value">${escapeHtml(String(totalLeft))}</div>
      <div class="slot-summary-meta">Seçili tarih aralığındaki toplam kalan rezervasyon kapasitesi</div>
      <div class="slot-chip-row"><span class="slot-chip">Toplam ${escapeHtml(String(items.length))} slot</span><span class="slot-chip">${escapeHtml(String(activeCount))} açık</span><span class="slot-chip">${escapeHtml(String(passiveCount))} pasif</span></div>
    </article>
    <article class="slot-summary-card">
      <h4>Rezervasyon Saati</h4>
      <div class="slot-summary-value">${escapeHtml(firstTime)} - ${escapeHtml(lastTime)}</div>
      <div class="slot-summary-meta">Tanımlı kabul penceresi ve oluşturulan slot saatleri</div>
    </article>
  `;
}

function renderSlotRows(items) {
  if (!items.length) {
    return `<tr><td colspan="7"><div class="empty-state"><p>Seçili aralıkta slot yok.</p></div></td></tr>`;
  }
  return items.map(item => `
    <tr>
      <td>${escapeHtml(item.slot_id)}</td>
      <td>${escapeHtml(item.date)}</td>
      <td>${escapeHtml(item.time)}</td>
      <td>${escapeHtml(item.area)}</td>
      <td><strong>${escapeHtml(item.capacity_left)}</strong> kaldı<br><small>${escapeHtml(item.booked_count)} dolu / ${escapeHtml(item.total_capacity)} toplam</small></td>
      <td>${item.is_active ? '<span class="pill open">MİSAFİRE AÇIK</span>' : '<span class="pill closed">PASİF</span>'}</td>
      <td>
        <div class="stack">
          <input type="number" min="1" value="${escapeHtml(item.total_capacity)}" data-slot-capacity="${escapeHtml(item.slot_id)}" aria-label="${escapeHtml(item.slot_id + ' toplam kapasite')}">
          <select data-slot-active="${escapeHtml(item.slot_id)}" aria-label="${escapeHtml(item.slot_id + ' aktiflik durumu')}">
            <option value="true" ${item.is_active ? 'selected' : ''}>Misafire açık</option>
            <option value="false" ${!item.is_active ? 'selected' : ''}>Pasif</option>
          </select>
          <button class="action-button primary" data-save-slot="${escapeHtml(item.slot_id)}" aria-label="${escapeHtml(item.slot_id + ' slotunu guncelle')}">Güncelle</button>
        </div>
      </td>
    </tr>
  `).join('');
}

function bindSlotActions() {
  document.querySelectorAll('[data-save-slot]').forEach(button => {
    button.addEventListener('click', async () => {
      const slotId = button.dataset.saveSlot;
      const capacity = document.querySelector(`[data-slot-capacity="${slotId}"]`).value;
      const isActive = document.querySelector(`[data-slot-active="${slotId}"]`).value === 'true';
      try {
        await apiFetch(`/hotels/${state.selectedHotelId}/restaurant/slots/${slotId}`, {
          method: 'PUT',
          body: {total_capacity: Number(capacity), is_active: isActive},
        });
        notify('Slot güncellendi.', 'success');
        loadRestaurantSlots();
      } catch (error) {
        notify(error.message, 'error');
      }
    });
  });
}

async function onCreateSlot(event) {
  event.preventDefault();
  if (!state.selectedHotelId) {
    notify('Hotel seçin.', 'warn');
    return;
  }
  const formPayload = formToJson(refs.slotCreateForm);
  if (!formPayload.time) {
    notify('Rezervasyon saati zorunlu.', 'warn');
    return;
  }

  const payload = {
    date_from: formPayload.date_from,
    date_to: formPayload.date_to,
    time: formPayload.time,
    area: formPayload.area,
    total_capacity: Number(formPayload.total_capacity),
    is_active: formPayload.is_active === 'on',
  };

  try {
    await apiFetch(`/hotels/${state.selectedHotelId}/restaurant/slots`, {method: 'POST', body: [payload]});
    notify('Rezervasyon saati oluşturuldu.', 'success');
    refs.slotCreateForm.reset();
    loadRestaurantSlots();
  } catch (error) {
    notify(error.message, 'error');
  }
}

async function loadSystemOverview() {
  const [systemOverview, readyState] = await Promise.all([
    apiFetch('/system/overview'),
    apiFetchFromAbsolute(READY_URL),
  ]);
  state.systemOverview = {systemOverview, readyState};
  renderSystemOverview();
}

function renderSystemOverview() {
  if (!state.systemOverview) return;
  const {systemOverview, readyState} = state.systemOverview;
  refs.systemChecks.innerHTML = Object.entries(systemOverview.checks || {}).map(([key, value]) => `
    <div class="status-block">
      <h4>${escapeHtml(key)}</h4>
      <pre>${escapeHtml(JSON.stringify(value, null, 2))}</pre>
    </div>
  `).join('');
  refs.systemMeta.innerHTML = `
    <div class="helper-box">
      <strong>Panel Domain</strong>
      <p>${escapeHtml(systemOverview.panel_url)}</p>
    </div>
    <div class="helper-box">
      <strong>Trusted Hosts</strong>
      <p>${escapeHtml((systemOverview.trusted_hosts || []).join(', '))}</p>
    </div>
    <div class="helper-box">
      <strong>Readiness</strong>
      <p>${escapeHtml(readyState.status || '-')}</p>
    </div>
  `;
}

async function loadSessionPreferences() {
  state.sessionPreferences = await apiFetch('/session/preferences');
  state.sessionStatus = state.sessionPreferences;
  renderSessionPreferences();
  renderLoginSessionState();
}

function renderSessionPreferences() {
  const prefs = state.sessionPreferences || state.sessionStatus;
  if (!prefs) return;

  refs.sessionRememberToggle.checked = Boolean(prefs.has_trusted_device);
  renderChoiceGroup(
    refs.systemVerificationOptions,
    'verification_preset',
    prefs.verification_options || [],
    prefs.verification_preset || '24_hours',
  );
  renderChoiceGroup(
    refs.systemSessionOptions,
    'session_preset',
    prefs.session_options || [],
    prefs.session_preset || '8_hours',
  );
  refs.sessionSummary.innerHTML = `
    <div class="helper-box">
      <strong>Giris hizlandirma</strong>
      <p>${prefs.has_trusted_device ? 'Bu cihaz tanimli. OTP tekrari ve oturum suresi secimleri aktif.' : 'Bu cihaz icin hizli giris kapali. Etkinlestirmek icin switchi acin ve 6 haneli kodu girin.'}</p>
    </div>
    <div class="status-strip">
      <div class="helper-box">
        <strong>Dogrulama tekrar suresi</strong>
        <p>${prefs.has_trusted_device ? escapeHtml(formatDate(prefs.verification_expires_at)) : '-'}</p>
      </div>
      <div class="helper-box">
        <strong>Oturum hatirlama</strong>
        <p>${prefs.has_trusted_device ? escapeHtml(formatDate(prefs.session_expires_at)) : '-'}</p>
      </div>
    </div>
  `;
  refs.trustedDevicePanel.innerHTML = prefs.has_trusted_device ? `
    <div class="helper-box">
      <strong>${escapeHtml(prefs.device_label || 'Tarayici cihazi')}</strong>
      <p>${escapeHtml(prefs.user_label || 'Aktif kullanici')} icin tanimli.</p>
      <div class="detail-list">
        <span>OTP atlama: ${prefs.verification_active ? 'Acik' : 'Kapali'}</span>
        <span>Session restore: ${prefs.session_active ? 'Acik' : 'Kapali'}</span>
        <span>Son dogrulama: ${escapeHtml(formatDate(prefs.last_verified_at))}</span>
      </div>
    </div>
  ` : '<div class="empty-state"><p>Bu cihaz icin kayitli hizli giris bulunmuyor.</p></div>';
  refs.forgetDeviceButton.hidden = !prefs.has_trusted_device;
  toggleSessionPreferenceState();
}

function toggleSessionPreferenceState() {
  const rememberEnabled = refs.sessionRememberToggle.checked;
  refs.sessionOtpField.hidden = !rememberEnabled;
  refs.sessionPreferencesForm.otp_code.required = rememberEnabled;
}

async function onSessionPreferencesSave(event) {
  event.preventDefault();
  const payload = {
    remember_device: refs.sessionRememberToggle.checked,
    verification_preset: getSelectedChoice(refs.sessionPreferencesForm, 'verification_preset', state.sessionPreferences?.verification_preset || '24_hours'),
    session_preset: getSelectedChoice(refs.sessionPreferencesForm, 'session_preset', state.sessionPreferences?.session_preset || '8_hours'),
  };
  const otpCode = String(refs.sessionPreferencesForm.otp_code.value || '').trim();
  if (payload.remember_device) {
    if (!otpCode) {
      notify('Tercihleri kaydetmek icin 6 haneli kod gerekli.', 'warn');
      return;
    }
    payload.otp_code = otpCode;
  }

  try {
    state.sessionPreferences = await apiFetch('/session/preferences', {method: 'PUT', body: payload});
    state.sessionStatus = state.sessionPreferences;
    refs.sessionPreferencesForm.otp_code.value = '';
    renderSessionPreferences();
    renderLoginSessionState();
    notify(payload.remember_device ? 'Cihaz tercihleri kaydedildi.' : 'Bu cihaz icin hizli giris kapatildi.', 'success');
  } catch (error) {
    notify(error.message, 'error');
  }
}

async function forgetTrustedDevice() {
  try {
    state.sessionPreferences = await apiFetch('/session/forget-device', {method: 'POST', body: {}});
    state.sessionStatus = state.sessionPreferences;
    refs.sessionPreferencesForm.otp_code.value = '';
    renderSessionPreferences();
    renderLoginSessionState();
    notify('Bu cihaz artik hatirlanmayacak.', 'success');
  } catch (error) {
    notify(error.message, 'error');
  }
}

function resolveConversationIntent(conversation, messages) {
  if (conversation?.current_intent) return String(conversation.current_intent);
  const assistant = [...(messages || [])].reverse().find(message => message.role === 'assistant');
  const internal = asObject(assistant?.internal_json);
  return String(internal.intent || 'intent yok');
}

function resolveConversationState(conversation, messages) {
  if (conversation?.current_state) return String(conversation.current_state);
  const assistant = [...(messages || [])].reverse().find(message => message.role === 'assistant');
  const internal = asObject(assistant?.internal_json);
  return String(internal.state || '-');
}

function extractLatestUserAudit(messages) {
  const userMessage = [...(messages || [])].reverse().find(message => message.role === 'user');
  const internal = asObject(userMessage?.internal_json);
  const routeAudit = asObject(internal.route_audit);
  return {
    senderProfileName: internal.sender_profile_name || '-',
    waIdMasked: internal.wa_id_masked || '-',
    waMessageId: internal.message_id || '-',
    route: routeAudit.route || '-',
    webhookIp: routeAudit.webhook_ip || '-',
    receivedAt: routeAudit.received_at || '-',
  };
}

function renderUserAuditSection(audit) {
  if (!audit) return '';
  return `
    <div class="audit-grid">
      <div class="helper-box"><strong>Gönderen Profil Adı</strong><p>${escapeHtml(audit.senderProfileName)}</p></div>
      <div class="helper-box"><strong>WA ID (maskeli)</strong><p>${escapeHtml(audit.waIdMasked)}</p></div>
      <div class="helper-box"><strong>WA Message ID</strong><p class="mono">${escapeHtml(audit.waMessageId)}</p></div>
      <div class="helper-box"><strong>Route Audit</strong><p class="mono">${escapeHtml(`${audit.route} | ${audit.webhookIp}`)}</p><p class="muted">${escapeHtml(formatDate(audit.receivedAt))}</p></div>
    </div>
  `;
}

function renderMessageAuditRow(message) {
  if (message.role !== 'user') return '';
  const internal = asObject(message.internal_json);
  if (!internal.message_id && !internal.route_audit) return '';
  const routeAudit = asObject(internal.route_audit);
  return `
    <div class="audit-row muted mono">
      profil=${escapeHtml(internal.sender_profile_name || '-')}
      | wa_id=${escapeHtml(internal.wa_id_masked || '-')}
      | msg_id=${escapeHtml(internal.message_id || '-')}
      | route=${escapeHtml(routeAudit.route || '-')}
      | ip=${escapeHtml(routeAudit.webhook_ip || '-')}
    </div>
  `;
}

async function reloadConfig() {
  try {
    await apiFetch('/reload-config', {method: 'POST', body: {}});
    notify('Konfigürasyon yeniden yüklendi.', 'success');
    loadSystemOverview();
    if (state.currentView === 'hotels') loadHotelProfileSection();
    if (state.currentView === 'faq') loadFaqs();
  } catch (error) {
    notify(error.message, 'error');
  }
}

async function logout() {
  try {
    await apiFetch('/logout', {method: 'POST', body: {}, allowRefresh: false});
  } catch (_error) {
    // UI logout should still continue even if the backend cookie already expired.
  }
  clearClientSession();
  await loadSessionStatus();
  renderLoginSessionState();
  notify('Oturum kapatildi.', 'info');
  showAuth();
}

function clearClientSession() {
  state.me = null;
  state.bootstrapPending = null;
  state.dashboard = null;
  state.conversationDetail = null;
  state.faqs = [];
  state.faqDetail = null;
  state.sessionPreferences = null;
  state.stayProfileRoomTypes = [];
}

async function apiFetch(path, {method = 'GET', body = null, auth = true, allowRefresh = true, logoutOn401 = true} = {}) {
  const headers = {'Content-Type': 'application/json'};
  if (auth && !isSafeMethod(method)) {
    const csrfToken = readCookie(CSRF_COOKIE);
    if (csrfToken) {
      headers['X-CSRF-Token'] = csrfToken;
    }
  }
  let response;
  try {
    response = await fetch(`${API_ROOT}${path}`, {
      method,
      credentials: 'same-origin',
      headers,
      body: body ? JSON.stringify(body) : null,
    });
  } catch (_error) {
    throw new Error('Baglanti sorunu. Lutfen tekrar deneyin.');
  }
  return handleResponse(response, {auth, allowRefresh, logoutOn401, request: {path, method, body}});
}

async function apiFetchFromAbsolute(path) {
  let response;
  try {
    response = await fetch(path, {credentials: 'same-origin'});
  } catch (_error) {
    throw new Error('Baglanti sorunu. Lutfen tekrar deneyin.');
  }
  return handleResponse(response, {auth: false, allowRefresh: false, logoutOn401: false, request: null});
}

async function handleResponse(response, options) {
  let payload = {};
  try {
    payload = await response.json();
  } catch (_error) {
    payload = {};
  }
  if (!response.ok) {
    if (options.auth && response.status === 401 && options.allowRefresh) {
      const refreshed = await refreshAccessSession({silent: true});
      if (refreshed && options.request) {
        return apiFetch(options.request.path, {
          method: options.request.method,
          body: options.request.body,
          auth: true,
          allowRefresh: false,
          logoutOn401: options.logoutOn401,
        });
      }
    }
    if (options.auth && response.status === 401 && options.logoutOn401) {
      clearClientSession();
      await loadSessionStatus();
      showAuth();
    }
    throw new Error(extractErrorMessage(payload));
  }
  return payload;
}

async function refreshAccessSession({silent = false} = {}) {
  if (state.refreshPromise) {
    return state.refreshPromise;
  }
  state.refreshPromise = (async () => {
    try {
      await apiFetch('/session/refresh', {method: 'POST', body: {}, auth: false, allowRefresh: false, logoutOn401: false});
      await loadSessionStatus();
      return true;
    } catch (error) {
      if (!silent) {
        notify(error.message, 'warn');
      }
      await loadSessionStatus();
      return false;
    } finally {
      state.refreshPromise = null;
    }
  })();
  return state.refreshPromise;
}

// extractErrorMessage wraps shared extractErrorDetail for admin panel compat
function extractErrorMessage(payload) {
  return extractErrorDetail(payload, '');
}

function getSelectedChoice(form, name, fallback) {
  const field = form.querySelector(`input[name="${name}"]:checked`);
  return field ? field.value : fallback;
}

function notify(message, tone = 'info') {
  refs.toast.textContent = message;
  refs.toast.className = `toast ${tone} is-visible`;
  window.clearTimeout(notify.timer);
  notify.timer = window.setTimeout(() => refs.toast.className = `toast ${tone}`, 2800);
}

// ---------------------------------------------------------------------------
// Notification phones
// ---------------------------------------------------------------------------

async function loadNotifPhones() {
  try {
    const phones = await apiFetch('/notification-phones');
    renderNotifPhones(phones);
  } catch (err) {
    notify('Bildirim numaralari yuklenemedi: ' + (err.message || err), 'error');
  }
}

function renderNotifPhones(phones) {
  if (!refs.notifPhoneTableBody) return;
  if (!phones || !phones.length) {
    refs.notifPhoneTableBody.innerHTML = '<tr><td colspan="4"><div class="empty-state"><p>Kayit yok</p></div></td></tr>';
    return;
  }
  refs.notifPhoneTableBody.innerHTML = phones.map(p => {
    const isDefault = p.is_default;
    const removeBtn = isDefault
      ? '<span class="badge dark">Varsayilan</span>'
      : `<button class="inline-button danger" data-remove-phone="${escapeHtml(p.phone)}" aria-label="${escapeHtml((p.label || p.phone) + ' bildirim numarasini kaldir')}">Kaldir</button>`;
    return `<tr>
      <td><code>${escapeHtml(p.phone)}</code></td>
      <td>${escapeHtml(p.label || '-')}</td>
      <td>${isDefault ? 'Evet' : 'Hayir'}</td>
      <td>${removeBtn}</td>
    </tr>`;
  }).join('');
  bindNotifPhoneActions();
}

function bindNotifPhoneActions() {
  document.querySelectorAll('[data-remove-phone]').forEach(button => {
    button.addEventListener('click', () => removeNotifPhone(button.dataset.removePhone));
  });
}

async function onAddNotifPhone(event) {
  event.preventDefault();
  const form = refs.addNotifPhoneForm;
  const phone = form.phone.value.trim();
  const label = form.label.value.trim();
  if (!phone) return;
  try {
    await apiFetch('/notification-phones', {method: 'POST', body: {phone, label}});
    notify('Numara eklendi', 'success');
    form.reset();
    await loadNotifPhones();
  } catch (err) {
    notify('Numara eklenemedi: ' + (err.message || err), 'error');
  }
}

async function removeNotifPhone(phone) {
  if (!confirm('Bu numarayi kaldirmak istediginize emin misiniz?')) return;
  const encoded = phone.replace('+', '_');
  try {
    await apiFetch('/notification-phones/' + encoded, {method: 'DELETE'});
    notify('Numara kaldirildi', 'success');
    await loadNotifPhones();
  } catch (err) {
    notify('Numara kaldirilamadi: ' + (err.message || err), 'error');
  }
}
"""
