# Area Code & Carrier Enforcement — Implementation Roadmap v2.0

**Date**: March 2026  
**Status**: COMPLETE  
**Completed**: March 18, 2026 (v4.4.1)  
**Total Effort**: 10.5 hours delivered

---

## Status Summary

All 6 phases delivered in v4.4.1. See `docs/implementation/V4.4.1_COMPLETE.md` for full delivery notes.

---

## Phase 0: Database Schema ✅ COMPLETE

- [x] Task 0.1: 7 tracking fields added to `Verification` model (`retry_attempts`, `area_code_matched`, `carrier_matched`, `real_carrier`, `carrier_surcharge`, `area_code_surcharge`, `voip_rejected`)
- [x] Task 0.2: Alembic migration created and run
- [x] Task 0.3: Migration verified on production

---

## Phase 1: Critical Bug Fixes ✅ COMPLETE

- [x] Task 1.1: Sprint removed from `CARRIER_PREMIUMS` in `pricing_calculator.py`
- [x] Task 1.2: Admin balance sync fixed — uses existing `tv_service` instance
- [x] Task 1.3: Surcharge breakdown returned from `calculate_sms_cost()`

---

## Phase 2: Area Code Retry Loop ✅ COMPLETE

- [x] Task 2.1: `_cancel_safe()` helper added to `textverified_service.py`
- [x] Task 2.2: Retry loop added to `create_verification()` — up to 3 attempts, final attempt always accepted
- [x] `retry_attempts` and `area_code_matched` returned in result dict

---

## Phase 3: VOIP Rejection ✅ COMPLETE

- [x] Task 3.1: `phonenumbers` dependency added to `requirements.txt`
- [x] Task 3.2: `PhoneValidator` service created at `app/services/phone_validator.py`
- [x] Task 3.3: VOIP/landline check integrated into retry loop, `voip_rejected` returned

---

## Phase 4: Carrier Lookup ✅ COMPLETE

- [x] Task 4.1: `carrier_lookup_api_key` config added
- [x] Task 4.2: `CarrierLookupService` created at `app/services/carrier_lookup.py`
- [x] Task 4.3: Carrier check integrated into retry loop, `real_carrier` and `carrier_matched` returned

---

## Phase 5: Analytics & Refund ✅ COMPLETE

- [x] Task 5.1: All 7 tracking fields stored in `Verification` record on purchase
- [x] Task 5.2: Carrier surcharge refunded on mismatch (tier-aware: PAYG full refund, Pro/Custom overage refund)
- [x] Task 5.3: `notify_carrier_mismatch_refund()` added to `NotificationDispatcher`
- [x] Task 5.4: `CarrierAnalytics` uses real carrier from lookup

---

## Phase 6: Integration Tests ✅ COMPLETE

- [x] Task 6.1: Area code retry tests — `tests/unit/test_area_code_retry.py`
- [x] Task 6.2: Carrier validation tests written
- [x] Task 6.3: VOIP rejection tests written
- [x] 61 tests passing, 100% coverage on new code

---

**All phases delivered. This roadmap is archived.**

---

## Phase 0: Database Schema (30 min) 🔧

**Priority**: CRITICAL — Must be done first  
**Blocks**: All other phases

### Task 0.1: Add tracking fields to Verification model

**File**: `app/models/verification.py`

```python
# Add after line 30 (after assigned_carrier)
retry_attempts = Column(Integer, default=0)
area_code_matched = Column(Boolean, default=True)
carrier_matched = Column(Boolean, default=True)
real_carrier = Column(String)  # From Numverify
carrier_surcharge = Column(Float, default=0.0)
area_code_surcharge = Column(Float, default=0.0)
voip_rejected = Column(Boolean, default=False)
```

### Task 0.2: Create Alembic migration

```bash
alembic revision -m "add_retry_tracking_fields"
```

**Migration file**:
```python
def upgrade():
    op.add_column('verifications', sa.Column('retry_attempts', sa.Integer(), default=0))
    op.add_column('verifications', sa.Column('area_code_matched', sa.Boolean(), default=True))
    op.add_column('verifications', sa.Column('carrier_matched', sa.Boolean(), default=True))
    op.add_column('verifications', sa.Column('real_carrier', sa.String()))
    op.add_column('verifications', sa.Column('carrier_surcharge', sa.Float(), default=0.0))
    op.add_column('verifications', sa.Column('area_code_surcharge', sa.Float(), default=0.0))
    op.add_column('verifications', sa.Column('voip_rejected', sa.Boolean(), default=False))

def downgrade():
    op.drop_column('verifications', 'voip_rejected')
    op.drop_column('verifications', 'area_code_surcharge')
    op.drop_column('verifications', 'carrier_surcharge')
    op.drop_column('verifications', 'real_carrier')
    op.drop_column('verifications', 'carrier_matched')
    op.drop_column('verifications', 'area_code_matched')
    op.drop_column('verifications', 'retry_attempts')
```

### Task 0.3: Run migration

```bash
alembic upgrade head
```

**Acceptance**:
- [ ] Migration runs without errors
- [ ] All 7 fields exist in `verifications` table
- [ ] Existing records have default values

---

## Phase 1: Critical Bug Fixes (30 min) 🐛

**Priority**: CRITICAL  
**Dependencies**: None

### Task 1.1: Remove Sprint from pricing

**File**: `app/services/pricing_calculator.py` line 18

**Change**:
```python
# BEFORE
CARRIER_PREMIUMS = {
    "verizon": 0.30,
    "tmobile": 0.25,
    "t-mobile": 0.25,
    "att": 0.20,
    "at&t": 0.20,
    "sprint": 0.20,  # ❌ REMOVE THIS LINE
}

# AFTER
CARRIER_PREMIUMS = {
    "verizon": 0.30,
    "tmobile": 0.25,
    "t-mobile": 0.25,
    "att": 0.20,
    "at&t": 0.20,
}
```

### Task 1.2: Fix admin balance sync

**File**: `app/api/verification/purchase_endpoints.py` line ~280

**Change**:
```python
# BEFORE
tv_bal = await TextVerifiedService().get_balance()

# AFTER
tv_bal = await tv_service.get_balance()
```

### Task 1.3: Store surcharge breakdown

**File**: `app/services/pricing_calculator.py`

**Update `calculate_sms_cost()` return**:
```python
return {
    "base_cost": base_cost,
    "filter_charges": filter_charges,
    "overage_charge": overage_charge,
    "total_cost": total_cost,
    "tier": user.subscription_tier,
    "carrier_surcharge": carrier_premium,  # NEW
    "area_code_surcharge": area_code_premium,  # NEW
}
```

**Acceptance**:
- [ ] Sprint removed from CARRIER_PREMIUMS
- [ ] Admin balance sync uses existing instance
- [ ] Surcharge breakdown returned in pricing

---

## Phase 2: Area Code Retry Loop (2 hours) 🔄

**Priority**: HIGH  
**Dependencies**: Phase 0, Phase 1

### Task 2.1: Add safe cancel helper

**File**: `app/services/textverified_service.py`

**Add method**:
```python
async def _cancel_safe(self, verification_id: str) -> bool:
    """Cancel verification without raising."""
    try:
        await asyncio.to_thread(self.client.verifications.cancel, verification_id)
        logger.info(f"Cancelled verification {verification_id}")
        return True
    except Exception as e:
        logger.warning(f"Cancel failed for {verification_id}: {e}")
        return False
```

### Task 2.2: Add retry loop to create_verification

**File**: `app/services/textverified_service.py`

**Update method signature**:
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
```

**Add retry loop** (after line 450):
```python
retry_attempts = 0
area_code_matched = False
result = None

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
    
    # Check area code match
    if not area_code or assigned_area_code == area_code:
        area_code_matched = True
        break
    
    # Mismatch — retry if not final attempt
    if retry_attempts < max_retries - 1:
        logger.warning(f"Area code mismatch: requested {area_code}, got {assigned_area_code}")
        await self._cancel_safe(result.id)
        retry_attempts += 1
        await asyncio.sleep(0.5)
    else:
        # Final attempt — accept
        logger.warning(f"Final attempt: accepting {assigned_area_code} (requested {area_code})")
        break
```

**Update return dict**:
```python
return {
    "id": result.id,
    "phone_number": assigned_number,
    "cost": result.total_cost,
    "retry_attempts": retry_attempts,  # NEW
    "area_code_matched": area_code_matched,  # NEW
    # ... existing fields
}
```

**Acceptance**:
- [ ] Retry loop cancels and retries on mismatch
- [ ] Final attempt always accepted
- [ ] `retry_attempts` returned
- [ ] `area_code_matched` returned

---

## Phase 3: VOIP Rejection (1 hour) 📵

**Priority**: MEDIUM  
**Dependencies**: Phase 2

### Task 3.1: Add phonenumbers dependency

**File**: `requirements.txt`

```
phonenumbers==8.13.48
```

### Task 3.2: Create phone validator service

**File**: `app/services/phone_validator.py` (NEW)

```python
import phonenumbers
from typing import Dict, Any

class PhoneValidator:
    @staticmethod
    def validate_assigned_number(phone: str, country: str = "US") -> Dict[str, Any]:
        try:
            parsed = phonenumbers.parse(phone, country)
            number_type = phonenumbers.number_type(parsed)
            
            type_map = {
                phonenumbers.NumberType.MOBILE: "MOBILE",
                phonenumbers.NumberType.FIXED_LINE: "FIXED_LINE",
                phonenumbers.NumberType.VOIP: "VOIP",
                phonenumbers.NumberType.UNKNOWN: "UNKNOWN",
            }
            
            return {
                "valid": phonenumbers.is_valid_number(parsed),
                "type": type_map.get(number_type, "UNKNOWN"),
                "is_mobile": number_type == phonenumbers.NumberType.MOBILE,
                "error": None,
            }
        except Exception as e:
            return {"valid": False, "type": "UNKNOWN", "is_mobile": False, "error": str(e)}
```

### Task 3.3: Integrate VOIP check into retry loop

**File**: `app/services/textverified_service.py`

**Add after area code check**:
```python
# Validate phone type
from app.services.phone_validator import PhoneValidator
validation = PhoneValidator.validate_assigned_number(assigned_number)

if validation["type"] in ["VOIP", "FIXED_LINE", "UNKNOWN"]:
    logger.warning(f"Rejecting {validation['type']} number: {assigned_number}")
    if retry_attempts < max_retries - 1:
        await self._cancel_safe(result.id)
        retry_attempts += 1
        await asyncio.sleep(0.5)
        continue
```

**Update return dict**:
```python
return {
    # ... existing fields
    "voip_rejected": validation["type"] == "VOIP",  # NEW
}
```

**Acceptance**:
- [ ] VOIP numbers rejected and retried
- [ ] Landline numbers rejected and retried
- [ ] Mobile numbers accepted
- [ ] `voip_rejected` returned

---

## Phase 4: Numverify Integration (3 hours) 🔍

**Priority**: HIGH  
**Dependencies**: Phase 3

### Task 4.1: Add Numverify config

**File**: `app/core/config.py`

```python
# Add after line 65
numverify_api_key: Optional[str] = None
```

**File**: `.env.example`

```
NUMVERIFY_API_KEY=your_key_here
```

### Task 4.2: Create Numverify service

**File**: `app/services/numverify_service.py` (NEW)

```python
import httpx
import asyncio
from typing import Dict, Any, Optional
from app.core.logging import get_logger
from app.core.cache import get_redis

logger = get_logger(__name__)

class NumverifyService:
    BASE_URL = "https://apilayer.net/api/validate"
    
    CARRIER_ALIASES = {
        "verizon": ["verizon", "cellco", "verizon wireless"],
        "att": ["at&t", "att", "cingular", "new cingular"],
        "tmobile": ["t-mobile", "tmobile", "metro", "metropcs", "sprint"],
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.enabled = bool(api_key)
        self.client = httpx.AsyncClient(timeout=5.0) if self.enabled else None
    
    async def lookup(self, phone: str) -> Dict[str, Any]:
        if not self.enabled:
            return {"success": False, "error": "Not configured"}
        
        # Check cache
        cache_key = f"numverify:{phone}"
        try:
            redis = get_redis()
            cached = redis.get(cache_key)
            if cached:
                import json
                return json.loads(cached)
        except Exception:
            pass
        
        # API call
        try:
            response = await self.client.get(
                self.BASE_URL,
                params={"number": phone, "country_code": "US", "access_key": self.api_key}
            )
            data = response.json()
            
            if not data.get("valid"):
                return {"success": False, "error": "Invalid"}
            
            result = {
                "success": True,
                "carrier": data.get("carrier", "").lower(),
                "line_type": data.get("line_type", "unknown"),
            }
            
            # Cache for 5 minutes
            try:
                import json
                redis.setex(cache_key, 300, json.dumps(result))
            except Exception:
                pass
            
            return result
        except asyncio.TimeoutError:
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            logger.error(f"Numverify failed: {e}")
            return {"success": False, "error": str(e)}
    
    def matches_requested(self, requested: str, actual: str) -> bool:
        req_lower = requested.lower()
        act_lower = actual.lower()
        
        for carrier, aliases in self.CARRIER_ALIASES.items():
            if req_lower in aliases:
                return act_lower in aliases
        
        return False
```

### Task 4.3: Integrate carrier check into retry loop

**File**: `app/services/textverified_service.py`

**Add after VOIP check**:
```python
# Carrier validation
real_carrier = None
carrier_matched = True

if carrier:
    from app.core.config import get_settings
    from app.services.numverify_service import NumverifyService
    
    settings = get_settings()
    numverify = NumverifyService(settings.numverify_api_key)
    
    if numverify.enabled:
        lookup = await numverify.lookup(assigned_number)
        if lookup["success"]:
            real_carrier = lookup["carrier"]
            carrier_matched = numverify.matches_requested(carrier, real_carrier)
            
            if not carrier_matched and retry_attempts < max_retries - 1:
                logger.warning(f"Carrier mismatch: requested {carrier}, got {real_carrier}")
                await self._cancel_safe(result.id)
                retry_attempts += 1
                await asyncio.sleep(0.5)
                continue
```

**Update return dict**:
```python
return {
    # ... existing fields
    "real_carrier": real_carrier,  # NEW
    "carrier_matched": carrier_matched,  # NEW
}
```

**Acceptance**:
- [ ] Numverify lookup called when carrier requested
- [ ] Carrier mismatch triggers retry
- [ ] Graceful degradation if API disabled
- [ ] Results cached for 5 minutes

---

## Phase 5: Analytics & Refund (2 hours) 💰

**Priority**: MEDIUM  
**Dependencies**: Phase 4

### Task 5.1: Store surcharges in Verification

**File**: `app/api/verification/purchase_endpoints.py`

**Update Verification creation** (line ~230):
```python
pricing_info = PricingCalculator.calculate_sms_cost(db, user_id, filters)

verification = Verification(
    # ... existing fields
    carrier_surcharge=pricing_info.get("carrier_surcharge", 0.0),  # NEW
    area_code_surcharge=pricing_info.get("area_code_surcharge", 0.0),  # NEW
    retry_attempts=textverified_result.get("retry_attempts", 0),  # NEW
    area_code_matched=textverified_result.get("area_code_matched", True),  # NEW
    carrier_matched=textverified_result.get("carrier_matched", True),  # NEW
    real_carrier=textverified_result.get("real_carrier"),  # NEW
    voip_rejected=textverified_result.get("voip_rejected", False),  # NEW
)
```

### Task 5.2: Refund carrier surcharge on mismatch (tier-aware)

**File**: `app/api/verification/purchase_endpoints.py`

**Add after verification creation**:
```python
# Refund carrier surcharge if mismatch (tier-aware)
if carrier and not textverified_result.get("carrier_matched", True):
    refund_amount = verification.carrier_surcharge
    
    # PAYG: Refund the surcharge ($0.30)
    # Pro/Custom: Filters are included, but refund overage cost difference
    if refund_amount > 0:
        if user.subscription_tier == "payg":
            # Full surcharge refund
            user.credits += refund_amount
            logger.info(f"PAYG refund: ${refund_amount:.2f} carrier surcharge to {user_id}")
        elif user.subscription_tier in ["pro", "custom"]:
            # Pro/Custom: Filters included in quota, but refund if overage was charged
            tier_config = TierConfig.get_tier_config(user.subscription_tier, db)
            overage_rate = tier_config.get("overage_rate", 0.30)
            
            # If this SMS pushed them into overage, refund the overage portion
            quota_info = QuotaService.get_monthly_usage(db, user_id)
            if quota_info["quota_used"] > quota_info["quota_limit"]:
                # Refund overage cost (not the surcharge, since filters are included)
                overage_refund = overage_rate
                user.credits += overage_refund
                refund_amount = overage_refund
                logger.info(f"{user.subscription_tier.upper()} refund: ${overage_refund:.2f} overage to {user_id}")
        
        # Notify user
        try:
            await notification_dispatcher.notify_carrier_mismatch_refund(
                user_id=user_id,
                verification_id=str(verification.id),
                requested_carrier=carrier,
                actual_carrier=textverified_result.get("real_carrier", "Unknown"),
                refund_amount=refund_amount,
                tier=user.subscription_tier,
            )
        except Exception:
            pass
```

### Task 5.3: Add refund notification

**File**: `app/services/notification_dispatcher.py`

**Add method**:
```python
async def notify_carrier_mismatch_refund(
    self,
    user_id: str,
    verification_id: str,
    requested_carrier: str,
    actual_carrier: str,
    refund_amount: float,
    tier: str,
) -> bool:
    try:
        if tier == "payg":
            message = f"Requested {requested_carrier}, got {actual_carrier}. ${refund_amount:.2f} surcharge refunded."
        else:
            message = f"Requested {requested_carrier}, got {actual_carrier}. ${refund_amount:.2f} overage refunded."
        
        notification = self.notification_service.create_notification(
            user_id=user_id,
            notification_type="carrier_mismatch_refund",
            title="Carrier Mismatch — Refund Issued",
            message=message,
        )
        self._broadcast_notification(user_id, notification)
        return True
    except Exception as e:
        logger.error(f"Failed to create carrier_mismatch_refund notification: {e}")
        return False
```

### Task 5.4: Fix CarrierAnalytics

**File**: `app/api/verification/purchase_endpoints.py`

**Update analytics creation** (line ~250):
```python
if carrier:
    analytics = CarrierAnalytics(
        verification_id=str(verification.id),
        user_id=user_id,
        requested_carrier=carrier,
        sent_to_textverified=carrier.lower().replace(" ", "_"),
        textverified_response=textverified_result.get("real_carrier") or "Mobile",  # UPDATED
        assigned_phone=textverified_result["phone_number"],
        assigned_area_code=textverified_result.get("assigned_area_code"),
        outcome="accepted",
        exact_match=textverified_result.get("carrier_matched", False),  # UPDATED
    )
```

**Acceptance**:
- [ ] Surcharges stored in Verification
- [ ] Carrier surcharge refunded on mismatch
- [ ] User notified of refund
- [ ] Analytics use real carrier from Numverify

---

## Phase 6: Integration Tests (2 hours) 🧪

**Priority**: HIGH  
**Dependencies**: All phases

### Task 6.1: Area code retry tests

**File**: `tests/integration/test_area_code_retry.py` (NEW)

```python
import pytest
from app.services.textverified_service import TextVerifiedService

@pytest.mark.asyncio
async def test_area_code_match_first_attempt():
    tv = TextVerifiedService()
    result = await tv.create_verification(
        service="whatsapp",
        area_code="212",
    )
    assert result["retry_attempts"] == 0
    assert result["area_code_matched"] is True

@pytest.mark.asyncio
async def test_area_code_retry_on_mismatch():
    # Mock TextVerified to return wrong area code first
    pass

@pytest.mark.asyncio
async def test_area_code_accepts_after_max_retries():
    pass
```

### Task 6.2: Carrier validation tests

**File**: `tests/integration/test_carrier_validation.py` (NEW)

```python
@pytest.mark.asyncio
async def test_carrier_match():
    pass

@pytest.mark.asyncio
async def test_carrier_mismatch_refund():
    pass

@pytest.mark.asyncio
async def test_numverify_disabled_graceful():
    pass
```

### Task 6.3: VOIP rejection tests

**File**: `tests/integration/test_voip_rejection.py` (NEW)

```python
def test_mobile_number_accepted():
    pass

def test_voip_number_rejected():
    pass

def test_landline_rejected():
    pass
```

**Acceptance**:
- [ ] All integration tests pass
- [ ] Tests cover retry loops
- [ ] Tests cover refund logic
- [ ] Tests cover graceful degradation

---

## Summary of Changes

### New Files Created (5)
1. `app/services/phone_validator.py` — VOIP/landline detection
2. `app/services/numverify_service.py` — Carrier lookup
3. `tests/integration/test_area_code_retry.py` — Retry tests
4. `tests/integration/test_carrier_validation.py` — Carrier tests
5. `tests/integration/test_voip_rejection.py` — VOIP tests

### Files Modified (6)
1. `app/models/verification.py` — Add 7 tracking fields
2. `app/services/pricing_calculator.py` — Remove Sprint, add surcharge breakdown
3. `app/services/textverified_service.py` — Add retry loop, VOIP check, carrier check
4. `app/api/verification/purchase_endpoints.py` — Store tracking data, refund logic
5. `app/services/notification_dispatcher.py` — Add refund notification
6. `app/core/config.py` — Add Numverify API key

### Database Changes (1)
- Alembic migration: Add 7 fields to `verifications` table

### Dependencies Added (2)
- `phonenumbers==8.13.48`
- `httpx` (if not present)

---

## Deployment Checklist

- [ ] Phase 0: Run DB migration
- [ ] Phase 1: Deploy bug fixes
- [ ] Phase 2: Deploy area code retry
- [ ] Phase 3: Deploy VOIP rejection
- [ ] Phase 4: Add `NUMVERIFY_API_KEY` to env, deploy
- [ ] Phase 5: Deploy refund logic
- [ ] Phase 6: Run integration tests
- [ ] Monitor retry rates in production
- [ ] Monitor refund rates in production

---

**Total Effort**: 10.5 hours  
**Phases**: 6  
**Files Modified**: 6  
**Files Created**: 5  
**DB Migrations**: 1
