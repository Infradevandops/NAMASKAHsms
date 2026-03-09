# GitHub Actions Setup Guide

**Strategy**: GitHub = Production (Clean Code) | GitLab = Auto-Synced Backup

---

## What We Created

### 1. CI Workflow (`.github/workflows/ci.yml`)
**Triggers**: Every push and pull request  
**What it does**:
- ✅ Runs all tests with PostgreSQL and Redis
- ✅ Checks code quality (linting, formatting)
- ✅ Security scanning (Bandit, Safety)
- ✅ Type checking (MyPy)
- ✅ Coverage reporting

### 2. GitLab Sync Workflow (`.github/workflows/sync-to-gitlab.yml`)
**Triggers**: Every push to main/develop  
**What it does**:
- ✅ Automatically mirrors GitHub → GitLab
- ✅ GitLab becomes backup copy
- ✅ Full git history preserved

### 3. Deploy Workflow (`.github/workflows/deploy.yml`)
**Triggers**: Push to main (after tests pass)  
**What it does**:
- ✅ Deploys to Render.com
- ✅ Runs health checks
- ✅ Notifies on success/failure

---

## Setup Steps (5 minutes)

### Step 1: Add GitLab Token to GitHub Secrets

1. **Go to your GitHub repo**: https://github.com/YOUR-USERNAME/YOUR-REPO

2. **Navigate to Settings**:
   - Click "Settings" tab
   - Click "Secrets and variables" → "Actions"

3. **Add GITLAB_TOKEN**:
   - Click "New repository secret"
   - Name: `GITLAB_TOKEN`
   - Value: `glpat-Oxf0N5r_-ehxfRhM86DOnG86MQp1Omg5MmxqCw.01.1202lxyp0`
   - Click "Add secret"

### Step 2: Add Render Deploy Hook (Optional)

1. **Get Render Deploy Hook**:
   - Go to Render dashboard
   - Select your service
   - Go to "Settings"
   - Copy "Deploy Hook URL"

2. **Add to GitHub Secrets**:
   - Name: `RENDER_DEPLOY_HOOK`
   - Value: `https://api.render.com/deploy/srv-xxxxx?key=xxxxx`
   - Click "Add secret"

3. **Add Production URL**:
   - Name: `PRODUCTION_URL`
   - Value: `https://your-app.onrender.com`
   - Click "Add secret"

### Step 3: Push to GitHub

```bash
# Add the workflows
git add .github/

# Commit
git commit -m "ci: Add GitHub Actions workflows for CI/CD and GitLab sync"

# Push to GitHub
git push origin main
```

### Step 4: Verify It's Working

1. **Check Actions Tab**:
   - Go to your GitHub repo
   - Click "Actions" tab
   - You should see workflows running

2. **Check GitLab**:
   - Go to: https://gitlab.com/oghenesuvwe-group/NAMASKAHsms
   - Verify latest commit matches GitHub

3. **Check Render** (if configured):
   - Go to Render dashboard
   - Verify deployment triggered

---

## Workflow Diagram

```
Developer
    ↓
  Push to GitHub (main branch)
    ↓
    ├─→ CI Workflow
    │   ├─ Run tests
    │   ├─ Security scan
    │   └─ Code quality checks
    │
    ├─→ Sync to GitLab
    │   └─ Mirror entire repo
    │
    └─→ Deploy to Render
        ├─ Trigger deployment
        └─ Health check
```

---

## How It Works

### Automatic Flow

1. **You push to GitHub**:
   ```bash
   git push origin main
   ```

2. **GitHub Actions automatically**:
   - ✅ Runs tests (must pass)
   - ✅ Scans for security issues
   - ✅ Syncs to GitLab (backup)
   - ✅ Deploys to Render (production)

3. **GitLab stays in sync**:
   - Every push to GitHub → Automatically pushed to GitLab
   - GitLab is always a mirror/backup
   - No manual sync needed

### Manual Triggers

You can also trigger workflows manually:

1. Go to GitHub → Actions tab
2. Select workflow (e.g., "Sync to GitLab")
3. Click "Run workflow"
4. Select branch
5. Click "Run workflow"

---

## Workflow Status Badges

Add these to your README.md:

```markdown
![CI](https://github.com/YOUR-USERNAME/YOUR-REPO/workflows/CI%20-%20Test%20%26%20Quality%20Checks/badge.svg)
![Sync](https://github.com/YOUR-USERNAME/YOUR-REPO/workflows/Sync%20to%20GitLab%20Backup/badge.svg)
![Deploy](https://github.com/YOUR-USERNAME/YOUR-REPO/workflows/Deploy%20to%20Production/badge.svg)
```

---

## Troubleshooting

### GitLab Sync Fails

**Error**: "Authentication failed"

**Solution**:
1. Check GITLAB_TOKEN secret is set correctly
2. Verify token has `write_repository` permission
3. Check token hasn't expired

**Fix**:
```bash
# Test token manually
cd "/Users/machine/My Drive/Github Projects/NAMASKAHsms-gitlab"
git push origin main
# If this works, token is fine
```

### Tests Fail

**Error**: Tests don't pass in CI

**Solution**:
1. Run tests locally first: `pytest tests/ -v`
2. Check environment variables are set
3. Verify database/redis connections

**Fix**:
```bash
# Run tests locally with same setup as CI
DATABASE_URL=postgresql://postgres:test@localhost/test \
REDIS_URL=redis://localhost:6379/0 \
pytest tests/ -v
```

### Deploy Fails

**Error**: Render deployment doesn't trigger

**Solution**:
1. Check RENDER_DEPLOY_HOOK is set
2. Verify deploy hook URL is correct
3. Check Render service is active

**Fix**:
```bash
# Test deploy hook manually
curl -X POST "YOUR_RENDER_DEPLOY_HOOK_URL"
```

---

## Customization

### Change When Sync Happens

Edit `.github/workflows/sync-to-gitlab.yml`:

```yaml
# Sync only on main branch
on:
  push:
    branches:
      - main

# Or sync on tags
on:
  push:
    tags:
      - 'v*'
```

### Add Slack Notifications

Add to any workflow:

```yaml
- name: Notify Slack
  if: always()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### Run Tests Only on PR

Edit `.github/workflows/ci.yml`:

```yaml
on:
  pull_request:
    branches: [ main ]
  # Remove push trigger
```

---

## Best Practices

### 1. Protect Main Branch

**GitHub Settings → Branches → Add rule**:
- ✅ Require pull request reviews
- ✅ Require status checks to pass (CI workflow)
- ✅ Require branches to be up to date

### 2. Use Develop Branch

```bash
# Create develop branch
git checkout -b develop
git push origin develop

# Work on features
git checkout -b feature/new-feature
# ... make changes ...
git push origin feature/new-feature

# Create PR to develop
# After review, merge to develop
# When ready, merge develop to main (triggers deploy)
```

### 3. Tag Releases

```bash
# Tag a release
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# This creates a release in GitHub
# And syncs to GitLab
```

### 4. Monitor Workflows

- Check Actions tab regularly
- Set up notifications for failures
- Review security scan reports

---

## Current Status

### ✅ Configured
- CI workflow (tests, security, quality)
- GitLab sync workflow
- Deploy workflow

### ⏳ Needs Setup
- [ ] Add GITLAB_TOKEN to GitHub secrets
- [ ] Add RENDER_DEPLOY_HOOK to GitHub secrets (optional)
- [ ] Add PRODUCTION_URL to GitHub secrets (optional)
- [ ] Push workflows to GitHub
- [ ] Verify sync is working

### 🎯 Next Steps
1. Add secrets to GitHub
2. Push workflows: `git push origin main`
3. Check Actions tab
4. Verify GitLab sync
5. Test deployment

---

## Summary

**What you get**:
- ✅ GitHub = Production source (clean code)
- ✅ GitLab = Auto-synced backup
- ✅ Automated testing on every push
- ✅ Security scanning
- ✅ Auto-deploy to Render
- ✅ No manual sync needed

**Workflow**:
```bash
# Just push to GitHub
git push origin main

# Everything else happens automatically:
# → Tests run
# → Code scanned
# → Synced to GitLab
# → Deployed to Render
```

**Time to set up**: 5 minutes  
**Maintenance**: Zero (fully automated)

---

**Ready to activate?** Follow Step 1-3 above to add secrets and push!
