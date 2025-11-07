/**
 * Enhanced Verification UI with real-time updates and modern UX
 */
class EnhancedVerificationUI {
    constructor() {
        this.selectedChannel = 'sms';
        this.activeVerifications = new Map();
        this.wsConnection = null;
        this.init();
    }

    init() {
        this.setupChannelSelector();
        this.setupWebSocket();
        this.setupRealTimeUpdates();
    }

    setupChannelSelector() {
        const container = document.getElementById('channel-selector');
        if (!container) return;

        const channels = [
            { id: 'sms', name: 'SMS', icon: '📱', description: '4 Providers' },
            { id: 'whatsapp', name: 'WhatsApp', icon: '💬', description: '2B+ Users' },
            { id: 'telegram', name: 'Telegram', icon: '✈️', description: 'Instant' }
        ];

        container.innerHTML = channels.map(channel => `
            <div class="channel-option ${channel.id === this.selectedChannel ? 'selected' : ''}" 
                 onclick="enhancedUI.selectChannel('${channel.id}')">
                <div class="channel-icon">${channel.icon}</div>
                <div style="font-weight: 600;">${channel.name}</div>
                <div style="font-size: 11px; color: var(--text-secondary);">${channel.description}</div>
            </div>
        `).join('');
    }

    selectChannel(channelId) {
        this.selectedChannel = channelId;
        this.setupChannelSelector();
        this.updateProviderStatus();
    }

    async updateProviderStatus() {
        const statusContainer = document.getElementById('provider-status');
        if (!statusContainer) return;

        try {
            const response = await fetch('/infrastructure/regions');
            const data = await response.json();
            
            statusContainer.innerHTML = `
                <div class="real-time-status">
                    <div class="status-indicator success"></div>
                    <span>All providers operational</span>
                    <span style="margin-left: auto; font-size: 12px; color: var(--text-secondary);">
                        ${Object.keys(data.regions).length} regions active
                    </span>
                </div>
            `;
        } catch (error) {
            statusContainer.innerHTML = `
                <div class="real-time-status">
                    <div class="status-indicator warning"></div>
                    <span>Checking provider status...</span>
                </div>
            `;
        }
    }

    async startVerification(service) {
        this.showLoadingState();
        
        try {
            // Get AI recommendation for optimal provider
            const recommendation = await fetch(`/ai/routing/recommend?service=${service}&country=US`);
            const providerData = await recommendation.json();
            
            // Start verification with recommended provider
            const response = await fetch('/verify/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    service: service,
                    channel: this.selectedChannel,
                    provider: providerData.recommended_provider
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.showVerificationCard(result);
                this.trackVerification(result.verification_id);
            } else {
                this.showError(result.message);
            }
        } catch (error) {
            this.showError('Failed to start verification');
        } finally {
            this.hideLoadingState();
        }
    }

    showVerificationCard(data) {
        const container = document.getElementById('active-verifications');
        if (!container) return;

        const card = document.createElement('div');
        card.className = 'verification-card';
        card.id = `verification-${data.verification_id}`;
        
        card.innerHTML = `
            <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 16px;">
                <div>
                    <h3 style="margin: 0; color: var(--text-primary);">${data.service}</h3>
                    <div style="font-size: 14px; color: var(--text-secondary);">
                        ${data.phone_number} • ${data.provider}
                    </div>
                </div>
                <div class="provider-status active">
                    <div class="status-indicator success"></div>
                    Active
                </div>
            </div>
            
            <div class="progress-bar">
                <div class="progress-fill" style="width: 20%"></div>
            </div>
            
            <div style="display: flex; gap: 12px; margin-top: 16px;">
                <button class="enhanced-button" onclick="enhancedUI.checkMessages('${data.verification_id}')">
                    📨 Check Messages
                </button>
                <button class="enhanced-button" style="background: #ef4444;" onclick="enhancedUI.cancelVerification('${data.verification_id}')">
                    ❌ Cancel
                </button>
            </div>
        `;

        container.appendChild(card);
        this.activeVerifications.set(data.verification_id, data);
    }

    async checkMessages(verificationId) {
        try {
            const response = await fetch(`/verify/${verificationId}/messages`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            });
            const data = await response.json();
            
            if (data.messages && data.messages.length > 0) {
                this.showMessages(verificationId, data.messages);
                this.updateProgress(verificationId, 100);
            } else {
                this.showToast('No messages yet. Checking again...', 'info');
                this.updateProgress(verificationId, 60);
            }
        } catch (error) {
            this.showToast('Failed to check messages', 'error');
        }
    }

    showMessages(verificationId, messages) {
        const card = document.getElementById(`verification-${verificationId}`);
        if (!card) return;

        const messagesHtml = messages.map(msg => `
            <div style="background: var(--bg-secondary); padding: 12px; border-radius: 8px; margin: 8px 0;">
                <div style="font-weight: 600; color: #10b981;">✅ Code Received</div>
                <div style="font-size: 18px; font-weight: bold; margin: 8px 0;">${msg.code}</div>
                <div style="font-size: 12px; color: var(--text-secondary);">${msg.timestamp}</div>
            </div>
        `).join('');

        card.innerHTML += `
            <div style="margin-top: 16px;">
                <h4>Messages:</h4>
                ${messagesHtml}
            </div>
        `;
    }

    updateProgress(verificationId, percentage) {
        const progressBar = document.querySelector(`#verification-${verificationId} .progress-fill`);
        if (progressBar) {
            progressBar.style.width = `${percentage}%`;
        }
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = 'toast-notification';
        
        const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
        toast.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 20px;">${icons[type]}</span>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(toast);
        setTimeout(() => toast.classList.add('show'), 100);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => document.body.removeChild(toast), 300);
        }, 3000);
    }

    showLoadingState() {
        const button = event.target;
        button.innerHTML = '<div class="loading-skeleton" style="width: 60px; height: 16px;"></div>';
        button.disabled = true;
    }

    hideLoadingState() {
        // Reset button states
        document.querySelectorAll('button[disabled]').forEach(btn => {
            btn.disabled = false;
            btn.innerHTML = btn.getAttribute('data-original-text') || 'Start Verification';
        });
    }

    setupWebSocket() {
        // WebSocket for real-time updates
        if (window.WebSocket) {
            this.wsConnection = new WebSocket(`ws://${window.location.host}/ws`);
            this.wsConnection.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleRealtimeUpdate(data);
            };
        }
    }

    handleRealtimeUpdate(data) {
        if (data.type === 'verification_update') {
            this.updateProgress(data.verification_id, data.progress);
        } else if (data.type === 'message_received') {
            this.showMessages(data.verification_id, [data.message]);
        }
    }

    setupRealTimeUpdates() {
        // Update provider status every 30 seconds
        setInterval(() => this.updateProviderStatus(), 30000);
        
        // Initial load
        this.updateProviderStatus();
    }
}

// Initialize enhanced UI
const enhancedUI = new EnhancedVerificationUI();

// Export for global access
window.enhancedUI = enhancedUI;