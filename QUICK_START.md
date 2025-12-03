# Quick Start - Production Deployment

## TL;DR - Deploy in 3 Steps

### Step 1: Validate
```bash
python3 scripts/validate_production.py
```

### Step 2: Start
```bash
./start_production.sh
```

### Step 3: Verify
```bash
curl https://namaskah.onrender.com/api/system/health
```

---

## What Was Fixed

| Issue | Status | Impact |
|-------|--------|--------|
| CORS hardcoded to wrong domain | ✅ Fixed | API calls now work |
| JWT secret key mismatch | ✅ Fixed | Authentication now works |
| Duplicate middleware | ✅ Fixed | No conflicts |
| Static files MIME types | ✅ Fixed | CSS/JS load correctly |
| No diagnostics | ✅ Added | Can debug issues |
| No validation | ✅ Added | Catch errors early |
| Manual startup | ✅ Automated | Consistent deployment |

---

## Key Endpoints

```bash
# Health check
curl https://namaskah.onrender.com/api/system/health

# Full diagnostics
curl https://namaskah.onrender.com/api/diagnostics

# Login
curl -X POST https://namaskah.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'

# Check balance (requires token)
curl -H "Authorization: Bearer TOKEN" \
  https://namaskah.onrender.com/api/user/balance
```

---

## Troubleshooting

### Landing page instead of dashboard?
```bash
# Check authentication
curl -H "Authorization: Bearer TOKEN" \
  https://namaskah.onrender.com/api/user/balance
# Should return balance, not 401
```

### CSS/JS not loading?
```bash
# Check MIME types
curl -I https://namaskah.onrender.com/static/css/dashboard.css
# Should show: Content-Type: text/css; charset=utf-8
```

### API errors?
```bash
# Check diagnostics
curl https://namaskah.onrender.com/api/diagnostics

# Check logs
tail -f server.log
```

---

## Files Changed

- ✅ `main.py` - CORS, middleware, diagnostics
- ✅ `app/core/dependencies.py` - JWT secret key
- ✅ `templates/dashboard.html` - Auth check script
- ✅ `static/js/auth-check.js` - New auth verification
- ✅ `scripts/validate_production.py` - New validation
- ✅ `start_production.sh` - New startup script

---

## Environment Check

```bash
# Verify .env.production has:
grep -E "ENVIRONMENT|SECRET_KEY|JWT_SECRET_KEY|DATABASE_URL|BASE_URL" .env.production

# Should show:
# ENVIRONMENT=production
# SECRET_KEY=...
# JWT_SECRET_KEY=...
# DATABASE_URL=postgresql://...
# BASE_URL=https://namaskah.onrender.com
```

---

## Deployment Commands

```bash
# Full deployment
./start_production.sh

# Or manual:
export $(cat .env.production | grep -v '^#' | xargs)
alembic upgrade head
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Monitoring

```bash
# Watch logs
tail -f server.log

# Check health every 60 seconds
watch -n 60 'curl -s https://namaskah.onrender.com/api/system/health | jq'

# Monitor database
watch -n 5 'psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"'
```

---

## Rollback

```bash
# If something breaks
pkill -f "uvicorn main:app"
git checkout main.py app/core/dependencies.py
./start.sh
```

---

## Documentation

- **Full Guide**: `DEPLOYMENT_GUIDE.md`
- **Troubleshooting**: `PRODUCTION_TROUBLESHOOTING.md`
- **All Fixes**: `PRODUCTION_FIXES.md`
- **Summary**: `FIXES_SUMMARY.md`

---

## Status

✅ **READY FOR PRODUCTION**

All critical issues fixed. Application tested and verified.

Deploy with confidence! 🚀
