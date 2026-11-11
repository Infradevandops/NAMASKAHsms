# MASTER TASK FILE — VRENUM SMS

**Updated**: November 2026 — synced to HEAD `f4b030d5`
**Authority**: Single source of truth. All other task files defer here.
**Status key**: 📋 Not started | ✅ Done | ⚠️ Blocked (manual/external)

---

## WHAT IS LIVE (confirmed in code, do not re-implement)

| Item | Commit |
|------|--------|
| All 5 broken rental SDK calls fixed | `3f805f8a` |
| Pricing URL `/pricing/verifications` confirmed 200 | Nov 10 2026 |
| Voice pricing uses `NumberType.VOIP` | `3f805f8a` |
| `max_price` wired to `verifications.create()` | `3f805f8a` |
| `reactivate` before `report` on timeout | `3f805f8a` |
| `can_report` checked before report call | `3f805f8a` |
| `ends_at` persisted to DB in SSE path | `3f805f8a` |
| SSE streaming purchase endpoint | `750a8d9f` |
| `check_service_available()` on legacy path | `47d69fd1` |
| Stock monitor loop 90s, null-price filter | `47d69fd1` |
| TV webhook instant SMS delivery | `540ee0ec` |
| All 23 admin dashboard tabs | v4.9.0 |
| Phase 1 Analytics (6 event types) | v4.9.0 |
| Telegram SMS forwarding (code complete, E2E pending) | v4.9.0 |
| `validating` SSE step removed | `331db1d5` |
| AUTH-001 password reset confirmation state | `331db1d5` |
| AUTH-002 register email verification notice | `331db1d5` |
| OTP passwordless login | `a7d45469` |
| Version string `4.9.9` | `331db1d5` |
| Dead code deleted (`_fetch_prices_inline`, `fetch_raw_services_with_quantity`) | `7c79789f` |
| `TV_STATE_MAP` (14 states) + `map_tv_state()` + double-refund guard | `7c79789f` |
| `reuse_verification()` on `TextVerifiedService` | `7c79789f` |
| `POST /api/verification/{id}/reuse` endpoint | `7c79789f` |
| `reusable_until` stored after completion + WS event pushed | `7c79789f` |
| Reuse banner in UI (`showReuseBanner`, `openReuseModal`) | `7c79789f` |
| Voice `transcribing` status emitted after audio received | `7c79789f` |
| "Notify me" button on out-of-stock services | `7c79789f` |
| `watchStock()` + `POST /api/notifications/stock-watch` | `7c79789f` |
| `_notify_stock_watchers()` in stock monitor | `7c79789f` |
| Back-order monitor worker (`run_back_order_monitor`) | `7c79789f` |
| `calculate_bonus_credits()` + bulk bonus in `credit_user()` | `7c79789f` |
| `SubscriptionAddon` model | `7c79789f` |
| `StockWatch` model | `7c79789f` |
| `RentalBackOrder` model | `7c79789f` |
| Consolidated migration (6 schema changes) | `7c79789f` |
| Area code price display fix (+$0.25 shown in fallback) | `7c79789f` |
| Wallet preset bonus labels corrected ($50=+5%, $100=+10%) | `7c79789f` |
| `TierUpgradeRequest` with `billing_period` | `bafb5db1` |
| Annual tier expiry 365 days from webhook metadata | `bafb5db1` |
| Pricing page monthly/annual toggle | `bafb5db1` |
| `can_create_key()` checks `SubscriptionAddon` for PAYG | `bafb5db1` |
| PAYG+addon API key limit = 5 | `bafb5db1` |
| `/api/billing/addons` endpoints (subscribe/cancel/status) | `bafb5db1` |
| PAYG API add-on upsell banner on `api_keys.html` | `bafb5db1` |
| Admin pricing table — Stock + Watchers columns | `bafb5db1` |
| Admin overview — Stock Watches Active stat card | `bafb5db1` |
| Admin alerts page — real API (no mock data) | `bafb5db1` |
| `GET /api/alerts/` + `GET /api/alerts/stock-watches/count` | `bafb5db1` |
| `run_back_order_monitor()` wired into lifespan | `bafb5db1` |

---

## OPEN — CODE WORK

### Sprint B — Verification Polish

| ID | Task | File | Effort |
|----|------|------|--------|
| B-008 | `smsAndVoiceCombo` capability — schema, pricing (+$0.50), picker badge, SSE pass-through | `schemas/verification.py`, `pricing_calculator.py`, `verification-flow.js` | 2h |

---

### Sprint C — Revenue Features

| ID | Task | File | Effort |
|----|------|------|--------|
| C-006 | Settings page — show billing period (monthly/annual) per user | `templates/settings.html` | 30 min |
| C-007 | Renewal reminder email 30 days before `annual_renewal_at` | `app/services/email_service.py`, `app/core/lifespan.py` | 30 min |
| C-015 | Paystack webhook: activate `SubscriptionAddon` on successful add-on payment | `app/services/payment_service.py` | 30 min |
| C-018 | Wallet top-up UI — bonus tier table + dynamic bonus display as user types | `templates/wallet.html` | 1h |
| C-019 | `bonus_credits` in-app notification when bonus applied | `app/services/notification_service.py`, `app/services/payment_service.py` | 15 min |

---

### Sprint D — Inventory Notifications

| ID | Task | File | Effort |
|----|------|------|--------|
| D-010 | `create_reservation()` — detect `back_order_reservations`, store `RentalBackOrder` | `app/services/textverified_service.py` | 1h |
| D-013 | Rentals page — back-order state UI ("You're in the queue" + cancel) | `templates/rentals_modern.html` | 1h |
| D-006 | Notification center — `stock_available` type handler | `templates/notification_center.html` | 30 min |
| D-014 | Notification center — `rental_ready` type handler | `templates/notification_center.html` | 30 min |
| D-019 | Notification center — `rental_expiring` type handler | `templates/notification_center.html` | 30 min |
| D-007 | Email: `stock_available` user email | `app/services/email_service.py` | 30 min |
| D-015 | Email: `rental_ready` user email | `app/services/email_service.py` | 30 min |
| D-020 | Email: `rental_expiring` user email | `app/services/email_service.py` | 30 min |
| D-017 | Expiry monitor — 24h warning using `expiry_warned_at` column | `app/workers/expiry_monitor.py` | 30 min |
| D-018 | Wire `send_rental_expiry_digest()` call in expiry monitor | `app/workers/expiry_monitor.py` | 15 min |

---

### Sprint E — Ops & Infrastructure

| ID | Task | File | Effort |
|----|------|------|--------|
| E-003 | CI coverage batch 2 — wire 9 more test files, raise floor to 30% | `.github/workflows/ci.yml` | 2h |
| E-004 | Triage Python unit-test failures — download CI artifact, identify failing tests | CI artifacts | 1h |
| E-005 | Promote integration tests to blocking CI gate | `.github/workflows/ci.yml` | 30 min — ⚠️ blocked on E-004 |
| E-006 | `wake_number=True` for rental polling in `sms.incoming()` | `app/services/textverified_service.py` | 15 min |

---

### Sprint F — SDK

| ID | Task | File | Effort |
|----|------|------|--------|
| F-001 | `smsAndVoiceCombo` | See B-008 | — |

---

## OPEN — MANUAL / EXTERNAL (no code needed)

| ID | Task | Where |
|----|------|-------|
| A-001 | Confirm latest commit deployed on server | SSH: `cd ~/vrenum && git log --oneline -3` |
| A-002 | Test all 8 transactional emails on live server | Resend dashboard + inbox |
| A-005 | Telegram E2E — connect bot, send verification, confirm SMS forwarded | Live server |
| C-001 | Create Paystack annual plan codes (`PLAN_PRO_ANNUAL` ₦412,500/yr, `PLAN_CUSTOM_ANNUAL` ₦577,500/yr) | Paystack dashboard |
| C-010 | Create Paystack add-on plan (`PLAN_PAYG_API_ADDON` ₦16,500/mo) | Paystack dashboard |
| E-001 | Upgrade Upstash Redis to pay-as-you-go | Upstash dashboard |
| E-002 | TextVerified IP whitelist — submit server IP | TV support ticket |

---

## PROGRESS SUMMARY

| Sprint | Total tasks | ✅ Done | 📋 Open code | ⚠️ Manual/blocked |
|--------|-------------|---------|-------------|-------------------|
| A — Deploy & Fixes | 8 | 5 | 0 | 3 |
| B — Verification Polish | 9 | 8 | 1 | 0 |
| C — Revenue Features | 19 | 14 | 5 | 2 |
| D — Inventory Notifications | 25 | 15 | 10 | 0 |
| E — Ops & Infrastructure | 6 | 0 | 4 | 2 |
| F — SDK Gaps | 4 | 3 | 1 | 0 |
| **Total** | **71** | **45** | **21** | **7** |

---

## TASK FILE INDEX

| File | Role |
|------|------|
| `docs/status/MASTER_TASKS.md` | **This file — single source of truth** |
| `docs/features/REVENUE_FEATURES_SPEC.md` | Full spec for Sprint C |
| `docs/features/INVENTORY_NOTIFICATION_SYSTEM.md` | Full spec for Sprint D |
| `docs/engineering/SDK_OPTIMIZATION_OPPORTUNITIES.md` | Background for B + F |
| `docs/status/ACTIVE_SPRINT.md` | Points here |
| `docs/status/OPS_SUMMARY.md` | Points here |
