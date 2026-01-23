
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
            document.getElementById('area-code-field-wrapper').style.display = 'block';
            document.getElementById('area-code-lock').style.display = 'none';
            await loadAreaCodes(); // Load area codes immediately for PAYG+ users
        }

        // Carrier (Pro+)
        if (currentRank >= 2) {
            document.getElementById('carrier-field-wrapper').style.display = 'block';
            document.getElementById('carrier-lock').style.display = 'none';
            await loadCarriers();
        }
    } catch (error) {
        console.warn('[Verify] Could not determine user tier:', error);
    }
}

async function loadCarriers() {
    const select = document.getElementById('carrier-select');
    
    try {
        // Show loading state
        select.innerHTML = '<option value="">Loading carriers...</option>';
        select.disabled = true;
        
        const token = localStorage.getItem('access_token');
        const res = await axios.get(`/api/verification/carriers/US`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        // Re-enable and populate
        select.disabled = false;
        select.innerHTML = '<option value="">Any Carrier</option>';
        
        if (res.data.carriers && res.data.carriers.length > 0) {
            res.data.carriers.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.id;
                
                // Add visual indicator based on success rate
                const icon = c.success_rate >= 90 ? '🟢' : 
                             c.success_rate >= 75 ? '🟡' : '🔴';
                
                // Format: "Verizon - 🟢 95.3% Success"
                opt.textContent = `${c.name} - ${icon} ${c.success_rate.toFixed(1)}% Success`;
                select.appendChild(opt);
            });
            console.log(`✅ Loaded ${res.data.carriers.length} carriers (source: ${res.data.source})`);
        }
    } catch (e) {
        console.error('[Verify] Failed to load carriers:', e);
        // Show error state with fallback
        select.disabled = false;
        select.innerHTML = '<option value="">Any Carrier (using fallback)</option>';
    }
}

async function loadAreaCodes(serviceId = null) {
    if ((TIER_RANK[userTier] || 0) < 1) return;

    const select = document.getElementById('area-code-select');
    
    try {
        // Show loading state
        select.innerHTML = '<option value="">Loading area codes...</option>';
        select.disabled = true;
        
        const token = localStorage.getItem('access_token');
        const res = await axios.get(`/api/verification/area-codes/US`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        allAreaCodes = res.data.area_codes;
        
        // Re-enable and populate
        select.disabled = false;
        select.innerHTML = '<option value="">Any Area Code</option>';
        
        if (allAreaCodes && allAreaCodes.length > 0) {
            allAreaCodes.forEach(ac => {
                const opt = document.createElement('option');
                opt.value = ac.area_code;
                
                // Add visual indicator if success rate available
                let displayText = `${ac.city}, ${ac.state} (${ac.area_code})`;
                if (ac.success_rate) {
                    const icon = ac.success_rate >= 90 ? '🟢' : 
                                 ac.success_rate >= 75 ? '🟡' : '🔴';
                    displayText = `${ac.city}, ${ac.state} (${ac.area_code}) - ${icon} ${ac.success_rate.toFixed(1)}%`;
                }
                
                opt.textContent = displayText;
                select.appendChild(opt);
            });
            console.log(`✅ Loaded ${allAreaCodes.length} area codes (source: ${res.data.source})`);
        }
    } catch (e) {
        console.error('[Verify] Failed to load area codes:', e);
        // Show error state with fallback
        select.disabled = false;
        select.innerHTML = '<option value="">Any Area Code (using fallback)</option>';
    }
}

async function loadServices() {
    console.log('Loading services for US...');
    try {
        const token = localStorage.getItem('access_token');
        const res = await axios.get(`/api/countries/US/services`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.data && res.data.services) {
            allServices = res.data.services;
            servicesLoaded = true;
            console.log(`✅ Loaded ${allServices.length} services for US from API`);
        }
    } catch (error) {
        console.error(`❌ Failed to load services for US from API:`, error);
        allServices = [
            { id: 'telegram', name: 'Telegram', cost: 0.50 },
            { id: 'whatsapp', name: 'WhatsApp', cost: 0.75 },
            { id: 'google', name: 'Google', cost: 0.50 },
            { id: 'facebook', name: 'Facebook', cost: 0.60 },
            { id: 'instagram', name: 'Instagram', cost: 0.65 },
            { id: 'twitter', name: 'Twitter', cost: 0.55 },
            { id: 'discord', name: 'Discord', cost: 0.45 },
            { id: 'tiktok', name: 'TikTok', cost: 0.70 }
        ];
        servicesLoaded = true;
        console.log(`⚠️ Using ${allServices.length} fallback US services`);
    }
}

function setupSearchListener() {
    const searchInput = document.getElementById('service-search');
    const dropdown = document.getElementById('service-dropdown');

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
        <div style="font-size: 12px; color: #6b7280; margin-top: 2px;">$${s.cost.toFixed(2)} per verification</div>
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
    document.getElementById('service-cost').textContent = `$${cost.toFixed(2)}`;
    document.getElementById('service-dropdown').style.display = 'none';
    document.getElementById('purchase-btn').disabled = false;
    document.getElementById('purchase-btn').textContent = 'Get SMS Code';
    console.log(`Selected: ${name} ($${cost})`);

    // Load area codes for selected service if user has access
    loadAreaCodes(id);

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
        const areaCode = document.getElementById('area-code-select').value;
        const carrier = document.getElementById('carrier-select').value;
        const token = localStorage.getItem('access_token');

        const params = new URLSearchParams({
            service: selectedService,
            country: 'US',
        });

        if (areaCode) params.append('area_code', areaCode);
        if (carrier) params.append('carrier', carrier);

        const res = await axios.get(`/api/verification/pricing?${params.toString()}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.data && res.data.total_price) {
            costDisplay.textContent = `$${res.data.total_price.toFixed(2)}`;
            console.log(`[Pricing] Base: $${res.data.provider_cost}, Total: $${res.data.total_price}`);
        }
    } catch (error) {
        console.error('[Pricing] Failed to update preview:', error);
    } finally {
        costDisplay.style.opacity = '1';
    }
}

async function purchaseVerification() {
    if (!selectedService) return;

    const btn = document.getElementById('purchase-btn');
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner-sm" style="border-color: rgba(255,255,255,0.3); border-top-color: white;"></div> Processing...';

    try {
        const areaCode = document.getElementById('area-code-select').value;
        const carrier = document.getElementById('carrier-select').value;
        const token = localStorage.getItem('access_token');

        const res = await axios.post('/api/v1/verify/create', {
            service_name: selectedService,
            country: 'US',
            capability: 'sms',
            area_code: areaCode || null,
            carrier: carrier || null,
            idempotency_key: crypto.randomUUID ? crypto.randomUUID() : Date.now().toString() + Math.random().toString()
        }, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.data && res.data.phone_number) {
            currentVerification = res.data;
            document.getElementById('phone-display').innerHTML = `
                <div style="display: flex; flex-direction: column; align-items: center; gap: 4px;">
                    <span style="font-size: 24px;">${res.data.phone_number}</span>
                    ${detectCarrier(res.data) ? `<span style="font-size: 11px; background: rgba(255,255,255,0.2); padding: 2px 8px; border-radius: 12px; font-weight: 500;">Please verify on 📶 ${detectCarrier(res.data)}</span>` : ''}
                </div>
            `;
            if (res.data.fallback_applied) {
                const existingAlert = document.querySelector('.fallback-alert');
                if (existingAlert) existingAlert.remove();

                const fallbackAlert = document.createElement('div');
                fallbackAlert.className = 'fallback-alert';
                fallbackAlert.style.cssText = 'background: #fffbeb; border: 1px solid #fcf6c2; color: #92400e; padding: 12px; border-radius: 8px; margin-bottom: 16px; font-size: 13px; display: flex; align-items:flex-start; gap: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);';
                fallbackAlert.innerHTML = `
                    <div style="font-size: 16px;">⚡</div>
                    <div>
                        <strong style="font-weight: 600; display: block; margin-bottom: 2px;">${i18n.t('verify.intelligent_fallback')}</strong>
                        ${i18n.t('verify.fallback_message')}
                    </div>
                `;
                const container = document.getElementById('reception-card').parentNode;
                container.insertBefore(fallbackAlert, document.getElementById('reception-card'));
            }

            document.getElementById('reception-card').style.display = 'block';
            startPolling(res.data.id);
            if (window.refreshBalance) window.refreshBalance();
        }
    } catch (error) {
        alert(error.response?.data?.detail || 'Purchase failed');
        btn.disabled = false;
        btn.textContent = 'Get SMS Code';
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
    // Updated waiting UI with Pulse Animation
    document.getElementById('status-text').innerHTML = `
    <div class="pulse-container">
        <div class="pulse-ring"></div>
        <div class="pulse-dot"></div>
    </div>
    <div style="font-weight:600; color:#2563eb;">Scanning Network...</div>
    <div id="timer-display" style="font-size:12px; color:#6b7280; margin-top:4px;">0s elapsed</div>
`;

    pollingInterval = setInterval(async () => {

        count++;
        try {
            // Update timer
            const timerEl = document.getElementById('timer-display');
            if (timerEl) timerEl.textContent = `${count * 5}s elapsed`;

            const token = localStorage.getItem('access_token');
            const res = await axios.get(`/api/verify/${id}/status`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (res.data.sms_code) {
                document.getElementById('code-display').textContent = res.data.sms_code;
                document.getElementById('status-text').textContent = 'SMS Received';
                document.getElementById('status-text').parentElement.style.background = '#d1fae5';
                document.getElementById('status-text').parentElement.style.borderColor = '#a7f3d0';
                document.getElementById('status-text').style.color = '#065f46';
                document.getElementById('code-display').style.color = '#059669';
                document.getElementById('copy-btn').style.display = 'block';

                // Play notification sound
                playNotificationSound();

                clearInterval(pollingInterval);
            } else if (count >= 60) {
                document.getElementById('status-text').textContent = 'Timeout - No SMS received';
                document.getElementById('status-text').parentElement.style.background = '#fee2e2';
                document.getElementById('status-text').parentElement.style.borderColor = '#fecaca';
                document.getElementById('status-text').style.color = '#991b1b';
                clearInterval(pollingInterval);
            }
        } catch (error) {
            if (count >= 60) clearInterval(pollingInterval);
        }
    }, 5000);
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
    document.getElementById('service-cost').textContent = '$0.00';
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
    document.getElementById('area-code-select').addEventListener('change', debouncedUpdatePricePreview);
    document.getElementById('carrier-select').addEventListener('change', debouncedUpdatePricePreview);

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

function detectCarrier(verificationData) {
    // Task 09: Carrier Mask Unveiling
    const requestedVars = document.getElementById('carrier-select');
    if (requestedVars && requestedVars.value) {
        const selectedOption = requestedVars.options[requestedVars.selectedIndex];
        return selectedOption.text.split('(')[0].trim();
    }
    return null; // Don't show if random/generic
}
