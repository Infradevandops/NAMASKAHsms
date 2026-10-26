# Security Setup Guide

## Quick Start

### 1. Install Pre-commit Hooks

```bash
# Install pre-commit framework
pip install pre-commit

# Install the git hooks
pre-commit install

# (Optional) Run against all files to verify setup
pre-commit run --all-files
```

### 2. Verify Installation

```bash
# Check that hooks are installed
ls -la .git/hooks/pre-commit

# Test by creating a dummy secret file
echo "FAKE_TOKEN=sk_test_123456789" > .env.test
git add .env.test

# This should fail with gitleaks error
git commit -m "test" 2>&1 | grep -i "gitleaks\|secret" && echo "✅ Hooks working!" || echo "❌ Hooks not working"

# Clean up
git reset .env.test
rm .env.test
```

### 3. Install Additional Security Tools

```bash
# Install gitleaks for manual scanning
brew install gitleaks  # macOS
# or
apt-get install gitleaks  # Linux

# Install git-filter-repo for history cleaning
pip install git-filter-repo

# Install BFG Repo-Cleaner (alternative)
brew install bfg  # macOS
```

## Usage

### Pre-commit Hooks

Hooks run automatically before each commit. To bypass (not recommended):

```bash
git commit --no-verify  # Skip all hooks
```

### Manual Secret Scanning

```bash
# Scan current repository
gitleaks detect --source . --verbose

# Scan git history
gitleaks detect --source . --verbose --log-opts=--all

# Generate report
gitleaks detect --source . --report-path gitleaks-report.json
```

### Clean Git History (If Needed)

**⚠️ WARNING: This rewrites git history. Coordinate with team before pushing.**

```bash
# Option 1: Using git-filter-repo (recommended)
git filter-repo --invert-paths --path .env.production --path .env

# Option 2: Using BFG Repo-Cleaner
bfg --delete-files .env.production
bfg --delete-files .env

# Force push to remote (after verification)
git push origin --force --all
git push origin --force --tags
```

## Environment Variables

### Development

Create `.env` with development values:

```bash
cp config/.env.example .env
# Edit .env with your local development credentials
```

### Production

**NEVER commit `.env.production`**

Use CI/CD secrets management:

- **GitHub Actions**: Use repository secrets
- **GitLab CI**: Use CI/CD variables
- **Docker**: Use secrets or environment files
- **Kubernetes**: Use ConfigMaps and Secrets

Example GitHub Actions:

```yaml
env:
  DATABASE_URL: ${{ secrets.DATABASE_URL }}
  TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
  PAYSTACK_SECRET_KEY: ${{ secrets.PAYSTACK_SECRET_KEY }}
```

## Best Practices

### ✅ DO

- ✅ Use `.env.example` with placeholder values
- ✅ Store secrets in CI/CD platform
- ✅ Rotate credentials regularly
- ✅ Use strong, unique passwords
- ✅ Enable 2FA on all accounts
- ✅ Review `.gitignore` before commits
- ✅ Use pre-commit hooks
- ✅ Scan code regularly with gitleaks

### ❌ DON'T

- ❌ Commit `.env` files
- ❌ Hardcode credentials in code
- ❌ Share credentials via chat/email
- ❌ Use same password for multiple services
- ❌ Commit API keys or tokens
- ❌ Disable pre-commit hooks
- ❌ Push credentials to public repositories
- ❌ Store credentials in comments

## Troubleshooting

### Pre-commit hooks not running

```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install

# Check hook file permissions
chmod +x .git/hooks/pre-commit
```

### False positives in gitleaks

```bash
# Whitelist specific patterns in .gitignore
# or configure gitleaks in .gitleaksignore

# Skip gitleaks for specific commit (not recommended)
git commit --no-verify
```

### Need to commit a secret for testing

```bash
# Create a test branch
git checkout -b test/secret-handling

# Commit with bypass
git commit --no-verify -m "test: secret handling"

# Delete branch after testing
git checkout main
git branch -D test/secret-handling
```

## Monitoring

### GitHub Secret Scanning

1. Go to repository Settings
2. Enable "Secret scanning"
3. Configure alerts
4. Review detected secrets

### Sentry Error Tracking

Monitor for unauthorized access attempts:

```bash
# Check Sentry dashboard
https://dev-vp.sentry.io/issues/
```

### Audit Logs

```bash
# View git commit history
git log --oneline --all

# Check for suspicious commits
git log --all --grep="secret\|token\|key" --oneline
```

## Incident Response

If credentials are exposed:

1. **Immediately rotate** all exposed credentials
2. **Remove from git history** using git-filter-repo
3. **Force push** to all remotes
4. **Notify team** of the incident
5. **Audit logs** for unauthorized access
6. **Update** CI/CD secrets
7. **Document** the incident

## Resources

- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
- [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [gitleaks Documentation](https://github.com/gitleaks/gitleaks)
- [pre-commit Framework](https://pre-commit.com/)
- [git-filter-repo](https://github.com/newren/git-filter-repo)

## Questions?

Contact: security@vrenum.app
