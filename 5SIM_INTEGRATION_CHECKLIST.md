# 5SIM API Integration Checklist

## ✅ **Ready to Deploy - Integration Steps**

### **1. Environment Configuration**
```bash
# Update .env file
FIVESIM_API_KEY=eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9...
FIVESIM_EMAIL=diamondman1960@gmail.com
FIVESIM_BASE_URL=https://5sim.net/v1
```

### **2. Core Service Implementation**
- [x] **Create 5SIM Service** - `app/services/fivesim_service.py` ✅
- [x] **Update TextVerified Service** - Replace with 5SIM calls ✅
- [x] **Database Migration** - Add 5SIM fields ✅
- [x] **API Endpoints** - Update verification endpoints ✅

### **3. Frontend Updates**
- [ ] **Service Selection** - Add 5SIM as provider option
- [ ] **Real-time Pricing** - Display 5SIM pricing
- [ ] **Status Updates** - Show 5SIM verification status
- [ ] **Error Handling** - 5SIM-specific error messages

---

## 🔧 **Implementation Tasks**

### **Task 1: 5SIM Service Class**
```python
# File: app/services/fivesim_service.py
class FiveSimService:
    def __init__(self):
        self.api_key = settings.fivesim_api_key
        self.base_url = "https://5sim.net/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
    
    async def get_balance(self) -> dict:
        """Get account balance"""
        
    async def buy_number(self, country: str, service: str) -> dict:
        """Purchase phone number"""
        
    async def check_sms(self, activation_id: str) -> dict:
        """Check for SMS messages"""
        
    async def get_pricing(self, country: str = None) -> dict:
        """Get service pricing"""
```

### **Task 2: Database Schema Update**
```sql
-- Add 5SIM specific fields
ALTER TABLE verifications ADD COLUMN fivesim_activation_id VARCHAR(50);
ALTER TABLE verifications ADD COLUMN fivesim_phone_number VARCHAR(20);
ALTER TABLE verifications ADD COLUMN fivesim_cost DECIMAL(10,4);
ALTER TABLE verifications ADD COLUMN provider VARCHAR(20) DEFAULT '5sim';
```

### **Task 3: API Endpoint Updates**
```python
# File: app/api/verify.py
@router.post("/verify/create")
async def create_verification_5sim(request: VerificationRequest):
    # Use 5SIM instead of TextVerified
    fivesim = FiveSimService()
    activation = await fivesim.buy_number(request.country, request.service)
    
    # Store verification with 5SIM data
    verification = Verification(
        user_id=request.user_id,
        fivesim_activation_id=activation['id'],
        phone_number=activation['phone'],
        service=request.service,
        status="waiting_sms",
        provider="5sim"
    )
    
    return {
        "verification_id": verification.id,
        "phone_number": activation['phone'],
        "status": "active"
    }
```

### **Task 4: Frontend Service Selection**
```javascript
// File: static/js/verification.js
// Update service selection to use 5SIM
const PROVIDERS = {
    '5sim': {
        name: '5SIM',
        countries: 156,
        services: 1000,
        pricing: 'dynamic'
    }
};

async function getAvailableServices(country) {
    const response = await fetch(`/api/5sim/services?country=${country}`);
    return await response.json();
}
```

---

## 📱 **Namaskah Pages Updates Needed**

### **1. Dashboard Page Updates**
```html
<!-- File: templates/dashboard.html -->
<!-- Update provider selection -->
<div class="provider-selection">
    <h3>SMS Provider</h3>
    <select id="provider-select">
        <option value="5sim" selected>5SIM (Active)</option>
        <option value="textverified" disabled>TextVerified (Unavailable)</option>
    </select>
</div>

<!-- Real-time pricing display -->
<div class="pricing-info">
    <h4>Current Pricing</h4>
    <div id="pricing-display">
        <span class="price">Loading...</span>
        <span class="currency">USD</span>
    </div>
</div>
```

### **2. Verification Page Updates**
```html
<!-- File: templates/verification.html -->
<!-- Update verification flow -->
<div class="verification-status">
    <div class="provider-info">
        <img src="/static/images/5sim-logo.png" alt="5SIM">
        <span>Powered by 5SIM</span>
    </div>
    
    <div class="phone-display">
        <h3>Your Verification Number</h3>
        <div class="phone-number" id="verification-phone">
            +1 (555) 123-4567
        </div>
        <div class="country-flag" id="country-flag">🇺🇸</div>
    </div>
    
    <div class="sms-status">
        <div class="status-indicator" id="sms-status">
            <span class="spinner"></span>
            <span>Waiting for SMS...</span>
        </div>
    </div>
</div>
```

### **3. Services Page Updates**
```html
<!-- File: templates/services.html -->
<!-- Update service availability -->
<div class="services-grid">
    <div class="service-card" data-service="whatsapp">
        <img src="/static/images/whatsapp.png" alt="WhatsApp">
        <h4>WhatsApp</h4>
        <div class="availability">
            <span class="status available">Available</span>
            <span class="price">$0.15</span>
        </div>
        <div class="countries">156 countries</div>
    </div>
    
    <div class="service-card" data-service="telegram">
        <img src="/static/images/telegram.png" alt="Telegram">
        <h4>Telegram</h4>
        <div class="availability">
            <span class="status available">Available</span>
            <span class="price">$0.12</span>
        </div>
        <div class="countries">156 countries</div>
    </div>
</div>
```

### **4. Admin Panel Updates**
```html
<!-- File: templates/admin/dashboard.html -->
<!-- Provider management -->
<div class="provider-management">
    <h3>SMS Providers</h3>
    <div class="provider-status">
        <div class="provider active">
            <span class="name">5SIM</span>
            <span class="status">✅ Active</span>
            <span class="balance">$45.67</span>
        </div>
        <div class="provider inactive">
            <span class="name">TextVerified</span>
            <span class="status">❌ Unavailable</span>
            <span class="balance">N/A</span>
        </div>
    </div>
</div>
```

---

## 🔄 **JavaScript Updates Required**

### **1. Update Verification Logic**
```javascript
// File: static/js/verification.js
class VerificationManager {
    constructor() {
        this.provider = '5sim';
        this.pollInterval = 5000; // 5 seconds
    }
    
    async createVerification(service, country) {
        const response = await fetch('/api/verify/create', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                service: service,
                country: country,
                provider: this.provider
            })
        });
        
        const data = await response.json();
        this.startPolling(data.verification_id);
        return data;
    }
    
    async checkSMS(verificationId) {
        const response = await fetch(`/api/verify/${verificationId}/messages`);
        return await response.json();
    }
}
```

### **2. Real-time Pricing Updates**
```javascript
// File: static/js/pricing.js
class PricingManager {
    async updatePricing(country, service) {
        try {
            const response = await fetch(`/api/5sim/pricing?country=${country}&service=${service}`);
            const pricing = await response.json();
            
            document.getElementById('pricing-display').innerHTML = `
                <span class="price">$${pricing.cost}</span>
                <span class="currency">USD</span>
                <span class="availability">${pricing.count} available</span>
            `;
        } catch (error) {
            console.error('Pricing update failed:', error);
        }
    }
}
```

---

## 🚀 **Deployment Steps**

### **Step 1: Update Environment**
```bash
# Update .env with 5SIM credentials
echo "FIVESIM_API_KEY=eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9..." >> .env
echo "FIVESIM_EMAIL=diamondman1960@gmail.com" >> .env
```

### **Step 2: Database Migration**
```bash
# Create and run migration
alembic revision --autogenerate -m "Add 5SIM support"
alembic upgrade head
```

### **Step 3: Test Integration**
```bash
# Test 5SIM API connection
python3 -c "
from app.services.fivesim_service import FiveSimService
import asyncio

async def test():
    service = FiveSimService()
    balance = await service.get_balance()
    print(f'5SIM Balance: {balance}')

asyncio.run(test())
"
```

### **Step 4: Update Frontend**
```bash
# Update static files
cp static/js/verification-5sim.js static/js/verification.js
cp templates/verification-5sim.html templates/verification.html
```

### **Step 5: Deploy & Test**
```bash
# Restart application
sudo systemctl restart namaskah-sms
# Test verification flow
curl -X POST http://localhost:8000/api/verify/create \
  -H "Content-Type: application/json" \
  -d '{"service":"whatsapp","country":"US"}'
```

---

---

## ✅ **COMPLETED TASKS - PHASE 1**

### **✅ RENTAL BACKEND IMPLEMENTED**
- ✅ **Rental Models** - `app/models/rental.py`
- ✅ **Rental Schemas** - `app/schemas/rental.py`
- ✅ **Rental Service** - `app/services/rental_service.py`
- ✅ **Rental API** - `app/api/rentals.py`
- ✅ **Database Migration** - Migration 004 applied
- ✅ **Error Handling** - Comprehensive exception handling

### **✅ 5SIM INTEGRATION IMPLEMENTED**
- ✅ **5SIM Service** - `app/services/fivesim_service.py`
- ✅ **Configuration** - Settings updated with 5SIM fields
- ✅ **Database Schema** - Migration 005 applied
- ✅ **API Endpoints** - `/5sim/balance`, `/5sim/pricing`, `/5sim/services`
- ✅ **Verification Updated** - Now uses 5SIM instead of TextVerified

---

## 🚀 **PHASE 2: FRONTEND INTEGRATION & TESTING**

### **Priority Tasks (Next 3 Days)**

#### **Task 1: Environment Setup**
- [ ] **Add API Key** - Set `FIVESIM_API_KEY` in `.env`
- [ ] **Test Connection** - Verify 5SIM API works
- [ ] **Validate Rental Endpoints** - Test all rental API calls

#### **Task 2: Frontend Updates**
- [ ] **Update Verification UI** - Connect to 5SIM endpoints
- [ ] **Test Rental UI** - Ensure rentals.js works with backend
- [ ] **Provider Selection** - Add 5SIM option to dashboard
- [ ] **Real-time Pricing** - Display 5SIM pricing

#### **Task 3: Integration Testing**
- [ ] **End-to-End Testing** - Full verification flow
- [ ] **Rental Flow Testing** - Create, extend, release rentals
- [ ] **Error Handling** - Test all error scenarios
- [ ] **Performance Testing** - Response time validation

---

## 🔧 **PHASE 3: PRODUCTION DEPLOYMENT**

### **Deployment Checklist**
- [ ] **Security Audit** - Review all endpoints
- [ ] **Load Testing** - Stress test with concurrent users
- [ ] **Monitoring Setup** - Health checks and alerts
- [ ] **Backup Strategy** - Database backup procedures
- [ ] **SSL Configuration** - HTTPS setup
- [ ] **Domain Setup** - Production domain configuration

### **Go-Live Requirements**
- [ ] **5SIM Account Funded** - Sufficient balance for operations
- [ ] **Payment Integration** - Paystack working
- [ ] **User Testing** - Beta user feedback
- [ ] **Documentation** - API docs updated

---

## 📊 **SUCCESS METRICS**

### **Technical Metrics**
- **API Response Time**: < 2 seconds P95
- **Uptime**: > 99.5%
- **Error Rate**: < 1%
- **Test Coverage**: > 85%

### **Business Metrics**
- **Verification Success Rate**: > 95%
- **Rental Utilization**: > 70%
- **User Satisfaction**: > 4.5/5
- **Revenue Growth**: Track monthly

---

## 🔄 **IMMEDIATE NEXT STEPS**

### **Today (Priority 1)**
1. **Add FIVESIM_API_KEY to .env**
2. **Test 5SIM API connection**
3. **Validate rental endpoints work**

### **Tomorrow (Priority 2)**
1. **Update frontend verification flow**
2. **Test rental UI integration**
3. **Fix any integration issues**

### **Day 3 (Priority 3)**
1. **End-to-end testing**
2. **Performance optimization**
3. **Prepare for production deployment**

**Status**: 🚀 **Ready for Phase 2 - Frontend Integration**nd-Backend Mismatch Discovered:**
- ✅ **Frontend Complete**: `static/js/rentals.js` exists with full rental UI
- ❌ **Backend Missing**: No rental API endpoints, models, or services found
- 🔄 **API Calls Expected**: Frontend makes calls to non-existent endpoints

### **Missing Backend Components**
```bash
# Expected but NOT FOUND:
app/api/rentals.py          # ❌ Missing rental API router
app/models/rental.py        # ❌ Missing rental database model  
app/services/rental_service.py  # ❌ Missing rental business logic
app/schemas/rental.py       # ❌ Missing rental validation schemas
```

### **Frontend Expects These Endpoints (ALL MISSING)**
```javascript
// From static/js/rentals.js - these endpoints don't exist:
GET    /rentals/active           // Load user's active rentals
POST   /rentals/{id}/extend      // Extend rental duration  
POST   /rentals/{id}/release     // Release rental early
GET    /rentals/{id}/messages    // Get rental SMS messages
POST   /rentals/create           // Create new rental (implied)
```

### **Database Schema Missing**
```sql
-- Rental table doesn't exist - needs creation:
CREATE TABLE rentals (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    service_name VARCHAR(50) NOT NULL,
    country_code VARCHAR(3) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    cost DECIMAL(10,4) NOT NULL,
    provider VARCHAR(20) DEFAULT '5sim'
);
```

### **Immediate Action Required**
1. **Create rental backend infrastructure**
2. **Implement missing API endpoints**  
3. **Add database migration for rentals**
4. **Connect existing frontend to new backend**

**Priority**: 🔥 **CRITICAL** - Frontend is broken without backend

---

## ✅ **Ready to Deploy Checklist**

### **5SIM Integration**
- [x] **5SIM API Key**: Available and tested
- [ ] **Service Implementation**: Create fivesim_service.py
- [ ] **Database Migration**: Add 5SIM fields
- [ ] **API Updates**: Update verification endpoints

### **Rental System (BLOCKING)**
- [ ] **❌ Rental Backend**: Must implement before deployment
- [ ] **❌ Rental API**: Create all missing endpoints
- [ ] **❌ Rental Models**: Add database schema
- [ ] **❌ Frontend Integration**: Connect existing UI to backend

**⚠️ DEPLOYMENT BLOCKED**: Cannot deploy until rental backend is implementedlementation**: Create FiveSimService class
- [ ] **Database Migration**: Add 5SIM fields
- [ ] **API Updates**: Replace TextVerified calls
- [ ] **Frontend Updates**: Update verification pages
- [ ] **Testing**: End-to-end verification test
- [ ] **Deployment**: Production deployment

**Status**: Ready to implement - All prerequisites met  
**Timeline**: 2-3 days for full integration  
**Priority**: P0 - Critical for SMS functionality