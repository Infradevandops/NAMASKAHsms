# ACTIVE SPRINT

**Updated**: November 2026
**HEAD**: `bafb5db1` on origin/main
**CI**: ✅ Passing — smoke-test + frontend-unit-tests (hard gates)
**Deploy**: ⏳ Pending CI pass on `331db1d5` → auto-triggers via deploy.yml

---

## SPRINT JUST COMPLETED ✅

Concurrent sprint execution — OTP login, AUTH fixes, SSE fix, version bump, SDK dead code removal, revenue backend, inventory notification backend, consolidated DB migration.

**Commits this session**:
- `a7d45469` — OTP passwordless login
- `331db1d5` — AUTH-001, AUTH-002, OPEN-1 (validating step), version 4.9.9

**Code written (not yet deployed)**:
- `TV_STATE_MAP` (14 states) + `map_tv_state()` + `reuse_verification()` on `TextVerifiedService`
- `POST /api/verification/{id}/reuse` endpoint
- `calculate_bonus_credits()` + bulk bonus wired in `credit_user()`
- `SubscriptionAddon`, `StockWatch`, `RentalBackOrder` models
- Stock watch API endpoints (POST/DELETE/GET)
- `_notify_stock_watchers()` in stock monitor
- Back-order monitor worker
- Consolidated migration `f1a2b3c4d5e6` (6 schema changes)
- Dead code deleted: `_fetch_prices_inline()` + `fetch_raw_services_with_quantity()`

---

## NEXT ACTIONS (in order)

### 🔴 Immediate — Server

| Action | Notes |
|--------|-------|
| Confirm `331db1d5` live | SSH: `cd ~/vrenum && git log --oneline -3` |
| Run migration | `docker compose exec app alembic upgrade head` — applies `f1a2b3c4d5e6` |
| Test 8 transactional emails | OTP code, welcome, password reset, low balance, verification receipt, payment receipt, tier upgrade, daily digest |
| Telegram E2E | Connect @vrenum_sms_bot, send real verification, confirm SMS forwarded |

### 🟡 Next Code Sprint

| ID | Item | File |
|----|------|------|
| A-003 | Area code price display — pass `area_code=True` to `check_service_available()` | `purchase_endpoints.py`, `verification-flow.js` |
| B-002 | Voice `transcribing` SSE status | `purchase_endpoints.py` |
| B-004 | WebSocket `reuse_available` event | `sms_polling_service.py` |
| B-006 | Reuse banner in UI | `verification-flow.js`, `verify_modern.html` |
| B-008 | `smsAndVoiceCombo` capability | `schemas/verification.py`, `pricing_calculator.py` |
| C-001 | Paystack annual plan codes | Paystack dashboard (15 min) |
| C-003 | Tier upgrade endpoint — `billing_period` param | `app/api/billing/tiers.py` |
| C-004 | Annual tier expiry = 365 days | `app/services/tier_service.py` |
| C-005 | Pricing page monthly/annual toggle | `templates/pricing.html` |
| C-011 | `can_use_api_keys()` — PAYG + addon | `app/services/tier_service.py` |
| C-018 | Wallet top-up bonus tier UI | `templates/wallet.html` |
| D-005 | "Notify me" button in verification picker | `static/js/verification-flow.js` |
| D-010 | `create_reservation()` back-order detection | `app/services/textverified_service.py` |
| D-017 | Expiry monitor 24h warning | `app/workers/expiry_monitor.py` |
| D-021 | Admin dashboard stock columns | `templates/admin/dashboard.html` |
| D-023 | Admin alerts page — real data | `templates/admin/alerts.html` |
| E-001 | Upstash Redis upgrade | Upstash dashboard |
| E-002 | TV IP whitelist | TV support ticket |
| E-003 | CI coverage batch 2 (9 files → 30%) | `.github/workflows/ci.yml` |

---

## ALL OPEN ITEMS

> Full task breakdown with status: `docs/status/MASTER_TASKS.md`

| Sprint | What | Done | Remaining |
|--------|------|------|-----------|
| A | Deploy & immediate fixes | 5/8 | 3 |
| B | Verification polish | 5/9 | 4 |
| C | Revenue features | 4/19 | 15 |
| D | Inventory notifications | 8/25 | 17 |
| E | Ops & infrastructure | 0/6 | 5 + 1 blocked |
| F | SDK gaps | 3/4 | 1 |

---

## TASK FILE INDEX

| File | Role |
|------|------|
| `docs/status/MASTER_TASKS.md` | **Single source of truth — all open work with full status** |
| `docs/features/REVENUE_FEATURES_SPEC.md` | Full spec for Sprint C |
| `docs/features/INVENTORY_NOTIFICATION_SYSTEM.md` | Full spec for Sprint D |
| `docs/engineering/SDK_OPTIMIZATION_OPPORTUNITIES.md` | Background for Sprints B + F |
| `docs/status/PLATFORM_STATUS.md` | Platform health snapshot |
| `docs/status/OPS_SUMMARY.md` | CI pipeline + infrastructure + gap list |
