# CI/CD Workflow Documentation

## Overview
This document describes the CI/CD pipeline for Namaskah SMS Platform.

**Last Updated**: 2026-01-31  
**Status**: ✅ Fully Implemented  
**Maturity Score**: 9/10 (Target: 10/10)

## Workflow Jobs

### 1. Test Suite ✅
- **Runs on**: Python 3.9, 3.11 (matrix)
- **Coverage**: 40% minimum (increasing to 70%)
- **Timeout**: 30 minutes
- **Triggers**: Push to main/develop, Pull requests
- **Artifacts**: Coverage reports (XML, HTML)

**What it does**:
- Installs dependencies with caching
- Runs unit tests with pytest
- Generates coverage reports
- Uploads to Codecov
- Fails if coverage < 40%

### 2. Code Quality (Lint) ✅
- **Tools**: Black, isort, Flake8, Mypy
- **Enforcement**: All checks must pass (hard failures)
- **Timeout**: 15 minutes

**What it does**:
- Black: Code formatting (line length 120)
- isort: Import sorting
- Flake8: Linting with specific ignores
- Mypy: Type checking (now enforced!)

### 3. Integration Tests ✅ NEW
- **Services**: PostgreSQL 15, Redis 7
- **Timeout**: 20 minutes
- **Fail Fast**: Stops on first failure

**What it does**:
- Spins up real PostgreSQL and Redis
- Runs integration tests (if they exist)
- Tests database operations
- Tests caching layer
- Validates service connectivity

### 4. Migration Testing ✅ NEW
- **Service**: PostgreSQL 15
- **Timeout**: 15 minutes

**What it does**:
- Tests forward migration (upgrade head)
- Tests rollback (downgrade -1)
- Tests idempotency (upgrade twice)
- Validates schema changes

### 5. Security Scan ✅ HARDENED
- **Tools**: Safety, Bandit, pip-audit
- **Enforcement**: Hard failures (no continue-on-error)
- **Severity**: MEDIUM+ blocked
- **Timeout**: 20 minutes

**What it does**:
- Safety: Checks for known vulnerabilities in dependencies
- Bandit: Scans Python code for security issues
- pip-audit: Audits Python packages
- Uploads security reports as artifacts

### 6. Container Security Scan ✅ NEW
- **Tool**: Trivy
- **Severity**: HIGH, CRITICAL
- **Timeout**: 15 minutes

**What it does**:
- Builds Docker image
- Scans for vulnerabilities
- Uploads results to GitHub Security
- Fails on HIGH/CRITICAL vulnerabilities

### 7. Secrets Scanning ✅ NEW
- **Tool**: Gitleaks
- **Scope**: Full git history
- **Timeout**: 10 minutes

**What it does**:
- Scans entire git history
- Detects leaked credentials
- Uses gitleaks.toml configuration
- Blocks on secrets found

### 8. CodeQL Analysis ✅
- **Languages**: Python, JavaScript/TypeScript
- **Schedule**: Weekly (Saturday 19:35 UTC)
- **Triggers**: Push to main, Pull requests

**What it does**:
- Static code analysis
- Security vulnerability detection
- Code quality checks
- Uploads to GitHub Security

## Deployment Flow

### Production Deployment ✅
- **Trigger**: Push to `main` branch
- **Requirements**: All jobs must pass
  - test (Python 3.9 & 3.11)
  - lint
  - integration
  - migration-test
  - security
  - container-scan
  - secrets-scan
- **Environment**: production
- **URL**: https://namaskah.app

**Steps**:
1. Deploy via Render webhook
2. Wait for deployment (60s)
3. Health check with 5 retries (10s interval)
4. Smoke test critical endpoints:
   - `/health`
   - `/api/v1/health`
   - `/api/diagnostics`
5. Notify on success/failure
6. Auto-rollback on failure (if webhook configured)

### Staging Deployment 🚧
- **Status**: Planned (not yet implemented)
- **Trigger**: Push to `develop` branch
- **See**: Task 3.3 in CI_HARDENING_TASKS_V2.md

## Branch Protection

### Required Status Checks
- ✅ test (Python 3.9)
- ✅ test (Python 3.11)
- ✅ lint
- ✅ integration
- ✅ migration-test
- ✅ security
- ✅ container-scan
- ✅ secrets-scan

### Configuration (Manual Setup Required)
Go to: Repository Settings → Branches → Add rule

**For `main` branch**:
- [x] Require pull request reviews (1 approval minimum)
- [x] Require status checks to pass
- [x] Require branches to be up to date
- [x] Require conversation resolution
- [x] Include administrators (recommended)
- [x] Require signed commits (optional)

## Secrets Required

### GitHub Secrets
- `RENDER_DEPLOY_HOOK` - Production deployment webhook
- `RENDER_ROLLBACK_HOOK` - Production rollback webhook
- `STAGING_DEPLOY_HOOK` - Staging deployment webhook
- `CODECOV_TOKEN` - Code coverage reporting

## Monitoring

All jobs report metrics:
- Build duration
- Test coverage
- Error rates
- Performance metrics

## Rollback Procedure

Automatic rollback triggers on:
1. Health check failure (5 attempts)
2. Smoke test failure
3. Any deployment step failure

Manual rollback:
```bash
curl -X POST $RENDER_ROLLBACK_HOOK
```

## Performance Baselines

| Metric | Threshold |
|--------|-----------|
| p95 Response Time | < 500ms |
| Error Rate | < 5% |
| Test Coverage | ≥ 70% |
| Security Issues | 0 HIGH/CRITICAL |

## Maintenance

### Weekly
- Dependabot PRs reviewed
- Security updates applied

### Monthly
- Performance baseline review
- CI/CD metrics analysis

## Troubleshooting

### Build Failures
1. Check job logs in GitHub Actions
2. Run tests locally: `pytest tests/unit/ -v`
3. Check coverage: `pytest --cov=app --cov-report=html`

### Deployment Failures
1. Check health endpoint: `curl https://namaskah.app/health`
2. Review deployment logs in Render
3. Trigger manual rollback if needed

### Performance Issues
1. Review Locust reports
2. Check `scripts/check_performance_thresholds.py` output
3. Analyze slow endpoints

## Contact

For CI/CD issues, contact the DevOps team.


## Secrets Required

### GitHub Secrets (Repository Settings → Secrets)
- `RENDER_DEPLOY_HOOK` - Production deployment webhook URL
- `RENDER_ROLLBACK_HOOK` - Production rollback webhook URL (optional)
- `STAGING_DEPLOY_HOOK` - Staging deployment webhook URL (planned)
- `CODECOV_TOKEN` - Codecov upload token (optional)
- `GITHUB_TOKEN` - Automatically provided by GitHub Actions

### How to Configure
1. Go to Repository Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add each secret with its value
4. Secrets are encrypted and not visible after creation

## Local Development

### Run CI Checks Locally
```bash
# Run all checks
./scripts/run_ci_checks.sh

# Run specific checks
black --check app/ tests/
pytest tests/unit/ --cov=app
bandit -r app/ -ll
```

### Pre-commit Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Monitoring and Metrics

### Build Metrics
- Average build duration: ~12-15 minutes
- Success rate target: > 95%
- Coverage trend: Increasing to 70%

### Artifacts
All builds generate artifacts:
- Test coverage reports (HTML, XML)
- Security scan reports (JSON, SARIF)
- Container scan results (SARIF)

**Retention**: 30 days

## Troubleshooting

### Build Failures

**Test failures**:
```bash
# Run tests locally
pytest tests/unit/ -v --cov=app

# Check specific test
pytest tests/unit/test_file.py::test_name -v
```

**Coverage below threshold**:
```bash
# Generate coverage report
pytest tests/unit/ --cov=app --cov-report=html

# Open htmlcov/index.html to see uncovered lines
```

**Linting failures**:
```bash
# Auto-fix formatting
black app/ tests/
isort app/ tests/

# Check what would change
black --check app/ tests/
```

**Type errors**:
```bash
# Run mypy locally
mypy app/ --ignore-missing-imports

# Add type hints or use type: ignore
```

**Security issues**:
```bash
# Check security locally
bandit -r app/ -ll

# Update vulnerable dependencies
pip install --upgrade package-name
```

**Container scan failures**:
```bash
# Build and scan locally
docker build -t namaskah:test .
docker run --rm aquasec/trivy image namaskah:test
```

### Deployment Failures

**Health check failed**:
1. Check Render logs for errors
2. Verify database migrations ran
3. Check environment variables
4. Test endpoints manually

**Rollback needed**:
```bash
# Manual rollback (if webhook configured)
curl -X POST $RENDER_ROLLBACK_HOOK
```

## Performance Baselines

| Metric | Current | Target |
|--------|---------|--------|
| Build Duration | ~12 min | < 15 min |
| Test Coverage | 40% | 70% |
| Security Issues | 0 HIGH/CRITICAL | 0 |
| Deployment Success | ~95% | > 99% |

## Roadmap

### ✅ Completed (Score: 9/10)
- [x] Remove security soft failures
- [x] Add container scanning
- [x] Add secrets scanning
- [x] Add integration tests
- [x] Add migration tests
- [x] Increase coverage to 40%
- [x] Create local validation script
- [x] Update documentation

### 🚧 In Progress (Target: 10/10)
- [ ] Increase coverage to 70%
- [ ] Add E2E tests with Playwright
- [ ] Add performance tests with Locust
- [ ] Add API contract tests
- [ ] Add staging environment
- [ ] Enable branch protection

### 📅 Planned
- [ ] Add monitoring integration
- [ ] Add build caching optimization
- [ ] Add parallel test execution
- [ ] Add dependency review action

## Maintenance

### Weekly
- Review Dependabot PRs
- Check security scan results
- Monitor build success rate

### Monthly
- Review coverage trends
- Update dependencies
- Review CI/CD metrics
- Optimize build times

## Contact

For CI/CD issues:
- Check this documentation first
- Review GitHub Actions logs
- Run checks locally with `./scripts/run_ci_checks.sh`
- Contact DevOps team

## Changelog

### 2026-01-31 - Major Update
- ✅ Removed all `continue-on-error` from security checks
- ✅ Added container scanning with Trivy
- ✅ Added secrets scanning with Gitleaks
- ✅ Added integration tests job
- ✅ Added migration testing job
- ✅ Increased coverage threshold to 40%
- ✅ Created local CI validation script
- ✅ Updated documentation to match reality
- ✅ Added CODEOWNERS file

### Previous
- See `.github/archive/CI_HARDENING_TASKS.md` for history

---

**Documentation Version**: 2.0  
**Last Updated**: 2026-01-31  
**Next Review**: After reaching 70% coverage
