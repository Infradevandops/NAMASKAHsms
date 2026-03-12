# Service Modal Redesign — Implementation Tasks

**Date**: 2026-03-12  
**Status**: 🔄 Ready for Execution  
**Reference**: `.kiro/SERVICE_MODAL_REDESIGN.md`

---

## Task 1: Expand Backend Fallback to 50+ Services

**File**: `app/api/verification/services_endpoint.py`  
**Lines**: 18–31 (replace `FALLBACK_SERVICES`)

**Current**: 10 services  
**Target**: 50+ services with official names

**Code**:
```python
# Fallback services (always available) — 50+ common services
FALLBACK_SERVICES = [
    # Top messaging & social (10)
    {"id": "whatsapp", "name": "WhatsApp", "price": 2.50},
    {"id": "telegram", "name": "Telegram", "price": 2.00},
    {"id": "discord", "name": "Discord", "price": 2.25},
    {"id": "instagram", "name": "Instagram", "price": 2.75},
    {"id": "facebook", "name": "Facebook", "price": 2.50},
    {"id": "google", "name": "Google", "price": 2.00},
    {"id": "twitter", "name": "Twitter", "price": 2.50},
    {"id": "microsoft", "name": "Microsoft", "price": 2.25},
    {"id": "amazon", "name": "Amazon", "price": 2.50},
    {"id": "uber", "name": "Uber", "price": 2.75},
    
    # Tech & platforms (10)
    {"id": "apple", "name": "Apple", "price": 2.50},
    {"id": "tiktok", "name": "TikTok", "price": 2.75},
    {"id": "snapchat", "name": "Snapchat", "price": 2.50},
    {"id": "linkedin", "name": "LinkedIn", "price": 2.75},
    {"id": "netflix", "name": "Netflix", "price": 2.00},
    {"id": "spotify", "name": "Spotify", "price": 2.00},
    {"id": "reddit", "name": "Reddit", "price": 2.00},
    {"id": "pinterest", "name": "Pinterest", "price": 2.00},
    {"id": "tumblr", "name": "Tumblr", "price": 2.00},
    {"id": "twitch", "name": "Twitch", "price": 2.50},
    
    # Finance & payments (10)
    {"id": "paypal", "name": "PayPal", "price": 2.50},
    {"id": "venmo", "name": "Venmo", "price": 0.50},
    {"id": "cashapp", "name": "Cash App", "price": 2.50},
    {"id": "coinbase", "name": "Coinbase", "price": 2.75},
    {"id": "binance", "name": "Binance", "price": 2.75},
    {"id": "robinhood", "name": "Robinhood", "price": 2.50},
    {"id": "stripe", "name": "Stripe", "price": 2.50},
    {"id": "square", "name": "Square", "price": 2.50},
    {"id": "chime", "name": "Chime", "price": 2.50},
    {"id": "revolut", "name": "Revolut", "price": 2.50},
    
    # E-commerce & retail (10)
    {"id": "walmart", "name": "Walmart", "price": 0.50},
    {"id": "target", "name": "Target", "price": 0.50},
    {"id": "ebay", "name": "eBay", "price": 2.00},
    {"id": "etsy", "name": "Etsy", "price": 2.00},
    {"id": "shopify", "name": "Shopify", "price": 2.50},
    {"id": "alibaba", "name": "Alibaba", "price": 2.50},
    {"id": "aliexpress", "name": "AliExpress", "price": 2.50},
    {"id": "wish", "name": "Wish", "price": 2.00},
    {"id": "mercari", "name": "Mercari", "price": 2.00},
    {"id": "poshmark", "name": "Poshmark", "price": 2.00},
    
    # Food & delivery (10)
    {"id": "doordash", "name": "DoorDash", "price": 2.50},
    {"id": "ubereats", "name": "Uber Eats", "price": 2.75},
    {"id": "grubhub", "name": "Grubhub", "price": 2.50},
    {"id": "postmates", "name": "Postmates", "price": 2.50},
    {"id": "instacart", "name": "Instacart", "price": 2.50},
    {"id": "seamless", "name": "Seamless", "price": 2.50},
    {"id": "deliveroo", "name": "Deliveroo", "price": 2.50},
    {"id": "justeat", "name": "Just Eat", "price": 2.50},
    {"id": "zomato", "name": "Zomato", "price": 2.50},
    {"id": "swiggy", "name": "Swiggy", "price": 2.50},
    
    # Travel & transport (10)
    {"id": "airbnb", "name": "Airbnb", "price": 2.75},
    {"id": "booking", "name": "Booking.com", "price": 2.50},
    {"id": "expedia", "name": "Expedia", "price": 2.50},
    {"id": "lyft", "name": "Lyft", "price": 2.75},
    {"id": "vrbo", "name": "VRBO", "price": 2.50},
    {"id": "tripadvisor", "name": "TripAdvisor", "price": 2.50},
    {"id": "kayak", "name": "Kayak", "price": 2.50},
    {"id": "hopper", "name": "Hopper", "price": 2.50},
    {"id": "skyscanner", "name": "Skyscanner", "price": 2.50},
    {"id": "hotels", "name": "Hotels.com", "price": 2.50},
    
    # Dating & social (8)
    {"id": "tinder", "name": "Tinder", "price": 2.50},
    {"id": "bumble", "name": "Bumble", "price": 2.50},
    {"id": "hinge", "name": "Hinge", "price": 2.50},
    {"id": "match", "name": "Match.com", "price": 0.50},
    {"id": "pof", "name": "Plenty of Fish", "price": 2.00},
    {"id": "okcupid", "name": "OkCupid", "price": 2.00},
    {"id": "grindr", "name": "Grindr", "price": 2.50},
    {"id": "meetme", "name": "MeetMe", "price": 2.00},
    
    # Gaming (8)
    {"id": "steam", "name": "Steam", "price": 2.50},
    {"id": "epicgames", "name": "Epic Games", "price": 2.50},
    {"id": "playstation", "name": "PlayStation", "price": 2.50},
    {"id": "xbox", "name": "Xbox", "price": 2.50},
    {"id": "nintendo", "name": "Nintendo", "price": 2.50},
    {"id": "roblox", "name": "Roblox", "price": 2.50},
    {"id": "fortnite", "name": "Fortnite", "price": 2.50},
    {"id": "valorant", "name": "Valorant", "price": 2.50},
    
    # Communication (8)
    {"id": "zoom", "name": "Zoom", "price": 2.00},
    {"id": "slack", "name": "Slack", "price": 2.50},
    {"id": "teams", "name": "Microsoft Teams", "price": 2.25},
    {"id": "skype", "name": "Skype", "price": 2.00},
    {"id": "viber", "name": "Viber", "price": 2.00},
    {"id": "wechat", "name": "WeChat", "price": 2.50},
    {"id": "line", "name": "LINE", "price": 2.50},
    {"id": "kakao", "name": "KakaoTalk", "price": 2.50},
]
```

**Verification**:
```bash
# Count services
grep -c '{"id":' app/api/verification/services_endpoint.py
# Should return: 84
```

---

## Task 2: Update TextVerified Service Mock

**File**: `app/services/textverified_service.py`  
**Lines**: 289–300 (replace `_mock_services()`)

**Code**:
```python
def _mock_services(self) -> List[Dict[str, Any]]:
    """Return comprehensive fallback services (84 services)."""
    # Import from services_endpoint to maintain single source of truth
    from app.api.verification.services_endpoint import FALLBACK_SERVICES
    return FALLBACK_SERVICES
```

**Why**: Single source of truth — backend and service layer use same fallback list.

---

## Task 3: Implement Stale-While-Revalidate Cache

**File**: `templates/verify_modern.html`  
**Location**: After line 380 (before existing `loadServices()`)

**Add new cache config and helper functions**:
```js
// ============================================================================
// CACHE CONFIGURATION — Stale-While-Revalidate Strategy
// ============================================================================

const _CACHE_CONFIG = {
    KEY: 'nsk_services_v3',              // Version bump to invalidate old cache
    TTL: 6 * 60 * 60 * 1000,             // 6 hours (cache lifetime)
    MIN_SERVICES: 20,                     // Reject cache if < 20 services
    STALE_THRESHOLD: 3 * 60 * 60 * 1000  // Refresh in background if > 3h old
};

// Get cached services with validation
function _getCachedServices() {
    try {
        const raw = localStorage.getItem(_CACHE_CONFIG.KEY);
        if (!raw) return null;
        
        const cached = JSON.parse(raw);
        
        // Validate structure
        if (!cached.timestamp || !cached.services || !Array.isArray(cached.services)) {
            return null;
        }
        
        // Reject if too few services (corrupted cache)
        if (cached.services.length < _CACHE_CONFIG.MIN_SERVICES) {
            console.warn(`⚠️ Cache rejected: only ${cached.services.length} services`);
            return null;
        }
        
        return cached;
    } catch (e) {
        console.error('Cache read error:', e);
        return null;
    }
}

// Save services to cache
function _setCachedServices(services, source) {
    try {
        const cacheData = {
            timestamp: Date.now(),
            services: services,
            source: source,
            count: services.length
        };
        localStorage.setItem(_CACHE_CONFIG.KEY, JSON.stringify(cacheData));
        console.log(`✅ Cached ${services.length} services (source: ${source})`);
    } catch (e) {
        console.error('Cache write error:', e);
    }
}

// Check if cache should be refreshed in background
function _shouldRefreshCache(cached) {
    if (!cached) return true;
    const age = Date.now() - cached.timestamp;
    return age > _CACHE_CONFIG.STALE_THRESHOLD;
}

// Check if cache is completely expired
function _isCacheExpired(cached) {
    if (!cached) return true;
    const age = Date.now() - cached.timestamp;
    return age > _CACHE_CONFIG.TTL;
}
```

---

## Task 4: Replace loadServices() with Preload Strategy

**File**: `templates/verify_modern.html`  
**Lines**: 401–467 (replace entire `loadServices()` function)

**Code**:
```js
// ============================================================================
// SERVICE LOADING — Preload on Page Load (Always Ready)
// ============================================================================

async function loadServices() {
    console.log('🔄 Loading services...');
    
    // Step 1: Check cache first
    const cached = _getCachedServices();
    
    if (cached && !_isCacheExpired(cached)) {
        // Cache valid — use immediately
        _modalItems['service'] = _buildServiceItems(cached.services);
        console.log(`✅ Loaded ${cached.count} services from cache (age: ${Math.round((Date.now() - cached.timestamp) / 60000)}m)`);
        
        // Background refresh if stale
        if (_shouldRefreshCache(cached)) {
            console.log('🔄 Cache stale, refreshing in background...');
            _refreshServicesInBackground();
        }
        
        return; // Services ready
    }
    
    // Step 2: Cache expired or missing — fetch from API
    console.log('🌐 Cache expired/missing, fetching from API...');
    await _fetchServicesFromAPI();
}

// Fetch services from API (with fallback)
async function _fetchServicesFromAPI() {
    try {
        const token = localStorage.getItem('access_token');
        const ctrl = new AbortController();
        const tid = setTimeout(() => ctrl.abort(), 15000);
        
        const res = await fetch('/api/countries/US/services', {
            headers: token ? { 'Authorization': `Bearer ${token}` } : {},
            signal: ctrl.signal
        });
        clearTimeout(tid);
        
        // Handle 401 — retry without auth (endpoint is public)
        let finalRes = res;
        if (res.status === 401) {
            const retryRes = await fetch('/api/countries/US/services');
            if (!retryRes.ok) throw new Error('fetch failed after 401 retry');
            finalRes = retryRes;
        } else if (!res.ok) {
            throw new Error(`fetch failed: ${res.status}`);
        }
        
        const data = await finalRes.json();
        const services = data.services || [];
        
        if (services.length < _CACHE_CONFIG.MIN_SERVICES) {
            throw new Error(`API returned only ${services.length} services`);
        }
        
        // Success — cache and populate
        _modalItems['service'] = _buildServiceItems(services);
        _setCachedServices(services, data.source || 'api');
        console.log(`✅ Loaded ${services.length} services from API`);
        
    } catch (e) {
        console.error('❌ API fetch failed:', e);
        
        // Try stale cache as last resort
        const staleCache = _getCachedServices();
        if (staleCache) {
            _modalItems['service'] = _buildServiceItems(staleCache.services);
            console.warn(`⚠️ Using stale cache (${staleCache.count} services, age: ${Math.round((Date.now() - staleCache.timestamp) / 60000)}m)`);
        } else {
            // Ultimate fallback — should never happen (backend has 84-service fallback)
            console.error('💥 No cache available, services unavailable');
            _modalItems['service'] = [];
        }
    }
}

// Background refresh (non-blocking)
async function _refreshServicesInBackground() {
    try {
        const res = await fetch('/api/countries/US/services');
        if (!res.ok) return;
        
        const data = await res.json();
        const services = data.services || [];
        
        if (services.length >= _CACHE_CONFIG.MIN_SERVICES) {
            _modalItems['service'] = _buildServiceItems(services);
            _setCachedServices(services, data.source || 'api');
            console.log(`✅ Background refresh complete (${services.length} services)`);
        }
    } catch (e) {
        console.warn('Background refresh failed:', e);
    }
}
```

---

## Task 5: Add Official Logo Rendering

**File**: `templates/verify_modern.html`  
**Location**: After `_buildServiceItems()` function (around line 398)

**Add new icon functions**:
```js
// ============================================================================
// SERVICE ICONS — Official Logos via SimpleIcons CDN
// ============================================================================

// Service logo mapping (simpleicons.org CDN)
const _SERVICE_LOGOS = {
    'whatsapp': 'https://cdn.simpleicons.org/whatsapp/25D366',
    'telegram': 'https://cdn.simpleicons.org/telegram/26A5E4',
    'google': 'https://cdn.simpleicons.org/google/4285F4',
    'facebook': 'https://cdn.simpleicons.org/facebook/1877F2',
    'instagram': 'https://cdn.simpleicons.org/instagram/E4405F',
    'discord': 'https://cdn.simpleicons.org/discord/5865F2',
    'twitter': 'https://cdn.simpleicons.org/twitter/1DA1F2',
    'microsoft': 'https://cdn.simpleicons.org/microsoft/5E5E5E',
    'amazon': 'https://cdn.simpleicons.org/amazon/FF9900',
    'uber': 'https://cdn.simpleicons.org/uber/000000',
    'apple': 'https://cdn.simpleicons.org/apple/000000',
    'tiktok': 'https://cdn.simpleicons.org/tiktok/000000',
    'snapchat': 'https://cdn.simpleicons.org/snapchat/FFFC00',
    'linkedin': 'https://cdn.simpleicons.org/linkedin/0A66C2',
    'netflix': 'https://cdn.simpleicons.org/netflix/E50914',
    'spotify': 'https://cdn.simpleicons.org/spotify/1DB954',
    'paypal': 'https://cdn.simpleicons.org/paypal/00457C',
    'venmo': 'https://cdn.simpleicons.org/venmo/3D95CE',
    'cashapp': 'https://cdn.simpleicons.org/cashapp/00D632',
    'coinbase': 'https://cdn.simpleicons.org/coinbase/0052FF',
    'binance': 'https://cdn.simpleicons.org/binance/F3BA2F',
    'robinhood': 'https://cdn.simpleicons.org/robinhood/00C805',
    'walmart': 'https://cdn.simpleicons.org/walmart/0071CE',
    'target': 'https://cdn.simpleicons.org/target/CC0000',
    'ebay': 'https://cdn.simpleicons.org/ebay/E53238',
    'etsy': 'https://cdn.simpleicons.org/etsy/F16521',
    'shopify': 'https://cdn.simpleicons.org/shopify/7AB55C',
    'doordash': 'https://cdn.simpleicons.org/doordash/FF3008',
    'ubereats': 'https://cdn.simpleicons.org/ubereats/5FB709',
    'grubhub': 'https://cdn.simpleicons.org/grubhub/F63440',
    'airbnb': 'https://cdn.simpleicons.org/airbnb/FF5A5F',
    'booking': 'https://cdn.simpleicons.org/bookingdotcom/003580',
    'lyft': 'https://cdn.simpleicons.org/lyft/FF00BF',
    'tinder': 'https://cdn.simpleicons.org/tinder/FF6B6B',
    'bumble': 'https://cdn.simpleicons.org/bumble/FFD700',
    'reddit': 'https://cdn.simpleicons.org/reddit/FF4500',
    'pinterest': 'https://cdn.simpleicons.org/pinterest/E60023',
    'tumblr': 'https://cdn.simpleicons.org/tumblr/35465C',
    'twitch': 'https://cdn.simpleicons.org/twitch/9146FF',
    'steam': 'https://cdn.simpleicons.org/steam/000000',
    'epicgames': 'https://cdn.simpleicons.org/epicgames/313131',
    'playstation': 'https://cdn.simpleicons.org/playstation/003791',
    'xbox': 'https://cdn.simpleicons.org/xbox/107C10',
    'nintendo': 'https://cdn.simpleicons.org/nintendo/E60012',
    'zoom': 'https://cdn.simpleicons.org/zoom/2D8CFF',
    'slack': 'https://cdn.simpleicons.org/slack/4A154B',
    'teams': 'https://cdn.simpleicons.org/microsoftteams/6264A7',
    'skype': 'https://cdn.simpleicons.org/skype/00AFF0',
    'viber': 'https://cdn.simpleicons.org/viber/665CAC',
    'wechat': 'https://cdn.simpleicons.org/wechat/07C160',
    'line': 'https://cdn.simpleicons.org/line/00B900',
    'kakao': 'https://cdn.simpleicons.org/kakaotalk/FFCD00',
    'stripe': 'https://cdn.simpleicons.org/stripe/008CDD',
    'square': 'https://cdn.simpleicons.org/square/3E4348',
    'chime': 'https://cdn.simpleicons.org/chime/00C389',
    'alibaba': 'https://cdn.simpleicons.org/alibabadotcom/FF6A00',
    'aliexpress': 'https://cdn.simpleicons.org/aliexpress/FF4747',
    'wish': 'https://cdn.simpleicons.org/wish/2FB7EC',
    'instacart': 'https://cdn.simpleicons.org/instacart/43B02A',
    'expedia': 'https://cdn.simpleicons.org/expedia/FFCB00',
    'tripadvisor': 'https://cdn.simpleicons.org/tripadvisor/34E0A1',
    'match': 'https://cdn.simpleicons.org/match/EA4C89',
    'pof': 'https://cdn.simpleicons.org/plentyoffish/FF6B6B',
    'okcupid': 'https://cdn.simpleicons.org/okcupid/0500BE',
    'grindr': 'https://cdn.simpleicons.org/grindr/FFCE00',
    'roblox': 'https://cdn.simpleicons.org/roblox/000000',
    'fortnite': 'https://cdn.simpleicons.org/epicgames/313131',
    'valorant': 'https://cdn.simpleicons.org/valorant/FF4655',
};

// Get service logo HTML
function getServiceLogoHTML(serviceId) {
    const id = serviceId.toLowerCase();
    const logoUrl = _SERVICE_LOGOS[id];
    
    if (logoUrl) {
        return `<img src="${logoUrl}" alt="${serviceId}" class="service-logo" />`;
    }
    
    // Fallback to generic icon (Phosphor icon placeholder)
    return `<div class="service-logo-fallback">📱</div>`;
}
```

---

## Task 6: Update Service Display to Show Logos

**File**: `templates/verify_modern.html`  
**Location**: Find `selectServiceInline()` function (around line 901)

**Replace line 907** (the one that sets `service-display` textContent):
```js
// OLD:
document.getElementById('service-display').textContent = item.label + (item.sub ? '  ' + item.sub : '');

// NEW:
document.getElementById('service-display').innerHTML = 
    `${getServiceLogoHTML(value)} <span style="margin-left:8px;">${item.label}</span> <span style="color:#6b7280;font-size:13px;margin-left:4px;">${item.sub || ''}</span>`;
```

---

## Task 7: Add CSS for Service Logos

**File**: `templates/verify_modern.html`  
**Location**: Inside `<style>` block (around line 230)

**Add**:
```css
/* Service logo styling */
.service-logo {
    width: 20px;
    height: 20px;
    object-fit: contain;
    display: inline-block;
    vertical-align: middle;
}

.service-logo-fallback {
    width: 20px;
    height: 20px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    vertical-align: middle;
}

#service-display {
    display: flex;
    align-items: center;
}
```

---

## Task 8: Ensure Services Load on DOMContentLoaded

**File**: `templates/verify_modern.html`  
**Location**: Find `document.addEventListener('DOMContentLoaded'` (around line 1016)

**Verify this line exists** (should already be there):
```js
document.addEventListener('DOMContentLoaded', () => {
    loadServices();   // ← This must be first — services preload immediately
    loadTier();
    loadBalance();
    updateProgress(1);
    // ... rest
});
```

---

## Verification Checklist

After implementing all tasks:

### Backend Verification
```bash
# 1. Count fallback services
grep -c '{"id":' app/api/verification/services_endpoint.py
# Expected: 84

# 2. Verify _mock_services imports from services_endpoint
grep -A 3 "def _mock_services" app/services/textverified_service.py
# Expected: imports FALLBACK_SERVICES

# 3. Start app and test endpoint
curl http://localhost:8000/api/countries/US/services | jq '.count'
# Expected: 84 (or more if TextVerified API is working)
```

### Frontend Verification
```bash
# 1. Check cache config exists
grep "_CACHE_CONFIG" templates/verify_modern.html
# Expected: 1 match

# 2. Check logo mapping exists
grep "_SERVICE_LOGOS" templates/verify_modern.html
# Expected: 1 match

# 3. Check loadServices uses new strategy
grep "stale-while-revalidate\|_getCachedServices\|_fetchServicesFromAPI" templates/verify_modern.html
# Expected: multiple matches
```

### Browser Verification
1. Open DevTools → Console
2. Navigate to `/verify`
3. Check console logs:
   - `✅ Loaded N services from cache` (on repeat visits)
   - `🌐 Cache expired/missing, fetching from API...` (on first visit)
4. Check localStorage:
   - Key `nsk_services_v3` should exist
   - Value should have `timestamp`, `services`, `count` fields
5. Click service input → services should be already populated (no loading spinner)
6. Search "apple" → Apple should appear with official logo
7. Select a service → logo should display in step 1 card

---

## Rollback Plan

If issues occur:

```bash
# Restore previous version
git checkout HEAD~1 -- templates/verify_modern.html
git checkout HEAD~1 -- app/api/verification/services_endpoint.py
git checkout HEAD~1 -- app/services/textverified_service.py

# Clear user caches (add to app)
localStorage.removeItem('nsk_services_v3');
localStorage.removeItem('nsk_services_cache');
localStorage.removeItem('nsk_services_priced_cache');
```

---

## Success Criteria

- [ ] Backend returns 84+ services (never empty)
- [ ] Services load instantly on page load (< 100ms from cache)
- [ ] Modal opens instantly with full list already rendered
- [ ] Search "apple" shows Apple with official logo
- [ ] All major services display official brand logos (not emojis)
- [ ] Cache persists across page reloads
- [ ] Background refresh works when cache > 3h old
- [ ] No "Failed to load" or "No services found" errors

---

**Ready to implement?** All code is provided above. Execute tasks 1–8 in order.
