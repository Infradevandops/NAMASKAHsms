# CI Workflow Monitoring Guide

## 🔗 Quick Links

**GitHub Actions**: https://github.com/Infradevandops/NAMASKAHsms/actions
**CI Workflow**: https://github.com/Infradevandops/NAMASKAHsms/actions/workflows/ci.yml
**Latest Run**: https://github.com/Infradevandops/NAMASKAHsms/actions/workflows/ci.yml?query=branch%3Amain

## 📊 Expected Workflow Jobs

### ✅ Should Pass (if properly configured)
1. **Test Suite** - Unit tests with 70% coverage
2. **Code Quality** - Black, isort, Flake8, Mypy
3. **Security Scan** - Safety, Bandit, pip-audit
4. **Secrets Detection** - Gitleaks scan

### ⚠️ May Fail (needs configuration)
5. **Integration Tests** - Needs PostgreSQL + Redis setup
6. **E2E Smoke Tests** - Needs running application
7. **Migration Test** - Needs Alembic migrations
8. **Container Security** - Needs valid Dockerfile
9. **Performance Tests** - Needs running application
10. **API Contract Tests** - Needs OpenAPI spec at `docs/api_v2_spec.yaml`

### 🚀 Deployment (conditional)
11. **Deploy to Production** - Only on push to `main` with all checks passing

## 🔍 Monitoring Commands

### Check workflow status
```bash
# View in browser
open https://github.com/Infradevandops/NAMASKAHsms/actions

# Or use GitHub CLI (if authenticated)
gh run list --workflow=ci.yml --limit 5
gh run view --log
gh run watch
```

### View specific job logs
```bash
gh run view <run-id> --log --job=<job-name>
```

## 🐛 Troubleshooting Expected Failures

### Coverage Failure
**Error**: Coverage below 70%
**Fix**: Current coverage is 81%, should pass. If fails, check test execution.

### E2E Test Failure
**Error**: Cannot connect to application
**Fix**: E2E tests need app running. May need to start app in CI or mock endpoints.

### Performance Test Failure
**Error**: Cannot connect to localhost:8000
**Fix**: App needs to be running. Check if uvicorn starts successfully.

### Contract Test Failure
**Error**: OpenAPI spec not found
**Fix**: Ensure `docs/api_v2_spec.yaml` exists or update path in workflow.

### Migration Test Failure
**Error**: Alembic command fails
**Fix**: Check if `alembic.ini` is configured and migrations exist.

### Container Scan Failure
**Error**: Docker build fails
**Fix**: Ensure `Dockerfile` is valid and builds successfully.

## 📈 Success Indicators

### All Green ✅
- All 10 jobs pass
- Coverage ≥ 70%
- No security vulnerabilities
- No secrets detected
- All tests pass

### Partial Success ⚠️
- Core tests pass (test, lint, security)
- Some optional tests fail (E2E, performance)
- Action: Fix failing tests incrementally

### Complete Failure ❌
- Core tests fail
- Action: Review logs and fix immediately

## 🔧 Quick Fixes

### If tests fail locally
```bash
# Run tests
pytest tests/unit/ --cov=app --cov-branch --cov-fail-under=70 -v

# Run linting
black --check app/ tests/
flake8 app/
mypy app/ --ignore-missing-imports

# Run security scans
safety check
bandit -r app/ -ll
pip-audit
```

### If CI fails but local passes
- Check Python version (3.9 vs 3.11)
- Check dependencies in requirements.txt
- Check environment variables
- Review GitHub Actions logs

## 📝 Next Steps After First Run

1. **Review all job results**
2. **Fix critical failures** (test, lint, security)
3. **Configure optional tests** (E2E, performance)
4. **Enable branch protection** once stable
5. **Monitor for 2-3 runs** before enforcing

## 🎯 Success Criteria

Before enabling branch protection:
- [ ] Test suite passes consistently
- [ ] Lint checks pass
- [ ] Security scans pass
- [ ] No false positives
- [ ] Coverage stable at 70%+
- [ ] At least 3 successful runs

## 📞 Support

If workflow fails unexpectedly:
1. Check job logs in GitHub Actions
2. Review `.github/workflows/ci.yml`
3. Check `.github/WORKFLOW_DOCUMENTATION.md`
4. Review `.github/IMPLEMENTATION_SUMMARY.md`

---

**Last Updated**: 2026-01-18
**Commit**: 52b2ac8
**Status**: Monitoring first run
