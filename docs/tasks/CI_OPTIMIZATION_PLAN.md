# CI Optimization Plan - Faster Scans

**Date**: April 23, 2026  
**Current Build Time**: ~18 minutes (7 min blocking, 16 min E2E)  
**Target Build Time**: ~4-5 minutes (blocking stages)  
**Potential Savings**: 40-60% faster

---

## 📊 Current Timing Breakdown

### Actual Timings (Run 24831115827)
```
Stage 1: Fast Checks (Parallel)
├── Secrets Detection:  8s  (10:50:24 → 10:50:32)
└── Code Quality:      16s  (10:50:24 → 10:50:40)

Stage 2: Unit Tests (Blocking)
└── Unit Tests:       110s  (10:50:43 → 10:52:33)
    ├── Setup:         ~30s  (checkout, deps, postgres)
    ├── Migrations:    ~10s  (alembic upgrade head)
    └── Tests:         ~70s  (1,542 tests)

Stage 3: E2E Tests (Non-blocking)
└── E2E Tests:        977s  (10:52:38 → 11:08:55) ~16 min
    ├── Setup:        ~120s  (deps, playwright, app start)
    └── Tests:        ~857s  (browser tests)

Total Blocking Time: ~134s (2m 14s)
Total Pipeline Time: ~1,111s (18m 31s)
```

---

## 🎯 Optimization Opportunities

### **High Impact** (Save 40-60s)

#### 1. Parallel Test Execution ⚡
**Current**: Sequential test execution  
**Improvement**: Run tests in parallel with pytest-xdist  
**Savings**: 40-50s (40-70% faster)

```yaml
- name: Run unit tests
  run: |
    pytest tests/unit/ -n auto \
      --cov=app \
      --cov-report=xml \
      --cov-fail-under=30 \
      --tb=short \
      --maxfail=5
```

**Impact**:
- 1,542 tests across 4 workers
- ~385 tests per worker
- Estimated time: 30-40s (from 70s)

#### 2. Cache Dependencies Aggressively 💾
**Current**: Partial pip caching  
**Improvement**: Cache everything (pip, apt, playwright)  
**Savings**: 15-20s

```yaml
- name: Cache PostgreSQL client
  uses: actions/cache@v4
  with:
    path: /usr/bin/psql
    key: ${{ runner.os }}-postgres-client-15

- name: Cache pip packages
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-

- name: Cache Playwright browsers
  uses: actions/cache@v4
  with:
    path: ~/.cache/ms-playwright
    key: ${{ runner.os }}-playwright-${{ hashFiles('**/requirements-test.txt') }}
```

**Impact**:
- PostgreSQL client: -5s
- Pip packages: -10s
- Playwright browsers: -60s (E2E only)

#### 3. Optimize Dependency Installation 📦
**Current**: Install all deps every time  
**Improvement**: Split into layers, cache wheels  
**Savings**: 10-15s

```yaml
- name: Install dependencies (cached)
  run: |
    # Only install PostgreSQL client if not cached
    if ! command -v psql &> /dev/null; then
      sudo apt-get update -qq
      sudo apt-get install -y -qq postgresql-client
    fi
    
    # Use pip cache and pre-built wheels
    pip install --upgrade pip wheel
    pip install -r requirements.txt --prefer-binary
    pip install -r requirements/requirements-test.txt --prefer-binary
```

**Impact**:
- apt-get update: -5s (skip if cached)
- pip install: -5s (use wheels)

---

### **Medium Impact** (Save 20-30s)

#### 4. Optimize Migration Execution 🗄️
**Current**: Run all migrations every time  
**Improvement**: Cache migrated DB schema  
**Savings**: 5-8s

```yaml
- name: Cache test database schema
  uses: actions/cache@v4
  with:
    path: /tmp/namaskah_test_schema.sql
    key: ${{ runner.os }}-db-schema-${{ hashFiles('alembic/versions/*.py') }}

- name: Initialize test database
  run: |
    if [ -f /tmp/namaskah_test_schema.sql ]; then
      echo "Restoring cached schema..."
      psql -h localhost -U postgres -d namaskah_test -f /tmp/namaskah_test_schema.sql
    else
      echo "Running migrations..."
      alembic upgrade head
      pg_dump -h localhost -U postgres -d namaskah_test --schema-only > /tmp/namaskah_test_schema.sql
    fi
```

**Impact**:
- First run: Same (10s)
- Subsequent runs: 2-3s (restore from cache)
- Average savings: 5-7s

#### 5. Reduce Test Verbosity 📝
**Current**: `-v` verbose output, full coverage report  
**Improvement**: Minimal output, summary only  
**Savings**: 3-5s

```yaml
- name: Run unit tests
  run: |
    pytest tests/unit/ -n auto \
      --quiet \
      --cov=app \
      --cov-report=term:skip-covered \
      --cov-fail-under=30 \
      --tb=line \
      --maxfail=5
```

**Impact**:
- Less I/O overhead
- Faster terminal rendering
- Cleaner logs

#### 6. Skip E2E on Non-Main Branches 🎯
**Current**: E2E runs on main only (already optimized)  
**Improvement**: Add PR label trigger  
**Savings**: 0s (already optimal)

```yaml
e2e-tests:
  if: |
    github.ref == 'refs/heads/main' || 
    contains(github.event.pull_request.labels.*.name, 'run-e2e')
```

**Impact**:
- Already optimized
- Optional: Add label-based trigger for PRs

---

### **Low Impact** (Save 5-10s)

#### 7. Optimize Code Quality Checks 🔍
**Current**: Sequential linting  
**Improvement**: Parallel linting  
**Savings**: 3-5s

```yaml
- name: Code quality checks
  run: |
    flake8 app/ --count --select=E9,F63,F7,F82 &
    black --check app/ --quiet &
    isort --check-only app/ --profile black --quiet &
    wait
```

**Impact**:
- Run all linters in parallel
- Fail fast on first error

#### 8. Use Faster GitHub Runners 💰
**Current**: ubuntu-latest (2-core)  
**Improvement**: ubuntu-latest-4-core or ubuntu-latest-8-core  
**Savings**: 10-20s (costs $0.008/min vs $0.008/min)

```yaml
jobs:
  tests:
    runs-on: ubuntu-latest-4-core  # 4 cores, 16GB RAM
```

**Impact**:
- 2x cores = ~40% faster tests
- Cost: +$0.016 per run (~$5/month for 300 runs)
- Worth it for faster feedback

#### 9. Optimize Secrets Scan 🔐
**Current**: Full repo scan with fetch-depth: 0  
**Improvement**: Scan only changed files  
**Savings**: 2-4s

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 2  # Only last 2 commits

- name: Run gitleaks
  run: |
    if [ "${{ github.event_name }}" == "pull_request" ]; then
      gitleaks detect --source . --log-opts="origin/${{ github.base_ref }}..HEAD"
    else
      gitleaks detect --source . --config tools/gitleaks.toml
    fi
```

**Impact**:
- PR scans: Only changed files
- Push scans: Full repo (safety)

---

## 🚀 Implementation Plan

### **Phase 1: Quick Wins** (30 min, 40-50s savings)

1. ✅ Add pytest-xdist for parallel tests
2. ✅ Add dependency caching
3. ✅ Optimize pip installation

**Expected Result**: 134s → 80-90s (40% faster)

### **Phase 2: Medium Optimizations** (1 hour, 20-30s savings)

4. ✅ Cache database schema
5. ✅ Reduce test verbosity
6. ✅ Parallel linting

**Expected Result**: 80-90s → 50-60s (25% faster)

### **Phase 3: Advanced** (2 hours, 10-20s savings)

7. ✅ Upgrade to 4-core runners
8. ✅ Optimize secrets scan
9. ✅ Fine-tune test selection

**Expected Result**: 50-60s → 35-45s (20% faster)

---

## 📊 Expected Improvements

### **Before Optimization**
```
Secrets Detection:    8s
Code Quality:        16s
Unit Tests:         110s (30s setup + 10s migrations + 70s tests)
E2E Tests:          977s (non-blocking)

Total Blocking:     134s (2m 14s)
Total Pipeline:   1,111s (18m 31s)
```

### **After Phase 1** (Quick Wins)
```
Secrets Detection:    8s
Code Quality:        16s
Unit Tests:          60s (20s setup + 5s migrations + 35s tests)
E2E Tests:          600s (non-blocking, cached playwright)

Total Blocking:      84s (1m 24s)  ⚡ 37% faster
Total Pipeline:     684s (11m 24s) ⚡ 38% faster
```

### **After Phase 2** (Medium)
```
Secrets Detection:    6s (optimized scan)
Code Quality:        12s (parallel linting)
Unit Tests:          50s (15s setup + 3s migrations + 32s tests)
E2E Tests:          600s (non-blocking)

Total Blocking:      68s (1m 8s)   ⚡ 49% faster
Total Pipeline:     668s (11m 8s)  ⚡ 40% faster
```

### **After Phase 3** (Advanced)
```
Secrets Detection:    6s
Code Quality:        12s
Unit Tests:          35s (10s setup + 2s migrations + 23s tests)
E2E Tests:          400s (non-blocking, 4-core)

Total Blocking:      53s (53s)     ⚡ 60% faster
Total Pipeline:     453s (7m 33s)  ⚡ 59% faster
```

---

## 💰 Cost Analysis

### **Current Cost** (2-core runners)
- Blocking time: 134s × $0.008/min = $0.018 per run
- Total time: 1,111s × $0.008/min = $0.148 per run
- Monthly (300 runs): $44.40

### **After Optimization** (4-core runners)
- Blocking time: 35s × $0.016/min = $0.009 per run
- Total time: 453s × $0.016/min = $0.121 per run
- Monthly (300 runs): $36.30

**Savings**: $8.10/month + 60% faster feedback!

---

## 🎯 Recommended Approach

### **Start with Phase 1** (Immediate, Free)

```yaml
# Add to tests job
- name: Install test dependencies
  run: |
    pip install pytest-xdist pytest-cov
    
- name: Run unit tests (parallel)
  run: |
    pytest tests/unit/ -n auto \
      --cov=app \
      --cov-report=xml \
      --cov-fail-under=30 \
      --tb=short \
      --maxfail=5
```

**Benefits**:
- 40% faster (110s → 60s)
- Zero cost
- 30 minutes to implement
- Immediate ROI

### **Then Phase 2** (1 hour, Free)

Add caching and optimize setup:

```yaml
- uses: actions/cache@v4
  with:
    path: |
      ~/.cache/pip
      ~/.cache/ms-playwright
    key: ${{ runner.os }}-deps-${{ hashFiles('**/requirements*.txt') }}
```

**Benefits**:
- Additional 15% faster
- Zero cost
- 1 hour to implement

### **Finally Phase 3** (Optional, $8/month savings)

Upgrade to 4-core runners if team needs faster feedback.

---

## 📋 Implementation Checklist

### Phase 1: Quick Wins ✅
- [ ] Install pytest-xdist
- [ ] Add parallel test execution (-n auto)
- [ ] Add pip caching
- [ ] Add PostgreSQL client caching
- [ ] Optimize pip install (--prefer-binary)
- [ ] Test locally
- [ ] Deploy to CI
- [ ] Verify 40% improvement

### Phase 2: Medium Optimizations
- [ ] Add database schema caching
- [ ] Reduce test verbosity (--quiet)
- [ ] Parallel linting
- [ ] Optimize secrets scan (changed files only)
- [ ] Test locally
- [ ] Deploy to CI
- [ ] Verify additional 15% improvement

### Phase 3: Advanced (Optional)
- [ ] Evaluate 4-core runner cost/benefit
- [ ] Upgrade runner if justified
- [ ] Fine-tune test selection
- [ ] Add test sharding if needed
- [ ] Monitor performance
- [ ] Verify 60% total improvement

---

## 🔍 Monitoring

### Key Metrics to Track
- **Blocking time**: Target <60s
- **Total time**: Target <8 minutes
- **Success rate**: Maintain 100%
- **Cost per run**: Target <$0.10
- **Developer feedback time**: Target <2 minutes

### Dashboard
```bash
# Check recent run times
gh run list --workflow=ci.yml --limit 10 --json conclusion,createdAt,updatedAt

# Average time
gh run list --workflow=ci.yml --limit 50 --json conclusion,createdAt,updatedAt | \
  jq '[.[] | select(.conclusion=="success")] | length'
```

---

## 💡 Additional Optimizations

### **Future Considerations**

1. **Test Sharding** (for 5,000+ tests)
   - Split tests across multiple jobs
   - Run in parallel
   - Merge coverage reports

2. **Selective Test Execution**
   - Run only tests affected by changes
   - Use pytest-testmon or pytest-picked
   - Fallback to full suite on main

3. **Pre-built Docker Images**
   - Cache entire test environment
   - Skip dependency installation
   - 90% faster setup

4. **Self-Hosted Runners**
   - Dedicated hardware
   - Persistent caching
   - 2-3x faster than GitHub runners
   - Cost: $50-100/month

---

## 🎯 Success Criteria

### **Phase 1 Success**
- ✅ Blocking time <90s (from 134s)
- ✅ Total time <12 minutes (from 18m)
- ✅ Zero cost increase
- ✅ 100% test success rate maintained

### **Phase 2 Success**
- ✅ Blocking time <70s
- ✅ Total time <11 minutes
- ✅ Zero cost increase
- ✅ Developer satisfaction improved

### **Phase 3 Success**
- ✅ Blocking time <60s
- ✅ Total time <8 minutes
- ✅ Cost neutral or reduced
- ✅ Team velocity increased

---

## 📝 Next Steps

1. **Immediate**: Implement Phase 1 (parallel tests)
2. **This Week**: Implement Phase 2 (caching)
3. **Next Sprint**: Evaluate Phase 3 (4-core runners)
4. **Ongoing**: Monitor and optimize

---

**Estimated Total Savings**: 60% faster (134s → 53s)  
**Implementation Time**: 2-3 hours  
**Cost Impact**: -$8/month (savings!)  
**ROI**: Immediate (faster feedback, happier developers)

---

**Ready to implement?** Start with Phase 1 for immediate 40% improvement! 🚀
