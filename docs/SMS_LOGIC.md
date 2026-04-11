# SMS Logic — Full Assessment

**Date**: April 6, 2026 | **Last Updated**: April 7, 2026  
**Scope**: Every deviation from TV's standard flow, all in-between logic gaps, voice verification, and newly discovered issues.

---

## PART 1 — Deviations From TV Standard Flow

---

### ✅ Deviation 1 — Wrong SMS Retrieval Method
**FIXED** — `poll_sms_standard()` now uses `sms.incoming(data=tv_object)` correctly.

**Was:** `sms.list(string_id)` — queried all SMS across entire account history  
**Now:** `sms.incoming(data=VerificationExpanded, since=created_at)` — only fresh SMS for this activation

**File:** `app/services/textverified_service.py` → `poll_sms_standard()`

---

### ✅ Deviation 2 — `parsed_code` Was Being Ignored
**FIXED** — `parsed_code` from TV used first. Regex is last resort only.

**Was:** Broken regex `\b(\d{4,8})\b` missed hyphenated codes like `806-185`  
**Now:** `sms.parsed_code` → hyphen regex → plain digit regex (in that order)

**Files:** `textverified_service.py` → `poll_sms_standard()`, `get_sms()`, and `sms_polling_service.py` → `_poll_legacy()`

---

### ✅ Deviation 3 — `VerificationExpanded` Object Discarded After Creation
**FIXED** — `ends_at` and `tv_object` now returned from `create_verification()`.

**Was:** Only `id` and `number` extracted, everything else discarded  
**Now:** `ends_at` stored, `tv_object` passed to `poll_sms_standard()`

**File:** `textverified_service.py` → `create_verification()` returns full dict including `tv_object`

---

### ⚠️ Deviation 4 — TV Verification State Never Read
**PARTIAL** — `get_verification_details()` added to read real TV state.  
Platform still maintains its own `status` string. Full sync with TV state enum not yet implemented.

**What works:**
- `get_verification_details()` fetches real TV state including `state`, `ends_at`, `can_cancel`, `can_report`
- `status_polling.py` reads TV status and updates local record
- Stale code guard: `status_polling.py` validates freshness via `check_sms(created_after=...)` before accepting incoming codes

**What's missing:**
- Platform uses string statuses (`pending`, `completed`, `timeout`, `cancelled`) instead of TV's `ReservationState` enum
- No mapping from `ReservationState.VERIFICATION_PENDING` / `VERIFICATION_COMPLETED` / `VERIFICATION_TIMED_OUT` / `VERIFICATION_REFUNDED` to platform statuses
- If TV marks a verification as refunded or timed out, the platform won't know unless it polls

**Priority:** Low — current approach works, TV state is read when needed, full enum sync is a nice-to-have.

```python
# TV state enum (not yet mapped)
ReservationState.VERIFICATION_PENDING
ReservationState.VERIFICATION_COMPLETED
ReservationState.VERIFICATION_TIMED_OUT
ReservationState.VERIFICATION_REFUNDED
```

---

### ✅ Deviation 5 — `verifications.report()` Never Called
**FIXED** — `report_verification()` now called on timeout.

**Was:** Platform ate every failed verification cost  
**Now:** `report_verification()` called on timeout → TV refunds automatically. Platform `AutoRefundService` is fallback only if TV report fails.

**File:** `sms_polling_service.py` → `_handle_timeout()`

---

### ✅ Deviation 6 — `ends_at` Never Used
**FIXED** — `ends_at` from TV now used to calculate real polling timeout.

**Was:** Hardcoded 10-minute timer regardless of TV's actual expiry  
**Now:** `timeout = min(ends_at_delta, config_max)` — uses TV's real expiry

**File:** `sms_polling_service.py` → `_poll_verification()` lines 72-78

---

### ✅ Deviation 7 — Voice Route Called Non-Existent Endpoint
**FIXED** — Route corrected in `voice_verify_modern.html`.

**Was:** `fetch('/api/verify/create')` → 404 always  
**Now:** `fetch('/api/verification/request')` → correct endpoint

---

### ✅ Deviation 8 — `submitVoiceCode()` Not Defined
**FIXED** — Manual code input section removed entirely.

**Was:** Static HTML had a button calling undefined `submitVoiceCode()` → JS error  
**Now:** Replaced with empty `#code-input-section` div. Polling JS auto-populates it with code display + copy button on success.

**File:** `templates/voice_verify_modern.html`

---

### ⚠️ Deviation 9 — `pricing-balance` Missing in Voice Template
**FIXED** — Element added to Step 2 pricing card.

**Was:** `getElementById('pricing-balance')` → null error on every load  
**Now:** Element present at line 107, balance loads via `loadBalance()`

**Note:** `loadBalance()` calls `/api/billing/balance` — if this endpoint is slow or fails, the balance shows `$0.00` with no error feedback to the user.

---

### ✅ Deviation 10 — Voice Polling Used Wrong Endpoint
**FIXED** — Polling endpoint corrected.

**Was:** `fetch('/api/verify/${id}/status')` → 404  
**Now:** `fetch('/api/verification/status/${verificationId}')` → correct

---

### ✅ Deviation 11 — Voice Area Codes Hardcoded
**FIXED** — Hardcoded options removed. Dynamic load with clean fallback.

**Was:** 4 hardcoded `<option>` elements (212, 310, 415, 479) as silent fallback  
**Now:** Select starts with "Loading area codes...", `loadAreaCodes()` populates dynamically. On API failure, falls back to single "Any Area Code" option.

**File:** `templates/voice_verify_modern.html`

---

### ✅ Deviation 12 — Voice Polling `setInterval` Leak
**FIXED** — Replaced with `setTimeout` chain.

**Was:** `setInterval` kept running after navigation → background API calls  
**Now:** `setTimeout` chain, `clearTimeout` on success/cancel/reset

**File:** `templates/voice_verify_modern.html` → `startWaiting()` function

---

## PART 2 — Newly Discovered Issues

---

### ✅ Issue 13 — Frontend Outcome Endpoint Mismatch (SMS Template)
**FIXED** — Backend aligned to match frontend.

**Was:** Frontend sent `POST /api/verification/outcome/{id}`, backend expected `PATCH /api/verification/{id}/outcome` → 404/405  
**Now:** Backend changed to `POST /api/verification/outcome/{id}` — matches both SMS and voice frontend calls.

**File:** `app/api/verification/outcome_endpoint.py`

---

### ✅ Issue 14 — Voice Tier Gate Missing at API Level
**FIXED** — Server-side tier enforcement added.

**Was:** Any user could POST `capability: 'voice'` regardless of tier  
**Now:** `purchase_endpoints.py` checks `capability == 'voice'` requires PAYG+ via `tier_manager.check_tier_hierarchy()`. Returns 402 for Freemium users.

**File:** `app/api/verification/purchase_endpoints.py`

---

### ✅ Issue 15 — Fake `_TVVerif` Object in Polling Service
**FIXED** — Added missing attributes to `_TVVerif`.

**Was:** Only had `number`, `created_at`, `id` — fragile if TV library inspects more  
**Now:** `_TVVerif` also carries `ends_at` and `service_name` from `tv_details` and `verification` record.

**File:** `app/services/sms_polling_service.py`

---

### ✅ Issue 16 — Voice Template Has No Timeout Outcome Call
**FIXED** — Voice template now calls outcome endpoint on timeout.

**Was:** Voice timeout just called `showError()` — no outcome recorded  
**Now:** On 300s timeout, voice template POSTs `{outcome: 'timeout'}` to `/api/verification/outcome/{id}` before showing error, matching the SMS template pattern.

**File:** `templates/voice_verify_modern.html`

---

## PART 3 — The Correct Standard Flow

### SMS & Voice — Standard Implementation

```python
# 1. Create — get VerificationExpanded back
tv_verification = client.verifications.create(
    service_name="whatsapp",
    capability=ReservationCapability.SMS,  # or VOICE
    area_code_select_option=["213", "310"],
)

# 2. Store key fields including ends_at
activation_id = tv_verification.id
phone_number  = tv_verification.number
expires_at    = tv_verification.ends_at    # real expiry from TV
cost          = tv_verification.total_cost

# 3. Poll using standard method — pass the OBJECT not a string
timeout = (tv_verification.ends_at - datetime.now(timezone.utc)).total_seconds()

for sms in client.sms.incoming(
    data=tv_verification,               # VerificationExpanded object
    since=tv_verification.created_at,   # built-in stale filter
    timeout=timeout,                    # real expiry from TV
    polling_interval=3.0
):
    code = sms.parsed_code              # TV already parsed it
    break

# 4. If no SMS — report to recover cost from TV
if not code:
    client.verifications.report(tv_verification.id)
    # TV refunds to account automatically
```

---

## PART 4 — Voice vs SMS

| | SMS | Voice |
|--|-----|-------|
| TV capability | `SMS` | `VOICE` |
| How code arrives | Text message | Automated phone call |
| `parsed_code` | ✅ Works | ✅ Works identically |
| Polling method | `sms.incoming()` | `sms.incoming()` — same |
| Typical wait | 10–60 seconds | 2–5 minutes |
| Success rate | ~95% | ~92% |
| Cost | $2.50 base | $2.50 + $0.30 surcharge |
| Tier requirement | All tiers | PAYG+ (API enforced) |
| Purchase endpoint | `/api/verification/request` | `/api/verification/request` (same) |
| Status endpoint | `/api/verification/status/{id}` | `/api/verification/status/{id}` (same) |
| Timeout outcome | ✅ POST to outcome endpoint | ✅ POST to outcome endpoint |

---

## PART 5 — Status Summary

### ✅ Fully Fixed (18 items)

| # | Issue | Fix | File |
|---|-------|-----|------|
| 1 | Wrong SMS method (`sms.list` string) | `poll_sms_standard()` with TV object | `textverified_service.py` |
| 2 | `parsed_code` ignored | Used first, regex is fallback | `textverified_service.py`, `sms_polling_service.py` |
| 3 | `VerificationExpanded` discarded | `ends_at` + `tv_object` now returned | `textverified_service.py` |
| 5 | `report()` never called | `report_verification()` on timeout | `sms_polling_service.py` |
| 6 | `ends_at` unused | Real timeout from TV expiry | `sms_polling_service.py` |
| 7 | Voice route 404 | Fixed to `/api/verification/request` | `voice_verify_modern.html` |
| 8 | `submitVoiceCode()` undefined | Manual input removed, auto-display only | `voice_verify_modern.html` |
| 10 | Voice polling wrong endpoint | Fixed to `/api/verification/status/{id}` | `voice_verify_modern.html` |
| 11 | Voice area codes hardcoded | Hardcoded options removed, dynamic load + clean fallback | `voice_verify_modern.html` |
| 12 | `setInterval` leak | `setTimeout` chain | `voice_verify_modern.html` |
| 13 | Outcome endpoint mismatch | Backend changed to `POST /verification/outcome/{id}` | `outcome_endpoint.py` |
| 14 | Voice tier gate missing | `check_tier_hierarchy(tier, 'payg')` added | `purchase_endpoints.py` |
| 15 | Fake `_TVVerif` fragile | Added `ends_at`, `service_name` attributes | `sms_polling_service.py` |
| 16 | Voice no timeout outcome | Added outcome POST on 300s timeout | `voice_verify_modern.html` |
| — | Stale SMS from recycled numbers | `created_after` filter in `get_sms()` and `check_sms()` | `textverified_service.py` |
| — | Empty code marked completed | Continues polling instead | `sms_polling_service.py` |
| — | WebSocket double accept crash | `register()` method (no second `accept()`) | `websocket/manager.py`, `websocket_endpoints.py` |
| — | Second code path unfiltered | `status_polling.py` validates freshness | `status_polling.py` |

### ⚠️ Partially Fixed (1 item)

| # | Issue | Status | Priority |
|---|-------|--------|----------|
| 4 | TV state enum not synced | `get_verification_details()` works, but platform uses own status strings. No enum mapping. | Low |

---

## PART 6 — Action Items

### ✅ Completed
- [x] **Issue 14**: Voice tier gate in `purchase_endpoints.py` — freemium blocked, PAYG+ allowed
- [x] **Issue 13**: Outcome endpoint aligned — backend now `POST /verification/outcome/{id}`
- [x] **Issue 8**: `submitVoiceCode()` button removed from `voice_verify_modern.html`
- [x] **Issue 15**: `_TVVerif` now carries `ends_at` and `service_name`
- [x] **Issue 11**: Hardcoded area code options removed from voice template
- [x] **Issue 16**: Voice template now calls outcome endpoint on timeout

### Remaining
- [ ] **Issue 4**: Map TV `ReservationState` enum to platform status strings (Low priority)
