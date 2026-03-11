# Service Loading Fix — Task List

**Date**: 2026-03-11  
**Status**: 🔄 Open  
**Symptom**: "Failed to load — tap to retry" on the Service selector in `verify_modern.html`  
**Screenshot**: Step 1 "Select Service" — input shows error placeholder, dropdown never populates

---

## Why It's Still Failing (Root Cause Summary)

The `.kiro` tasks fixed `static/js/verification.js` and `services_endpoint.py`.  
Neither of those files is what the user sees.

The active template is `templates/verify_modern.html`. It has its **own inline `loadServices()` function** (line 401) that was never touched. That function has two independent failure modes:

### Failure Mode A — No fallback in the catch block
When the `fetch('/api/countries/US/services')` call fails for any reason (network error, timeout, non-2xx response), the catch block does:
```js
_modalItems['service'] = [];   // ← empties the list
input.placeholder = 'Failed to load — tap to retry';  // ← shows the error
```
There is no hardcoded fallback. The fix in `static/js/verification.js` is irrelevant — that file's `loadServices()` is never called from `verify_modern.html`.

### Failure Mode B — Double router registration causes route ambiguity
`services_endpoint.py` defines `prefix="/api/countries"`.  
In `main.py` it is registered **twice**:
- Line 188: `fastapi_app.include_router(services_endpoint_router)` → mounts at `/api/countries/US/services` ✅
- Line 192: `fastapi_app.include_router(verification_router, prefix="/api")` → `verification_router` includes `services_router` which already has `prefix="/api/countries"` → second copy mounts at `/api/api/countries/US/services` ❌

FastAPI silently registers both. The first wins for routing so the endpoint is reachable, but the duplicate registration is a latent bug that will cause confusion and should be removed.

### Failure Mode C — `res.ok` check throws on 401/403 before fallback runs
The fetch sends `Authorization: Bearer ${token}`. If the token is expired or missing, the server returns 401. `res.ok` is false → `throw new Error('fetch failed')` → catch block fires → empty list + error placeholder. The backend fallback never runs because the request never reaches the endpoint logic.

---

## Task 1 — Fix `verify_modern.html` catch block: add hardcoded fallback

**File**: `templates/verify_modern.html`  
**Lines**: ~440–444 (the catch block inside `loadServices()`)

**Current code**:
```js
} catch (e) {
    console.error('Failed to load services:', e);
    _modalItems['service'] = [];
    const input = document.getElementById('service-search-input');
    if (input) { input.placeholder = 'Failed to load — tap to retry'; input.onclick = () => { input.placeholder = 'Search services...'; input.onclick = null; loadServices(); }; }
}
```

**Fixed code**:
```js
} catch (e) {
    console.error('Failed to load services:', e);
    const FALLBACK = [
        { id: 'whatsapp',   name: 'WhatsApp',   price: 2.50 },
        { id: 'telegram',   name: 'Telegram',   price: 2.00 },
        { id: 'google',     name: 'Google',     price: 2.00 },
        { id: 'facebook',   name: 'Facebook',   price: 2.50 },
        { id: 'instagram',  name: 'Instagram',  price: 2.75 },
        { id: 'discord',    name: 'Discord',    price: 2.25 },
        { id: 'twitter',    name: 'Twitter',    price: 2.50 },
        { id: 'microsoft',  name: 'Microsoft',  price: 2.25 },
        { id: 'amazon',     name: 'Amazon',     price: 2.50 },
        { id: 'uber',       name: 'Uber',       price: 2.75 },
    ];
    _modalItems['service'] = _buildServiceItems(FALLBACK);
    console.warn(`⚠️ Using ${FALLBACK.length} hardcoded fallback services`);
}
```

**Why**: Replaces the empty-list assignment with a populated fallback so the dropdown always has options regardless of API or auth state.

### Checklist
- [ ] `_modalItems['service']` is never set to `[]` in the catch block
- [ ] `FALLBACK` array has ≥ 8 services with valid `id`, `name`, `price` fields
- [ ] `_buildServiceItems(FALLBACK)` is called so items match the expected `{ value, label, sub, price }` shape
- [ ] The `'Failed to load — tap to retry'` placeholder is removed from the catch block
- [ ] Console shows `⚠️ Using N hardcoded fallback services` when API fails
- [ ] Service dropdown populates immediately even when the API call fails

### Tests
**Manual — API working**:
1. Log in, navigate to `/verify`
2. Open DevTools → Network tab
3. Confirm `GET /api/countries/US/services` returns 200 with `source: "api"` or `"fallback"`
4. Service dropdown populates within 15s ✅

**Manual — Simulate API failure**:
1. Open DevTools → Network tab → right-click the services request → Block request URL
2. Reload `/verify`
3. Service dropdown must still populate with fallback services ✅
4. Console shows `⚠️ Using 10 hardcoded fallback services` ✅
5. No `'Failed to load — tap to retry'` placeholder visible ✅

**Manual — Expired token**:
1. Open DevTools → Application → Local Storage → delete `access_token`
2. Navigate to `/verify` without logging in
3. Service dropdown must still populate with fallback services ✅
4. User can select a service (they'll be prompted to log in at purchase step) ✅

---

## Task 2 — Remove duplicate router registration in `main.py`

**File**: `main.py`  
**Lines**: ~185–192

**Current code**:
```python
from app.api.verification.services_endpoint import router as services_endpoint_router
...
fastapi_app.include_router(services_endpoint_router)          # ← registers /api/countries/...
...
fastapi_app.include_router(verification_router, prefix="/api") # ← also registers /api/api/countries/... via verification_router
```

**Fixed code**: Remove the standalone `services_endpoint_router` import and registration. The route is already covered by `verification_router`.

```python
# Remove these two lines:
from app.api.verification.services_endpoint import router as services_endpoint_router
fastapi_app.include_router(services_endpoint_router)
```

**Why**: `verification_router` already includes `services_router` (confirmed in `app/api/verification/router.py` line 6). The standalone registration is a leftover from before the verification router was assembled. Keeping it creates a duplicate route at `/api/countries/...` and a ghost route at `/api/api/countries/...`.

### Checklist
- [ ] `services_endpoint_router` import removed from `main.py`
- [ ] `fastapi_app.include_router(services_endpoint_router)` line removed from `main.py`
- [ ] `GET /api/countries/US/services` still returns 200 after removal (served by `verification_router`)
- [ ] `GET /api/api/countries/US/services` returns 404 (ghost route gone)
- [ ] No other router in `main.py` imports `services_endpoint_router`

### Tests
**curl after fix**:
```bash
# Must return 200
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/countries/US/services
# Must return 404
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/api/countries/US/services
```

**App startup**:
- [ ] App starts without `AssertionError: Duplicate route` warnings in logs
- [ ] `/docs` shows `GET /api/countries/{country}/services` listed exactly once

---

## Task 3 — Make the services endpoint public (no auth required)

**File**: `app/api/verification/services_endpoint.py`  
**Problem**: The frontend sends `Authorization: Bearer ${token}` but the endpoint has no `Depends(get_current_user)`. However, if any upstream middleware or future change adds auth enforcement, a missing/expired token will cause 401 → catch block → empty list. More importantly, the service list is not user-specific data — there is no reason to require auth.

**Fix**: Explicitly document the endpoint as public and ensure no auth dependency is ever added. Also handle the case where the frontend sends an expired token gracefully by not relying on auth at all.

Since the endpoint already has no `Depends` auth, the fix is defensive — add a comment and confirm the CSRF middleware already whitelists `/api/countries`:

```python
@router.get("/{country}/services")
async def get_services(country: str):
    """
    Get services list. PUBLIC endpoint — no auth required.
    Service list is not user-specific. Auth header is accepted but ignored.
    CSRF middleware already whitelists /api/countries (see csrf_middleware.py:67).
    """
```

### Checklist
- [ ] Endpoint has no `Depends(get_current_user)` or any auth dependency
- [ ] Docstring explicitly marks it as public
- [ ] `GET /api/countries/US/services` returns 200 with no `Authorization` header
- [ ] `GET /api/countries/US/services` returns 200 with an expired/invalid token
- [ ] `GET /api/countries/US/services` returns 200 with no token at all

### Tests
```bash
# No token — must return 200
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/countries/US/services

# Invalid token — must return 200 (not 401)
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer invalid.token.here" \
  http://localhost:8000/api/countries/US/services

# Valid token — must return 200
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $VALID_TOKEN" \
  http://localhost:8000/api/countries/US/services
```

---

## Task 4 — Add `res.status === 401` retry-with-refresh in `verify_modern.html`

**File**: `templates/verify_modern.html`  
**Problem**: If a token refresh mechanism exists elsewhere in the app, the services fetch should attempt a token refresh on 401 before falling back. Currently it immediately throws on any non-ok status.

**Fix**: Add a 401-specific branch that attempts a token refresh, then retries once before falling back:

```js
const res = await fetch('/api/countries/US/services', {
    headers: { 'Authorization': `Bearer ${token}` },
    signal: ctrl.signal
});
clearTimeout(tid);

if (res.status === 401) {
    // Token expired — try without auth (endpoint is public)
    const retryRes = await fetch('/api/countries/US/services', { signal: ctrl.signal });
    if (!retryRes.ok) throw new Error('fetch failed after 401 retry');
    const data = await retryRes.json();
    // ... rest of success path
} else if (!res.ok) {
    throw new Error('fetch failed');
}
```

**Why**: Since the endpoint is public (Task 3), a 401 retry without the auth header will succeed. This eliminates the auth-expiry failure mode entirely without requiring a full token refresh flow.

### Checklist
- [ ] 401 response triggers an unauthenticated retry of the same endpoint
- [ ] Unauthenticated retry succeeds and populates the dropdown
- [ ] Non-401 errors (500, network failure, timeout) still fall through to the hardcoded fallback (Task 1)
- [ ] No infinite retry loop (retry happens exactly once)

### Tests
**Manual — expired token**:
1. Set `localStorage.access_token = 'expired.token.value'`
2. Navigate to `/verify`
3. Network tab shows: first request returns 401, second request (no auth header) returns 200
4. Service dropdown populates ✅

---

## Acceptance Criteria (all 4 tasks complete)

| Scenario | Expected Result |
|----------|----------------|
| API working, valid token | Dropdown populates from API (`source: api`) |
| API working, no token | Dropdown populates from API (public endpoint, no auth needed) |
| API working, expired token | Dropdown populates via unauthenticated retry |
| API down, any token state | Dropdown populates from hardcoded fallback (10 services) |
| Network timeout (>15s) | Dropdown populates from hardcoded fallback |
| `localStorage` cache hit | Dropdown populates instantly from cache, no API call |
| Ghost route `/api/api/countries/...` | Returns 404 |
| App startup | No duplicate route warnings in logs |

---

## Implementation Order

1. **Task 1** — highest impact, fixes the visible symptom immediately
2. **Task 3** — makes the endpoint reliably public before Task 4 depends on it
3. **Task 4** — adds the 401 retry path that relies on Task 3
4. **Task 2** — cleanup, lowest risk, do last

---

## Files to Change

| File | Task | Change |
|------|------|--------|
| `templates/verify_modern.html` | 1, 4 | Fix catch block fallback + add 401 retry |
| `main.py` | 2 | Remove duplicate `services_endpoint_router` registration |
| `app/api/verification/services_endpoint.py` | 3 | Add public docstring, confirm no auth dep |
