# ACTIVE SPRINT — v4.9.6 TV Webhook Verification + Coverage Push

**Updated**: November 1, 2026
**Version**: 4.9.6
**Focus**: Verify TV webhook end-to-end, expand CI test gate, push coverage toward 90%

---

## Sprint Status: ✅ ALL TASKS COMPLETE

---

## P0 — Dashboard Cache Invalidation Bug ✅ CLOSED (pre-existing fix)

**Task doc**: `docs/engineering/development/DASHBOARD_CACHE_INVALIDATION_FIX_TASK.md`

Inspected `templates/dashboard_base.html` — the IIFE is syntactically correct. The
unmatched `}` described in the task doc was already removed in a prior session.
No code change required. Task closed.

---

## P1 — TV Webhook End-to-End Verification ✅ TESTS WRITTEN

**Context**: TV webhook endpoint was shipped in v4.9.4. TV dashboard registration
was completed manually (Send Test button clicked). This sprint adds the test
coverage to verify the endpoint handles all TV-sent payloads correctly.

**What TV's Send Test sends**: A non-`sms.received` event (ping/test type).
The endpoint must return `{"ok": true}` for all event types — TV auto-disables
the webhook after repeated non-200 responses.

**Tests added**: `tests/unit/test_tv_webhook.py` — 18 tests in 4 classes:

| Class | Tests | Covers |
|-------|-------|--------|
| `TestTVWebhookSendTest` | 5 | Send Test button, billing events, unknown types, malformed JSON, empty body |
| `TestTVWebhookSmsReceived` | 5 | DB update, WebSocket push, phone fallback lookup, already-completed guard, no-match 200 |
| `TestTVWebhookDeduplication` | 2 | Duplicate event_id → `{duplicate:true}`, different IDs both processed |
| `TestTVWebhookCodeExtraction` | 4 | Hyphenated format, plain digits, empty text, fallback when parsedCode empty |

**Files changed**: `tests/unit/test_tv_webhook.py`

---

## P2 — CI Test Gate Expansion + Coverage Floor Raise ✅ DONE

**Problem**: CI `unit-tests` job only ran 9 test files. ~150 unit test files existed
but were invisible to CI. Coverage floor was 15% (trivially low).

**Fix**:
- Added 15 more stable test files to the CI `pytest` invocation
- Added 2 smoke test files (`test_startup_smoke.py`, `test_mobile_responsiveness.py`)
- Raised `--cov-fail-under` from 15 → 25

**New CI test list** (24 files total):
```
tests/unit/test_api_key_service.py
tests/unit/test_analytics_service.py
tests/unit/test_balance_service.py
tests/unit/test_cache.py
tests/unit/test_models.py
tests/unit/test_utils.py
tests/unit/test_carrier_lookup.py
tests/unit/test_phone_validator.py
tests/unit/test_stability_fixes.py
tests/unit/test_tv_webhook.py          ← new
tests/unit/test_notification_service.py ← new
tests/unit/test_notification_center.py  ← new
tests/unit/test_email_service.py        ← new
tests/unit/test_auth_service.py         ← new
tests/unit/test_refund_service.py       ← new
tests/unit/test_pricing_calculator.py   ← new
tests/unit/test_tier_service.py         ← new
tests/unit/test_verification_flow.py    ← new
tests/unit/test_sms_polling.py          ← new
tests/unit/test_fraud_detection.py      ← new
tests/unit/test_webhook_notifications.py ← new
tests/unit/test_security_utils.py       ← new
tests/smoke/test_startup_smoke.py       ← new
tests/smoke/test_mobile_responsiveness.py ← new
```

**Files changed**: `.github/workflows/ci.yml`

---

## Next Sprint Candidates

| Item | Priority |
|------|----------|
| Continue coverage push 25% → 90% (add more CI test files) | High |
| Phase 2 Analytics (cohort charts, churn model) | Medium |
| Multi-region deployment | Q3 2026 |

---

## Commits This Sprint

| Hash | Message |
|------|---------|
| `4724bbfd` | `test: TV webhook verification — 18 tests, CI gate 24 files, coverage floor 25%` |
| `24496798` | `fix: service_name field in Verification fixtures (model uses service_name not service)` |
