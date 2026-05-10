# Automated Testing for Area Code Feature

**Version**: v4.7.0
**Status**: Ready for Deployment
**Last Updated**: Current Session

---

## 🎯 Overview

Automated test suite that runs on deployment to verify area code tier gating functionality.

---

## 📦 Test Suite Components

### 1. Smoke Tests (`tests/smoke/test_area_code_smoke.py`)

**Purpose**: Quick validation after deployment

**Tests**:
1. ✅ Health Check - API is responding
2. ✅ PAYG Voice Fee - $0.25 charged correctly
3. ✅ Pro Voice Included - No fee charged
4. ✅ Freemium Blocked - Area code selection blocked
5. ✅ API Response Format - All required fields present

**Runtime**: ~2 minutes

**Usage**:
```bash
# Test staging
python3 tests/smoke/test_area_code_smoke.py --env staging

# Test production
python3 tests/smoke/test_area_code_smoke.py --env production

# Custom URL
python3 tests/smoke/test_area_code_smoke.py --url https://custom.url
```

---

### 2. Deployment Script (`scripts/deploy_area_code_feature.sh`)

**Purpose**: Automated deployment with testing

**Steps**:
1. Run pre-deployment checks (standalone tests)
2. Create backup
3. Deploy code
4. Wait for deployment
5. Run smoke tests
6. Verify health
7. Monitor for errors

**Usage**:
```bash
# Deploy to staging
./scripts/deploy_area_code_feature.sh staging

# Deploy to production (requires confirmation)
./scripts/deploy_area_code_feature.sh production
```

---

### 3. CI/CD Workflow (`.github/workflows/area_code_tests.yml`)

**Purpose**: Automated testing on every push

**Triggers**:
- Push to `main` or `staging` branch
- Pull requests to `main`
- Manual workflow dispatch

**Jobs**:
1. **Smoke Tests**: Run on staging and production
2. **Unit Tests**: Run standalone tests

**Notifications**: Slack alert on production failure

---

## 🚀 Deployment Process

### Staging Deployment

```bash
# 1. Run deployment script
./scripts/deploy_area_code_feature.sh staging

# 2. Script automatically:
#    - Runs standalone tests
#    - Deploys code
#    - Runs smoke tests
#    - Verifies health

# 3. Review results
cat smoke_test_results_staging_*.json
```

### Production Deployment

```bash
# 1. Ensure staging tests passed
cat smoke_test_results_staging_*.json

# 2. Run production deployment
./scripts/deploy_area_code_feature.sh production

# 3. Confirm deployment when prompted
# Type: yes

# 4. Monitor results
tail -f logs/app.log
```

---

## 📊 Test Results

### Success Criteria

**Smoke Tests**:
- ✅ All 5 tests passing
- ✅ 100% success rate
- ✅ No API errors

**Deployment**:
- ✅ Health check returns 200
- ✅ No errors in 60-second monitoring
- ✅ All endpoints responding

### Failure Handling

**If Smoke Tests Fail**:
1. Deployment script exits with error
2. Review test results JSON file
3. Check application logs
4. Consider rollback

**If Production Tests Fail**:
1. Slack notification sent
2. Immediate investigation required
3. Rollback if critical

---

## 🔧 Configuration

### Test Users

Configure in `tests/smoke/test_area_code_smoke.py`:

```python
test_users = {
    "freemium": {
        "email": "freemium@test.com",
        "password": "test123"
    },
    "payg": {
        "email": "payg@test.com",
        "password": "test123"
    },
    "pro": {
        "email": "pro@test.com",
        "password": "test123"
    },
    "custom": {
        "email": "custom@test.com",
        "password": "test123"
    }
}
```

### Environment URLs

```python
env_urls = {
    "production": "https://namaskah.app",
    "staging": "https://staging.namaskah.app",
    "local": "http://localhost:8000"
}
```

---

## 📝 Test Results Format

### JSON Output

```json
{
  "environment": "staging",
  "base_url": "https://staging.namaskah.app",
  "timestamp": "2026-05-08T12:00:00",
  "results": [
    {
      "test": "Health Check",
      "passed": true,
      "message": "✅ API health check passed"
    },
    {
      "test": "PAYG Voice Area Code Fee",
      "passed": true,
      "message": "✅ PAYG voice area code fee correct: $0.25"
    }
  ]
}
```

---

## 🎯 Quick Commands

### Run All Tests
```bash
# Standalone tests
python3 tests/standalone_area_code_test.py

# Smoke tests (staging)
python3 tests/smoke/test_area_code_smoke.py --env staging

# Smoke tests (production)
python3 tests/smoke/test_area_code_smoke.py --env production
```

### Deploy with Tests
```bash
# Staging
./scripts/deploy_area_code_feature.sh staging

# Production
./scripts/deploy_area_code_feature.sh production
```

### Check Results
```bash
# View latest results
cat smoke_test_results_*.json | jq

# Count passed tests
cat smoke_test_results_*.json | jq '.results | map(select(.passed)) | length'

# List failed tests
cat smoke_test_results_*.json | jq '.results | map(select(.passed == false))'
```

---

## 🚨 Troubleshooting

### Test Failures

**"Login failed"**:
- Check test user credentials
- Verify users exist in database
- Check authentication endpoint

**"API returned 500"**:
- Check application logs
- Verify database connection
- Check for deployment errors

**"Health check failed"**:
- Verify application is running
- Check network connectivity
- Review deployment status

### Deployment Issues

**"Standalone tests failed"**:
- Fix code issues before deploying
- Run tests locally first
- Check test implementation

**"Smoke tests failed on production"**:
- Review error messages
- Check production logs
- Consider immediate rollback

---

## ✅ Pre-Deployment Checklist

Before running deployment:

- [ ] All standalone tests passing locally
- [ ] Code reviewed and approved
- [ ] Test users created in target environment
- [ ] Backup created
- [ ] Rollback plan ready
- [ ] Monitoring dashboards open
- [ ] Team notified

---

## 📞 Support

### Documentation
- **Deployment Guide**: `AREA_CODE_DEPLOYMENT_READINESS.md`
- **Testing Guide**: `AREA_CODE_TESTING_GUIDE.md`
- **Quick Reference**: `AREA_CODE_QUICK_REFERENCE.md`

### Contacts
- **On-Call**: Check team schedule
- **Slack**: #deployments channel
- **Escalation**: Tech lead

---

**Last Updated**: Current Session
**Status**: ✅ Ready for Automated Deployment
