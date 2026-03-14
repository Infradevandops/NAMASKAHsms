# TextVerified Carrier Quick Reference

## 🎯 TL;DR - The Truth About Carriers

**What users think they're selecting**: Specific carriers (Verizon, AT&T, T-Mobile, etc.)  
**What TextVerified actually returns**: Generic types ("Mobile", "Landline", "VOIP")  
**What this means**: Carrier selection is a **preference**, not a **guarantee**

---

## 📋 Carrier Values Reference

### What Users Can Select (Frontend)
```javascript
const AVAILABLE_CARRIERS = [
  { id: "verizon", name: "Verizon" },
  { id: "att", name: "AT&T" },
  { id: "tmobile", name: "T-Mobile" },
  { id: "sprint", name: "Sprint" },
  { id: "us_cellular", name: "US Cellular" }
];
```

### What We Send to TextVerified
```python
carrier_select_option = ["us_cellular"]  # Normalized format
```

### What TextVerified Returns
```python
assigned_carrier = "Mobile"  # Generic type, NOT specific carrier
```

### Possible Return Values
| Value | Meaning | Frequency |
|-------|---------|-----------|
| `"Mobile"` | Any mobile carrier | ~95% |
| `"Landline"` | Traditional phone line | ~3% |
| `"VOIP"` | Internet-based number | ~2% |
| `null` / `""` | Unknown | <1% |

---

## 🔄 Carrier Normalization

### Input → Normalized → TextVerified
```python
"US Cellular"  → "us_cellular"  → ["us_cellular"]
"AT&T"         → "att"          → ["att"]
"T-Mobile"     → "t_mobile"     → ["t_mobile"]
"Verizon"      → "verizon"      → ["verizon"]
"Sprint"       → "sprint"       → ["sprint"]
```

### Normalization Rules
```python
def normalize_carrier(carrier: str) -> str:
    return carrier.lower().replace(" ", "_").replace("&", "")
```

---

## ✅ Validation Logic (Current)

### Mobile Fallback Acceptance
```python
# These are considered valid mobile carriers
MOBILE_KEYWORDS = ["mobile", "cellular", "wireless"]

# User requests: "us_cellular"
# TextVerified returns: "Mobile"
# Result: ✅ ACCEPTED (mobile fallback)

# User requests: "us_cellular"
# TextVerified returns: "Landline"
# Result: ❌ REJECTED (type mismatch)
```

### Validation Flow
```
1. User selects carrier → "US Cellular"
2. Normalize → "us_cellular"
3. Send to TextVerified → ["us_cellular"]
4. TextVerified returns → "Mobile"
5. Check if mobile fallback → YES
6. Accept verification → ✅ SUCCESS
```

---

## 🚨 Common Issues

### Issue 1: Carrier Mismatch (FIXED)
**Before Fix**:
```
User requests: us_cellular
TextVerified returns: Mobile
Validation: us_cellular != mobile → FAIL
Result: 409 Conflict
```

**After Fix**:
```
User requests: us_cellular
TextVerified returns: Mobile
Validation: Mobile is valid fallback → PASS
Result: 201 Created
```

### Issue 2: Landline Assignment
```
User requests: verizon (mobile)
TextVerified returns: Landline
Validation: Not a mobile fallback → FAIL
Result: 409 Conflict (CORRECT BEHAVIOR)
```

---

## 📊 Carrier Availability Matrix

### US Mobile Carriers (Real World)
| Carrier | Market Share | TextVerified Support | Success Rate |
|---------|--------------|---------------------|--------------|
| Verizon | 31% | ⚠️ Best Effort | ~85% |
| AT&T | 28% | ⚠️ Best Effort | ~82% |
| T-Mobile | 26% | ⚠️ Best Effort | ~80% |
| US Cellular | 1.5% | ⚠️ Best Effort | ~60% |
| Sprint (Legacy) | 0% | ❌ Merged with T-Mobile | ~0% |

**Note**: Success rates are estimates. TextVerified doesn't guarantee specific carriers.

---

## 🛠️ Developer Guide

### How to Add a New Carrier

1. **Update Frontend List** (`carrier_endpoints.py`):
```python
FALLBACK_CARRIERS = [
    # ... existing carriers ...
    {"id": "boost", "name": "Boost Mobile"},  # Add new
]
```

2. **No Backend Changes Needed**:
- Normalization happens automatically
- Validation accepts any mobile carrier
- TextVerified handles the request

3. **Test the Flow**:
```bash
curl -X POST /api/verification/request \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "service": "telegram",
    "country": "US",
    "carriers": ["boost"]
  }'
```

### How to Debug Carrier Issues

1. **Check Logs**:
```bash
grep "Carrier validation" logs/app.log
grep "Carrier fallback" logs/app.log
grep "Carrier mismatch" logs/app.log
```

2. **Check Database**:
```sql
SELECT 
    requested_carrier,
    assigned_carrier,
    operator,
    status
FROM verifications
WHERE requested_carrier IS NOT NULL
ORDER BY created_at DESC
LIMIT 20;
```

3. **Check Metrics**:
```python
# Add to monitoring
carrier_mismatch_total
carrier_fallback_accepted_total
carrier_validation_failed_total
```

---

## 🎯 Best Practices

### For Product/UX
1. ✅ Use "Prefer Carrier" instead of "Select Carrier"
2. ✅ Add tooltip: "We'll try to match your preference"
3. ✅ Show actual carrier after purchase
4. ✅ Set expectations: "Subject to availability"

### For Engineering
1. ✅ Always accept "Mobile" for mobile carrier requests
2. ✅ Log all carrier mismatches for analytics
3. ✅ Monitor carrier success rates
4. ✅ Consider carrier lookup API for accuracy

### For Support
1. ✅ Explain carrier selection is best-effort
2. ✅ Offer refund if wrong carrier type (mobile vs landline)
3. ✅ Suggest area code filtering as alternative
4. ✅ Escalate if specific carrier is critical

---

## 🔮 Future Enhancements

### Phase 1: Analytics (This Month)
```python
# Track carrier preference vs actual
metrics = {
    "requested": "verizon",
    "assigned": "Mobile",
    "success": True,
    "timestamp": "2026-03-14T18:56:33Z"
}
```

### Phase 2: Carrier Lookup API (Next Quarter)
```python
# Integrate real carrier lookup
actual_carrier = await carrier_lookup_api.lookup(phone_number)
# Returns: "Verizon Wireless" (specific)
```

### Phase 3: Smart Carrier Selection (Q3 2026)
```python
# ML model predicts carrier availability
recommended_carriers = ml_model.predict_available_carriers(
    service="telegram",
    area_code="415",
    time_of_day="evening"
)
# Returns: ["att", "tmobile"] (high availability)
```

---

## 📞 Quick Troubleshooting

### User Can't Create Verification with Carrier
1. Check if carrier is in allowed list
2. Verify user tier allows carrier filtering (PAYG+)
3. Check TextVerified API status
4. Review recent logs for errors
5. Try without carrier filter to isolate issue

### All Carrier Requests Failing
1. Check if fix is deployed (mobile fallback logic)
2. Verify TextVerified API is responding
3. Check if validation logic was reverted
4. Review error logs for patterns

### Specific Carrier Always Fails
1. That carrier may not be available in TextVerified
2. Consider removing from frontend list
3. Add to documentation as "limited availability"
4. Suggest alternative carriers to users

---

## 📚 Related Documentation

- [TEXTVERIFIED_CARRIER_ANALYSIS.md](./TEXTVERIFIED_CARRIER_ANALYSIS.md) - Full analysis
- [VERIFICATION_TROUBLESHOOTING.md](./VERIFICATION_TROUBLESHOOTING.md) - User guide
- [RELIABILITY_REPORT.md](./RELIABILITY_REPORT.md) - System reliability

---

**Last Updated**: March 14, 2026  
**Maintained By**: Engineering Team  
**Status**: ACTIVE
