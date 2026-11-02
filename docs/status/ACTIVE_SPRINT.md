# ACTIVE SPRINT — Stability Pass Before Version Lock

**Updated**: November 1, 2026
**Focus**: Stabilise everything shipped in the last 24h, confirm CI green on `ee895ce8`,
           then define the next phase. No version bump until CI is confirmed green and
           the pending deploy fires.

---

## Sprint Context

This sprint closes out a dense 24-hour push that shipped 15 commits across 3 themes:

1. **Verification flow hardening** (v4.9.4–v4.9.7) — SSE purchase, TV webhook, dynamic
   `ends_at`, orphan recovery, stock P0 fixes, notification bugs
2. **TV SDK correctness** — 5 broken rental SDK calls fixed, voice pricing corrected,
   `max_price` wired, `reactivate` before `report`, `ends_at` persisted to DB
3. **Area code selector** — city enrichment, surcharge-accurate pricing, 23h cache refresh

---

## Commits Shipped — Last 24 Hours

| Hash | Time | What | CI | Prod |
|------|------|------|----|------|
| `750a8d9f` | 15:52 | SSE purchase, dynamic ends_at, TV webhook, orphan recovery | ✅ | ✅ Live |
| `27fb5484` | 15:52 | Fix 405 on /api/notifications/categories | ✅ | ✅ Live |
| `c7787519` | 15:53 | Redis lock on _notify_waiting (duplicate notifications) | ✅ | ✅ Live |
| `59b2b3df` | 15:53 | Dark theme CSS hex fallbacks, 16 stability tests | ✅ | ✅ Live |
| `4724bbfd` | 16:17 | 18 TV webhook tests, CI gate 24 files, coverage floor 25% | ✅ | ✅ Live |
| `24496798` | 16:23 | Fix service_name field in Verification fixtures | ✅ | ✅ Live |
| `ea07a447` | 16:24 | Docs — ACTIVE_SPRINT + CHANGELOG v4.9.6 | ✅ | ✅ Live |
| `8d6aa0bd` | 16:31 | Docs — PLATFORM_STATUS, OPS_SUMMARY v4.9.6 | ✅ | ✅ Live |
| `ebc2a901` | 16:42 | Docs — TV stock accuracy assessment | ✅ | ✅ Live |
| `47d69fd1` | 16:55 | P0: availability gate, null-price filter, stock monitor, spinner | ✅ | ✅ Live |
| `ae3b8be0` | 19:16 | Docs — v4.9.7 status update | ✅ | ✅ Live |
| `2bf97dbc` | 20:07 | Green-CI-gated deploy, real /health endpoint, feature smoke | ✅ | ✅ Live |
| `325cbdc1` | 20:21 | Two-branch strategy, CI targets main PRs, 6 stale branches deleted | ✅ | ✅ Live |
| `3f805f8a` | 20:39 | TV SDK fixes + area code city enrichment + 23h cache refresh | ⚠️ CI fail (2 tests) | ⏳ Pending |
| `ee895ce8` | 20:41 | Fix 2 broken reservation tests to match SDK-correct impl | ⏳ Running | ⏳ Pending deploy |

**Deploy gate**: `deploy.yml` only fires when CI passes. Commits 1–13 are live.
Commits 14–15 deploy automatically once `ee895ce8` CI goes green.

---

## What Is Live Right Now

### Verification Flow
- ✅ SSE streaming purchase with step-by-step progress
- ✅ "Cancel (you will not be charged)" visible until charge commits
- ✅ Dynamic `ends_at` window from TV — no hardcoded 2-min timeout
- ✅ TV webhook instant SMS delivery — no polling wait
- ✅ Orphan verification recovery on page reload
- ✅ "Still working..." message after 10s on purchasing step
- ✅ P0 availability gate on legacy purchase path (fail fast <1s)
- ✅ Null-price services filtered from picker
- ✅ Out-of-stock services greyed out and unclickable

### Infrastructure
- ✅ Real `/health` endpoint with DB + Redis checks
- ✅ Deploy hard-gated on CI pass (no more broken deploys)
- ✅ Stock monitor 90s loop (cache always warm)
- ✅ demandBadge JS broken ternary fixed

### Notifications
- ✅ 405 fix on /api/notifications/categories
- ✅ Duplicate "Still Waiting" notifications eliminated (Redis lock)
- ✅ Dark theme notification dropdown CSS fixed

---

## Pending Deploy (ee895ce8 — awaiting CI green)

- ⏳ Area code modal shows city names ("212 — New York, NY")
- ⏳ /check endpoint graceful fallback on TV outage
- ⏳ check_service_available() returns surcharge-inclusive price
- ⏳ 5 broken rental SDK calls fixed (AttributeError in prod)
- ⏳ Voice pricing uses correct NumberType.VOIP
- ⏳ max_price wired to TV's verifications.create()
- ⏳ reactivate before report on timeout (saves refund cost)
- ⏳ ends_at persisted to DB in SSE path
- ⏳ 23h area code cache background refresh

---

## Open Tasks — This Sprint

### P0 — Confirm CI green on ee895ce8
Check `https://github.com/Infradevandops/NAMASKAHsms/actions` for the run on `ee895ce8`.
The two fixed tests (`test_create_reservation_success`, `test_get_reservation_messages`)
now mock `ReservationSaleExpanded` + `reservations.details()` correctly.
No other CI-gated files were touched.

### P1 — Verify pricing URL on VPS (unverified claim)
`check_service_available()` now uses the SDK `verifications.pricing()` method which
internally calls `/api/pub/v2/pricing/verifications`. The old raw HTTP bypass used
`/api/pub/v2/verifications/pricing`. Whether TV accepts both paths is unverified —
Cloudflare blocks curl from dev machines.

**Test from VPS**:
```bash
# Get bearer token
curl -s -X POST https://www.textverified.com/api/pub/v2/auth \
  -H "X-API-KEY: $TEXTVERIFIED_API_KEY" \
  -H "X-API-USERNAME: $TEXTVERIFIED_EMAIL"

# Test old path
curl -s -X POST https://www.textverified.com/api/pub/v2/verifications/pricing \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"serviceName":"whatsapp","areaCode":false,"carrier":false,"numberType":"mobile","capability":"sms"}'

# Test SDK path
curl -s -X POST https://www.textverified.com/api/pub/v2/pricing/verifications \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"serviceName":"whatsapp","areaCode":false,"carrier":false,"numberType":"mobile","capability":"sms"}'
```

### P2 — Telegram E2E live test
Code complete since v4.9.0. Pending manual test with a real Telegram account.
Steps in `docs/features/TELEGRAM_ACCEPTANCE_CRITERIA.md`.

---

## Next Phase — After Stability Confirmed

### Phase: CI Coverage Push (25% → 60%)

The CI gate runs 24 test files. ~150 test files exist but are not wired.
Goal: expand the gate in batches, raise `--cov-fail-under` to 60%.

**Next batch to audit and add** (audit for stability before wiring):
```
tests/unit/test_textverified_service.py   ← already stable, add now
tests/unit/test_verification_endpoints.py
tests/unit/test_payment_service.py
tests/unit/test_auth_endpoints.py
tests/unit/test_wallet_service.py
tests/unit/test_transaction_service.py
tests/unit/test_tier_manager.py
tests/unit/test_quota_service.py
tests/unit/test_stock_monitor.py
tests/unit/test_area_code_check.py
```

**Process**: Run each file locally against the test DB, fix any failures, then add to
`ci.yml` pytest invocation. Raise `--cov-fail-under` by 5% per batch.

### Phase: Phase 2 Analytics

Pre-work: assess what data is already in the DB (user_events table, purchase_outcomes).
Identify which charts can be served from existing queries vs new aggregations.
Create task doc at `docs/features/PHASE2_ANALYTICS.md`.

Scope:
1. Cohort analysis — user retention by signup week
2. Revenue breakdown — by tier, by service, by day
3. Churn signal — users with no activity in 14+ days

### Phase: Reuse + Reactivate (TV cost savings)

`verifications.reuse()` and `verifications.reactivate()` are implemented in
`textverified_service.py` but never surfaced to users.

- **Reactivate**: When a verification times out, check `can_reactivate` first (already
  done in `_handle_timeout`). If reactivated, show user "Extending your window..." and
  restart the polling timer. No repurchase cost.
- **Reuse**: After a completed verification, if `reusable_until` is not expired, offer
  "Verify another service with this number" at a lower price. Surface in the post-code
  receipt UI.

### Phase: smsAndVoiceCombo capability

TV supports `ReservationCapability.SMS_AND_VOICE_COMBO`. Currently unused.
Would allow one number to receive both SMS and voice — useful for services that
try SMS first then fall back to voice call. Pricing TBD from TV.

---

## Acceptance Criteria for Stability Lock

Before bumping to a stable version:

- [ ] CI green on `ee895ce8` confirmed
- [ ] Deploy fired and server running `ee895ce8`
- [ ] Pricing URL verified from VPS (both paths or confirm SDK path only)
- [ ] Telegram E2E live test passed
- [ ] `test_textverified_service.py` added to CI gate (it's stable now)
- [ ] No Sentry errors from the new SDK fixes in first 24h post-deploy
