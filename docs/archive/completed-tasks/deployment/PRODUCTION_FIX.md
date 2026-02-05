# Production Deployment Fix - Missing aiohttp Dependency

## Issue
Production deployment failing with:
```
ModuleNotFoundError: No module named 'aiohttp'
```

## Root Cause
The Phase 2.5 Notification System (mobile push notifications) requires `aiohttp` for making HTTP requests to FCM/APNs, but this dependency was not added to `requirements.txt`.

## Fix Applied
Added `aiohttp==3.9.1` to `requirements.txt` under Phase 2.5 dependencies section.

## Files Modified
- `requirements.txt` - Added aiohttp dependency

## Commit and Deploy

```bash
# Stage the fix
git add requirements.txt

# Commit
git commit -m "fix: add missing aiohttp dependency for mobile push notifications

- Added aiohttp==3.9.1 to requirements.txt
- Required for Phase 2.5 mobile notification service
- Fixes production deployment ModuleNotFoundError"

# Push to trigger deployment
git push origin main
```

## Verification
After deployment, check:
1. Application starts successfully
2. No import errors in logs
3. Health check endpoint responds: `curl https://namaskah.app/health`
4. Mobile notification endpoints are accessible

## Additional Notes
- aiohttp is used by `app/services/mobile_notification_service.py`
- Required for FCM (Firebase Cloud Messaging) and APNs (Apple Push Notification service)
- Version 3.9.1 is stable and compatible with Python 3.11
