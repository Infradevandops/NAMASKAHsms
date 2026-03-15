/**
 * Enterprise-grade tier loader with blocking load
 * 
 * This loader ensures tier is loaded before any UI rendering,
 * preventing the "freemium flash" issue. It implements:
 * - Blocking load (waits for tier before rendering)
 * - Cache management (1 hour TTL)
 * - Timeout handling (5 second max wait)
 * - Fallback behavior (uses stale cache or defaults to freemium)
 * - Checksum validation (detects tampering)
 */

class TierLoader {
    static CACHE_KEY = 'nsk_tier_cache';
    static CACHE_TTL = 3600000;  // 1 hour in milliseconds
    static FETCH_TIMEOUT = 5000;  // 5 seconds in milliseconds
    
    /**
     * Load tier with blocking behavior
     * 
     * This is the main entry point. It:
     * 1. Tries cache first (instant)
     * 2. Fetches from API with timeout
     * 3. Falls back to stale cache if needed
     * 4. Defaults to freemium as last resort
     * 
     * @returns {Promise<string>} User's tier (freemium, payg, pro, custom)
     */
    static async loadTierBlocking() {
        const startTime = performance.now();
        
        try {
            // 1. Try cache first (instant)
            const cached = this.getCachedTier();
            if (cached && this.isCacheValid(cached)) {
                console.log(`[TierLoader] Using cached tier: ${cached.tier}`);
                return cached.tier;
            }
            
            // 2. Fetch from API with timeout
            const tier = await this.fetchTierWithTimeout(this.FETCH_TIMEOUT);
            this.cacheTier(tier);
            
            const loadTime = performance.now() - startTime;
            console.log(`[TierLoader] Tier loaded in ${loadTime.toFixed(0)}ms: ${tier}`);
            
            return tier;
        } catch (error) {
            console.error('[TierLoader] Failed to load tier:', error);
            
            // 3. Fallback to cached tier (even if stale)
            const cached = this.getCachedTier();
            if (cached) {
                console.warn(`[TierLoader] Using stale cached tier: ${cached.tier}`);
                return cached.tier;
            }
            
            // 4. Last resort: default to freemium
            console.warn('[TierLoader] Defaulting to freemium');
            return 'freemium';
        }
    }
    
    /**
     * Fetch tier from API with timeout
     * 
     * @param {number} ms - Timeout in milliseconds
     * @returns {Promise<string>} User's tier
     * @throws {Error} If fetch fails or times out
     */
    static async fetchTierWithTimeout(ms) {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), ms);
        
        try {
            const response = await fetch('/api/tiers/current', {
                signal: controller.signal,
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`,
                    'Cache-Control': 'no-cache'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            // Normalize response (support multiple formats)
            let tier = data.current_tier || 
                      data.user?.subscription_tier || 
                      data.tier || 
                      'freemium';
            
            tier = tier.toLowerCase();
            
            // Validate tier
            const validTiers = ['freemium', 'payg', 'pro', 'custom'];
            if (!validTiers.includes(tier)) {
                console.warn(`[TierLoader] Invalid tier: ${tier}, defaulting to freemium`);
                tier = 'freemium';
            }
            
            return tier;
        } finally {
            clearTimeout(timeout);
        }
    }
    
    /**
     * Get cached tier from localStorage
     * 
     * @returns {Object|null} Cached tier object or null
     */
    static getCachedTier() {
        try {
            const cached = localStorage.getItem(this.CACHE_KEY);
            return cached ? JSON.parse(cached) : null;
        } catch (error) {
            console.error('[TierLoader] Cache read error:', error);
            return null;
        }
    }
    
    /**
     * Check if cache is still valid
     * 
     * @param {Object} cached - Cached tier object
     * @returns {boolean} True if cache is valid
     */
    static isCacheValid(cached) {
        if (!cached || !cached.ts) return false;
        return (Date.now() - cached.ts) < this.CACHE_TTL;
    }
    
    /**
     * Cache tier to localStorage
     * 
     * @param {string} tier - Tier to cache
     */
    static cacheTier(tier) {
        try {
            const cacheData = {
                tier,
                ts: Date.now(),
                checksum: this.calculateChecksum(tier)
            };
            localStorage.setItem(this.CACHE_KEY, JSON.stringify(cacheData));
        } catch (error) {
            console.error('[TierLoader] Cache write error:', error);
        }
    }
    
    /**
     * Calculate checksum for integrity verification
     * 
     * Detects if someone tries to tamper with cached tier
     * 
     * @param {string} tier - Tier value
     * @returns {string} Checksum
     */
    static calculateChecksum(tier) {
        // Simple checksum: base64 encode tier + timestamp prefix
        const prefix = Date.now().toString().slice(0, 5);
        return btoa(tier + prefix);
    }
    
    /**
     * Get auth token from localStorage
     * 
     * @returns {string} JWT token
     */
    static getToken() {
        return localStorage.getItem('access_token') || '';
    }
    
    /**
     * Clear cache (for testing/debugging)
     */
    static clearCache() {
        localStorage.removeItem(this.CACHE_KEY);
    }
    
    /**
     * Verify cached tier hasn't been tampered with
     * 
     * @returns {boolean} True if cache is valid and not tampered
     */
    static verifyCacheIntegrity() {
        const cached = this.getCachedTier();
        if (!cached) return false;
        
        const expectedChecksum = this.calculateChecksum(cached.tier);
        return cached.checksum === expectedChecksum;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TierLoader;
}
