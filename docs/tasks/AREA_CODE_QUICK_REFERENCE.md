# Area Code Tier Gating - Quick Reference Guide

**Version**: v4.7.0
**Status**: Ready for QA
**Last Updated**: Current Session

---

## 🎯 Quick Overview

Tier-gated area code selection for voice verification and rentals with dynamic pricing.

### Pricing at a Glance
| Tier | Voice | Rental |
|------|-------|--------|
| Freemium | ❌ Blocked | ❌ Blocked |
| PAYG | +$0.25 | +$0.50 |
| Pro | ✅ Free | ✅ Free |
| Custom | ✅ Free | ✅ Free |

---

## 🔧 Technical Quick Reference

### Backend Endpoints

**Voice Verification**:
```http
POST /api/verification/request
Content-Type: application/json

{
  "service": "whatsapp",
  "country": "US",
  "capability": "voice",
  "area_codes": ["212"]  // Optional
}

Response:
{
  "cost": 2.75,
  "base_cost": 2.50,
  "area_code_fee": 0.25,
  "requested_area_code": "212"
}
```

**Rental**:
```http
POST /api/verification/rentals/request
Content-Type: application/json

{
  "service": "whatsapp",
  "duration_hours": 24.0,
  "area_code": "212"  // Optional
}

Response:
{
  "cost": 15.50,
  "base_cost": 15.00,
  "area_code_fee": 0.50,
  "requested_area_code": "212"
}
```

### Core Functions

**Pricing Calculator** (`app/services/pricing_calculator.py`):
```python
# Voice
PricingCalculator.calculate_voice_cost(
    db, user_id, provider_price=1.0, area_code="212"
)

# Rental
PricingCalculator.calculate_rental_cost(
    db, user_id, duration_hours=24, provider_cost=5.0, area_code="212"
)
```

### Tier Gating Logic
```python
if area_code:
    if tier == "freemium":
        raise ValueError("Area code not available for Freemium")

    if tier == "payg":
        fee = 0.25  # voice
        fee = 0.50  # rentals

    if tier in ["pro", "custom"]:
        fee = 0.00  # included
```

---

## 🎨 Frontend Quick Reference

### Pages
- **Voice**: `/voice-verify` → `templates/voice_verify_modern.html`
- **Rentals**: `/rentals` → `templates/rentals_modern.html`

### UI Elements

**Badge Display**:
```javascript
// PAYG
badge.textContent = '+$0.25';  // or '+$0.50'
badge.style.background = '#fef3c7';
badge.style.color = '#92400e';

// Pro/Custom
badge.textContent = 'Included';
badge.style.background = '#d1fae5';
badge.style.color = '#065f46';
```

**Pricing Breakdown**:
```javascript
{
  base_cost: 15.00,
  area_code_fee: 0.50,  // or 0.00
  total_cost: 15.50
}
```

---

## 🧪 Testing Quick Reference

### Run Standalone Tests
```bash
cd "/Users/machine/My Drive/Github Projects/Namaskah. app"
python3 tests/standalone_area_code_test.py
```

**Expected Output**: 10/10 tests passing (100%)

### Manual Test Users
```sql
-- Create test users
INSERT INTO users (id, email, subscription_tier, credits) VALUES
  ('test_freemium', 'freemium@test.com', 'freemium', 50.0),
  ('test_payg', 'payg@test.com', 'payg', 50.0),
  ('test_pro', 'pro@test.com', 'pro', 50.0),
  ('test_custom', 'custom@test.com', 'custom', 50.0);
```

### Quick Test Scenarios

**1. PAYG Voice with Area Code**:
- Login as payg@test.com
- Create voice verification with area code "212"
- Verify: Fee = $0.25, Total = Base + $0.25

**2. Pro Rental with Area Code**:
- Login as pro@test.com
- Create rental with area code "212"
- Verify: Fee = $0.00, Total = Base only

**3. Freemium Blocked**:
- Login as freemium@test.com
- Area code section should be hidden
- API should block if attempted

---

## 🐛 Common Issues & Solutions

### Issue: Area code section not showing
**Solution**: Check user tier via `/api/auth/me`

### Issue: Fee not calculated correctly
**Solution**: Check tier configuration in `subscription_tiers` table

### Issue: API returns 402 error
**Solution**: User doesn't have sufficient balance or wrong tier

### Issue: Tests failing with SQLite ARRAY error
**Solution**: Use standalone tests instead (`standalone_area_code_test.py`)

---

## 📊 Monitoring

### Key Metrics to Watch
- Area code usage rate by tier
- Fee revenue (voice vs rental)
- Tier upgrade conversions
- Error rates on area code requests
- API response times

### Expected Behavior
- API response: <500ms
- Error rate: <1%
- Fee accuracy: 100%
- Balance deduction: Accurate

---

## 🔍 Debugging

### Check User Tier
```python
user = db.query(User).filter(User.id == user_id).first()
print(f"Tier: {user.subscription_tier}")
```

### Check Tier Config
```python
from app.models.subscription_tier import SubscriptionTier
tier = db.query(SubscriptionTier).filter(
    SubscriptionTier.tier == "payg"
).first()
print(f"Has area code: {tier.has_area_code_selection}")
```

### Check Pricing Calculation
```python
from app.services.pricing_calculator import PricingCalculator
result = PricingCalculator.calculate_voice_cost(
    db, user_id, provider_price=1.0, area_code="212"
)
print(f"Base: ${result['base_cost']}")
print(f"Fee: ${result['area_code_fee']}")
print(f"Total: ${result['total_cost']}")
```

### Check API Request
```bash
# Voice with area code
curl -X POST http://localhost:8000/api/verification/request \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service": "whatsapp",
    "country": "US",
    "capability": "voice",
    "area_codes": ["212"]
  }'
```

---

## 📝 File Locations

### Backend
```
app/services/pricing_calculator.py          # Core pricing logic
app/api/verification/purchase_endpoints.py  # Voice API
app/api/verification/rental_endpoints.py    # Rental API
app/services/textverified_service.py        # Provider integration
```

### Frontend
```
templates/voice_verify_modern.html          # Voice page
templates/rentals_modern.html               # Rental page
```

### Tests
```
tests/standalone_area_code_test.py          # Standalone tests
tests/unit/test_voice_area_code_gating.py   # Voice unit tests
tests/unit/test_rental_area_code_gating.py  # Rental unit tests
```

### Documentation
```
docs/tasks/AREA_CODE_IMPLEMENTATION_STATUS.md      # Main status
docs/tasks/AREA_CODE_MANUAL_TESTING_CHECKLIST.md   # Test cases
docs/tasks/AREA_CODE_DEPLOYMENT_READINESS.md       # Deployment
docs/tasks/AREA_CODE_FINAL_REPORT.md               # Full report
docs/tasks/AREA_CODE_EXECUTIVE_SUMMARY.md          # Executive summary
docs/tasks/AREA_CODE_QUICK_REFERENCE.md            # This file
```

---

## 🚀 Deployment Commands

### Local Development
```bash
# Start server
./start.sh
# or
uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# Run tests
python3 tests/standalone_area_code_test.py
```

### Staging
```bash
# Deploy backend
git push staging main

# Deploy frontend
# (Frontend is bundled with backend)

# Run smoke tests
curl https://staging.namaskah.app/api/health
```

### Production
```bash
# Create backup
pg_dump $DATABASE_URL > backup.sql

# Deploy
git push production main

# Monitor
tail -f /var/log/namaskah/app.log
```

---

## 📞 Support

### Questions?
- **Technical**: Check implementation docs
- **Testing**: See manual testing checklist
- **Deployment**: See deployment readiness doc

### Need Help?
- Review `AREA_CODE_FINAL_REPORT.md` for comprehensive details
- Check `AREA_CODE_MANUAL_TESTING_CHECKLIST.md` for test cases
- See `AREA_CODE_DEPLOYMENT_READINESS.md` for deployment plan

---

## ✅ Quick Checklist

### Before Testing
- [ ] Test users created
- [ ] Server running locally
- [ ] Database seeded
- [ ] Browser DevTools open

### During Testing
- [ ] Test all 4 tiers
- [ ] Verify fee calculations
- [ ] Check balance deductions
- [ ] Test edge cases
- [ ] Document results

### After Testing
- [ ] Update test results
- [ ] Report bugs found
- [ ] Verify fixes
- [ ] Sign off on readiness

---

**Last Updated**: Current Session
**Version**: v4.7.0
**Status**: ✅ Ready for QA
