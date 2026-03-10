# Namaskah SMS - Setup Guide

**Last Updated:** March 9, 2026  
**Status:** Production Ready (98% Complete)

---

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- Git

### Installation

```bash
# 1. Clone repository
git clone https://github.com/YOUR-USERNAME/namaskah-sms.git
cd namaskah-sms

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment
cp .env.example .env
# Edit .env with your configuration

# 5. Initialize database
python scripts/fix_production_schema.py

# 6. Run application
./start.sh
# or
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

**Open:** `http://localhost:8000`

---

## GitHub Actions Setup

### Required Secrets

Go to: **GitHub Repo → Settings → Secrets and variables → Actions**

Add these secrets:

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `GITLAB_TOKEN` | GitLab personal access token for backup sync | Optional |
| `RENDER_DEPLOY_HOOK` | Render deployment webhook URL | Optional |
| `PRODUCTION_URL` | Production URL for health checks | Optional |

### How to Get Secrets

#### GitLab Token (for auto-backup)
1. Go to: https://gitlab.com/-/user_settings/personal_access_tokens
2. Create token with `write_repository` scope
3. Copy token (starts with `glpat-`)
4. Add to GitHub secrets as `GITLAB_TOKEN`

#### Render Deploy Hook
1. Go to: https://dashboard.render.com
2. Select your service
3. Go to Settings → Deploy Hook
4. Copy the URL
5. Add to GitHub secrets as `RENDER_DEPLOY_HOOK`

---

## CI/CD Workflows

### Automatic Workflows

**On every push:**
1. **CI Tests** - Runs tests, linting, security scans
2. **GitLab Sync** - Mirrors code to GitLab (if token configured)
3. **Deploy** - Deploys to Render on main branch (if hook configured)

### Manual Triggers

All workflows can be triggered manually from:
**GitHub → Actions → Select workflow → Run workflow**

---

## Environment Variables

### Required for Production

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Security
SECRET_KEY=your-secret-key-min-32-chars
JWT_SECRET_KEY=your-jwt-secret-key-min-32-chars

# External Services
TEXTVERIFIED_API_KEY=your-textverified-api-key
PAYSTACK_SECRET_KEY=your-paystack-secret-key

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ORIGINS=https://your-domain.com
```

### Optional

```bash
# Emergency access (leave unset to disable)
EMERGENCY_SECRET=random-secret-for-emergency-access

# Environment
ENVIRONMENT=production
```

---

## Security Checklist

Before deploying to production:

- [ ] Rotate all API keys and secrets
- [ ] Set unique `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Update `DATABASE_URL` to production database
- [ ] Configure `CORS_ORIGINS` to production domain
- [ ] Remove or secure `EMERGENCY_SECRET`
- [ ] Enable HTTPS (handled by Render)
- [ ] Review GitHub secrets are set correctly

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_wallet_service.py -v

# Run integration tests
pytest tests/integration/ -v
```

---

## Deployment

### Automatic Deployment (Recommended)

1. Push to `main` branch
2. GitHub Actions runs tests
3. If tests pass, deploys to Render automatically
4. Health check verifies deployment

### Manual Deployment

```bash
# Trigger deploy hook manually
curl -X POST "$RENDER_DEPLOY_HOOK"
```

---

## Monitoring

### Health Checks

- **Basic:** `GET /health`
- **Readiness:** `GET /health/ready`
- **Liveness:** `GET /health/live`
- **Detailed:** `GET /health/detailed`

### Logs

```bash
# View Render logs
# Go to: https://dashboard.render.com → Your Service → Logs

# Local logs
tail -f logs/app.log
```

---

## Troubleshooting

### Tests Failing in CI

**Check:**
1. All required environment variables set
2. PostgreSQL and Redis services running
3. Database migrations applied

**Fix:**
```bash
# Run tests locally first
pytest tests/ -v

# Check specific failure
pytest tests/path/to/test.py -v -s
```

### GitLab Sync Failing

**Check:**
1. `GITLAB_TOKEN` secret is set
2. Token has `write_repository` permission
3. Token is not expired

**Fix:**
- Regenerate token on GitLab
- Update GitHub secret

### Deployment Failing

**Check:**
1. `RENDER_DEPLOY_HOOK` is correct
2. Tests passed before deployment
3. Render service is active

**Fix:**
- Check Render dashboard for errors
- Review deployment logs
- Verify environment variables on Render

---

## Support

- **Documentation:** See README.md and PROJECT_STATUS.md
- **Issues:** GitHub Issues
- **CI/CD Status:** GitHub Actions tab

---

## Next Steps

1. ✅ Complete this setup
2. ✅ Run tests locally
3. ✅ Push to GitHub
4. ✅ Verify CI/CD workflows
5. ✅ Deploy to production
6. 📊 Monitor production metrics

---

**Ready to deploy!** The platform is production-ready at 98% completion.
