# Tasks

_Nothing open. See TODO.md for remaining manual Render steps._

---

## ✅ Done — Sprint (Mar 2026)

- `safe_add_tiers` migration — `NoSuchTableError: users` → table-existence guard added
- `add_user_preferences` migration — same crash → same guard added
- `quota_pricing_v3_1` migration — `subscription_tier` queries wrapped in column-existence check; `quota_transactions` FK crash covered by early-return guard
- `add_preferred_area_codes` migration — no idempotency guard → `_column_exists()` added
- Security middleware re-enabled in `main.py` (was commented out with "Temporarily disabled for CI fix")
- `app/middleware/logging.py.broken` + `security.py.broken` — deleted
- Pricing router re-enabled in `main.py`
- Emergency endpoint hardcoded secret → moved to `EMERGENCY_SECRET` env var
- `CORS_ORIGINS=*` wildcard blocked in production via `config.py` validator

## ✅ Done — Prior Sprint

- T1 · `require_tier` reads `subscription_tier`
- T2 · `auto_topup_service` rewired to `charge_authorization`; `deduct_credits` triggers `check_and_topup`
- T3 · `create_test_token` added to `tests/conftest.py`
- T4 · `generate_api_key` added to `app/utils/security.py`
- T5 · `consolidated_verification.py` stub created
- T6 · All unit + integration test files compile cleanly
- T7 · Webhook idempotency + idempotency key on `POST /wallet/paystack/initialize`; `IntegrityError` in `credit_user` fixed
- T8 · `bandit` clean (0 HIGH/MEDIUM); `compare_digest` on all 4 signature sites
- T9 · `@pytest.mark.requires_db` added to PostgreSQL/Redis-dependent tests
- Billing tab — all 7 features complete (PDF invoices, card on file, auto-recharge, spending limits, low-balance alerts, renewal info, payment method gate)
- `require_payment_method` dependency on API key routes
- `credit_service.deduct_credits` — spending limit check + low-balance email alert
- `GET /api/verification/textverified/balance` → 404 fixed
- `TextVerifiedService` singleton fixed
- Migration `001`, `002`, `003` `DuplicateColumn` → idempotency guards added
- `websocket_router` registered twice → fixed
- `str | None` Pydantic crash on Python 3.9 → `Optional[X]` fix
- `hash_password` missing → aliased `get_password_hash`
- `settings.smtp_host/smtp_user/from_email` → corrected field names
