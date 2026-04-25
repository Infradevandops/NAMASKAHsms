# Sentry Deployment Checklist

## ✅ Completed

- [x] Sentry SDK installed (`sentry-sdk[fastapi]==2.20.0`)
- [x] Config fields added to `app/core/config.py`
- [x] Sentry initialization in `app/core/lifespan.py`
- [x] DSN added to `.env.example`
- [x] Integration modules configured (FastAPI, SQLAlchemy, Redis)
- [x] Error filtering implemented
- [x] User context helpers created
- [x] Documentation created

## 🚀 Deployment Steps

### 1. Local Testing (5 minutes)

```bash
# 1. Ensure .env has Sentry DSN
echo "SENTRY_DSN=https://faa408669682f1f0ab6c7a59e8237ab8@o4508547757179968.ingest.us.sentry.io/4510054775717968" >> .env

# 2. Start the app
./start.sh

# 3. Check logs for "Sentry initialized"
# Should see: "Sentry initialized: development v4.4.1"

# 4. Test error capture
curl http://localhost:8000/api/test-sentry  # (create this endpoint or trigger an error)

# 5. Check Sentry dashboard
# Go to: https://dev-vp.sentry.io/issues/
```

### 2. Production Deployment (10 minutes)

#### Render.com

1. **Add Environment Variable**
   - Go to: Render Dashboard → Your Service → Environment
   - Add: `SENTRY_DSN` = `https://faa408669682f1f0ab6c7a59e8237ab8@o4508547757179968.ingest.us.sentry.io/4510054775717968`
   - Save changes

2. **Deploy**
   ```bash
   git add .
   git commit -m "feat: integrate Sentry error tracking"
   git push origin main
   ```

3. **Verify Deployment**
   - Check Render logs for "Sentry initialized: production"
   - Visit your app to generate traffic
   - Check Sentry dashboard for events

4. **Test Error Tracking**
   - Trigger a known error (e.g., invalid API call)
   - Check Sentry dashboard within 30 seconds
   - Verify error appears with full context

### 3. Configure Alerts (5 minutes)

1. **Slack Integration** (Recommended)
   - Sentry → Settings → Integrations → Slack
   - Connect workspace
   - Choose channel (e.g., #alerts)
   - Set alert rules:
     - New issue: Immediate
     - Issue frequency: > 10 events/hour
     - Issue regression: Immediate

2. **Email Alerts**
   - Sentry → Settings → Alerts
   - Create alert rule:
     - Name: "Critical Errors"
     - Conditions: Error level = error or fatal
     - Actions: Send email to team

3. **Issue Assignment**
   - Sentry → Settings → Issue Owners
   - Auto-assign based on file path:
     ```
     path:app/services/payment_service.py team@namaskah.app
     path:app/services/sms_service.py team@namaskah.app
     ```

### 4. Dashboard Setup (5 minutes)

1. **Create Custom Dashboard**
   - Sentry → Dashboards → Create Dashboard
   - Add widgets:
     - Error rate (last 24h)
     - Most common errors
     - Errors by endpoint
     - Errors by user tier
     - Response time p95

2. **Set as Default**
   - Pin dashboard for quick access

### 5. Team Onboarding (5 minutes)

1. **Invite Team Members**
   - Sentry → Settings → Members
   - Invite with appropriate roles:
     - Admin: Full access
     - Member: View and comment
     - Billing: Billing only

2. **Share Documentation**
   - Send `docs/SENTRY_SETUP.md` to team
   - Schedule 15-min walkthrough

## 📊 Success Metrics

After 24 hours, verify:

- [ ] At least 1 event captured (even if just info)
- [ ] No "Sentry initialization failed" errors in logs
- [ ] Alerts configured and tested
- [ ] Team has access to dashboard
- [ ] Error context includes user info

## 🔍 Monitoring

### Daily
- Check Sentry dashboard for new issues
- Review critical errors

### Weekly
- Review error trends
- Identify patterns
- Update filters if needed

### Monthly
- Review usage vs. quota
- Optimize sample rates if needed
- Update alert rules based on patterns

## 🐛 Known Issues

### Redis CancelledError (Current)
**Status**: Now tracked in Sentry  
**Location**: `app/core/unified_cache.py`  
**Impact**: Low (graceful degradation)  
**Action**: Monitor frequency in Sentry

### Expected Errors (Filtered)
- 404 Not Found
- Invalid credentials (auth failures)
- Health check timeouts

## 📈 Next Steps

1. **Week 1**: Monitor and tune filters
2. **Week 2**: Set up performance monitoring
3. **Week 3**: Create custom error grouping rules
4. **Week 4**: Implement error budgets

## 🆘 Rollback Plan

If Sentry causes issues:

```bash
# 1. Remove from environment
unset SENTRY_DSN

# 2. Restart app
# Sentry will log warning but app continues normally

# 3. Fix issue and redeploy
```

## 📞 Support

- **Sentry Issues**: https://sentry.io/support/
- **Integration Help**: See `docs/SENTRY_SETUP.md`
- **Team Lead**: Check Render logs first

---

**Deployment Date**: _____________  
**Deployed By**: _____________  
**Verified By**: _____________  
**Status**: ⏳ Pending → ✅ Complete
