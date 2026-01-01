/**
 * Tier Management JavaScript
 * Handles tier badge display, upgrade modals, and feature gating
 */

class TierManager {
    constructor() {
        this.currentTier = null;
        this.tierConfig = null;
        this.init();
    }

    async init() {
        await this.loadCurrentTier();
        this.renderTierBadge();
        this.setupEventListeners();
    }

    async loadCurrentTier() {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) return;

            const response = await fetch('/api/tiers/current', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.currentTier = data.current_tier;
                this.tierConfig = data;
            }
        } catch (error) {
            console.error('Failed to load tier:', error);
        }
    }

    renderTierBadge() {
        const headerRight = document.querySelector('.header-right');
        if (!headerRight || !this.currentTier) return;

        const badgeContainer = document.createElement('div');
        badgeContainer.className = 'tier-badge-container';
        badgeContainer.innerHTML = `
      <span class="tier-badge tier-badge-${this.currentTier}">
        <i class="ph ph-crown"></i>
        ${this.getTierDisplayName()}
      </span>
      ${this.currentTier === 'freemium' ? '<a href="/pricing" class="upgrade-link">Upgrade</a>' : ''}
    `;

        // Insert before balance display
        const balanceDisplay = headerRight.querySelector('.balance-display');
        if (balanceDisplay) {
            headerRight.insertBefore(badgeContainer, balanceDisplay);
        }
    }

    getTierDisplayName() {
        const names = {
            'freemium': 'Free',
            'payg': 'PAYG',
            'pro': 'Pro',
            'custom': 'Custom'
        };
        return names[this.currentTier] || 'Free';
    }

    setupEventListeners() {
        // Listen for 402 errors (Payment Required)
        window.addEventListener('fetch-error-402', (e) => {
            this.showUpgradeModal(e.detail);
        });
    }

    showUpgradeModal(details = {}) {
        const requiredTier = details.required_tier || 'payg';
        const feature = details.feature || 'this feature';
        const message = details.message || `${feature} requires ${requiredTier} tier`;

        const modal = document.createElement('div');
        modal.className = 'upgrade-modal-overlay active';
        modal.innerHTML = `
      <div class="upgrade-modal">
        <div class="upgrade-modal-header">
          <i class="ph ph-lock feature-locked-icon"></i>
          <h2>Upgrade Required</h2>
          <p>${message}</p>
        </div>

        <div class="tier-comparison-box">
          <div class="tier-row">
            <span class="tier-label">Your Plan</span>
            <span class="tier-value locked">
              <i class="ph ph-x"></i>
              ${this.getTierDisplayName()}
            </span>
          </div>
          <div class="tier-row">
            <span class="tier-label">Required Plan</span>
            <span class="tier-value unlocked">
              <i class="ph ph-check"></i>
              ${requiredTier.charAt(0).toUpperCase() + requiredTier.slice(1)}
            </span>
          </div>
          ${this.getFeatureComparison(requiredTier)}
        </div>

        <div class="upgrade-cta-buttons">
          <button class="btn-upgrade btn-upgrade-secondary" onclick="tierManager.closeUpgradeModal()">
            Maybe Later
          </button>
          <button class="btn-upgrade btn-upgrade-primary" onclick="tierManager.upgradeTo('${requiredTier}')">
            Upgrade to ${requiredTier.charAt(0).toUpperCase() + requiredTier.slice(1)}
          </button>
        </div>
      </div>
    `;

        document.body.appendChild(modal);

        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeUpgradeModal();
            }
        });
    }

    getFeatureComparison(targetTier) {
        const features = {
            'payg': [
                { name: 'Location Filters', current: false, target: true },
                { name: 'ISP Filters', current: false, target: true },
                { name: 'Custom Balance', current: false, target: true }
            ],
            'pro': [
                { name: 'API Access', current: this.currentTier !== 'freemium', target: true },
                { name: 'All Filters Included', current: false, target: true },
                { name: 'API Keys', current: this.currentTier === 'payg' ? '0' : '0', target: '10' },
                { name: 'Affiliate Program', current: false, target: true }
            ],
            'custom': [
                { name: 'API Access', current: this.currentTier === 'pro', target: true },
                { name: 'Unlimited API Keys', current: false, target: true },
                { name: 'Enhanced Affiliate', current: false, target: true },
                { name: 'Dedicated Support', current: false, target: true }
            ]
        };

        const featureList = features[targetTier] || features.payg;
        return featureList.map(f => `
      <div class="tier-row">
        <span class="tier-label">${f.name}</span>
        <div style="display: flex; gap: 20px;">
          <span class="tier-value ${f.current ? 'unlocked' : 'locked'}">
            ${f.current || '✗'}
          </span>
          <span>→</span>
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
            const token = localStorage.getItem('access_token');
            const response = await fetch('/api/tiers/upgrade', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ target_tier: targetTier })
            });

            if (response.ok) {
                alert('Successfully upgraded! Page will reload.');
                window.location.reload();
            } else {
                const error = await response.json();
                alert(error.detail || 'Upgrade failed');
            }
        } catch (error) {
            console.error('Upgrade failed:', error);
            alert('Upgrade failed. Please try again.');
        }
    }

    checkFeatureAccess(feature) {
        const featureMap = {
            'api_keys': ['pro', 'custom'],
            'location_filters': ['payg', 'pro', 'custom'],
            'isp_filter': ['payg', 'pro', 'custom'],
            'affiliate_program': ['pro', 'custom']
        };

        const allowedTiers = featureMap[feature] || [];
        return allowedTiers.includes(this.currentTier);
    }

    lockFeature(element, feature, requiredTier) {
        element.classList.add('feature-locked');

        const overlay = document.createElement('div');
        overlay.className = 'feature-lock-overlay';
        overlay.innerHTML = `
      <i class="ph ph-lock"></i>
      <h4>${this.getFeatureName(feature)}</h4>
      <p>Available in ${requiredTier.charAt(0).toUpperCase() + requiredTier.slice(1)} tier</p>
      <button class="btn" onclick="tierManager.showUpgradeModal({
        required_tier: '${requiredTier}',
        feature: '${this.getFeatureName(feature)}'
      })">
        Upgrade Now
      </button>
    `;

        element.style.position = 'relative';
        element.appendChild(overlay);
    }

    getFeatureName(feature) {
        const names = {
            'api_keys': 'API Keys',
            'location_filters': 'Location Filters',
            'isp_filter': 'ISP/Carrier Filtering',
            'affiliate_program': 'Affiliate Program'
        };
        return names[feature] || feature;
    }
}

// Initialize tier manager
let tierManager;
document.addEventListener('DOMContentLoaded', () => {
    tierManager = new TierManager();
});

// Export for use in other scripts
window.TierManager = TierManager;
window.tierManager = tierManager;
