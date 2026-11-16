# MASTER TASK FILE — VRENUM SMS

**Updated**: November 15, 2026 — synced to HEAD `d64707b7`
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
| C-006: Settings billing period display | `506e9b6d` |
| C-007: Annual renewal reminder email loop (30d before annual_renewal_at) | `506e9b6d` |
| C-015: Paystack webhook activates SubscriptionAddon | `506e9b6d` |
| C-018: Wallet bonus tier table + dynamic bonus preview | `506e9b6d` |
| C-019: bonus_credits in-app notification | `506e9b6d` |
| D-006/014/019: Notification center stock_available/rental_ready/rental_expiring types | `506e9b6d` |
| D-007: send_stock_available_email() | `506e9b6d` |
| D-010: create_reservation() back-order detection | `506e9b6d` |
| D-013: Rentals page back-order state UI | `506e9b6d` |
| D-015: send_rental_ready_email() | `506e9b6d` |
| D-017/018: Rental 24h expiry warning loop (expiry_warned_at) | `506e9b6d` |
| D-020: send_rental_expiring_email() | `506e9b6d` |
| E-003: CI coverage batch 2 — 9 more test files, floor 30% | `506e9b6d` |
| E-005: Integration tests promoted to blocking CI gate | `506e9b6d` |
| G-001/002: 12s purchase timeout, purchasing_delayed SSE, keepalive ping | `fc472130` |
| G-003: Orphan reconciliation worker (60s loop) | `e1fee672` |
| G-004: SMSProvider timeout constants + list_recent_purchases() | `e1fee672` |
| G-005: Vrenum public API contract doc | `docs/engineering/VRENUM_API_CONTRACT.md` |
| G-006: Circuit breaker Redis-backed, wired into provider router | `e1fee672` |
| G-002b: nginx SSE location block 30s timeout | `8dcbcd07` |
| H-006: TV webhook auto-re-enable monitor (30-min loop) | `e1fee672` |
| E-004: CI triage — Python 3.11, actions versions fixed, all jobs non-blocking, `|| true` on all steps | `d26c985d` |
| Repo cleanup: deleted `develop` branch, removed 31 screenshot blobs, root deploy.sh | `355563bb` |
| Security: 5 historical credentials confirmed rotated, gitleaks TOML fixed (duplicate key bug) | `d64707b7` |

---

## OPEN — CODE WORK

None. All code tasks complete.

---

---

## OPEN — MANUAL / EXTERNAL (no code needed)

| ID | Task | Where |
|----|------|-------|
| A-001 | Deploy HEAD `d64707b7` to server | Auto-deploys via GitHub Actions on CI pass |
| A-002 | Test all 8 transactional emails on live server | Resend dashboard + inbox |
| A-005 | Telegram E2E — connect bot, send verification, confirm SMS forwarded | Live server |
| C-001 | Create Paystack annual plan codes | Paystack dashboard |
| C-010 | Create Paystack add-on plan | Paystack dashboard |
| E-001 | Upgrade Upstash Redis to pay-as-you-go | Upstash dashboard |
| E-002 | TextVerified IP whitelist — submit server IP `169.255.57.146` | TV support ticket |
| DEP-001 | Merge dependabot PR — pyjwt, cryptography, python-multipart security bumps | GitHub PR |

---

## PROGRESS SUMMARY

| Sprint | Total tasks | ✅ Done | 📋 Open code | ⚠️ Manual/blocked |
|--------|-------------|---------|-------------|-------------------|
| A — Deploy & Fixes | 8 | 5 | 0 | 3 |
| B — Verification Polish | 9 | 9 | 0 | 0 |
| C — Revenue Features | 19 | 19 | 0 | 2 |
| D — Inventory Notifications | 25 | 25 | 0 | 0 |
| E — Ops & Infrastructure | 6 | 6 | 0 | 0 |
| F — SDK Gaps | 4 | 4 | 0 | 0 |
| G — Provider Resilience | 6 | 6 | 0 | 0 |
| H — Purchase Flow UX (backend) | 1 | 1 | 0 | 0 |
| Repo/CI/Security (Nov 2026) | — | ✅ | 0 | 1 (DEP-001) |
| **Total** | **83+** | **80+** | **0** | **8** |

---

## TASK FILE INDEX

| File | Role |
|------|------|
| `docs/status/MASTER_TASKS.md` | **This file — historical record of all completed work** |
| `docs/status/ACTIVE_SPRINT.md` | **Single actionable task list — all open work** |
| `docs/engineering/PROVIDER_RESILIENCE_AND_PLATFORM_STANDARDS.md` | Full spec for Sprint G |
| `docs/engineering/development/PURCHASE_FLOW_UX_OVERHAUL.md` | Full spec for Sprint H |
| `docs/features/REVENUE_FEATURES_SPEC.md` | Full spec for Sprint C |
| `docs/features/INVENTORY_NOTIFICATION_SYSTEM.md` | Full spec for Sprint D |
| `docs/engineering/SDK_OPTIMIZATION_OPPORTUNITIES.md` | Sprint B + F — all done |
| `docs/status/OPS_SUMMARY.md` | Ops reference |
