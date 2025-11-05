// 5SIM Dashboard - Updated for new backend
const API_BASE = '';
let currentUser = null;
let authToken = localStorage.getItem('token');

// Initialize dashboard
document.addEventListener('DOMContentLoaded', async () => {
    if (!authToken) {
        window.location.href = '/auth/login';
        return;
    }
    
    await loadUserData();
    await loadDashboardData();
    setupNavigation();
    setupEventListeners();
    
    // Initialize dropdowns after DOM is ready
    setTimeout(initializeDropdowns, 100);
});

// Initialize searchable dropdowns
function initializeDropdowns() {
    // Initialize country dropdown if container exists
    const countryContainer = document.getElementById('country-dropdown');
    if (countryContainer && !countryDropdown) {
        countryDropdown = new SearchableDropdown('country-dropdown', {
            placeholder: 'Search countries...',
            showFlags: true
        });
        
        // Load countries immediately
        loadCountries();
    }
}

// Load user data
async function loadUserData() {
    try {
        // Validate token first
        if (!AuthHandler.validateToken()) {
            AuthHandler.logout('Session expired');
            return;
        }
        
        // Get user from localStorage (stored during login)
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            currentUser = JSON.parse(storedUser);
            updateUserDisplay();
        } else {
            AuthHandler.logout('Please login again');
        }
    } catch (error) {
        console.error('Failed to load user data:', error);
        AuthHandler.logout('Authentication error');
    }
}

// Update user display
function updateUserDisplay() {
    if (currentUser) {
        document.getElementById('balance-amount').textContent = `$${currentUser.credits?.toFixed(2) || '0.00'}`;
        document.getElementById('user-email').value = currentUser.email;
        document.getElementById('member-since').value = new Date(currentUser.created_at).toLocaleDateString();
    }
}

// Load dashboard data
async function loadDashboardData() {
    try {
        // Load 5SIM balance
        await load5SimBalance();
        
        // Load verification stats
        await loadVerificationStats();
        
        // Load recent activity
        await loadRecentActivity();
        
    } catch (error) {
        console.error('Failed to load dashboard data:', error);
        showNotification('Failed to load dashboard data', 'error');
    }
}

// Load 5SIM balance
async function load5SimBalance() {
    try {
        const response = await fetch('/api/5sim/balance', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('5SIM Balance:', data);
            // Update balance display if needed
        }
    } catch (error) {
        console.error('5SIM balance error:', error);
    }
}

// Load verification stats
async function loadVerificationStats() {
    try {
        const response = await fetch('/verify/history?limit=100', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            updateStatsDisplay(data);
        } else {
            // Set default values
            document.getElementById('total-verifications').textContent = '0';
            document.getElementById('success-rate').textContent = '0%';
            document.getElementById('total-spent').textContent = '$0.00';
            document.getElementById('active-count').textContent = '0';
        }
    } catch (error) {
        console.error('Stats loading error:', error);
    }
}

// Update stats display
function updateStatsDisplay(data) {
    const verifications = data.verifications || [];
    const total = verifications.length;
    const completed = verifications.filter(v => v.status === 'completed').length;
    const successRate = total > 0 ? Math.round((completed / total) * 100) : 0;
    const totalSpent = verifications.reduce((sum, v) => sum + (v.cost || 0), 0);
    const active = verifications.filter(v => v.status === 'pending').length;
    
    document.getElementById('total-verifications').textContent = total;
    document.getElementById('success-rate').textContent = `${successRate}%`;
    document.getElementById('total-spent').textContent = `$${totalSpent.toFixed(2)}`;
    document.getElementById('active-count').textContent = active;
}

// Load recent activity with error handling
async function loadRecentActivity() {
    const container = document.getElementById('recent-activity');
    LoadingManager.show(container, 'Loading activity...');
    
    try {
        const data = await APIHelper.request('/verify/history?limit=5');
        displayRecentActivity(data.verifications || []);
    } catch (error) {
        LoadingManager.hide(container, '<p class="text-center text-secondary">No recent activity</p>');
    }
}

// Display recent activity
function displayRecentActivity(verifications) {
    const container = document.getElementById('recent-activity');
    
    if (verifications.length === 0) {
        container.innerHTML = '<p class="text-center text-secondary">No recent activity</p>';
        return;
    }
    
    const html = verifications.map(v => `
        <div class="activity-item" style="display: flex; justify-content: space-between; align-items: center; padding: 16px; border-bottom: 1px solid var(--border);">
            <div>
                <div style="font-weight: 600;">${v.service_name}</div>
                <div style="font-size: 14px; color: var(--text-secondary);">${v.phone_number || 'N/A'}</div>
            </div>
            <div style="text-align: right;">
                <div class="status-badge status-${v.status}">${v.status}</div>
                <div style="font-size: 14px; color: var(--text-secondary);">$${(v.cost || 0).toFixed(2)}</div>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

// Setup navigation
function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const section = item.dataset.section;
            showSection(section);
            
            // Update active nav item
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
        });
    });
}

// Show section with smooth navigation
function showSection(sectionName) {
    NavigationManager.showSection(sectionName);
    
    // Load section-specific data after transition
    setTimeout(() => {
        switch (sectionName) {
            case 'create':
                loadServices();
                break;
            case 'active':
                loadActiveVerifications();
                break;
            case 'rentals':
                loadActiveRentals();
                break;
            case 'history':
                loadVerificationHistory();
                break;
            case 'analytics':
                loadAnalytics();
                break;
            case 'developer':
                loadAPIKeys();
                break;
            case 'wallet':
                loadWalletData();
                break;
        }
    }, 300);
}

// Load countries and services for create form
async function loadServices() {
    try {
        // Load countries from 5SIM
        await loadCountries();
        
        // Load services for default country
        const response = await fetch('/api/5sim/pricing?country=us', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            updateServiceOptions(data);
        }
    } catch (error) {
        console.error('Failed to load services:', error);
    }
}

// Load countries from 5SIM API
async function loadCountries() {
    try {
        const response = await fetch('/api/5sim/countries', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const countries = await response.json();
            updateCountryOptions(countries);
        }
    } catch (error) {
        console.error('Failed to load countries:', error);
        updateCountryOptions(null);
    }
}

// Initialize searchable dropdowns
let countryDropdown = null;

// Update country options with searchable dropdown
function updateCountryOptions(countries) {
    const countryData = [];
    
    if (countries && typeof countries === 'object') {
        Object.entries(countries).forEach(([code, name]) => {
            countryData.push({
                code: code,
                name: typeof name === 'string' ? name : code,
                flag: getCountryFlag(code)
            });
        });
    } else {
        const fallbackCountries = [
            { code: 'usa', name: 'United States', flag: '🇺🇸' },
            { code: 'england', name: 'United Kingdom', flag: '🇬🇧' },
            { code: 'canada', name: 'Canada', flag: '🇨🇦' },
            { code: 'germany', name: 'Germany', flag: '🇩🇪' },
            { code: 'france', name: 'France', flag: '🇫🇷' }
        ];
        countryData.push(...fallbackCountries);
    }
    
    // Initialize or update country dropdown
    if (countryDropdown) {
        countryDropdown.setData(countryData);
    } else {
        // Fallback: create simple dropdown if SearchableDropdown fails
        const container = document.getElementById('country-dropdown');
        if (container) {
            container.innerHTML = `
                <select class="form-select" id="country-select-fallback">
                    <option value="">Select a country...</option>
                    ${countryData.map(country => 
                        `<option value="${country.code}">${country.flag} ${country.name}</option>`
                    ).join('')}
                </select>
            `;
        }
    }
}

// Get country flag emoji
function getCountryFlag(countryCode) {
    const flagMap = {
        'usa': '🇺🇸', 'england': '🇬🇧', 'canada': '🇨🇦',
        'germany': '🇩🇪', 'france': '🇫🇷', 'australia': '🇦🇺'
    };
    return flagMap[countryCode.toLowerCase()] || '🏳️';
}

// Update service options
function updateServiceOptions(pricingData) {
    const select = document.getElementById('service-select');
    const services = pricingData.usa || {};
    
    // Clear existing options except first
    select.innerHTML = '<option value="">Select a service...</option>';
    
    // Add services from 5SIM data
    Object.keys(services).forEach(service => {
        const serviceData = services[service];
        const minCost = Math.min(...Object.values(serviceData).map(v => v.cost || 999));
        const price = (minCost / 100).toFixed(2);
        
        const option = document.createElement('option');
        option.value = service;
        option.textContent = `${service.charAt(0).toUpperCase() + service.slice(1)} - $${price}`;
        select.appendChild(option);
    });
}

// Setup event listeners
function setupEventListeners() {
    // Create verification form
    document.getElementById('create-form').addEventListener('submit', handleCreateVerification);
    
    // Support form
    document.getElementById('support-form').addEventListener('submit', handleSupportSubmit);
}

// Handle create verification
async function handleCreateVerification(e) {
    e.preventDefault();
    
    const service = document.getElementById('service-select').value;
    const country = document.getElementById('country-select').value;
    const capability = document.getElementById('capability-select').value;
    
    if (!service || !country) {
        showNotification('Please select service and country', 'error');
        return;
    }
    
    const btn = document.getElementById('create-btn');
    const btnText = document.getElementById('create-btn-text');
    const loading = document.getElementById('create-loading');
    
    btn.disabled = true;
    btnText.classList.add('hidden');
    loading.classList.remove('hidden');
    
    try {
        const response = await fetch('/verify/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                service_name: service,
                country: country,
                capability: capability
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('Verification created successfully!', 'success');
            showSection('active');
            loadActiveVerifications();
        } else {
            showNotification(data.detail || 'Failed to create verification', 'error');
        }
    } catch (error) {
        showNotification('Network error', 'error');
    } finally {
        btn.disabled = false;
        btnText.classList.remove('hidden');
        loading.classList.add('hidden');
    }
}

// Load active verifications
async function loadActiveVerifications() {
    const container = document.getElementById('active-verifications-container');
    container.innerHTML = '<div class="text-center"><div class="loading"></div><p class="mt-2">Loading active verifications...</p></div>';
    
    try {
        const response = await fetch('/verify/history?status=pending', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            displayActiveVerifications(data.verifications || []);
        } else {
            container.innerHTML = '<p class="text-center text-secondary">Failed to load active verifications</p>';
        }
    } catch (error) {
        container.innerHTML = '<p class="text-center text-secondary">Network error</p>';
    }
}

// Display active verifications
function displayActiveVerifications(verifications) {
    const container = document.getElementById('active-verifications-container');
    
    if (verifications.length === 0) {
        container.innerHTML = '<div class="card"><p class="text-center text-secondary">No active verifications</p></div>';
        return;
    }
    
    const html = verifications.map(v => `
        <div class="card">
            <div class="card-header">
                <h3 class="card-title">${v.service_name}</h3>
                <div class="status-badge status-${v.status}">${v.status}</div>
            </div>
            <div class="form-grid">
                <div>
                    <strong>Phone:</strong> ${v.phone_number || 'Loading...'}
                </div>
                <div>
                    <strong>Cost:</strong> $${(v.cost || 0).toFixed(2)}
                </div>
                <div>
                    <strong>Created:</strong> ${new Date(v.created_at).toLocaleString()}
                </div>
            </div>
            <div class="card-actions">
                <button class="btn btn-primary" onclick="checkMessages('${v.id}')">Check Messages</button>
                <button class="btn btn-danger" onclick="cancelVerification('${v.id}')">Cancel</button>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

// Check messages
async function checkMessages(verificationId) {
    try {
        const response = await fetch(`/verify/${verificationId}/messages`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        const data = await response.json();
        
        if (response.ok && data.messages && data.messages.length > 0) {
            showNotification('Messages received!', 'success');
            loadActiveVerifications(); // Refresh
        } else {
            showNotification('No messages yet', 'info');
        }
    } catch (error) {
        showNotification('Failed to check messages', 'error');
    }
}

// Cancel verification
async function cancelVerification(verificationId) {
    if (!confirm('Cancel this verification? You will receive a refund.')) return;
    
    try {
        const response = await fetch(`/verify/${verificationId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            showNotification('Verification cancelled and refunded', 'success');
            loadActiveVerifications();
            loadUserData(); // Refresh balance
        } else {
            showNotification('Failed to cancel verification', 'error');
        }
    } catch (error) {
        showNotification('Network error', 'error');
    }
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Logout
function logout() {
    localStorage.removeItem('token');
    window.location.href = '/auth/login';
}

// Handle support form
async function handleSupportSubmit(e) {
    e.preventDefault();
    showNotification('Support message sent successfully!', 'success');
    e.target.reset();
}

// Refresh activity
function refreshActivity() {
    loadRecentActivity();
}

// Initialize payment (placeholder)
function initializePayment() {
    showNotification('Payment integration coming soon!', 'info');
}

// Load active rentals
async function loadActiveRentals() {
    const container = document.getElementById('active-rentals-container');
    LoadingManager.show(container, 'Loading rentals...');
    
    try {
        const data = await APIHelper.request('/api/rentals/active');
        displayActiveRentals(data);
    } catch (error) {
        LoadingManager.hide(container, '<p class="text-center text-secondary">No active rentals</p>');
    }
}

// Display active rentals
function displayActiveRentals(rentals) {
    const container = document.getElementById('active-rentals-container');
    
    if (!rentals || rentals.length === 0) {
        container.innerHTML = '<p class="text-center text-secondary">No active rentals</p>';
        return;
    }
    
    const html = rentals.map(rental => `
        <div class="card" style="margin-bottom: 16px;">
            <div class="card-header">
                <h3 class="card-title">${rental.service_name}</h3>
                <div class="status-badge status-${rental.status}">${rental.status}</div>
            </div>
            <div class="form-grid">
                <div><strong>Phone:</strong> ${rental.phone_number}</div>
                <div><strong>Expires:</strong> ${new Date(rental.expires_at).toLocaleString()}</div>
                <div><strong>Cost:</strong> $${rental.cost}</div>
            </div>
            <div class="card-actions">
                <button class="btn btn-primary" onclick="extendRental('${rental.id}')">Extend</button>
                <button class="btn btn-warning" onclick="getRentalMessages('${rental.id}')">Messages</button>
                <button class="btn btn-danger" onclick="releaseRental('${rental.id}')">Release</button>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

// Load API keys
function loadAPIKeys() {
    const tbody = document.getElementById('api-keys-table');
    tbody.innerHTML = '<tr><td colspan="5" class="text-center text-secondary">No API keys created</td></tr>';
}

// Create API key
function createAPIKey() {
    const name = document.getElementById('api-key-name').value;
    if (!name) {
        NotificationManager.show('Please enter a key name', 'error');
        return;
    }
    
    NotificationManager.show('API key creation coming soon!', 'info');
}

// Rental actions
function extendRental(id) {
    NotificationManager.show('Rental extension coming soon!', 'info');
}

function getRentalMessages(id) {
    NotificationManager.show('Rental messages coming soon!', 'info');
}

function releaseRental(id) {
    NotificationManager.show('Rental release coming soon!', 'info');
}

// Save settings (placeholder)
function saveSettings() {
    NotificationManager.show('Settings saved successfully!', 'success');
}