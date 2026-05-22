# Test Remediation Phase 4 - Complete Test Suite Fix

**Created**: May 20, 2026
**Current Status**: 81.2% Pass Rate (2,079/2,559 passing)
**Target**: 95%+ Pass Rate
**Errors**: 45 (CRITICAL - Must fix first)
**Failures**: 404

---

## 🎯 Current State

```
Total Tests:    2,559
Passing:        2,079 (81.2%)
Failing:        404 (15.8%)
Errors:         45 (1.8%)
Skipped:        30 (1.2%)
XPassed:        1 (0.04%)
```

**Critical Finding**: 45 ERRORS must be fixed before addressing failures.

---

## 🚨 Phase 4A: Fix Errors First (CRITICAL)

**Priority**: P0 - BLOCKING
**Effort**: 4-6 hours
**Impact**: Errors prevent tests from running at all

### Step 1: Identify Error Types (30 min)
```bash
python3 -m pytest --tb=short -x 2>&1 | grep -A 10 "ERROR"
```

**Common Error Types**:
- Import errors (missing modules)
- Fixture errors (undefined fixtures)
- Setup/teardown errors (database, mocks)
- Dependency errors (missing packages)

### Step 2: Fix Import Errors (1-2 hours)
- [ ] Check for circular imports
- [ ] Verify all test imports exist
- [ ] Fix missing model/service imports
- [ ] Update deprecated imports

### Step 3: Fix Fixture Errors (1-2 hours)
- [ ] Verify all fixtures defined in conftest.py
- [ ] Fix fixture scope issues
- [ ] Add missing fixtures
- [ ] Fix fixture dependencies

### Step 4: Fix Setup/Teardown Errors (1-2 hours)
- [ ] Database initialization errors
- [ ] Mock setup errors
- [ ] Cleanup errors
- [ ] Resource allocation errors

**Validation**: Run tests again, verify 0 errors
```bash
python3 -m pytest --tb=no -q 2>&1 | grep "error"
```

---

## 🔧 Phase 4B: Fix Mock Infrastructure (8-10 hours)

**Priority**: P1 - HIGH
**Effort**: 8-10 hours
**Impact**: Fixes ~200 failures

### Task 1: TextVerified Service Mock (3 hours)
**Files**:
- `tests/unit/test_verification_endpoints_comprehensive.py` (15 failures)
- `tests/unit/test_sms_service_complete.py` (6 failures)
- Other verification tests (~20 failures)

**Problem**: Mock not intercepting service calls

**Solution**:
```python
# Create proper fixture in conftest.py
@pytest.fixture
def mock_textverified_service(monkeypatch):
    """Mock TextVerified service at the correct layer."""
    mock_service = MagicMock()
    mock_service.enabled = True
    mock_service.create_verification = AsyncMock(
        return_value={
            "id": "tv-123",
            "phone_number": "+12025551234",
            "cost": 0.50,
        }
    )
    mock_service.get_sms = AsyncMock(return_value=None)
    mock_service.cancel_number = AsyncMock()

    # Patch at import time, not runtime
    monkeypatch.setattr(
        "app.services.textverified_service.TextVerifiedService",
        lambda: mock_service
    )
    return mock_service
```

**Tests to Fix**:
- [ ] `test_get_available_services_success`
- [ ] `test_get_available_services_unavailable`
- [ ] `test_create_verification_success`
- [ ] `test_create_verification_with_filters`
- [ ] All 15 verification endpoint tests
- [ ] All 6 SMS service tests
- [ ] ~20 other verification tests

**Validation**:
```bash
python3 -m pytest tests/unit/test_verification_endpoints_comprehensive.py -v
```

---

### Task 2: Email/SMTP Service Mock (2 hours)
**Files**:
- `tests/unit/test_email_service.py` (5 failures)
- `tests/unit/test_email_notifications.py` (2 failures)
- `tests/unit/test_email_templates_enhancements.py` (3 failures)

**Problem**: SMTP not mocked, tests try to send real emails

**Solution**:
```python
@pytest.fixture
def mock_smtp(monkeypatch):
    """Mock SMTP at the correct layer."""
    mock_smtp_instance = MagicMock()
    mock_smtp_instance.sendmail = MagicMock(return_value={})
    mock_smtp_instance.quit = MagicMock()

    mock_smtp_class = MagicMock(return_value=mock_smtp_instance)
    monkeypatch.setattr("smtplib.SMTP", mock_smtp_class)
    monkeypatch.setattr("smtplib.SMTP_SSL", mock_smtp_class)

    return mock_smtp_instance
```

**Tests to Fix**:
- [ ] `test_send_payment_receipt`
- [ ] `test_send_payment_failed_alert`
- [ ] `test_send_refund_notification`
- [ ] `test_disabled_service`
- [ ] `test_actual_smtp_send`
- [ ] `test_create_verification_completed_html`
- [ ] `test_create_weekly_digest_html`
- [ ] `test_send_test_email_success`
- [ ] `test_send_test_email_with_custom_variables`
- [ ] `test_ac3_test_email_sends`

**Validation**:
```bash
python3 -m pytest tests/unit/test_email*.py -v
```

---

### Task 3: Push Notification Mock (2 hours)
**Files**:
- `tests/unit/test_mobile_notifications.py` (12 failures)

**Problem**: FCM/APNs mock returns 0 sent count

**Solution**:
```python
@pytest.fixture
def mock_fcm(monkeypatch):
    """Mock Firebase Cloud Messaging."""
    mock_send = MagicMock(return_value={"success": 1, "failure": 0})
    monkeypatch.setattr("firebase_admin.messaging.send", mock_send)
    return mock_send

@pytest.fixture
def mock_apns(monkeypatch):
    """Mock Apple Push Notification Service."""
    mock_send = MagicMock(return_value={"success": 1, "failure": 0})
    monkeypatch.setattr("app.services.notification_service.send_apns", mock_send)
    return mock_send
```

**Tests to Fix**:
- [ ] `test_send_push_notification_android` (6 tests)
- [ ] `test_send_push_notification_ios` (6 tests)

**Validation**:
```bash
python3 -m pytest tests/unit/test_mobile_notifications.py -v
```

---

### Task 4: Provider Router Mock (1.5 hours)
**Files**:
- `tests/unit/providers/test_provider_router.py` (8 failures)
- `tests/unit/providers/test_provider_router_extended.py` (5 failures)

**Problem**: Provider abstraction layer mocking incomplete

**Solution**:
```python
@pytest.fixture
def mock_provider_router(monkeypatch):
    """Mock provider router."""
    mock_router = MagicMock()
    mock_router.get_provider = MagicMock(return_value=mock_textverified_service)
    mock_router.failover = MagicMock(return_value=mock_backup_provider)

    monkeypatch.setattr(
        "app.services.provider_router.ProviderRouter",
        lambda: mock_router
    )
    return mock_router
```

**Tests to Fix**:
- [ ] All 8 provider router tests
- [ ] All 5 provider router extended tests

**Validation**:
```bash
python3 -m pytest tests/unit/providers/ -v
```

---

### Task 5: Payment/Paystack Mock (1.5 hours)
**Files**:
- Various payment-related tests (~15 failures)

**Problem**: Paystack API mocking incomplete

**Solution**:
```python
@pytest.fixture
def mock_paystack(monkeypatch):
    """Mock Paystack payment gateway."""
    mock_paystack = MagicMock()
    mock_paystack.transaction.initialize = MagicMock(
        return_value={
            "status": True,
            "data": {
                "authorization_url": "https://checkout.paystack.com/test",
                "reference": "test-ref-123"
            }
        }
    )
    mock_paystack.transaction.verify = MagicMock(
        return_value={
            "status": True,
            "data": {
                "status": "success",
                "amount": 1000,
                "reference": "test-ref-123"
            }
        }
    )

    monkeypatch.setattr("app.services.payment_service.paystack", mock_paystack)
    return mock_paystack
```

**Tests to Fix**:
- [ ] Payment initialization tests
- [ ] Payment verification tests
- [ ] Webhook tests
- [ ] Refund tests

**Validation**:
```bash
python3 -m pytest tests/unit/test_payment*.py -v
```

---

## 🔄 Phase 4C: Update Test Expectations (4-6 hours)

**Priority**: P2 - MEDIUM
**Effort**: 4-6 hours
**Impact**: Fixes ~100 failures

### Task 1: Auth Endpoint Tests (2 hours)
**Files**:
- `tests/unit/test_auth_endpoints_comprehensive.py` (7 failures)

**Problem**: Response format changed

**Solution**: Update assertions to match new response structure
```python
# Old expectation
assert response.json() == {"access_token": "...", "token_type": "bearer"}

# New expectation
assert response.json() == {
    "access_token": "...",
    "refresh_token": "...",  # Added in v4.7.x
    "token_type": "bearer",
    "expires_in": 3600
}
```

**Tests to Fix**:
- [ ] `test_logout_success`
- [ ] `test_refresh_token_success`
- [ ] `test_refresh_token_invalid`
- [ ] `test_refresh_token_missing`
- [ ] `test_refresh_token_expired`
- [ ] `test_create_api_key_tier_restriction`
- [ ] `test_list_api_keys_empty`

---

### Task 2: Error Handling Tests (2 hours)
**Files**:
- `tests/unit/test_error_handling_comprehensive.py` (8 failures)

**Problem**: Error messages changed

**Solution**: Update error message assertions
```python
# Old expectation
assert "Invalid email" in response.json()["detail"]

# New expectation (more specific)
assert "Email format is invalid" in response.json()["detail"]
```

**Tests to Fix**:
- [ ] `test_invalid_email_format`
- [ ] `test_missing_required_field`
- [ ] `test_missing_token`
- [ ] `test_invalid_token`
- [ ] `test_wrong_credentials`
- [ ] `test_duplicate_registration`
- [ ] `test_empty_string_input`
- [ ] `test_boundary_conditions`

---

### Task 3: Response Format Updates (2 hours)
**Files**: Various endpoint tests

**Problem**: API response structure evolved

**Solution**: Update all response assertions to match current API

**Tests to Fix**:
- [ ] Verification endpoint responses
- [ ] Wallet endpoint responses
- [ ] Tier endpoint responses
- [ ] Admin endpoint responses

---

## 🏗️ Phase 4D: Infrastructure Tests (4-6 hours)

**Priority**: P3 - LOW
**Effort**: 4-6 hours
**Impact**: Fixes ~80 failures

### Task 1: Voice/Rental Area Code Gating (2 hours)
**Files**:
- `tests/unit/test_voice_area_code_gating.py` (5 failures)
- `tests/unit/test_rental_area_code_gating.py` (5 failures)

**Problem**: Tier gating logic changed in v4.7.1

**Solution**: Update tier checks to match current implementation

---

### Task 2: Middleware Tests (1 hour)
**Files**:
- `tests/unit/test_middleware_comprehensive.py` (5 failures)

**Problem**: Middleware behavior changed

**Solution**: Update middleware test expectations

---

### Task 3: WebSocket Tests (1 hour)
**Files**:
- `tests/unit/test_websocket.py` (4 failures)

**Problem**: WebSocket event structure changed in v4.5.0

**Solution**: Update WebSocket event assertions

---

### Task 4: Other Infrastructure (2 hours)
**Files**: Various

**Tests to Fix**:
- [ ] Tier service (4 tests)
- [ ] Refund policy (4 tests)
- [ ] Configuration (1 test)
- [ ] Document service (1 test)
- [ ] Core modules (1 test)

---

## 📋 Phase 4E: New Feature Validation (2-3 hours)

**Priority**: P1 - HIGH
**Effort**: 2-3 hours
**Impact**: Validates v4.7.3 features

### Task 1: Disputes Enhancements (45 min)
**Status**: ✅ ALREADY FIXED (16 tests passing)

---

### Task 2: Email Template Enhancements (30 min)
**Files**: `tests/unit/test_email_templates_enhancements.py`

**Tests to Fix**:
- [ ] `test_send_test_email_success`
- [ ] `test_send_test_email_with_custom_variables`
- [ ] `test_ac3_test_email_sends`

---

### Task 3: Manual Feature Validation (1 hour)
- [ ] Test disputes flow in staging
- [ ] Test email templates in staging
- [ ] Test GDPR export in staging
- [ ] Test support tab in staging

---

## 📊 Progress Tracking

### Phase 4A: Fix Errors ⏳
- [ ] Identify error types (30 min)
- [ ] Fix import errors (1-2 hours)
- [ ] Fix fixture errors (1-2 hours)
- [ ] Fix setup/teardown errors (1-2 hours)
- **Total**: 4-6 hours
- **Target**: 0 errors

### Phase 4B: Fix Mock Infrastructure ⏳
- [ ] TextVerified mock (3 hours) - ~41 tests
- [ ] Email/SMTP mock (2 hours) - ~10 tests
- [ ] Push notification mock (2 hours) - ~12 tests
- [ ] Provider router mock (1.5 hours) - ~13 tests
- [ ] Payment/Paystack mock (1.5 hours) - ~15 tests
- **Total**: 10 hours
- **Target**: ~91 tests fixed

### Phase 4C: Update Test Expectations ⏳
- [ ] Auth endpoint tests (2 hours) - ~7 tests
- [ ] Error handling tests (2 hours) - ~8 tests
- [ ] Response format updates (2 hours) - ~20 tests
- **Total**: 6 hours
- **Target**: ~35 tests fixed

### Phase 4D: Infrastructure Tests ⏳
- [ ] Voice/rental gating (2 hours) - ~10 tests
- [ ] Middleware tests (1 hour) - ~5 tests
- [ ] WebSocket tests (1 hour) - ~4 tests
- [ ] Other infrastructure (2 hours) - ~11 tests
- **Total**: 6 hours
- **Target**: ~30 tests fixed

### Phase 4E: New Feature Validation ⏳
- [x] Disputes enhancements - ✅ DONE
- [ ] Email template enhancements (30 min) - ~3 tests
- [ ] Manual validation (1 hour)
- **Total**: 1.5 hours
- **Target**: ~3 tests fixed

---

## 🎯 Overall Timeline

| Phase | Effort | Tests Fixed | Priority |
|-------|--------|-------------|----------|
| **4A: Errors** | 4-6 hours | 45 errors → 0 | P0 |
| **4B: Mocks** | 10 hours | ~91 failures | P1 |
| **4C: Expectations** | 6 hours | ~35 failures | P2 |
| **4D: Infrastructure** | 6 hours | ~30 failures | P3 |
| **4E: New Features** | 1.5 hours | ~3 failures | P1 |
| **TOTAL** | **27.5-29.5 hours** | **~204 issues** | - |

**Estimated Timeline**: 4-5 working days (8 hours/day)

---

## 🎯 Success Metrics

### Current State
- Pass Rate: 81.2% (2,079/2,559)
- Errors: 45
- Failures: 404

### Target State (After Phase 4)
- Pass Rate: 95%+ (2,435+/2,559)
- Errors: 0
- Failures: <125

### Stretch Goal
- Pass Rate: 98%+ (2,508+/2,559)
- Errors: 0
- Failures: <50

---

## 🚀 Execution Strategy

### Option 1: Sequential (Recommended)
1. **Day 1**: Phase 4A (Errors) - 6 hours
2. **Day 2**: Phase 4B Part 1 (TextVerified + Email) - 5 hours
3. **Day 3**: Phase 4B Part 2 (Notifications + Providers + Payments) - 5 hours
4. **Day 4**: Phase 4C (Expectations) - 6 hours
5. **Day 5**: Phase 4D + 4E (Infrastructure + Validation) - 7.5 hours

### Option 2: Parallel (Faster but riskier)
1. **Day 1-2**: Phase 4A + 4B (Errors + Mocks) - 16 hours
2. **Day 3**: Phase 4C (Expectations) - 6 hours
3. **Day 4**: Phase 4D + 4E (Infrastructure + Validation) - 7.5 hours

### Option 3: Prioritized (Deploy sooner)
1. **Day 1**: Phase 4A (Errors) - 6 hours → Deploy
2. **Week 2**: Phase 4B + 4E (Mocks + New Features) - 11.5 hours
3. **Week 3**: Phase 4C + 4D (Expectations + Infrastructure) - 12 hours

---

## 📞 Resources

| Resource | Command |
|----------|---------|
| **Run all tests** | `python3 -m pytest -v` |
| **Run with coverage** | `python3 -m pytest --cov=app --cov-report=html` |
| **Run specific file** | `python3 -m pytest tests/unit/test_file.py -v` |
| **Stop on first failure** | `python3 -m pytest -x` |
| **Show full traceback** | `python3 -m pytest --tb=long` |
| **Run only errors** | `python3 -m pytest --lf` |

---

## ✅ Completion Criteria

### Phase 4 Complete When:
- [ ] Zero errors in test suite
- [ ] Pass rate ≥95%
- [ ] All mock infrastructure working
- [ ] All new features validated
- [ ] Documentation updated

### Ready to Deploy When:
- [ ] Pass rate ≥95%
- [ ] Zero errors
- [ ] All P0 and P1 tests passing
- [ ] Manual validation complete
- [ ] Staging tests passed

---

**Created**: May 20, 2026
**Status**: Ready to Execute
**Estimated Completion**: May 24-27, 2026 (4-5 days)
