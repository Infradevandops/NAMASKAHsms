# Area Code Implementation - Quick Checklist

**Task**: Implement tier-gated area code support for voice & rentals
**Document**: `docs/tasks/AREA_CODE_IMPLEMENTATION_VOICE_RENTALS.md`
**Status**: 📋 Ready to Start

---

## ✅ Phase 1: Voice Verification (Week 1)

### Backend
- [ ] Add `calculate_voice_cost()` with tier logic
- [ ] Update `/api/verification/request` endpoint with tier validation
- [ ] Add tier check before area code processing
- [ ] Implement PAYG fee ($0.25) and Pro/Custom inclusion

### Frontend
- [ ] Add `checkUserTier()` function
- [ ] Show/hide advanced options based on tier
- [ ] Display fee for PAYG, "Included" for Pro/Custom
- [ ] Add upgrade prompt for Freemium users
- [ ] Update pricing breakdown dynamically

### Testing
- [ ] Unit tests for tier gating logic
- [ ] Integration tests for complete flow
- [ ] Test all 4 tiers (Freemium, PAYG, Pro, Custom)
- [ ] Test pricing calculations

### Documentation
- [ ] Update API docs with tier requirements
- [ ] Add pricing page updates
- [ ] Create user guide for area codes
- [ ] Update FAQ

---

## ✅ Phase 2: Rentals (Week 2)

### Backend
- [ ] Add `area_code` parameter to `create_reservation()`
- [ ] Implement area code preference chain for rentals
- [ ] Add `calculate_rental_cost()` with tier logic
- [ ] Update `/api/rentals/create` endpoint with tier validation
- [ ] Implement PAYG fee ($0.50) and Pro/Custom inclusion

### Frontend
- [ ] Add advanced options section to rentals page
- [ ] Add area code dropdown
- [ ] Add availability check
- [ ] Add alternative suggestions
- [ ] Update pricing breakdown
- [ ] Add tier-based UI gating

### Testing
- [ ] Unit tests for rental area code logic
- [ ] Integration tests for rental flow
- [ ] Test tier gating
- [ ] Test pricing calculations

### Documentation
- [ ] Update rentals documentation
- [ ] Add area code feature to changelog
- [ ] Update pricing page
- [ ] Create rental area code guide

---

## 📊 Tier Gating Summary

| Tier | Voice Area Code | Rental Area Code | Fee |
|------|----------------|------------------|-----|
| Freemium | ❌ Not available | ❌ Not available | N/A |
| PAYG | ✅ Available | ✅ Available | +$0.25 / +$0.50 |
| Pro | ✅ Included | ✅ Included | $0 (included) |
| Custom | ✅ Included | ✅ Included | $0 (included) |

---

## 🎯 Quick Start

1. Read full plan: `docs/tasks/AREA_CODE_IMPLEMENTATION_VOICE_RENTALS.md`
2. Start with Phase 1 (Voice)
3. Complete testing before Phase 2
4. Deploy incrementally (voice first, then rentals)

---

## 📞 Key Files

### Backend
- `app/services/textverified_service.py` - Add area code to rentals
- `app/services/verification_service.py` - Add tier gating
- `app/services/rental_service.py` - Add tier gating
- `app/api/core/verification.py` - Update endpoint
- `app/api/core/rentals.py` - Update endpoint

### Frontend
- `templates/voice_verify_modern.html` - Add tier checks
- `templates/rentals.html` - Add area code UI

### Tests
- `tests/unit/test_voice_area_code_gating.py` - New
- `tests/unit/test_rental_area_code_gating.py` - New
- `tests/integration/test_voice_area_code_flow.py` - New

---

**Estimated Time**: 2 weeks
**Priority**: HIGH (Voice), MEDIUM (Rentals)
**Status**: Ready to implement
