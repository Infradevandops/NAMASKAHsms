# Force Production Redeploy

## Current Issue
Production container is running **stale code** with the old import error:
```
NameError: name 'Session' is not defined
File "/app/app/api/admin/dashboard.py", line 21
```

## Root Cause
- ✅ Code was fixed locally
- ✅ Code was committed and pushed to GitHub
- ❌ Production container hasn't been redeployed yet
- ❌ Still running old code from previous deployment

## Solution: Force Redeploy

### Option 1: Render.com Dashboard (Recommended)
1. Go to https://dashboard.render.com
2. Select your service (Namaskah SMS)
3. Click "Manual Deploy" → "Deploy latest commit"
4. Wait for deployment to complete
5. Verify: `curl https://namaskah.onrender.com/api/system/health`

### Option 2: Git Push Trigger
```bash
# Make a small change and push to trigger auto-deploy
echo "# Redeploy trigger" >> README.md
git add README.md
git commit -m "trigger: force production redeploy"
git push origin main
```

### Option 3: SSH into Production (if available)
```bash
# SSH to production server
ssh user@production-server

# Pull latest code
cd /app
git pull origin main

# Restart application
pkill -f "uvicorn main:app"
./start_production.sh
```

## What Will Happen After Redeploy
1. ✅ Latest code will be deployed
2. ✅ `Session` import will be available
3. ✅ Dashboard router will load correctly
4. ✅ Application will start successfully
5. ✅ Health check will pass

## Verification After Redeploy
```bash
# Check health
curl https://namaskah.onrender.com/api/system/health

# Check diagnostics
curl https://namaskah.onrender.com/api/diagnostics

# Check logs
# (via Render.com dashboard or SSH)
```

## Timeline
- **Commit pushed:** ✅ Done
- **Code on GitHub:** ✅ Done
- **Production redeployed:** ⏳ Pending
- **Error fixed:** ⏳ Pending (after redeploy)

## Next Steps
1. Go to Render.com dashboard
2. Click "Manual Deploy"
3. Wait ~2-3 minutes for deployment
4. Verify with health check

---

**Status:** Ready to redeploy, just need to trigger it on Render.com
