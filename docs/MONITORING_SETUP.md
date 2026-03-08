# Monitoring Setup Guide
**Lightweight Alternative to Datadog**

## Why Not Datadog?

- ❌ $15-30/month (overkill for current stage)
- ❌ Complex setup
- ❌ Designed for large teams
- ✅ Use Sentry + built-in tools instead

---

## Recommended Stack

### 1. Sentry (Error Tracking) - FREE
```bash
# Install
pip install sentry-sdk[fastapi]

# Sign up: https://sentry.io (FREE tier: 5K errors/month)
# Get your DSN

# Add to .env
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
```

**Integration:**
```python
# main.py
from app.core.monitoring import init_monitoring

init_monitoring(environment="production")
```

**Cost:** $0/month (FREE tier sufficient)

---

### 2. Render Logs (Built-in) - FREE
```bash
# View logs in Render Dashboard
# Or download via CLI
render logs --tail

# Set up log alerts (free)
# Dashboard → Service → Alerts
```

**Cost:** $0/month

---

### 3. Uptime Monitoring - FREE
```bash
# Option A: UptimeRobot (https://uptimerobot.com)
# - 50 monitors free
# - 5-minute checks
# - Email/SMS alerts

# Option B: Better Uptime (https://betteruptime.com)
# - 10 monitors free
# - Status page included
```

**Cost:** $0/month

---

### 4. Health Checks (Already Built-in)
```bash
# Your app already has:
GET /system/health
GET /system/metrics

# Monitor these endpoints with UptimeRobot
```

---

## Quick Setup (10 minutes)

### Step 1: Install Sentry
```bash
pip install -r requirements-monitoring.txt
```

### Step 2: Get Sentry DSN
1. Sign up at https://sentry.io
2. Create new project (Python/FastAPI)
3. Copy DSN

### Step 3: Add to Environment
```bash
# Render Dashboard → Environment
SENTRY_DSN=your-dsn-here
```

### Step 4: Deploy
```bash
git add .
git commit -m "Add Sentry monitoring"
git push
```

---

## What You Get

### Error Tracking
- ✅ Real-time error alerts
- ✅ Stack traces
- ✅ User context
- ✅ Performance monitoring
- ✅ Release tracking

### Logs
- ✅ Structured logging
- ✅ Search & filter
- ✅ Download for analysis

### Uptime
- ✅ 24/7 monitoring
- ✅ Instant alerts
- ✅ Status page

---

## Cost Comparison

| Solution | Monthly Cost | Features |
|----------|-------------|----------|
| **Datadog** | $15-30 | Everything (overkill) |
| **Sentry + Render** | $0 | Perfect for your stage |
| **Upgrade later** | $26 | When you have 1K+ users |

---

## When to Upgrade

**Stick with FREE tier until:**
- ✅ 1,000+ daily active users
- ✅ 10K+ requests/day
- ✅ Multiple services/microservices
- ✅ Team of 5+ engineers

**Then consider:**
- Sentry Pro ($26/mo)
- Grafana Cloud (still free)
- Or Datadog (if you really need it)

---

## Monitoring Checklist

- [ ] Install Sentry
- [ ] Add SENTRY_DSN to environment
- [ ] Set up UptimeRobot (3 monitors: web, API, health)
- [ ] Configure Render log alerts
- [ ] Test error tracking (trigger test error)
- [ ] Set up status page (Better Uptime)

---

## Next Steps

1. **Now:** Set up Sentry (10 min)
2. **Week 1:** Add UptimeRobot monitors
3. **Week 2:** Configure log alerts
4. **Month 1:** Review metrics, adjust as needed

**Total cost:** $0/month
**Total time:** 30 minutes

---

## Resources

- Sentry Docs: https://docs.sentry.io/platforms/python/guides/fastapi/
- UptimeRobot: https://uptimerobot.com
- Render Logs: https://render.com/docs/logs
- Better Uptime: https://betteruptime.com
