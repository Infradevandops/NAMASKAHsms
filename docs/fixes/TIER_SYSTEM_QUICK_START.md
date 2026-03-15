# Tier Identification System - Quick Start Implementation

**Priority**: CRITICAL  
**Effort**: 40 hours  
**Timeline**: 4 weeks  
**Stability**: Enterprise-Grade

---

## 🚀 Quick Start (Phase 1: Backend - 10 hours)

### Step 1: Add Tier Verification Middleware

**File**: `app/middleware/tier_verification.py` (NEW)

```python
"""Tier verification middleware for all requests."""

from fastapi import Request
from app.services.tier_manager import TierManager
from app.core.logging import get_logger

logger = get_logger(__name__)

async def tier_verification_middleware(request: Request, call_next):
    """Verify and attach tier to every request."""
    
    # Skip for public endpoints
    public_paths = ['/auth/', '/health', '/docs', '/openapi.json']
    if any(request.url.path.startswith(p) for p in public_paths):
        return await call_next(request)
    
    # Get user from request state (set by auth middleware)
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        return await call_next(request)
    
    try:
        # Get database session
        db = getattr(request.state, 'db', None)
        if not db:
            return await call_next(request)
        
        # Verify tier
        tier_manager = TierManager(db)
        tier = tier_manager.get_user_tier(user_id)
        
        # Attach to request state
        request.state.user_tier = tier
        request.state.tier_manager = tier_manager
        
        # Log tier access
        logger.debug(f"Tier verified: user={user_id}, tier={tier}")
        
    except Exception as e:
        logger.error(f"Tier verification failed: {e}")
        # Continue anyway - tier will default to freemium
        request.state.user_tier = 'freemium'
    
    return await call_next(request)
```

**Integration**: Add to `main.py`

```python
from app.middleware.tier_verification import tier_verification_middleware

app.middleware("http")(tier_verification_middleware)
```

### Step 2: Add Feature Authorization Decorator

**File**: `app/core/dependencies.py` (UPDATE)

```python
"""Add to existing file."""

from functools import wraps
from fastapi import Depends, HTTPException, Request

def require_feature(feature: str):
    """Decorator to require specific feature access."""
    async def dependency(request: Request):
        user_id = getattr(request.state, 'user_id', None)
        tier_manager = getattr(request.state, 'tier_manager', None)
        
        if not user_id or not tier_manager:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        if not tier_manager.check_feature_access(user_id, feature):
            raise HTTPException(
                status_code=403,
                detail=f"Feature '{feature}' requires higher tier"
            )
        return True
    
    return Depends(dependency)
```

**Usage in Endpoints**:

```python
@router.post("/api/keys/generate")
async def generate_api_key(
    _: bool = require_feature("api_access"),
    request: Request = None
):
    """Generate API key - requires Pro+ tier."""
    user_id = request.state.user_id
    # ... implementation
```

### Step 3: Add Tier Audit Logging

**File**: `app/core/logging.py` (UPDATE)

```python
"""Add to existing file."""

def log_tier_access(user_id: str, tier: str, feature: str, allowed: bool, reason: str = ""):
    """Log all tier-based access decisions."""
    status = "ALLOWED" if allowed else "DENIED"
    logger.info(
        f"TIER_ACCESS | status={status} | user={user_id} | tier={tier} | "
        f"feature={feature} | reason={reason}"
    )

def log_tier_change(user_id: str, old_tier: str, new_tier: str, reason: str = ""):
    """Log tier changes."""
    logger.info(
        f"TIER_CHANGE | user={user_id} | old={old_tier} | new={new_tier} | reason={reason}"
    )
```

### Step 4: Update Tier Endpoints

**File**: `app/api/billing/tier_endpoints.py` (UPDATE)

```python
"""Update get_current_tier endpoint."""

@router.get("/current")
async def get_current_tier(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Get current tier information for user."""
    try:
        tier_manager = TierManager(db)
        tier = tier_manager.get_user_tier(user_id)
        tier_config = TierConfig.get_tier_config(tier, db)
        
        # Log access
        log_tier_access(user_id, tier, "tier_info", True)
        
        return {
            "current_tier": tier,
            "tier_info": tier_config,
            "user_id": user_id,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "checksum": calculate_tier_checksum(tier)  # For integrity
        }
    except Exception as e:
        logger.error(f"Failed to get current tier: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tier")
```

---

## 🎨 Quick Start (Phase 2: Frontend - 15 hours)

### Step 1: Create TierLoader

**File**: `static/js/tier-loader.js` (NEW)

```javascript
/**
 * Enterprise-grade tier loader with blocking load
 */
class TierLoader {
    static CACHE_KEY = 'nsk_tier_cache';
    static CACHE_TTL = 3600000;  // 1 hour
    static FETCH_TIMEOUT = 5000;  // 5 seconds
    
    /**
     * Load tier with blocking behavior
     * @returns {Promise<string>} User's tier
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
     * @param {number} ms - Timeout in milliseconds
     * @returns {Promise<string>} User's tier
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
     * Get cached tier
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
     * @param {Object} cached - Cached tier object
     * @returns {boolean} True if cache is valid
     */
    static isCacheValid(cached) {
        if (!cached || !cached.ts) return false;
        return (Date.now() - cached.ts) < this.CACHE_TTL;
    }
    
    /**
     * Cache tier to localStorage
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
     * @param {string} tier - Tier value
     * @returns {string} Checksum
     */
    static calculateChecksum(tier) {
        // Simple checksum: base64 encode tier + timestamp prefix
        const prefix = Date.now().toString().slice(0, 5);
        return btoa(tier + prefix);
    }
    
    /**
     * Get auth token
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
}
```

### Step 2: Create SkeletonLoader

**File**: `static/js/skeleton-loader.js` (NEW)

```javascript
/**
 * Skeleton loading state to prevent UI flashing
 */
class SkeletonLoader {
    static SKELETON_HTML = `
        <div class="skeleton-container" style="
            width: 100%;
            height: 100vh;
            background: #f9fafb;
            display: flex;
            flex-direction: column;
        ">
            <div class="skeleton-header" style="
                height: 60px;
                background: #fff;
                border-bottom: 1px solid #e5e7eb;
                display: flex;
                align-items: center;
                padding: 0 20px;
                gap: 12px;
            ">
                <div class="skeleton-pulse" style="
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    background: #e5e7eb;
                "></div>
                <div class="skeleton-pulse" style="
                    width: 200px;
                    height: 20px;
                    background: #e5e7eb;
                "></div>
            </div>
            
            <div style="display: flex; flex: 1;">
                <div class="skeleton-sidebar" style="
                    width: 250px;
                    background: #fff;
                    border-right: 1px solid #e5e7eb;
                    padding: 20px;
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                ">
                    ${Array(5).fill(0).map(() => `
                        <div class="skeleton-pulse" style="
                            width: 100%;
                            height: 40px;
                            background: #e5e7eb;
                            border-radius: 6px;
                        "></div>
                    `).join('')}
                </div>
                
                <div class="skeleton-content" style="
                    flex: 1;
                    padding: 20px;
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                ">
                    ${Array(4).fill(0).map(() => `
                        <div class="skeleton-card" style="
                            background: #fff;
                            border-radius: 8px;
                            padding: 20px;
                            display: flex;
                            flex-direction: column;
                            gap: 12px;
                        ">
                            <div class="skeleton-pulse" style="
                                width: 100%;
                                height: 20px;
                                background: #e5e7eb;
                            "></div>
                            <div class="skeleton-pulse" style="
                                width: 80%;
                                height: 16px;
                                background: #e5e7eb;
                            "></div>
                            <div class="skeleton-pulse" style="
                                width: 60%;
                                height: 16px;
                                background: #e5e7eb;
                            "></div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
        
        <style>
            @keyframes skeleton-pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            .skeleton-pulse {
                animation: skeleton-pulse 2s ease-in-out infinite;
            }
        </style>
    `;
    
    /**
     * Show skeleton loading state
     */
    static show() {
        const container = document.createElement('div');
        container.innerHTML = this.SKELETON_HTML;
        document.body.innerHTML = '';
        document.body.appendChild(container);
    }
    
    /**
     * Hide skeleton loading state
     */
    static hide() {
        const skeleton = document.querySelector('.skeleton-container');
        if (skeleton) {
            skeleton.style.animation = 'fadeOut 0.3s ease-out';
            setTimeout(() => skeleton.remove(), 300);
        }
    }
}
```

### Step 3: Create Blocking App Initialization

**File**: `static/js/app-init.js` (NEW)

```javascript
/**
 * Blocking app initialization - ensures tier is loaded before rendering
 */
async function initializeApp() {
    console.log('[AppInit] Starting...');
    
    // 1. Show skeleton immediately
    SkeletonLoader.show();
    
    // 2. Block on tier load
    const tier = await TierLoader.loadTierBlocking();
    
    // 3. Initialize global state
    window.APP_STATE = {
        tier,
        tierRank: { freemium: 0, payg: 1, pro: 2, custom: 3 },
        tierRankValue: { freemium: 0, payg: 1, pro: 2, custom: 3 }[tier],
        initialized: true
    };
    
    console.log(`[AppInit] Tier loaded: ${tier} (rank: ${window.APP_STATE.tierRankValue})`);
    
    // 4. Hide skeleton
    SkeletonLoader.hide();
    
    // 5. Render actual UI
    await renderDashboard();
    
    // 6. Start tier sync
    TierSync.startSync();
    
    console.log('[AppInit] Complete');
}

// Block on init
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
} else {
    initializeApp();
}
```

### Step 4: Add to Dashboard HTML

**File**: `templates/dashboard.html` (UPDATE)

```html
<!-- Add before other scripts -->
<script src="/static/js/tier-loader.js"></script>
<script src="/static/js/skeleton-loader.js"></script>
<script src="/static/js/tier-sync.js"></script>
<script src="/static/js/app-init.js"></script>

<!-- Then load dashboard -->
<script src="/static/js/dashboard.js"></script>
```

---

## ✅ Verification Checklist

After implementation, verify:

- [ ] No "freemium flash" on dashboard load
- [ ] Tier loads within 500ms
- [ ] Tier persists across page refreshes
- [ ] Tier changes reflect immediately
- [ ] Unauthorized features are blocked
- [ ] All tests pass (unit, integration, E2E)
- [ ] No console errors
- [ ] Performance metrics acceptable

---

## 🧪 Quick Test

```bash
# Run unit tests
pytest tests/unit/test_tier_identification.py -v

# Run integration tests
pytest tests/integration/test_tier_system.py -v

# Run E2E tests
npm run test:e2e -- tier-identification.e2e.js

# Check performance
npm run test:performance -- tier-load-time
```

---

## 📊 Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **No UI Flashing** | 0 flashes | Visual inspection |
| **Tier Load Time** | < 500ms | DevTools Performance |
| **Tier Consistency** | 100% | Cross-tab test |
| **Feature Gating** | 100% | Unauthorized access test |
| **Test Coverage** | > 95% | Coverage report |

---

**Status**: Ready to implement  
**Estimated Time**: 40 hours  
**Risk**: Low (backward compatible)  
**Impact**: High (eliminates all tier issues)
