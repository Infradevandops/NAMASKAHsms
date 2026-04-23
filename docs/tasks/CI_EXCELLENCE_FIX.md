# CI Excellence Fix - Task Plan

**Date**: April 23, 2026  
**Priority**: 🟡 Medium  
**Effort**: 30 minutes  
**Impact**: High (100% CI health)

---

## 🎯 Objective

Fix the Activity schema mismatch to achieve 100% CI health and improve pipeline reliability.

---

## 🐛 Current Issue

**Error**:
```
foreign key constraint "activities_user_id_fkey" cannot be implemented
DETAIL: Key columns "user_id" and "id" are of incompatible types: 
  character varying and integer.
```

**Impact**:
- 3 tests failing in `test_activity_feed.py`
- CI success rate: 40% (should be >90%)
- Schema drift between test and production

**Root Cause**: 
- `Activity.user_id` is VARCHAR
- `User.id` in test DB is INTEGER
- `User.id` in production is VARCHAR (from BaseModel)
- Test DB schema doesn't match production

---

## ✅ Solution

### Option A: Verify BaseModel ID Type (RECOMMENDED)

**Action**: Ensure User.id uses VARCHAR consistently

**Steps**:
1. Check BaseModel.id type
2. Verify production User table schema
3. Update test DB to match production
4. Run migrations in CI

**Effort**: 15 minutes  
**Risk**: Low

### Option B: Fix Activity Model

**Action**: Update Activity.user_id to use Integer if User.id is Integer

**Steps**:
1. Check User.id actual type in production
2. Update Activity model FK type
3. Create migration
4. Test locally

**Effort**: 20 minutes  
**Risk**: Medium (requires migration)

---

## 📋 Implementation Plan

### Phase 1: Investigation (5 min)

**Task 1.1: Check BaseModel ID Type**
```bash
# Check BaseModel definition
grep -A 5 "class BaseModel" app/models/base.py

# Expected: id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
```

**Task 1.2: Check Production User Schema**
```bash
# Connect to production DB
psql $DATABASE_URL -c "\d users"

# Check id column type
# Expected: id | character varying | not null
```

**Task 1.3: Check Test DB Schema**
```bash
# Check test DB User table
psql postgresql://postgres:test_password@localhost:5432/namaskah_test -c "\d users"

# If id is integer, this is the problem
```

**Expected Finding**: Test DB has User.id as INTEGER, production has VARCHAR

---

### Phase 2: Fix Test Database (10 min)

**Task 2.1: Add Migration Step to CI**

Update `.github/workflows/ci.yml`:

```yaml
# In the tests job, after "Install dependencies"
- name: Initialize test database
  env:
    DATABASE_URL: postgresql://postgres:test_password@localhost:5432/namaskah_test
    REDIS_URL: redis://localhost:6379/0
    SECRET_KEY: test-secret-key-for-ci-only-min-32-chars-long
    JWT_SECRET_KEY: test-jwt-secret-key-for-ci-only-min-32-chars-long
    ENVIRONMENT: testing
  run: |
    # Create database if not exists
    psql -h localhost -U postgres -c "CREATE DATABASE namaskah_test;" 2>/dev/null || true
    
    # Run migrations to ensure schema matches production
    alembic upgrade head

- name: Run unit tests
  # ... existing test configuration
```

**Task 2.2: Update conftest.py**

Ensure test fixtures create tables properly:

```python
# tests/conftest.py
@pytest.fixture(scope="session")
def engine():
    """Create test database engine."""
    from app.core.database import Base
    from app.models import *  # Import all models
    
    engine = create_engine(TEST_DATABASE_URL)
    
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    
    # Create all tables with correct schema
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)
```

---

### Phase 3: Verify Fix (10 min)

**Task 3.1: Test Locally**
```bash
# Drop and recreate test DB
dropdb namaskah_test 2>/dev/null || true
createdb namaskah_test

# Run migrations
alembic upgrade head

# Run failing tests
pytest tests/unit/test_activity_feed.py::TestActivityEndpoints -v

# Expected: All tests pass
```

**Task 3.2: Run Full Test Suite**
```bash
# Run all unit tests
pytest tests/unit/ -v --maxfail=10

# Expected: 1,542 tests collected, all passing
```

**Task 3.3: Check Coverage**
```bash
# Run with coverage
pytest tests/unit/ --cov=app --cov-report=term-missing --cov-fail-under=30

# Expected: Coverage >30%, all tests pass
```

---

### Phase 4: Deploy Fix (5 min)

**Task 4.1: Commit Changes**
```bash
git add .github/workflows/ci.yml tests/conftest.py
git commit -m "fix: add migration step to CI for schema consistency

- Run alembic upgrade head before tests
- Ensures test DB schema matches production
- Fixes Activity.user_id FK constraint error
- Resolves 3 failing tests in test_activity_feed.py

Impact:
- CI success rate: 40% → 100%
- Test failures: 3 → 0
- Schema drift: eliminated

Closes #CI-001"
```

**Task 4.2: Push to Main**
```bash
git push origin main
```

**Task 4.3: Monitor CI**
```bash
# Watch GitHub Actions
gh run watch

# Or visit: https://github.com/yourusername/namaskah-sms/actions
```

---

## 🎯 Success Criteria

### Must Have
- [ ] All 1,542 tests collected
- [ ] All tests passing (0 failures)
- [ ] CI success rate >90%
- [ ] Schema consistency verified
- [ ] Migrations run in CI

### Nice to Have
- [ ] Coverage tracking enabled
- [ ] E2E tests more reliable
- [ ] Build time <10 minutes

---

## 📊 Expected Outcomes

### Before Fix
```
Test Collection:     ✅ 1,542 tests
Test Execution:      🟡 12 passed, 3 failed
CI Success Rate:     40% (2/5 runs)
Schema Consistency:  ❌ Test ≠ Production
Build Time:          ~6 minutes
```

### After Fix
```
Test Collection:     ✅ 1,542 tests
Test Execution:      ✅ 1,542 passed, 0 failed
CI Success Rate:     100% (5/5 runs)
Schema Consistency:  ✅ Test = Production
Build Time:          ~7 minutes (+1 min for migrations)
```

---

## 🚨 Rollback Plan

If fix causes issues:

```bash
# Revert CI changes
git revert HEAD

# Or restore previous workflow
git checkout HEAD~1 .github/workflows/ci.yml

# Push revert
git push origin main
```

**Risk**: Very low (only adds migration step, doesn't change logic)

---

## 📝 Additional Improvements (Optional)

### Improvement 1: Add Coverage Tracking (15 min)

```yaml
# Add to ci.yml after unit tests
- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v4
  with:
    file: ./coverage.xml
    fail_ci_if_error: false
    verbose: true
```

### Improvement 2: Cache Dependencies (10 min)

```yaml
# Add to ci.yml in tests job
- uses: actions/setup-python@v5
  with:
    python-version: ${{ env.PYTHON_VERSION }}
    cache: 'pip'
    cache-dependency-path: |
      requirements.txt
      requirements/requirements-test.txt
```

### Improvement 3: Parallel Test Execution (20 min)

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest tests/unit/ -n auto -v
```

---

## 🔍 Verification Checklist

### Pre-Deployment
- [ ] BaseModel.id type verified (VARCHAR)
- [ ] Production schema documented
- [ ] Test DB schema matches production
- [ ] Local tests passing
- [ ] Migration step added to CI

### Post-Deployment
- [ ] CI run successful
- [ ] All tests passing
- [ ] No new errors introduced
- [ ] Build time acceptable (<10 min)
- [ ] Coverage threshold met (>30%)

### Monitoring (24 hours)
- [ ] Next 5 CI runs successful
- [ ] No schema-related errors
- [ ] Test execution stable
- [ ] No performance degradation

---

## 📈 Metrics to Track

| Metric | Before | Target | After |
|--------|--------|--------|-------|
| Test Failures | 3 | 0 | TBD |
| CI Success Rate | 40% | >90% | TBD |
| Build Time | 6 min | <10 min | TBD |
| Schema Drift | Yes | No | TBD |
| Coverage | 30%+ | 30%+ | TBD |

---

## 🎯 Next Steps After Fix

1. **Monitor CI for 24 hours** - Ensure stability
2. **Add coverage tracking** - Track trends over time
3. **Improve E2E tests** - Reduce flakiness
4. **Add integration tests** - Test API endpoints
5. **Performance testing** - Add load tests

---

## 📚 Related Documentation

- `docs/tasks/CI_CIRCULAR_IMPORT_FIX.md` - Previous CI fix (v4.4.2)
- `docs/CURRENT_STATE.md` - Platform status
- `.github/workflows/ci.yml` - CI configuration
- `tests/conftest.py` - Test fixtures

---

## 💡 Key Insights

1. **Schema Drift Is Common** - Test and production DBs can diverge
2. **Migrations Are Critical** - Always run migrations in CI
3. **Fail Fast Is Good** - 3 failures caught early
4. **CI Design Is Solid** - Only minor fix needed

---

## ✅ Definition of Done

- [ ] Migration step added to CI workflow
- [ ] All 1,542 tests passing
- [ ] CI success rate >90% (next 5 runs)
- [ ] Schema consistency verified
- [ ] Documentation updated
- [ ] Team notified of fix

---

**Estimated Total Time**: 30 minutes  
**Risk Level**: Low  
**Impact**: High (100% CI health)  
**Priority**: Medium (not blocking production)

---

**Ready to Execute**: Yes  
**Blockers**: None  
**Dependencies**: None

---

## 🚀 Quick Start

```bash
# 1. Check current state
pytest tests/unit/test_activity_feed.py -v

# 2. Apply fix (update ci.yml)
# Add migration step before tests

# 3. Test locally
dropdb namaskah_test && createdb namaskah_test
alembic upgrade head
pytest tests/unit/ -v

# 4. Deploy
git add .github/workflows/ci.yml
git commit -m "fix: add migration step to CI"
git push origin main

# 5. Monitor
gh run watch
```

---

**Status**: Ready for implementation  
**Owner**: DevOps/Backend Team  
**Reviewer**: Tech Lead
