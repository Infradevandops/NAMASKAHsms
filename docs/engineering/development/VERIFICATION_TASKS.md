# Verification System — Consolidated Task File

**Created**: November 2026
**Updated**: November 2026 — post sprint execution
**Status**: Open items reduced to 2. OPEN-1 and OPEN-4 closed. OPEN-3 partially done.

> Open items are also tracked in `docs/status/MASTER_TASKS.md` (B-002, B-004, B-006, B-008).
> This file is the technical reference for the verification system.

---

## WHAT IS LIVE (all deployed, confirmed on server)

### SDK Fixes — `3f805f8a`
| Fix | File |
|-----|------|
| `reservations.get()` → `reservations.details()` | `textverified_service.py` |
| `reservations.messages()` → `sms.list(data=rental)` | `textverified_service.py` |
| `reservations.extend()` → `extend_nonrenewable(RentalDuration)` | `textverified_service.py` |
| `verifications.get()` → `verifications.details()` | `textverified_service.py` |
| `create_reservation()` duration enum + sale response fixed | `textverified_service.py` |
| `check_service_available()` uses SDK `verifications.pricing()` | `textverified_service.py` |
| Voice pricing uses `NumberType.VOIP` | `textverified_service.py` |
| `max_price` wired to `verifications.create()` | `textverified_service.py` |
| Dead `carrier` reads removed from `get_verification_details()` | `textverified_service.py` |
| `reactivate_verification()` method added | `textverified_service.py` |
| Voice: `sms_content` used as transcription (no `audio_url` — field doesn't exist on SDK `Sms`) | `sms_polling_service.py` |
| `_handle_timeout()`: reactivate → check `can_report` → report order | `sms_polling_service.py` |
| Dead carrier enrichment removed from `_poll_textverified()` | `sms_polling_service.py` |

### Purchase Flow Fixes — `47d69fd1`, `750a8d9f`, `3f805f8a`
| Fix | File |
|-----|------|
| SSE streaming purchase endpoint (`/verification/request/stream`) | `purchase_endpoints.py` |
| `check_service_available()` added to legacy purchase path | `purchase_endpoints.py` |
| `ends_at` from TV persisted to DB in SSE recording step | `purchase_endpoints.py` |
| `check_service_available()` passes `capability` (sms/voice) | `purchase_endpoints.py` |
| `can_report` checked before calling `report_verification()` on timeout | `sms_polling_service.py` |

### Stock Accuracy Fixes — `47d69fd1`
| Fix | File |
|-----|------|
| `price=null` services filtered from picker at API layer | `services.py` |
| Out-of-stock services greyed out and unclickable in JS picker | `verification-flow.js` |
| Stock monitor loop sleep 120s → 90s (cache TTL is 120s) | `stock_monitor.py` |
| `purchasing` step shows "Still working..." after 10s | `verification-flow.js` |
| `demandBadge` broken ternary fixed (was JS syntax error) | `verification-flow.js` |

### TV Webhook — `540ee0ec`
| Fix | File |
|-----|------|
| TV webhook endpoint live at `/api/verification/webhook/tv` | `tv_webhook.py` |
| HMAC signature verification with `whsec_` secret | `tv_webhook.py` |
| Webhook registered in TV dashboard | — |
| Instant SMS delivery to browser via WebSocket on webhook arrival | `tv_webhook.py` |
| Deduplication by event ID (Redis, 24h TTL) | `tv_webhook.py` |

### Pricing URL — Confirmed Nov 10 2026
- `/api/pub/v2/pricing/verifications` → **200** ✅ (SDK path — what we use)
- `/api/pub/v2/verifications/pricing` → **404** ❌ (old path — confirmed dead)

---

## OPEN ITEMS

### ~~OPEN-1~~ — `validating` SSE step ✅ DONE `331db1d5`
Removed. SSE flow now goes straight `purchasing` → `recording`.

---

### OPEN-2 — No `transcribing` intermediate status for voice in SSE path
**Severity**: P3 (UX only)
**Master task**: B-002
**File**: `app/api/verification/purchase_endpoints.py`

`mark_verification_transcribing()` exists in `verification_status_service.py` but is never called from the SSE purchase path. Voice verifications waiting for transcription show as `pending` with no indication audio was received.

**Fix**: After `complete` event fires for voice, emit a `transcribing` SSE step before polling starts.

---

### OPEN-3 — `reuse` and `reactivate` never surfaced in UI
**Severity**: P2 (revenue)
**Master tasks**: B-003 through B-006

**Status**:
- ✅ B-003: `reusable_until` column added to `Verification` model
- ✅ B-005: `POST /api/verification/{id}/reuse` endpoint created (`reuse_endpoint.py`)
- ✅ B-007: `TV_STATE_MAP` + `reuse_verification()` on `TextVerifiedService`
- 📋 B-004: WebSocket `reuse_available` event not yet pushed from `sms_polling_service.py`
- 📋 B-006: Reuse banner not yet in UI (`verification-flow.js`, `verify_modern.html`)

**Remaining fix**:
1. In `sms_polling_service.py` after `_complete_verification()`: read `tv_result.reuse.reusable_until`, store on record, push WebSocket event `{type: "reuse_available", fee: 0.25, reusable_until: ...}` if balance ≥ $0.25
2. In `verification-flow.js`: on `reuse_available` WS event, show dismissible banner with service picker link

---

### ~~OPEN-4~~ — Stock monitor docstring ✅ DONE
Fixed. Docstring now reads "refreshes stock every 90 seconds".

---

### OPEN-5 (new) — `smsAndVoiceCombo` capability unused
**Severity**: P3 (revenue)
**Master task**: B-008
**Files**: `app/schemas/verification.py`, `app/services/pricing_calculator.py`, `static/js/verification-flow.js`

TV supports a third capability `smsAndVoiceCombo`. Platform only offers `sms` and `voice`. Add combo to the purchase schema enum, price at base + $0.50, pass through to `verifications.create()`. No polling changes needed — `sms.incoming()` handles both.

---

## SDK GROUND TRUTH (reference)

### What the `Sms` dataclass actually has
```python
@dataclass
class Sms:
    id: str
    to_value: str
    created_at: datetime
    encrypted: bool
    from_value: Optional[str]
    sms_content: Optional[str]   # voice transcription comes through here
    parsed_code: Optional[str]
# NO audio_url. NO transcription field. Voice delivers via sms_content.
```

### What `VerificationExpanded` actually has
```python
@dataclass
class VerificationExpanded:
    number: str
    created_at: datetime
    ends_at: datetime
    id: str
    cancel: CancelAction        # { can_cancel: bool }
    reactivate: ReactivationAction  # { can_reactivate: bool }
    report: ReportAction        # { can_report: bool }
    reuse: ReuseAction          # { reusable_until: Optional[datetime] }
    service_name: str
    state: ReservationState
    total_cost: float
# NO carrier. NO audio_url. NO transcription. NO status string.
```

### `ReservationState` — full enum (platform only handles a subset)
```
verificationPending / verificationCompleted / verificationCanceled
verificationTimedOut / verificationReported / verificationRefunded
verificationReused / verificationReactivated
renewableActive / renewableOverdue / renewableExpired / renewableRefunded
nonrenewableActive / nonrenewableExpired / nonrenewableRefunded
```
Platform maps to `pending/completed/failed` — `verificationReused` and `verificationReactivated` are never checked.

### Stock signal truth
- `GET /api/pub/v2/services` → `service_name` + `capability` only. **No price. No quantity.**
- `POST /api/pub/v2/pricing/verifications` → `price` only. This is the only reliable availability signal.
- `quantity` in raw JSON is not in TV's API contract — present sometimes, not guaranteed.
- `price=null` from pricing endpoint = out of stock. This is our inference, not a documented TV signal, but it works in practice.

### SDK retry behaviour (invisible to our timeout logic)
The SDK session has `Retry(total=3, backoff_factor=1)` on 429/5xx. A single `verifications.create()` can silently take up to 7 extra seconds (1+2+4s backoff) on top of normal response time. SSE timeout comment added to `purchase_endpoints.py` noting this risk.

### New SDK methods now implemented
- `verifications.reuse(id)` — called from `POST /api/verification/{id}/reuse`
- `TV_STATE_MAP` covers all 14 `ReservationState` values — `verificationRefunded` skips platform refund (double-refund prevention)
- `map_tv_state(tv_state)` helper on `TextVerifiedService`

---

## ACCEPTANCE CRITERIA — SSE PURCHASE FLOW (all met ✅)

- [x] Verification countdown uses real `ends_at` from TV — no hardcoded duration
- [x] "Cancel (you will not be charged)" visible until `purchasing` step fires
- [x] Cancel button disappears once charge is committed
- [x] Each loading message maps to a real backend operation
- [x] If pricing check fails → user sees error immediately, no charge
- [x] If balance insufficient → user sees error immediately, no charge
- [x] If TV create fails → user sees specific error, no charge
- [x] Navigating away during active verification → returning to /verify restores session
- [x] `localStorage.active_verification_id` cleared on completion/failure/cancel
- [x] Existing `POST /api/verification/request` still works (API key users)
- [x] TV webhook delivers SMS instantly to browser via WebSocket
- [x] Polling continues as fallback if WebSocket disconnected

---

## SOURCE DOCS (superseded — kept for reference)

| Doc | Status |
|-----|--------|
| `TV_API_FLOW_GAP_ASSESSMENT.md` | Superseded by this file |
| `TV_API_REAL_FLOW.md` | Superseded by this file |
| `TV_STOCK_VERIFICATION_FLOW_ASSESSMENT.md` | Superseded by this file |
| `TV_PURCHASE_FLOW_ALIGNMENT_TASK.md` | Superseded by this file |
