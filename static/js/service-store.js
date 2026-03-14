/**
 * ServiceStore - Single source of truth for service data
 * Implements stale-while-revalidate caching strategy
 * 
 * Usage:
 *   await ServiceStore.init();  // Load services on page load
 *   const services = ServiceStore.getAll();  // Get all services
 *   const results = ServiceStore.search('apple');  // Search services
 */

const ServiceStore = {
    // State
    services: [],
    loading: false,
    error: null,
    lastFetch: null,
    source: null,
    
    // Config
    CACHE_KEY: 'nsk_services_v5',
    CACHE_TTL: 6 * 60 * 60 * 1000,  // 6 hours
    STALE_THRESHOLD: 3 * 60 * 60 * 1000,  // 3 hours
    MIN_SERVICES: 1,
    
    /**
     * Initialize store - load from cache or API
     * Always returns immediately with cached data if available
     * Refreshes in background if stale
     */
    async init() {
        console.log('🔄 ServiceStore: Initializing...');
        
        // Try cache first
        const cached = this._loadFromCache();
        
        if (cached && this._isCacheValid(cached)) {
            // Use cache immediately
            this.services = cached.services;
            this.lastFetch = cached.timestamp;
            this.source = 'cache';
            const age = Math.round((Date.now() - cached.timestamp) / 60000);
            console.log(`✅ ServiceStore: Loaded ${this.services.length} services from cache (age: ${age}m)`);
            
            // Background refresh if stale
            if (this._isStale(cached)) {
                console.log('🔄 ServiceStore: Cache stale, refreshing in background...');
                this.refresh();
            }
            
            return;
        }
        
        // Cache invalid/missing - fetch immediately
        console.log('🌐 ServiceStore: Cache expired/missing, fetching from API...');
        await this.fetch();
    },
    
    /**
     * Fetch services from API with retry logic
     */
    async fetch() {
        if (this.loading) return;
        
        this.loading = true;
        this.error = null;
        
        const maxRetries = 3;
        let lastError = null;
        
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                const token = localStorage.getItem('access_token');
                const ctrl = new AbortController();
                const tid = setTimeout(() => ctrl.abort(), 15000);
                
                const res = await fetch('/api/countries/US/services', {
                    headers: token ? { 'Authorization': `Bearer ${token}` } : {},
                    signal: ctrl.signal
                });
                clearTimeout(tid);
                
                // Handle 401 - retry without auth (endpoint is public)
                let finalRes = res;
                if (res.status === 401) {
                    const retryRes = await fetch('/api/countries/US/services');
                    if (!retryRes.ok) throw new Error('fetch failed after 401 retry');
                    finalRes = retryRes;
                } else if (!res.ok) {
                    throw new Error(`fetch failed: ${res.status}`);
                }
                
                const data = await finalRes.json();
                
                // Check if API returned error
                if (data.source === 'error' || data.error) {
                    throw new Error(data.error || 'API returned error');
                }
                
                const services = data.services || [];
                
                if (services.length === 0) {
                    throw new Error('API returned zero services');
                }
                
                // Success - update state and cache
                this.services = services;
                this.lastFetch = Date.now();
                this.source = data.source || 'api';
                this._saveToCache(services, this.source);
                
                console.log(`✅ ServiceStore: Loaded ${services.length} services from ${this.source}`);
                this.loading = false;
                return;
                
            } catch (e) {
                lastError = e;
                console.warn(`⚠️ ServiceStore: Attempt ${attempt}/${maxRetries} failed:`, e.message);
                
                if (attempt < maxRetries) {
                    await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
                    continue;
                }
            }
        }
        
        // All retries failed
        console.error('❌ ServiceStore: All API attempts failed:', lastError);
        this.error = lastError.message;
        
        // Try stale cache as last resort
        const staleCache = this._loadFromCache();
        if (staleCache && staleCache.services.length > 0) {
            this.services = staleCache.services;
            this.lastFetch = staleCache.timestamp;
            this.source = 'stale-cache';
            const age = Math.round((Date.now() - staleCache.timestamp) / 60000);
            console.warn(`⚠️ ServiceStore: Using stale cache (${staleCache.count} services, age: ${age}m)`);
        } else {
            // NO FALLBACK - throw error
            console.error('💥 ServiceStore: No cache available, TextVerified API is required');
            this.services = [];
            throw new Error('TextVerified API is unavailable and no cached data exists. Please contact support.');
        }
        
        this.loading = false;
    },
    
    /**
     * Background refresh (non-blocking)
     */
    async refresh() {
        try {
            const res = await fetch('/api/countries/US/services');
            if (!res.ok) return;
            
            const data = await res.json();
            const services = data.services || [];
            
            if (services.length >= this.MIN_SERVICES) {
                this.services = services;
                this.lastFetch = Date.now();
                this.source = data.source || 'api';
                this._saveToCache(services, this.source);
                console.log(`✅ ServiceStore: Background refresh complete (${services.length} services)`);
                
                // Notify subscribers
                this._notifySubscribers();
            }
        } catch (e) {
            console.warn('⚠️ ServiceStore: Background refresh failed:', e);
        }
    },
    
    /**
     * Get service by ID
     */
    get(id) {
        return this.services.find(s => s.id === id);
    },
    
    /**
     * Search services by query
     */
    search(query) {
        if (!query) return this.services;
        
        const q = query.toLowerCase();
        return this.services.filter(s => 
            s.id.toLowerCase().includes(q) || 
            s.name.toLowerCase().includes(q)
        );
    },
    
    /**
     * Get all services
     */
    getAll() {
        return this.services;
    },
    
    /**
     * Subscribe to changes
     */
    subscribe(callback) {
        if (!this._subscribers) this._subscribers = [];
        this._subscribers.push(callback);
        
        // Return unsubscribe function
        return () => {
            const idx = this._subscribers.indexOf(callback);
            if (idx > -1) this._subscribers.splice(idx, 1);
        };
    },
    
    /**
     * Notify subscribers of changes
     */
    _notifySubscribers() {
        if (!this._subscribers) return;
        this._subscribers.forEach(cb => {
            try {
                cb(this.services);
            } catch (e) {
                console.error('ServiceStore: Subscriber error:', e);
            }
        });
    },
    
    /**
     * Load from cache
     */
    _loadFromCache() {
        try {
            const raw = localStorage.getItem(this.CACHE_KEY);
            if (!raw) return null;
            
            const cached = JSON.parse(raw);
            
            // Validate structure
            if (!cached.timestamp || !cached.services || !Array.isArray(cached.services)) {
                return null;
            }
            
            // Reject if zero services (corrupted cache)
            if (cached.services.length === 0) {
                console.warn(`⚠️ ServiceStore: Cache rejected (empty)`);
                return null;
            }
            
            return cached;
        } catch (e) {
            console.error('ServiceStore: Cache read error:', e);
            return null;
        }
    },
    
    /**
     * Save to cache
     */
    _saveToCache(services, source) {
        try {
            const cacheData = {
                version: 4,
                timestamp: Date.now(),
                services: services,
                source: source,
                count: services.length
            };
            localStorage.setItem(this.CACHE_KEY, JSON.stringify(cacheData));
            console.log(`✅ ServiceStore: Cached ${services.length} services (source: ${source})`);
        } catch (e) {
            console.error('ServiceStore: Cache write error:', e);
        }
    },
    
    /**
     * Check if cache is valid
     */
    _isCacheValid(cached) {
        const age = Date.now() - cached.timestamp;
        return age < this.CACHE_TTL && cached.services.length > 0;
    },
    
    /**
     * Check if cache is stale (needs background refresh)
     */
    _isStale(cached) {
        const age = Date.now() - cached.timestamp;
        return age > this.STALE_THRESHOLD;
    }
};

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.ServiceStore = ServiceStore;
}
