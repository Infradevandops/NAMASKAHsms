# Area Code Implementation - Consolidated Guide

**Version**: v4.6.1
**Date**: May 10, 2026
**Status**: 🎯 Ready for Implementation
**Estimated Time**: 2 weeks

---

## 🎯 Executive Summary

Implement tier-gated area code selection for voice verification and rentals, following the proven SMS verification pattern.

**Provider Support**: ✅ Confirmed via API signature inspection
**Pattern**: Reuse SMS verification tier gating logic
**Revenue Impact**: +$2,025/mo (projected for 1000 users)

---

## 📊 Tier Gating Matrix

| Tier | Voice Area Code | Rental Area Code | Fee Structure |
|------|----------------|------------------|---------------|
| **Freemium** | ❌ Disabled | ❌ Disabled | N/A |
| **PAYG** | ✅ Enabled | ✅ Enabled | +$0.25 / +$0.50 |
| **Pro** | ✅ Enabled | ✅ Enabled | Included ($0) |
| **Custom** | ✅ Enabled | ✅ Enabled | Included ($0) |

**Rationale**:
- Freemium: Basic service only (no filtering)
- PAYG: Pay-per-use premium feature
- Pro/Custom: Included as value proposition
- Rentals fee higher: Longer duration = higher value

---

## 🚀 Implementation Phases

### Phase 1: Voice Verification (5 days)

#### Day 1-2: Backend
**Files**: `app/services/verification_service.py`, `app/api/core/verification.py`

```python
# verification_service.py
async def calculate_voice_cost(
    user: User,
    service: str,
    area_code: Optional[str] = None,
) -> Dict[str, float]:
    """Calculate voice cost with tier-aware area code pricing."""
    base_cost = await self.get_base_cost(service, "voice")
    tier = user.subscription_tier or "freemium"

    # Tier gating
    if area_code:
        if tier == "freemium":
            raise HTTPException(403, "Area code requires PAYG+")
        area_code_fee = 0.25 if tier == "payg" else 0.0
    else:
        area_code_fee = 0.0

    return {
        "base_cost": base_cost,
        "area_code_fee": area_code_fee,
        "total_cost": base_cost + area_code_fee,
    }
```

**Acceptance Criteria**:
- [ ] Freemium users get 403 error with area code
- [ ] PAYG users charged $0.25 extra
- [ ] Pro/Custom users charged $0 extra
- [ ] Cost calculation accurate for all tiers

#### Day 3: Frontend
**File**: `templates/voice_verify_modern.html`

```javascript
// Check tier and show/hide options
async function initVoicePage() {
    const user = await fetchCurrentUser();
    const tier = user.subscription_tier || 'freemium';

    if (tier === 'freemium') {
        hideAdvancedOptions();
        showUpgradePrompt();
    } else {
        showAdvancedOptions();
        updateFeeDisplay(tier);
    }
}

function updateFeeDisplay(tier) {
    const feeText = tier === 'payg' ? '+$0.25' : 'Included';
    document.getElementById('area-code-fee').textContent = feeText;
}
```

**Acceptance Criteria**:
- [ ] Freemium: Advanced options hidden
- [ ] Freemium: Upgrade prompt shown
- [ ] PAYG: "+$0.25" fee displayed
- [ ] Pro/Custom: "Included" displayed
- [ ] Pricing updates dynamically

#### Day 4: Testing
**File**: `tests/unit/test_voice_area_code_gating.py`

```python
class TestVoiceAreaCodeGating:
    async def test_freemium_blocked(self):
        user = User(tier="freemium")
        with pytest.raises(HTTPException) as exc:
            await calculate_voice_cost(user, "google", "213")
        assert exc.value.status_code == 403

    async def test_payg_fee(self):
        user = User(tier="payg")
        cost = await calculate_voice_cost(user, "google", "213")
        assert cost["area_code_fee"] == 0.25

    async def test_pro_included(self):
        user = User(tier="pro")
        cost = await calculate_voice_cost(user, "google", "213")
        assert cost["area_code_fee"] == 0.0
```

**Acceptance Criteria**:
- [ ] All tier tests pass
- [ ] Edge cases covered
- [ ] Integration tests pass

#### Day 5: Deploy & Monitor
- [ ] Deploy to staging
- [ ] Run smoke tests
- [ ] Deploy to production
- [ ] Monitor for 24h

---

### Phase 2: Rentals (5 days)

#### Day 1-2: Backend
**Files**: `app/services/textverified_service.py`, `app/services/rental_service.py`

```python
# textverified_service.py
async def create_reservation(
    service: str,
    duration_hours: float,
    area_code: Optional[str] = None,  # NEW
) -> Dict[str, Any]:
    area_code_options = None
    if area_code:
        area_code_options = await self._build_area_code_preference(area_code)

    reservation = await asyncio.to_thread(
        self.client.reservations.create,
        service_name=service,
        duration=int(duration_hours * 60),
        area_code_select_option=area_code_options,  # NEW
    )

    return {
        "id": reservation.id,
        "phone_number": reservation.number,
        "requested_area_code": area_code,
        "assigned_area_code": reservation.number[2:5],
        "area_code_matched": reservation.number[2:5] == area_code if area_code else None,
    }

# rental_service.py
async def calculate_rental_cost(
    user: User,
    service: str,
    duration_hours: float,
    area_code: Optional[str] = None,
) -> Dict[str, float]:
    base_cost = await self.get_base_cost(service, duration_hours)
    tier = user.subscription_tier or "freemium"

    if area_code:
        if tier == "freemium":
            raise HTTPException(403, "Area code requires PAYG+")
        area_code_fee = 0.50 if tier == "payg" else 0.0
    else:
        area_code_fee = 0.0

    return {
        "base_cost": base_cost,
        "area_code_fee": area_code_fee,
        "total_cost": base_cost + area_code_fee,
    }
```

**Acceptance Criteria**:
- [ ] Area code parameter added to create_reservation()
- [ ] Area code preference chain works
- [ ] Tier gating logic correct
- [ ] PAYG fee is $0.50 (not $0.25)

#### Day 3: Frontend
**File**: `templates/rentals.html`

```html
<!-- Advanced Options (copy from voice_verify_modern.html) -->
<div id="rental-advanced-options">
    <div onclick="toggleRentalAdvanced()">
        ▶ Advanced Options <span class="premium-badge">PREMIUM</span>
    </div>
    <div id="rental-advanced-body" style="display:none;">
        <label>Area Code (Optional)</label>
        <select id="rental-area-code">
            <option value="">Any Area Code (Fastest)</option>
            <!-- Populated dynamically -->
        </select>
        <div id="rental-ac-status"></div>
    </div>
</div>

<!-- Pricing -->
<div class="pricing-row">
    <span>Base Cost</span>
    <span id="rental-base">$15.00</span>
</div>
<div class="pricing-row" id="rental-ac-fee-row">
    <span>Area Code Filter <span class="tier-badge">PAYG</span></span>
    <span id="rental-ac-fee">$0.50</span>
</div>
<div class="pricing-row">
    <span>Total</span>
    <span id="rental-total">$15.50</span>
</div>
```

**Acceptance Criteria**:
- [ ] Advanced options section added
- [ ] Area code dropdown populated
- [ ] Tier-based UI gating works
- [ ] Pricing updates dynamically
- [ ] Matches voice verification UX

#### Day 4: Testing
**File**: `tests/unit/test_rental_area_code_gating.py`

```python
class TestRentalAreaCodeGating:
    async def test_freemium_blocked(self):
        user = User(tier="freemium")
        with pytest.raises(HTTPException) as exc:
            await calculate_rental_cost(user, "google", 24.0, "213")
        assert exc.value.status_code == 403

    async def test_payg_higher_fee(self):
        user = User(tier="payg")
        cost = await calculate_rental_cost(user, "google", 24.0, "213")
        assert cost["area_code_fee"] == 0.50  # Higher than voice

    async def test_pro_included(self):
        user = User(tier="pro")
        cost = await calculate_rental_cost(user, "google", 24.0, "213")
        assert cost["area_code_fee"] == 0.0
```

**Acceptance Criteria**:
- [ ] All tier tests pass
- [ ] Fee is $0.50 (not $0.25)
- [ ] Integration tests pass

#### Day 5: Deploy & Monitor
- [ ] Deploy to staging
- [ ] Run smoke tests
- [ ] Deploy to production
- [ ] Monitor for 24h

---

## ✅ Master Acceptance Criteria

### Voice Verification
- [ ] **Tier Gating**: Freemium blocked, PAYG/Pro/Custom allowed
- [ ] **Pricing**: PAYG +$0.25, Pro/Custom $0
- [ ] **UI**: Advanced options hidden for Freemium
- [ ] **UI**: Fee displayed correctly per tier
- [ ] **API**: Tier validation on backend
- [ ] **Tests**: 100% passing (unit + integration)
- [ ] **Docs**: Updated with tier requirements

### Rentals
- [ ] **Backend**: area_code parameter added
- [ ] **Backend**: Area code preference chain works
- [ ] **Tier Gating**: Freemium blocked, PAYG/Pro/Custom allowed
- [ ] **Pricing**: PAYG +$0.50, Pro/Custom $0
- [ ] **UI**: Advanced options section added
- [ ] **UI**: Matches voice verification UX
- [ ] **API**: Tier validation on backend
- [ ] **Tests**: 100% passing (unit + integration)
- [ ] **Docs**: Updated with tier requirements

### Cross-Cutting
- [ ] **Security**: Tier validation on backend (never trust frontend)
- [ ] **Audit**: All area code usage logged
- [ ] **Monitoring**: Success rate tracked
- [ ] **Documentation**: User guides updated
- [ ] **Support**: FAQ updated with tier info

---

## 🧪 Test Plan

### Unit Tests (20 tests)
```bash
# Voice
tests/unit/test_voice_area_code_gating.py          # 8 tests
tests/unit/test_voice_cost_calculation.py          # 4 tests

# Rentals
tests/unit/test_rental_area_code_gating.py         # 8 tests
tests/unit/test_rental_cost_calculation.py         # 4 tests
```

### Integration Tests (8 tests)
```bash
# Voice
tests/integration/test_voice_area_code_flow.py     # 4 tests

# Rentals
tests/integration/test_rental_area_code_flow.py    # 4 tests
```

### Manual Tests (10 scenarios)
```
Voice:
1. Freemium user tries area code → Blocked
2. PAYG user uses area code → Charged $0.25
3. Pro user uses area code → No extra charge
4. Area code matches → Success
5. Area code unavailable → Alternatives shown

Rentals:
6. Freemium user tries area code → Blocked
7. PAYG user uses area code → Charged $0.50
8. Pro user uses area code → No extra charge
9. Area code matches → Success
10. Area code unavailable → Alternatives shown
```

---

## 📊 Success Metrics

### Week 1 (Voice)
- [ ] 0 critical errors
- [ ] >80% area code match rate
- [ ] >30% adoption by eligible users
- [ ] <5 support tickets

### Week 2 (Rentals)
- [ ] 0 critical errors
- [ ] >85% area code match rate
- [ ] >25% adoption by eligible users
- [ ] <3 support tickets

### Month 1
- [ ] Voice revenue: $1,000+ from fees
- [ ] Rental revenue: $300+ from fees
- [ ] Tier upgrades: 5+ conversions
- [ ] User satisfaction: >4.5/5

---

## 🚨 Rollback Plan

### If Critical Issues Found
1. **Immediate**: Disable area code option via feature flag
2. **Within 1h**: Revert deployment
3. **Within 4h**: Fix issue and redeploy
4. **Within 24h**: Post-mortem and prevention plan

### Feature Flags
```python
# config.py
VOICE_AREA_CODE_ENABLED = os.getenv("VOICE_AREA_CODE_ENABLED", "true") == "true"
RENTAL_AREA_CODE_ENABLED = os.getenv("RENTAL_AREA_CODE_ENABLED", "true") == "true"
```

---

## 📁 File Checklist

### Backend (6 files)
- [ ] `app/services/verification_service.py` - Add calculate_voice_cost()
- [ ] `app/services/rental_service.py` - Add calculate_rental_cost()
- [ ] `app/services/textverified_service.py` - Add area_code to create_reservation()
- [ ] `app/api/core/verification.py` - Add tier validation
- [ ] `app/api/core/rentals.py` - Add tier validation
- [ ] `app/models/subscription_tier.py` - Verify has_area_code_selection field

### Frontend (2 files)
- [ ] `templates/voice_verify_modern.html` - Add tier checks
- [ ] `templates/rentals.html` - Add area code UI

### Tests (4 files)
- [ ] `tests/unit/test_voice_area_code_gating.py` - New
- [ ] `tests/unit/test_rental_area_code_gating.py` - New
- [ ] `tests/integration/test_voice_area_code_flow.py` - New
- [ ] `tests/integration/test_rental_area_code_flow.py` - New

### Documentation (3 files)
- [ ] `docs/API.md` - Update with tier requirements
- [ ] `docs/PRICING.md` - Update with area code fees
- [ ] `docs/FAQ.md` - Add tier restriction info

---

## 🎯 Definition of Done

**Voice Verification**:
- ✅ All acceptance criteria met
- ✅ All tests passing
- ✅ Code reviewed
- ✅ Deployed to production
- ✅ Monitored for 24h
- ✅ Documentation updated
- ✅ No critical issues

**Rentals**:
- ✅ All acceptance criteria met
- ✅ All tests passing
- ✅ Code reviewed
- ✅ Deployed to production
- ✅ Monitored for 24h
- ✅ Documentation updated
- ✅ No critical issues

---

## 📞 Quick Reference

**Start Implementation**:
```bash
# Create feature branch
git checkout -b feature/area-code-tier-gating

# Start with voice verification
# Follow Phase 1 (Days 1-5)

# Then implement rentals
# Follow Phase 2 (Days 1-5)
```

**Run Tests**:
```bash
# Unit tests
pytest tests/unit/test_voice_area_code_gating.py -v
pytest tests/unit/test_rental_area_code_gating.py -v

# Integration tests
pytest tests/integration/test_voice_area_code_flow.py -v
pytest tests/integration/test_rental_area_code_flow.py -v

# All tests
pytest tests/ -k "area_code" -v
```

**Deploy**:
```bash
# Staging
git push origin feature/area-code-tier-gating
# Deploy via CI/CD to staging

# Production (after testing)
git checkout main
git merge feature/area-code-tier-gating
git push origin main
# Deploy via CI/CD to production
```

---

**Status**: 🎯 Ready for Implementation
**Next Action**: Start Phase 1, Day 1 (Backend)
**Estimated Completion**: 2 weeks from start
