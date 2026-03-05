# Active Tasks

## 🔴 P0 — Bugs (production impact)

### T2 · Verify auto-recharge triggers correctly after debit
- **File**: `app/services/auto_topup_service.py`
- [ ] Manual test: trigger a debit that drops balance below threshold and confirm auto-recharge initiates

---

## ✅ Done

- T1 · `require_tier` reads `subscription_tier` (fixed + verified)
- T2 · `auto_topup_service` rewired to read `UserPreference.auto_recharge` / `recharge_amount`
- T3 · `create_test_token` added to `tests/conftest.py`; 4 files collect cleanly
- T4 · `generate_api_key` added to `app/utils/security.py`
- T5 · `consolidated_verification.py` stub created with `router` re-export
- T6 · All unit + integration test files compile cleanly (0 collection errors)
- T7 · Webhook idempotency verified; idempotency key wired through `POST /wallet/paystack/initialize`; race condition test passes — also fixed `IntegrityError` bug in `credit_user` (concurrent duplicate insert now handled as idempotent success)
- T8 · `bandit` clean (0 HIGH/MEDIUM); `compare_digest` used in all 4 signature comparison sites
- T9 · Integration suite run; `@pytest.mark.requires_db` added to PostgreSQL/Redis-dependent tests
- Billing tab — all 7 features complete (PDF invoices, card on file, auto-recharge, spending limits, low-balance alerts, renewal info, payment method gate)
- `require_payment_method` dependency on API key routes
- `credit_service.deduct_credits` — spending limit check + low-balance email alert
- Phantom `on_credits_deducted_enhanced` / `on_credits_added` calls removed
- `t.transaction_type` → `t.type` export bug fixed
- All startup blockers resolved (see `BLOCKING_ISSUES.md`)
