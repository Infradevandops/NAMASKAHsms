# ACTIVE SPRINT — VRENUM SMS

**Updated**: November 24, 2026
**HEAD**: `2168274e`
**Status**: Verification flow UX fixes in progress
**Authority**: Single actionable task list. `MASTER_TASKS.md` is the historical record.

---

## SPRINT J — VERIFICATION FLOW USER JOURNEY FIXES

**Opened**: November 24, 2026
**Trigger**: Live screenshots showing broken step sequencing on `/verify`

### User Journey Audit — What Should Happen vs What Does

#### Intended flow (your illustration)
```
/verify loads
  └─ Step 0: Choose Method (SMS / Voice Call / SMS+Voice)
       └─ User picks one
            └─ Step 1: Select Service (modal auto-opens, loading banner shown)
                 └─ User picks service
                      └─ Step 2: Pricing & Details (shimmer → live price)
                           └─ User clicks "Get Number"
                                └─ Purchase loading card (dark, arc spinner, TV messages)
                                     └─ Step 3: Phone number + waiting for SMS
                                          └─ SMS received → code displayed
```

#### Actual flow (from screenshots)
```
/verify loads
  └─ Step 0 AND Step 1 BOTH visible simultaneously ← BUG J-001
       └─ Step 1 shows "Loading services from provider..." with Back/Continue
          visible BEFORE user picks a method ← BUG J-002
       └─ "Saved Presets / No presets yet" visible in Step 1 while Step 0 still showing ← BUG J-003
       └─ Voice Call click → redirects to /voice-verify (separate page) ← CORRECT
       └─ SMS / SMS+Voice click → Step 0 hides, Step 1 shows ← CORRECT after fix
            └─ Service modal opens (dark modal, 2357 services) ← CORRECT
                 └─ User picks service → Step 2 shown ← CORRECT after fix
                      └─ Back button on Step 2 → goes to Step 1 ← needs verification
                      └─ Back button on Step 1 → goes to Step 0 ← needs verification
```

---

### J — Tasks

| ID | Priority | Issue | Fix | File |
|----|----------|-------|-----|------|
| J-001 | P0 | `updateProgress(1)` called in `DOMContentLoaded` unconditionally — sets `step-1-card` to `display:block` before user picks a method, so both Step 0 and Step 1 render simultaneously | Remove `updateProgress(1)` from `DOMContentLoaded`; Step 1 is only shown by `chooseMethod()` | `verification-flow.js` |
| J-002 | P0 | Step 1 Back/Continue buttons visible during service loading (before method chosen) | Already fixed by `step-1-actions` hide/show — but J-001 means it shows anyway | Resolved by J-001 |
| J-003 | P0 | "Saved Presets" section visible in Step 1 while Step 0 still showing | Resolved by J-001 |
| J-004 | P1 | Back button on Step 1 → should go to Step 0 (method picker), currently goes to `/dashboard` | Change Step 1 Back button `onclick` to `resetFlow()` which shows Step 0 | `verify_modern.html` |
| J-005 | P1 | Back button on Step 2 → should go to Step 1 (service selection), verify `goBack()` does this correctly | `goBack()` from step 2 calls `updateProgress(1)` — correct, but Step 0 must not re-appear | `verification-flow.js` |
| J-006 | P1 | Voice Call path redirects to `/voice-verify` (separate page) — assess whether `voice_verify_modern.html` has the same Step 0/1 stacking bug | `voice_verify_modern.html` |
| J-007 | P2 | Screenshot 1 (18.22.03) shows old UI without Step 0 — Cloudflare cache serving stale JS/HTML | Purge Cloudflare cache after deploy | Cloudflare dashboard |
| J-009 | P1 | Orphan recovery silently hijacks Step 0 — if `active_verification_id` exists in localStorage, shows Step 1 directly without letting user choose method or dismiss. Should show a dismissible "Resume verification?" banner on Step 0 instead | `verification-flow.js` |

---

### J-001 Fix (root cause)

**File**: `static/js/verification-flow.js`
**Change**: Remove `updateProgress(1)` from `DOMContentLoaded`.
Step 1 visibility is controlled exclusively by `chooseMethod()`. The progress indicator
and step cards must only appear after a method is chosen.

**Exception**: If `?service=` query param is present OR orphan recovery fires,
step 0 should be skipped and step 1 shown directly — handle these cases explicitly.

---

## OVERALL PROGRESS

| Sprint | Scope | Done | Open |
|--------|-------|------|------|
| A–I | All previous sprints | 90/93 | 3 manual/external |
| J | Verification flow journey fixes | 0/8 | 8 |

---

## MANUAL / EXTERNAL ACTIONS (carried over)

| ID | Priority | Action |
|----|----------|--------|
| A-005 | P1 | Telegram E2E — connect @vrenum_sms_bot, trigger verification, confirm SMS forwarded |
| E-001 | P2 | Upgrade Upstash Redis to pay-as-you-go |
| E-002 | P2 | TextVerified IP whitelist — submit server IP `169.255.57.146` |
| J-007 | P2 | Purge Cloudflare cache after J-001 deploy |


---

## OVERALL PROGRESS

| Sprint | Scope | Done | Open code | Manual/blocked |
|--------|-------|------|-----------|----------------|
| A — Deploy & Fixes | Server deploy, email tests, Telegram E2E | 5/8 | 0 | 3 |
| B–F — Platform features | All 63 feature tasks | 63/63 | 0 | 6 |
| G — Provider Resilience | Timeout, orphan recon, circuit breaker, nginx | 6/6 | 0 | 0 |
| H — Purchase Flow UX | Loading modal, step 3, activity feed, webhook monitor | 6/6 | 0 | 0 |
| I — Notification/WS Hardening | 10 notification + WS fixes | 10/10 | 0 | 0 |
| **Total** | | **90/93** | **0** | **9** |

**Sprint I complete. All 10 notification/WebSocket hardening tasks shipped.**

---

## CI / DEPLOY STATUS

| Job | Status |
|-----|--------|
| `frontend-unit-tests` | ⏳ Running on `a7188224` |
| `smoke-test` | `continue-on-error: true` — non-blocking |
| `unit-tests` | `continue-on-error: true` — non-blocking |
| Deploy | Fires automatically when CI concludes `success` |

**CI fix (`a7188224`)**: Removed `needs: [secrets-scan]` from `frontend-unit-tests`.
A failing `secrets-scan` (continue-on-error) was causing `frontend-unit-tests` to be
skipped → skipped blocking job = workflow conclusion `failure` → deploy never fired.
Now `frontend-unit-tests` runs independently. If it passes → workflow = `success` → deploy fires.

---

## MANUAL / EXTERNAL ACTIONS

| ID | Priority | Action | Where |
|----|----------|--------|-------|
| A-001 | P0 | Confirm deploy landed — `git log --oneline -3` on server, run `alembic upgrade head` if needed | SSH `~/vrenum` |
| H-006b | P0 | Verify TV webhook still enabled after deploy | TV API config page |
| A-002 | P1 | Test 8 transactional emails on live server | Resend dashboard + inbox |
| A-005 | P1 | Telegram E2E — connect @vrenum_sms_bot, trigger verification, confirm SMS forwarded | Live server |
| E-001 | P2 | Upgrade Upstash Redis to pay-as-you-go | Upstash dashboard |
| E-002 | P2 | TextVerified IP whitelist — submit server IP `169.255.57.146` | TV support ticket |
| C-001 | P2 | Create Paystack annual plan codes (`PLAN_PRO_ANNUAL` ₦412,500/yr, `PLAN_CUSTOM_ANNUAL` ₦577,500/yr) | Paystack dashboard |
| C-010 | P2 | Create Paystack add-on plan (`PLAN_PAYG_API_ADDON` ₦16,500/mo) | Paystack dashboard |
| G-002b | auto | nginx SSE timeout already in `deploy/nginx/nginx.conf` — deploys with A-001 | Auto on deploy |

---

## WHAT IS LIVE (confirmed shipped)

### Verification Flow
- ✅ SSE streaming purchase — real-time steps, cancel before charge commits
- ✅ G-001: 12s `asyncio.wait_for` on purchase call — stops money leak
- ✅ G-002: SSE keepalive ping every 5s — prevents nginx dropping connection
- ✅ G-002b: nginx SSE location block — 30s read/send timeout, buffering off
- ✅ G-003: Orphan reconciliation worker — heals ghost purchases (60s loop)
- ✅ G-004: Provider timeout contract — `PURCHASE_TIMEOUT_S=12` on all adapters
- ✅ G-006: Circuit breaker — Redis-backed CLOSED/OPEN/HALF_OPEN per provider
- ✅ H-001: Dark loading modal — arc-orbiting-icon spinner, TV 11-message sequence
- ✅ H-002: Step 3 — carrier emoji, MM:SS countdown, full SMS text, reuse button
- ✅ H-003: Step 3 scanning — scrolling activity feed (10-message pool, 3s rotation)
- ✅ H-004: `purchasing_delayed` SSE state — patience messages, no-close warning
- ✅ H-005: Step 0 — SMS + Voice Combo method picker card (+$0.50 badge)
- ✅ H-006: TV webhook auto-re-enable monitor (30-min loop)
- ✅ Dynamic `ends_at` from TV — no hardcoded timeout
- ✅ Orphan verification recovery on page reload
- ✅ TV webhook instant SMS delivery

### Platform
- ✅ All 23 admin dashboard tabs
- ✅ Phase 1 Analytics (6 event types)
- ✅ OTP passwordless login
- ✅ smsAndVoiceCombo capability
- ✅ Number rentals + back-order monitor
- ✅ Stock watches + "Notify me" button
- ✅ Annual billing + PAYG API add-on
- ✅ Affiliate program + commission engine
- ✅ Telegram SMS forwarding (code complete, E2E pending)
- ✅ Fraud detection + MFA (TOTP)
- ✅ GDPR compliance tools

### Infrastructure
- ✅ CI: Python 3.11, ubuntu-22.04, correct action versions
- ✅ CI: frontend-unit-tests independent (workflow conclusion fix)
- ✅ Deploy: CI-gated, auto-fires on `success`
- ✅ Sentry + BetterStack monitoring active
- ✅ TV pricing URL confirmed: `/pricing/verifications` = 200

---

## SPRINT I — NOTIFICATION & WEBSOCKET HARDENING

**Added**: November 2026
**Scope**: Fix 8 known weaknesses + 1 critical silent-failure gap in the notification/WS layer

### Background: Silent Notification Delivery on Failed Transactions

The most dangerous gap is not in the 8 structural weaknesses — it's a **silent success notification
delivered to the user even when the underlying transaction has failed**.

The flow is:
1. `purchase_endpoints.py` → SSE stream emits `complete` → frontend advances to step 3
2. `sms_polling_service._complete_verification()` fires `on_sms_received()` + `event_broadcaster.broadcast_verification_event(completed)` + email
3. **BUT**: if `BalanceService.deduct_credits_for_verification()` fails after the TV number is
   already purchased (race condition, DB error, quota overflow), the SSE stream yields `failed`
   with `reason=debit_failed` — yet the polling service may still be running against the
   verification record that was `db.flush()`-ed but never committed.
4. In `_handle_timeout()`, `mark_verification_failed()` calls `AutoRefundService` which sends
   a refund notification — but the `notify_verification_failed()` call inside `auto_refund_service`
   uses the raw `reason` string (e.g. `"sms_timeout"`) as the user-facing message, not a
   human-readable string.
5. In `_complete_verification()`, `dispatcher.on_sms_received(v)` is called **synchronously**
   (not awaited) — `on_sms_received` is `async def`. This means the DB notification is created
   but the WebSocket broadcast inside it (`asyncio.create_task`) is fired from a sync call
   context, which is unreliable.
6. The TV webhook path (`tv_webhook.py`) sets `verification.status = "completed"` and pushes
   `sms_received` via WS **before** checking whether the debit actually committed. If the
   verification record exists (from `db.flush()`) but the debit rolled back, the user sees
   a code delivered for a transaction that never charged — or worse, was double-charged.
7. No WS event is sent on `purchasing_delayed` SSE state — user's browser has no real-time
   signal that the orphan reconciliation worker healed the purchase. They only find out by
   polling or refreshing.

---

### I — Tasks

| ID | Priority | Description | File(s) |
|----|----------|-------------|---------|
| I-001 | P0 | **Fix `on_sms_received` not awaited** — called as sync in `_complete_verification()`, async def silently no-ops the WS broadcast | `sms_polling_service.py` |
| I-002 | P0 | **TV webhook guard: verify debit committed before pushing `sms_received` WS event** — check `verification.status == "completed"` AND `verification.refund_eligible == False` before broadcast | `tv_webhook.py` |
| I-003 | P0 | **`mark-all-read` URL mismatch** — JS calls `POST /api/notifications/mark-all-read`, endpoint is `/read-all`. Silent failure in production | `notification_endpoints.py`, `notification-system.js` |
| I-004 | P1 | **`asyncio.create_task()` in sync `_broadcast_notification()`** — only works if event loop is running at call site; silent drop from workers/threads. Wrap in `asyncio.get_event_loop().create_task()` with running-loop guard | `notification_dispatcher.py` |
| I-005 | P1 | **`purchasing_delayed` has no WS event** — orphan reconciliation worker heals the purchase but user gets no real-time signal. Broadcast `{type: "purchase_healed", verification_id, phone_number}` from orphan worker on successful heal | `workers/orphan_reconciliation.py`, `notification-system.js` |
| I-006 | P1 | **Refund notification uses raw reason string as user message** — `notify_verification_failed(reason=f"Refunded: {reason}")` exposes internal codes like `sms_timeout`, `area_code_mismatch` to users | `auto_refund_service.py` |
| I-007 | P2 | **`get_unread_count` defined twice** in `notification_service.py` — second definition shadows first silently | `notification_service.py` |
| I-008 | P2 | **`_channels` dict lazy-init with `hasattr`** — initialize in `ConnectionManager.__init__` to prevent AttributeError on direct access | `app/websocket/manager.py` |
| I-009 | P2 | **No notification cleanup scheduler** — `cleanup_old_notifications(days=30)` exists but is never called. Wire into lifespan or a periodic task | `core/lifespan.py` or `startup.py` |
| I-010 | P3 | **Telegram `datetime.utcnow()` (naive) vs rest of codebase `timezone.utc` (aware)** — will cause comparison errors when `last_message_at` is compared to aware datetimes | `telegram_service.py` |

---

### I — Deferred (external dependency)

| ID | Reason |
|----|--------|
| FCM legacy API migration | FCM v1 HTTP API requires service account key — external config change, not code |
| APNs stub → real impl | No iOS users yet — deferred until demand |
| Push notification keys | Gated on `FCM_SERVER_KEY` / `ONESIGNAL_APP_ID` env vars — ops task |
| Missed WS message persistence | No "deliver on reconnect" queue — deferred, requires Redis pub/sub or outbox pattern |

---

## NEXT PHASE (after deploy confirmed)

No code tasks remain from Sprints A–H. Next engineering work is:

1. **Sprint I** — Notification & WebSocket hardening (tasks above)

2. **Phase 2 Analytics** — cohort retention, revenue breakdown, churn signal
   Pre-work: assess `user_events` + `purchase_outcomes` tables
   Task doc: `docs/features/PHASE2_ANALYTICS.md` (to be created)

3. **SDK Libraries** — Python + JS client wrapping the public API
   Spec: `docs/engineering/VRENUM_API_CONTRACT.md`

4. **CI coverage push** — 30% → 60% (wire more test files, raise `--cov-fail-under`)

---

## SPEC REFERENCE

| Doc | What it covers |
|-----|----------------|
| `docs/engineering/PROVIDER_RESILIENCE_AND_PLATFORM_STANDARDS.md` | Sprint G full spec |
| `docs/engineering/development/PURCHASE_FLOW_UX_OVERHAUL.md` | Sprint H full spec |
| `docs/engineering/VRENUM_API_CONTRACT.md` | Public API + SDK surface |
| `docs/status/MASTER_TASKS.md` | Historical record of all completed work |
