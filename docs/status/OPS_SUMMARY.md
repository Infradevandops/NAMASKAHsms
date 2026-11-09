# OPS SUMMARY

**Last Updated**: November 2026 (post email hardening)
**Deployed**: `e06e91ce` on origin/main (manual deploy trigger needed — see P0)
**Server**: https://vrenum.app — TV operational, $42.15 balance, 416 services live

---

## CURRENT SERVER STATE

| Check | Result |
|-------|--------|
| `GET /health` | `degraded` (fix pushed, awaiting manual deploy) |
| `GET /api/monitoring/health/detailed` | `healthy` |
| TV balance | $42.15 |
| TV enabled | true |
| Services available | 416 / 2353 |
| Quantity data | null on all (secondary IP not whitelisted with TV) |
| DB latency | ~165ms (Neon) |
| Redis latency | ~118ms (Upstash) |
| Memory | 51.7% (0.79/1.9GB) |
| Disk | 80% (61/76GB) — watch |
| Uptime | 3d 16h+ |
| Version reported | 4.9.1 (stale — should be 4.9.9) |

---

## CREDENTIAL ROTATION

All credentials rotated. One infrastructure action remaining.

| Credential | Status |
|------------|--------|
| TEXTVERIFIED_API_KEY | ✅ Rotated |
| JWT_SECRET_KEY | ✅ Rotated |
| ADMIN_PASSWORD | ✅ Rotated |
| DATABASE_URL (Neon password) | ✅ Rotated |
| REDIS_URL (Upstash token) | ✅ Rotated |
| PAYSTACK_SECRET_KEY + PUBLIC_KEY | ✅ Rotated |
| GOOGLE_CLIENT_ID + SECRET | ✅ Rotated |
| TELEGRAM_BOT_TOKEN | ✅ Rotated |
| SENTRY_DSN | ✅ Rotated |
| **Server IP whitelisted with TV** | ⚠️ Pending |

---

## SPRINT HISTORY — COMMITS SINCE LAST OPS SUMMARY

### Purchase Flow Overhaul (Nov 2–3, 2026) — v4.9.8–v4.9.9

Root cause: startup fired 2351 concurrent pricing calls → TV 429 → broken stock,
broken pricing preview, 500 errors on purchase.

| Commit | Fix |
|--------|-----|
| `fa4ec0d8` | Purchase 500 — Decimal/float mismatch + NOT NULL on purchase_outcomes |
| `887854f3` | Pricing screen shows real tier-adjusted cost |
| `fb9d35d6` | Real stock availability — quantity from cache before TV charges |
| `332d766d` | Root cause: remove bulk pricing fetch from startup (was causing 429) |
| `b30f579b` | Stock map price-based availability + cancel flow + polling guard |
| `6d082955` | build_stock_map: skip outcome check for null-price services (2351→58 Redis calls) |
| `37c5c49e` | Prioritize popular services in pricing fetch, semaphore 10→3 |
| `fe4b5cf4` | Inline pricing timeout 12s→30s, prewarm 20s→60s |
| `950ce684` | Non-blocking service list — names immediately, prices in background |
| `4302e789` | `TEXTVERIFIED_PROXY_URL` env var — route TV calls through proxy if IP blocked |

### Webhook + Pricing URL + Balance (Nov 2, 2026)

| Commit | Fix |
|--------|-----|
| `3ea44750` | TV webhook: handle `v2.sms.received` + **pricing URL confirmed**: `/api/pub/v2/pricing/verifications` |
| `dc9be6ca` | Balance display consistency across all pages |
| `6baaafb2` | Fix detached SQLAlchemy instance in notification email dispatch |

### CI + Security (Nov 2, 2026)

| Commit | Fix |
|--------|-----|
| `5c55c71a` | Add CodeQL workflow |
| `0c2bea62` | Streamline CI ruleset for solo/small team |
| `5b0c1608` | CI green — isort + gitleaks allowlist for template files |

### This Session (Nov 7, 2026)

| Commit | Fix |
|--------|-----|
| `23560e8c` | v4.9.9 changelog + fix duplicate version numbers |
| `e06e91ce` | Health check fix: accept `TEXTVERIFIED_EMAIL` not just `TEXTVERIFIED_USERNAME` |

### Email System Hardening (Nov 2026)

| Commit | Fix |
|--------|-----|
| `978b6b87` | EMAIL-001–043: email classes, preference policy, outbox worker, contact durability, template autoescape, 30 tests |
| `1bc1e955` | Formatting fixes (black/isort) |
| `1042b600` | gitleaks allowlist for `.env.development` dev placeholders |
| `d8239024` | TASKS.md all checkboxes ticked with commit evidence |

---

## OPEN OPS ACTIONS

1. **Trigger deploy manually** — GitHub Actions → Deploy to Production → Run workflow.
   Verify `GET /health` returns `healthy` after.

2. **Run `alembic upgrade head` on server** — adds `email_outbox` and `contact_submissions` tables.
   ```bash
   ssh root@<vps-ip> "cd ~/vrenum && docker compose exec app alembic upgrade head"
   ```

3. **Whitelist new server IP with TextVerified** — contact TV support with the new IP.
   Until done: `quantity: null` on all services (cosmetic only, purchases work).
   Alternatively set `TEXTVERIFIED_PROXY_URL` in `.env.production` to route through proxy.

4. **`docker system prune -f` on server** — disk at 80%, reclaim old image layers.

5. **Update version string** — `app/core/config.py` `version` field → `4.9.9`.

6. **Telegram E2E test** — manual test with real Telegram account.

7. **Resend webhook endpoint** — add `RESEND_WEBHOOK_SECRET` to `.env.production` and implement endpoint for delivery/bounce events (P2).

---

## CI PIPELINE

```
secrets-scan → code-quality → frontend-unit-tests → unit-tests (BLOCKING)
                                                   → integration-tests (non-blocking)
                                                   → e2e-tests (non-blocking, main only)
```

Blocking gate: 24 test files, `--cov-fail-under=25`.

---

## CONFIRMED TECHNICAL FACTS

| Fact | Source |
|------|--------|
| TV pricing URL: `/api/pub/v2/pricing/verifications` | `3ea44750` |
| TV webhook event types: `sms.received` + `v2.sms.received` | `3ea44750` |
| Startup bulk pricing caused 429 rate limiting | `332d766d` |
| `quantity: null` = secondary IP not whitelisted, not a code bug | Live check |
| `tv_configured: false` = wrong env var name in health check | `e06e91ce` |
| All credentials rotated | Confirmed by user |
| TV balance $42.15 | Live `/api/monitoring/health/detailed` |
| Email preference GET was hardcoded `True` — now real data | `978b6b87` |
| Contact form now persists to DB before ack | `978b6b87` |
| `email_outbox` + `contact_submissions` tables need migration on server | `a1b2c3d4e5f6` |

---

## INFRASTRUCTURE

| Component | Status |
|-----------|--------|
| FastAPI app (uvicorn, 2 workers) | ✅ Running |
| PostgreSQL (Neon) | ✅ Running, 165ms |
| Redis (Upstash) | ✅ Running, 118ms |
| TV webhook endpoint | ✅ Live, handles v2.sms.received |
| WebSocket manager | ✅ Active |
| Background services (13 loops) | ✅ All active |
| Sentry error tracking | ✅ Active |
| BetterStack uptime | ✅ Active |
| GitHub Actions CI | ✅ Active |
| Deploy workflow | ✅ CI-gated (manual trigger needed for current fix) |
| `TEXTVERIFIED_PROXY_URL` | ✅ Supported in code, not yet set in .env.production |
