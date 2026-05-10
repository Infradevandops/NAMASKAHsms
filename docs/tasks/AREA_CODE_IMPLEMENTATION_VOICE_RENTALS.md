# Area Code Implementation - Voice & Rentals (Tier-Gated)

**Version**: v4.6.1
**Date**: May 10, 2026
**Status**: 📋 Planning
**Priority**: HIGH (Voice), MEDIUM (Rentals)

---

## 🎯 Objective

Implement stable, tier-gated area code selection for:
1. **Voice Verification** (Complete existing implementation)
2. **Rentals** (New feature)

Both features should follow the same patterns as SMS verification with proper tier gating.

---

## 📊 Current Status

### SMS Verification ✅
- **Status**: Fully implemented and stable
- **Tier Gating**: Pay-As-You-Go+ ($0.25 fee)
- **Features**: Area code selection, availability check, alternatives
- **Success Rate**: 85-95%

### Voice Verification ⚠️
- **Status**: UI implemented, needs backend completion
- **Tier Gating**: Not implemented
- **Features**: Area code dropdown exists, no gating
- **Provider Support**: ✅ Confirmed (API signature)

### Rentals ❌
- **Status**: Not implemented
- **Tier Gating**: Not implemented
- **Features**: None
- **Provider Support**: ✅ Confirmed (API signature)

---

## 🎯 Tier Gating Strategy

### Current Tier Structure

| Tier | Monthly | Area Code | ISP Filter | API Access |
|------|---------|-----------|------------|------------|
| **Freemium** | $0 | ❌ | ❌ | ❌ |
| **Pay-As-You-Go** | $0 | ✅ +$0.25 | ❌ | ✅ |
| **Pro** | $25 | ✅ Included | ✅ Included | ✅ |
| **Custom** | $35 | ✅ Included | ✅ Included | ✅ |

### Proposed Gating Rules

#### Voice Verification
```
Freemium:  ❌ No area code option (any available number)
PAYG:      ✅ Area code selection (+$0.25 per verification)
Pro:       ✅ Area code included (no extra fee)
Custom:    ✅ Area code included (no extra fee)
```

#### Rentals
```
Freemium:  ❌ No area code option (any available number)
PAYG:      ✅ Area code selection (+$0.50 per rental)
Pro:       ✅ Area code included (no extra fee)
Custom:    ✅ Area code included (no extra fee)
```

**Rationale**:
- Rentals have higher base cost → higher area code fee for PAYG
- Pro/Custom tiers get area code included (premium feature)
- Freemium gets basic service only (no filtering)

---

## 📋 Implementation Tasks

### Phase 1: Voice Verification (HIGH Priority)

#### Task 1.1: Backend - Tier Gating Logic ✅
**File**: `app/services/verification_service.py`

```python
async def calculate_voice_cost(
    self,
    user: User,
    service: str,
    area_code: Optional[str] = None,
) -> Dict[str, Any]:
    """Calculate voice verification cost with tier-aware pricing."""

    # Get base cost from provider
    base_cost = await self.textverified.get_service_price(service, "voice")

    # Get user tier
    tier = user.subscription_tier or "freemium"

    # Area code fee logic
    area_code_fee = 0.0
    if area_code:
        if tier == "freemium":
            raise PermissionError("Area code selection requires Pay-As-You-Go or higher")
        elif tier == "payg":
            area_code_fee = 0.25  # PAYG pays per use
        # Pro and Custom: included (no fee)

    total_cost = base_cost + area_code_fee

    return {
        "base_cost": base_cost,
        "area_code_fee": area_code_fee,
        "total_cost": total_cost,
        "tier": tier,
    }
```

#### Task 1.2: Frontend - Tier Gating UI ✅
**File**: `templates/voice_verify_modern.html`

```javascript
// Check user tier on page load
async function checkUserTier() {
    const res = await fetch('/api/auth/me', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
    });
    const user = await res.json();
    const tier = user.subscription_tier || 'freemium';

    // Show/hide advanced options based on tier
    const advancedOptions = document.getElementById('voice-advanced-options');

    if (tier === 'freemium') {
        advancedOptions.style.display = 'none';
        // Show upgrade prompt
        showUpgradePrompt('Area code selection requires Pay-As-You-Go or higher');
    } else {
        advancedOptions.style.display = 'block';

        // Show fee for PAYG
        if (tier === 'payg') {
            document.getElementById('area-code-fee-notice').textContent = '+$0.25 per verification';
        } else {
            document.getElementById('area-code-fee-notice').textContent = 'Included in your plan';
        }
    }
}
```

#### Task 1.3: Pricing Display ✅
**File**: `templates/voice_verify_modern.html`

```html
<!-- Pricing breakdown -->
<div class="pricing-row">
    <span class="pricing-label">Base Cost</span>
    <span class="pricing-value" id="pricing-base">$3.50</span>
</div>

<div class="pricing-row" id="area-code-fee-row" style="display:none;">
    <span class="pricing-label">
        Area Code Filter
        <span class="tier-badge">PAYG</span>
    </span>
    <span class="pricing-value" id="pricing-area-filter">$0.25</span>
</div>

<div class="pricing-row">
    <span class="pricing-label">Total Cost</span>
    <span class="pricing-value" id="pricing-total">$3.75</span>
</div>
```

#### Task 1.4: API Endpoint Updates ✅
**File**: `app/api/core/verification.py`

```python
@router.post("/request")
async def create_verification(
    request: VerificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create verification with tier-aware area code gating."""

    # Validate tier permissions
    if request.area_codes and current_user.subscription_tier == "freemium":
        raise HTTPException(
            status_code=403,
            detail="Area code selection requires Pay-As-You-Go or higher tier"
        )

    # Calculate cost with tier-aware pricing
    cost_breakdown = await verification_service.calculate_voice_cost(
        user=current_user,
        service=request.service,
        area_code=request.area_codes[0] if request.area_codes else None,
    )

    # Check balance
    if current_user.credits < cost_breakdown["total_cost"]:
        raise HTTPException(status_code=402, detail="Insufficient balance")

    # Create verification
    result = await textverified_service.create_verification(
        service=request.service,
        area_code=request.area_codes[0] if request.area_codes else None,
        capability="voice",
    )

    # Deduct cost
    await wallet_service.deduct_credits(
        user=current_user,
        amount=cost_breakdown["total_cost"],
        description=f"Voice verification: {request.service}",
    )

    return result
```

---

### Phase 2: Rentals (MEDIUM Priority)

#### Task 2.1: Backend - Add Area Code Support ✅
**File**: `app/services/textverified_service.py`

```python
async def create_reservation(
    self,
    service: str,
    country: str = "US",
    duration_hours: float = 24.0,
    area_code: Optional[str] = None,  # ← Add this
) -> Dict[str, Any]:
    """Create a long-term reservation (rental) for a service."""
    if not self.enabled:
        raise RuntimeError("TextVerified service disabled")

    try:
        duration_minutes = int(duration_hours * 60)

        # Build area code preference if provided
        area_code_options: Optional[List[str]] = None
        if area_code:
            area_code_options = await self._build_area_code_preference(area_code)
            logger.info(
                f"Rental area code preference chain for {area_code}: "
                f"{area_code_options[:5]}... ({len(area_code_options)} options)"
            )

        reservation = await asyncio.to_thread(
            self.client.reservations.create,
            service_name=service,
            duration=duration_minutes,
            area_code_select_option=area_code_options,  # ← Add this
        )

        # Check if area code matched
        assigned_number = reservation.number
        assigned_area_code = (
            assigned_number[2:5] if assigned_number.startswith("+1") else None
        )
        area_code_matched = (
            assigned_area_code == area_code if area_code else None
        )

        return {
            "id": reservation.id,
            "phone_number": reservation.number,
            "cost": float(reservation.total_cost),
            "ends_at": reservation.ends_at,
            "status": reservation.state.value,
            "tv_object": reservation,
            "requested_area_code": area_code,
            "assigned_area_code": assigned_area_code,
            "area_code_matched": area_code_matched,
        }
    except Exception as e:
        logger.error(f"TextVerified reservation creation failed: {e}")
        raise
```

#### Task 2.2: Backend - Tier Gating for Rentals ✅
**File**: `app/services/rental_service.py`

```python
async def calculate_rental_cost(
    self,
    user: User,
    service: str,
    duration_hours: float,
    area_code: Optional[str] = None,
) -> Dict[str, Any]:
    """Calculate rental cost with tier-aware pricing."""

    # Get base cost from provider
    base_cost = await self.textverified.get_rental_price(service, duration_hours)

    # Get user tier
    tier = user.subscription_tier or "freemium"

    # Area code fee logic
    area_code_fee = 0.0
    if area_code:
        if tier == "freemium":
            raise PermissionError("Area code selection requires Pay-As-You-Go or higher")
        elif tier == "payg":
            area_code_fee = 0.50  # Higher fee for rentals
        # Pro and Custom: included (no fee)

    total_cost = base_cost + area_code_fee

    return {
        "base_cost": base_cost,
        "area_code_fee": area_code_fee,
        "total_cost": total_cost,
        "tier": tier,
    }
```

#### Task 2.3: Frontend - Rentals UI with Area Code ✅
**File**: `templates/rentals.html`

```html
<!-- Advanced Options (matching voice verification) -->
<div id="rental-advanced-options" style="margin-top: var(--spacing-md);">
    <div style="cursor: pointer; display: flex; align-items: center; gap: 8px; padding: 12px; background: rgba(102, 126, 234, 0.05); border-radius: 8px; margin-bottom: 12px;" onclick="toggleRentalAdvanced()">
        <span id="rental-advanced-icon" style="transition: transform 0.2s;">▶</span>
        <span style="font-weight: 600; font-size: 14px;">Advanced Options</span>
        <span class="premium-badge" style="margin-left: auto;">PREMIUM</span>
    </div>
    <div id="rental-advanced-body" style="display: none;">
        <!-- Area Code Selection -->
        <div class="form-group">
            <label class="form-label">
                Area Code
                <span style="font-size: 11px; color: var(--text-muted); font-weight: 400; margin-left: 4px;">(Optional)</span>
            </label>
            <select class="form-select" id="rental-area-code-select" onchange="checkRentalAreaCode(this.value)">
                <option value="">Any Area Code (Fastest)</option>
            </select>
            <div id="rental-ac-status" style="margin-top: 8px; font-size: 13px;"></div>
            <div id="rental-ac-alternatives" style="margin-top: 8px;"></div>
        </div>
    </div>
</div>

<!-- Pricing with Area Code Fee -->
<div class="pricing-row">
    <span class="pricing-label">Base Cost</span>
    <span class="pricing-value" id="rental-pricing-base">$15.00</span>
</div>

<div class="pricing-row" id="rental-area-code-fee-row" style="display:none;">
    <span class="pricing-label">
        Area Code Filter
        <span class="tier-badge">PAYG</span>
    </span>
    <span class="pricing-value" id="rental-pricing-area-filter">$0.50</span>
</div>

<div class="pricing-row">
    <span class="pricing-label">Total Cost</span>
    <span class="pricing-value" id="rental-pricing-total">$15.50</span>
</div>
```

#### Task 2.4: API Endpoint for Rentals ✅
**File**: `app/api/core/rentals.py`

```python
@router.post("/create")
async def create_rental(
    request: RentalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create rental with tier-aware area code gating."""

    # Validate tier permissions
    if request.area_code and current_user.subscription_tier == "freemium":
        raise HTTPException(
            status_code=403,
            detail="Area code selection requires Pay-As-You-Go or higher tier"
        )

    # Calculate cost with tier-aware pricing
    cost_breakdown = await rental_service.calculate_rental_cost(
        user=current_user,
        service=request.service,
        duration_hours=request.duration_hours,
        area_code=request.area_code,
    )

    # Check balance
    if current_user.credits < cost_breakdown["total_cost"]:
        raise HTTPException(status_code=402, detail="Insufficient balance")

    # Create rental
    result = await textverified_service.create_reservation(
        service=request.service,
        duration_hours=request.duration_hours,
        area_code=request.area_code,
    )

    # Deduct cost
    await wallet_service.deduct_credits(
        user=current_user,
        amount=cost_breakdown["total_cost"],
        description=f"Rental: {request.service} ({request.duration_hours}h)",
    )

    return result
```

---

## 🧪 Testing Strategy

### Unit Tests

```python
# tests/unit/test_voice_area_code_gating.py

class TestVoiceAreaCodeGating:
    """Test tier gating for voice verification area codes."""

    async def test_freemium_cannot_use_area_code(self):
        """Freemium users cannot select area codes."""
        user = create_user(tier="freemium")

        with pytest.raises(PermissionError):
            await verification_service.calculate_voice_cost(
                user=user,
                service="google",
                area_code="213",
            )

    async def test_payg_pays_area_code_fee(self):
        """PAYG users pay $0.25 for area code."""
        user = create_user(tier="payg")

        cost = await verification_service.calculate_voice_cost(
            user=user,
            service="google",
            area_code="213",
        )

        assert cost["area_code_fee"] == 0.25
        assert cost["total_cost"] == cost["base_cost"] + 0.25

    async def test_pro_area_code_included(self):
        """Pro users get area code included."""
        user = create_user(tier="pro")

        cost = await verification_service.calculate_voice_cost(
            user=user,
            service="google",
            area_code="213",
        )

        assert cost["area_code_fee"] == 0.0
        assert cost["total_cost"] == cost["base_cost"]

    async def test_custom_area_code_included(self):
        """Custom users get area code included."""
        user = create_user(tier="custom")

        cost = await verification_service.calculate_voice_cost(
            user=user,
            service="google",
            area_code="213",
        )

        assert cost["area_code_fee"] == 0.0
        assert cost["total_cost"] == cost["base_cost"]


# tests/unit/test_rental_area_code_gating.py

class TestRentalAreaCodeGating:
    """Test tier gating for rental area codes."""

    async def test_freemium_cannot_use_area_code(self):
        """Freemium users cannot select area codes for rentals."""
        user = create_user(tier="freemium")

        with pytest.raises(PermissionError):
            await rental_service.calculate_rental_cost(
                user=user,
                service="google",
                duration_hours=24.0,
                area_code="213",
            )

    async def test_payg_pays_higher_fee_for_rentals(self):
        """PAYG users pay $0.50 for rental area code."""
        user = create_user(tier="payg")

        cost = await rental_service.calculate_rental_cost(
            user=user,
            service="google",
            duration_hours=24.0,
            area_code="213",
        )

        assert cost["area_code_fee"] == 0.50
        assert cost["total_cost"] == cost["base_cost"] + 0.50

    async def test_pro_rental_area_code_included(self):
        """Pro users get rental area code included."""
        user = create_user(tier="pro")

        cost = await rental_service.calculate_rental_cost(
            user=user,
            service="google",
            duration_hours=24.0,
            area_code="213",
        )

        assert cost["area_code_fee"] == 0.0
        assert cost["total_cost"] == cost["base_cost"]
```

### Integration Tests

```python
# tests/integration/test_voice_area_code_flow.py

async def test_voice_verification_with_area_code_payg():
    """Test complete voice verification flow with area code (PAYG user)."""
    # Create PAYG user with balance
    user = create_user(tier="payg", credits=10.0)

    # Create verification with area code
    response = await client.post(
        "/api/verification/request",
        json={
            "service": "google",
            "country": "US",
            "capability": "voice",
            "area_codes": ["213"]
        },
        headers={"Authorization": f"Bearer {user.token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Verify area code was requested
    assert data["requested_area_code"] == "213"

    # Verify cost includes area code fee
    # Base: $3.50, Area code: $0.25 = $3.75
    assert data["cost"] == 3.75


async def test_rental_with_area_code_pro():
    """Test complete rental flow with area code (Pro user)."""
    # Create Pro user with balance
    user = create_user(tier="pro", credits=20.0)

    # Create rental with area code
    response = await client.post(
        "/api/rentals/create",
        json={
            "service": "google",
            "duration_hours": 24.0,
            "area_code": "213"
        },
        headers={"Authorization": f"Bearer {user.token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Verify area code was requested
    assert data["requested_area_code"] == "213"

    # Verify no area code fee (included in Pro)
    assert "area_code_fee" not in data or data["area_code_fee"] == 0.0
```

---

## 📊 Success Metrics

### Voice Verification
- **Area code match rate**: >80% (PAYG/Pro/Custom)
- **User adoption**: 40% of eligible users use area code
- **Support tickets**: <5% related to area code issues
- **Revenue impact**: +$0.25 per PAYG verification with area code

### Rentals
- **Area code match rate**: >85% (longer duration = better inventory)
- **User adoption**: 30% of eligible users use area code
- **Support tickets**: <3% related to area code issues
- **Revenue impact**: +$0.50 per PAYG rental with area code

---

## 🚀 Deployment Plan

### Phase 1: Voice (Week 1)
- **Day 1-2**: Implement tier gating backend
- **Day 3**: Update frontend with tier checks
- **Day 4**: Write and run tests
- **Day 5**: Deploy to staging
- **Day 6-7**: Test and monitor

### Phase 2: Rentals (Week 2)
- **Day 1-2**: Implement backend area code support
- **Day 3**: Build rentals UI with area code
- **Day 4**: Write and run tests
- **Day 5**: Deploy to staging
- **Day 6-7**: Test and monitor

### Phase 3: Production (Week 3)
- **Day 1**: Deploy voice to production
- **Day 2-3**: Monitor voice metrics
- **Day 4**: Deploy rentals to production
- **Day 5-7**: Monitor rentals metrics

---

## 📝 Documentation Updates

### User-Facing
- Update pricing page with area code fees
- Add tier comparison table
- Create "How to use area codes" guide
- Update FAQ with tier restrictions

### Developer-Facing
- Update API documentation
- Add tier gating examples
- Document pricing calculations
- Update integration guides

---

## 🎯 Acceptance Criteria

### Voice Verification ✅
- [ ] Freemium users cannot access area code option
- [ ] PAYG users see +$0.25 fee for area code
- [ ] Pro/Custom users see "Included" for area code
- [ ] Pricing updates dynamically based on tier
- [ ] API enforces tier restrictions
- [ ] Tests passing (unit + integration)
- [ ] Documentation updated

### Rentals ✅
- [ ] Freemium users cannot access area code option
- [ ] PAYG users see +$0.50 fee for area code
- [ ] Pro/Custom users see "Included" for area code
- [ ] Pricing updates dynamically based on tier
- [ ] API enforces tier restrictions
- [ ] Tests passing (unit + integration)
- [ ] Documentation updated

---

## 🔒 Security Considerations

1. **Tier Validation**: Always validate tier on backend (never trust frontend)
2. **Balance Checks**: Verify sufficient balance before creating verification/rental
3. **Rate Limiting**: Apply tier-specific rate limits
4. **Audit Logging**: Log all area code usage for billing verification
5. **Error Handling**: Don't expose tier logic in error messages

---

## 💰 Revenue Impact

### Projected Monthly Revenue (1000 users)

**Voice Verification**:
- PAYG users (40%): 400 users × 10 verifications/mo × $0.25 = $1,000/mo
- Pro upgrades: 5% conversion × 400 users × $25/mo = $500/mo
- **Total**: $1,500/mo

**Rentals**:
- PAYG users (30%): 300 users × 2 rentals/mo × $0.50 = $300/mo
- Pro upgrades: 3% conversion × 300 users × $25/mo = $225/mo
- **Total**: $525/mo

**Combined Impact**: $2,025/mo additional revenue

---

## 📞 Support Plan

### Common Issues
1. "Why can't I select area code?" → Tier restriction, show upgrade path
2. "Area code didn't match" → Explain inventory limitations, offer alternatives
3. "Extra fee for area code?" → Explain PAYG pricing, suggest Pro upgrade

### Upgrade Prompts
- Show upgrade CTA when freemium user clicks area code
- Highlight savings for Pro users (area code included)
- Track conversion rate from upgrade prompts

---

**Status**: 📋 Ready for Implementation
**Estimated Effort**: 2 weeks (1 week voice, 1 week rentals)
**Priority**: HIGH (Voice), MEDIUM (Rentals)
**Dependencies**: None (provider support confirmed)
