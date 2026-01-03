/**
 * Pricing Card Component
 * Displays tier pricing with i18n and currency support
 */

class PricingCard {
    constructor(tier, container) {
        this.tier = tier;
        this.container = container;
        this.i18nCurrency = window.i18nCurrency;
        this.render();
    }

    render() {
        const pricing = this.i18nCurrency.getTierPricing(this.tier);
        const features = this.i18nCurrency.getTierFeatures(this.tier);
        const tierName = window.i18n?.t(`tiers.${this.tier}`) || this.tier;

        const card = document.createElement('div');
        card.className = `pricing-card pricing-card-${this.tier}`;
        card.innerHTML = `
            <div class="pricing-header">
                <h3 class="pricing-title">${tierName}</h3>
                <div class="pricing-amount">
                    <span class="price-value" data-i18n-currency data-amount="${pricing.monthly || pricing.perSms}" data-from="USD">
                        ${this.i18nCurrency.formatPrice(pricing.monthly || pricing.perSms)}
                    </span>
                    <span class="price-period">
                        ${pricing.monthly ? window.i18n?.t('common.per_month') || '/month' : window.i18n?.t('common.per_sms') || '/SMS'}
                    </span>
                </div>
            </div>

            ${pricing.quota ? `
                <div class="pricing-quota">
                    <span class="quota-label">${window.i18n?.t('common.quota') || 'Quota'}:</span>
                    <span class="quota-value">${pricing.quota} SMS</span>
                    <span class="overage-label">${window.i18n?.t('common.overage') || 'Overage'}:</span>
                    <span class="overage-value" data-i18n-currency data-amount="${pricing.overage}" data-from="USD">
                        ${this.i18nCurrency.formatPrice(pricing.overage)}/SMS
                    </span>
                </div>
            ` : ''}

            <ul class="pricing-features">
                ${features.map(feature => `
                    <li class="feature-item">
                        <span class="feature-icon">✓</span>
                        <span class="feature-text">${feature}</span>
                    </li>
                `).join('')}
            </ul>

            <button class="pricing-button" data-tier="${this.tier}">
                ${window.i18n?.t('common.select') || 'Select'}
            </button>
        `;

        this.container.appendChild(card);
    }
}

/**
 * Pricing Grid Component
 * Displays all tiers in a responsive grid
 */
class PricingGrid {
    constructor(containerId = 'pricing-grid') {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        this.tiers = ['freemium', 'payg', 'pro', 'custom'];
        this.render();
        this.attachEventListeners();
    }

    render() {
        this.container.innerHTML = '';
        this.container.className = 'pricing-grid';

        this.tiers.forEach(tier => {
            const tierContainer = document.createElement('div');
            tierContainer.className = 'pricing-card-wrapper';
            this.container.appendChild(tierContainer);
            new PricingCard(tier, tierContainer);
        });
    }

    attachEventListeners() {
        this.container.querySelectorAll('.pricing-button').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tier = e.target.dataset.tier;
                this.handleTierSelection(tier);
            });
        });
    }

    handleTierSelection(tier) {
        document.dispatchEvent(new CustomEvent('tierSelected', { detail: { tier } }));
        if (typeof showToast === 'function') {
            showToast(`Tier ${tier} selected`, 'success');
        }
    }
}

/**
 * Pricing Breakdown Component
 * Shows detailed cost breakdown for a verification
 */
class PricingBreakdown {
    constructor(containerId = 'pricing-breakdown') {
        this.container = document.getElementById(containerId);
        this.i18nCurrency = window.i18nCurrency;
    }

    show(baseCost, filters = {}, tier = 'payg') {
        if (!this.container) return;

        const breakdown = this.i18nCurrency.getPricingBreakdown(baseCost, filters, tier);

        this.container.innerHTML = `
            <div class="breakdown-item">
                <span class="breakdown-label">${window.i18n?.t('common.base_cost') || 'Base Cost'}:</span>
                <span class="breakdown-value">${breakdown.base}</span>
            </div>

            ${Object.entries(breakdown.filters).length > 0 ? `
                <div class="breakdown-filters">
                    ${Object.entries(breakdown.filters).map(([type, cost]) => `
                        <div class="breakdown-item">
                            <span class="breakdown-label">${type.charAt(0).toUpperCase() + type.slice(1)} ${window.i18n?.t('common.filter') || 'Filter'}:</span>
                            <span class="breakdown-value">+${cost}</span>
                        </div>
                    `).join('')}
                </div>
            ` : ''}

            <div class="breakdown-total">
                <span class="breakdown-label">${window.i18n?.t('common.total') || 'Total'}:</span>
                <span class="breakdown-value total">${breakdown.total}</span>
            </div>
        `;

        this.container.style.display = 'block';
    }

    hide() {
        if (this.container) {
            this.container.style.display = 'none';
        }
    }
}

// Initialize pricing grid on page load
document.addEventListener('DOMContentLoaded', () => {
    new PricingGrid();
});
