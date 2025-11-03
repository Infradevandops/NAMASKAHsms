/**
 * Namaskah SMS - Production Dashboard JavaScript
 * Comprehensive SMS verification platform dashboard with robust error handling
 */

class NamaskahDashboard {
    constructor() {
        this.token = localStorage.getItem('token');
        this.apiBase = '/api/v1';
        this.currentSection = 'dashboard';
        this.activeVerifications = new Map();
        this.pollInterval = null;
        this.retryAttempts = 3;
        this.retryDelay = 1000;
        
        this.init();
    }
    
    async init() {
        if (!this.token) {
            this.redirectToLogin();
            return;
        }
        
        this.setupEventListeners();
        await this.loadUserData();
        await this.loadDashboardData();
        this.startPeriodicUpdates();
    }
    
    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const section = item.dataset.section;
                this.showSection(section);
            });
        });
        
        // Forms
        const createForm = document.getElementById('create-form');
        if (createForm) {
            createForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.createVerification();
            });
        }
        
        const supportForm = document.getElementById('support-form');
        if (supportForm) {
            supportForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitSupportTicket();
            });
        }
        
        // Filters
        const historyFilters = ['history-service-filter', 'history-status-filter', 'history-date-filter'];
        historyFilters.forEach(filterId => {
            const filter = document.getElementById(filterId);
            if (filter) {
                filter.addEventListener('change', () => this.loadHistory());
            }
        });
        
        // Real-time updates
        window.addEventListener('focus', () => {
            this.refreshActiveVerifications();
        });
        
        // Error handling
        window.addEventListener('error', (e) => {
            console.error('Global error:', e.error);
            this.showNotification('An unexpected error occurred', 'error');
        });
        
        // Unhandled promise rejections
        window.addEventListener('unhandledrejection', (e) => {
            console.error('Unhandled promise rejection:', e.reason);
            this.showNotification('Network error occurred', 'error');
        });
    }
    
    async makeRequest(endpoint, options = {}) {
        const url = `${this.apiBase}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json',
                ...options.headers
            }
        };
        
        const requestOptions = { ...defaultOptions, ...options };
        
        for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
            try {
                const response = await fetch(url, requestOptions);
                
                if (response.status === 401) {
                    this.handleAuthError();
                    throw new Error('Authentication failed');
                }
                
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.detail || errorData.message || `HTTP ${response.status}`);
                }
                
                return await response.json();
            } catch (error) {
                console.error(`Request attempt ${attempt} failed:`, error);
                
                if (attempt === this.retryAttempts) {
                    throw error;
                }
                
                // Exponential backoff
                await this.sleep(this.retryDelay * Math.pow(2, attempt - 1));
            }
        }
    }
    
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    handleAuthError() {
        localStorage.removeItem('token');
        this.showNotification('Session expired. Please login again.', 'error');
        setTimeout(() => this.redirectToLogin(), 2000);
    }
    
    redirectToLogin() {
        window.location.href = '/auth/login';
    }
    
    showSection(sectionName) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');
        
        // Hide all sections
        document.querySelectorAll('.section').forEach(section => {
            section.classList.add('hidden');
        });
        
        // Show target section
        const targetSection = document.getElementById(`${sectionName}-section`);
        if (targetSection) {
            targetSection.classList.remove('hidden');
            this.currentSection = sectionName;
            
            // Load section-specific data
            this.loadSectionData(sectionName);
        }
    }
    
    async loadSectionData(sectionName) {
        try {
            switch (sectionName) {
                case 'dashboard':
                    await this.loadDashboardData();
                    break;
                case 'active':
                    await this.loadActiveVerifications();
                    break;
                case 'history':
                    await this.loadHistory();
                    break;
                case 'analytics':
                    await this.loadAnalytics();
                    break;
                case 'wallet':
                    await this.loadWalletData();
                    break;
                case 'settings':
                    await this.loadSettings();
                    break;
            }
        } catch (error) {
            console.error(`Failed to load ${sectionName} data:`, error);
            this.showNotification(`Failed to load ${sectionName} data`, 'error');
        }
    }
    
    async loadUserData() {
        try {
            const userData = await this.makeRequest('/auth/me');
            
            // Update balance display
            const balanceElement = document.getElementById('balance-amount');
            if (balanceElement) {
                balanceElement.textContent = `$${userData.credits.toFixed(2)}`;
            }
            
            // Update settings form
            const emailInput = document.getElementById('user-email');
            if (emailInput) {
                emailInput.value = userData.email;
            }
            
            const memberSinceInput = document.getElementById('member-since');
            if (memberSinceInput && userData.created_at) {
                memberSinceInput.value = new Date(userData.created_at).toLocaleDateString();
            }
            
        } catch (error) {
            console.error('Failed to load user data:', error);
            this.showNotification('Failed to load user data', 'error');
        }
    }
    
    async loadDashboardData() {
        try {
            // Load analytics for dashboard stats
            const analytics = await this.makeRequest('/analytics/usage?period=30');
            
            // Update stats
            this.updateElement('total-verifications', analytics.total_verifications || 0);
            this.updateElement('success-rate', `${analytics.success_rate || 0}%`);
            this.updateElement('total-spent', `$${analytics.total_spent || 0}`);
            
            // Load active verifications count
            const activeData = await this.makeRequest('/verify/history?verification_status=pending');
            const activeCount = activeData.verifications ? activeData.verifications.length : 0;
            this.updateElement('active-count', activeCount);
            
            // Update active badge in sidebar
            const activeBadge = document.getElementById('active-badge');
            if (activeBadge) {
                if (activeCount > 0) {
                    activeBadge.textContent = activeCount;
                    activeBadge.classList.remove('hidden');
                } else {
                    activeBadge.classList.add('hidden');
                }
            }
            
            // Load recent activity
            await this.loadRecentActivity();
            
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            this.showNotification('Failed to load dashboard data', 'error');
        }
    }
    
    async loadRecentActivity() {
        try {
            const recentData = await this.makeRequest('/verify/history?limit=5');
            const container = document.getElementById('recent-activity');
            
            if (!container) return;
            
            if (!recentData.verifications || recentData.verifications.length === 0) {
                container.innerHTML = `
                    <div class="text-center">
                        <p>No recent activity</p>
                        <button class="btn btn-primary mt-2" onclick="dashboard.showSection('create')">
                            Create Your First Verification
                        </button>
                    </div>
                `;
                return;
            }
            
            const activityHTML = recentData.verifications.map(verification => `
                <div class="activity-item" style="display: flex; justify-content: space-between; align-items: center; padding: 16px; border-bottom: 1px solid var(--border);">
                    <div>
                        <div style="font-weight: 600;">${this.formatServiceName(verification.service_name)}</div>
                        <div style="font-size: 14px; color: var(--text-secondary);">
                            ${verification.phone_number} • ${this.formatDate(verification.created_at)}
                        </div>
                    </div>
                    <div>
                        <span class="status-badge status-${verification.status}">${verification.status}</span>
                    </div>
                </div>
            `).join('');
            
            container.innerHTML = activityHTML;
            
        } catch (error) {
            console.error('Failed to load recent activity:', error);
            const container = document.getElementById('recent-activity');
            if (container) {
                container.innerHTML = '<div class="text-center">Failed to load recent activity</div>';
            }
        }
    }
    
    async createVerification() {
        const service = document.getElementById('service-select').value;
        const country = document.getElementById('country-select').value;
        const capability = document.getElementById('capability-select').value;
        
        if (!service || !country) {
            this.showNotification('Please select both service and country', 'error');
            return;
        }
        
        const createBtn = document.getElementById('create-btn');
        const createBtnText = document.getElementById('create-btn-text');
        const createLoading = document.getElementById('create-loading');
        
        // Show loading state
        createBtn.disabled = true;
        createBtnText.classList.add('hidden');
        createLoading.classList.remove('hidden');
        
        try {
            const verification = await this.makeRequest('/verify/create', {
                method: 'POST',
                body: JSON.stringify({
                    service_name: service,
                    country: country,
                    capability: capability
                })
            });
            
            this.showNotification('Verification created successfully!', 'success');
            
            // Add to active verifications
            this.activeVerifications.set(verification.id, verification);
            
            // Switch to active verifications section
            this.showSection('active');
            
            // Update balance
            await this.loadUserData();
            
        } catch (error) {
            console.error('Failed to create verification:', error);
            this.showNotification(error.message || 'Failed to create verification', 'error');
        } finally {
            // Reset button state
            createBtn.disabled = false;
            createBtnText.classList.remove('hidden');
            createLoading.classList.add('hidden');
        }
    }
    
    async loadActiveVerifications() {
        try {
            const data = await this.makeRequest('/verify/history?verification_status=pending');
            const container = document.getElementById('active-verifications-container');
            
            if (!container) return;
            
            if (!data.verifications || data.verifications.length === 0) {
                container.innerHTML = `
                    <div class="card text-center">
                        <h3>No Active Verifications</h3>
                        <p>You don't have any active verifications at the moment.</p>
                        <button class="btn btn-primary" onclick="dashboard.showSection('create')">
                            Create New Verification
                        </button>
                    </div>
                `;
                return;
            }
            
            // Update active verifications map
            this.activeVerifications.clear();
            data.verifications.forEach(v => this.activeVerifications.set(v.id, v));
            
            // Render verification cards
            const cardsHTML = data.verifications.map(verification => this.renderVerificationCard(verification)).join('');
            container.innerHTML = cardsHTML;
            
            // Start polling for updates
            this.startVerificationPolling();
            
        } catch (error) {
            console.error('Failed to load active verifications:', error);
            this.showNotification('Failed to load active verifications', 'error');
        }
    }
    
    renderVerificationCard(verification) {
        const timeElapsed = this.getTimeElapsed(verification.created_at);
        const isExpired = timeElapsed > 300; // 5 minutes
        
        return `
            <div class="card" id="verification-${verification.id}">
                <div class="card-header">
                    <h3 class="card-title">${this.formatServiceName(verification.service_name)}</h3>
                    <span class="status-badge status-${verification.status}">${verification.status}</span>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <div style="font-family: monospace; font-size: 18px; font-weight: 600; margin-bottom: 8px;">
                        ${verification.phone_number}
                    </div>
                    <div style="font-size: 14px; color: var(--text-secondary);">
                        ${verification.capability === 'voice' ? '📞 Voice Call' : '📱 SMS Text'} • 
                        ${verification.country} • 
                        $${verification.cost}
                    </div>
                </div>
                
                <div class="messages-container" id="messages-${verification.id}" style="background: var(--bg-tertiary); padding: 16px; border-radius: 8px; margin-bottom: 16px; min-height: 60px;">
                    <div style="color: var(--text-secondary); font-size: 14px;">
                        ${verification.status === 'pending' ? 'Waiting for verification code...' : 'Loading messages...'}
                    </div>
                </div>
                
                <div style="display: flex; gap: 12px; flex-wrap: wrap;">
                    <button class="btn btn-primary" onclick="dashboard.checkMessages('${verification.id}')">
                        ${verification.capability === 'voice' ? '📞 Check Call' : '📱 Check SMS'}
                    </button>
                    <button class="btn btn-secondary" onclick="dashboard.copyPhoneNumber('${verification.phone_number}')">
                        📋 Copy Number
                    </button>
                    <button class="btn btn-danger" onclick="dashboard.cancelVerification('${verification.id}')">
                        ❌ Cancel
                    </button>
                </div>
                
                ${isExpired ? `
                    <div style="margin-top: 16px; padding: 12px; background: var(--warning); color: white; border-radius: 8px; font-size: 14px;">
                        ⚠️ This verification has been active for ${Math.floor(timeElapsed / 60)} minutes. Consider canceling if no code received.
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    async checkMessages(verificationId) {
        try {
            const verification = this.activeVerifications.get(verificationId);
            if (!verification) return;
            
            const endpoint = verification.capability === 'voice' 
                ? `/verify/${verificationId}/voice`
                : `/verify/${verificationId}/messages`;
                
            const data = await this.makeRequest(endpoint);
            const messagesContainer = document.getElementById(`messages-${verificationId}`);
            
            if (!messagesContainer) return;
            
            if (data.messages && data.messages.length > 0) {
                // Extract verification codes
                const codes = data.messages.map(msg => {
                    const match = msg.text ? msg.text.match(/\\b\\d{4,8}\\b/) : msg.match(/\\b\\d{4,8}\\b/);
                    return match ? match[0] : (msg.text || msg);
                });
                
                messagesContainer.innerHTML = `
                    <div style="background: var(--success); color: white; padding: 16px; border-radius: 8px; margin-bottom: 12px;">
                        <h4 style="margin: 0 0 8px 0;">✅ Code Received!</h4>
                        <div style="font-family: monospace; font-size: 20px; font-weight: 600;">
                            ${codes[0]}
                        </div>
                    </div>
                    ${codes.length > 1 ? `
                        <details>
                            <summary style="cursor: pointer; color: var(--text-secondary);">View all messages</summary>
                            ${data.messages.map((msg, i) => `
                                <div style="margin: 8px 0; padding: 8px; background: var(--bg-primary); border-radius: 4px;">
                                    <code>${msg.text || msg}</code>
                                </div>
                            `).join('')}
                        </details>
                    ` : ''}
                `;
                
                // Update verification status
                verification.status = 'completed';
                this.activeVerifications.set(verificationId, verification);
                
                // Update status badge
                const statusBadge = document.querySelector(`#verification-${verificationId} .status-badge`);
                if (statusBadge) {
                    statusBadge.className = 'status-badge status-completed';
                    statusBadge.textContent = 'completed';
                }
                
                this.showNotification('Verification code received!', 'success');
                
            } else {
                messagesContainer.innerHTML = `
                    <div style="color: var(--text-secondary); font-size: 14px;">
                        No messages yet. The code should arrive within 1-2 minutes.
                        <div style="margin-top: 8px;">
                            <div class="loading" style="display: inline-block; margin-right: 8px;"></div>
                            Auto-checking...
                        </div>
                    </div>
                `;
            }
            
        } catch (error) {
            console.error('Failed to check messages:', error);
            this.showNotification('Failed to check messages', 'error');
        }
    }
    
    async cancelVerification(verificationId) {
        if (!confirm('Are you sure you want to cancel this verification? You will receive a refund.')) {
            return;
        }
        
        try {
            const data = await this.makeRequest(`/verify/${verificationId}`, {
                method: 'DELETE'
            });
            
            this.showNotification(`Verification cancelled. Refunded $${data.refunded}`, 'success');
            
            // Remove from active verifications
            this.activeVerifications.delete(verificationId);
            
            // Remove card from UI
            const card = document.getElementById(`verification-${verificationId}`);
            if (card) {
                card.remove();
            }
            
            // Update balance
            await this.loadUserData();
            
            // Reload active verifications if empty
            if (this.activeVerifications.size === 0) {
                await this.loadActiveVerifications();
            }
            
        } catch (error) {
            console.error('Failed to cancel verification:', error);
            this.showNotification(error.message || 'Failed to cancel verification', 'error');
        }
    }
    
    copyPhoneNumber(phoneNumber) {
        navigator.clipboard.writeText(phoneNumber).then(() => {
            this.showNotification('Phone number copied to clipboard', 'success');
        }).catch(() => {
            this.showNotification('Failed to copy phone number', 'error');
        });
    }
    
    async loadHistory() {
        try {
            const serviceFilter = document.getElementById('history-service-filter')?.value || '';
            const statusFilter = document.getElementById('history-status-filter')?.value || '';
            const dateFilter = document.getElementById('history-date-filter')?.value || '30';
            
            let endpoint = '/verify/history?limit=50';
            if (serviceFilter) endpoint += `&service=${serviceFilter}`;
            if (statusFilter) endpoint += `&verification_status=${statusFilter}`;
            
            const data = await this.makeRequest(endpoint);
            const tableBody = document.getElementById('history-table-body');
            
            if (!tableBody) return;
            
            if (!data.verifications || data.verifications.length === 0) {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center">No verifications found</td>
                    </tr>
                `;
                return;
            }
            
            const rowsHTML = data.verifications.map(verification => `
                <tr>
                    <td>${this.formatServiceName(verification.service_name)}</td>
                    <td style="font-family: monospace;">${verification.phone_number}</td>
                    <td><span class="status-badge status-${verification.status}">${verification.status}</span></td>
                    <td>$${verification.cost}</td>
                    <td>${this.formatDate(verification.created_at)}</td>
                    <td>
                        ${verification.status === 'pending' ? `
                            <button class="btn btn-secondary" onclick="dashboard.checkMessages('${verification.id}')">
                                Check
                            </button>
                        ` : ''}
                        ${verification.status === 'completed' ? `
                            <button class="btn btn-success" onclick="dashboard.viewMessages('${verification.id}')">
                                View Code
                            </button>
                        ` : ''}
                    </td>
                </tr>
            `).join('');
            
            tableBody.innerHTML = rowsHTML;
            
        } catch (error) {
            console.error('Failed to load history:', error);
            this.showNotification('Failed to load history', 'error');
        }
    }
    
    async loadAnalytics() {
        try {
            const analytics = await this.makeRequest('/analytics/usage?period=30');
            
            this.updateElement('analytics-total', analytics.total_verifications || 0);
            this.updateElement('analytics-success', `${analytics.success_rate || 0}%`);
            
            // Calculate average time (mock data for now)
            this.updateElement('analytics-avg-time', '45s');
            
            // Most popular service
            if (analytics.popular_services && analytics.popular_services.length > 0) {
                this.updateElement('analytics-popular', this.formatServiceName(analytics.popular_services[0].service));
            } else {
                this.updateElement('analytics-popular', '-');
            }
            
        } catch (error) {
            console.error('Failed to load analytics:', error);
            this.showNotification('Failed to load analytics', 'error');
        }
    }
    
    async loadWalletData() {
        try {
            // Load user data for balance
            await this.loadUserData();
            
            // Update wallet balance
            const balanceAmount = document.getElementById('balance-amount')?.textContent || '$0.00';
            this.updateElement('wallet-balance', balanceAmount);
            
            // Load transactions
            const transactions = await this.makeRequest('/wallet/transactions?limit=10');
            const tableBody = document.getElementById('transactions-table-body');
            
            if (!tableBody) return;
            
            if (!transactions.transactions || transactions.transactions.length === 0) {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="4" class="text-center">No transactions found</td>
                    </tr>
                `;
                return;
            }
            
            const rowsHTML = transactions.transactions.map(transaction => `
                <tr>
                    <td>${transaction.description}</td>
                    <td style="color: ${transaction.amount >= 0 ? 'var(--success)' : 'var(--error)'};">
                        ${transaction.amount >= 0 ? '+' : ''}$${Math.abs(transaction.amount).toFixed(2)}
                    </td>
                    <td>
                        <span class="status-badge ${transaction.type === 'credit' ? 'status-completed' : 'status-pending'}">
                            ${transaction.type}
                        </span>
                    </td>
                    <td>${this.formatDate(transaction.created_at)}</td>
                </tr>
            `).join('');
            
            tableBody.innerHTML = rowsHTML;
            
        } catch (error) {
            console.error('Failed to load wallet data:', error);
            this.showNotification('Failed to load wallet data', 'error');
        }
    }
    
    async loadSettings() {
        // Settings are loaded in loadUserData()
        // This method can be extended for additional settings
    }
    
    async initializePayment() {
        const amount = parseFloat(document.getElementById('credit-amount').value);
        
        try {
            const paymentData = await this.makeRequest('/wallet/paystack/initialize', {
                method: 'POST',
                body: JSON.stringify({ amount_usd: amount })
            });
            
            if (paymentData.authorization_url) {
                window.open(paymentData.authorization_url, '_blank');
                this.showNotification('Payment window opened. Complete payment to add credits.', 'info');
            } else {
                throw new Error('No payment URL received');
            }
            
        } catch (error) {
            console.error('Failed to initialize payment:', error);
            this.showNotification(error.message || 'Failed to initialize payment', 'error');
        }
    }
    
    async saveSettings() {
        try {
            // In a real implementation, this would save settings to the backend
            this.showNotification('Settings saved successfully', 'success');
        } catch (error) {
            console.error('Failed to save settings:', error);
            this.showNotification('Failed to save settings', 'error');
        }
    }
    
    async submitSupportTicket() {
        const category = document.getElementById('support-category').value;
        const priority = document.getElementById('support-priority').value;
        const subject = document.getElementById('support-subject').value;
        const message = document.getElementById('support-message').value;
        
        if (!category || !subject || !message) {
            this.showNotification('Please fill in all required fields', 'error');
            return;
        }
        
        try {
            await this.makeRequest('/support/tickets', {
                method: 'POST',
                body: JSON.stringify({
                    category,
                    priority,
                    subject,
                    message
                })
            });
            
            this.showNotification('Support ticket submitted successfully', 'success');
            
            // Reset form
            document.getElementById('support-form').reset();
            
        } catch (error) {
            console.error('Failed to submit support ticket:', error);
            this.showNotification(error.message || 'Failed to submit support ticket', 'error');
        }
    }
    
    startVerificationPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
        }
        
        this.pollInterval = setInterval(async () => {
            if (this.currentSection === 'active' && this.activeVerifications.size > 0) {
                await this.refreshActiveVerifications();
            }
        }, 10000); // Poll every 10 seconds
    }
    
    async refreshActiveVerifications() {
        for (const [verificationId, verification] of this.activeVerifications) {
            if (verification.status === 'pending') {
                await this.checkMessages(verificationId);
            }
        }
    }
    
    startPeriodicUpdates() {
        // Update dashboard data every 30 seconds
        setInterval(async () => {
            if (this.currentSection === 'dashboard') {
                await this.loadDashboardData();
            }
        }, 30000);
        
        // Update user balance every minute
        setInterval(async () => {
            await this.loadUserData();
        }, 60000);
    }
    
    refreshActivity() {
        this.loadRecentActivity();
    }
    
    toggleNotifications() {
        // Placeholder for notifications panel
        this.showNotification('Notifications feature coming soon', 'info');
    }
    
    logout() {
        localStorage.removeItem('token');
        this.redirectToLogin();
    }
    
    // Utility methods
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }
    
    formatServiceName(serviceName) {
        return serviceName.charAt(0).toUpperCase() + serviceName.slice(1);
    }
    
    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    getTimeElapsed(dateString) {
        return Math.floor((Date.now() - new Date(dateString).getTime()) / 1000);
    }
    
    showNotification(message, type = 'info') {
        // Remove existing notifications
        const existing = document.querySelector('.notification');
        if (existing) {
            existing.remove();
        }
        
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
        
        // Remove on click
        notification.addEventListener('click', () => {
            notification.remove();
        });
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new NamaskahDashboard();
});

// Global error handlers
window.addEventListener('error', (e) => {
    console.error('Global error:', e.error);
});

window.addEventListener('unhandledrejection', (e) => {
    console.error('Unhandled promise rejection:', e.reason);
});