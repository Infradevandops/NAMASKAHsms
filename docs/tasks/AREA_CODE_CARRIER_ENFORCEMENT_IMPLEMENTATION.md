# Area Code & Carrier Enforcement Implementation

**Version**: 1.0  
**Created**: March 2026  
**Status**: Ready for Implementation  
**Estimated Total Effort**: 8–9 hours

---

## Overview

TextVerified treats carrier and area code as **preferences, not guarantees**. This implementation adds a retry loop with post-assignment validation to maximize match rates, plus honest analytics and surcharge refunds when enforcement fails.

**Realistic Ceilings**:
- Area code match rate: **~85–95%** (retry loop + proximity chain)
- Carrier match rate: **~60–75%** (Numverify + retry loop, inventory-dependent)
- Carrier guarantee: **0%** (impossible with TextVerified alone)

---

## Phase 3C — Fix Existing Bugs (Do This First)

**Effort**: 30 min  
**Priority**: CRITICAL — fixes live 500 errors  

### Task 3C.1: Remove `sprint` from CARRIER_PREMIUMS

- [ ] **File**: `app/services/pricing_calculator.py` line 20
- [ ] Remove `"sprint": 0.20` from `CARRIER_PREMIUMS` dict
- [ ] Sprint merged with T-Mobile — charging for a dead carrier is misleading

**Acceptance Criteria**:
- `CARRIER_PREMIUMS` has no `sprint` entry
- Existing `tmobile` / `t-mobile` entries cover Sprint users

### Task 3C.2: Fix `assigned_carrier` stored value

- [ ] **File**: `app/api/verification/purchase_endpoints.py` ~line 230
- [ ] Change `assigned_carrier=carrier` → `assigned_carrier=textverified_result.get("assigned_carrier") or "Mobile"`
- [ ] Currently stores the user's **preference** as if it were the **assignment** — misleading

**Acceptance Criteria**:
- `Verification.assigned_carrier` reflects what TextVerified actually returned, not the user's request
- `requested_carrier` field still stores the user's preference (already correct)

### Task 3C.3: Fix admin balance sync `TextVerifiedService` instantiation

- [ ] **File**: `app/api/verification/purchase_endpoints.py` ~line 280
- [ ] Change `await TextVerifiedService().get_balance()` → `await tv_service.get_balance()`
- [ ] `tv_service` already exists in scope — creating a new instance is wasteful and was previously causing `UnboundLocalError`

**Acceptance Criteria**:
- Admin balance sync uses the existing `tv_service` instance
- No `UnboundLocalError` on verification requests
- Verification endpoint returns 201 for admin users

---

## Phase 2A — Area Code Retry Loop (Free, Highest ROI)

**Effort**: 2 hours  
**Priority**: HIGH  
**Dependencies**: None  
**External APIs**: None (area code is extracted from the phone number itself)

### Task 2A.1: Add retry loop to `create_verification()`

- [ ] **File**: `app/services/textverified_service.py`
- [ ] Add `max_retries: int = 3` parameter to `create_verification()`
- [ ] Wrap the `self.client.verifications.create()` call in a retry loop
- [ ] After each assignment, extract area code from phone number (`number[2:5]` for +1 numbers)
- [ ] If area code doesn't match requested, cancel the number and retry
- [ ] Add `await asyncio.sleep(0.5)` between retries
- [ ] On final attempt, accept whatever is assigned (don't cancel)

### Task 2A.2: Add safe cancel helper

- [ ] **File**: `app/services/textverified_service.py`
- [ ] Create `async def _cancel_safe(self, verification_id: str) -> bool` helper
- [ ] Wraps `self.client.verifications.cancel()` in try/except
- [ ] Logs failures but never raises

### Task 2A.3: Track retry metadata in response

- [ ] Return `retry_attempts`, `area_code_matched` in the `create_verification()` response dict
- [ ] Log each retry attempt with requested vs assigned area code

**Acceptance Criteria**:
- [ ] Area code mismatch triggers cancel + retry (up to 3 attempts)
- [ ] Final attempt is always accepted regardless of match
- [ ] `retry_attempts` count is returned in the response
- [ ] `area_code_matched: bool` is returned in the response
- [ ] No retry occurs when `area_code` is `None`
- [ ] Cancellation failures don't block the retry loop

---

## Phase 2B — libphonenumber VOIP Rejection

**Effort**: 1 hour  
**Priority**: MEDIUM  
**Dependencies**: Phase 2A  

### Task 2B.1: Add `phonenumbers` dependency

- [ ] Add `phonenumbers==8.13.48` to `requirements.txt`

### Task 2B.2: Create phone validator service

- [ ] **File**: `app/services/phone_validator.py` (new file)
- [ ] Function: `validate_assigned_number(phone: str, country: str = "US") -> dict`
- [ ] Returns: `{"valid": bool, "type": str, "area_code": str, "is_mobile": bool, "error": str|None}`
- [ ] Type mapping: `FIXED_LINE`, `MOBILE`, `VOIP`, `UNKNOWN`

### Task 2B.3: Integrate into retry loop

- [ ] **File**: `app/services/textverified_service.py`
- [ ] After assignment (inside retry loop), call `validate_assigned_number()`
- [ ] If type is `VOIP` or `FIXED_LINE`, cancel and retry
- [ ] Log the rejection reason

**Acceptance Criteria**:
- [ ] VOIP numbers are rejected and retried
- [ ] Landline numbers are rejected and retried
- [ ] Mobile numbers pass validation
- [ ] Invalid numbers are rejected
- [ ] `phonenumbers` library is in `requirements.txt`

---

## Phase 3A — Numverify Carrier Lookup + Carrier Retry

**Effort**: 3 hours  
**Priority**: HIGH  
**Dependencies**: Phase 2A  

### Task 3A.1: Add Numverify config

- [ ] Add `NUMVERIFY_API_KEY` to `.env.example`
- [ ] Add `numverify_api_key: Optional[str]` to `app/core/config.py` settings

### Task 3A.2: Create Numverify service

- [ ] **File**: `app/services/numverify_service.py` (new file)
- [ ] Class: `NumverifyService`
- [ ] Method: `async def lookup(self, phone: str) -> dict` — returns `{"success": bool, "carrier": str, "line_type": str}`
- [ ] Method: `def matches_requested(self, requested: str, actual_carrier: str) -> bool`
- [ ] Define `CARRIER_ALIASES` dict mapping normalized names to known aliases:
  ```
  "verizon": ["verizon", "cellco", "verizon wireless"]
  "att": ["at&t", "att", "cingular", "new cingular"]
  "tmobile": ["t-mobile", "tmobile", "metro by t-mobile", "metropcs"]
  ```
- [ ] Use `httpx.AsyncClient` with 5s timeout
- [ ] Never raise — return `{"success": False}` on any error
- [ ] Add `httpx` to `requirements.txt` if not present

### Task 3A.3: Integrate carrier check into retry loop

- [ ] **File**: `app/services/textverified_service.py`
- [ ] After area code check passes (inside retry loop), run Numverify lookup if `carrier` is requested
- [ ] If `numverify.matches_requested()` returns `False`, cancel and retry
- [ ] On final attempt, accept regardless of carrier match
- [ ] Return `real_carrier`, `carrier_matched`, `numverify_used` in response

### Task 3A.4: Graceful degradation

- [ ] If `NUMVERIFY_API_KEY` is not set, skip carrier validation entirely
- [ ] If Numverify API times out or errors, accept the number (don't block purchase)
- [ ] Log all Numverify failures as warnings

**Acceptance Criteria**:
- [ ] Carrier mismatch triggers cancel + retry (up to remaining retries from area code loop)
- [ ] `real_carrier` from Numverify is returned in the response
- [ ] `carrier_matched: bool` is returned in the response
- [ ] Service works normally when `NUMVERIFY_API_KEY` is not set
- [ ] Numverify failures never block a purchase
- [ ] Alias matching works (e.g., "cellco" matches "verizon" request)

---

## Phase 3B — Fix Analytics + Surcharge Refund

**Effort**: 2 hours  
**Priority**: MEDIUM  
**Dependencies**: Phase 3A  

### Task 3B.1: Fix `CarrierAnalytics.exact_match`

- [ ] **File**: `app/api/verification/purchase_endpoints.py`
- [ ] Update `CarrierAnalytics` creation to use Numverify result:
  - `textverified_response` = `textverified_result.get("real_carrier") or "Mobile"`
  - `exact_match` = `textverified_result.get("carrier_matched", False)`
- [ ] `exact_match` should only be `True` when Numverify confirms the real carrier matches

**Acceptance Criteria**:
- [ ] `exact_match` is `True` only when Numverify confirms a real carrier match
- [ ] `textverified_response` stores the actual carrier from Numverify, not "Mobile"
- [ ] When Numverify is disabled, `exact_match` is always `False`

### Task 3B.2: Refund carrier surcharge on mismatch

- [ ] **File**: `app/api/verification/purchase_endpoints.py`
- [ ] After purchase, if `carrier_matched` is `False` and retries exhausted:
  - Calculate carrier surcharge from `PricingCalculator.CARRIER_PREMIUMS`
  - Refund surcharge to `user.credits`
  - Log the refund
  - Send notification via `NotificationDispatcher`

**Acceptance Criteria**:
- [ ] Carrier surcharge is refunded when carrier doesn't match after all retries
- [ ] Refund amount matches the surcharge that was charged
- [ ] User is notified of the mismatch and refund
- [ ] No refund occurs when carrier matches or when no carrier was requested
- [ ] Refund is committed in the same DB transaction

### Task 3B.3: Update Verification record with real carrier

- [ ] **File**: `app/api/verification/purchase_endpoints.py`
- [ ] Set `assigned_carrier` = `textverified_result.get("real_carrier")` (from Numverify)
- [ ] Add `carrier_matched` field to response JSON

**Acceptance Criteria**:
- [ ] `Verification.assigned_carrier` stores the real carrier from Numverify
- [ ] API response includes `carrier_matched: bool`
- [ ] When Numverify is disabled, `assigned_carrier` = `"Mobile"` (TextVerified default)

---

## Implementation Order

| Order | Phase | Effort | Impact | Notes |
|-------|-------|--------|--------|-------|
| 1 | **3C** — Bug fixes | 30 min | Fixes live 500 errors | Do TODAY |
| 2 | **2A** — Area code retry | 2 hrs | ~85-95% area code match | Free, no external API |
| 3 | **2B** — VOIP rejection | 1 hr | Blocks bad number types | Requires `phonenumbers` |
| 4 | **3A** — Numverify + carrier retry | 3 hrs | ~60-75% carrier match | Requires API key |
| 5 | **3B** — Analytics fix + refund | 2 hrs | Honest data + user trust | Requires Phase 3A |

---

## Files Modified

| File | Phases | Changes |
|------|--------|---------|
| `app/services/textverified_service.py` | 2A, 2B, 3A | Retry loop, VOIP check, carrier check |
| `app/api/verification/purchase_endpoints.py` | 3C, 3B | Bug fixes, analytics fix, surcharge refund |
| `app/services/pricing_calculator.py` | 3C | Remove `sprint` |
| `app/services/phone_validator.py` | 2B | New file |
| `app/services/numverify_service.py` | 3A | New file |
| `app/core/config.py` | 3A | Add `NUMVERIFY_API_KEY` |
| `requirements.txt` | 2B, 3A | Add `phonenumbers`, `httpx` |
| `.env.example` | 3A | Add `NUMVERIFY_API_KEY` |

---

## Testing Checklist

### Phase 2A Tests
- [ ] Area code match on first attempt — no retry
- [ ] Area code mismatch — retries and matches on attempt 2
- [ ] Area code mismatch — exhausts retries, accepts last assignment
- [ ] No area code requested — no retry loop
- [ ] Cancel failure during retry — loop continues

### Phase 2B Tests
- [ ] Mobile number passes validation
- [ ] VOIP number triggers retry
- [ ] Landline number triggers retry
- [ ] Invalid number triggers retry

### Phase 3A Tests
- [ ] Carrier matches on first attempt — no retry
- [ ] Carrier mismatch — retries and matches
- [ ] Carrier mismatch — exhausts retries, accepts
- [ ] Numverify disabled — skips carrier check
- [ ] Numverify timeout — accepts number
- [ ] Alias matching works (cellco → verizon)

### Phase 3B Tests
- [ ] `exact_match` is `True` when Numverify confirms match
- [ ] `exact_match` is `False` when Numverify disabled
- [ ] Carrier surcharge refunded on mismatch
- [ ] No refund when carrier matches
- [ ] User notification sent on refund

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| TextVerified charges for cancelled numbers | Cap retries at 3; check TV cancellation policy |
| Numverify API downtime | Graceful degradation — skip carrier check, accept number |
| Retry loop adds latency | Max 3 retries × ~1.5s = ~4.5s worst case; acceptable for SMS purchase |
| Numverify rate limits | Cache lookups by phone number (5 min TTL); use semaphore |
| Carrier aliases incomplete | Start with top 3 carriers; expand based on analytics data |
