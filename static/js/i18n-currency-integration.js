/**
 * i18n & Currency Integration
 * Handles localized pricing, formatting, and currency conversion
 */

class I18nCurrencyIntegration {
    constructor() {
        this.i18n = window.i18n;
        this.currency = window.currency;
        this.locale = this.i18n?.locale || 'en';
        this.currencyCode = this.currency?.currency || 'USD';
    }

    /**
     * Format price with localized currency and i18n
     */
    formatPrice(amount, fromCurrency = 'USD') {
        if (!this.currency) return `${amount.toFixed(2)}`;
        return this.currency.format(amount, fromCurrency);
    }

    /**
     * Get localized tier pricing
     */
    getTierPricing(tier) {
        const pricing = {
            freemium: { monthly: 0, perSms: 2.22 },
            payg: { monthly: 0, perSms: 2.50 },
            pro: { monthly: 25, quota: 15, overage: 0.30 },
            custom: { monthly: 35, quota: 25, overage: 0.20 }
        };
        
        const tierData = pricing[tier] || {};
        const localized = {};
        
        for (const [key, value] of Object.entries(tierData)) {
            if (typeof value === 'number' && key !== 'quota') {
                localized[key] = this.formatPrice(value);
            } else {
                localized[key] = value;
            }
        }
        
        return localized;
    }

    /**
     * Format filter charges with currency
     */
    getFilterCharges() {
        return {
            state: this.formatPrice(0.25),
            city: this.formatPrice(0.25),
            isp: this.formatPrice(0.50)
        };
    }

    /**
     * Get localized tier features
     */
    getTierFeatures(tier) {
        const features = {
            freemium: [
                this.i18n.t('tiers.features.random_numbers'),
                this.i18n.t('tiers.features.no_api'),
                this.i18n.t('tiers.features.no_filters')
            ],
            payg: [
                this.i18n.t('tiers.features.location_filters'),
                this.i18n.t('tiers.features.isp_filters'),
                this.i18n.t('tiers.features.no_api')
            ],
            pro: [
                this.i18n.t('tiers.features.all_filters'),
                this.i18n.t('tiers.features.api_access'),
                this.i18n.t('tiers.features.affiliate')
            ],
            custom: [
                this.i18n.t('tiers.features.all_filters'),
                this.i18n.t('tiers.features.unlimited_api'),
                this.i18n.t('tiers.features.affiliate'),
                this.i18n.t('tiers.features.priority_support')
            ]
        };
        
        return features[tier] || [];
    }

    /**
     * Format quota display
     */
    formatQuota(used, total, tier) {
        const percentage = (used / total) * 100;
        const remaining = total - used;
        
        return {
            used: used.toFixed(2),
            total: total.toFixed(2),
            remaining: remaining.toFixed(2),
            percentage: percentage.toFixed(1),
            status: percentage >= 100 ? 'exceeded' : percentage >= 80 ? 'warning' : 'ok'
        };
    }

    /**
     * Get localized pricing breakdown
     */
    getPricingBreakdown(baseCost, filters = {}, tier = 'payg') {
        let total = baseCost;
        const breakdown = {
            base: this.formatPrice(baseCost),
            filters: {},
            total: ''
        };

        if (tier === 'payg') {
            if (filters.state || filters.city) {
                breakdown.filters.location = this.formatPrice(0.25);
                total += 0.25;
            }
            if (filters.isp) {
                breakdown.filters.isp = this.formatPrice(0.50);
                total += 0.50;
            }
        }

        breakdown.total = this.formatPrice(total);
        return breakdown;
    }

    /**
     * Update all currency elements on page
     */
    updateCurrencyDisplay() {
        document.querySelectorAll('[data-i18n-currency]').forEach(el => {
            const amount = parseFloat(el.dataset.amount);
            const from = el.dataset.from || 'USD';
            el.textContent = this.formatPrice(amount, from);
        });
    }

    /**
     * Update all i18n elements on page
     */
    updateI18nDisplay() {
        if (this.i18n) {
            this.i18n.translatePage();
        }
    }

    /**
     * Full page update (i18n + currency)
     */
    updatePageDisplay() {
        this.updateI18nDisplay();
        this.updateCurrencyDisplay();
    }
}

// Initialize integration
const i18nCurrency = new I18nCurrencyIntegration();

// Listen for language changes
document.addEventListener('languageChanged', () => {
    i18nCurrency.locale = i18n?.locale || 'en';
    i18nCurrency.updatePageDisplay();
});

// Listen for currency changes
document.addEventListener('currencyChanged', () => {
    i18nCurrency.currencyCode = currency?.currency || 'USD';
    i18nCurrency.updatePageDisplay();
});
