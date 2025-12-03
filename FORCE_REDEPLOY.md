# Force Production Redeploy

## Current Issue
Production is showing stale code error:
```
NameError: name 'Session' is not defined in dashboard.py
```

This is from an **old container** that hasn't been redeployed with the latest code.

## Verification
✅ Local code is correct:
```bash
python3 -m py_compile app/api/admin/dashboard.py
# Result: ✅ dashboard.py syntax valid
```

✅ All imports present:
```bash
grep "from sqlalchemy.orm import Session" app/api/admin/dashboard.py
# Result: ✅ Found
```

## Solution: Force Redeploy

### Option 1: Render.com Dashboard (Recommended)
1. Go to https://dashboard.render.com
2. Select your service
3. Click "Manual Deploy" → "Deploy latest commit"
4. Wait for deployment to complete
5. Verify: `curl https://namaskah.onrender.com/api/system/health`

### Option 2: Git Push Trigger
```bash
# Make a small change and push to trigger redeploy
echo "# Force redeploy" >> FORCE_REDEPLOY.md
git add FORCE_REDEPLOY.md
git commit -m "chore: force production redeploy"
git push origin main
```

### Option 3: SSH to Production (If Available)
```bash
# SSH into production server
ssh user@production-server

# Stop current process
pkill -f "uvicorn main:app"

# Pull latest code
cd /app
git pull origin main

# Start with new code
./start_production.sh
```

## What Changed
- ✅ Fixed CORS configuration
- ✅ Fixed JWT authentication
- ✅ Fixed middleware conflicts
- ✅ Fixed MIME types
- ✅ Added diagnostics
- ✅ Added validation
- ✅ Fixed startup script

## After Redeploy
```bash
# Verify health
curl https://namaskah.onrender.com/api/system/health

# Should return:
# {"status":"healthy","database":"connected","authentication":"active"}

# Check diagnostics
curl https://namaskah.onrender.com/api/diagnostics

# Test authentication
curl -X POST https://namaskah.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'
```

## Git Status
- Latest commit: `ea30747`
- Branch: `main`
- Status: Ready for deployment

## Timeline
1. Code fixed locally ✅
2. Committed to git ✅
3. Pushed to GitHub ✅
4. **Waiting for production redeploy** ⏳

**Next Step: Trigger production redeploy using one of the options above**
