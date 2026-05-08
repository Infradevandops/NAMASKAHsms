# Namaskah Task List
> All issues below have been **verified** against the actual codebase.

---

## 🔴 CRITICAL — Broken Functionality

### T-01 · Settings: Missing `/api/` prefix on 3 endpoints
**Verified:** `settings.html` lines 2140, 2150, 2160
These calls will 404 — the backend routes live at `/api/user/*` but the frontend calls `/user/*`.
- `fetch('/user/change-password', ...)` → should be `/api/user/change-password`
- `fetch('/user/logout-all', ...)` → should be `/api/user/logout-all`
- `fetch('/user/delete-account', ...)` → should be `/api/user/delete-account`

---

### T-02 · Settings: Forwarding router is commented out
**Verified:** `app/api/core/router.py` line 52
```python
# router.include_router(forwarding_router, prefix="/api")
```
The entire SMS Forwarding tab in Settings calls `/forwarding/*` endpoints that are never registered. Every save/test/load call silently fails.

---

### T-03 · History: Broken script tag structure
**Verified:** `history.html` — 2 opening `<script>` tags (lines 53, 237) but only 1 closing `</script>` (line 508).
The second `<script>` at line 237 is opened inside the `{% block content %}` block without a matching close before `{% block scripts %}`. This causes the audit modal HTML to be treated as JavaScript.

---

### T-04 · Settings: Notifications tab JS references IDs that don't exist in its HTML
**Verified:** `settings.html` lines 2011, 2012, 2020, 2031
`loadNotificationsTab()` tries to set `notif-unread-count`, `notif-count-all`, `notif-list` etc. — none of these IDs exist in the `notifications-tab` div (lines 258–277). The tab only has 2 toggle switches. All JS calls throw silent errors.

---

### T-05 · Profile: `/profile` route does not exist
**Verified:** Searched all `.py` files — `profile.html` template exists but no route serves it. Navigating to `/profile` returns 404. The sidebar has no link to it either (double-confirmed: no mention of "profile" in `sidebar.html`).

---

### T-06 · Profile: Avatar upload endpoint does not exist
**Verified:** Searched all `.py` files — no route for `/api/user/avatar`. The upload silently fails with a console log: `"Avatar upload endpoint not available"`. The preview works locally but nothing is persisted.

---

## 🟠 HIGH — Missing Navigation / Dead Links

### T-07 · Sidebar: No link to Profile page
**Verified:** `sidebar.html` — zero mentions of "profile" or `/profile`. Users have no way to navigate to their profile from the dashboard.

---

### T-08 · Sidebar: No link to Notifications page
**Verified:** `sidebar.html` — no link to `/notifications`. The route exists (`main_routes.py` line 209) and the template exists, but it's unreachable from the sidebar.

---

### T-09 · Landing & Footer: `/docs` link works but is FastAPI's auto-generated Swagger UI
**Verified:** `main_routes.py` line 101 — `/docs` serves `api_docs.html`. Route exists. However, the landing nav links to `/docs` expecting a user-facing API documentation page. Confirmed it renders `api_docs.html` not Swagger — this is fine but worth noting the page should be polished.

---

### T-10 · Landing footer: Internal GitHub repo URL exposed
**Verified:** `landing.html` line 413
```
https://github.com/Infradevandops/NAMASKAHsms
```
This exposes the internal repo name and org. Should be replaced with the public-facing URL or removed.

---

### T-11 · Landing: No cookie consent banner
**Verified:** `landing.html` is a standalone file (does not extend `base.html`). The cookie consent banner lives in `base.html` (lines 96–117) but `landing.html` never includes it. All other pages that extend `base.html` get it automatically.

---

## 🟡 MEDIUM — Incorrect Behaviour

### T-12 · Register: No confirm password field
**Verified:** `register.html` — only one `<input type="password">` field. Users can mistype their password with no feedback.

---

### T-13 · Register: Password strength meter has 3 segments but 4 scoring criteria
**Verified:** `register.html` lines 176–178 (3 segments) vs lines 219–223 (4 checks: length, uppercase, number, special char). Score of 4 triggers `.strong` which fills all 3 segments — the 4th criterion has no visual representation.

---

### T-14 · Register: Uses `alert()` on success instead of toast
**Verified:** `register.html` line 273
```js
alert("Account created successfully! Please log in.");
```
Inconsistent with the rest of the app which uses `window.errorHandler.showToast()`.

---

### T-15 · Profile: Uses `alert()` instead of toast (5 instances)
**Verified:** `profile.html` lines 401, 407, 481, 483, 487
All profile save/validation feedback uses `alert()` instead of the toast system.

---

### T-16 · Settings: Uses `alert()` instead of toast (8+ instances)
**Verified:** `settings.html` lines 1482, 1517, 1631, 1635, 1647, 1650, 1654, 1674, 1677, 1681
Forwarding config, refund modal, blacklist modal all use `alert()`.

---

### T-17 · Verify: `#scanning-service-name` element is never populated
**Verified:** `verify_modern.html` line 225 — the element exists in the DOM but no JavaScript ever sets its `textContent`. The scanning screen shows a blank service name while waiting for SMS.

---

### T-18 · Verify: Step 1 "Back" button calls `history.back()`
**Verified:** `verify_modern.html` line 149
```html
<button onclick="history.back()">Back</button>
```
On Step 1 there is nothing to go back to within the app — this navigates the user away from the site entirely if they came from an external link.

---

### T-19 · History: No pagination — flat load of 100 records
**Verified:** `history.html` line 83
```js
fetch('/api/verify/history?limit=100', ...)
```
No pagination controls exist in the template. Users with more than 100 verifications silently lose older records.

---

### T-20 · History: No service name filter
**Verified:** `history.html` — only `filter-status` (select) and `filter-date` (date input) exist. No way to filter by service (e.g. show only WhatsApp verifications).

---

### T-21 · History: `reuseVerification()` function defined but never called
**Verified:** `history.html` line 478 — function exists in JS but no button in the HTML calls it. Users cannot re-run a previous verification from history.

---

### T-22 · Settings API Docs tab: Hardcoded wrong base URL
**Verified:** `settings.html` line 625
```html
<code>https://namaskah.app/api</code>
```
Production URL is `https://vrenum.onrender.com`. This shows the wrong base URL to developers using the API docs tab.

---

### T-23 · Analytics: Empty chart sections render even with no data
**Verified:** `analytics.html` — "Carrier Match Rate" and "Outcome Categories" chart containers always render with placeholder text `"No carrier data yet"` / `"No outcome data yet"` even for new users. Makes the page look broken on first visit.

---

### T-24 · Analytics: Date range picker and chart range buttons don't sync
**Verified:** `analytics.html` — the date picker (from/to inputs) and the 7/30/90 day buttons are independent controls. Clicking "7 Days" only re-renders the verifications chart using a slice of already-loaded data; it does not re-fetch with a new date range. The date picker and buttons can show contradictory ranges simultaneously.

---

### T-25 · Landing: Hardcoded "10,000+ verifications" stat
**Verified:** `landing.html` line 108 — static copy, not pulled from any API. Should either be real data or removed to avoid misleading users.

---

## 🟢 LOW — Polish / Cleanup

### T-26 · API Keys page: Standalone dark-themed page, no sidebar/navbar
**Verified:** `api_keys.html` — does not extend `dashboard_base.html`. Has its own `<html>`, `<head>`, dark CSS variables. Completely inconsistent with the rest of the dashboard. Users are stranded with no navigation.

---

### T-27 · Pricing page: Comparison table missing rows
**Verified:** `pricing.html` — table only has Price, API Access, Location Filters, Support. Missing: ISP Filters, Affiliate Program, Monthly Quota — all listed in the README tier comparison.

---

### T-28 · Pricing page: No mention of auto-refund guarantee
**Verified:** `pricing.html` — the auto-refund guarantee is a key selling point (on landing page) but absent from the pricing page where purchase decisions are made.

---

### T-29 · Pricing page: Only 3 FAQ items
**Verified:** `pricing.html` — 3 questions total. Very thin for a pricing page. Missing: "What happens to unused quota?", "Can I get a refund?", "How does the auto-refund work?", "What payment methods are accepted?".

---

### T-30 · Register: No display name / username field
**Verified:** `register.html` — only email and password collected at signup. Profile page has a display name field but it defaults to the email prefix. Users have no opportunity to set a name at registration.

---

### T-31 · Login: Google button styled inconsistently vs Register page
**Verified:** `login.html` — Google button is a full-width button with inline SVG. `register.html` — Google button uses a different layout with flex + gap. Both work but look different.

---

### T-32 · Dashboard: No notification bell/badge in navbar
**Verified:** `dashboard.html` and `dashboard_base.html` — no notification indicator in the top bar. Notifications page and route exist but users have no visual cue of unread notifications.

---

### T-33 · Dashboard: Recent activity table has no "View All" link
**Verified:** `dashboard.html` — the activity table shows 10 items with pagination but no direct link to `/history` from the card header.

---

### T-34 · Verify: No "New Verification" shortcut after code received
**Verified:** `verify_modern.html` — after SMS code is received, the only option is "Back to Service Selection" (a small secondary button). No prominent CTA to start a new verification immediately.

---

### T-35 · Verify: Step 2 delivery time is hardcoded
**Verified:** `verify_modern.html` — `<span class="pricing-value" id="pricing-time">~30s</span>` is never updated dynamically. All services show `~30s` regardless of actual expected delivery time.

---

## Summary

| Priority | Count |
|----------|-------|
| 🔴 Critical | 6 |
| 🟠 High | 5 |
| 🟡 Medium | 14 |
| 🟢 Low | 10 |
| **Total** | **35** |
