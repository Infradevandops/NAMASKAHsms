/**
 * Tier Management Module
 * Handles tier badge display, upgrade modals, and feature gating
 * 
 * Converted to ES6 module - maintains backward compatibility via window attachment
 */

import { ENDPOINTS, STORAGE_KEYS, TIERS, TIER_DISPLAY_NAMES } from './constants.js';
import { getAuthToken, hasAuthToken, getAuthHeaders } from './auth-helpers.js';

/**
 * Feature access map - which tiers can access which features
 */
export const FEATURE_ACCESS_MAP = {
    'api_keys': [TIERS.PRO, TIERS.CUSTOM],
    'location_filters': [TIERS.PAYG, TIERS.PRO, TIERS.CUSTOM],
    'isp_filter': [TIERS.PAYG, TIERS.PRO, TIERS.CUSTOM],
    'affiliate_program': [TIERS.PRO, TIERS.CUSTOM],
    'bulk_discounts': [TIERS.PRO, TIERS.CUSTOM],
    'priority_support': [TIERS.PRO, TIERS.CUSTOM],
    'custom_branding': [TIERS.CUSTOM],
    'dedicated_support': [TIERS.CUSTOM]
};

/**
 * Feature display names
 */
export const FEATURE_NAMES = {
    'api_keys': 'API Keys',
    'location_filters': 'Location Filters',
    'isp_filter': 'ISP/Carrier Filtering',
    'affiliate_program': 'Affiliate Program',
    'bulk_discounts': 'Bulk Purchase Discounts',
    'priority_support': 'Priority Support',
    'custom_branding': 'Custom Branding',
    'dedicated_support': 'Dedicated Support'
};

/**
 * TierManager class - manages tier display and feature gating
 */
export class TierManager {
    constructor(options = {}) {
        this.currentTier = null;
        this.tierConfig = null;
        this.autoInit = options.autoInit !== false;
        
        if (this.autoInit) {
            this.init();
        }
    }

    async init() {
        await this.loadCurrentTier();
        this.renderTierBadge();
        this.setupEventListeners();
    }

    async loadCurrentTier() {
        try {
            if (!hasAuthToken()) return;

            const response = await fetch(ENDPOINTS.TIERS.CURRENT, {
                headers: getAuthHeaders(),
                credentials: 'include'
            });

            if (response.ok) {
                const data = await response.json();
                this.currentTier = data.current_tier;
                this.tierConfig = data;
            }
        } catch (error) {
            this._log('error', 'Failed to load tier:', error);
        }
    }

    renderTierBadge() {
        const headerRight = document.querySelector('.header-right');
        if (!headerRight || !this.currentTier) return;

        // Remove existing badge if present
        const existingBadge = headerRight.querySelector('.tier-badge-container');
        if (existingBadge) existingBadge.remove();

        const badgeContainer = document.createElement('div');
        badgeContainer.className = 'tier-badge-container';
        badgeContainer.innerHTML = `
            <span class="tier-badge tier-badge-${this.currentTier}" aria-label="Current plan: ${this.getTierDisplayName()}">
                <i class="ph ph-crown" aria-hidden="true"></i>
                ${this.getTierDisplayName()}
            </span>
            ${this.currentTier === TIERS.FREEMIUM ? '<a href="/pricing" class="upgrade-link" aria-label="Upgrade your plan">Upgrade</a>' : ''}
        `;

        const balanceDisplay = headerRight.querySelector('.balance-display');
        if (balanceDisplay) {
            headerRight.insertBefore(badgeContainer, balanceDisplay);
        } else {
            headerRight.appendChild(badgeContainer);
        }
    }

    getTierDisplayName() {
        return TIER_DISPLAY_NAMES[this.currentTier] || 'Free';
    }

    setupEventListeners() {
        // Listen for 402 errors (Payment Required)
        window.addEventListener('fetch-error-402', (e) => {
            this.showUpgradeModal(e.detail);
        });

        // Listen for escape key to close modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeUpgradeModal();
            }
        });
    }

    showUpgradeModal(details = {}) {
        const requiredTier = details.required_tier || TIERS.PAYG;
        const feature = details.feature || 'this feature';
        const message = details.message || `${feature} requires ${requiredTier} tier`;

        // Remove existing modal if present
        this.closeUpgradeModal();

        const modal = document.createElement('div');
        modal.className = 'upgrade-modal-overlay active';
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
        modal.setAttribute('aria-labelledby', 'upgrade-modal-title');
        modal.innerHTML = `
            <div class="upgrade-modal">
                <div class="upgrade-modal-header">
                    <i class="ph ph-lock feature-locked-icon" aria-hidden="true"></i>
                    <h2 id="upgrade-modal-title">Upgrade Required</h2>
                    <p>${this._escapeHtml(message)}</p>
                </div>

                <div class="tier-comparison-box">
                    <div class="tier-row">
                        <span class="tier-label">Your Plan</span>
                        <span class="tier-value locked">
                            <i class="ph ph-x" aria-hidden="true"></i>
                            ${this.getTierDisplayName()}
                        </span>
                    </div>
                    <div class="tier-row">
                        <span class="tier-label">Required Plan</span>
                        <span class="tier-value unlocked">
                            <i class="ph ph-check" aria-hidden="true"></i>
                            ${this._capitalize(requiredTier)}
                        </span>
                    </div>
                    ${this._getFeatureComparison(requiredTier)}
                </div>

                <div class="upgrade-cta-buttons">
                    <button class="btn-upgrade btn-upgrade-secondary" data-action="close" aria-label="Close upgrade modal">
                        Maybe Later
                    </button>
                    <button class="btn-upgrade btn-upgrade-primary" data-action="upgrade" data-tier="${requiredTier}" aria-label="Upgrade to ${requiredTier} plan">
                        Upgrade to ${this._capitalize(requiredTier)}
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Event delegation for buttons
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeUpgradeModal();
            }
            
            const action = e.target.dataset.action;
            if (action === 'close') {
                this.closeUpgradeModal();
            } else if (action === 'upgrade') {
                this.upgradeTo(e.target.dataset.tier);
            }
        });

        // Focus trap
        const firstButton = modal.querySelector('button');
        if (firstButton) firstButton.focus();
    }

    _getFeatureComparison(targetTier) {
        const features = {
            [TIERS.PAYG]: [
                { name: 'Location Filters', current: false, target: true },
                { name: 'ISP Filters', current: false, target: true },
                { name: 'Custom Balance', current: false, target: true }
            ],
            [TIERS.PRO]: [
                { name: 'API Access', current: this.currentTier !== TIERS.FREEMIUM, target: true },
                { name: 'All Filters Included', current: false, target: true },
                { name: 'API Keys', current: '0', target: '10' },
                { name: 'Affiliate Program', current: false, target: true }
            ],
            [TIERS.CUSTOM]: [
                { name: 'API Access', current: this.currentTier === TIERS.PRO, target: true },
                { name: 'Unlimited API Keys', current: false, target: true },
                { name: 'Enhanced Affiliate', current: false, target: true },
                { name: 'Dedicated Support', current: false, target: true }
            ]
        };

        const featureList = features[targetTier] || features[TIERS.PAYG];
        return featureList.map(f => `
            <div class="tier-row">
                <span class="tier-label">${f.name}</span>
                <div style="display: flex; gap: 20px;">
                    <span class="tier-value ${f.current ? 'unlocked' : 'locked'}">
                        ${f.current || '✗'}
                    </span>
                    <span aria-hidden="true">→</span>
                    <span class="tier-value unlocked">
                        ${f.target || '✓'}
                    </span>
                </div>
            </div>
        `).join('');
    }

    closeUpgradeModal() {
        const modal = document.querySelector('.upgrade-modal-overlay');
        if (modal) {
            modal.remove();
        }
    }

    async upgradeTo(targetTier) {
        try {
            const response = await fetch(ENDPOINTS.TIERS.UPGRADE, {
                method: 'POST',
                headers: {
                    ...getAuthHeaders(),
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({ target_tier: targetTier })
            });

            if (response.ok) {
                this._showToast('Successfully upgraded! Page will reload.', 'success');
                setTimeout(() => window.location.reload(), 1500);
            } else {
                const error = await response.json();
                this._showToast(error.detail || 'Upgrade failed', 'error');
            }
        } catch (error) {
            this._log('error', 'Upgrade failed:', error);
            this._showToast('Upgrade failed. Please try again.', 'error');
        }
    }

    checkFeatureAccess(feature) {
        const allowedTiers = FEATURE_ACCESS_MAP[feature] || [];
        return allowedTiers.includes(this.currentTier);
    }

    lockFeature(element, feature, requiredTier) {
        if (!element) return;
        
        element.classList.add('feature-locked');
        element.setAttribute('aria-disabled', 'true');

        const overlay = document.createElement('div');
        overlay.className = 'feature-lock-overlay';
        overlay.innerHTML = `
            <i class="ph ph-lock" aria-hidden="true"></i>
            <h4>${FEATURE_NAMES[feature] || feature}</h4>
            <p>Available in ${this._capitalize(requiredTier)} tier</p>
            <button class="btn" data-action="show-upgrade" data-tier="${requiredTier}" data-feature="${feature}" aria-label="Upgrade to unlock ${FEATURE_NAMES[feature] || feature}">
                Upgrade Now
            </button>
        `;

        overlay.querySelector('button').addEventListener('click', () => {
            this.showUpgradeModal({
                required_tier: requiredTier,
                feature: FEATURE_NAMES[feature] || feature
            });
        });

        element.style.position = 'relative';
        element.appendChild(overlay);
    }

    unlockFeature(element) {
        if (!element) return;
        
        element.classList.remove('feature-locked');
        element.removeAttribute('aria-disabled');
        
        const overlay = element.querySelector('.feature-lock-overlay');
        if (overlay) overlay.remove();
    }

    _capitalize(str) {
        if (!str) return '';
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    _escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    _showToast(message, type = 'info') {
        if (typeof window !== 'undefined' && window.showToast) {
            window.showToast(message, type);
        } else {
            alert(message);
        }
    }

    _log(level, message, data = null) {
        if (typeof window !== 'undefined' && window.FrontendLogger) {
            window.FrontendLogger[level](message, data);
        } else {
            const logFn = level === 'error' ? console.error : level === 'warn' ? console.warn : console.log;
            logFn(`[TierManager] ${message}`, data || '');
        }
    }
}

// Factory function
export function initTierManager(options = {}) {
    const manager = new TierManager(options);
    
    // Expose globally for legacy scripts
    if (typeof window !== 'undefined') {
        window.tierManager = manager;
    }
    
    return manager;
}

// Auto-initialize on DOMContentLoaded if in browser
let tierManager;
if (typeof window !== 'undefined' && typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            tierManager = initTierManager();
        });
    } else {
        tierManager = initTierManager();
    }
}

// Attach to window for legacy scripts
if (typeof window !== 'undefined') {
    window.TierManager = TierManager;
    window.initTierManager = initTierManager;
    window.FEATURE_ACCESS_MAP = FEATURE_ACCESS_MAP;
    window.FEATURE_NAMES = FEATURE_NAMES;
}

export { tierManager };
