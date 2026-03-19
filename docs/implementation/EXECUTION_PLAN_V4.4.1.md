# Implementation Execution Plan - v4.4.1

**Strategy**: Test-first, deploy incrementally, rollback-ready  
**Total Effort**: 10.5 hours (split into 3 deployments)

---

## Deployment 1: Schema + Bug Fixes (1.5 hours)

### Phase 0: Database Schema (1 hour)

#### Step 1: Write schema tests FIRST

**File**: `tests/unit/test_verification_schema.py` (NEW)

```python
"""Test verification schema changes."""
import pytest
from app.models.verification import Verification

def test_verification_has_retry_fields():
    """Verify new retry tracking fields exist."""
    v = Verification(user_id="test", service_name="whatsapp", cost=2.50)
    
    assert hasattr(v, "retry_attempts")
    assert hasattr(v, "area_code_matched")
    assert hasattr(v, "carrier_matched")
    assert hasattr(v, "real_carrier")
    assert hasattr(v, "carrier_surcharge")
    assert hasattr(v, "area_code_surcharge")
    assert hasattr(v, "voip_rejected")

def test_retry_attempts_defaults_to_zero():
    v = Verification(user_id="test", service_name="whatsapp", cost=2.50)
    assert v.retry_attempts == 0

def test_matched_fields_default_to_true():
    v = Verification(user_id="test", service_name="whatsapp", cost=2.50)
    assert v.area_code_matched is True
    assert v.carrier_matched is True

def test_surcharge_fields_default_to_zero():
    v = Verification(user_id="test", service_name="whatsapp", cost=2.50)
    assert v.carrier_surcharge == 0.0
    assert v.area_code_surcharge == 0.0
```

**Run**: `pytest tests/unit/test_verification_schema.py -v` (SHOULD FAIL)

#### Step 2: Update Verification model

**File**: `app/models/verification.py` (line ~30)

```python
# Retry tracking (v4.4.1)
retry_attempts = Column(Integer, default=0)
area_code_matched = Column(Boolean, default=True)
carrier_matched = Column(Boolean, default=True)
real_carrier = Column(String)
carrier_surcharge = Column(Float, default=0.0)
area_code_surcharge = Column(Float, default=0.0)
voip_rejected = Column(Boolean, default=False)
```

#### Step 3: Create migration

```bash
alembic revision -m "add_retry_tracking_v4_4_1"
```

**Migration file**:
```python
def upgrade():
    op.add_column('verifications', sa.Column('retry_attempts', sa.Integer(), server_default='0'))
    op.add_column('verifications', sa.Column('area_code_matched', sa.Boolean(), server_default='true'))
    op.add_column('verifications', sa.Column('carrier_matched', sa.Boolean(), server_default='true'))
    op.add_column('verifications', sa.Column('real_carrier', sa.String()))
    op.add_column('verifications', sa.Column('carrier_surcharge', sa.Float(), server_default='0.0'))
    op.add_column('verifications', sa.Column('area_code_surcharge', sa.Float(), server_default='0.0'))
    op.add_column('verifications', sa.Column('voip_rejected', sa.Boolean(), server_default='false'))

def downgrade():
    op.drop_column('verifications', 'voip_rejected')
    op.drop_column('verifications', 'area_code_surcharge')
    op.drop_column('verifications', 'carrier_surcharge')
    op.drop_column('verifications', 'real_carrier')
    op.drop_column('verifications', 'carrier_matched')
    op.drop_column('verifications', 'area_code_matched')
    op.drop_column('verifications', 'retry_attempts')
```

#### Step 4: Test migration

```bash
alembic upgrade head
pytest tests/unit/test_verification_schema.py -v  # SHOULD PASS
alembic downgrade -1  # Test rollback
alembic upgrade head  # Re-apply
```

---

### Phase 1: Bug Fixes (30 min)

#### Step 1: Write tests

**File**: `tests/unit/test_pricing_fixes.py` (NEW)

```python
def test_sprint_removed():
    from app.services.pricing_calculator import PricingCalculator
    assert "sprint" not in PricingCalculator.CARRIER_PREMIUMS

def test_surcharge_breakdown_returned(mock_db, mock_user):
    from app.services.pricing_calculator import PricingCalculator
    result = PricingCalculator.calculate_sms_cost(
        mock_db, "test_user", {"carrier": "verizon", "area_code": "212"}
    )
    assert "carrier_surcharge" in result
    assert "area_code_surcharge" in result
```

**Run**: `pytest tests/unit/test_pricing_fixes.py -v` (SHOULD FAIL)

#### Step 2: Fix pricing calculator

**File**: `app/services/pricing_calculator.py`

Remove Sprint (line 18):
```python
CARRIER_PREMIUMS = {
    "verizon": 0.30,
    "tmobile": 0.25,
    "t-mobile": 0.25,
    "att": 0.20,
    "at&t": 0.20,
}
```

Add surcharge breakdown (line 50):
```python
carrier_premium = 0.0
area_code_premium = 0.0

if user.subscription_tier == "payg":
    if filters.get("area_code"):
        area_code_premium = PricingCalculator.AREA_CODE_PREMIUMS.get(str(filters["area_code"]), 0.25)
    if filters.get("carrier"):
        carrier_premium = PricingCalculator.CARRIER_PREMIUMS.get(str(filters["carrier"]).lower(), 0.50)

filter_charges = carrier_premium + area_code_premium

return {
    "base_cost": base_cost,
    "filter_charges": filter_charges,
    "overage_charge": overage_charge,
    "total_cost": total_cost,
    "tier": user.subscription_tier,
    "carrier_surcharge": carrier_premium,
    "area_code_surcharge": area_code_premium,
}
```

#### Step 3: Fix admin balance sync

**File**: `app/api/verification/purchase_endpoints.py` (line ~280)

```python
if user.is_admin:
    try:
        tv_bal = await tv_service.get_balance()  # Use existing instance
        live_balance = tv_bal.get("balance")
        if live_balance is not None:
            user.credits = live_balance
    except Exception as _sync_err:
        logger.warning(f"TV balance sync failed: {_sync_err}")
```

#### Step 4: Run tests

```bash
pytest tests/unit/test_pricing_fixes.py -v  # SHOULD PASS
pytest tests/unit/ -v  # Run all unit tests
```

---

### Deployment 1: Deploy to Production

```bash
# Commit changes
git add app/models/ alembic/ app/services/ app/api/ tests/
git commit -m "feat: v4.4.1 schema + bug fixes"

# Deploy
# 1. Run migration: alembic upgrade head
# 2. Deploy code
# 3. Monitor for 24 hours
```

**Acceptance**:
- [ ] Migration runs successfully
- [ ] No errors in production
- [ ] Existing verifications unaffected
- [ ] Sprint removed from pricing
- [ ] Surcharge breakdown working

---

## Deployment 2: Area Code Retry + VOIP (4 hours)

### Phase 2: Area Code Retry (2.5 hours)

#### Step 1: Write tests FIRST

**File**: `tests/unit/test_area_code_retry.py` (NEW)

```python
import pytest
from unittest.mock import Mock, patch
from app.services.textverified_service import TextVerifiedService

@pytest.mark.asyncio
async def test_cancel_safe_no_exception():
    tv = TextVerifiedService()
    with patch.object(tv.client.verifications, 'cancel', side_effect=Exception("Error")):
        result = await tv._cancel_safe("test_id")
        assert result is False

@pytest.mark.asyncio
async def test_area_code_match_first_try():
    tv = TextVerifiedService()
    mock_result = Mock(id="test", number="+12125551234", total_cost=2.50)
    
    with patch.object(tv.client.verifications, 'create', return_value=mock_result):
        result = await tv.create_verification(service="whatsapp", area_code="212")
        
        assert result["retry_attempts"] == 0
        assert result["area_code_matched"] is True

@pytest.mark.asyncio
async def test_area_code_mismatch_retries():
    tv = TextVerifiedService()
    mock_wrong = Mock(id="test1", number="+17135551234", total_cost=2.50)
    mock_right = Mock(id="test2", number="+12125551234", total_cost=2.50)
    
    with patch.object(tv.client.verifications, 'create', side_effect=[mock_wrong, mock_right]):
        with patch.object(tv, '_cancel_safe', return_value=True):
            result = await tv.create_verification(service="whatsapp", area_code="212")
            
            assert result["retry_attempts"] == 1
            assert result["area_code_matched"] is True

@pytest.mark.asyncio
async def test_accepts_after_max_retries():
    tv = TextVerifiedService()
    mock_wrong = Mock(id="test", number="+17135551234", total_cost=2.50)
    
    with patch.object(tv.client.verifications, 'create', return_value=mock_wrong):
        with patch.object(tv, '_cancel_safe', return_value=True):
            result = await tv.create_verification(service="whatsapp", area_code="212", max_retries=3)
            
            assert result["retry_attempts"] == 2
            assert result["area_code_matched"] is False
```

**Run**: `pytest tests/unit/test_area_code_retry.py -v` (SHOULD FAIL)

#### Step 2: Implement retry logic

**File**: `app/services/textverified_service.py`

Add cancel helper:
```python
async def _cancel_safe(self, verification_id: str) -> bool:
    try:
        await asyncio.to_thread(self.client.verifications.cancel, verification_id)
        logger.info(f"Cancelled {verification_id}")
        return True
    except Exception as e:
        logger.warning(f"Cancel failed {verification_id}: {e}")
        return False
```

Update create_verification:
```python
async def create_verification(
    self,
    service: str,
    country: str = "US",
    area_code: Optional[str] = None,
    carrier: Optional[str] = None,
    capability: str = "sms",
    max_retries: int = 3,
) -> Dict[str, Any]:
    # ... existing setup code ...
    
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
        
        if not area_code or assigned_area_code == area_code:
            area_code_matched = True
            break
        
        if retry_attempts < max_retries - 1:
            logger.warning(f"Area code mismatch: {area_code} != {assigned_area_code}")
            await self._cancel_safe(result.id)
            retry_attempts += 1
            await asyncio.sleep(0.5)
        else:
            logger.warning(f"Final attempt: accepting {assigned_area_code}")
            break
    
    return {
        "id": result.id,
        "phone_number": assigned_number,
        "cost": result.total_cost,
        "retry_attempts": retry_attempts,
        "area_code_matched": area_code_matched,
        # ... existing fields
    }
```

#### Step 3: Run tests

```bash
pytest tests/unit/test_area_code_retry.py -v  # SHOULD PASS
```

---

### Phase 3: VOIP Rejection (1.5 hours)

#### Step 1: Add dependency

```bash
echo "phonenumbers==8.13.48" >> requirements.txt
pip install phonenumbers==8.13.48
```

#### Step 2: Write tests

**File**: `tests/unit/test_phone_validator.py` (NEW)

```python
from app.services.phone_validator import PhoneValidator

def test_mobile_validated():
    result = PhoneValidator.validate_assigned_number("+12125551234")
    assert result["valid"] is True
    assert result["type"] == "MOBILE"

def test_invalid_handled():
    result = PhoneValidator.validate_assigned_number("invalid")
    assert result["valid"] is False
    assert result["error"] is not None
```

**Run**: `pytest tests/unit/test_phone_validator.py -v` (SHOULD FAIL)

#### Step 3: Implement validator

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

#### Step 4: Integrate into retry loop

**File**: `app/services/textverified_service.py`

Add after area code check:
```python
from app.services.phone_validator import PhoneValidator

validation = PhoneValidator.validate_assigned_number(assigned_number)

if validation["type"] in ["VOIP", "FIXED_LINE", "UNKNOWN"]:
    logger.warning(f"Rejecting {validation['type']}: {assigned_number}")
    if retry_attempts < max_retries - 1:
        await self._cancel_safe(result.id)
        retry_attempts += 1
        await asyncio.sleep(0.5)
        continue
```

Update return:
```python
return {
    # ... existing
    "voip_rejected": validation.get("type") == "VOIP",
}
```

#### Step 5: Run tests

```bash
pytest tests/unit/test_phone_validator.py -v
pytest tests/unit/test_area_code_retry.py -v
```

---

### Deployment 2: Deploy to Production

```bash
git add app/services/ requirements.txt tests/
git commit -m "feat: area code retry + VOIP rejection"

# Deploy
# Monitor retry rates
# Monitor VOIP rejection rate
```

**Acceptance**:
- [ ] Area code retry working
- [ ] VOIP rejection working
- [ ] No increase in errors
- [ ] Purchase latency < 5s

---

## Monitoring & Rollback

### Key Metrics
- Area code match rate (target: 85%+)
- Retry attempts avg (target: <1.5)
- VOIP rejection rate (target: 5-10%)
- Purchase success rate (target: >95%)

### Rollback Commands
```bash
# Rollback code
git revert HEAD

# Rollback migration
alembic downgrade -1
```

---

**Status**: Ready for Phase 0-3 implementation  
**Next**: Phases 4-6 (Numverify + Refunds) - 5 hours
