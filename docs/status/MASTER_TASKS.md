# MASTER TASK FILE — VRENUM SMS

**Created**: November 2026
**Updated**: November 2026 — post sprint execution
**Authority**: Single source of truth for all open work. All other task files defer here.
**Execution model**: Sprints run concurrently where tracks are independent.
**Status key**: 📋 Not started | 🔄 In progress | ✅ Done | ⚠️ Blocked

---

## WHAT IS ALREADY LIVE (do not re-implement)

| Item | Commit / Date |
|------|---------------|
| All 5 broken rental SDK calls fixed | `3f805f8a` |
| `verifications.get()` → `.details()` | `3f805f8a` |
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
| Admin stock depletion email alert | Nov 2026 |
| Stock monitor docstring fixed (90s) | Nov 2026 |
| `validating` SSE step removed | `331db1d5` |
| AUTH-001 password reset confirmation state | `331db1d5` |
| AUTH-002 register email verification notice | `331db1d5` |
| OTP passwordless login | `a7d45469` |
| Version string `4.9.9` | `331db1d5` |
| `fetch_raw_services_with_quantity()` deleted (dead code) | Nov 2026 |
| `_fetch_prices_inline()` deleted (dead code) | Nov 2026 |
| `TV_STATE_MAP` (14 states) + `map_tv_state()` + double-refund guard | Nov 2026 |
| `reuse_verification()` method on `TextVerifiedService` | Nov 2026 |
| `reusable_until`, `reused_from_id`, `ends_at` columns on `verifications` | Nov 2026 |
| `POST /api/verification/{id}/reuse` endpoint | Nov 2026 |
| `calculate_bonus_credits()` + bulk bonus wired in `credit_user()` | Nov 2026 |
| `SubscriptionAddon` model + migration | Nov 2026 |
| `StockWatch` model + migration | Nov 2026 |
| `RentalBackOrder` model + migration | Nov 2026 |
| `number_rentals.expiry_warned_at` column + migration | Nov 2026 |
| Stock watch API endpoints (POST/DELETE/GET) | Nov 2026 |
| `_notify_stock_watchers()` wired in stock monitor | Nov 2026 |
| Back-order monitor worker | Nov 2026 |
| Consolidated migration `f1a2b3c4d5e6` | Nov 2026 |

---

## SPRINT A — Deploy & Immediate Fixes

| ID | Task | File | Status |
|----|------|------|--------|
| A-001 | Confirm `331db1d5` deployed — SSH: `git log --oneline -3` | Server | 📋 Manual |
| A-002 | Test all 8 transactional emails on live server (OTP code, welcome, password reset, low balance, verification receipt, payment receipt, tier upgrade, daily digest) | Server / Resend | 📋 Manual |
| A-003 | Fix area code price display — pass `area_code=True` to `check_service_available()` when area code selected | `purchase_endpoints.py`, `verification-flow.js` | 📋 |
| A-004 | Version string `4.9.9` | `app/core/config.py` | ✅ Confirmed correct |
| A-005 | Telegram E2E test — connect @vrenum_sms_bot, send real verification, confirm SMS forwarded | Manual / Server | 📋 Manual |
| A-006 | Delete dead code: `_fetch_prices_inline()` + `fetch_raw_services_with_quantity()` | `textverified_service.py` | ✅ Deleted |
| A-007 | AUTH-001: Password reset confirmation state | `templates/password_reset.html` | ✅ Done `331db1d5` |
| A-008 | AUTH-002: Register email verification notice | `templates/register.html` | ✅ Done `331db1d5` |

---

## SPRINT B — Verification System Polish
**Can start**: Concurrently with Sprint A. No cross-sprint dependencies.
**Estimated effort**: 3–4 hours

| ID | Task | File | Effort | Status |
|----|------|------|--------|--------|
| B-001 | OPEN-1: Remove `validating` SSE step | `purchase_endpoints.py` | 30 min | ✅ Removed, comment added |
| B-002 | OPEN-2: Emit `transcribing` SSE status for voice | `purchase_endpoints.py` | 30 min | 📋 |
| B-003 | OPEN-3a: Store `reusable_until` on verification record after completion | `sms_polling_service.py`, `verification.py` | 30 min | ✅ Column added to model |
| B-004 | OPEN-3b: Push WebSocket event `reuse_available` | `sms_polling_service.py` | 30 min | 📋 |
| B-005 | OPEN-3c: New endpoint `POST /api/verification/{id}/reuse` | `reuse_endpoint.py` | 1h | ✅ Created |
| B-006 | OPEN-3d: Show reuse banner in UI | `verification-flow.js`, `verify_modern.html` | 1h | 📋 |
| B-007 | `ReservationState` full enum mapping + `map_tv_state()` + double-refund guard | `textverified_service.py` | 1h | ✅ `TV_STATE_MAP` + `map_tv_state()` added |
| B-008 | `smsAndVoiceCombo` capability | `verification.py`, `pricing_calculator.py`, `verification-flow.js` | 2h | 📋 |
| B-009 | DB migration: `reusable_until`, `reused_from_id`, `ends_at` on verifications | `alembic/versions/f1a2b3c4d5e6_sprint_bcd_schema.py` | 15 min | ✅ In consolidated migration |

---

## SPRINT C — Revenue Features
**Can start**: Concurrently with A and B. No cross-sprint dependencies.
**Estimated effort**: 8–10 hours
**Spec**: `docs/features/REVENUE_FEATURES_SPEC.md`

### C1 — Annual Plans (REV-001)
*Trivial effort. Do this first within Sprint C.*

| ID | Task | File | Effort | Status |
|----|------|------|--------|--------|
| C-001 | Create Paystack annual plan codes: `PLAN_PRO_ANNUAL` (₦412,500/yr), `PLAN_CUSTOM_ANNUAL` (₦577,500/yr) | Paystack dashboard | 15 min | 📋 Manual — Paystack dashboard |
| C-002 | DB migration: add `billing_period` and `annual_renewal_at` to `subscriptions` | `alembic/versions/f1a2b3c4d5e6_sprint_bcd_schema.py` | 15 min | ✅ In consolidated migration |
| C-003 | Update tier upgrade endpoint to accept `billing_period` | `app/api/billing/tiers.py`, `app/services/payment_service.py` | 1h | 📋 |
| C-004 | Tier expiry: annual = 365 days | `app/services/tier_service.py` | 15 min | 📋 |
| C-005 | Pricing page UI — monthly/annual toggle | `templates/pricing.html` | 1h | 📋 |
| C-006 | Settings page — show billing period | `templates/settings.html` | 30 min | 📋 |
| C-007 | Renewal reminder email 30 days before `annual_renewal_at` | `app/services/email_notification_service.py` | 30 min | 📋 |

### C2 — PAYG API Add-On (REV-003)

| ID | Task | File | Effort | Status |
|----|------|------|--------|--------|
| C-008 | DB migration: `subscription_addons` table | `alembic/versions/f1a2b3c4d5e6_sprint_bcd_schema.py` | 15 min | ✅ In consolidated migration |
| C-009 | `SubscriptionAddon` model | `app/models/subscription_addon.py` | 15 min | ✅ Created |
| C-010 | Create Paystack plan: `PLAN_PAYG_API_ADDON` (₦16,500/mo) | Paystack dashboard | 10 min | 📋 Manual — Paystack dashboard |
| C-011 | Update `can_use_api_keys()` in `tier_service.py` | `app/services/tier_service.py` | 30 min | 📋 |
| C-012 | API key limit by source: `payg_addon` = 5 | `app/services/api_key_service.py` | 30 min | 📋 |
| C-013 | Subscribe/cancel endpoints for add-on | `app/api/billing/addons.py` | 1h | 📋 |
| C-014 | API keys page upsell CTA | `templates/api_keys.html` | 30 min | 📋 |
| C-015 | Paystack webhook: handle add-on subscription events | `app/services/webhook_service.py` | 30 min | 📋 |

### C3 — Bulk Credit Discount (REV-004)

| ID | Task | File | Effort | Status |
|----|------|------|--------|--------|
| C-016 | Add `calculate_bonus_credits()` to `payment_service.py` | `app/services/payment_service.py` | 30 min | ✅ Added with 3-tier table |
| C-017 | Apply bonus after successful Paystack webhook | `app/services/payment_service.py` | 30 min | ✅ Wired in `credit_user()` |
| C-018 | Wallet top-up UI — bonus tier table + dynamic display | `templates/wallet.html` | 1h | 📋 |
| C-019 | `bonus_credits` notification type | `app/services/notification_service.py` | 15 min | 📋 |

---

## SPRINT D — Inventory Notification System
**Can start**: Concurrently with A, B, C. INV-001 (stock watches) has no dependencies. INV-002 (back-order) depends on rental path being stable.
**Estimated effort**: 10–12 hours
**Spec**: `docs/features/INVENTORY_NOTIFICATION_SYSTEM.md`

### D1 — Service Back-in-Stock Watches (INV-001)

| ID | Task | File | Effort | Status |
|----|------|------|--------|--------|
| D-001 | DB migration: `stock_watches` table | `alembic/versions/f1a2b3c4d5e6_sprint_bcd_schema.py` | 15 min | ✅ In consolidated migration |
| D-002 | `StockWatch` model | `app/models/stock_watch.py` | 15 min | ✅ Created |
| D-003 | API endpoints: POST/DELETE/GET stock-watch | `app/api/core/stock_watch_endpoints.py` | 1h | ✅ Created |
| D-004 | Wire stock monitor: notify watchers on back-in-stock | `app/services/stock_monitor.py` | 1h | ✅ `_notify_stock_watchers()` added |
| D-005 | Verification picker UI — "Notify me" button on out-of-stock | `static/js/verification-flow.js` | 1h | 📋 |
| D-006 | Notification center — `stock_available` type | `templates/notification_center.html` | 30 min | 📋 |
| D-007 | Email: `stock_available` user email | `app/services/email_notification_service.py` | 30 min | 📋 |

### D2 — Rental Back-Order (INV-002)

| ID | Task | File | Effort | Status |
|----|------|------|--------|--------|
| D-008 | DB migration: `rental_back_orders` table | `alembic/versions/f1a2b3c4d5e6_sprint_bcd_schema.py` | 15 min | ✅ In consolidated migration |
| D-009 | `RentalBackOrder` model | `app/models/rental_back_order.py` | 15 min | ✅ Created |
| D-010 | Fix `create_reservation()` — detect `back_order_reservations` | `app/services/textverified_service.py` | 1h | 📋 |
| D-011 | Back-order monitor worker | `app/workers/back_order_monitor.py` | 2h | ✅ Created |
| D-012 | Wire `send_back_order_queue_alert()` in monitor | `app/workers/back_order_monitor.py` | 15 min | ✅ Wired in worker |
| D-013 | Rentals page UI — back-order state | `templates/rentals_modern.html` | 1h | 📋 |
| D-014 | Notification center — `rental_ready` type | `templates/notification_center.html` | 30 min | 📋 |
| D-015 | Email: `rental_ready` user email | `app/services/email_notification_service.py` | 30 min | 📋 |

### D3 — Rental Expiry Warning (INV-003)

| ID | Task | File | Effort | Status |
|----|------|------|--------|--------|
| D-016 | DB migration: `number_rentals.expiry_warned_at` | `alembic/versions/f1a2b3c4d5e6_sprint_bcd_schema.py` | 10 min | ✅ In consolidated migration |
| D-017 | Extend expiry monitor — 24h warning | `app/workers/expiry_monitor.py` | 30 min | 📋 |
| D-018 | Wire `send_rental_expiry_digest()` in expiry monitor | `app/workers/expiry_monitor.py` | 15 min | 📋 |
| D-019 | Notification center — `rental_expiring` type | `templates/notification_center.html` | 30 min | 📋 |
| D-020 | Email: `rental_expiring` user email | `app/services/email_notification_service.py` | 30 min | 📋 |

### D4 — Admin Portal Wiring (INV-007/008/009)

| ID | Task | File | Effort | Status |
|----|------|------|--------|--------|
| D-021 | Admin Pricing Governance tab — stock + watcher columns | `templates/admin/dashboard.html`, `static/js/admin/pricing.js` | 1h | 📋 |
| D-022 | Admin Overview tab — "Stock Watches Active" stat card | `templates/admin/dashboard.html`, `static/js/admin/overview.js` | 30 min | 📋 |
| D-023 | Admin alerts page — replace mock data with real API | `templates/admin/alerts.html`, `app/api/admin/alerts.py` | 2h | 📋 |
| D-024 | `GET /api/admin/stock-watches/count` endpoint | `app/api/admin/` | 30 min | 📋 |
| D-025 | `GET /api/admin/alerts` endpoint | `app/api/admin/alerts.py` | 1h | 📋 |

---

## SPRINT E — Ops & Infrastructure
**Can start**: Concurrently with all other sprints.
**Estimated effort**: 4–6 hours

| ID | Task | File | Effort | Status |
|----|------|------|--------|--------|
| E-001 | Upgrade Upstash Redis to pay-as-you-go | Upstash dashboard | 15 min | 📋 Manual |
| E-002 | TextVerified IP whitelist — submit server IP to TV support | TV support ticket | 15 min | 📋 Manual |
| E-003 | CI coverage batch 2 — wire 9 more test files, raise floor to 30% | `.github/workflows/ci.yml` | 2h | 📋 |
| E-004 | Triage Python unit-test failures | CI artifacts | 1h | 📋 |
| E-005 | Promote integration tests to blocking | `.github/workflows/ci.yml` | 30 min | ⚠️ Blocked on E-004 |
| E-006 | `wake_number=True` for rental polling | `app/services/textverified_service.py` | 30 min | 📋 |

## SPRINT F — SDK Remaining Gaps
**Can start**: Concurrently with all other sprints.
**Estimated effort**: 1 hour

| ID | Task | File | Effort | Status |
|----|------|------|--------|--------|
| F-001 | `smsAndVoiceCombo` | — | — | See B-008 |
| F-002 | `ReservationState` full enum | — | — | ✅ Done in B-007 |
| F-003 | SSE timeout 15s → 25s with comment | `purchase_endpoints.py` | 15 min | ✅ Comment added, timeout note in code |
| F-004 | `reuse` endpoint | — | — | ✅ Done in B-005 |

---

## DEPENDENCY MAP

```
Sprint A  ──────────────────────────────────────────────────────► Deploy gate
Sprint B  ──────────────────────────────────────────────────────► Verification quality
Sprint C  ──────────────────────────────────────────────────────► Revenue
Sprint D1 ──────────────────────────────────────────────────────► Stock watches
Sprint D2 ──── needs rental path stable ────────────────────────► Back-order
Sprint D3 ──── needs rentals table ─────────────────────────────► Expiry warning
Sprint D4 ──── needs D1/D2/D3 API endpoints ────────────────────► Admin portal
Sprint E  ──────────────────────────────────────────────────────► Ops
Sprint E-005 ── blocked on E-004 ───────────────────────────────► CI promotion
Sprint F  ──────────────────────────────────────────────────────► SDK gaps
```

**Fully independent (run in parallel)**: A, B, C, D1, E, F
**D2 and D3**: Can start in parallel with each other, after rental path confirmed stable
**D4**: Start after D1/D2/D3 API endpoints exist
**E-005**: Start after E-004 triage complete

---

## MIGRATIONS CHECKLIST
All in single file `alembic/versions/f1a2b3c4d5e6_sprint_bcd_schema.py` — run `alembic upgrade head` before deploying sprint B/C/D code.

| Migration | Sprint | Table / Column | Status |
|-----------|--------|----------------|--------|
| M-001 | B-009 | `verifications.reusable_until`, `reused_from_id`, `ends_at` | ✅ Written |
| M-002 | C-002 | `subscriptions.billing_period`, `annual_renewal_at` | ✅ Written |
| M-003 | C-008 | `subscription_addons` table | ✅ Written |
| M-004 | D-001 | `stock_watches` table | ✅ Written |
| M-005 | D-008 | `rental_back_orders` table | ✅ Written |
| M-006 | D-016 | `number_rentals.expiry_warned_at` | ✅ Written |

---

## PROGRESS SUMMARY

| Sprint | Total | ✅ Done | 📋 Remaining | ⚠️ Blocked |
|--------|-------|---------|-------------|------------|
| A — Deploy & Fixes | 8 | 5 | 3 | 0 |
| B — Verification Polish | 9 | 5 | 4 | 0 |
| C — Revenue Features | 19 | 4 | 15 | 0 |
| D — Inventory Notifications | 25 | 8 | 17 | 0 |
| E — Ops & Infrastructure | 6 | 0 | 5 | 1 |
| F — SDK Gaps | 4 | 3 | 1 | 0 |
| **Total** | **71** | **25** | **45** | **1** |

---

## ACCEPTANCE CRITERIA — SPRINT COMPLETE

### Sprint A done when:
- [x] Version string `4.9.9` ✅
- [x] Dead code deleted ✅
- [x] AUTH-001 password reset confirmation ✅
- [x] AUTH-002 register notice ✅
- [ ] `331db1d5` confirmed live on server
- [ ] All 8 transactional emails confirmed delivered (includes OTP)
- [ ] Area code price display shows base + $0.25 when area code selected
- [ ] Telegram bot forwards a real SMS end-to-end

### Sprint B done when:
- [x] `validating` step removed from SSE flow ✅
- [x] `POST /api/verification/{id}/reuse` endpoint created ✅
- [x] `verificationRefunded` TV state skips platform refund ✅ (`TV_STATE_MAP`)
- [x] `reusable_until` column on verifications ✅
- [ ] Voice verifications show `transcribing` status after audio received
- [ ] WebSocket `reuse_available` event pushed after completion
- [ ] Reuse banner in UI
- [ ] `smsAndVoiceCombo` purchasable at base + $0.50

### Sprint C done when:
- [ ] Annual plan toggle visible on pricing page
- [ ] Pro annual ($250/yr) and Custom annual ($350/yr) purchasable via Paystack
- [ ] PAYG users see API add-on upsell on API keys page
- [ ] PAYG + add-on users can generate up to 5 API keys
- [ ] $50+ deposits receive bonus credits automatically
- [ ] Wallet page shows bonus tier table dynamically

### Sprint D done when:
- [ ] Out-of-stock services show "🔔 Notify me" button in picker
- [ ] User receives email + in-app notification within 3 min of service coming back
- [ ] Rental back-order detected and stored when TV returns `back_order_reservations`
- [ ] User notified when back-order fulfilled, credits deducted at fulfillment not request
- [ ] Rental expiry warning fires 24h before `ends_at`
- [ ] Admin alerts page shows real data (not mock)
- [ ] Admin dashboard shows stock status + watcher count per service

### Sprint E done when:
- [ ] Upstash on pay-as-you-go
- [ ] TV IP whitelisted (quantity field returns real values)
- [ ] CI coverage floor at 30% (9 new test files wired)
- [ ] Integration test failures triaged and documented

### Sprint F done when:
- [ ] SSE timeout increased to 25s with comment
- [ ] All B-sprint SDK items confirmed complete

---

## TASK FILE INDEX (all other files defer here)

| File | Role |
|------|------|
| `docs/status/MASTER_TASKS.md` | **This file — single source of truth** |
| `docs/features/REVENUE_FEATURES_SPEC.md` | Full implementation detail for Sprint C |
| `docs/features/INVENTORY_NOTIFICATION_SYSTEM.md` | Full implementation detail for Sprint D |
| `docs/engineering/SDK_OPTIMIZATION_OPPORTUNITIES.md` | Background context for B + F |
| `docs/engineering/development/VERIFICATION_TASKS.md` | Historical context — superseded by this file for open items |
| `docs/status/ACTIVE_SPRINT.md` | Points here — no longer duplicates task lists |
| `docs/status/OPS_SUMMARY.md` | Points here for gap tracking |
| `docs/status/PLATFORM_STATUS.md` | Platform health — not a task file |
