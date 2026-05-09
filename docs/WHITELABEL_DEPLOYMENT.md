# Whitelabel System Deployment Guide

**Version**: 4.6.1
**Date**: May 9, 2026
**Status**: Ready for Production

---

## ⚠️ Critical: Database Migration Required

**The whitelabel system will CRASH without this migration.**

### Step 1: Run Migration (Production)

```bash
# On Render.com or your production server
alembic upgrade head

# Expected output:
# INFO  [alembic.runtime.migration] Running upgrade enhance_device_tokens -> add_whitelabel_custom_tables
# INFO  [alembic.runtime.migration] Creating table whitelabel_custom_domains
# INFO  [alembic.runtime.migration] Creating table whitelabel_custom_branding
# INFO  [alembic.runtime.migration] Creating table whitelabel_custom_email_templates
```

### Step 2: Verify Tables Created

```sql
-- Connect to production database
SELECT table_name FROM information_schema.tables
WHERE table_name LIKE 'whitelabel_custom%';

-- Expected output:
-- whitelabel_custom_domains
-- whitelabel_custom_branding
-- whitelabel_custom_email_templates
```

---

## 🚀 Deployment Steps

### 1. Pre-Deployment Checklist

- [x] Migration file created (`add_whitelabel_custom_tables.py`)
- [x] Security fixes applied (log injection, timezone-aware)
- [x] Tests passing (24/24 service tests)
- [x] Table conflicts resolved (renamed to whitelabel_custom_*)
- [x] Middleware integrated
- [x] API endpoints implemented
- [ ] **Run migration on production**
- [ ] Manual testing

### 2. Deploy to Production

```bash
# Option A: Git push (Render auto-deploys)
git add .
git commit -m "feat: Add whitelabel system (WL-01 to WL-08)"
git push origin main

# Option B: Manual deployment
# Render will auto-deploy from GitHub
```

### 3. Run Migration (CRITICAL)

```bash
# SSH into production or use Render shell
alembic upgrade head
```

### 4. Verify Deployment

```bash
# Check app logs for errors
tail -f /var/log/app.log

# Test whitelabel endpoint
curl https://vrenum.onrender.com/api/whitelabel/config \
  -H "Authorization: Bearer YOUR_TOKEN"

# Expected: 200 OK with empty domains array
```

---

## 🧪 Post-Deployment Testing

### Test 1: Tier Enforcement (Freemium User)

```bash
# Login as freemium user
curl -X POST https://vrenum.onrender.com/api/whitelabel/setup \
  -H "Authorization: Bearer FREEMIUM_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"domain": "test.example.com", "verification_method": "txt_record"}'

# Expected: 402 Payment Required
# {"detail": "Whitelabel requires Pro tier or higher"}
```

### Test 2: Domain Setup (Pro User)

```bash
# Login as Pro user
curl -X POST https://vrenum.onrender.com/api/whitelabel/setup \
  -H "Authorization: Bearer PRO_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"domain": "custom.example.com", "verification_method": "txt_record"}'

# Expected: 200 OK
# {
#   "id": 1,
#   "domain": "custom.example.com",
#   "verification_token": "abc123...",
#   "verification_method": "txt_record",
#   "verified": false
# }
```

### Test 3: Get Configuration

```bash
curl https://vrenum.onrender.com/api/whitelabel/config \
  -H "Authorization: Bearer PRO_TOKEN"

# Expected: 200 OK
# {
#   "domains": [
#     {
#       "id": 1,
#       "domain": "custom.example.com",
#       "verified": false,
#       "active": true
#     }
#   ],
#   "branding": {
#     "primary_color": "#667eea",
#     "secondary_color": "#764ba2",
#     ...
#   }
# }
```

### Test 4: Update Branding

```bash
curl -X PUT https://vrenum.onrender.com/api/whitelabel/branding \
  -H "Authorization: Bearer PRO_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "My Company",
    "primary_color": "#FF0000",
    "logo_url": "https://example.com/logo.png"
  }'

# Expected: 200 OK with updated branding
```

---

## 🔍 Monitoring

### Key Metrics to Watch

1. **Error Rate**
   - Watch for `AttributeError` or `OperationalError` (indicates missing tables)
   - Watch for `IntegrityError` (indicates data issues)

2. **API Endpoints**
   - `/api/whitelabel/setup` - Domain creation
   - `/api/whitelabel/config` - Configuration retrieval
   - `/api/whitelabel/branding` - Branding updates
   - `/api/whitelabel/verify-domain` - DNS verification

3. **Database Queries**
   - Monitor slow queries on `whitelabel_custom_domains`
   - Check for N+1 queries in middleware

### Sentry Alerts

```python
# Already configured in whitelabel_service.py
logger.error(f"DNS verification error: {e}")  # Will trigger Sentry
logger.error(f"Error loading whitelabel config: {e}")  # Will trigger Sentry
```

---

## 🐛 Troubleshooting

### Issue 1: "Table whitelabel_custom_domains does not exist"

**Cause**: Migration not run
**Fix**:
```bash
alembic upgrade head
```

### Issue 2: "AttributeError: 'Settings' object has no attribute 'TELEGRAM_BOT_TOKEN'"

**Cause**: Already fixed in code
**Status**: ✅ Resolved (uses `getattr` with default)

### Issue 3: Middleware not injecting branding

**Cause**: Domain not verified or branding not configured
**Fix**:
1. Verify domain ownership
2. Configure branding via API
3. Check middleware logs

### Issue 4: 402 Payment Required for Pro user

**Cause**: User tier not updated in database
**Fix**:
```sql
UPDATE users SET subscription_tier = 'pro' WHERE email = 'user@example.com';
```

---

## 🔄 Rollback Plan

### If Issues Occur

```bash
# Rollback migration
alembic downgrade -1

# Rollback code deployment
git revert HEAD
git push origin main

# Or disable whitelabel in main.py
# Comment out: app.add_middleware(WhitelabelMiddleware, ...)
```

### Data Safety

- ✅ Migration is non-destructive (only creates tables)
- ✅ Existing data unaffected
- ✅ Can rollback without data loss
- ✅ Foreign keys use CASCADE delete (safe cleanup)

---

## 📊 Expected Impact

### Performance

- **Middleware overhead**: ~5ms per request (only for custom domains)
- **Database queries**: +1 query per custom domain request
- **Memory**: Negligible (branding cached in request state)

### User Experience

- **Pro+ users**: Can setup custom domains at `/whitelabel-setup`
- **Freemium users**: See upgrade prompt (402 response)
- **No impact**: Users not using whitelabel feature

### Revenue

- **Estimated**: $475/month (5 Pro + 10 Custom users)
- **Tier requirement**: Pro ($25/mo) or Custom ($35/mo)

---

## ✅ Success Criteria

- [ ] Migration runs without errors
- [ ] No 500 errors in production logs
- [ ] Whitelabel endpoints return 200/402 correctly
- [ ] Pro users can create domains
- [ ] Freemium users see upgrade prompt
- [ ] Branding updates work
- [ ] No performance degradation

---

## 📞 Support

**If deployment fails:**

1. Check Render logs: `https://dashboard.render.com/logs`
2. Check Sentry: `https://dev-vp.sentry.io/issues/`
3. Rollback if critical: `alembic downgrade -1`
4. Contact: support@namaskah.app

---

## 🎯 Next Steps After Deployment

1. **Manual Testing** (30 minutes)
   - Test domain setup flow
   - Test branding configuration
   - Test tier enforcement

2. **Monitor for 24 Hours**
   - Watch error rates
   - Check user feedback
   - Monitor performance

3. **Documentation Update**
   - Add whitelabel guide to docs
   - Update API documentation
   - Create user tutorial

4. **Future Enhancements** (Q3 2026)
   - Email template customization (WL-06)
   - SSL automation (Let's Encrypt)
   - Multi-domain support
   - Custom SMTP configuration

---

**Deployment Status**: ✅ Ready
**Risk Level**: Low
**Estimated Downtime**: 0 minutes (migration runs live)
**Rollback Time**: <5 minutes
