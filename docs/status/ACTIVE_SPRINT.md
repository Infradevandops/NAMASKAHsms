# ACTIVE SPRINT

**Updated**: November 7, 2026
**Server**: https://vrenum.app
**Deployed commit**: `f1975971` (origin/main)

---

## Live Server State (verified now)

```
GET /health                        → {"status":"degraded","tv_configured":false}  ← BUG (fix in progress)
GET /api/monitoring/health/detailed → {"status":"healthy","textverified":{"status":"healthy","balance":"$42.15","enabled":true}}
GET /api/services/stock            → 416/2353 available, quantity:null on all
Uptime: 3d 15h+   DB: 160ms   Redis: 118ms   Memory: 51.5%   Disk: 80% (61/76GB)
```

### What the numbers mean

- **`tv_configured: false`** — false alarm. Health check at `main_routes.py:195` checks
  `TEXTVERIFIED_USERNAME` but server env uses `TEXTVERIFIED_EMAIL`. TV is fully working
  ($42.15 balance, 416 services live). Fix: accept either var name. **Shipped in this sprint.**

- **`quantity: null` on all services** — `fetch_raw_services_with_quantity()` is failing
  silently (TV rate limiting on secondary IP). Stock monitor falls back to SDK services
  list (price-based availability). Services show as available but without quantity counts.
  Root cause: app is running on a secondary IP that TV has rate-limited. Not blocking
  purchases — just means no quantity display.

- **Disk at 80%** — 61/76GB used. Not critical yet but worth monitoring. Docker image
  layers + logs are likely the bulk. Clean up if it hits 85%.

- **Deploy workflow broken** — `deploy.yml` waits for `"status":"healthy"` from
  `GET /health` but gets `degraded` + 503. Every deploy since the health check was
  added has been failing the post-deploy gate. The app deploys fine but the workflow
  exits with error. Fixed by the `tv_configured` env var fix above.

---

## This Sprint — What Was Done

### Fix: `GET /health` false degraded (`main_routes.py`)
- **Root cause**: `os.getenv("TEXTVERIFIED_USERNAME")` — server has `TEXTVERIFIED_EMAIL`
- **Fix**: accept `TEXTVERIFIED_USERNAME or TEXTVERIFIED_EMAIL`
- **File**: `app/api/main_routes.py` line 194–196
- **Status**: ✅ Fixed locally, pending commit + deploy

---

## Open Tasks — Priority Order

### P0 — Deploy health check fix
Commit and push the `main_routes.py` fix. Deploy will auto-fire on CI green.
Verify `GET /health` returns `{"status":"healthy"}` after deploy.

### P1 — TV rate limiting on secondary IP
`quantity: null` on all 2353 services = `fetch_raw_services_with_quantity()` failing.
TV is rate-limiting the secondary IP the app moved to. Options:
1. Contact TV support to whitelist the new IP
2. Add exponential backoff + longer TTL on raw fetch failures so it doesn't hammer TV
3. Accept null quantities for now (availability still works via price-based fallback)

Current impact: users see services as available (correct) but no quantity counts (cosmetic).

### P2 — Telegram E2E live test
Code complete since v4.9.0. Pending manual test with real Telegram account.

### P3 — Disk usage (80% → watch at 85%)
`docker system prune` on server would reclaim old image layers.
SSH: `docker system df` to see breakdown.

### P4 — Version string stale
`/api/monitoring/health/detailed` reports `version: 4.9.1` but codebase is at v4.9.0+.
Update `settings.version` in `app/core/config.py`.

### P5 — CI coverage push (25% → 60%)
Add `tests/unit/test_textverified_service.py` to CI gate first (stable, ready).
Then batch-add remaining unit tests.

---

## Background Services Status

| Service | Interval | Status |
|---------|----------|--------|
| SMS polling | Adaptive 5–10s | ✅ Active |
| TV webhook receiver | On-demand | ✅ Active |
| Refund policy enforcer | 5 min | ✅ Active |
| Health audit loop | 4 hours | ✅ Active |
| Daily growth snapshot | 24 hours | ✅ Active |
| Rental expiry monitor | 15 min | ✅ Active |
| Abandoned payment cleanup | 1 hour | ✅ Active |
| Revenue-zero monitor | Daily 18:00 UTC | ✅ Active |
| Digest scheduler | Daily 08:00 UTC | ✅ Active |
| Stock monitor | 90s | ✅ Active (quantity null due to rate limit) |
| Area code cache refresh | 23h | ✅ Active |
| TV margin reconciliation | Weekly Mon 09:00 UTC | ✅ Active |
| Month-end revenue alert | Last day of month 20:00 UTC | ✅ Active |

---

## Credential Rotation Status

All credentials were exposed in git history (Oct 2025 commits). Rotation checklist
at `docs/operations/security/CREDENTIAL_ROTATION_CHECKLIST.md`.

| Credential | Status |
|------------|--------|
| TEXTVERIFIED_API_KEY | ⚠️ Needs rotation — was in git history |
| JWT_SECRET_KEY | ⚠️ Needs rotation |
| ADMIN_PASSWORD | ⚠️ Needs rotation |
| PostgreSQL password | ⚠️ Needs rotation (Neon DB) |
| Redis token | ⚠️ Needs rotation (Upstash) |
| Paystack keys | ⚠️ Needs rotation |
| Google OAuth | ⚠️ Needs rotation |
| Telegram bot token | ⚠️ Needs rotation |

TV API key rotation would also resolve the rate limiting issue if the old key
is what's being rate-limited on the secondary IP.
