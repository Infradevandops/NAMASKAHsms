# ACTIVE SPRINT — v4.9.4 Stability Hardening

**Updated**: November 1, 2026
**Version**: 4.9.4
**Focus**: Stabilise dashboard notifications, eliminate duplicate events, fix dark theme

---

## Sprint Status: ✅ ALL TASKS COMPLETE

---

## P1 — Fix `/api/notifications/categories` 405 Error ✅ COMPLETE

**Bug**: `notification_center_router` had `prefix="/api/notifications"` and was included into a parent router that also had `prefix="/api/notifications"`. Result: double prefix `/api/notifications/api/notifications/categories` → 405.

**Fix applied**:
- `app/api/core/notification_endpoints.py` — strip `notification_center_router.prefix = ""` before `include_router()`. Parent prefix already covers the path.

**Files changed**: `app/api/core/notification_endpoints.py`

---

## P2 — Duplicate "Still Waiting" Notifications ✅ COMPLETE

**Bug**: Two gunicorn workers both called `_notify_waiting()` for the same verification → user saw duplicate "⏳ Still Waiting" notifications. `_handle_timeout` already had a Redis lock; `_notify_waiting` did not.

**Fix applied**:
- `app/services/sms_polling_service.py` — `_notify_waiting()` now accepts `verification_id` kwarg and acquires `lock:notif_waiting:{verification_id}` (TTL 60s) before creating the notification. Second worker finds lock held and returns immediately.
- Call site in `_poll_textverified` updated to pass `str(verification.id)`.

**Files changed**: `app/services/sms_polling_service.py`

---

## P3 — Dark Theme CSS Hex Fallbacks ✅ COMPLETE

**Bug**: `notification-improvements.css` dark mode selectors used bare `var(--gray-800)` etc. with no fallback. If CSS variables weren't defined in the dark scope, dropdown stayed white.

**Fix applied**:
- `static/css/notification-improvements.css` — all `[data-theme="dark"]` selectors now use `var(--gray-NNN, #hexvalue)` fallback syntax. Added missing dark overrides for `.notification-title`, `.notification-message`, `.notification-time`.

**Files changed**: `static/css/notification-improvements.css`

---

## Tests ✅

- `tests/unit/test_stability_fixes.py` — 16 new tests covering all 3 fixes
  - 6 tests: `/api/notifications/categories` returns 200, correct shape, accurate counts
  - 5 tests: `_notify_waiting` Redis lock deduplication
  - 5 tests: CSS hex fallback static analysis
- Added to CI `unit-tests` job in `.github/workflows/ci.yml`

---

## Next Sprint Candidates

| Item | Priority |
|------|----------|
| Telegram E2E test (live device) | Manual |
| Test coverage 81% → 90% | High |
| Phase 2 Analytics (cohort charts, churn model) | Medium |
| SDK libraries (Python, JavaScript) | Low |
| Multi-region deployment | Q3 2026 |

**Reference**: `docs/status/NOTIFICATION_DARK_THEME_FIXES.md`


**Bug**: Frontend hardcoded `totalDurationMs = 120000` (2 min). TV gives ~60 min windows.
Auto-cancelling valid verifications and refunding users who still had 58 minutes left.

**Fix applied**:
- `purchase_endpoints.py` already returned `ends_at` + `created_at` in response
- `verification-flow.js` `createVerification()` now reads `ends_at`/`created_at` from SSE `complete` event
- Polling `startPolling()` computes `totalDurationMs` dynamically from `ends_at - created_at`
- Auto-timeout only fires when `remainingMs <= 0` (server's real window)
- Hardcoded 2-min duration removed

**Files changed**: `static/js/verification-flow.js`

---

## P2 — TV Webhook for Instant SMS Delivery ✅ COMPLETE

**Fix applied**:
- `app/api/verification/tv_webhook.py` — duplicate `_verify_signature` removed, single clean HMAC implementation
- HMAC signature enforcement added: reads `TV_WEBHOOK_SECRET` from settings, validates `X-Signature` header
- Router mounted in `main.py` at `/api/verification/webhook/tv`
- `static/js/components/sms-websocket.js` — dispatches `ws:message` CustomEvent on every WebSocket message
- `static/js/verification-flow.js` — `handleWebSocketSmsReceived()` added, listens for `ws:message`, stops polling and shows code instantly on `sms_received` event

**Still needs** (manual step — cannot be automated):
- Register endpoint in TV dashboard: app.textverified.com → API Configuration → API Webhooks
- Endpoint URL: `https://vrenum.app/api/verification/webhook/tv`
- Click Save → Send Test → verify `{"ok": true}` response

**Files changed**: `app/api/verification/tv_webhook.py`, `static/js/components/sms-websocket.js`, `static/js/verification-flow.js`

---

## P3 — SSE Streaming Purchase ✅ COMPLETE

**Fix applied**:
- `app/services/textverified_service.py` — `check_service_available()` added: calls TV pricing endpoint before purchase, returns `{available, price, reason}`
- `app/api/verification/purchase_endpoints.py` — `POST /verification/request/stream` SSE endpoint added
  - Streams: `pricing_check → balance_check → purchasing → validating → recording → complete/failed`
  - Each step maps to a real backend operation
  - `purchasing` step fires only when TV `purchase_with_failover()` is called (charge commits here)
  - `failed` events include specific `reason` and `message`
  - Existing `POST /verification/request` untouched (API key users, backward compat)
- `static/js/verification-flow.js` — `createVerification()` replaced with SSE streaming client
  - Shows `purchase-loading-card` during stream
  - Cancel button visible until `purchasing` step fires, then hidden
  - Each SSE step updates loading message
  - `cancelPurchase()` added for pre-charge cancellation
- `templates/verify_modern.html` — `purchase-loading-card` added between modal container and step-2

**Files changed**: `app/services/textverified_service.py`, `app/api/verification/purchase_endpoints.py`, `static/js/verification-flow.js`, `templates/verify_modern.html`

---

## P4 — Orphaned Verification Recovery ✅ COMPLETE (was already done)

**Status**: Already implemented in `DOMContentLoaded` in `verification-flow.js`.
- Checks `localStorage.active_verification_id` on page load
- Calls status endpoint, restores step 3 UI if still pending
- Computes `totalDurationMs` from `ends_at`/`created_at` on restore

---

## Sprint Completion Criteria

- [x] P1: Verification countdown uses real `ends_at`, no premature cancellation/refund
- [x] P2: TV webhook endpoint live, HMAC verified, SMS arrives without polling (pending TV dashboard registration)
- [x] P3: SSE streaming purchase, pricing pre-check before charge, loading state visible
- [x] P4: Orphaned verification restores on page return

---

## Next Sprint Candidates

| Item | Priority |
|------|----------|
| Register TV webhook URL in dashboard | Immediate (manual) |
| Test coverage 81% → 90% | High |
| Phase 2 Analytics (cohort charts, churn model) | Medium |
| SDK libraries (Python, JavaScript) | Low |
| Multi-region deployment | Q3 2026 |

**Reference**: `docs/engineering/development/TV_PURCHASE_FLOW_ALIGNMENT_TASK.md`
