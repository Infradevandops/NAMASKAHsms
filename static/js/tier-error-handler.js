/**
 * Tier Error Handler
 * 
 * Intercepts HTTP 402 (Payment Required) responses globally and displays
 * the tier-locked modal to guide users to upgrade their subscription.
 * 
 * Feature: tier-system-rbac
 * Validates: Requirements 13.1, 13.2, 13.3, 13.4, 13.5
 */

(function() {
    'use strict';

    // Store original fetch
    const originalFetch = window.fetch;

    /**
     * Enhanced fetch that intercepts 402 responses
     */
    window.fetch = async function(...args) {
        try {
            const response = await originalFetch.apply(this, args);
            
            // Check for 402 Payment Required
            if (response.status === 402) {
                await handle402Response(response.clone(), args[0]);
            }
            
            return response;
        } catch (error) {
            throw error;
        }
    };

    /**
     * Handle 402 Payment Required response
     * @param {Response} response - The fetch response
     * @param {string|Request} url - The request URL
     */
    async function handle402Response(response, url) {
        try {
            const data = await response.json();
            const detail = data.detail || {};
            
            // Extract tier information from response
            const options = {
                message: typeof detail === 'string' ? detail : detail.message,
                requiredTier: detail.required_tier || 'payg',
                currentTier: detail.current_tier || 'freemium',
                upgradeUrl: detail.upgrade_url || '/pricing'
            };
            
            // Show tier-locked modal if available
            if (typeof window.showTierLockedModal === 'function') {
                window.showTierLockedModal(options);
            } else {
                // Fallback: show alert and redirect
                const tierName = getTierDisplayName(options.requiredTier);
                const message = options.message || `This feature requires ${tierName} tier or higher.`;
                
                if (confirm(message + '\n\nWould you like to upgrade now?')) {
                    window.location.href = options.upgradeUrl;
                }
            }
            
            console.log('[TierErrorHandler] 402 intercepted:', {
                url: typeof url === 'string' ? url : url.url,
                requiredTier: options.requiredTier,
                currentTier: options.currentTier
            });
            
        } catch (parseError) {
            console.error('[TierErrorHandler] Failed to parse 402 response:', parseError);
            
            // Fallback for non-JSON responses
            if (typeof window.showTierLockedModal === 'function') {
                window.showTierLockedModal({
                    message: 'This feature requires a higher subscription tier.',
                    requiredTier: 'payg'
                });
            }
        }
    }

    /**
     * Get display name for tier code
     * @param {string} tier - Tier code
     * @returns {string} Display name
     */
    function getTierDisplayName(tier) {
        const names = {
            'freemium': 'Freemium',
            'payg': 'Pay-As-You-Go',
            'pro': 'Pro',
            'custom': 'Custom'
        };
        return names[tier] || tier;
    }

    /**
     * Intercept XMLHttpRequest for legacy code
     */
    const originalXHROpen = XMLHttpRequest.prototype.open;
    const originalXHRSend = XMLHttpRequest.prototype.send;

    XMLHttpRequest.prototype.open = function(method, url, ...rest) {
        this._url = url;
        return originalXHROpen.apply(this, [method, url, ...rest]);
    };

    XMLHttpRequest.prototype.send = function(...args) {
        this.addEventListener('load', function() {
            if (this.status === 402) {
                handleXHR402Response(this);
            }
        });
        return originalXHRSend.apply(this, args);
    };

    /**
     * Handle 402 response from XMLHttpRequest
     * @param {XMLHttpRequest} xhr - The XHR object
     */
    function handleXHR402Response(xhr) {
        try {
            const data = JSON.parse(xhr.responseText);
            const detail = data.detail || {};
            
            const options = {
                message: typeof detail === 'string' ? detail : detail.message,
                requiredTier: detail.required_tier || 'payg',
                currentTier: detail.current_tier || 'freemium',
                upgradeUrl: detail.upgrade_url || '/pricing'
            };
            
            if (typeof window.showTierLockedModal === 'function') {
                window.showTierLockedModal(options);
            }
            
            console.log('[TierErrorHandler] XHR 402 intercepted:', {
                url: xhr._url,
                requiredTier: options.requiredTier
            });
            
        } catch (e) {
            console.error('[TierErrorHandler] Failed to handle XHR 402:', e);
        }
    }

    /**
     * Manual trigger for testing
     * @param {Object} options - Modal options
     */
    window.triggerTierLocked = function(options = {}) {
        if (typeof window.showTierLockedModal === 'function') {
            window.showTierLockedModal(options);
        } else {
            console.error('[TierErrorHandler] showTierLockedModal not available');
        }
    };

    // Log initialization
    console.log('[TierErrorHandler] Initialized - intercepting 402 responses');

})();
