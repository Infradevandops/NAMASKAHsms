// Services Module - Enhanced with Error Handling and Fallback
let servicesData = null;
let searchDebounceTimer = null;
let loadingAttempts = 0;
const MAX_LOADING_ATTEMPTS = 3;

// Enhanced service loading with retry mechanism
async function loadServices() {
    if (servicesData) {
        renderServices();
        return;
    }
    
    loadingAttempts++;
    
    try {
        console.log(`🔄 Loading services (attempt ${loadingAttempts}/${MAX_LOADING_ATTEMPTS})...`);
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // Reduced timeout
        
        const res = await fetch(`${API_BASE}/services/list`, {
            signal: controller.signal,
            headers: {
                'Accept': 'application/json',
                'Cache-Control': 'no-cache'
            }
        });
        
        clearTimeout(timeoutId);
        
        if (!res.ok) {
            throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }
        
        const data = await res.json();
        
        // Validate response structure
        if (!data || !data.categories) {
            throw new Error('Invalid services data structure');
        }
        
        servicesData = data;
        renderServices();
        
        const total = Object.values(servicesData.categories).reduce((sum, arr) => sum + arr.length, 0) + (servicesData.uncategorized?.length || 0);
        console.log(`✅ ${total} services loaded successfully!`);
        
        if (typeof showNotification === 'function') {
            showNotification(`✅ ${total} services loaded!`, 'success');
        }
        
        // Reset attempts on success
        loadingAttempts = 0;
        
    } catch (err) {
        console.error('Failed to load services:', err);
        
        if (loadingAttempts < MAX_LOADING_ATTEMPTS) {
            console.log(`⏳ Retrying in 1 second... (${loadingAttempts}/${MAX_LOADING_ATTEMPTS})`);
            setTimeout(loadServices, 1000);
            return;
        }
        
        // Show error notification
        if (typeof showNotification === 'function') {
            showNotification('⚠️ Loading fallback services...', 'warning');
        }
        
        // Use fallback data immediately
        loadFallbackServices();
    }
}

// Fallback services data
function loadFallbackServices() {
    console.log('📦 Loading fallback services data...');
    
    servicesData = {
        categories: {
            "Social": [
                "telegram", "whatsapp", "discord", "instagram", "facebook", 
                "twitter", "snapchat", "tiktok", "reddit", "linkedin", "signal"
            ],
            "Finance": [
                "paypal", "cashapp", "venmo", "coinbase", "robinhood", "stripe", "square"
            ],
            "Shopping": [
                "amazon", "ebay", "etsy", "mercari", "poshmark", "depop"
            ],
            "Gaming": [
                "steam", "epic", "xbox", "playstation", "nintendo"
            ],
            "Other": [
                "google", "microsoft", "apple", "uber", "lyft", "airbnb"
            ]
        },
        uncategorized: [],
        tiers: {
            "tier1": { name: "High-Demand", price: 0.75, services: ["whatsapp", "telegram", "discord", "google"] },
            "tier2": { name: "Standard", price: 1.0, services: ["instagram", "facebook", "twitter", "tiktok"] },
            "tier3": { name: "Premium", price: 1.5, services: ["paypal"] },
            "tier4": { name: "Specialty", price: 2.0, services: [] }
        }
    };
    
    renderServices();
    
    if (typeof showNotification === 'function') {
        showNotification('📦 Loaded fallback services (limited set)', 'warning');
    }
}

function formatServiceName(service) {
    const special = {
        'twitter': 'X (Twitter)',
        'x': 'X (Twitter)',
        'whatsapp': 'WhatsApp',
        'instagram': 'Instagram',
        'facebook': 'Facebook',
        'telegram': 'Telegram',
        'discord': 'Discord',
        'tiktok': 'TikTok',
        'snapchat': 'Snapchat',
        'linkedin': 'LinkedIn',
        'youtube': 'YouTube',
        'paypal': 'PayPal',
        'cashapp': 'Cash App',
        'coinbase': 'Coinbase'
    };
    
    if (special[service.toLowerCase()]) {
        return special[service.toLowerCase()];
    }
    
    return service.charAt(0).toUpperCase() + service.slice(1);
}

function renderServices() {
    const container = document.getElementById('categories-container');
    
    if (!container) {
        console.error('❌ Categories container not found!');
        return;
    }
    
    if (!servicesData) {
        container.innerHTML = '<div style="text-align: center; padding: 20px; color: var(--text-secondary);">Loading services...</div>';
        return;
    }
    
    const search = document.getElementById('service-search')?.value?.toLowerCase() || '';
    const categoryFilter = document.getElementById('category-filter')?.value || '';
    let html = '';
    
    // Tier colors and badges with N coin pricing
    const tierInfo = {
        'tier1': { color: '#10b981', badge: 'HIGH-DEMAND', price: 'N0.75' },
        'tier2': { color: '#3b82f6', badge: 'STANDARD', price: 'N1.00' },
        'tier3': { color: '#f59e0b', badge: 'PREMIUM', price: 'N1.50' },
        'tier4': { color: '#ef4444', badge: 'SPECIALTY', price: 'N2.00' }
    };
    
    function getServiceTier(service) {
        if (!servicesData.tiers) return 'tier4';
        for (const [tierId, tierData] of Object.entries(servicesData.tiers)) {
            if (tierData.services && tierData.services.includes(service.toLowerCase())) {
                return tierId;
            }
        }
        return 'tier4';
    }
    
    const categoryOrder = ['Social', 'Messaging', 'Finance', 'Shopping', 'Gaming', 'Dating', 'Food', 'Crypto', 'Other'];
    
    categoryOrder.forEach(category => {
        // Skip if category filter is active and doesn't match
        if (categoryFilter && categoryFilter !== category) return;
        
        if (servicesData.categories && servicesData.categories[category]) {
            let services = servicesData.categories[category];
            if (search) {
                services = services.filter(s => s.toLowerCase().includes(search));
            }
            if (services.length > 0) {
                html += `<div style="min-width: 85px;">`;
                html += `<div style="font-weight: bold; font-size: 0.7rem; color: var(--accent); margin-bottom: 6px; border-bottom: 1px solid var(--accent); padding-bottom: 2px;">${category}</div>`;
                services.slice(0, 8).forEach(service => {
                    const tier = getServiceTier(service);
                    const tierData = tierInfo[tier];
                    const serviceName = formatServiceName(service);
                    const safeService = window.SecurityUtils ? window.SecurityUtils.sanitizeServiceName(service) : service.replace(/[^a-zA-Z0-9-_]/g, '');
                    const safeServiceName = window.SecurityUtils ? window.SecurityUtils.sanitizeHTML(serviceName) : serviceName;
                    
                    html += `<div data-service="${safeService}" class="service-item" style="font-size: 0.65rem; padding: 3px; cursor: pointer; border-radius: 3px; transition: all 0.2s; display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;" onmouseover="this.style.background='var(--accent)'; this.style.color='white'" onmouseout="this.style.background=''; this.style.color=''">
                        <span>${safeServiceName}</span>
                        <span style="font-size: 0.55rem; background: ${tierData.color}; color: white; padding: 1px 3px; border-radius: 2px; font-weight: bold;">${tierData.price}</span>
                    </div>`;
                });
                if (services.length > 8) {
                    html += `<div style="font-size: 0.6rem; color: var(--text-secondary); padding: 2px;">+${services.length - 8} more</div>`;
                }
                html += `</div>`;
            }
        }
    });
    
    container.innerHTML = html || '<div style="text-align: center; padding: 20px; color: var(--text-secondary);">No services found</div>';
}

async function selectService(service) {
    try {
        const serviceSelect = document.getElementById('service-select');
        if (serviceSelect) {
            serviceSelect.value = service;
        }
        
        // Get dynamic price for selected service (now always returns a price)
        const capability = document.querySelector('input[name="capability"]:checked')?.value || 'sms';
        const price = await getServicePrice(service, capability);
        const priceText = `N${price}`;
        
        const serviceInfo = document.getElementById('service-info');
        if (serviceInfo) {
            serviceInfo.innerHTML = `✅ Selected: <strong>${formatServiceName(service)}</strong> • ${capability === 'voice' ? '📞' : '📱'} ${capability.toUpperCase()} (${priceText})`;
            serviceInfo.style.color = '#10b981';
        }
        
        // Show capability selection and create button
        const capabilitySection = document.getElementById('capability-selection');
        const createBtn = document.getElementById('create-verification-btn');
        
        if (capabilitySection) capabilitySection.classList.remove('hidden');
        if (createBtn) createBtn.classList.remove('hidden');
        
        // Update visual selection
        document.querySelectorAll('#categories-container > div > div[onclick]').forEach(el => {
            el.style.fontWeight = 'normal';
        });
        
        console.log(`✅ Selected service: ${service}`);
        
    } catch (error) {
        console.error('Error selecting service:', error);
        if (typeof showNotification === 'function') {
            showNotification('⚠️ Error selecting service', 'error');
        }
    }
}

// Enhanced dynamic pricing function with fallback
async function getServicePrice(serviceName, capability = 'sms') {
    try {
        const headers = {
            'Accept': 'application/json'
        };
        
        if (window.token) {
            headers['Authorization'] = `Bearer ${window.token}`;
        }
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);
        
        const res = await (window.SecurityUtils ? 
            window.SecurityUtils.secureFetch(`${API_BASE}/services/price/${encodeURIComponent(serviceName)}`, {
                headers: headers,
                signal: controller.signal
            }) : 
            fetch(`${API_BASE}/services/price/${encodeURIComponent(serviceName)}`, {
                headers: headers,
                signal: controller.signal
            }));
        
        clearTimeout(timeoutId);
        
        if (res.ok) {
            const data = await res.json();
            return capability === 'voice' 
                ? (data.base_price + data.voice_premium).toFixed(2)
                : data.base_price.toFixed(2);
        }
    } catch (err) {
        console.error('Price fetch error:', err);
    }
    
    // Fallback pricing if API fails
    const fallbackPrices = {
        'whatsapp': 0.75, 'telegram': 0.75, 'discord': 0.75, 'google': 0.75,
        'instagram': 1.00, 'facebook': 1.00, 'twitter': 1.00, 'tiktok': 1.00,
        'paypal': 1.50, 'venmo': 1.50, 'cashapp': 1.50
    };
    
    const basePrice = fallbackPrices[serviceName.toLowerCase()] || 2.00;
    const voicePremium = 0.30;
    
    return capability === 'voice' 
        ? (basePrice + voicePremium).toFixed(2)
        : basePrice.toFixed(2);
}

// Modal functions
function showUnlistedModal() {
    const modal = document.getElementById('unlisted-modal');
    if (modal) {
        modal.classList.remove('hidden');
    }
}

function closeUnlistedModal() {
    const modal = document.getElementById('unlisted-modal');
    const input = document.getElementById('unlisted-service-name');
    
    if (modal) modal.classList.add('hidden');
    if (input) input.value = '';
}

function selectUnlistedService() {
    const input = document.getElementById('unlisted-service-name');
    const serviceName = input?.value?.trim()?.toLowerCase();
    
    if (!serviceName) {
        if (typeof showNotification === 'function') {
            showNotification('⚠️ Please enter a service name', 'error');
        }
        return;
    }
    
    closeUnlistedModal();
    selectService(serviceName);
}

function selectGeneralPurpose() {
    const input = document.getElementById('unlisted-service-name');
    const serviceName = input?.value?.trim() || 'general';
    closeUnlistedModal();
    selectService(serviceName);
}

// Search and filter functions
function filterServices() {
    const searchInput = document.getElementById('service-search');
    const searchTerm = searchInput?.value?.toLowerCase() || '';
    
    // Hide suggestions when searching
    const suggestions = document.getElementById('service-suggestions');
    if (searchTerm && suggestions) {
        suggestions.classList.add('hidden');
    } else {
        // Show suggestions if category is selected but no search
        const categoryFilter = document.getElementById('category-filter');
        const category = categoryFilter?.value;
        if (category && category !== '') {
            showCategoryServices(category);
        }
    }
    
    if (searchDebounceTimer) clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => renderServices(), 200);
}

function filterByCategory() {
    const categoryFilter = document.getElementById('category-filter');
    const category = categoryFilter?.value;
    
    // Show service suggestions for selected category
    if (category && category !== '') {
        showCategoryServices(category);
    } else {
        // Hide suggestions when showing all categories
        const suggestions = document.getElementById('service-suggestions');
        if (suggestions) suggestions.classList.add('hidden');
    }
    
    renderServices();
}

// Show service suggestions when category is selected
function showCategoryServices(category) {
    if (!servicesData || !servicesData.categories) return;
    
    const services = servicesData.categories[category] || [];
    const suggestionsContainer = document.getElementById('service-suggestions');
    const suggestionGrid = suggestionsContainer?.querySelector('.suggestion-grid');
    
    if (services.length > 0 && suggestionsContainer && suggestionGrid) {
        // Show top 8 popular services in this category
        const popularServices = services.slice(0, 8);
        suggestionGrid.innerHTML = popularServices.map(service => {
            const safeService = window.SecurityUtils ? window.SecurityUtils.sanitizeServiceName(service) : service.replace(/[^a-zA-Z0-9-_]/g, '');
            return `<button data-service="${safeService}" class="suggestion-btn" 
                     onclick="selectServiceFromSuggestion('${safeService}')" 
                     style="padding: 6px 12px; background: #667eea; color: white; border: none; border-radius: 16px; font-size: 11px; font-weight: 600; cursor: pointer; transition: all 0.2s;">
                ${window.SecurityUtils ? window.SecurityUtils.sanitizeHTML(formatServiceName(service)) : formatServiceName(service)}
            </button>`;
        }).join('');
        suggestionsContainer.classList.remove('hidden');
    } else if (suggestionsContainer) {
        suggestionsContainer.classList.add('hidden');
    }
}

// Select service from suggestion
function selectServiceFromSuggestion(serviceName) {
    const serviceSelect = document.getElementById('service-select');
    const suggestions = document.getElementById('service-suggestions');
    
    if (serviceSelect) serviceSelect.value = serviceName;
    if (suggestions) suggestions.classList.add('hidden');
    
    selectService(serviceName);
}

// Capability update function
async function updateCapability() {
    const capabilityInput = document.querySelector('input[name="capability"]:checked');
    const capability = capabilityInput?.value || 'sms';
    const info = document.getElementById('service-info');
    const serviceSelect = document.getElementById('service-select');
    const service = serviceSelect?.value;
    
    if (service && info) {
        const smsPrice = await getServicePrice(service, 'sms');
        const voicePrice = await getServicePrice(service, 'voice');
        
        // Update capability labels (now always have prices)
        const smsLabel = document.getElementById('sms-price');
        const voiceLabel = document.getElementById('voice-price');
        
        if (smsLabel) smsLabel.textContent = `N${smsPrice}`;
        if (voiceLabel) voiceLabel.textContent = `N${voicePrice}`;
        
        const currentPrice = capability === 'voice' ? voicePrice : smsPrice;
        const priceText = `N${currentPrice}`;
        info.innerHTML = `✅ Selected: <strong>${formatServiceName(service)}</strong> • ${capability === 'voice' ? '📞' : '📱'} ${capability.toUpperCase()} (${priceText})`;
        info.style.color = '#10b981';
    } else if (info) {
        // Reset to default prices
        const smsLabel = document.getElementById('sms-price');
        const voiceLabel = document.getElementById('voice-price');
        
        if (smsLabel) smsLabel.textContent = 'N1.00';
        if (voiceLabel) voiceLabel.textContent = 'N1.30';
        
        info.innerHTML = `⚡ Click a service to select • ${capability === 'voice' ? '📞' : '📱'} ${capability.toUpperCase()}`;
        info.style.color = '';
    }
}

function selectCapability(type) {
    const smsInput = document.querySelector('input[name="capability"][value="sms"]');
    const voiceInput = document.querySelector('input[name="capability"][value="voice"]');
    const smsLabel = document.getElementById('capability-sms-label');
    const voiceLabel = document.getElementById('capability-voice-label');
    
    if (smsInput) smsInput.checked = (type === 'sms');
    if (voiceInput) voiceInput.checked = (type === 'voice');
    
    if (smsLabel) smsLabel.style.borderColor = (type === 'sms') ? '#fbbf24' : 'transparent';
    if (voiceLabel) voiceLabel.style.borderColor = (type === 'voice') ? '#fbbf24' : 'transparent';
    
    updateCapability();
}

// Secure event delegation for service selection
function setupSecureEventHandlers() {
    const container = document.getElementById('categories-container');
    if (container) {
        container.addEventListener('click', (e) => {
            const serviceItem = e.target.closest('.service-item');
            if (serviceItem) {
                const service = serviceItem.dataset.service;
                if (service && window.SecurityUtils) {
                    const sanitizedService = window.SecurityUtils.sanitizeServiceName(service);
                    if (sanitizedService) {
                        selectService(sanitizedService);
                    }
                }
            }
        });
    }
    
    const suggestions = document.getElementById('service-suggestions');
    if (suggestions) {
        suggestions.addEventListener('click', (e) => {
            const suggestionBtn = e.target.closest('.suggestion-btn');
            if (suggestionBtn) {
                const service = suggestionBtn.dataset.service;
                if (service && window.SecurityUtils) {
                    const sanitizedService = window.SecurityUtils.sanitizeServiceName(service);
                    if (sanitizedService) {
                        selectServiceFromSuggestion(sanitizedService);
                    }
                }
            }
        });
    }
}

// Only load services after authentication
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Services module initialized');
    
    // Setup secure event handlers
    setupSecureEventHandlers();
    
    // Check if user is authenticated before loading services
    const token = localStorage.getItem('token');
    if (token) {
        loadFallbackServices();
        setTimeout(() => loadServices(), 100);
    } else {
        console.log('🔒 Services require authentication');
    }
});

// Function to load services after login
window.loadServicesAfterAuth = function() {
    loadFallbackServices();
    setTimeout(() => loadServices(), 100);
};

// Export functions for global access
window.loadServices = loadServices;
window.selectService = selectService;
window.getServicePrice = getServicePrice;
window.showUnlistedModal = showUnlistedModal;
window.closeUnlistedModal = closeUnlistedModal;
window.selectUnlistedService = selectUnlistedService;
window.selectGeneralPurpose = selectGeneralPurpose;
window.filterServices = filterServices;
window.filterByCategory = filterByCategory;
window.selectServiceFromSuggestion = selectServiceFromSuggestion;
window.updateCapability = updateCapability;
window.selectCapability = selectCapability;

console.log('✅ Enhanced Services module loaded with error handling and fallback');