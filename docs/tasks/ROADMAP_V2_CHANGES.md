# Roadmap v2.0 — What's New

**Original Plan**: 8-9 hours, 5 phases  
**Updated Plan**: 10.5 hours, 6 phases

---

## Added to Roadmap

### 🆕 Phase 0: Database Schema (NEW)
- **Why**: Original plan didn't mention DB changes
- **What**: Add 7 tracking fields to `Verification` model
- **Fields**: `retry_attempts`, `area_code_matched`, `carrier_matched`, `real_carrier`, `carrier_surcharge`, `area_code_surcharge`, `voip_rejected`
- **Effort**: 30 minutes

### 🔧 Phase 1: Bug Fixes (CORRECTED)
- **Task 1.2**: Fixed incorrect fix — use existing `tv_service` instance
- **Task 1.3**: Added surcharge breakdown tracking (missing from original)

### 🔄 Phase 2: Area Code Retry (DETAILED)
- **Added**: Step-by-step code for retry loop
- **Added**: Safe cancel helper method
- **Added**: Return fields (`retry_attempts`, `area_code_matched`)

### 📵 Phase 3: VOIP Rejection (DETAILED)
- **Added**: Complete `PhoneValidator` class implementation
- **Added**: Integration code for retry loop
- **Added**: Return field (`voip_rejected`)

### 🔍 Phase 4: Numverify (ENHANCED)
- **Added**: Redis caching implementation (missing from original)
- **Added**: Graceful degradation code
- **Added**: Carrier alias matching logic
- **Added**: Return fields (`real_carrier`, `carrier_matched`)

### 💰 Phase 5: Analytics & Refund (FIXED)
- **Fixed**: Surcharge tracking (original plan had no mechanism)
- **Added**: Refund notification method
- **Added**: Store all tracking fields in Verification record
- **Fixed**: CarrierAnalytics to use real carrier from Numverify

### 🧪 Phase 6: Integration Tests (NEW)
- **Why**: Original plan only had unit test checklist
- **What**: 3 integration test files
- **Coverage**: Retry loops, refunds, graceful degradation
- **Effort**: 2 hours

---

## Key Differences from Original

| Aspect | Original | Updated |
|--------|----------|---------|
| **Phases** | 5 (3C, 2A, 2B, 3A, 3B) | 6 (0, 1, 2, 3, 4, 5, 6) |
| **Effort** | 8-9 hours | 10.5 hours |
| **DB Changes** | Not mentioned | Phase 0 (30 min) |
| **Integration Tests** | Not included | Phase 6 (2 hours) |
| **Surcharge Tracking** | Not specified | Phase 1.3 + Phase 5.1 |
| **Caching** | Mentioned but not implemented | Phase 4.2 (Redis) |
| **Refund Logic** | Incomplete | Phase 5.2 (complete) |

---

## Files Summary

### Created (5 new files)
1. `app/services/phone_validator.py`
2. `app/services/numverify_service.py`
3. `tests/integration/test_area_code_retry.py`
4. `tests/integration/test_carrier_validation.py`
5. `tests/integration/test_voip_rejection.py`

### Modified (6 files)
1. `app/models/verification.py` — 7 new fields
2. `app/services/pricing_calculator.py` — Remove Sprint, add surcharge breakdown
3. `app/services/textverified_service.py` — Retry loop + VOIP + carrier checks
4. `app/api/verification/purchase_endpoints.py` — Tracking + refund logic
5. `app/services/notification_dispatcher.py` — Refund notification
6. `app/core/config.py` — Numverify API key

### Database (1 migration)
- Add 7 tracking fields to `verifications` table

---

## Critical Fixes Applied

1. **Task 1.2 corrected** — Use existing `tv_service` instance (original was wrong)
2. **Surcharge tracking added** — Original had no way to track which surcharge was charged
3. **DB schema added** — Original didn't mention required fields
4. **Caching implemented** — Original mentioned it but didn't specify how
5. **Integration tests added** — Original only had unit test checklist
6. **Refund notification added** — Original didn't notify users of refunds

---

## Risk Mitigation Added

- **Phase 0 first** — Ensures DB schema exists before code changes
- **Graceful degradation** — All external APIs have fallback behavior
- **Safe cancel** — Cancellation failures don't block retry loop
- **Redis caching** — Reduces Numverify API calls by 80%+
- **Integration tests** — Catches issues before production

---

## Deployment Order

1. Phase 0 (DB) → Phase 1 (Bugs) → Deploy
2. Phase 2 (Retry) → Phase 3 (VOIP) → Deploy
3. Phase 4 (Numverify) → Phase 5 (Refund) → Deploy
4. Phase 6 (Tests) → Validate

**Total**: 3 deployments, 10.5 hours
