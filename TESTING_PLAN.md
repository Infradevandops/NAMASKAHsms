# 🧪 Testing Plan - Phase 4

**Version**: 1.0  
**Created**: January 2026  
**Goal**: Increase test coverage from 23% → 50%  
**Timeline**: 2 weeks (Week 7-8)  
**Priority**: CRITICAL

---

## 📊 Current State

### Coverage Analysis
```
Current Coverage: 23%
Target Coverage: 50%
Gap: +27%

Backend: 23% → 50% (+27%)
Frontend: 0% → 30% (+30%)
E2E: 0% → 5 critical flows
```

### Existing Tests
- ✅ Basic unit tests (services)
- ❌ Integration tests (disabled)
- ❌ Frontend tests
- ❌ E2E tests
- ❌ Security tests

---

## 🎯 Testing Strategy

### 1. Backend Testing (23% → 50%)

#### Priority 1: Payment Service (CRITICAL)
**Why**: Handles money, must be bulletproof  
**Time**: 2 days

```python
# tests/unit/test_payment_service.py
- test_initialize_payment_success()
- test_initialize_payment_duplicate_idempotency()
- test_verify_payment_success()
- test_verify_payment_not_found()
- test_process_webhook_success()
- test_process_webhook_duplicate()
- test_race_condition_balance_update()
- test_concurrent_payments()
- test_payment_retry_mechanism()
- test_payment_timeout_handling()
```

**Coverage Target**: 90%+

#### Priority 2: Wallet Service
**Why**: Core business logic  
**Time**: 1.5 days

```python
# tests/unit/test_wallet_service.py
- test_get_balance()
- test_add_credits()
- test_deduct_credits()
- test_insufficient_balance()
- test_transaction_history()
- test_concurrent_balance_updates()
- test_negative_balance_prevention()
```

**Coverage Target**: 85%+

#### Priority 3: SMS Service
**Why**: Main product feature  
**Time**: 1.5 days

```python
# tests/unit/test_sms_service.py
- test_create_verification()
- test_get_verification_status()
- test_poll_messages()
- test_textverified_api_failure()
- test_verification_timeout()
- test_concurrent_verifications()
```

**Coverage Target**: 80%+

#### Priority 4: Auth Service
**Why**: Security critical  
**Time**: 1 day

```python
# tests/unit/test_auth_service.py
- test_register_user()
- test_login_success()
- test_login_invalid_credentials()
- test_jwt_token_generation()
- test_jwt_token_validation()
- test_refresh_token()
- test_oauth_google()
```

**Coverage Target**: 85%+

---

### 2. Integration Tests (Enable Existing)

#### Setup Infrastructure
**Time**: 1 day

```yaml
# docker-compose.test.yml
services:
  postgres-test:
    image: postgres:13
    environment:
      POSTGRES_DB: namaskah_test
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
  
  redis-test:
    image: redis:6
```

#### Enable Tests
```python
# tests/integration/test_payment_flow.py
- test_full_payment_flow()
- test_webhook_processing()
- test_balance_update_after_payment()

# tests/integration/test_verification_flow.py
- test_create_and_poll_verification()
- test_verification_with_insufficient_balance()
```

**Coverage Target**: 60%+

---

### 3. Frontend Testing (0% → 30%)

#### Component Tests
**Time**: 2 days

```javascript
// tests/components/WalletCard.test.js
- renders balance correctly
- handles payment initialization
- shows loading state
- displays error messages

// tests/components/VerificationForm.test.js
- submits verification request
- validates form inputs
- handles API errors
- displays success state
```

#### Integration Tests
**Time**: 1 day

```javascript
// tests/integration/payment.test.js
- complete payment flow
- webhook callback handling
- balance update after payment

// tests/integration/verification.test.js
- create verification
- poll for messages
- display SMS code
```

**Tools**: React Testing Library, Jest, MSW (API mocking)

---

### 4. E2E Tests (Critical Flows)

#### Setup
**Time**: 0.5 days

```bash
npm install --save-dev @playwright/test
# or
npm install --save-dev cypress
```

#### Critical Flows
**Time**: 1.5 days

```javascript
// tests/e2e/auth.spec.js
test('user can register and login', async ({ page }) => {
  // Register
  await page.goto('/register');
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'password123');
  await page.click('button[type="submit"]');
  
  // Verify redirect to dashboard
  await expect(page).toHaveURL('/dashboard');
});

// tests/e2e/payment.spec.js
test('user can add credits', async ({ page }) => {
  // Login
  await login(page);
  
  // Navigate to wallet
  await page.goto('/wallet');
  
  // Initialize payment
  await page.click('button:has-text("Add Credits")');
  await page.fill('[name="amount"]', '10');
  await page.click('button:has-text("Pay with Paystack")');
  
  // Verify redirect to Paystack
  await expect(page.url()).toContain('paystack.com');
});

// tests/e2e/verification.spec.js
test('user can create verification', async ({ page }) => {
  // Login
  await login(page);
  
  // Navigate to verify
  await page.goto('/verify');
  
  // Select country and service
  await page.selectOption('[name="country"]', 'US');
  await page.selectOption('[name="service"]', 'whatsapp');
  
  // Create verification
  await page.click('button:has-text("Get Number")');
  
  // Verify phone number displayed
  await expect(page.locator('.phone-number')).toBeVisible();
});
```

**Coverage**: 5 critical flows

---

## 🔒 Security Testing

### Automated Scans
**Time**: 0.5 days

```bash
# Python security
pip install bandit safety
bandit -r app/
safety check

# Dependency vulnerabilities
npm audit
pip-audit

# OWASP ZAP scan
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://localhost:8000
```

### Manual Tests
**Time**: 0.5 days

- [ ] SQL injection attempts
- [ ] XSS attempts
- [ ] CSRF token validation
- [ ] Rate limiting verification
- [ ] Authentication bypass attempts
- [ ] Authorization checks

---

## 📅 Implementation Timeline

### Week 7: Backend Testing
**Days 1-2**: Payment Service (90% coverage)
- Idempotency tests
- Race condition tests
- Webhook tests

**Days 3-4**: Wallet + SMS Services (85% coverage)
- Balance operations
- Verification flow
- TextVerified integration

**Day 5**: Auth Service (85% coverage)
- JWT tests
- OAuth tests
- Session management

### Week 8: Frontend + E2E
**Days 1-2**: Component Tests (30% coverage)
- Wallet components
- Verification components
- Dashboard components

**Days 3-4**: E2E Tests (5 flows)
- Auth flow
- Payment flow
- Verification flow

**Day 5**: Security + Integration
- Enable integration tests
- Security scans
- Final coverage report

---

## 🎯 Success Criteria

### Coverage Targets
- ✅ Backend: 50%+ (from 23%)
- ✅ Frontend: 30%+ (from 0%)
- ✅ E2E: 5 critical flows
- ✅ Integration: Enabled and passing

### Quality Gates
- ✅ All tests pass in CI
- ✅ No critical security vulnerabilities
- ✅ Payment tests cover race conditions
- ✅ E2E tests cover happy paths
- ✅ Test execution time <5 minutes

### Documentation
- ✅ Test README with run instructions
- ✅ Coverage report generated
- ✅ CI/CD integration documented

---

## 🛠️ Tools & Infrastructure

### Backend
- **pytest**: Test framework
- **pytest-cov**: Coverage reporting
- **pytest-asyncio**: Async test support
- **factory-boy**: Test data factories
- **freezegun**: Time mocking

### Frontend
- **Jest**: Test runner
- **React Testing Library**: Component testing
- **MSW**: API mocking
- **Playwright/Cypress**: E2E testing

### CI/CD
- **GitHub Actions**: Test automation
- **Codecov**: Coverage tracking
- **Pre-commit hooks**: Local testing

---

## 📝 Test Writing Guidelines

### Unit Tests
```python
# Good: Fast, isolated, focused
def test_add_credits_success():
    wallet = WalletService()
    result = wallet.add_credits(user_id=1, amount=10.0)
    assert result.balance == 10.0

# Bad: Slow, coupled, broad
def test_entire_payment_flow():
    # Don't test everything in one test
    pass
```

### Integration Tests
```python
# Good: Tests real interactions
@pytest.mark.integration
def test_payment_updates_database(db_session):
    payment_service = PaymentService(db_session)
    result = payment_service.process_payment(...)
    
    # Verify database state
    user = db_session.query(User).get(1)
    assert user.balance == 10.0
```

### E2E Tests
```javascript
// Good: Tests user journey
test('user can complete payment', async ({ page }) => {
  await login(page);
  await addCredits(page, 10);
  await verifyBalanceUpdated(page, 10);
});

// Bad: Tests implementation details
test('payment API returns 200', async () => {
  // This is an integration test, not E2E
});
```

---

## 🚀 Quick Start

### Run All Tests
```bash
# Backend
pytest

# Frontend
npm test

# E2E
npm run test:e2e

# Coverage
pytest --cov=app --cov-report=html
```

### Run Specific Tests
```bash
# Payment tests only
pytest tests/unit/test_payment_service.py -v

# Integration tests
pytest tests/integration/ -v

# E2E smoke tests
npm run test:e2e:smoke
```

### CI Integration
```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 📊 Progress Tracking

### Week 7 Checklist
- [ ] Payment service tests (90%)
- [ ] Wallet service tests (85%)
- [ ] SMS service tests (80%)
- [ ] Auth service tests (85%)
- [ ] Backend coverage: 50%+

### Week 8 Checklist
- [ ] Component tests (30%)
- [ ] E2E tests (5 flows)
- [ ] Integration tests enabled
- [ ] Security scans passing
- [ ] Documentation complete

---

**Next Steps**: Start with Payment Service tests (highest priority)
