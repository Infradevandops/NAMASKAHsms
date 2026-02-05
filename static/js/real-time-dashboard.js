/**
 * Real-time Dashboard Fixes
 * Handles live balance sync, status updates, and real-time data
 */

class RealTimeDashboard {
    constructor() {
        this.updateInterval = null;
        this.balanceInterval = null;
        this.statusPolling = new Map();
        this.cache = new Map();
        this.isOnline = navigator.onLine;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.startRealTimeUpdates();
        this.clearStaleCache();
        this.fixCalculations();
    }

    setupEventListeners() {
        // Online/offline detection
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.forceRefreshAll();
        });
        
        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.showOfflineIndicator();
        });

        // Page visibility change
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.forceRefreshAll();
            }
        });

        // Focus events
        window.addEventListener('focus', () => {
            this.forceRefreshAll();
        });
    }

    // 1. Fix Balance Sync - Real-time API calls
    async syncBalance() {
        if (!this.isOnline) return;

        try {
            // Clear cache for fresh data
            this.cache.delete('balance');
            
            const response = await fetch('/api/user/balance', {
                headers: {
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            const balance = parseFloat(data.credits) || 0;
            
            // Update balance display immediately
            this.updateBalanceDisplay(balance);
            
            // Cache for 30 seconds only
            this.cache.set('balance', balance, Date.now() + 30000);
            
            return balance;
        } catch (error) {
            console.error('Balance sync failed:', error);
            this.showErrorIndicator('balance');
        }
    }

    updateBalanceDisplay(balance) {
        const displays = [
            document.getElementById('balance-display'),
            document.getElementById('billing-balance'),
            document.querySelector('.balance-badge')
        ];

        displays.forEach(el => {
            if (el) {
                el.textContent = `$${balance.toFixed(2)}`;
                el.classList.add('updated');
                setTimeout(() => el.classList.remove('updated'), 1000);
            }
        });
    }

    // 2. Fix Status Updates - Proper polling service
    startStatusPolling(verificationId) {
        if (this.statusPolling.has(verificationId)) {
            return; // Already polling
        }

        const pollInterval = setInterval(async () => {
            try {
                const status = await this.checkVerificationStatus(verificationId);
                this.updateVerificationStatus(verificationId, status);
                
                // Stop polling if completed or failed
                if (['completed', 'failed', 'cancelled'].includes(status.status)) {
                    this.stopStatusPolling(verificationId);
                }
            } catch (error) {
                console.error('Status polling failed:', error);
            }
        }, 3000); // Poll every 3 seconds

        this.statusPolling.set(verificationId, pollInterval);
    }

    async checkVerificationStatus(verificationId) {
        const response = await fetch(`/api/verification/status/${verificationId}`, {
            headers: { 'Cache-Control': 'no-cache' }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        return await response.json();
    }

    updateVerificationStatus(verificationId, statusData) {
        // Update status in activity table
        const statusElements = document.querySelectorAll(`[data-verification-id="${verificationId}"]`);
        
        statusElements.forEach(el => {
            const statusEl = el.querySelector('.status-tag');
            if (statusEl) {
                statusEl.className = `tag ${this.getStatusClass(statusData.status)}`;
                statusEl.innerHTML = `${this.getStatusIcon(statusData.status)} ${statusData.status}`;
            }
        });

        // Update any modals or detailed views
        this.updateVerificationModal(verificationId, statusData);
    }

    stopStatusPolling(verificationId) {
        const interval = this.statusPolling.get(verificationId);
        if (interval) {
            clearInterval(interval);
            this.statusPolling.delete(verificationId);
        }
    }

    // 3. Fix Calculations - Success rate & spending
    async updateAnalytics() {
        if (!this.isOnline) return;

        try {
            this.cache.delete('analytics');
            
            const response = await fetch('/api/analytics/summary', {
                headers: { 'Cache-Control': 'no-cache' }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            
            // Fix calculations
            const totalSms = data.total_verifications || 0;
            const successfulSms = data.successful_verifications || 0;
            const totalSpent = data.total_spent || data.revenue || 0;
            const successRate = totalSms > 0 ? (successfulSms / totalSms) * 100 : 0;

            // Update displays with correct calculations
            this.updateElement('total-sms', totalSms);
            this.updateElement('successful-sms', successfulSms);
            this.updateElement('total-spent', `$${totalSpent.toFixed(2)}`);
            this.updateElement('success-rate', `${successRate.toFixed(1)}%`);

            // Cache for 1 minute
            this.cache.set('analytics', data, Date.now() + 60000);
            
        } catch (error) {
            console.error('Analytics update failed:', error);
            this.showErrorIndicator('analytics');
        }
    }

    // 4. Add real-time updates - WebSocket or polling
    startRealTimeUpdates() {
        // Balance updates every 30 seconds
        this.balanceInterval = setInterval(() => {
            this.syncBalance();
        }, 30000);

        // Analytics updates every 60 seconds
        this.updateInterval = setInterval(() => {
            this.updateAnalytics();
            this.updateRecentActivity();
        }, 60000);

        // Initial load
        this.forceRefreshAll();
    }

    async updateRecentActivity() {
        if (!this.isOnline) return;

        try {
            this.cache.delete('recent_activity');
            
            const response = await fetch('/api/dashboard/activity/recent', {
                headers: { 'Cache-Control': 'no-cache' }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            this.renderRecentActivity(data.activities || []);
            
        } catch (error) {
            console.error('Recent activity update failed:', error);
        }
    }

    renderRecentActivity(activities) {
        const tbody = document.getElementById('activity-table');
        const emptyState = document.getElementById('empty-activity-state');
        const tableContainer = document.getElementById('activity-table-container');

        if (!tbody) return;

        tbody.innerHTML = '';

        if (activities.length === 0) {
            if (emptyState) emptyState.style.display = 'block';
            if (tableContainer) tableContainer.style.display = 'none';
            return;
        }

        if (emptyState) emptyState.style.display = 'none';
        if (tableContainer) tableContainer.style.display = 'block';

        activities.forEach(activity => {
            const row = document.createElement('tr');
            row.dataset.verificationId = activity.id;
            
            const statusClass = this.getStatusClass(activity.status);
            const statusIcon = this.getStatusIcon(activity.status);
            const timeAgo = this.formatTimeAgo(new Date(activity.created_at));

            row.innerHTML = `
                <td>${this.escapeHtml(activity.service_name || 'N/A')}</td>
                <td>${this.escapeHtml(activity.phone_number || 'N/A')}</td>
                <td>${timeAgo}</td>
                <td><span class="tag status-tag ${statusClass}">${statusIcon} ${activity.status || 'pending'}</span></td>
            `;

            tbody.appendChild(row);

            // Start polling for pending statuses
            if (['pending', 'processing'].includes(activity.status)) {
                this.startStatusPolling(activity.id);
            }
        });
    }

    // 5. Clear stale cache - Force fresh data
    clearStaleCache() {
        // Clear all cached data
        this.cache.clear();
        
        // Clear browser cache for API calls
        if ('caches' in window) {
            caches.keys().then(names => {
                names.forEach(name => {
                    if (name.includes('api')) {
                        caches.delete(name);
                    }
                });
            });
        }

        // Clear localStorage cache
        Object.keys(localStorage).forEach(key => {
            if (key.startsWith('cache_') || key.startsWith('api_')) {
                localStorage.removeItem(key);
            }
        });
    }

    forceRefreshAll() {
        this.clearStaleCache();
        this.syncBalance();
        this.updateAnalytics();
        this.updateRecentActivity();
    }

    // Utility methods
    updateElement(id, value) {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = value;
            el.classList.add('updated');
            setTimeout(() => el.classList.remove('updated'), 1000);
        }
    }

    getStatusClass(status) {
        switch (status) {
            case 'completed': return 'tag-green';
            case 'failed': 
            case 'cancelled': return 'tag-red';
            default: return 'tag-yellow';
        }
    }

    getStatusIcon(status) {
        switch (status) {
            case 'completed': return '<i class="ph ph-check"></i>';
            case 'failed': 
            case 'cancelled': return '<i class="ph ph-x"></i>';
            default: return '<i class="ph ph-clock"></i>';
        }
    }

    formatTimeAgo(date) {
        const seconds = Math.floor((new Date() - date) / 1000);
        if (seconds < 60) return 'Just now';
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `${minutes}m ago`;
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours}h ago`;
        const days = Math.floor(hours / 24);
        if (days < 7) return `${days}d ago`;
        return date.toLocaleDateString();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showErrorIndicator(component) {
        const indicator = document.createElement('div');
        indicator.className = 'error-indicator';
        indicator.innerHTML = '⚠️ Update failed';
        indicator.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #fee2e2;
            color: #991b1b;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 14px;
            z-index: 9999;
        `;
        
        document.body.appendChild(indicator);
        setTimeout(() => indicator.remove(), 3000);
    }

    showOfflineIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'offline-indicator';
        indicator.innerHTML = '📡 Offline - Some features unavailable';
        indicator.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: #fbbf24;
            color: #92400e;
            padding: 8px;
            text-align: center;
            font-size: 14px;
            z-index: 9999;
        `;
        
        document.body.appendChild(indicator);
    }

    // Fix tier display
    async updateTierDisplay() {
        try {
            const response = await fetch('/api/user/tier', {
                headers: { 'Cache-Control': 'no-cache' }
            });

            if (response.ok) {
                const data = await response.json();
                const tierName = data.tier_name || 'Freemium';
                
                const tierBadge = document.getElementById('tier-badge-display');
                if (tierBadge) {
                    tierBadge.textContent = tierName.toUpperCase();
                }
            }
        } catch (error) {
            console.error('Tier update failed:', error);
        }
    }

    destroy() {
        // Clean up intervals
        if (this.balanceInterval) {
            clearInterval(this.balanceInterval);
        }
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        
        // Stop all status polling
        this.statusPolling.forEach(interval => clearInterval(interval));
        this.statusPolling.clear();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.realTimeDashboard = new RealTimeDashboard();
});

// Add CSS for update animations
const style = document.createElement('style');
style.textContent = `
    .updated {
        animation: highlight 1s ease-in-out;
    }
    
    @keyframes highlight {
        0% { background-color: #dbeafe; }
        100% { background-color: transparent; }
    }
    
    .error-indicator {
        animation: slideIn 0.3s ease-out;
    }
    
    @keyframes slideIn {
        from { transform: translateX(100%); }
        to { transform: translateX(0); }
    }
`;
document.head.appendChild(style);