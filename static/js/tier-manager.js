/**
 * Tier Manager
 * Manages tier state, feature access gating, and tier UI rendering.
 */

import { TIERS, TIER_DISPLAY_NAMES, TIER_BADGE_CLASSES } from './constants.js';
import { hasAuthToken, getAuthHeaders } from './auth-helpers.js';

const FEATURE_TIER_MAP = {
    api_keys: [TIERS.PRO, TIERS.CUSTOM],
    voice_verification: [TIERS.PAYG, TIERS.PRO, TIERS.CUSTOM],
    area_code: [TIERS.PAYG, TIERS.PRO, TIERS.CUSTOM],
    isp_filter: [TIERS.PRO, TIERS.CUSTOM],
    bulk_discount: [TIERS.PRO, TIERS.CUSTOM],
    affiliate: [TIERS.PRO, TIERS.CUSTOM],
    priority_support: [TIERS.PRO, TIERS.CUSTOM],
    dedicated_support: [TIERS.CUSTOM],
};

export class TierManager {
    constructor(options = {}) {
        this.currentTier = TIERS.FREEMIUM;
        this._onTierChange = options.onTierChange || null;
        if (options.autoInit !== false) {
            this.loadCurrentTier();
        }
    }

    checkFeatureAccess(feature) {
        const allowed = FEATURE_TIER_MAP[feature];
        if (!allowed) return true;
        return allowed.includes(this.currentTier);
    }

    async loadCurrentTier() {
        if (!hasAuthToken()) return;
        try {
            const resp = await fetch('/api/tiers/current', {
                headers: getAuthHeaders(),
            });
            if (!resp.ok) return;
            const data = await resp.json();
            this.currentTier = data.current_tier || TIERS.FREEMIUM;
            if (this._onTierChange) this._onTierChange(this.currentTier);
        } catch (_) {}
    }

    renderTierBadge() {
        const existing = document.querySelector('.tier-badge');
        if (existing) existing.remove();

        const badge = document.createElement('span');
        badge.className = `tier-badge ${TIER_BADGE_CLASSES[this.currentTier] || ''}`;
        badge.textContent = TIER_DISPLAY_NAMES[this.currentTier] || this.currentTier;

        const target = document.querySelector('.header-right') || document.body;
        target.prepend(badge);
        return badge;
    }

    showUpgradeModal({ required_tier, message } = {}) {
        const overlay = document.createElement('div');
        overlay.className = 'upgrade-modal-overlay';
        overlay.style.cssText =
            'position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:9999;display:flex;align-items:center;justify-content:center;';

        const tierName = TIER_DISPLAY_NAMES[required_tier] || required_tier || 'higher';
        overlay.innerHTML = `
            <div style="background:#fff;border-radius:12px;padding:32px;max-width:400px;width:90%;text-align:center;">
                <h2 style="margin:0 0 12px;">Upgrade Required</h2>
                <p style="color:#6b7280;margin:0 0 24px;">${message || `This feature requires ${tierName} tier.`}</p>
                <a href="/pricing" style="display:inline-block;padding:12px 24px;background:#FE3C72;color:#fff;border-radius:8px;text-decoration:none;font-weight:600;">View Plans</a>
                <button onclick="this.closest('.upgrade-modal-overlay').remove()" style="display:block;margin:12px auto 0;background:none;border:none;color:#9ca3af;cursor:pointer;">Cancel</button>
            </div>`;

        document.body.appendChild(overlay);
        return overlay;
    }

    lockFeature(element, feature, required_tier) {
        element.classList.add('feature-locked');
        element.style.position = 'relative';

        const overlay = document.createElement('div');
        overlay.className = 'feature-lock-overlay';
        overlay.style.cssText =
            'position:absolute;inset:0;background:rgba(255,255,255,0.85);display:flex;align-items:center;justify-content:center;border-radius:inherit;z-index:10;';

        const tierName = TIER_DISPLAY_NAMES[required_tier] || required_tier;
        overlay.innerHTML = `<span style="font-size:13px;color:#6b7280;">Requires ${tierName}</span>`;
        element.appendChild(overlay);
    }
}

if (typeof window !== 'undefined') {
    window.TierManager = TierManager;
}
