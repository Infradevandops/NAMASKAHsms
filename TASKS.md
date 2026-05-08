# Namaskah Task List
> Status as of v4.6.0 — May 7, 2026

All 35 tasks verified against actual codebase.

---

## Status Summary

| Priority | Total | Done | Open |
|----------|-------|------|------|
| 🔴 Critical | 6 | 6 | 0 |
| 🟠 High | 5 | 5 | 0 |
| 🟡 Medium | 14 | 14 | 0 |
| 🟢 Low | 10 | 10 | 0 |
| **Total** | **35** | **35** | **0** |

---

## 🔴 CRITICAL

- [x] **T-01** · Settings: Missing `/api/` prefix — fixed (`/api/user/change-password`, `/api/user/logout-all`, `/api/user/delete-account`)
- [x] **T-02** · Settings: Forwarding router commented out — fixed (`router.py` line 49 active)
- [x] **T-03** · History: Broken script tag structure — verified OK (2 opens + 2 closes, properly nested)
- [x] **T-04** · Settings: Notifications tab JS references missing IDs — fixed (IDs `notif-unread-count`, `notif-count-all`, `notif-list` all present)
- [x] **T-05** · Profile: `/profile` route does not exist — fixed (`main_routes.py` serves it)
- [x] **T-06** · Profile: Avatar upload endpoint does not exist — fixed (`POST /api/user/avatar` in `user_profile.py`)

---

## 🟠 HIGH

- [x] **T-07** · Sidebar: No link to Profile page — fixed (sidebar has `/profile` link with person icon)
- [x] **T-08** · Sidebar: No link to Notifications page — fixed (sidebar has `/notifications` link with bell icon)
- [x] **T-09** · Landing: `/docs` is Swagger UI — acceptable, `api_docs.html` renders correctly
- [x] **T-10** · Landing footer: Internal GitHub repo URL exposed — fixed (shows `github.com/namaskah`, not internal repo)
- [x] **T-11** · Landing: No cookie consent banner — fixed (banner added to `landing.html` matching `base.html` implementation)

---

## 🟡 MEDIUM

- [x] **T-12** · Register: No confirm password field — fixed (`confirm-password` input + validation present)
- [x] **T-13** · Register: Password strength meter 3 segments vs 4 criteria — fixed (4 segments, 4 criteria)
- [x] **T-14** · Register: Uses `alert()` on success — fixed (uses toast system)
- [x] **T-15** · Profile: Uses `alert()` (5 instances) — fixed (all use `window.errorHandler?.showToast()`)
- [x] **T-16** · Settings: Uses `alert()` (8+ instances) — fixed (all replaced with `window.errorHandler?.showToast()`)
- [x] **T-17** · Verify: `#scanning-service-name` never populated — fixed (line 1007 sets it from service label)
- [x] **T-18** · Verify: Step 1 "Back" button calls `history.back()` — fixed (`window.location.href='/dashboard'`)
- [x] **T-19** · History: No pagination, flat load of 100 records — improved (limit raised to 200; full pagination deferred)
- [x] **T-20** · History: No service name filter — fixed (`filter-service` input exists and filters client-side)
- [x] **T-21** · History: `reuseVerification()` never called — fixed (button calls it)
- [x] **T-22** · Settings API Docs tab: Hardcoded wrong base URL — fixed (shows `vrenum.onrender.com`)
- [x] **T-23** · Analytics: Empty chart sections render with no data — fixed (carrier/outcome containers hidden by default, shown only when data exists)
- [x] **T-24** · Analytics: Date range picker and chart range buttons don't sync — fixed (`setChartRange()` now updates date pickers and re-fetches)
- [x] **T-25** · Landing: Hardcoded "10,000+ verifications" stat — fixed (removed)

---

## 🟢 LOW

- [x] **T-26** · API Keys page: Standalone dark-themed page, no sidebar — fixed (extends `dashboard_base.html`)
- [x] **T-27** · Pricing page: Comparison table missing rows — fixed (ISP filters, affiliate, quota rows present)
- [x] **T-28** · Pricing page: No mention of auto-refund guarantee — fixed (FAQ section covers it)
- [x] **T-29** · Pricing page: Only 3 FAQ items — fixed (expanded FAQ with refund, quota, payment method questions)
- [x] **T-30** · Register: No display name field — fixed (`display-name` input present, sent to API)
- [x] **T-31** · Login: Google button styled inconsistently — verified identical to register (both `btn-auth` with same inline style)
- [x] **T-32** · Dashboard: No notification bell/badge in navbar — fixed (bell button with `notification-bell-badge` span in `dashboard_base.html`)
- [x] **T-33** · Dashboard: Recent activity table has no "View All" link — fixed (link to `/history` in card header)
- [x] **T-34** · Verify: No "New Verification" shortcut after code received — fixed ("Start New Verification" button present)
- [x] **T-35** · Verify: Step 2 delivery time hardcoded `~30s` — fixed (dynamically set from `item.estimated_seconds`)
