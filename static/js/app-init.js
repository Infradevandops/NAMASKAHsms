/**
 * Blocking app initialization
 * 
 * This ensures tier is loaded before any UI rendering, preventing the
 * "freemium flash" issue. The flow is:
 * 1. Show skeleton immediately
 * 2. Block on tier load (wait for tier)
 * 3. Initialize global state
 * 4. Hide skeleton
 * 5. Render dashboard
 * 6. Start tier sync
 */

async function initializeApp() {
    console.log('[AppInit] Starting...');
    
    try {
        // 1. Show skeleton immediately
        if (typeof SkeletonLoader !== 'undefined') {
            SkeletonLoader.show();
            console.log('[AppInit] Skeleton shown');
        }
        
        // 2. Block on tier load
        if (typeof TierLoader === 'undefined') {
            throw new Error('TierLoader not loaded');
        }
        
        const tier = await TierLoader.loadTierBlocking();
        console.log(`[AppInit] Tier loaded: ${tier}`);
        
        // 3. Initialize global state
        window.APP_STATE = {
            tier,
            tierRank: { freemium: 0, payg: 1, pro: 2, custom: 3 },
            tierRankValue: { freemium: 0, payg: 1, pro: 2, custom: 3 }[tier],
            initialized: true,
            loadTime: performance.now()
        };
        
        console.log(`[AppInit] Global state initialized: tier=${tier}, rank=${window.APP_STATE.tierRankValue}`);
        
        // 4. Hide skeleton
        if (typeof SkeletonLoader !== 'undefined') {
            SkeletonLoader.hide();
            console.log('[AppInit] Skeleton hidden');
        }
        
        // 5. Render dashboard (this is handled by existing dashboard.js)
        // The dashboard.js file will render the actual UI
        console.log('[AppInit] Dashboard ready to render');
        
        // 6. Start tier sync (if available)
        if (typeof TierSync !== 'undefined') {
            TierSync.startSync();
            console.log('[AppInit] Tier sync started');
        }
        
        console.log('[AppInit] Complete');
        
    } catch (error) {
        console.error('[AppInit] Initialization failed:', error);
        
        // Fallback: hide skeleton and show error
        if (typeof SkeletonLoader !== 'undefined') {
            SkeletonLoader.hide();
        }
        
        // Initialize with default state
        window.APP_STATE = {
            tier: 'freemium',
            tierRank: { freemium: 0, payg: 1, pro: 2, custom: 3 },
            tierRankValue: 0,
            initialized: false,
            error: error.message
        };
        
        // Show error message
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #fee2e2;
            border: 1px solid #fecaca;
            color: #991b1b;
            padding: 16px;
            border-radius: 8px;
            z-index: 10000;
            max-width: 400px;
        `;
        errorDiv.innerHTML = `
            <strong>Initialization Error</strong><br>
            ${error.message}<br>
            <small>Please refresh the page</small>
        `;
        document.body.appendChild(errorDiv);
    }
}

/**
 * Initialize on DOM ready
 * 
 * This blocks the entire app initialization until the DOM is ready,
 * ensuring all required libraries are loaded.
 */
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
} else {
    // DOM is already ready
    initializeApp();
}

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { initializeApp };
}
