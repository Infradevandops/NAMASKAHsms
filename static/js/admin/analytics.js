/**
 * Analytics Manager for Admin Dashboard
 * Handles all analytics data loading and display
 */

class AnalyticsManager {
    constructor() {
        this.refreshInterval = 30000; // 30 seconds
        this.autoRefreshEnabled = true;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.startAutoRefresh();
        // Load initial data
        this.loadOverview();
    }

    setupEventListeners() {
        // Tab switching
        document.querySelectorAll('[data-analytics-tab]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tab = e.target.dataset.analyticsTab;
                this.switchTab(tab);
            });
        });

        // Export buttons
        document.getElementById('export-overview')?.addEventListener('click', () => {
            this.exportToCSV('overview');
        });
    }

    startAutoRefresh() {
        if (this.autoRefreshEnabled) {
            setInterval(() => this.refreshAllData(), this.refreshInterval);
        }
    }

    async refreshAllData() {
        await this.loadOverview();
        await this.loadAtRiskUsers();
        await this.loadLiveEvents();
    }

    switchTab(tab) {
        // Hide all tabs
        document.querySelectorAll('[data-analytics-content]').forEach(el => {
            el.style.display = 'none';
        });

        // Show selected tab
        const tabEl = document.querySelector(`[data-analytics-content="${tab}"]`);
        if (tabEl) {
            tabEl.style.display = 'block';
            
            // Load data for this tab
            switch(tab) {
                case 'overview':
                    this.loadOverview();
                    break;
                case 'at-risk':
                    this.loadAtRiskUsers();
                    break;
                case 'live-events':
                    this.loadLiveEvents();
                    break;
                case 'cohorts':
                    this.loadCohortAnalysis();
                    break;
                case 'revenue':
                    this.loadRevenueData();
                    break;
                case 'services':
                    this.loadPopularServices();
                    break;
                case 'stats':
                    this.loadEventStats();
                    break;
            }
        }
    }

    async loadOverview() {
        try {
            const response = await fetch('/api/admin/analytics/overview', {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });
            const data = await response.json();
            this.displayOverview(data);
        } catch (error) {
            console.error('Error loading overview:', error);
            this.showError('overview', 'Failed to load overview data');
        }
    }

    displayOverview(data) {
        const container = document.getElementById('overview-metrics');
        if (!container) return;

        container.innerHTML = `
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Total Users</div>
                    <div class="metric-value">${data.total_users || 0}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">New Users (30d)</div>
                    <div class="metric-value">${data.new_users_30d || 0}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Active Users (7d)</div>
                    <div class="metric-value">${data.active_users_7d || 0}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Success Rate</div>
                    <div class="metric-value">${data.success_rate || 0}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Revenue (30d)</div>
                    <div class="metric-value">$${(data.total_revenue_30d || 0).toFixed(2)}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Avg Cost/Verification</div>
                    <div class="metric-value">$${(data.avg_verification_cost || 0).toFixed(2)}</div>
                </div>
            </div>
        `;
    }

    async loadAtRiskUsers() {
        try {
            const response = await fetch('/api/admin/analytics/users/at-risk?limit=50', {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });
            const data = await response.json();
            this.displayAtRiskUsers(data.at_risk_users || []);
        } catch (error) {
            console.error('Error loading at-risk users:', error);
            this.showError('at-risk', 'Failed to load at-risk users');
        }
    }

    displayAtRiskUsers(users) {
        const container = document.getElementById('at-risk-users-table');
        if (!container) return;

        if (users.length === 0) {
            container.innerHTML = '<p>No at-risk users found</p>';
            return;
        }

        const html = `
            <table class="analytics-table">
                <thead>
                    <tr>
                        <th>Email</th>
                        <th>Credits</th>
                        <th>Last Activity</th>
                        <th>Days Inactive</th>
                        <th>Verifications</th>
                    </tr>
                </thead>
                <tbody>
                    ${users.map(user => `
                        <tr>
                            <td>${user.email}</td>
                            <td>$${user.credits.toFixed(2)}</td>
                            <td>${new Date(user.last_activity).toLocaleDateString()}</td>
                            <td>${user.days_inactive}</td>
                            <td>${user.verification_count}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        container.innerHTML = html;
    }

    async loadLiveEvents() {
        try {
            const response = await fetch('/api/admin/analytics/events/live?limit=100', {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });
            const data = await response.json();
            this.displayLiveEvents(data.events || []);
        } catch (error) {
            console.error('Error loading live events:', error);
            this.showError('live-events', 'Failed to load live events');
        }
    }

    displayLiveEvents(events) {
        const container = document.getElementById('live-events-feed');
        if (!container) return;

        if (events.length === 0) {
            container.innerHTML = '<p>No events yet</p>';
            return;
        }

        const html = events.map(event => `
            <div class="event-item">
                <div class="event-type">${this.getEventEmoji(event.event_type)} ${event.event_type}</div>
                <div class="event-user">${event.user_email}</div>
                <div class="event-time">${new Date(event.created_at).toLocaleTimeString()}</div>
            </div>
        `).join('');
        
        container.innerHTML = html;
    }

    async loadCohortAnalysis() {
        try {
            const response = await fetch('/api/admin/analytics/users/cohorts', {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });
            const data = await response.json();
            this.displayCohortAnalysis(data.cohorts || []);
        } catch (error) {
            console.error('Error loading cohort analysis:', error);
            this.showError('cohorts', 'Failed to load cohort analysis');
        }
    }

    displayCohortAnalysis(cohorts) {
        const container = document.getElementById('cohort-analysis');
        if (!container) return;

        if (cohorts.length === 0) {
            container.innerHTML = '<p>No cohort data available</p>';
            return;
        }

        const html = `
            <table class="analytics-table">
                <thead>
                    <tr>
                        <th>Cohort Date</th>
                        <th>Size</th>
                        <th>Day 1 Retention</th>
                        <th>Day 7 Retention</th>
                        <th>Day 30 Retention</th>
                    </tr>
                </thead>
                <tbody>
                    ${cohorts.map(cohort => `
                        <tr>
                            <td>${cohort.cohort_date}</td>
                            <td>${cohort.cohort_size}</td>
                            <td>${cohort.day_1_retention}%</td>
                            <td>${cohort.day_7_retention}%</td>
                            <td>${cohort.day_30_retention}%</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        container.innerHTML = html;
    }

    async loadRevenueData() {
        try {
            const response = await fetch('/api/admin/analytics/revenue/daily?days=30', {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });
            const data = await response.json();
            this.displayRevenueData(data.daily_revenue || []);
        } catch (error) {
            console.error('Error loading revenue data:', error);
            this.showError('revenue', 'Failed to load revenue data');
        }
    }

    displayRevenueData(revenue) {
        const container = document.getElementById('revenue-chart');
        if (!container) return;

        if (revenue.length === 0) {
            container.innerHTML = '<p>No revenue data available</p>';
            return;
        }

        const html = `
            <table class="analytics-table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Revenue</th>
                        <th>Transactions</th>
                    </tr>
                </thead>
                <tbody>
                    ${revenue.map(day => `
                        <tr>
                            <td>${day.date}</td>
                            <td>$${day.revenue.toFixed(2)}</td>
                            <td>${day.transaction_count}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        container.innerHTML = html;
    }

    async loadPopularServices() {
        try {
            const response = await fetch('/api/admin/analytics/services/popular?limit=10', {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });
            const data = await response.json();
            this.displayPopularServices(data.popular_services || []);
        } catch (error) {
            console.error('Error loading popular services:', error);
            this.showError('services', 'Failed to load popular services');
        }
    }

    displayPopularServices(services) {
        const container = document.getElementById('popular-services');
        if (!container) return;

        if (services.length === 0) {
            container.innerHTML = '<p>No service data available</p>';
            return;
        }

        const html = `
            <table class="analytics-table">
                <thead>
                    <tr>
                        <th>Service</th>
                        <th>Count</th>
                        <th>Avg Cost</th>
                    </tr>
                </thead>
                <tbody>
                    ${services.map(service => `
                        <tr>
                            <td>${service.service}</td>
                            <td>${service.count}</td>
                            <td>$${service.avg_cost.toFixed(2)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        container.innerHTML = html;
    }

    async loadEventStats() {
        try {
            const response = await fetch('/api/admin/analytics/events/stats', {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });
            const data = await response.json();
            this.displayEventStats(data);
        } catch (error) {
            console.error('Error loading event stats:', error);
            this.showError('stats', 'Failed to load event statistics');
        }
    }

    displayEventStats(stats) {
        const container = document.getElementById('event-stats');
        if (!container) return;

        const eventTypes = stats.event_types || {};
        const html = `
            <div class="stats-summary">
                <div class="stat">
                    <div class="stat-label">Total Events</div>
                    <div class="stat-value">${stats.total_events || 0}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Unique Users</div>
                    <div class="stat-value">${stats.unique_users || 0}</div>
                </div>
            </div>
            <div class="event-types">
                <h4>Event Type Breakdown</h4>
                <ul>
                    ${Object.entries(eventTypes).map(([type, count]) => `
                        <li>${type}: ${count}</li>
                    `).join('')}
                </ul>
            </div>
        `;
        container.innerHTML = html;
    }

    getEventEmoji(eventType) {
        const emojis = {
            'signup': '📝',
            'login': '🔐',
            'logout': '🚪',
            'verification_success': '✅',
            'verification_failed': '❌',
            'payment_completed': '💳',
            'tier_upgrade': '⬆️',
            'tier_downgrade': '⬇️',
        };
        return emojis[eventType] || '📊';
    }

    getToken() {
        // Get token from localStorage or cookie
        return localStorage.getItem('token') || document.cookie.split('token=')[1]?.split(';')[0];
    }

    showError(section, message) {
        const container = document.getElementById(`${section}-error`);
        if (container) {
            container.innerHTML = `<div class="error-message">${message}</div>`;
        }
    }

    exportToCSV(section) {
        // Implementation for CSV export
        console.log(`Exporting ${section} to CSV`);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.analyticsManager = new AnalyticsManager();
});
