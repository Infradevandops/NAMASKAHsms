# TextVerified Alignment - Execution Checklist

**Version**: 1.0  
**Date**: March 14, 2026  
**Status**: Ready for Execution  
**Total Effort**: 60-80 hours over 3-4 weeks

---

## 📋 Quick Navigation

- **[Milestone 1: Stop the Bleeding](#milestone-1-stop-the-bleeding)** (Days 1-3) - CRITICAL
- **[Milestone 2: Data Integrity](#milestone-2-data-integrity)** (Days 4-7)
- **[Milestone 3: Align Carrier List](#milestone-3-align-carrier-list)** (Days 8-12)
- **[Milestone 4: Pricing Alignment](#milestone-4-pricing-alignment)** (Days 13-16)
- **[Milestone 5: Observability](#milestone-5-observability)** (Days 17-20)

---

## 🎯 Milestone 1: Stop the Bleeding (Days 1-3)

### ✅ Task 1.1: Fix Carrier Validation Logic

**Priority**: 🔥 CRITICAL  
**Effort**: 2 hours  
**Owner**: Backend Engineer  
**Status**: [ ] Not Started [ ] In Progress [ ] Complete

#### Step 1: Backup Current Code
```bash
# Create backup branch
git checkout -b backup/carrier-validation-$(date +%Y%m%d)
git push origin backup/carrier-validation-$(date +%Y%m%d)

# Verify current state
grep -n "is_mobile_fallback" app/api/verification/purchase_endpoints.py
```

**Checklist**:
- [ ] Backup branch created
- [ ] Current code reviewed and understood

#### Step 2: Remove Strict Carrier Validation

**File**: `app/api/verification/purchase_endpoints.py`

**Find and Replace** (Lines 223-248):

```python
# FIND THIS:
            # Step 2.1: CRITICAL CARRIER VALIDATION (Task 2.3)
            # If user requested a specific carrier, verify the assigned carrier matches
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
                     logger.warning(...)
                     try:
                         await tv_service.cancel_verification(textverified_result["id"])
                     except Exception as cancel_error:
                         logger.error(...)
                     logger.info(...)
                     raise HTTPException(...)
                 elif is_mobile_fallback:
                     logger.info(...)

# REPLACE WITH THIS:
            # Step 2.1: CARRIER PREFERENCE LOGGING (TextVerified best-effort)
            # TextVerified treats carrier as a preference, not a guarantee
            if carrier:
                assigned_carrier = textverified_result.get("assigned_carrier")
                logger.info(
                    f"Carrier preference applied: requested={carrier}, "
                    f"assigned_type={assigned_carrier} (TextVerified best-effort, not guaranteed)"
                )
                # No validation — TextVerified returns generic types, not specific carriers
```

**Checklist**:
- [ ] Old validation block removed
- [ ] New logging added
- [ ] File saved

#### Step 3: Mark Carrier Extraction as Deprecated

**File**: `app/services/textverified_service.py`

**Find and Update** (method `_extract_carrier_from_number`):

```python
# BEFORE:
def _extract_carrier_from_number(self, phone_number: str) -> Optional[str]:
    """Extract carrier from phone number.
    Priority 1.6: Basic implementation for US mobile numbers.
    """
    if not phone_number:
        return None
    clean = str(phone_number).replace("+", "").replace("-", "").replace(" ", "")
    if len(clean) >= 10:
        return "Mobile"
    return "Unknown"

# AFTER:
def _extract_carrier_from_number(self, phone_number: str) -> Optional[str]:
    """DEPRECATED: TextVerified does not return specific carrier info.
    
    This method always returns 'Mobile' for valid US numbers because TextVerified's
    API response does not include specific carrier information. Do not use this for
    carrier validation or decision-making.
    
    See: docs/TEXTVERIFIED_CARRIER_ANALYSIS.md
    """
    if not phone_number:
        return None
    clean = str(phone_number).replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
    if len(clean) >= 10:
        return "Mobile"  # Always returns "Mobile" — TextVerified doesn't provide specific carrier
    return "Unknown"
```

**Checklist**:
- [ ] Deprecation notice added
- [ ] Comments updated
- [ ] File saved

#### Step 4: Run Tests

```bash
# Run unit tests for verification module
pytest tests/unit/test_verification_service.py -v

# Run integration tests
pytest tests/integration/test_carrier_verification.py -v

# Check for regressions
pytest tests/ -k "carrier" -v
```

**Checklist**:
- [ ] All tests pass
- [ ] No new failures introduced
- [ ] Coverage maintained or improved

#### Step 5: Manual Testing

```bash
# Start local server
python -m uvicorn main:app --reload

# Test 1: Create verification with carrier=verizon
curl -X POST http://localhost:8000/api/verification/request \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service": "telegram",
    "country": "US",
    "carriers": ["verizon"]
  }'

# Expected: 201 Created (not 409 Conflict)

# Test 2: Create verification with carrier=us_cellular
curl -X POST http://localhost:8000/api/verification/request \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service": "discord",
    "country": "US",
    "carriers": ["us_cellular"]
  }'

# Expected: 201 Created (not 409 Conflict)

# Test 3: Check logs for carrier preference message
tail -f logs/app.log | grep "Carrier preference applied"
```

**Checklist**:
- [ ] Test 1 passes (verizon carrier)
- [ ] Test 2 passes (us_cellular carrier)
- [ ] Test 3 shows correct log message
- [ ] No 409 errors in logs

#### Step 6: Commit and Push

```bash
git add app/api/verification/purchase_endpoints.py
git add app/services/textverified_service.py
git commit -m "fix(carrier): remove strict validation, accept TextVerified best-effort

- Remove post-purchase carrier validation that was causing 409 Conflict errors
- TextVerified returns generic types (Mobile) not specific carriers
- Carrier selection is now treated as preference, not guarantee
- Add deprecation notice to _extract_carrier_from_number()
- Log carrier preference for analytics

Fixes: #ISSUE_NUMBER
Related: docs/TEXTVERIFIED_CARRIER_ANALYSIS.md"

git push origin feature/carrier-validation-fix
```

**Checklist**:
- [ ] Commit message is clear and references issue
- [ ] Code pushed to feature branch
- [ ] Ready for PR review

---

### ✅ Task 1.2: Fix Service Loading Error Recovery

**Priority**: 🔥 CRITICAL  
**Effort**: 3 hours  
**Owner**: Frontend Engineer  
**Status**: [ ] Not Started [ ] In Progress [ ] Complete

#### Step 1: Identify Service Loading Code

```bash
# Find service loading logic
grep -r "Services unavailable" templates/
grep -r "No results found" templates/
grep -r "services_list" static/js/
```

**Checklist**:
- [ ] Service loading code located
- [ ] Error handling identified

#### Step 2: Add Error State Handling

**File**: `templates/verify_modern.html` (or relevant template)

**Add Error State**:
```html
<!-- Add to modal -->
<div id="service-error-state" style="display: none;">
  <div class="error-container">
    <h3>⚠️ Unable to Load Services</h3>
    <p>We couldn't connect to our SMS provider. Please try again.</p>
    <button id="retry-services-btn" class="btn btn-primary">
      🔄 Retry
    </button>
  </div>
</div>

<!-- Update service input -->
<input 
  type="text" 
  id="service-input" 
  placeholder="Select service..."
  disabled
  data-error-state="false"
/>
```

**Checklist**:
- [ ] Error state HTML added
- [ ] Retry button added
- [ ] Input disabled state added

#### Step 3: Add JavaScript Error Handling

**File**: `static/js/verification-modal.js` (or relevant JS file)

```javascript
// Add to verification modal initialization
class VerificationModal {
  constructor() {
    this.servicesLoaded = false;
    this.initializeErrorHandling();
  }
  
  initializeErrorHandling() {
    const serviceInput = document.getElementById('service-input');
    const retryBtn = document.getElementById('retry-services-btn');
    const errorState = document.getElementById('service-error-state');
    
    // Prevent modal open when services not loaded
    serviceInput.addEventListener('click', (e) => {
      if (!this.servicesLoaded) {
        e.preventDefault();
        this.showErrorState();
        return false;
      }
      this.openModal();
    });
    
    // Retry button
    retryBtn.addEventListener('click', async () => {
      await this.loadServices();
    });
  }
  
  showErrorState() {
    const errorState = document.getElementById('service-error-state');
    const serviceInput = document.getElementById('service-input');
    
    errorState.style.display = 'block';
    serviceInput.style.cursor = 'not-allowed';
    serviceInput.style.opacity = '0.5';
    serviceInput.setAttribute('data-error-state', 'true');
    
    // Show toast notification
    this.showToast('Services unavailable. Please try again.', 'error');
  }
  
  hideErrorState() {
    const errorState = document.getElementById('service-error-state');
    const serviceInput = document.getElementById('service-input');
    
    errorState.style.display = 'none';
    serviceInput.style.cursor = 'pointer';
    serviceInput.style.opacity = '1';
    serviceInput.setAttribute('data-error-state', 'false');
  }
  
  async loadServices() {
    try {
      const response = await fetch('/api/verification/services');
      const data = await response.json();
      
      if (!data.services || data.services.length === 0) {
        throw new Error('No services returned');
      }
      
      this.services = data.services;
      this.servicesLoaded = true;
      this.hideErrorState();
      this.showToast('Services loaded successfully', 'success');
      
    } catch (error) {
      console.error('Failed to load services:', error);
      this.servicesLoaded = false;
      this.showErrorState();
    }
  }
  
  showToast(message, type = 'info') {
    // Implementation depends on your toast library
    console.log(`[${type.toUpperCase()}] ${message}`);
  }
}
```

**Checklist**:
- [ ] Error state JavaScript added
- [ ] Retry logic implemented
- [ ] Input disabled when services not loaded
- [ ] Toast notifications added

#### Step 4: Hide Filter Settings on Error

**File**: `templates/verify_modern.html`

```html
<!-- Update filter settings button -->
<button 
  id="filter-settings-btn" 
  class="btn btn-settings"
  style="display: none;"
>
  ⚙️ Filters
</button>
```

**JavaScript**:
```javascript
// In VerificationModal class
hideErrorState() {
  // ... existing code ...
  
  // Hide filter settings
  const filterBtn = document.getElementById('filter-settings-btn');
  filterBtn.style.display = 'none';
}

hideErrorState() {
  // ... existing code ...
  
  // Show filter settings
  const filterBtn = document.getElementById('filter-settings-btn');
  filterBtn.style.display = 'block';
}
```

**Checklist**:
- [ ] Filter button hidden on error
- [ ] Filter button shown on success

#### Step 5: Test Error Recovery

```bash
# Test 1: Simulate API failure
# Temporarily break the services endpoint and verify error state shows

# Test 2: Verify retry works
# Click retry button and verify services load

# Test 3: Verify input is disabled
# Check that clicking input shows error toast

# Test 4: Verify filter button hidden
# Confirm filter settings button is hidden during error state
```

**Checklist**:
- [ ] Error state displays correctly
- [ ] Retry button works
- [ ] Input disabled state works
- [ ] Filter button hidden/shown correctly

#### Step 6: Commit and Push

```bash
git add templates/verify_modern.html
git add static/js/verification-modal.js
git commit -m "fix(ui): add error recovery for service loading failures

- Prevent modal open when services fail to load
- Add error state with retry button
- Disable service input during error state
- Hide filter settings when services unavailable
- Show user-friendly error messages

Fixes: #ISSUE_NUMBER"

git push origin feature/service-loading-error-recovery
```

**Checklist**:
- [ ] Changes committed
- [ ] Code pushed to feature branch
- [ ] Ready for PR review

---

### ✅ Task 1.3: Honest Carrier UX — Rename to "Prefer Carrier"

**Priority**: 🟡 MEDIUM  
**Effort**: 1.5 hours  
**Owner**: Frontend + Backend Engineer  
**Status**: [ ] Not Started [ ] In Progress [ ] Complete

#### Step 1: Update Frontend Labels

**File**: `templates/verify_modern.html`

```html
<!-- BEFORE -->
<label>Carrier Filter</label>

<!-- AFTER -->
<label>Carrier Preference</label>
```

**Add Tooltip**:
```html
<div class="filter-info">
  <i class="info-icon" title="We'll request this carrier from our provider. Subject to availability.">ℹ️</i>
  <span class="tooltip-text">
    We'll try to get your preferred carrier, but availability varies. 
    You may receive a number from a different carrier.
  </span>
</div>
```

**Checklist**:
- [ ] Label changed to "Carrier Preference"
- [ ] Tooltip added
- [ ] Tooltip text is clear and honest

#### Step 2: Update Backend API Response

**File**: `app/api/verification/carrier_endpoints.py`

```python
@router.get("/carriers/{country}")
async def get_available_carriers(country: str, ...):
    # ... existing code ...
    
    carriers = [
        {
            "id": "verizon",
            "name": "Verizon",
            "guarantee": False,  # Add this
            "type": "preference",  # Add this
        },
        # ... other carriers ...
    ]
    
    return {
        "success": True,
        "country": country,
        "carriers": carriers,
        "note": "Carrier selection is a preference, not a guarantee",  # Add this
    }
```

**Checklist**:
- [ ] `guarantee: false` added to all carriers
- [ ] `type: "preference"` added
- [ ] Note added to response

#### Step 3: Update Documentation

**File**: `docs/CARRIER_QUICK_REFERENCE.md` (already exists, just verify)

**Verify Contains**:
- [ ] "Carrier Preference" terminology used
- [ ] "Best effort" language used
- [ ] Clear explanation of what TextVerified returns

#### Step 4: Test Changes

```bash
# Test 1: Check API response
curl http://localhost:8000/api/verification/carriers/US | jq '.carriers[0]'

# Expected output includes:
# "guarantee": false
# "type": "preference"

# Test 2: Check frontend displays correctly
# Open verification modal and verify:
# - Label says "Carrier Preference"
# - Tooltip appears on hover
# - Tooltip text is clear
```

**Checklist**:
- [ ] API response includes guarantee and type fields
- [ ] Frontend displays "Carrier Preference" label
- [ ] Tooltip displays correctly
- [ ] Tooltip text is clear

#### Step 5: Commit and Push

```bash
git add templates/verify_modern.html
git add app/api/verification/carrier_endpoints.py
git commit -m "ux: rename 'Carrier Filter' to 'Carrier Preference' with honest messaging

- Change label from 'Carrier Filter' to 'Carrier Preference'
- Add tooltip explaining best-effort nature
- Add 'guarantee: false' to API response
- Add 'type: preference' to carrier objects
- Update documentation

Fixes: #ISSUE_NUMBER"

git push origin feature/honest-carrier-ux
```

**Checklist**:
- [ ] Changes committed
- [ ] Code pushed to feature branch
- [ ] Ready for PR review

---

## 🎯 Milestone 2: Data Integrity (Days 4-7)

### ✅ Task 2.1: Clean Up Verification Model

**Priority**: 🟡 MEDIUM  
**Effort**: 2 hours  
**Owner**: Backend Engineer  
**Status**: [ ] Not Started [ ] In Progress [ ] Complete

#### Step 1: Document Current State

```bash
# Check current operator field usage
grep -r "\.operator" app/ --include="*.py" | head -20

# Check verification model
grep -A 5 "operator = Column" app/models/verification.py
```

**Checklist**:
- [ ] Current usage documented
- [ ] Model structure understood

#### Step 2: Update Verification Record Creation

**File**: `app/api/verification/purchase_endpoints.py` (around line 260)

```python
# BEFORE:
verification = Verification(
    ...
    operator=textverified_result.get("assigned_carrier") or carrier,
    assigned_carrier=textverified_result.get("assigned_carrier"),
    ...
)

# AFTER:
verification = Verification(
    ...
    requested_carrier=carrier,  # What user asked for
    assigned_carrier=textverified_result.get("assigned_carrier"),  # What TV returned
    operator=carrier,  # Legacy field — keep for backward compatibility
    ...
)
```

**Checklist**:
- [ ] `requested_carrier` set correctly
- [ ] `assigned_carrier` set correctly
- [ ] `operator` kept for backward compatibility
- [ ] Comments added explaining fields

#### Step 3: Add Model Documentation

**File**: `app/models/verification.py`

```python
class Verification(BaseModel):
    """SMS/Voice verification model."""
    
    __tablename__ = "verifications"
    
    # ... existing fields ...
    
    requested_carrier = Column(String)  # What user requested (e.g., "verizon")
    assigned_carrier = Column(String)   # What TextVerified returned (e.g., "Mobile")
    operator = Column(String)           # DEPRECATED: Use requested_carrier or assigned_carrier instead
    
    # ... rest of model ...
```

**Checklist**:
- [ ] Comments added to model
- [ ] Deprecation notice on operator field
- [ ] Field purposes clear

#### Step 4: Test Data Integrity

```bash
# Create test verification with carrier
curl -X POST http://localhost:8000/api/verification/request \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"service": "telegram", "country": "US", "carriers": ["verizon"]}'

# Query database
sqlite3 namaskah.db "SELECT requested_carrier, assigned_carrier, operator FROM verifications ORDER BY created_at DESC LIMIT 1;"

# Expected output:
# verizon|Mobile|verizon
```

**Checklist**:
- [ ] Test verification created
- [ ] Database query shows correct values
- [ ] requested_carrier has user's selection
- [ ] assigned_carrier has TextVerified's response

#### Step 5: Commit and Push

```bash
git add app/api/verification/purchase_endpoints.py
git add app/models/verification.py
git commit -m "refactor: clean up verification model carrier fields

- Use requested_carrier for user's original selection
- Use assigned_carrier for TextVerified's response
- Keep operator field for backward compatibility
- Add documentation explaining field purposes
- Mark operator as deprecated

Fixes: #ISSUE_NUMBER"

git push origin feature/clean-verification-model
```

**Checklist**:
- [ ] Changes committed
- [ ] Code pushed to feature branch
- [ ] Ready for PR review

---

### ✅ Task 2.2: Fix Receipt Generation

**Priority**: 🟡 MEDIUM  
**Effort**: 1.5 hours  
**Owner**: Backend Engineer  
**Status**: [ ] Not Started [ ] In Progress [ ] Complete

#### Step 1: Find Receipt Generation Code

```bash
# Find where VerificationReceipt is created
grep -r "VerificationReceipt(" app/ --include="*.py"

# Find receipt generation logic
grep -r "isp_carrier" app/ --include="*.py"
```

**Checklist**:
- [ ] Receipt generation code located
- [ ] Current implementation understood

#### Step 2: Update Receipt Creation

**File**: (wherever VerificationReceipt is created)

```python
# BEFORE:
receipt = VerificationReceipt(
    ...
    area_code=verification.requested_area_code,
    isp_carrier=verification.requested_carrier,
    ...
)

# AFTER:
receipt = VerificationReceipt(
    ...
    area_code=verification.assigned_area_code or verification.requested_area_code,
    isp_carrier=verification.assigned_carrier or verification.requested_carrier,
    ...
)
```

**Checklist**:
- [ ] Receipt uses assigned values when available
- [ ] Falls back to requested values if assigned is null
- [ ] Logic is correct

#### Step 3: Test Receipt Generation

```bash
# Create verification with carrier and area code
curl -X POST http://localhost:8000/api/verification/request \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "service": "telegram",
    "country": "US",
    "carriers": ["verizon"],
    "area_codes": ["415"]
  }'

# Query receipt
sqlite3 namaskah.db "SELECT area_code, isp_carrier FROM verification_receipts ORDER BY created_at DESC LIMIT 1;"

# Expected: Shows assigned values, not requested values
```

**Checklist**:
- [ ] Test verification created
- [ ] Receipt shows assigned values
- [ ] Fallback to requested values works if assigned is null

#### Step 4: Commit and Push

```bash
git add app/services/receipt_service.py  # or wherever receipts are created
git commit -m "fix: show actual assigned values in receipts, not requested

- Use assigned_area_code and assigned_carrier in receipts
- Fall back to requested values if assigned is null
- Receipts now show what user actually received

Fixes: #ISSUE_NUMBER"

git push origin feature/fix-receipt-generation
```

**Checklist**:
- [ ] Changes committed
- [ ] Code pushed to feature branch
- [ ] Ready for PR review

---

### ✅ Task 2.3: Add Carrier Analytics Table

**Priority**: 🟡 MEDIUM  
**Effort**: 3 hours  
**Owner**: Backend Engineer  
**Status**: [ ] Not Started [ ] In Progress [ ] Complete

#### Step 1: Create Analytics Model

**New File**: `app/models/carrier_analytics.py`

```python
"""Carrier analytics model for tracking carrier preferences vs actual assignments."""

from sqlalchemy import Column, String, DateTime, Boolean, Integer
from app.models.base import BaseModel
from datetime import datetime, timezone


class CarrierAnalytics(BaseModel):
    """Track carrier preference requests and outcomes."""
    
    __tablename__ = "carrier_analytics"
    
    verification_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    requested_carrier = Column(String, nullable=False)  # What user asked for
    sent_to_textverified = Column(String, nullable=False)  # Normalized value sent to API
    textverified_response = Column(String)  # What TextVerified returned
    assigned_phone = Column(String)  # Phone number assigned
    assigned_area_code = Column(String)  # Area code of assigned number
    outcome = Column(String)  # accepted, cancelled, timeout, completed, error
    exact_match = Column(Boolean, default=False)  # Did assigned match requested?
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
```

**Checklist**:
- [ ] Model file created
- [ ] All fields defined
- [ ] Indexes added for common queries

#### Step 2: Create Database Migration

```bash
# Generate migration
alembic revision --autogenerate -m "Add carrier_analytics table"

# Check generated migration
cat alembic/versions/[latest_migration].py
```

**Checklist**:
- [ ] Migration file generated
- [ ] Migration creates carrier_analytics table
- [ ] Indexes created

#### Step 3: Update Verification Purchase Endpoint

**File**: `app/api/verification/purchase_endpoints.py`

```python
# Add import
from app.models.carrier_analytics import CarrierAnalytics

# In request_verification function, after successful verification:
if carrier:
    # Record carrier analytics
    analytics = CarrierAnalytics(
        verification_id=str(verification.id),
        user_id=user_id,
        requested_carrier=carrier,
        sent_to_textverified=carrier.lower().replace(" ", "_").replace("&", ""),
        textverified_response=textverified_result.get("assigned_carrier"),
        assigned_phone=textverified_result["phone_number"],
        assigned_area_code=textverified_result.get("assigned_area_code"),
        outcome="accepted",
        exact_match=(textverified_result.get("assigned_carrier", "").lower() == carrier.lower()),
    )
    db.add(analytics)
    db.commit()
    
    logger.info(
        f"Carrier analytics recorded: user={user_id}, "
        f"requested={carrier}, assigned={textverified_result.get('assigned_carrier')}, "
        f"exact_match={analytics.exact_match}"
    )
```

**Checklist**:
- [ ] Import added
- [ ] Analytics record created for each carrier request
- [ ] All fields populated correctly
- [ ] Logging added

#### Step 4: Test Analytics Recording

```bash
# Run migration
alembic upgrade head

# Create verification with carrier
curl -X POST http://localhost:8000/api/verification/request \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"service": "telegram", "country": "US", "carriers": ["verizon"]}'

# Query analytics
sqlite3 namaskah.db "SELECT requested_carrier, textverified_response, exact_match FROM carrier_analytics ORDER BY created_at DESC LIMIT 1;"

# Expected: Shows carrier preference and whether it matched
```

**Checklist**:
- [ ] Migration runs successfully
- [ ] Analytics table created
- [ ] Analytics records created for carrier requests
- [ ] Data is queryable

#### Step 5: Commit and Push

```bash
git add app/models/carrier_analytics.py
git add alembic/versions/[migration_file].py
git add app/api/verification/purchase_endpoints.py
git commit -m "feat: add carrier analytics table for tracking preferences

- Create carrier_analytics model
- Record every carrier preference request
- Track requested vs assigned carrier
- Track exact match rate
- Enable future analytics and reporting

Fixes: #ISSUE_NUMBER"

git push origin feature/carrier-analytics
```

**Checklist**:
- [ ] Changes committed
- [ ] Code pushed to feature branch
- [ ] Ready for PR review

---

## 📋 Milestone 3-5 Summary

Due to token limits, here's a summary of remaining milestones:

### Milestone 3: Align Carrier List (Days 8-12)
- **Task 3.1**: Remove Sprint, add disclaimers
- **Task 3.2**: Research carrier lookup APIs
- **Task 3.3**: Build real success rates from analytics

### Milestone 4: Pricing Alignment (Days 13-16)
- **Task 4.1**: Audit carrier filter pricing
- **Task 4.2**: Block purchase without price

### Milestone 5: Observability (Days 17-20)
- **Task 5.1**: Add TextVerified API health metrics
- **Task 5.2**: Add structured logging
- **Task 5.3**: Build admin analytics dashboard

---

## ✅ Definition of Done

Every task is complete when:

- [ ] Code changes committed and pushed
- [ ] All tests pass (unit + integration)
- [ ] Manual testing completed
- [ ] No new linting errors
- [ ] Documentation updated
- [ ] PR reviewed and approved
- [ ] Merged to main branch
- [ ] Deployed to staging
- [ ] Verified in staging environment

---

## 🚀 Deployment Checklist

Before deploying to production:

- [ ] All Milestone 1 tasks complete
- [ ] Staging environment tested
- [ ] Rollback plan documented
- [ ] Team notified of changes
- [ ] Monitoring alerts configured
- [ ] Support team briefed
- [ ] User communication prepared

---

## 📞 Support & Questions

- **Technical Issues**: dev@namaskah.app
- **Product Questions**: product@namaskah.app
- **Urgent Issues**: #engineering-urgent Slack channel

---

**Last Updated**: March 14, 2026  
**Status**: Ready for Execution  
**Next Step**: Start Milestone 1, Task 1.1
