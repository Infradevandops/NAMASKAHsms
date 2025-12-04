/**
 * Namaskah Dashboard - Main JavaScript
 * Single source of truth for dashboard functionality
 */
(function() {
    'use strict';

    // State
    const state = {
        user: null,
        balance: 0,
        currentView: 'home',
        verification: {
            step: 1,
            country: null,
            service: null,
            cost: 0,
            verificationId: null,
            pollingInterval: null,
            countries: [],
            services: {}
        }
    };

    // DOM Ready
    document.addEventListener('DOMContentLoaded', init);

    function init() {
        setupEventListeners();
        loadUserData();
        loadBalance();
        setupViewSwitching();
        hideModals();
    }

    // ==================== Event Listeners ====================
    function setupEventListeners() {
        // Sidebar toggle
        const sidebarToggle = document.getElementById('sidebar-toggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', toggleSidebar);
        }

        // User menu
        const userAvatarBtn = document.getElementById('user-avatar-btn');
        if (userAvatarBtn) {
            userAvatarBtn.addEventListener('click', toggleUserDropdown);
        }

        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            const dropdown = document.getElementById('user-dropdown');
            const avatarBtn = document.getElementById('user-avatar-btn');
            if (dropdown && !dropdown.contains(e.target) && !avatarBtn.contains(e.target)) {
                dropdown.classList.remove('show');
            }
        });

        // Logout buttons
        document.getElementById('logout-btn')?.addEventListener('click', handleLogout);
        document.getElementById('dropdown-logout')?.addEventListener('click', handleLogout);

        // Verification modal
        document.getElementById('new-verification-btn')?.addEventListener('click', openVerificationModal);
        document.getElementById('quick-verification-btn')?.addEventListener('click', openVerificationModal);
        document.getElementById('verification-close-btn')?.addEventListener('click', closeVerificationModal);
        document.getElementById('step1-cancel')?.addEventListener('click', closeVerificationModal);
        document.getElementById('step1-next')?.addEventListener('click', () => goToVerificationStep(2));
        document.getElementById('step2-back')?.addEventListener('click', () => goToVerificationStep(1));
        document.getElementById('step2-next')?.addEventListener('click', () => goToVerificationStep(3));
        document.getElementById('step3-back')?.addEventListener('click', () => goToVerificationStep(2));
        document.getElementById('step3-purchase')?.addEventListener('click', purchaseVerification);
        document.getElementById('step4-close')?.addEventListener('click', closeVerificationModal);
        document.getElementById('step4-copy')?.addEventListener('click', () => copyToClipboard('code-value'));
        document.getElementById('copy-phone-btn')?.addEventListener('click', () => copyToClipboard('phone-value'));
        document.getElementById('copy-code-btn')?.addEventListener('click', () => copyToClipboard('code-value'));

        // Country/Service selects
        document.getElementById('country-select')?.addEventListener('change', onCountryChange);
        document.getElementById('service-select')?.addEventListener('change', onServiceChange);

        // Credits modal
        document.getElementById('quick-credits-btn')?.addEventListener('click', openCreditsModal);
        document.getElementById('add-credits-btn')?.addEventListener('click', openCreditsModal);
        document.getElementById('credits-close-btn')?.addEventListener('click', closeCreditsModal);
        document.getElementById('credits-cancel-btn')?.addEventListener('click', closeCreditsModal);
        document.getElementById('credits-proceed-btn')?.addEventListener('click', proceedToPayment);

        // Package selection
        document.querySelectorAll('.package').forEach(pkg => {
            pkg.addEventListener('click', function() {
                selectPackage(this);
            });
        });

        // Close modals on overlay click
        document.querySelectorAll('.modal-overlay').forEach(overlay => {
            overlay.addEventListener('click', function(e) {
                if (e.target === this) {
                    hideModals();
                }
            });
        });

        // Close modals on Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                hideModals();
            }
        });

        // Refresh balance on window focus
        window.addEventListener('focus', loadBalance);
    }

    // ==================== Sidebar ====================
    function toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.classList.toggle('collapsed');
            localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
        }
    }

    // ==================== User Menu ====================
    function toggleUserDropdown() {
        const dropdown = document.getElementById('user-dropdown');
        if (dropdown) {
            dropdown.classList.toggle('show');
        }
    }

    async function loadUserData() {
        try {
            const response = await fetch('/api/user/profile');
            if (!response.ok) return;
            const user = await response.json();
            state.user = user;
            
            const emailEl = document.getElementById('dropdown-email');
            const initialsEl = document.getElementById('user-initials');
            
            if (emailEl) emailEl.textContent = user.email || 'User';
            if (initialsEl) {
                const initials = (user.email || 'U').charAt(0).toUpperCase();
                initialsEl.textContent = initials;
            }
        } catch (error) {
            console.error('Failed to load user data:', error);
        }
    }

    async function handleLogout(e) {
        e.preventDefault();
        if (!confirm('Are you sure you want to logout?')) return;
        
        try {
            await fetch('/api/auth/logout', { method: 'POST' });
        } catch (error) {
            console.error('Logout error:', error);
        }
        localStorage.clear();
        window.location.href = '/auth/login';
    }

    // ==================== Balance ====================
    async function loadBalance() {
        try {
            const response = await fetch('/api/user/balance', {
                headers: { 'Cache-Control': 'no-cache' }
            });
            if (!response.ok) return;
            const data = await response.json();
            state.balance = parseFloat(data.credits) || 0;
            updateBalanceDisplay();
        } catch (error) {
            console.error('Failed to load balance:', error);
        }
    }

    function updateBalanceDisplay() {
        const formatted = '$' + state.balance.toFixed(2);
        const elements = [
            document.getElementById('header-balance'),
            document.getElementById('stat-balance'),
            document.getElementById('wallet-balance')
        ];
        elements.forEach(el => {
            if (el) el.textContent = formatted;
        });
    }

    // Global sync function
    window.syncBalance = loadBalance;

    // ==================== View Switching ====================
    function setupViewSwitching() {
        const urlParams = new URLSearchParams(window.location.search);
        const view = urlParams.get('view') || 'home';
        switchView(view);

        document.querySelectorAll('.nav-item[data-view]').forEach(item => {
            item.addEventListener('click', function(e) {
                e.preventDefault();
                const targetView = this.getAttribute('data-view');
                switchView(targetView);
                updateURL(targetView);
            });
        });

        // Restore sidebar state
        if (localStorage.getItem('sidebarCollapsed') === 'true') {
            document.getElementById('sidebar')?.classList.add('collapsed');
        }
    }

    function switchView(viewName) {
        state.currentView = viewName;
        
        // Hide all views
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        
        // Show target view
        const targetView = document.getElementById(`${viewName}-view`);
        if (targetView) {
            targetView.classList.add('active');
        }

        // Update nav active state
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('data-view') === viewName) {
                item.classList.add('active');
            }
        });

        // Update page title
        const titles = {
            home: 'Dashboard',
            rentals: 'Rentals',
            wallet: 'Wallet',
            profile: 'Profile',
            settings: 'Settings'
        };
        const titleEl = document.getElementById('page-title');
        if (titleEl) titleEl.textContent = titles[viewName] || 'Dashboard';

        // Load view-specific content
        loadViewContent(viewName);
    }

    function updateURL(view) {
        const url = view === 'home' ? '/dashboard' : `/dashboard?view=${view}`;
        window.history.pushState({ view }, '', url);
    }

    window.addEventListener('popstate', function(e) {
        const view = e.state?.view || 'home';
        switchView(view);
    });

    // ==================== View Content Loading ====================
    function loadViewContent(viewName) {
        switch (viewName) {
            case 'home':
                loadDashboardStats();
                loadRecentActivity();
                break;
            case 'rentals':
                loadRentals();
                break;
            case 'wallet':
                loadTransactions();
                break;
            case 'profile':
                loadProfile();
                break;
            case 'settings':
                loadSettings();
                break;
        }
    }

    async function loadDashboardStats() {
        try {
            const response = await fetch('/api/dashboard/stats');
            if (!response.ok) return;
            const data = await response.json();
            
            const statsMap = {
                'stat-verifications': data.total_verifications || 0,
                'stat-success-rate': (data.success_rate || 0) + '%',
                'stat-rentals': data.active_rentals || 0
            };
            
            Object.entries(statsMap).forEach(([id, value]) => {
                const el = document.getElementById(id);
                if (el) el.textContent = value;
            });
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    }

    async function loadRecentActivity() {
        const container = document.getElementById('recent-activity');
        if (!container) return;

        try {
            const response = await fetch('/api/dashboard/activity/recent');
            if (!response.ok) throw new Error('Failed to load');
            const data = await response.json();
            
            if (!data.activities || data.activities.length === 0) {
                container.innerHTML = '<div class="empty-state"><i class="ph ph-clock"></i><p>No recent activity</p></div>';
                return;
            }

            container.innerHTML = data.activities.map(activity => `
                <div class="activity-item">
                    <div class="activity-info">
                        <div class="activity-service">${escapeHtml(activity.service_name || 'Unknown')}</div>
                        <div class="activity-details">${escapeHtml(activity.phone_number || '')} • $${(activity.cost || 0).toFixed(2)}</div>
                    </div>
                    <span class="activity-status status-${activity.status || 'pending'}">${activity.status || 'pending'}</span>
                </div>
            `).join('');
        } catch (error) {
            container.innerHTML = '<div class="empty-state"><p>Unable to load activity</p></div>';
        }
    }

    async function loadRentals() {
        const container = document.getElementById('rentals-list');
        if (!container) return;

        try {
            const response = await fetch('/api/rentals/active');
            if (!response.ok) throw new Error('Failed to load');
            const data = await response.json();
            
            if (!data.rentals || data.rentals.length === 0) {
                container.innerHTML = '<div class="empty-state"><i class="ph ph-phone"></i><p>No active rentals</p><button class="btn btn-primary btn-sm" onclick="openRentalModal()">Get a Rental</button></div>';
                return;
            }

            container.innerHTML = data.rentals.map(rental => `
                <div class="activity-item">
                    <div class="activity-info">
                        <div class="activity-service">${escapeHtml(rental.phone_number)}</div>
                        <div class="activity-details">${escapeHtml(rental.service)} • Expires: ${formatDate(rental.expires_at)}</div>
                    </div>
                    <span class="activity-status status-${rental.status}">${rental.status}</span>
                </div>
            `).join('');
        } catch (error) {
            container.innerHTML = '<div class="empty-state"><p>Unable to load rentals</p></div>';
        }
    }

    async function loadTransactions() {
        const container = document.getElementById('transactions-list');
        if (!container) return;

        try {
            const response = await fetch('/api/billing/transactions?limit=20');
            if (!response.ok) throw new Error('Failed to load');
            const data = await response.json();
            
            if (!data.transactions || data.transactions.length === 0) {
                container.innerHTML = '<div class="empty-state"><i class="ph ph-receipt"></i><p>No transactions yet</p></div>';
                return;
            }

            container.innerHTML = data.transactions.map(t => `
                <div class="activity-item">
                    <div class="activity-info">
                        <div class="activity-service">${escapeHtml(t.type || t.description)}</div>
                        <div class="activity-details">${formatDate(t.created_at)}</div>
                    </div>
                    <span class="transaction-amount ${t.amount >= 0 ? 'positive' : 'negative'}">
                        ${t.amount >= 0 ? '+' : ''}$${Math.abs(t.amount).toFixed(2)}
                    </span>
                </div>
            `).join('');
        } catch (error) {
            container.innerHTML = '<div class="empty-state"><p>Unable to load transactions</p></div>';
        }
    }

    async function loadProfile() {
        const container = document.getElementById('profile-form-container');
        if (!container) return;

        try {
            const response = await fetch('/api/user/profile');
            if (!response.ok) throw new Error('Failed to load');
            const user = await response.json();
            
            container.innerHTML = `
                <form id="profile-form">
                    <div class="form-group">
                        <label for="profile-email">Email</label>
                        <input type="email" id="profile-email" value="${escapeHtml(user.email || '')}" disabled>
                    </div>
                    <div class="form-group">
                        <label for="profile-name">Full Name</label>
                        <input type="text" id="profile-name" value="${escapeHtml(user.name || '')}" placeholder="Your name">
                    </div>
                    <div class="form-group">
                        <label for="profile-phone">Phone</label>
                        <input type="text" id="profile-phone" value="${escapeHtml(user.phone || '')}" placeholder="Your phone">
                    </div>
                    <div class="form-group">
                        <label for="profile-country">Country</label>
                        <input type="text" id="profile-country" value="${escapeHtml(user.country || '')}" placeholder="Your country">
                    </div>
                    <div class="form-actions">
                        <button type="submit" class="btn btn-primary">Save Changes</button>
                        <button type="button" class="btn btn-secondary" onclick="loadProfile()">Cancel</button>
                    </div>
                </form>
            `;

            document.getElementById('profile-form').addEventListener('submit', saveProfile);
        } catch (error) {
            container.innerHTML = '<div class="empty-state"><p>Unable to load profile</p></div>';
        }
    }

    async function saveProfile(e) {
        e.preventDefault();
        
        const data = {
            name: document.getElementById('profile-name').value,
            phone: document.getElementById('profile-phone').value,
            country: document.getElementById('profile-country').value
        };

        try {
            const response = await fetch('/api/user/profile', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                showToast('Profile updated successfully', 'success');
            } else {
                showToast('Failed to update profile', 'error');
            }
        } catch (error) {
            showToast('Error updating profile', 'error');
        }
    }

    function loadSettings() {
        const container = document.getElementById('settings-form-container');
        if (!container) return;

        container.innerHTML = `
            <div class="settings-section">
                <h3>Notifications</h3>
                <label class="toggle-label">
                    <input type="checkbox" id="email-notifications" checked>
                    <span>Email Notifications</span>
                </label>
                <label class="toggle-label">
                    <input type="checkbox" id="sms-notifications" checked>
                    <span>SMS Notifications</span>
                </label>
            </div>
            <div class="settings-section">
                <h3>Security</h3>
                <button class="btn btn-secondary btn-block" onclick="changePassword()">Change Password</button>
            </div>
            <div class="settings-section">
                <h3>Data</h3>
                <button class="btn btn-secondary btn-block" onclick="exportData()">Export My Data</button>
            </div>
        `;
    }

    window.changePassword = function() {
        const newPassword = prompt('Enter new password (min 8 characters):');
        if (!newPassword) return;
        if (newPassword.length < 8) {
            showToast('Password must be at least 8 characters', 'error');
            return;
        }

        fetch('/api/user/change-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password: newPassword })
        }).then(r => {
            if (r.ok) showToast('Password changed successfully', 'success');
            else showToast('Failed to change password', 'error');
        }).catch(() => showToast('Error changing password', 'error'));
    };

    window.exportData = function() {
        fetch('/api/gdpr/export')
            .then(r => r.blob())
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'my-data.json';
                a.click();
                window.URL.revokeObjectURL(url);
            })
            .catch(() => showToast('Failed to export data', 'error'));
    };

    // ==================== Verification Modal ====================
    function openVerificationModal() {
        const modal = document.getElementById('verification-modal');
        if (modal) {
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
            resetVerificationState();
            loadCountries();
            goToVerificationStep(1);
        }
    }

    function closeVerificationModal() {
        const modal = document.getElementById('verification-modal');
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = '';
        }
        
        if (state.verification.pollingInterval) {
            clearInterval(state.verification.pollingInterval);
            state.verification.pollingInterval = null;
        }
    }

    function resetVerificationState() {
        state.verification.step = 1;
        state.verification.country = null;
        state.verification.service = null;
        state.verification.cost = 0;
        state.verification.verificationId = null;
        
        document.getElementById('country-select').value = '';
        document.getElementById('service-select').innerHTML = '<option value="">-- Select Service --</option>';
        document.getElementById('service-price').style.display = 'none';
        document.getElementById('sms-code-container').style.display = 'none';
        document.getElementById('polling-status').style.display = 'flex';
        document.getElementById('step4-copy').style.display = 'none';
        document.getElementById('insufficient-warning').style.display = 'none';
    }

    async function loadCountries() {
        try {
            const response = await fetch('/api/countries/');
            const data = await response.json();
            state.verification.countries = data.countries || [];
            
            const select = document.getElementById('country-select');
            select.innerHTML = '<option value="">-- Select Country --</option>';
            
            state.verification.countries.forEach(country => {
                const option = document.createElement('option');
                option.value = country.code;
                option.textContent = `${country.name} (${country.code})`;
                select.appendChild(option);
            });
        } catch (error) {
            console.error('Failed to load countries:', error);
            showToast('Failed to load countries', 'error');
        }
    }

    async function onCountryChange() {
        const country = document.getElementById('country-select').value;
        state.verification.country = country;
        
        const serviceSelect = document.getElementById('service-select');
        serviceSelect.innerHTML = '<option value="">-- Select Service --</option>';
        document.getElementById('service-price').style.display = 'none';
        
        if (!country) return;

        try {
            const response = await fetch(`/api/countries/${country}/services`);
            const data = await response.json();
            state.verification.services[country] = data.services || [];
            
            state.verification.services[country].forEach(service => {
                const option = document.createElement('option');
                option.value = service.name;
                option.textContent = `${service.name} - $${(service.cost || 0.50).toFixed(2)}`;
                select.appendChild(option);
            });
        } catch (error) {
            console.error('Failed to load services:', error);
        }
    }

    function onServiceChange() {
        const service = document.getElementById('service-select').value;
        state.verification.service = service;
        
        if (service && state.verification.country) {
            const services = state.verification.services[state.verification.country] || [];
            const serviceData = services.find(s => s.name === service);
            if (serviceData) {
                state.verification.cost = serviceData.cost || 0.50;
                document.getElementById('price-value').textContent = '$' + state.verification.cost.toFixed(2);
                document.getElementById('service-price').style.display = 'block';
            }
        }
    }

    function goToVerificationStep(step) {
        // Validation
        if (step === 2 && !state.verification.country) {
            showToast('Please select a country', 'warning');
            return;
        }
        if (step === 3 && !state.verification.service) {
            showToast('Please select a service', 'warning');
            return;
        }

        state.verification.step = step;

        // Update progress indicators
        document.querySelectorAll('.progress-step').forEach(el => {
            const s = parseInt(el.dataset.step);
            el.classList.remove('active', 'completed');
            if (s < step) el.classList.add('completed');
            if (s === step) el.classList.add('active');
        });

        // Show correct step content
        document.querySelectorAll('.verification-step').forEach(el => {
            el.classList.remove('active');
        });
        const stepEl = document.querySelector(`.verification-step[data-step="${step}"]`);
        if (stepEl) stepEl.classList.add('active');

        // Step 3: Update confirmation
        if (step === 3) {
            const countryOption = document.querySelector(`#country-select option[value="${state.verification.country}"]`);
            document.getElementById('confirm-country').textContent = countryOption?.textContent || state.verification.country;
            document.getElementById('confirm-service').textContent = state.verification.service;
            document.getElementById('confirm-cost').textContent = '$' + state.verification.cost.toFixed(2);
            document.getElementById('confirm-balance').textContent = '$' + state.balance.toFixed(2);
            
            // Check insufficient balance
            const warning = document.getElementById('insufficient-warning');
            const purchaseBtn = document.getElementById('step3-purchase');
            if (state.balance < state.verification.cost) {
                warning.style.display = 'flex';
                purchaseBtn.disabled = true;
            } else {
                warning.style.display = 'none';
                purchaseBtn.disabled = false;
            }
        }
    }

    async function purchaseVerification() {
        const btn = document.getElementById('step3-purchase');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-sm"></span> Processing...';

        try {
            const response = await fetch('/api/verify/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    country: state.verification.country,
                    service_name: state.verification.service,
                    capability: 'sms'
                })
            });

            const data = await response.json();

            if (response.status === 402) {
                showToast('Insufficient credits. Please add credits.', 'error');
                return;
            }
            if (response.status === 503) {
                showToast('Service temporarily unavailable', 'error');
                return;
            }
            if (!response.ok) {
                showToast(data.detail || 'Purchase failed', 'error');
                return;
            }

            state.verification.verificationId = data.verification_id || data.id;
            document.getElementById('phone-value').textContent = data.phone_number;
            
            goToVerificationStep(4);
            startSMSPolling();
            loadBalance();
            
            showToast('Verification started!', 'success');
        } catch (error) {
            showToast('Network error: ' + error.message, 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Purchase Now';
        }
    }

    function startSMSPolling() {
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/verify/${state.verification.verificationId}/status`);
                const data = await response.json();

                if (data.sms_code) {
                    clearInterval(pollInterval);
                    state.verification.pollingInterval = null;
                    
                    document.getElementById('code-value').textContent = data.sms_code;
                    document.getElementById('sms-text').textContent = data.sms_text || '';
                    document.getElementById('sms-code-container').style.display = 'block';
                    document.getElementById('polling-status').style.display = 'none';
                    document.getElementById('step4-copy').style.display = 'block';
                    
                    showToast('SMS code received!', 'success');
                }
            } catch (error) {
                console.error('Polling error:', error);
            }
        }, 3000);

        state.verification.pollingInterval = pollInterval;

        // Stop after 5 minutes
        setTimeout(() => {
            if (state.verification.pollingInterval) {
                clearInterval(state.verification.pollingInterval);
                state.verification.pollingInterval = null;
                showToast('SMS polling timed out', 'warning');
            }
        }, 5 * 60 * 1000);
    }

    // ==================== Credits Modal ====================
    function openCreditsModal() {
        const modal = document.getElementById('credits-modal');
        if (modal) {
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
            document.getElementById('credit-amount').value = '';
            document.querySelectorAll('.package').forEach(p => p.classList.remove('selected'));
        }
    }

    function closeCreditsModal() {
        const modal = document.getElementById('credits-modal');
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = '';
        }
    }

    function selectPackage(element) {
        const amount = parseFloat(element.dataset.amount);
        const bonus = parseFloat(element.dataset.bonus);
        const total = amount + bonus;
        
        document.getElementById('credit-amount').value = total.toFixed(2);
        document.querySelectorAll('.package').forEach(p => p.classList.remove('selected'));
        element.classList.add('selected');
    }

    async function proceedToPayment() {
        const amount = parseFloat(document.getElementById('credit-amount').value);
        
        if (!amount || amount <= 0) {
            showToast('Please enter a valid amount', 'warning');
            return;
        }

        const btn = document.getElementById('credits-proceed-btn');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-sm"></span> Processing...';

        try {
            const response = await fetch('/api/billing/add-credits', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ amount: amount })
            });

            const data = await response.json();
            
            if (response.ok) {
                showToast(`Credits added! New balance: $${data.new_balance.toFixed(2)}`, 'success');
                closeCreditsModal();
                loadBalance();
                if (state.currentView === 'wallet') {
                    loadTransactions();
                }
            } else {
                showToast(data.detail || 'Failed to add credits', 'error');
            }
        } catch (error) {
            showToast('Error: ' + error.message, 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Proceed to Payment';
        }
    }

    // ==================== Modals Utility ====================
    function hideModals() {
        document.querySelectorAll('.modal-overlay').forEach(modal => {
            modal.classList.remove('show');
        });
        document.body.style.overflow = '';
        
        if (state.verification.pollingInterval) {
            clearInterval(state.verification.pollingInterval);
            state.verification.pollingInterval = null;
        }
    }

    // ==================== Utilities ====================
    function copyToClipboard(elementId) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        const text = element.textContent;
        navigator.clipboard.writeText(text).then(() => {
            showToast('Copied to clipboard!', 'success');
        }).catch(() => {
            showToast('Failed to copy', 'error');
        });
    }

    function showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <i class="ph ph-${type === 'success' ? 'check-circle' : type === 'error' ? 'x-circle' : type === 'warning' ? 'warning' : 'info'}"></i>
            <span>${escapeHtml(message)}</span>
        `;
        
        container.appendChild(toast);
        
        setTimeout(() => toast.classList.add('show'), 10);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function formatDate(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    // ==================== Global Exports ====================
    window.openVerificationModal = openVerificationModal;
    window.closeVerificationModal = closeVerificationModal;
    window.openCreditsModal = openCreditsModal;
    window.closeCreditsModal = closeCreditsModal;
    window.openRentalModal = function() { showToast('Rental feature coming soon', 'info'); };

})();
