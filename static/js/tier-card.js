/**
 * Tier Card Module
 * Handles tier display, loading states, and CTA buttons
 * 
 * Extracted from inline dashboard.html script for:
 * - Better cacheability
 * - Testability
 * - Maintainability
 */

import { 
    TIMEOUTS, 
    STATES, 
    ENDPOINTS,
    TIER_DISPLAY_NAMES, 
    TIER_BADGE_CLASSES, 
    TIER_FEATURES,
    TIER_CTA_CONFIG,
    STORAGE_KEYS
} from './constants.js';
import { hasAuthToken, getAuthHeaders } from './auth-helpers.js';

/**
 * TierCard class - manages the tier card widget
 */
export class TierCard {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        
        if (!this.container) {
            console.error(`TierCard: Container #${containerId} not found`);
            return;
        }

        // Configuration
        this.timeout = options.timeout || TIMEOUTS.API_REQUEST;
        this.failsafeTimeout = options.failsafeTimeout || TIMEOUTS.FAILSAFE;
        this.refreshInterval = options.refreshInterval || TIMEOUTS.REFRESH_INTERVAL;
        this.onStateChange = options.onStateChange || null;

        // State
        this.state = STATES.INITIAL;
        this.currentData = null;
        this.abortController = null;
        this.timeoutId = null;
        this.failsafeId = null;
        this.refreshIntervalId = null;

        // Element references
        this.elements = {
            tierName: document.getElementById('tier-name'),
            tierPrice: document.getElementById('tier-price'),
            featuresList: document.getElementById('tier-features-list'),
            ctaButtons: {
                upgrade: document.getElementById('upgrade-btn'),
                compare: document.getElementById('compare-plans-btn'),
                addCredits: document.getElementById('add-credits-btn'),
                usage: document.getElementById('usage-btn'),
                manage: document.getElementById('manage-btn'),
                contact: document.getElementById('contact-btn')
            }
        };

        // Bind methods
        this.load = this.load.bind(this);
        this.retry = this.retry.bind(this);
    }

    /**
     * Initialize the tier card
     */
    init() {
        this.load();
        this.startAutoRefresh();
        this.setupFailsafe();
    }

    /**
     * Set up failsafe timeout
     */
    setupFailsafe() {
        this.failsafeId = setTimeout(() => {
            if (this.state === STATES.LOADING) {
                this._log('warn', `Failsafe triggered after ${this.failsafeTimeout}ms`);
                this.setState(STATES.TIMEOUT);
            }
        }, this.failsafeTimeout);
    }

    /**
     * Start auto-refresh interval
     */
    startAutoRefresh() {
        if (this.refreshIntervalId) {
            clearInterval(this.refreshIntervalId);
        }
        
        this.refreshIntervalId = setInterval(() => {
            if (hasAuthToken()) {
                this.load();
            }
        }, this.refreshInterval);
    }

    /**
     * Stop auto-refresh
     */
    stopAutoRefresh() {
        if (this.refreshIntervalId) {
            clearInterval(this.refreshIntervalId);
            this.refreshIntervalId = null;
        }
    }

    /**
     * Load tier information
     */
    async load() {
        this._log('info', 'Loading tier information...');

        // Clear previous timers
        this._clearTimers();

        // Check authentication
        if (!hasAuthToken()) {
            this._log('warn', 'No auth token found');
            this.setState(STATES.UNAUTHENTICATED);
            return;
        }

        this.setState(STATES.LOADING);

        // Create abort controller for timeout
        this.abortController = new AbortController();

        // Set request timeout
        this.timeoutId = setTimeout(() => {
            this._log('warn', `Request timeout after ${this.timeout}ms`);
            this.abortController.abort();
            this.setState(STATES.TIMEOUT);
        }, this.timeout);

        try {
            this._log('info', `API Call: GET ${ENDPOINTS.TIERS.CURRENT}`);

            const response = await fetch(ENDPOINTS.TIERS.CURRENT, {
                credentials: 'include',
                headers: getAuthHeaders(),
                signal: this.abortController.signal
            });

            this._clearTimers();
            this._log('info', `API Response: ${response.status}`);

            // Handle 401 Unauthorized
            if (response.status === 401) {
                this._log('warn', '401 Unauthorized - session may have expired');
                this.setState(STATES.SESSION_EXPIRED);
                return;
            }

            // Handle other errors
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // Parse response
            const data = await response.json();
            this.currentData = data;

            // Cache data for fallback
            this._cacheData(data);

            this._log('info', 'Tier loaded successfully', { tier: data.current_tier });
            this.setState(STATES.LOADED, data);

        } catch (error) {
            this._clearTimers();

            // Ignore abort errors (handled by timeout)
            if (error.name === 'AbortError') {
                return;
            }

            this._log('error', 'Tier load failed', { error: error.message });

            // Try cached data as fallback
            const cachedData = this._getCachedData();
            if (cachedData) {
                this._log('info', 'Using cached tier data as fallback');
                this.setState(STATES.LOADED, cachedData);
                this._showCacheWarning();
                return;
            }

            this.setState(STATES.ERROR, { message: error.message });
        }
    }

    /**
     * Retry loading
     */
    retry() {
        this.load();
    }

    /**
     * Set the current state and update UI
     */
    setState(state, data = null) {
        this.state = state;

        // Update container classes
        this.container.classList.remove(
            'tier-card-loading',
            'tier-card-error',
            'tier-card-loaded'
        );

        // Update aria attributes
        this.container.setAttribute('aria-busy', state === STATES.LOADING ? 'true' : 'false');

        switch (state) {
            case STATES.LOADING:
                this.container.classList.add('tier-card-loading');
                this._renderLoading();
                break;

            case STATES.UNAUTHENTICATED:
                this.container.classList.add('tier-card-error');
                this._renderUnauthenticated();
                break;

            case STATES.SESSION_EXPIRED:
                this.container.classList.add('tier-card-error');
                this._renderSessionExpired();
                break;

            case STATES.TIMEOUT:
                this.container.classList.add('tier-card-error');
                this._renderTimeout();
                break;

            case STATES.ERROR:
                this.container.classList.add('tier-card-error');
                this._renderError(data?.message);
                break;

            case STATES.LOADED:
                this.container.classList.add('tier-card-loaded');
                this._renderLoaded(data);
                break;
        }

        // Call state change callback
        if (this.onStateChange) {
            this.onStateChange(state, data);
        }
    }

    /**
     * Render loading state
     */
    _renderLoading() {
        this.elements.tierName.innerHTML = '<span class="loading-spinner"></span> Loading...';
        this.elements.tierPrice.textContent = '';
        this.elements.featuresList.innerHTML = '';
        this._hideAllCTAs();
    }

    /**
     * Render unauthenticated state
     */
    _renderUnauthenticated() {
        this.elements.tierName.innerHTML = '🔒 Not logged in';
        this.elements.tierPrice.textContent = '';
        this.elements.featuresList.innerHTML = `
            <div style="margin-top: 12px;">
                <a href="/auth/login" class="btn btn-primary" aria-label="Log in to view your subscription plan">
                    Log in to view your plan
                </a>
            </div>
        `;
        this._hideAllCTAs();
    }

    /**
     * Render session expired state
     */
    _renderSessionExpired() {
        this.elements.tierName.innerHTML = '🔐 Session expired';
        this.elements.tierPrice.textContent = '';
        this.elements.featuresList.innerHTML = `
            <div style="margin-top: 12px;">
                <a href="/auth/login" class="btn btn-primary" aria-label="Log in again to continue">
                    Log in again
                </a>
            </div>
        `;
        this._hideAllCTAs();
    }

    /**
     * Render timeout state
     */
    _renderTimeout() {
        this.elements.tierName.innerHTML = '⏱️ Request timed out';
        this.elements.tierPrice.textContent = '';
        this.elements.featuresList.innerHTML = `
            <div style="color: var(--text-muted); margin-bottom: 12px;">
                The server took too long to respond.
            </div>
            <button class="btn btn-secondary" onclick="window.tierCard?.retry()" aria-label="Try loading tier information again">
                🔄 Try again
            </button>
        `;
        this._hideAllCTAs();
    }

    /**
     * Render error state
     */
    _renderError(message) {
        const errorMsg = message || 'Unable to load plan information';
        this.elements.tierName.innerHTML = '⚠️ Error';
        this.elements.tierPrice.textContent = '';
        this.elements.featuresList.innerHTML = `
            <div style="color: var(--text-muted); margin-bottom: 12px;">
                ${this._escapeHtml(errorMsg)}
            </div>
            <button class="btn btn-secondary" onclick="window.tierCard?.retry()" aria-label="Retry loading tier information">
                🔄 Retry
            </button>
        `;
        // Show upgrade button as fallback action
        if (this.elements.ctaButtons.upgrade) {
            this.elements.ctaButtons.upgrade.style.display = 'inline-flex';
        }
    }

    /**
     * Render loaded state with tier data
     */
    _renderLoaded(data) {
        const tierCode = data.current_tier || 'freemium';
        const tierName = TIER_DISPLAY_NAMES[tierCode] || 'Unknown';
        const badgeClass = TIER_BADGE_CLASSES[tierCode] || '';

        // Render tier name with badge
        this.elements.tierName.innerHTML = `
            <span class="tier-badge ${badgeClass}" style="font-size: 18px; padding: 6px 16px;">
                ${tierName}
            </span>
        `;

        // Render price
        if (data.price_monthly !== undefined) {
            this.elements.tierPrice.textContent = data.price_monthly === 0 
                ? 'Free' 
                : `$${data.price_monthly}/month`;
        }

        // Render features
        const features = TIER_FEATURES[tierCode] || [{ text: 'Basic features included', available: true }];
        let featuresHtml = '';
        
        for (const feature of features) {
            const icon = feature.available ? '✓' : '✗';
            const style = feature.available 
                ? 'color: var(--tier-freemium);' 
                : 'color: var(--text-muted);';
            featuresHtml += `<div style="margin-bottom: 4px; ${style}">${icon} ${feature.text}</div>`;
        }

        // Add quota info if available
        if (data.quota_usd > 0) {
            featuresHtml += `<div style="margin-bottom: 4px; color: var(--tier-freemium);">✓ $${data.quota_usd} monthly quota</div>`;
        }

        this.elements.featuresList.innerHTML = featuresHtml;

        // Render CTAs
        this._renderCTAs(tierCode);

        // Show quota card if applicable
        this._updateQuotaDisplay(tierCode, data);
    }

    /**
     * Render CTA buttons based on tier
     */
    _renderCTAs(tierCode) {
        const config = TIER_CTA_CONFIG[tierCode] || TIER_CTA_CONFIG.freemium;
        this._hideAllCTAs();

        for (const cta of config) {
            const btn = this.elements.ctaButtons[cta.id.replace('-btn', '').replace('compare-plans', 'compare').replace('add-credits', 'addCredits')];
            if (!btn) continue;

            btn.style.display = 'inline-flex';
            btn.className = `btn btn-${cta.variant}`;
            btn.textContent = cta.label;
            btn.setAttribute('aria-label', `${cta.label} - ${TIER_DISPLAY_NAMES[tierCode]} tier action`);

            // Set click handler
            if (cta.href) {
                btn.onclick = () => { window.location.href = cta.href; };
            } else if (cta.action && typeof window[cta.action] === 'function') {
                btn.onclick = () => { window[cta.action](); };
            }
        }
    }

    /**
     * Hide all CTA buttons
     */
    _hideAllCTAs() {
        for (const btn of Object.values(this.elements.ctaButtons)) {
            if (btn) btn.style.display = 'none';
        }
    }

    /**
     * Update quota display
     */
    _updateQuotaDisplay(tierCode, data) {
        const quotaCard = document.getElementById('quota-card');
        const apiStatsCard = document.getElementById('api-stats-card');

        if (tierCode !== 'freemium' && data.quota_usd > 0 && quotaCard) {
            quotaCard.style.display = 'block';
            
            const quotaUsed = data.quota_used_usd || 0;
            const quotaLimit = data.quota_usd || 0;
            const percentage = quotaLimit > 0 ? Math.min((quotaUsed / quotaLimit) * 100, 100) : 0;

            const quotaFill = document.getElementById('quota-fill');
            const quotaText = document.getElementById('quota-text');

            if (quotaFill) {
                quotaFill.style.width = `${percentage}%`;
                quotaFill.style.background = percentage >= 100 ? '#ef4444' 
                    : percentage > 80 ? '#f59e0b' 
                    : 'var(--primary)';
            }

            if (quotaText) {
                quotaText.textContent = `$${quotaUsed.toFixed(2)} / $${quotaLimit.toFixed(2)}`;
            }
        }

        if (tierCode !== 'freemium' && apiStatsCard) {
            apiStatsCard.style.display = 'block';
            
            const smsCount = document.getElementById('api-sms-count');
            const apiCalls = document.getElementById('api-calls-count');
            const apiKeys = document.getElementById('api-keys-count');

            if (smsCount) smsCount.textContent = data.sms_count || 0;
            if (apiCalls) apiCalls.textContent = data.sms_count || 0;
            if (apiKeys) apiKeys.textContent = data.features?.api_key_limit || 0;
        }
    }

    /**
     * Show cache warning indicator
     */
    _showCacheWarning() {
        const warning = document.createElement('div');
        warning.style.cssText = 'color: var(--tier-pro); font-size: 12px; margin-top: 8px;';
        warning.textContent = '⚠️ Showing cached data';
        this.elements.featuresList.appendChild(warning);
    }

    /**
     * Cache tier data to localStorage
     */
    _cacheData(data) {
        try {
            localStorage.setItem(STORAGE_KEYS.CACHED_TIER, JSON.stringify(data));
        } catch (e) {
            // Ignore storage errors
        }
    }

    /**
     * Get cached tier data
     */
    _getCachedData() {
        try {
            const cached = localStorage.getItem(STORAGE_KEYS.CACHED_TIER);
            return cached ? JSON.parse(cached) : null;
        } catch (e) {
            return null;
        }
    }

    /**
     * Clear all timers
     */
    _clearTimers() {
        if (this.timeoutId) {
            clearTimeout(this.timeoutId);
            this.timeoutId = null;
        }
        if (this.failsafeId) {
            clearTimeout(this.failsafeId);
            this.failsafeId = null;
        }
    }

    /**
     * Escape HTML to prevent XSS
     */
    _escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Log helper
     */
    _log(level, message, data = null) {
        if (window.FrontendLogger) {
            window.FrontendLogger[level](message, data);
        } else {
            console[level === 'error' ? 'error' : level === 'warn' ? 'warn' : 'log'](
                `[TierCard] ${message}`,
                data || ''
            );
        }
    }

    /**
     * Destroy the tier card instance
     */
    destroy() {
        this._clearTimers();
        this.stopAutoRefresh();
        
        if (this.abortController) {
            this.abortController.abort();
        }
    }
}

// Factory function for easy initialization
export function initTierCard(containerId = 'tier-card', options = {}) {
    const tierCard = new TierCard(containerId, options);
    tierCard.init();
    
    // Expose globally for onclick handlers
    window.tierCard = tierCard;
    
    return tierCard;
}

// For non-module scripts (IIFE compatibility)
if (typeof window !== 'undefined') {
    window.TierCard = TierCard;
    window.initTierCard = initTierCard;
}
