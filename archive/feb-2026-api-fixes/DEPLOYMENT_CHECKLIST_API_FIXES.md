# API 404 Fixes - Deployment Checklist

## Pre-Deployment ✅

- [x] Code implemented
- [x] Syntax validation passed
- [x] Automated tests passed
- [x] Documentation created
- [x] Architecture diagrams created
- [x] Quick reference guide created

## Deployment Steps

### 1. Backup Current State
```bash
# Backup current code
git add .
git commit -m "Backup before API fixes deployment"

# Backup database (if needed)
# pg_dump namaskah > backup_$(date +%Y%m%d).sql
```

### 2. Deploy Changes
```bash
# Pull latest changes (if using git)
git pull origin main

# Or manually copy files:
# - app/api/compatibility_routes.py (NEW)
# - main.py (MODIFIED)
```

### 3. Restart Application
```bash
# Stop current server
# pkill -f "uvicorn main:app"

# Start server
./start.sh

# Or with uvicorn directly
# uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Verify Deployment
```bash
# Run automated tests
python3 test_api_fixes.py

# Expected output:
# ✅ ALL TESTS PASSED
```

### 5. Manual Verification
```bash
# Get auth token first
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@namaskah.app","password":"Namaskah@Admin2024"}' \
  | jq -r '.access_token')

# Test each fixed endpoint
echo "Testing /api/billing/balance..."
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/billing/balance

echo "Testing /api/user/me..."
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/user/me

echo "Testing /api/tiers/current..."
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/tiers/current

echo "Testing /api/notifications/categories..."
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/notifications/categories

echo "Testing /api/user/settings..."
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/user/settings
```

### 6. Check Logs
```bash
# Monitor logs for errors
tail -f logs/app.log

# Look for:
# ✅ "GET /api/billing/balance HTTP/1.1" 200 OK
# ✅ "GET /api/user/me HTTP/1.1" 200 OK
# ✅ "GET /api/tiers/current HTTP/1.1" 200 OK

# Should NOT see:
# ❌ "GET /api/billing/balance HTTP/1.1" 404 Not Found
```

### 7. Frontend Verification
```bash
# Open application in browser
open http://localhost:8000

# Login and check:
# - Dashboard loads without errors
# - Balance displays correctly
# - User info displays correctly
# - Tier information displays correctly
# - No 404 errors in browser console
```

## Post-Deployment Monitoring

### Hour 1: Immediate Monitoring
- [ ] Check error logs every 15 minutes
- [ ] Monitor 404 error rate (should be ~0%)
- [ ] Verify user reports (should be none)
- [ ] Check response times (should be unchanged)

### Day 1: Active Monitoring
- [ ] Review error logs 3x per day
- [ ] Monitor API endpoint usage
- [ ] Check for any regression issues
- [ ] Verify all features working

### Week 1: Passive Monitoring
- [ ] Daily log review
- [ ] Track compatibility route usage
- [ ] Monitor performance metrics
- [ ] Collect user feedback

## Success Criteria

### Technical Metrics
- ✅ 404 error rate < 1%
- ✅ All compatibility routes return 200 OK
- ✅ Response times unchanged (< 500ms)
- ✅ No new errors introduced
- ✅ All tests passing

### User Experience
- ✅ Dashboard loads without errors
- ✅ Balance displays correctly
- ✅ User info displays correctly
- ✅ No console errors
- ✅ Smooth user experience

## Rollback Procedure

If issues occur:

### Quick Rollback (< 1 minute)
```bash
# 1. Edit main.py
# Comment out line:
# fastapi_app.include_router(compatibility_router, prefix="/api")

# 2. Restart server
./start.sh
```

### Full Rollback (< 5 minutes)
```bash
# 1. Restore from git
git checkout HEAD~1 main.py
rm app/api/compatibility_routes.py

# 2. Restart server
./start.sh

# 3. Verify
python3 test_api_fixes.py  # Should fail (expected)
```

## Troubleshooting

### Issue: Import Error
```
Error: ModuleNotFoundError: No module named 'app.api.compatibility_routes'
```

**Solution:**
```bash
# Verify file exists
ls -la app/api/compatibility_routes.py

# Check Python path
python3 -c "import sys; print(sys.path)"

# Restart server
./start.sh
```

### Issue: 404 Still Occurring
```
GET /api/billing/balance HTTP/1.1" 404 Not Found
```

**Solution:**
```bash
# Check router registration
python3 test_api_fixes.py

# Verify main.py changes
grep "compatibility_router" main.py

# Restart server
./start.sh
```

### Issue: Authentication Error
```
401 Unauthorized
```

**Solution:**
```bash
# Verify token is valid
echo $TOKEN

# Get new token
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@namaskah.app","password":"Namaskah@Admin2024"}' \
  | jq -r '.access_token')

# Retry request
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/billing/balance
```

## Documentation Links

- [API_FIXES_SUMMARY.md](../API_FIXES_SUMMARY.md) - Complete summary
- [API_QUICK_REFERENCE.md](../API_QUICK_REFERENCE.md) - Quick reference
- [docs/API_404_FIXES.md](./API_404_FIXES.md) - Technical details
- [docs/API_COMPATIBILITY_ARCHITECTURE.md](./API_COMPATIBILITY_ARCHITECTURE.md) - Architecture

## Support Contacts

- **Technical Issues**: Check logs at `logs/app.log`
- **Questions**: See documentation above
- **Emergency**: Rollback using procedure above

---

## Deployment Sign-Off

- [ ] Pre-deployment checklist complete
- [ ] Deployment steps executed
- [ ] Verification tests passed
- [ ] Monitoring plan in place
- [ ] Rollback procedure documented
- [ ] Team notified

**Deployed By**: _________________  
**Date**: _________________  
**Time**: _________________  
**Status**: ✅ Success / ❌ Rolled Back

---

**Ready for Production** ✅
