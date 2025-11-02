// Enhanced Verification Flow - Fixed Version
class VerificationFlow {
    constructor() {
        this.currentVerificationId = null;
        this.pollInterval = null;
        this.token = localStorage.getItem('token');
        this.apiBase = '';
        this.init();
    }

    init() {
        if (!this.token) {
            window.location.href = '/auth/login';
            return;
        }
        this.loadServices();
        this.loadCountries();
        this.loadUserBalance();
        this.loadActiveVerifications();
    }

    async loadServices() {
        try {
            const response = await this.secureFetch('/verify/services');
            const data = await response.json();
            this.populateServiceSelect(data.services || []);
        } catch (error) {
            console.error('Failed to load services:', error);
            this.populateServiceSelect(this.getFallbackServices());
        }
    }

    async loadCountries() {
        try {
            const response = await this.secureFetch('/countries/popular');
            const data = await response.json();
            this.populateCountrySelect(data.countries || []);
        } catch (error) {
            console.error('Failed to load countries:', error);
            this.populateCountrySelect(this.getFallbackCountries());
        }
    }

    async loadUserBalance() {
        try {
            const response = await this.secureFetch('/auth/me');
            const user = await response.json();
            const creditsEl = document.getElementById('user-credits');
            if (creditsEl) {
                creditsEl.textContent = user.credits.toFixed(2);
            }
        } catch (error) {
            console.error('Failed to load balance:', error);
        }
    }

    async loadActiveVerifications() {
        try {
            const response = await this.secureFetch('/verify/history?verification_status=pending');
            const data = await response.json();
            this.displayActiveVerifications(data.verifications || []);
        } catch (error) {
            console.error('Failed to load verifications:', error);
            this.displayVerificationError();
        }
    }

    async createVerification() {
        const service = document.getElementById('service-select')?.value;
        const country = document.getElementById('country-select')?.value;
        const capability = document.getElementById('capability-select')?.value || 'sms';

        if (!service || !country) {
            this.showNotification('Please select service and country', 'error');
            return;
        }

        this.setLoading(true);

        try {
            const response = await this.secureFetch('/verify/create', {
                method: 'POST',
                body: JSON.stringify({
                    service_name: service,
                    country: country,
                    capability: capability
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.currentVerificationId = data.id;
                this.displayVerification(data);
                this.showNotification('Verification created successfully!', 'success');
                this.startPolling();
                this.loadUserBalance();
            } else {
                this.handleCreateError(response.status, data);
            }
        } catch (error) {
            console.error('Create verification error:', error);
            this.showNotification('Network error. Please try again.', 'error');
        } finally {
            this.setLoading(false);
        }
    }

    async checkMessages(verificationId) {
        try {
            const response = await this.secureFetch(`/verify/${verificationId}/messages`);
            const data = await response.json();

            if (response.ok && data.messages?.length > 0) {
                this.displayMessages(data.messages);
                this.stopPolling();
                return true;
            }
            return false;
        } catch (error) {
            console.error('Check messages error:', error);
            return false;
        }
    }

    async cancelVerification(verificationId) {
        if (!confirm('Cancel this verification and get refund?')) return;

        try {
            const response = await this.secureFetch(`/verify/${verificationId}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (response.ok) {
                this.showNotification(`Cancelled! Refunded $${data.refunded.toFixed(2)}`, 'success');
                this.loadActiveVerifications();
                this.loadUserBalance();
            } else {
                throw new Error(data.detail || 'Cancellation failed');
            }
        } catch (error) {
            console.error('Cancel error:', error);
            this.showNotification(error.message, 'error');
        }
    }

    // Secure fetch with CSRF protection
    async secureFetch(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        };

        return fetch(url, { ...defaultOptions, ...options });
    }

    populateServiceSelect(services) {
        const select = document.getElementById('service-select');
        if (!select) return;

        select.innerHTML = '<option value="">Select a service...</option>';
        
        services.forEach(service => {
            const option = document.createElement('option');
            option.value = service.name;
            option.textContent = `${service.name.charAt(0).toUpperCase() + service.name.slice(1)} - $${service.price}`;
            select.appendChild(option);
        });
    }

    populateCountrySelect(countries) {
        const select = document.getElementById('country-select');
        if (!select) return;

        select.innerHTML = '<option value="">Select a country...</option>';
        
        countries.forEach(country => {
            const option = document.createElement('option');
            option.value = country.code;
            option.textContent = `${country.name} ${country.voice_supported ? '(Voice Available)' : '(SMS Only)'}`;
            select.appendChild(option);
        });
    }

    displayVerification(data) {
        const phoneEl = document.getElementById('phone-number');
        const serviceEl = document.getElementById('service-name');
        const statusEl = document.getElementById('status');

        if (phoneEl) phoneEl.textContent = data.phone_number || 'Loading...';
        if (serviceEl) serviceEl.textContent = data.service_name;
        if (statusEl) {
            statusEl.textContent = data.status;
            statusEl.className = `status-badge status-${data.status}`;
        }

        const detailsEl = document.getElementById('verification-details');
        if (detailsEl) detailsEl.classList.remove('hidden');
    }

    displayActiveVerifications(verifications) {
        const container = document.getElementById('active-verifications');
        if (!container) return;

        if (verifications.length === 0) {
            container.innerHTML = '<p>No active verifications</p>';
            return;
        }

        container.innerHTML = verifications.map(v => `
            <div class="verification-card" data-id="${v.id}">
                <div class="verification-header">
                    <span class="service-name">${this.escapeHtml(v.service_name)}</span>
                    <span class="status-badge status-${v.status}">${v.status}</span>
                </div>
                <div class="phone-number">${this.escapeHtml(v.phone_number || 'Pending...')}</div>
                <div class="card-actions">
                    <button onclick="verificationFlow.checkMessages('${v.id}')" class="btn btn-secondary">Check Messages</button>
                    <button onclick="verificationFlow.cancelVerification('${v.id}')" class="btn btn-danger">Cancel</button>
                </div>
            </div>
        `).join('');
    }

    displayMessages(messages) {
        const container = document.getElementById('messages-section');
        if (!container) return;

        const messagesHtml = messages.map(msg => {
            const messageText = typeof msg === 'object' ? msg.text : msg;
            const code = messageText.match(/\b\d{4,8}\b/)?.[0] || messageText;
            return `
                <div class="message">
                    <div class="message-code">${this.escapeHtml(code)}</div>
                    <div class="message-full">${this.escapeHtml(messageText)}</div>
                    <button onclick="navigator.clipboard.writeText('${this.escapeHtml(code)}')" class="btn btn-secondary btn-sm">Copy</button>
                </div>
            `;
        }).join('');

        container.innerHTML = `
            <h3>Verification Code Received</h3>
            <div class="messages-list">${messagesHtml}</div>
        `;
        container.classList.remove('hidden');
    }

    displayVerificationError() {
        const container = document.getElementById('active-verifications');
        if (container) {
            container.innerHTML = `
                <div class="error-state">
                    <p>Failed to load verifications</p>
                    <button onclick="verificationFlow.loadActiveVerifications()" class="btn btn-secondary">Retry</button>
                </div>
            `;
        }
    }

    handleCreateError(status, data) {
        let message = 'Failed to create verification';
        
        switch (status) {
            case 402:
                message = `Insufficient credits. ${data.detail}`;
                break;
            case 401:
                message = 'Session expired. Please login again';
                setTimeout(() => this.logout(), 2000);
                break;
            case 503:
                message = 'Service temporarily unavailable';
                break;
            default:
                message = data.detail || message;
        }
        
        this.showNotification(message, 'error');
    }

    startPolling() {
        if (this.pollInterval) clearInterval(this.pollInterval);
        
        this.pollInterval = setInterval(async () => {
            if (this.currentVerificationId) {
                const hasMessages = await this.checkMessages(this.currentVerificationId);
                if (hasMessages) {
                    this.stopPolling();
                }
            }
        }, 10000);
    }

    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }

    setLoading(loading) {
        const btn = document.getElementById('create-btn');
        const text = document.getElementById('create-btn-text');
        const spinner = document.getElementById('create-loading');

        if (btn) btn.disabled = loading;
        if (text) text.style.display = loading ? 'none' : 'inline';
        if (spinner) spinner.style.display = loading ? 'inline-block' : 'none';
    }

    showNotification(message, type = 'info') {
        const container = document.getElementById('notification-container') || document.body;
        
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        container.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    logout() {
        localStorage.removeItem('token');
        window.location.href = '/auth/login';
    }

    getFallbackServices() {
        return [
            {name: 'telegram', price: 0.75},
            {name: 'whatsapp', price: 0.75},
            {name: 'discord', price: 0.75},
            {name: 'google', price: 0.75}
        ];
    }

    getFallbackCountries() {
        return [
            {code: 'US', name: 'United States', voice_supported: true},
            {code: 'GB', name: 'United Kingdom', voice_supported: true},
            {code: 'CA', name: 'Canada', voice_supported: true}
        ];
    }
}

// Initialize verification flow
let verificationFlow;
document.addEventListener('DOMContentLoaded', () => {
    verificationFlow = new VerificationFlow();
});

// Global functions for dashboard
function createVerification() {
    verificationFlow?.createVerification();
}

function showSection(section) {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    event.target.classList.add('active');
    
    document.querySelectorAll('.verification-section').forEach(s => {
        s.classList.add('hidden');
    });
    
    const sectionEl = document.getElementById(`${section}-section`);
    if (sectionEl) sectionEl.classList.remove('hidden');
    
    if (section === 'active') {
        verificationFlow?.loadActiveVerifications();
    }
}

function logout() {
    verificationFlow?.logout();
}