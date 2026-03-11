# Service Loading Errors - Root Cause & Fix

## The Problem (Why "Failed to load" Appears)

### **Root Cause: NO ERROR HANDLING in Services Endpoint**

**File:** `app/api/verification/services_endpoint.py`

```python
@router.get("/{country}/services")
async def get_services(country: str):
    """Get services — returns immediately from cache or service names, prices filled async."""
    settings = get_settings()
    raw = await _tv.get_services_list()  # ❌ NO TRY/EXCEPT - CRASHES IF API FAILS
    return {
        "services": [
            {
                "id": s["id"],
                "name": s["name"],
                "price": round(s["price"] * settings.price_markup, 2),
                "cost": round(s["price"] * settings.price_markup, 2),
            }
            for s in raw
        ],
        "total": len(raw),
    }
```

### **What Happens When API Fails:**

1. TextVerified API is unreachable
2. `get_services_list()` throws exception
3. **NO CATCH** → Exception propagates
4. FastAPI returns 500 error
5. Frontend shows "Failed to load"
6. User can't select service

### **Why This Happens:**

| Scenario | Current Behavior | Expected Behavior |
|----------|------------------|-------------------|
| TextVerified API down | 500 error, crash | Return fallback services |
| Network timeout | 500 error, crash | Return cached or fallback |
| Cache miss + API slow | 500 error, crash | Return fallback immediately |
| Invalid response | 500 error, crash | Return fallback |

---

## The Fix

### **Fix 1: Add Error Handling to Services Endpoint**

**File:** `app/api/verification/services_endpoint.py`

```python
from fastapi import APIRouter, HTTPException
from app.core.config import get_settings
from app.core.unified_cache import cache
from app.services.textverified_service import TextVerifiedService
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/countries", tags=["Services"])
_tv = TextVerifiedService()

# Fallback services (always available)
FALLBACK_SERVICES = [
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
]

@router.get("/{country}/services")
async def get_services(country: str):
    """Get services with fallback on error."""
    settings = get_settings()
    
    try:
        # Try to get from API
        raw = await _tv.get_services_list()
        
        if not raw:
            logger.warning(f"Empty services list for {country}, using fallback")
            raw = FALLBACK_SERVICES
        
        return {
            "services": [
                {
                    "id": s["id"],
                    "name": s["name"],
                    "price": round(s["price"] * settings.price_markup, 2),
                    "cost": round(s["price"] * settings.price_markup, 2),
                }
                for s in raw
            ],
            "total": len(raw),
            "source": "api"
        }
    
    except Exception as e:
        logger.error(f"Failed to get services for {country}: {str(e)}", exc_info=True)
        
        # Return fallback services
        return {
            "services": [
                {
                    "id": s["id"],
                    "name": s["name"],
                    "price": round(s["price"] * settings.price_markup, 2),
                    "cost": round(s["price"] * settings.price_markup, 2),
                }
                for s in FALLBACK_SERVICES
            ],
            "total": len(FALLBACK_SERVICES),
            "source": "fallback",
            "error": "API unavailable, using cached services"
        }


@router.get("/{country}/services/batch-pricing")
async def get_services_batch_pricing(country: str):
    """Return services with accurate pricing from 24h cache. Warms cache if cold."""
    settings = get_settings()
    
    try:
        # Try cache first
        cached = await cache.get("tv:services_list")
        if cached:
            return {
                "services": [
                    {
                        "id": s["id"],
                        "name": s["name"],
                        "price": round(s["price"] * settings.price_markup, 2),
                        "cost": round(s["price"] * settings.price_markup, 2),
                    }
                    for s in cached
                ],
                "total": len(cached),
                "source": "cache"
            }
        
        # Cache cold — try API
        raw = await _tv.get_services_list()
        
        if not raw:
            logger.warning(f"Empty services list for {country}, using fallback")
            raw = FALLBACK_SERVICES
        
        return {
            "services": [
                {
                    "id": s["id"],
                    "name": s["name"],
                    "price": round(s["price"] * settings.price_markup, 2),
                    "cost": round(s["price"] * settings.price_markup, 2),
                }
                for s in raw
            ],
            "total": len(raw),
            "source": "warming"
        }
    
    except Exception as e:
        logger.error(f"Failed to get batch pricing for {country}: {str(e)}", exc_info=True)
        
        # Return fallback
        return {
            "services": [
                {
                    "id": s["id"],
                    "name": s["name"],
                    "price": round(s["price"] * settings.price_markup, 2),
                    "cost": round(s["price"] * settings.price_markup, 2),
                }
                for s in FALLBACK_SERVICES
            ],
            "total": len(FALLBACK_SERVICES),
            "source": "fallback",
            "error": "API unavailable, using cached services"
        }
```

### **Fix 2: Improve Frontend Error Handling**

**File:** `static/js/verification.js` (UPDATE loadServices function)

```javascript
async function loadServices() {
    console.log('Loading services for US...');
    const select = document.getElementById('service-select');
    
    try {
        // Show loading state
        select.innerHTML = '<option value="">Loading services...</option>';
        select.disabled = true;
        
        const token = localStorage.getItem('access_token');
        const res = await axios.get(`/api/countries/US/services`, {
            headers: { 'Authorization': `Bearer ${token}` },
            timeout: 5000  // 5 second timeout
        });

        if (res.data && res.data.services && res.data.services.length > 0) {
            allServices = res.data.services;
            servicesLoaded = true;
            
            // Populate select
            select.innerHTML = '<option value="">Select a service...</option>';
            allServices.forEach(service => {
                const option = document.createElement('option');
                option.value = service.id;
                option.textContent = `${service.name} - $${service.cost.toFixed(2)}`;
                select.appendChild(option);
            });
            
            select.disabled = false;
            
            // Show source indicator
            const source = res.data.source || 'unknown';
            console.log(`✅ Loaded ${allServices.length} services from ${source}`);
            
            // If using fallback, show warning
            if (source === 'fallback') {
                console.warn('⚠️ Using fallback services - API unavailable');
                showNotification('Using cached services', 'warning');
            }
        } else {
            throw new Error('No services returned from API');
        }
    } catch (error) {
        console.error(`❌ Failed to load services:`, error);
        
        // Use hardcoded fallback
        allServices = [
            { id: 'telegram', name: 'Telegram', cost: 2.00 },
            { id: 'whatsapp', name: 'WhatsApp', cost: 2.50 },
            { id: 'google', name: 'Google', cost: 2.00 },
            { id: 'facebook', name: 'Facebook', cost: 2.50 },
            { id: 'instagram', name: 'Instagram', cost: 2.75 },
            { id: 'twitter', name: 'Twitter', cost: 2.50 },
            { id: 'discord', name: 'Discord', cost: 2.25 },
            { id: 'tiktok', name: 'TikTok', cost: 2.70 }
        ];
        servicesLoaded = true;
        
        // Populate select with fallback
        select.innerHTML = '<option value="">Select a service...</option>';
        allServices.forEach(service => {
            const option = document.createElement('option');
            option.value = service.id;
            option.textContent = `${service.name} - $${service.cost.toFixed(2)}`;
            select.appendChild(option);
        });
        
        select.disabled = false;
        
        console.log(`⚠️ Using ${allServices.length} fallback services`);
        showNotification('Using cached services - API unavailable', 'warning');
    }
}

// Helper function to show notifications
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 16px;
        background: ${type === 'warning' ? '#fbbf24' : '#3b82f6'};
        color: white;
        border-radius: 8px;
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
    `;
    
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 5000);
}
```

### **Fix 3: Add Timeout to TextVerified Service**

**File:** `app/services/textverified_service.py` (UPDATE get_services_list)

```python
async def get_services_list(self) -> List[Dict[str, Any]]:
    """Fetch live services from TextVerified API with timeout."""
    if not self.enabled:
        return self._mock_services()

    from app.core.unified_cache import cache

    # Return full cached result if available
    try:
        cached = await cache.get(_SERVICES_CACHE_KEY)
        if cached:
            return cached
    except Exception:
        pass

    # Fast path: fetch only service names
    try:
        cached_names = await cache.get(_SERVICES_NAMES_CACHE_KEY)
        if cached_names:
            return cached_names
    except Exception:
        pass

    try:
        # Add timeout to prevent hanging
        services = await asyncio.wait_for(
            asyncio.to_thread(
                self.client.services.list,
                NumberType.MOBILE,
                ReservationType.VERIFICATION,
            ),
            timeout=10.0,  # 10 second timeout
        )
        
        if not services:
            logger.warning("TextVerified returned empty services list")
            return self._mock_services()
        
        result = [
            {
                "id": s.service_name,
                "name": s.service_name.title(),
                "price": 2.50,
                "cost": 2.50,
            }
            for s in services
        ]
        
        try:
            await cache.set(_SERVICES_NAMES_CACHE_KEY, result, _SERVICES_NAMES_TTL)
        except Exception:
            pass
        
        # Kick off background pricing fetch
        asyncio.create_task(self._fetch_and_cache_pricing(services))
        return result
    
    except asyncio.TimeoutError:
        logger.error("TextVerified API timeout (10s)")
        return self._mock_services()
    
    except Exception as e:
        logger.error(f"Failed to get services: {e}", exc_info=True)
        return self._mock_services()
```

---

## Testing the Fix

### **Test 1: API Working**
```bash
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:9527/api/countries/US/services
# Should return: {"services": [...], "source": "api"}
```

### **Test 2: API Down (Simulate)**
```bash
# Stop TextVerified service, then:
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:9527/api/countries/US/services
# Should return: {"services": [...], "source": "fallback", "error": "API unavailable..."}
```

### **Test 3: Timeout**
```bash
# Simulate slow API (add delay in TextVerified), then:
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:9527/api/countries/US/services
# Should timeout and return fallback after 10 seconds
```

---

## Impact

| Scenario | Before | After |
|----------|--------|-------|
| API down | ❌ 500 error, "Failed to load" | ✅ Fallback services shown |
| Network timeout | ❌ 500 error, "Failed to load" | ✅ Fallback services shown |
| Cache miss | ❌ 500 error, "Failed to load" | ✅ Fallback services shown |
| Slow API | ❌ Hangs indefinitely | ✅ Times out after 10s, shows fallback |
| User experience | ❌ Can't select service | ✅ Always can select service |

---

## Deployment

1. Update `app/api/verification/services_endpoint.py` with error handling
2. Update `app/services/textverified_service.py` with timeout
3. Update `static/js/verification.js` with frontend fallback
4. Test all three scenarios
5. Deploy to production

---

## Summary

**The "Failed to load" error is caused by:**
- ❌ No error handling in services endpoint
- ❌ No timeout on TextVerified API calls
- ❌ No fallback when API fails

**The fix provides:**
- ✅ Graceful error handling with fallback services
- ✅ 10-second timeout to prevent hanging
- ✅ Frontend fallback for offline scenarios
- ✅ User can always select a service

This fix should be applied **IMMEDIATELY** before the verification flow overhaul.

