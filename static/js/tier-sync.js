/**
 * Tier Synchronization System
 * 
 * Ensures tier consistency across:
 * - Multiple tabs/windows
 * - Page refreshes
 * - Tier changes
 * 
 * Implements:
 * - Cross-tab storage events
 * - Periodic verification
 * - Tier change events
 * - Automatic reload on mismatch
 */

class TierSync {
    static VERIFICATION_INTERVAL = 60000;  // 1 minute
    static verificationTimer = null;
    
    /**
     * Start tier synchronization
     * 
     * Listens for:
     * - Storage events (tier changes in other tabs)
     * - Periodic verification (every minute)
     */
    static startSync() {
        console.log('[TierSync] Starting...');
        
        // Listen for storage events (tier changes in other tabs)
        window.addEventListener('storage', (e) => {
            if (e.key === 'nsk_tier_cache') {
                this.handleStorageChange(e);
            }
        });
        
        // Periodically verify tier hasn't changed
        this.verificationTimer = setInterval(() => {
            this.verifyTier();
        }, this.VERIFICATION_INTERVAL);
        
        console.log('[TierSync] Started');
    }
    
    /**
     * Handle storage change event (tier changed in another tab)
     * 
     * @param {StorageEvent} e - Storage event
     */
    static handleStorageChange(e) {
        try {
            const newValue = e.newValue ? JSON.parse(e.newValue) : null;
            const newTier = newValue?.tier;
            
            if (newTier && newTier !== window.APP_STATE?.tier) {
                console.log(`[TierSync] Tier changed in another tab: ${window.APP_STATE?.tier} → ${newTier}`);
                
                // Emit event
                this.emitTierChangeEvent(newTier);
                
                // Update global state
                if (window.APP_STATE) {
                    window.APP_STATE.tier = newTier;
                    window.APP_STATE.tierRankValue = { freemium: 0, payg: 1, pro: 2, custom: 3 }[newTier];
                }
                
                // Reload page to reflect changes
                console.log('[TierSync] Reloading page to reflect tier change');
                setTimeout(() => window.location.reload(), 500);
            }
        } catch (error) {
            console.error('[TierSync] Error handling storage change:', error);
        }
    }
    
    /**
     * Verify tier hasn't changed on server
     * 
     * Periodically checks if tier has changed on the server side
     * (e.g., due to expiration or admin action)
     */
    static async verifyTier() {
        try {
            const response = await fetch('/api/tiers/current', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                    'Cache-Control': 'no-cache'
                }
            });
            
            if (!response.ok) {
                console.warn('[TierSync] Verification failed:', response.status);
                return;
            }
            
            const data = await response.json();
            const serverTier = (data.current_tier || 'freemium').toLowerCase();
            const localTier = window.APP_STATE?.tier || 'freemium';
            
            if (serverTier !== localTier) {
                console.warn(
                    `[TierSync] Tier mismatch detected: local=${localTier}, server=${serverTier}`
                );
                
                // Update cache
                if (typeof TierLoader !== 'undefined') {
                    TierLoader.cacheTier(serverTier);
                }
                
                // Update global state
                if (window.APP_STATE) {
                    window.APP_STATE.tier = serverTier;
                    window.APP_STATE.tierRankValue = { freemium: 0, payg: 1, pro: 2, custom: 3 }[serverTier];
                }
                
                // Emit event
                this.emitTierChangeEvent(serverTier);
                
                // Reload page
                console.log('[TierSync] Reloading page due to tier mismatch');
                setTimeout(() => window.location.reload(), 500);
            }
        } catch (error) {
            console.error('[TierSync] Verification error:', error);
        }
    }
    
    /**
     * Emit tier change event
     * 
     * Allows other parts of the app to listen for tier changes
     * 
     * @param {string} newTier - New tier value
     */
    static emitTierChangeEvent(newTier) {
        try {
            const event = new CustomEvent('tier:changed', {
                detail: { tier: newTier }
            });
            window.dispatchEvent(event);
            console.log('[TierSync] Tier change event emitted:', newTier);
        } catch (error) {
            console.error('[TierSync] Error emitting event:', error);
        }
    }
    
    /**
     * Listen for tier changes
     * 
     * Usage:
     * TierSync.on('changed', (newTier) => {
     *   console.log('Tier changed to:', newTier);
     * });
     * 
     * @param {string} event - Event name ('changed')
     * @param {Function} callback - Callback function
     */
    static on(event, callback) {
        if (event === 'changed') {
            window.addEventListener('tier:changed', (e) => {
                callback(e.detail.tier);
            });
        }
    }
    
    /**
     * Stop tier synchronization
     * 
     * Clears verification timer and removes listeners
     */
    static stopSync() {
        if (this.verificationTimer) {
            clearInterval(this.verificationTimer);
            this.verificationTimer = null;
        }
        console.log('[TierSync] Stopped');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TierSync;
}
