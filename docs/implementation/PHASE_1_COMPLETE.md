# Phase 1 Complete: Bug Fixes ✅

**Date**: March 17, 2026  
**Duration**: ~30 minutes  
**Status**: DEPLOYED

---

## What Was Done

### 1. Tests Created (Test-First)
- **File**: `tests/unit/test_pricing_fixes.py`
- **Tests**: 5 tests covering all bug fixes
- **Result**: All tests pass ✅

### 2. Sprint Removed
- **File**: `app/services/pricing_calculator.py`
- **Change**: Removed `"sprint": 0.20` from CARRIER_PREMIUMS
- **Reason**: Sprint merged with T-Mobile in 2020

### 3. Surcharge Breakdown Added
- **File**: `app/services/pricing_calculator.py`
- **Changes**:
  - Track `carrier_premium` and `area_code_premium` separately
  - Return `carrier_surcharge` and `area_code_surcharge` in response
- **Purpose**: Enable refund logic in Phase 5

### 4. Admin Balance Sync Fixed
- **File**: `app/api/verification/purchase_endpoints.py`
- **Change**: Use existing `tv_service` instance instead of creating new one
- **Impact**: Prevents potential UnboundLocalError

---

## Testing Results

```bash
$ pytest tests/unit/test_pricing_fixes.py -v
============================== 5 passed in 12.32s ==============================
```

### Tests Passing:
- ✅ Sprint removed from CARRIER_PREMIUMS
- ✅ Expected carriers present (Verizon, T-Mobile, AT&T)
- ✅ Surcharge breakdown returned for PAYG with filters
- ✅ Surcharge breakdown zero for no filters
- ✅ Surcharge breakdown zero for freemium

---

## Code Changes

### Before (Sprint):
```python
CARRIER_PREMIUMS = {
    "verizon": 0.30,
    "tmobile": 0.25,
    "t-mobile": 0.25,
    "att": 0.20,
    "at&t": 0.20,
    "sprint": 0.20,  # ❌ DEPRECATED
}
```

### After (Sprint):
```python
CARRIER_PREMIUMS = {
    "verizon": 0.30,
    "tmobile": 0.25,
    "t-mobile": 0.25,
    "att": 0.20,
    "at&t": 0.20,
    # Sprint merged with T-Mobile in 2020 - removed in v4.4.1
}
```

### Before (Surcharge):
```python
return {
    "base_cost": base_cost,
    "filter_charges": filter_charges,
    "overage_charge": overage_charge,
    "total_cost": total_cost,
    "tier": user.subscription_tier,
}
```

### After (Surcharge):
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

### Before (Admin Sync):
```python
tv_bal = await TextVerifiedService().get_balance()  # ❌ New instance
```

### After (Admin Sync):
```python
tv_bal = await tv_service.get_balance()  # ✅ Existing instance
```

---

## Impact

### Sprint Removal
- **Users affected**: Anyone trying to select Sprint carrier
- **Behavior**: Sprint no longer appears in carrier list
- **Recommendation**: Use T-Mobile instead (Sprint merged with T-Mobile)

### Surcharge Breakdown
- **Users affected**: All PAYG users with filters
- **Behavior**: API now returns individual surcharge amounts
- **Purpose**: Enables refund logic when carrier/area code doesn't match

### Admin Balance Sync
- **Users affected**: Admin users only
- **Behavior**: No more UnboundLocalError on verification purchase
- **Impact**: More reliable admin verification purchases

---

## Next Steps

### Phase 2: Area Code Retry (2.5 hours)
- Add retry loop to TextVerifiedService
- Cancel and retry on area code mismatch
- Accept after 3 attempts

### Files to Modify:
1. `app/services/textverified_service.py`
2. `tests/unit/test_area_code_retry.py` (NEW)

---

## Commit Message

```
fix: remove Sprint, add surcharge breakdown, fix admin sync (v4.4.1)

Bug Fixes:
- Remove Sprint from CARRIER_PREMIUMS (merged with T-Mobile)
- Add carrier_surcharge and area_code_surcharge to pricing response
- Fix admin balance sync to use existing tv_service instance

Tests:
- Add 5 unit tests for pricing fixes
- All tests passing ✅

Breaking Changes:
- Sprint carrier no longer available (use T-Mobile)

Related: Phase 1 of v4.4.1 implementation
```

---

**Phase 1 Status**: ✅ COMPLETE  
**Ready for**: Phase 2 (Area Code Retry)
