# Verification Flow Overhaul - Implementation Checklist

## Backend Implementation

### ✅ Step 1: Create Availability Check Endpoint

**File:** `app/api/verification/availability_endpoints.py` (NEW)

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.services.textverified_service import TextVerifiedService

router = APIRouter(prefix="/verification", tags=["Verification"])

class AvailabilityCheckRequest(BaseModel):
    service: str
    area_code: Optional[str] = None
    carrier: Optional[str] = None
    country: str = "US"

@router.post("/check-availability")
async def check_availability(
    request: AvailabilityCheckRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Check if specific service/area-code/carrier combination is available."""
    tv_service = TextVerifiedService()
    
    try:
        # Check availability with TextVerified
        result = await tv_service.check_availability(
            service=request.service,
            area_code=request.area_code,
            carrier=request.carrier,
            country=request.country
        )
        
        return {
            "available": result.get("available", False),
            "service": request.service,
            "area_code": request.area_code,
            "carrier": request.carrier,
            "estimated_cost": result.get("cost", 2.50),
            "message": "Ready to purchase" if result.get("available") else "Not available",
            "alternatives": result.get("alternatives", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### ✅ Step 2: Add Method to TextVerifiedService

**File:** `app/services/textverified_service.py` (ADD METHOD)

```python
async def check_availability(
    self,
    service: str,
    area_code: Optional[str] = None,
    carrier: Optional[str] = None,
    country: str = "US"
) -> Dict[str, Any]:
    """
    Check if specific combination is available.
    Returns availability status + alternatives.
    """
    if not self.enabled:
        return {"available": False, "error": "Service disabled"}
    
    try:
        # Build preference list
        area_code_prefs = []
        if area_code:
            area_code_prefs = await self._build_area_code_preference(area_code)
        
        carrier_prefs = []
        if carrier:
            carrier_prefs = [carrier]
        
        # Call TextVerified API with preferences
        result = await asyncio.to_thread(
            self.client.services.check_availability,
            service_name=service,
            area_codes=area_code_prefs,
            carriers=carrier_prefs,
            country=country
        )
        
        return {
            "available": result.get("available", False),
            "cost": result.get("cost", 2.50),
            "alternatives": result.get("alternatives", [])
        }
    except Exception as e:
        logger.error(f"Availability check failed: {e}")
        return {"available": False, "error": str(e)}
```

### ✅ Step 3: Create Options Endpoint (Parallel Loading)

**File:** `app/api/verification/options_endpoints.py` (NEW)

```python
from fastapi import APIRouter, Depends
import asyncio

from app.core.dependencies import get_current_user_id
from app.services.textverified_service import TextVerifiedService

router = APIRouter(prefix="/verification", tags=["Verification"])

@router.get("/options")
async def get_verification_options(
    country: str = "US",
    user_id: str = Depends(get_current_user_id),
):
    """Load all verification options in parallel."""
    tv_service = TextVerifiedService()
    
    try:
        # Load all in parallel
        services, area_codes, carriers = await asyncio.gather(
            tv_service.get_services_list(),
            tv_service.get_area_codes_list(),
            tv_service.get_available_carriers(country),
            return_exceptions=True
        )
        
        return {
            "services": services if not isinstance(services, Exception) else [],
            "area_codes": area_codes if not isinstance(area_codes, Exception) else [],
            "carriers": carriers if not isinstance(carriers, Exception) else [],
            "country": country
        }
    except Exception as e:
        logger.error(f"Failed to load options: {e}")
        return {
            "services": [],
            "area_codes": [],
            "carriers": [],
            "error": str(e)
        }
```

### ✅ Step 4: Update Router

**File:** `app/api/verification/router.py` (UPDATE)

```python
from app.api.verification.availability_endpoints import router as availability_router
from app.api.verification.options_endpoints import router as options_router

# Include new routers
router.include_router(availability_router)
router.include_router(options_router)
```

---

## Frontend Implementation

### ✅ Step 5: Create Multi-Step Form Component

**File:** `static/js/verification-multistep.js` (NEW)

```javascript
class VerificationMultiStep {
    constructor() {
        this.currentStep = 1;
        this.selectedService = null;
        this.selectedAreaCode = null;
        this.selectedCarrier = null;
        this.availabilityStatus = null;
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.loadOptions();
    }

    setupEventListeners() {
        // Step navigation
        document.getElementById('step-1-next').addEventListener('click', () => this.goToStep(2));
        document.getElementById('step-2-next').addEventListener('click', () => this.validateAreaCode());
        document.getElementById('step-3-next').addEventListener('click', () => this.validateCarrier());
        document.getElementById('step-4-check').addEventListener('click', () => this.checkAvailability());
        document.getElementById('step-5-purchase').addEventListener('click', () => this.purchaseVerification());
        
        // Back buttons
        document.querySelectorAll('.step-back').forEach(btn => {
            btn.addEventListener('click', (e) => this.goToStep(parseInt(e.target.dataset.step)));
        });
    }

    async loadOptions() {
        try {
            const response = await axios.get('/api/verification/options', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
            });
            
            this.populateServices(response.data.services);
            this.populateAreaCodes(response.data.area_codes);
            this.populateCarriers(response.data.carriers);
        } catch (error) {
            console.error('Failed to load options:', error);
            this.showError('Failed to load verification options');
        }
    }

    populateServices(services) {
        const select = document.getElementById('service-select');
        services.forEach(service => {
            const option = document.createElement('option');
            option.value = service.id;
            option.textContent = `${service.name} - $${service.cost.toFixed(2)}`;
            select.appendChild(option);
        });
        
        select.addEventListener('change', (e) => {
            this.selectedService = e.target.value;
        });
    }

    populateAreaCodes(areaCodes) {
        const select = document.getElementById('area-code-select');
        select.innerHTML = '<option value="">Any Area Code</option>';
        
        areaCodes.forEach(ac => {
            const option = document.createElement('option');
            option.value = ac.area_code;
            option.textContent = `${ac.city}, ${ac.state} (${ac.area_code})`;
            select.appendChild(option);
        });
        
        select.addEventListener('change', (e) => {
            this.selectedAreaCode = e.target.value || null;
        });
    }

    populateCarriers(carriers) {
        const select = document.getElementById('carrier-select');
        select.innerHTML = '<option value="">Any Carrier</option>';
        
        carriers.forEach(carrier => {
            const option = document.createElement('option');
            option.value = carrier.id;
            const icon = carrier.success_rate >= 90 ? '🟢' : 
                        carrier.success_rate >= 75 ? '🟡' : '🔴';
            option.textContent = `${carrier.name} - ${icon} ${carrier.success_rate.toFixed(1)}%`;
            select.appendChild(option);
        });
        
        select.addEventListener('change', (e) => {
            this.selectedCarrier = e.target.value || null;
        });
    }

    async validateAreaCode() {
        if (!this.selectedService) {
            this.showError('Please select a service first');
            return;
        }
        
        try {
            const response = await axios.post('/api/verification/check-availability', {
                service: this.selectedService,
                area_code: this.selectedAreaCode,
                country: 'US'
            }, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
            });
            
            if (response.data.available) {
                this.showSuccess('✅ Area code available');
                this.goToStep(3);
            } else {
                this.showError('❌ Area code not available');
                this.showAlternatives(response.data.alternatives);
            }
        } catch (error) {
            console.error('Validation failed:', error);
            this.showError('Failed to validate area code');
        }
    }

    async validateCarrier() {
        try {
            const response = await axios.post('/api/verification/check-availability', {
                service: this.selectedService,
                area_code: this.selectedAreaCode,
                carrier: this.selectedCarrier,
                country: 'US'
            }, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
            });
            
            if (response.data.available) {
                this.showSuccess('✅ Carrier available');
                this.goToStep(4);
            } else {
                this.showError('❌ Carrier not available');
                this.showAlternatives(response.data.alternatives);
            }
        } catch (error) {
            console.error('Validation failed:', error);
            this.showError('Failed to validate carrier');
        }
    }

    async checkAvailability() {
        try {
            const response = await axios.post('/api/verification/check-availability', {
                service: this.selectedService,
                area_code: this.selectedAreaCode,
                carrier: this.selectedCarrier,
                country: 'US'
            }, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
            });
            
            this.availabilityStatus = response.data;
            
            if (response.data.available) {
                document.getElementById('step-5-purchase').disabled = false;
                this.showAvailabilityResult(response.data);
                this.goToStep(5);
            } else {
                document.getElementById('step-5-purchase').disabled = true;
                this.showError('Combination not available');
                this.showAlternatives(response.data.alternatives);
            }
        } catch (error) {
            console.error('Availability check failed:', error);
            this.showError('Failed to check availability');
        }
    }

    async purchaseVerification() {
        try {
            const response = await axios.post('/api/verification/request', {
                service: this.selectedService,
                area_code: this.selectedAreaCode,
                carrier: this.selectedCarrier,
                country: 'US'
            }, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
            });
            
            // Display phone number and start polling
            document.getElementById('phone-number').textContent = response.data.phone_number;
            this.startPolling(response.data.verification_id);
        } catch (error) {
            console.error('Purchase failed:', error);
            this.showError('Failed to purchase verification');
        }
    }

    goToStep(step) {
        // Hide all steps
        document.querySelectorAll('.step').forEach(s => s.style.display = 'none');
        
        // Show selected step
        document.getElementById(`step-${step}`).style.display = 'block';
        this.currentStep = step;
    }

    showError(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-error';
        alert.textContent = message;
        document.body.appendChild(alert);
        setTimeout(() => alert.remove(), 5000);
    }

    showSuccess(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-success';
        alert.textContent = message;
        document.body.appendChild(alert);
        setTimeout(() => alert.remove(), 3000);
    }

    showAlternatives(alternatives) {
        if (!alternatives || alternatives.length === 0) return;
        
        const div = document.createElement('div');
        div.className = 'alternatives';
        div.innerHTML = '<h4>Try these alternatives:</h4>';
        
        alternatives.forEach(alt => {
            div.innerHTML += `
                <div class="alternative-item">
                    <span>${alt.area_code || 'Any'} - ${alt.carrier || 'Any'}</span>
                    <span>$${alt.cost.toFixed(2)}</span>
                </div>
            `;
        });
        
        document.getElementById(`step-${this.currentStep}`).appendChild(div);
    }

    showAvailabilityResult(data) {
        const div = document.getElementById('availability-result');
        div.innerHTML = `
            <div class="availability-success">
                <h3>✅ Ready to Purchase</h3>
                <p>Service: ${data.service}</p>
                <p>Area Code: ${data.area_code || 'Any'}</p>
                <p>Carrier: ${data.carrier || 'Any'}</p>
                <p>Cost: $${data.estimated_cost.toFixed(2)}</p>
            </div>
        `;
    }

    startPolling(verificationId) {
        // Start SMS polling (existing logic)
        // ...
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    window.verificationMultiStep = new VerificationMultiStep();
});
```

### ✅ Step 6: Update HTML Template

**File:** `templates/verify_modern.html` (UPDATE)

Replace the current form with multi-step form (see document for full HTML)

---

## Database Updates

### ✅ Step 7: Update Verification Model

**File:** `app/models/verification.py` (UPDATE)

```python
# Add these fields to Verification model
requested_area_code = Column(String)
assigned_area_code = Column(String)
area_code_matched = Column(Boolean, default=True)

requested_carrier = Column(String)
assigned_carrier = Column(String)
carrier_matched = Column(Boolean, default=True)

availability_checked_at = Column(DateTime)
availability_result = Column(String)  # "available" or "out_of_stock"
```

---

## Testing Checklist

- [ ] Unit tests for availability check endpoint
- [ ] Integration tests for multi-step flow
- [ ] Error scenario tests (out of stock, API failures)
- [ ] Performance tests (parallel loading)
- [ ] UI/UX tests (form validation, error messages)
- [ ] End-to-end tests (full purchase flow)

---

## Deployment Checklist

- [ ] Code review
- [ ] Merge to main branch
- [ ] Deploy to staging
- [ ] Smoke tests on staging
- [ ] Deploy to production (10% traffic)
- [ ] Monitor error rates
- [ ] Gradual rollout (50% → 100%)
- [ ] Collect user feedback

---

## Rollback Plan

If issues occur:
1. Revert to previous version
2. Keep old endpoint active
3. Investigate root cause
4. Fix and re-deploy

---

## Success Criteria

✅ Failed purchases reduced from 8-12% to <2%  
✅ Refund rate reduced from 5-7% to <1%  
✅ User satisfaction increased to 92%+  
✅ Conversion rate increased to 85%+  
✅ No performance regression  

