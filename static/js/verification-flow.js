// State management
// State management Controller
const VerificationFlow = {
    currentStep: 1,
    selectedService: null,
    selectedServicePrice: null,
    selectedAreaCode: null,
    selectedCarrier: null,
    verificationId: null,
    elapsedSeconds: 0,
    scanInterval: null,
    userTier: 'freemium',
    tierRank: { freemium: 0, payg: 1, pro: 2, custom: 3 }
};

// Service stock availability map — loaded once on page init
let _stockMap = {};
async function _loadStockMap() {
    try {
        const res = await fetch('/api/services/stock');
        if (res.ok) {
            const data = await res.json();
            _stockMap = data.services || {};
        }
    } catch (e) { /* non-critical */ }
}
function _getStockInfo(serviceSlug) {
    if (!_stockMap || !Object.keys(_stockMap).length) return null;
    const key = (serviceSlug || '').toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '');
    return _stockMap[key] || _stockMap[(serviceSlug || '').toLowerCase()] || null;
}

function _getStockDot(serviceSlug) {
    const info = _getStockInfo(serviceSlug);
    if (!info) return '';
    const available = info.available;
    const color = available ? '#10b981' : '#ef4444';
    const label = available ? 'In stock' : 'Out of stock';
    return `<span style="display:inline-flex;align-items:center;gap:4px;margin-left:8px;vertical-align:middle;flex-shrink:0;">`
        + `<span style="width:8px;height:8px;border-radius:50%;background:${color};flex-shrink:0;"></span>`
        + `<span style="font-size:11px;color:${color};font-weight:500;">${label}</span>`
        + `</span>`;
}

function chooseMethod(method) {
    if (method === 'voice') {
        window.location.href = '/voice-verify';
        return;
    }
    // SMS — show progress + step 1
    document.getElementById('step-0-card').style.display = 'none';
    document.getElementById('progress-indicator').style.display = 'block';
    document.getElementById('step-1-card').style.display = 'block';
}

 Call this whenever tier changes or service is selected.
 * Controls: upsell, subscribed-tip, advanced-options, area-code lock, carrier lock.
 */
function applyTierGating() {
    const normalizedTier = (VerificationFlow.userTier || 'freemium').toLowerCase();
    const rank = VerificationFlow.tierRank[normalizedTier] || 0;
    const hasService = !!VerificationFlow.selectedService;

    console.log(`[TierGating] Tier: ${normalizedTier}, Rank: ${rank}, HasService: ${hasService}`);

    // Advanced options section (only visible for PAYG+ AND service selected)
    const advSection = document.getElementById('advanced-options-section');
    if (advSection) advSection.style.display = (rank >= 1 && hasService) ? 'block' : 'none';

    // Upsell vs subscribed tip (only visible when service selected)
    const upsell = document.getElementById('freemium-upsell');
    const subTip = document.getElementById('subscribed-tip');
    if (hasService) {
        const shouldShowUpsell = rank < 1;
        const shouldShowTip = rank >= 1;
        if (upsell) {
            upsell.style.display = shouldShowUpsell ? 'block' : 'none';
            console.log(`[TierGating] Upsell: ${shouldShowUpsell ? 'SHOW' : 'HIDE'}`);
        }
        if (subTip) {
            subTip.style.display = shouldShowTip ? 'block' : 'none';
            console.log(`[TierGating] SubTip: ${shouldShowTip ? 'SHOW' : 'HIDE'}`);
        }
    } else {
        if (upsell) upsell.style.display = 'none';
        if (subTip) subTip.style.display = 'none';
    }

    // Area code lock
    const acInput = document.getElementById('area-code-search-input');
    const acLock = document.getElementById('area-code-lock-msg');
    if (acInput) acInput.disabled = rank < 1;
    if (acLock) acLock.style.display = rank < 1 ? 'block' : 'none';

    // Carrier lock
    const carrierSel = document.getElementById('carrier-select-inline');
    const carrierLock = document.getElementById('carrier-lock-msg');
    if (carrierSel) carrierSel.disabled = rank < 1;
    if (carrierLock) carrierLock.style.display = rank < 1 ? 'block' : 'none';
}

// --- Immersive Modal System (Task 3) ---
let _modalType = null;
let _modalItems = {};
let _pinnedServices = JSON.parse(localStorage.getItem('nsk_pinned_services') || '[]');
let _recentServices = JSON.parse(localStorage.getItem('nsk_recent_services') || '[]');

function openImmersiveModal(type) {
    // Check if services are available
    if (type === 'service' && (!_modalItems['service'] || _modalItems['service'].length === 0)) {
        window.toast && window.toast.error('Services unavailable. Please refresh the page.');
        return;  // Don't open modal
    }

    _modalType = type;
    const container = document.getElementById('immersive-modal-container');
    const titles = { service: 'Select Service', 'area-code': 'Select Area Code', carrier: 'Select Carrier' };
    const subs = { service: 'Select a platform to receive SMS', 'area-code': 'Filter by specific US area code', carrier: 'Choose a specific mobile network' };

    container.innerHTML = `
        <div class="immersive-modal-backdrop" id="modal-backdrop">
            <div class="immersive-modal">
                <div class="modal-header">
                    <div class="modal-header-title">
                        <h2>${titles[type]}</h2>
                        <p>${subs[type]}${type === 'service' ? ` — ${(_modalItems['service']||[]).length} available` : ''}</p>
                    </div>
                    <button class="modal-close-btn" onclick="closeImmersiveModal()">✕</button>
                </div>

                <div class="modal-search-wrapper">
                    <div class="modal-search-field">
                        <i class="ph ph-magnifying-glass"></i>
                        <input type="text" id="modal-search-input" class="modal-search-input"
                               placeholder="Search ${type}..." oninput="filterImmersiveModal(this.value)" autofocus>
                    </div>
                    <button class="modal-settings-btn" onclick="toggleModalFilters()" title="Filter by area code">
                        <i class="ph ph-sliders-horizontal"></i>
                    </button>
                </div>

                <div id="modal-filters-section" class="modal-filter-card" style="display:none;">
                    <div class="filter-row">
                        <div class="filter-label-group">
                            <span class="filter-label">Area Code Filter</span>
                        </div>
                        <label class="switch">
                            <input type="checkbox" id="toggle-ac" ${VerificationFlow.selectedAreaCode ? 'checked' : ''} onchange="handleModalFilterToggle('ac', this.checked)">
                            <span class="slider"></span>
                        </label>
                        <select id="modal-ac-select" class="filter-dropdown" onchange="onFilterDropdownChange('ac', this.value, this.options[this.selectedIndex].text)" style="display:none;">
                            <option value="">Select</option>
                        </select>
                    </div>
                </div>

                <div id="modal-list-content" class="modal-content-list">
                    <!-- List items rendered here -->
                </div>
            </div>
        </div>
    `;

    document.getElementById('modal-backdrop').addEventListener('click', (e) => {
        if (e.target.id === 'modal-backdrop') closeImmersiveModal();
    });

    renderImmersiveList(type);
    if (type === 'area-code' && (!_modalItems['area-code'] || _modalItems['area-code'].length === 0)) {
        loadAreaCodes().then(() => renderImmersiveList('area-code'));
    }
    setTimeout(() => document.getElementById('modal-search-input').focus(), 100);
}

function closeImmersiveModal() {
    document.getElementById('immersive-modal-container').innerHTML = '';
}

function renderImmersiveList(type, query = '') {
    const listContainer = document.getElementById('modal-list-content');
    const items = _modalItems[type] || [];
    const normalizedQuery = query.toLowerCase();

    const filtered = items.filter(item =>
        item.label.toLowerCase().includes(normalizedQuery) ||
        (item.value || '').toLowerCase().includes(normalizedQuery)
    );

    // Hide/show filter button based on availability
    const filterBtn = document.querySelector('.modal-settings-btn');
    if (filterBtn) {
        filterBtn.style.display = filtered.length === 0 ? 'none' : 'block';
    }

    if (filtered.length === 0) {
        if (type === 'service' && items.length === 0) {
            // Show error with retry for services only if API actually failed (empty items)
            listContainer.innerHTML = `
                <div style="padding:40px; text-align:center;">
                    <div style="color:#EF4444; font-size:16px; margin-bottom:16px;">
                        ⚠️ Unable to load services from provider
                    </div>
                    <div style="color:#6B7280; font-size:14px; margin-bottom:24px;">
                        Please check your connection and try again
                    </div>
                    <button onclick="retryLoadServices(); closeImmersiveModal();"
                            style="padding:10px 24px; background:#FE3C72; color:white; border:none; border-radius:8px; cursor:pointer; font-size:14px; font-weight:600;">
                        Retry
                    </button>
                </div>
            `;
        } else {
            // Standard "No results" for search mismatches or other empty types
            listContainer.innerHTML = `
                <div style="padding:40px; text-align:center; color:#6B7280;">
                    <div style="font-size:24px; margin-bottom:12px;"></div>
                    <div style="font-size:15px; font-weight:500;">No results found for "${query}"</div>
                    <div style="font-size:13px; margin-top:4px;">Try a different search or check your spelling</div>
                </div>
            `;
        }
        return;
    }

    let html = '';

    if (type === 'service') {
        const pinned = filtered.filter(i => _pinnedServices.includes(i.value));
        const recent = filtered.filter(i => !_pinnedServices.includes(i.value) && _recentServices.includes(i.value));

        // Category grouping (only when not searching)
        const _CAT_LABELS = {
            social: '💬 Social & Messaging',
            dating: '❤️ Dating',
            finance: '💳 Finance & Crypto',
            tech: '💻 Tech & Productivity',
            delivery: '🚗 Delivery & Travel',
            streaming: '🎮 Gaming & Streaming',
            shopping: '🛍️ Shopping',
            other: '📱 Other Services',
        };

        const remaining = filtered.filter(i =>
            !_pinnedServices.includes(i.value) && !_recentServices.includes(i.value)
        );

        if (pinned.length > 0) {
            html += `<div class="modal-list-section">
                <div class="list-section-title">PINNED</div>
                ${pinned.map(i => renderImmersiveItem(i, true)).join('')}
            </div>`;
        }
        if (recent.length > 0 && !normalizedQuery) {
            html += `<div class="modal-list-section">
                <div class="list-section-title">RECENTLY USED</div>
                ${recent.map(i => renderImmersiveItem(i, false)).join('')}
            </div>`;
        }

        if (normalizedQuery) {
            // Flat list when searching
            html += remaining.map(i => renderImmersiveItem(i, false)).join('');
        } else {
            // Group by category
            const byCategory = {};
            for (const item of remaining) {
                const cat = item.category || 'other';
                if (!byCategory[cat]) byCategory[cat] = [];
                byCategory[cat].push(item);
            }
            const catOrder = ['social', 'dating', 'finance', 'tech', 'delivery', 'streaming', 'shopping', 'other'];
            for (const cat of catOrder) {
                if (!byCategory[cat] || byCategory[cat].length === 0) continue;
                // Sort by availability only — in stock first, out of stock last
                byCategory[cat].sort((a, b) => {
                    const aAvail = (a.available !== false) ? 1 : 0;
                    const bAvail = (b.available !== false) ? 1 : 0;
                    return bAvail - aAvail;
                });
                html += `<div class="modal-list-section">
                    <div class="list-section-title">${_CAT_LABELS[cat] || cat.toUpperCase()}</div>
                    ${byCategory[cat].map(i => renderImmersiveItem(i, false)).join('')}
                </div>`;
            }
        }
    } else {
        html = filtered.map(i => renderImmersiveItem(i, false)).join('');
    }

    listContainer.innerHTML = html;
}

function renderImmersiveItem(item, isPinned) {
    if (_modalType === 'service') {
        const iconUrl = _getServiceIcon(item.value);
        const stockInfo = _getStockInfo(item.value) || {};
        const available = stockInfo.available !== false;
        const stockColor = available ? '#10b981' : '#ef4444';
        const qty = stockInfo.quantity ?? item.quantity ?? null;
        const qtyLabel = qty === null ? '' : qty >= 999 ? '999+' : String(qty);
        const stockLabel = available
            ? (qtyLabel ? `${qtyLabel} available` : 'In stock')
            : 'Out of stock';
        const priceStr = item.price > 0 ? `$${parseFloat(item.price).toFixed(2)}` : '';
        const rateStr = item.success_rate != null ? `${item.success_rate}% success` : '';
        const demandBadge = item.demand === 'high'
            ? `<span style="font-size:10px;background:#fef3c7;color:#92400e;padding:1px 5px;border-radius:3px;font-weight:600;margin-left:4px;">High demand</span>`
            : '';
        const capBadge = item.capability === 'voice'
            ? `<span style="font-size:10px;background:#ede9fe;color:#6d28d9;padding:1px 5px;border-radius:3px;font-weight:600;margin-left:4px;">Voice</span>`
            : item.capability === 'sms_and_voice'
            ? `<span style="font-size:10px;background:#e0f2fe;color:#0369a1;padding:1px 5px;border-radius:3px;font-weight:600;margin-left:4px;">SMS+Voice</span>`
            : '';

        // Out-of-stock items are non-selectable — greyed out, pointer-events disabled
        const isUnavailable = !available;
        const itemStyle = isUnavailable ? 'opacity:0.45;cursor:not-allowed;pointer-events:none;' : '';
        const clickAttr = isUnavailable ? '' : `onclick="selectImmersiveItem('${item.value.replace(/'/g,"\\'")  }', '${item.label.replace(/'/g,"\\'") }', ${item.price || 0})"`;

        return `
            <div class="list-item" ${clickAttr} style="${itemStyle}">
                <div class="list-item-icon">
                    <img src="${iconUrl}" onerror="this.style.display='none'">
                </div>
                <div class="list-item-info" style="flex:1;min-width:0;">
                    <div class="list-item-name" style="display:flex;align-items:center;flex-wrap:wrap;gap:2px;">
                        ${item.label}
                        <span style="width:7px;height:7px;border-radius:50%;background:${stockColor};flex-shrink:0;margin-left:6px;"></span>
                        <span style="font-size:11px;color:${stockColor};font-weight:500;">${stockLabel}</span>
                        ${demandBadge}${capBadge}
                    </div>
                    <div style="display:flex;align-items:center;gap:8px;margin-top:2px;">
                        ${priceStr ? `<span style="font-size:12px;font-weight:600;color:#374151;">${priceStr}</span>` : ''}
                        ${rateStr ? `<span style="font-size:11px;color:#6b7280;">${rateStr}</span>` : ''}
                    </div>
                </div>
                <div class="list-item-pin ${isPinned ? 'active' : ''}" onclick="event.stopPropagation(); togglePin('${item.value.replace(/'/g,"\\'") }')" title="${isPinned ? 'Unpin' : 'Pin to top'}">
                    <i class="ph${isPinned ? '-fill' : ''} ph-push-pin"></i>
                </div>
            </div>
        `;
    } else {
        // Area code or carrier — simple row, no icon/pin
        const sub = item.sub ? `<div style="font-size:11px;color:#9ca3af;">${item.sub}</div>` : '';
        const right = item.price ? `<div style="font-size:13px;font-weight:600;color:#374151;">+${formatMoney(item.price)}</div>` : '';
        return `
            <div class="list-item" onclick="selectImmersiveItem('${item.value.replace(/'/g,"\\'") }', '${item.label.replace(/'/g,"\\'") }', ${item.price || 0})" style="padding:12px 16px;">
                <div class="list-item-info" style="flex:1;">
                    <div class="list-item-name">${item.label}</div>
                    ${sub}
                </div>
                ${right}
            </div>
        `;
    }
}

function filterImmersiveModal(val) {
    renderImmersiveList(_modalType, val);
}

function toggleModalFilters() {
    const section = document.getElementById('modal-filters-section');
    section.style.display = section.style.display === 'none' ? 'flex' : 'none';
}

function handleModalFilterToggle(type, checked) {
    if (type === 'ac') {
        const dd = document.getElementById('modal-ac-select');
        if (checked) {
            if (dd) {
                dd.style.display = 'inline-block';
                populateFilterDropdown('ac');
            }
        } else {
            if (dd) dd.style.display = 'none';
            VerificationFlow.selectedAreaCode = null;
            const acInput = document.getElementById('area-code-search-input');
            if (acInput) acInput.value = '';
            updateSelectionChips();
        }
    }

    updatePricing();
}

function populateFilterDropdown(type) {
    if (type === 'ac') {
        const dd = document.getElementById('modal-ac-select');
        if (!dd) return;
        const items = _modalItems['area-code'] || [];
        if (items.length === 0) {
            loadAreaCodes().then(() => populateFilterDropdown('ac'));
            return;
        }
        dd.innerHTML = '<option value="">Select ▾</option>' + items.map(i =>
            `<option value="${i.value}" ${i.value === VerificationFlow.selectedAreaCode ? 'selected' : ''}>${i.value}${i.sub ? ' — ' + i.sub : ''}</option>`
        ).join('');
    }
}

function onFilterDropdownChange(type, value, label) {
    if (type === 'ac') {
        VerificationFlow.selectedAreaCode = value || null;
        const acInput = document.getElementById('area-code-search-input');
        if (acInput) acInput.value = value || '';
    }
    updatePricing();
    updateSelectionChips();
}

function togglePin(serviceId) {
    if (_pinnedServices.includes(serviceId)) {
        _pinnedServices = _pinnedServices.filter(id => id !== serviceId);
    } else {
        _pinnedServices.push(serviceId);
    }
    localStorage.setItem('nsk_pinned_services', JSON.stringify(_pinnedServices));
    renderImmersiveList('service', document.getElementById('modal-search-input').value);
}

function updateSelectionChips() {
    const container = document.getElementById('selection-chips');
    if (!container) return;
    let html = '';
    if (VerificationFlow.selectedAreaCode) {
        const acItem = (_modalItems['area-code'] || []).find(i => i.value === VerificationFlow.selectedAreaCode);
        const label = acItem ? `${acItem.value}${acItem.sub ? ' — ' + acItem.sub : ''}` : VerificationFlow.selectedAreaCode;
        html += `<span style="display:inline-flex;align-items:center;gap:6px;padding:6px 12px;background:#eff6ff;border:1px solid #bfdbfe;border-radius:20px;font-size:13px;color:#1d4ed8;">
            📍 ${label}
            <button onclick="clearAreaCode();updateSelectionChips();" style="background:none;border:none;color:#1d4ed8;cursor:pointer;font-size:14px;padding:0;">✕</button>
        </span>`;
    }

    container.innerHTML = html;
    container.style.display = html ? 'flex' : 'none';
}

function selectImmersiveItem(value, label, price) {
    if (_modalType === 'service') {
        VerificationFlow.selectedService = value;
        VerificationFlow.selectedServicePrice = price;

        // Track recently used (max 5, deduplicated)
        _recentServices = [value, ..._recentServices.filter(id => id !== value)].slice(0, 5);
        localStorage.setItem('nsk_recent_services', JSON.stringify(_recentServices));
        localStorage.setItem('nsk_last_service', value);

        const display = document.getElementById('service-selected-display');
        const input = document.getElementById('service-search-input');

        input.value = label;
        display.style.display = 'flex';
        document.getElementById('service-display').textContent = label;
        const costEl = document.getElementById('selected-service-cost');
        if (costEl) costEl.textContent = price > 0 ? formatMoney(price) : '';

        applyTierGating();

    } else if (_modalType === 'area-code') {
        VerificationFlow.selectedAreaCode = value || null;
        const acInput = document.getElementById('area-code-search-input');
        const clearBtn = document.getElementById('clear-ac-btn');
        if (acInput) acInput.value = label || '';
        if (clearBtn) clearBtn.style.display = value ? 'block' : 'none';
        updateSelectionChips();

        // Persist to server
        if (value) {
            const token = localStorage.getItem('access_token');
            fetch('/api/user/verification/area-codes', {
                method: 'PUT',
                headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
                body: JSON.stringify({ area_codes: [value] })
            }).catch(() => {});
        }
    } else if (_modalType === 'carrier') {
        VerificationFlow.selectedCarrier = value || null;
        const cSel = document.getElementById('carrier-select-inline');
        if (cSel) cSel.value = value || '';
        updateSelectionChips();
    }

    updatePricing();
    updateContinueBtn();
    closeImmersiveModal();
}

// Service selection management
function clearServiceSelection() {
    VerificationFlow.selectedService = null;
    VerificationFlow.selectedServicePrice = null;
    document.getElementById('service-selected-display').style.display = 'none';
    document.getElementById('service-search-input').value = '';
    document.getElementById('continue-btn').disabled = true;

    applyTierGating();
}

function toggleAdvanced() {
    const body = document.getElementById('advanced-options-body');
    const icon = document.getElementById('advanced-toggle-icon');
    if (!body) return;
    const open = body.style.display === 'block';
    body.style.display = open ? 'none' : 'block';
    if (icon) icon.textContent = open ? '▶' : '▼';
}

// Area code management
function clearAreaCode() {
    const acInput = document.getElementById('area-code-search-input');
    const clearBtn = document.getElementById('clear-ac-btn');
    if (acInput) acInput.value = '';
    if (clearBtn) clearBtn.style.display = 'none';
    VerificationFlow.selectedAreaCode = null;

    // Phase 4 Check logic resets
    if(typeof debouncedCheckAreaCode === 'function') debouncedCheckAreaCode('');

    updatePricing();
}

function updateContinueBtn() {
    const btn = document.getElementById('continue-btn');

    // If we have a pending API check or error, disable
    const msg = document.getElementById('ac-message');
    let isErrorState = false;
    if (msg && msg.style.display === 'block' && ['#dc2626', '#92400e'].includes(msg.style.color)) {
        isErrorState = true;
    }

    if (btn) btn.disabled = !VerificationFlow.selectedService || isErrorState;

    // Refresh balance when entering step 2 UI
    if (VerificationFlow.currentStep === 2) {
        loadStatusInfo();
    }
}

function updateProgress(step) {
    VerificationFlow.currentStep = step;
    for (let i = 1; i <= 3; i++) {
        const stepEl = document.getElementById(`step-${i}`);
        const cardEl = document.getElementById(`step-${i}-card`);
        if (i < step) { stepEl.classList.add('completed'); stepEl.classList.remove('active'); }
        else if (i === step) { stepEl.classList.add('active'); stepEl.classList.remove('completed'); }
        else { stepEl.classList.remove('active', 'completed'); }
        cardEl.style.display = i === step ? 'block' : 'none';
    }
    document.getElementById('progress-fill').style.width = (((step - 1) / 2) * 100) + '%';
}

function confirmService() {
    if (!VerificationFlow.selectedService) return;
    const item = (_modalItems['service'] || []).find(i => i.value === VerificationFlow.selectedService);
    document.getElementById('pricing-service').textContent = item?.label || VerificationFlow.selectedService;
    document.getElementById('pricing-time').textContent = item?.estimated_seconds ? `~${item.estimated_seconds}s` : '~30s';

    // Show area code if selected
    if (VerificationFlow.selectedAreaCode) {
        const acItem = (_modalItems['area-code'] || []).find(i => i.value === VerificationFlow.selectedAreaCode);
        document.getElementById('pricing-area-code').textContent = acItem ? `${acItem.value}${acItem.sub ? ' — ' + acItem.sub : ''}` : VerificationFlow.selectedAreaCode;
        document.getElementById('pricing-area-code-row').style.display = '';
    } else {
        document.getElementById('pricing-area-code-row').style.display = 'none';
    }



    updatePricing();
    loadBalance(); // Refresh balance before confirming
    updateProgress(2);
    setTimeout(() => document.getElementById('step-2-card').scrollIntoView({ behavior: 'smooth' }), 300);
}

const _LS_SERVICES_KEY = 'nsk_services_cache';
const _LS_SERVICES_PRICED_KEY = 'nsk_services_priced_cache';
const _LS_AREA_CODES_KEY = 'nsk_area_codes_cache';
const _LS_TTL = 30 * 60 * 1000;       // 30 min for names
const _LS_PRICED_TTL = 24 * 60 * 60 * 1000; // 24h for priced cache

function _lsGet(key, ttl) {
    try {
        const raw = localStorage.getItem(key);
        if (!raw) return null;
        const { ts, data } = JSON.parse(raw);
        if (Date.now() - ts > (ttl || _LS_TTL)) { localStorage.removeItem(key); return null; }
        return data;
    } catch { return null; }
}
function _lsSet(key, data) {
    try { localStorage.setItem(key, JSON.stringify({ ts: Date.now(), data })); } catch {}
}

function _buildServiceItems(services) {
    const popularIds = ['telegram', 'whatsapp', 'google', 'facebook', 'instagram', 'twitter', 'discord', 'tinder'];
    const seen = new Set();
    const unique = services.filter(s => {
        const key = (s.id || '').toLowerCase();
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
    });
    return [
        ...unique.map(s => {
            const slug = (s.id || '').toLowerCase();
            const stockInfo = _getStockInfo(slug) || {};
            return {
                value: s.id,
                label: s.name || s.id,
                price: s.price,
                popular: popularIds.includes(slug),
                available: stockInfo.available !== false,
                quantity: stockInfo.quantity ?? null,
                category: stockInfo.category || 'other',
                success_rate: stockInfo.success_rate ?? null,
                demand: stockInfo.demand || 'normal',
                capability: s.capability || 'sms',
            };
        }),
        { value: '__other__', label: 'Other (type name)', price: 0, popular: false, category: 'other' }
    ];
}

// NO FALLBACK SERVICES - All services MUST come from TextVerified API
// If API is down, the platform should show an error, not fake data

async function loadServices() {
    const input = document.getElementById('service-search-input');
    const spinner = document.getElementById('service-loading-spinner');
    if (input) {
        input.classList.add('skeleton-loader');
        input.placeholder = 'Loading services from provider...';
    }
    if (spinner) spinner.style.display = 'block';

    try {
        await Promise.all([window.ServiceStore.init(), _loadStockMap()]);

        const services = window.ServiceStore.getAll();
        if (!services || services.length === 0) {
            throw new Error('No services available from API');
        }

        _modalItems['service'] = _buildServiceItems(services);
        console.log(`✅ Loaded ${services.length} services from TextVerified API`);

        if (input) {
            input.classList.remove('skeleton-loader');
            input.placeholder = 'Search services e.g. Telegram, WhatsApp...';
        }
        if (spinner) spinner.style.display = 'none';

        // Hide retry button on success
        const retryBtn = document.getElementById('service-retry-btn');
        if (retryBtn) retryBtn.style.display = 'none';

        // Subscribe to updates
        window.ServiceStore.subscribe((updatedServices) => {
            if (updatedServices && updatedServices.length > 0) {
                _modalItems['service'] = _buildServiceItems(updatedServices);
                console.log(`🔄 Updated to ${updatedServices.length} services`);
            }
        });
    } catch (error) {
        if (input) {
            input.classList.remove('skeleton-loader');
            input.placeholder = 'Services unavailable - please refresh page';
        }
        if (spinner) spinner.style.display = 'none';
        console.error('❌ Failed to load services from TextVerified API:', error);

        // Show error to user - DO NOT use fallback
        window.toast && window.toast.error(
            'Unable to load services from provider. Please refresh the page or contact support if the issue persists.'
        );

        // Disable service selection
        if (input) {
            input.disabled = true;
            input.onclick = null;  // Remove click handler
            input.style.cursor = 'not-allowed';  // Visual feedback
        }

        // Show retry button
        const retryBtn = document.getElementById('service-retry-btn');
        if (retryBtn) retryBtn.style.display = 'block';

        _modalItems['service'] = [];
    }
}

async function retryLoadServices() {
    window.toast && window.toast.info('Retrying...');

    // Hide retry button while retrying
    const retryBtn = document.getElementById('service-retry-btn');
    if (retryBtn) retryBtn.style.display = 'none';

    // Re-enable input
    const input = document.getElementById('service-search-input');
    if (input) {
        input.disabled = false;
        input.placeholder = 'Search services e.g. Telegram, WhatsApp...';
        input.onclick = () => openImmersiveModal('service');
        input.style.cursor = 'pointer';
    }

    // Retry loading
    await loadServices();

    // Refresh modal if open
    const modalContainer = document.getElementById('immersive-modal-container');
    if (modalContainer && modalContainer.innerHTML) {
        renderImmersiveList('service');
    }
}

async function loadAreaCodes() {
    applyTierGating();

    const cached = _lsGet(_LS_AREA_CODES_KEY);
    if (cached && cached.length > 1) { _modalItems['area-code'] = cached; return; }

    try {
        const token = localStorage.getItem('access_token');
        const ctrl = new AbortController();
        const tid = setTimeout(() => ctrl.abort(), 10000);
        const res = await fetch('/api/area-codes?country=US', { headers: { 'Authorization': `Bearer ${token}` }, signal: ctrl.signal });
        clearTimeout(tid);
        const data = res.ok ? await res.json() : {};
        const codes = data.area_codes || [];
        _modalItems['area-code'] = codes.map(c => ({ value: c.area_code, label: c.area_code, sub: `${c.city || ''}, ${c.state || ''}`.trim().replace(/^,\s*/, '') }));
        if (codes.length) _lsSet(_LS_AREA_CODES_KEY, _modalItems['area-code']);
        console.log(`✅ Loaded ${codes.length} area codes from API`);
    } catch (e) {
        console.error('❌ Failed to load area codes:', e);
        _modalItems['area-code'] = [];
    }
}

async function loadCarriers() {
    applyTierGating();

    // Issue #7: carrier caching (24h localStorage)
    const _LS_CARRIERS_KEY = 'nsk_carriers_cache';
    const cached = _lsGet(_LS_CARRIERS_KEY, 24 * 60 * 60 * 1000);
    if (cached && cached.length > 0) {
        // Parse cached HTML to rebuild _modalItems
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = cached;
        const options = tempDiv.querySelectorAll('option');
        _modalItems['carrier'] = Array.from(options)
            .filter(opt => opt.value)
            .map(opt => ({ value: opt.value, label: opt.textContent.trim(), price: 0.50 }));
        console.log(`✅ Loaded ${_modalItems['carrier'].length} carriers from cache`);
        return;
    }

    try {
        const token = localStorage.getItem('access_token');
        const ctrl = new AbortController();
        const tid = setTimeout(() => ctrl.abort(), 10000);
        const res = await fetch('/api/verification/carriers/US', { headers: { 'Authorization': `Bearer ${token}` }, signal: ctrl.signal });
        clearTimeout(tid);
        const data = res.ok ? await res.json() : {};
        const carriers = data.carriers || [];
        _modalItems['carrier'] = carriers.map(c => ({ value: c.id || c.name, label: c.name, price: c.price || 0.50 }));

        const html = '<option value="">Any Carrier</option>' +
            _modalItems['carrier'].map(c => `<option value="${c.value}">${c.label}</option>`).join('');

        _lsSet(_LS_CARRIERS_KEY, html);
        console.log(`✅ Loaded ${carriers.length} carriers from API`);
    } catch (e) {
        console.error('❌ Failed to load carriers:', e);
        _modalItems['carrier'] = [];
    }
}

// Create verification — SSE streaming purchase
async function createVerification() {
    if (!VerificationFlow.selectedService) {
        window.toast && window.toast.error('Please select a service');
        return;
    }

    const btn = document.getElementById('get-number-btn');
    const serviceId = VerificationFlow.selectedService;
    const areaCode = VerificationFlow.selectedAreaCode || null;
    const carrier = VerificationFlow.selectedCarrier || null;

    // Show purchase loading card, hide step-2
    document.getElementById('step-2-card').style.display = 'none';
    const loadingCard = document.getElementById('purchase-loading-card');
    if (loadingCard) loadingCard.style.display = 'block';
    const iconEl = document.getElementById('loading-service-icon');
    if (iconEl) iconEl.src = _getServiceIcon(serviceId);

    function updateLoadingMessage(msg) {
        const el = document.getElementById('purchase-loading-message');
        if (el) el.textContent = msg;
    }
    function hideCancelButton() {
        const btn = document.getElementById('purchase-cancel-btn');
        if (btn) btn.style.display = 'none';
    }
    function hidePurchaseLoadingState() {
        if (loadingCard) loadingCard.style.display = 'none';
    }

    try {
        const response = await fetch('/api/verification/request/stream', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                service: serviceId,
                country: 'US',
                capability: 'sms',
                area_codes: areaCode ? [areaCode] : [],
                carriers: carrier ? [carrier] : [],
                max_price: VerificationFlow.selectedServicePrice
                    ? parseFloat((VerificationFlow.selectedServicePrice * 1.10).toFixed(2))
                    : null
            })
        });

        if (!response.ok || !response.body) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || 'Failed to start verification stream');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // keep incomplete line
            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                let event;
                try { event = JSON.parse(line.slice(6)); } catch { continue; }

                switch (event.step) {
                    case 'pricing_check':
                        updateLoadingMessage('Confirming availability...');
                        break;
                    case 'balance_check':
                        updateLoadingMessage('Checking your balance...');
                        break;
                    case 'purchasing':
                        updateLoadingMessage('Securing your number...');
                        hideCancelButton();
                        // Show "still working" message if TV takes longer than 10s
                        VerificationFlow._purchasingTimer = setTimeout(() => {
                            updateLoadingMessage('Still working — this can take up to 30 seconds...');
                        }, 10000);
                        break;
                    case 'validating':
                        clearTimeout(VerificationFlow._purchasingTimer);
                        updateLoadingMessage('Validating number quality...');
                        break;
                    case 'recording':
                        updateLoadingMessage('Almost done...');
                        break;
                    case 'complete':
                        clearTimeout(VerificationFlow._purchasingTimer);
                        hidePurchaseLoadingState();
                        VerificationFlow.verificationId = event.verification_id;
                        VerificationFlow.createdAt = event.created_at || new Date().toISOString();
                        if (event.ends_at) {
                            VerificationFlow.totalDurationMs =
                                new Date(event.ends_at).getTime() - new Date(VerificationFlow.createdAt).getTime();
                        }
                        localStorage.setItem('active_verification_id', event.verification_id);
                        document.getElementById('phone-number').textContent = formatPhone(event.phone_number);
                        document.getElementById('display-verification-id').textContent = event.verification_id || '-';
                        const _svcLabel = (_modalItems['service'] || []).find(i => i.value === serviceId)?.label || serviceId;
                        document.getElementById('scanning-service-name').textContent = _svcLabel;
                        updateProgress(3);
                        startPolling();
                        if (event.fallback_applied) {
                            showFallbackWarning(event.requested_area_code, event.assigned_area_code, true);
                        } else {
                            window.toast && window.toast.success('Number received — waiting for SMS...');
                        }
                        return;
                    case 'failed':
                        clearTimeout(VerificationFlow._purchasingTimer);
                        hidePurchaseLoadingState();
                        document.getElementById('step-2-card').style.display = 'block';
                        if (btn) { btn.disabled = false; btn.innerHTML = 'Get Number →'; }
                        const msg = event.message || 'Failed to create verification';
                        if (event.reason === 'no_inventory') {
                            const slug = (serviceId || '').toLowerCase();
                            if (_stockMap[slug]) _stockMap[slug].available = false;
                            window.toast && window.toast.error(`${serviceId} is out of stock. Please try a different service.`);
                        } else if (event.reason === 'insufficient_balance') {
                            window.toast && window.toast.error('Insufficient balance. Please add credits to your wallet.');
                        } else {
                            window.toast && window.toast.error(msg);
                        }
                        return;
                }
            }
        }
    } catch (error) {
        console.error('SSE stream error:', error);
        const loadingCard = document.getElementById('purchase-loading-card');
        if (loadingCard) loadingCard.style.display = 'none';
        document.getElementById('step-2-card').style.display = 'block';
        if (btn) { btn.disabled = false; btn.innerHTML = 'Get Number →'; }
        window.toast && window.toast.error(error.message || 'Failed to create verification');
    }
}

function cancelPurchase() {
    // Only safe before 'purchasing' step fires (cancel button is hidden after that)
    const loadingCard = document.getElementById('purchase-loading-card');
    if (loadingCard) loadingCard.style.display = 'none';
    document.getElementById('step-2-card').style.display = 'block';
    window.toast && window.toast.info('Purchase cancelled.');
}

// Global error handler for unhandled promise rejections (Task 8)
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    const btn = document.getElementById('get-number-btn');
    if (btn) {
        btn.disabled = false;
        btn.textContent = 'Get Number →';
    }
    window.toast && window.toast.error('An unexpected error occurred. Please try again.');
});

// WebSocket instant SMS delivery handler (TV webhook → WebSocket push)
// Listens for sms_received events pushed by tv_webhook.py via websocket_manager
function handleWebSocketSmsReceived(message) {
    if (
        message.type === 'sms_received' &&
        message.verification_id === VerificationFlow.verificationId
    ) {
        stopPolling();
        VerificationFlow.smsReceived = true;

        document.getElementById('sms-code').textContent = message.sms_code || '------';
        document.getElementById('code-received').style.display = 'block';
        const scanContainer = document.querySelector('.scanning-container');
        if (scanContainer) scanContainer.style.display = 'none';

        document.getElementById('receipt-carrier').textContent = 'Auto';
        document.getElementById('receipt-area-code').textContent = 'Any';

        window.toast && window.toast.success('SMS code received!');
        playArrivalSound();
        localStorage.removeItem('active_verification_id');
        if (localStorage.getItem('nsk_auto_copy') === 'true') {
            navigator.clipboard.writeText(message.sms_code || '').catch(() => {});
        }
    }
}

// Wire into the existing WebSocket notification system
// sms-websocket.js dispatches a custom event 'ws:message' with the parsed payload
document.addEventListener('ws:message', (e) => {
    if (e.detail && e.detail.type === 'sms_received') {
        handleWebSocketSmsReceived(e.detail);
    }
});

function showFallbackWarning(requested, assigned, sameState) {
    const existing = document.getElementById('fallback-warning');
    if (existing) existing.remove();
    const el = document.createElement('div');
    el.id = 'fallback-warning';
    const container = document.querySelector('.scanning-container') || document.getElementById('step-3-card');
    const msg = sameState
        ? `<strong>${requested}</strong> unavailable — assigned nearby <strong>${assigned}</strong> (same state).`
        : `<strong>${requested}</strong> unavailable — assigned <strong>${assigned}</strong> (different state). <a href="/settings?tab=verification" style="color:#b45309;text-decoration:underline;">Update preferences →</a>`;
    el.style.cssText = sameState
        ? 'background:#f0fdf4;border:1px solid #86efac;border-radius:8px;padding:12px 16px;margin-bottom:16px;font-size:13px;color:#166534;'
        : 'background:#fffbeb;border:1px solid #fcd34d;border-radius:8px;padding:12px 16px;margin-bottom:16px;font-size:13px;color:#92400e;';
    el.innerHTML = msg;
    container.parentNode.insertBefore(el, container);
    if (window.toast) {
        sameState
            ? window.toast.info(`Area code ${requested} unavailable — assigned nearby ${assigned}`)
            : window.toast.warning(`Area code ${requested} unavailable — assigned ${assigned} (different state)`);
    }
}

// Start scanning with API polling
// Start scanning with Server-Synced Polling
function startPolling() {
    VerificationFlow.elapsedSeconds = 0;
    VerificationFlow.serverOffset = 0; // Offset between client and server time

    let pollCount = 0;
    const initialDelay = 2000;

    async function poll() {
        if (!VerificationFlow.verificationId || VerificationFlow.currentStep !== 3) return;

        try {
            const res = await fetch(`/api/verification/status/${VerificationFlow.verificationId}`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
            });

            if (res.ok) {
                const data = await res.json();

                // 1. Synchronize Clocks (Phase 12: Brutal Parity)
                if (data.server_time) {
                    const serverTime = new Date(data.server_time).getTime();
                    VerificationFlow.serverOffset = serverTime - Date.now();
                }

                // 2. Handle Terminal States
                if ((data.status === 'completed' || data.status === 'success') && data.sms_code) {
                    VerificationFlow.smsReceived = true;
                    stopPolling();

                    document.getElementById('sms-code').textContent = data.sms_code;
                    document.getElementById('code-received').style.display = 'block';
                    document.querySelector('.scanning-container').style.display = 'none';

                    document.getElementById('receipt-carrier').textContent = data.assigned_carrier || data.operator || 'Auto';
                    document.getElementById('receipt-area-code').textContent = data.assigned_area_code || 'Any';

                    if (data.fallback_applied) {
                        document.getElementById('receipt-fallback-row').style.display = 'flex';
                        document.getElementById('receipt-requested-ac').textContent = data.requested_area_code || '-';
                    }

                    window.toast.success('SMS code received');
                    playArrivalSound();
                    localStorage.removeItem('active_verification_id');
                    if (localStorage.getItem('nsk_auto_copy') === 'true') {
                        navigator.clipboard.writeText(data.sms_code).catch(() => {});
                    }
                    return;
                } else if (['failed', 'error', 'timeout', 'cancelled'].includes(data.status)) {
                    stopPolling();
                    let msg = data.failure_reason ? data.failure_reason.replace(/_/g, ' ') : 'Verification closed.';
                    showError('Session Closed', msg.charAt(0).toUpperCase() + msg.slice(1));
                    return;
                }

                // 3. Update Sync Timer
                if (data.ends_at) {
                    const endsAt = new Date(data.ends_at).getTime();
                    const now = Date.now() + VerificationFlow.serverOffset;
                    const remainingMs = Math.max(0, endsAt - now);
                    // Compute real window from TV's ends_at - created_at (never hardcode)
                    if (!VerificationFlow.totalDurationMs && VerificationFlow.createdAt) {
                        VerificationFlow.totalDurationMs =
                            endsAt - new Date(VerificationFlow.createdAt).getTime();
                    }
                    const totalDurationMs = VerificationFlow.totalDurationMs || (endsAt - (endsAt - remainingMs));

                    const remainingSec = Math.round(remainingMs / 1000);
                    const elapsedSec = Math.max(0, Math.round((totalDurationMs - remainingMs) / 1000));

                    VerificationFlow.elapsedSeconds = elapsedSec;

                    // Update UI
                    const elEl = document.getElementById('elapsed-time');
                    const elapsedEl = document.getElementById('progress-elapsed');
                    const remainEl = document.getElementById('progress-remaining');
                    const progressFill = document.getElementById('progress-bar-fill') || document.querySelector('.scanning-progress-bar');

                    if (elEl) elEl.textContent = elapsedSec;
                    if (elapsedEl) elapsedEl.textContent = elapsedSec + 's elapsed';
                    if (remainEl) remainEl.textContent = remainingSec + 's left';
                    if (progressFill) progressFill.style.width = Math.min(100, (elapsedSec / 120 * 100)) + '%';

                    // Update scanning status text dynamically
                    const scanStateEl = document.getElementById('scanning-text-state');
                    if (scanStateEl) {
                        if (elapsedSec < 5) {
                            scanStateEl.textContent = 'Establishing secure connection...';
                        } else if (elapsedSec < 15) {
                            scanStateEl.textContent = 'Awaiting response from service...';
                        } else {
                            scanStateEl.textContent = 'Listening for incoming SMS...';
                        }
                    }

                    updateTimerRing(elapsedSec, 120);

                    // Auto-timeout if server says we're done
                    if (remainingMs <= 0) {
                        stopPolling();
                        window.toast.error('Verification timed out. You have not been charged.');
                        goBack();
                        return;
                    }
                }
            }
        } catch (e) { console.warn('Sync poll failed:', e); }

        // 4. Adaptive Polling Interval
        pollCount++;
        let nextDelay = 3000;
        if (pollCount < 5) nextDelay = 2000; // Fast start
        else if (pollCount > 15) nextDelay = 5000; // Back off

        VerificationFlow.scanInterval = setTimeout(poll, nextDelay);
    }

    // Kick off first poll
    poll();

    // Background UI ticker (keeps the ring smooth between polls)
    const ticker = setInterval(() => {
        if (VerificationFlow.currentStep !== 3 || VerificationFlow.smsReceived) {
            clearInterval(ticker);
            return;
        }
        // Local increment for smooth animation, will be corrected by next poll
        const progressFill = document.getElementById('progress-bar-fill') || document.querySelector('.scanning-progress-bar');
        if (progressFill && VerificationFlow.elapsedSeconds < 120) {
            const currentWidth = parseFloat(progressFill.style.width || "0");
            progressFill.style.width = Math.min(100, currentWidth + (0.5 / 120 * 100)) + '%';
        }
    }, 500);
}


function stopPolling() {
    clearTimeout(VerificationFlow.scanInterval);
}

// Copy phone number
function formatPhone(raw) {
    const d = (raw || '').replace(/\D/g, '');
    if (d.length === 11 && d[0] === '1') return `+1 (${d.slice(1,4)}) ${d.slice(4,7)}-${d.slice(7)}`;
    if (d.length === 10) return `+1 (${d.slice(0,3)}) ${d.slice(3,6)}-${d.slice(6)}`;
    return raw;
}

async function copyPhoneNumber(withCountryCode = true) {
    const raw = document.getElementById('phone-number').textContent;
    // Strip to digits only, then reformat based on preference
    const digits = raw.replace(/\D/g, '');
    let toCopy;
    if (withCountryCode) {
        // Always include +1 prefix
        toCopy = digits.length === 11 ? `+${digits}` : `+1${digits}`;
    } else {
        // Local number only — last 10 digits, formatted (XXX) XXX-XXXX
        const local = digits.slice(-10);
        toCopy = `(${local.slice(0,3)}) ${local.slice(3,6)}-${local.slice(6)}`;
    }
    try {
        await navigator.clipboard.writeText(toCopy);
        const btnId = withCountryCode ? 'copy-with-code-btn' : 'copy-without-code-btn';
        const btn = document.getElementById(btnId);
        const original = btn.textContent;
        btn.textContent = '✓ Copied';
        setTimeout(() => { btn.textContent = original; }, 2000);
        window.toast.success(`Copied: ${toCopy}`);
    } catch (err) {
        console.error('Clipboard failed', err);
    }
}

// Copy SMS code
async function copySMSCode() {
    const code = document.getElementById('sms-code').textContent.trim();
    try {
        await navigator.clipboard.writeText(code);
        const btn = document.getElementById('copy-code-btn');
        const txt = document.getElementById('copy-code-text');
        const ico = document.getElementById('copy-code-icon');
        if (btn) btn.classList.add('copied');
        if (txt) txt.textContent = 'Copied!';
        if (ico) ico.textContent = '\u2713';
        setTimeout(() => {
            if (btn) btn.classList.remove('copied');
            if (txt) txt.textContent = 'Copy Code';
            if (ico) ico.textContent = '\ud83d\udccb';
        }, 2500);
        window.toast.success('Code copied!');
    } catch (err) {
        console.error('Clipboard failed', err);
    }
}

function toggleAutoCopy(enabled) {
    localStorage.setItem('nsk_auto_copy', enabled.toString());
}

// Init auto-copy toggle state
document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.getElementById('auto-copy-toggle');
    if (toggle) toggle.checked = localStorage.getItem('nsk_auto_copy') === 'true';
});

// Update timer ring fill based on elapsed seconds
function updateTimerRing(elapsed, max) {
    const ring = document.getElementById('timer-ring-fill');
    if (!ring) return;
    const circumference = 100.53; // 2π × 16
    const ratio = Math.min(elapsed / max, 1);
    ring.style.strokeDashoffset = circumference * ratio;
    if (ratio > 0.75)      ring.className = 'timer-ring-fill danger';
    else if (ratio > 0.5)  ring.className = 'timer-ring-fill warning';
    else                   ring.className = 'timer-ring-fill';
}

// Cancel verification
function cancelVerification() {
    document.getElementById('cancel-btn').style.display = 'none';
    document.getElementById('cancel-confirm-btn').style.display = 'block';
}

async function confirmCancel() {
    if (VerificationFlow.verificationId) {
        try {
            const token = localStorage.getItem('access_token');
            const res = await fetch(`/api/verification/cancel/${VerificationFlow.verificationId}`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
            });
            if (res.ok) {
                const data = await res.json();
                if (data.refund_amount > 0)
                    window.toast && window.toast.success(`Cancelled — ${formatMoney(data.refund_amount)} refunded`);
            }
        } catch (e) { /* non-critical */ }
    }
    resetFlow();
}

async function blacklistNumber(phone, service) {
    const token = localStorage.getItem('access_token');
    try {
        const res = await fetch('/api/blacklist', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone_number: phone, service_name: service || 'unknown', reason: 'No SMS received', is_manual: true })
        });
        if (res.ok) window.toast?.success('Number blacklisted.');
        else window.toast?.error('Failed to blacklist number');
    } catch(e) { window.toast?.error('Failed to blacklist number'); }
}


function goBack() {
    if (VerificationFlow.currentStep <= 1) return;

    if (VerificationFlow.currentStep === 3) {
        if (VerificationFlow.verificationId) {
            const token = localStorage.getItem('access_token');
            fetch(`/api/verification/cancel/${VerificationFlow.verificationId}`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            }).catch(() => {});
        }
        clearTimeout(VerificationFlow.scanInterval);
        VerificationFlow.verificationId = null;
        VerificationFlow.elapsedSeconds = 0;
        updateProgress(2);
    } else if (VerificationFlow.currentStep === 2) {
        updateProgress(1);
    }

    const card = document.getElementById(`step-${VerificationFlow.currentStep}-card`);
    if (card) card.scrollIntoView({ behavior: 'smooth' });
}

function showOtherServiceInput() {
    const existing = document.getElementById('other-service-input-row');
    if (existing) { existing.querySelector('input').focus(); return; }
    const row = document.createElement('div');
    row.id = 'other-service-input-row';
    row.style.cssText = 'margin-top:8px; display:flex; gap:8px;';
    row.innerHTML = `
        <input id="other-service-input" type="text" placeholder="Enter service name" class="form-input"
            style="flex:1; padding:8px 12px; border:1px solid var(--border-color,#e5e7eb); border-radius:8px; font-size:14px;"
            onkeydown="if(event.key==='Enter') confirmOtherService()">
        <button class="btn btn-primary" onclick="confirmOtherService()" style="white-space:nowrap;">OK</button>
        <button class="btn btn-secondary" onclick="this.closest('#other-service-input-row').remove()" style="white-space:nowrap;">Cancel</button>
    `;
    document.getElementById('service-search-input').insertAdjacentElement('afterend', row);
    row.querySelector('input').focus();
}

function confirmOtherService() {
    const input = document.getElementById('other-service-input');
    const name = (input?.value || '').trim();
    if (!name) return;
    VerificationFlow.selectedService = name;
    VerificationFlow.selectedServicePrice = null;
    document.getElementById('service-search-input').value = name;
    document.getElementById('service-display').textContent = name;
    document.getElementById('service-selected-display').style.display = 'flex';
    document.getElementById('other-service-input-row')?.remove();
    document.getElementById('continue-btn').disabled = false;
    updatePricing();
}

function resetFlow() {
    clearTimeout(VerificationFlow.scanInterval);
    VerificationFlow.currentStep = 1;
    VerificationFlow.selectedService = null;
    VerificationFlow.selectedServicePrice = null;
    VerificationFlow.selectedAreaCode = null;
    VerificationFlow.selectedCarrier = null;
    VerificationFlow.verificationId = null;
    VerificationFlow.elapsedSeconds = 0;

    // UI resets
    clearServiceSelection();
    document.querySelectorAll('.step-card').forEach(c => c.classList.remove('active'));

    // Go back to method picker
    document.getElementById('step-0-card').style.display = 'block';
    document.getElementById('progress-indicator').style.display = 'none';
    document.getElementById('step-1-card').style.display = 'none';
    document.getElementById('step-2-card').style.display = 'none';
    document.getElementById('step-3-card').style.display = 'none';

    const acInput = document.getElementById('area-code-search-input');
    if (acInput) acInput.value = '';
    const cSel = document.getElementById('carrier-select-inline');
    if (cSel) cSel.value = '';
    document.getElementById('continue-btn').disabled = true;
    document.getElementById('error-container').style.display = 'none';
    document.getElementById('code-received').style.display = 'none';
    const fw = document.getElementById('fallback-warning');
    if (fw) fw.remove();
    document.getElementById('step-0-card').scrollIntoView({ behavior: 'smooth' });
}

function showError(title, message) {
    clearTimeout(VerificationFlow.scanInterval);
    document.getElementById('error-title').textContent = title;
    document.getElementById('error-message').textContent = message;
    document.getElementById('error-container').style.display = 'block';
    window.toast.error(title);
}



function _getServiceIcon(serviceId) {
    const iconMap = {
        whatsapp: 'whatsapp', telegram: 'telegram', google: 'google', facebook: 'facebook',
        instagram: 'instagram', discord: 'discord', twitter: 'x', microsoft: 'microsoft',
        amazon: 'amazon', uber: 'uber', netflix: 'netflix', spotify: 'spotify',
        paypal: 'paypal', venmo: 'venmo', cashapp: 'cashapp', apple: 'apple',
        snapchat: 'snapchat', tiktok: 'tiktok', linkedin: 'linkedin', github: 'github',
        gitlab: 'gitlab', slack: 'slack', zoom: 'zoom', dropbox: 'dropbox',
        airbnb: 'airbnb', doordash: 'doordash', grubhub: 'grubhub', postmates: 'postmates',
        tinder: 'tinder', bumble: 'bumble', hinge: 'hinge', match: 'match',
        steam: 'steam', twitch: 'twitch', epicgames: 'epicgames',
        skype: 'skype', viber: 'viber', line: 'line', wechat: 'wechat',
        coinbase: 'coinbase', binance: 'binance', robinhood: 'robinhood',
        walmart: 'walmart', target: 'target', ebay: 'ebay', etsy: 'etsy', shopify: 'shopify',
        ubereats: 'ubereats', booking: 'bookingdotcom', expedia: 'expedia', lyft: 'lyft',
        reddit: 'reddit', pinterest: 'pinterest', tumblr: 'tumblr',
        playstation: 'playstation', xbox: 'xbox', nintendo: 'nintendo',
        teams: 'microsoftteams', signal: 'signal', messenger: 'messenger'
    };
    const icon = iconMap[serviceId.toLowerCase()] || 'circle';
    return `https://cdn.simpleicons.org/${icon}/E8003D`;
}

// --- Area Codes & Tier Loading ---
// NOTE: full loadAreaCodes() is defined above (around line 530) — this stub is intentionally removed

async function loadTier() {
    // Issue #3 fix: apply cached tier immediately, then validate in background
    let hasCached = false;
    try {
        const cached = localStorage.getItem('nsk_tier_cache');
        if (cached) {
            const { ts, tier } = JSON.parse(cached);
            if (Date.now() - ts < 3600000) {
                VerificationFlow.userTier = tier;
                hasCached = true;
                loadAreaCodes(); // unblock UI immediately from cache
                loadCarriers();
            }
        }
    } catch {}
    // Always revalidate in background (non-blocking regardless of cache)
    try {
        const token = localStorage.getItem('access_token');
        const ctrl = new AbortController();
        const tid = setTimeout(() => ctrl.abort(), 5000);
        const res = await fetch('/api/tiers/current', { headers: { 'Authorization': `Bearer ${token}` }, signal: ctrl.signal });
        clearTimeout(tid);
        if (res.ok) {
            const d = await res.json();
            // Support multiple API response formats
            let freshTier = 'freemium';
            if (d.current_tier) freshTier = d.current_tier;
            else if (d.user?.subscription_tier) freshTier = d.user.subscription_tier;
            else if (d.tier) freshTier = d.tier;

            freshTier = freshTier.toLowerCase();
            localStorage.setItem('nsk_tier_cache', JSON.stringify({ ts: Date.now(), tier: freshTier }));
            if (freshTier !== VerificationFlow.userTier) {
                VerificationFlow.userTier = freshTier;
                console.log(`[Tier] Updated to: ${freshTier}`);
                loadAreaCodes();
                loadCarriers();
                updatePricing();
                applyTierGating();
            }
        }
    } catch(e) { console.error('[Tier] Background validation failed:', e); }
    if (!hasCached) { loadAreaCodes(); loadCarriers(); }
    applyTierGating();
}

// Cmd+K / Ctrl+K shortcut to open service search
document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (VerificationFlow.currentStep === 1 && _modalItems['service']?.length) openImmersiveModal('service');
    }
});

document.addEventListener('DOMContentLoaded', async () => {
    try {
    // Orphaned verification recovery — restore active session if user navigated away
    const orphanId = localStorage.getItem('active_verification_id');
    if (orphanId) {
        const token = localStorage.getItem('access_token');
        fetch(`/api/verification/status/${orphanId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        }).then(r => r.ok ? r.json() : null).then(data => {
            if (data && data.status === 'pending' && data.phone_number) {
                VerificationFlow.verificationId = orphanId;
                if (data.ends_at) {
                    VerificationFlow.createdAt = data.created_at || new Date().toISOString();
                    VerificationFlow.totalDurationMs =
                        new Date(data.ends_at).getTime() - new Date(VerificationFlow.createdAt).getTime();
                }
                document.getElementById('step-0-card').style.display = 'none';
                document.getElementById('progress-indicator').style.display = 'block';
                document.getElementById('phone-number').textContent = formatPhone(data.phone_number);
                updateProgress(3);
                startPolling();
                window.toast && window.toast.info('Resuming your active verification.');
            } else {
                localStorage.removeItem('active_verification_id');
            }
        }).catch(() => localStorage.removeItem('active_verification_id'));
    }

    // Load tier FIRST — must know tier before any UI renders
    await loadTier();

    // Load services (critical path)
    await loadServices();

    // Load balance in background
    loadBalance();

    // Load presets (Pro+ only, non-blocking)
    loadPresets();

    updateProgress(1);

    // Pre-select service from query param
    const params = new URLSearchParams(window.location.search);
    const preService = params.get('service');
    if (preService) {
        // Wait for services to be ready
        let retries = 0;
        const checkServices = setInterval(() => {
            const items = _modalItems['service'] || [];
            if (items.length > 0 || retries++ > 10) {
                clearInterval(checkServices);
                const item = items.find(i => i.value.toLowerCase() === preService.toLowerCase());
                if (item) {
                    selectImmersiveItem(item.value, item.label, item.price);
                } else {
                    VerificationFlow.selectedService = preService;
                    document.getElementById('service-search-input').value = preService;
                    document.getElementById('service-display').textContent = preService;
                    document.getElementById('service-selected-display').style.display = 'flex';
                    document.getElementById('continue-btn').disabled = false;
                }
            }
        }, 100);
    }
    } catch(e) { console.error('Page init error:', e); }
});

async function loadBalance() {
    try {
        const res = await fetch('/api/billing/balance', { headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` } });
        if (res.ok) {
            const d = await res.json();
            document.getElementById('pricing-balance').textContent = formatMoney(parseFloat(d.balance ?? d.credits ?? 0));
        }
    } catch(e) {}
}

async function updatePricing() {
    const areaCode = VerificationFlow.selectedAreaCode || null;
    const service = VerificationFlow.selectedService || null;
    const capability = VerificationFlow.selectedCapability || 'sms';
    const el = document.getElementById('pricing-cost');
    if (!el) return;

    if (service) {
        try {
            const params = new URLSearchParams({ service, country: 'US', capability });
            if (areaCode) params.append('area_code', areaCode);
            const token = localStorage.getItem('access_token');
            const res = await fetch(`/api/verification/price?${params}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                el.textContent = formatMoney(data.total_cost);
                return;
            }
        } catch (e) {}
    }

    // Fallback to local calculation
    let price = VerificationFlow.selectedServicePrice || 2.63;
    let filterCharges = 0;
    if (VerificationFlow.userTier === 'payg' && areaCode) filterCharges += 0.25;
    el.textContent = formatMoney(price + filterCharges);
}
// Phase 4 Area Code Check Logic
let _acCheckTimeout = null;
let _acCheckAbort = null;

function debouncedCheckAreaCode(value) {
    const btn = document.getElementById('clear-ac-btn');
    if (btn) btn.style.display = value ? 'block' : 'none';

    // Reset state
    const input = document.getElementById('area-code-search-input');
    const badge = document.getElementById('ac-status-badge');
    const msg = document.getElementById('ac-message');
    const alts = document.getElementById('ac-alternatives');
    const spinner = document.getElementById('ac-spinner');

    // Clean up purely visual locking if they haven't typed yet, just to be safe
    if (input) input.style.borderColor = '#e5e7eb';
    if (input) input.style.backgroundColor = '#fff';
    if (badge) badge.style.display = 'none';
    if (msg) msg.style.display = 'none';
    if (alts) alts.style.display = 'none';

    // Basic validation
    const code = value.replace(/\D/g, '');
    VerificationFlow.selectedAreaCode = code.length === 3 ? code : null;
    updateSelectionChips();
    updateContinueBtn();

    if (code.length < 3) {
        if (_acCheckTimeout) clearTimeout(_acCheckTimeout);
        if (spinner) spinner.style.display = 'none';
        return;
    }

    if (!VerificationFlow.selectedService) return; // Need service to score

    // Set loading
    if (spinner) spinner.style.display = 'block';
    if (btn) btn.style.display = 'none';

    if (_acCheckTimeout) clearTimeout(_acCheckTimeout);
    if (_acCheckAbort) _acCheckAbort.abort();

    _acCheckTimeout = setTimeout(() => {
        checkAreaCodeAPI(code);
    }, 500);
}

async function checkAreaCodeAPI(code) {
    const input = document.getElementById('area-code-search-input');
    const badge = document.getElementById('ac-status-badge');
    const msg = document.getElementById('ac-message');
    const alts = document.getElementById('ac-alternatives');
    const spinner = document.getElementById('ac-spinner');
    const btn = document.getElementById('clear-ac-btn');
    const continueBtn = document.getElementById('continue-btn');

    _acCheckAbort = new AbortController();
    try {
        const res = await fetch(`/api/area-codes/check?service=${encodeURIComponent(VerificationFlow.selectedService)}&area_code=${encodeURIComponent(code)}`, {
            signal: _acCheckAbort.signal
        });

        spinner.style.display = 'none';
        btn.style.display = 'block';

        if (!res.ok) {
            // Probably unsupported provider format or invalid
            const data = await res.json().catch(()=>({}));
            input.style.borderColor = '#ef4444';
            msg.textContent = data.error?.message || data.detail || 'Unsupported area code';
            msg.style.color = '#dc2626';
            msg.style.display = 'block';
            updateContinueBtn();
            return;
        }

        const data = await res.json();

        if (data.status === 'available') {
            input.style.borderColor = '#10b981';
            input.style.backgroundColor = '#f0fdf4';
            badge.textContent = '✓ Available';
            badge.style.color = '#10b981';
            badge.style.display = 'inline-block';
            msg.textContent = data.message;
            msg.style.color = '#059669';
            msg.style.display = 'block';
            updateContinueBtn();

        } else if (data.status === 'unavailable') {
            input.style.borderColor = '#f59e0b';
            input.style.backgroundColor = '#fffbeb';
            badge.textContent = 'Unavailable';
            badge.style.color = '#d97706';
            badge.style.display = 'inline-block';
            msg.textContent = data.message;
            msg.style.color = '#92400e';
            msg.style.display = 'block';

            // Mark state as custom error to block continue button explicitly
            continueBtn.disabled = true;

            if (data.alternatives && data.alternatives.length > 0) {
                renderAlternatives(data.alternatives);
            }

        } else if (data.status === 'unknown') {
            input.style.borderColor = '#e5e7eb';
            msg.textContent = data.message;
            msg.style.color = '#6b7280';
            msg.style.display = 'block';
            updateContinueBtn();

            if (data.alternatives && data.alternatives.length > 0) {
                renderAlternatives(data.alternatives);
            }
        }

    } catch (e) {
        if (e.name === 'AbortError') return;
        spinner.style.display = 'none';
        btn.style.display = 'block';
        console.error('Area code check failed', e);
        // Fallback to unknown if API fails
        msg.textContent = "Availability will be confirmed on purchase. You won't be charged if unavailable.";
        msg.style.color = '#6b7280';
        msg.style.display = 'block';
        updateContinueBtn();
    }
}

function renderAlternatives(alts) {
    const list = document.getElementById('ac-alternatives');
    let html = '<div style="font-size:11px; font-weight:600; color:#6b7280; margin-top:4px;">Try nearby options:</div>';

    alts.forEach(alt => {
        let dotColor = '#9ca3af'; // unknown
        if (alt.status === 'available') dotColor = '#10b981';
        if (alt.status === 'unavailable') dotColor = '#ef4444';

        const tierLabels = {
            'same_city': 'Same City',
            'nearby': 'Nearby',
            'same_state': 'Same State'
        };

        html += `
            <div onclick="selectAlternative('${alt.area_code}')" style="display:flex; justify-content:space-between; align-items:center; padding:6px 10px; background:#f9fafb; border:1px solid #f3f4f6; border-radius:6px; cursor:pointer; transition:background 0.2s;" onmouseover="this.style.background='#f3f4f6'" onmouseout="this.style.background='#f9fafb'">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="width:8px; height:8px; border-radius:50%; background:${dotColor};"></span>
                    <span style="font-size:13px; font-weight:600; color:#374151;">${alt.area_code}</span>
                    <span style="font-size:12px; color:#6b7280;">(${alt.city})</span>
                </div>
                <div style="font-size:11px; margin-left:8px; color:#9ca3af; background:#fff; padding:2px 6px; border:1px solid #e5e7eb; border-radius:4px;">
                    ${tierLabels[alt.proximity] || alt.proximity}
                </div>
            </div>
        `;
    });
    list.innerHTML = html;
    list.style.display = 'flex';
}

function selectAlternative(code) {
    const input = document.getElementById('area-code-search-input');
    input.value = code;
    debouncedCheckAreaCode(code);
}

// === Presets ===
let _presets = [];

async function loadPresets() {
    const rank = VerificationFlow.tierRank[(VerificationFlow.userTier || '').toLowerCase()] || 0;
    if (rank < 2) return; // Pro+ only
    document.getElementById('presets-section').style.display = 'block';
    try {
        const token = localStorage.getItem('access_token');
        const res = await fetch('/api/presets/', { headers: { 'Authorization': `Bearer ${token}` } });
        if (!res.ok) return;
        _presets = await res.json();
        renderPresets();
    } catch(e) { /* silent */ }
}

function renderPresets() {
    const list = document.getElementById('presets-list');
    const empty = document.getElementById('presets-empty');
    if (!_presets.length) { list.innerHTML = ''; empty.style.display = 'block'; return; }
    empty.style.display = 'none';
    list.innerHTML = _presets.map(p => `
        <div style="display:inline-flex; align-items:center; gap:6px; padding:6px 12px; background:#fff0f0; border:1px solid #ffd1d1; border-radius:20px; font-size:13px; cursor:pointer;" onclick="applyPreset('${p.id}')">
            <span style="font-weight:600; color:#37352F;">${p.name}</span>
            <button onclick="event.stopPropagation(); deletePreset('${p.id}')" style="background:none; border:none; color:#9ca3af; cursor:pointer; font-size:14px; padding:0; line-height:1;">&times;</button>
        </div>
    `).join('');
}

function applyPreset(id) {
    const p = _presets.find(x => x.id === id);
    if (!p) return;
    const items = _modalItems['service'] || [];
    const match = items.find(i => i.value === p.service_id);
    if (match) selectImmersiveItem(match.value, match.label, match.price || 0);
    if (p.area_code) {
        const acInput = document.getElementById('area-code-search-input');
        if (acInput) { acInput.value = p.area_code; debouncedCheckAreaCode(p.area_code); }
        const adv = document.getElementById('advanced-options-body');
        if (adv) adv.style.display = 'block';
        const icon = document.getElementById('advanced-toggle-icon');
        if (icon) icon.textContent = '▼';
    }
}

async function saveCurrentAsPreset() {
    const svc = VerificationFlow.selectedService;
    if (!svc) return;

    const presetsSection = document.getElementById('presets-section');
    if (document.getElementById('preset-name-input-row')) return;

    const row = document.createElement('div');
    row.id = 'preset-name-input-row';
    row.style.cssText = 'display:flex;gap:8px;margin-top:8px;';
    row.innerHTML = `
        <input id="preset-name-input" type="text" placeholder='e.g. "WhatsApp NY"'
            style="flex:1;padding:6px 10px;border:1px solid #e5e7eb;border-radius:6px;font-size:13px;"
            onkeydown="if(event.key==='Enter')confirmSavePreset();if(event.key==='Escape')cancelSavePreset();">
        <button onclick="confirmSavePreset()" style="background:#FE3C72;color:white;border:none;padding:6px 12px;border-radius:6px;font-size:12px;font-weight:600;cursor:pointer;">Save</button>
        <button onclick="cancelSavePreset()" style="background:none;border:1px solid #e5e7eb;padding:6px 10px;border-radius:6px;font-size:12px;cursor:pointer;">Cancel</button>
    `;
    presetsSection.appendChild(row);
    setTimeout(() => document.getElementById('preset-name-input')?.focus(), 50);
}

function cancelSavePreset() {
    document.getElementById('preset-name-input-row')?.remove();
}

async function confirmSavePreset() {
    const input = document.getElementById('preset-name-input');
    const name = (input?.value || '').trim();
    if (!name) { input?.focus(); return; }
    cancelSavePreset();
    const svc = VerificationFlow.selectedService;
    try {
        const token = localStorage.getItem('access_token');
        const ac = document.getElementById('area-code-search-input')?.value || null;
        const res = await fetch('/api/presets/', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, service_id: svc, country_id: 'US', area_code: ac || null })
        });
        if (!res.ok) { const d = await res.json().catch(()=>({})); window.toast?.error(d.detail || 'Failed to save'); return; }
        _presets.push(await res.json());
        renderPresets();
        window.toast?.success('Preset saved');
    } catch(e) { window.toast?.error('Failed to save preset'); }
}

async function deletePreset(id) {
    try {
        const token = localStorage.getItem('access_token');
        await fetch(`/api/presets/${id}`, { method: 'DELETE', headers: { 'Authorization': `Bearer ${token}` } });
        _presets = _presets.filter(p => p.id !== id);
        renderPresets();
    } catch(e) { /* silent */ }
}

// Show save button when a service is selected
const _origSelectImm = selectImmersiveItem;
selectImmersiveItem = function(value, label, price) {
    _origSelectImm(value, label, price);
    const saveBtn = document.getElementById('save-preset-btn');
    if (saveBtn && VerificationFlow.selectedService) {
        const rank = VerificationFlow.tierRank[(VerificationFlow.userTier || '').toLowerCase()] || 0;
        saveBtn.style.display = rank >= 2 ? 'inline-block' : 'none';
    }
};

