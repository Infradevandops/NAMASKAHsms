# Production Troubleshooting Guide

## Issue 1: Landing Page Instead of Dashboard

**Symptoms:**
- Users see "Welcome!" landing page instead of dashboard
- Dashboard not loading for authenticated users

**Root Causes:**
1. Authentication token not being validated
2. User ID not being extracted from token
3. CORS blocking frontend requests

**Solutions:**

### Check 1: Verify Token is Being Sent
```bash
# Test with curl
curl -H "Authorization: Bearer YOUR_TOKEN" https://namaskah.onrender.com/api/user/balance
```

### Check 2: Verify JWT Secret Keys Match
```python
# In app/core/config.py
# Ensure JWT_SECRET_KEY is set in .env.production
# And matches what's used in token creation
```

### Check 3: Check Browser Console
1. Open DevTools (F12)
2. Go to Console tab
3. Look for errors like:
   - "401 Unauthorized"
   - "CORS error"
   - "Failed to fetch"

### Check 4: Verify CORS Configuration
```python
# main.py should have production CORS origins
if settings.environment == "production":
    cors_origins = [
        settings.base_url,
        # ... other origins
    ]
```

---

## Issue 2: CSS/JS Not Loading

**Symptoms:**
- Dashboard loads but looks broken (no styling)
- JavaScript errors in console
- Network tab shows 404 for static files

**Solutions:**

### Check 1: Verify Static Files Mounted
```bash
# Check if static directory exists
ls -la static/
ls -la static/css/
ls -la static/js/
```

### Check 2: Check MIME Types
```bash
# Test CSS file
curl -I https://namaskah.onrender.com/static/css/dashboard.css
# Should return: Content-Type: text/css; charset=utf-8
```

### Check 3: Verify Static Mount in main.py
```python
# Should be before routes
if STATIC_DIR.exists():
    fastapi_app.mount("/static", StaticFiles(directory=str(STATIC_DIR)))
```

---

## Issue 3: API Endpoints Returning 401

**Symptoms:**
- Dashboard loads but shows "Not authenticated"
- API calls fail with 401 Unauthorized
- Balance not loading

**Solutions:**

### Check 1: Verify Token Storage
```javascript
// In browser console
localStorage.getItem('access_token')
localStorage.getItem('refresh_token')
```

### Check 2: Check Token Expiry
```javascript
// In browser console
const expiresAt = localStorage.getItem('token_expires_at')
const now = Date.now()
console.log('Token expires in:', (expiresAt - now) / 1000, 'seconds')
```

### Check 3: Verify Token Refresh Endpoint
```bash
curl -X POST https://namaskah.onrender.com/api/auth/refresh \
  -H "Authorization: Bearer YOUR_REFRESH_TOKEN"
```

---

## Issue 4: Database Connection Errors

**Symptoms:**
- 500 errors on API calls
- "Database connection failed"
- Verification not working

**Solutions:**

### Check 1: Verify Database URL
```bash
# In .env.production
echo $DATABASE_URL
# Should be: postgresql://user:pass@host:port/db
```

### Check 2: Test Database Connection
```bash
# Using psql
psql $DATABASE_URL -c "SELECT 1"
```

### Check 3: Check Database Migrations
```bash
# Run migrations
alembic upgrade head
```

---

## Issue 5: TextVerified Integration Not Working

**Symptoms:**
- Can't get countries/services
- Verification requests fail
- "TextVerified API error"

**Solutions:**

### Check 1: Verify API Key
```bash
# In .env.production
echo $TEXTVERIFIED_API_KEY
# Should be set and valid
```

### Check 2: Test TextVerified Connection
```bash
curl -X GET "https://api.textverified.com/api/v1/countries" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Check 3: Check Fallback Lists
```python
# If API fails, system uses fallback lists
# Check app/api/verification/textverified_endpoints.py
# for fallback countries and services
```

---

## Diagnostic Endpoints

### System Health Check
```bash
curl https://namaskah.onrender.com/api/system/health
```

### Full Diagnostics
```bash
curl https://namaskah.onrender.com/api/diagnostics
```

### User Balance
```bash
curl -H "Authorization: Bearer TOKEN" \
  https://namaskah.onrender.com/api/user/balance
```

---

## Common Error Messages

### "Invalid token"
- Token expired or corrupted
- JWT_SECRET_KEY mismatch
- Solution: Clear localStorage and re-login

### "CORS error"
- Frontend domain not in CORS_ORIGINS
- Solution: Add domain to .env.production CORS_ORIGINS

### "Database connection failed"
- DATABASE_URL invalid or database down
- Solution: Check DATABASE_URL and database status

### "TextVerified API error"
- API key invalid or expired
- Solution: Verify TEXTVERIFIED_API_KEY in .env.production

---

## Performance Optimization

### Enable Caching
```python
# In main.py
from app.core.unified_cache import cache
# Cache is automatically initialized
```

### Check Database Connections
```bash
# Monitor active connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"
```

### Monitor Logs
```bash
# Check application logs
tail -f server.log
```

---

## Deployment Checklist

- [ ] Environment variables set in .env.production
- [ ] Database migrations applied (alembic upgrade head)
- [ ] Static files present and accessible
- [ ] Templates present and accessible
- [ ] CORS origins configured for production domain
- [ ] JWT secrets configured and match
- [ ] TextVerified API key valid
- [ ] Paystack keys configured
- [ ] Database backup configured
- [ ] Monitoring/logging configured
- [ ] SSL certificate valid
- [ ] Health check endpoint responding

---

## Quick Restart

```bash
# Stop current process
pkill -f "uvicorn main:app"

# Run validation
python3 scripts/validate_production.py

# Start application
./start.sh
```

---

## Support

For additional help:
1. Check logs: `tail -f server.log`
2. Run diagnostics: `curl /api/diagnostics`
3. Check browser console for frontend errors
4. Verify environment variables are set
