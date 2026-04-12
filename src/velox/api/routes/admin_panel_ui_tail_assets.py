"""Tail script sections for the admin operations panel."""

# ruff: noqa: E501

ADMIN_PANEL_TAIL_SCRIPT = """\
async function loadFaqs() {
  const hotelId = state.selectedHotelId;
  if (!hotelId) {
    refs.faqTableBody.innerHTML = '<tr><td colspan="5"><div class="empty-state"><p>Önce bir otel seçin.</p></div></td></tr>';
    refs.faqDetail.innerHTML = '<div class="empty-state"><p>Ayrıntıları görmek için listeden bir SSS kaydı seçin.</p></div>';
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
    refs.faqDetail.innerHTML = '<div class="empty-state"><p>Ayrıntıları görmek için listeden bir SSS kaydı seçin.</p></div>';
  } else {
    renderFaqDetail(state.faqDetail);
  }
}

function renderFaqRows(items) {
  if (!items.length) {
    return '<tr><td colspan="5"><div class="empty-state"><p>Filtreyle eşleşen bir SSS kaydı bulunamadı.</p></div></td></tr>';
  }
  return items.map(item => {
    const pillClass = item.status === 'ACTIVE' ? 'open' : (item.status === 'REMOVED' ? 'closed' : 'pending');
    const questionPreview = `${item.question?.tr || '-'} / ${item.question?.en || '-'}`;
    const answerPreview = `${item.answer?.tr || '-'} / ${item.answer?.en || '-'}`;
    return `
      <tr>
        <td><strong>${escapeHtml(item.topic || '-')}</strong></td>
        <td><span class="pill ${pillClass}">${escapeHtml(formatFaqStatus(item.status || '-'))}</span></td>
        <td><span class="muted">${escapeHtml(questionPreview).slice(0, 180)}</span></td>
        <td><span class="muted">${escapeHtml(answerPreview).slice(0, 180)}</span></td>
        <td>
          <div class="stack">
            <button class="action-button primary" data-faq-open="${escapeHtml(item.faq_id)}" aria-label="${escapeHtml((item.topic || 'SSS') + ' ayrıntılarını aç')}">Detay</button>
            ${item.status === 'ACTIVE'
              ? `<button class="action-button warn" data-faq-status="${escapeHtml(item.faq_id)}" data-next-status="PAUSED" aria-label="${escapeHtml((item.topic || 'SSS') + ' kaydını pasife al')}">Pasife Al</button>`
              : ''}
            ${(item.status === 'PAUSED' || item.status === 'DRAFT')
              ? `<button class="action-button primary" data-faq-status="${escapeHtml(item.faq_id)}" data-next-status="ACTIVE" aria-label="${escapeHtml((item.topic || 'SSS') + ' kaydını etkinleştir')}">Aktif Et</button>`
              : ''}
            ${item.status !== 'REMOVED'
              ? `<button class="action-button danger" data-faq-remove="${escapeHtml(item.faq_id)}" aria-label="${escapeHtml((item.topic || 'SSS') + ' kaydını kaldır')}">Kaldır</button>`
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
        notify(`SSS durumu ${formatFaqStatus(nextStatus)} olarak güncellendi.`, 'success');
        await loadFaqs();
      } catch (error) {
        notify(error.message, 'error');
      }
    });
  });

  document.querySelectorAll('[data-faq-remove]').forEach(button => {
    button.addEventListener('click', async () => {
      const faqId = button.dataset.faqRemove;
      const reason = window.prompt('Kaldırma gerekçesini yazın:');
      if (!reason || !reason.trim()) {
        notify('Kaldırma gerekçesi zorunludur.', 'warn');
        return;
      }
      try {
        await apiFetch(`/hotels/${state.selectedHotelId}/faq/${faqId}`, {
          method: 'DELETE',
          body: {reason: reason.trim()},
        });
        notify('SSS kaydı hemen kaldırıldı.', 'success');
        await loadFaqs();
      } catch (error) {
        notify(error.message, 'error');
      }
    });
  });
}

function renderFaqDetail(item) {
  if (!item) {
    refs.faqDetail.innerHTML = '<div class="empty-state"><p>Ayrıntıları görmek için listeden bir SSS kaydı seçin.</p></div>';
    return;
  }
  const variants = item.question_variants || {};
  refs.faqDetail.innerHTML = `
    <div class="module-header">
      <div>
        <h3>${escapeHtml(item.topic || 'SSS Ayrıntısı')}</h3>
        <p>Soru ve cevaplar aynı panelde incelenir. Durum değişikliği ve kaldırma işlemi anında uygulanır.</p>
      </div>
      <span class="pill ${item.status === 'ACTIVE' ? 'open' : (item.status === 'REMOVED' ? 'closed' : 'pending')}">${escapeHtml(formatFaqStatus(item.status || '-'))}</span>
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
        <strong>Yönetim Bilgisi</strong>
        <p class="mono">Güncelleyen: ${escapeHtml(item.updated_by || '-')} · ${escapeHtml(formatDate(item.updated_at) || '-')}</p>
        <p class="mono">Kaldırma nedeni: ${escapeHtml(item.removed_reason || '-')}</p>
      </div>
    </div>
  `;
}

async function loadHotelProfileSection() {
  const hotelId = refs.hotelProfileSelect.value || state.selectedHotelId;
  if (!hotelId) {
    refs.hotelProfileEditor.value = '';
    refs.hotelProfileMeta.innerHTML = '<div class="empty-state"><p>Önce bir otel seçin.</p></div>';
    refs.hotelProfileSections.innerHTML = '<div class="empty-state"><p>Bölümleri görüntülemek için bir otel seçin.</p></div>';
    refs.hotelProfileSectionBody.innerHTML = '<div class="empty-state"><p>Dinamik düzenleyici burada görüntülenir.</p></div>';
    refs.hotelFactsConflict.innerHTML = '<div class="empty-state"><p>Çakışma ayrıntıları burada görüntülenir.</p></div>';
    refs.hotelFactsStatus.innerHTML = '<div class="empty-state"><p>Veri sürümü durumunu görmek için bir otel seçin.</p></div>';
    refs.hotelFactsHistory.innerHTML = '<div class="empty-state"><p>Yayın geçmişini görmek için bir otel seçin.</p></div>';
    refs.hotelFactsEvents.innerHTML = '<div class="empty-state"><p>Denetim kayıtlarını görmek için bir otel seçin.</p></div>';
    renderHotelFactsVersionDetail(null);
    state.hotelProfileDraft = null;
    state.hotelProfileLoadedSourceChecksum = null;
    state.hotelProfileLoadedDraftSnapshot = null;
    state.hotelProfileHasUnsavedChanges = false;
    state.hotelFactsConflict = null;
    state.hotelFactsStatus = null;
    state.hotelFactsDraftValidation = null;
    state.hotelFactsVersions = [];
    state.hotelFactsEvents = [];
    state.hotelFactsVersionDetail = null;
    state.hotelFactsApiUnavailable = false;
    renderHotelProfileMeta();
    if (refs.publishHotelFacts) refs.publishHotelFacts.disabled = true;
    if (refs.saveHotelProfile) refs.saveHotelProfile.disabled = true;
    return;
  }
  const hotelDetail = await apiFetch(`/hotels/${hotelId}`);
  const factsResults = await Promise.allSettled([
    apiFetch(`/hotels/${hotelId}/facts/status`),
    apiFetch(`/hotels/${hotelId}/facts/versions`),
    apiFetch(`/hotels/${hotelId}/facts/events`),
  ]);
  const missingFactsApi = factsResults.some(result => (
    result.status === 'rejected' && Number(result.reason?.status) === 404
  ));
  const criticalFactsError = factsResults.find(result => (
    result.status === 'rejected' && Number(result.reason?.status) !== 404
  ));
  if (criticalFactsError?.status === 'rejected') {
    throw criticalFactsError.reason;
  }

  state.hotelDetail = hotelDetail;
  if (missingFactsApi) {
    state.hotelFactsApiUnavailable = true;
    state.hotelFactsStatus = buildLegacyHotelFactsStatus(hotelDetail);
    state.hotelFactsVersions = [];
    state.hotelFactsEvents = [];
  } else {
    state.hotelFactsApiUnavailable = false;
    const statusResult = factsResults[0];
    const versionsResult = factsResults[1];
    const eventsResult = factsResults[2];
    state.hotelFactsStatus = statusResult.status === 'fulfilled' ? statusResult.value : null;
    state.hotelFactsVersions = versionsResult.status === 'fulfilled' && Array.isArray(versionsResult.value?.items)
      ? versionsResult.value.items
      : [];
    state.hotelFactsEvents = eventsResult.status === 'fulfilled' && Array.isArray(eventsResult.value?.items)
      ? eventsResult.value.items
      : [];
  }
  state.hotelProfileDraft = normalizeHotelProfileDraft(state.hotelDetail.profile_json || {});
  state.hotelProfileLoadedSourceChecksum = state.hotelFactsStatus?.draft_source_profile_checksum || null;
  state.hotelFactsDraftValidation = buildHotelFactsDraftValidationFromStatus(state.hotelFactsStatus);
  state.hotelProfileFaqActiveIndex = 0;
  syncHotelProfileEditorFromDraft();
  state.hotelProfileLoadedDraftSnapshot = refs.hotelProfileEditor.value;
  state.hotelProfileHasUnsavedChanges = false;
  renderHotelProfileMeta();
  renderHotelProfileWorkspace();
  renderHotelFactsConflict(state.hotelFactsConflict);
  renderHotelFactsStatus(state.hotelFactsStatus);
  renderHotelFactsHistory(state.hotelFactsVersions);
  renderHotelFactsEvents(state.hotelFactsEvents);
  const preferredVersion = resolvePreferredHotelFactsVersion(state.hotelFactsVersions);
  if (preferredVersion != null) {
    await loadHotelFactsVersionDetail(preferredVersion, {silent: true});
  } else {
    state.hotelFactsVersionDetail = null;
    renderHotelFactsVersionDetail(null);
  }
}

function buildLegacyHotelFactsStatus(hotelDetail) {
  return {
    state: 'in_sync',
    current_version: null,
    published_by: 'legacy_profile_store',
    published_at: hotelDetail?.updated_at || null,
    draft_facts_checksum: null,
    current_facts_checksum: null,
    draft_source_profile_checksum: null,
    draft_matches_runtime: true,
    draft_publishable: true,
    blockers: [],
    warnings: [],
  };
}

function renderHotelProfileMeta() {
  if (!refs.hotelProfileMeta) return;
  if (!state.hotelDetail) {
    refs.hotelProfileMeta.innerHTML = '<div class="empty-state"><p>Önce bir otel seçin.</p></div>';
    return;
  }
  if (refs.saveHotelProfile) refs.saveHotelProfile.textContent = 'Taslağı Kaydet';
  if (refs.publishHotelFacts) refs.publishHotelFacts.textContent = 'Değişiklikleri Yayına Al';
  const name = state.hotelDetail.name_en || state.hotelDetail.name_tr || 'Otel';
  const dirty = Boolean(state.hotelProfileHasUnsavedChanges);
  const localValidation = getHotelFactsDraftValidation();
  const publishable = Boolean(localValidation?.publishable);
  const statusPillClass = dirty ? 'warn' : 'success';
  const statusPillText = dirty ? 'Taslakta kaydedilmemiş değişiklikler var' : 'Taslak düzenleyici güncel';
  const guidance = dirty
    ? 'Önce taslağı kaydedin, ardından isterseniz değişiklikleri yayına alın.'
    : 'Bu ekrandaki değişiklikler önce taslağa kaydedilir. Misafirlere yalnızca yayına alınan bilgiler gösterilir.';
  const validationLabel = publishable ? 'Yayına alınabilir' : 'Yayına almadan önce düzeltin';
  const modeLabel = isHotelProfileTechnicalMode() ? 'Teknik ayarlar açık' : 'Standart düzenleme açık';
  refs.hotelProfileMeta.innerHTML = `
    <div class="helper-box">
      <strong>${escapeHtml(name)}</strong>
      <p>${escapeHtml(guidance)}</p>
      <div class="profile-summary-strip mt-sm">
        <span class="pill ${statusPillClass}">${escapeHtml(statusPillText)}</span>
        <span class="profile-summary-chip">Yayın kontrolü: ${escapeHtml(validationLabel)}</span>
        <span class="profile-summary-chip">Mod: ${escapeHtml(modeLabel)}</span>
      </div>
      ${isHotelProfileTechnicalMode()
        ? `<p class="mono">Otel kimliği: ${escapeHtml(String(state.hotelDetail.hotel_id || '-'))}</p>`
        : '<p class="muted">Teknik kimlik ve eşleştirme alanları yalnızca Teknik Ayarlar modunda görünür.</p>'}
    </div>
  `;
}

async function saveHotelProfile() {
  if (document.activeElement instanceof HTMLElement) {
    document.activeElement.blur();
  }
  const hotelId = refs.hotelProfileSelect.value || state.selectedHotelId;
  if (!hotelId) {
    notify('Lütfen bir otel seçin.', 'warn');
    return;
  }
  if (!state.hotelProfileHasUnsavedChanges) {
    notify('Kaydedilecek yeni bir değişiklik yok.', 'info');
    return;
  }
  let profileJson;
  const localEditorSnapshot = refs.hotelProfileEditor.value;
  try {
    profileJson = JSON.parse(refs.hotelProfileEditor.value);
  } catch (_error) {
    notify('Profil JSON verisi ayrıştırılamadı.', 'error');
    return;
  }
  try {
    const response = await apiFetch(`/hotels/${hotelId}/profile`, {
      method: 'PUT',
      body: {
        profile_json: profileJson,
        expected_source_profile_checksum: state.hotelProfileLoadedSourceChecksum || null,
      },
    });
    clearHotelFactsConflict();
    state.hotelFactsStatus = response.facts_status || null;
    renderHotelFactsStatus(state.hotelFactsStatus);
    notify(buildHotelProfileSaveMessage(response), resolveHotelFactsTone(response.facts_status), 4200);
    await loadHotelProfileSection();
  } catch (error) {
    if (error?.status === 409) {
      await loadHotelProfileSection();
      setHotelFactsConflict(buildHotelFactsConflict(error, {
        action: 'save',
        localEditorSnapshot,
      }));
    }
    notify(error.message, 'error');
  }
}

function clearHotelFactsConflict() {
  state.hotelFactsConflict = null;
  renderHotelFactsConflict(null);
}

function setHotelFactsConflict(conflict) {
  state.hotelFactsConflict = conflict;
  renderHotelFactsConflict(conflict);
}

function renderHotelFactsConflict(conflict) {
  if (!refs.hotelFactsConflict) return;
  if (!conflict || Number(conflict.hotelId || 0) !== Number(state.selectedHotelId || refs.hotelProfileSelect?.value || 0)) {
    refs.hotelFactsConflict.innerHTML = '<div class="empty-state"><p>Çakışma ayrıntıları burada görüntülenir.</p></div>';
    return;
  }

  const items = Array.isArray(conflict.diffSummary?.items) ? conflict.diffSummary.items : [];
  const remainingCount = Number(conflict.diffSummary?.remainingCount || 0);
  const itemMarkup = items.length
    ? items.map(item => `<span>• ${escapeHtml(item.path || '-')}: ${escapeHtml(item.label || '-')}</span>`).join('')
    : '<span>• Alan ozeti yok</span>';
  const canRestoreLocalDraft = Boolean(conflict.localEditorSnapshot);
  const currentVersionButton = conflict.currentVersion
    ? `<button class="action-button secondary" type="button" data-facts-version-detail="${escapeHtml(String(conflict.currentVersion))}">Aktif Sürümü Aç</button>`
    : '';
  const restoreButton = canRestoreLocalDraft
    ? '<button class="action-button warn" type="button" data-facts-conflict-restore-draft="true">Yerel Taslağı Geri Yükle</button>'
    : '';
  const checksumDetails = conflict.code === 'hotel_facts_rollback_conflict'
    ? `
        <p class="mono">Beklenen aktif sürüm: ${escapeHtml(conflict.expectedCurrentVersion != null ? `v${String(conflict.expectedCurrentVersion)}` : '-')}</p>
        <p class="mono">Güncel aktif sürüm: ${escapeHtml(conflict.currentVersion != null ? `v${String(conflict.currentVersion)}` : '-')}</p>
      `
    : `
        <p class="mono">Beklenen taslak checksum: ${escapeHtml(conflict.expectedSourceProfileChecksum || '-')}</p>
        <p class="mono">Güncel taslak checksum: ${escapeHtml(conflict.currentSourceProfileChecksum || '-')}</p>
      `;
  const summaryDetails = conflict.code === 'hotel_facts_rollback_conflict'
    ? '<p class="muted">Panel son yayın durumunu yeniden yükledi. Aktif sürümü açıp kararınızı tekrar verebilirsiniz.</p>'
    : `
        <p class="muted">Panel sunucudaki taslağı yeniden yükledi. İsterseniz yerel taslağı düzenleyiciye geri alıp değişiklikleri elle birleştirebilirsiniz.</p>
        <p class="mono">Farklı alan sayısı: ${escapeHtml(String(conflict.diffSummary?.totalCount || 0))}</p>
        <p class="mono">Etkilenen kök alan sayısı: ${escapeHtml(String(conflict.diffSummary?.rootPathCount || 0))}</p>
      `;
  const footerNote = remainingCount > 0
    ? `<p class="muted mt-sm">İlk ${escapeHtml(String(items.length))} fark gösteriliyor. ${escapeHtml(String(remainingCount))} ek alan daha var.</p>`
    : '';

  refs.hotelFactsConflict.innerHTML = `
    <div class="helper-box">
      <strong>${escapeHtml(conflict.title)}</strong>
      <p>${escapeHtml(conflict.message || 'Conflict algilandi.')}</p>
      ${checksumDetails}
      ${summaryDetails}
      <div class="module-actions mt-sm">
        ${restoreButton}
        ${currentVersionButton}
        <button class="action-button secondary" type="button" data-facts-conflict-dismiss="true">Kapat</button>
      </div>
    </div>
    <div class="helper-box">
      <strong>Fark Özeti</strong>
      <div class="detail-list">${itemMarkup}</div>
      ${footerNote}
    </div>
  `;
}

function buildHotelFactsConflict(error, {action, localEditorSnapshot = ''} = {}) {
  const detail = asObject(error?.payload?.detail);
  if (!detail.code) return null;
  const diffSummary = summarizeHotelProfileTopLevelDiff(localEditorSnapshot, refs.hotelProfileEditor?.value || '');
  return {
    action: action || 'unknown',
    code: String(detail.code || ''),
    title: resolveHotelFactsConflictTitle(detail.code),
    message: String(detail.message || error?.message || 'Conflict algilandi.'),
    hotelId: Number(detail.hotel_id || state.selectedHotelId || refs.hotelProfileSelect?.value || 0),
    expectedSourceProfileChecksum: detail.expected_source_profile_checksum || null,
    currentSourceProfileChecksum: detail.current_source_profile_checksum || null,
    expectedCurrentVersion: detail.expected_current_version ?? null,
    currentVersion: detail.current_version ?? state.hotelFactsStatus?.current_version ?? null,
    localEditorSnapshot,
    diffSummary,
  };
}

function resolveHotelFactsConflictTitle(code) {
  switch (String(code || '')) {
    case 'hotel_profile_conflict':
      return 'Taslak Kaydetme Çakışması';
    case 'hotel_facts_publish_conflict':
      return 'Yayımlama Çakışması';
    case 'hotel_facts_rollback_conflict':
      return 'Geri Alma Çakışması';
    default:
      return 'Veri Sürümü Çakışması';
  }
}

function summarizeHotelProfileTopLevelDiff(localSnapshot, serverSnapshot) {
  const localParsed = parseEditorJson(localSnapshot);
  const serverParsed = parseEditorJson(serverSnapshot);
  if (!localParsed.ok || !serverParsed.ok) {
    return {
      parseable: false,
      totalCount: 0,
      rootPathCount: 0,
      remainingCount: 0,
      items: [],
    };
  }

  const allItems = diffJsonValues(localParsed.value, serverParsed.value);
  const visibleItems = allItems.slice(0, 10);
  const rootPathCount = new Set(allItems.map(item => extractRootPath(item.path))).size;
  return {
    parseable: true,
    totalCount: allItems.length,
    rootPathCount,
    remainingCount: Math.max(0, allItems.length - visibleItems.length),
    items: visibleItems,
  };
}

function diffJsonValues(localValue, serverValue, path = '') {
  if (JSON.stringify(localValue) === JSON.stringify(serverValue)) {
    return [];
  }

  const currentPath = path || '(root)';
  if (isPlainObject(localValue) && isPlainObject(serverValue)) {
    const keys = Array.from(new Set([
      ...Object.keys(localValue),
      ...Object.keys(serverValue),
    ])).sort();
    const items = [];
    keys.forEach(key => {
      items.push(...diffJsonValues(
        localValue[key],
        serverValue[key],
        path ? `${path}.${key}` : key,
      ));
    });
    return items.length ? items : [{path: currentPath, label: 'Obje icerigi farkli'}];
  }

  if (Array.isArray(localValue) && Array.isArray(serverValue)) {
    if (localValue.length !== serverValue.length) {
      return [{
        path: currentPath,
        label: `Liste boyutu farkli (${localValue.length} / ${serverValue.length})`,
      }];
    }
    return [{path: currentPath, label: 'Liste icerigi farkli'}];
  }

  if (typeof localValue === 'undefined') {
    return [{path: currentPath, label: 'Sunucuda eklendi'}];
  }
  if (typeof serverValue === 'undefined') {
    return [{path: currentPath, label: 'Sunucudan kaldirildi'}];
  }
  if (valueKind(localValue) !== valueKind(serverValue)) {
    return [{
      path: currentPath,
      label: `Tip farkli (${valueKind(localValue)} / ${valueKind(serverValue)})`,
    }];
  }

  return [{
    path: currentPath,
    label: `Yerel ${previewDiffValue(localValue)} / Sunucu ${previewDiffValue(serverValue)}`,
  }];
}

function isPlainObject(value) {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function valueKind(value) {
  if (Array.isArray(value)) return 'array';
  if (value === null) return 'null';
  return typeof value;
}

function previewDiffValue(value) {
  if (value === null) return 'null';
  if (typeof value === 'string') {
    return truncateDiffPreview(`"${value}"`);
  }
  if (typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }
  if (Array.isArray(value)) {
    return `[${value.length}]`;
  }
  if (isPlainObject(value)) {
    return `{${Object.keys(value).length} alan}`;
  }
  return truncateDiffPreview(String(value));
}

function truncateDiffPreview(value) {
  return value.length > 44 ? `${value.slice(0, 41)}...` : value;
}

function cssEscapeValue(value) {
  return JSON.stringify(String(value || '')).slice(1, -1);
}

function extractRootPath(path) {
  if (!path || path === '(root)') return '(root)';
  return String(path).split(/[.[]/, 1)[0] || '(root)';
}

function parseEditorJson(snapshot) {
  if (typeof snapshot !== 'string' || !snapshot.trim()) {
    return {ok: false, value: null};
  }
  try {
    return {ok: true, value: JSON.parse(snapshot)};
  } catch (_error) {
    return {ok: false, value: null};
  }
}

function restoreHotelFactsConflictDraft() {
  const snapshot = state.hotelFactsConflict?.localEditorSnapshot;
  if (!snapshot) {
    notify('Geri yüklenecek yerel taslak bulunamadı.', 'warn');
    return;
  }
  refs.hotelProfileEditor.value = snapshot;
  const parsed = parseEditorJson(snapshot);
  if (parsed.ok) {
    state.hotelProfileDraft = normalizeHotelProfileDraft(parsed.value);
    renderHotelProfileWorkspace();
    scheduleHotelFactsDraftValidation({immediate: true, silent: true});
  }
  notify('Yerel taslak düzenleyiciye geri yüklendi. Kaydetmeden önce farkları gözden geçirin.', 'warn');
}

function dismissHotelFactsConflict() {
  clearHotelFactsConflict();
}

function applyHotelProfileJsonToForm() {
  const parsed = parseEditorJson(refs.hotelProfileEditor?.value || '');
  if (!parsed.ok) {
    notify('Ham JSON ayrıştırılamadı. Önce JSON hatalarını düzeltin.', 'error');
    return;
  }
  state.hotelProfileDraft = normalizeHotelProfileDraft(parsed.value);
  renderHotelProfileWorkspace();
  scheduleHotelFactsDraftValidation({immediate: true, silent: true});
  notify('Ham JSON form alanlarına aktarıldı.', 'success');
}

const HOTEL_PROFILE_SECTIONS = [
  {id: 'general', label: 'Genel'},
  {id: 'contacts', label: 'İletişim ve Konum'},
  {id: 'rooms', label: 'Odalar'},
  {id: 'pricing', label: 'Pansiyon ve Fiyat'},
  {id: 'transfers', label: 'Transfer'},
  {id: 'restaurant', label: 'Restoran'},
  {id: 'faq', label: 'SSS'},
  {id: 'policies', label: 'Politikalar'},
  {id: 'idle_reset', label: 'Konuşma Sıfırlama'},
  {id: 'assistant', label: 'Yapay Zekâ Akışı', technicalOnly: true},
];

const HOTEL_TYPE_OPTIONS = [
  {value: 'boutique', label: 'Butik otel'},
  {value: 'resort', label: 'Resort otel'},
  {value: 'city', label: 'Şehir oteli'},
  {value: 'villa', label: 'Villa / özel konaklama'},
];

const HIGHLIGHT_OPTIONS = [
  {value: 'beachside', label: 'Plaja yakın'},
  {value: 'central_location', label: 'Merkezi konum'},
  {value: 'excellent_reviews', label: 'Yüksek misafir puanı'},
  {value: 'pool_jacuzzi', label: 'Havuz ve jakuzi'},
  {value: 'family_friendly', label: 'Aile dostu'},
  {value: 'regional_breakfast', label: 'Bölgesel kahvaltı'},
];

const CONTACT_ROLE_OPTIONS = [
  {value: '', label: 'Rol seçin'},
  {value: 'RECEPTION', label: 'Resepsiyon'},
  {value: 'RESTAURANT', label: 'Restoran'},
  {value: 'HOUSEKEEPING', label: 'Kat hizmetleri'},
  {value: 'ADMIN', label: 'Yönetici'},
  {value: 'OTHER', label: 'Diğer'},
];

const CONTACT_PRESET_OPTIONS = [
  {preset: 'RECEPTION', label: 'Resepsiyon Ekle', key: 'reception', name: 'Resepsiyon', role: 'RECEPTION'},
  {preset: 'RESTAURANT', label: 'Restoran Ekle', key: 'restaurant', name: 'Restoran', role: 'RESTAURANT'},
  {preset: 'HOUSEKEEPING', label: 'Kat Hizmetleri Ekle', key: 'housekeeping', name: 'Kat hizmetleri', role: 'HOUSEKEEPING'},
  {preset: 'ADMIN', label: 'Yönetici Ekle', key: 'escalation_admin', name: 'Yönetici', role: 'ADMIN'},
  {preset: 'OTHER', label: 'Diğer İletişim', key: 'contact', name: '', role: 'OTHER'},
];

const CURRENCY_OPTIONS = [
  {value: 'EUR', label: 'Euro (EUR)'},
  {value: 'USD', label: 'ABD Doları (USD)'},
  {value: 'TRY', label: 'Türk Lirası (TRY)'},
  {value: 'GBP', label: 'İngiliz Sterlini (GBP)'},
];

const TIMEZONE_OPTIONS = [
  {value: 'Europe/Istanbul', label: 'Türkiye saati (Europe/Istanbul)'},
  {value: 'UTC', label: 'UTC'},
  {value: 'Europe/London', label: 'Londra saati (Europe/London)'},
  {value: 'Europe/Berlin', label: 'Berlin saati (Europe/Berlin)'},
];

const BOARD_TYPE_OPTIONS = [
  {value: 'RO', label: 'Sadece Oda'},
  {value: 'BB', label: 'Oda + Kahvaltı'},
  {value: 'HB', label: 'Yarım Pansiyon'},
  {value: 'FB', label: 'Tam Pansiyon'},
  {value: 'AI', label: 'Her Şey Dahil'},
];

const BOARD_TYPE_PRESET_OPTIONS = [
  {preset: 'RO', label: 'Sadece Oda', nameTr: 'Sadece Oda', nameEn: 'Room Only', breakfastHours: '', breakfastType: ''},
  {preset: 'BB', label: 'Oda + Kahvaltı', nameTr: 'Oda + Kahvaltı', nameEn: 'Bed & Breakfast', breakfastHours: '08:00-10:30', breakfastType: 'acik_buyfe'},
  {preset: 'HB', label: 'Yarım Pansiyon', nameTr: 'Yarım Pansiyon', nameEn: 'Half Board', breakfastHours: '08:00-10:30', breakfastType: 'acik_buyfe'},
  {preset: 'FB', label: 'Tam Pansiyon', nameTr: 'Tam Pansiyon', nameEn: 'Full Board', breakfastHours: '08:00-10:30', breakfastType: 'acik_buyfe'},
  {preset: 'AI', label: 'Her Şey Dahil', nameTr: 'Her Şey Dahil', nameEn: 'All Inclusive', breakfastHours: '07:30-10:30', breakfastType: 'acik_buyfe'},
];

const BREAKFAST_TYPE_OPTIONS = [
  {value: 'acik_buyfe', label: 'Açık büfe'},
  {value: 'set_menu', label: 'Set menü'},
  {value: 'a_la_carte', label: 'A la carte'},
];

const BED_TYPE_OPTIONS = [
  {value: 'king', label: 'King yatak'},
  {value: 'queen', label: 'Queen yatak'},
  {value: 'double', label: 'Çift kişilik yatak'},
  {value: 'twin', label: 'İki ayrı yatak'},
  {value: 'sofa_bed', label: 'Açılır kanepe'},
];

const ROOM_VIEW_OPTIONS = [
  {value: 'garden', label: 'Bahçe manzarası'},
  {value: 'pool', label: 'Havuz manzarası'},
  {value: 'street', label: 'Cadde / çevre manzarası'},
  {value: 'pool_mountain', label: 'Havuz ve dağ manzarası'},
  {value: 'pool_garden', label: 'Havuz ve bahçe manzarası'},
];

const ROOM_TYPE_PRESET_OPTIONS = [
  {
    preset: 'STANDARD',
    label: 'Standart Oda',
    defaults: {
      name: {tr: 'Standart Oda', en: 'Standard Room'},
      max_pax: 2,
      size_m2: 22,
      bed_type: 'queen',
      view: 'garden',
      features: [],
      extra_bed: false,
      baby_crib: false,
      accessible: false,
    },
  },
  {
    preset: 'SUPERIOR',
    label: 'Superior Oda',
    defaults: {
      name: {tr: 'Superior Oda', en: 'Superior Room'},
      max_pax: 3,
      size_m2: 28,
      bed_type: 'king',
      view: 'pool',
      features: ['modern'],
      extra_bed: true,
      baby_crib: true,
      accessible: false,
    },
  },
  {
    preset: 'FAMILY',
    label: 'Aile Odası',
    defaults: {
      name: {tr: 'Aile Odası', en: 'Family Room'},
      max_pax: 4,
      size_m2: 35,
      bed_type: 'king',
      view: 'garden',
      features: ['spacious'],
      extra_bed: true,
      baby_crib: true,
      accessible: false,
    },
  },
  {
    preset: 'SUITE',
    label: 'Suit',
    defaults: {
      name: {tr: 'Suit', en: 'Suite'},
      max_pax: 4,
      size_m2: 40,
      bed_type: 'king',
      view: 'pool',
      features: ['spacious'],
      extra_bed: true,
      baby_crib: true,
      accessible: false,
    },
  },
];

const ROOM_AMENITY_OPTIONS = [
  {value: 'klima', label: 'Klima'},
  {value: 'minibar (ucretsiz su)', label: 'Minibar ve ücretsiz su'},
  {value: 'TV (Digiturk)', label: 'TV (Digiturk)'},
  {value: 'kasa', label: 'Kasa'},
  {value: 'sac kurutma makinesi', label: 'Saç kurutma makinesi'},
  {value: 'banyo urunleri', label: 'Banyo ürünleri'},
  {value: 'su isitici', label: 'Su ısıtıcı'},
  {value: 'self-servis su/kahve/bitki cayi', label: 'Self servis su, kahve ve bitki çayı'},
];

const ROOM_FEATURE_OPTIONS = [
  {value: 'accessible', label: 'Erişime uygun'},
  {value: 'ground_floor', label: 'Zemin kat'},
  {value: 'honeymoon_recommended', label: 'Balayı için uygun'},
  {value: 'spacious', label: 'Geniş oda'},
  {value: 'jacuzzi', label: 'Jakuzi'},
  {value: 'rooftop', label: 'Çatı katı / teras'},
  {value: 'quiet', label: 'Sessiz'},
  {value: 'modern', label: 'Modern tasarım'},
];

const FAQ_TOPIC_OPTIONS = [
  {value: '', label: 'Kategori seçin'},
  {value: 'check_in_time', label: 'Check-in saati'},
  {value: 'check_out_time', label: 'Check-out saati'},
  {value: 'early_checkin', label: 'Erken check-in'},
  {value: 'late_checkout', label: 'Geç check-out'},
  {value: 'late_arrival', label: 'Geç varış'},
  {value: 'breakfast_hours', label: 'Kahvaltı saatleri'},
  {value: 'restaurant_external_guests', label: 'Dış misafir restoran kullanımı'},
  {value: 'room_service', label: 'Oda servisi'},
  {value: 'room_amenities', label: 'Oda olanakları'},
  {value: 'accessible_room', label: 'Erişilebilir oda'},
  {value: 'child_policy', label: 'Çocuk politikası'},
  {value: 'family_suitability', label: 'Aile uygunluğu'},
  {value: 'pet_policy', label: 'Evcil hayvan politikası'},
  {value: 'smoking_policy_details', label: 'Sigara politikası'},
  {value: 'parking', label: 'Otopark'},
  {value: 'wifi', label: 'Wi‑Fi'},
  {value: 'pool', label: 'Havuz'},
  {value: 'heated_pool', label: 'Isıtmalı havuz'},
  {value: 'spa_hamam', label: 'Spa / hamam'},
  {value: 'beach_distance', label: 'Plaj mesafesi'},
  {value: 'private_beach', label: 'Özel plaj'},
  {value: 'airport_transfer', label: 'Havalimanı transferi'},
  {value: 'tour_excursion', label: 'Tur / gezi'},
  {value: 'nearest_pharmacy_hospital', label: 'Eczane / hastane yakınlığı'},
  {value: 'currency_exchange', label: 'Döviz bozdurma'},
  {value: 'fethiye_distance', label: 'Fethiye merkez mesafesi'},
  {value: 'laundry_service', label: 'Çamaşır hizmeti'},
  {value: 'pool_bar_hours', label: 'Havuz bar saatleri'},
  {value: 'a_la_carte_bar_hours', label: 'A la carte bar saatleri'},
  {value: 'minibar_prices', label: 'Minibar ücretleri'},
  {value: 'birthday_honeymoon_surprise', label: 'Doğum günü / balayı sürprizi'},
  {value: 'elevator', label: 'Asansör'},
  {value: 'total_rooms', label: 'Toplam oda sayısı'},
];

const RESTAURANT_CONCEPT_OPTIONS = [
  {value: 'a_la_carte', label: 'A la carte'},
  {value: 'buffet', label: 'Açık büfe'},
  {value: 'mixed', label: 'Karma servis'},
];

const RESTAURANT_AREA_OPTIONS = [
  {value: 'outdoor', label: 'Açık alan'},
  {value: 'indoor', label: 'Kapalı alan'},
];

const SERVICE_CHARGE_OPTIONS = [
  {value: 'free', label: 'Ücretsiz'},
  {value: 'paid', label: 'Ücretli'},
  {value: 'paid_handoff', label: 'Ücretli, ekip onayı ile'},
];

const PREPAYMENT_AMOUNT_OPTIONS = [
  {value: '', label: 'Ön ödeme yok'},
  {value: '1_night', label: '1 gecelik ücret'},
  {value: 'full_stay', label: 'Toplam konaklama tutarı'},
];

const EXCEPTION_REFUND_OPTIONS = [
  {value: '', label: 'İstisna iadesi yok'},
  {value: 'full_refund', label: 'Tam iade'},
  {value: 'total_minus_1_night', label: 'Toplam tutardan 1 gece düşülerek iade'},
];

const CANCELLATION_RULE_PRESET_OPTIONS = [
  {
    preset: 'FREE_CANCEL',
    label: 'Ücretsiz İptal',
    defaults: {
      free_cancel_deadline_days: 5,
      prepayment_days_before: 7,
      prepayment_amount: '1_night',
      prepayment_immediate: false,
      refund: true,
      refund_after_deadline: false,
      exception_days_before: null,
      exception_refund: '',
    },
  },
  {
    preset: 'NON_REFUNDABLE',
    label: 'İadesiz Rezervasyon',
    defaults: {
      free_cancel_deadline_days: null,
      prepayment_days_before: null,
      prepayment_amount: '1_night',
      prepayment_immediate: true,
      refund: false,
      refund_after_deadline: false,
      exception_days_before: 21,
      exception_refund: 'total_minus_1_night',
    },
  },
];

const PAYMENT_METHOD_OPTIONS = [
  {value: 'BANK_TRANSFER', label: 'Havale / EFT'},
  {value: 'PAYMENT_LINK', label: 'Ödeme linki'},
  {value: 'POS', label: 'Kart / POS'},
  {value: 'CASH', label: 'Nakit'},
  {value: 'MAIL_ORDER', label: 'Mail order'},
];

const HANDOFF_OPTIONS = [
  {value: 'human_handoff', label: 'Ekibe yönlendir'},
  {value: 'availability_handoff', label: 'Müsaitliğe göre ekibe yönlendir'},
  {value: 'availability_paid_handoff', label: 'Müsaitlik ve ücret için ekibe yönlendir'},
  {value: 'reception', label: 'Resepsiyon yönlendirsin'},
];

const SMOKING_ROOM_OPTIONS = [
  {value: 'non_smoking', label: 'Odada sigara içilmez'},
  {value: 'smoking_allowed', label: 'Odada sigara içilebilir'},
];

const CHILD_POLICY_OPTIONS = [
  {value: '', label: 'Çocuk politikası seçin'},
  {value: 'Tüm yaşlar kabul edilir', label: 'Tüm yaşlar kabul edilir'},
  {value: 'Belirli yaş kısıtı var', label: 'Belirli yaş kısıtı var'},
  {value: 'Çocuk kabul edilmez', label: 'Çocuk kabul edilmez'},
];

const BEDDING_AVAILABILITY_OPTIONS = [
  {value: '', label: 'Seçim yapın'},
  {value: 'Ücretsiz', label: 'Ücretsiz'},
  {value: 'Ücretli', label: 'Ücretli'},
  {value: 'Müsaitliğe göre', label: 'Müsaitliğe göre'},
  {value: 'Sunulmuyor', label: 'Sunulmuyor'},
];

const SMOKING_AREA_OPTIONS = [
  {value: 'balcony', label: 'Balkon'},
  {value: 'garden', label: 'Bahçe'},
  {value: 'poolside', label: 'Havuz çevresi'},
  {value: 'restaurant_outdoor', label: 'Restoran açık alanı'},
];

const POOL_TYPE_OPTIONS = [
  {value: 'open', label: 'Açık havuz'},
  {value: 'indoor', label: 'Kapalı havuz'},
];

const LAUNDRY_TURNAROUND_OPTIONS = [
  {value: '', label: 'Teslim süresi seçin'},
  {value: 'same_day', label: 'Aynı gün'},
  {value: '1_day', label: '1 gün'},
  {value: '2_days', label: '2 gün'},
  {value: 'on_request', label: 'Talebe göre'},
];

const SERVICE_POINT_OPTIONS = [
  {value: '', label: 'Teslim noktası seçin'},
  {value: 'reception', label: 'Resepsiyon'},
  {value: 'housekeeping', label: 'Kat hizmetleri'},
  {value: 'room_service', label: 'Oda içinden alım'},
  {value: 'lobby', label: 'Lobi'},
];

function getHotelProfileMode() {
  return state.hotelProfileMode === 'technical' ? 'technical' : 'standard';
}

function isHotelProfileTechnicalMode() {
  return getHotelProfileMode() === 'technical';
}

function getVisibleHotelProfileSections() {
  const technical = isHotelProfileTechnicalMode();
  return HOTEL_PROFILE_SECTIONS.filter(section => technical || !section.technicalOnly);
}

function ensureVisibleHotelProfileSection() {
  const visibleSections = getVisibleHotelProfileSections();
  if (!visibleSections.some(section => section.id === state.hotelProfileSection)) {
    state.hotelProfileSection = visibleSections[0]?.id || 'general';
  }
}

function syncHotelProfileAdvancedModeVisibility() {
  const advancedPanel = document.querySelector('[data-advanced-mode="hotel-profile-json"]');
  if (!(advancedPanel instanceof HTMLElement)) return;
  advancedPanel.hidden = !isHotelProfileTechnicalMode();
  if (!isHotelProfileTechnicalMode() && 'open' in advancedPanel) {
    advancedPanel.open = false;
  }
}

function humanizeProfileToken(value) {
  return String(value || '')
    .split('_')
    .filter(Boolean)
    .map(part => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(' ');
}

function formatBoardTypeCodeLabel(value) {
  return resolveSelectChoiceLabel(BOARD_TYPE_OPTIONS, value) || humanizeProfileToken(value);
}

function formatBreakfastTypeLabel(value) {
  return resolveSelectChoiceLabel(BREAKFAST_TYPE_OPTIONS, value) || humanizeProfileToken(value);
}

function formatPrepaymentAmountLabel(value) {
  return resolveSelectChoiceLabel(PREPAYMENT_AMOUNT_OPTIONS, value) || humanizeProfileToken(value);
}

function formatExceptionRefundLabel(value) {
  return resolveSelectChoiceLabel(EXCEPTION_REFUND_OPTIONS, value) || humanizeProfileToken(value);
}

function formatCancellationRuleKeyLabel(key) {
  const normalized = String(key || '').trim();
  const suffixMatch = normalized.match(/^(.*?)(?:_(\\d+))?$/);
  const baseKey = suffixMatch?.[1] || normalized;
  const suffix = suffixMatch?.[2] || '';
  const mapping = {
    FREE_CANCEL: 'Ücretsiz iptal',
    NON_REFUNDABLE: 'İadesiz rezervasyon',
  };
  const label = mapping[String(baseKey || '').toUpperCase()] || humanizeProfileToken(baseKey) || 'İptal kuralı';
  return suffix ? `${label} ${suffix}` : label;
}

function formatContactRoleLabel(value) {
  if (!String(value || '').trim()) return '';
  return resolveSelectChoiceLabel(CONTACT_ROLE_OPTIONS, value) || humanizeProfileToken(value);
}

function formatFaqTopicLabel(value) {
  if (!String(value || '').trim()) return '';
  return resolveSelectChoiceLabel(FAQ_TOPIC_OPTIONS, value) || humanizeProfileToken(value);
}

function buildRoomTypeSelectionOptions(roomTypes) {
  const items = Array.isArray(roomTypes) ? roomTypes : [];
  const seen = new Set();
  return items
    .map((item, index) => {
      const room = asObject(item);
      const value = String(room.name?.tr || room.name?.en || `Oda ${String(index + 1)}`).trim();
      if (!value || seen.has(value)) return null;
      seen.add(value);
      return {value, label: value};
    })
    .filter(Boolean);
}

function normalizeHotelProfileDraft(rawProfile) {
  const draft = asObject(JSON.parse(JSON.stringify(rawProfile || {})));
  draft.hotel_name = asObject(draft.hotel_name);
  draft.hotel_name.tr = String(draft.hotel_name.tr || '');
  draft.hotel_name.en = String(draft.hotel_name.en || '');
  draft.description = asObject(draft.description);
  draft.description.tr = String(draft.description.tr || '');
  draft.description.en = String(draft.description.en || '');
  draft.season = asObject(draft.season);
  draft.contacts = asObject(draft.contacts);
  draft.location = asObject(draft.location);
  draft.room_types = Array.isArray(draft.room_types) ? draft.room_types : [];
  draft.room_common = asObject(draft.room_common);
  draft.room_common.amenities = Array.isArray(draft.room_common.amenities) ? draft.room_common.amenities : [];
  draft.board_types = Array.isArray(draft.board_types) ? draft.board_types : [];
  draft.rate_mapping = asObject(draft.rate_mapping);
  draft.cancellation_rules = asObject(draft.cancellation_rules);
  draft.transfer_routes = Array.isArray(draft.transfer_routes) ? draft.transfer_routes : [];
  draft.restaurant = asObject(draft.restaurant);
  draft.restaurant.area_types = Array.isArray(draft.restaurant.area_types) ? draft.restaurant.area_types : [];
  draft.restaurant.hours = asObject(draft.restaurant.hours);
  draft.restaurant.menu = asObject(draft.restaurant.menu);
  draft.faq_data = Array.isArray(draft.faq_data) ? draft.faq_data : [];
  draft.facility_policies = asObject(draft.facility_policies);
  draft.payment = asObject(draft.payment);
  draft.payment.methods = Array.isArray(draft.payment.methods) ? draft.payment.methods : [];
  draft.operational = asObject(draft.operational);
  draft.highlights = Array.isArray(draft.highlights) ? draft.highlights : [];
  draft.hotel_conversational_flow = asObject(draft.hotel_conversational_flow);
  draft.hotel_conversational_flow.style = String(draft.hotel_conversational_flow.style || 'concise_premium');
  draft.hotel_conversational_flow.max_paragraph_lines = Number(draft.hotel_conversational_flow.max_paragraph_lines || 3);
  draft.hotel_conversational_flow.max_list_items = Number(draft.hotel_conversational_flow.max_list_items || 5);
  draft.hotel_conversational_flow.max_follow_up_questions = Number(draft.hotel_conversational_flow.max_follow_up_questions || 2);
  draft.hotel_conversational_flow.avoid_repeating_confirmed_facts = Boolean(draft.hotel_conversational_flow.avoid_repeating_confirmed_facts ?? true);
  draft.hotel_conversational_flow.summarize_large_price_lists = Boolean(draft.hotel_conversational_flow.summarize_large_price_lists ?? true);
  draft.hotel_conversational_flow.ask_before_full_price_dump = Boolean(draft.hotel_conversational_flow.ask_before_full_price_dump ?? true);
  draft.assistant = asObject(draft.assistant);
  draft.assistant.menu_source_documents = Array.isArray(draft.assistant.menu_source_documents) ? draft.assistant.menu_source_documents : [];
  draft.assistant.menu_scope_prompt = String(draft.assistant.menu_scope_prompt || '');
  draft.conversation_idle_reset = asObject(draft.conversation_idle_reset);
  draft.conversation_idle_reset.enabled = Boolean(draft.conversation_idle_reset.enabled ?? true);
  draft.conversation_idle_reset.idle_timeout_minutes = Number(draft.conversation_idle_reset.idle_timeout_minutes || 20);
  draft.conversation_idle_reset.warning_before_minutes = Number(draft.conversation_idle_reset.warning_before_minutes || 5);
  draft.conversation_idle_reset.warning_message_tr = String(draft.conversation_idle_reset.warning_message_tr || '');
  draft.conversation_idle_reset.warning_message_en = String(draft.conversation_idle_reset.warning_message_en || '');
  draft.conversation_idle_reset.closed_message_tr = String(draft.conversation_idle_reset.closed_message_tr || '');
  draft.conversation_idle_reset.closed_message_en = String(draft.conversation_idle_reset.closed_message_en || '');
  if (!draft.hotel_id && state.hotelDetail?.hotel_id) draft.hotel_id = state.hotelDetail.hotel_id;
  return draft;
}

function syncHotelProfileEditorFromDraft() {
  refs.hotelProfileEditor.value = JSON.stringify(state.hotelProfileDraft || {}, null, 2);
  syncHotelProfileDirtyState();
}

function syncHotelProfileDirtyState() {
  const currentSnapshot = refs.hotelProfileEditor?.value || '';
  state.hotelProfileHasUnsavedChanges = Boolean(
    state.hotelProfileLoadedDraftSnapshot != null
    && currentSnapshot !== state.hotelProfileLoadedDraftSnapshot
  );
  renderHotelProfileMeta();
  renderHotelFactsStatus(state.hotelFactsStatus);
}

function renderHotelProfileWorkspace() {
  if (!refs.hotelProfileSections || !refs.hotelProfileSectionBody) return;
  if (!state.hotelProfileMode) state.hotelProfileMode = 'standard';
  if (!state.hotelProfileDraft) {
    refs.hotelProfileSections.innerHTML = '<div class="empty-state"><p>Bölümleri görüntülemek için bir otel seçin.</p></div>';
    refs.hotelProfileSectionBody.innerHTML = '<div class="empty-state"><p>Dinamik düzenleyici burada görüntülenir.</p></div>';
    state.hotelProfileSearch = '';
    return;
  }
  ensureVisibleHotelProfileSection();
  syncHotelProfileAdvancedModeVisibility();
  const visibleSections = getVisibleHotelProfileSections();
  const technicalMode = isHotelProfileTechnicalMode();
  refs.hotelProfileSections.innerHTML = `
    <div class="helper-box">
      <strong>Dinamik Otel Düzenleyicisi</strong>
      <p class="muted">${escapeHtml(
        technicalMode
          ? 'Teknik alanlar görünür. Kimlik, eşleştirme ve gelişmiş JSON düzenlemeleri bu modda yapılır.'
          : 'Günlük güncellemeler için sade görünüm. Teknik kimlik ve sistem alanları gizlendi.'
      )}</p>
      <div class="module-actions mt-sm">
        <button class="action-button ${technicalMode ? 'secondary' : 'primary'}" type="button" data-profile-mode="standard">Standart Düzenleme</button>
        <button class="action-button ${technicalMode ? 'warn' : 'secondary'}" type="button" data-profile-mode="technical">Teknik Ayarlar</button>
      </div>
      <div class="profile-summary-strip mt-sm">
        <span class="profile-summary-chip">Oda tipi: ${escapeHtml(String((state.hotelProfileDraft.room_types || []).length))}</span>
        <span class="profile-summary-chip">Pansiyon türü: ${escapeHtml(String((state.hotelProfileDraft.board_types || []).length))}</span>
        <span class="profile-summary-chip">Transfer güzergâhı: ${escapeHtml(String((state.hotelProfileDraft.transfer_routes || []).length))}</span>
        <span class="profile-summary-chip">SSS kaydı: ${escapeHtml(String((state.hotelProfileDraft.faq_data || []).length))}</span>
      </div>
      <div class="profile-section-tabs mt-md">
        ${visibleSections.map(section => `
          <button
            class="profile-section-tab ${state.hotelProfileSection === section.id ? 'is-active' : ''}"
            type="button"
            data-hotel-profile-section="${escapeHtml(section.id)}"
          ><span>${escapeHtml(section.label)}</span></button>
        `).join('')}
      </div>
      <div class="profile-toolbar">
        ${renderTextField('Bölüm içinde ara', '__section_search__', state.hotelProfileSearch || '', {placeholder: 'Alan, değer veya kart adı ara...'})}
        <div class="profile-toolbar-actions">
          <button class="action-button secondary" type="button" data-clear-profile-search ${state.hotelProfileSearch ? '' : 'disabled'}>Temizle</button>
        </div>
      </div>
      ${renderHotelProfileSectionOverview()}
    </div>
  `;
  refs.hotelProfileSectionBody.innerHTML = renderHotelProfileSectionBody();
  applyHotelProfileSectionSearch();
  applyHotelProfileValidationDecorations();
}

function renderHotelProfileSectionOverview() {
  const items = buildHotelProfileSectionOverview();
  return `
    ${renderHotelProfileOverviewSummary(items)}
    <div class="profile-overview-grid">
      ${items.map(item => `
        <button class="profile-overview-card ${state.hotelProfileSection === item.id ? 'is-active' : ''}" type="button" data-profile-overview-section="${escapeHtml(item.id)}" data-profile-overview-target="${escapeHtml(item.id)}" data-profile-overview-path="">
          <span class="profile-overview-status ${escapeHtml(item.status)}" data-profile-overview-status>${escapeHtml(item.status_label)}</span>
          <h4 class="mt-sm">${escapeHtml(item.label)}</h4>
          <p data-profile-overview-description>${escapeHtml(item.description)}</p>
          <div class="profile-overview-metrics" data-profile-overview-metrics>
            <span>${escapeHtml(String(item.blockers))} engelleyici</span>
            <span>${escapeHtml(String(item.warnings))} uyarı</span>
          </div>
        </button>
      `).join('')}
    </div>
  `;
}

function renderHotelProfileOverviewSummary(items) {
  const summary = buildHotelProfileOverviewSummary(items);
  return `
    <div class="helper-box profile-overview-summary" data-profile-overview-summary>
      <div class="profile-overview-header">
        <div>
          <h4>Bölüm İlerleme Özeti</h4>
          <p>Zorunlu alanların durumu, engelleyici sorunlar ve uyarılar tek bakışta görünür.</p>
        </div>
        <div>
          <div class="profile-progress-track" aria-label="Bölüm ilerleme oranı">
            <span class="profile-progress-fill" data-profile-progress-fill style="width:${escapeHtml(String(summary.percent))}%"></span>
          </div>
          <p class="muted mt-sm" data-profile-progress-text>%${escapeHtml(String(summary.percent))} tamamlandı</p>
        </div>
      </div>
      <div class="profile-summary-strip mt-md">
        <span class="profile-summary-chip" data-profile-summary-chip="complete">${escapeHtml(String(summary.completeSections))}/${escapeHtml(String(summary.totalSections))} bölüm hazır</span>
        <span class="profile-summary-chip" data-profile-summary-chip="incomplete">${escapeHtml(String(summary.incompleteSections))} bölüm eksik</span>
        <span class="profile-summary-chip" data-profile-summary-chip="blocker">${escapeHtml(String(summary.blockerSections))} bölümde engelleyici sorun var</span>
        <span class="profile-summary-chip" data-profile-summary-chip="warning">${escapeHtml(String(summary.warningSections))} bölümde uyarı var</span>
      </div>
      ${summary.missingItems.length ? `
        <div class="mt-md">
          <strong>Eksik Alan Özeti</strong>
          <div class="profile-gap-list" data-profile-overview-missing>
            ${summary.missingItems.map(item => `
              <button class="profile-gap-chip" type="button" data-profile-overview-target="${escapeHtml(item.id)}" data-profile-overview-path="${escapeHtml(item.path || '')}">${escapeHtml(item.section)} • ${escapeHtml(item.label)}</button>
            `).join('')}
            ${summary.remainingMissing > 0 ? `<span class="profile-gap-count">+${escapeHtml(String(summary.remainingMissing))} alan daha</span>` : ''}
          </div>
        </div>
      ` : `
        <p class="muted mt-md" data-profile-overview-missing>Tüm bölümlerde temel zorunlu alanlar dolduruldu.</p>
      `}
    </div>
  `;
}

function renderHotelProfileSectionBody() {
  switch (state.hotelProfileSection) {
    case 'general':
      return renderHotelProfileGeneralSection();
    case 'contacts':
      return renderHotelProfileContactsSection();
    case 'rooms':
      return renderHotelProfileRoomsSection();
    case 'pricing':
      return renderHotelProfilePricingSection();
    case 'transfers':
      return renderHotelProfileTransfersSection();
    case 'restaurant':
      return renderHotelProfileRestaurantSection();
    case 'faq':
      return renderHotelProfileFaqSection();
    case 'policies':
      return renderHotelProfilePoliciesSection();
    case 'idle_reset':
      return renderHotelProfileIdleResetSection();
    case 'assistant':
      return renderHotelProfileAssistantSection();
    default:
      return renderHotelProfileGeneralSection();
  }
}

function renderHotelProfileGeneralSection() {
  const draft = state.hotelProfileDraft || {};
  const technicalMode = isHotelProfileTechnicalMode();
  return `
    <div class="helper-box">
      <strong>Genel Bilgiler</strong>
      <p class="muted">Otel kimliği, adlar, sezon bilgisi, açıklamalar ve öne çıkan başlıklar.</p>
    </div>
    <div class="profile-section-grid mt-md">
      ${technicalMode ? renderTextField('Otel Kimliği', 'hotel_id', draft.hotel_id ?? '', {type: 'number', full: false, numberKind: 'int', disabled: true}) : ''}
      ${technicalMode
        ? renderTextField('Otel Türü', 'hotel_type', draft.hotel_type || '')
        : renderSelectField('Otel Türü', 'hotel_type', draft.hotel_type || 'boutique', HOTEL_TYPE_OPTIONS, {help: 'Otelinizin misafire sunulan genel sınıfını seçin.'})}
      ${renderTextField('Otel Adı (TR)', 'hotel_name.tr', draft.hotel_name?.tr || '')}
      ${renderTextField('Otel Adı (EN)', 'hotel_name.en', draft.hotel_name?.en || '')}
      ${technicalMode
        ? renderTextField('Saat Dilimi', 'timezone', draft.timezone || '')
        : renderSelectField('Saat Dilimi', 'timezone', draft.timezone || 'Europe/Istanbul', TIMEZONE_OPTIONS, {help: 'Mesaj saatleri ve operasyon akışı bu saate göre çalışır.'})}
      ${technicalMode
        ? renderTextField('Temel Para Birimi', 'currency_base', draft.currency_base || '')
        : renderSelectField('Temel Para Birimi', 'currency_base', draft.currency_base || 'EUR', CURRENCY_OPTIONS, {help: 'Misafir fiyatlarında temel gösterim para birimidir.'})}
      ${technicalMode ? renderTextField('PMS', 'pms', draft.pms || '') : ''}
      ${renderTextField('WhatsApp Numarası', 'whatsapp_number', draft.whatsapp_number || '', {placeholder: '+90 5xx xxx xx xx', help: 'Misafirlerin yazdığı ana iletişim numarası.'})}
      ${renderTextField('Sezon Açılışı', 'season.open', draft.season?.open || '', {placeholder: '04-20', help: 'Ay-gün biçiminde girin. Örnek: 20 Nisan için 04-20.', format: 'month-day', inputMode: 'numeric', maxLength: 5})}
      ${renderTextField('Sezon Kapanışı', 'season.close', draft.season?.close || '', {placeholder: '11-10', help: 'Ay-gün biçiminde girin. Örnek: 10 Kasım için 11-10.', format: 'month-day', inputMode: 'numeric', maxLength: 5})}
      ${renderTextField('Açıklama (TR)', 'description.tr', draft.description?.tr || '', {textarea: true, full: true, placeholder: 'Örn: Ölüdeniz’e yakın, sakin atmosferli butik otelimiz aileler ve çiftler için uygundur.', help: 'Misafire gösterilecek kısa tanıtım metnini yazın.'})}
      ${renderTextField('Açıklama (EN)', 'description.en', draft.description?.en || '', {textarea: true, full: true, placeholder: 'E.g. Our boutique hotel near Oludeniz offers a calm atmosphere for couples and families.', help: 'Write the short property introduction shown to international guests.'})}
      ${technicalMode
        ? renderListField('Öne Çıkanlar', 'highlights', draft.highlights || [], {full: true, help: 'Her satıra bir öne çıkan madde girin. Örnek: plaja yakın, aile dostu.'})
        : renderMultiCheckboxField('Öne Çıkan Başlıklar', 'highlights', draft.highlights || [], HIGHLIGHT_OPTIONS, {full: true, help: 'Misafirin ilk bakışta göreceği ana başlıkları seçin.'})}
    </div>
  `;
}

function renderHotelProfileContactsSection() {
  const draft = state.hotelProfileDraft || {};
  const contacts = Object.entries(asObject(draft.contacts));
  const technicalMode = isHotelProfileTechnicalMode();
  const nearbyPlaces = Array.isArray(draft.location?.nearby) ? draft.location.nearby : [];
  return `
    <div class="helper-box">
      <strong>İletişim Kayıtları</strong>
      <p class="muted">${escapeHtml(
        technicalMode
          ? 'İletişim kayıtları sözlük yapısında korunur. Anahtar alanını değiştirerek teknik anahtarı da güncelleyebilirsiniz.'
          : 'Misafire gösterilen telefon, e-posta ve çalışma saatlerini iletişim kartları üzerinden güncelleyin. Yeni kayıt eklerken önce iletişim tipini seçin.'
      )}</p>
      <div class="module-actions mt-sm">
        ${technicalMode
          ? '<button class="action-button primary" type="button" data-profile-add-map-entry="contacts">Yeni İletişim Kaydı</button>'
          : CONTACT_PRESET_OPTIONS.map(option => `<button class="action-button ${option.preset === 'OTHER' ? 'secondary' : 'primary'}" type="button" data-profile-add-contact-preset="${escapeHtml(option.preset)}">${escapeHtml(option.label)}</button>`).join('')}
      </div>
    </div>
    <div class="profile-section-stack mt-md">
      ${contacts.length ? contacts.map(([key, item], index) => renderContactCard(key, item, index)).join('') : '<div class="empty-state"><p>Henüz iletişim kaydı yok.</p></div>'}
    </div>
    <div class="helper-box mt-md">
      <strong>Konum</strong>
      <p class="muted">${escapeHtml(
        technicalMode
          ? 'Sık kullanılan konum alanları ayrı alanlar olarak sunulur. Yakındaki noktalar JSON biçiminde düzenlenir.'
          : 'Adres, harita bağlantıları ve yakındaki yerleri misafirin göreceği dille düzenleyin.'
      )}</p>
    </div>
    <div class="profile-section-grid mt-md">
      ${renderTextField('Ülke', 'location.country', draft.location?.country || '', {placeholder: 'Türkiye'})}
      ${renderTextField('Şehir', 'location.city', draft.location?.city || '', {placeholder: 'Muğla'})}
      ${renderTextField('İlçe', 'location.district', draft.location?.district || '', {placeholder: 'Fethiye'})}
      ${renderTextField('Adres', 'location.address', draft.location?.address || '', {full: true, placeholder: 'Mahalle, cadde ve kapı numarasını yazın.'})}
      ${renderTextField('Google Maps Otel', 'location.google_maps_hotel', draft.location?.google_maps_hotel || '', {full: true, placeholder: 'https://maps.google.com/...'} )}
      ${renderTextField('Google Maps Restoran', 'location.google_maps_restaurant', draft.location?.google_maps_restaurant || '', {full: true, placeholder: 'https://maps.google.com/...'} )}
      ${technicalMode ? renderJsonField('Yakındaki Noktalar', 'location.nearby', draft.location?.nearby || [], {full: true, help: 'JSON dizi biçiminde düzenleyin.'}) : `
        <div class="field full">
          <div class="helper-box">
            <strong>Yakındaki Yerler</strong>
            <p class="muted">Misafirin duyacağı yakın yerleri ad ve mesafe bilgisiyle ayrı ayrı düzenleyin.</p>
            <div class="module-actions mt-sm">
              <button class="action-button primary" type="button" data-profile-add-object-item="location.nearby">Yeni Yakın Nokta</button>
            </div>
          </div>
          <div class="profile-section-stack mt-md">
            ${nearbyPlaces.length ? nearbyPlaces.map((item, index) => renderNearbyPlaceCard(item, index)).join('') : '<div class="empty-state"><p>Henüz yakındaki yer eklenmedi.</p></div>'}
          </div>
        </div>
      `}
    </div>
  `;
}

function renderHotelProfileRoomsSection() {
  const draft = state.hotelProfileDraft || {};
  const technicalMode = isHotelProfileTechnicalMode();
  const roomTypes = Array.isArray(draft.room_types) ? draft.room_types : [];
  return `
    <div class="helper-box">
      <strong>Oda Ortak Alanları</strong>
      <p class="muted">Tüm odalara ait ortak politika ve olanak alanları.</p>
    </div>
    <div class="profile-section-grid mt-md">
      ${renderCheckboxField('Odada sigara içilebilir', 'room_common.smoking', Boolean(draft.room_common?.smoking), {help: 'Kapalı ise odalarda sigara içilmesine izin verilmez.'})}
      ${renderCheckboxField('Bağlantılı Odalar', 'room_common.connecting_rooms', Boolean(draft.room_common?.connecting_rooms))}
      ${renderCheckboxField('Balkon var', 'room_common.balcony', Boolean(draft.room_common?.balcony))}
      ${renderCheckboxField('Günlük Temizlik', 'room_common.daily_cleaning', Boolean(draft.room_common?.daily_cleaning))}
      ${technicalMode
        ? renderListField('Olanaklar', 'room_common.amenities', draft.room_common?.amenities || [], {full: true, help: 'Her satıra bir olanak girin.'})
        : renderMultiCheckboxField('Oda Olanakları', 'room_common.amenities', draft.room_common?.amenities || [], ROOM_AMENITY_OPTIONS, {full: true, help: 'Misafirin odada göreceği standart olanakları seçin.'})}
    </div>
    <div class="helper-box mt-md">
      <strong>Oda Tipleri</strong>
      <p class="muted">${escapeHtml(
        technicalMode
          ? 'PMS eşleştirmesi ve misafire gösterilen bilgiler aynı ekranda düzenlenir.'
          : 'Misafire görünen oda bilgilerini sade alanlarla düzenleyin. Teknik eşleştirmeler gizlendi.'
      )}</p>
      <div class="module-actions mt-sm">
        ${technicalMode
          ? '<button class="action-button primary" type="button" data-profile-add-list-item="room_types">Yeni Oda Tipi</button>'
          : ROOM_TYPE_PRESET_OPTIONS.map(option => `
              <button
                class="action-button secondary"
                type="button"
                data-profile-add-room-preset="${escapeHtml(option.preset)}"
              >${escapeHtml(option.label)}</button>
            `).join('')}
      </div>
    </div>
    <div class="profile-section-stack mt-md">
      ${roomTypes.length ? roomTypes.map((item, index) => renderRoomTypeCard(item, index)).join('') : '<div class="empty-state"><p>Henüz oda tipi kaydı yok.</p></div>'}
    </div>
  `;
}

function renderHotelProfilePricingSection() {
  const draft = state.hotelProfileDraft || {};
  const technicalMode = isHotelProfileTechnicalMode();
  const boardTypes = Array.isArray(draft.board_types) ? draft.board_types : [];
  const rateMappings = Object.entries(asObject(draft.rate_mapping));
  const cancellationRules = Object.entries(asObject(draft.cancellation_rules));
  return `
    <div class="helper-box">
      <strong>Pansiyon Türleri</strong>
      <p class="muted">${escapeHtml(
        technicalMode
          ? 'Misafirin gördüğü pansiyon paketi, kahvaltı saatleri ve iptal koşulları bu bölümden yönetilir.'
          : 'Önce misafire sunulan pansiyon paketini ekleyin, ardından uygun iptal kuralını seçin. Teknik rezervasyon eşleştirmesi arka planda taslak olarak hazırlanır.'
      )}</p>
      <div class="module-actions mt-sm">
        ${technicalMode
          ? '<button class="action-button primary" type="button" data-profile-add-list-item="board_types">Yeni Pansiyon Türü</button>'
          : BOARD_TYPE_PRESET_OPTIONS.map(option => `
              <button
                class="action-button secondary"
                type="button"
                data-profile-add-board-preset="${escapeHtml(option.preset)}"
              >${escapeHtml(option.label)}</button>
            `).join('')}
      </div>
    </div>
    <div class="profile-section-stack mt-md">
      ${boardTypes.length ? boardTypes.map((item, index) => renderBoardTypeCard(item, index)).join('') : '<div class="empty-state"><p>Henüz pansiyon türü kaydı yok.</p></div>'}
    </div>
    ${technicalMode ? `
      <div class="helper-box mt-md">
        <strong>Rezervasyon Sistemi Eşleştirmesi</strong>
        <p class="muted">Bu alanlar PMS teknik kimlikleriyle çalışır. Günlük kullanım için standart mod yeterlidir.</p>
        <div class="module-actions mt-sm">
          <button class="action-button primary" type="button" data-profile-add-map-entry="rate_mapping">Yeni Fiyat Eşleştirmesi</button>
        </div>
      </div>
      <div class="profile-section-stack mt-md">
        ${rateMappings.length ? rateMappings.map(([key, item], index) => renderRateMappingCard(key, item, index)).join('') : '<div class="empty-state"><p>Henüz fiyat eşleştirmesi yok.</p></div>'}
      </div>
    ` : renderStandardRateMappingSummary(draft.rate_mapping, draft.cancellation_rules)}
    <div class="helper-box mt-md">
      <strong>İptal Kuralları</strong>
      <p class="muted">İptal, ön ödeme ve istisna iadesi seçeneklerini teknik kod görmeden düzenleyin.</p>
      <div class="module-actions mt-sm">
        ${technicalMode
          ? '<button class="action-button primary" type="button" data-profile-add-map-entry="cancellation_rules">Yeni Kural</button>'
          : CANCELLATION_RULE_PRESET_OPTIONS.map(option => `
              <button
                class="action-button secondary"
                type="button"
                data-profile-add-cancellation-preset="${escapeHtml(option.preset)}"
              >${escapeHtml(option.label)}</button>
            `).join('')}
      </div>
    </div>
    <div class="profile-section-stack mt-md">
      ${cancellationRules.length ? cancellationRules.map(([key, item], index) => renderCancellationRuleCard(key, item, index)).join('') : '<div class="empty-state"><p>Henüz iptal kuralı yok.</p></div>'}
    </div>
  `;
}

function renderHotelProfileTransfersSection() {
  const routes = Array.isArray(state.hotelProfileDraft?.transfer_routes) ? state.hotelProfileDraft.transfer_routes : [];
  const technicalMode = isHotelProfileTechnicalMode();
  return `
    <div class="helper-box">
      <strong>Transfer Güzergâhları</strong>
      <p class="muted">${escapeHtml(
        technicalMode
          ? 'Güzergâh, fiyat, kapasite ve büyük araç kuralları burada tutulur.'
          : 'Güzergâh, fiyat ve yolculuk süresini güncelleyin. Teknik rota kodları gizlendi.'
      )}</p>
      <div class="module-actions mt-sm">
        <button class="action-button primary" type="button" data-profile-add-list-item="transfer_routes">Yeni Güzergâh</button>
      </div>
    </div>
    <div class="profile-section-stack mt-md">
      ${routes.length ? routes.map((item, index) => renderTransferRouteCard(item, index)).join('') : '<div class="empty-state"><p>Henüz transfer güzergâhı yok.</p></div>'}
    </div>
  `;
}

function renderHotelProfileRestaurantSection() {
  const restaurant = asObject(state.hotelProfileDraft?.restaurant);
  const assistant = asObject(state.hotelProfileDraft?.assistant);
  const technicalMode = isHotelProfileTechnicalMode();
  const hours = asObject(restaurant.hours);
  const menu = asObject(restaurant.menu);
  if (technicalMode) {
    return `
      <div class="helper-box">
        <strong>Restoran</strong>
        <p class="muted">Restoran kapasitesi, saatleri, menü katalogu ve menü-kaynak sınırları bu bölümden yönetilir.</p>
      </div>
      <div class="profile-section-grid mt-md">
        <div class="field full">
          <div class="helper-box">
            <strong>Restoran Menüsü (Teknik)</strong>
            <p class="muted">Menü kaynak dokümanları, strict menü kural metni ve kategori bazlı menü katalogu. Bu alanlar modelin menü cevap sınırını doğrudan belirler.</p>
          </div>
        </div>
        ${renderListField('Menü Kaynak Dokümanları', 'assistant.menu_source_documents', assistant.menu_source_documents || [], {full: true, help: 'Her satıra tek bir menü URL adresi girin. Menü sorularında yalnızca bu dokümanlar kaynak kabul edilir.'})}
        ${renderTextField('Menü Kapsam Talimatı (Strict)', 'assistant.menu_scope_prompt', assistant.menu_scope_prompt || '', {textarea: true, full: true, placeholder: 'Yalnızca tanımlı menü dokümanlarına dayanarak yanıt ver...', help: 'Bu metin system prompta aynen eklenir.'})}
        ${renderJsonField('Menü Kataloğu (Kategori -> Ürünler)', 'restaurant.menu', menu || {}, {full: true, help: 'JSON yapısı örneği: {"starters":[{"name_tr":"...", "name_en":"...", "price":"..."}]}.'})}
        ${renderTextField('Restoran Adı', 'restaurant.name', restaurant.name || '')}
        ${renderTextField('Konsept', 'restaurant.concept', restaurant.concept || '')}
        ${renderTextField('Minimum Kapasite', 'restaurant.capacity_min', restaurant.capacity_min ?? 0, {type: 'number', numberKind: 'int', min: 0, max: 1000, placeholder: 'Örn: 10'})}
        ${renderTextField('Maksimum Kapasite', 'restaurant.capacity_max', restaurant.capacity_max ?? 0, {type: 'number', numberKind: 'int', min: 1, max: 1000, placeholder: 'Örn: 80'})}
        ${renderTextField('Yapay Zekâ İçin Maksimum Grup Büyüklüğü', 'restaurant.max_ai_party_size', restaurant.max_ai_party_size ?? 8, {type: 'number', numberKind: 'int', min: 1, max: 100})}
        ${renderTextField('Geç Kalma Toleransı (dk)', 'restaurant.late_tolerance_min', restaurant.late_tolerance_min ?? 15, {type: 'number', numberKind: 'int', min: 0, max: 240, placeholder: 'Örn: 15'})}
        ${renderCheckboxField('Dış Misafir Kabul Edilir', 'restaurant.external_guests_allowed', Boolean(restaurant.external_guests_allowed))}
        ${renderListField('Alan Türleri', 'restaurant.area_types', restaurant.area_types || [], {help: 'Her satıra bir alan türü girin. Örnek: outdoor, indoor.'})}
        ${renderTextField('Otel Misafiri Kahvaltı', 'restaurant.breakfast_hotel_guest', restaurant.breakfast_hotel_guest || '')}
        ${renderTextField('Dış Misafir Kahvaltı', 'restaurant.breakfast_external_guest', restaurant.breakfast_external_guest || '')}
        ${renderTextField('Öğle / Akşam Yemeği', 'restaurant.lunch_dinner', restaurant.lunch_dinner || '')}
        ${renderJsonField('Saatler', 'restaurant.hours', restaurant.hours || {}, {full: true, help: 'JSON nesnesi olarak düzenleyin: {"breakfast":"08:00-10:30"}'})}
      </div>
    `;
  }
  return `
    <div class="helper-box">
      <strong>Restoran</strong>
      <p class="muted">Misafire görünen restoran bilgilerini, menü kaynaklarını ve menü kapsamını bu bölümden yönetin.</p>
    </div>
    <div class="profile-section-grid mt-md">
      <div class="field full">
        <div class="helper-box">
          <strong>Genel Restoran Bilgisi</strong>
          <p class="muted">Misafirin restoranın ne olduğunu ve kimlerin kullanabildiğini bu bloktan anlayacağı bilgileri güncelleyin.</p>
        </div>
      </div>
      ${renderTextField('Restoran Adı', 'restaurant.name', restaurant.name || '', {placeholder: 'Örn: Olive Lounge'})}
      ${renderSelectField('Konsept', 'restaurant.concept', restaurant.concept || 'a_la_carte', RESTAURANT_CONCEPT_OPTIONS, {help: 'Misafire sunulan servis biçimini seçin.'})}
      ${renderCheckboxField('Dış Misafir Kabul Edilir', 'restaurant.external_guests_allowed', Boolean(restaurant.external_guests_allowed))}
      <div class="field full">
        <div class="helper-box">
          <strong>Alan ve Kapasite</strong>
          <p class="muted">Oturma alanı ve kapasite bilgilerinin doğru görünmesini sağlayın.</p>
        </div>
      </div>
      ${renderTextField('Minimum Kapasite', 'restaurant.capacity_min', restaurant.capacity_min ?? 0, {type: 'number', numberKind: 'int', min: 0, max: 1000, placeholder: 'Örn: 10'})}
      ${renderTextField('Maksimum Kapasite', 'restaurant.capacity_max', restaurant.capacity_max ?? 0, {type: 'number', numberKind: 'int', min: 1, max: 1000, placeholder: 'Örn: 80'})}
      ${renderTextField('Geç Kalma Toleransı (dk)', 'restaurant.late_tolerance_min', restaurant.late_tolerance_min ?? 15, {type: 'number', numberKind: 'int', min: 0, max: 240, placeholder: 'Örn: 15'})}
      ${renderMultiCheckboxField('Servis Alanları', 'restaurant.area_types', restaurant.area_types || [], RESTAURANT_AREA_OPTIONS, {help: 'Misafirin oturabileceği alanları seçin.'})}
      <div class="field full">
        <div class="helper-box">
          <strong>Kahvaltı ve Ücretlendirme</strong>
          <p class="muted">Otel misafiri ve dış misafir için ücret bilgisini ayrı ayrı seçin.</p>
        </div>
      </div>
      ${renderSelectField('Otel Misafiri Kahvaltı', 'restaurant.breakfast_hotel_guest', restaurant.breakfast_hotel_guest || 'free', SERVICE_CHARGE_OPTIONS, {help: 'Kahvaltının otel misafirleri için ücret durumunu seçin.'})}
      ${renderSelectField('Dış Misafir Kahvaltı', 'restaurant.breakfast_external_guest', restaurant.breakfast_external_guest || 'paid', SERVICE_CHARGE_OPTIONS, {help: 'Dış misafirin kahvaltı ücret durumunu seçin.'})}
      ${renderSelectField('Öğle / Akşam Servisi', 'restaurant.lunch_dinner', restaurant.lunch_dinner || 'paid', SERVICE_CHARGE_OPTIONS, {help: 'Öğle ve akşam servisi ücretlendirmesini seçin.'})}
      <div class="field full">
        <div class="helper-box">
          <strong>Servis Saatleri</strong>
          <p class="muted">Misafire söylenecek servis saatlerini net biçimde girin.</p>
        </div>
      </div>
      ${renderTextField('Kahvaltı Saatleri', 'restaurant.hours.breakfast', hours.breakfast || '', {placeholder: '08:00-10:30', format: 'time-range', inputMode: 'numeric', maxLength: 11})}
      ${renderTextField('Öğle Saatleri', 'restaurant.hours.lunch', hours.lunch || '', {placeholder: '12:00-17:00', format: 'time-range', inputMode: 'numeric', maxLength: 11})}
      ${renderTextField('Akşam Saatleri', 'restaurant.hours.dinner', hours.dinner || '', {placeholder: '18:00-22:00', format: 'time-range', inputMode: 'numeric', maxLength: 11})}
      <div class="field full">
        <div class="helper-box">
          <strong>Restoran Menüsü</strong>
          <p class="muted">Modelin menü yanıtları yalnızca bu kaynaklara ve menü kataloguna dayanır. Kaynak ve katalog tutarlı değilse menü yanıt kalitesi düşer.</p>
        </div>
      </div>
      ${renderListField('Menü Kaynak Dokümanları', 'assistant.menu_source_documents', assistant.menu_source_documents || [], {full: true, help: 'Her satıra tek bir menü URL adresi girin. Örnek: https://www.kassandrarestaurant.com/alacarte.pdf'})}
      ${renderTextField('Menü Kapsam Talimatı', 'assistant.menu_scope_prompt', assistant.menu_scope_prompt || '', {textarea: true, full: true, placeholder: 'Menü sorularında sadece tanımlı kaynaklardan yanıt ver...', help: 'Doküman dışı ürün/fiyat uydurmayı engelleyen kuralları burada tutun.'})}
      ${renderJsonField('Menü Kataloğu (Opsiyonel ama önerilir)', 'restaurant.menu', menu || {}, {full: true, help: 'Kategori bazlı ürünleri JSON olarak girin. Örnek: {"wine":[{"name_tr":"...", "price":"..."}]}'} )}
    </div>
  `;
}

function renderHotelProfileFaqSection() {
  const faqEntries = Array.isArray(state.hotelProfileDraft?.faq_data) ? state.hotelProfileDraft.faq_data : [];
  const activeIndex = getActiveHotelProfileFaqIndex(faqEntries);
  const activeFaq = activeIndex >= 0 ? faqEntries[activeIndex] : null;
  const technicalMode = isHotelProfileTechnicalMode();
  return `
    <div class="helper-box">
      <strong>SSS</strong>
      <p class="muted">${escapeHtml(
        technicalMode
          ? 'Tüm dil varyantları, teknik alanlar ve içerik durumu bu bölümde yönetilir.'
          : 'Misafirin gördüğü soru ve cevapları sade görünümde düzenleyin. Ek diller isteğe bağlı olarak açılır.'
      )}</p>
      <div class="module-actions mt-sm">
        <button class="action-button primary" type="button" data-profile-add-list-item="faq_data">Yeni SSS Kaydı</button>
      </div>
    </div>
    <div class="profile-section-stack mt-md">
      ${faqEntries.length ? `
        <div class="helper-box">
          <div class="profile-card-selector">
            <div class="field">
              <label>SSS Kaydı Seçimi</label>
              <select data-profile-faq-active="true">
                ${faqEntries.map((item, index) => `
                  <option value="${escapeHtml(String(index))}" ${index === activeIndex ? 'selected' : ''}>
                    ${escapeHtml(buildFaqOptionLabel(item, index))}
                  </option>
                `).join('')}
              </select>
            </div>
            <div class="profile-card-selector-meta">
              <span class="profile-summary-chip">Toplam SSS: ${escapeHtml(String(faqEntries.length))}</span>
              <span class="profile-summary-chip">Açık kayıt: ${escapeHtml(String(activeIndex + 1))}</span>
            </div>
          </div>
        </div>
        ${activeFaq ? renderFaqCard(activeFaq, activeIndex) : ''}
      ` : '<div class="empty-state"><p>Henüz SSS kaydı yok.</p></div>'}
    </div>
  `;
}

function renderHotelProfilePoliciesSection() {
  const draft = state.hotelProfileDraft || {};
  const technicalMode = isHotelProfileTechnicalMode();
  const payment = asObject(draft.payment);
  const facilityPolicies = asObject(draft.facility_policies);
  const checkIn = asObject(facilityPolicies.check_in);
  const checkOut = asObject(facilityPolicies.check_out);
  const children = asObject(facilityPolicies.children);
  const pets = asObject(facilityPolicies.pets);
  const smoking = asObject(facilityPolicies.smoking);
  const parking = asObject(facilityPolicies.parking);
  const pool = asObject(facilityPolicies.pool);
  const wifi = asObject(facilityPolicies.wifi);
  const accessibility = asObject(facilityPolicies.accessibility);
  const wellness = asObject(facilityPolicies.wellness);
  const localServices = asObject(facilityPolicies.local_services);
  const pharmacy = asObject(localServices.pharmacy);
  const currencyExchange = asObject(localServices.currency_exchange);
  const laundry = asObject(facilityPolicies.laundry);
  const operational = asObject(draft.operational);
  const eurBank = asObject(payment.eur_bank);
  const tryBank = asObject(payment.try_bank);
  const accessibleRoomChoices = buildRoomTypeSelectionOptions(draft.room_types);
  if (technicalMode) {
    return `
      <div class="helper-box">
        <strong>Politika Alanları</strong>
        <p class="muted">Teknik modda ham politika bloklarını doğrudan düzenleyebilirsiniz.</p>
      </div>
      <div class="profile-section-grid mt-md">
        ${renderJsonField('Ödeme', 'payment', draft.payment || {}, {full: true})}
        ${renderJsonField('Tesis Politikaları', 'facility_policies', draft.facility_policies || {}, {full: true})}
        ${renderJsonField('Operasyonel Ayarlar', 'operational', draft.operational || {}, {full: true})}
      </div>
    `;
  }
  return `
    <div class="helper-box">
      <strong>Politikalar</strong>
      <p class="muted">Misafire söylenen kuralları başlık başlık güncelleyin. Teknik JSON alanları standart modda gizlendi.</p>
    </div>
    <div class="profile-section-stack mt-md">
      ${renderPolicyCard('Giriş / Çıkış', 'Check-in, check-out ve geç giriş kuralları.', `
        ${renderTextField('Check-in Saati', 'facility_policies.check_in.time', checkIn.time || '', {placeholder: '14:00', format: 'time', inputMode: 'numeric', maxLength: 5})}
        ${renderSelectField('Erken Check-in', 'facility_policies.check_in.early_checkin', checkIn.early_checkin || 'availability_handoff', HANDOFF_OPTIONS, {help: 'Erken giriş talebi geldiğinde nasıl yönlendirileceğini seçin.'})}
        ${renderTextField('Geç Varış Saati', 'facility_policies.check_in.late_arrival_after', checkIn.late_arrival_after || '', {placeholder: '00:00', format: 'time', inputMode: 'numeric', maxLength: 5})}
        ${renderCheckboxField('Geç Varış İçin Haber Verilsin', 'facility_policies.check_in.late_arrival_contact_required', Boolean(checkIn.late_arrival_contact_required), {help: 'Açık olduğunda misafirden geç varış için önceden haber vermesi beklenir.'})}
        ${renderTextField('Check-out Saati', 'facility_policies.check_out.time', checkOut.time || '', {placeholder: '12:00', format: 'time', inputMode: 'numeric', maxLength: 5})}
        ${renderSelectField('Geç Check-out', 'facility_policies.check_out.late_checkout', checkOut.late_checkout || 'availability_paid_handoff', HANDOFF_OPTIONS, {help: 'Geç çıkış talebi geldiğinde izlenecek akışı seçin.'})}
      `)}
      ${renderPolicyCard('Çocuk ve Ek Yatak', 'Aile konaklamalarında paylaşılan temel bilgiler.', `
        ${renderSelectField('Çocuk Politikası', 'facility_policies.children.policy', children.policy || '', CHILD_POLICY_OPTIONS, {help: 'Konaklamada çocuk kabul durumunu seçin.'})}
        ${renderSelectField('Ek Yatak', 'facility_policies.children.extra_bed', children.extra_bed || '', BEDDING_AVAILABILITY_OPTIONS, {help: 'İlave yatağın ücret ve müsaitlik durumunu seçin.'})}
        ${renderSelectField('Bebek Yatağı', 'facility_policies.children.baby_crib', children.baby_crib || '', BEDDING_AVAILABILITY_OPTIONS, {help: 'Bebek yatağı sunuluyorsa koşulunu seçin.'})}
        ${renderTextField('Yatak Notu (TR)', 'facility_policies.children.bedding_note_tr', children.bedding_note_tr || '', {textarea: true, full: true, placeholder: 'Örn: İlave yatak yalnızca belirli oda tiplerinde sağlanır.', help: 'Ailelerin ek yatak veya bebek yatağıyla ilgili bilmesi gereken kısa notu yazın.'})}
        ${renderTextField('Yatak Notu (EN)', 'facility_policies.children.bedding_note_en', children.bedding_note_en || '', {textarea: true, full: true, placeholder: 'E.g. Extra beds are available only in selected room types.', help: 'Write the short bedding note shown to international guests.'})}
      `)}
      ${renderPolicyCard('Evcil Hayvan ve Sigara', 'Misafirin en sık sorduğu erişim kuralları.', `
        ${renderCheckboxField('Evcil Hayvan Kabul Edilir', 'facility_policies.pets.allowed', Boolean(pets.allowed))}
        ${renderTextField('Evcil Hayvan Açıklaması (TR)', 'facility_policies.pets.reply_tr', pets.reply_tr || '', {textarea: true, full: true, placeholder: 'Örn: Evcil hayvan kabul edilmez. Rehber köpek için lütfen önceden bilgi verin.'})}
        ${renderTextField('Evcil Hayvan Açıklaması (EN)', 'facility_policies.pets.reply_en', pets.reply_en || '', {textarea: true, full: true, placeholder: 'E.g. Pets are not allowed. Please inform us in advance for guide dogs.'})}
        ${renderSelectField('Odalarda Sigara', 'facility_policies.smoking.rooms', smoking.rooms || 'non_smoking', SMOKING_ROOM_OPTIONS)}
        ${renderMultiCheckboxField('Sigara İçilebilen Alanlar', 'facility_policies.smoking.allowed_areas', smoking.allowed_areas || [], SMOKING_AREA_OPTIONS, {full: true, help: 'Misafire açık olan alanları işaretleyin.'})}
        ${renderTextField('Sigara Açıklaması (TR)', 'facility_policies.smoking.reply_tr', smoking.reply_tr || '', {textarea: true, full: true, placeholder: 'Örn: Odalarda sigara içilmez, yalnızca balkonlarda izin verilir.'})}
        ${renderTextField('Sigara Açıklaması (EN)', 'facility_policies.smoking.reply_en', smoking.reply_en || '', {textarea: true, full: true, placeholder: 'E.g. Smoking is not allowed in rooms and is permitted only on balconies.'})}
      `)}
      ${renderPolicyCard('Park, Havuz ve Wi‑Fi', 'Tesis kullanımına dair sık sorulan bilgiler.', `
        ${renderCheckboxField('Otele Ait Otopark Var', 'facility_policies.parking.hotel_parking', Boolean(parking.hotel_parking))}
        ${renderTextField('Cadde Park Bilgisi', 'facility_policies.parking.street_parking', parking.street_parking || '', {placeholder: 'Ücretsiz cadde parkı mevcut'})}
        ${renderTextField('Özel Otopark Bilgisi', 'facility_policies.parking.private_parking', parking.private_parking || '', {placeholder: 'Karşıda ücretli özel otopark'})}
        ${renderTextField('Park Açıklaması (TR)', 'facility_policies.parking.reply_tr', parking.reply_tr || '', {textarea: true, full: true, placeholder: 'Örn: Otel önünde sınırlı sayıda ücretsiz park alanı vardır.'})}
        ${renderTextField('Park Açıklaması (EN)', 'facility_policies.parking.reply_en', parking.reply_en || '', {textarea: true, full: true, placeholder: 'E.g. A limited number of free parking spots are available in front of the hotel.'})}
        ${renderSelectField('Havuz Türü', 'facility_policies.pool.type', pool.type || 'open', POOL_TYPE_OPTIONS)}
        ${renderTextField('Havuz Saatleri', 'facility_policies.pool.hours', pool.hours || '', {placeholder: '08:00-19:00 veya 24/7', format: 'time-range-flex', inputMode: 'numeric', maxLength: 11})}
        ${renderCheckboxField('Havuz Isıtmalı', 'facility_policies.pool.heated', Boolean(pool.heated))}
        ${renderSelectField('Otel Misafiri Havuz Kullanımı', 'facility_policies.pool.hotel_guest', pool.hotel_guest || 'free', SERVICE_CHARGE_OPTIONS)}
        ${renderSelectField('Dış Misafir Havuz Kullanımı', 'facility_policies.pool.external_guest', pool.external_guest || 'paid_handoff', SERVICE_CHARGE_OPTIONS)}
        ${renderCheckboxField('Wi‑Fi Var', 'facility_policies.wifi.available', Boolean(wifi.available))}
        ${renderCheckboxField('Wi‑Fi Ücretsiz', 'facility_policies.wifi.free', Boolean(wifi.free))}
        ${renderTextField('Wi‑Fi Saatleri', 'facility_policies.wifi.hours', wifi.hours || '', {placeholder: '24/7 veya 08:00-23:00', format: 'time-range-flex', inputMode: 'numeric', maxLength: 11})}
      `)}
      ${renderPolicyCard('Erişilebilirlik', 'Asansör, erişilebilir oda ve misafire verilecek açıklamalar.', `
        ${renderCheckboxField('Asansör Var', 'facility_policies.accessibility.elevator_available', Boolean(accessibility.elevator_available))}
        ${accessibleRoomChoices.length
          ? renderMultiCheckboxField('Erişilebilir Oda Tipleri', 'facility_policies.accessibility.accessible_room_types', accessibility.accessible_room_types || [], accessibleRoomChoices, {full: true, help: 'Misafire erişilebilir olarak sunulan oda tiplerini işaretleyin.'})
          : renderListField('Erişilebilir Oda Tipleri', 'facility_policies.accessibility.accessible_room_types', accessibility.accessible_room_types || [], {full: true, help: 'Her satıra bir oda tipi yazın.'})}
        ${renderTextField('Erişilebilirlik Açıklaması (TR)', 'facility_policies.accessibility.reply_tr', accessibility.reply_tr || '', {textarea: true, full: true, placeholder: 'Örn: Asansör mevcuttur ve giriş katta erişilebilir oda seçeneği bulunur.'})}
        ${renderTextField('Erişilebilirlik Açıklaması (EN)', 'facility_policies.accessibility.reply_en', accessibility.reply_en || '', {textarea: true, full: true, placeholder: 'E.g. An elevator is available and accessible rooms are offered on the entrance level.'})}
      `)}
      ${renderPolicyCard('Ödeme', 'Kabul edilen yöntemler ve misafire gösterilen açıklamalar.', `
        <div class="field full">
          <div class="helper-box">
            <strong>Misafire Gösterilen Ödeme Bilgisi</strong>
            <p class="muted">Misafirin hangi ödeme yöntemlerini gördüğünü ve yönlendirme metnini bu alandan düzenleyin.</p>
          </div>
        </div>
        ${renderMultiCheckboxField('Ödeme Yöntemleri', 'payment.methods', payment.methods || [], PAYMENT_METHOD_OPTIONS, {full: true, help: 'Kabul edilen yöntemleri işaretleyin.'})}
        ${renderTextField('Ödeme Açıklaması (TR)', 'payment.reply_tr', payment.reply_tr || '', {textarea: true, full: true, placeholder: 'Örn: Nakit, havale ve kart ile ödeme kabul edilir.'})}
        ${renderTextField('Ödeme Açıklaması (EN)', 'payment.reply_en', payment.reply_en || '', {textarea: true, full: true, placeholder: 'E.g. Cash, bank transfer and card payments are accepted.'})}
        <div class="field full">
          <div class="helper-box">
            <strong>EUR Hesap Bilgileri</strong>
            <p class="muted">Euro havale bilgilerini misafire iletilecek şekilde güncelleyin.</p>
          </div>
        </div>
        ${renderTextField('EUR Banka Adı', 'payment.eur_bank.bank', eurBank.bank || '', {placeholder: 'Örn: Garanti BBVA'})}
        ${renderTextField('EUR Hesap Sahibi', 'payment.eur_bank.account_holder', eurBank.account_holder || '', {placeholder: 'Şirket veya otel hesap adı'})}
        ${renderTextField('EUR Swift', 'payment.eur_bank.swift', eurBank.swift || '', {placeholder: 'Örn: TGBATRIS'})}
        <div class="field full">
          <div class="helper-box">
            <strong>TRY Hesap Bilgileri</strong>
            <p class="muted">Türk lirası havale bilgilerinin misafire doğru iletilmesini sağlayın.</p>
          </div>
        </div>
        ${renderTextField('TRY Banka Adı', 'payment.try_bank.bank', tryBank.bank || '', {placeholder: 'Örn: İş Bankası'})}
        ${renderTextField('TRY Hesap Sahibi', 'payment.try_bank.account_holder', tryBank.account_holder || '', {placeholder: 'Şirket veya otel hesap adı'})}
        <div class="field full">
          <div class="helper-box">
            <strong>Manuel Onay Gerektiren Talepler</strong>
            <p class="muted">Ödeme linki veya mail order isteyen misafirlerin hangi ekibe yönlendirileceğini seçin.</p>
          </div>
        </div>
        ${renderSelectField('Ödeme Linki Talebi', 'payment.payment_link_handling', payment.payment_link_handling || 'human_handoff', HANDOFF_OPTIONS, {help: 'Misafir ödeme linki istediğinde devreye girecek akışı seçin.'})}
        ${renderSelectField('Mail Order Talebi', 'payment.mail_order_handling', payment.mail_order_handling || 'human_handoff', HANDOFF_OPTIONS, {help: 'Mail order isteyen misafirin hangi ekibe yönleneceğini seçin.'})}
      `)}
      ${renderPolicyCard('Wellness ve Yerel Hizmetler', 'Spa imkânları, eczane yönlendirmesi ve döviz bozdurma bilgileri.', `
        ${renderCheckboxField('Spa Var', 'facility_policies.wellness.spa', Boolean(wellness.spa))}
        ${renderCheckboxField('Hamam Var', 'facility_policies.wellness.hamam', Boolean(wellness.hamam))}
        ${renderCheckboxField('Sauna Var', 'facility_policies.wellness.sauna', Boolean(wellness.sauna))}
        ${renderCheckboxField('Masaj Var', 'facility_policies.wellness.massage', Boolean(wellness.massage))}
        ${renderSelectField('Yakın Wellness Yönlendirmesi', 'facility_policies.wellness.offsite_guidance', wellness.offsite_guidance || 'reception', HANDOFF_OPTIONS, {help: 'Tesiste wellness yoksa misafir hangi ekibe yönlendirilsin seçin.'})}
        ${renderTextField('Eczane Mesafesi', 'facility_policies.local_services.pharmacy.distance', pharmacy.distance || '', {placeholder: '200 metre', help: 'Misafire söylenecek yaklaşık mesafeyi yazın.'})}
        ${renderTextField('Eczane Konum Açıklaması', 'facility_policies.local_services.pharmacy.location_tr', pharmacy.location_tr || '', {placeholder: 'Ana çarşının arka sokağında', help: 'Kısa ve kolay anlaşılır bir tarif yazın.'})}
        ${renderSelectField('Eczane Detay Talepleri', 'facility_policies.local_services.pharmacy.details_handling', pharmacy.details_handling || 'reception', HANDOFF_OPTIONS, {help: 'Daha detaylı tarif veya hastane yönlendirmesinde hangi ekip devreye girecek seçin.'})}
        ${renderCheckboxField('Döviz Bozdurma Var', 'facility_policies.local_services.currency_exchange.available', Boolean(currencyExchange.available))}
        ${renderSelectField('Döviz Bozdurma Noktası', 'facility_policies.local_services.currency_exchange.location', currencyExchange.location || '', SERVICE_POINT_OPTIONS, {help: 'Misafirin döviz bozdurma için ilk temas edeceği noktayı seçin.'})}
      `)}
      ${renderPolicyCard('Çamaşır ve Operasyon', 'Tesis içi hizmetler ve istisna akışları.', `
        ${renderCheckboxField('Çamaşır Hizmeti Var', 'facility_policies.laundry.available', Boolean(laundry.available))}
        ${renderTextField('Çamaşır Saatleri', 'facility_policies.laundry.hours', laundry.hours || '', {placeholder: '24/7 veya 09:00-18:00', format: 'time-range-flex', inputMode: 'numeric', maxLength: 11})}
        ${renderSelectField('Teslim Süresi', 'facility_policies.laundry.turnaround', laundry.turnaround || '', LAUNDRY_TURNAROUND_OPTIONS, {help: 'Misafire söylenecek ortalama hazırlık süresini seçin.'})}
        ${renderSelectField('Teslim Noktası', 'facility_policies.laundry.drop_off', laundry.drop_off || '', SERVICE_POINT_OPTIONS, {help: 'Kirli çamaşırın nereye bırakılacağını seçin.'})}
        ${renderSelectField('Teslim Alma Noktası', 'facility_policies.laundry.pickup', laundry.pickup || '', SERVICE_POINT_OPTIONS, {help: 'Temiz çamaşırın nereden alınacağını seçin.'})}
        ${renderSelectField('Hızlı Servis Talepleri', 'facility_policies.laundry.expedited_handling', laundry.expedited_handling || 'reception', HANDOFF_OPTIONS, {help: 'Acil çamaşır talebi geldiğinde hangi ekip devreye girecek seçin.'})}
        ${renderSelectField('Fiyat Bilgisi Talepleri', 'facility_policies.laundry.pricing_handling', laundry.pricing_handling || 'reception', HANDOFF_OPTIONS, {help: 'Çamaşır ücretini sorduğunda misafirin nereye yönleneceğini seçin.'})}
        ${renderSelectField('No-show Politikası', 'operational.no_show_policy', operational.no_show_policy || 'human_handoff', HANDOFF_OPTIONS)}
        ${renderSelectField('Erken Ayrılış İadesi', 'operational.early_departure_refund', operational.early_departure_refund || 'human_handoff', HANDOFF_OPTIONS)}
        ${renderTextField('Minimum Konaklama', 'operational.min_stay', operational.min_stay ?? '', {type: 'number', numberKind: 'int', emptyNull: true, min: 1, max: 365, placeholder: 'Örn: 2', help: 'Misafirin en az kaç gece kalabileceğini yazın.'})}
        ${renderTextField('Maksimum Konaklama', 'operational.max_stay', operational.max_stay ?? '', {type: 'number', numberKind: 'int', emptyNull: true, min: 1, max: 365, placeholder: 'Örn: 14', help: 'Misafirin en fazla kaç gece kalabileceğini yazın.'})}
        ${renderTextField('Yaş Sınırı', 'operational.age_restriction', operational.age_restriction ?? '', {type: 'number', numberKind: 'int', emptyNull: true, min: 0, max: 99, placeholder: 'Örn: 18', help: 'Yalnızca yaş sınırı varsa girin. Yoksa boş bırakın.'})}
        ${renderTextField('Yanıt SLA (dk)', 'operational.response_sla_minutes', operational.response_sla_minutes ?? 15, {type: 'number', numberKind: 'int', min: 1, max: 1440, placeholder: 'Örn: 15', help: 'Ekibin misafire dönüş süresi hedefini dakika olarak girin.'})}
        ${renderTextField('Teknik Sorun Mesajı', 'operational.tool_error_fallback', operational.tool_error_fallback || '', {textarea: true, full: true, placeholder: 'Örn: Şu anda sistemi kontrol edemiyorum, resepsiyon kısa süre içinde size yardımcı olacak.', help: 'Sistem yanıt veremezse misafire gösterilecek güvenli mesajı yazın.'})}
      `)}
    </div>
  `;
}

function renderPolicyCard(title, description, fieldsHtml) {
  return `
    <article class="profile-item-card">
      <header>
        <h4>${escapeHtml(title)}</h4>
        <p class="muted">${escapeHtml(description)}</p>
      </header>
      <div class="profile-inline-grid">
        ${fieldsHtml}
      </div>
    </article>
  `;
}

function renderHotelProfileIdleResetSection() {
  const cfg = asObject(state.hotelProfileDraft?.conversation_idle_reset);
  return `
    <div class="helper-box">
      <strong>Konuşma Sıfırlama Ayarları</strong>
      <p class="muted">Müşteri, botun son yanıtından sonra belirli bir süre içinde yanıt vermezse konuşma otomatik olarak kapatılır. Kapanmadan önce bir uyarı mesajı gönderilir.</p>
    </div>
    <div class="profile-section-grid mt-md">
      ${renderCheckboxField('Otomatik Sıfırlama Aktif', 'conversation_idle_reset.enabled', cfg.enabled ?? true, {help: 'Kapalıyken konuşmalar hiçbir zaman otomatik olarak sıfırlanmaz.'})}
      ${renderTextField('Zaman Aşımı (dakika)', 'conversation_idle_reset.idle_timeout_minutes', cfg.idle_timeout_minutes ?? 20, {type: 'number', numberKind: 'int', min: 5, max: 1440, help: 'Müşteriden yanıt gelmezse konuşmanın kapatılacağı süre (dakika).'})}
      ${renderTextField('Uyarı Süresi (dakika)', 'conversation_idle_reset.warning_before_minutes', cfg.warning_before_minutes ?? 5, {type: 'number', numberKind: 'int', min: 1, max: 60, help: 'Kapanmadan kaç dakika önce uyarı mesajı gönderilecek.'})}
      ${renderTextField('Uyarı Mesajı (TR)', 'conversation_idle_reset.warning_message_tr', cfg.warning_message_tr || '', {textarea: true, full: true, placeholder: 'Uzun süredir yanıt alamadık...', help: 'Türkçe müşterilere gönderilecek uyarı mesajı.'})}
      ${renderTextField('Uyarı Mesajı (EN)', 'conversation_idle_reset.warning_message_en', cfg.warning_message_en || '', {textarea: true, full: true, placeholder: 'We haven\\'t received a response...', help: 'İngilizce müşterilere gönderilecek uyarı mesajı.'})}
      ${renderTextField('Kapanış Mesajı (TR)', 'conversation_idle_reset.closed_message_tr', cfg.closed_message_tr || '', {textarea: true, full: true, placeholder: 'Konuşmanız otomatik olarak kapatılmıştır...', help: 'Türkçe müşterilere konuşma kapandığında gönderilecek mesaj.'})}
      ${renderTextField('Kapanış Mesajı (EN)', 'conversation_idle_reset.closed_message_en', cfg.closed_message_en || '', {textarea: true, full: true, placeholder: 'Your conversation has been automatically closed...', help: 'İngilizce müşterilere konuşma kapandığında gönderilecek mesaj.'})}
    </div>
  `;
}

function renderHotelProfileAssistantSection() {
  const flow = asObject(state.hotelProfileDraft?.hotel_conversational_flow);
  return `
    <div class="helper-box">
      <strong>Yapay Zekâ / Konuşma Akışı</strong>
      <p class="muted">Mesaj uzunluğu, liste sınırı ve takip sorusu davranışı bu ayarlardan yönetilir.</p>
    </div>
    <div class="profile-section-grid mt-md">
      ${renderTextField('Yanıt Stili', 'hotel_conversational_flow.style', flow.style || 'concise_premium')}
      ${renderTextField('Paragraf Başına Maksimum Satır', 'hotel_conversational_flow.max_paragraph_lines', flow.max_paragraph_lines ?? 3, {type: 'number', numberKind: 'int'})}
      ${renderTextField('Maksimum Liste Öğesi', 'hotel_conversational_flow.max_list_items', flow.max_list_items ?? 5, {type: 'number', numberKind: 'int'})}
      ${renderTextField('Maksimum Takip Sorusu', 'hotel_conversational_flow.max_follow_up_questions', flow.max_follow_up_questions ?? 2, {type: 'number', numberKind: 'int'})}
      ${renderCheckboxField('Onaylanmış Bilgileri Tekrarlama', 'hotel_conversational_flow.avoid_repeating_confirmed_facts', Boolean(flow.avoid_repeating_confirmed_facts))}
      ${renderCheckboxField('Uzun Fiyat Listelerini Özetle', 'hotel_conversational_flow.summarize_large_price_lists', Boolean(flow.summarize_large_price_lists))}
      ${renderCheckboxField('Tam Fiyat Listesini Göstermeden Önce Sor', 'hotel_conversational_flow.ask_before_full_price_dump', Boolean(flow.ask_before_full_price_dump))}
    </div>
  `;
}

function renderContactCard(key, item, index) {
  const contact = asObject(item);
  const technicalMode = isHotelProfileTechnicalMode();
  const title = technicalMode
    ? `İletişim Kaydı ${String(index + 1)}`
    : (formatContactRoleLabel(contact.role || '') || contact.name || humanizeProfileToken(key) || `İletişim ${String(index + 1)}`);
  return `
    <article class="profile-item-card">
      <header>
        <h4>${escapeHtml(title)}</h4>
        <button class="action-button danger" type="button" data-profile-remove-map-entry="contacts" data-profile-map-key-value="${escapeHtml(key)}">Sil</button>
      </header>
      <div class="profile-inline-grid">
        ${technicalMode ? renderMapKeyField('İletişim Anahtarı', 'contacts', key) : ''}
        ${renderTextField('Ad', `contacts.${key}.name`, contact.name || '')}
        ${technicalMode
          ? renderTextField('Rol', `contacts.${key}.role`, contact.role || '', {help: 'Misafirin göreceği iletişim başlığıdır. Örn: Resepsiyon'})
          : renderSelectField('İletişim Türü', `contacts.${key}.role`, contact.role || '', CONTACT_ROLE_OPTIONS, {help: 'Misafirin hangi ekibe ulaşacağını anlaşılır şekilde seçin.'})}
        ${renderTextField('Telefon', `contacts.${key}.phone`, contact.phone || '', {placeholder: '+90 5xx xxx xx xx'})}
        ${renderTextField('E-posta', `contacts.${key}.email`, contact.email || '', {placeholder: 'info@example.com'})}
        ${renderTextField('Saatler', `contacts.${key}.hours`, contact.hours || '', {placeholder: '08:00-23:00 veya 24/7', help: 'Saat aralığı girerken biçim otomatik düzenlenir.', format: 'time-range-flex', inputMode: 'numeric', maxLength: 11})}
      </div>
    </article>
  `;
}

function renderRoomTypeCard(item, index) {
  const room = asObject(item);
  const technicalMode = isHotelProfileTechnicalMode();
  return `
    <article class="profile-item-card">
      <header>
        <h4>Oda Tipi ${escapeHtml(String(index + 1))}</h4>
        <button class="action-button danger" type="button" data-profile-remove-list-item="room_types" data-profile-index="${escapeHtml(String(index))}">Sil</button>
      </header>
      <div class="profile-inline-grid">
        ${technicalMode ? renderTextField('ID', `room_types[${index}].id`, room.id ?? index + 1, {type: 'number', numberKind: 'int'}) : ''}
        ${technicalMode ? renderTextField('PMS Oda Tipi Kimliği', `room_types[${index}].pms_room_type_id`, room.pms_room_type_id ?? 0, {type: 'number', numberKind: 'int'}) : ''}
        ${renderTextField('Ad (TR)', `room_types[${index}].name.tr`, room.name?.tr || '')}
        ${renderTextField('Ad (EN)', `room_types[${index}].name.en`, room.name?.en || '')}
        ${renderTextField('Maksimum Kişi Sayısı', `room_types[${index}].max_pax`, room.max_pax ?? 2, {type: 'number', numberKind: 'int', min: 1, max: 20, placeholder: 'Örn: 2'})}
        ${renderTextField('Büyüklük (m²)', `room_types[${index}].size_m2`, room.size_m2 ?? 0, {type: 'number', numberKind: 'int', min: 1, max: 1000, placeholder: 'Örn: 24'})}
        ${technicalMode
          ? renderTextField('Yatak Tipi', `room_types[${index}].bed_type`, room.bed_type || '')
          : renderSelectField('Yatak Tipi', `room_types[${index}].bed_type`, room.bed_type || '', BED_TYPE_OPTIONS, {help: 'Misafirin odada göreceği ana yatak düzenini seçin.'})}
        ${technicalMode
          ? renderTextField('Manzara', `room_types[${index}].view`, room.view || '')
          : renderSelectField('Manzara', `room_types[${index}].view`, room.view || '', ROOM_VIEW_OPTIONS, {help: 'Misafire sunulan ana manzara bilgisini seçin.'})}
        ${renderCheckboxField('İlave Yatak', `room_types[${index}].extra_bed`, Boolean(room.extra_bed))}
        ${renderCheckboxField('Bebek Yatağı', `room_types[${index}].baby_crib`, Boolean(room.baby_crib))}
        ${renderCheckboxField('Erişilebilir', `room_types[${index}].accessible`, Boolean(room.accessible))}
        ${technicalMode
          ? renderListField('Özellikler', `room_types[${index}].features`, room.features || [], {full: true, help: 'Her satıra misafirin odada göreceği tek bir özellik yazın.'})
          : renderMultiCheckboxField('Öne Çıkan Oda Özellikleri', `room_types[${index}].features`, room.features || [], ROOM_FEATURE_OPTIONS, {full: true, help: 'Odada özellikle vurgulamak istediğiniz başlıkları seçin.'})}
        ${renderTextField('Açıklama (TR)', `room_types[${index}].description.tr`, room.description?.tr || '', {textarea: true, full: true, placeholder: 'Örn: Bahçe manzaralı, ferah ve sessiz odamız iki misafir için idealdir.', help: 'Misafirin oda kartında göreceği kısa açıklamayı yazın.'})}
        ${renderTextField('Açıklama (EN)', `room_types[${index}].description.en`, room.description?.en || '', {textarea: true, full: true, placeholder: 'E.g. Our spacious and quiet garden-view room is ideal for two guests.', help: 'Write the short room description shown to international guests.'})}
      </div>
    </article>
  `;
}

function renderBoardTypeCard(item, index) {
  const board = asObject(item);
  const technicalMode = isHotelProfileTechnicalMode();
  const title = technicalMode
    ? `Pansiyon Türü ${String(index + 1)}`
    : (board.name?.tr || formatBoardTypeCodeLabel(board.code) || `Pansiyon ${String(index + 1)}`);
  return `
    <article class="profile-item-card">
      <header>
        <h4>${escapeHtml(title)}</h4>
        <button class="action-button danger" type="button" data-profile-remove-list-item="board_types" data-profile-index="${escapeHtml(String(index))}">Sil</button>
      </header>
      <div class="profile-inline-grid">
        ${technicalMode ? renderTextField('ID', `board_types[${index}].id`, board.id ?? index + 1, {type: 'number', numberKind: 'int'}) : ''}
        ${technicalMode
          ? renderTextField('Code', `board_types[${index}].code`, board.code || '')
          : renderSelectField('Pansiyon Tipi', `board_types[${index}].code`, board.code || '', BOARD_TYPE_OPTIONS, {help: 'Misafire sunulan pansiyon paketini seçin.'})}
        ${renderTextField('Ad (TR)', `board_types[${index}].name.tr`, board.name?.tr || '')}
        ${renderTextField('Ad (EN)', `board_types[${index}].name.en`, board.name?.en || '')}
        ${renderTextField('Kahvaltı Saatleri', `board_types[${index}].breakfast_hours`, board.breakfast_hours || '', {placeholder: '08:00-10:30', format: technicalMode ? '' : 'time-range', inputMode: technicalMode ? '' : 'numeric', maxLength: technicalMode ? '' : 11})}
        ${technicalMode
          ? renderTextField('Kahvaltı Türü', `board_types[${index}].breakfast_type`, board.breakfast_type || '')
          : renderSelectField('Kahvaltı Türü', `board_types[${index}].breakfast_type`, board.breakfast_type || '', BREAKFAST_TYPE_OPTIONS, {help: 'Servis biçimini anlaşılır şekilde seçin.'})}
      </div>
      ${technicalMode ? '' : renderBoardTypeCancellationHint(board.code || '')}
    </article>
  `;
}

function renderBoardTypeCancellationHint(boardCode) {
  const rules = asObject(state.hotelProfileDraft?.cancellation_rules);
  const boardLabel = formatBoardTypeCodeLabel(boardCode) || 'Bu pansiyon paketi';
  const freeCancelReady = Object.prototype.hasOwnProperty.call(rules, 'FREE_CANCEL');
  const nonRefundableReady = Object.prototype.hasOwnProperty.call(rules, 'NON_REFUNDABLE');
  return `
    <div class="helper-box mt-md">
      <strong>İptal Kuralı İpucu</strong>
      <p class="muted">${escapeHtml(
        freeCancelReady
          ? `${boardLabel} için ücretsiz iptal kuralı hazır. Gerekirse aşağıdan iadesiz rezervasyon kuralı da ekleyebilirsiniz.`
          : `${boardLabel} için genelde önce Ücretsiz İptal kuralı eklenir. İhtiyaç varsa İadesiz Rezervasyon kartını ayrıca açın.`
      )}</p>
      <div class="profile-summary-strip mt-sm">
        <span class="pill ${freeCancelReady ? 'success' : 'warn'}">Ücretsiz İptal ${escapeHtml(freeCancelReady ? 'hazır' : 'bekleniyor')}</span>
        <span class="pill ${nonRefundableReady ? 'success' : 'closed'}">İadesiz Rezervasyon ${escapeHtml(nonRefundableReady ? 'hazır' : 'yok')}</span>
      </div>
    </div>
  `;
}

function renderStandardRateMappingSummary(rateMapping, cancellationRules) {
  const mappingObject = asObject(rateMapping);
  const ruleEntries = Object.entries(asObject(cancellationRules));
  if (!ruleEntries.length) {
    return `
      <div class="helper-box mt-md">
        <strong>Rezervasyon Sistemi Eşleştirmeleri</strong>
        <p class="muted">İptal kuralı eklediğinizde PMS bağlantı durumu burada özetlenir. Teknik kimlikler yalnızca Teknik Ayarlar modunda tamamlanır.</p>
      </div>
    `;
  }
  const completedCount = ruleEntries.filter(([key]) => {
    const mapping = asObject(mappingObject[key]);
    return Number(mapping.rate_type_id || 0) > 0 && Number(mapping.rate_code_id || 0) > 0;
  }).length;
  const cards = ruleEntries.map(([key], index) => {
    const mapping = asObject(mappingObject[key]);
    const hasMapping = Object.prototype.hasOwnProperty.call(mappingObject, key);
    const hasTechnicalIds = Number(mapping.rate_type_id || 0) > 0 && Number(mapping.rate_code_id || 0) > 0;
    const statusClass = hasTechnicalIds ? 'success' : (hasMapping ? 'warn' : 'closed');
    const statusLabel = hasTechnicalIds ? 'Hazır' : (hasMapping ? 'Teknik eşleştirme bekleniyor' : 'Teknik eşleştirme açılmadı');
    const helperText = hasTechnicalIds
      ? 'Bu iptal kuralı rezervasyon sistemi tarafına bağlandı.'
      : (hasMapping
        ? 'Kimlikler Teknik Ayarlar modunda tamamlanır.'
        : 'Bu kural için teknik eşleştirme taslağı henüz oluşmadı.');
    return `
      <article class="profile-item-card">
        <header>
          <h4>${escapeHtml(formatCancellationRuleKeyLabel(key) || `İptal Kuralı ${String(index + 1)}`)}</h4>
          <span class="pill ${statusClass}">${escapeHtml(statusLabel)}</span>
        </header>
        <p class="muted">${escapeHtml(helperText)}</p>
      </article>
    `;
  }).join('');
  return `
    <div class="helper-box mt-md">
      <strong>Rezervasyon Sistemi Eşleştirmeleri</strong>
      <p class="muted">İptal kurallarının PMS bağlantı durumu aşağıda özetlenir. Teknik kimlikler yalnızca Teknik Ayarlar modunda düzenlenir.</p>
      <div class="module-actions mt-sm">
        <span class="profile-summary-chip">Hazır: ${escapeHtml(String(completedCount))}</span>
        <span class="profile-summary-chip">Bekleyen: ${escapeHtml(String(ruleEntries.length - completedCount))}</span>
      </div>
    </div>
    <div class="profile-section-stack mt-md">${cards}</div>
  `;
}

function renderRateMappingCard(key, item, index) {
  const mapping = asObject(item);
  const linkedRule = asObject(asObject(state.hotelProfileDraft?.cancellation_rules)[key]);
  const hasLinkedRule = Object.keys(linkedRule).length > 0;
  const hasTechnicalIds = Number(mapping.rate_type_id || 0) > 0 && Number(mapping.rate_code_id || 0) > 0;
  const helperText = hasLinkedRule
    ? (hasTechnicalIds
      ? `${formatCancellationRuleKeyLabel(key)} için teknik eşleştirme düzenleniyor.`
      : `${formatCancellationRuleKeyLabel(key)} için teknik eşleştirme düzenleniyor. Kimlikler girilmezse yayın öncesi blocker oluşur.`)
    : 'Bu teknik eşleştirme için aynı anahtarda iptal kuralı ekleyin.';
  return `
    <article class="profile-item-card">
      <header>
        <h4>Fiyat Eşleştirmesi ${escapeHtml(String(index + 1))}</h4>
        <button class="action-button danger" type="button" data-profile-remove-map-entry="rate_mapping" data-profile-map-key-value="${escapeHtml(key)}">Sil</button>
      </header>
      <div class="helper-box mt-sm">
        <strong>Bağlı İptal Kuralı</strong>
        <p class="muted">${escapeHtml(helperText)}</p>
        <div class="profile-summary-strip mt-sm">
          <span class="pill ${hasLinkedRule ? 'success' : 'closed'}">Bağlı kural ${escapeHtml(hasLinkedRule ? 'hazır' : 'yok')}</span>
          <span class="pill ${hasTechnicalIds ? 'success' : 'warn'}">Kimlikler ${escapeHtml(hasTechnicalIds ? 'girildi' : 'bekleniyor')}</span>
        </div>
      </div>
      <div class="profile-inline-grid mt-md">
        ${renderMapKeyField('Eşleştirme Anahtarı', 'rate_mapping', key)}
        ${renderTextField('Fiyat Türü Kimliği', `rate_mapping.${key}.rate_type_id`, mapping.rate_type_id ?? 0, {type: 'number', numberKind: 'int', placeholder: 'Örn: 24178', help: 'PMS tarafındaki fiyat türü kimliğini girin.'})}
        ${renderTextField('Fiyat Kodu Kimliği', `rate_mapping.${key}.rate_code_id`, mapping.rate_code_id ?? 0, {type: 'number', numberKind: 'int', placeholder: 'Örn: 183666', help: 'PMS tarafındaki fiyat kodu kimliğini girin.'})}
      </div>
    </article>
  `;
}

function renderCancellationRuleCard(key, item, index) {
  const rule = asObject(item);
  const technicalMode = isHotelProfileTechnicalMode();
  const linkedMapping = asObject(asObject(state.hotelProfileDraft?.rate_mapping)[key]);
  const hasLinkedMapping = Object.keys(linkedMapping).length > 0;
  const linkedMappingReady = Number(linkedMapping.rate_type_id || 0) > 0 && Number(linkedMapping.rate_code_id || 0) > 0;
  const title = technicalMode
    ? `İptal Kuralı ${String(index + 1)}`
    : formatCancellationRuleKeyLabel(key);
  return `
    <article class="profile-item-card">
      <header>
        <h4>${escapeHtml(title)}</h4>
        <button class="action-button danger" type="button" data-profile-remove-map-entry="cancellation_rules" data-profile-map-key-value="${escapeHtml(key)}">Sil</button>
      </header>
      ${technicalMode ? `
        <div class="helper-box mt-sm">
          <strong>Bağlı Teknik Eşleştirme</strong>
          <p class="muted">${escapeHtml(
            hasLinkedMapping
              ? 'Bu kural için bağlı fiyat eşleştirmesi hazır. Kimlikler tamamlanmadıysa yayın öncesi blocker oluşur.'
              : 'Bu kural için bağlı fiyat eşleştirmesi bulunamadı. Aynı anahtarda teknik eşleştirme açın.'
          )}</p>
          <div class="profile-summary-strip mt-sm">
            <span class="pill ${hasLinkedMapping ? 'success' : 'closed'}">Bağlı eşleştirme ${escapeHtml(hasLinkedMapping ? 'hazır' : 'yok')}</span>
            <span class="pill ${linkedMappingReady ? 'success' : 'warn'}">Kimlikler ${escapeHtml(linkedMappingReady ? 'girildi' : 'bekleniyor')}</span>
          </div>
        </div>
      ` : ''}
      <div class="profile-inline-grid${technicalMode ? ' mt-md' : ''}">
        ${technicalMode ? renderMapKeyField('Kural Anahtarı', 'cancellation_rules', key) : ''}
        ${renderTextField('Ücretsiz İptal Son Günü', `cancellation_rules.${key}.free_cancel_deadline_days`, rule.free_cancel_deadline_days, {type: 'number', numberKind: 'int', emptyNull: true, min: 0, max: 365, placeholder: 'Örn: 5', help: 'Varıştan kaç gün öncesine kadar ücretsiz iptal sunulduğunu yazın.'})}
        ${renderTextField('Ön Ödeme Kaç Gün Önce Alınır?', `cancellation_rules.${key}.prepayment_days_before`, rule.prepayment_days_before, {type: 'number', numberKind: 'int', emptyNull: true, min: 0, max: 365, placeholder: 'Örn: 7', help: 'Varışa kaç gün kala ön ödeme alınacağını belirtin.'})}
        ${technicalMode
          ? renderTextField('Ön Ödeme Tutarı', `cancellation_rules.${key}.prepayment_amount`, rule.prepayment_amount || '')
          : renderSelectField('Ön Ödeme Tutarı', `cancellation_rules.${key}.prepayment_amount`, rule.prepayment_amount || '', PREPAYMENT_AMOUNT_OPTIONS, {help: 'Misafirin önceden ödeyeceği tutarı seçin.'})}
        ${renderCheckboxField('Ön Ödeme Rezervasyon Anında Alınsın', `cancellation_rules.${key}.prepayment_immediate`, Boolean(rule.prepayment_immediate), {help: 'Açık olduğunda misafir rezervasyon sırasında hemen ödeme yapar.'})}
        ${renderCheckboxField('İptal Sonrası İade Yapılır', `cancellation_rules.${key}.refund`, Boolean(rule.refund ?? true), {help: 'Kapalıysa bu kural iadesiz rezervasyon olarak çalışır.'})}
        ${renderCheckboxField('Süre Geçse de İade Yapılabilir', `cancellation_rules.${key}.refund_after_deadline`, Boolean(rule.refund_after_deadline), {help: 'Açık olduğunda son tarihten sonra da iade verilebilir.'})}
        ${renderTextField('İstisna Gün Sayısı', `cancellation_rules.${key}.exception_days_before`, rule.exception_days_before, {type: 'number', numberKind: 'int', emptyNull: true, min: 0, max: 365, placeholder: 'Örn: 21', help: 'İstisna iadesinin kaç gün öncesine kadar geçerli olduğunu belirtin.'})}
        ${technicalMode
          ? renderTextField('İstisna İadesi', `cancellation_rules.${key}.exception_refund`, rule.exception_refund || '')
          : renderSelectField('İstisna İadesi', `cancellation_rules.${key}.exception_refund`, rule.exception_refund || '', EXCEPTION_REFUND_OPTIONS, {help: 'İstisna durumunda yapılacak iade biçimini seçin.'})}
      </div>
    </article>
  `;
}

function renderTransferRouteCard(item, index) {
  const route = asObject(item);
  const technicalMode = isHotelProfileTechnicalMode();
  const oversizeVehicle = asObject(route.oversize_vehicle);
  if (technicalMode) {
    return `
      <article class="profile-item-card">
        <header>
          <h4>Transfer Güzergâhı ${escapeHtml(String(index + 1))}</h4>
          <button class="action-button danger" type="button" data-profile-remove-list-item="transfer_routes" data-profile-index="${escapeHtml(String(index))}">Sil</button>
        </header>
        <div class="profile-inline-grid">
          ${renderTextField('Güzergâh Kodu', `transfer_routes[${index}].route_code`, route.route_code || '')}
          ${renderTextField('Nereden', `transfer_routes[${index}].from_location`, route.from_location || '')}
          ${renderTextField('Nereye', `transfer_routes[${index}].to_location`, route.to_location || '')}
          ${renderTextField('Fiyat (EUR)', `transfer_routes[${index}].price_eur`, route.price_eur ?? 0, {type: 'number', numberKind: 'float', min: 0, max: 10000, step: '0.01'})}
          ${renderTextField('Araç Tipi', `transfer_routes[${index}].vehicle_type`, route.vehicle_type || '')}
          ${renderTextField('Maksimum Kişi Sayısı', `transfer_routes[${index}].max_pax`, route.max_pax ?? 1, {type: 'number', numberKind: 'int', min: 1, max: 50})}
          ${renderTextField('Süre (dk)', `transfer_routes[${index}].duration_min`, route.duration_min ?? 0, {type: 'number', numberKind: 'int', min: 1, max: 1440})}
          ${renderCheckboxField('Bebek Koltuğu', `transfer_routes[${index}].baby_seat`, Boolean(route.baby_seat))}
          ${renderJsonField('Büyük Araç Ayarı', `transfer_routes[${index}].oversize_vehicle`, route.oversize_vehicle || {}, {full: true})}
        </div>
      </article>
    `;
  }
  return `
    <article class="profile-item-card">
      <header>
        <h4>Transfer Güzergâhı ${escapeHtml(String(index + 1))}</h4>
        <button class="action-button danger" type="button" data-profile-remove-list-item="transfer_routes" data-profile-index="${escapeHtml(String(index))}">Sil</button>
      </header>
      <div class="profile-section-stack mt-md">
        <div class="helper-box">
          <strong>Güzergâh Bilgisi</strong>
          <p class="muted">Başlangıç ve varış noktalarını misafirin kolay anlayacağı şekilde yazın.</p>
        </div>
        <div class="profile-inline-grid">
          ${renderTextField('Nereden', `transfer_routes[${index}].from_location`, route.from_location || '', {placeholder: 'Örn: Dalaman Havalimanı'})}
          ${renderTextField('Nereye', `transfer_routes[${index}].to_location`, route.to_location || '', {placeholder: 'Örn: Kassandra Ölüdeniz'})}
          ${renderTextField('Süre (dk)', `transfer_routes[${index}].duration_min`, route.duration_min ?? 0, {type: 'number', numberKind: 'int', min: 1, max: 1440, placeholder: 'Örn: 70', help: 'Tahmini yolculuk süresini dakika olarak girin.'})}
        </div>
        <div class="helper-box mt-md">
          <strong>Standart Araç ve Fiyat</strong>
          <p class="muted">Standart araç tipi, kişi kapasitesi ve temel fiyat bilgisi.</p>
        </div>
        <div class="profile-inline-grid">
          ${renderTextField('Fiyat (EUR)', `transfer_routes[${index}].price_eur`, route.price_eur ?? 0, {type: 'number', numberKind: 'float', min: 0, max: 10000, step: '0.01', placeholder: 'Örn: 45', help: 'Tek yön transfer ücretini EUR cinsinden girin.'})}
          ${renderTextField('Araç Tipi', `transfer_routes[${index}].vehicle_type`, route.vehicle_type || '', {placeholder: 'Örn: Sedan veya VIP araç'})}
          ${renderTextField('Maksimum Kişi Sayısı', `transfer_routes[${index}].max_pax`, route.max_pax ?? 1, {type: 'number', numberKind: 'int', min: 1, max: 50, placeholder: 'Örn: 3', help: 'Bu araçta rahat seyahat eden en yüksek kişi sayısını yazın.'})}
          ${renderCheckboxField('Bebek Koltuğu', `transfer_routes[${index}].baby_seat`, Boolean(route.baby_seat), {help: 'Bu araçta bebek koltuğu sağlanabiliyorsa işaretleyin.'})}
        </div>
        <div class="helper-box mt-md">
          <strong>Büyük Araç Seçeneği</strong>
          <p class="muted">Kalabalık gruplar için alternatif araç tanımlayın. Kullanılmıyorsa boş bırakabilirsiniz.</p>
        </div>
        <div class="profile-inline-grid">
          ${renderTextField('Büyük Araç Tipi', `transfer_routes[${index}].oversize_vehicle.type`, oversizeVehicle.type || '', {placeholder: 'Örn: VIP minibüs', help: 'Kalabalık gruplar için önerilen araç tipi.'})}
          ${renderTextField('Büyük Araç Fiyatı (EUR)', `transfer_routes[${index}].oversize_vehicle.price_eur`, oversizeVehicle.price_eur ?? '', {type: 'number', numberKind: 'float', emptyNull: true, min: 0, max: 10000, step: '0.01', placeholder: 'Örn: 70', help: 'Alternatif büyük araç ücretini EUR cinsinden girin.'})}
          ${renderTextField('Büyük Araç Kaç Kişiden Sonra Gerekir?', `transfer_routes[${index}].oversize_vehicle.min_pax`, oversizeVehicle.min_pax ?? '', {type: 'number', numberKind: 'int', emptyNull: true, min: 2, max: 50, placeholder: 'Örn: 4', help: 'Bu sayı ve üzerindeki gruplarda büyük araç önerilir.'})}
        </div>
      </div>
    </article>
  `;
}

function renderNearbyPlaceCard(item, index) {
  const place = asObject(item);
  const title = String(place.name || '').trim() || `Yakın nokta ${index + 1}`;
  return `
    <div class="profile-item-card">
      <div class="profile-item-head">
        <div>
          <strong>${escapeHtml(title)}</strong>
          <small>${escapeHtml(String(place.distance || '').trim() || 'Mesafe belirtilmedi')}</small>
        </div>
        <div class="module-actions">
          <button class="action-button danger" type="button" data-profile-remove-object-item="location.nearby" data-profile-index="${escapeHtml(String(index))}">Sil</button>
        </div>
      </div>
      <div class="profile-section-grid mt-md">
        ${renderTextField('Yer Adı', `location.nearby[${index}].name`, place.name || '', {help: 'Misafirin göreceği yer adını yazın.'})}
        ${renderTextField('Mesafe / Süre', `location.nearby[${index}].distance`, place.distance || '', {placeholder: '300 metre veya 20 dakika', help: 'Örnek: 300 metre, 20 dakika, 1 km.'})}
      </div>
    </div>
  `;
}

function renderFaqCard(item, index) {
  const faq = asObject(item);
  const technicalMode = isHotelProfileTechnicalMode();
  return `
    <article class="profile-item-card">
      <header>
        <h4>SSS ${escapeHtml(String(index + 1))}</h4>
        <button class="action-button danger" type="button" data-profile-remove-list-item="faq_data" data-profile-index="${escapeHtml(String(index))}">Sil</button>
      </header>
      <div class="profile-inline-grid">
        ${!technicalMode ? `
          <div class="field full">
            <div class="helper-box">
              <strong>Temel SSS Bilgisi</strong>
              <p class="muted">Önce misafirin göreceği ana soru ve cevabı tamamlayın. Ek diller alttaki gelişmiş bölümde kalır.</p>
            </div>
          </div>
        ` : ''}
        ${technicalMode ? renderTextField('SSS Kimliği', `faq_data[${index}].faq_id`, faq.faq_id || '') : ''}
        ${technicalMode
          ? renderTextField('Kategori', `faq_data[${index}].topic`, faq.topic || '', {placeholder: 'Örn: check_in_time'})
          : renderSelectField('Kategori', `faq_data[${index}].topic`, faq.topic || '', FAQ_TOPIC_OPTIONS, {help: 'Misafirin sorusuna en yakın konu başlığını seçin.'})}
        ${renderSelectField('Durum', `faq_data[${index}].status`, faq.status || 'ACTIVE', [
          {value: 'DRAFT', label: 'Taslak'},
          {value: 'ACTIVE', label: 'Aktif'},
          {value: 'PAUSED', label: 'Duraklatıldı'},
          {value: 'REMOVED', label: 'Kaldırıldı'},
        ])}
        ${renderTextField('Misafirin Sorusu (TR)', `faq_data[${index}].question_tr`, faq.question_tr || '', {textarea: true, full: true, placeholder: 'Örn: Check-in saati kaç?'})}
        ${renderTextField('Standart Cevap (TR)', `faq_data[${index}].answer_tr`, faq.answer_tr || '', {textarea: true, full: true, placeholder: 'Örn: Standart check-in saatimiz 14:00 itibarıyladır.'})}
        ${technicalMode ? renderTextField('Soru (EN)', `faq_data[${index}].question_en`, faq.question_en || '', {textarea: true, full: true, placeholder: 'E.g. What time is check-in?'}) : ''}
        ${technicalMode ? renderTextField('Cevap (EN)', `faq_data[${index}].answer_en`, faq.answer_en || '', {textarea: true, full: true, placeholder: 'E.g. Our standard check-in time starts at 14:00.'}) : ''}
        ${technicalMode ? renderListField('Türkçe Varyantlar', `faq_data[${index}].question_variants_tr`, faq.question_variants_tr || [], {help: 'Her satıra bir Türkçe varyant girin.', placeholder: 'Örn: Giriş saati kaç?\\\\nOdaya saat kaçta yerleşebiliriz?'}) : ''}
        ${technicalMode ? renderListField('İngilizce Varyantlar', `faq_data[${index}].question_variants_en`, faq.question_variants_en || [], {help: 'Her satıra bir İngilizce varyant girin.', placeholder: 'E.g. What time is check-in?\\\\nWhen can we get into the room?'}) : ''}
        ${technicalMode ? renderListField('Rusça Varyantlar', `faq_data[${index}].question_variants_ru`, faq.question_variants_ru || [], {help: 'Her satıra bir Rusça varyant girin.'}) : ''}
        ${technicalMode ? renderListField('Almanca Varyantlar', `faq_data[${index}].question_variants_de`, faq.question_variants_de || [], {help: 'Her satıra bir Almanca varyant girin.'}) : ''}
        ${technicalMode ? renderListField('Arapça Varyantlar', `faq_data[${index}].question_variants_ar`, faq.question_variants_ar || [], {help: 'Her satıra bir Arapça varyant girin.'}) : ''}
        ${technicalMode ? renderListField('İspanyolca Varyantlar', `faq_data[${index}].question_variants_es`, faq.question_variants_es || [], {help: 'Her satıra bir İspanyolca varyant girin.'}) : ''}
        ${technicalMode ? renderListField('Fransızca Varyantlar', `faq_data[${index}].question_variants_fr`, faq.question_variants_fr || [], {help: 'Her satıra bir Fransızca varyant girin.'}) : ''}
        ${technicalMode ? renderListField('Çince Varyantlar', `faq_data[${index}].question_variants_zh`, faq.question_variants_zh || [], {help: 'Her satıra bir Çince varyant girin.'}) : ''}
        ${technicalMode ? renderListField('Hintçe Varyantlar', `faq_data[${index}].question_variants_hi`, faq.question_variants_hi || [], {help: 'Her satıra bir Hintçe varyant girin.'}) : ''}
        ${technicalMode ? renderListField('Portekizce Varyantlar', `faq_data[${index}].question_variants_pt`, faq.question_variants_pt || [], {help: 'Her satıra bir Portekizce varyant girin.'}) : ''}
        ${!technicalMode ? `
          <div class="field full">
            <details class="helper-box">
              <summary><strong>Ek diller ve alternatif sorular</strong></summary>
              <div class="profile-inline-grid mt-md">
                <div class="field full">
                  <small class="helper">Bu bölüm isteğe bağlıdır. İngilizce içerik ve alternatif soru varyasyonlarını burada zenginleştirebilirsiniz.</small>
                </div>
                ${renderTextField('Soru (EN)', `faq_data[${index}].question_en`, faq.question_en || '', {textarea: true, full: true, placeholder: 'E.g. What time is check-in?'})}
                ${renderTextField('Cevap (EN)', `faq_data[${index}].answer_en`, faq.answer_en || '', {textarea: true, full: true, placeholder: 'E.g. Our standard check-in time starts at 14:00.'})}
                ${renderListField('Türkçe Alternatif Sorular', `faq_data[${index}].question_variants_tr`, faq.question_variants_tr || [], {help: 'Her satıra bir Türkçe alternatif soru girin.', placeholder: 'Örn: Giriş saati kaç?\\\\nOdaya saat kaçta yerleşebiliriz?'})}
                ${renderListField('İngilizce Alternatif Sorular', `faq_data[${index}].question_variants_en`, faq.question_variants_en || [], {help: 'Her satıra bir İngilizce alternatif soru girin.', placeholder: 'E.g. What time is check-in?\\\\nWhen can we get into the room?'})}
                <div class="field full">
                  <small class="helper">Rusça, Almanca, Arapça ve diğer dil varyantları Teknik Ayarlar modunda ayrıntılı olarak düzenlenir.</small>
                </div>
              </div>
            </details>
          </div>
        ` : ''}
      </div>
    </article>
  `;
}

function buildFaqOptionLabel(item, index) {
  const faq = asObject(item);
  const topic = formatFaqTopicLabel(faq.topic || '').trim();
  const question = String(faq.question_tr || faq.question_en || '').trim();
  const suffix = topic || question || 'İsimsiz kayıt';
  return `SSS ${index + 1} • ${suffix}`;
}

function getActiveHotelProfileFaqIndex(items) {
  if (!Array.isArray(items) || !items.length) {
    state.hotelProfileFaqActiveIndex = 0;
    return -1;
  }
  const currentIndex = Number(state.hotelProfileFaqActiveIndex || 0);
  if (Number.isFinite(currentIndex) && currentIndex >= 0 && currentIndex < items.length) {
    return currentIndex;
  }
  state.hotelProfileFaqActiveIndex = 0;
  return 0;
}

function renderTextField(label, path, value, options = {}) {
  const fieldClass = options.full ? 'field full' : 'field';
  const inputType = options.type || 'text';
  if (options.textarea) {
    return `
      <div class="${fieldClass}" data-profile-path="${escapeHtml(path)}" data-profile-search-text="${escapeHtml(buildProfileSearchText(label, value))}">
        <label>${escapeHtml(label)}</label>
        <textarea
          data-profile-field="${escapeHtml(path)}"
          ${options.placeholder ? `placeholder="${escapeHtml(options.placeholder)}"` : ''}
          ${options.disabled ? 'disabled' : ''}
        >${escapeHtml(value ?? '')}</textarea>
        ${options.help ? `<small class="helper">${escapeHtml(options.help)}</small>` : ''}
      </div>
    `;
  }
  return `
    <div class="${fieldClass}" data-profile-path="${escapeHtml(path)}" data-profile-search-text="${escapeHtml(buildProfileSearchText(label, value))}">
      <label>${escapeHtml(label)}</label>
        <input
          type="${escapeHtml(inputType)}"
          value="${escapeHtml(value ?? '')}"
          data-profile-field="${escapeHtml(path)}"
          ${options.format ? `data-profile-format="${escapeHtml(options.format)}"` : ''}
          ${options.numberKind ? `data-number-kind="${escapeHtml(options.numberKind)}"` : ''}
          ${options.emptyNull ? 'data-empty-null="true"' : ''}
          ${options.min != null ? `data-min-value="${escapeHtml(String(options.min))}" min="${escapeHtml(String(options.min))}"` : ''}
          ${options.max != null ? `data-max-value="${escapeHtml(String(options.max))}" max="${escapeHtml(String(options.max))}"` : ''}
          ${options.step != null ? `step="${escapeHtml(String(options.step))}"` : ''}
          ${options.inputMode ? `inputmode="${escapeHtml(options.inputMode)}"` : ''}
          ${options.maxLength ? `maxlength="${escapeHtml(String(options.maxLength))}"` : ''}
          ${options.placeholder ? `placeholder="${escapeHtml(options.placeholder)}"` : ''}
          ${options.disabled ? 'disabled' : ''}
        >
        ${options.help ? `<small class="helper">${escapeHtml(options.help)}</small>` : ''}
      </div>
  `;
}

function renderSelectField(label, path, value, choices, options = {}) {
  const fieldClass = options.full ? 'field full' : 'field';
  const normalizedChoices = Array.isArray(choices) ? [...choices] : [];
  const explicitChoiceExists = normalizedChoices.some(choice => String(resolveSelectChoiceValue(choice)) === String(value || ''));
  const customValue = String(value || '').trim();
  if (customValue && !explicitChoiceExists) {
    normalizedChoices.push({value: customValue, label: humanizeProfileToken(customValue) || customValue});
  }
  const selectedLabel = resolveSelectChoiceLabel(normalizedChoices, value);
  const helperText = customValue && !explicitChoiceExists
    ? `${options.help || ''}${options.help ? ' ' : ''}Teknik modda tanımlanmış özel değer korunur.`
    : (options.help || '');
  return `
    <div class="${fieldClass}" data-profile-path="${escapeHtml(path)}" data-profile-search-text="${escapeHtml(buildProfileSearchText(label, selectedLabel || value))}">
      <label>${escapeHtml(label)}</label>
      <select data-profile-field="${escapeHtml(path)}" ${options.disabled ? 'disabled' : ''}>
        ${normalizedChoices.map(choice => `
          <option value="${escapeHtml(resolveSelectChoiceValue(choice))}" ${String(value || '') === String(resolveSelectChoiceValue(choice)) ? 'selected' : ''}>${escapeHtml(resolveSelectChoiceLabel([choice], resolveSelectChoiceValue(choice)))}</option>
        `).join('')}
      </select>
      ${helperText ? `<small class="helper">${escapeHtml(helperText)}</small>` : ''}
    </div>
  `;
}

function normalizeProfileFormattedValue(format, value) {
  const raw = String(value || '').trim();
  switch (String(format || '')) {
    case 'month-day': {
      const digits = raw.replace(/\\D/g, '').slice(0, 4);
      if (digits.length <= 2) return digits;
      return `${digits.slice(0, 2)}-${digits.slice(2)}`;
    }
    case 'time': {
      const digits = raw.replace(/\\D/g, '').slice(0, 4);
      if (digits.length <= 2) return digits;
      return `${digits.slice(0, 2)}:${digits.slice(2)}`;
    }
    case 'time-range': {
      const digits = raw.replace(/\\D/g, '').slice(0, 8);
      if (digits.length <= 2) return digits;
      if (digits.length <= 4) return `${digits.slice(0, 2)}:${digits.slice(2)}`;
      if (digits.length <= 6) return `${digits.slice(0, 2)}:${digits.slice(2, 4)}-${digits.slice(4)}`;
      return `${digits.slice(0, 2)}:${digits.slice(2, 4)}-${digits.slice(4, 6)}:${digits.slice(6)}`;
    }
    case 'time-range-flex': {
      if (!raw || /[A-Za-z/]/.test(raw)) return raw;
      return normalizeProfileFormattedValue('time-range', raw);
    }
    default:
      return raw;
  }
}

function isProfileFormattedValueValid(format, value) {
  const raw = String(value || '').trim();
  if (!raw) return true;
  switch (String(format || '')) {
    case 'month-day':
      return /^\\d{2}-\\d{2}$/.test(raw);
    case 'time':
      return /^\\d{2}:\\d{2}$/.test(raw);
    case 'time-range':
      return /^\\d{2}:\\d{2}-\\d{2}:\\d{2}$/.test(raw);
    case 'time-range-flex':
      return /[A-Za-z/]/.test(raw) || /^\\d{2}:\\d{2}-\\d{2}:\\d{2}$/.test(raw);
    default:
      return true;
  }
}

function isProfileNumberValueValid(field) {
  if (!(field instanceof HTMLElement)) return true;
  if (!field.dataset.numberKind) return true;
  const raw = String(field.value || '').trim();
  if (!raw) return field.dataset.emptyNull === 'true';
  const parsed = field.dataset.numberKind === 'int'
    ? Number.parseInt(raw, 10)
    : Number.parseFloat(raw);
  if (!Number.isFinite(parsed)) return false;
  const minValue = field.dataset.minValue != null && field.dataset.minValue !== ''
    ? Number.parseFloat(field.dataset.minValue)
    : null;
  const maxValue = field.dataset.maxValue != null && field.dataset.maxValue !== ''
    ? Number.parseFloat(field.dataset.maxValue)
    : null;
  if (minValue != null && parsed < minValue) return false;
  if (maxValue != null && parsed > maxValue) return false;
  return true;
}

function applyProfileFieldFormatting(field) {
  const format = String(field.dataset.profileFormat || '').trim();
  if (format) {
    const normalizedValue = normalizeProfileFormattedValue(format, field.value || '');
    if (normalizedValue !== field.value) field.value = normalizedValue;
  }
  const formatValid = !format || isProfileFormattedValueValid(format, field.value || '');
  const numberValid = isProfileNumberValueValid(field);
  field.classList.toggle('is-invalid', !(formatValid && numberValid));
}

function renderMultiCheckboxField(label, path, values, choices, options = {}) {
  const fieldClass = options.full ? 'field full' : 'field';
  const selectedValues = Array.isArray(values) ? values.map(value => String(value)) : [];
  const selectedLabels = selectedValues.map(value => resolveSelectChoiceLabel(choices, value)).join(' ');
  const knownValues = choices.map(choice => resolveSelectChoiceValue(choice));
  const hiddenValues = selectedValues.filter(value => !knownValues.includes(String(value)));
  const helperText = hiddenValues.length
    ? `${options.help || 'Bir veya daha fazla seçenek işaretleyin.'} Teknik modda düzenlenen ${hiddenValues.length} özel değer korunur.`
    : (options.help || '');
  return `
    <div class="${fieldClass}" data-profile-path="${escapeHtml(path)}" data-profile-search-text="${escapeHtml(buildProfileSearchText(label, selectedLabels))}">
      <label>${escapeHtml(label)}</label>
      <div class="stack">
        ${choices.map(choice => {
          const choiceValue = resolveSelectChoiceValue(choice);
          const choiceLabel = resolveSelectChoiceLabel([choice], choiceValue);
          const checked = selectedValues.includes(String(choiceValue));
          return `
            <label class="toggle-row">
              <span class="toggle-copy">
                <strong>${escapeHtml(choiceLabel)}</strong>
              </span>
              <span class="switch">
                <input
                  type="checkbox"
                  data-profile-multi-field="${escapeHtml(path)}"
                  data-profile-multi-value="${escapeHtml(choiceValue)}"
                  data-profile-multi-known-values="${escapeHtml(JSON.stringify(knownValues))}"
                  ${checked ? 'checked' : ''}
                >
                <span class="switch-track"><span class="switch-thumb"></span></span>
              </span>
            </label>
          `;
        }).join('')}
      </div>
      ${helperText ? `<small class="helper">${escapeHtml(helperText)}</small>` : ''}
    </div>
  `;
}

function resolveSelectChoiceValue(choice) {
  if (choice && typeof choice === 'object') return String(choice.value || '');
  return String(choice || '');
}

function resolveSelectChoiceLabel(choices, value) {
  const match = (choices || []).find(choice => String(resolveSelectChoiceValue(choice)) === String(value || ''));
  if (match && typeof match === 'object') return String(match.label || match.value || '');
  if (match != null) return String(match || '');
  return String(value || '');
}

function renderCheckboxField(label, path, checked, options = {}) {
  const fieldClass = options.full ? 'field full' : 'field';
  return `
    <div class="${fieldClass}" data-profile-path="${escapeHtml(path)}" data-profile-search-text="${escapeHtml(buildProfileSearchText(label, checked ? 'evet' : 'hayir'))}">
      <label class="toggle-row">
        <span class="toggle-copy">
          <strong>${escapeHtml(label)}</strong>
          <small>${escapeHtml(options.help || 'Açık / kapalı alan')}</small>
        </span>
        <span class="switch">
          <input type="checkbox" data-profile-field="${escapeHtml(path)}" ${checked ? 'checked' : ''}>
          <span class="switch-track"><span class="switch-thumb"></span></span>
        </span>
      </label>
    </div>
  `;
}

function renderListField(label, path, values, options = {}) {
  const fieldClass = options.full ? 'field full' : 'field';
  return `
    <div class="${fieldClass}" data-profile-path="${escapeHtml(path)}" data-profile-search-text="${escapeHtml(buildProfileSearchText(label, values))}">
      <label>${escapeHtml(label)}</label>
      <textarea class="profile-list-textarea" data-profile-list-field="${escapeHtml(path)}"${options.placeholder ? ` placeholder="${escapeHtml(options.placeholder)}"` : ""}>${escapeHtml((values || []).join('\\\\n'))}</textarea>
      <small class="helper">${escapeHtml(options.help || 'Her satır ayrı bir öğe olarak kaydedilir.')}</small>
    </div>
  `;
}

function renderJsonField(label, path, value, options = {}) {
  const fieldClass = options.full ? 'field full' : 'field';
  return `
    <div class="${fieldClass}" data-profile-path="${escapeHtml(path)}" data-profile-search-text="${escapeHtml(buildProfileSearchText(label, value))}">
      <label>${escapeHtml(label)}</label>
      <textarea class="profile-json-textarea" data-profile-json-field="${escapeHtml(path)}">${escapeHtml(JSON.stringify(value ?? {}, null, 2))}</textarea>
      <small class="helper">${escapeHtml(options.help || 'JSON biçiminde düzenleyin.')}</small>
    </div>
  `;
}

function renderMapKeyField(label, collection, key) {
  return `
    <div class="field" data-profile-path="${escapeHtml(collection)}" data-profile-search-text="${escapeHtml(buildProfileSearchText(label, key))}">
      <label>${escapeHtml(label)}</label>
      <input
        type="text"
        value="${escapeHtml(key)}"
        data-profile-map-key="${escapeHtml(collection)}"
        data-profile-map-old-key="${escapeHtml(key)}"
      >
    </div>
  `;
}

function onHotelProfileSectionNav(event) {
  const modeButton = event.target.closest('[data-profile-mode]');
  if (modeButton) {
    state.hotelProfileMode = modeButton.dataset.profileMode === 'technical' ? 'technical' : 'standard';
    ensureVisibleHotelProfileSection();
    renderHotelProfileWorkspace();
    return;
  }
  const button = event.target.closest('[data-hotel-profile-section]');
  if (!button) return;
  state.hotelProfileSection = button.dataset.hotelProfileSection;
  renderHotelProfileWorkspace();
  focusFirstHotelProfileIssueInSection(state.hotelProfileSection);
}

function onHotelProfileSectionSearchInput(event) {
  const field = event.target;
  if (!(field instanceof HTMLElement)) return;
  if (!field.matches('[data-profile-field="__section_search__"]')) return;
  state.hotelProfileSearch = String(field.value || '');
  applyHotelProfileSectionSearch();
  const clearButton = refs.hotelProfileSections?.querySelector('[data-clear-profile-search]');
  if (clearButton instanceof HTMLButtonElement) {
    clearButton.disabled = !state.hotelProfileSearch.trim();
  }
}

function onHotelProfileSectionSearchClick(event) {
  const button = event.target.closest('[data-clear-profile-search]');
  if (!button) return;
  state.hotelProfileSearch = '';
  renderHotelProfileWorkspace();
}

function onHotelProfileSectionInput(event) {
  const field = event.target;
  if (!(field instanceof HTMLElement)) return;
  if (!field.dataset.profileFormat && !field.dataset.numberKind) return;
  applyProfileFieldFormatting(field);
}

function onHotelProfileSectionClick(event) {
  const overviewButton = event.target.closest('[data-profile-overview-target]');
  if (overviewButton) {
    openHotelProfileOverviewTarget(
      overviewButton.dataset.profileOverviewTarget || '',
      overviewButton.dataset.profileOverviewPath || '',
    );
    return;
  }

  const issueButton = event.target.closest('[data-profile-issue-path]');
  if (issueButton) {
    openHotelProfileIssuePath(issueButton.dataset.profileIssuePath || '');
    return;
  }

  const contactPresetButton = event.target.closest('[data-profile-add-contact-preset]');
  if (contactPresetButton) {
    addContactPresetToDraft(contactPresetButton.dataset.profileAddContactPreset || 'OTHER');
    syncHotelProfileEditorFromDraft();
    renderHotelProfileWorkspace();
    scheduleHotelFactsDraftValidation({silent: true});
    return;
  }

  const boardPresetButton = event.target.closest('[data-profile-add-board-preset]');
  if (boardPresetButton) {
    addBoardTypePresetToDraft(boardPresetButton.dataset.profileAddBoardPreset || '');
    syncHotelProfileEditorFromDraft();
    renderHotelProfileWorkspace();
    scheduleHotelFactsDraftValidation({silent: true});
    return;
  }

  const roomPresetButton = event.target.closest('[data-profile-add-room-preset]');
  if (roomPresetButton) {
    addRoomTypePresetToDraft(roomPresetButton.dataset.profileAddRoomPreset || '');
    syncHotelProfileEditorFromDraft();
    renderHotelProfileWorkspace();
    scheduleHotelFactsDraftValidation({silent: true});
    return;
  }

  const cancellationPresetButton = event.target.closest('[data-profile-add-cancellation-preset]');
  if (cancellationPresetButton) {
    addCancellationRulePresetToDraft(cancellationPresetButton.dataset.profileAddCancellationPreset || '');
    syncHotelProfileEditorFromDraft();
    renderHotelProfileWorkspace();
    scheduleHotelFactsDraftValidation({silent: true});
    return;
  }

  const addListButton = event.target.closest('[data-profile-add-list-item]');
  if (addListButton) {
    const collection = addListButton.dataset.profileAddListItem;
    const list = ensureDraftList(collection);
    list.push(createDefaultListItem(collection));
    if (collection === 'faq_data') {
      state.hotelProfileFaqActiveIndex = Math.max(0, list.length - 1);
    }
    syncHotelProfileEditorFromDraft();
    renderHotelProfileWorkspace();
    scheduleHotelFactsDraftValidation({silent: true});
    return;
  }

  const addObjectButton = event.target.closest('[data-profile-add-object-item]');
  if (addObjectButton) {
    const path = addObjectButton.dataset.profileAddObjectItem;
    const list = ensureDraftListByPath(path);
    list.push(createDefaultPathListItem(path));
    syncHotelProfileEditorFromDraft();
    renderHotelProfileWorkspace();
    scheduleHotelFactsDraftValidation({silent: true});
    return;
  }

  const removeListButton = event.target.closest('[data-profile-remove-list-item]');
  if (removeListButton) {
    const collection = removeListButton.dataset.profileRemoveListItem;
    const index = Number(removeListButton.dataset.profileIndex || -1);
    const list = ensureDraftList(collection);
    if (index >= 0 && index < list.length) {
      list.splice(index, 1);
      if (collection === 'faq_data') {
        state.hotelProfileFaqActiveIndex = Math.max(0, Math.min(state.hotelProfileFaqActiveIndex, list.length - 1));
      }
      syncHotelProfileEditorFromDraft();
      renderHotelProfileWorkspace();
      scheduleHotelFactsDraftValidation({silent: true});
    }
    return;
  }

  const removeObjectButton = event.target.closest('[data-profile-remove-object-item]');
  if (removeObjectButton) {
    const path = removeObjectButton.dataset.profileRemoveObjectItem;
    const index = Number(removeObjectButton.dataset.profileIndex || -1);
    const list = ensureDraftListByPath(path);
    if (index >= 0 && index < list.length) {
      list.splice(index, 1);
      syncHotelProfileEditorFromDraft();
      renderHotelProfileWorkspace();
      scheduleHotelFactsDraftValidation({silent: true});
    }
    return;
  }

  const addMapButton = event.target.closest('[data-profile-add-map-entry]');
  if (addMapButton) {
    const collection = addMapButton.dataset.profileAddMapEntry;
    const target = ensureDraftMap(collection);
    const key = nextProfileMapKey(collection, target);
    target[key] = createDefaultMapEntry(collection);
    ensureLinkedProfileMapEntry(collection, key);
    syncHotelProfileEditorFromDraft();
    renderHotelProfileWorkspace();
    scheduleHotelFactsDraftValidation({silent: true});
    return;
  }

  const removeMapButton = event.target.closest('[data-profile-remove-map-entry]');
  if (removeMapButton) {
    const collection = removeMapButton.dataset.profileRemoveMapEntry;
    const key = removeMapButton.dataset.profileMapKeyValue || '';
    const target = ensureDraftMap(collection);
    delete target[key];
    if (collection === 'cancellation_rules' && !isHotelProfileTechnicalMode()) {
      const mappings = ensureDraftMap('rate_mapping');
      delete mappings[key];
    }
    syncHotelProfileEditorFromDraft();
    renderHotelProfileWorkspace();
    scheduleHotelFactsDraftValidation({silent: true});
  }
}

function onHotelProfileSectionChange(event) {
  const field = event.target;
  if (!(field instanceof HTMLElement)) return;
  if (field.dataset.profileFormat || field.dataset.numberKind) {
    applyProfileFieldFormatting(field);
  }

  if (field.dataset.profileFaqActive) {
    const nextIndex = Number(field.value || 0);
    state.hotelProfileFaqActiveIndex = Number.isFinite(nextIndex) && nextIndex >= 0 ? nextIndex : 0;
    renderHotelProfileWorkspace();
    return;
  }

  if (field.dataset.profileMapKey) {
    renameDraftMapKey(field);
    return;
  }
  if (field.dataset.profileMultiField) {
    const path = field.dataset.profileMultiField;
    const value = String(field.dataset.profileMultiValue || '');
    const current = Array.isArray(getProfileValueByPath(state.hotelProfileDraft, path))
      ? [...getProfileValueByPath(state.hotelProfileDraft, path)]
      : [];
    let knownValues = [];
    try {
      knownValues = JSON.parse(field.dataset.profileMultiKnownValues || '[]').map(item => String(item));
    } catch (_error) {
      knownValues = [];
    }
    const preserved = knownValues.length
      ? current.filter(item => !knownValues.includes(String(item)))
      : [];
    const selectedKnown = new Set(
      current
        .filter(item => !knownValues.length || knownValues.includes(String(item)))
        .map(item => String(item))
    );
    if (field.checked) selectedKnown.add(value);
    else selectedKnown.delete(value);
    const next = knownValues.length
      ? [...preserved, ...Array.from(selectedKnown)]
      : Array.from(selectedKnown);
    setProfileValueByPath(state.hotelProfileDraft, path, next);
    syncHotelProfileEditorFromDraft();
    scheduleHotelFactsDraftValidation({silent: true});
    return;
  }
  if (field.dataset.profileField) {
    setProfileValueByPath(state.hotelProfileDraft, field.dataset.profileField, coerceProfileFieldValue(field));
    syncHotelProfileEditorFromDraft();
    scheduleHotelFactsDraftValidation({silent: true});
    return;
  }
  if (field.dataset.profileListField) {
    setProfileValueByPath(
      state.hotelProfileDraft,
      field.dataset.profileListField,
      String(field.value || '').split('\\n').map(item => item.trim()).filter(Boolean),
    );
    syncHotelProfileEditorFromDraft();
    scheduleHotelFactsDraftValidation({silent: true});
    return;
  }
  if (field.dataset.profileJsonField) {
    try {
      const parsed = JSON.parse(String(field.value || '{}'));
      setProfileValueByPath(state.hotelProfileDraft, field.dataset.profileJsonField, parsed);
      field.classList.remove('is-invalid');
      syncHotelProfileEditorFromDraft();
      scheduleHotelFactsDraftValidation({silent: true});
    } catch (_error) {
      field.classList.add('is-invalid');
      notify('JSON alani parse edilemedi. Lutfen gecerli JSON girin.', 'error');
    }
  }
}

function applyHotelProfileSectionSearch() {
  if (!refs.hotelProfileSectionBody) return;
  const term = String(state.hotelProfileSearch || '').trim().toLocaleLowerCase('tr');
  const fieldNodes = Array.from(refs.hotelProfileSectionBody.querySelectorAll('[data-profile-search-text]'));
  let visibleFields = 0;
  fieldNodes.forEach(node => {
    if (!(node instanceof HTMLElement)) return;
    const haystack = String(node.dataset.profileSearchText || '').toLocaleLowerCase('tr');
    const matched = !term || haystack.includes(term);
    node.hidden = !matched;
    if (matched) visibleFields += 1;
  });

  refs.hotelProfileSectionBody.querySelectorAll('.profile-item-card').forEach(card => {
    if (!(card instanceof HTMLElement)) return;
    const hasVisibleField = Boolean(card.querySelector('[data-profile-search-text]:not([hidden])'));
    const matchedByTitle = !term || card.textContent.toLocaleLowerCase('tr').includes(term);
    card.hidden = !(matchedByTitle || hasVisibleField);
  });

  const existingState = refs.hotelProfileSectionBody.querySelector('[data-profile-search-empty]');
  if (existingState instanceof HTMLElement) existingState.remove();

  if (term && visibleFields === 0 && !refs.hotelProfileSectionBody.querySelector('.profile-item-card:not([hidden])')) {
    refs.hotelProfileSectionBody.insertAdjacentHTML(
      'beforeend',
      '<div class="empty-state mt-md" data-profile-search-empty><p>Aramanızla eşleşen alan bulunamadı.</p></div>',
    );
  }
}

function scheduleHotelFactsDraftValidation(options = {}) {
  if (!state.hotelProfileDraft || !state.selectedHotelId || state.hotelFactsApiUnavailable) return;
  if (state.hotelFactsDraftValidationHandle) {
    window.clearTimeout(state.hotelFactsDraftValidationHandle);
    state.hotelFactsDraftValidationHandle = null;
  }
  const delay = options.immediate ? 0 : 450;
  state.hotelFactsDraftValidationHandle = window.setTimeout(() => {
    state.hotelFactsDraftValidationHandle = null;
    runHotelFactsDraftValidation({silent: options.silent !== false});
  }, delay);
}

async function runHotelFactsDraftValidation(options = {}) {
  const hotelId = refs.hotelProfileSelect.value || state.selectedHotelId;
  if (!hotelId || !state.hotelProfileDraft) return;
  try {
    const validation = await apiFetch(`/hotels/${hotelId}/facts/validate`, {
      method: 'POST',
      body: {profile_json: state.hotelProfileDraft},
    });
    state.hotelFactsDraftValidation = buildHotelFactsDraftValidationState(state.hotelFactsStatus, validation);
    renderHotelFactsStatus(state.hotelFactsStatus);
    renderHotelProfileMeta();
    applyHotelProfileValidationDecorations();
  } catch (error) {
    state.hotelFactsDraftValidation = buildHotelFactsDraftValidationState(state.hotelFactsStatus, {
      publishable: false,
      facts_checksum: state.hotelFactsDraftValidation?.facts_checksum || state.hotelFactsStatus?.draft_facts_checksum || null,
      source_profile_checksum: state.hotelFactsDraftValidation?.source_profile_checksum || null,
      blockers: [
        {
          code: 'draft_schema_invalid',
          message: error?.message || 'Taslak doğrulaması çalıştırılamadı.',
          path: 'profile_json',
          severity: 'blocker',
        },
      ],
      warnings: [],
    });
    renderHotelFactsStatus(state.hotelFactsStatus);
    renderHotelProfileMeta();
    applyHotelProfileValidationDecorations();
    if (!options.silent) notify(error.message, 'error');
  }
}

function buildHotelFactsDraftValidationFromStatus(status) {
  const currentStatus = asObject(status);
  return {
    publishable: Boolean(currentStatus.draft_publishable),
    validated_facts_checksum: currentStatus.draft_facts_checksum ?? null,
    validated_source_profile_checksum: currentStatus.draft_source_profile_checksum ?? null,
    facts_checksum: currentStatus.draft_facts_checksum ?? null,
    source_profile_checksum: currentStatus.draft_source_profile_checksum ?? null,
    draft_matches_runtime: Boolean(currentStatus.draft_matches_runtime),
    blockers: Array.isArray(currentStatus.blockers) ? currentStatus.blockers : [],
    warnings: Array.isArray(currentStatus.warnings) ? currentStatus.warnings : [],
  };
}

function buildHotelFactsDraftValidationState(existingStatus, validation) {
  const status = asObject(existingStatus);
  const currentVersion = status.current_version ?? null;
  const currentFactsChecksum = status.current_facts_checksum ?? null;
  const draftFactsChecksum = validation.validated_facts_checksum ?? validation.facts_checksum ?? status.draft_facts_checksum ?? null;
  const sourceProfileChecksum = validation.validated_source_profile_checksum ?? validation.source_profile_checksum ?? null;
  const serverBlockers = Array.isArray(validation.blockers) ? validation.blockers : [];
  const serverWarnings = Array.isArray(validation.warnings) ? validation.warnings : [];
  const localIssues = buildLocalHotelProfileIssues(state.hotelProfileDraft || {});
  const blockers = [...serverBlockers, ...localIssues.blockers];
  const warnings = [...serverWarnings, ...localIssues.warnings];
  return {
    publishable: Boolean(validation.publishable) && blockers.length === 0,
    validated_facts_checksum: draftFactsChecksum,
    validated_source_profile_checksum: sourceProfileChecksum,
    facts_checksum: draftFactsChecksum,
    source_profile_checksum: sourceProfileChecksum,
    draft_matches_runtime: Boolean(currentFactsChecksum && draftFactsChecksum && currentFactsChecksum === draftFactsChecksum),
    blockers,
    warnings,
  };
}

function buildLocalHotelProfileIssues(draft = {}) {
  const blockers = [];
  const warnings = [];
  const operational = asObject(draft.operational);
  const restaurant = asObject(draft.restaurant);
  const contacts = asObject(draft.contacts);
  const location = asObject(draft.location);
  const rateMapping = asObject(draft.rate_mapping);
  const cancellationRules = asObject(draft.cancellation_rules);
  const minStay = Number(operational.min_stay ?? 0);
  const maxStay = Number(operational.max_stay ?? 0);
  if (Number.isFinite(minStay) && Number.isFinite(maxStay) && minStay > 0 && maxStay > 0 && minStay > maxStay) {
    blockers.push({
      code: 'stay_range_invalid',
      message: 'Minimum konaklama, maksimum konaklamadan büyük olamaz.',
      path: 'operational.min_stay',
      severity: 'blocker',
    });
  }
  const capacityMin = Number(restaurant.capacity_min ?? 0);
  const capacityMax = Number(restaurant.capacity_max ?? 0);
  const maxAiPartySize = Number(restaurant.max_ai_party_size ?? 0);
  if (Number.isFinite(capacityMin) && Number.isFinite(capacityMax) && capacityMin > 0 && capacityMax > 0 && capacityMin > capacityMax) {
    blockers.push({
      code: 'restaurant_capacity_range_invalid',
      message: 'Minimum kapasite, maksimum kapasiteden büyük olamaz.',
      path: 'restaurant.capacity_min',
      severity: 'blocker',
    });
  }
  if (Number.isFinite(maxAiPartySize) && maxAiPartySize > 0 && Number.isFinite(capacityMax) && capacityMax > 0 && maxAiPartySize > capacityMax) {
    blockers.push({
      code: 'restaurant_ai_party_size_invalid',
      message: 'Yapay zekâ için maksimum grup büyüklüğü, restoran maksimum kapasitesini aşamaz.',
      path: 'restaurant.max_ai_party_size',
      severity: 'blocker',
    });
  }
  Object.entries(contacts).forEach(([key, item]) => {
    const contact = asObject(item);
    const hasContactContent = Boolean(
      String(contact.phone || '').trim()
      || String(contact.email || '').trim()
      || String(contact.hours || '').trim()
      || String(contact.name || '').trim()
      || String(contact.role || '').trim()
    );
    const hasContactChannel = Boolean(String(contact.phone || '').trim() || String(contact.email || '').trim());
    if (!hasContactContent) {
      blockers.push({
        code: 'contact_empty_invalid',
        message: 'İletişim kaydı boş bırakılamaz. Telefon veya e-posta ekleyin ya da kaydı silin.',
        path: `contacts.${key}.phone`,
        severity: 'blocker',
      });
      return;
    }
    if (!hasContactChannel) {
      blockers.push({
        code: 'contact_channel_missing',
        message: 'İletişim kaydında telefon veya e-posta bulunmalıdır.',
        path: `contacts.${key}.phone`,
        severity: 'blocker',
      });
    }
  });
  (Array.isArray(location.nearby) ? location.nearby : []).forEach((item, index) => {
    const place = asObject(item);
    const placeName = String(place.name || '').trim();
    const placeDistance = String(place.distance || '').trim();
    if (!placeName || !placeDistance) {
      blockers.push({
        code: 'nearby_place_incomplete',
        message: 'Yakın nokta kaydında yer adı ve mesafe birlikte girilmelidir.',
        path: !placeName ? `location.nearby[${index}].name` : `location.nearby[${index}].distance`,
        severity: 'blocker',
      });
    }
  });
  Object.keys(rateMapping).forEach(key => {
    if (!Object.prototype.hasOwnProperty.call(cancellationRules, key)) {
      blockers.push({
        code: 'rate_mapping_rule_missing',
        message: 'Fiyat eşleştirmesi için aynı anahtarda bir iptal kuralı bulunmalıdır.',
        path: `rate_mapping.${key}`,
        severity: 'blocker',
      });
    }
  });
  Object.keys(cancellationRules).forEach(key => {
    if (!Object.prototype.hasOwnProperty.call(rateMapping, key)) {
      blockers.push({
        code: 'cancellation_rule_mapping_missing',
        message: 'İptal kuralı için aynı anahtarda bir fiyat eşleştirmesi bulunmalıdır.',
        path: `cancellation_rules.${key}`,
        severity: 'blocker',
      });
    }
  });
  Object.entries(cancellationRules).forEach(([key, item]) => {
    const rule = asObject(item);
    const prepaymentDaysBefore = Number(rule.prepayment_days_before ?? 0);
    const exceptionDaysBefore = Number(rule.exception_days_before ?? 0);
    const hasExceptionDays = Number.isFinite(exceptionDaysBefore) && exceptionDaysBefore > 0;
    const hasExceptionRefund = Boolean(rule.exception_refund);
    if (Boolean(rule.prepayment_immediate) && Number.isFinite(prepaymentDaysBefore) && prepaymentDaysBefore > 0) {
      blockers.push({
        code: 'cancellation_prepayment_timing_conflict',
        message: 'Rezervasyon anında ön ödeme alınırsa ayrıca gün sayısı girilmemelidir.',
        path: `cancellation_rules.${key}.prepayment_days_before`,
        severity: 'blocker',
      });
    }
    if (!Boolean(rule.refund ?? true) && Boolean(rule.refund_after_deadline)) {
      blockers.push({
        code: 'cancellation_refund_conflict',
        message: 'İadesiz rezervasyonda son tarihten sonra iade açık olamaz.',
        path: `cancellation_rules.${key}.refund_after_deadline`,
        severity: 'blocker',
      });
    }
    if (hasExceptionDays && !hasExceptionRefund) {
      blockers.push({
        code: 'cancellation_exception_refund_missing',
        message: 'İstisna gün sayısı girildiğinde istisna iadesi de seçilmelidir.',
        path: `cancellation_rules.${key}.exception_refund`,
        severity: 'blocker',
      });
    }
    if (!hasExceptionDays && hasExceptionRefund) {
      blockers.push({
        code: 'cancellation_exception_days_missing',
        message: 'İstisna iadesi seçildiyse kaç gün öncesine kadar geçerli olduğu da girilmelidir.',
        path: `cancellation_rules.${key}.exception_days_before`,
        severity: 'blocker',
      });
    }
  });
  (Array.isArray(draft.board_types) ? draft.board_types : []).forEach((item, index) => {
    const board = asObject(item);
    const hasBoardName = Boolean(String(board.name?.tr || '').trim() || String(board.name?.en || '').trim());
    const isEmptyBoard = !String(board.code || '').trim()
      && !hasBoardName
      && !String(board.breakfast_hours || '').trim()
      && !String(board.breakfast_type || '').trim();
    if (isEmptyBoard) {
      blockers.push({
        code: 'board_type_empty_invalid',
        message: 'Boş pansiyon kartı kaydedilemez. Kartı doldurun veya silin.',
        path: `board_types[${index}].code`,
        severity: 'blocker',
      });
      return;
    }
    if (!String(board.code || '').trim()) {
      blockers.push({
        code: 'board_type_code_missing',
        message: 'Pansiyon kartında pansiyon tipi seçilmelidir.',
        path: `board_types[${index}].code`,
        severity: 'blocker',
      });
    }
    if (!hasBoardName) {
      blockers.push({
        code: 'board_type_name_missing',
        message: 'Pansiyon kartında en az bir görünen ad bulunmalıdır.',
        path: `board_types[${index}].name.tr`,
        severity: 'blocker',
      });
    }
  });
  (Array.isArray(draft.faq_data) ? draft.faq_data : []).forEach((item, index) => {
    const faq = asObject(item);
    const hasFaqQuestion = Boolean(String(faq.question_tr || '').trim() || String(faq.question_en || '').trim());
    const hasFaqAnswer = Boolean(String(faq.answer_tr || '').trim() || String(faq.answer_en || '').trim());
    const isEmptyFaq = !String(faq.topic || '').trim()
      && !hasFaqQuestion
      && !hasFaqAnswer
      && !(Array.isArray(faq.question_variants_tr) && faq.question_variants_tr.length)
      && !(Array.isArray(faq.question_variants_en) && faq.question_variants_en.length);
    if (isEmptyFaq) {
      blockers.push({
        code: 'faq_entry_empty_invalid',
        message: 'Boş SSS kartı kaydedilemez. Soru ve cevap ekleyin veya kartı silin.',
        path: `faq_data[${index}].question_tr`,
        severity: 'blocker',
      });
      return;
    }
    if (!String(faq.topic || '').trim()) {
      blockers.push({
        code: 'faq_topic_missing',
        message: 'SSS kartında kategori seçilmelidir.',
        path: `faq_data[${index}].topic`,
        severity: 'blocker',
      });
    }
    if (!hasFaqQuestion) {
      blockers.push({
        code: 'faq_question_missing',
        message: 'SSS kartında en az bir soru metni bulunmalıdır.',
        path: `faq_data[${index}].question_tr`,
        severity: 'blocker',
      });
    }
    if (!hasFaqAnswer) {
      blockers.push({
        code: 'faq_answer_missing',
        message: 'SSS kartında en az bir cevap metni bulunmalıdır.',
        path: `faq_data[${index}].answer_tr`,
        severity: 'blocker',
      });
    }
  });
  (Array.isArray(draft.room_types) ? draft.room_types : []).forEach((item, index) => {
    const room = asObject(item);
    const roomMaxPax = Number(room.max_pax ?? 0);
    const roomSize = Number(room.size_m2 ?? 0);
    const roomHasDetailContent = Number(room.pms_room_type_id ?? 0) > 0
      || Number(roomSize) > 0
      || Boolean(String(room.bed_type || '').trim())
      || Boolean(String(room.view || '').trim())
      || Boolean(String(room.description?.tr || '').trim())
      || Boolean(String(room.description?.en || '').trim())
      || (Array.isArray(room.features) && room.features.length > 0)
      || Boolean(room.extra_bed)
      || Boolean(room.baby_crib)
      || Boolean(room.accessible);
    const hasRoomName = Boolean(String(room.name?.tr || '').trim() || String(room.name?.en || '').trim());
    if (roomHasDetailContent && !hasRoomName) {
      blockers.push({
        code: 'room_name_missing',
        message: 'Oda kartında ad girilmeden diğer bilgiler kaydedilemez.',
        path: `room_types[${index}].name.tr`,
        severity: 'blocker',
      });
    }
    if (Number.isFinite(roomMaxPax) && roomMaxPax < 1) {
      blockers.push({
        code: 'room_max_pax_invalid',
        message: 'Oda maksimum kişi sayısı en az 1 olmalıdır.',
        path: `room_types[${index}].max_pax`,
        severity: 'blocker',
      });
    }
    if (Number.isFinite(roomSize) && roomSize < 1) {
      blockers.push({
        code: 'room_size_invalid',
        message: 'Oda büyüklüğü 1 m² veya daha fazla olmalıdır.',
        path: `room_types[${index}].size_m2`,
        severity: 'blocker',
      });
    }
  });
  (Array.isArray(draft.transfer_routes) ? draft.transfer_routes : []).forEach((item, index) => {
    const route = asObject(item);
    const routeMaxPax = Number(route.max_pax ?? 0);
    const routeDuration = Number(route.duration_min ?? 0);
    const routePrice = Number(route.price_eur ?? 0);
    const oversize = asObject(route.oversize_vehicle);
    const oversizeMinPax = Number(oversize.min_pax ?? 0);
    const hasRouteContent = Boolean(
      String(route.from_location || '').trim()
      || String(route.to_location || '').trim()
      || String(route.vehicle_type || '').trim()
      || routePrice > 0
      || routeDuration > 0
      || Boolean(String(oversize.type || '').trim())
      || Number(oversize.price_eur ?? 0) > 0
      || oversizeMinPax > 0
    );
    if (hasRouteContent && !String(route.from_location || '').trim()) {
      blockers.push({
        code: 'transfer_from_location_missing',
        message: 'Transfer güzergâhında başlangıç noktası girilmelidir.',
        path: `transfer_routes[${index}].from_location`,
        severity: 'blocker',
      });
    }
    if (hasRouteContent && !String(route.to_location || '').trim()) {
      blockers.push({
        code: 'transfer_to_location_missing',
        message: 'Transfer güzergâhında varış noktası girilmelidir.',
        path: `transfer_routes[${index}].to_location`,
        severity: 'blocker',
      });
    }
    if (hasRouteContent && !String(route.vehicle_type || '').trim()) {
      blockers.push({
        code: 'transfer_vehicle_type_missing',
        message: 'Transfer güzergâhında araç tipi seçilmelidir.',
        path: `transfer_routes[${index}].vehicle_type`,
        severity: 'blocker',
      });
    }
    if (Number.isFinite(routeMaxPax) && routeMaxPax < 1) {
      blockers.push({
        code: 'transfer_max_pax_invalid',
        message: 'Transfer araç kapasitesi en az 1 kişi olmalıdır.',
        path: `transfer_routes[${index}].max_pax`,
        severity: 'blocker',
      });
    }
    if (Number.isFinite(routeDuration) && routeDuration < 1) {
      blockers.push({
        code: 'transfer_duration_invalid',
        message: 'Transfer süresi en az 1 dakika olmalıdır.',
        path: `transfer_routes[${index}].duration_min`,
        severity: 'blocker',
      });
    }
    if (Number.isFinite(routePrice) && routePrice < 0) {
      blockers.push({
        code: 'transfer_price_invalid',
        message: 'Transfer fiyatı negatif olamaz.',
        path: `transfer_routes[${index}].price_eur`,
        severity: 'blocker',
      });
    }
    if (Number.isFinite(oversizeMinPax) && oversizeMinPax > 0 && Number.isFinite(routeMaxPax) && routeMaxPax > 0 && oversizeMinPax <= routeMaxPax) {
      blockers.push({
        code: 'transfer_oversize_threshold_invalid',
        message: 'Büyük araç eşiği, standart araç kapasitesinden büyük olmalıdır.',
        path: `transfer_routes[${index}].oversize_vehicle.min_pax`,
        severity: 'blocker',
      });
    }
  });
  return {blockers, warnings};
}

function applyHotelProfileValidationDecorations() {
  updateHotelProfileSectionOverviewCards();
  applyHotelProfileSectionIssueBadges();
  applyHotelProfileFieldMarkers();
  renderHotelProfileSectionIssues();
}

function updateHotelProfileSectionOverviewCards() {
  if (!refs.hotelProfileSections) return;
  const items = buildHotelProfileSectionOverview();
  const summaryNode = refs.hotelProfileSections.querySelector('[data-profile-overview-summary]');
  if (summaryNode instanceof HTMLElement) {
    summaryNode.outerHTML = renderHotelProfileOverviewSummary(items);
  }
  items.forEach(item => {
    const card = refs.hotelProfileSections.querySelector(`[data-profile-overview-section="${cssEscapeValue(item.id)}"]`);
    if (!(card instanceof HTMLElement)) return;
    card.classList.toggle('is-active', state.hotelProfileSection === item.id);
    const statusNode = card.querySelector('[data-profile-overview-status]');
    if (statusNode instanceof HTMLElement) {
      statusNode.className = `profile-overview-status ${item.status}`;
      statusNode.textContent = item.status_label;
    }
    const descriptionNode = card.querySelector('[data-profile-overview-description]');
    if (descriptionNode instanceof HTMLElement) {
      descriptionNode.textContent = item.description;
    }
    const metricsNode = card.querySelector('[data-profile-overview-metrics]');
    if (metricsNode instanceof HTMLElement) {
      metricsNode.innerHTML = `
        <span>${escapeHtml(String(item.blockers))} engelleyici</span>
        <span>${escapeHtml(String(item.warnings))} uyarı</span>
      `;
    }
  });
}

function applyHotelProfileSectionIssueBadges() {
  if (!refs.hotelProfileSections) return;
  const summary = summarizeHotelProfileIssuesBySection();
  refs.hotelProfileSections.querySelectorAll('[data-hotel-profile-section]').forEach(button => {
    if (!(button instanceof HTMLElement)) return;
    button.querySelectorAll('.profile-section-badge').forEach(node => node.remove());
    const section = button.dataset.hotelProfileSection || '';
    const issue = summary[section];
    if (!issue || (!issue.blockers && !issue.warnings)) return;
    const severity = issue.blockers ? 'blocker' : 'warning';
    const total = issue.blockers + issue.warnings;
    button.insertAdjacentHTML(
      'beforeend',
      `<span class="profile-section-badge ${severity}">${escapeHtml(issue.blockers ? `${issue.blockers} engelleyici` : `${issue.warnings} uyarı`)}${total > 1 ? ` / ${escapeHtml(String(total))}` : ''}</span>`,
    );
  });
}

function applyHotelProfileFieldMarkers() {
  if (!refs.hotelProfileSectionBody) return;
  const issues = getHotelProfileIssuesForSection(state.hotelProfileSection);
  refs.hotelProfileSectionBody.querySelectorAll('[data-profile-path]').forEach(node => {
    if (!(node instanceof HTMLElement)) return;
    node.classList.remove('profile-field-invalid', 'profile-field-warning');
    const path = node.dataset.profilePath || '';
    const matched = issues.filter(issue => matchesProfileIssuePath(path, issue.path || ''));
    if (matched.some(issue => issue.severity === 'blocker')) {
      node.classList.add('profile-field-invalid');
    } else if (matched.some(issue => issue.severity === 'warning')) {
      node.classList.add('profile-field-warning');
    }
  });
}

function renderHotelProfileSectionIssues() {
  if (!refs.hotelProfileSectionBody) return;
  const existing = refs.hotelProfileSectionBody.querySelector('[data-profile-issues-panel]');
  if (existing instanceof HTMLElement) existing.remove();
  const issues = getHotelProfileIssuesForSection(state.hotelProfileSection);
  if (!issues.length) return;
  refs.hotelProfileSectionBody.insertAdjacentHTML('afterbegin', `
    <div class="helper-box" data-profile-issues-panel>
      <strong>Bu bölüm için doğrulama notları</strong>
      <div class="profile-issue-panel">
        ${issues.map(issue => `
          <div class="profile-issue-row ${escapeHtml(issue.severity || 'warning')}">
            <div class="stack">
              <strong>${escapeHtml(issue.code || issue.severity || 'issue')}</strong>
              <span class="muted">${escapeHtml(issue.message || '-')}</span>
              <span class="mono">${escapeHtml(issue.path || '-')}</span>
            </div>
            <button class="action-button secondary action-button-sm" type="button" data-profile-issue-path="${escapeHtml(issue.path || '')}">Alana Git</button>
          </div>
        `).join('')}
      </div>
    </div>
  `);
}

function summarizeHotelProfileIssuesBySection(status) {
  const summary = Object.create(null);
  getHotelProfileIssues(status).forEach(issue => {
    const section = mapHotelProfileIssueToSection(issue.path || '');
    if (!summary[section]) summary[section] = {blockers: 0, warnings: 0};
    if (issue.severity === 'blocker') summary[section].blockers += 1;
    else summary[section].warnings += 1;
  });
  return summary;
}

function buildHotelProfileSectionOverview() {
  const draft = state.hotelProfileDraft || {};
  const issueSummary = summarizeHotelProfileIssuesBySection();
  return getVisibleHotelProfileSections().map(section => {
    const completion = getHotelProfileSectionCompletion(section.id, draft);
    const issues = issueSummary[section.id] || {blockers: 0, warnings: 0};
    let status = 'complete';
    let statusLabel = 'Hazır';
    if (issues.blockers) {
      status = 'blocker';
      statusLabel = `${issues.blockers} engelleyici`;
    } else if (issues.warnings) {
      status = 'warning';
      statusLabel = `${issues.warnings} uyarı`;
    } else if (!completion.complete) {
      status = 'incomplete';
      statusLabel = 'Eksik';
    }
    return {
      id: section.id,
      label: section.label,
      status,
      status_label: statusLabel,
      description: completion.description,
      blockers: issues.blockers,
      warnings: issues.warnings,
      completion,
    };
  });
}

function buildHotelProfileOverviewSummary(items = buildHotelProfileSectionOverview()) {
  const normalizedItems = Array.isArray(items) ? items : [];
  const totalSections = normalizedItems.length;
  const completeSections = normalizedItems.filter(item => item.completion?.complete).length;
  const incompleteSections = normalizedItems.filter(item => !item.completion?.complete).length;
  const blockerSections = normalizedItems.filter(item => item.status === 'blocker').length;
  const warningSections = normalizedItems.filter(item => item.status === 'warning').length;
  const percent = totalSections ? Math.round((completeSections / totalSections) * 100) : 0;
  const missing = normalizedItems.flatMap(item => {
    const fields = Array.isArray(item.completion?.missing) ? item.completion.missing : [];
    return fields.map(field => ({
      id: item.id,
      section: item.label,
      label: field.label,
      path: field.path,
    }));
  });
  return {
    totalSections,
    completeSections,
    incompleteSections,
    blockerSections,
    warningSections,
    percent,
    missingItems: missing.slice(0, 6),
    remainingMissing: Math.max(0, missing.length - 6),
  };
}

function getHotelProfileSectionCompletion(sectionId, draft) {
  switch (sectionId) {
    case 'general':
      return describeCompletion([
        {ok: Boolean(draft.hotel_name?.tr || draft.hotel_name?.en), label: 'TR veya EN hotel adi', path: 'hotel_name'},
        {ok: Boolean(draft.hotel_type), label: 'otel türü', path: 'hotel_type'},
        {ok: Boolean(draft.currency_base), label: 'temel para birimi', path: 'currency_base'},
        {ok: Boolean(draft.timezone), label: 'saat dilimi', path: 'timezone'},
        {ok: Boolean(draft.whatsapp_number), label: 'WhatsApp numarası', path: 'whatsapp_number'},
        {ok: Boolean(draft.season?.open), label: 'sezon açılışı', path: 'season.open'},
        {ok: Boolean(draft.season?.close), label: 'sezon kapanışı', path: 'season.close'},
      ], 'Temel kimlik, sezon ve para birimi tanımlandı.');
    case 'contacts':
      return describeCompletion([
        {ok: Object.keys(asObject(draft.contacts)).length > 0, label: 'en az 1 iletişim kaydı', path: 'contacts'},
        {ok: Boolean(draft.location?.city), label: 'şehir', path: 'location.city'},
        {ok: Boolean(draft.location?.address), label: 'adres', path: 'location.address'},
      ], 'İletişim ve konum bilgileri hazır.');
    case 'rooms':
      return describeCompletion([
        {ok: Array.isArray(draft.room_types) && draft.room_types.length > 0, label: 'en az 1 oda tipi', path: 'room_types'},
        {ok: Array.isArray(draft.room_types) && draft.room_types.some(item => Boolean(item?.name?.tr || item?.name?.en)), label: 'oda tipi adı', path: 'room_types'},
        {ok: Array.isArray(draft.room_types) && draft.room_types.some(item => Number(item?.max_pax || 0) > 0), label: 'maksimum kişi sayısı', path: 'room_types'},
        {ok: Array.isArray(draft.room_types) && draft.room_types.some(item => Boolean(item?.description?.tr || item?.description?.en)), label: 'oda açıklaması', path: 'room_types'},
        {ok: Array.isArray(draft.room_common?.amenities) && draft.room_common.amenities.length > 0, label: 'oda olanak listesi', path: 'room_common.amenities'},
      ], 'Oda tipleri ve ortak oda bilgileri hazır.');
    case 'pricing':
      return describeCompletion([
        {ok: Array.isArray(draft.board_types) && draft.board_types.length > 0, label: 'en az 1 pansiyon türü', path: 'board_types'},
        {ok: Object.keys(asObject(draft.rate_mapping)).length > 0, label: 'fiyat eşleştirmesi', path: 'rate_mapping'},
        {ok: Object.values(asObject(draft.rate_mapping)).some(item => Number(item?.rate_type_id || 0) > 0 && Number(item?.rate_code_id || 0) > 0), label: 'fiyat türü / kod kimliği', path: 'rate_mapping'},
        {ok: Object.keys(asObject(draft.cancellation_rules)).length > 0, label: 'iptal kuralı', path: 'cancellation_rules'},
      ], 'Pansiyon ve fiyat eşleştirmeleri girildi.');
    case 'transfers':
      return describeCompletion([
        {ok: Array.isArray(draft.transfer_routes) && draft.transfer_routes.length > 0, label: 'en az 1 transfer güzergâhı', path: 'transfer_routes'},
        {ok: Array.isArray(draft.transfer_routes) && draft.transfer_routes.some(item => Boolean(item?.from_location) && Boolean(item?.to_location)), label: 'güzergâh başlangıç / varış noktası', path: 'transfer_routes'},
        {ok: Array.isArray(draft.transfer_routes) && draft.transfer_routes.some(item => Number(item?.price_eur || 0) > 0), label: 'transfer fiyatı (EUR)', path: 'transfer_routes'},
      ], 'Transfer güzergâhları tanımlandı.');
    case 'restaurant':
      return describeCompletion([
        {ok: Boolean(draft.restaurant?.name), label: 'restoran adı', path: 'restaurant.name'},
        {ok: Number(draft.restaurant?.capacity_max || 0) > 0, label: 'restoran maksimum kapasitesi', path: 'restaurant.capacity_max'},
        {ok: Array.isArray(draft.restaurant?.area_types) && draft.restaurant.area_types.length > 0, label: 'restoran alan türü', path: 'restaurant.area_types'},
        {ok: Object.keys(asObject(draft.restaurant?.hours)).length > 0, label: 'restoran saatleri', path: 'restaurant.hours'},
        {ok: Array.isArray(draft.assistant?.menu_source_documents) && draft.assistant.menu_source_documents.length > 0, label: 'menü kaynak dokümanları', path: 'assistant.menu_source_documents'},
        {ok: Boolean(String(draft.assistant?.menu_scope_prompt || '').trim()), label: 'menü kapsam talimatı', path: 'assistant.menu_scope_prompt'},
      ], 'Restoran kimliği ve saatleri tanımlandı.');
    case 'faq':
      return describeCompletion([
        {ok: Array.isArray(draft.faq_data) && draft.faq_data.length > 0, label: 'en az 1 SSS kaydı', path: 'faq_data'},
        {ok: Array.isArray(draft.faq_data) && draft.faq_data.some(item => Boolean(item?.question_tr || item?.question_en)), label: 'SSS sorusu', path: 'faq_data'},
        {ok: Array.isArray(draft.faq_data) && draft.faq_data.some(item => Boolean(item?.answer_tr || item?.answer_en)), label: 'SSS cevabı', path: 'faq_data'},
      ], 'SSS kayıtları hazır.');
    case 'policies':
      return describeCompletion([
        {ok: Object.keys(asObject(draft.payment)).length > 0, label: 'ödeme politikası', path: 'payment'},
        {ok: Object.keys(asObject(draft.facility_policies)).length > 0 || Object.keys(asObject(draft.operational)).length > 0, label: 'tesis veya operasyon politikası', path: 'facility_policies'},
      ], 'Politika ve operasyon alanları dolduruldu.');
    case 'assistant':
      return describeCompletion([
        {ok: Boolean(draft.hotel_conversational_flow?.style), label: 'yanıt stili', path: 'hotel_conversational_flow.style'},
        {ok: Number(draft.hotel_conversational_flow?.max_paragraph_lines || 0) > 0, label: 'paragraf başına maksimum satır', path: 'hotel_conversational_flow.max_paragraph_lines'},
        {ok: Number(draft.hotel_conversational_flow?.max_list_items || 0) > 0, label: 'maksimum liste öğesi', path: 'hotel_conversational_flow.max_list_items'},
        {ok: Number(draft.hotel_conversational_flow?.max_follow_up_questions || 0) > 0, label: 'maksimum takip sorusu', path: 'hotel_conversational_flow.max_follow_up_questions'},
      ], 'Yapay zekâ akışı parametreleri tanımlandı.');
    default:
      return {complete: false, description: 'Alanlar bekleniyor.', passed: 0, total: 0, missing: []};
  }
}

function describeCompletion(checks, completeMessage) {
  const normalizedChecks = checks.map(item => (
    typeof item === 'object' && item !== null
      ? {ok: Boolean(item.ok), label: String(item.label || ''), path: String(item.path || '')}
      : {ok: Boolean(item), label: '', path: ''}
  ));
  const total = normalizedChecks.length;
  const passed = normalizedChecks.filter(item => item.ok).length;
  const missing = normalizedChecks.filter(item => !item.ok).map(item => ({
    label: item.label,
    path: item.path,
  })).filter(item => item.label);
  if (passed >= total) {
    return {complete: true, description: completeMessage, passed, total, missing: []};
  }
  const missingPreview = missing.slice(0, 2).map(item => item.label).join(', ');
  const remaining = missing.length > 2 ? ` +${missing.length - 2}` : '';
  return {
    complete: false,
    description: missingPreview ? `Eksik: ${missingPreview}${remaining}` : `${passed}/${total} zorunlu alan hazır.`,
    passed,
    total,
    missing,
  };
}

function getHotelFactsDraftValidation() {
  if (state.hotelFactsDraftValidation) return state.hotelFactsDraftValidation;
  return buildHotelFactsDraftValidationFromStatus(state.hotelFactsStatus);
}

function getHotelProfileIssues(status = getHotelFactsDraftValidation()) {
  const blockers = Array.isArray(status?.blockers) ? status.blockers : [];
  const warnings = Array.isArray(status?.warnings) ? status.warnings : [];
  return [...blockers, ...warnings];
}

function getHotelProfileIssuesForSection(sectionId) {
  return getHotelProfileIssues().filter(issue => mapHotelProfileIssueToSection(issue.path || '') === sectionId);
}

function mapHotelProfileIssueToSection(path) {
  const normalized = String(path || '').trim();
  if (!normalized || normalized === 'profile_json') return 'general';
  const root = extractRootPath(normalized);
  if (['hotel_name', 'hotel_type', 'timezone', 'currency_base', 'pms', 'whatsapp_number', 'season', 'description', 'highlights'].includes(root)) return 'general';
  if (['contacts', 'location'].includes(root)) return 'contacts';
  if (['room_types', 'room_common'].includes(root)) return 'rooms';
  if (['board_types', 'rate_mapping', 'cancellation_rules'].includes(root)) return 'pricing';
  if (root === 'transfer_routes') return 'transfers';
  if (root === 'restaurant') return 'restaurant';
  if (root === 'assistant') return 'restaurant';
  if (root === 'faq_data') return 'faq';
  if (['payment', 'facility_policies', 'operational'].includes(root)) return 'policies';
  if (root === 'hotel_conversational_flow') return 'assistant';
  return 'general';
}

function matchesProfileIssuePath(fieldPath, issuePath) {
  const normalizedField = String(fieldPath || '').trim();
  const normalizedIssue = String(issuePath || '').trim();
  if (!normalizedField || !normalizedIssue) return false;
  return normalizedField === normalizedIssue
    || normalizedField.startsWith(`${normalizedIssue}.`)
    || normalizedIssue.startsWith(`${normalizedField}.`)
    || normalizedField.startsWith(`${normalizedIssue}[`)
    || normalizedIssue.startsWith(`${normalizedField}[`);
}

function openHotelProfileOverviewTarget(sectionId, path) {
  if (!sectionId) return;
  state.hotelProfileSearch = '';
  if (state.hotelProfileSection !== sectionId) {
    state.hotelProfileSection = sectionId;
    renderHotelProfileWorkspace();
  }
  if (path) {
    window.requestAnimationFrame(() => {
      openHotelProfileIssuePath(path);
    });
    return;
  }
  focusFirstHotelProfileIssueInSection(sectionId);
}

function focusFirstHotelProfileIssueInSection(sectionId) {
  const issues = getHotelProfileIssuesForSection(sectionId);
  if (!issues.length) return false;
  const prioritized = issues.find(issue => issue.severity === 'blocker') || issues[0];
  if (!prioritized?.path) return false;
  window.requestAnimationFrame(() => {
    openHotelProfileIssuePath(prioritized.path);
  });
  return true;
}

function openHotelProfileIssuePath(path) {
  const targetSection = mapHotelProfileIssueToSection(path);
  state.hotelProfileSearch = '';
  const faqIndexMatch = String(path || '').match(/^faq_data\\[(\\d+)\\]/);
  if (targetSection === 'faq' && faqIndexMatch) {
    const nextIndex = Number(faqIndexMatch[1]);
    if (Number.isFinite(nextIndex) && nextIndex >= 0) {
      state.hotelProfileFaqActiveIndex = nextIndex;
    }
  }
  if (state.hotelProfileSection !== targetSection) {
    state.hotelProfileSection = targetSection;
    renderHotelProfileWorkspace();
  }
  window.requestAnimationFrame(() => {
    if (!refs.hotelProfileSectionBody) return;
    const target = Array.from(refs.hotelProfileSectionBody.querySelectorAll('[data-profile-path]')).find(node => {
      return node instanceof HTMLElement && matchesProfileIssuePath(node.dataset.profilePath || '', path);
    });
    if (!(target instanceof HTMLElement)) return;
    target.classList.add('profile-focus-pulse');
    target.scrollIntoView({behavior: 'smooth', block: 'center'});
    window.setTimeout(() => target.classList.remove('profile-focus-pulse'), 1200);
    const focusable = target.querySelector('input, textarea, select');
    if (focusable instanceof HTMLElement && !focusable.hasAttribute('disabled')) focusable.focus();
  });
}

function renameDraftMapKey(field) {
  const collection = field.dataset.profileMapKey || '';
  const oldKey = field.dataset.profileMapOldKey || '';
  const newKey = String(field.value || '').trim();
  if (!collection || !oldKey || !newKey) {
    field.value = oldKey;
    notify('Key alani bos birakilamaz.', 'warn');
    return;
  }
  const target = ensureDraftMap(collection);
  const linkedCollection = getLinkedProfileMapCollection(collection);
  const linkedTarget = linkedCollection ? ensureDraftMap(linkedCollection) : null;
  if (newKey !== oldKey && Object.prototype.hasOwnProperty.call(target, newKey)) {
    field.value = oldKey;
    notify('Bu key zaten kullaniliyor.', 'warn');
    return;
  }
  if (linkedTarget && Object.prototype.hasOwnProperty.call(linkedTarget, oldKey) && newKey !== oldKey && Object.prototype.hasOwnProperty.call(linkedTarget, newKey)) {
    field.value = oldKey;
    notify('Bağlı teknik anahtar zaten kullanılıyor.', 'warn');
    return;
  }
  if (newKey !== oldKey) {
    target[newKey] = target[oldKey];
    delete target[oldKey];
    if (linkedTarget && Object.prototype.hasOwnProperty.call(linkedTarget, oldKey)) {
      linkedTarget[newKey] = linkedTarget[oldKey];
      delete linkedTarget[oldKey];
    }
    syncHotelProfileEditorFromDraft();
    renderHotelProfileWorkspace();
    scheduleHotelFactsDraftValidation({silent: true});
  }
}

function getLinkedProfileMapCollection(collection) {
  switch (String(collection || '')) {
    case 'cancellation_rules':
      return 'rate_mapping';
    case 'rate_mapping':
      return 'cancellation_rules';
    default:
      return '';
  }
}

function ensureLinkedProfileMapEntry(collection, key) {
  const linkedCollection = getLinkedProfileMapCollection(collection);
  const normalizedKey = String(key || '').trim();
  if (!linkedCollection || !normalizedKey) return null;
  const linkedTarget = ensureDraftMap(linkedCollection);
  if (!Object.prototype.hasOwnProperty.call(linkedTarget, normalizedKey)) {
    linkedTarget[normalizedKey] = createDefaultMapEntry(linkedCollection);
  }
  return linkedTarget[normalizedKey];
}

function ensureDraftList(collection) {
  if (!Array.isArray(state.hotelProfileDraft?.[collection])) {
    state.hotelProfileDraft[collection] = [];
  }
  return state.hotelProfileDraft[collection];
}

function ensureDraftListByPath(path) {
  const current = getProfileValueByPath(state.hotelProfileDraft, path);
  if (!Array.isArray(current)) {
    setProfileValueByPath(state.hotelProfileDraft, path, []);
  }
  return getProfileValueByPath(state.hotelProfileDraft, path);
}

function ensureDraftMap(collection) {
  if (!state.hotelProfileDraft?.[collection] || typeof state.hotelProfileDraft[collection] !== 'object' || Array.isArray(state.hotelProfileDraft[collection])) {
    state.hotelProfileDraft[collection] = {};
  }
  return state.hotelProfileDraft[collection];
}

function addContactPresetToDraft(preset) {
  const contacts = ensureDraftMap('contacts');
  const config = CONTACT_PRESET_OPTIONS.find(option => option.preset === String(preset || '').toUpperCase()) || CONTACT_PRESET_OPTIONS.find(option => option.preset === 'OTHER');
  const baseKey = String(config?.key || 'contact');
  let nextKey = baseKey;
  let suffix = 2;
  while (Object.prototype.hasOwnProperty.call(contacts, nextKey)) {
    nextKey = `${baseKey}_${suffix}`;
    suffix += 1;
  }
  contacts[nextKey] = {
    phone: '',
    email: '',
    hours: '',
    name: config?.name || '',
    role: config?.role || 'OTHER',
  };
  return nextKey;
}

function addBoardTypePresetToDraft(preset) {
  const boardTypes = ensureDraftList('board_types');
  const config = BOARD_TYPE_PRESET_OPTIONS.find(option => option.preset === String(preset || '').toUpperCase());
  const defaultItem = createDefaultListItem('board_types');
  const item = {
    ...defaultItem,
    code: config?.preset || defaultItem.code,
    name: {
      tr: config?.nameTr || '',
      en: config?.nameEn || '',
    },
    breakfast_hours: config?.breakfastHours || '',
    breakfast_type: config?.breakfastType || '',
  };
  boardTypes.push(item);
  return boardTypes.length - 1;
}

function addRoomTypePresetToDraft(preset) {
  const roomTypes = ensureDraftList('room_types');
  const config = ROOM_TYPE_PRESET_OPTIONS.find(option => option.preset === String(preset || '').toUpperCase());
  const defaultItem = createDefaultListItem('room_types');
  const item = {
    ...defaultItem,
    ...asObject(config?.defaults),
    name: {
      tr: config?.defaults?.name?.tr || '',
      en: config?.defaults?.name?.en || '',
    },
    description: {tr: '', en: ''},
  };
  roomTypes.push(item);
  return roomTypes.length - 1;
}

function addCancellationRulePresetToDraft(preset) {
  const rules = ensureDraftMap('cancellation_rules');
  const normalizedPreset = String(preset || '').toUpperCase();
  const config = CANCELLATION_RULE_PRESET_OPTIONS.find(option => option.preset === normalizedPreset);
  const baseKey = config?.preset || nextProfileMapKey('cancellation_rules', rules);
  let nextKey = baseKey;
  let suffix = 2;
  while (Object.prototype.hasOwnProperty.call(rules, nextKey)) {
    nextKey = `${baseKey}_${suffix}`;
    suffix += 1;
  }
  rules[nextKey] = {
    ...createDefaultMapEntry('cancellation_rules'),
    ...asObject(config?.defaults),
  };
  ensureRateMappingEntryForKey(nextKey);
  return nextKey;
}

function ensureRateMappingEntryForKey(key) {
  return ensureLinkedProfileMapEntry('cancellation_rules', key);
}

function nextProfileMapKey(collection, current) {
  const prefixes = {
    contacts: 'new_contact',
    rate_mapping: 'new_rate',
    cancellation_rules: 'new_rule',
  };
  const prefix = prefixes[collection] || 'new_item';
  let index = 1;
  while (Object.prototype.hasOwnProperty.call(current, `${prefix}_${index}`)) {
    index += 1;
  }
  return `${prefix}_${index}`;
}

function createDefaultListItem(collection) {
  switch (collection) {
    case 'room_types':
      return {
        id: (state.hotelProfileDraft.room_types || []).length + 1,
        pms_room_type_id: 0,
        name: {tr: '', en: ''},
        max_pax: 2,
        size_m2: 0,
        bed_type: '',
        view: '',
        features: [],
        extra_bed: false,
        baby_crib: false,
        accessible: false,
        description: {tr: '', en: ''},
      };
    case 'board_types':
      return {
        id: (state.hotelProfileDraft.board_types || []).length + 1,
        code: '',
        name: {tr: '', en: ''},
        breakfast_hours: '',
        breakfast_type: '',
      };
    case 'transfer_routes':
      return {
        route_code: '',
        from_location: '',
        to_location: '',
        price_eur: 0,
        vehicle_type: '',
        max_pax: 1,
        duration_min: 0,
        baby_seat: false,
        oversize_vehicle: {},
      };
    case 'faq_data':
      return {
        faq_id: '',
        topic: '',
        status: 'ACTIVE',
        question_tr: '',
        question_en: '',
        question_variants_tr: [],
        question_variants_en: [],
        question_variants_ru: [],
        question_variants_de: [],
        question_variants_ar: [],
        question_variants_es: [],
        question_variants_fr: [],
        question_variants_zh: [],
        question_variants_hi: [],
        question_variants_pt: [],
        answer_tr: '',
        answer_en: '',
      };
    default:
      return {};
  }
}

function createDefaultPathListItem(path) {
  switch (String(path || '')) {
    case 'location.nearby':
      return {name: '', distance: ''};
    default:
      return {};
  }
}

function createDefaultMapEntry(collection) {
  switch (collection) {
    case 'contacts':
      return {phone: '', email: '', hours: '', name: '', role: ''};
    case 'rate_mapping':
      return {rate_type_id: 0, rate_code_id: 0};
    case 'cancellation_rules':
      return {
        free_cancel_deadline_days: null,
        prepayment_days_before: null,
        prepayment_amount: '1_night',
        prepayment_immediate: false,
        refund: true,
        refund_after_deadline: false,
        exception_days_before: null,
        exception_refund: '',
      };
    default:
      return {};
  }
}

function buildProfileSearchText(label, value) {
  if (Array.isArray(value)) return `${label} ${value.join(' ')}`.trim();
  if (value && typeof value === 'object') return `${label} ${JSON.stringify(value)}`.trim();
  return `${label} ${String(value ?? '')}`.trim();
}

function coerceProfileFieldValue(field) {
  if (field.type === 'checkbox') return Boolean(field.checked);
  if (field.dataset.numberKind === 'int') {
    if (field.dataset.emptyNull === 'true' && !String(field.value || '').trim()) return null;
    return Number.parseInt(String(field.value || '0'), 10) || 0;
  }
  if (field.dataset.numberKind === 'float') {
    if (field.dataset.emptyNull === 'true' && !String(field.value || '').trim()) return null;
    return Number.parseFloat(String(field.value || '0')) || 0;
  }
  return String(field.value || '');
}

function getProfileValueByPath(root, path) {
  return tokenizeProfilePath(path).reduce((current, token) => (
    current == null ? undefined : current[token]
  ), root);
}

function setProfileValueByPath(root, path, value) {
  const tokens = tokenizeProfilePath(path);
  if (!tokens.length) return;
  let cursor = root;
  for (let index = 0; index < tokens.length - 1; index += 1) {
    const token = tokens[index];
    const nextToken = tokens[index + 1];
    if (cursor[token] == null) {
      cursor[token] = typeof nextToken === 'number' ? [] : {};
    }
    cursor = cursor[token];
  }
  cursor[tokens[tokens.length - 1]] = value;
}

function tokenizeProfilePath(path) {
  const tokens = [];
  const matcher = /([^[.\\]]+)|\\[(\\d+)\\]/g;
  let match;
  while ((match = matcher.exec(String(path || ''))) !== null) {
    if (match[1] != null) tokens.push(match[1]);
    else if (match[2] != null) tokens.push(Number(match[2]));
  }
  return tokens;
}

function renderHotelFactsStatus(status) {
  if (!refs.hotelFactsStatus) return;
  if (!status) {
    refs.hotelFactsStatus.innerHTML = '<div class="empty-state"><p>Veri sürümü durumu alınamadı.</p></div>';
    if (refs.publishHotelFacts) refs.publishHotelFacts.disabled = true;
    if (refs.saveHotelProfile) refs.saveHotelProfile.disabled = true;
    return;
  }

  const localValidation = getHotelFactsDraftValidation();
  const technicalMode = isHotelProfileTechnicalMode();
  const blockers = Array.isArray(localValidation?.blockers) ? localValidation.blockers : [];
  const warnings = Array.isArray(localValidation?.warnings) ? localValidation.warnings : [];
  const stateCopy = getHotelFactsStateCopy(status);
  const blockerItems = blockers.length
    ? blockers.map(item => `<span>• ${escapeHtml(item.path || '-')}: ${escapeHtml(item.message || item.code || '-')}</span>`).join('')
    : '<span>• Engelleyici sorun yok</span>';
  const warningItems = warnings.length
    ? warnings.map(item => `<span>• ${escapeHtml(item.path || '-')}: ${escapeHtml(item.message || item.code || '-')}</span>`).join('')
    : '<span>• Uyarı yok</span>';

  refs.hotelFactsStatus.innerHTML = `
    <div class="status-list">
      <div class="status-block">
        <h4>Canlıya Alma Durumu</h4>
        <p><span class="pill ${escapeHtml(stateCopy.pill)}">${escapeHtml(stateCopy.label)}</span></p>
        <p class="muted">${escapeHtml(stateCopy.description)}</p>
      </div>
      <div class="status-block">
        <h4>Yayın Özeti</h4>
        <p class="mono">Canlı sürüm: ${escapeHtml(status.current_version != null ? `v${String(status.current_version)}` : '-')}</p>
        <p class="mono">Yayınlayan: ${escapeHtml(status.published_by || '-')}</p>
        <p class="mono">Tarih: ${escapeHtml(formatDate(status.published_at) || '-')}</p>
      </div>
      <div class="status-block">
        <h4>${technicalMode ? 'Taslak / Canlı Karşılaştırması' : 'Taslak Durumu'}</h4>
        <p class="mono">${technicalMode ? `Kaydedilmiş taslak checksum: ${escapeHtml(status.draft_facts_checksum || '-')}` : `Canlı sistem ile aynı mı: ${status.draft_matches_runtime ? 'Evet' : 'Hayır'}`}</p>
        <p class="mono">${technicalMode ? `Canlı checksum: ${escapeHtml(status.current_facts_checksum || '-')}` : `Kaydedilmiş taslak var mı: ${status.draft_facts_checksum ? 'Evet' : 'Hayır'}`}</p>
        <p class="mono">${technicalMode ? `Eşit mi: ${status.draft_matches_runtime ? 'Evet' : 'Hayır'}` : `Kaynak profil güncel mi: ${status.draft_source_profile_checksum ? 'Evet' : 'Hayır'}`}</p>
      </div>
      <div class="status-block">
        <h4>Yayın Kontrolü</h4>
        ${technicalMode ? `<p class="mono">Yerel taslak checksum: ${escapeHtml(localValidation?.facts_checksum || '-')}</p>` : ''}
        <p class="mono">Engelleyici alan: ${escapeHtml(String(blockers.length))}</p>
        <p class="mono">Uyarı: ${escapeHtml(String(warnings.length))}</p>
        <p class="muted">${escapeHtml(
          state.hotelProfileHasUnsavedChanges
            ? 'Kaydedilmemiş değişiklikler var. Yayına almadan önce taslağı kaydedin.'
            : (localValidation?.publishable ? 'Taslak yayına alınmaya hazır.' : 'Taslakta önce düzeltilmesi gereken alanlar var.')
        )}</p>
      </div>
    </div>
    <div class="helper-panel mt-md">
      <div class="helper-box">
        <strong>Engelleyici Sorunlar</strong>
        <div class="detail-list">${blockerItems}</div>
      </div>
      <div class="helper-box">
        <strong>Uyarılar</strong>
        <div class="detail-list">${warningItems}</div>
      </div>
    </div>
  `;

  if (refs.publishHotelFacts) {
    refs.publishHotelFacts.disabled = !canPublishHotelFacts(status) || state.hotelProfileHasUnsavedChanges;
  }
  if (refs.saveHotelProfile) {
    refs.saveHotelProfile.disabled = !state.hotelProfileHasUnsavedChanges;
  }
}

function renderHotelFactsHistory(items) {
  if (!refs.hotelFactsHistory) return;
  if (!Array.isArray(items) || !items.length) {
    refs.hotelFactsHistory.innerHTML = '<div class="empty-state"><p>Bu otel için henüz yayın geçmişi yok.</p></div>';
    return;
  }

  const selectedVersion = Number(state.hotelFactsVersionDetail?.version || 0);
  const rows = items.slice(0, 6).map(item => {
    const entryType = String(item.entry_type || 'PUBLISH');
    const isDraftSnapshot = entryType === 'DRAFT_SAVE';
    const pillClass = item.is_current ? 'success' : (isDraftSnapshot ? 'info' : 'closed');
    const pillText = item.is_current ? 'Aktif' : (isDraftSnapshot ? 'Taslak' : 'Arşiv');
    const versionNumber = Number(item.version || 0);
    const isSelected = selectedVersion && versionNumber === selectedVersion;
    return `
      <tr class="${isSelected ? 'is-selected' : ''}">
        <td><span class="pill ${pillClass}">${pillText}</span></td>
        <td class="mono">v${escapeHtml(String(item.version || '-'))}</td>
        <td class="mono">${escapeHtml(item.published_by || '-')}</td>
        <td class="mono">${escapeHtml(formatDate(item.published_at) || '-')}</td>
        <td class="mono">${escapeHtml(String(item.blocker_count ?? 0))}</td>
        <td class="mono">${escapeHtml(String(item.warning_count ?? 0))}</td>
        <td class="mono">${escapeHtml(item.checksum || '-')}</td>
        <td class="action-cell">
          <button class="action-button secondary ${isSelected ? 'is-active' : ''}" type="button" data-facts-version-detail="${escapeHtml(String(item.version || ''))}">${isSelected ? 'Açık' : 'Detay'}</button>
          <button class="action-button warn" type="button" data-facts-version-rollback="${escapeHtml(String(item.version || ''))}" ${item.is_current ? 'disabled' : ''}>Canlıya Al</button>
        </td>
      </tr>
    `;
  }).join('');

  refs.hotelFactsHistory.innerHTML = `
    <div class="helper-box">
      <strong>Yayın Geçmişi</strong>
      <p class="muted">Son 6 sürüm (taslak kaydı + yayın) gösterilir. Aktif sürüm canlı sistem tarafından kullanılır.</p>
    </div>
    <div class="table-shell">
      <table>
        <thead>
          <tr>
            <th>Durum</th>
            <th>Versiyon</th>
            <th>Yayınlayan</th>
            <th>Tarih</th>
            <th>Engelleyici</th>
            <th>Uyarı</th>
            <th>Checksum</th>
            <th>İşlem</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

function renderHotelFactsEvents(items) {
  if (!refs.hotelFactsEvents) return;
  if (!Array.isArray(items) || !items.length) {
    refs.hotelFactsEvents.innerHTML = '<div class="empty-state"><p>Bu otel için henüz veri sürümü denetim kaydı yok.</p></div>';
    return;
  }

  const selectedVersion = Number(state.hotelFactsVersionDetail?.version || 0);
  const rows = items.slice(0, 8).map(item => {
    const metadata = asObject(item.metadata);
    const isRollback = item.event_type === 'ROLLBACK';
    const isDraftSave = item.event_type === 'DRAFT_SAVE';
    const pillClass = isRollback ? 'warn' : (isDraftSave ? 'success' : 'info');
    const versionNumber = Number(item.version || 0);
    const isSelected = selectedVersion && versionNumber === selectedVersion;
    const eventLabel = isRollback
      ? 'Geri Alma'
      : isDraftSave
        ? 'Taslak Kaydedildi'
      : item.event_type === 'PUBLISH'
        ? 'Yayımlama'
        : (item.event_type || '-');
    const note = isRollback
      ? `Önceki sürüm: ${metadata.previous_version != null ? `v${escapeHtml(String(metadata.previous_version))}` : '-'}`
      : isDraftSave
        ? `Taslak checksum: ${escapeHtml(metadata.draft_facts_checksum || '-')}`
        : `Kaynak checksum: ${escapeHtml(metadata.source_profile_checksum || '-')}`;
    return `
      <tr class="${isSelected ? 'is-selected' : ''}">
        <td><span class="pill ${pillClass}">${escapeHtml(eventLabel)}</span></td>
        <td class="mono">v${escapeHtml(String(item.version || '-'))}</td>
        <td class="mono">${escapeHtml(item.actor || '-')}</td>
        <td class="mono">${escapeHtml(formatDate(item.occurred_at) || '-')}</td>
        <td class="mono">${note}</td>
        <td class="action-cell">
          <button class="action-button secondary ${isSelected ? 'is-active' : ''}" type="button" data-facts-version-detail="${escapeHtml(String(item.version || ''))}">${isSelected ? 'Açık' : 'Sürümü Aç'}</button>
        </td>
      </tr>
    `;
  }).join('');

  refs.hotelFactsEvents.innerHTML = `
    <div class="helper-box">
      <strong>Veri Sürümü Denetim Geçmişi</strong>
      <p class="muted">Taslak kaydetme, yayınlama ve geri alma işlemleri zaman sırasına göre listelenir.</p>
    </div>
    <div class="table-shell">
      <table>
        <thead>
          <tr>
            <th>Olay</th>
            <th>Versiyon</th>
            <th>İşlemi Yapan</th>
            <th>Zaman</th>
            <th>Not</th>
            <th>İşlem</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

function resolvePreferredHotelFactsVersion(items) {
  if (!Array.isArray(items) || !items.length) return null;
  if (state.hotelFactsVersionDetail) {
    const selectedVersion = Number(state.hotelFactsVersionDetail.version || 0);
    if (selectedVersion && items.some(item => Number(item.version) === selectedVersion)) {
      return selectedVersion;
    }
  }
  const currentItem = items.find(item => item.is_current);
  if (currentItem) return Number(currentItem.version || 0);
  return Number(items[0].version || 0) || null;
}

function revealHotelFactsVersionDetail() {
  if (!refs.hotelFactsVersionDetail) return;
  if (state.hotelFactsVersionDetailRevealTimer) {
    window.clearTimeout(state.hotelFactsVersionDetailRevealTimer);
    state.hotelFactsVersionDetailRevealTimer = null;
  }
  refs.hotelFactsVersionDetail.classList.remove('facts-detail-focus', 'profile-focus-pulse');
  void refs.hotelFactsVersionDetail.offsetWidth;
  refs.hotelFactsVersionDetail.classList.add('facts-detail-focus', 'profile-focus-pulse');
  refs.hotelFactsVersionDetail.scrollIntoView({behavior: 'smooth', block: 'start'});
  state.hotelFactsVersionDetailRevealTimer = window.setTimeout(() => {
    refs.hotelFactsVersionDetail.classList.remove('facts-detail-focus', 'profile-focus-pulse');
    state.hotelFactsVersionDetailRevealTimer = null;
  }, 1400);
}

async function loadHotelFactsVersionDetail(version, {silent = false} = {}) {
  const hotelId = refs.hotelProfileSelect.value || state.selectedHotelId;
  const versionNumber = Number(version || 0);
  if (!hotelId || !versionNumber) {
    state.hotelFactsVersionDetail = null;
    renderHotelFactsVersionDetail(null);
    return;
  }
  try {
    const detail = await apiFetch(`/hotels/${hotelId}/facts/versions/${versionNumber}`);
    state.hotelFactsVersionDetail = detail;
    renderHotelFactsHistory(state.hotelFactsVersions);
    renderHotelFactsEvents(state.hotelFactsEvents);
    renderHotelFactsVersionDetail(detail);
    if (!silent) revealHotelFactsVersionDetail();
  } catch (error) {
    state.hotelFactsVersionDetail = null;
    renderHotelFactsVersionDetail(null);
    if (!silent) notify(error.message, 'error');
  }
}

function renderHotelFactsVersionDetail(detail) {
  if (!refs.hotelFactsVersionDetail) return;
  if (!detail) {
    refs.hotelFactsVersionDetail.innerHTML = '<div class="empty-state"><p>Ayrıntıları görmek için bir yayın sürümü seçin.</p></div>';
    return;
  }

  const facts = asObject(detail.facts);
  const validation = asObject(detail.validation);
  const blockers = Array.isArray(validation.blockers) ? validation.blockers : [];
  const warnings = Array.isArray(validation.warnings) ? validation.warnings : [];
  const blockerItems = blockers.length
    ? blockers.map(item => `<span>• ${escapeHtml(item.path || '-')}: ${escapeHtml(item.message || item.code || '-')}</span>`).join('')
    : '<span>• Engelleyici sorun yok</span>';
  const warningItems = warnings.length
    ? warnings.map(item => `<span>• ${escapeHtml(item.path || '-')}: ${escapeHtml(item.message || item.code || '-')}</span>`).join('')
    : '<span>• Uyarı yok</span>';
  const roomTypes = Array.isArray(facts.room_types) ? facts.room_types.length : 0;
  const faqs = Array.isArray(facts.faq_data) ? facts.faq_data.length : 0;
  const transfers = Array.isArray(facts.transfer_routes) ? facts.transfer_routes.length : 0;
  const isCurrent = Boolean(detail.is_current);
  const entryType = String(detail.entry_type || 'PUBLISH');
  const isDraftSnapshot = !isCurrent && entryType === 'DRAFT_SAVE';
  const statusPillClass = isCurrent ? 'success' : (isDraftSnapshot ? 'info' : 'closed');
  const statusPillText = isCurrent ? 'Aktif Sürüm' : (isDraftSnapshot ? 'Taslak Sürümü' : 'Arşiv Sürümü');

  refs.hotelFactsVersionDetail.innerHTML = `
    <div class="helper-box">
      <strong>Sürüm Ayrıntıları</strong>
      <p class="muted">Seçilen sürümün içeriği ve doğrulama sonucu burada görüntülenir.</p>
    </div>
    <div class="status-list">
      <div class="status-block">
        <h4>Versiyon</h4>
        <p><span class="pill ${statusPillClass}">${statusPillText}</span></p>
        <p class="mono">v${escapeHtml(String(detail.version || '-'))}</p>
        <p class="mono">Checksum: ${escapeHtml(detail.checksum || '-')}</p>
      </div>
      <div class="status-block">
        <h4>Sürüm Bilgisi</h4>
        <p class="mono">Tür: ${escapeHtml(isDraftSnapshot ? 'Taslak Kaydı' : 'Yayın')}</p>
        <p class="mono">Yayınlayan: ${escapeHtml(detail.published_by || '-')}</p>
        <p class="mono">Tarih: ${escapeHtml(formatDate(detail.published_at) || '-')}</p>
        <p class="mono">Kaynak checksum: ${escapeHtml(detail.source_profile_checksum || '-')}</p>
      </div>
      <div class="status-block">
        <h4>İçerik Özeti</h4>
        <p class="mono">Oda tipi: ${escapeHtml(String(roomTypes))}</p>
        <p class="mono">SSS kaydı: ${escapeHtml(String(faqs))}</p>
        <p class="mono">Transfer güzergâhı: ${escapeHtml(String(transfers))}</p>
      </div>
      <div class="status-block">
        <h4>Doğrulama Özeti</h4>
        <p class="mono">Engelleyici sorun: ${escapeHtml(String(blockers.length))}</p>
        <p class="mono">Uyarı: ${escapeHtml(String(warnings.length))}</p>
        <p class="muted">${isCurrent ? 'Bu sürüm şu anda canlı sistem tarafından kullanılıyor.' : 'İsterseniz bu sürümü "Canlıya Al" ile aktif sürüme taşıyabilirsiniz.'}</p>
      </div>
    </div>
    <div class="helper-panel mt-md">
      <div class="helper-box">
        <strong>Engelleyici Sorunlar</strong>
        <div class="detail-list">${blockerItems}</div>
      </div>
      <div class="helper-box">
        <strong>Uyarılar</strong>
        <div class="detail-list">${warningItems}</div>
      </div>
    </div>
  `;
}

async function rollbackHotelFacts(version) {
  const hotelId = refs.hotelProfileSelect.value || state.selectedHotelId;
  const versionNumber = Number(version || 0);
  const localEditorSnapshot = refs.hotelProfileEditor?.value || '';
  if (!hotelId || !versionNumber) {
    notify('Geri alma için geçerli bir sürüm seçin.', 'warn');
    return;
  }
  if (!window.confirm(`v${versionNumber} sürümünü yeniden canlıya almak istediğinize emin misiniz?`)) {
    return;
  }
  try {
    const response = await apiFetch(`/hotels/${hotelId}/facts/rollback`, {
      method: 'POST',
      body: {
        version: versionNumber,
        expected_current_version: state.hotelFactsStatus?.current_version || null,
      },
    });
    clearHotelFactsConflict();
    notify(`Canlı sürüm v${response.version || versionNumber} olarak geri alındı.`, 'success');
    await loadHotelProfileSection();
  } catch (error) {
    await loadHotelProfileSection();
    if (error?.status === 409) {
      setHotelFactsConflict(buildHotelFactsConflict(error, {
        action: 'rollback',
        localEditorSnapshot,
      }));
    }
    notify(error.message, 'error');
  }
}

function getHotelFactsStateCopy(status) {
  const stateName = String(status?.state || '');
  switch (stateName) {
    case 'in_sync':
      return {
        label: 'Canlı ile Eşit',
        description: 'Taslak ile canlı sürüm aynı. Yeni publish gerekmiyor.',
        pill: 'success',
      };
    case 'draft_pending_publish':
      return {
        label: 'Yayın Bekliyor',
        description: 'Taslak geçerli ancak canlı sürümden farklı. Canlıya almak için yayın gerekir.',
        pill: 'warn',
      };
    case 'blocked':
      return {
        label: 'Engelleyici Sorun Var',
        description: 'Taslak engelleyici sorun içeriyor. Mevcut canlı sürüm korunuyor.',
        pill: 'danger',
      };
    case 'unpublished':
      return {
        label: 'Henüz Yayımlanmadı',
        description: 'Bu otel için henüz yayımlanmış veri sürümü yok.',
        pill: 'info',
      };
    case 'blocked_unpublished':
      return {
        label: 'Yayın Yok / Engelleyici Sorun Var',
        description: 'İlk yayın için engelleyici alanlar düzeltilmeli.',
        pill: 'danger',
      };
    default:
      return {
        label: 'Bilinmiyor',
        description: 'Veri sürümü durumu netleştirilemedi.',
        pill: 'closed',
      };
  }
}

function canPublishHotelFacts(status) {
  const stateName = String(status?.state || '');
  return stateName === 'draft_pending_publish' || stateName === 'unpublished';
}

function resolveHotelFactsTone(status) {
  const stateName = String(status?.state || '');
  if (stateName === 'blocked' || stateName === 'blocked_unpublished') return 'warn';
  if (stateName === 'draft_pending_publish') return 'warn';
  return 'success';
}

function buildHotelProfileSaveMessage(response) {
  const status = response?.facts_status || {};
  const stateName = String(status.state || '');
  if (stateName === 'in_sync') {
    return `Profil kaydedildi (${response.profile_path}). Taslak canlı sürüm ile aynı.`;
  }
  if (stateName === 'draft_pending_publish') {
    return `Profil kaydedildi (${response.profile_path}). Taslak canlıdan farklı; "Canlıya Al" ile yayımlayın.`;
  }
  if (stateName === 'blocked' || stateName === 'blocked_unpublished') {
    return `Profil kaydedildi (${response.profile_path}). Taslak engelleyici sorun içeriyor; canlı sürüm korunuyor.`;
  }
  return `Profil kaydedildi (${response.profile_path}).`;
}

async function publishHotelFacts() {
  if (document.activeElement instanceof HTMLElement) {
    document.activeElement.blur();
  }
  const hotelId = refs.hotelProfileSelect.value || state.selectedHotelId;
  const localEditorSnapshot = refs.hotelProfileEditor?.value || '';
  if (!hotelId) {
    notify('Lütfen bir otel seçin.', 'warn');
    return;
  }
  if (state.hotelProfileHasUnsavedChanges) {
    notify('Kaydedilmemiş değişiklikler var. Önce "Taslağı Kaydet" ile taslağı güncelleyin.', 'warn');
    return;
  }
  try {
    const response = await apiFetch(`/hotels/${hotelId}/facts/publish`, {
      method: 'POST',
      body: {
        expected_source_profile_checksum: state.hotelProfileLoadedSourceChecksum || null,
      },
    });
    clearHotelFactsConflict();
    notify(`Canlı sürüm güncellendi. Sürüm ${response.version || '-'}.`, response.published ? 'success' : 'info');
    await loadHotelProfileSection();
  } catch (error) {
    if (error?.status === 409) {
      await loadHotelProfileSection();
      setHotelFactsConflict(buildHotelFactsConflict(error, {
        action: 'publish',
        localEditorSnapshot,
      }));
    }
    notify(error.message, 'error');
  }
}

function filterRestaurantSlotsByDisplay(items) {
  const mode = refs.slotDisplayInterval?.value || '1d';
  if (mode === 'hidden') return [];
  if (mode === '1m') return items;

  const sorted = [...items].sort((a, b) => {
    const left = `${a.date}T${a.time}`;
    const right = `${b.date}T${b.time}`;
    return left.localeCompare(right);
  });

  const monthDiff = (a, b) => ((b.getUTCFullYear() - a.getUTCFullYear()) * 12) + (b.getUTCMonth() - a.getUTCMonth());
  const shouldKeep = (prevDate, currentDate) => {
    switch (mode) {
      case '1h': return currentDate.getUTCHours() !== prevDate.getUTCHours() || currentDate.getUTCDate() !== prevDate.getUTCDate() || currentDate.getUTCMonth() !== prevDate.getUTCMonth() || currentDate.getUTCFullYear() !== prevDate.getUTCFullYear();
      case '2h': return (currentDate - prevDate) >= 2 * 60 * 60 * 1000;
      case '1d': return currentDate.toISOString().slice(0,10) !== prevDate.toISOString().slice(0,10);
      case '3d': return (currentDate - prevDate) >= 3 * 24 * 60 * 60 * 1000;
      case '1w': return (currentDate - prevDate) >= 7 * 24 * 60 * 60 * 1000;
      case '15d': return (currentDate - prevDate) >= 15 * 24 * 60 * 60 * 1000;
      case '30d': return (currentDate - prevDate) >= 30 * 24 * 60 * 60 * 1000;
      case '2mo': return monthDiff(prevDate, currentDate) >= 2;
      default: return true;
    }
  };

  const result = [];
  let prev = null;
  sorted.forEach(item => {
    const current = new Date(`${item.date}T${item.time}Z`);
    if (!prev || shouldKeep(prev, current)) {
      result.push(item);
      prev = current;
    }
  });
  return result;
}

function applySlotDisplayFilter() {
  const filteredItems = filterRestaurantSlotsByDisplay(state.restaurantSlots || []);
  refs.slotTableBody.innerHTML = renderSlotRows(filteredItems);
  if (refs.slotSummaryCards) refs.slotSummaryCards.innerHTML = renderSlotSummaryCards(filteredItems);
  bindSlotActions();
}

async function loadRestaurantSlots(options = {}) {
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
  const shouldSyncRestaurantFilters = Boolean(options && options.syncRestaurantFilters);
  if (shouldSyncRestaurantFilters) {
    state.restaurantDateFrom = params.get('date_from') || '';
    state.restaurantDateTo = params.get('date_to') || '';
    if (refs.restaurantDateFrom) refs.restaurantDateFrom.value = state.restaurantDateFrom;
    if (refs.restaurantDateTo) refs.restaurantDateTo.value = state.restaurantDateTo;
  }
  const response = await apiFetch(`/hotels/${hotelId}/restaurant/slots?${params.toString()}`);
  state.restaurantSlots = response.items || [];
  applySlotDisplayFilter();
  if (shouldSyncRestaurantFilters && typeof loadRestaurantHolds === 'function') {
    await loadRestaurantHolds();
  }
}

function renderSlotSummaryCards(items) {
  if (!items.length) {
    return '<div class="module-card"><div class="empty-state"><p>Grafik için önce slot oluşturun veya filtreyle yükleyin.</p></div></div>';
  }
  const uniqueWindows = new Map();
  items.forEach(item => {
    const key = [item.area, item.window_date_from || item.date, item.window_date_to || item.date, item.window_start_time || item.time, item.window_end_time || item.time].join('|');
    if (!uniqueWindows.has(key)) uniqueWindows.set(key, item);
  });
  const summaryItems = Array.from(uniqueWindows.values());
  const totalCapacity = summaryItems.reduce((sum, item) => sum + Number(item.reservation_limit || item.total_capacity || 0), 0);
  const totalBooked = summaryItems.reduce((sum, item) => sum + Number(item.window_booked_reservations || item.booked_count || 0), 0);
  const totalLeft = summaryItems.reduce((sum, item) => sum + Number(item.capacity_left || 0), 0);
  const totalPartyLimit = summaryItems.reduce((sum, item) => sum + Number(item.total_party_size_limit || 0), 0);
  const totalPartyBooked = summaryItems.reduce((sum, item) => sum + Number(item.window_booked_party_size || 0), 0);
  const activeCount = summaryItems.filter(item => item.is_active).length;
  const passiveCount = summaryItems.length - activeCount;
  const firstTime = items.map(item => String(item.time || '')).sort()[0] || '-';
  const lastTime = items.map(item => String(item.time || '')).sort().slice(-1)[0] || '-';
  const usagePct = totalCapacity > 0 ? Math.min(100, Math.round((totalBooked / totalCapacity) * 100)) : 0;
  const freePct = totalCapacity > 0 ? Math.max(0, 100 - usagePct) : 0;
  return `
    <article class="slot-summary-card">
      <h4>Kapasite Grafiği</h4>
      <div class="slot-summary-value">${escapeHtml(String(totalLeft))} boş / ${escapeHtml(String(totalCapacity))}</div>
      <div class="slot-progress" aria-label="Kapasite kullanım grafiği"><div class="slot-progress-bar" style="width:${escapeHtml(String(usagePct))}%"></div></div>
      <div class="slot-summary-meta">Dolu: ${escapeHtml(String(totalBooked))} • Kişi: ${escapeHtml(String(totalPartyBooked))}/${escapeHtml(String(totalPartyLimit))} • Boş yüzdesi: ${escapeHtml(String(freePct))}%</div>
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
      <td><strong>${escapeHtml(item.capacity_left)}</strong> kaldı<br><small>${escapeHtml(item.window_booked_reservations ?? item.booked_count)} dolu / ${escapeHtml(item.reservation_limit ?? item.total_capacity)} toplam rezervasyon</small><br><small>Toplam kişi: ${escapeHtml(item.window_booked_party_size ?? 0)} / ${escapeHtml(item.total_party_size_limit ?? '-')}</small><br><small>Kişi: ${escapeHtml(item.min_party_size ?? 1)}-${escapeHtml(item.max_party_size ?? 8)}</small></td>
      <td>${item.is_active ? '<span class="pill open">MİSAFİRE AÇIK</span>' : '<span class="pill closed">PASİF</span>'}</td>
      <td>
        <div class="stack">
          <input type="number" min="1" value="${escapeHtml(item.reservation_limit ?? item.total_capacity)}" data-slot-capacity="${escapeHtml(item.slot_id)}" aria-label="${escapeHtml(item.slot_id + ' toplam rezervasyon limiti')}">
          <input type="number" min="1" value="${escapeHtml(item.min_party_size ?? 1)}" data-slot-min-party="${escapeHtml(item.slot_id)}" aria-label="${escapeHtml(item.slot_id + ' min kisi')}">
          <input type="number" min="1" value="${escapeHtml(item.max_party_size ?? 8)}" data-slot-max-party="${escapeHtml(item.slot_id)}" aria-label="${escapeHtml(item.slot_id + ' max kisi')}">
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
      const minParty = document.querySelector(`[data-slot-min-party="${slotId}"]`).value;
      const maxParty = document.querySelector(`[data-slot-max-party="${slotId}"]`).value;
      const isActive = document.querySelector(`[data-slot-active="${slotId}"]`).value === 'true';
      try {
        await apiFetch(`/hotels/${state.selectedHotelId}/restaurant/slots/${slotId}`, {
          method: 'PUT',
          body: {
            total_capacity: Number(capacity),
            reservation_limit: Number(capacity),
            min_party_size: Number(minParty),
            max_party_size: Number(maxParty),
            is_active: isActive,
          },
        });
        notify('Slot güncellendi.', 'success');
        loadRestaurantSlots();
      } catch (error) {
        notify(error.message, 'error');
      }
    });
  });
}

async function onDeleteSlots(event) {
  event.preventDefault();
  if (!state.selectedHotelId) {
    notify('Hotel seçin.', 'warn');
    return;
  }

  const form = refs.slotDeleteForm;
  const dateFrom = form.querySelector('[name="date_from"]').value;
  const dateTo = form.querySelector('[name="date_to"]').value;
  const startTime = form.querySelector('[name="start_time"]').value;
  const endTime = form.querySelector('[name="end_time"]').value;
  const areaField = form.querySelector('[name="area"]');
  const area = areaField ? String(areaField.value || '').trim() : '';
  const weekdays = Array.from(form.querySelectorAll('[name="weekdays"]:checked')).map(input => Number(input.value));

  if (!dateFrom || !dateTo || !startTime || !endTime) {
    notify('Tarih ve saat aralığı zorunlu.', 'warn');
    return;
  }

  const dayLabelMap = ['Pzt', 'Sal', 'Car', 'Per', 'Cum', 'Cmt', 'Paz'];
  const weekdayText = weekdays.length ? weekdays.map(day => dayLabelMap[day] || '?').join(', ') : 'tum gunler';
  const areaText = area || 'tum alanlar';
  const confirmed = window.confirm(
    `Bu işlem ${dateFrom} - ${dateTo} arasında ${startTime} - ${endTime} saatleri icindeki ${areaText} slotlarını silecek. Gun filtresi: ${weekdayText}. Devam edilsin mi?`
  );
  if (!confirmed) return;

  const payload = {
    date_from: dateFrom,
    date_to: dateTo,
    start_time: startTime,
    end_time: endTime,
  };
  if (weekdays.length) payload.weekdays = weekdays;
  if (area) payload.area = area;

  try {
    const response = await apiFetch(`/hotels/${state.selectedHotelId}/restaurant/slots`, {
      method: 'DELETE',
      body: payload,
    });
    notify(`${response.deleted_count || 0} slot silindi.`, 'success');
    loadRestaurantSlots();
  } catch (error) {
    notify(error.message, 'error');
  }
}

async function onCreateSlot(event) {
  event.preventDefault();
  if (!state.selectedHotelId) {
    notify('Hotel seçin.', 'warn');
    return;
  }
  const formPayload = formToJson(refs.slotCreateForm);
  if (!formPayload.start_time || !formPayload.end_time) {
    notify('Başlangıç ve bitiş saati zorunlu.', 'warn');
    return;
  }

  const reservationLimit = Number(formPayload.reservation_limit);
  const totalPartySizeLimit = Number(formPayload.total_party_size_limit);
  const minPartySize = Number(formPayload.min_party_size || 1);
  const maxPartySize = Number(formPayload.max_party_size || 8);
  if (!Number.isFinite(reservationLimit) || reservationLimit < 1) {
    notify('Toplam rezervasyon sayısı zorunlu.', 'warn');
    return;
  }
  if (!Number.isFinite(totalPartySizeLimit) || totalPartySizeLimit < 1) {
    notify('Toplam kişi sayısı limiti zorunlu.', 'warn');
    return;
  }
  if (!Number.isFinite(minPartySize) || minPartySize < 1 || !Number.isFinite(maxPartySize) || maxPartySize < minPartySize) {
    notify('Geçerli bir kişi aralığı girin.', 'warn');
    return;
  }

  const payload = {
    date_from: formPayload.date_from,
    date_to: formPayload.date_to,
    start_time: formPayload.start_time,
    end_time: formPayload.end_time,
    area: formPayload.area,
    total_capacity: reservationLimit,
    reservation_limit: reservationLimit,
    total_party_size_limit: totalPartySizeLimit,
    min_party_size: minPartySize,
    max_party_size: maxPartySize,
    is_active: formPayload.is_active === 'on',
  };

  try {
    await apiFetch(`/hotels/${state.selectedHotelId}/restaurant/slots`, {method: 'POST', body: [payload]});
    notify('Tarihler arası kapasite oluşturuldu.', 'success');
    refs.slotCreateForm.reset();
    loadRestaurantSlots();
  } catch (error) {
    notify(error.message, 'error');
  }
}

async function loadSystemOverview() {
  const systemOverview = await apiFetch('/system/overview');
  const readyState = {
    status: systemOverview.status || '-',
    checks: systemOverview.checks || {},
  };
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
      <p>${escapeHtml(prefs.user_label || 'Aktif kullanıcı')} için tanımlı.</p>
      <div class="detail-list">
        <span>OTP atlama: ${prefs.verification_active ? 'Açık' : 'Kapalı'}</span>
        <span>Oturum geri yükleme: ${prefs.session_active ? 'Açık' : 'Kapalı'}</span>
        <span>Son doğrulama: ${escapeHtml(formatDate(prefs.last_verified_at))}</span>
      </div>
    </div>
  ` : '<div class="empty-state"><p>Bu cihaz için kayıtlı hızlı giriş bulunmuyor.</p></div>';
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
      notify('Tercihleri kaydetmek için 6 haneli kod gerekli.', 'warn');
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
    notify(payload.remember_device ? 'Cihaz tercihleri kaydedildi.' : 'Bu cihaz için hızlı giriş kapatıldı.', 'success');
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
    notify('Bu cihaz artık hatırlanmayacak.', 'success');
  } catch (error) {
    notify(error.message, 'error');
  }
}

function formatConversationState(value) {
  const mapping = {
    GREETING: 'Karşılama',
    PENDING_APPROVAL: 'Onay Bekliyor',
    CONFIRMED: 'Onaylandı',
    HANDOFF: 'İnsan Devrinde',
    CLOSED: 'Kapalı',
  };
  return mapping[String(value || '').toUpperCase()] || String(value || '-');
}

function formatFaqStatus(value) {
  const mapping = {
    DRAFT: 'Taslak',
    ACTIVE: 'Aktif',
    PAUSED: 'Duraklatıldı',
    REMOVED: 'Kaldırıldı',
  };
  return mapping[String(value || '').toUpperCase()] || String(value || '-');
}

function formatTicketStatus(value) {
  const mapping = {
    OPEN: 'Açık',
    IN_PROGRESS: 'İşlemde',
    RESOLVED: 'Çözüldü',
    CLOSED: 'Kapalı',
  };
  return mapping[String(value || '').toUpperCase()] || String(value || '-');
}

function formatPriorityLabel(value) {
  const mapping = {
    HIGH: 'Yüksek',
    MEDIUM: 'Orta',
    LOW: 'Düşük',
  };
  return mapping[String(value || '').toUpperCase()] || String(value || '-');
}

function formatHoldType(value) {
  const mapping = {
    STAY: 'Konaklama',
    STAY_HOLD: 'Konaklama',
    RESTAURANT: 'Restoran',
    RESTAURANT_HOLD: 'Restoran',
    TRANSFER: 'Transfer',
    TRANSFER_HOLD: 'Transfer',
  };
  return mapping[String(value || '').toUpperCase()] || String(value || '-');
}

function formatOperationalStatus(value) {
  const mapping = {
    OPEN: 'Açık',
    PENDING: 'Beklemede',
    PENDING_APPROVAL: 'Onay Bekliyor',
    APPROVED: 'Onaylandı',
    CONFIRMED: 'Onaylandı',
    REJECTED: 'Reddedildi',
    CANCELLED: 'İptal Edildi',
    CLOSED: 'Kapalı',
  };
  return mapping[String(value || '').toUpperCase()] || String(value || '-');
}

function resolveConversationIntent(conversation, messages) {
  if (conversation?.current_intent) return String(conversation.current_intent);
  const assistant = [...(messages || [])].reverse().find(message => message.role === 'assistant');
  const internal = asObject(assistant?.internal_json);
  return String(internal.intent || 'intent yok');
}

function resolveConversationState(conversation, messages) {
  if (conversation?.current_state) return formatConversationState(conversation.current_state);
  const assistant = [...(messages || [])].reverse().find(message => message.role === 'assistant');
  const internal = asObject(assistant?.internal_json);
  return formatConversationState(internal.state || '-');
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
  state.conversationsTotal = 0;
  state.selectedConversationIds = new Set();
  state.faqs = [];
  state.faqDetail = null;
  state.hotelProfileLoadedSourceChecksum = null;
  state.hotelProfileLoadedDraftSnapshot = null;
  state.hotelProfileHasUnsavedChanges = false;
  state.hotelProfileMode = 'standard';
  state.hotelProfileFaqActiveIndex = 0;
  state.hotelFactsStatus = null;
  state.hotelFactsDraftValidation = null;
  state.hotelFactsVersions = [];
  state.hotelFactsVersionDetail = null;
  state.hotelFactsVersionDetailRevealTimer = null;
  state.hotelFactsApiUnavailable = false;
  state.sessionPreferences = null;
  state.stayWizardReprocessStatus = '';
  state.stayProfileRoomTypes = [];
  stopAuthKeepAlive();
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
    var error = new Error(extractErrorMessage(payload));
    error.status = response.status;
    error.payload = payload;
    throw error;
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

// ── Auth keep-alive: proactive token refresh + visibility handler ──────────
// Refreshes the access token well before it expires (every 50 min for 60 min TTL).
// Also refreshes immediately when the user returns to a hidden tab.
const AUTH_KEEPALIVE_MS = 50 * 60 * 1000; // 50 minutes

function startAuthKeepAlive() {
  stopAuthKeepAlive();
  state._authKeepAliveTimer = window.setInterval(authKeepAliveTick, AUTH_KEEPALIVE_MS);
  if (!state._visibilityBound) {
    state._visibilityBound = true;
    document.addEventListener('visibilitychange', onVisibilityChange);
  }
}

function stopAuthKeepAlive() {
  if (state._authKeepAliveTimer) {
    window.clearInterval(state._authKeepAliveTimer);
    state._authKeepAliveTimer = null;
  }
}

async function authKeepAliveTick() {
  // Only refresh if we're logged in (panel visible)
  if (!state.me) return;
  await refreshAccessSession({silent: true});
}

async function onVisibilityChange() {
  if (document.visibilityState !== 'visible') return;
  if (!state.me) return;
  // Check if access cookie is still present
  const hasAccess = Boolean(readCookie('velox_admin_access'));
  if (hasAccess) return; // token still alive, nothing to do
  // Token expired while tab was hidden — attempt silent refresh
  const recovered = await refreshAccessSession({silent: true});
  if (!recovered) {
    clearClientSession();
    showAuth();
    notify('Oturum suresi doldu — lutfen tekrar giris yapin.', 'warn');
  }
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
