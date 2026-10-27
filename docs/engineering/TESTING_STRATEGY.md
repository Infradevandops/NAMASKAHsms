# 🧪 Admin Credentials Testing - Quick Reference

**Date:** October 25, 2026  
**Purpose:** Test admin credentials before production deployment

---

## Quick Answer

### Should You Test Before Deploying?

**YES - ALWAYS TEST FIRST** ✅

**Recommended Flow:**
1. **Local Testing** (30 min) - Your machine
2. **Docker Testing** (30 min) - Production-like environment
3. **Staging Deployment** (2-4 hours) - Real infrastructure
4. **Production Deployment** (1 hour) - Live

**Total Time:** 4-6 hours for comprehensive testing

---

## Testing Methods

### Method 1: Local Testing (Fastest)

```bash
# Start application
./scripts/start.sh

# Test admin login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@vrenum.app",
    "password": "Namaskah@Admin2024"
  }'

# Or use the test script
./scripts/test-admin-credentials.sh http://localhost:8000
```

**Time:** 5-10 minutes  
**Risk:** Low (local only)  
**Catches:** Basic functionality issues

---

### Method 2: Docker Testing (Production-Like)

```bash
# Start Docker environment
cd deploy/docker
docker-compose up -d

# Wait for services
sleep 10

# Test admin credentials
./scripts/test-admin-credentials.sh http://localhost:8000

# Run integration tests
pytest tests/integration/ -v

# Cleanup
docker-compose down
```

**Time:** 30 minutes  
**Risk:** Low (local Docker)  
**Catches:** Integration issues, infrastructure problems

---

### Method 3: Staging Deployment (Recommended)

```bash
# Deploy to staging server
bash scripts/deployment/deploy_production.sh staging

# Test admin credentials
./scripts/test-admin-credentials.sh https://staging.vrenum.app

# Run full test suite
pytest tests/ -v

# Manual testing
# - Login via web UI
# - Test all admin features
# - Verify integrations
```

**Time:** 2-4 hours  
**Risk:** Low (staging only)  
**Catches:** All issues before production

---

### Method 4: Production Deployment (Not Recommended First)

```bash
# Deploy to production
bash scripts/deployment/deploy_production.sh production

# Test admin credentials
./scripts/test-admin-credentials.sh https://vrenum.app

# Monitor closely
# - Check logs
# - Monitor errors
# - Monitor uptime
```

**Time:** 1 hour  
**Risk:** High (affects live users)  
**Catches:** Production-specific issues

---

## Using the Test Script

### Basic Usage

```bash
# Test local environment
./scripts/test-admin-credentials.sh

# Test specific environment
./scripts/test-admin-credentials.sh http://localhost:8000

# Test staging
./scripts/test-admin-credentials.sh https://staging.vrenum.app

# Test production
./scripts/test-admin-credentials.sh https://vrenum.app

# Test with custom credentials
./scripts/test-admin-credentials.sh http://localhost:8000 admin@vrenum.app Namaskah@Admin2024
```

### What It Tests

1. ✅ Health check
2. ✅ Admin login
3. ✅ User info retrieval
4. ✅ Admin dashboard access
5. ✅ Token refresh
6. ✅ Logout
7. ✅ Token invalidation

---

## Testing Checklist

### Before Staging Deployment
- [ ] Local tests pass
- [ ] Docker tests pass
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] No errors in logs

### Before Production Deployment
- [ ] Staging tests pass
- [ ] Admin login works
- [ ] All features work
- [ ] Integrations work
- [ ] Performance acceptable
- [ ] Security headers present
- [ ] SSL certificate valid
- [ ] Backups working
- [ ] Monitoring configured
- [ ] Team approval obtained

---

## Troubleshooting

### Login Fails

```bash
# Check if user exists
sudo -u postgres psql -d vrenum -c \
  "SELECT email, is_admin FROM users WHERE email='admin@vrenum.app';"

# Check password
python3 << 'EOF'
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
password = "Namaskah@Admin2024"
hash_from_db = "$2b$12$..."  # Replace with actual hash
print(pwd_context.verify(password, hash_from_db))
EOF
```

### Admin Access Denied

```bash
# Update admin flag
sudo -u postgres psql -d vrenum -c \
  "UPDATE users SET is_admin=true WHERE email='admin@vrenum.app';"
```

### Token Invalid

```bash
# Check JWT configuration
grep JWT_SECRET_KEY .env

# Verify token
python3 << 'EOF'
import jwt
token = "eyJ..."  # Your token
decoded = jwt.decode(token, options={"verify_signature": False})
print(decoded)
EOF
```

---

## Recommended Approach

### For First Deployment

**Step 1: Local Testing (30 min)**
```bash
./scripts/start.sh
./scripts/test-admin-credentials.sh http://localhost:8000
pytest tests/ -v
```

**Step 2: Docker Testing (30 min)**
```bash
cd deploy/docker
docker-compose up -d
./scripts/test-admin-credentials.sh http://localhost:8000
pytest tests/integration/ -v
docker-compose down
```

**Step 3: Staging Deployment (2-4 hours)**
```bash
bash scripts/deployment/deploy_production.sh staging
./scripts/test-admin-credentials.sh https://staging.vrenum.app
pytest tests/ -v
# Manual testing
```

**Step 4: Production Deployment (1 hour)**
```bash
bash scripts/deployment/deploy_production.sh production
./scripts/test-admin-credentials.sh https://vrenum.app
# Monitor closely
```

**Total Time:** 4-6 hours

---

## Decision Matrix

| Scenario | Approach | Time | Risk |
|----------|----------|------|------|
| First deployment | Test First (Full) | 6 hours | Low |
| Small update | Local + Docker | 1 hour | Low |
| Hotfix | Deploy + Monitor | 1 hour | Medium |
| Major change | Full pipeline | 8 hours | Low |

---

## Key Files

### Testing Documentation
- `docs/deployment/ADMIN_CREDENTIALS_TESTING.md` - Full guide
- `scripts/test-admin-credentials.sh` - Test script

### Deployment Documentation
- `docs/deployment/DEPLOYMENT_BEST_PRACTICES.md` - Deployment guide
- `docs/deployment/DEPLOYMENT_CHECKLIST.md` - Verification checklist
- `docs/deployment/DEPLOYMENT_QUICK_REFERENCE.md` - Quick commands

---

## Admin Credentials

### Local Development
- **Email:** `admin@vrenum.app`
- **Password:** `Namaskah@Admin2024`
- **URL:** `http://localhost:8000/login`

### Staging
- **Email:** `admin@vrenum.app`
- **Password:** `Namaskah@Admin2024` (or staging-specific)
- **URL:** `https://staging.vrenum.app/login`

### Production
- **Email:** `admin@vrenum.app`
- **Password:** `[ROTATE BEFORE LAUNCH]`
- **URL:** `https://vrenum.app/login`

---

## Summary

### Best Practice
1. ✅ Test locally first
2. ✅ Test in Docker
3. ✅ Deploy to staging
4. ✅ Test thoroughly
5. ✅ Deploy to production
6. ✅ Monitor closely

### Why Test First?
- ✅ Catch issues early
- ✅ No impact on users
- ✅ Can rollback easily
- ✅ Team can validate
- ✅ Verify integrations

### Time Investment
- **Testing:** 4-6 hours
- **Deployment:** 1 hour
- **Monitoring:** 1-2 hours
- **Total:** 6-9 hours

### Risk Reduction
- Local testing: 80% risk reduction
- Docker testing: 95% risk reduction
- Staging testing: 99% risk reduction

---

## Next Steps

1. **Run local tests**
   ```bash
   ./scripts/test-admin-credentials.sh http://localhost:8000
   ```

2. **Run Docker tests**
   ```bash
   cd deploy/docker
   docker-compose up -d
   ./scripts/test-admin-credentials.sh http://localhost:8000
   ```

3. **Deploy to staging**
   ```bash
   bash scripts/deployment/deploy_production.sh staging
   ```

4. **Test on staging**
   ```bash
   ./scripts/test-admin-credentials.sh https://staging.vrenum.app
   ```

5. **Deploy to production**
   ```bash
   bash scripts/deployment/deploy_production.sh production
   ```

---

**Recommendation:** Test first, deploy second. Never deploy directly to production without testing.

**Status:** Ready for testing  
**Date:** October 25, 2026  
**Version:** 1.0
