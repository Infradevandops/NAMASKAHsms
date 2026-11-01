# TV Stock Accuracy + Verification Flow Optimization

**Created**: November 1, 2026
**Version**: 4.9.6
**Priority**: 🔴 CRITICAL — stock shown as available may not be purchasable

---

## 1. Last Deploy to Production

**Commit**: `8d6aa0bd` — `docs: update PLATFORM_STATUS, OPS_SUMMARY, ACTIVE_SPRINT`
**Date**: November 1, 2026
**Branch**: `main`

Last feature-bearing deploy: `750a8d9f` — `feat: v4.9.4 verification flow — SSE purchase, dynamic ends_at, TV webhook, orphan recovery`

**What shipped to prod since v4.9.1**:

| Version | What shipped |
|---------|-------------|
| v4.9.2 | Service categories, price per service, success rate, demand badge, `max_price` guard |
| v4.9.3 | JS test suite (92 tests), mobile responsiveness, CI frontend gate |
| v4.9.4 | SSE streaming purchase, dynamic `ends_at` window, TV webhook instant SMS, orphan recovery |
| v4.9.5 | Notification 405 fix, duplicate lock, dark theme CSS |
| v4.9.6 | TV webhook test coverage, CI gate 24 files |

---

## 2. How the Platform Captures Available Products from TV's API

### What TV's API Actually Provides

TV has two relevant endpoints:

**`GET /api/pub/v2/services`** — returns a list of services with:
- `serviceName` — slug (e.g. `whatsapp`)
- `capability` — `sms` or `voice`
- `price` — **`null` means out of stock**. A non-null price means TV has inventory.
- `quantity` — **not always present**. When present, it's the number of available numbers.

**`POST /api/pub/v2/verifications/pricing`** — per-service pre-purchase check:
- Returns `price` and `quantity` for a specific service at purchase time
- This is the most accurate availability signal — it's what TV checks internally before charging

### What Our Platform Does

**Stock monitor** (`stock_monitor.py`) — runs every 15 minutes:
1. Calls `fetch_raw_services_with_quantity()` — hits `GET /api/pub/v2/services` directly (bypasses SDK which drops `quantity`)
2. For each service: `available = qty > 0` if quantity present, else `available = price is not None and price > 0`
3. Corrects with real purchase outcomes (`services:outcome:{slug}`) — if a purchase just failed, marks unavailable for 30 min
4. Writes to `services:stock` Redis key with 2-minute TTL

**Services cache** (`tv:services_list`) — 24-hour TTL:
- Populated by `get_services_list()` which calls the SDK `services.list()` then `_fetch_prices_inline()`
- `_fetch_prices_inline()` calls `POST /api/pub/v2/verifications/pricing` per service (up to 10 concurrent)
- If inline pricing times out, falls back to names-only cache (price=null) and fires background task

**SSE purchase flow** — `check_service_available()` called at step 1:
- Calls `POST /api/pub/v2/verifications/pricing` live, right before purchase
- Returns `{available: false, reason: "no_inventory"}` if `price == null`
- This is the last gate before charge commits

---

## 3. Critical Problem: Stock Shown as Available May Not Be Purchasable

### Root Cause Analysis

**Gap 1 — 15-minute staleness window**
The stock monitor refreshes every 15 minutes. TV inventory can sell out in seconds for popular services (WhatsApp, Telegram). A service shown as "in stock" in the UI may have sold out 14 minutes ago.

**Gap 2 — `quantity` field is unreliable from TV**
`fetch_raw_services_with_quantity()` tries to read `quantity`, `qty`, `availableCount`, `available_count`, `count` from the raw API response. TV's SDK documentation does not guarantee this field is present. In practice, `quantity` is often `null` — so availability falls back to `price is not None`, which is a weaker signal.

**Gap 3 — 24-hour services cache can serve stale prices**
`tv:services_list` has a 24-hour TTL. If a service goes out of stock, the cached `price` is still non-null for up to 24 hours. The stock monitor (2-min TTL) and the services cache (24-hour TTL) are out of sync — the stock dot on the UI reads from the stock monitor, but the purchase flow reads from the services cache for pricing.

**Gap 4 — `check_service_available()` is the only real-time gate, but it's only in the SSE path**
The legacy `POST /verification/request` endpoint does NOT call `check_service_available()`. It calls `_get_provider_price()` which reads from the 24-hour cache. A user on the legacy path can attempt to purchase an out-of-stock service and only discover it's unavailable when TV's `verifications.create()` throws — after the UI has already shown "Securing your number..." for 5-30 seconds.

**Gap 5 — `price = null` from TV means out of stock, but our code treats it as "unknown"**
In `build_stock_map()`: `available = price is not None and float(price) > 0`. This is correct. But in `get_services_list()`, a null-price entry is cached in `tv:services_names` and served to the frontend as a valid service — just without a price displayed. The frontend shows it in the picker with no price, and the user can still attempt to purchase it.

### What This Means in Production

A user can:
1. See a service marked "in stock" (stock dot green)
2. Click it, see a price displayed
3. Start the SSE purchase flow
4. Hit `check_service_available()` at step 1 → get `no_inventory` → see "No numbers available"

OR on the legacy path:
1. See a service marked "in stock"
2. Start purchase
3. Wait 5-30 seconds while TV's `verifications.create()` runs
4. Get a `no_inventory` ProviderError → see "Provider temporarily unavailable"

The SSE path handles this correctly. The legacy path does not. The stock display is best-effort, not guaranteed.

---

## 4. Verification Flow — Current vs TV's Flow

### TV's Actual Flow (from SDK + API docs)

```
1. Check availability     POST /api/pub/v2/verifications/pricing
                          → price=null means stop, price>0 means proceed

2. Create verification    POST /api/pub/v2/verifications
                          → returns VerificationExpanded with:
                            - id (activation_id)
                            - number (phone number)
                            - ends_at (real expiry, typically 10-60 min)
                            - total_cost
                            - cancel.can_cancel
                            - report.can_report

3. Poll for SMS           GET /api/pub/v2/verifications/{id}/sms
   (or webhook push)      → sms.incoming() iterator with since= filter
                          → parsedCode is TV's extracted code
                          → TV webhook POSTs instantly on SMS arrival

4. Complete or report     If SMS received → done
                          If timeout → verifications.report(id) → TV refunds to account
                          If cancel → verifications.cancel(id) → refund if can_cancel
```

### Our Platform's Flow (SSE path)

```
Step 1: pricing_check     check_service_available() → POST /api/pub/v2/verifications/pricing
                          ✅ Matches TV step 1

Step 2: balance_check     DB query for user credits
                          ✅ Correct

Step 3: purchasing        provider_router.purchase_with_failover()
                          → TextVerifiedAdapter → verifications.create()
                          → VOIP check, area code retry (up to 2 attempts)
                          ✅ Correct, but 5-30s blocking with no sub-step feedback

Step 4: validating        No actual validation happens here
                          ⚠️ This step fires immediately after purchase_result returns
                          It's a UX label only — no real work

Step 5: recording         DB write + BalanceService.deduct_credits_for_verification()
                          ✅ Correct

Step 6: complete          Returns verification_id, phone_number, ends_at, created_at
                          ✅ Correct
```

### Our Platform's Flow (legacy POST /verification/request)

```
1. Idempotency check      Redis + DB
2. Fraud score            Non-blocking, logs only
3. Tier validation        Area code / voice gating
4. _get_provider_price()  Reads from 24h cache — NOT a live availability check
                          ⚠️ No check_service_available() call here
5. PricingCalculator      Calculate cost
6. Balance check          BalanceService.check_sufficient_balance()
7. purchase_with_failover() Blocks 5-30s
8. DB write + debit
9. Polling start
```

---

## 5. Optimization Plan

### Fix 1 — Add `check_service_available()` to legacy purchase path (CRITICAL)

**File**: `app/api/verification/purchase_endpoints.py`
**Where**: After tier validation, before `_get_provider_price()`

```python
# After tier validation, before pricing
avail = await _tv_service.check_service_available(request.service)
if not avail["available"]:
    raise HTTPException(
        status_code=422,
        detail=f"No numbers available for '{request.service}' right now. Please try another service.",
    )
```

This makes the legacy path fail fast (< 1s) instead of burning 5-30s on TV's `verifications.create()`.

### Fix 2 — Filter out null-price services from the service picker (CRITICAL)

**File**: `app/api/core/services.py` → `get_services_stock()`
**File**: `static/js/verification-flow.js` → service picker render

Services with `price = null` from TV mean out of stock. They should either:
- Not appear in the picker at all, OR
- Appear greyed out with "Unavailable" label and be non-selectable

Currently they appear with no price and are selectable.

### Fix 3 — Reduce stock monitor TTL from 2 min to match UI refresh (MEDIUM)

`_STOCK_CACHE_TTL = 120` (2 min) but the background loop sleeps for `_STOCK_CACHE_TTL` (120s) between refreshes. The cache expires exactly when the next refresh fires — there's no overlap. If the refresh is slow, the cache is empty and `get_stock_map()` triggers a synchronous refresh on the next request.

Change loop sleep to 90s so the cache is always warm:

```python
await asyncio.sleep(90)  # refresh before 120s TTL expires
```

### Fix 4 — SSE `validating` step should do real work (LOW)

Currently `validating` fires immediately after `purchase_result` returns with no actual work. This is misleading. Either:
- Remove it and go straight from `purchasing` → `recording`, OR
- Use it to call `get_verification_details()` to confirm the number is live on TV's side

### Fix 5 — Loading spinner intervals (UX)

Current SSE steps and their real durations:

| Step | Real duration | Spinner needed? |
|------|--------------|-----------------|
| `pricing_check` | ~500ms | No — too fast |
| `balance_check` | ~50ms | No — too fast |
| `purchasing` | 5–30s | ✅ YES — spinner + "still working" message after 10s |
| `validating` | ~0ms (fake) | Remove or make real |
| `recording` | ~200ms | No — too fast |
| `complete` | — | Show phone number |

The only step that needs a spinner with a timeout message is `purchasing`. Add a client-side timer: if `purchasing` step has been active for >10s, show "This is taking longer than usual — still working...".

---

## 6. Recommended Implementation Order

| Priority | Fix | File | Effort |
|----------|-----|------|--------|
| 🔴 P0 | Add `check_service_available()` to legacy purchase path | `purchase_endpoints.py` | 5 lines |
| 🔴 P0 | Filter `price=null` services from picker | `services.py` + `verification-flow.js` | Small |
| 🟡 P1 | Stock monitor loop sleep 120s → 90s | `stock_monitor.py` | 1 line |
| 🟡 P1 | `purchasing` step: "still working" message after 10s | `verification-flow.js` | Small |
| 🟢 P2 | Remove fake `validating` step or make it real | `purchase_endpoints.py` + JS | Small |

---

## 7. TV API Signals — Reference

| Signal | Meaning | Our handling |
|--------|---------|-------------|
| `price = null` from services list | Out of stock | ✅ Stock monitor marks unavailable |
| `price = null` from pricing endpoint | Out of stock | ✅ `check_service_available()` returns false |
| `price > 0` from pricing endpoint | Available right now | ✅ Used as gate in SSE path |
| `quantity = 0` | Out of stock | ✅ Stock monitor marks unavailable |
| `quantity = null` | Unknown (TV didn't return it) | ⚠️ Falls back to price signal |
| `verifications.create()` throws `no_inventory` | Sold out between check and purchase | ✅ Caught as ProviderError, surfaced to user |
| `verifications.report(id)` | Failed verification → TV refunds | ✅ Called on timeout |
| `verifications.cancel(id)` | User cancel → TV refunds if can_cancel | ✅ Called on cancel |

---

## 8. Files to Change for P0 Fixes

```
app/api/verification/purchase_endpoints.py   — add check_service_available() to legacy path
app/api/core/services.py                     — filter price=null from stock response
static/js/verification-flow.js               — grey out / hide unavailable services in picker
app/services/stock_monitor.py                — loop sleep 120 → 90
```
