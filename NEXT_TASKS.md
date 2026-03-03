# Next Tasks

---

## 🔴 CRITICAL — Payment webhook doesn't set tier after Pro/Custom upgrade

**Why critical:** User pays $25/$35, gets redirected back from Paystack, but `subscription_tier` is never updated. They've been charged and are still on Freemium. Revenue + trust damage.

**Root cause:** `POST /api/wallet/paystack/webhook` credits the user's balance but has no logic to check `metadata.upgrade_to` and set `user.subscription_tier`.

**Fix:**
- `app/api/billing/payment_endpoints.py` webhook handler — after crediting user, check `metadata.get('upgrade_to')` and if present, set `user.subscription_tier = metadata['upgrade_to']` + `db.commit()`
- `static/js/dashboard-ultra-stable.js` `confirmUpgrade()` — already passes `metadata: { upgrade_to: tier }` in the initialize payload ✅

**Files:** `app/api/billing/payment_endpoints.py`

---

## 🔴 CRITICAL — Wallet page: 4 broken API calls + 2 blocking dialogs

**Why critical:** Users can't add credits via card (primary revenue flow). Every payment attempt hits a 404.

**Known bugs (from SIDEBAR_AUDIT_TASKS.md):**

| # | Issue | Fix |
|---|---|---|
| 1 | `POST /api/billing/initialize-payment` → 404 | Change to `POST /api/wallet/paystack/initialize` |
| 2 | `GET /api/billing/payment-status/{ref}` → 404 | Already aliased in `compatibility_routes.py` ✅ — confirm wallet.html uses it |
| 3 | `GET /api/user/credits/history` → 404 | Change to `GET /api/wallet/history` |
| 4 | `GET /api/billing/crypto-addresses` → 404 | Already stubbed in `compatibility_routes.py` ✅ — confirm wallet.html uses it |
| 5 | `alert()` in `confirmCryptoPayment()` | Replace with toast |
| 6 | `alert()` in `addCustomCredits()` | Replace with toast |

**Files:** `templates/wallet.html`

---

## 🟠 HIGH — Test coverage: verification + tier upgrade flows have zero tests

**Why high:** The two most complex flows (verification create/poll, tier upgrade) were just rewritten and have no tests. A regression here breaks core revenue.

**What to cover:**
- `POST /api/verify/create` — balance check, capability stored, activation_id set
- `GET /api/verify/{id}/status` — returns sms_code when completed
- `GET /api/verify/{id}/sms` — uses activation_id not DB UUID
- `POST /api/billing/tiers/upgrade` — PAYG commits to DB, paid returns pending_payment

**Files:** `tests/unit/test_verification_routes.py` (new), `tests/unit/test_tier_endpoints.py` (new)

---

## 🟡 MEDIUM — Analytics page charts render empty despite real data

**Why medium:** Page loads and shows zeros even when verifications exist. Cosmetic but erodes trust in the platform.

**Root cause:** `dashboard_router.py` `/analytics/summary` now returns `daily_verifications`, `spending_by_service`, `top_services` ✅ — but `templates/analytics.html` chart rendering code needs to be verified it reads those exact field names.

**Fix:** Audit `analytics.html` JS against the actual API response shape. Patch any field name mismatches.

**Files:** `templates/analytics.html`

---

## 🟢 LOW — Test coverage: overall 23% → 50% (Q1 roadmap target)

**Why low priority now:** Core flows are working. Coverage expansion is valuable but not blocking anything.

**Approach:** Add integration tests for the critical user journeys:
1. Register → login → create verification → receive code
2. Add credits → webhook → balance updated
3. Upgrade to PAYG → tier updated immediately

**Files:** `tests/integration/test_core_flows.py`

---

## Priority Order

| Rank | Severity | Task |
|---|---|---|
| 1 | 🔴 CRITICAL | Webhook doesn't set tier after paid upgrade |
| 2 | 🔴 CRITICAL | Wallet page broken payment flow |
| 3 | 🟠 HIGH | Unit tests for verification + tier upgrade |
| 4 | 🟡 MEDIUM | Analytics charts field mismatch |
| 5 | 🟢 LOW | Broader test coverage (23% → 50%) |
