# Sentry Integration Guide

## Overview

Sentry is now integrated into Namaskah for production error tracking and monitoring.

## What's Monitored

✅ **Error Tracking**
- Unhandled exceptions
- API errors
- Database errors
- Redis connection issues
- External API failures (TextVerified, Paystack)

✅ **Performance Monitoring**
- API endpoint response times
- Database query performance
- Redis cache performance
- Background task execution

✅ **User Context**
- User ID and email
- Subscription tier
- Request details
- Breadcrumbs (actions leading to error)

## Configuration

### 1. Local Development

Add to your `.env` file:

```bash
SENTRY_DSN=https://faa408669682f1f0ab6c7a59e8237ab8@o4508547757179968.ingest.us.sentry.io/4510054775717968
ENVIRONMENT=development
```

### 2. Production (Render.com)

Add environment variable in Render dashboard:

```
SENTRY_DSN = https://faa408669682f1f0ab6c7a59e8237ab8@o4508547757179968.ingest.us.sentry.io/4510054775717968
ENVIRONMENT = production
```

### 3. Optional Settings

```bash
# Adjust sampling rates (default: 0.1 = 10%)
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1
```

## Features

### Automatic Error Capture

All unhandled exceptions are automatically sent to Sentry:

```python
# No code changes needed - automatic!
raise ValueError("Something went wrong")
```

### Manual Error Capture

For specific error tracking:

```python
from app.core.sentry import capture_tier_error, set_user_context

# Track tier-related errors
capture_tier_error(
    user_id="123",
    tier="pro",
    error=exception,
    context={"action": "upgrade"}
)

# Set user context for all subsequent errors
set_user_context(
    user_id="123",
    tier="pro",
    email="user@example.com"
)
```

### Performance Tracking

```python
from app.core.sentry import capture_performance_metric

capture_performance_metric(
    metric_name="sms_verification_time",
    value=2.5,  # seconds
    tags={"country": "US", "service": "google"}
)
```

## What Gets Filtered

Sentry automatically filters out:
- ❌ 404 errors (not found)
- ❌ Health check errors
- ❌ Invalid credential errors (expected auth failures)
- ❌ Sensitive headers (Authorization, Cookie)

## Integrations Enabled

1. **FastAPI** - Automatic request/response tracking
2. **SQLAlchemy** - Database query monitoring
3. **Redis** - Cache operation tracking
4. **Logging** - Structured log integration
5. **Threading** - Background task monitoring

## Viewing Errors

1. Go to: https://dev-vp.sentry.io/settings/projects/python-fastapi/
2. Navigate to "Issues" to see errors
3. Click any issue for:
   - Full stack trace
   - User context
   - Breadcrumbs (what led to error)
   - Environment details
   - Release version

## Alerts

Configure alerts in Sentry dashboard:
- Email notifications
- Slack integration
- PagerDuty integration
- Custom webhooks

## Release Tracking

Sentry automatically tracks releases using your app version:

```python
# app/core/config.py
version: str = "4.4.2"  # Automatically sent to Sentry
```

View errors by release to identify which deployment caused issues.

## Best Practices

### DO ✅
- Keep SENTRY_DSN in environment variables (never commit)
- Use user context for better debugging
- Review Sentry dashboard weekly
- Set up Slack alerts for critical errors
- Use release tracking to identify bad deploys

### DON'T ❌
- Don't send sensitive data (passwords, tokens)
- Don't ignore Sentry alerts
- Don't set sample rate to 1.0 in production (expensive)
- Don't commit DSN to git

## Testing Sentry

Test that Sentry is working:

```python
# Add to any endpoint temporarily
from app.core.sentry import set_user_context
import sentry_sdk

set_user_context(user_id="test", tier="freemium", email="test@example.com")
sentry_sdk.capture_message("Sentry test from Namaskah", level="info")
```

Check Sentry dashboard - you should see the message within seconds.

## Troubleshooting

### Sentry not capturing errors?

1. Check DSN is set: `echo $SENTRY_DSN`
2. Check logs for "Sentry initialized" message
3. Verify environment is not "testing"
4. Test with manual capture: `sentry_sdk.capture_message("test")`

### Too many errors?

1. Adjust sample rates in config
2. Add more filters in `before_send_sentry()`
3. Use Sentry's "Ignore" feature for known issues

### Missing context?

Make sure to call `set_user_context()` after authentication:

```python
# In auth middleware
from app.core.sentry import set_user_context

set_user_context(
    user_id=current_user.id,
    tier=current_user.tier,
    email=current_user.email
)
```

## Cost

- **Free tier**: 5,000 errors/month
- **Team tier**: $26/month for 50,000 errors
- **Business tier**: $80/month for 500,000 errors

Current usage: Monitor in Sentry dashboard → Settings → Usage & Billing

## Support

- Sentry Docs: https://docs.sentry.io/platforms/python/guides/fastapi/
- Namaskah Team: support@namaskah.app
- Sentry Support: https://sentry.io/support/

---

**Status**: ✅ Integrated and Ready  
**Last Updated**: April 25, 2026  
**Version**: 4.4.2
