/**
 * Dashboard Widgets Component
 * Displays balance, quota, and tier information with i18n and currency
 */

class DashboardWidget {
    constructor(type, containerId) {
        this.type = type;
        this.container = document.getElementById(containerId);
        this.i18nCurrency = window.i18nCurrency;
        if (this.container) {
            this.render();
        }
    }

    render() {
        switch (this.type) {
            case 'balance':
                this.renderBalance();
                break;
            case 'quota':
                this.renderQuota();
                break;
            case 'tier':
                this.renderTier();
                break;
            case 'bonus-sms':
                this.renderBonusSMS();
                break;
        }
    }

    renderBalance() {
        const i18n = window.i18n;
        this.container.innerHTML = `
            <div class="widget widget-balance">
                <div class="widget-header">
                    <h3 class="widget-title" data-i18n="wallet.current_balance">
                        ${i18n?.t('wallet.current_balance') || 'Current Balance'}
                    </h3>
                    <span class="widget-icon">💰</span>
                </div>
                <div class="widget-content">
                    <div class="balance-amount" data-i18n-currency data-amount="0" data-from="USD">
                        $0.00
                    </div>
                    <div class="balance-meta">
                        <span class="meta-label" data-i18n="wallet.this_month">
                            ${i18n?.t('wallet.this_month') || 'This Month'}
                        </span>
                        <span class="meta-value" data-i18n-currency data-amount="0" data-from="USD">
                            $0.00
                        </span>
                    </div>
                </div>
                <button class="widget-action" data-i18n="wallet.add_credits">
                    ${i18n?.t('wallet.add_credits') || 'Add Credits'}
                </button>
            </div>
        `;
    }

    renderQuota() {
        const i18n = window.i18n;
        this.container.innerHTML = `
            <div class="widget widget-quota">
                <div class="widget-header">
                    <h3 class="widget-title" data-i18n="common.quota">
                        ${i18n?.t('common.quota') || 'Monthly Quota'}
                    </h3>
                    <span class="widget-icon">📊</span>
                </div>
                <div class="widget-content">
                    <div class="quota-bar">
                        <div class="quota-progress" style="width: 0%"></div>
                    </div>
                    <div class="quota-stats">
                        <div class="stat">
                            <span class="stat-label" data-i18n="common.used">
                                ${i18n?.t('common.used') || 'Used'}
                            </span>
                            <span class="stat-value quota-used">0</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label" data-i18n="common.remaining">
                                ${i18n?.t('common.remaining') || 'Remaining'}
                            </span>
                            <span class="stat-value quota-remaining">0</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderTier() {
        const i18n = window.i18n;
        this.container.innerHTML = `
            <div class="widget widget-tier">
                <div class="widget-header">
                    <h3 class="widget-title" data-i18n="tiers.current_plan">
                        ${i18n?.t('tiers.current_plan') || 'Current Plan'}
                    </h3>
                    <span class="widget-icon">⭐</span>
                </div>
                <div class="widget-content">
                    <div class="tier-badge" id="tier-badge">
                        Freemium
                    </div>
                    <div class="tier-features">
                        <ul id="tier-features-list"></ul>
                    </div>
                </div>
                <button class="widget-action" data-i18n="tiers.upgrade_to">
                    ${i18n?.t('tiers.upgrade_to') || 'Upgrade'}
                </button>
            </div>
        `;
    }

    renderBonusSMS() {
        const i18n = window.i18n;
        this.container.innerHTML = `
            <div class="widget widget-bonus">
                <div class="widget-header">
                    <h3 class="widget-title" data-i18n="common.bonus_sms">
                        ${i18n?.t('common.bonus_sms') || 'Bonus SMS'}
                    </h3>
                    <span class="widget-icon">🎁</span>
                </div>
                <div class="widget-content">
                    <div class="bonus-amount">
                        <span class="bonus-value" id="bonus-sms-count">0</span>
                        <span class="bonus-unit" data-i18n="common.sms">
                            ${i18n?.t('common.sms') || 'SMS'}
                        </span>
                    </div>
                    <div class="bonus-info">
                        <p class="info-text" data-i18n="common.bonus_info">
                            ${i18n?.t('common.bonus_info') || 'Bonus SMS from deposits'}
                        </p>
                    </div>
                </div>
            </div>
        `;
    }

    updateBalance(amount, monthlySpent) {
        const balanceEl = this.container.querySelector('.balance-amount');
        const monthlyEl = this.container.querySelector('.meta-value');
        
        if (balanceEl) {
            balanceEl.textContent = this.i18nCurrency.formatPrice(amount);
            balanceEl.dataset.amount = amount;
        }
        if (monthlyEl) {
            monthlyEl.textContent = this.i18nCurrency.formatPrice(monthlySpent);
            monthlyEl.dataset.amount = monthlySpent;
        }
    }

    updateQuota(used, total) {
        const progress = this.container.querySelector('.quota-progress');
        const usedEl = this.container.querySelector('.quota-used');
        const remainingEl = this.container.querySelector('.quota-remaining');
        
        const percentage = (used / total) * 100;
        
        if (progress) {
            progress.style.width = `${Math.min(percentage, 100)}%`;
            progress.className = `quota-progress ${percentage >= 100 ? 'exceeded' : percentage >= 80 ? 'warning' : 'ok'}`;
        }
        if (usedEl) usedEl.textContent = used.toFixed(2);
        if (remainingEl) remainingEl.textContent = Math.max(0, total - used).toFixed(2);
    }

    updateTier(tier, features) {
        const badge = this.container.querySelector('#tier-badge');
        const list = this.container.querySelector('#tier-features-list');
        
        if (badge) {
            badge.textContent = window.i18n?.t(`tiers.${tier}`) || tier;
            badge.className = `tier-badge tier-${tier}`;
        }
        
        if (list && features) {
            list.innerHTML = features.map(f => `<li>${f}</li>`).join('');
        }
    }

    updateBonusSMS(count) {
        const countEl = this.container.querySelector('#bonus-sms-count');
        if (countEl) {
            countEl.textContent = count;
        }
    }
}

// Initialize widgets on page load
document.addEventListener('DOMContentLoaded', () => {
    // Auto-initialize all widgets with data-widget attribute
    document.querySelectorAll('[data-widget]').forEach(el => {
        const type = el.getAttribute('data-widget');
        new DashboardWidget(type, el.id);
    });
});
