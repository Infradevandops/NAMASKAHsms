# 🧪 Admin Credentials Testing Strategy - Production Testing Guide

**Date:** October 25, 2026  
**Purpose:** Test admin credentials in production-like environments before deploying to production

---

## Overview

There are **two main approaches** to testing admin credentials:

1. **Test First, Then Deploy** (Recommended)
   - Deploy to staging environment
   - Test all credentials and functionality
   - Verify everything works
   - Then deploy to production

2. **Deploy First, Then Test** (Not Recommended)
   - Deploy directly to production
   - Test in production
   - Risk: Issues affect live users

---

## Recommended Approach: Test First (Staging Environment)

### Why Staging First?
- ✅ Catch issues before production
- ✅ Test with real infrastructure
- ✅ Verify all integrations work
- ✅ No impact on live users
- ✅ Can rollback if needed
- ✅ Team can validate together

---

## Option 1: Staging Environment Setup (RECOMMENDED)

### Step 1: Create Staging Server

```bash
# Provision staging server (same as production)
# Ubuntu 22.04 LTS, same specs as production

# Example: DigitalOcean, AWS, Linode, etc.
# - 2GB RAM minimum
# - 20GB SSD
# - Same region as production
```

### Step 2: Deploy to Staging

```bash
# Clone repository
git clone https://github.com/Infradevandops/NAMASKAHsms.git /opt/vrenum-staging

# Setup environment
cd /opt/vrenum-staging
python3.9 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure staging environment
cp config/.env.production.example .env.staging
# Edit .env.staging with staging credentials
nano .env.staging

# Setup database
sudo -u postgres psql << EOF
CREATE DATABASE vrenum_staging;
CREATE USER vrenum_staging WITH PASSWORD 'staging_password';
GRANT ALL PRIVILEGES ON DATABASE vrenum_staging TO vrenum_staging;
EOF

# Run migrations
bash scripts/deployment/migrate.sh

# Start application
./scripts/start.sh
```

### Step 3: Test Admin Credentials

#### Test 1: Login via API
```bash
# Test admin login
curl -X POST https://staging.vrenum.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@vrenum.app",
    "password": "Namaskah@Admin2024"
  }'

# Expected response:
# {
#   "access_token": "eyJ...",
#   "refresh_token": "eyJ...",
#   "token_type": "bearer",
#   "user": {
#     "id": "...",
#     "email": "admin@vrenum.app",
#     "is_admin": true
#   }
# }
```

#### Test 2: Login via Web UI
```bash
# Open browser
https://staging.vrenum.app/login

# Enter credentials:
# Email: admin@vrenum.app
# Password: Namaskah@Admin2024

# Verify:
# - Login succeeds
# - Redirects to dashboard
# - Admin panel accessible
# - All features work
```

#### Test 3: Admin Dashboard Access
```bash
# Test admin endpoints
curl -X GET https://staging.vrenum.app/admin \
  -H "Authorization: Bearer $TOKEN"

# Verify:
# - Admin dashboard loads
# - User management works
# - Analytics display
# - Settings accessible
```

#### Test 4: External API Integration
```bash
# Test TextVerified integration
curl -X POST https://staging.vrenum.app/api/verify/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "telegram",
    "country": "US"
  }'

# Test Paystack integration
curl -X POST https://staging.vrenum.app/api/wallet/paystack/initialize \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 1000
  }'
```

### Step 4: Comprehensive Testing Checklist

#### Authentication Tests
- [ ] Admin login via API works
- [ ] Admin login via web UI works
- [ ] JWT token is valid
- [ ] Refresh token works
- [ ] Logout works
- [ ] Session invalidation works
- [ ] MFA works (if enabled)

#### Admin Dashboard Tests
- [ ] Dashboard loads
- [ ] User management works
- [ ] Analytics display correctly
- [ ] Settings are accessible
- [ ] Reports generate
- [ ] Exports work

#### API Tests
- [ ] SMS verification works
- [ ] Payment processing works
- [ ] Wallet operations work
- [ ] Tier management works
- [ ] API keys work
- [ ] Webhooks work

#### Integration Tests
- [ ] TextVerified integration works
- [ ] Paystack integration works
- [ ] Email notifications work
- [ ] Sentry error tracking works
- [ ] Redis cache works
- [ ] Database operations work

#### Security Tests
- [ ] HTTPS enforced
- [ ] Security headers present
- [ ] CORS configured correctly
- [ ] Rate limiting works
- [ ] Input validation works
- [ ] SQL injection prevented

---

## Option 2: Local Testing with Production-Like Setup

### If You Can't Deploy to Staging First

#### Step 1: Setup Local Production-Like Environment

```bash
# Use Docker to simulate production
cd deploy/docker
docker-compose -f docker-compose.yml up -d

# This creates:
# - PostgreSQL database
# - Redis cache
# - Nginx reverse proxy
# - Application container
```

#### Step 2: Test Admin Credentials Locally

```bash
# Test login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@vrenum.app",
    "password": "Namaskah@Admin2024"
  }'

# Test web UI
open http://localhost:8000/login
```

#### Step 3: Run Full Test Suite

```bash
# Run all tests
pytest --cov=app

# Run specific tests
pytest tests/unit/test_auth_service.py -v
pytest tests/integration/test_auth_api.py -v
```

---

## Option 3: Hybrid Approach (BEST PRACTICE)

### Recommended Testing Flow

```
1. Local Testing (Your Machine)
   ↓
2. Docker Testing (Local Production-Like)
   ↓
3. Staging Deployment (Real Infrastructure)
   ↓
4. Production Deployment (Live)
```

### Step-by-Step

#### Phase 1: Local Testing (30 minutes)
```bash
# 1. Start application locally
./scripts/start.sh

# 2. Test admin login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@vrenum.app",
    "password": "Namaskah@Admin2024"
  }'

# 3. Run test suite
pytest tests/ -v

# 4. Check logs
tail -f logs/app.log
```

#### Phase 2: Docker Testing (30 minutes)
```bash
# 1. Start Docker environment
cd deploy/docker
docker-compose up -d

# 2. Wait for services to start
sleep 10

# 3. Test admin login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@vrenum.app",
    "password": "Namaskah@Admin2024"
  }'

# 4. Test web UI
open http://localhost:8000/login

# 5. Run integration tests
pytest tests/integration/ -v

# 6. Cleanup
docker-compose down
```

#### Phase 3: Staging Deployment (2-4 hours)
```bash
# 1. Deploy to staging server
bash scripts/deployment/deploy_production.sh staging

# 2. Run smoke tests
pytest tests/smoke/ -v

# 3. Test admin credentials
curl -X POST https://staging.vrenum.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@vrenum.app",
    "password": "Namaskah@Admin2024"
  }'

# 4. Run full test suite
pytest tests/ -v

# 5. Manual testing
# - Login via web UI
# - Test all admin features
# - Test all integrations
# - Verify monitoring

# 6. Performance testing
# - Load testing
# - Stress testing
# - Endurance testing
```

#### Phase 4: Production Deployment (1 hour)
```bash
# 1. Final verification
# - All staging tests passed
# - Team approval obtained
# - Backup created
# - Rollback plan ready

# 2. Deploy to production
bash scripts/deployment/deploy_production.sh production

# 3. Verify deployment
curl -X POST https://vrenum.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@vrenum.app",
    "password": "Namaskah@Admin2024"
  }'

# 4. Monitor
# - Check logs
# - Monitor errors (Sentry)
# - Monitor uptime (Better Stack)
# - Monitor performance
```

---

## Testing Checklist

### Pre-Deployment Testing

#### Local Environment
- [ ] Admin login works locally
- [ ] All tests pass
- [ ] No errors in logs
- [ ] Database migrations work
- [ ] Redis cache works

#### Docker Environment
- [ ] Docker containers start
- [ ] Admin login works in Docker
- [ ] All services communicate
- [ ] Integration tests pass
- [ ] Performance acceptable

#### Staging Environment
- [ ] Staging deployment successful
- [ ] Admin login works on staging
- [ ] All features work
- [ ] Integrations work
- [ ] Monitoring works
- [ ] Performance acceptable
- [ ] Security headers present
- [ ] SSL certificate valid
- [ ] Backups working
- [ ] Team approval obtained

### Production Deployment

- [ ] Backup created
- [ ] Rollback plan ready
- [ ] Monitoring configured
- [ ] Alerts configured
- [ ] Team notified
- [ ] Deployment window scheduled
- [ ] Admin credentials verified
- [ ] All systems operational
- [ ] Performance acceptable
- [ ] No errors in logs

---

## Testing Scripts

### Create Test Script

```bash
#!/bin/bash
# test-admin-credentials.sh

set -e

echo "🧪 Testing Admin Credentials"
echo "================================"

# Configuration
API_URL="${1:-http://localhost:8000}"
EMAIL="admin@vrenum.app"
PASSWORD="Namaskah@Admin2024"

echo "Testing against: $API_URL"
echo ""

# Test 1: Login
echo "Test 1: Admin Login"
RESPONSE=$(curl -s -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"password\": \"$PASSWORD\"
  }")

TOKEN=$(echo $RESPONSE | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
  echo "❌ Login failed"
  echo "Response: $RESPONSE"
  exit 1
fi

echo "✅ Login successful"
echo "Token: ${TOKEN:0:20}..."
echo ""

# Test 2: Get User Info
echo "Test 2: Get User Info"
USER_RESPONSE=$(curl -s -X GET "$API_URL/api/auth/me" \
  -H "Authorization: Bearer $TOKEN")

IS_ADMIN=$(echo $USER_RESPONSE | jq -r '.is_admin')

if [ "$IS_ADMIN" != "true" ]; then
  echo "❌ User is not admin"
  exit 1
fi

echo "✅ User is admin"
echo ""

# Test 3: Access Admin Dashboard
echo "Test 3: Access Admin Dashboard"
ADMIN_RESPONSE=$(curl -s -X GET "$API_URL/admin" \
  -H "Authorization: Bearer $TOKEN")

if echo $ADMIN_RESPONSE | grep -q "error"; then
  echo "❌ Admin dashboard access failed"
  exit 1
fi

echo "✅ Admin dashboard accessible"
echo ""

# Test 4: Health Check
echo "Test 4: Health Check"
HEALTH=$(curl -s -X GET "$API_URL/health")

if echo $HEALTH | grep -q "ok"; then
  echo "✅ Application healthy"
else
  echo "⚠️  Application health check inconclusive"
fi

echo ""
echo "================================"
echo "✅ All tests passed!"
```

### Run Test Script

```bash
# Local testing
bash test-admin-credentials.sh http://localhost:8000

# Docker testing
bash test-admin-credentials.sh http://localhost:8000

# Staging testing
bash test-admin-credentials.sh https://staging.vrenum.app

# Production testing
bash test-admin-credentials.sh https://vrenum.app
```

---

## Troubleshooting

### Login Fails

```bash
# Check if user exists
sudo -u postgres psql -d vrenum -c "SELECT email, is_admin FROM users WHERE email='admin@vrenum.app';"

# Check password hash
sudo -u postgres psql -d vrenum -c "SELECT email, password_hash FROM users WHERE email='admin@vrenum.app';"

# Verify password
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
# Check admin flag
sudo -u postgres psql -d vrenum -c "SELECT email, is_admin FROM users WHERE email='admin@vrenum.app';"

# Update admin flag if needed
sudo -u postgres psql -d vrenum -c "UPDATE users SET is_admin=true WHERE email='admin@vrenum.app';"
```

### Token Invalid

```bash
# Check JWT configuration
grep JWT_SECRET_KEY .env

# Verify token expiration
python3 << 'EOF'
import jwt
token = "eyJ..."  # Your token
decoded = jwt.decode(token, options={"verify_signature": False})
print(decoded)
EOF
```

---

## Recommendation

### Best Practice Flow

1. **Local Testing** (30 min)
   - Test on your machine
   - Run full test suite
   - Verify all features

2. **Docker Testing** (30 min)
   - Test in Docker environment
   - Simulate production setup
   - Run integration tests

3. **Staging Deployment** (2-4 hours)
   - Deploy to staging server
   - Run comprehensive tests
   - Get team approval
   - Verify all integrations

4. **Production Deployment** (1 hour)
   - Deploy to production
   - Monitor closely
   - Be ready to rollback

### Timeline

- **Total Testing Time:** 4-6 hours
- **Deployment Time:** 1 hour
- **Monitoring Time:** 1-2 hours post-deployment

---

## Decision Matrix

| Scenario | Approach | Time | Risk |
|----------|----------|------|------|
| First deployment | Test First (Staging) | 6 hours | Low |
| Small update | Test First (Local + Docker) | 2 hours | Low |
| Hotfix | Deploy First (with monitoring) | 1 hour | Medium |
| Major change | Test First (Full pipeline) | 8 hours | Low |

---

## Conclusion

### Recommended: **Test First, Then Deploy**

**Why:**
- ✅ Catch issues before production
- ✅ Verify all integrations work
- ✅ No impact on live users
- ✅ Can rollback if needed
- ✅ Team can validate together

**Process:**
1. Local testing (30 min)
2. Docker testing (30 min)
3. Staging deployment (2-4 hours)
4. Production deployment (1 hour)

**Total Time:** 4-6 hours for comprehensive testing

---

**Status:** Ready for testing  
**Date:** October 25, 2026  
**Version:** 1.0
