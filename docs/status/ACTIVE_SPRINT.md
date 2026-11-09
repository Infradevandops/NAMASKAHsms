# ACTIVE SPRINT

**Updated**: November 2026 (post email hardening)
**Server**: https://vrenum.app — ✅ Healthy
**Deployed**: `e06e91ce` (origin/main) — manual deploy trigger needed

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
Needs a manual deploy trigger from GitHub Actions → Deploy to Production → Run workflow.

**TV is fully operational** — $42.15 balance, 416 services available, purchases working.

---

## What Happened — Sprint History

### Session 1–3: Purchase Flow Overhaul + CI + Security (Nov 2–3, 2026)

See `docs/status/OPS_SUMMARY.md` for full commit table. Root cause: startup fired 2351
concurrent pricing calls → TV 429 → broken stock, broken pricing preview, 500 errors.

### Session 4: Health Check Fix (Nov 7, 2026)

| Commit | Fix |
|--------|-----|
| `23560e8c` | v4.9.9 changelog + fix duplicate version numbers |
| `e06e91ce` | **Health check fix**: accept `TEXTVERIFIED_EMAIL` not just `TEXTVERIFIED_USERNAME` |

### Session 5: Email System Hardening (Nov 2026)

| Commit | Fix |
|--------|-----|
| `978b6b87` | EMAIL-001–043: email classes, preference policy, outbox worker, contact durability, template autoescape, 30 tests |
| `1bc1e955` | Formatting fixes (black/isort) |
| `1042b600` | gitleaks allowlist for `.env.development` dev placeholders |
| `d8239024` | TASKS.md all checkboxes ticked with commit evidence |

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

### P0 — Trigger deploy manually + run migration
1. GitHub Actions → Deploy to Production → Run workflow.
2. After deploy: `alembic upgrade head` on server (adds `email_outbox` + `contact_submissions` tables).

Verify after deploy:
```
curl -s https://vrenum.app/health
# Expected: {"status":"healthy","service":"vrenum-sms","checks":{"db":"ok","redis":"ok","tv_configured":true}}
```

### P1 — Register server IP with TextVerified
All `quantity: null` on services — secondary IP not whitelisted. Purchases work fine.
`TEXTVERIFIED_PROXY_URL` env var available as workaround.

### P2 — Disk at 80% (61/76GB)
Run on server: `docker system prune -f`

### P3 — Telegram E2E live test
Code complete since v4.9.0. Steps in `docs/features/TELEGRAM_ACCEPTANCE_CRITERIA.md`.

### P4 — Version string stale
`/api/monitoring/health/detailed` reports `version: 4.9.1`. Update `settings.version` in `app/core/config.py` to `4.9.9`.

### P2 (email follow-ups)
- Resend webhook endpoint for delivery/bounce events (needs `RESEND_WEBHOOK_SECRET`)
- Outbox dashboard widget in admin panel
- Digest scheduler `can_send()` check per user before send

---

## Confirmed Facts (from code + live checks)

- **Pricing URL**: `/api/pub/v2/pricing/verifications` ✅ confirmed in `3ea44750`
- **TV balance**: $42.15 — healthy, well above $5 alert threshold
- **Stock**: 416/2353 available — price-based (quantity null due to IP rate limit)
- **Purchases**: Working — `verifications.create()` handles out-of-stock natively
- **Webhook**: Handles both `sms.received` and `v2.sms.received` event types
- **Rate limit root cause**: Startup was firing 2351 concurrent pricing calls → 429. Fixed in `332d766d`.
- **Email outbox**: `email_outbox` + `contact_submissions` tables need `alembic upgrade head` on server
- **Email preference GET**: Was hardcoded `True` — now derives from real data (`978b6b87`)
- **Contact form**: Now persists to DB before responding — forwarding failure no longer loses submission
