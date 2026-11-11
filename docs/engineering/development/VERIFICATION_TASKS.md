# Verification System — Consolidated Task File

**Created**: November 2026
**Consolidates**: TV_API_FLOW_GAP_ASSESSMENT.md, TV_API_REAL_FLOW.md, TV_STOCK_VERIFICATION_FLOW_ASSESSMENT.md, TV_PURCHASE_FLOW_ALIGNMENT_TASK.md
**Status**: Most work complete. 4 open items remain.

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

### OPEN-1 — `validating` SSE step does no real work
**Severity**: P3 (UX only)
**File**: `app/api/verification/purchase_endpoints.py`

After `purchasing` completes, `validating` fires immediately with zero real work. It is a UX label only. Options:
- Remove it — go straight `purchasing` → `recording`
- Wire it to `get_verification_details()` to confirm number is live and surface `can_cancel` to frontend

**Recommended**: Remove. The step misleads users into thinking validation is happening.

---

### OPEN-2 — No `transcribing` intermediate status for voice in SSE path
**Severity**: P3 (UX only)
**File**: `app/api/verification/purchase_endpoints.py`

`mark_verification_transcribing()` exists in `verification_status_service.py` but is never called from the SSE purchase path. Voice verifications waiting for transcription show as `pending` with no indication audio was received. Users think the verification is still waiting for a call.

**Fix**: After `complete` event fires for voice, emit a `transcribing` SSE step before polling starts.

---

### OPEN-3 — `reuse` and `reactivate` never surfaced in UI
**Severity**: P2 (cost saving + revenue)
**Files**: `textverified_service.py` (methods exist), `verification-flow.js`, `verify_modern.html`
**Revenue spec**: `docs/features/REVENUE_FEATURES_SPEC.md` → Feature 2

TV supports:
- **Reactivate**: Resume a timed-out verification (extends window). Free retry, no repurchase.
- **Reuse**: Use same number for a different service. Costs less than new purchase.

Both methods are implemented in `textverified_service.py` but never called from the UI.

**Reuse monetization**: Charge $0.25 convenience fee. Only shown if user balance ≥ $0.25. If balance is short, option doesn't appear — no friction.

**Fix**:
1. Store `reusable_until` on verification record after completion (from `tv_result.reuse.reusable_until`)
2. Push WebSocket event `reuse_available` with fee and expiry
3. Show dismissible banner in UI: "Reuse this number for another service — $0.25"
4. New endpoint: `POST /api/verification/{id}/reuse` — deducts $0.25, calls `tv_service.reuse_verification()`
5. On timeout, check `can_reactivate` before issuing refund — offer "Try again (free)" to user

---

### OPEN-4 — Stock monitor docstring says "15-minute refresh" (should be 90s)
**Severity**: P3 (docs)
**File**: `app/services/stock_monitor.py` → `run_stock_monitor()`

```python
# Current (wrong):
"""Background loop — 15-minute refresh."""

# Fix:
"""Background loop — refreshes stock every 90 seconds."""
```

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
The SDK session has `Retry(total=3, backoff_factor=1)` on 429/5xx. A single `verifications.create()` can silently take up to 7 extra seconds (1+2+4s backoff) on top of normal response time. Our `asyncio.wait_for(..., timeout=15.0)` may not be long enough under load.

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
