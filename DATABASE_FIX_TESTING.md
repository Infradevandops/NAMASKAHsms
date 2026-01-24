# DATABASE SCHEMA FIX - TESTING GUIDE

## 🎯 **No Shell Access? No Problem!**

You can now check and fix the database schema via API endpoints.

---

## 📊 **STEP 1: Check Database Status**

### Endpoint: `GET /api/health/db-schema`

**Public endpoint** - No authentication required

```bash
curl https://namaskah.onrender.com/api/health/db-schema
```

### Expected Responses:

**✅ If Fixed (Healthy)**:
```json
{
  "status": "healthy",
  "database": "connected",
  "schema_version": "4.0.0",
  "critical_features": {
    "idempotency_protection": true,
    "verification_creation": true,
    "polling_services": true
  },
  "message": "All systems operational"
}
```

**🔴 If Broken (Degraded)**:
```json
{
  "status": "degraded",
  "database": "connected",
  "schema_version": "4.0.0",
  "critical_features": {
    "idempotency_protection": false,
    "verification_creation": false,
    "polling_services": false
  },
  "message": "Database migration pending"
}
```

---

## 🔧 **STEP 2: Fix Database (If Needed)**

### Endpoint: `POST /api/admin/db/fix-schema`

**Admin only** - Requires admin authentication

```bash
curl -X POST https://namaskah.onrender.com/api/admin/db/fix-schema \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Expected Response:

**✅ Success**:
```json
{
  "status": "success",
  "fixes_applied": [
    "Added idempotency_key column and index"
  ],
  "message": "Database schema is now up to date"
}
```

**✅ Already Fixed**:
```json
{
  "status": "success",
  "fixes_applied": [
    "No fixes needed"
  ],
  "message": "Database schema is now up to date"
}
```

---

## 🧪 **STEP 3: Verify Fix Worked**

### Test Verification Creation

```bash
curl -X POST https://namaskah.onrender.com/api/v1/verify/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "telegram",
    "country": "US",
    "idempotency_key": "test-'$(date +%s)'"
  }'
```

**Expected**: `201 Created` with verification details

**Before Fix**: `500 Internal Server Error`

---

## 📋 **Quick Test Checklist**

1. **Check Status**:
   ```bash
   curl https://namaskah.onrender.com/api/health/db-schema | jq .status
   ```
   - Should return: `"healthy"` or `"degraded"`

2. **If Degraded, Apply Fix** (as admin):
   ```bash
   curl -X POST https://namaskah.onrender.com/api/admin/db/fix-schema \
     -H "Authorization: Bearer $ADMIN_TOKEN" | jq
   ```

3. **Verify Status Again**:
   ```bash
   curl https://namaskah.onrender.com/api/health/db-schema | jq .status
   ```
   - Should now return: `"healthy"`

4. **Test Verification Creation**:
   - Go to https://namaskah.onrender.com/verify
   - Select a service
   - Click "Get SMS Code"
   - Should work without 500 error

---

## 🔍 **Monitoring**

### Watch Logs for Success:
```
✅ Successfully added idempotency_key column and index
```

### Watch Logs for Errors Stopping:
Before fix:
```
ERROR - Error in poll_voice_verifications: column verifications.idempotency_key does not exist
```

After fix:
```
INFO - Voice polling service started
INFO - SMS polling service started
```

---

## 🚨 **Troubleshooting**

### Issue: "Database migration pending" persists

**Solution 1**: Wait for Render.com deployment to complete (3-5 min)

**Solution 2**: Manually trigger fix via admin endpoint

**Solution 3**: Check Render.com logs for build errors

### Issue: Admin endpoint returns 401/403

**Cause**: Not authenticated as admin

**Solution**: 
1. Login as admin user
2. Get JWT token from response
3. Use token in Authorization header

---

## 📊 **Alternative: Browser Testing**

1. Open: https://namaskah.onrender.com/api/health/db-schema
2. Check JSON response in browser
3. Look for `"status": "healthy"`

---

## ⏱️ **Timeline**

- **Deployment**: ~3-5 minutes after push
- **Health Check**: Instant
- **Fix Application**: ~1 second
- **Verification**: Instant

---

**Created**: January 24, 2026  
**Status**: Ready for testing
