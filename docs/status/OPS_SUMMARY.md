# OPS SUMMARY

**Last Updated**: November 1, 2026
**Version**: 4.9.6
**Status**: ✅ All systems operational

---

## RECENT SPRINTS

### v4.9.6 — TV Webhook Verification + CI Expansion (Nov 1, 2026)
- TV webhook Send Test verified — endpoint returns `{"ok": true}` for all event types
- 18 new tests in `tests/unit/test_tv_webhook.py`
- CI unit-tests gate expanded: 9 → 24 test files
- Coverage floor raised: 15% → 25%
- Fixed `service_name` field in Verification test fixtures

### v4.9.5 — Stability Hardening (Nov 1, 2026)
- Fixed `/api/notifications/categories` 405 (double-prefix router bug)
- Fixed duplicate "Still Waiting" notifications (Redis distributed lock)
- Fixed dark theme notification dropdown (CSS hex fallbacks)
- 16 new tests in `tests/unit/test_stability_fixes.py`

### v4.9.4 — Verification Flow (Oct 31, 2026)
- SSE streaming purchase with real-time progress steps
- Dynamic verification window from TV `ends_at` (removed hardcoded 2-min)
- TV webhook endpoint — instant SMS delivery, HMAC signature enforcement
- Orphaned verification recovery on page return

### v4.9.3 — Frontend Infrastructure (Oct 26, 2026)
- JS test suite wired: 92/92 passing (13 suites)
- Mobile responsiveness: 5 public pages fixed at 320px–768px
- CI `frontend-unit-tests` blocking job added

---

## CI PIPELINE

```
secrets-scan → code-quality → frontend-unit-tests → unit-tests (blocking)
                                                   → integration-tests (non-blocking)
                                                   → e2e-tests (non-blocking, main only)
```

**Unit test gate** (24 files):
- Core: api_key_service, analytics_service, balance_service, cache, models, utils
- Verification: carrier_lookup, phone_validator, sms_polling, verification_flow, tv_webhook
- Notifications: notification_service, notification_center, stability_fixes
- Services: email_service, refund_service, pricing_calculator, tier_service, fraud_detection
- Security: security_utils, webhook_notifications
- Smoke: startup_smoke, mobile_responsiveness

---

## KNOWN GAPS

| Gap | Impact | Plan |
|-----|--------|------|
| Coverage 81.48% vs 90% target | Medium — CI floor at 25% | Expand CI test gate each sprint |
| Telegram E2E not live-tested | Low — code complete | Manual test with real Telegram account |
| Integration tests non-blocking | Medium | Stabilise and promote to blocking |

---

## INFRASTRUCTURE

| Component | Status |
|-----------|--------|
| FastAPI app (gunicorn, 2 workers) | ✅ Running |
| PostgreSQL | ✅ Running |
| Redis | ✅ Running |
| TV webhook endpoint | ✅ Live, registered in TV dashboard |
| WebSocket manager | ✅ Active |
| Background services (9) | ✅ All active |
| Sentry error tracking | ✅ Active |
| BetterStack uptime | ✅ Active |
| GitHub Actions CI | ✅ Active (24-file gate) |
