/**
 * Dashboard Initialization Module
 * 
 * Initializes all dashboard widgets:
 * - Tier Card
 * - Analytics Stats
 * - Recent Activity
 * 
 * This module replaces the inline script in dashboard.html
 */

import { TIMEOUTS, ENDPOINTS, STORAGE_KEYS } from './constants.js';
import { hasAuthToken, getAuthHeaders } from './auth-helpers.ts';
import { initTierCard } from './tier-card.js';

// ============================================
// ANALYTICS WIDGET
// ============================================
class AnalyticsWidget {
    constructor() {
        this.elements = {
            totalSms: document.getElementById('total-sms'),
            successfulSms: document.getElementById('successful-sms'),
            totalSpent: document.getElementById('total-spent'),
            successRate: document.getElementById('success-rate')
        };
    }

    async load() {
        if (!hasAuthToken()) return;

        this._log('info', 'Loading analytics...');

        try {
            const response = await fetch(ENDPOINTS.ANALYTICS.SUMMARY, {
                credentials: 'include',
                headers: getAuthHeaders()
            });

            if (!response.ok) return;

            const data = await response.json();
            this._log('info', 'Analytics loaded', data);
            this._render(data);

        } catch (error) {
            this._log('error', 'Analytics load failed', { error: error.message });
        }
    }

    _render(data) {
        if (this.elements.totalSms) {
            this.elements.totalSms.textContent = data.total_verifications || 0;
        }
        if (this.elements.successfulSms) {
            this.elements.successfulSms.textContent = data.successful_verifications || 0;
        }
        if (this.elements.totalSpent) {
            const spent = data.revenue || data.total_spent || 0;
            this.elements.totalSpent.textContent = `$${spent.toFixed(2)}`;
            this.elements.totalSpent.setAttribute('data-amount', spent);
        }
        if (this.elements.successRate) {
            const rate = data.success_rate || 0;
            this.elements.successRate.textContent = `${rate.toFixed(1)}%`;
        }
    }

    _log(level, message, data = null) {
        if (window.FrontendLogger) {
            window.FrontendLogger[level](message, data);
        }
    }
}

// ============================================
// ACTIVITY WIDGET
// ============================================
class ActivityWidget {
    constructor() {
        this.elements = {
            loading: document.getElementById('activity-loading'),
            table: document.getElementById('activity-table'),
            empty: document.getElementById('empty-state'),
            body: document.getElementById('activity-body')
        };
    }

    async load() {
        if (!hasAuthToken()) {
            this._showEmpty();
            return;
        }

        this._log('info', 'Loading recent activity...');

        try {
            const response = await fetch(ENDPOINTS.DASHBOARD.ACTIVITY, {
                credentials: 'include',
                headers: getAuthHeaders()
            });

            this._hideLoading();

            if (!response.ok) {
                this._showEmpty();
                return;
            }

            const activities = await response.json();

            if (!activities || activities.length === 0) {
                this._showEmpty();
                return;
            }

            this._log('info', `Activity loaded: ${activities.length} items`);
            this._render(activities);

        } catch (error) {
            this._log('error', 'Activity load failed', { error: error.message });
            this._hideLoading();
            this._showEmpty();
        }
    }

    _render(activities) {
        let html = '';

        for (const activity of activities) {
            const statusColor = activity.status === 'completed' ? '#10b981'
                : activity.status === 'failed' ? '#ef4444'
                    : '#f59e0b';

            html += `
                <tr style="border-bottom: 1px solid rgba(0,0,0,0.05);">
                    <td style="padding: 12px;">${this._escapeHtml(activity.service_name || 'Unknown')}</td>
                    <td style="padding: 12px;">${this._escapeHtml(activity.phone_number || '-')}</td>
                    <td style="padding: 12px;">${this._formatTime(activity.created_at)}</td>
                    <td style="padding: 12px; color: ${statusColor};">${this._escapeHtml(activity.status || 'pending')}</td>
                </tr>
            `;
        }

        if (this.elements.body) {
            this.elements.body.innerHTML = html;
        }
        if (this.elements.table) {
            this.elements.table.style.display = 'table';
        }
    }

    _hideLoading() {
        if (this.elements.loading) {
            this.elements.loading.style.display = 'none';
        }
    }

    _showEmpty() {
        this._hideLoading();
        if (this.elements.empty) {
            this.elements.empty.style.display = 'block';
        }
    }

    _escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    _formatTime(isoString) {
        if (!isoString) return '-';
        try {
            return new Date(isoString).toLocaleString();
        } catch (e) {
            return isoString;
        }
    }

    _log(level, message, data = null) {
        if (window.FrontendLogger) {
            window.FrontendLogger[level](message, data);
        }
    }
}

// ============================================
// MODAL HANDLERS
// ============================================
function showComparePlansModal() {
    const currentTier = window.tierCard?.currentData?.current_tier || 'freemium';
    if (typeof window.showTierCompareModal === 'function') {
        window.showTierCompareModal(currentTier);
    }
}

function closeComparePlansModal() {
    if (typeof window.closeTierCompareModal === 'function') {
        window.closeTierCompareModal();
    }
}

// ============================================
// INITIALIZATION
// ============================================
function initDashboard() {
    // Initialize Tier Card
    const tierCard = initTierCard('tier-card');

    // Initialize Analytics
    const analytics = new AnalyticsWidget();
    analytics.load();

    // Initialize Activity
    const activity = new ActivityWidget();
    activity.load();

    // Set up periodic refresh
    setInterval(() => {
        if (hasAuthToken()) {
            tierCard.load();
            analytics.load();
        }
    }, TIMEOUTS.REFRESH_INTERVAL);

    // Expose modal handlers globally
    window.showComparePlansModal = showComparePlansModal;
    window.closeComparePlansModal = closeComparePlansModal;

    return { tierCard, analytics, activity };
}

// Auto-initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDashboard);
} else {
    initDashboard();
}

// Export for external use
export { initDashboard, AnalyticsWidget, ActivityWidget };
