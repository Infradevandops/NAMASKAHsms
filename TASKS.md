# Active Tasks

## 🔴 P0 — Bugs (production impact)

### T1 · `require_tier` reads wrong field
- **File**: `app/core/dependencies.py`
- **Bug**: `getattr(user, 'tier', 'freemium')` — column is `subscription_tier`
- **Impact**: All tier-gated routes silently treat every user as freemium; Pro/PAYG enforcement is broken
- **Fix**: Change to `getattr(user, 'subscription_tier', 'freemium')`
- [x] Fix field name
- [x] Verify `/api/keys/` returns 402 for freemium users

### T2 · `auto_topup_service` reads non-existent User fields
- **File**: `app/services/auto_topup_service.py`
- **Bug**: Reads `user.auto_topup_enabled` / `user.auto_topup_amount` — neither exists on `User` model
- **Impact**: Auto-recharge background service always silently no-ops
- **Fix**: Read from `UserPreference.auto_recharge` / `UserPreference.recharge_amount` (already populated by billing tab)
- [x] Rewrite service to query `UserPreference`
- [ ] Verify auto-recharge triggers correctly after debit

---

## 🟡 P1 — Test Suite (56 unit + 3 integration broken at collection)

### T3 · Add `create_test_token` to `conftest.py`
- **Broken files**: `test_analytics_endpoints.py`, `test_analytics_enhanced.py`, `test_performance.py`, `test_security.py` (skip `test_e2e_user_journeys.py` — E2E)
- **Fix**: Add `create_test_token(user_id, email) -> str` helper to `tests/conftest.py` using `create_access_token` from `app.utils.security`
- [x] Add helper
- [x] Confirm 4 files collect cleanly

### T4 · Fix `app.utils.security` missing `generate_api_key`
- **Broken file**: `tests/unit/test_security_utils.py`
- **Fix**: Add `generate_api_key(length: int) -> str` to `app/utils/security.py` (delegates to `secrets.token_hex`)
- [x] Add function
- [x] Confirm test collects and passes

### T5 · Stub `app.api.verification.consolidated_verification`
- **Broken files**: `tests/unit/test_verification_routes.py`, `tests/test_verification_flow.py`
- **Fix**: Create `app/api/verification/consolidated_verification.py` re-exporting from existing verification routers
- [x] Create stub module
- [x] Confirm files collect

### T6 · Fix syntax/indentation errors in test files
- **56 unit test files** and **3 integration test files** have `IndentationError` / `SyntaxError`
- Integration files with known errors:
  - `tests/integration/test_database_operations.py` line 303
  - `tests/integration/test_redis_operations.py` line 260
  - `tests/integration/test_user_lifecycle_integration.py` line 45
- [x] Fix 3 integration files (known lines)
- [ ] Audit and fix unit test files (run `python3 -m py_compile` across all)
- [ ] Target: 0 collection errors

---

## 🟡 P2 — TODO.md Q1 2026

### T7 · Payment flow hardening
- **Status**: `with_for_update` + `PaymentLog` state machine already in `payment_service.py` (12 references)
- **Remaining**:
  - [ ] Verify webhook idempotency end-to-end (duplicate webhook replays same reference → no double credit)
  - [ ] Add idempotency key validation to `POST /api/wallet/paystack/initialize` (reject duplicate keys)
  - [ ] Race condition test: concurrent credits for same reference

### T8 · Security hardening
- [ ] Install `bandit` (`pip install bandit`) and add to `requirements-dev.txt`
- [ ] Run `bandit -r app/ -ll` and resolve HIGH/MEDIUM findings
- [ ] Audit `hmac.new` usage in 4 files — confirmed valid but verify `compare_digest` used for all signature comparisons (timing-safe)
  - `app/services/payment_service.py:193`
  - `app/services/webhook_service.py:38`
  - `app/api/core/forwarding.py:279`
  - `app/services/paystack_service.py:120`

### T9 · Enable integration tests
- **Status**: `docker-compose.test.yml` uses SQLite — integration tests use `TestClient` (no real DB/Redis needed for most)
- [x] Fix 3 broken integration files (covered by T6)
- [ ] Run full integration suite and get to green
- [ ] Document any tests that genuinely need PostgreSQL/Redis and mark with `@pytest.mark.requires_db`

---

## ✅ Done

- Billing tab — all 7 features complete (PDF invoices, card on file, auto-recharge, spending limits, low-balance alerts, renewal info, payment method gate)
- `require_payment_method` dependency on API key routes
- `credit_service.deduct_credits` — spending limit check + low-balance email alert
- Phantom `on_credits_deducted_enhanced` / `on_credits_added` calls removed
- `t.transaction_type` → `t.type` export bug fixed
- All startup blockers resolved (see `BLOCKING_ISSUES.md`)
