# Dashboard Fix Tasks

**File:** `templates/dashboard.html`  
**JS:** `static/js/dashboard-ultra-stable.js` + inline `<script type="module">` in dashboard.html  
**Status:** 🔴 3 bugs confirmed

---

## Bug 1 — Recent Activity table always empty

**Root cause:** `constants.js` `ENDPOINTS.DASHBOARD.ACTIVITY` = `/api/dashboard/activity`  
but `dashboard_activity.py` registers the route as `GET /api/dashboard/activity/recent` (with `/recent` suffix).  
The inline module script calls `ENDPOINTS.DASHBOARD.ACTIVITY` → hits `dashboard_router.py`'s stub which returns `{ activities: [], total: 0 }` → table stays empty.

**Fix:** `app/api/core/dashboard_activity.py` — change route from `/activity/recent` → `/activity`  
(The stub in `dashboard_router.py` at `/api/dashboard/activity` can then be removed to avoid the duplicate.)

**Files to change:**
- `app/api/core/dashboard_activity.py` line 17: `@router.get("/activity/recent")` → `@router.get("/activity")`
- `app/api/dashboard_router.py`: remove the `/dashboard/activity` stub (lines ~155–165) to eliminate the duplicate that shadows the real implementation

---

## Bug 2 — Notification bell badge never shows unread count

**Root cause:** `notification-system.js` (loaded in `dashboard_base.html`) reads `data.unread_count` from `GET /api/notifications`.  
`dashboard_router.py` `/notifications` already returns `unread_count` ✅ — but `notification_router` (from `core/notification_endpoints.py`) is mounted **before** `dashboard_router` in `main.py`, so whichever `/api/notifications` route fires first wins.

**Actual issue:** The `notification-system.js` badge update path needs confirming. Check `static/js/notification-system.js` — if it calls `/api/notifications/unread-count` instead of `/api/notifications`, the badge works via `dashboard_router.py`'s `/notifications/unread-count` endpoint which returns `{ unread_count }` ✅.

**Fix:** Verify `notification-system.js` uses `/api/notifications/unread-count`. If it uses `/api/notifications`, ensure `dashboard_router.py`'s handler responds first (it already returns `unread_count`). No code change needed if unread-count endpoint is used — just confirm.

**Files to check:**
- `static/js/notification-system.js` — find which endpoint it polls for the badge count

---

## Bug 3 — "Add Credits" button goes to `/pricing` instead of `/wallet`

**Root cause:** `dashboard-ultra-stable.js` line ~300:
```js
addCreditsBtn.onclick = () => { window.location.href = CONFIG.ENDPOINTS.PRICING; }
// CONFIG.ENDPOINTS.PRICING = '/pricing'
```
The screenshot shows the button labelled "Add Credits" — users expect to land on the wallet/payment page, not the pricing/tier page.

**Fix:** `static/js/dashboard-ultra-stable.js` — change `Add Credits` button href from `/pricing` → `/wallet`

```js
// Before
addCreditsBtn.onclick = function(e) {
    e.preventDefault();
    window.location.href = CONFIG.ENDPOINTS.PRICING;
};

// After
addCreditsBtn.onclick = function(e) {
    e.preventDefault();
    window.location.href = '/wallet';
};
```

**Files to change:**
- `static/js/dashboard-ultra-stable.js` ~line 300

---

## Bug 4 — Upgrade button redirects to `/pricing` page (no in-context flow)

**Root cause:** `dashboard-ultra-stable.js` wires Upgrade → `window.location.href = '/pricing'`. The pricing page's `selectTier()` then redirects back to `/dashboard?view=billing` which is an unhandled query param — user lands on a plain dashboard with nothing triggered.

**Expected:** Upgrade button opens a standalone modal directly on the dashboard with a complete self-contained upgrade flow:

```
Step 1 — Plan picker
  Cards: PAYG | Pro ($25/mo) | Custom ($35/mo)
  Current plan greyed out / marked active

Step 2a — PAYG (free tier change)
  Confirm screen → POST /api/billing/tiers/upgrade?target_tier=payg
  → success toast + tier card refresh (no payment needed)

Step 2b — Pro / Custom (paid)
  Confirm + "Pay $X/mo" CTA
  → POST /api/wallet/paystack/initialize { amount_usd: 25|35 }
  → redirect to Paystack authorization_url
  → webhook credits user; tier set post-payment
```

**Backend gap:** `tier_endpoints.py` `POST /upgrade` returns `status: "pending_payment"` but never writes `user.subscription_tier` to DB for PAYG (free) upgrades. Needs a one-line fix to commit the tier change when no payment is required.

**Files to change:**
- `static/js/dashboard-ultra-stable.js` — change Upgrade `onclick` from redirect → `openUpgradeModal()`
- `static/js/dashboard-ultra-stable.js` — add `openUpgradeModal()` with 3-step flow (plan picker → confirm → payment/done)
- `app/api/billing/tier_endpoints.py` `POST /upgrade` — for free tiers (PAYG), set `user.subscription_tier = target_tier` and `db.commit()` before returning

---

## Bug 5 — New Verification modal is SMS-only, no voice option

### Current state (audited)

The dashboard's New Verification button opens an inline modal in `dashboard-ultra-stable.js` with:
- Service select (fetches `/api/services` ✅)
- Country select (hardcoded US only)
- `POST /api/verify/create` with `{ service, country }` — no `capability` field
- Polls `/api/verify/{id}/sms` every 5s for the code

Two full verification pages already exist:
- `templates/verify_modern.html` — SMS flow, 3-step, fully wired, polls `/api/verify/status/{id}` ✅
- `templates/voice_verify_modern.html` — Voice flow, 3-step, but calls `POST /api/v1/verify/create` with `capability: 'voice'` → **404** (v1 router includes verification but the route is `/verify/create` not `/api/v1/verify/create` with voice support)

The `VerificationCreate` schema already has `capability: str = Field(default="sms")` ✅  
The `VoicePollingService` background service polls `Verification` records where `capability == "voice"` ✅  
But `verification_routes.py` `POST /verify/create` never passes `capability` to the DB record or to TextVerified — it always purchases an SMS number.

### Expected behaviour

New Verification button → opens a modal with:

```
Step 0 — Verification type picker (NEW)
  [📱 SMS Verification]   [☎️ Voice Verification]
  Fast · ~30s             Via phone call · 2-5 min
  $2.50                   $3.50

  → selecting either advances to the existing 3-step flow
    (service select → pricing confirm → waiting/polling)
    with the correct capability passed through
```

The existing `verify_modern.html` and `voice_verify_modern.html` pages are the reference implementation — the modal should replicate their flows inline rather than navigating away.

### Gaps to fix

| # | Gap | Fix |
|---|---|---|
| 1 | Modal has no type picker (SMS vs Voice) | Add Step 0 to the modal in `dashboard-ultra-stable.js` |
| 2 | `POST /api/verify/create` ignores `capability` field | `verification_routes.py` — pass `capability` to `Verification` model and to `tv_service.purchase_number()` |
| 3 | Voice page calls `POST /api/v1/verify/create` → 404 | `voice_verify_modern.html` — change to `POST /api/verify/create` |
| 4 | Voice page services are hardcoded (not fetched from API) | `voice_verify_modern.html` `updateServices()` — replace hardcoded list with `fetch('/api/services')` (same fix as SMS page already has) |
| 5 | Voice page `cancelVerification()` uses `confirm()` blocking dialog | Replace with confirm-button pattern (already done on SMS page) |

**Files to change:**
- `static/js/dashboard-ultra-stable.js` — add Step 0 type picker to modal; pass `capability` in create payload; branch polling: SMS polls `/api/verify/{id}/sms`, Voice polls `/api/verify/status/{id}` for `sms_code`
- `app/api/verification/verification_routes.py` — accept and store `capability`; pass to TextVerified purchase call
- `templates/voice_verify_modern.html` — fix endpoint URL + fetch services from API + replace `confirm()` dialog

---

## Button Status Summary

| Button | Current Behaviour | Expected | Status |
|---|---|---|---|
| 📱 New Verification | Opens SMS-only modal | Opens modal with SMS/Voice picker → full flow | 🔴 Incomplete |
| Add Credits | Redirects to `/pricing` | Redirects to `/wallet` | 🔴 Wrong destination |
| View Usage | Redirects to `/analytics` | Redirects to `/analytics` | ✅ Working |
| Upgrade | Redirects to `/pricing` (broken return flow) | Opens upgrade modal in-context | 🔴 Broken flow |

---

## Data Widget Status Summary

| Widget | Endpoint Called | Issue | Status |
|---|---|---|---|
| Total SMS / Successful / Total Spent / Success Rate | `GET /api/analytics/summary` | Returns real data ✅ | ✅ Working |
| Recent Activity table | `GET /api/dashboard/activity` | Hits stub (returns `[]`) instead of real `/activity/recent` handler | 🔴 Always empty |
| Notification bell badge | `GET /api/notifications/unread-count` | Needs verification | 🟡 Unconfirmed |

---

## Fix Order (priority)

1. **Bug 1** — Fix activity route (highest impact, table is visibly broken)
2. **Bug 3** — Fix Add Credits destination (UX confusion)
3. **Bug 5** — New Verification modal: add type picker + voice support (core feature gap)
4. **Bug 4** — Upgrade modal (replaces broken redirect flow)
5. **Bug 2** — Confirm/fix notification badge (minor, may already work)
