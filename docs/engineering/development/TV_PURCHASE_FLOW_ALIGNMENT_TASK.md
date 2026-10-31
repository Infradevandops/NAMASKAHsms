# Task: TV Purchase Flow Alignment & Verification Window Fix

**Status:** Planned
**Priority:** Critical
**Area:** Verification flow, purchase endpoints, frontend UX
**Created:** October 31, 2026

---

## Background — What TV's Real Flow Looks Like

From direct observation of app.textverified.com (WhatsApp purchase, Oct 31 2026):

### TV Pre-Purchase Sequence (before charging)
TV runs a multi-step async check BEFORE assigning a number or charging:
1. "Checking current line availability for selected service" → "Initiating..."
2. "Checking current line availability" → "Connecting to cellular network"
3. "Checking current line availability" → "Connected!"
4. "Searching for unused numbers" → "Verifying immediate number pool availability"
5. "Searching for unused numbers" → "Filtering out recently recycled numbers"
6. "Searching for unused numbers" → "Scanning number blocks for unused SIM"
7. "Checking major carrier networks" → "Measuring latency and connection strength"
8. "Checking major carrier networks" → "Pinging AT&T • T-Mobile • Verizon"

**High demand path (WhatsApp had only 39 in stock):**
- "This service is experiencing high demand" → "Estimating current queue length"
- "Reserving your place in queue" → "We appreciate your patience"
- Eventually assigns number OR fails gracefully (no charge)

### TV Post-Purchase State
- Number assigned with **~60 minute window** (Time Left: 58:21 observed)
- "Waiting to receive an SMS from WhatsApp. Please note that services may take multiple attempts."
- "Please request only one code. Multiple requests may result in issues."
- After SMS received: "Successfully Received Your SMS — Would you like to do another?"
- **Reuse offer**: "Use again for 0.75 credits (0:47)" — cheaper reuse within window
- Active verification count shown: "You have 1 of 4 pending verifications"

### TV Support Bot Confirmation
TV support confirmed: "Our numbers change regularly and sometimes our most popular services end up selling out. Our numbers are first come first serve and we are working on expanding capacity."

---

## Critical Bugs Found

### Bug 1 — WRONG VERIFICATION WINDOW (Critical)
**File:** `static/js/verification-flow.js` line 951
**Current:** `const totalDurationMs = 120000; // 2 minutes standard`
**Reality:** TV now gives ~60 minutes (3600 seconds)
**Impact:** Frontend shows wrong countdown, auto-times-out users after 2 min when they have 58 min left, progress bar fills in 2 min

**Fix:** Use `ends_at` from the status poll response to calculate actual duration dynamically instead of hardcoding 120000. The `data.ends_at` is already returned by the status endpoint — compute `totalDurationMs = endsAt - createdAt` from the first poll response.

### Bug 2 — NO QUEUE/LOADING STATE DURING PURCHASE (High)
**Current:** User clicks "Get Number" → spinner → either number or error. No intermediate states.
**TV does:** Shows animated loading modal with status messages for 5-30 seconds before assigning number.
**Impact:** Users think it's broken when it's just searching. Silent failures look identical to slow searches.

**Fix:** Add a "Searching for your number..." loading state in `step-2-card` between clicking "Get Number" and receiving the response. Show animated status messages cycling through search states. Keep "Cancel (you will not be charged)" visible throughout.

### Bug 3 — SILENT PURCHASE / DEBIT WITH NO UI (High)
**Current:** `createVerification()` in `verification-flow.js` calls the API, but if the page is navigated away or the modal closes during the API call, the purchase completes silently. User gets debited, no number shown.
**Impact:** Users see debit in notifications but no active verification to use.

**Fix:** 
- Store `verificationId` in `localStorage` immediately when purchase starts
- On page load, check for orphaned active verifications and restore the UI
- Add `POST /api/verification/request` response to include `ends_at` so frontend can show the window

### Bug 4 — ends_at NOT IN PURCHASE RESPONSE (Medium)
**File:** `app/api/verification/purchase_endpoints.py` line ~661
**Current:** Response does not include `ends_at`
**Impact:** Frontend can't show accurate time remaining until first status poll

**Fix:** Add `ends_at` and `created_at` to the purchase response from `purchase_result.expires_at`

### Bug 5 — REUSE FEATURE NOT IMPLEMENTED (Low/Future)
TV offers reusing a number at a discount within the verification window.
SDK has `ReuseAction` with `can_reuse` field on `VerificationExpanded`.
Not implementing now but note for future.

---

## Implementation Plan

### Phase 1 — Fix Verification Window (30 min, Critical)

**`static/js/verification-flow.js`**
- Remove hardcoded `totalDurationMs = 120000`
- On first successful status poll, compute: `totalDurationMs = new Date(data.ends_at) - new Date(data.created_at)`
- Store in `VerificationFlow.totalDurationMs`
- Update all progress bar calculations to use dynamic value
- Update "~Xs remaining" display to use actual `ends_at`

**`app/api/verification/purchase_endpoints.py`**
- Add `ends_at` and `created_at` to purchase response (from `purchase_result.expires_at`)

### Phase 2 — Loading State During Purchase (45 min, High)

**`templates/verify_modern.html`**
- Add loading overlay card between step 2 and step 3
- Shows animated spinner + cycling status messages

**`static/js/verification-flow.js`**
- Show loading state immediately on "Get Number" click
- Cycle through messages: "Checking availability..." → "Searching for unused numbers..." → "Filtering recycled numbers..." → "Connecting to carrier..."
- On success: transition to step 3 (number received)
- On failure: show error with specific message

### Phase 3 — Orphaned Verification Recovery (30 min, High)

**`static/js/verification-flow.js`**
- On DOMContentLoaded, check `localStorage.getItem('active_verification_id')`
- If found, call `GET /api/verification/status/{id}`
- If status is `pending`, restore step 3 UI and resume polling
- If status is `completed/failed/timeout`, clear localStorage

**`app/api/verification/purchase_endpoints.py`**
- Store `verification_id` in response so frontend can persist it

### Phase 4 — TV Webhook for Instant SMS (Future session)

TV sends `SmsWebhookEvent` to a registered webhook URL.
Register `POST /api/verification/webhook/tv-sms` with TV.
On webhook receipt: update verification status in DB, push via WebSocket to user.
Eliminates polling entirely.

---

## Files to Modify

| File | Change |
|------|--------|
| `static/js/verification-flow.js` | Dynamic window duration, loading state, orphan recovery |
| `app/api/verification/purchase_endpoints.py` | Add `ends_at`/`created_at` to response |
| `templates/verify_modern.html` | Loading state card |

---

## Acceptance Criteria

- [ ] Verification countdown shows correct time (up to 60 min) based on actual `ends_at`
- [ ] Progress bar fills over the actual window duration, not 2 minutes
- [ ] "Get Number" shows loading state with status messages for duration of API call
- [ ] If user navigates away during active verification, returning to `/verify` restores the active session
- [ ] Purchase response includes `ends_at` and `created_at`
- [ ] No auto-timeout before `ends_at` is reached

---

## Notes

- TV's 60-min window is confirmed from screenshots (Time Left: 58:21 and 57:49 and 54:15)
- TV's queue system is server-side — our `verifications.create()` SDK call blocks until a number is assigned or fails. The queue wait happens inside that blocking call. We don't need to implement queue UI separately — just show a loading state for the duration of the `create()` call.
- The "high demand" state in TV's UI corresponds to our `create_verification()` taking longer than usual. Currently we have a 2-attempt retry loop which is correct. The loading state just needs to be visible during this wait.
- WhatsApp QTY=39 confirmed real-time quantity works. Our raw services fetch should capture this.
