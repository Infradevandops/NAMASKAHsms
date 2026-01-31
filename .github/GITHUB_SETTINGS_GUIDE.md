# GitHub Settings Configuration Guide

**Repository**: NAMASKAHsms  
**Purpose**: Configure secrets and branch protection for CI/CD  
**Time Required**: 30-45 minutes  
**Difficulty**: Easy (point-and-click)

---

## 📋 Overview

This guide walks you through configuring GitHub Settings for your CI/CD pipeline:
1. **GitHub Secrets** - Store sensitive credentials securely
2. **Branch Protection** - Enforce CI checks before merging

---

## 🔐 Part 1: Configure GitHub Secrets (15 minutes)

### What Are GitHub Secrets?

GitHub Secrets are encrypted environment variables that store sensitive information like API keys, webhooks, and tokens. They're used by GitHub Actions but never exposed in logs.

### Step-by-Step Instructions

#### 1. Navigate to Repository Settings

```
1. Go to: https://github.com/Infradevandops/NAMASKAHsms
2. Click the "Settings" tab (top right, next to Insights)
3. In the left sidebar, click "Secrets and variables"
4. Click "Actions"
```

**Direct Link**: https://github.com/Infradevandops/NAMASKAHsms/settings/secrets/actions

---

#### 2. Check Existing Secrets

You should see a list of existing secrets. Look for:
- ✅ `RENDER_DEPLOY_HOOK` - Should already exist
- ❓ `RENDER_ROLLBACK_HOOK` - Needs to be added
- ❓ `STAGING_DEPLOY_HOOK` - Optional (for staging environment)
- ❓ `CODECOV_TOKEN` - Optional (for Codecov integration)

---

#### 3. Add RENDER_ROLLBACK_HOOK (Required)

**What it does**: Allows automatic rollback if deployment fails

**Steps**:
```
1. Click "New repository secret" (green button, top right)
2. Name: RENDER_ROLLBACK_HOOK
3. Secret: [Your Render rollback webhook URL]
4. Click "Add secret"
```

**How to get the webhook URL**:
```
1. Go to your Render dashboard: https://dashboard.render.com
2. Select your service (NAMASKAHsms)
3. Go to Settings → Deploy Hooks
4. Look for "Rollback Hook" or create a new deploy hook
5. Copy the webhook URL (looks like: https://api.render.com/deploy/srv-xxx?key=xxx)
6. Paste it into GitHub as the secret value
```

**Example** (don't use this, get your own):
```
https://api.render.com/deploy/srv-abc123?key=xyz789
```

---

#### 4. Add STAGING_DEPLOY_HOOK (Optional)

**What it does**: Enables automatic deployment to staging environment

**Steps**:
```
1. Click "New repository secret"
2. Name: STAGING_DEPLOY_HOOK
3. Secret: [Your Render staging webhook URL]
4. Click "Add secret"
```

**Note**: Only add this if you have a staging environment set up in Render.

---

#### 5. Add CODECOV_TOKEN (Optional)

**What it does**: Uploads coverage reports to Codecov for tracking

**Steps**:
```
1. Go to: https://codecov.io
2. Sign in with GitHub
3. Add your repository
4. Copy the upload token
5. In GitHub: Click "New repository secret"
6. Name: CODECOV_TOKEN
7. Secret: [Your Codecov token]
8. Click "Add secret"
```

**Note**: Only needed if you want coverage tracking on Codecov.

---

#### 6. Verify Secrets

After adding secrets, you should see:
```
✅ RENDER_DEPLOY_HOOK
✅ RENDER_ROLLBACK_HOOK
✅ STAGING_DEPLOY_HOOK (optional)
✅ CODECOV_TOKEN (optional)
```

**Important**: 
- You can't view secret values after creation (they're encrypted)
- You can only update or delete them
- Secrets are available to all workflows in the repository

---

## 🛡️ Part 2: Configure Branch Protection (15 minutes)

### What Is Branch Protection?

Branch protection rules prevent direct pushes to important branches and require CI checks to pass before merging pull requests.

### Step-by-Step Instructions

#### 1. Navigate to Branch Protection Settings

```
1. Go to: https://github.com/Infradevandops/NAMASKAHsms
2. Click "Settings" tab
3. In left sidebar, click "Branches"
4. Under "Branch protection rules", click "Add rule" or "Add branch protection rule"
```

**Direct Link**: https://github.com/Infradevandops/NAMASKAHsms/settings/branches

---

#### 2. Configure Protection for 'main' Branch

**Branch name pattern**: `main`

**Settings to Enable**:

##### ✅ Require a pull request before merging
```
☑ Require a pull request before merging
  ☑ Require approvals: 1
  ☐ Dismiss stale pull request approvals when new commits are pushed
  ☑ Require review from Code Owners
  ☐ Restrict who can dismiss pull request reviews
  ☑ Allow specified actors to bypass required pull requests
```

**Why**: Ensures code review before merging

---

##### ✅ Require status checks to pass before merging
```
☑ Require status checks to pass before merging
  ☑ Require branches to be up to date before merging
  
  Search for status checks:
  ☑ test / Python 3.9
  ☑ test / Python 3.11
  ☑ lint
  ☑ integration
  ☑ migration-test
  ☑ security
  ☑ container-scan
  ☑ secrets-scan
```

**Why**: All CI checks must pass before merging

**Note**: Status checks will appear after the first CI run. If you don't see them yet:
1. Make a small change and push to trigger CI
2. Wait for CI to complete
3. Come back and add the status checks

---

##### ✅ Require conversation resolution before merging
```
☑ Require conversation resolution before merging
```

**Why**: All PR comments must be resolved

---

##### ✅ Require signed commits (Optional but Recommended)
```
☑ Require signed commits
```

**Why**: Ensures commits are verified and authentic

**Note**: Only enable if your team uses GPG signing

---

##### ✅ Require linear history (Optional)
```
☑ Require linear history
```

**Why**: Prevents merge commits, keeps history clean

**Note**: This forces rebase or squash merges

---

##### ✅ Include administrators
```
☑ Do not allow bypassing the above settings
```

**Why**: Even admins must follow the rules

**Important**: This is the most secure option but can slow down urgent fixes

---

#### 3. Rules Configuration Summary

**Recommended Settings**:
```
Branch name pattern: main

✅ Require pull request before merging
   • Require 1 approval
   • Require review from Code Owners

✅ Require status checks to pass
   • Require branches to be up to date
   • Required checks:
     - test (Python 3.9)
     - test (Python 3.11)
     - lint
     - integration
     - migration-test
     - security
     - container-scan
     - secrets-scan

✅ Require conversation resolution

✅ Do not allow bypassing settings (include administrators)

Optional:
☐ Require signed commits
☐ Require linear history
```

---

#### 4. Save the Rule

```
1. Scroll to bottom
2. Click "Create" or "Save changes"
3. Confirm the rule is active
```

---

#### 5. Configure Protection for 'develop' Branch (Optional)

If you use a `develop` branch, repeat the same steps:

```
Branch name pattern: develop

Same settings as 'main' branch
```

---

## ✅ Verification Checklist

### Secrets Configuration
- [ ] Navigated to Settings → Secrets and variables → Actions
- [ ] Verified `RENDER_DEPLOY_HOOK` exists
- [ ] Added `RENDER_ROLLBACK_HOOK`
- [ ] (Optional) Added `STAGING_DEPLOY_HOOK`
- [ ] (Optional) Added `CODECOV_TOKEN`
- [ ] All secrets show in the list

### Branch Protection
- [ ] Navigated to Settings → Branches
- [ ] Created rule for `main` branch
- [ ] Enabled "Require pull request before merging"
- [ ] Set "Require approvals" to 1
- [ ] Enabled "Require status checks to pass"
- [ ] Added all 8 required status checks
- [ ] Enabled "Require conversation resolution"
- [ ] Enabled "Do not allow bypassing settings"
- [ ] Saved the rule
- [ ] Rule shows as active

---

## 🧪 Testing Your Configuration

### Test Secrets

**Method 1**: Check workflow runs
```
1. Go to: https://github.com/Infradevandops/NAMASKAHsms/actions
2. Click on latest workflow run
3. Check "Deploy to Production" job
4. Should see: "✅ Deployed to production" (if RENDER_DEPLOY_HOOK works)
5. If deployment fails, should see: "✅ Rollback initiated" (if RENDER_ROLLBACK_HOOK works)
```

**Method 2**: Manual test (safe)
```
1. Go to Actions tab
2. Select "CI/CD Pipeline" workflow
3. Click "Run workflow" (right side)
4. Select branch: main
5. Click "Run workflow"
6. Watch the deployment job
```

---

### Test Branch Protection

**Method 1**: Try direct push (should fail)
```bash
# This should be blocked
git checkout main
echo "test" >> README.md
git add README.md
git commit -m "test: direct push"
git push origin main

# Expected result: ❌ Push rejected
# Error: "required status checks" or "pull request required"
```

**Method 2**: Create a pull request
```bash
# Create a feature branch
git checkout -b test-branch-protection
echo "test" >> README.md
git add README.md
git commit -m "test: branch protection"
git push origin test-branch-protection

# Go to GitHub and create a PR
# Expected result: ✅ PR created, but can't merge until:
#   - CI checks pass
#   - 1 approval received
#   - Conversations resolved
```

---

## 🚨 Troubleshooting

### Issue: Can't find status checks

**Problem**: Status checks don't appear in the dropdown

**Solution**:
1. Push a commit to trigger CI
2. Wait for CI to complete
3. Go back to branch protection settings
4. Status checks should now appear in the search

---

### Issue: Secrets not working

**Problem**: Workflow can't access secrets

**Solution**:
1. Check secret names match exactly (case-sensitive)
2. Verify secrets are in "Actions" section (not "Dependabot" or "Codespaces")
3. Check workflow file uses correct syntax: `${{ secrets.SECRET_NAME }}`
4. Re-create the secret if needed

---

### Issue: Branch protection too strict

**Problem**: Can't merge even with passing CI

**Solution**:
1. Check all conversations are resolved
2. Verify you have required approvals
3. Ensure branch is up to date with base branch
4. Temporarily disable "Include administrators" if urgent

---

### Issue: Status checks not running

**Problem**: CI doesn't run on pull requests

**Solution**:
1. Check `.github/workflows/ci.yml` has `pull_request` trigger
2. Verify workflow file is on the base branch (main)
3. Check Actions are enabled: Settings → Actions → General
4. Look for workflow errors in Actions tab

---

## 📚 Additional Resources

### GitHub Documentation
- **Secrets**: https://docs.github.com/en/actions/security-guides/encrypted-secrets
- **Branch Protection**: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- **Status Checks**: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/about-status-checks

### Render Documentation
- **Deploy Hooks**: https://render.com/docs/deploy-hooks
- **Rollback**: https://render.com/docs/deploys#rollbacks

### Your Repository Links
- **Settings**: https://github.com/Infradevandops/NAMASKAHsms/settings
- **Secrets**: https://github.com/Infradevandops/NAMASKAHsms/settings/secrets/actions
- **Branches**: https://github.com/Infradevandops/NAMASKAHsms/settings/branches
- **Actions**: https://github.com/Infradevandops/NAMASKAHsms/actions

---

## 🎯 Quick Reference

### Secrets to Add
```
Required:
  • RENDER_ROLLBACK_HOOK - Rollback webhook from Render

Optional:
  • STAGING_DEPLOY_HOOK - Staging deployment webhook
  • CODECOV_TOKEN - Coverage tracking token
```

### Status Checks to Require
```
1. test (Python 3.9)
2. test (Python 3.11)
3. lint
4. integration
5. migration-test
6. security
7. container-scan
8. secrets-scan
```

### Branch Protection Settings
```
✅ Require pull request (1 approval)
✅ Require status checks (8 checks)
✅ Require conversation resolution
✅ Do not allow bypassing
```

---

## ✅ Completion

After completing this guide, you will have:
- ✅ All required secrets configured
- ✅ Branch protection enabled on main
- ✅ CI checks required before merging
- ✅ Code review process enforced
- ✅ Automatic rollback capability

**Next Steps**:
1. Test by creating a pull request
2. Verify CI runs automatically
3. Confirm you can't merge without approval
4. Check rollback works (optional)

---

**Last Updated**: 2026-01-31  
**Maintainer**: DevOps Team  
**Questions?**: Check troubleshooting section or ask in team chat
