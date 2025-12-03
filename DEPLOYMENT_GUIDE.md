# Production Deployment Guide

## Pre-Deployment Checklist

### 1. Environment Configuration
```bash
# Verify .env.production exists and has all required variables
cat .env.production

# Required variables:
# - ENVIRONMENT=production
# - SECRET_KEY (32+ chars)
# - JWT_SECRET_KEY (32+ chars)
# - DATABASE_URL (PostgreSQL)
# - TEXTVERIFIED_API_KEY
# - PAYSTACK_SECRET_KEY
# - BASE_URL (https://namaskah.onrender.com)
# - CORS_ORIGINS
```

### 2. Database Setup
```bash
# Ensure database is accessible
psql $DATABASE_URL -c "SELECT 1"

# Apply migrations
alembic upgrade head

# Verify tables exist
psql $DATABASE_URL -c "\dt"
```

### 3. Static Files
```bash
# Verify static files exist
ls -la static/css/dashboard.css
ls -la static/js/dashboard.js
ls -la static/js/auth-check.js
```

### 4. Templates
```bash
# Verify templates exist
ls -la templates/dashboard.html
ls -la templates/landing_modern.html
ls -la templates/auth_simple.html
```

---

## Deployment Steps

### Step 1: Run Validation
```bash
# Run comprehensive validation
python3 scripts/validate_production.py

# Expected output:
# ✅ Environment variables configured
# ✅ Static files present
# ✅ Templates present
# ✅ All imports successful
# ✅ Database connected
# RESULTS: 5/5 checks passed
```

### Step 2: Apply Migrations
```bash
# Apply any pending database migrations
alembic upgrade head

# Verify migrations applied
alembic current
```

### Step 3: Start Server
```bash
# Option 1: Using production script (recommended)
./start_production.sh

# Option 2: Manual start with Uvicorn
export $(cat .env.production | grep -v '^#' | xargs)
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --loop uvloop
```

### Step 4: Verify Deployment
```bash
# Check health endpoint
curl https://namaskah.onrender.com/api/system/health

# Check diagnostics
curl https://namaskah.onrender.com/api/diagnostics

# Test landing page
curl https://namaskah.onrender.com/

# Test authentication
curl -X POST https://namaskah.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'
```

---

## Post-Deployment Verification

### 1. Frontend Verification
- [ ] Landing page loads at `/`
- [ ] Dashboard loads at `/dashboard` (when authenticated)
- [ ] Login page loads at `/auth/login`
- [ ] CSS styling is applied
- [ ] JavaScript is working (check console)
- [ ] Images and fonts load correctly

### 2. API Verification
```bash
# Get health status
curl https://namaskah.onrender.com/api/system/health

# Get diagnostics
curl https://namaskah.onrender.com/api/diagnostics

# Test user balance (requires token)
curl -H "Authorization: Bearer TOKEN" \
  https://namaskah.onrender.com/api/user/balance

# Test countries endpoint
curl https://namaskah.onrender.com/api/verification/textverified/countries

# Test services endpoint
curl https://namaskah.onrender.com/api/verification/textverified/services
```

### 3. Authentication Verification
```bash
# Register new user
curl -X POST https://namaskah.onrender.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPassword123"}'

# Login
curl -X POST https://namaskah.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPassword123"}'

# Refresh token
curl -X POST https://namaskah.onrender.com/api/auth/refresh \
  -H "Authorization: Bearer REFRESH_TOKEN"

# Logout
curl -X POST https://namaskah.onrender.com/api/auth/logout \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

### 4. Database Verification
```bash
# Check database connection
psql $DATABASE_URL -c "SELECT count(*) FROM users;"

# Check active connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# Check table sizes
psql $DATABASE_URL -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

---

## Monitoring

### Real-Time Logs
```bash
# Follow application logs
tail -f server.log

# Filter for errors
tail -f server.log | grep ERROR

# Filter for specific module
tail -f server.log | grep "verification"
```

### Health Checks
```bash
# Set up periodic health checks
watch -n 60 'curl -s https://namaskah.onrender.com/api/system/health | jq'

# Or use a monitoring service
# - Uptime Robot
# - Pingdom
# - New Relic
```

### Database Monitoring
```bash
# Monitor active queries
watch -n 5 'psql $DATABASE_URL -c "SELECT pid, usename, query FROM pg_stat_activity WHERE state = '\''active'\'';"'

# Monitor connection count
watch -n 5 'psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"'

# Monitor slow queries (if enabled)
psql $DATABASE_URL -c "SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

---

## Troubleshooting

### Issue: Landing page instead of dashboard
```bash
# Check authentication
curl -H "Authorization: Bearer TOKEN" \
  https://namaskah.onrender.com/api/user/balance

# Check CORS
curl -H "Origin: https://namaskah.onrender.com" \
  https://namaskah.onrender.com/api/system/health

# Check token validation
# See PRODUCTION_TROUBLESHOOTING.md
```

### Issue: CSS/JS not loading
```bash
# Check static files
curl -I https://namaskah.onrender.com/static/css/dashboard.css
# Should return: Content-Type: text/css; charset=utf-8

# Check MIME types
curl -I https://namaskah.onrender.com/static/js/dashboard.js
# Should return: Content-Type: application/javascript; charset=utf-8
```

### Issue: API errors
```bash
# Check diagnostics
curl https://namaskah.onrender.com/api/diagnostics

# Check logs
tail -f server.log | grep ERROR

# Check database
psql $DATABASE_URL -c "SELECT 1"
```

---

## Performance Optimization

### 1. Enable Caching
```python
# Already enabled in main.py
from app.core.unified_cache import cache
```

### 2. Database Connection Pooling
```python
# Configured in app/core/database.py
# Pool size: 10
# Max overflow: 20
```

### 3. Compression
```python
# Already enabled in main.py
GZipMiddleware(minimum_size=1000)
```

### 4. Worker Configuration
```bash
# Recommended workers = (2 × CPU cores) + 1
# For 2 CPU: 5 workers
# For 4 CPU: 9 workers

uvicorn main:app --workers 4 --loop uvloop --http httptools
```

---

## Scaling

### Horizontal Scaling
```bash
# Use load balancer (nginx, HAProxy)
# Run multiple instances on different ports
# Configure sticky sessions for authentication

# Example with nginx
upstream namaskah {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}

server {
    listen 443 ssl;
    server_name namaskah.onrender.com;
    
    location / {
        proxy_pass http://namaskah;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Vertical Scaling
```bash
# Increase worker count
uvicorn main:app --workers 8

# Increase database pool size
# In app/core/database.py
database_pool_size: int = 20
database_max_overflow: int = 40
```

---

## Backup & Recovery

### Database Backup
```bash
# Full backup
pg_dump $DATABASE_URL > backup.sql

# Compressed backup
pg_dump $DATABASE_URL | gzip > backup.sql.gz

# Restore from backup
psql $DATABASE_URL < backup.sql
```

### Application Backup
```bash
# Backup static files
tar -czf static-backup.tar.gz static/

# Backup templates
tar -czf templates-backup.tar.gz templates/

# Backup environment
cp .env.production .env.production.backup
```

---

## Rollback Procedure

If deployment fails:

```bash
# 1. Stop current process
pkill -f "uvicorn main:app"

# 2. Check git status
git status

# 3. Revert to previous version
git checkout HEAD~1

# 4. Restore environment if needed
cp .env.production.backup .env.production

# 5. Restart application
./start_production.sh

# 6. Verify
curl https://namaskah.onrender.com/api/system/health
```

---

## Security Checklist

- [ ] HTTPS enabled (SSL certificate valid)
- [ ] SECRET_KEY and JWT_SECRET_KEY are strong (32+ chars)
- [ ] Database password is strong
- [ ] API keys are not exposed in logs
- [ ] CORS origins are restricted
- [ ] Rate limiting is enabled
- [ ] CSRF protection is enabled
- [ ] XSS protection is enabled
- [ ] SQL injection protection is enabled
- [ ] Sensitive data is not logged
- [ ] Database backups are encrypted
- [ ] Access logs are monitored

---

## Support & Documentation

- **Troubleshooting**: See `PRODUCTION_TROUBLESHOOTING.md`
- **Fixes Applied**: See `PRODUCTION_FIXES.md`
- **API Documentation**: See `docs/API_DOCUMENTATION.md`
- **Security**: See `docs/SECURITY_AND_COMPLIANCE.md`

---

## Emergency Contacts

- **Database Issues**: Check database provider dashboard
- **API Issues**: Check logs and diagnostics endpoint
- **Frontend Issues**: Check browser console
- **Authentication Issues**: Check token validation

---

## Next Steps

1. Deploy to production
2. Monitor logs and health checks
3. Test all user flows
4. Set up automated backups
5. Configure monitoring alerts
6. Document any custom configurations
7. Train team on deployment procedures
