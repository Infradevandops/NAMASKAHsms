# CI Test Failures — Fix Tasklist

**Baseline**: 1076 passed, 678 failed, 56 errors  
**Current**: 1124 passed, 671 failed, 15 errors  
**Target**: 0 errors, <50 failures (pre-existing untestable), coverage ≥60%

---

## ✅ Task 1 — AuthService method mismatch

Added 10 missing methods to `AuthService`: `register_user`, `create_api_key`, `verify_api_key`, `deactivate_api_key`, `get_user_api_keys`, `reset_password_request`, `reset_password`, `verify_admin_access`, `create_or_get_google_user`, `verify_email`. All 17 tests in `test_auth_service.py` now pass.

---

## Task 2 — Hardcoded emails still causing 401s

**Scope**: Integration tests still POSTing to `/api/auth/login` with static emails  
**Root cause**: Some integration tests hardcode credentials that don't match fixture-created users.

**Checklist**
- [ ] `grep -r "test@example.com\|admin@example.com\|user@example.com" tests/` — list remaining hits
- [ ] For each hit: replace with the email from the relevant fixture user
- [ ] Verify login calls use the same email used to create the user in that test's setup

**Acceptance criteria**
- No test POSTs to `/api/auth/login` with a credential that wasn't created in that test's fixture
- The `"Login attempt with non-existent email"` log lines drop to 0

---

## ✅ Task 3 — Reseller service fixture errors

Created `app/services/reseller_service.py` from scratch. Fixed imports in `test_reseller_service.py`. UUID sub-account emails to prevent UNIQUE collisions. All 12 tests pass.

---

## ✅ Task 4 — Notification preferences fixture errors

Fixed hardcoded user IDs → `uuid4()`. Fixed `test_defaults` fixture to use get-or-create. Fixed `auth_headers` in conftest to return a callable factory. All 12 tests pass.

---

## ✅ Task 5 — Webhook service expanded fixture errors

Extended `WebhookService` with sync methods (`create_webhook`, `list_webhooks`, `delete_webhook`, `generate_signature`, `verify_signature`, `trigger_webhook`). Made `db` arg optional. Fixed patch target `aiohttp→httpx`. All 8 tests pass.

---

## ✅ Task 6 — SMS polling fixture errors

UUID'd hardcoded `poll_test@example.com` and `ver_123` verification ID. All 6 tests pass.

---

## Task 7 — TextVerified tests not mocked

**Scope**: `tests/unit/test_textverified_service.py` (16 failures)  
**Root cause**: Tests hit real TextVerified API or fail because credentials are missing.

**Checklist**
- [ ] Audit each test — identify which make real HTTP calls
- [ ] Patch `httpx.AsyncClient` or `TextVerifiedService` methods with `AsyncMock`
- [ ] Ensure no test requires `TEXTVERIFIED_API_KEY` to be set

**Acceptance criteria**
- All 16 tests pass with credentials unset
- No real HTTP calls made during test run

---

## Task 8 — Redis operations tests failing

**Scope**: `tests/unit/test_redis_operations.py` (14 failures)  
**Root cause**: Tests require a live Redis connection.

**Checklist**
- [ ] Add `fakeredis` or `unittest.mock` patching for all Redis calls
- [ ] Confirm `redis_client` fixture is injected into all tests in this file

**Acceptance criteria**
- All 14 tests pass without a live Redis instance
- No `ConnectionRefusedError` in test output

---

## Task 9 — Frontend/integration tests (server-dependent)

**Scope**: `tests/test_tier_locked_modal.py` (39), `tests/test_settings_integration.py` (33), `tests/test_dashboard_integration.py` (28), `tests/test_tier_card_states.py` (12), `tests/test_e2e_user_journeys.py` (12)

**Checklist**
- [ ] Run one failing test with `--tb=long` to confirm root cause
- [ ] If browser/Playwright dependent: move to `tests/e2e/` and add to `--ignore` in `ci.yml`
- [ ] If FastAPI `TestClient` based: fix fixture setup

**Acceptance criteria**
- Each file either passes with TestClient, or is moved to `tests/e2e/` with a documented reason

---

## Task 10 — Integration test errors (access_token KeyError + UNIQUE verifications)

**Scope**: `tests/test_critical_admin.py` (5), `tests/integration/test_settings_api.py` (4), `tests/integration/test_wallet_api.py` (3), `tests/integration/test_analytics_api.py` (2), `tests/test_tier_security.py` (1) — 15 errors total

**Root cause**:
- `KeyError: 'access_token'` — 9 errors: login response doesn't return `access_token` key; tests index it directly
- `UNIQUE constraint failed: verifications.id` — 5 errors: hardcoded `verify_0..4` IDs collide across test runs

**Checklist**
- [ ] Find login response shape and fix tests to use correct key (likely `token` not `access_token`)
- [ ] UUID the hardcoded verification IDs in affected fixtures
- [ ] Remaining 404s — confirm routes exist or skip

**Acceptance criteria**
- 0 errors in these 5 files
- `KeyError: 'access_token'` eliminated

---

## ✅ Task — auto_topup patch target + Decimal/float bugs

Fixed `PaymentService→PaystackService` patch target in `test_auto_topup.py`. Fixed `Decimal + float` arithmetic in `auto_topup_service.py`, `payment_service.py`, `credit_service.py`, `refund_service.py`, `auto_refund_service.py`, `reseller_service.py`, `admin.py`, `credit_endpoints.py`. All 5 auto_topup tests pass.

---

## ✅ Task — AnalyticsService missing methods

Added `calculate_summary`, `group_by_service`, `calculate_daily_stats`, `get_top_services` to `AnalyticsService`. Fixed fixture to pass `db_session`. All 4 tests pass.

---

## Task 11 — Remaining CI jobs (Gitleaks, Bandit)

**Checklist**
- [ ] Run gitleaks locally, find exact trigger, update `tools/gitleaks.toml`
- [ ] Confirm `bandit==1.7.6` pinned in CI
- [ ] Run `safety check` and `semgrep` locally before pushing

**Acceptance criteria**
- Secrets Detection job: ✅ Green
- Security Scan job: ✅ Green

---

## Task 12 — Coverage and cleanup

**Checklist**
- [ ] Delete `tests/unit/test_payment_race_condition.py`
- [ ] Raise `--cov-fail-under` from 36% to 60% after errors reach 0

**Acceptance criteria**
- `test_payment_race_condition.py` deleted
- `--cov-fail-under=60` passes in CI
- Deployment Readiness job unblocks
