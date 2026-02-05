# Q1 2026 Complete Roadmap - Security, Testing & Infrastructure

**Status**: Ready for Implementation  
**Priority**: 🔥 HIGH  
**Total Duration**: 4.5 weeks (parallel to payment hardening)  
**Dependencies**: PAYMENT_HARDENING_ROADMAP.md

---

## 📊 Overview

This roadmap covers the remaining 60% of Q1 2026 objectives:
- Security hardening (OWASP Top 10)
- Integration test infrastructure
- E2E smoke tests
- Test coverage expansion (81.48% → 90%+)

**Parallel Execution**: Can run alongside payment hardening

---

## 🔒 Part 1: Security Hardening (2 weeks)

### Phase 1.1: OWASP Top 10 Scanning (3 days)

**Task 1.1.1: SQL Injection Prevention**
**Files**: All `app/api/**/*.py`, `app/services/**/*.py`

```python
# Audit all raw SQL queries
grep -r "text(" app/ | grep -v "test"
grep -r "execute(" app/ | grep -v "test"

# Replace with parameterized queries
# Before:
db.execute(f"SELECT * FROM users WHERE email = '{email}'")

# After:
db.execute(text("SELECT * FROM users WHERE email = :email"), {"email": email})
```

**Tools**: 
- Bandit (Python security linter)
- SQLMap (SQL injection testing)

**Tests**: `tests/security/test_sql_injection.py` (20 tests)

**Task 1.1.2: XSS Prevention**
**Files**: `app/api/**/*.py`, `templates/**/*.html`

```python
# Add output encoding
from markupsafe import escape

# Sanitize all user inputs in responses
def sanitize_output(data: dict) -> dict:
    for key, value in data.items():
        if isinstance(value, str):
            data[key] = escape(value)
    return data
```

**Tests**: `tests/security/test_xss_prevention.py` (15 tests)

**Task 1.1.3: CSRF Protection**
**Files**: `app/middleware/csrf_middleware.py`

```python
# Enable CSRF for state-changing operations
from fastapi_csrf_protect import CsrfProtect

@app.post("/api/payment/initialize")
async def initialize_payment(
    csrf_protect: CsrfProtect = Depends()
):
    await csrf_protect.validate_csrf(request)
    # Process payment
```

**Tests**: `tests/security/test_csrf_protection.py` (10 tests)

---

### Phase 1.2: Authentication & Authorization (3 days)

**Task 1.2.1: JWT Security Audit**
**File**: `app/core/auth_security.py`

```python
# Strengthen JWT configuration
JWT_ALGORITHM = "RS256"  # Change from HS256
JWT_EXPIRY = 900  # 15 minutes (reduce from 7 days)
REFRESH_TOKEN_EXPIRY = 604800  # 7 days

# Add token rotation
def rotate_token(old_token: str) -> str:
    # Blacklist old token
    # Issue new token
    pass
```

**Checks**:
- Token expiry validation
- Signature algorithm strength
- Token blacklisting mechanism
- Refresh token rotation

**Tests**: `tests/security/test_jwt_security.py` (12 tests)

**Task 1.2.2: Session Security**
**File**: `app/core/session_manager.py`

```python
# Add session fixation prevention
# Add concurrent session limits
# Add session timeout
# Add IP binding (optional)

class SessionManager:
    MAX_SESSIONS_PER_USER = 5
    SESSION_TIMEOUT = 3600  # 1 hour
    
    def validate_session(self, session_id: str, user_ip: str):
        # Check timeout
        # Check IP match
        # Check session limit
        pass
```

**Tests**: `tests/security/test_session_security.py` (10 tests)

**Task 1.2.3: Password Security**
**File**: `app/services/auth_service.py`

```python
# Audit password hashing
# Ensure bcrypt with proper rounds
BCRYPT_ROUNDS = 12  # Minimum

# Add password complexity requirements
# Add password breach checking (HaveIBeenPwned API)
# Add rate limiting on login attempts
```

**Tests**: `tests/security/test_password_security.py` (8 tests)

---

### Phase 1.3: Input Validation & Sanitization (2 days)

**Task 1.3.1: Comprehensive Input Validation**
**Files**: `app/schemas/**/*.py`

```python
# Add validators to all Pydantic models
from pydantic import validator, constr

class UserInput(BaseModel):
    email: EmailStr
    username: constr(min_length=3, max_length=50, regex=r'^[a-zA-Z0-9_-]+$')
    
    @validator('username')
    def sanitize_username(cls, v):
        return sanitize_input(v)
```

**Audit**:
- All API endpoints for input validation
- File upload validation
- JSON payload size limits
- Query parameter validation

**Tests**: `tests/security/test_input_validation.py` (25 tests)

**Task 1.3.2: Path Traversal Prevention**
**File**: `app/utils/path_security.py`

```python
def safe_path_join(base: str, user_input: str) -> str:
    """Prevent path traversal attacks."""
    # Normalize path
    # Check for ../ sequences
    # Validate within base directory
    pass
```

**Tests**: `tests/security/test_path_traversal.py` (8 tests)

---

### Phase 1.4: Secrets & Dependency Management (2 days)

**Task 1.4.1: Secrets Scanning**
**Tools**: 
- GitLeaks (scan git history)
- TruffleHog (find secrets)
- detect-secrets (pre-commit hook)

```bash
# Run secrets scan
gitleaks detect --source . --verbose

# Add pre-commit hook
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
EOF
```

**Task 1.4.2: Dependency Vulnerability Scanning**
**Tools**:
- Safety (Python dependencies)
- pip-audit (Python packages)
- Dependabot (GitHub)

```bash
# Scan dependencies
safety check --json
pip-audit --format json

# Create vulnerability report
python scripts/security_audit.py
```

**Task 1.4.3: Environment Variable Security**
**File**: `app/core/config_secrets.py`

```python
# Ensure no secrets in code
# Validate all secrets loaded from env
# Add secrets rotation mechanism

class SecureConfig:
    def __init__(self):
        self._validate_secrets()
    
    def _validate_secrets(self):
        required = ['JWT_SECRET_KEY', 'DATABASE_URL', 'PAYSTACK_SECRET_KEY']
        for secret in required:
            if not os.getenv(secret):
                raise ValueError(f"Missing required secret: {secret}")
```

**Tests**: `tests/security/test_secrets_management.py` (10 tests)

---

### Phase 1.5: Security Testing & Reporting (2 days)

**Task 1.5.1: Automated Security Scans**
**File**: `.github/workflows/security.yml`

```yaml
name: Security Scan
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Bandit
        run: bandit -r app/ -f json -o bandit-report.json
      
      - name: Run Safety
        run: safety check --json
      
      - name: Run GitLeaks
        run: gitleaks detect --source . --verbose
      
      - name: Upload Reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: |
            bandit-report.json
            safety-report.json
```

**Task 1.5.2: Security Test Suite**
**Files**: `tests/security/test_security_complete.py`

```python
# Comprehensive security test suite
- SQL injection tests (20)
- XSS tests (15)
- CSRF tests (10)
- Auth bypass tests (12)
- Path traversal tests (8)
- Input validation tests (25)

Total: 90+ security tests
```

**Task 1.5.3: Security Documentation**
**File**: `docs/SECURITY_COMPLIANCE.md`

- OWASP Top 10 compliance checklist
- Security testing procedures
- Incident response plan
- Vulnerability disclosure policy

---

## 🧪 Part 2: Test Infrastructure (1.5 weeks)

### Phase 2.1: Integration Test Setup (3 days)

**Task 2.1.1: PostgreSQL Test Database**
**File**: `tests/conftest.py`

```python
import pytest
from sqlalchemy import create_engine
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:15") as postgres:
        yield postgres

@pytest.fixture(scope="session")
def test_db_engine(postgres_container):
    engine = create_engine(postgres_container.get_connection_url())
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()
```

**Tests**: `tests/integration/test_database_operations.py` (15 tests)

**Task 2.1.2: Redis Test Instance**
**File**: `tests/conftest.py`

```python
from testcontainers.redis import RedisContainer

@pytest.fixture(scope="session")
def redis_container():
    with RedisContainer("redis:7") as redis:
        yield redis

@pytest.fixture
def test_redis(redis_container):
    client = redis.Redis.from_url(redis_container.get_connection_url())
    yield client
    client.flushall()
```

**Tests**: `tests/integration/test_redis_operations.py` (12 tests)

**Task 2.1.3: External API Mocking**
**File**: `tests/mocks/external_apis.py`

```python
from unittest.mock import Mock, patch
import responses

@pytest.fixture
def mock_textverified():
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.POST,
            "https://api.textverified.com/purchase",
            json={"success": True, "number": "+1234567890"},
            status=200
        )
        yield rsps

@pytest.fixture
def mock_paystack():
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.POST,
            "https://api.paystack.co/transaction/initialize",
            json={"status": True, "data": {"reference": "test_ref"}},
            status=200
        )
        yield rsps
```

**Tests**: `tests/integration/test_external_api_mocks.py` (10 tests)

---

### Phase 2.2: Test Fixtures & Factories (2 days)

**Task 2.2.1: Model Factories**
**File**: `tests/factories.py`

```python
import factory
from app.models import User, Transaction, Verification

class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = None
    
    id = factory.Faker('uuid4')
    email = factory.Faker('email')
    username = factory.Faker('user_name')
    credits = 100.0
    tier = "freemium"

class TransactionFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Transaction
        sqlalchemy_session = None
    
    user_id = factory.LazyAttribute(lambda o: UserFactory().id)
    amount = 10.0
    type = "credit"
    status = "completed"
```

**Task 2.2.2: Test Data Generators**
**File**: `tests/generators.py`

```python
def generate_test_users(count: int = 10):
    return [UserFactory() for _ in range(count)]

def generate_test_transactions(user_id: str, count: int = 5):
    return [TransactionFactory(user_id=user_id) for _ in range(count)]
```

---

### Phase 2.3: CI/CD Integration (2 days)

**Task 2.3.1: GitHub Actions Workflow**
**File**: `.github/workflows/tests.yml`

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=app --cov-report=xml
      
      - name: Run integration tests
        run: pytest tests/integration/ -v
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/test
          REDIS_URL: redis://localhost:6379
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

**Task 2.3.2: Test Coverage Reporting**
**File**: `.coveragerc`

```ini
[run]
source = app
omit = 
    */tests/*
    */migrations/*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
```

---

## 🎭 Part 3: E2E Testing (1 week)

### Phase 3.1: E2E Test Setup (2 days)

**Task 3.1.1: Playwright Setup**
**File**: `tests/e2e/conftest.py`

```python
import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()

@pytest.fixture
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()
```

**Task 3.1.2: Test Utilities**
**File**: `tests/e2e/utils.py`

```python
def login_user(page, email: str, password: str):
    page.goto("http://localhost:8000/login")
    page.fill('input[name="email"]', email)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_url("**/dashboard")

def create_verification(page, service: str, country: str):
    page.goto("http://localhost:8000/verify")
    page.select_option('select[name="service"]', service)
    page.select_option('select[name="country"]', country)
    page.click('button[type="submit"]')
```

---

### Phase 3.2: Critical User Journeys (3 days)

**Task 3.2.1: Registration & Login Flow**
**File**: `tests/e2e/test_auth_journey.py`

```python
def test_user_registration_flow(page):
    # Navigate to registration
    # Fill form
    # Submit
    # Verify email sent
    # Verify redirect to dashboard

def test_login_flow(page):
    # Navigate to login
    # Enter credentials
    # Submit
    # Verify dashboard loads

def test_password_reset_flow(page):
    # Request password reset
    # Check email
    # Reset password
    # Login with new password
```

**Tests**: 8 E2E tests

**Task 3.2.2: Payment Flow**
**File**: `tests/e2e/test_payment_journey.py`

```python
def test_add_credits_flow(page):
    login_user(page, "test@example.com", "password")
    # Navigate to wallet
    # Click add credits
    # Enter amount
    # Initialize payment
    # Mock Paystack redirect
    # Verify credits added

def test_payment_failure_flow(page):
    # Simulate payment failure
    # Verify error message
    # Verify no credits added
```

**Tests**: 6 E2E tests

**Task 3.2.3: Verification Flow**
**File**: `tests/e2e/test_verification_journey.py`

```python
def test_create_verification_flow(page):
    login_user(page, "test@example.com", "password")
    # Navigate to verify
    # Select service
    # Select country
    # Purchase number
    # Verify number displayed
    # Check for SMS
    # Verify code received

def test_verification_timeout_flow(page):
    # Create verification
    # Wait for timeout
    # Verify refund processed
```

**Tests**: 10 E2E tests

---

### Phase 3.3: Smoke Test Suite (2 days)

**Task 3.3.1: Critical Path Smoke Tests**
**File**: `tests/e2e/test_smoke.py`

```python
@pytest.mark.smoke
def test_homepage_loads(page):
    page.goto("http://localhost:8000")
    assert page.title() == "Namaskah - SMS Verification"

@pytest.mark.smoke
def test_api_health(page):
    response = page.request.get("http://localhost:8000/health")
    assert response.status == 200

@pytest.mark.smoke
def test_login_works(page):
    login_user(page, "test@example.com", "password")
    assert "dashboard" in page.url

@pytest.mark.smoke
def test_payment_initialize_works(page):
    # Quick payment initialization test
    pass
```

**Tests**: 15 smoke tests (run on every deploy)

**Task 3.3.2: CI/CD Integration**
**File**: `.github/workflows/e2e.yml`

```yaml
name: E2E Tests
on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Playwright
        run: |
          pip install playwright
          playwright install chromium
      
      - name: Start application
        run: |
          uvicorn main:app --host 0.0.0.0 --port 8000 &
          sleep 10
      
      - name: Run smoke tests
        run: pytest tests/e2e/ -m smoke -v
      
      - name: Run full E2E suite
        run: pytest tests/e2e/ -v
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
```

---

## ✅ Success Criteria

### Security
- [ ] Zero high/critical vulnerabilities (Bandit, Safety)
- [ ] All OWASP Top 10 addressed
- [ ] 90+ security tests passing
- [ ] Secrets scanning in CI/CD
- [ ] Security documentation complete

### Testing
- [ ] PostgreSQL integration tests enabled
- [ ] Redis integration tests enabled
- [ ] External APIs mocked
- [ ] Test coverage: 81.48% → 90%+
- [ ] 150+ new tests added

### E2E
- [ ] 24+ E2E tests covering critical journeys
- [ ] 15 smoke tests running on every deploy
- [ ] E2E tests in CI/CD
- [ ] All critical user flows validated

---

## 📊 Timeline

| Part | Duration | Tests Added |
|------|----------|-------------|
| Security Hardening | 2 weeks | 90+ |
| Test Infrastructure | 1.5 weeks | 37+ |
| E2E Testing | 1 week | 24+ |
| **Total** | **4.5 weeks** | **151+** |

**Parallel Execution**: Can run alongside PAYMENT_HARDENING_ROADMAP.md

---

## 🔗 Dependencies

- PAYMENT_HARDENING_ROADMAP.md (can run in parallel)
- Docker (for testcontainers)
- Playwright (for E2E tests)
- GitHub Actions (for CI/CD)

---

**Last Updated**: January 2026  
**Owner**: QA & Security Teams  
**Reviewer**: DevOps Team
