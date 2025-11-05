# 5SIM Implementation Tasks & Roadmap

## 🎯 **Implementation Tasks Breakdown**

### **Phase 1: Core Integration (Days 1-3)**

#### **Task 1.1: Backend Service Implementation**
- [ ] **Create FiveSimService class** - `app/services/fivesim_service.py`
  - Implement authentication with JWT token
  - Add balance checking functionality
  - Create number purchasing logic
  - Add SMS checking mechanism
  - Include rental number support

- [ ] **Database Schema Updates** - `alembic/versions/add_5sim_support.py`
  - Add `fivesim_activation_id` column
  - Add `fivesim_phone_number` column
  - Add `fivesim_cost` column
  - Add `provider` column (default: '5sim')
  - Add `rental_duration` column for rental numbers
  - Add `rental_expires_at` column

- [ ] **API Endpoint Updates** - `app/api/verify.py`
  - Replace TextVerified calls with 5SIM
  - Add rental number endpoints
  - Update verification status handling
  - Add cost tracking

#### **Task 1.2: Rental Numbers Feature (Backend)**
```python
# File: app/services/fivesim_service.py
class FiveSimService:
    async def rent_number(self, country: str, service: str, duration_days: int = 1) -> dict:
        """Rent phone number for extended period"""
        response = await self.client.post(
            f"{self.base_url}/user/buy/hosting/{country}/{service}",
            json={"days": duration_days},
            headers=self.headers
        )
        return response.json()
    
    async def extend_rental(self, hosting_id: str, additional_days: int) -> dict:
        """Extend rental period"""
        response = await self.client.post(
            f"{self.base_url}/user/extend/{hosting_id}",
            json={"days": additional_days},
            headers=self.headers
        )
        return response.json()
    
    async def get_rental_messages(self, hosting_id: str) -> dict:
        """Get all messages for rental number"""
        response = await self.client.get(
            f"{self.base_url}/user/hosting/{hosting_id}/messages",
            headers=self.headers
        )
        return response.json()
```

#### **Task 1.3: Rental API Endpoints**
```python
# File: app/api/rental.py
@router.post("/rental/create")
async def create_rental_number(request: RentalRequest):
    """Create rental number for extended use"""
    
@router.get("/rental/{rental_id}/messages")
async def get_rental_messages(rental_id: str):
    """Get all messages for rental number"""
    
@router.post("/rental/{rental_id}/extend")
async def extend_rental(rental_id: str, days: int):
    """Extend rental period"""
```

### **Phase 2: Frontend Integration (Days 4-6)**

#### **Task 2.1: Dashboard Updates**
- [ ] **Provider Selection UI** - `templates/dashboard.html`
  - Add 5SIM provider option
  - Show provider status (active/inactive)
  - Display account balance
  - Add provider switching functionality

- [ ] **Real-time Pricing Display** - `static/js/pricing.js`
  - Fetch 5SIM pricing dynamically
  - Update pricing every 30 minutes
  - Show service availability count
  - Display country-specific pricing

#### **Task 2.2: Verification Page Updates**
- [ ] **Verification Flow UI** - `templates/verification.html`
  - Update provider branding to 5SIM
  - Add country flag display
  - Show verification timer
  - Add SMS polling status

- [ ] **Verification JavaScript** - `static/js/verification.js`
  - Update API calls to use 5SIM endpoints
  - Add real-time SMS checking
  - Handle 5SIM-specific responses
  - Add error handling for 5SIM errors

#### **Task 2.3: Rental Numbers UI (Frontend)**
- [ ] **Rental Dashboard** - `templates/rental/dashboard.html`
  - List active rental numbers
  - Show rental expiration dates
  - Add extend rental functionality
  - Display rental message history

- [ ] **Rental Creation Form** - `templates/rental/create.html`
  - Service selection dropdown
  - Country selection
  - Duration selector (1-30 days)
  - Cost calculator

- [ ] **Rental JavaScript** - `static/js/rental.js`
```javascript
class RentalManager {
    async createRental(service, country, days) {
        const response = await fetch('/api/rental/create', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                service: service,
                country: country,
                duration_days: days
            })
        });
        return await response.json();
    }
    
    async getRentalMessages(rentalId) {
        const response = await fetch(`/api/rental/${rentalId}/messages`);
        return await response.json();
    }
    
    async extendRental(rentalId, additionalDays) {
        const response = await fetch(`/api/rental/${rentalId}/extend`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({days: additionalDays})
        });
        return await response.json();
    }
}
```

### **Phase 3: Advanced Features (Days 7-10)**

#### **Task 3.1: Admin Panel Updates**
- [ ] **Provider Management** - `templates/admin/providers.html`
  - 5SIM account overview
  - Balance monitoring
  - Usage statistics
  - Provider health status

- [ ] **Rental Management** - `templates/admin/rentals.html`
  - All active rentals overview
  - Revenue from rentals
  - Expiration alerts
  - Bulk rental operations

#### **Task 3.2: Services Page Enhancement**
- [ ] **Service Grid Updates** - `templates/services.html`
  - Show 5SIM availability for each service
  - Display real-time pricing
  - Add rental option toggle
  - Show success rates

- [ ] **Service Details** - `templates/service_detail.html`
  - Detailed service information
  - Country availability matrix
  - Pricing comparison (SMS vs Rental)
  - Historical success rates

---

## 📊 **Rental Numbers Feature Specification**

### **Backend Implementation**
```python
# File: app/models/rental.py
class RentalNumber(Base):
    __tablename__ = "rental_numbers"
    
    id = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    fivesim_hosting_id = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    country = Column(String, nullable=False)
    service = Column(String, nullable=False)
    duration_days = Column(Integer, nullable=False)
    cost_per_day = Column(Numeric(10, 4), nullable=False)
    total_cost = Column(Numeric(10, 4), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    status = Column(String, default="active")  # active, expired, cancelled
    
    # Relationships
    user = relationship("User", back_populates="rental_numbers")
    messages = relationship("RentalMessage", back_populates="rental")

class RentalMessage(Base):
    __tablename__ = "rental_messages"
    
    id = Column(Integer, primary_key=True)
    rental_id = Column(String, ForeignKey("rental_numbers.id"))
    sender = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    received_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    rental = relationship("RentalNumber", back_populates="messages")
```

### **Frontend Rental UI**
```html
<!-- File: templates/rental/dashboard.html -->
<div class="rental-dashboard">
    <div class="rental-header">
        <h2>My Rental Numbers</h2>
        <button class="btn btn-primary" onclick="createRental()">
            <i class="fas fa-plus"></i> Rent New Number
        </button>
    </div>
    
    <div class="rental-grid">
        <div class="rental-card active">
            <div class="rental-info">
                <div class="phone-number">+1 (555) 123-4567</div>
                <div class="service-badge">WhatsApp</div>
                <div class="country-flag">🇺🇸</div>
            </div>
            <div class="rental-status">
                <div class="expires">Expires: 2 days</div>
                <div class="messages-count">5 messages</div>
                <button class="btn btn-sm btn-outline-primary">Extend</button>
            </div>
        </div>
    </div>
</div>

<!-- Rental Creation Modal -->
<div class="modal" id="rentalModal">
    <div class="modal-content">
        <h3>Rent Phone Number</h3>
        <form id="rentalForm">
            <select name="service" required>
                <option value="whatsapp">WhatsApp - $1.50/day</option>
                <option value="telegram">Telegram - $1.20/day</option>
                <option value="discord">Discord - $1.00/day</option>
            </select>
            
            <select name="country" required>
                <option value="US">🇺🇸 United States</option>
                <option value="UK">🇬🇧 United Kingdom</option>
                <option value="CA">🇨🇦 Canada</option>
            </select>
            
            <input type="number" name="days" min="1" max="30" value="1" required>
            <label>Duration (days)</label>
            
            <div class="cost-calculator">
                <span>Total Cost: $<span id="totalCost">1.50</span></span>
            </div>
            
            <button type="submit" class="btn btn-primary">Rent Number</button>
        </form>
    </div>
</div>
```

---

## 📋 **Complete Task List**

### **Backend Tasks**
- [ ] Create `FiveSimService` class with all methods
- [ ] Add rental number functionality to service
- [ ] Create `RentalNumber` and `RentalMessage` models
- [ ] Update verification API endpoints
- [ ] Create rental API endpoints (`/api/rental/*`)
- [ ] Add database migration for 5SIM fields
- [ ] Add database migration for rental tables
- [ ] Update health checks to use 5SIM
- [ ] Add background task for rental expiration alerts

### **Frontend Tasks**
- [ ] Update dashboard with 5SIM provider selection
- [ ] Add real-time pricing display
- [ ] Update verification page with 5SIM branding
- [ ] Create rental dashboard page
- [ ] Create rental creation modal
- [ ] Update services page with rental options
- [ ] Add rental management to admin panel
- [ ] Update JavaScript for 5SIM API calls
- [ ] Add rental JavaScript functionality
- [ ] Update CSS for rental UI components

### **Testing Tasks**
- [ ] Unit tests for FiveSimService
- [ ] Integration tests with 5SIM API
- [ ] Frontend testing for rental features
- [ ] End-to-end verification testing
- [ ] Rental number lifecycle testing
- [ ] Performance testing under load

### **Deployment Tasks**
- [ ] Update environment variables
- [ ] Run database migrations
- [ ] Deploy backend changes
- [ ] Deploy frontend updates
- [ ] Configure monitoring for 5SIM
- [ ] Test production deployment
- [ ] Setup rental expiration alerts

---

## 🗓️ **Implementation Timeline**

### **Day 1-2: Backend Core**
- FiveSimService implementation
- Database migrations
- Basic API endpoints

### **Day 3-4: Rental Feature**
- Rental backend implementation
- Rental database schema
- Rental API endpoints

### **Day 5-6: Frontend Core**
- Dashboard updates
- Verification page updates
- Basic 5SIM integration

### **Day 7-8: Rental UI**
- Rental dashboard creation
- Rental creation modal
- Rental management features

### **Day 9-10: Testing & Deployment**
- Comprehensive testing
- Production deployment
- Monitoring setup

---

## ✅ **Rental Feature Confirmation**

**YES - Rental numbers are included in both backend and frontend:**

### **Backend Rental Features:**
- `rent_number()` method in FiveSimService
- `RentalNumber` and `RentalMessage` models
- Rental API endpoints (`/api/rental/*`)
- Rental expiration handling
- Message history for rental numbers

### **Frontend Rental Features:**
- Rental dashboard page
- Rental creation modal with cost calculator
- Rental management interface
- Message viewing for rental numbers
- Extend rental functionality

**Status**: ✅ **Complete roadmap with rental features included**  
**Timeline**: 10 days for full implementation including rental numbers  
**Priority**: P0 - Critical for SMS functionality