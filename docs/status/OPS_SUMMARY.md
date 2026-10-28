# Vrenum Ops & Platform Summary

> **Version** v4.9.1 · **Updated** October 26, 2026
> Your single reference for what's running, what's broken, what's missing, and what to do next.

---

## Quick Health Check

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
| Analytics | [GA4](https://analytics.google.com) (G-M15PBV1P55) | Traffic trends |
| Page analytics | [Sabilytics](https://www.sabilytics.com) (ek3athooftac) | User flows |

---

## Section 1 — Infrastructure: When Things Break

### Deployment setup (actual)

- **Code lives on:** Mac → GitHub repo
- **Deploy method:** GitHub Actions CI/CD — push to `main` → SSH deploy via `appleboy/ssh-action` (~3 min)
- **Server:** `root@169.255.57.146` (Ubuntu 24.04, Docker Compose)
- **Repo path on server:** `~/vrenum/Vrenum/` (git repo nested inside `~/vrenum/`)
- **Containers:** `vrenum-app` (port 8000), `vrenum-nginx` (80/443), `vrenum-certbot`
- **Env file:** `~/vrenum/Vrenum/.env.production` — never in the repo
- **`docker-compose.yml`:** in git root, uses `env_file: .env.production`

```bash
# Deploy: push to main — GitHub Actions handles the rest
git push origin main

# Manual deploy / force restart after .env.production change
ssh root@169.255.57.146 "cd ~/vrenum/Vrenum && git pull && docker compose up -d --build --force-recreate"

# Watch live logs
ssh root@169.255.57.146 "cd ~/vrenum/Vrenum && docker compose logs -f app --tail=100"

# Health check
curl -s https://vrenum.app/api/monitoring/health/detailed | python3 -m json.tool

# Verify an env var loaded into the container
ssh root@169.255.57.146 "cd ~/vrenum/Vrenum && docker compose exec app printenv ADMIN_NOTIFY_EMAIL"

# Edit env vars on server
ssh root@169.255.57.146 "nano ~/vrenum/Vrenum/.env.production"
# Then force-recreate to reload
```

> ⚠️ `git clean -fd` is destructive — deletes untracked files. `docker-compose.yml` is now in git so it's safe, but never run `git clean` on the server without checking first.

---

### Database goes down

**What you'll see:** 500 errors everywhere. Sentry floods with `sqlalchemy.exc.OperationalError`.

**Most likely cause:** Neon free tier auto-pauses the DB after 5 minutes of idle.

**Fix:**
1. Open [Neon dashboard](https://console.neon.tech) → wake the DB manually
2. If it keeps happening → upgrade Neon to paid (disables auto-pause)
3. `pool_pre_ping=True` is already set in `database.py` so reconnects are automatic once the DB is awake

---

### Redis goes down

**What you'll see:** Health endpoint shows `"backend": "memory"`. Rate limiting resets on restart. Logged-out tokens aren't revoked. Stock availability dots disappear from the verification page.

**Fix:**
```bash
# 1. Confirm the URL is correct on the server
ssh root@169.255.57.146 "grep REDIS_URL ~/vrenum/Vrenum/.env.production"
# Should show: profound-yak-85016.upstash.io

# 2. Force-recreate (plain restart does NOT re-read the env file)
ssh root@169.255.57.146 "cd ~/vrenum/Vrenum && docker compose up -d --force-recreate"
```

**If you get NXDOMAIN:** The Upstash instance was deleted. Create a new one, paste the new `rediss://` URL into `.env.production`, then force-recreate.

---

### Traffic spike

**What you'll see:** p95 latency climbs above 1s. Server CPU >80%.

**Immediate fix:** Edit `~/vrenum/Vrenum/.env.production` on the VPS → bump `WORKERS=4` → force-recreate.

**Find the slow endpoint:** Sentry → Performance tab → sort by p95 latency.

---

### TextVerified balance low

**What you'll see:** SMS verifications fail with "insufficient funds".

**Check:** `curl https://vrenum.app/api/monitoring/health/detailed` → look at `textverified.balance`.

**Rule:** Top up when balance drops below **$10**. Each SMS costs ~$2.63.

---

## Section 2 — Emails: What's Sending

### ✅ All emails wired and sending (v4.9.1)

| Event | Email sent | Wired in |
|-------|-----------|----------|
| User registers | Welcome | `auth_routes.py` |
| Email needs verifying | Verification link + unsub footer | `auth_routes.py` |
| Password reset requested | Reset link + unsub footer | `user_settings.py` |
| SMS verification starts | Verification initiated | `purchase_endpoints.py` |
| SMS code received | Verification completed | `sms_polling_service.py` |
| Payment succeeds | Receipt + user_name | `payment_service.py` |
| Payment fails | Failure alert | `payment_service.py` |
| Auto-refund issued | Refund processed + user_name | `refund_service.py` |
| Balance low | Low balance alert | `balance_service.py` |
| Tier upgrade | Upgrade confirmation + features | `tier_manager.py` |
| Notification created | Generic notification email | `notification_dispatcher.py` |
| Daily (08:00 UTC) | Daily digest of unread notifications | `lifespan.py` scheduler |
| Weekly (Mon 08:00 UTC) | Weekly digest + stats | `lifespan.py` scheduler |
| Revenue = $0 at 18:00 UTC | Critical alert → `vrenum.proton.me` | `lifespan.py` + `alerting_service.py` |

> All 5 transactional templates include unsubscribe footer (CAN-SPAM compliant).
> For email provider setup — see [Email Setup Guide](../operations/EMAIL_SETUP.md).

---

## Section 3 — Revenue: What's Tracked

### ✅ All revenue tracked (v4.9.1)

- Every Paystack payment writes to `balance_transactions` + `revenue_recognition`
- Crypto deposits: admin approval at `/admin/settlements/approve/{ref}` calls `revenue_recognition_service.recognize_revenue()`
- Admin dashboard shows total revenue, DAU, monthly targets
- `financial_statements_service.py` handles P&L
- Affiliate commissions tracked in `commission` table
- Revenue-zero alert fires at 18:00 UTC → `vrenum.proton.me`

### ⚠️ Still missing

**No TextVerified cost reconciliation** — we charge $2.63/SMS, TV charges ~$2.00–$2.40. `provider_settlement_service.py` exists but isn't scheduled. Add a weekly cron comparing `verifications.cost` totals against TV balance delta.

**No month-end target notification** — `monthly_target` model and `target_tracking_service.py` exist. Missing: scheduled check at month-end that emails admin if target was missed.

---

## Section 4 — SEO: What's Done vs What's Missing

### ✅ Done

- GA4 on every page
- Google Search Console connected, sitemap submitted
- OG + Twitter Card tags on all pages
- Canonical tags on all pages
- JSON-LD structured data on service pages
- 5 blog pages, 20 service pages, 5 static SEO pages
- `robots.txt` pointing to vrenum.app
- Dynamic `/sitemap.xml` FastAPI route (returns proper `application/xml`)
- Sabilytics on all pages via `base.html` → `cookie_consent.html`

### ⚠️ Still missing

- Blog pages missing unique meta descriptions
- No `Article` JSON-LD structured data on blog pages
- Core Web Vitals not audited — run `tools/lighthouse_audit.js` against production

---

## Section 5 — Monitoring

| Tool | Monitors | Access |
|------|----------|--------|
| Better Stack | Uptime, response time | Link above |
| Sentry | Errors, performance, releases | Link above |
| Sabilytics | Page views, user flows | sabilytics.com |
| GA4 | Traffic, conversions | analytics.google.com |
| `/api/monitoring/health/detailed` | DB, Redis, TextVerified live | vrenum.app |
| Revenue-zero alert | Email at 18:00 UTC if $0 revenue | → vrenum.proton.me |

### Prometheus + Grafana — local only, NOT in production

The `deploy/monitoring/` stack is configured but not deployed. Options:

**Option A — Grafana Cloud free tier** ← recommended
Free tier: 10K metrics, 50GB logs, 14-day retention. Connect via `/metrics` endpoint.

**Option B — Deploy to server** ← not recommended
Adds ~500MB RAM. SSH tunnel to view: `ssh -L 3000:localhost:3000 root@169.255.57.146`

---

## Section 6 — Sentry: How to Read It

### The three tabs you'll use

**Issues tab** — grouped errors, sorted by frequency. After every deploy, sort by "First Seen" to catch new regressions immediately.

**Performance tab** — p50/p95 latency per endpoint. Anything above 500ms is worth investigating.

**Releases tab** — error rate per deploy. A spike right after a deploy means that deploy caused it.

### Error types and what they mean

| Error in Sentry | What it means | What to do |
|----------------|--------------|------------|
| `sqlalchemy.exc.OperationalError` | DB dropped (Neon auto-pause or network blip) | Check Neon dashboard |
| `redis.exceptions.ConnectionError` | Upstash instance dead or wrong URL | Check `~/vrenum/Vrenum/.env.production` REDIS_URL |
| `httpx.ConnectTimeout` | TextVerified API slow or down | Check TextVerified status page |
| `AttributeError: 'NoneType'` | Code expected a DB record that doesn't exist | Read the stack trace — missing null check |
| `jwt.exceptions.ExpiredSignatureError` | Token expired, user needs to re-login | Normal — only worry if rate > 5% of requests |
| `KeyError` in webhook handler | Paystack changed their payload format | Check Paystack changelog, fix `webhook_service.py` |
| `pydantic.ValidationError` | Frontend sending wrong field names or types | Compare endpoint schema vs what the frontend sends |

---

## Section 7 — Deploy Reference

```bash
# Standard deploy — push to main, CI/CD does the rest
git push origin main

# Manual / force restart after .env.production change
ssh root@169.255.57.146 "cd ~/vrenum/Vrenum && git pull && docker compose up -d --build --force-recreate"

# Verify an env var loaded into the container
ssh root@169.255.57.146 "cd ~/vrenum/Vrenum && docker compose exec app printenv ADMIN_NOTIFY_EMAIL"

# Health check
curl -s https://vrenum.app/api/monitoring/health/detailed | python3 -m json.tool

# Watch live logs
ssh root@169.255.57.146 "cd ~/vrenum/Vrenum && docker compose logs -f app --tail=100"

# Confirm Redis is connected (not memory fallback)
curl -s https://vrenum.app/api/monitoring/health/detailed \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['checks']['cache']['backend'])"

# Edit env vars on server
ssh root@169.255.57.146 "nano ~/vrenum/Vrenum/.env.production"
# Then force-recreate to reload
```

---

## Section 8 — Open Tasks Summary

All 18 tasks complete as of v4.9.1. One pending verification item:
- ⏳ Telegram E2E flow — bot created, webhook registered, Redis token linking done. Needs live test with real Telegram account.

### ✅ Completed (Tasks 009–018)

| # | Task | File | Version |
|---|------|------|---------|
| 009 | Wire low balance alert email | `balance_service.py` | 4.9.0 |
| 010 | Wire tier upgrade email | `tier_manager.py` | 4.9.0 |
| 011 | Pass `user_name` to payment/refund emails | `payment_service.py`, `refund_service.py` | 4.9.0 |
| 012 | `_unsub_footer()` on all 5 transactional templates | `email_service.py` | 4.9.1 |
| 013 | Notification dispatcher email wired correctly | `notification_dispatcher.py` | 4.9.1 |
| 014 | Blog Sabilytics | already in `base.html` | 4.9.1 |
| 015 | Dynamic sitemap XML | `app/api/main_routes.py` | 4.9.1 |
| 016 | Revenue-zero alert at 18:00 UTC | `alerting_service.py`, `lifespan.py` | 4.9.1 |
| 017 | Crypto approval → revenue recognition | `app/api/admin/actions.py` | 4.9.1 |
| 018 | Daily + weekly digest scheduler | `lifespan.py` | 4.9.1 |

### ⚠️ Env var confirmed live on VPS
```
ADMIN_NOTIFY_EMAIL=vrenum.proton.me  ✅ confirmed Oct 26 2026
```

---

> **Next review:** After Telegram E2E verification + first 100 users.
