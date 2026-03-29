# CI Pipeline - Minimal & Reliable

**Status**: Simplified for stability  
**Performance**: ~3-4 minutes  
**Philosophy**: Block only on critical failures

---

## Pipeline Overview

### Three-Stage Approach

```
Stage 1: Fast Checks (1 min)
├── secrets-scan (gitleaks)
└── code-quality (black, flake8, isort)
    ↓
Stage 2: Unit Tests (2-3 min) — BLOCKING
└── tests (pytest with coverage ≥42%)
    ↓
Stage 3: E2E Tests (optional, non-blocking, main only)
└── e2e-tests (pytest-playwright async)
```

### What Blocks Deployment
- ✅ **Secrets Detection** - No hardcoded credentials
- ✅ **Code Quality** - Black formatting, isort imports, flake8 syntax
- ✅ **Unit Tests** - Coverage ≥42%, all tests pass

### What Doesn't Block
- ❌ **E2E Tests** - Non-blocking, informational only
- ❌ **Accessibility Audit** - Removed (too flaky)
- ❌ **Database Backup** - Removed (separate concern)
- ❌ **Security Scan** - Removed (bandit/safety/semgrep too noisy)

---

## Why This Approach?

### The Problem with Complex CI
- 10+ minute runs = slow feedback loop
- Multiple stages = multiple failure points
- E2E tests = flaky, environment-dependent
- Accessibility audits = false positives
- Security scans = too many low-severity findings

### The Solution
- **Minimal blocking checks** - Only what matters for deployment
- **Fast feedback** - 3-4 minutes instead of 10+
- **Reliable** - No flaky tests blocking PRs
- **Maintainable** - Simple to debug when it fails

---

## Configuration

### `.github/workflows/ci.yml`
- 3 jobs: secrets-scan, code-quality, tests
- E2E tests optional (non-blocking)
- All jobs run in parallel where possible
- Dependencies: fast checks → unit tests → E2E

### `pytest.ini`
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
timeout = 30
```

### `tests/e2e/conftest.py`
Async fixtures for browser, page, base_url, test_user.

---

## Running Tests Locally

### Unit Tests
```bash
pytest tests/unit/ -v --cov=app --cov-fail-under=42
```

### E2E Tests
```bash
# Start app
TESTING=1 uvicorn main:app --host 0.0.0.0 --port 8000

# Run tests
pytest tests/e2e/ -v
```

---

## Troubleshooting

### Tests Failing Locally but Passing in CI
- Ensure `TESTING=1` environment variable is set
- Check database is initialized: `psql -U postgres -c "CREATE DATABASE namaskah_test;"`
- Verify Redis is running: `redis-cli ping`

### CI Taking Too Long
- Check if E2E tests are running (they're non-blocking, so shouldn't block deployment)
- Verify no large files are being uploaded as artifacts

### Secrets Detection Failing
- Run `gitleaks detect --source . --config tools/gitleaks.toml` locally
- Update `tools/gitleaks.toml` allowlist if needed

---

## Future Improvements

1. **Add pre-commit hooks** - Catch formatting issues before push
2. **Cache dependencies** - Speed up pip install
3. **Parallel jobs** - Run secrets-scan and code-quality in parallel
4. **Conditional E2E** - Only run E2E if frontend code changed
5. **Scheduled security scans** - Run bandit/safety on schedule, not on every push

---

## Philosophy

> **Simple > Complex**  
> **Reliable > Comprehensive**  
> **Fast Feedback > Perfect Coverage**

This CI pipeline prioritizes developer experience and deployment reliability over exhaustive checks. The goal is to catch real problems (secrets, syntax, test failures) while staying out of the way.
