# CI Pipeline Documentation

**Last Updated**: March 29, 2026  
**Status**: Optimized & Stable  
**Performance**: ~5-6 minutes (down from 10+ minutes)

---

## Pipeline Overview

### Current Architecture
Single consolidated pipeline with 6 sequential stages:

```
Stage 1: Fast Checks (2 min)
├── secrets-scan (gitleaks)
├── code-quality (black, flake8, isort)
└── security (bandit, safety, semgrep)
    ↓
Stage 2: Unit Tests (3-4 min)
└── tests (pytest with coverage ≥42%)
    ↓
Stage 3: E2E Tests (2-3 min, main only)
└── e2e-tests (pytest-playwright async)
    ↓
Stage 4: Accessibility (2-3 min, main/schedule only)
└── accessibility-audit (axe, pa11y, lighthouse)
    ↓
Stage 5: Database Backup (1 min, main only)
└── db-backup (S3 backup)
    ↓
Stage 6: Deployment Readiness (main only)
└── deployment-readiness (validation)
```

### Key Optimizations
- **Sequential stages** with `needs:` dependencies (fail fast)
- **Conditional execution** (E2E/backup/accessibility only on main)
- **Consolidated workflows** (ci.yml + security-testing.yml merged)
- **Disabled redundant workflow** (security-testing.yml)

---

## E2E Test Fixes

### Fixture Scope Issue
**Problem**: Session-scoped async fixtures not supported by pytest-asyncio  
**Solution**: Changed `browser` fixture to function-scoped

```python
# Before (broken)
@pytest.fixture(scope="session")
async def browser():
    ...

# After (working)
@pytest.fixture
async def browser():
    ...
```

### Test Conversions
All E2E tests converted from sync to async Playwright API:
- `test_welcome_flow.py` - 11 tests
- `test_auth_flow.py` - 3 tests
- `test_verification_flow_v2.py` - 4 tests
- `test_critical_journeys.py` - Already async
- `test_critical_paths.py` - Already async
- `test_dashboard_pages.py` - Already async
- `test_verification_flow.py` - Already async

### Configuration
- **pytest.ini**: `asyncio_mode = auto`
- **conftest.py**: Async fixtures with proper scopes
- **Workflow env**: `TESTING=1` flag skips non-critical tasks

---

## Performance Breakdown

### Before Optimization
```
ci.yml (parallel)                    ~8 min
security-testing.yml (parallel)      ~8 min
Total (parallel overhead)            ~10+ min
```

### After Optimization
```
Stage 1: Fast checks                 ~2 min
Stage 2: Unit tests                  ~3-4 min
Stage 3: E2E tests (main only)       ~2-3 min
Stage 4: Accessibility (main only)   ~2-3 min
Stage 5: Backup (main only)          ~1 min
Total (sequential)                   ~5-6 min
```

**Savings**: 40-50% reduction in CI time

---

## Configuration Files

### `.github/workflows/ci.yml`
Main consolidated pipeline with all 6 stages and job dependencies.

### `.github/workflows/security-testing.yml`
Disabled (consolidated into ci.yml).

### `pytest.ini`
```ini
[pytest]
asyncio_mode = auto
markers =
    asyncio: marks tests as async
    e2e: marks tests as end-to-end
    smoke: marks tests as smoke tests
testpaths = tests
timeout = 30
```

### `tests/e2e/conftest.py`
Async fixtures for browser, page, base_url, test_user, test_timeout.

---

## Running Tests Locally

### E2E Tests
```bash
# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-playwright

# Install Playwright browsers
playwright install chromium

# Start app
TESTING=1 uvicorn main:app --host 0.0.0.0 --port 8000

# Run E2E tests
pytest tests/e2e/ -v

# Run specific test file
pytest tests/e2e/test_welcome_flow.py -v

# Run with markers
pytest tests/e2e/ -m smoke -v
```

### Unit Tests
```bash
pytest tests/unit/ -v --cov=app --cov-fail-under=42
```

---

## Troubleshooting

### E2E Tests Failing with Fixture Errors
**Error**: `requested an async fixture 'browser' with no plugin or hook`  
**Fix**: Ensure `pytest.ini` has `asyncio_mode = auto` and all tests use `@pytest.mark.asyncio`

### App Startup Timeout in CI
**Error**: `Timeout 15000ms exceeded waiting for navigation`  
**Fix**: Ensure `TESTING=1` is set in workflow to skip non-critical initialization

### CSP Header Blocking Tests
**Error**: `EvalError: Evaluating a string as JavaScript violates CSP`  
**Fix**: CSP header automatically allows `unsafe-eval` in test environment

### Playwright Sync API Error
**Error**: `It looks like you are using Playwright Sync API inside the asyncio loop`  
**Fix**: Use async API (`from playwright.async_api import ...`) and `await` all calls

---

## Future Improvements

1. **Caching**: Add pip cache for faster dependency installation
2. **Parallel stages**: Run stages 3-5 in parallel (they're independent)
3. **Matrix testing**: Test against multiple Python versions
4. **Artifact caching**: Cache Playwright browsers between runs
5. **Conditional E2E**: Only run E2E tests if frontend code changed

---

## References

- [Workflow file](/.github/workflows/ci.yml)
- [pytest-asyncio docs](https://pytest-asyncio.readthedocs.io/)
- [Playwright async API](https://playwright.dev/python/docs/api/class-browser)
- [GitHub Actions syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
