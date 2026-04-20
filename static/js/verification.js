
function formatPhone(raw) {
    const d = (raw || '').replace(/\D/g, '');
    if (d.length === 11 && d[0] === '1') return `+1 (${d.slice(1,4)}) ${d.slice(4,7)}-${d.slice(7)}`;
    return raw;
}

let selectedService = null;
let currentVerification = null;
let pollingInterval = null;
let allServices = [];
let allAreaCodes = [];
let servicesLoaded = false;
let userTier = 'freemium';

const TIER_RANK = {
    'freemium': 0,
    'payg': 1,
    'starter': 1,
    'pro': 2,
    'custom': 3
};

/**
 * Check tier access and toggle UI filters
 */
async function checkTierAccess() {
    try {
        const token = localStorage.getItem('access_token');
        const res = await axios.get('/api/tiers/current', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        userTier = res.data.current_tier || 'freemium';
        console.log(`[Verify] User Tier: ${userTier}`);

        const currentRank = TIER_RANK[userTier.toLowerCase()] || 0;

        // Area Code (PAYG+)
        if (currentRank >= 1) {
            const wrap = document.getElementById('area-code-field-wrapper');
            const lock = document.getElementById('area-code-lock');
            if(wrap) wrap.style.display = 'block';
            if(lock) lock.style.display = 'none';
        }

    } catch (error) {
        console.warn('[Verify] Could not determine user tier:', error);
    }
}

async function loadServices() {
    console.log('Loading services for US...');
    const select = document.getElementById('service-select');
    
    try {
        // Show loading state
        select.innerHTML = '<option value="">Loading services...</option>';
        select.disabled = true;
        
        const token = localStorage.getItem('access_token');
        const res = await axios.get(`/api/countries/US/services`, {
            headers: { 'Authorization': `Bearer ${token}` },
            timeout: 5000  // 5 second timeout
        });

        if (res.data && res.data.services && res.data.services.length > 0) {
            allServices = res.data.services;
            servicesLoaded = true;
            
            // Populate select
            select.innerHTML = '<option value="">Select a service...</option>';
            allServices.forEach(service => {
                const option = document.createElement('option');
                option.value = service.id;
                option.textContent = `${service.name} - ${formatMoney(service.cost)}`;
                select.appendChild(option);
            });
            
            select.disabled = false;
            
            // Show source indicator
            const source = res.data.source || 'unknown';
            console.log(`✅ Loaded ${allServices.length} services from ${source}`);
            
            // If using fallback, show warning
            if (source === 'fallback') {
                console.warn('⚠️ Using fallback services - API unavailable');
            }
        } else {
            throw new Error('No services returned from API');
        }
    } catch (error) {
        console.error(`❌ Failed to load services for US from API:`, error);
        
        // Use hardcoded fallback
        allServices = [
            { id: 'whatsapp', name: 'WhatsApp', cost: 2.50 },
            { id: 'telegram', name: 'Telegram', cost: 2.00 },
            { id: 'discord', name: 'Discord', cost: 2.25 },
            { id: 'instagram', name: 'Instagram', cost: 2.75 },
            { id: 'facebook', name: 'Facebook', cost: 2.50 },
            { id: 'google', name: 'Google', cost: 2.00 },
            { id: 'twitter', name: 'Twitter', cost: 2.50 },
            { id: 'microsoft', name: 'Microsoft', cost: 2.25 }
        ];
        servicesLoaded = true;
        
        // Populate select with fallback
        select.innerHTML = '<option value="">Select a service...</option>';
        allServices.forEach(service => {
            const option = document.createElement('option');
            option.value = service.id;
            option.textContent = `${service.name} - ${formatMoney(service.cost)}`;
            select.appendChild(option);
        });
        
        select.disabled = false;
        
        console.log(`⚠️ Using ${allServices.length} fallback services`);
    }
}

function setupSearchListener() {
    const searchInput = document.getElementById('service-search');
    const dropdown = document.getElementById('service-dropdown');

    searchInput.addEventListener('focus', () => {
        if (!servicesLoaded) return;
        const query = searchInput.value.toLowerCase().trim();
        if (!query) {
            const top = allServices.slice(0, 10);
            if (top.length > 0) {
                dropdown.innerHTML = top.map(s => {
                    const safeName = s.name.replace(/'/g, "\\'");
                    return `<div class="service-option" onclick="selectService('${safeName}', '${s.id || s.name}')">${s.name}</div>`;
                }).join('');
                dropdown.style.display = 'block';
            }
        }
    });

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();

        if (!servicesLoaded) {
            dropdown.innerHTML = '<div style="padding: 12px; color: #9ca3af; text-align: center;">Loading services...</div>';
            dropdown.style.display = 'block';
            return;
        }

        if (!query || query.length < 1) {
            dropdown.style.display = 'none';
            return;
        }

        const filtered = allServices.filter(s => s.name.toLowerCase().includes(query));

        if (filtered.length === 0) {
            dropdown.innerHTML = '<div style="padding: 12px; color: #9ca3af; text-align: center;">No services found</div>';
            dropdown.style.display = 'block';
            return;
        }

        dropdown.innerHTML = filtered.slice(0, 10).map(s => {
            const safeName = s.name.replace(/'/g, "\\'");
            return `
    <div onclick="selectService('${s.id}', '${safeName}', ${s.cost})" 
         style="padding: 12px; cursor: pointer; border-bottom: 1px solid #f3f4f6; transition: background 0.15s;"
         onmouseover="this.style.background='#f9fafb'"
         onmouseout="this.style.background='white'">
        <div style="font-weight: 600; color: #1f2937;">${s.name}</div>
        <div style="font-size: 12px; color: #6b7280; margin-top: 2px;">${formatMoney(s.cost)} per verification</div>
    </div>
    `;
        }).join('');
        dropdown.style.display = 'block';

        console.log(`Found ${filtered.length} services for "${query}"`);
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (e.target !== searchInput && !dropdown.contains(e.target)) {
            dropdown.style.display = 'none';
        }
    });
}

function selectService(id, name, cost) {
    selectedService = id;
    document.getElementById('service-search').value = name;
    document.getElementById('service-cost').textContent = formatMoney(cost);
    document.getElementById('service-dropdown').style.display = 'none';
    document.getElementById('purchase-btn').disabled = false;
    document.getElementById('purchase-btn').textContent = 'Get SMS Code';
    console.log(`Selected: ${name} (${formatMoney(cost)})`);

    // Update favorite button
    const btn = document.getElementById('favorite-btn');
    if (btn) {
        if (favoriteServices.isFavorite(id)) {
            btn.textContent = '⭐';
            btn.style.color = '#f59e0b';
        } else {
            btn.textContent = '☆';
            btn.style.color = '#6b7280';
        }
    }

    // Remove area code load triggering since we use purely dynamic typing now.

    // Trigger dynamic pricing preview
    debouncedUpdatePricePreview();
}

/**
 * Debounce utility to limit frequency of API calls
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Debounced version of price preview
const debouncedUpdatePricePreview = debounce(updatePricePreview, 500);

async function updatePricePreview() {
    if (!selectedService) return;

    const costDisplay = document.getElementById('service-cost');
    costDisplay.style.opacity = '0.5';

    try {
        const areaCodeInput = document.getElementById('area-code-search-input');
        const areaCode = areaCodeInput ? areaCodeInput.value.replace(/\D/g, '') : null;
        const token = localStorage.getItem('access_token');

        const params = new URLSearchParams({
            service: selectedService,
            country: 'US',
        });

        if (areaCode && areaCode.length === 3) params.append('area_code', areaCode);

        const res = await axios.get(`/api/verification/pricing?${params.toString()}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.data && res.data.total_price) {
            costDisplay.textContent = formatMoney(res.data.total_price);
            console.log(`[Pricing] Base: ${formatMoney(res.data.provider_cost)}, Total: ${formatMoney(res.data.total_price)}`);
        }
    } catch (error) {
        console.error('[Pricing] Failed to update preview:', error);
    } finally {
        costDisplay.style.opacity = '1';
    }
}

// Track which area code user originally wanted before selecting an alternative
let _originalRequestedAreaCode = null;

async function purchaseVerification() {
    if (!selectedService) return;

    const btn = document.getElementById('purchase-btn');
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner-sm" style="border-color: rgba(255,255,255,0.3); border-top-color: white;"></div> Processing...';

    try {
        const areaCodeInput = document.getElementById('area-code-search-input');
        const rawCode = areaCodeInput ? areaCodeInput.value.replace(/\D/g, '') : '';
        const finalAreaCode = (rawCode && rawCode.length === 3) ? rawCode : null;
        const token = localStorage.getItem('access_token');

        // Build payload — schema uses area_codes (list) not area_code
        const payload = {
            service: selectedService,
            country: 'US',
            capability: 'sms',
            area_codes: finalAreaCode ? [finalAreaCode] : null,
            idempotency_key: (typeof crypto !== 'undefined' && crypto.randomUUID)
                ? crypto.randomUUID()
                : (Date.now().toString(36) + Math.random().toString(36).slice(2)),
        };

        // Phase 6.4: track if this is an alternative selection
        if (_originalRequestedAreaCode && finalAreaCode && finalAreaCode !== _originalRequestedAreaCode) {
            payload.selected_from_alternatives = true;
            payload.original_request = _originalRequestedAreaCode;
        }

        const res = await axios.post('/api/v1/verification/request', payload, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.data && res.data.phone_number) {
            _originalRequestedAreaCode = null;  // Reset after successful purchase
            currentVerification = res.data;
            const formatted = formatPhone(res.data.phone_number);
            document.getElementById('phone-display').innerHTML = `
                <div style="display: flex; flex-direction: column; align-items: center; gap: 8px;">
                    <span style="font-size: 24px; letter-spacing: 1px;">${formatted}</span>
                    <button onclick="navigator.clipboard.writeText('${res.data.phone_number}')" style="background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.4); color: white; padding: 4px 14px; border-radius: 6px; cursor: pointer; font-size: 12px;">Copy</button>
                    <span style="font-size: 11px; background: rgba(255,255,255,0.2); padding: 2px 8px; border-radius: 12px; font-weight: 500;">Ready to Verify</span>
                </div>
            `;
            if (res.data.fallback_applied) {
                _showFallbackAlert();
            }
            document.getElementById('reception-card').style.display = 'block';
            startPolling(res.data.id);
            if (window.refreshBalance) window.refreshBalance();
        }
    } catch (error) {
        const data = error.response?.data;

        // Phase 5: handle area code unavailable — show alternatives instead of generic alert
        if (data && data.error === 'area_code_unavailable') {
            _handleAreaCodeUnavailable(data);
            btn.disabled = false;
            btn.textContent = 'Get SMS Code';
            return;
        }

        // All other errors
        const msg = data?.detail || data?.message || 'Purchase failed. Please try again.';
        _showPurchaseError(msg);
        btn.disabled = false;
        btn.textContent = 'Get SMS Code';
    }
}

function _showFallbackAlert() {
    const existing = document.querySelector('.fallback-alert');
    if (existing) existing.remove();
    const alert = document.createElement('div');
    alert.className = 'fallback-alert';
    alert.style.cssText = 'background:#fffbeb;border:1px solid #fcd34d;color:#92400e;padding:12px;border-radius:8px;margin-bottom:16px;font-size:13px;display:flex;align-items:flex-start;gap:10px;';
    alert.innerHTML = `
        <div style="font-size:16px;">⚡</div>
        <div><strong style="display:block;margin-bottom:2px;">Nearby area code assigned</strong>
        Your requested area code wasn't available. We found you the closest match.</div>
    `;
    const card = document.getElementById('reception-card');
    if (card) card.parentNode.insertBefore(alert, card);
}

function _showPurchaseError(message) {
    const existing = document.querySelector('.purchase-error-alert');
    if (existing) existing.remove();
    const alert = document.createElement('div');
    alert.className = 'purchase-error-alert';
    alert.style.cssText = 'background:#fef2f2;border:1px solid #fca5a5;color:#991b1b;padding:12px;border-radius:8px;margin-bottom:16px;font-size:13px;';
    alert.textContent = message;
    const btn = document.getElementById('purchase-btn');
    if (btn) btn.parentNode.insertBefore(alert, btn);
    setTimeout(() => alert.remove(), 6000);
}

function _handleAreaCodeUnavailable(data) {
    const areaCodeInput = document.getElementById('area-code-search-input');
    const currentCode = areaCodeInput ? areaCodeInput.value.replace(/\D/g, '') : '';

    // Store the original request so it can be tracked if user picks an alternative
    if (currentCode.length === 3) _originalRequestedAreaCode = currentCode;

    // Remove stale alerts
    document.querySelectorAll('.ac-unavailable-alert').forEach(el => el.remove());

    const alts = data.alternatives || [];
    const altHTML = alts.length > 0 ? `
        <div style="margin-top:10px;">
            <p style="font-size:12px;margin-bottom:6px;font-weight:600;">Select a nearby alternative:</p>
            <div style="display:flex;flex-wrap:wrap;gap:8px;">
                ${alts.slice(0, 6).map(alt => `
                    <button
                        onclick="selectAlternativeCode('${alt.area_code}')"
                        style="background:#f0fdf4;border:1px solid #6ee7b7;color:#065f46;padding:6px 12px;border-radius:6px;cursor:pointer;font-size:13px;font-weight:500;"
                        title="${alt.city || ''}, ${alt.state || ''}"
                    >${alt.area_code}<span style="font-weight:400;font-size:11px;"> ${alt.city || alt.state || ''}</span></button>
                `).join('')}
            </div>
        </div>
    ` : '';

    const alertEl = document.createElement('div');
    alertEl.className = 'ac-unavailable-alert';
    alertEl.style.cssText = 'background:#fffbeb;border:1px solid #fcd34d;color:#92400e;padding:14px;border-radius:8px;margin-bottom:16px;font-size:13px;';
    alertEl.innerHTML = `
        <strong style="display:block;margin-bottom:4px;">⚠️ ${data.message || 'Area code not available right now.'}</strong>
        <span style="font-size:12px;">No credits were charged.</span>
        ${altHTML}
    `;

    const btn = document.getElementById('purchase-btn');
    if (btn) btn.parentNode.insertBefore(alertEl, btn);
}

function selectAlternativeCode(code) {
    // Remove any stale unavailable alerts
    document.querySelectorAll('.ac-unavailable-alert').forEach(el => el.remove());

    const areaCodeInput = document.getElementById('area-code-search-input');
    if (areaCodeInput) {
        areaCodeInput.value = code;
        debouncedCheckAreaCode(code);
        debouncedUpdatePricePreview();
    }
}



async function cancelVerification() {
    if (!currentVerification) return;

    const btn = document.getElementById('cancel-btn');
    btn.disabled = true;
    btn.textContent = 'Cancelling...';

    try {
        const token = localStorage.getItem('access_token');
        await axios.delete(`/api/verify/${currentVerification.id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
    } catch (error) {
        console.error('Cancel failed:', error);
    }

    resetForm();
}

function startPolling(id) {
    let count = 0;
    
    // Initialize WebSocket with fallback
    const smsWS = new SMSWebSocket(id);
    
    // Updated waiting UI with Pulse Animation
    document.getElementById('status-text').innerHTML = `
    <div class="pulse-container">
        <div class="pulse-ring"></div>
        <div class="pulse-dot"></div>
    </div>
    <div style="font-weight:600; color:#2563eb;">Scanning Network...</div>
    <div id="timer-display" style="font-size:12px; color:#6b7280; margin-top:4px;">0s elapsed</div>
    <div id="connection-status" style="font-size:10px; color:#9ca3af; margin-top:4px;">🟢 Connected</div>
`;

    // Handle WebSocket messages
    smsWS.onMessage((data) => {
        if (data.type === 'sms_update' && data.data) {
            if (data.data.sms_code) {
                displaySMSCode(data.data.sms_code);
                smsWS.close();
            }
        }
    });

    // Update connection status
    smsWS.onConnect(() => {
        const statusEl = document.getElementById('connection-status');
        if (statusEl) statusEl.innerHTML = '🟢 Live updates';
    });

    smsWS.onDisconnect(() => {
        const statusEl = document.getElementById('connection-status');
        if (statusEl) statusEl.innerHTML = '🟡 Reconnecting...';
    });

    // Connect WebSocket
    smsWS.connect();

    // Timer interval
    pollingInterval = setInterval(() => {
        count++;
        const timerEl = document.getElementById('timer-display');
        if (timerEl) timerEl.textContent = `${count * 5}s elapsed`;

        // Update connection status if using fallback
        if (smsWS.useFallback) {
            const statusEl = document.getElementById('connection-status');
            if (statusEl) statusEl.innerHTML = '🔵 Polling mode';
        }

        // Timeout after 5 minutes
        if (count >= 60) {
            document.getElementById('status-text').textContent = 'Timeout - No SMS received';
            document.getElementById('status-text').parentElement.style.background = '#fee2e2';
            document.getElementById('status-text').parentElement.style.borderColor = '#fecaca';
            document.getElementById('status-text').style.color = '#991b1b';
            clearInterval(pollingInterval);
            smsWS.close();
        }
    }, 5000);

    // Store WebSocket reference for cleanup
    currentVerification.websocket = smsWS;
}

function displaySMSCode(code) {
    document.getElementById('code-display').textContent = code;
    document.getElementById('status-text').textContent = 'SMS Received';
    document.getElementById('status-text').parentElement.style.background = '#d1fae5';
    document.getElementById('status-text').parentElement.style.borderColor = '#a7f3d0';
    document.getElementById('status-text').style.color = '#065f46';
    document.getElementById('code-display').style.color = '#059669';
    document.getElementById('copy-btn').style.display = 'block';

    // Play notification sound
    playNotificationSound();

    if (pollingInterval) clearInterval(pollingInterval);
}

function copyCode() {
    const code = document.getElementById('code-display').textContent.trim();

    // Success animation helper
    const animateSuccess = () => {
        const btn = document.getElementById('copy-btn');
        const originalText = btn.textContent;
        const originalBg = btn.style.background;

        btn.textContent = 'Copied!';
        btn.style.background = '#059669';

        setTimeout(() => {
            btn.textContent = 'Copy Code'; // Hardcoded reset, better than keeping "Copied!" if they click again
            btn.style.background = '#10b981';
        }, 2000);
    };

    // Try Modern API
    if (navigator.clipboard) {
        navigator.clipboard.writeText(code).then(animateSuccess).catch(() => fallbackCopy(code, animateSuccess));
    } else {
        fallbackCopy(code, animateSuccess);
    }
}

function fallbackCopy(text, onSuccess) {
    const textArea = document.createElement("textarea");
    textArea.value = text;

    // Ensure it's not visible but part of DOM
    textArea.style.position = "fixed";
    textArea.style.left = "-9999px";
    textArea.style.top = "0";
    document.body.appendChild(textArea);

    textArea.focus();
    textArea.select();

    try {
        const successful = document.execCommand('copy');
        if (successful) onSuccess();
    } catch (err) {
        console.error('Fallback copy failed', err);
    }

    document.body.removeChild(textArea);
}

async function resetForm() {
    if (currentVerification) {
        // Close WebSocket if exists
        if (currentVerification.websocket) {
            currentVerification.websocket.close();
        }
        
        try {
            const token = localStorage.getItem('access_token');
            await axios.delete(`/api/verify/${currentVerification.id}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
        } catch (error) { }
    }

    selectedService = null;
    currentVerification = null;
    if (pollingInterval) clearInterval(pollingInterval);

    document.getElementById('service-search').value = '';
    document.getElementById('service-cost').textContent = formatMoney(0);
    document.getElementById('reception-card').style.display = 'none';
    document.getElementById('code-display').textContent = '------';
    document.getElementById('copy-btn').style.display = 'none';
    document.getElementById('cancel-btn').disabled = false;
    document.getElementById('cancel-btn').textContent = 'Cancel';
    document.getElementById('purchase-btn').disabled = true;
    document.getElementById('purchase-btn').textContent = 'Continue';

    // Reset status styling
    const statusContainer = document.getElementById('status-text').parentElement;
    statusContainer.style.background = '#f0f9ff';
    statusContainer.style.borderColor = '#bfdbfe';
    document.getElementById('status-text').style.color = '#1e40af';
    document.getElementById('code-display').style.color = '#2563eb';

    // Remove fallback alert if present
    const existingAlert = document.querySelector('.fallback-alert');
    if (existingAlert) {
        existingAlert.remove();
    }

    if (window.refreshBalance) window.refreshBalance();
}

// Sound initialization
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

function playNotificationSound() {
    // Simple crisp "ping" using oscillator to avoid external dependencies
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const oscillator = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioCtx.destination);

    oscillator.type = 'sine';
    oscillator.frequency.setValueAtTime(880, audioCtx.currentTime); // A5
    oscillator.frequency.exponentialRampToValueAtTime(440, audioCtx.currentTime + 0.5);

    gainNode.gain.setValueAtTime(0.5, audioCtx.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.5);

    oscillator.start();
    oscillator.stop(audioCtx.currentTime + 0.5);
}

// Utility function for error display
function showError(message) {
    console.error('[Verify Error]', message);
    alert(message);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', async function () {
    console.log('Initializing SMS Verification page...');

    // Check if axios is available
    if (typeof axios === 'undefined') {
        console.error('Axios is not loaded. Please ensure the CDN script is loaded before this script.');
        return;
    }

    await checkTierAccess(); // Check tier gating first
    await loadServices();

    // Add listeners for filters to update pricing
    const aci = document.getElementById('area-code-search-input');
    if (aci) aci.addEventListener('input', debouncedUpdatePricePreview);

    // Tier 3: Load Presets logic
    const currentRank = TIER_RANK[userTier.toLowerCase()] || 0;
    if (currentRank >= 2) {
        document.getElementById('save-preset-ui').style.display = 'block';
        loadUserPresets();
    } else {
        document.getElementById('presets-list').style.display = 'none';
        document.getElementById('save-preset-ui').style.display = 'none';
        document.getElementById('preset-lock').style.display = 'block';
    }

    setupSearchListener();
    console.log('✅ Page ready');
});

// --- Preset Logic ---
async function loadUserPresets() {
    try {
        const token = localStorage.getItem('access_token');
        const res = await axios.get('/api/v1/presets/', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        const list = document.getElementById('presets-list');
        if (res.data.length === 0) {
            list.innerHTML = '<div style="font-size: 12px; color: #9ca3af; text-align: center; padding: 10px;">No presets saved yet</div>';
            return;
        }

        list.innerHTML = res.data.map(p => `
        <div class="preset-item" style="display: flex; justify-content: space-between; align-items: center; padding: 8px; background: #f0f9ff; border: 1px solid #bfdbfe; border-radius: 6px; margin-bottom: 6px; cursor: pointer;"
             onclick="applyPreset('${p.service_id}', '${p.country_id}', '${p.area_code || ''}', '${p.carrier || ''}')">
            <div style="font-size: 12px; font-weight: 600; color: #1e40af; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 140px;">
                ${p.name}
            </div>
            <button onclick="deletePreset('${p.id}', event)" style="background: none; border: none; font-size: 10px; color: #ef4444; cursor: pointer; padding: 2px;">
                ✕
            </button>
        </div>
    `).join('');

    } catch (e) {
        console.error("Failed to load presets", e);
    }
}

async function saveCurrentPreset() {
    const name = document.getElementById('preset-name-input').value.trim();
    if (!name || !selectedService) {
        alert("Please select a service and enter a name");
        return;
    }

    try {
        const token = localStorage.getItem('access_token');
        await axios.post('/api/v1/presets/', {
            name: name,
            service_id: selectedService,
            country_id: document.getElementById('country-select').value,
            area_code: document.getElementById('area-code-select').value || null,
            carrier: document.getElementById('carrier-select').value || null
        }, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        document.getElementById('preset-name-input').value = '';
        loadUserPresets(); // Refresh list

    } catch (e) {
        alert(e.response?.data?.detail || "Failed to save preset");
    }
}

async function deletePreset(id, event) {
    event.stopPropagation();
    if (!confirm("Delete this preset?")) return;

    try {
        const token = localStorage.getItem('access_token');
        await axios.delete(`/api/v1/presets/${id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        loadUserPresets();
    } catch (e) {
        console.error("Failed to delete", e);
    }
}

async function applyPreset(serviceId, countryId, areaCode, carrier) {
    console.log("Applying preset:", serviceId, areaCode, carrier);

    const s = allServices.find(x => x.id === serviceId);
    if (s) {
        selectService(s.id, s.name, s.cost);
    } else {
        selectedService = serviceId;
        loadAreaCodes(serviceId);
        debouncedUpdatePricePreview();
    }

    setTimeout(() => {
        if (areaCode) document.getElementById('area-code-select').value = areaCode;
        if (carrier) document.getElementById('carrier-select').value = carrier;
        debouncedUpdatePricePreview();
    }, 1000);
}

// Area Code Live Validation Functions

let _jsCheckTimeout = null;
let _jsCheckAbort = null;

function clearAreaCode() {
    const acInput = document.getElementById('area-code-search-input');
    if (acInput) acInput.value = '';
    debouncedCheckAreaCode('');
    debouncedUpdatePricePreview();
}

function debouncedCheckAreaCode(value) {
    if(!value) {
        // Reset states
        const input = document.getElementById('area-code-search-input');
        if(input) {
            input.style.borderColor = '#e5e7eb';
            input.style.backgroundColor = '#fff';
        }
        if(_jsCheckTimeout) clearTimeout(_jsCheckTimeout);
        return;
    }
    
    const code = value.replace(/\D/g, '');
    if (code.length < 3) return;
    
    if (!selectedService) return;
    
    if (_jsCheckTimeout) clearTimeout(_jsCheckTimeout);
    if (_jsCheckAbort) _jsCheckAbort.abort();
    
    _jsCheckTimeout = setTimeout(() => {
        checkAreaCodeAPI(code);
    }, 500);
}

async function checkAreaCodeAPI(code) {
    const input = document.getElementById('area-code-search-input');
    const msg = document.getElementById('ac-message');
    const badge = document.getElementById('ac-status-badge');
    const btn = document.getElementById('purchase-btn');
    
    _jsCheckAbort = new AbortController();
    try {
        const res = await fetch(`/api/area-codes/check?service=${encodeURIComponent(selectedService)}&area_code=${encodeURIComponent(code)}`, {
            signal: _jsCheckAbort.signal
        });
        
        if (!res.ok) {
            const data = await res.json().catch(()=>({}));
            if(input) {
                input.style.borderColor = '#ef4444';
                input.style.backgroundColor = '#fff';
            }
            if(msg) {
                msg.textContent = data.error?.message || data.detail || 'Unsupported';
                msg.style.color = '#dc2626';
                msg.style.display = 'block';
            }
            if(btn) btn.disabled = true;
            return;
        }
        
        const data = await res.json();
        
        if (data.status === 'available') {
            if(input) {
                input.style.borderColor = '#10b981';
                input.style.backgroundColor = '#f0fdf4';
            }
            if(msg) {
                msg.textContent = data.message;
                msg.style.color = '#059669';
                msg.style.display = 'block';
            }
            if(btn) btn.disabled = false;
        } else if (data.status === 'unavailable') {
            if(input) {
                input.style.borderColor = '#f59e0b';
                input.style.backgroundColor = '#fffbeb';
            }
            if(msg) {
                msg.textContent = data.message;
                msg.style.color = '#92400e';
                msg.style.display = 'block';
            }
            if(btn) btn.disabled = true;
            
            // Note: If using `verification.js`, the UI needs manual alt rendering
            // We'll rely on the main `verify_modern.html` to be the primary interface,
            // but keep the logic here synced.
        } else {
            if(input) {
                input.style.borderColor = '#e5e7eb';
                input.style.backgroundColor = '#fff';
            }
            if(msg) {
                msg.textContent = data.message;
                msg.style.color = '#6b7280';
                msg.style.display = 'block';
            }
            if(btn) btn.disabled = false;
        }
        
    } catch (e) {
        if (e.name === 'AbortError') return;
        if(input) input.style.borderColor = '#e5e7eb';
        if(btn) btn.disabled = false;
    }
}

