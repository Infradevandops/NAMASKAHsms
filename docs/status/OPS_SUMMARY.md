# Vrenum Ops & Platform Summary

> **Version** v4.8.2 · **Updated** June 2026
> Your single reference for what's running, what's broken, what's missing, and what to do next.

---

## Quick Health Check

Run this any time you want to know if everything is alive:

```bash
curl -s https://vrenum.app/api/monitoring/health/detailed | python3 -m json.tool
```

What you want to see:

```json
{
  "status": "healthy",
  "checks": {
    "database": { "status": "healthy" },
    "cache":    { "backend": "redis" },   ← must say redis, not memory
    "textverified": { "balance": 48.40 }  ← keep above $10
  }
}
```

---

## Live Dashboards

| Dashboard | Link | What to look for |
|-----------|------|-----------------|
| Uptime | [Better Stack](https://uptime.betterstack.com/team/t545038/monitors/4422808) | All green, 0 incidents |
| Errors | [Sentry](https://dev-vp.sentry.io/issues/) | Zero new issues after a deploy |
| Hosting | [Render](https://dashboard.render.com) | Last deploy succeeded |
| Analytics | [GA4](https://analytics.google.com) (G-M15PBV1P55) | Traffic trends |
| Page analytics | [Sabilytics](https://www.sabilytics.com) (ek3athooftac) | User flows |

---

## Section 1 — Infrastructure: When Things Break

### Database goes down

**What you'll see:** 500 errors everywhere. Sentry floods with `sqlalchemy.exc.OperationalError`.

**Most likely cause:** Neon free tier auto-pauses the DB after 5 minutes of idle.

**Fix:**
1. Open [Neon dashboard](https://console.neon.tech) → wake the DB manually
2. If it keeps happening → upgrade Neon to paid (disables auto-pause)
3. `pool_pre_ping=True` is already set in `database.py` so reconnects are automatic once the DB is awake

---

### Redis goes down

**What you'll see:** Health endpoint shows `"backend": "memory"`. Rate limiting resets on restart. Logged-out tokens aren't revoked.

**Fix:**
```bash
# 1. Confirm the URL is correct on the server
grep REDIS_URL ~/vrenum/.env.production
# Should show: profound-yak-85016.upstash.io

# 2. Force-recreate (plain restart does NOT re-read the env file)
docker compose up -d --force-recreate
```

**If you get NXDOMAIN:** The Upstash instance was deleted. Create a new one, paste the new `rediss://` URL into `.env.production`, then force-recreate.

---

### Traffic spike

**What you'll see:** p95 latency climbs above 1s. Render CPU >80%.

**Immediate fix:** Render dashboard → your service → Scale → bump to 2 workers (already set in `render.yaml`, just needs a redeploy).

**Find the slow endpoint:** Sentry → Performance tab → sort by p95 latency.

**Longer term:** Add Redis caching to the slow endpoint. Check for N+1 queries in the stack trace.

---

### TextVerified balance low

**What you'll see:** SMS verifications fail with "insufficient funds".

**Check:** `curl https://vrenum.app/api/monitoring/health/detailed` → look at `textverified.balance`.

**Rule:** Top up when balance drops below **$10**. Each SMS costs ~$2.63.

---

## Section 2 — Emails: What's Sending vs What's Not

### ✅ Sending right now

| Event | Email sent | Wired in |
|-------|-----------|----------|
| User registers | Welcome | `auth_routes.py` |
| Email needs verifying | Verification link | `auth_routes.py` |
| Password reset requested | Reset link | `user_settings.py` |
| SMS verification starts | Verification initiated | `purchase_endpoints.py` |
| SMS code received | Verification completed | `sms_polling_service.py` |
| Payment succeeds | Receipt | `payment_service.py` |
| Payment fails | Failure alert | `payment_service.py` |
| Auto-refund issued | Refund processed | `refund_service.py` |

---

### ⏳ Built but not wired yet

These templates exist in `email_service.py` and are ready to send — they just have no caller yet.

| Email | What triggers it | Where to add the call |
|-------|-----------------|----------------------|
| Low balance alert | After any wallet debit, if `credits < threshold` | `balance_service.py` — **admin accounts are excluded automatically** |
| Tier upgrade | After tier change confirmed | `app/api/billing/tiers.py` |
| Generic notification | When a notification is created | `notification_dispatcher.py` |
| Daily digest | Scheduled — 08:00 UTC daily | `lifespan.py` background tasks |
| Weekly digest | Scheduled — Monday 08:00 UTC | `lifespan.py` background tasks |

> For email provider setup, DNS records, and scaling plan — see [Email Setup Guide](../operations/EMAIL_SETUP.md).

---

### ⏳ Personalisation missing

These emails send fine but greet the user as "Hi there," instead of their name. The `_greeting()` helper already exists — callers just aren't passing `user_name` yet.

Affected: `send_verification_email`, `send_password_reset`, `send_payment_receipt`, `send_payment_failed_alert`, `send_refund_notification`

**Fix pattern** (same for all five):
```python
# In the caller — fetch the user first
user = await db.get(User, user_id)

# Then pass display_name into the call
await email_service.send_payment_receipt(
    user.email,
    {**payment_details, "user_name": user.display_name}
)

# In email_service._receipt_html() — add at the top of the body
greeting = self._greeting(d.get("user_name"))
```

---

### ⏳ Unsubscribe footer missing

Templates 1–5 (verification link, password reset, receipt, failed, refund) don't include the unsubscribe footer. The `_unsub_footer()` method exists — just needs to be called.

**Fix:** In each `_*_html()` method, add `{self._unsub_footer()}` before the closing `</td>` of the body section.

---

## Section 3 — Revenue: What's Tracked vs What's Missing

### ✅ Already tracked

- Every Paystack payment writes to `balance_transactions` + `revenue_recognition`
- Admin dashboard shows total revenue, DAU, monthly targets
- `financial_statements_service.py` handles P&L and revenue recognition
- Affiliate commissions tracked in the `commission` table

---

### ⚠️ Gaps

**No alert when daily revenue hits zero**
Silent payment processor outages can kill revenue for hours without anyone noticing.
Add to `alerting_service.py`: if `SUM(revenue today) == 0` by 18:00 UTC → Slack alert.

**No month-end target notification**
`monthly_target` model and `target_tracking_service.py` both exist. Missing: a scheduled check at month-end that emails the admin if the target was missed.

**No TextVerified cost reconciliation**
We charge users $2.63/SMS. TextVerified charges us ~$2.00–$2.40. The margin isn't being verified automatically.
`provider_settlement_service.py` exists but isn't scheduled. Add a weekly cron that compares `verifications.cost` totals against the TextVerified balance delta.

**Crypto payments not in revenue totals**
Crypto deposits go through admin approval at `/admin/settlements/approve`. That endpoint doesn't call `revenue_recognition_service.record_payment()`, so crypto revenue is invisible in the admin dashboard.

---

## Section 4 — SEO: What's Done vs What's Missing

### ✅ Done

- GA4 on every page
- Google Search Console connected, sitemap submitted (42 URLs)
- OG + Twitter Card tags on all pages
- Canonical tags on all pages
- JSON-LD structured data on service pages
- 5 blog pages, 20 service pages, 5 static SEO pages
- `robots.txt` pointing to vrenum.app

---

### ⚠️ Gaps

**Blog pages may be missing Sabilytics**
Check if `templates/blog/*.html` extend `base.html`. If they do, Sabilytics is already included. If they're standalone, add the script tag before `</head>`.

**Sitemap is static**
`static/sitemap.xml` is a hand-written file. New blog posts or service pages won't appear in it automatically. Add a `GET /sitemap.xml` FastAPI route that generates the XML dynamically, then resubmit to Google Search Console.

**Blog pages missing unique meta descriptions**
Each blog page should have its own `<meta name="description">` targeting the specific keyword. Without it, Google picks arbitrary text from the page.

**No Article structured data on blog pages**
Google can show rich results (date, author, headline) for articles with `Article` JSON-LD. Add it to each blog template with `headline`, `datePublished`, `author`, and `image` fields.

**Core Web Vitals not audited**
Run `tools/lighthouse_audit.js` against production. Targets: LCP < 2.5s, CLS < 0.1. The glassmorphism `backdrop-filter` CSS is a known CLS risk on mobile.

---

## Section 5 — Monitoring Dashboards

### What's actually running in production

| Tool | Monitors | Access |
|------|----------|--------|
| Better Stack | Uptime, response time | Link above |
| Sentry | Errors, performance, releases | Link above |
| Sabilytics | Page views, user flows | sabilytics.com |
| GA4 | Traffic, conversions | analytics.google.com |
| `/api/monitoring/health/detailed` | DB, Redis, TextVerified live status | vrenum.app |

---

### Prometheus + Grafana — local only, NOT in production

The `deploy/monitoring/` stack is configured but never deployed to the server. It's a local dev tool. Three options to get real dashboards:

**Option A — Render's built-in metrics** ← do this first, it's free and already there
Render dashboard → your service → Metrics tab. Shows CPU, memory, request count, response time. No setup needed.

**Option B — Grafana Cloud free tier** ← recommended if you want proper dashboards
Free tier: 10K metrics, 50GB logs, 14-day retention. Connect via the `/metrics` endpoint (Prometheus format already exposed by the app).

**Option C — Deploy monitoring stack to server** ← not recommended
Adds ~500MB RAM to a 2GB server. Only do this if you've upgraded the server.
```bash
# On server
cd ~/vrenum/deploy/monitoring && docker compose up -d
# SSH tunnel to view locally
ssh -L 3000:localhost:3000 root@169.255.57.146
# Open http://localhost:3000
```

---

## Section 6 — Sentry: How to Read It

### The three tabs you'll use

**Issues tab** — grouped errors, sorted by frequency. After every deploy, sort by "First Seen" to catch new regressions immediately.

**Performance tab** — p50/p95 latency per endpoint. Anything above 500ms is worth investigating.

**Releases tab** — error rate per deploy. A spike right after a deploy means that deploy caused it.

---

### Error types and what they mean

| Error in Sentry | What it means | What to do |
|----------------|--------------|------------|
| `sqlalchemy.exc.OperationalError` | DB dropped (Neon auto-pause or network blip) | Check Neon dashboard |
| `redis.exceptions.ConnectionError` | Upstash instance dead or wrong URL | Check `.env.production` REDIS_URL |
| `httpx.ConnectTimeout` | TextVerified API slow or down | Check TextVerified status page |
| `AttributeError: 'NoneType'` | Code expected a DB record that doesn't exist | Read the stack trace — missing null check |
| `jwt.exceptions.ExpiredSignatureError` | Token expired, user needs to re-login | Normal — only worry if rate > 5% of requests |
| `KeyError` in webhook handler | Paystack changed their payload format | Check Paystack changelog, fix `webhook_service.py` |
| `pydantic.ValidationError` | Frontend sending wrong field names or types | Compare endpoint schema vs what the frontend sends |

---

### Four alert rules to set up now

Go to **Sentry → Alerts → Create Alert Rule**:

1. Error spike — `event.count() > 10 in 5 minutes` → Slack #alerts
2. New issue type — any issue seen for the first time → Slack #alerts
3. Performance regression — p95 latency > 2s for 5 minutes → Slack #alerts
4. Payment errors — issues tagged `payment` → Slack #alerts + email immediately

---

### How to debug any Sentry issue (step by step)

1. Click the issue → read the full stack trace top to bottom
2. Open the **Breadcrumbs** tab — shows every DB query and HTTP call that happened before the crash
3. Open the **Tags** tab — `user_id`, `endpoint`, `tier` tell you exactly who hit it and where
4. Check **Similar Issues** — if 50 users hit the same thing, it's systemic, not a one-off
5. Reproduce it: copy the request from the **Request** tab and replay with `curl`

---

### What's already configured in Sentry

- User ID and email attached to every authenticated request (via `app/core/sentry.py`)
- Release tracking active — errors are tagged to the deploy that introduced them
- Performance sample rate: 10% (temporarily set to 100% when actively debugging a slow endpoint)

---

## Section 7 — Deploy Reference

```bash
# Full deploy from Mac (rsync + rebuild + health check)
bash scripts/deploy.sh

# Force restart — use this when you change .env.production
# plain "restart" does NOT re-read the env file
ssh root@169.255.57.146 "cd ~/vrenum && docker compose up -d --force-recreate"

# Check everything is healthy
curl -s https://vrenum.app/api/monitoring/health/detailed | python3 -m json.tool

# Watch live logs
ssh root@169.255.57.146 "cd ~/vrenum && docker compose logs -f app --tail=100"

# Confirm Redis is connected (not memory fallback)
curl -s https://vrenum.app/api/monitoring/health/detailed \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['checks']['cache']['backend'])"
```

---

## Section 8 — Open Tasks Summary

All 8 original TASKS.md items are complete. New tasks added (TASK-009 through TASK-018):

### 🟠 High — do these next

| # | Task | File |
|---|------|------|
| 009 | Wire low balance alert email after wallet debit | `balance_service.py` |
| 010 | Wire tier upgrade email to billing endpoint | `app/api/billing/tiers.py` |
| 011 | Pass `user_name` to payment/refund email callers | `payment_service.py`, `refund_service.py` |

### 🟡 Medium

| # | Task | File |
|---|------|------|
| 012 | Add `_unsub_footer()` to transactional templates 1–5 | `email_service.py` |
| 013 | Wire notification dispatcher to send emails | `notification_dispatcher.py` |
| 014 | Add Sabilytics to blog templates if standalone | `templates/blog/*.html` |
| 015 | Make sitemap.xml a dynamic FastAPI route | `app/api/main_routes.py` |

### 🟢 Low — when you have time

| # | Task | File |
|---|------|------|
| 016 | Add revenue-zero alert (daily check at 18:00 UTC) | `alerting_service.py` |
| 017 | Wire crypto approval to revenue recognition | admin settlements endpoint |
| 018 | Schedule daily + weekly digest emails | `lifespan.py` |

---

> **Next review:** After first 100 users or 30 days post-launch, whichever comes first.
