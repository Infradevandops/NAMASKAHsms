# Sentry Quick Reference

## 🚨 Common Operations

### Check if Sentry is Active

```bash
# Check environment variable
echo $SENTRY_DSN

# Check logs
grep "Sentry initialized" logs/app.log
```

### Manually Capture Error

```python
import sentry_sdk

# Simple message
sentry_sdk.capture_message("Something happened", level="info")

# Exception
try:
    risky_operation()
except Exception as e:
    sentry_sdk.capture_exception(e)
```

### Add User Context

```python
from app.core.sentry import set_user_context

set_user_context(
    user_id="123",
    tier="pro",
    email="user@example.com"
)
```

### Add Custom Context

```python
import sentry_sdk

sentry_sdk.set_context("payment", {
    "amount": 100.00,
    "currency": "NGN",
    "provider": "paystack"
})

sentry_sdk.set_tag("feature", "sms_verification")
```

### Track Performance

```python
import sentry_sdk

# Transaction
with sentry_sdk.start_transaction(op="sms", name="verify_number"):
    # Your code here
    result = verify_phone_number()
```

## 🔗 Quick Links

- **Dashboard**: https://dev-vp.sentry.io/issues/
- **Project Settings**: https://dev-vp.sentry.io/settings/projects/python-fastapi/
- **Alerts**: https://dev-vp.sentry.io/alerts/
- **Performance**: https://dev-vp.sentry.io/performance/

## 📊 Key Metrics to Watch

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Error Rate | < 0.1% | 0.1-1% | > 1% |
| Response Time (p95) | < 500ms | 500-1000ms | > 1000ms |
| Redis Errors | 0 | 1-5/hour | > 5/hour |
| Payment Errors | 0 | 1-2/day | > 2/day |

## 🎯 Error Priority

### P0 - Critical (Fix immediately)
- Payment processing failures
- Database connection lost
- Authentication system down

### P1 - High (Fix within 24h)
- SMS verification failures
- API rate limiting issues
- Cache connection errors

### P2 - Medium (Fix within week)
- UI rendering issues
- Non-critical API errors
- Performance degradation

### P3 - Low (Fix when convenient)
- Cosmetic issues
- Rare edge cases
- Optimization opportunities

## 🔧 Troubleshooting

### Error: "Sentry DSN not configured"
```bash
# Add to .env
echo "SENTRY_DSN=https://..." >> .env
```

### Error: "Too many events"
```python
# Reduce sample rate in config.py
sentry_traces_sample_rate: float = 0.05  # 5% instead of 10%
```

### Error: "Missing user context"
```python
# Add after authentication
from app.core.sentry import set_user_context
set_user_context(user_id=user.id, tier=user.tier, email=user.email)
```

## 📱 Mobile Alerts

Set up Sentry mobile app for on-the-go monitoring:
1. Download Sentry app (iOS/Android)
2. Login with your account
3. Enable push notifications
4. Get alerted immediately for critical errors

## 🎓 Learning Resources

- **Sentry Docs**: https://docs.sentry.io/
- **FastAPI Integration**: https://docs.sentry.io/platforms/python/guides/fastapi/
- **Best Practices**: https://docs.sentry.io/product/best-practices/

---

**Keep this handy for quick reference!**
