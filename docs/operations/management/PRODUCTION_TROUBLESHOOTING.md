# Production Issue Troubleshooting

**Status**: Investigating  
**Date**: February 5, 2026

---

## 🔍 What's Not Working?

Please provide:

1. **Error message** or symptoms
2. **Which feature** is broken (login, payment, API, etc.)
3. **When** it started (after deployment, specific time)
4. **Error logs** from production

---

## 🚨 Common Production Issues & Fixes

### 1. Login Not Working

**Symptoms**: Can't login with admin@namaskah.app

**Check**:
```bash
# Check if user exists
psql $DATABASE_URL -c "SELECT email, is_admin, is_active FROM users WHERE email='admin@namaskah.app';"

# Check password hash
psql $DATABASE_URL -c "SELECT email, password_hash IS NOT NULL as has_password FROM users WHERE email='admin@namaskah.app';"
```

**Fix**:
```bash
# Reset admin password
psql $DATABASE_URL -c "
UPDATE users 
SET password_hash = '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqJfLKZvSu',
    is_active = true,
    is_admin = true
WHERE email = 'admin@namaskah.app';
"
# Password will be: Admin123!
```

### 2. Database Connection Issues

**Symptoms**: 500 errors, connection refused

**Check**:
```bash
# Test database connection
psql $DATABASE_URL -c "SELECT 1;"

# Check connection string
echo $DATABASE_URL | sed 's/:[^:]*@/:***@/'
```

**Fix**:
```bash
# Update DATABASE_URL in environment
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"

# Restart service
systemctl restart namaskah-api
```

### 3. Payment Tables Missing

**Symptoms**: Payment errors, table not found

**Check**:
```bash
# Check if tables exist
psql $DATABASE_URL -c "\dt payment_logs"
psql $DATABASE_URL -c "\dt sms_transactions"
```

**Fix**:
```bash
# Run migration
psql $DATABASE_URL -f scripts/create_payment_tables.sql

# Verify
psql $DATABASE_URL -c "SELECT COUNT(*) FROM payment_logs;"
```

### 4. Redis Connection Issues

**Symptoms**: Rate limiting not working, lock errors

**Check**:
```bash
# Test Redis connection
redis-cli -u $REDIS_URL ping

# Check if Redis is running
systemctl status redis
```

**Fix**:
```bash
# Start Redis
systemctl start redis

# Update REDIS_URL
export REDIS_URL="redis://localhost:6379"
```

### 5. Import Errors

**Symptoms**: Module not found, import errors

**Check**:
```bash
# Test imports
python3 -c "from app.services.payment_service import PaymentService"
python3 -c "from app.middleware.rate_limiting import rate_limit"
```

**Fix**:
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Restart service
systemctl restart namaskah-api
```

---

## 🔧 Quick Diagnostic Commands

```bash
# 1. Check service status
systemctl status namaskah-api

# 2. Check recent logs
journalctl -u namaskah-api -n 50 --no-pager

# 3. Check database
psql $DATABASE_URL -c "SELECT version();"

# 4. Check Redis
redis-cli ping

# 5. Test API
curl https://api.namaskah.app/health

# 6. Check environment variables
env | grep -E "DATABASE_URL|REDIS_URL|SECRET_KEY" | sed 's/=.*/=***/'
```

---

## 📝 Provide These Details

To help fix the issue, please provide:

```bash
# 1. Error logs
journalctl -u namaskah-api -n 100 --no-pager > error_logs.txt

# 2. Service status
systemctl status namaskah-api > service_status.txt

# 3. Database status
psql $DATABASE_URL -c "\dt" > db_tables.txt

# 4. Environment check
env | grep -E "DATABASE|REDIS|SECRET" | sed 's/=.*/=***/' > env_check.txt
```

---

## 🚀 Emergency Fixes

### Fix 1: Restart Everything
```bash
systemctl restart namaskah-api
systemctl restart redis
systemctl restart postgresql
```

### Fix 2: Reset Admin User
```bash
psql $DATABASE_URL << EOF
UPDATE users 
SET password_hash = '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqJfLKZvSu',
    is_active = true,
    is_admin = true,
    email_verified = true
WHERE email = 'admin@namaskah.app';
EOF
```

### Fix 3: Rollback Payment Changes
```bash
# If payment hardening is causing issues
git revert 7217b01
git push origin main
```

---

## 📞 Next Steps

1. **Describe the issue**: What exactly is not working?
2. **Share error logs**: Copy error messages
3. **Specify environment**: Production URL, hosting platform
4. **Recent changes**: What was deployed recently?

**I'll provide a specific fix once I know the issue.**
