# TV API Flow vs Platform Flow — Gap Assessment

**Created**: October 25, 2026
**Version**: 4.9.0
**Author**: Amazon Q Analysis
**Priority**: 🔴 P0 gaps identified — voice capability check is broken

---

## 1. TV API Ground Truth

What TextVerified's API actually does, in order:

```
1. POST /api/pub/v2/verifications/pricing
        → price=null means out of stock — stop here
        → price>0 means inventory exists — proceed

2. POST /api/pub/v2/verifications
        → returns VerificationExpanded:
            - id           (activation_id)
            - number       (phone number assigned)
            - ends_at      (real expiry — typically 10–60 min)
            - total_cost
            - cancel.can_cancel
            - report.can_report

3. Poll for result (two mechanisms):
        a. sms.incoming(data=tv_obj, since=created_at, timeout=N)
              → blocking iterator, yields on SMS/voice arrival
              → parsedCode is TV's extracted code
        b. Webhook POST → instant push on SMS arrival (faster)

4. Finalise:
        → SMS received          → done, no action needed
        → Timeout               → verifications.report(id) → TV refunds to account
        → User cancel           → verifications.cancel(id) → refund if can_cancel=true
```

---

## 2. Platform Flow — Current State

### SSE Path (`POST /verification/request/stream`)

| Step | What fires | Real work? | Matches TV? |
|------|-----------|------------|-------------|
| `pricing_check` | `check_service_available()` → `POST /verifications/pricing` | ✅ Yes | ✅ Yes |
| `balance_check` | DB query for user credits | ✅ Yes | N/A |
| `purchasing` | `provider_router.purchase_with_failover()` → `verifications.create()` | ✅ Yes (5–30s) | ✅ Yes |
| `validating` | Nothing — fires immediately | ❌ No real work | ❌ No |
| `recording` | DB write + `BalanceService.deduct_credits_for_verification()` | ✅ Yes | N/A |
| `complete` | Returns `verification_id`, `phone_number`, `ends_at` | ✅ Yes | ✅ Yes |

### Legacy Path (`POST /verification/request`)

| Step | What fires | Gap? |
|------|-----------|------|
| Idempotency check | Redis + DB | ✅ None |
| Fraud score | Non-blocking, logs only | ✅ None |
| Tier validation | Area code / voice gating | ✅ None |
| `check_service_available()` | Live TV pricing call | ✅ Fixed (P0 applied) |
| `_get_provider_price()` | Reads from 24h cache | ✅ Backed by live check above |
| `PricingCalculator` | Calculate cost | ✅ None |
| Balance check | `BalanceService.check_sufficient_balance()` | ✅ None |
| `purchase_with_failover()` | Blocks 5–30s | ✅ None |
| DB write + debit | | ✅ None |
| Polling start | `sms_polling_service.start_polling()` | ✅ None |

---

## 3. Gaps Found

### Gap 1 — `check_service_available()` hardcodes `capability: "sms"` for voice purchases
**Severity**: 🔴 P0
**File**: `app/services/textverified_service.py` → `check_service_available()`
**File**: `app/api/verification/purchase_endpoints.py` (call site)

`check_service_available()` always sends `"capability": "sms"` in the TV pricing request body, even when the user requests a voice verification. TV prices voice separately — a service may be available for SMS but not voice, or at a different price. The availability check is therefore inaccurate for all voice purchases.

Same issue exists in `_fetch_prices_inline()` — the 24h services cache is always populated with SMS pricing. Voice cost calculations fall back to `PricingCalculator.calculate_voice_cost()` applying a multiplier to the SMS price rather than TV's actual voice price.

**Fix**:
```python
# textverified_service.py
async def check_service_available(
    self, service_name: str, capability: str = "sms"
) -> dict:
    ...
    json={
        "serviceName": service_name,
        "areaCode": False,
        "carrier": False,
        "numberType": "mobile",
        "capability": capability,   # was hardcoded "sms"
    },
```

Call site in `purchase_endpoints.py` (both legacy and SSE paths):
```python
avail = await _tv_service.check_service_available(
    request.service, capability=request.capability
)
```

---

### Gap 2 — `validating` SSE step does no real work
**Severity**: 🟡 P2
**File**: `app/api/verification/purchase_endpoints.py` → `request_verification_stream()`

After `purchasing` completes, `validating` fires immediately with zero real work. It is a UX label only. TV's `VerificationExpanded` object already has `can_cancel` and `can_report` flags. The validating step could call `get_verification_details()` to confirm the number is live on TV's side before committing the DB write, or it should be removed entirely.

**Options**:
- Remove `validating` and go straight `purchasing` → `recording`
- Use it to call `get_verification_details()` and surface `can_cancel` to the frontend

---

### Gap 3 — `poll_sms_standard()` does not handle TV voice audio responses
**Severity**: 🔴 P0 (voice path only)
**File**: `app/services/textverified_service.py` → `poll_sms_standard()`
**File**: `app/services/sms_polling_service.py` → `_poll_textverified()`

Voice verifications go through `poll_sms_standard()` which uses `sms.incoming()`. The method only parses `sms_content` and `parsed_code`. If TV returns a voice result with an `audio_url` but no parseable code, the current code path is:

```python
# sms_polling_service.py — _poll_textverified()
if verification.capability == "voice" and not code and transcription:
    code = "VOICE_RECV"
    text = transcription
```

But `poll_sms_standard()` itself does not extract `audio_url` or `transcription` from TV's voice response object — it only returns `{"success": True, "code": parsed, "sms": sms.sms_content}`. If TV returns audio-only with no transcription, `code` is empty, `transcription` is None, and the verification falls through to `_handle_timeout()` — triggering an unnecessary refund cycle.

**Fix**: The `Sms` SDK dataclass has NO `audio_url` or `transcription` fields — `getattr` will
always return `None`. Voice delivers its result as `sms_content` text. The fix is to treat
`sms_content` as the transcription for voice verifications when `parsed_code` is empty:
```python
# In poll_sms_standard() _blocking_poll, after extracting parsed:
if not parsed and verification_capability == "voice":
    # sms_content IS the transcription for voice
    return {
        "success": True,
        "code": sms.sms_content or "VOICE_RECV",
        "sms": sms.sms_content or "",
        "received_at": msg_time.isoformat(),
    }
```

---

### Gap 4 — `ends_at` from TV not persisted to DB in SSE path
**Severity**: 🟡 P1
**File**: `app/api/verification/purchase_endpoints.py` → `request_verification_stream()` recording step

In the SSE stream's `recording` step, the `Verification` object is created without an `ends_at` field. `purchase_result.expires_at` is returned in the `complete` SSE event but not written to DB. The polling service then calculates timeout from `settings.sms_polling_max_minutes` as a fallback. TV's actual window (10–60 min per service) may differ from the platform's configured max, causing either premature timeouts or over-long polling.

**Fix** (SSE recording step):
```python
ends_at_dt = None
if purchase_result.expires_at:
    ends_at_dt = datetime.fromisoformat(purchase_result.expires_at)

verification = Verification(
    ...
    ends_at=ends_at_dt,   # add this
)
```

---

### Gap 5 — `report_verification()` called without checking `can_report`
**Severity**: 🟡 P1
**File**: `app/services/sms_polling_service.py` → `_handle_timeout()`

TV's `VerificationExpanded` object has a `can_report` flag that controls whether reporting is valid for a given verification. The platform calls `report_verification()` unconditionally on timeout without checking this flag. Failed report calls are silently swallowed (`logger.warning`), but the refund is not triggered — meaning the platform absorbs the cost without recovering it from TV.

**Fix**:
```python
if provider == "textverified":
    details = await self.textverified.get_verification_details(
        verification.activation_id
    )
    if details.get("can_report", True):  # default True if details unavailable
        provider_refunded = await self.textverified.report_verification(
            verification.activation_id
        )
    else:
        logger.warning(
            f"can_report=False for {verification.activation_id} — skipping report"
        )
```

---

### Gap 6 — Voice: `mark_sms_code_received()` stores `"VOICE_RECV"` as the code
**Severity**: 🟢 P2 (UX)
**File**: `app/services/sms_polling_service.py` → `_poll_textverified()`

When a voice verification completes, the platform stores `"VOICE_RECV"` as `sms_code` in the DB. Users querying the status endpoint or history see `"VOICE_RECV"` as their code rather than the actual transcription. The transcription is stored separately in `verification.transcription`, but the primary `sms_code` field is misleading.

**Fix**: Store the actual transcription (or first N chars) as `sms_code` for voice completions, with `"VOICE_RECV"` only as a fallback when transcription is unavailable.

---

### Gap 7 — No `transcribing` intermediate status in SSE path
**Severity**: 🟢 P2 (UX)
**File**: `app/api/verification/purchase_endpoints.py` → `request_verification_stream()`

`mark_verification_transcribing()` exists in `verification_status_service.py` but is never called from the SSE purchase path. Voice verifications that are waiting for transcription show as `pending` with no indication that audio was received and transcription is in progress. This causes users to think the verification is still waiting for a call.

---

### Gap 8 — Stale comment in `stock_monitor.py`
**Severity**: 🟢 P3 (docs)
**File**: `app/services/stock_monitor.py` → `run_stock_monitor()`

The docstring says `"15-minute refresh"` but the loop sleeps for 90 seconds. The 90s fix was applied but the comment was not updated.

**Fix**:
```python
async def run_stock_monitor() -> None:
    """Background loop — refreshes stock every 90 seconds."""
```

---

## 4. Gap Summary Table

| # | Gap | Severity | File | Status |
|---|-----|----------|------|--------|
| 1 | `check_service_available()` hardcodes `capability: "sms"` | 🔴 P0 | `textverified_service.py` | ✅ Fixed `3f805f8a` |
| 2 | `validating` SSE step does no real work | 🟡 P2 | `purchase_endpoints.py` | 📋 Open |
| 3 | Voice: `sms_content` not used as transcription | 🔴 P0 | `sms_polling_service.py` | ✅ Fixed `3f805f8a` |
| 4 | `ends_at` not persisted to DB in SSE path | 🟡 P1 | `purchase_endpoints.py` | ✅ Fixed `3f805f8a` |
| 5 | `report_verification()` called without checking `can_report` | 🟡 P1 | `sms_polling_service.py` | ✅ Fixed `3f805f8a` |
| 6 | Voice stores `"VOICE_RECV"` instead of transcription | 🟢 P2 | `sms_polling_service.py` | ✅ Fixed `3f805f8a` |
| 7 | No `transcribing` status in SSE path for voice | 🟢 P2 | `purchase_endpoints.py` | 📋 Open |
| 8 | Stale `"15-minute refresh"` comment in stock monitor | 🟢 P3 | `stock_monitor.py` | 📋 Open |
| — | `check_service_available()` added to legacy path | 🔴 P0 | `purchase_endpoints.py` | ✅ Fixed `47d69fd1` |
| — | Stock monitor loop sleep 120s → 90s | 🟡 P1 | `stock_monitor.py` | ✅ Fixed `47d69fd1` |
| — | 5 broken rental SDK calls | 🔴 P0 | `textverified_service.py` | ✅ Fixed `3f805f8a` |
| — | Voice pricing uses wrong `NumberType` | 🔴 P0 | `textverified_service.py` | ✅ Fixed `3f805f8a` |
| — | `max_price` never passed to `verifications.create()` | 🟡 P1 | `textverified_service.py` | ✅ Fixed `3f805f8a` |
| — | Dead `carrier` reads on `VerificationExpanded` | 🟡 P1 | `textverified_service.py` | ✅ Fixed `3f805f8a` |
| — | `reactivate` before `report` on timeout | 🟡 P1 | `sms_polling_service.py` | ✅ Fixed `3f805f8a` |
| — | Area code modal shows state only, not city | 🟢 P2 | `area_code_endpoints.py` | ✅ Fixed `3f805f8a` |
| — | Pricing URL `/verifications/pricing` vs `/pricing/verifications` | ⚠️ | `textverified_service.py` | ⚠️ Unverified — needs VPS test |

---

## 5. Recommended Implementation Order

| Priority | Gap | Effort |
|----------|-----|--------|
| 🔴 P0 | Gap 1 — pass `capability` to `check_service_available()` | ~10 lines, 2 files |
| 🔴 P0 | Gap 3 — return `audio_url`/`transcription` from `poll_sms_standard()` | ~5 lines |
| 🟡 P1 | Gap 4 — persist `ends_at` to DB in SSE path | ~5 lines |
| 🟡 P1 | Gap 5 — check `can_report` before calling `report_verification()` | ~10 lines |
| 🟢 P2 | Gap 6 — store transcription as `sms_code` for voice | ~5 lines |
| 🟢 P2 | Gap 7 — emit `transcribing` SSE status for voice | ~5 lines |
| 🟢 P2 | Gap 2 — remove or make `validating` step real | ~5 lines |
| 🟢 P3 | Gap 8 — fix stale comment in `stock_monitor.py` | 1 line |

---

## 6. TV API Signal Reference

| Signal | Meaning | Platform handling |
|--------|---------|-------------------|
| `price = null` from services list | Out of stock | ✅ Stock monitor marks unavailable |
| `price = null` from pricing endpoint | Out of stock | ✅ `check_service_available()` returns false |
| `price > 0` from pricing endpoint | Available right now | ✅ Used as gate in both paths |
| `quantity = 0` | Out of stock | ✅ Stock monitor marks unavailable |
| `quantity = null` | Unknown (TV didn't return it) | ⚠️ Falls back to price signal |
| `capability = "sms"` in pricing request | SMS availability check | ✅ SMS path correct |
| `capability = "voice"` in pricing request | Voice availability check | ❌ Never sent — always "sms" |
| `can_cancel = true` | Cancellation will trigger refund | ✅ Used in cancel flow |
| `can_report = true` | Reporting will trigger refund | ❌ Not checked before report call |
| `verifications.report(id)` | Failed verification → TV refunds | ✅ Called on timeout |
| `verifications.cancel(id)` | User cancel → TV refunds if can_cancel | ✅ Called on cancel |
| `audio_url` on voice SMS object | Voice audio received | ❌ Field does not exist on `Sms` dataclass — voice delivers via `sms_content` |
| `transcription` on voice SMS object | Voice transcription | ❌ Field does not exist on `Sms` dataclass — `sms_content` is the transcription |

---

## 7. Related Docs

- [TV_STOCK_VERIFICATION_FLOW_ASSESSMENT.md](./TV_STOCK_VERIFICATION_FLOW_ASSESSMENT.md) — stock accuracy + P0 fixes (some applied)
- [TV_PURCHASE_FLOW_ALIGNMENT_TASK.md](./development/TV_PURCHASE_FLOW_ALIGNMENT_TASK.md) — purchase flow alignment task
- [VOICE_VS_SMS_VERIFICATION.md](./api/VOICE_VS_SMS_VERIFICATION.md) — voice vs SMS API differences
- [TV_API_REAL_FLOW.md](./TV_API_REAL_FLOW.md) — full SDK source truth, rental breakage, corrections
