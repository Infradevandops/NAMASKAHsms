# Purchase Flow Fix Walkthrough — v2
**Date**: November 3, 2026
**Status**: Active — ready to implement
**Scope**: Stock display · Purchase flow correctness · Rate limiting · UI/UX

---

## TV Support Response — Critical Insight

TV support said:
> "If you are getting blocked, that usually means you are sending **invalid requests**
> or your requests are **too frequent**."

This reframes the Cloudflare block. It is NOT a permanent IP ban — it is a rate limit
trigger caused by our request pattern. The proxy is working ($43.65 balance confirmed)
but we are still hitting 429s on the pricing endpoint. The root cause is:

- `check_service_available()` calls `verifications.pricing()` on every purchase attempt
- `_fetch_prices_inline()` fires up to 10 concurrent pricing calls during service list load
- `refresh_stock_cache()` was calling `fetch_raw_services_with_quantity()` which hit
  `/api/pub/v2/services` — another endpoint that can trigger rate limits

**Rule going forward**: Only call TV pricing endpoints when absolutely necessary.
Cache aggressively. Never call pricing in a loop at startup.

---

## What TV's Purchase UI Tells Us (from artifacts)

From the TV screenshots:

1. **Service list shows quantity per service** — e.g. "999+ available" for Telegram.
   TV exposes this via the pricing endpoint response, not the services list endpoint.
   The `quantity` field IS returned by `POST /api/pub/v2/pricing/verifications` per service.

2. **Purchase flow is linear and immediate** — select service → click buy → number
   appears. No multi-step confirmation screen. The number is shown with a countdown timer.

3. **No "waiting for code" limbo** — if purchase fails, the UI resets immediately.
   There is no state where the user sees a waiting screen for a failed purchase.

4. **Quantity shown in service list** — each service card shows available count.
   This comes from the per-service pricing call, not a bulk endpoint.

---

## Current State Diagnosis

### Bug 1 — Stock Map Always Empty or All-False

**Chain**:
```
lifespan startup
  → get_services_list()           writes tv:services_list (prices may be null if inline pricing timed out)
  → run_stock_monitor() loop      first run after 90s sleep
      → refresh_stock_cache()
          → fetch_raw_services_with_quantity()   hits /api/pub/v2/services
              → TV returns quantity=0 for ALL services (TV doesn't expose stock counts here)
          → every service: qty=0 → available=False
      → services:stock written with all available=False
  → GET /api/services/stock returns all services as unavailable
  → frontend renders all services greyed out, pointer-events:none
  → user cannot select any service
```

**Why quantity=0**: TV's `/api/pub/v2/services` endpoint does NOT return quantity.
The `fetch_raw_services_with_quantity()` function tries 5 different field names
(`quantity`, `qty`, `availableCount`, `available_count`, `count`) — all return null.
The function logs `"0 with quantity"` every single run. This has never worked.

**Fix**: Remove `fetch_raw_services_with_quantity()` from `refresh_stock_cache()`.
Use price-based availability exclusively: `price > 0` = in stock.
The quantity shown in TV's UI comes from the per-service pricing response — we already
capture this in `_fetch_prices_inline()` via `payload.get("quantity")`. Use that.

---

### Bug 2 — Cancel Button Hidden Too Early

**Current code** (line 861 in verification-flow.js):
```javascript
case 'purchasing':
    updateLoadingMessage('Securing your number...');
    hideCancelButton();   // ← WRONG: hides cancel at the START of purchasing
```

The cancel button is hidden when `purchasing` step STARTS — but the TV call hasn't
completed yet. The user has no cancel option during the 5–30s TV call.

**Correct behaviour**: Cancel button stays visible throughout `purchasing` step.
It should only be hidden AFTER `complete` fires (number acquired, charge committed).
Before `complete`: cancel = abort stream, no charge.
After `complete`: cancel = call cancel API, get refund.

---

### Bug 3 — Purchase Failure Does Not Reset Flow

**Current code** — `failed` case in SSE handler:
```javascript
case 'failed':
    hidePurchaseLoadingState();
    document.getElementById('step-2-card').style.display = 'block';
    // shows toast, returns
```

This correctly resets to step 2. BUT: the `cancelPurchase()` function (called by the
cancel button during loading) does NOT abort the SSE stream reader. The `while(true)`
read loop continues running even after the user clicks cancel, because there's no
`AbortController` on the fetch. The stream keeps reading until the server closes it.

Also: `hideCancelButton()` is called at `purchasing` step start, so the cancel button
disappears exactly when the user most needs it (during the slow TV call).

---

### Bug 4 — "Still Waiting" Notifications for Failed Purchases

From screenshots: "Still Waiting — Waiting for SMS code for tinder..." fires even
when the purchase showed "Failed to create verification".

**Root cause**: The `failed` SSE event fires correctly and the JS returns early —
`startPolling()` is NOT called in the JS on failure. So the frontend is clean.

The issue is **orphan recovery** in `verification-flow.js` (line ~1441):
```javascript
fetch(`/api/verification/status/${orphanId}`, ...)
```
On page load, if `localStorage` has an `active_verification_id`, the flow resumes
polling for it. If a previous failed purchase left a stale ID in localStorage,
the orphan recovery picks it up and starts polling a verification that was never
successfully created (or was created but immediately failed).

Also: `sms_polling_service.start_polling()` is called in `lifespan.py`'s
`resume_pending_verifications()` on startup — this picks up any `pending` status
verifications from the DB, including ones that failed at the TV level but whose
DB record was written before the failure was detected.

---

### Bug 5 — Price Shows $2.63 (Hardcoded Fallback)

The pricing card shows `$2.63` which is the freemium hardcoded fallback.
`updatePricing()` calls `GET /api/verification/price` — if that endpoint returns
an error (because `_get_provider_price()` can't find the service in cache),
it falls back to the local `calculateLocalPrice()` which uses `$2.63`.

The real price from our probe: tinder=$0.50, google=$0.75, etc.
The custom tier markup makes these ~$0.90. The $2.63 is never correct for any tier.

**Fix**: `GET /api/verification/price` must always return a real price.
If the services cache is cold, do a single live pricing call for that service.
This already exists in `_fetch_single_service_price()` — it just needs to be
reliably triggered when cache is cold.

---

### Bug 6 — Rate Limiting From Invalid/Frequent Requests

TV support confirmed: blocks come from invalid requests or too-frequent calls.

**Sources of excessive TV API calls in our codebase**:
1. `check_service_available()` — called on every purchase attempt (1 call, acceptable)
2. `_fetch_prices_inline()` — 10 concurrent calls on service list load (429 risk)
3. `fetch_raw_services_with_quantity()` — called every 90s by stock monitor (wasteful,
   hits an endpoint that returns no useful data)
4. `_fetch_and_cache_pricing()` — background task firing 10 concurrent calls

**TV rate limit**: Per their docs, rate limits apply per endpoint per time window.
Sending 10 concurrent pricing calls every time the service list is requested is
the likely trigger. The proxy routes all calls through one IP — so all 10 concurrent
calls look like a burst from one IP.

**Fix**:
- Reduce `_fetch_prices_inline()` semaphore from 10 → 3 concurrent calls
- Add 200ms delay between pricing calls in the inline fetch
- Remove `fetch_raw_services_with_quantity()` entirely from stock monitor
- Cache service prices for 24h — never re-fetch unless cache is explicitly evicted
- Add `Retry-After` header handling: if TV returns 429, back off for the specified
  duration before retrying

---

## Implementation Plan

### Phase 1 — Fix Stock Map (P0, ~30 min)

**File**: `app/services/stock_monitor.py`

Changes:
- `refresh_stock_cache()`: remove `fetch_raw_services_with_quantity()` call entirely.
  Fall straight to `build_stock_map()`.
- `build_stock_map()`: `available = price is not None and float(price) > 0`.
  Also read `quantity` from the cached service entry if present (populated by
  `_fetch_prices_inline()`).

**File**: `app/core/lifespan.py`

Changes:
- After `get_services_list()` completes at startup, immediately call
  `refresh_stock_cache()` to warm `services:stock` before the first request hits.
  No more 90s cold window.

---

### Phase 2 — Fix Rate Limiting (P0, ~20 min)

**File**: `app/services/textverified_service.py`

Changes:
- `_fetch_prices_inline()`: reduce semaphore 10 → 3. Add `await asyncio.sleep(0.2)`
  between each call to spread the burst.
- `check_service_available()`: already has 429 handling (returns `available=True`).
  Add `Retry-After` header read: if TV sends `Retry-After: N`, cache a backoff key
  in Redis and skip pricing calls for that service for N seconds.
- Remove `fetch_raw_services_with_quantity()` from being called anywhere except
  explicit admin debug endpoints.

---

### Phase 3 — Fix Cancel Button Timing (P0, ~20 min)

**File**: `static/js/verification-flow.js`

Changes:
- Add `AbortController` to the SSE fetch so `cancelPurchase()` can actually abort it:
  ```javascript
  const abortCtrl = new AbortController();
  VerificationFlow._streamAbort = abortCtrl;
  const response = await fetch('/api/verification/request/stream', {
      signal: abortCtrl.signal, ...
  });
  ```
- `cancelPurchase()`: call `VerificationFlow._streamAbort?.abort()` before resetting UI.
- Remove `hideCancelButton()` from `purchasing` case. Cancel button stays visible
  through the entire loading sequence.
- Only hide cancel button on `complete` (charge committed, number in hand).
- On `complete`: swap cancel button text to "Cancel & Refund" and wire to `confirmCancel()`.

---

### Phase 4 — Fix Orphan Recovery (P1, ~20 min)

**File**: `static/js/verification-flow.js`

Changes:
- On `failed` SSE event: `localStorage.removeItem('active_verification_id')`.
  Prevents orphan recovery from picking up a failed purchase on next page load.
- In orphan recovery: before resuming polling, call
  `GET /api/verification/status/{id}` — only resume if status is `pending`.
  If status is `failed`/`error`/`cancelled`/`timeout`, clear localStorage and skip.

**File**: `app/services/sms_polling_service.py`

Changes:
- `resume_pending_verifications()`: add check — if `verification.activation_id` is
  null or empty, mark as `failed` immediately instead of starting polling.
  A verification with no `activation_id` means the TV purchase never completed.

---

### Phase 5 — Fix Price Display (P1, ~15 min)

**File**: `static/js/verification-flow.js`

Changes:
- `updatePricing()`: on fetch error, do NOT fall back to `$2.63`. Show "Calculating..."
  and retry once after 2s. If still failing, show "Price unavailable — proceed to confirm".
- The real price is always shown on the `complete` SSE event (`cost` field) — ensure
  the pricing card updates from this value after purchase.

---

### Phase 6 — Show Quantity in Service List (P2, ~30 min)

TV's pricing endpoint returns `quantity` per service. Our `_fetch_prices_inline()`
already captures it. It's stored in `tv:services_list` and `services:stock`.

**File**: `static/js/verification-flow.js`

Changes in `renderImmersiveItem()`:
- `qty` is already read: `const qty = stockInfo.quantity ?? item.quantity ?? null`
- `qtyLabel` is already computed but only shows when `available=true`
- Fix: show quantity label regardless of the `available` flag if qty > 0.
  Format: `"999+ available"` if qty >= 999, else `"${qty} available"`.
- If qty is null (not returned by TV for this service): show "In stock" when
  `available=true`, nothing when `available=false`.

---

## Correct Purchase Flow (Target State)

```
User selects service
  ↓
[UI] Show pricing card with real tier-adjusted price
  ↓
User clicks "Get Number"
  ↓
[UI] Hide step-2, show purchase-loading-card
     Cancel button visible: "Cancel (you will not be charged)"
     Message: "Confirming availability..."
  ↓
SSE: pricing_check → "Confirming availability..."   [cancel = abort stream, no charge]
SSE: balance_check → "Checking your balance..."     [cancel = abort stream, no charge]
SSE: purchasing    → "Securing your number..."      [cancel = abort stream, no charge]
     (TV call blocks 5–30s here)
     If TV fails → SSE: failed → reset to step-2, clear localStorage, no polling
  ↓
SSE: validating    → "Validating number..."         [cancel = abort stream, no charge]
SSE: recording     → "Almost done..."               [cancel = abort stream, no charge]
  ↓
SSE: complete      → show phone number, start polling
     Cancel button changes to "Cancel & Refund"     [cancel = call cancel API, get refund]
     localStorage.setItem('active_verification_id', id)
  ↓
Polling runs every 3s
  → status=completed + sms_code → show code, clear localStorage, stop polling
  → status=failed/timeout/cancelled → show error, clear localStorage, stop polling
  → still pending → update timer, continue polling
```

**Debit point**: Only after `recording` step succeeds (DB write + `deduct_credits_for_verification()`).
TV is charged at `purchasing` step. If DB write fails after TV purchase, TV number is
cancelled via the rollback handler in `purchase_endpoints.py`.

---

## Files to Modify

| File | Changes | Phase |
|------|---------|-------|
| `app/services/stock_monitor.py` | Remove fetch_raw, price-based availability | 1 |
| `app/core/lifespan.py` | Warm services:stock at startup | 1 |
| `app/services/textverified_service.py` | Semaphore 10→3, 429 backoff, remove fetch_raw | 2 |
| `static/js/verification-flow.js` | AbortController, cancel timing, orphan fix, qty display | 3,4,5,6 |
| `app/services/sms_polling_service.py` | Skip polling if no activation_id | 4 |

---

## Verification Checklist

- [x] Service list loads — all services selectable (unpriced = unknown, not greyed out)
- [x] Out-of-stock services only greyed out after confirmed purchase failure
- [x] Cancel button visible throughout entire purchase loading sequence
- [x] Cancel before `complete`: stream aborted, no charge, UI resets to step-2
- [x] Cancel after `complete`: cancel API called, refund shown, UI resets
- [x] Purchase failure: UI resets to step-2, localStorage cleared, polling NOT started
- [x] Verifications with no activation_id marked failed immediately (no phantom polling)
- [x] `build_stock_map()` only checks outcomes for priced services (~82, not 2351)
- [x] Background pricing runs popular services first (tinder, google, whatsapp etc.)
- [x] TV pricing calls capped at semaphore=3
- [ ] Price shown matches tier-adjusted price (not $2.63) — pending verification
- [ ] Popular services show green dots after background pricing completes (~60s post-startup)
