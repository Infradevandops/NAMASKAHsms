# SMSPool Filtering Implementation - Technical Summary

**Based on**: app.log analysis + TextVerified codebase review  
**Date**: Current  
**Status**: Implementation Ready

---

## 🎯 Key Findings from Codebase Analysis

### Current TextVerified Filtering (US-Only)
```python
# From: app/services/textverified_service.py (lines 600-650)
await tv_service.create_verification(
    service="telegram",
    country="US",
    area_code="415",           # 3-digit US area code
    carrier="verizon",         # verizon/att/tmobile
    capability="sms"           # sms or voice
)
```

**Filtering Mechanism**:
- Area Code: Proximity chain from live TextVerified index (same-state fallback)
- Carrier: Preference list (best-effort, not guaranteed)
- Line Type: Post-purchase validation with retry (v4.4.1)
- Retry Logic: Up to 3 attempts, cancels if VOIP/landline/wrong carrier

---

## 🌍 SMSPool API Filtering (International)

### Critical Endpoints (from app.log)

#### 1. Success Rate Endpoint (FREE)
```http
GET /request/success_rate?service=telegram
Response: {
  "GB": {
    "Vodafone UK": {"success_rate": 0.92, "cost": 0.85},
    "EE": {"success_rate": 0.88, "cost": 0.90}
  },
  "DE": {
    "Vodafone DE": {"success_rate": 0.95, "cost": 1.20}
  }
}
```
**Use**: Auto-select best operator by country/service

#### 2. Paid Lookup Endpoint ($0.005/lookup)
```http
POST /carrier/paid_lookup
Body: {"key": "API_KEY", "number": "+447700900123"}
Response: {
  "carrier": "Vodafone UK",
  "carrier_type": "mobile",  # mobile/landline/voip
  "country": "GB"
}
```
**Use**: Pre-validate carrier/line type BEFORE purchase

#### 3. Purchase Endpoint
```http
POST /order/sms
Body: {
  "key": "API_KEY",
  "country": "GB",           # ISO country code
  "service": "telegram",
  "operator": "Vodafone UK"  # CARRIER FILTER
}
Response: {
  "success": 1,
  "number": "+447700900123",
  "order_id": "12345",
  "cost": 0.85
}
```

#### 4. Check SMS Endpoint
```http
POST /sms/check
Body: {"key": "API_KEY", "orderid": "12345"}
Response: {
  "status": 3,  # 3 = received
  "sms": "Your code is 123456",
  "full_sms": "Your code is 123456"
}
```

---

## 🔄 Filter Mapping Strategy

### Country-Based Routing
```python
if country == "US":
    provider = TextVerifiedProvider()  # Keeps area code support
else:
    provider = SMSPoolProvider()      # International
```

### Carrier Mapping
```python
CARRIER_MAPPING = {
    # US (for reference)
    "verizon": ["Verizon", "Verizon Wireless"],
    "att": ["AT&T", "AT&T Mobility"],
    "tmobile": ["T-Mobile", "T-Mobile USA"],
    
    # UK
    "vodafone_uk": ["Vodafone UK", "Vodafone"],
    "ee": ["EE", "Everything Everywhere"],
    "o2_uk": ["O2 UK", "O2"],
    
    # Germany
    "vodafone_de": ["Vodafone DE"],
    "telekom_de": ["Deutsche Telekom", "T-Mobile DE"],
    
    # France
    "orange_fr": ["Orange France", "Orange"],
    "sfr": ["SFR"],
    
    # India
    "airtel": ["Airtel", "Bharti Airtel"],
    "jio": ["Jio", "Reliance Jio"],
}
```

### State/Area Code Handling
```python
# SMSPool does NOT support state/area code filtering
# Solution: US requests MUST use TextVerified

if area_code and country != "US":
    logger.warning(f"Area code {area_code} ignored for {country} (not supported)")
    area_code = None  # Clear filter
```

---

## 📋 Implementation in purchase_endpoints.py

### Current Flow (Line 195-280)
```python
# Step 1: Tier validation
# Step 2: Calculate cost
# Step 3: Check balance
# Step 4: Call TextVerified API
# Step 5: Create verification record
# Step 6: Deduct credits
```

### New Flow with SMSPool
```python
# After line 195 (tier validation)

# ROUTING LOGIC
if request.country == "US":
    # Existing TextVerified logic (lines 215-280)
    result = await tv_service.create_verification(...)
else:
    # NEW: SMSPool logic
    from app.services.providers.smspool_provider import SMSPoolProvider
    from app.services.filters.smspool_filters import SMSPoolFilters
    
    smspool = SMSPoolProvider(api_key=settings.SMSPOOL_API_KEY)
    
    # Map carrier filter
    operator = SMSPoolFilters.apply_carrier_filter(
        country=request.country,
        carrier=carrier
    )
    
    # Purchase with operator filter
    result = await smspool.purchase_number(
        country_code=request.country,
        service=request.service,
        filters={"operator": operator, "line_type": "mobile"}
    )
    
    # Map to TextVerified format for compatibility
    textverified_result = {
        "id": result["order_id"],
        "phone_number": result["phone_number"],
        "cost": result["cost"],
        "provider": "smspool",
        "assigned_carrier": result["operator"],
        # ... rest of fields
    }

# Continue with existing verification record creation (line 260+)
```

---

## 🗄️ Database Schema Updates

### Verification Model (Already Compatible!)
```python
# app/models/verification.py - NO CHANGES NEEDED
class Verification(BaseModel):
    provider = Column(String, default="textverified")  # Add "smspool"
    activation_id = Column(String)  # Works for both (TV ID or SMSPool order_id)
    requested_carrier = Column(String)  # User preference
    assigned_carrier = Column(String)  # Actual operator
    country = Column(String)  # Already supports international
```

**Migration**: Add index on `provider` column
```sql
CREATE INDEX idx_verifications_provider ON verifications(provider);
```

---

## 🧪 Testing Strategy

### Unit Tests
```python
# tests/unit/test_smspool_provider.py
async def test_purchase_with_operator_filter():
    provider = SMSPoolProvider(api_key="test")
    result = await provider.purchase_number(
        country_code="GB",
        service="telegram",
        filters={"operator": "Vodafone UK"}
    )
    assert result["operator"] == "Vodafone UK"

async def test_carrier_lookup():
    provider = SMSPoolProvider(api_key="test")
    lookup = await provider.carrier_lookup("+447700900123")
    assert lookup["carrier_type"] == "mobile"
```

### Integration Tests
```python
# tests/integration/test_provider_routing.py
async def test_us_routes_to_textverified():
    response = await client.post("/verification/request", json={
        "service": "telegram",
        "country": "US",
        "area_codes": ["415"]
    })
    verification = db.query(Verification).first()
    assert verification.provider == "textverified"

async def test_uk_routes_to_smspool():
    response = await client.post("/verification/request", json={
        "service": "telegram",
        "country": "GB",
        "carriers": ["vodafone_uk"]
    })
    verification = db.query(Verification).first()
    assert verification.provider == "smspool"
    assert verification.assigned_carrier == "Vodafone UK"
```

---

## 💰 Cost Tracking

### SMSPool Costs
- SMS Purchase: $0.10-$3.00 (country-dependent)
- Carrier Lookup: $0.005 per lookup
- Success Rate Query: FREE

### Pricing Strategy
```python
# app/services/pricing_calculator.py
PROVIDER_MARKUP = {
    "textverified": 1.15,  # 15% markup
    "smspool": 1.20        # 20% markup (higher international costs)
}

def calculate_sms_cost(provider: str, base_cost: float) -> float:
    return base_cost * PROVIDER_MARKUP[provider]
```

---

## 🚀 Deployment Checklist

- [ ] Add `SMSPOOL_API_KEY` to environment variables
- [ ] Create `app/services/providers/` directory
- [ ] Implement `SMSPoolProvider` class
- [ ] Implement `SMSPoolFilters` class
- [ ] Update `purchase_endpoints.py` routing logic
- [ ] Add database index on `provider` column
- [ ] Write unit tests (90%+ coverage)
- [ ] Write integration tests
- [ ] Deploy to staging
- [ ] Test with real SMSPool API
- [ ] Phased rollout (10% → 50% → 100%)

---

## 📊 Success Metrics

- ✅ 90%+ success rate for international verifications
- ✅ <3s average number acquisition time
- ✅ 100% carrier filter accuracy (via paid_lookup)
- ✅ Zero downtime during rollout
- ✅ Cost per verification within 20% of projections

---

**Next Steps**: Implement Phase 1 (SMSPool API Client) in `app/integrations/smspool_client.py`
