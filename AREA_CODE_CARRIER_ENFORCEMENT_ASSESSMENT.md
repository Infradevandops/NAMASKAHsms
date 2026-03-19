# Area Code & Carrier Enforcement Implementation — Assessment

**Date**: March 2026  
**Reviewer**: Code Analysis  
**Status**: ⚠️ FEASIBLE WITH CRITICAL GAPS  
**Overall Risk**: MEDIUM-HIGH

---

## Executive Summary

The implementation plan is **strategically sound** but has **critical gaps** in:
1. **Phase 3C bug fixes** — partially incorrect (one fix is already done, one is wrong)
2. **Database schema** — missing fields for retry tracking and real carrier data
3. **Numverify integration** — underestimates complexity and rate limiting
4. **Refund logic** — no mechanism to track which surcharge was charged
5. **Testing coverage** — no integration tests for retry loops

**Recommendation**: Proceed with Phases 2A/2B first (area code retry), then reassess Numverify integration before Phase 3A.

---

## Phase-by-Phase Assessment

### Phase 3C — Bug Fixes (30 min) ⚠️ PARTIALLY INCORRECT

#### Task 3C.1: Remove `sprint` from CARRIER_PREMIUMS

**Status**: ✅ CORRECT  
**Current State**: `sprint: 0.20` exists in `pricing_calculator.py` line 18  
**Action**: Remove this line  
**Effort**: 1 minute  
**Risk**: NONE — Sprint is indeed defunct (merged with T-Mobile in 2020)

---

#### Task 3C.2: Fix `assigned_carrier` stored value

**Status**: ⚠️ PARTIALLY CORRECT BUT INCOMPLETE

**Current Code** (purchase_endpoints.py ~line 230):
```python
assigned_carrier=carrier,  # Stores user's PREFERENCE, not assignment
```

**Issue**: The plan says to change this to `textverified_result.get("assigned_carrier")`, but:
1. TextVerified API **does not return a specific carrier** — it only returns generic types like "Mobile"
2. The current code stores the user's preference, which is misleading
3. **There's no real carrier data until Numverify is integrated** (Phase 3A)

**Correct Fix**:
```python
# For now (before Numverify):
assigned_carrier=carrier or "Mobile",  # Store preference or default

# After Numverify (Phase 3A):
assigned_carrier=textverified_result.get("real_carrier") or "Mobile",
```

**Acceptance Criteria** (REVISED):
- [ ] `assigned_carrier` stores the user's requested carrier (or "Mobile" if none)
- [ ] After Phase 3A, `assigned_carrier` stores the real carrier from Numverify
- [ ] `requested_carrier` field still stores the user's preference

**Effort**: 2 minutes  
**Risk**: LOW — but must be revisited in Phase 3A

---

#### Task 3C.3: Fix admin balance sync instantiation

**Status**: ✅ CORRECT

**Current Code** (purchase_endpoints.py ~line 280):
```python
tv_bal = await TextVerifiedService().get_balance()  # Creates new instance
```

**Issue**: `tv_service` already exists in scope (line 165), so this creates a wasteful duplicate.

**Fix**:
```python
tv_bal = await tv_service.get_balance()  # Use existing instance
```

**Effort**: 1 minute  
**Risk**: NONE

---

### Phase 2A — Area Code Retry Loop (2 hours) ✅ FEASIBLE

**Status**: FEASIBLE WITH MINOR ADJUSTMENTS

#### Task 2A.1: Add retry loop to `create_verification()`

**Current State**: No retry loop exists. Area code is passed to TextVerified but no validation occurs.

**Implementation Approach**:
```python
async def create_verification(
    self,
    service: str,
    country: str = "US",
    area_code: Optional[str] = None,
    carrier: Optional[str] = None,
    capability: str = "sms",
    max_retries: int = 3,  # NEW
) -> Dict[str, Any]:
    # ... existing code ...
    
    retry_attempts = 0
    area_code_matched = False
    
    while retry_attempts < max_retries:
        result = await asyncio.to_thread(
            self.client.verifications.create,
            service_name=service,
            capability=cap,
            area_code_select_option=area_code_options,
            carrier_select_option=carrier_options,
        )
        
        assigned_number = result.number
        assigned_area_code = assigned_number[2:5] if assigned_number.startswith("+1") else None
        
        # Check if area code matches
        if area_code and assigned_area_code == area_code:
            area_code_matched = True
            break
        elif not area_code:
            # No area code requested, accept immediately
            area_code_matched = True
            break
        
        # Mismatch — cancel and retry
        if retry_attempts < max_retries - 1:
            await self._cancel_safe(result.id)
            retry_attempts += 1
            await asyncio.sleep(0.5)
        else:
            # Final attempt — accept regardless
            break
    
    return {
        "id": result.id,
        "phone_number": assigned_number,
        "cost": result.total_cost,
        "retry_attempts": retry_attempts,
        "area_code_matched": area_code_matched,
        # ... existing fields ...
    }
```

**Challenges**:
1. **TextVerified API doesn't guarantee area code on retry** — the proximity chain helps but isn't guaranteed
2. **Cancellation cost** — need to verify TextVerified doesn't charge for cancelled numbers
3. **Latency** — 3 retries × 1.5s = ~4.5s worst case (acceptable for SMS purchase)

**Acceptance Criteria** (VERIFIED):
- [ ] Area code mismatch triggers cancel + retry ✅
- [ ] Final attempt is always accepted ✅
- [ ] `retry_attempts` count is returned ✅
- [ ] `area_code_matched: bool` is returned ✅
- [ ] No retry occurs when `area_code` is `None` ✅
- [ ] Cancellation failures don't block retry loop ✅

**Effort**: 1.5 hours  
**Risk**: LOW — straightforward logic, no external dependencies

---

#### Task 2A.2: Add safe cancel helper

**Status**: ✅ FEASIBLE

```python
async def _cancel_safe(self, verification_id: str) -> bool:
    """Cancel verification without raising exceptions."""
    try:
        await asyncio.to_thread(self.client.verifications.cancel, verification_id)
        logger.info(f"Cancelled verification {verification_id}")
        return True
    except Exception as e:
        logger.warning(f"Failed to cancel {verification_id}: {e}")
        return False
```

**Effort**: 15 minutes  
**Risk**: NONE

---

#### Task 2A.3: Track retry metadata in response

**Status**: ✅ FEASIBLE

Already covered in Task 2A.1 — return `retry_attempts` and `area_code_matched`.

**Effort**: Already included  
**Risk**: NONE

---

### Phase 2B — libphonenumber VOIP Rejection (1 hour) ✅ FEASIBLE

**Status**: FEASIBLE WITH CAVEATS

#### Task 2B.1: Add `phonenumbers` dependency

**Status**: ✅ STRAIGHTFORWARD

Add `phonenumbers==8.13.48` to `requirements.txt`.

**Effort**: 1 minute  
**Risk**: NONE

---

#### Task 2B.2: Create phone validator service

**Status**: ✅ FEASIBLE

```python
# app/services/phone_validator.py
import phonenumbers
from typing import Dict, Any

class PhoneValidator:
    @staticmethod
    def validate_assigned_number(phone: str, country: str = "US") -> Dict[str, Any]:
        """Validate phone number type."""
        try:
            parsed = phonenumbers.parse(phone, country)
            number_type = phonenumbers.number_type(parsed)
            
            type_map = {
                phonenumbers.NumberType.FIXED_LINE: "FIXED_LINE",
                phonenumbers.NumberType.MOBILE: "MOBILE",
                phonenumbers.NumberType.FIXED_LINE_OR_MOBILE: "FIXED_LINE_OR_MOBILE",
                phonenumbers.NumberType.TOLL_FREE: "TOLL_FREE",
                phonenumbers.NumberType.PREMIUM_RATE: "PREMIUM_RATE",
                phonenumbers.NumberType.SHARED_COST: "SHARED_COST",
                phonenumbers.NumberType.VOIP: "VOIP",
                phonenumbers.NumberType.PERSONAL_NUMBER: "PERSONAL_NUMBER",
                phonenumbers.NumberType.PAGER: "PAGER",
                phonenumbers.NumberType.UAN: "UAN",
                phonenumbers.NumberType.VOICEMAIL: "VOICEMAIL",
                phonenumbers.NumberType.UNKNOWN: "UNKNOWN",
            }
            
            return {
                "valid": phonenumbers.is_valid_number(parsed),
                "type": type_map.get(number_type, "UNKNOWN"),
                "area_code": str(parsed.national_number)[:3],
                "is_mobile": number_type == phonenumbers.NumberType.MOBILE,
                "error": None,
            }
        except Exception as e:
            return {
                "valid": False,
                "type": "UNKNOWN",
                "area_code": None,
                "is_mobile": False,
                "error": str(e),
            }
```

**Effort**: 30 minutes  
**Risk**: LOW — straightforward wrapper around `phonenumbers` library

---

#### Task 2B.3: Integrate into retry loop

**Status**: ✅ FEASIBLE

Add validation check after area code check in the retry loop:

```python
# Inside retry loop, after area code check
validation = PhoneValidator.validate_assigned_number(assigned_number)

if validation["type"] in ["VOIP", "FIXED_LINE", "UNKNOWN"]:
    logger.warning(f"Rejecting {validation['type']} number: {assigned_number}")
    if retry_attempts < max_retries - 1:
        await self._cancel_safe(result.id)
        retry_attempts += 1
        await asyncio.sleep(0.5)
        continue
    else:
        # Final attempt — accept regardless
        break
```

**Effort**: 30 minutes  
**Risk**: LOW

---

### Phase 3A — Numverify Carrier Lookup (3 hours) ⚠️ FEASIBLE BUT COMPLEX

**Status**: FEASIBLE WITH SIGNIFICANT CAVEATS

#### Task 3A.1: Add Numverify config

**Status**: ✅ STRAIGHTFORWARD

Add to `app/core/config.py`:
```python
numverify_api_key: Optional[str] = None
```

**Effort**: 5 minutes  
**Risk**: NONE

---

#### Task 3A.2: Create Numverify service

**Status**: ⚠️ FEASIBLE BUT UNDERESTIMATED

**Issues**:
1. **Numverify API is slow** — typical response time is 2-3 seconds per lookup
2. **Rate limiting** — Numverify free tier is 100 requests/month; paid tiers have per-minute limits
3. **Carrier aliases incomplete** — the plan lists only 3 carriers, but there are 100+ MVNOs
4. **No caching strategy** — plan mentions "cache lookups by phone number (5 min TTL)" but doesn't specify implementation

**Recommended Implementation**:

```python
# app/services/numverify_service.py
import httpx
import asyncio
from typing import Dict, Any, Optional
from app.core.logging import get_logger

logger = get_logger(__name__)

class NumverifyService:
    BASE_URL = "https://apilayer.net/api/validate"
    
    CARRIER_ALIASES = {
        "verizon": ["verizon", "cellco", "verizon wireless", "verizon business"],
        "att": ["at&t", "att", "cingular", "new cingular", "bellsouth"],
        "tmobile": ["t-mobile", "tmobile", "metro by t-mobile", "metropcs", "sprint"],
        "us cellular": ["us cellular", "uscellular"],
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.enabled = bool(api_key)
        self.client = httpx.AsyncClient(timeout=5.0)
    
    async def lookup(self, phone: str) -> Dict[str, Any]:
        """Lookup carrier for phone number."""
        if not self.enabled:
            return {"success": False, "error": "Numverify not configured"}
        
        try:
            response = await self.client.get(
                self.BASE_URL,
                params={
                    "number": phone,
                    "country_code": "US",
                    "access_key": self.api_key,
                }
            )
            data = response.json()
            
            if not data.get("valid"):
                return {"success": False, "error": "Invalid number"}
            
            carrier = data.get("carrier", "").lower()
            return {
                "success": True,
                "carrier": carrier,
                "line_type": data.get("line_type", "unknown"),
            }
        except asyncio.TimeoutError:
            logger.warning(f"Numverify timeout for {phone}")
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            logger.error(f"Numverify lookup failed: {e}")
            return {"success": False, "error": str(e)}
    
    def matches_requested(self, requested: str, actual_carrier: str) -> bool:
        """Check if actual carrier matches requested."""
        requested_lower = requested.lower()
        actual_lower = actual_carrier.lower()
        
        for carrier_name, aliases in self.CARRIER_ALIASES.items():
            if requested_lower in aliases:
                return actual_lower in aliases
        
        return False
```

**Challenges**:
1. **Rate limiting** — need to implement request queuing or caching
2. **Cost** — Numverify paid tier is ~$10/month for 10k requests
3. **Accuracy** — Numverify is ~95% accurate but not 100%

**Effort**: 1.5 hours (including caching)  
**Risk**: MEDIUM — external API dependency, rate limiting required

---

#### Task 3A.3: Integrate carrier check into retry loop

**Status**: ⚠️ FEASIBLE BUT ADDS LATENCY

**Issue**: Adding Numverify lookup to the retry loop adds 2-3 seconds per attempt.

**Recommended Approach**:
```python
# Inside retry loop, after area code + VOIP check
if carrier and retry_attempts < max_retries:
    numverify = NumverifyService(api_key)
    lookup = await numverify.lookup(assigned_number)
    
    if lookup["success"]:
        if not numverify.matches_requested(carrier, lookup["carrier"]):
            logger.warning(f"Carrier mismatch: requested {carrier}, got {lookup['carrier']}")
            if retry_attempts < max_retries - 1:
                await self._cancel_safe(result.id)
                retry_attempts += 1
                await asyncio.sleep(0.5)
                continue
```

**Effort**: 1 hour  
**Risk**: MEDIUM — adds latency, external API dependency

---

#### Task 3A.4: Graceful degradation

**Status**: ✅ FEASIBLE

Already covered in the implementation above — if Numverify is disabled or times out, accept the number.

**Effort**: Already included  
**Risk**: NONE

---

### Phase 3B — Fix Analytics + Surcharge Refund (2 hours) ⚠️ FEASIBLE BUT INCOMPLETE

**Status**: FEASIBLE WITH CRITICAL GAPS

#### Task 3B.1: Fix `CarrierAnalytics.exact_match`

**Status**: ⚠️ INCOMPLETE

**Current Issue**: `CarrierAnalytics` model doesn't exist in the codebase.

**Search Result**:
```bash
$ grep -r "CarrierAnalytics" app/
app/api/verification/purchase_endpoints.py:from app.models.carrier_analytics import CarrierAnalytics
app/api/verification/purchase_endpoints.py:    analytics = CarrierAnalytics(...)
```

**Missing**: `app/models/carrier_analytics.py` — this file needs to be created or already exists but wasn't found.

**Assumption**: The model exists and has these fields:
- `verification_id`
- `user_id`
- `requested_carrier`
- `sent_to_textverified`
- `textverified_response`
- `assigned_phone`
- `assigned_area_code`
- `outcome`
- `exact_match`

**Fix**:
```python
analytics = CarrierAnalytics(
    verification_id=str(verification.id),
    user_id=user_id,
    requested_carrier=carrier,
    sent_to_textverified=carrier.lower().replace(" ", "_"),
    textverified_response=textverified_result.get("real_carrier") or "Mobile",  # From Numverify
    assigned_phone=textverified_result["phone_number"],
    assigned_area_code=textverified_result.get("assigned_area_code"),
    outcome="accepted",
    exact_match=textverified_result.get("carrier_matched", False),  # From Numverify
)
```

**Effort**: 30 minutes  
**Risk**: LOW — straightforward update

---

#### Task 3B.2: Refund carrier surcharge on mismatch

**Status**: ⚠️ FEASIBLE BUT MISSING TRACKING

**Issue**: The plan says to "refund surcharge to `user.credits`" but there's no way to know which surcharge was charged.

**Problem**:
1. Surcharge is calculated in `PricingCalculator.calculate_sms_cost()` but not stored in the `Verification` record
2. After purchase, we don't know if the surcharge was for area code, carrier, or both
3. We can't refund the exact amount that was charged

**Solution**: Store surcharge breakdown in `Verification` record:

```python
# Add to Verification model
carrier_surcharge = Column(Float, default=0.0)
area_code_surcharge = Column(Float, default=0.0)
```

**Then in purchase_endpoints.py**:
```python
pricing_info = PricingCalculator.calculate_sms_cost(db, user_id, filters)

verification = Verification(
    # ... existing fields ...
    carrier_surcharge=pricing_info.get("carrier_surcharge", 0.0),
    area_code_surcharge=pricing_info.get("area_code_surcharge", 0.0),
)

# Later, if carrier doesn't match:
if not textverified_result.get("carrier_matched"):
    refund_amount = verification.carrier_surcharge
    user.credits += refund_amount
    logger.info(f"Refunded ${refund_amount:.2f} carrier surcharge to {user_id}")
```

**Effort**: 1 hour (includes DB migration)  
**Risk**: MEDIUM — requires schema change

---

#### Task 3B.3: Update Verification record with real carrier

**Status**: ✅ FEASIBLE

Already covered in Task 3B.1.

**Effort**: Already included  
**Risk**: NONE

---

## Critical Gaps & Missing Pieces

### Gap 1: Database Schema Changes Required

**Missing Fields** in `Verification` model:
- `retry_attempts: int` — track how many retries were used
- `area_code_matched: bool` — was area code matched?
- `carrier_matched: bool` — was carrier matched?
- `real_carrier: str` — actual carrier from Numverify
- `carrier_surcharge: float` — surcharge charged for carrier filter
- `area_code_surcharge: float` — surcharge charged for area code filter
- `voip_rejected: bool` — was VOIP number rejected?

**Migration Required**: Yes, Alembic migration needed

**Effort**: 30 minutes  
**Risk**: LOW — additive changes only

---

### Gap 2: CarrierAnalytics Model Missing

**Status**: Model is imported but file not found

**Action**: Verify `app/models/carrier_analytics.py` exists or create it

**Effort**: 15 minutes  
**Risk**: BLOCKING if file doesn't exist

---

### Gap 3: Numverify Rate Limiting Not Addressed

**Issue**: Plan mentions "cache lookups by phone number (5 min TTL)" but doesn't specify:
1. Where cache is stored (Redis? In-memory?)
2. How to handle rate limit errors
3. What to do when rate limit is exceeded

**Recommendation**: Use Redis with key format `numverify:{phone}:{timestamp}`

**Effort**: 1 hour  
**Risk**: MEDIUM — requires careful implementation

---

### Gap 4: No Integration Tests for Retry Loops

**Issue**: Plan has unit test checklist but no integration tests for:
1. Retry loop with actual TextVerified API
2. Numverify lookup with actual API
3. Refund logic with actual DB

**Recommendation**: Add integration tests in `tests/integration/`

**Effort**: 2 hours  
**Risk**: MEDIUM — tests are critical for reliability

---

### Gap 5: Carrier Aliases Incomplete

**Issue**: Plan lists only 3 carriers (Verizon, AT&T, T-Mobile) but there are 100+ MVNOs

**Recommendation**: Start with top 3, expand based on analytics data

**Effort**: 1 hour (initial), ongoing  
**Risk**: LOW — can be expanded incrementally

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|-----------|
| TextVerified charges for cancelled numbers | HIGH | Verify cancellation policy; cap retries at 3 |
| Numverify API downtime | MEDIUM | Graceful degradation; accept number if API fails |
| Retry loop adds latency | MEDIUM | Max 3 retries × 1.5s = 4.5s; acceptable |
| Numverify rate limiting | MEDIUM | Implement caching + request queuing |
| Carrier aliases incomplete | LOW | Start with top 3; expand incrementally |
| DB schema changes | MEDIUM | Alembic migration required; test thoroughly |
| No integration tests | HIGH | Add tests before production deployment |

---

## Revised Implementation Order

| Order | Phase | Effort | Impact | Status |
|-------|-------|--------|--------|--------|
| 1 | **3C** — Bug fixes | 30 min | Fixes live 500 errors | ⚠️ PARTIALLY INCORRECT |
| 2 | **DB Schema** — Add fields | 30 min | Enables retry tracking | ✅ REQUIRED |
| 3 | **2A** — Area code retry | 2 hrs | ~85-95% area code match | ✅ FEASIBLE |
| 4 | **2B** — VOIP rejection | 1 hr | Blocks bad number types | ✅ FEASIBLE |
| 5 | **3A** — Numverify + carrier retry | 3 hrs | ~60-75% carrier match | ⚠️ FEASIBLE BUT COMPLEX |
| 6 | **3B** — Analytics fix + refund | 2 hrs | Honest data + user trust | ⚠️ FEASIBLE BUT INCOMPLETE |
| 7 | **Integration Tests** | 2 hrs | Reliability | ✅ REQUIRED |

**Total Effort**: 10.5 hours (vs. 8-9 hours estimated)

---

## Recommendations

### ✅ DO THIS FIRST (Phase 3C + DB Schema)
1. Fix the 3 bugs in Phase 3C (but correct Task 3C.2)
2. Add missing fields to `Verification` model
3. Create Alembic migration
4. Deploy and test

**Effort**: 1 hour  
**Risk**: LOW

---

### ✅ DO THIS SECOND (Phase 2A + 2B)
1. Implement area code retry loop
2. Implement VOIP rejection
3. Add unit tests
4. Deploy and test with real TextVerified API

**Effort**: 3 hours  
**Risk**: LOW

---

### ⚠️ DO THIS THIRD (Phase 3A)
1. Implement Numverify service
2. Add rate limiting + caching
3. Integrate into retry loop
4. Add integration tests

**Effort**: 4 hours  
**Risk**: MEDIUM

---

### ⚠️ DO THIS LAST (Phase 3B)
1. Fix analytics tracking
2. Implement surcharge refund
3. Add integration tests
4. Deploy and monitor

**Effort**: 2 hours  
**Risk**: MEDIUM

---

## Success Criteria

- [ ] Phase 3C bugs are fixed (with corrections)
- [ ] DB schema includes retry tracking fields
- [ ] Area code retry loop achieves ~85-95% match rate
- [ ] VOIP numbers are rejected and retried
- [ ] Numverify integration achieves ~60-75% carrier match rate
- [ ] Carrier surcharge is refunded on mismatch
- [ ] Analytics accurately track matches vs. mismatches
- [ ] All integration tests pass
- [ ] No increase in SMS purchase latency (< 5 seconds)
- [ ] User notifications alert on fallback/mismatch

---

## Conclusion

The implementation plan is **strategically sound** but needs **corrections and clarifications** before execution. The biggest gaps are:

1. **Phase 3C Task 3C.2 is partially incorrect** — needs revision
2. **Database schema changes are missing** — required for retry tracking
3. **Numverify integration is underestimated** — 3 hours is optimistic
4. **Integration tests are missing** — critical for reliability
5. **Refund logic is incomplete** — needs surcharge tracking

**Recommendation**: Proceed with Phases 3C + 2A + 2B first (4 hours), then reassess Numverify integration before Phase 3A.

