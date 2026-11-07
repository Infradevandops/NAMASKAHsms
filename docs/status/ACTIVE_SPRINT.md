# ACTIVE SPRINT

**Updated**: November 7, 2026
**Server**: https://vrenum.app — ✅ Healthy
**Deployed**: `e06e91ce` (origin/main)

---

## Live Server State (verified via HTTP)

```
GET /health                         → degraded (tv_configured:false) ← fix deployed, awaiting redeploy
GET /api/monitoring/health/detailed → healthy | TV $42.15 | DB 165ms | Redis 118ms
GET /api/services/stock             → 416/2353 available, quantity:null on all
Uptime: 3d 16h+  |  Memory: 51.7%  |  Disk: 80% (61/76GB)  |  CPU: 9.5%
```

**`GET /health` still shows degraded** — the fix (`e06e91ce`) is pushed to origin/main
but the deploy workflow was itself broken by the same bug (health gate returning 503).
The fix needs a manual deploy trigger or the deploy workflow needs to be run once
with the health gate temporarily bypassed. See P0 below.

**TV is fully operational** — $42.15 balance, 416 services available, purchases working.

---

## What Happened — Full Sprint History

This sprint covers ~25 commits from `f1975971` to `e06e91ce` across two sessions.

### Session 1: Purchase Flow Overhaul (Nov 2–3, 2026)

The app was hitting TV 429 rate limits because startup was firing 2351 concurrent
pricing calls. This cascaded into broken stock, broken pricing preview, and 500 errors
on purchase.

| Commit | Fix |
|--------|-----|
| `fa4ec0d8` | Purchase 500 errors — Decimal/float mismatch + NOT NULL on purchase_outcomes |
| `887854f3` | Pricing screen shows real tier-adjusted cost (was showing $2.63, charging $0.90) |
| `fb9d35d6` | Real stock availability — quantity from cache before TV charges |
| `332d766d` | **Root cause fix**: remove bulk pricing fetch from startup (was causing 429) |
| `b30f579b` | Stock map price-based availability + cancel flow + polling guard |
| `6d082955` | build_stock_map skips outcome check for null-price services (2351→58 Redis calls) |
| `37c5c49e` | Prioritize popular services in pricing fetch, semaphore 10→3 |
| `fe4b5cf4` | Inline pricing timeout 12s→30s, prewarm 20s→60s |
| `950ce684` | Non-blocking service list — return names immediately, price in background |
| `4302e789` | `TEXTVERIFIED_PROXY_URL` support — route TV calls through proxy when IP blocked |

### Session 2: Webhook + Pricing URL + Balance (Nov 2, 2026)

| Commit | Fix |
|--------|-----|
| `3ea44750` | TV webhook handles `v2.sms.received` + **pricing URL confirmed**: `/api/pub/v2/pricing/verifications` |
| `dc9be6ca` | Balance display consistency — admin sees platform credits, TV balance as provider_balance |
| `6baaafb2` | Fix detached SQLAlchemy instance in notification email dispatch |
| `d4366646` | Add purchasability probe script |

### Session 3: CI + Security (Nov 2, 2026)

| Commit | Fix |
|--------|-----|
| `5c55c71a` | Add CodeQL workflow |
| `0c2bea62` | Streamline CI ruleset for solo/small team |
| `8a27be01` | Verify clean pipeline after ruleset changes |
| `5b0c1608` | CI green — isort formatting + gitleaks allowlist for template files |

### Session 4: This session (Nov 7, 2026)

| Commit | Fix |
|--------|-----|
| `23560e8c` | v4.9.9 changelog + fix duplicate version numbers |
| `e06e91ce` | **Health check fix**: accept `TEXTVERIFIED_EMAIL` not just `TEXTVERIFIED_USERNAME` |

---

## Credential Rotation Status

All credentials rotated ✅. One remaining action:

| Item | Status |
|------|--------|
| TEXTVERIFIED_API_KEY | ✅ Rotated |
| JWT_SECRET_KEY | ✅ Rotated |
| ADMIN_PASSWORD | ✅ Rotated |
| PostgreSQL password | ✅ Rotated |
| Redis token | ✅ Rotated |
| Paystack keys | ✅ Rotated |
| Google OAuth | ✅ Rotated |
| Telegram bot token | ✅ Rotated |
| **Server IP whitelisted with TV** | ⚠️ Pending — secondary IP not yet registered |

---

## Open Tasks — Priority Order

### P0 — Trigger deploy manually (health fix is stuck)
The `e06e91ce` health check fix is on origin/main but the deploy workflow won't
auto-fire because the previous deploy's health gate returned 503 (the bug we just fixed).
Need to trigger deploy manually from GitHub Actions → Deploy to Production → Run workflow.

After deploy, verify:
```
curl -s https://vrenum.app/health
# Expected: {"status":"healthy","service":"vrenum-sms","checks":{"db":"ok","redis":"ok","tv_configured":true}}
```

### P1 — Register server IP with TextVerified
The app moved to a secondary IP. TV is rate-limiting/blocking the raw services
quantity endpoint from that IP (`fetch_raw_services_with_quantity` returns empty,
all `quantity: null`). `TEXTVERIFIED_PROXY_URL` support was added (`4302e789`) as
a workaround but the real fix is whitelisting the new server IP with TV support.

Until resolved: stock shows 416 available (price-based, correct) but no quantity counts.
Purchases work fine — TV's `verifications.create()` handles out-of-stock at purchase time.

**Action**: Contact TV support with new server IP to whitelist it.

### P2 — Disk at 80% (61/76GB)
Run on server: `docker system prune -f` to reclaim old image layers.
Monitor — alert threshold is 90%.

### P3 — Telegram E2E live test
Code complete since v4.9.0. Pending manual test with real Telegram account.
Steps in `docs/features/TELEGRAM_ACCEPTANCE_CRITERIA.md`.

### P4 — Version string stale
`/api/monitoring/health/detailed` reports `version: 4.9.1`.
Update `settings.version` in `app/core/config.py` to `4.9.9`.

---

## Confirmed Facts (from code + live checks)

- **Pricing URL**: `/api/pub/v2/pricing/verifications` ✅ confirmed in `3ea44750`
  (was `/api/pub/v2/verifications/pricing` — now fixed)
- **TV balance**: $42.15 — healthy, well above $5 alert threshold
- **Stock**: 416/2353 available — price-based (quantity null due to IP rate limit)
- **Purchases**: Working — `verifications.create()` handles out-of-stock natively
- **Webhook**: Handles both `sms.received` and `v2.sms.received` event types
- **Rate limit root cause**: Startup was firing 2351 concurrent pricing calls → 429.
  Fixed in `332d766d` — startup no longer bulk-fetches pricing.
- **`TEXTVERIFIED_PROXY_URL`**: Env var supported. Set in `.env.production` to route
  TV calls through a proxy if IP blocking persists after whitelisting.
