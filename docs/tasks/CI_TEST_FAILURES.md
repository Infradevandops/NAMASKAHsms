# CI Test Failures — Fix Tasklist

**Baseline**: 1076 passed, 678 failed, 56 errors  
**Target**: 0 errors, <50 failures (pre-existing untestable), coverage ≥60%

---

## Task 1 — AuthService method mismatch

**Scope**: `tests/unit/test_auth_service.py`, `tests/unit/test_auth_endpoints_comprehensive.py`  
**Root cause**: Tests call methods that don't exist on `AuthService` (`register_user`, `create_api_key`, `verify_api_key`, `reset_password_request`, `reset_password`, `verify_admin_access`, `create_or_get_google_user`, `verify_email`). Actual methods: `create_user`, `authenticate_user`, `create_user_token`.

**Checklist**
- [ ] Map every missing method call in both test files to its real equivalent in `auth_service.py`
- [ ] Update test calls to use correct method names and signatures
- [ ] Where no equivalent exists (e.g. `verify_email`, `reset_password`), mock at the router level or skip with `pytest.mark.skip` + reason

**Acceptance criteria**
- `test_auth_service.py` — 0 `AttributeError` failures
- `test_auth_endpoints_comprehensive.py` — 0 failures caused by missing auth methods
- No new methods added to `AuthService` unless they genuinely belong there

---

## Task 2 — Hardcoded emails still causing 401s

**Scope**: Any test file still using `test@example.com`, `admin@example.com`, or other static emails in login payloads  
**Root cause**: UUID email fix in Fix 6 covered 15 files but some integration tests still hardcode credentials that don't match the fixture-created users.

**Checklist**
- [ ] `grep -r "test@example.com\|admin@example.com\|user@example.com" tests/` — list all remaining hits
- [ ] For each hit: replace with the email from the relevant fixture user, or create the user before logging in
- [ ] Verify login calls use the same email that was used to create the user in that test's setup

**Acceptance criteria**
- `grep -r "test@example.com" tests/` returns 0 results
- No test POSTs to `/api/auth/login` with a credential that wasn't created in that test's fixture/setup
- The 27 `"Login attempt with non-existent email"` log lines drop to 0 in test output

---

## Task 3 — Reseller service fixture errors

**Scope**: `tests/unit/test_reseller_service.py` (11 errors)  
**Root cause**: Missing fixtures or broken imports at collection time.

**Checklist**
- [ ] Run `pytest tests/unit/test_reseller_service.py --tb=long` and capture full error
- [ ] Add any missing fixtures to `conftest.py` (e.g. `reseller_user`, `sub_account`)
- [ ] Fix any import errors (check if `ResellerService` exists and is importable)
- [ ] If `ResellerService` doesn't exist, mark all tests `pytest.mark.skip(reason="service not implemented")`

**Acceptance criteria**
- `test_reseller_service.py` collects without errors
- Either all tests pass, or all are explicitly skipped with a reason

---

## Task 4 — Notification preferences fixture errors

**Scope**: `tests/unit/test_notification_preferences.py` (10 errors)  
**Root cause**: Missing fixtures at setup time.

**Checklist**
- [ ] Run `pytest tests/unit/test_notification_preferences.py --tb=long` and capture full error
- [ ] Add missing fixtures to `conftest.py`
- [ ] Confirm `NotificationPreference` model is importable and table exists in test DB

**Acceptance criteria**
- `test_notification_preferences.py` collects without errors
- Test pass rate ≥80% (failures only for genuine logic bugs, not setup)

---

## Task 5 — Webhook service expanded fixture errors

**Scope**: `tests/unit/test_webhook_service_expanded.py` (8 errors)  
**Root cause**: Missing fixtures or import errors.

**Checklist**
- [ ] Run `pytest tests/unit/test_webhook_service_expanded.py --tb=long`
- [ ] Add missing fixtures; confirm `WebhookService` is importable
- [ ] Check for duplicate with `test_webhook_service_complete.py` — consolidate if overlapping

**Acceptance criteria**
- `test_webhook_service_expanded.py` collects without errors
- 0 setup errors; failures only for logic bugs

---

## Task 6 — SMS polling fixture errors

**Scope**: `tests/unit/test_sms_polling.py` (3 errors)  
**Root cause**: SQLAlchemy errors at setup — likely missing table or FK issue.

**Checklist**
- [ ] Run `pytest tests/unit/test_sms_polling.py --tb=long` and identify exact SQLAlchemy error
- [ ] If FK/table missing: add model to conftest imports or mock the DB call
- [ ] If async setup issue: ensure `asyncio_mode=auto` is applied

**Acceptance criteria**
- `test_sms_polling.py` collects and runs without SQLAlchemy errors
- Core polling logic tests pass

---

## Task 7 — TextVerified tests not mocked

**Scope**: `tests/unit/test_textverified_service.py` (16 failures)  
**Root cause**: Tests hit the real TextVerified API or fail because credentials are missing — no mocking in place.

**Checklist**
- [ ] Audit each test — identify which make real HTTP calls
- [ ] Patch `httpx.AsyncClient` or `TextVerifiedService` methods with `AsyncMock` for all network calls
- [ ] Ensure no test requires `TEXTVERIFIED_API_KEY` to be set

**Acceptance criteria**
- All 16 tests pass with credentials unset (`TEXTVERIFIED_API_KEY=""`)
- No real HTTP calls made during test run (verify with `--capture=no` and no outbound requests)

---

## Task 8 — Redis operations tests failing

**Scope**: `tests/unit/test_redis_operations.py` (14 failures)  
**Root cause**: Tests require a live Redis connection; test environment has no Redis.

**Checklist**
- [ ] Add `fakeredis` or `unittest.mock` patching for all Redis calls in these tests
- [ ] Or add a `redis_client` fixture using `fakeredis.FakeRedis()` (already in conftest — verify it's being used)
- [ ] Confirm `redis_client` fixture is injected into all tests in this file

**Acceptance criteria**
- All 14 tests pass without a live Redis instance
- `fakeredis` used consistently — no `ConnectionRefusedError` in test output

---

## Task 9 — Frontend/integration tests (server-dependent)

**Scope**: `tests/test_tier_locked_modal.py` (39), `tests/test_settings_integration.py` (33), `tests/test_dashboard_integration.py` (28), `tests/test_tier_card_states.py` (12), `tests/test_e2e_user_journeys.py` (12)  
**Root cause**: These tests likely require a running server, browser, or JS rendering — failing because test client doesn't serve frontend assets.

**Checklist**
- [ ] Run one failing test with `--tb=long` to confirm root cause (server vs. fixture vs. logic)
- [ ] If browser/Playwright dependent: move to `tests/e2e/` and add to `--ignore` in `ci.yml`
- [ ] If FastAPI `TestClient` based: fix fixture setup so app starts correctly
- [ ] If testing HTML/template rendering: mock template responses or test logic only

**Acceptance criteria**
- Each file either: passes with TestClient, or is moved to `tests/e2e/` with a documented reason
- No frontend test causes the CI Tests job to fail

---

## Task 10 — Remaining CI jobs (Gitleaks, Bandit)

**Scope**: `.github/workflows/ci.yml`, `tools/gitleaks.toml`

**Checklist**
- [ ] Run gitleaks locally: `docker run -v $(pwd):/repo zricethezav/gitleaks detect --source /repo -c tools/gitleaks.toml` — identify exact triggering line
- [ ] Add allowlist entry in `tools/gitleaks.toml` for any false positives
- [ ] Confirm `bandit==1.7.6` is pinned in CI (not 1.7.8)
- [ ] Run `safety check` and `semgrep` locally to confirm they pass before pushing

**Acceptance criteria**
- Secrets Detection job: ✅ Green
- Security Scan job: ✅ Green
- No real secrets in codebase (only false positives allowlisted)

---

## Task 11 — Coverage and cleanup

**Checklist**
- [ ] Delete `tests/unit/test_payment_race_condition.py` (segfault risk, currently only `--ignore`d)
- [ ] After Tasks 1–9 land: run full suite and record new passing count
- [ ] Raise `--cov-fail-under` in `ci.yml` from 36% to 60%

**Acceptance criteria**
- `test_payment_race_condition.py` deleted and removed from `--ignore` list in `ci.yml`
- `--cov-fail-under=60` passes in CI
- Deployment Readiness job unblocks (auto-triggers when other 3 jobs go green)
