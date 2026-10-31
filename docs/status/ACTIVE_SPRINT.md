# ACTIVE SPRINT — v4.9.2 Verification Flow Stability

**Updated**: October 31, 2026
**Version**: 4.9.2
**Focus**: Make verification flow work correctly end-to-end

---

## What Changed From Last Sprint

Previous sprint (P1-P4) is deferred. The verification flow — the core revenue action — has
critical bugs that must be fixed before anything else matters. A user who can't successfully
complete a verification is a lost customer regardless of mobile responsiveness or coverage %.

---

## P1 — Fix Verification Window (CRITICAL — users being wrongly refunded)

**Bug**: Frontend hardcodes `totalDurationMs = 120000` (2 min). TV now gives ~60 min windows.
We auto-cancel valid verifications and refund users who still have 58 minutes left.

**Fix**:
- Add `ends_at` + `created_at` to purchase response (`purchase_endpoints.py`)
- Remove hardcoded 2-min duration from `verification-flow.js`
- Compute `totalDurationMs = ends_at - created_at` dynamically from TV's response
- Auto-timeout only when `ends_at` is actually reached

**Files**: `app/api/verification/purchase_endpoints.py`, `static/js/verification-flow.js`

**Done when**: Countdown shows real remaining time, no premature cancellation.

---

## P2 — TV Webhook for Instant SMS Delivery (HIGH — eliminates polling lag)

**Why**: Currently polling every 2-3s. TV has a webhook system that pushes SMS instantly.
Registering our endpoint eliminates all polling lag and reduces TV API load.

**What TV sends** (from SDK `SmsWebhookEvent`):
```json
{
  "id": "evt_abc",
  "event": "sms.received",
  "attempt": 1,
  "occurredAt": "...",
  "data": {
    "to": "+17022853600",
    "parsedCode": "876094",
    "smsContent": "Your WhatsApp code is 876-094",
    "reservationId": "tv_verification_id",
    "createdAt": "..."
  }
}
```

**What to build**:

1. New file `app/api/verification/tv_webhook.py`:
   - `POST /api/verification/webhook/tv`
   - Dedup by event `id` (TV retries — must be idempotent)
   - Match `reservationId` → our `activation_id` → find verification
   - Update `verification.status = "completed"`, store `sms_code`
   - Push via WebSocket to user's browser instantly
   - Return 200 for ALL event types (billing, backorder) — TV disables webhook on failures

2. Mount router in `main.py`

3. Frontend `verification-flow.js`: listen for `sms_received` WebSocket message,
   stop polling, show code. Polling stays as fallback.

4. Register URL in TV dashboard: app.textverified.com → API Configuration → API Webhooks
   → Endpoint URL: `https://vrenum.app/api/verification/webhook/tv` → Save → Send Test

**Files**: `app/api/verification/tv_webhook.py` (new), `main.py`, `static/js/verification-flow.js`

**Done when**: TV "Send Test" returns success, SMS arrives in browser without polling.

---

## P3 — SSE Streaming Purchase with Real Pre-Check (HIGH — no more silent failures)

**Why**: We charge first, fail after. TV checks availability before charging.
`verifications.create()` blocks 5-30s with no user feedback.

**What to build**:

1. `check_service_available()` in `textverified_service.py` — calls TV pricing endpoint
   before purchase. Fails fast if service unavailable, no charge.

2. `POST /api/verification/request/stream` — SSE endpoint streaming real steps:
   - `pricing_check` → real TV pricing call
   - `balance_check` → real DB query
   - `purchasing` → `verifications.create()` blocks here (5-30s)
   - `validating` → VOIP/area code check
   - `recording` → DB write + debit
   - `complete` / `failed` with specific reason

3. Frontend SSE client in `createVerification()` — reads stream, updates UI per step,
   shows "Cancel (you will not be charged)" until `purchasing` step fires.

4. Loading state card in `verify_modern.html` — visible during purchase, real messages only.

**Files**: `app/services/textverified_service.py`, `app/api/verification/purchase_endpoints.py`,
`static/js/verification-flow.js`, `templates/verify_modern.html`

**Done when**: User sees real step-by-step progress, pricing failure shows error before charge.

---

## P4 — Orphaned Verification Recovery (MEDIUM — silent debit with no UI)

**Why**: If user navigates away during active verification, they're charged but see nothing.

**Fix**: On `/verify` page load, check `localStorage.active_verification_id`,
call status endpoint, restore step 3 UI if still pending.

**Files**: `static/js/verification-flow.js`

**Done when**: Returning to `/verify` during active verification restores the session.

---

## Deferred (not this sprint)

| Item | Reason |
|------|--------|
| TV cost reconciliation (old P1) | Valid but not blocking revenue |
| Mobile responsiveness (old P2) | No users yet to lose |
| Month-end target alert (old P3) | No revenue target set yet |
| Test coverage 81%→90% (old P4) | After flow is stable |
| TV reuse feature | Nice-to-have |

---

## Sprint Completion Criteria

- [ ] P1: Verification countdown uses real `ends_at`, no premature cancellation/refund
- [ ] P2: TV webhook endpoint live, "Send Test" passes, SMS arrives without polling
- [ ] P3: SSE streaming purchase, pricing pre-check before charge, loading state visible
- [ ] P4: Orphaned verification restores on page return

**Reference**: `docs/engineering/development/TV_PURCHASE_FLOW_ALIGNMENT_TASK.md`
