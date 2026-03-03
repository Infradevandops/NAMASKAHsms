# Sidebar Pages Full Audit

> Settings fixes are complete locally — pending `git push` → Render redeploy (screenshot confirms alert() still live on prod).
> Privacy page intentionally uses a local lock icon (🔒) — no external icon CDN needed there.

---

## 1. Settings — ✅ Fixed (Pending Deploy)

**Tabs:** Account · Security · Notifications · Billing · API Keys · SMS Forwarding · Blacklist

All 6 bugs fixed. See `SETTINGS_FIX_TASKS.md`.

---

## 2. Dashboard — 🔴 Broken (3 bugs)

**File:** `templates/dashboard.html`  
**JS:** `dashboard-ultra-stable.js` + inline module script

| # | Tab/Section | Issue | Detail |
|---|---|---|---|
| 1 | Recent Activity | `ENDPOINTS.DASHBOARD.ACTIVITY` = `/api/dashboard/activity/recent` → 404 | Route in `dashboard_router.py` is `GET /api/dashboard/activity` (no `/recent` suffix) |
| 2 | Notifications (sidebar badge) | `GET /api/notifications` returns `{ notifications: [...], total }` but sidebar reads `data.unread_count` | `dashboard_router.py` `/notifications` returns no `unread_count` field — badge always stays hidden |
| 3 | Tier card | `GET /api/tiers/current` returns `{ tier, name, features }` but `dashboard-ultra-stable.js` likely reads `data.current_tier` | `compatibility_routes.py` alias returns `current_tier` ✅ but `dashboard_router.py` duplicate returns `tier` — whichever responds first determines if it works |

**Fix:**
- Bug 1: Change `ENDPOINTS.DASHBOARD.ACTIVITY` in `constants.js` from `/api/dashboard/activity/recent` → `/api/dashboard/activity`
- Bug 2: Add `unread_count` to `dashboard_router.py` `/notifications` response
- Bug 3: Standardise — `dashboard_router.py` `/tiers/current` should return `current_tier` not `tier`

---

## 3. SMS Verification — 🔴 Broken (5 bugs)

**File:** `templates/verify_modern.html`  
**Tabs/Steps:** Select Service → Pricing & Confirmation → Waiting for SMS

| # | Step | Issue | Detail |
|---|---|---|---|
| 1 | Step 3 — Create | `POST /api/v1/verify/create` → 404 | v1 router doesn't include verification routes. Working path: `POST /api/verify/create` |
| 2 | Step 3 — Polling | No SMS polling at all | `startScanning()` only counts seconds — never calls `GET /api/verify/status/{id}`. Code is never displayed |
| 3 | Step 1 — Services | Hardcoded 8 services | `updateServices()` ignores `GET /api/services` which exists in `dashboard_router.py` and returns real data |
| 4 | Step 1 — Countries | Hardcoded 4 countries in `<select>` | `GET /api/countries` exists in `dashboard_router.py` — not used |
| 5 | Step 3 — Cancel | `confirm()` blocking dialog | `cancelVerification()` uses native `confirm()` |

**Fix:**
- Bug 1: `/api/v1/verify/create` → `/api/verify/create`
- Bug 2: Add `setInterval` in `startScanning()` calling `GET /api/verify/status/${verificationId}` every 3s; on `status === 'completed'` show code and clear interval
- Bug 3: Replace hardcoded grid with `fetch('/api/services')` on `DOMContentLoaded`
- Bug 4: Replace hardcoded `<select>` options with `fetch('/api/countries')` on load
- Bug 5: Replace `confirm()` with a visible "Confirm Cancel" button state

---

## 4. Wallet — 🔴 Broken (6 bugs)

**File:** `templates/wallet.html`  
**Sections:** Balance · Add Credits (Card + Crypto) · Credit History · Transaction History

| # | Section | Issue | Detail |
|---|---|---|---|
| 1 | Add Credits — Card | `POST /api/billing/initialize-payment` → 404 | Actual path: `POST /api/wallet/paystack/initialize` |
| 2 | Add Credits — Card | `GET /api/billing/payment-status/{ref}` → 404 | No such route exists anywhere |
| 3 | Credit History | `GET /api/user/credits/history` → 404 | `ENDPOINTS.USER.CREDITS_HISTORY` = `/api/user/credits/history` — no such route. Actual: `GET /api/wallet/history` |
| 4 | Add Credits — Crypto | `GET /api/billing/crypto-addresses` → 404 | No such route exists |
| 5 | Add Credits — Crypto | `alert()` in `confirmCryptoPayment()` | Blocking dialog |
| 6 | Add Credits — Card | `alert()` in `addCustomCredits()` | Blocking dialog |

**Fix:**
- Bug 1: Change to `/api/wallet/paystack/initialize`
- Bug 2: Add `GET /billing/payment-status/{reference}` alias in `compatibility_routes.py` → proxy to `GET /api/wallet/paystack/verify?reference={reference}`
- Bug 3: Change to `/api/wallet/history` (or add alias `GET /user/credits/history` in `compatibility_routes.py`)
- Bug 4: Add stub `GET /billing/crypto-addresses` in `compatibility_routes.py` returning addresses from env vars
- Bugs 5–6: Replace `alert()` with inline toast or button feedback

---

## 5. History — 🟡 Minor (2 bugs)

**File:** `templates/history.html`  
**Sections:** Filter bar · Verification table · Export

| # | Section | Issue | Detail |
|---|---|---|---|
| 1 | Table render | `item.service_name` used but `dashboard_router.py` `/verify/history` returns `service` not `service_name` | Field name mismatch — column shows blank |
| 2 | Detail popup | `alert()` in `viewDetails()` | Blocking dialog for SMS message display |

**Fix:**
- Bug 1: `dashboard_router.py` `/verify/history` — add `service_name` field (alias `service`) to response, or fix `renderHistory()` to read `item.service || item.service_name`
- Bug 2: Replace `alert()` with an inline expandable row or small modal

---

## 6. Analytics — 🟡 Minor (2 bugs)

**File:** `templates/analytics.html`  
**Sections:** Date range · Stats grid · 3 charts · Top services table

| # | Section | Issue | Detail |
|---|---|---|---|
| 1 | All charts | `daily_verifications`, `spending_by_service`, `top_services` fields missing | `dashboard_router.py` `/analytics/summary` returns stub zeros with none of these fields — charts render empty state every time |
| 2 | Export | `alert()` in `exportData()` | Blocking dialog when no data |

**Fix:**
- Bug 1: Extend `dashboard_router.py` `/analytics/summary` to query and return `daily_verifications`, `spending_by_service`, `top_services` from the Verification + Transaction models
- Bug 2: Replace `alert()` with inline disabled-button state

---

## 7. Notifications — 🟡 Minor (2 bugs)

**File:** `templates/notifications.html`  
**Sections:** Filter tabs (All/Unread/System/Payment/Verification) · Notification list · Mark all read

| # | Section | Issue | Detail |
|---|---|---|---|
| 1 | Notification list | `n.is_read` used in template but `dashboard_router.py` `/notifications` returns `read` not `is_read` | Unread styling never applies; "✓ Read" button never shows |
| 2 | Mark all read | `POST /api/notifications/mark-all-read` — `dashboard_router.py` has no such route | `core/notification_endpoints.py` has it at `/api/notifications/mark-all-read` ✅ — but `dashboard_router.py` also registers `GET /api/notifications` which may shadow the notification router. Route conflict risk |

**Fix:**
- Bug 1: Fix `dashboard_router.py` `/notifications` to return `is_read` instead of `read` (matches model's `is_read` column)
- Bug 2: Remove duplicate `GET /api/notifications` from `dashboard_router.py` — let `core/notification_endpoints.py` own all `/api/notifications/*` routes

---

## 8. Pricing — 🟡 Minor (2 bugs)

**File:** `templates/pricing.html`  
**Sections:** 4 tier cards · Feature comparison table · FAQ

| # | Section | Issue | Detail |
|---|---|---|---|
| 1 | Tier cards | `selectTier('payg')` redirects to `/dashboard?view=billing` | Query param `?view=billing` is not handled anywhere in dashboard JS |
| 2 | Tier cards | `selectTier('pro'/'custom')` redirects to `/dashboard?view=settings&upgrade=tier` | Same — unhandled query params, user lands on plain dashboard with no upgrade flow triggered |

**Fix:**
- Both bugs: Change redirect targets to `/settings?tab=billing` (already exists and works) instead of unhandled dashboard query params

---

## 9. Privacy (GDPR) — 🔴 Broken (5 bugs)

**File:** `templates/gdpr_settings.html`  
**Sections:** Data Export · Privacy Preferences · Activity Log · Delete Account  
**Note:** Uses local emoji icons only (🔒, 📥, 📋, 🗑️) — no external icon CDN, intentional ✅

| # | Section | Issue | Detail |
|---|---|---|---|
| 1 | Data Export | `GET /gdpr/export` → 404 | `gdpr.py` router (prefix `/gdpr`) is never mounted in `main.py` |
| 2 | Delete Account | `DELETE /gdpr/account` → 404 | Same — router not mounted |
| 3 | Activity Log | `GET /api/user/activity` → 404 | No such route exists anywhere |
| 4 | Privacy Preferences | `PUT /api/user/settings` sends `analytics_consent`, `marketing_consent` | `UserSettingsUpdate` model only accepts `email_notifications` + `sms_alerts` — extra fields silently dropped |
| 5 | Export + Delete | `alert()` in `exportData()` and `deleteAccount()` | Blocking dialogs |

**Fix:**
- Bugs 1–2: Add to `main.py`: `from app.api.core.gdpr import router as gdpr_router` then `fastapi_app.include_router(gdpr_router)`
- Bug 3: Add `GET /user/activity` stub in `compatibility_routes.py` returning `{ activities: [] }`
- Bug 4: Add `analytics_consent: bool = False` and `marketing_consent: bool = False` to `UserSettingsUpdate` in `compatibility_routes.py`
- Bug 5: Replace `alert()` with inline status text on the export button and delete button (same pattern as Settings Security tab fix)

---

## 10. Logout — ✅ Clean

**Sidebar footer:** `templates/components/sidebar.html`

- `POST /api/auth/logout` → exists ✅
- Clears localStorage, redirects to `/` ✅
- `confirm()` — acceptable for destructive action

---

## Master Summary

| # | Page | Status | Bug Count | Priority |
|---|---|---|---|---|
| 1 | Settings | ✅ Deploy pending | 0 | Deploy now |
| 2 | Dashboard | 🔴 Broken | 3 | High |
| 3 | SMS Verification | 🔴 Broken | 5 | High |
| 4 | Wallet | 🔴 Broken | 6 | High |
| 5 | History | 🟡 Minor | 2 | Medium |
| 6 | Analytics | 🟡 Minor | 2 | Medium |
| 7 | Notifications | 🟡 Minor | 2 | Medium |
| 8 | Pricing | 🟡 Minor | 2 | Low |
| 9 | Privacy (GDPR) | 🔴 Broken | 5 | High |
| 10 | Logout | ✅ Clean | 0 | — |

**Total bugs: 27**  
**Broken pages: 4** (Dashboard, SMS Verification, Wallet, Privacy)  
**Fix order:** Deploy Settings → SMS Verification → Wallet → Privacy/GDPR → Dashboard → History/Analytics/Notifications → Pricing
