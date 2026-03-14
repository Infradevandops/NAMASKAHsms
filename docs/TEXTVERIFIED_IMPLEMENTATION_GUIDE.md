# TextVerified Alignment - Implementation Guide

**Version**: 1.0  
**Date**: March 14, 2026  
**Status**: Ready for Execution  
**Audience**: Engineering Team

---

## 🎯 Quick Start

This guide provides step-by-step implementation instructions for the TextVerified Alignment Roadmap. Each task includes:
- Detailed code changes
- Acceptance criteria checklist
- Testing procedures
- Rollback procedures

**Total Estimated Effort**: 60-80 hours over 3-4 weeks

---

## 📋 Milestone 1: Stop the Bleeding (Days 1-3)

### Task 1.1: Fix Carrier Validation Logic

**Effort**: 2 hours  
**Files**: `app/api/verification/purchase_endpoints.py`, `app/services/textverified_service.py`

#### Step 1: Understand Current State

```bash
# Check current carrier validation logic
grep -n "Carrier validation" app/api/verification/purchase_endpoints.py
grep -n "_extract_carrier_from_number" app/services/textverified_service.py
```

#### Step 2: Remove Strict Carrier Validation

**File**: `app/api/verification/purchase_endpoints.py` (Lines 223-248)

**BEFORE**:
```python
# Step 2.1: CRITICAL CARRIER VALIDATION (Task 2.3)
if carrier:
    assigned_carrier = textverified_result.get("assigned_carrier")
    logger.info(f"Carrier validation: requested={carrier}, assigned={assigned_carrier}")
    
    # Accept "Mobile" as valid fallback for any mobile carrier request
    mobile_carriers = ["mobile", "cellular", "wireless"]
    req_norm = carrier.lower().replace("-", "").replace(" ", "").replace("&", "")
    asgn_norm = (assigned_carrier or "").lower().replace("-", "").replace(" ", "").replace("&", "")
    
    # Check if mismatch is acceptable (Mobile is valid fallback)
    is_mobile_fallback = asgn_norm in mobile_carriers and any(mc in req_norm for mc in mobile_carriers)
    
    if assigned_carrier and asgn_norm != req_norm and not is_mobile_fallback:
        # ... cancel and raise 409
```

**AFTER**:
```python
# Step 2.1: CARRIER PREFERENCE LOGGING (TextVerified best-effort)
if carrier:
    assigned_carrier = textverified_result.get("assigned_carrier")
    logger.info(
        f"Carrier preference applied: requested={carrier}, "
        f"assigned_type={assigned_carrier} (TextVerified best-effort, not guaranteed)"
    )
    # No validation — TextVerified treats carrier as preference, not guarantee
```

**Implementation**:
<function_calls>
<invoke name="fsRead">
<parameter name="paths">["/Users/machine/My Drive/Github Projects/Namaskah. app/app/api/verification/purchase_endpoints.py"]