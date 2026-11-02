# Area Code Selector — How TV Area Codes Are Captured and Served to Users

**Created**: October 25, 2026
**Updated**: October 25, 2026 — all gaps implemented
**Source**: SDK source (`services_api.py`, `verifications_api.py`, `dtypes.py`) +
           platform code (`area_code_endpoints.py`, `area_code_geo.py`, `textverified_service.py`,
           `verification-flow.js`)
**Purpose**: Document the complete area code data flow from TV's API to the user's screen,
             including what TV provides, what we add, and where the gaps are.

## Implementation Status

| Gap | Fix | File | Status |
|-----|-----|------|--------|
| Modal shows state only, not city | Enrich endpoint with NANPA city data | `area_code_endpoints.py` | ✅ Done |
| `/check` blocks on TV outage | Fall through if TV list empty | `area_code_endpoints.py` | ✅ Done |
| `check_service_available()` ignores area code surcharge | Add `area_code_requested` param | `textverified_service.py` | ✅ Done |
| Purchase paths don't pass area code flag to pricing | Wire `area_code_requested=bool(area_code)` | `purchase_endpoints.py` | ✅ Done |
| No background area code cache refresh | 23h refresh loop in lifespan | `lifespan.py` | ✅ Done |

---

## 1. What TV Actually Provides for Area Codes

### The endpoint

```
GET /api/pub/v2/area-codes
→ List[AreaCode]
```

SDK `AreaCode` dataclass (confirmed from `dtypes.py`):
```python
@dataclass
class AreaCode:
    area_code: str   # "212"
    state: str       # "NY"
```

**That is all TV gives us.** Two fields per code. No city. No availability signal.
No quantity. No indication of which codes have numbers in stock right now.

TV's own SDK docstring says:
> "Please fetch area codes and services, as we update our available area codes and services frequently."

This means TV's supported area code list changes — codes get added and removed.
The list must be fetched live and cached, not hardcoded.

### What `area_code_select_option` does on `verifications.create()`

From `verifications_api.py` (`NewVerificationRequest`):
```python
area_code_select_option: Optional[List[str]] = None
# Serialises to: "areaCodeSelectOption": ["212", "917", "646", ...]
```

This is an **ordered preference list**. TV picks the best available number from the list
in order. If none of the listed codes have inventory, TV assigns whatever it has — it does
**not** reject the purchase. This is a preference, not a hard filter.

The pricing endpoint also accepts `area_code: bool` — a boolean meaning "I want area code
filtering" (affects price), not the actual code value:
```python
# VerificationPriceCheckRequest
area_code: bool   # True = filtering requested, adds surcharge to price
```

---

## 2. What the Platform Adds on Top of TV

TV gives us `area_code` + `state`. The platform enriches this with:

**NANPA data** (`app/assets/nanpa_index.json` loaded by `area_code_geo.py`):
```json
{
  "212": {
    "major_city": "New York",
    "state": "NY",
    "lat": 40.7128,
    "lng": -74.0060,
    "metro": "New York"
  }
}
```

This gives us city name, coordinates, and metro area — none of which TV provides.
Used for:
- Showing "212 — New York, NY" in the modal instead of just "212 — NY"
- Geo-proximity ranking of alternatives (haversine distance)
- Same-city / nearby / same-state tiering

**Purchase intelligence** (`PurchaseIntelligenceService`):
- Historical purchase outcomes per `(service, area_code)` pair
- Scores availability as `available` / `unavailable` / `unknown` with confidence
- Used by `/check` endpoint to warn users before they attempt a purchase

---

## 3. The Full Data Flow — From TV to User Screen

### Phase A: Area code list population (on page load)

```
User opens /verify
    ↓
verification-flow.js → loadAreaCodes()
    ↓
GET /api/area-codes?country=US                    [area_code_endpoints.py]
    ↓
cache.get("area_codes:US")  ← 1-hour TTL
    ↓ miss
_tv.get_area_codes_list()
    ↓
SDK: client.services.area_codes()
    ↓
GET /api/pub/v2/area-codes → [{area_code, state}, ...]
    ↓
cache.set("area_codes:US", result, 3600)
    ↓
Returns: [{area_code: "212", state: "NY"}, {area_code: "917", state: "NY"}, ...]
    ↓
JS builds modal items:
    value: c.area_code          → "212"
    label: c.area_code          → "212"
    sub:   `${c.city}, ${c.state}` → "NY"   ← city is blank (TV doesn't provide it)
```

**Current gap**: `c.city` is always empty because TV's `AreaCode` only has `area_code`
and `state`. The sub-label shows `"212 — NY"` instead of `"212 — New York, NY"`.
The NANPA city data exists in `area_code_geo.py` but is not piped into this endpoint.

### Phase B: User types an area code — live availability check

```
User types "212" in area code input
    ↓
debouncedCheckAreaCode("212")  [500ms debounce]
    ↓
GET /api/area-codes/check?area_code=212&service=whatsapp   [area_code_endpoints.py]
    ↓
1. Validate: is "212" a 3-digit number? ✅
2. Validate: is "212" in NANPA_DATA? ✅ (local geo data)
3. Is "212" in TV's supported list? (from cache)
   → If not: 400 "Area code not supported by provider"
4. PurchaseIntelligenceService.score_availability("whatsapp", "212")
   → reads historical purchase outcomes from DB
   → returns {available: True/False/None, confidence: 0.0-1.0}
5. Build response:
   → status: "available" | "unavailable" | "unknown"
   → message: human-readable explanation
   → alternatives: nearby codes if unavailable/unknown
    ↓
UI renders:
  "available"   → green border, "✓ Available" badge, continue enabled
  "unavailable" → amber border, "Unavailable" badge, alternatives shown, continue blocked
  "unknown"     → grey message, alternatives shown, continue enabled with warning
```

### Phase C: User selects area code, proceeds to purchase

```
User clicks "Continue →"
    ↓
VerificationFlow.selectedAreaCode = "212"
    ↓
createVerification() → POST /api/verification/request/stream
    ↓
SSE: pricing_check
  check_service_available(service, capability)
  → SDK verifications.pricing(area_code=True, ...)   ← area_code=True means filtering requested
  → returns price with area code surcharge included
    ↓
SSE: purchasing
  provider_router.purchase_with_failover(area_code="212", ...)
    ↓
  textverified_service.create_verification(area_code="212", ...)
    ↓
  _build_area_code_preference("212")
    ↓
    _get_area_codes_by_state()
      → cache.get("tv:area_codes_by_state")  ← 24h TTL
      → if miss: get_area_codes_list() → group by state
      → {"NY": ["212", "917", "646", "718", "347", "929", ...], ...}
    ↓
    finds "212" → state "NY"
    returns ["212", "917", "646", "718", "347", "929", ...]
    ↓
  verifications.create(
      service_name=service,
      capability=cap,
      area_code_select_option=["212", "917", "646", ...],  ← full NY chain
      max_price=max_price,
  )
    ↓
  TV assigns best available number from the preference list
    ↓
  assigned_number = result.number  e.g. "+19175551234"
  assigned_area_code = "917"
    ↓
  area_code_match = "917" in ["212","917","646",...]  → True (same-state match)
  fallback_applied = ("917" != "212")  → True
  same_state_fallback = True
    ↓
SSE: complete → {phone_number, ends_at, fallback_applied, assigned_area_code, requested_area_code}
    ↓
UI shows fallback warning:
  "212 unavailable — assigned nearby 917 (same state)"
```

---

## 4. The Three-Layer Availability Signal

The platform uses three independent signals to determine area code availability,
applied in order from cheapest to most accurate:

### Layer 1 — TV's supported list (is the code valid at all?)
```
Source: GET /api/pub/v2/area-codes
Cache:  1 hour (area_codes:US)
Signal: Is this area code in TV's active list?
Cost:   Free — already cached for area code modal
Use:    Gate in /check endpoint — reject unknown codes immediately
```

### Layer 2 — Purchase intelligence (has it worked recently?)
```
Source: Platform DB — purchase_outcomes table
Cache:  None — live DB query
Signal: Historical success/failure rate for (service, area_code) pair
Cost:   DB query (~5ms)
Use:    /check endpoint — warn user before they attempt purchase
        Informs retry decision in create_verification() (score.confidence >= 0.6)
```

### Layer 3 — TV's proximity chain (what to try if preferred code fails?)
```
Source: TV area codes grouped by state (tv:area_codes_by_state, 24h cache)
Signal: All codes in the same state as the requested code
Cost:   Free — already cached from area code list
Use:    area_code_select_option preference list sent to verifications.create()
        TV picks best available from the chain
```

---

## 5. What TV Honors vs What It Ignores

| What we send | What TV does | Confirmed from SDK |
|-------------|-------------|-------------------|
| `area_code_select_option: ["212"]` | Tries to assign a 212 number | ✅ |
| `area_code_select_option: ["212","917","646"]` | Tries each in order, assigns first available | ✅ |
| `area_code_select_option: []` or `None` | Assigns any available number | ✅ |
| `area_code_select_option: ["999"]` (invalid) | Assigns any available number (ignores invalid) | Likely — unverified |
| `area_code: True` in pricing request | Returns price with area code surcharge | ✅ |
| `area_code: False` in pricing request | Returns base price without surcharge | ✅ |

**TV does not guarantee the assigned number matches the requested area code.**
It is a preference. If no numbers are available in any of the listed codes, TV assigns
whatever it has. Our platform detects this mismatch post-assignment and either:
- Accepts it (same-state fallback) and notifies the user
- Cancels and retries (up to `max_retries=2`)
- Raises `AreaCodeUnavailableException` with alternatives if retries exhausted

---

## 6. Current Gaps and Improvements

### Gap 1 — Area code modal shows state only, not city (UX)
**Where**: `area_code_endpoints.py` → `get_area_codes()` response
**Problem**: TV returns `{area_code, state}`. The JS reads `c.city` which is always empty.
Modal shows `"212 — NY"` instead of `"212 — New York, NY"`.
**Fix**: Enrich the endpoint response with NANPA city data before returning:

```python
# area_code_endpoints.py — get_area_codes()
from app.services.area_code_geo import NANPA_DATA

codes = await _tv.get_area_codes_list()
enriched = []
for c in codes:
    ac = c.get("area_code", "")
    nanpa = NANPA_DATA.get(ac, {})
    enriched.append({
        "area_code": ac,
        "state": c.get("state", ""),
        "city": nanpa.get("major_city", ""),   # add city from NANPA
    })
result = {"success": True, "area_codes": enriched}
```

JS already reads `c.city` — no frontend change needed.

---

### Gap 2 — `/check` endpoint does not validate against TV's live list on cache miss
**Where**: `area_code_endpoints.py` → `check_area_code_availability()`
**Problem**: If the 1-hour cache is cold, the check endpoint fetches TV's list and caches it.
But if TV's API is down during that fetch, `tv_supported` is empty and every area code
fails the "not supported by provider" check — blocking all area code purchases.
**Fix**: Fall through to NANPA validation if TV list is unavailable:

```python
if area_code not in supported_strings and supported_strings:
    # Only reject if we actually have a list — don't block on TV outage
    raise HTTPException(status_code=400, detail="Area code not supported by provider")
```

---

### Gap 3 — Area code cache TTL mismatch
**Where**: `area_code_endpoints.py` vs `textverified_service.py`

| Cache key | TTL | Used by |
|-----------|-----|---------|
| `area_codes:US` | 1 hour | `/check` endpoint, modal list |
| `tv:area_codes_list` | 24 hours | `_build_area_code_preference()` |
| `tv:area_codes_by_state` | 24 hours | `_build_area_code_preference()` |

The `/check` endpoint uses `area_codes:US` (1h). The purchase path uses
`tv:area_codes_by_state` (24h). A code could be in the 1h cache (valid for check)
but not in the 24h state cache (missing from proximity chain). They should share
the same underlying data. The 24h cache is the authoritative one — the 1h cache
should be derived from it, not fetched separately.

---

### Gap 4 — `check_service_available()` does not account for area code surcharge in price
**Where**: `textverified_service.py` → `check_service_available()`
**Problem**: The availability check calls `verifications.pricing(area_code=False, ...)`.
When a user has selected an area code, the actual purchase price will be higher
(area code surcharge). The balance check uses the non-surcharge price, so a user
with exactly enough balance for the base price may fail at purchase time.
**Fix**: Pass `area_code=bool(area_code_requested)` to `check_service_available()`:

```python
# purchase_endpoints.py — both legacy and SSE paths
area_code = request.area_codes[0] if request.area_codes else None
avail = await _tv_service.check_service_available(
    request.service,
    capability=request.capability,
    area_code_requested=bool(area_code),   # add this
)
```

```python
# textverified_service.py — check_service_available()
async def check_service_available(
    self, service_name: str, capability: str = "sms",
    area_code_requested: bool = False,
) -> dict:
    snap = await asyncio.wait_for(
        asyncio.to_thread(
            self.client.verifications.pricing,
            service_name=service_name,
            area_code=area_code_requested,   # was hardcoded False
            carrier=False,
            number_type=num_type,
            capability=cap,
        ),
        timeout=8.0,
    )
```

---

## 7. Proactive Area Code Capture — How It Should Work

The current flow is **reactive** — area codes are fetched when the user opens the modal.
The proactive approach pre-fetches and keeps the list warm so users never wait.

### On platform startup (lifespan)
```python
# app/core/lifespan.py — add to startup sequence
async def _warm_area_codes():
    tv = TextVerifiedService()
    if tv.enabled:
        await tv.get_area_codes_list()   # populates tv:area_codes_list (24h)
        await tv._get_area_codes_by_state()  # populates tv:area_codes_by_state (24h)
        logger.info("Area code cache warmed on startup")

asyncio.create_task(_warm_area_codes())
```

### Background refresh (every 23 hours — before 24h TTL expires)
```python
# Add to the existing stock monitor loop or a dedicated background task
async def run_area_code_refresh():
    while True:
        await asyncio.sleep(23 * 3600)  # refresh before 24h TTL expires
        tv = TextVerifiedService()
        if tv.enabled:
            # Bust both caches to force fresh fetch
            await cache.set("tv:area_codes_list", None, 1)
            await cache.set("tv:area_codes_by_state", None, 1)
            await tv.get_area_codes_list()
            await tv._get_area_codes_by_state()
            logger.info("Area code cache refreshed (background)")
```

### On the `/area-codes` endpoint — enrich with NANPA city data
```python
@router.get("")
async def get_area_codes(country: str = Query(...), user_id: str = Depends(get_current_user_id)):
    cached = await cache.get(_CACHE_KEY)
    if cached:
        return cached

    codes = await _tv.get_area_codes_list()

    # Enrich with NANPA city data — TV only gives area_code + state
    enriched = []
    for c in codes:
        ac = c.get("area_code", "")
        nanpa = NANPA_DATA.get(ac, {})
        enriched.append({
            "area_code": ac,
            "state": c.get("state", ""),
            "city": nanpa.get("major_city", ""),
        })

    result = {"success": True, "area_codes": enriched}
    if enriched:
        await cache.set(_CACHE_KEY, result, _CACHE_TTL)
    return result
```

---

## 8. How the UI Operates This With Users — Step by Step

### Step 1: Modal opens (PAYG+ users only)
- `loadAreaCodes()` fires on `chooseMethod('sms')` if tier ≥ PAYG
- Fetches from `/api/area-codes?country=US` (1h cache)
- Builds modal items: `{value: "212", label: "212", sub: "New York, NY"}`
- Modal shows flat list grouped by nothing — just code + city + state
- User can search by typing (filters `label` and `value`)

### Step 2: User types a 3-digit code
- `debouncedCheckAreaCode(value)` fires after 500ms idle
- Validates locally: must be 3 digits
- Fires `GET /api/area-codes/check?area_code=212&service=whatsapp`
- Shows spinner on the input while waiting (~200ms)
- On response:
  - `available` → green border, "✓ Available" badge, continue button enabled
  - `unavailable` → amber border, "Unavailable" badge, alternatives rendered below input, continue blocked
  - `unknown` → grey message "No data yet — you won't be charged if unavailable", alternatives shown, continue enabled

### Step 3: Alternatives rendering
When status is `unavailable` or `unknown`, the `/check` endpoint returns up to 8 alternatives:
```json
[
  {"area_code": "917", "city": "New York", "state": "NY", "proximity": "same_city", "status": "available"},
  {"area_code": "646", "city": "New York", "state": "NY", "proximity": "same_city", "status": "unknown"},
  {"area_code": "201", "city": "Jersey City", "state": "NJ", "proximity": "nearby", "status": "available"}
]
```
Each renders as a clickable chip with a colored dot (green/amber/grey).
Clicking one calls `selectAlternative(code)` which re-runs `debouncedCheckAreaCode(code)`.

### Step 4: Selection chip
Once a valid area code is selected, a chip appears below the input:
`📍 212 — New York, NY  [✕]`
Clicking ✕ calls `clearAreaCode()` which resets the selection.

### Step 5: Purchase
The selected area code is sent as `area_codes: ["212"]` in the SSE request body.
The backend builds the full same-state proximity chain and sends it to TV as
`area_code_select_option`. TV assigns the best available number from that chain.

### Step 6: Post-purchase feedback
If TV assigned a different area code than requested:
- `fallback_applied: true` in the SSE `complete` event
- `showFallbackWarning(requested, assigned, sameState)` fires
- Same-state: green banner "212 unavailable — assigned nearby 917 (same state)"
- Different-state: amber banner "212 unavailable — assigned 305 (different state)" + link to update preferences

---

## 9. Data Sources Summary

| Data | Source | Cache TTL | Used for |
|------|--------|-----------|---------|
| Area code list (code + state) | TV `GET /api/pub/v2/area-codes` | 24h (`tv:area_codes_list`) | Proximity chain building |
| Area codes by state index | Derived from TV list | 24h (`tv:area_codes_by_state`) | `_build_area_code_preference()` |
| Area code list for modal | TV list + NANPA enrichment | 1h (`area_codes:US`) | Modal display |
| City / metro / coordinates | NANPA `nanpa_index.json` (local asset) | In-memory (module load) | City labels, geo proximity |
| Historical availability | Platform DB `purchase_outcomes` | None (live query) | `/check` scoring |
| Proximity alternatives | NANPA haversine calculation | None (computed) | `/check` alternatives |

---

## 10. Files Involved

| File | Role |
|------|------|
| `app/api/verification/area_code_endpoints.py` | `/area-codes` and `/area-codes/check` endpoints |
| `app/services/textverified_service.py` | `get_area_codes_list()`, `_get_area_codes_by_state()`, `_build_area_code_preference()` |
| `app/services/area_code_geo.py` | NANPA data, haversine proximity, `get_nearby()`, `get_ranked_alternatives()` |
| `app/assets/nanpa_index.json` | Local NANPA area code metadata (city, state, lat/lng, metro) |
| `static/js/verification-flow.js` | `loadAreaCodes()`, `debouncedCheckAreaCode()`, `renderAlternatives()`, `selectAlternative()` |
| `app/core/lifespan.py` | Startup cache warming (to be added) |
