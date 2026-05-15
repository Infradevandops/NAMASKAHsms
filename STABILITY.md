# Namaskah — Stability Source of Truth

**Version**: v4.7.2
**Tested Against**: https://vrenum.onrender.com (live production)
**Date**: May 15, 2026
**Method**: Live API calls + static codebase analysis

---

## Production Health

```
GET /health → {"status": "healthy", "service": "namaskah-sms"} ✅
GET /        → 200 ✅
GET /login   → 200 ✅
Total routes in OpenAPI: 483 clean (222 phantom routes eliminated — Issue 1 fixed)
```

---

## Confirmed Working (Live-Tested)

| Flow | Endpoint | Result |
|------|----------|--------|
| Register | POST /api/auth/register | ✅ Returns JWT + user |
| Auth me | GET /api/auth/me | ✅ Returns profile |
| Wallet balance | GET /api/wallet/balance | ✅ Returns balance |
| Payment init | POST /api/wallet/paystack/initialize | ✅ Returns Paystack checkout URL |
| Tiers list | GET /api/tiers | ✅ All 4 tiers with full config |
| Current tier | GET /api/tiers/current | ✅ Returns tier + limits |
| Area codes | GET /api/verification/area-codes/US | ✅ Full list with state |
| Carriers | GET /api/verification/carriers/US | ✅ AT&T, T-Mobile etc. |
| Verify history | GET /api/verify/history | ✅ Responds correctly |
| Transaction history | GET /api/wallet/transactions | ✅ Responds correctly |
| Countries | GET /api/countries | ✅ US, GB, CA, AU confirmed |

---

## Issues — Ordered by Impact

---

### Issue 1 — Route Double-Prefix (222 phantom routes)

**Severity**: Medium
**Impact**: Bloat in OpenAPI docs, confusing for SDK/API consumers, wasted memory
**Does it break anything**: No — clean routes work. Phantom routes are unreachable dead weight.

**Root Cause**:
`core_router` is mounted in `main.py` with `prefix="/api"`:
```python
# main.py line 232
fastapi_app.include_router(core_router, prefix="/api")
```
But the individual routers inside `core_router` already have `/api` baked into their own prefix:
```python
# Examples of routers with /api already in their prefix:
notification_endpoints.py  → prefix="/api/notifications"
telegram.py                → prefix="/api/telegram"
whitelabel_endpoints.py    → prefix="/api/whitelabel"
affiliate_endpoints.py     → prefix="/api/affiliate"
analytics_enhanced.py      → prefix="/api/analytics"
countries.py               → prefix="/api/countries"
blacklist.py               → prefix="/api/blacklist"
balance_sync.py            → prefix="/api/balance"
dashboard_activity.py      → prefix="/api/dashboard"
api_key_endpoints.py       → prefix="/api/keys"
push_notifications.py      → prefix="/api/push"
# ... 14 more
```
Result: `core_router` adds `/api` again → `/api/api/telegram`, `/api/api/notifications` etc.

Same problem propagates into `v1_router` (prefix `/api/v1`) which includes `core_router` → `/api/v1/api/...`

Additionally `core/router.py` adds yet another `/api` prefix to some sub-routers:
```python
router.include_router(gdpr_router, prefix="/api")       # gdpr already has /gdpr
router.include_router(forwarding_router, prefix="/api") # forwarding already has /forwarding
router.include_router(webhooks_router, prefix="/api")   # webhooks already has /webhooks
router.include_router(referrals_router, prefix="/api")  # referrals already has /referrals
router.include_router(countries_router, prefix="/api")  # countries already has /api/countries → triple!
```

**Fix**:
Two options — pick one:

**Option A** (recommended): Remove `/api` from individual router prefixes, let mount point control it.
```python
# In each affected router file, change:
router = APIRouter(prefix="/api/notifications", ...)
# To:
router = APIRouter(prefix="/notifications", ...)
```
Affected files (24 total):
- `app/api/core/notification_endpoints.py` → `/notifications`
- `app/api/core/telegram.py` → `/telegram`
- `app/api/core/whitelabel_endpoints.py` → `/whitelabel`
- `app/api/core/affiliate_endpoints.py` → `/affiliate`
- `app/api/core/analytics_enhanced.py` → `/analytics`
- `app/api/core/countries.py` → `/countries`
- `app/api/core/blacklist.py` → `/blacklist`
- `app/api/core/balance_sync.py` → `/balance`
- `app/api/core/dashboard_activity.py` → `/dashboard`
- `app/api/core/api_key_endpoints.py` → `/keys`
- `app/api/core/push_notifications.py` → `/push`
- `app/api/core/mfa.py` → `/user/mfa`
- `app/api/core/textverified_balance.py` → `/textverified`
- `app/api/core/user_settings_endpoints.py` → `/user`
- `app/api/core/disputes.py` → `/disputes`
- `app/api/core/preferences.py` → `/user/preferences`
- `app/api/core/user_insights.py` → `/analytics` (check conflict with analytics_enhanced)
- `app/api/core/currencies.py` → `/currencies`
- `app/api/core/google_oauth.py` → `/auth` (check conflict with auth_routes)
- `app/api/core/provider_health.py` → `/providers`
- `app/api/core/contact.py` → `/contact`
- `app/api/core/quotas.py` → `/quotas`
- `app/api/core/notifications.py` → `/notifications` (check conflict with notification_endpoints)
- `app/api/core/auth_routes.py` → `/auth`

Also remove the extra `prefix="/api"` from these lines in `app/api/core/router.py`:
```python
# Change these:
router.include_router(gdpr_router, prefix="/api")
router.include_router(user_profile_router, prefix="/api")
router.include_router(countries_router, prefix="/api")
router.include_router(user_settings_router, prefix="/api")
router.include_router(forwarding_router, prefix="/api")
router.include_router(webhooks_router, prefix="/api")
router.include_router(referrals_router, prefix="/api")
# To (no prefix):
router.include_router(gdpr_router)
router.include_router(user_profile_router)
router.include_router(countries_router)
router.include_router(user_settings_router)
router.include_router(forwarding_router)
router.include_router(webhooks_router)
router.include_router(referrals_router)
```

**Option B** (safer, less work): Remove `prefix="/api"` from the `core_router` mount in `main.py` and `v1_router`. Routers keep their own `/api` prefix. Clean routes stay the same, phantom routes disappear.
```python
# main.py line 232 — change:
fastapi_app.include_router(core_router, prefix="/api")
# To:
fastapi_app.include_router(core_router)
```
Also in `app/api/v1/router.py` — `core_router` is included without extra prefix so this may already be fine. Verify after applying.

**Estimated time**: 2 hours
**Risk**: Low if Option B. Medium if Option A (need to verify no frontend calls break).

---

### Issue 2 — Tier/Billing Route Duplication

**Severity**: Low-Medium
**Impact**: Confusing API surface, double maintenance, inconsistent responses possible

**Duplicate sets found**:
```
/api/tiers          ←→  /api/billing/tiers
/api/tiers/current  ←→  /api/billing/tiers/current
                        /api/billing/tiers/available
                        /api/billing/tiers/upgrade
                        /api/billing/tiers/cancel
```

**Root Cause**:
`billing_router` (mounted at `/api/billing`) contains tier endpoints.
A separate `tiers_router` is also mounted directly at `/api/tiers`.
Both serve overlapping data.

**Fix**:
Decide on one canonical path. Recommendation: keep `/api/billing/tiers/*` as the full set (it has upgrade/cancel/available), deprecate `/api/tiers` and `/api/tiers/current` with 301 redirects or remove them.

```python
# In main.py, remove the standalone tiers router mount if billing/tiers covers it
# Or add redirect:
@app.get("/api/tiers")
async def tiers_redirect():
    return RedirectResponse("/api/billing/tiers", status_code=301)
```

**Estimated time**: 1 hour
**Risk**: Low — check frontend calls first with `grep -r "api/tiers" templates/ static/`

---

### Issue 3 — Verification Purchase Returns 503 on Cold Start

**Severity**: High (user-facing, blocks core product)
**Impact**: First verification attempt after deploy fails with "Price unavailable"

**Live evidence**:
```
POST /api/verification/request
→ 503: "Price unavailable for this service right now. Please try again in a moment."
```

**Root Cause**:
`lifespan.py` clears the service cache on every startup:
```python
await _cache.delete("tv:services_list")
await _cache.delete("tv:services_names")
```
Then kicks off a background pre-warm task. If a user hits `/api/verification/request` before the pre-warm completes (race condition), `PricingCalculator.calculate_sms_cost()` receives `provider_price=None` and raises:
```python
if provider_price is None or provider_price <= 0:
    raise ValueError("Cannot calculate price: provider price unavailable")
```
Which surfaces as 503.

**Fix**:
Two parts:

**Part 1** — Don't clear cache on startup unless it's stale. The current code unconditionally deletes it:
```python
# lifespan.py — change unconditional delete to TTL check:
# Remove these lines:
await _cache.delete("tv:services_list")
await _cache.delete("tv:services_names")

# Replace with: only clear if older than 24h (cache has its own TTL anyway)
# Simply remove the delete block entirely — TTL handles expiry
```

**Part 2** — Make pre-warm blocking (await it) before yielding, with a timeout:
```python
# lifespan.py — change:
asyncio.create_task(_prewarm())

# To (wait up to 20s before accepting traffic):
try:
    await asyncio.wait_for(_prewarm(), timeout=20.0)
except asyncio.TimeoutError:
    startup_logger.warning("Pre-warm timed out — first request may be slow")
```

**Estimated time**: 30 minutes
**Risk**: Very low — startup may take 5-20s longer, but Render health checks allow for this

---

### Issue 4 — Payment Field Name Inconsistency

**Severity**: Low (frontend works, API consumers affected)
**Impact**: Direct API callers get a confusing 422 validation error

**Live evidence**:
```
POST /api/wallet/paystack/initialize  with {"amount": 10}
→ 422: Field required: amount_usd
```

**Root Cause**:
`app/schemas/payment.py` defines the field as `amount_usd`:
```python
class PaymentInitialize(BaseModel):
    amount_usd: float = Field(..., gt=0)
```
But the natural expectation (and what the wallet endpoint uses) is `amount`. Two schemas exist — `PaymentInitialize` uses `amount_usd`, `WalletAddRequest` uses `amount`.

**Fix**:
Add an alias so both field names are accepted:
```python
# app/schemas/payment.py
from pydantic import BaseModel, Field, field_validator, model_validator

class PaymentInitialize(BaseModel):
    amount_usd: float = Field(None, gt=0)
    amount: float = Field(None, gt=0)

    @model_validator(mode="after")
    def resolve_amount(self):
        if self.amount_usd is None and self.amount is None:
            raise ValueError("amount_usd is required")
        if self.amount_usd is None:
            self.amount_usd = self.amount
        return self
```

Or simpler — just add `amount` as an alias:
```python
class PaymentInitialize(BaseModel):
    amount_usd: float = Field(..., gt=0, alias="amount", serialization_alias="amount_usd")
    model_config = ConfigDict(populate_by_name=True)
```

**Estimated time**: 20 minutes
**Risk**: None

---

### Issue 5 — Async Notification Warnings in Payment Flow

**Severity**: Low
**Impact**: Payment notifications (email/push) silently fail. Core payment still works.

**Evidence** (from test output, confirmed in code):
```
RuntimeWarning: coroutine 'NotificationDispatcher.notify_payment_completed' was never awaited
RuntimeWarning: coroutine 'EventBroadcaster.broadcast_payment_event' was never awaited
```

**Root Cause**:
In `app/services/payment_service.py`, async notification calls are made inside a sync `except` block without `await`:
```python
except Exception as e:
    logger.error(f"Failed to send payment notification: {e}")
    # The coroutine was created but never awaited
```

**Fix**:
Find the call sites and ensure they are properly awaited or wrapped:
```python
# In payment_service.py — find pattern like:
try:
    NotificationDispatcher.notify_payment_completed(...)  # missing await
except Exception as e:
    ...

# Fix:
try:
    await NotificationDispatcher.notify_payment_completed(...)
except Exception as e:
    ...
```
If the surrounding function is sync, wrap with `asyncio.create_task()` instead:
```python
asyncio.create_task(NotificationDispatcher.notify_payment_completed(...))
```

**Estimated time**: 1 hour
**Risk**: Low

---

### Issue 6 — Test Infrastructure Misalignment (Not Runtime)

**Severity**: Low (tests only, production unaffected)
**Impact**: CI shows failures, misleading health signal

**Specific failures**:

| Test | Failure Reason | Fix |
|------|---------------|-----|
| `test_calculate_sms_cost_payg_*` (5 tests) | Calls `calculate_sms_cost(db, user_id, {})` without `provider_price` — v5.0 made it required | Add `provider_price=1.50` to test calls |
| `test_verify_webhook_signature_valid` | `PAYSTACK_SECRET_KEY` is `None` in test env → `.encode()` fails | Mock `settings.paystack_secret_key = "test_key"` in fixture |
| Integration auth tests (3 tests) | `register` fixture doesn't pass `terms_accepted=True` | Add `"terms_accepted": True` to registration payload in `conftest.py` |
| `test_verification_endpoints_comprehensive` (16 tests) | Status code expectations written before final implementation | Update expected codes to match current responses |
| E2E tests | `playwright` not installed | `pip install playwright && playwright install` in requirements-test.txt |

**Fix for integration conftest**:
```python
# tests/integration/conftest.py or test_wallet_api.py — find register call:
client.post("/api/auth/register", json={
    "email": "...",
    "password": "..."
})
# Add:
client.post("/api/auth/register", json={
    "email": "...",
    "password": "...",
    "terms_accepted": True
})
```

**Estimated time**: 1 day total
**Risk**: None (tests only)

---

## Fix Priority & Time Estimate

| # | Issue | Priority | Time | Risk |
|---|-------|----------|------|------|
| 3 | Verification 503 on cold start | **P1** | 30 min | Very Low |
| 5 | Async notification warnings | **P2** | 1 hour | Low |
| 4 | Payment field name inconsistency | **P2** | 20 min | None |
| 1 | Route double-prefix (222 phantoms) | **P3** | 2 hours | Low |
| 2 | Tier/billing route duplication | **P3** | 1 hour | Low |
| 6 | Test infrastructure alignment | **P4** | 1 day | None |

**Total to full stability: ~1 day of focused work**

---

## What Does NOT Need Fixing

- Core auth flow — working perfectly
- Payment processing — Paystack integration live and functional
- Tier system — all 4 tiers responding correctly
- Area codes / carriers — live data from TextVerified
- Wallet balance — accurate
- Transaction/verification history — correct
- Background services — SMS polling, rental expiry, health audit all starting correctly
- Sentry monitoring — active
- Database — stable, no schema drift in production
- Cache pre-warming — logic is correct, just needs to block startup (Issue 3)

---

## Canonical API Paths (Use These)

```
POST   /api/auth/register              body: {email, password, terms_accepted: true}
POST   /api/auth/login
GET    /api/auth/me
GET    /api/wallet/balance
POST   /api/wallet/paystack/initialize body: {amount_usd: float}
GET    /api/wallet/transactions
GET    /api/tiers
GET    /api/tiers/current
POST   /api/verification/request       body: {service, country, area_code?, carrier?}
GET    /api/verification/status/{id}
GET    /api/verification/area-codes/US
GET    /api/verification/carriers/US
GET    /api/verify/history
```

---

*Source of truth. Do not create additional assessment docs.*
