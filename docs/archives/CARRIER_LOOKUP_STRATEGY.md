# Carrier Lookup Strategy

**Date**: March 14, 2026  
**Status**: Decision Made  
**Recommendation**: Google libphonenumber

---

## Problem Statement

TextVerified API does not return specific carrier information in responses. The `assigned_carrier` field always contains generic types ("Mobile", "Landline", "VOIP") rather than specific carrier names (Verizon, AT&T, T-Mobile). This is a fundamental API limitation, not a bug.

---

## Evaluated Options

### Option 1: Commercial Carrier Lookup APIs
- **Examples**: TelcoAPI, Twilio Lookup, Neustar, Bandwidth
- **Cost**: $50-500/month for 10k-100k lookups
- **Latency**: 100-300ms per lookup
- **Accuracy**: 98%+
- **Verdict**: ❌ Too expensive, adds latency to critical path

### Option 2: Numverify API
- **Cost**: Free tier (100 requests/month), $9.99/month (10k requests)
- **Latency**: 200-500ms per lookup
- **Accuracy**: 98%+ for US numbers
- **Verdict**: ⚠️ Good fallback, but adds latency and requires external API

### Option 3: Google libphonenumber ✅ SELECTED
- **Cost**: Free (open source)
- **Latency**: <5ms (offline, no API call)
- **Accuracy**: 95%+ for US numbers
- **Pros**: 
  - Industry standard (used by Google, Facebook, Uber)
  - Offline validation (no external dependencies)
  - 60x faster than commercial APIs
  - Validates format, extracts area code, detects number type
  - Zero cost
- **Cons**: Does not return specific carrier name (only type: mobile/landline/voip)
- **Verdict**: ✅ Best choice for current needs

### Option 4: Internal CarrierAnalytics Only
- **Cost**: Free (uses existing database)
- **Latency**: <10ms (database query)
- **Accuracy**: Grows over time (0% → 95%+ after 1000+ verifications)
- **Verdict**: ✅ Already implemented, complements libphonenumber

---

## Recommended Solution: Google libphonenumber

### Why libphonenumber?

1. **No Cost**: Free, open source, no API keys or subscriptions
2. **No Latency**: Offline validation, <5ms per number
3. **Industry Standard**: Used by Google, Facebook, Uber, Stripe
4. **Reliability**: No external API dependency, no rate limits
5. **Validation**: Catches invalid numbers before TextVerified call (saves credits)
6. **Type Detection**: Identifies mobile vs landline vs VOIP

### What It Does

```python
import phonenumbers

# Parse and validate
number = phonenumbers.parse("+14155552671", "US")
phonenumbers.is_valid_number(number)  # True/False

# Extract components
number.country_code  # 1
number.national_number  # 4155552671

# Get number type
from phonenumbers import phonenumberutil
phonenumberutil.number_type(number)  # MOBILE, FIXED_LINE, etc.

# Get carrier (if available)
from phonenumbers import carrier
carrier.name_for_number(number, "en_US")  # "Verizon" (if available)
```

### What It Doesn't Do

- Does not guarantee specific carrier assignment from TextVerified
- Does not provide real-time carrier lookup
- Limited carrier name database (not all carriers available)

### Implementation Plan

**Phase 2 (Q2 2026)**: Add libphonenumber validation

1. Add `phonenumbers` to `requirements.txt`
2. Create `app/services/phone_validator.py`:
   ```python
   def validate_phone_number(phone: str, country: str = "US") -> dict:
       """Validate phone number and extract metadata."""
       try:
           number = phonenumbers.parse(phone, country)
           if not phonenumbers.is_valid_number(number):
               return {"valid": False, "error": "Invalid phone number"}
           
           return {
               "valid": True,
               "country_code": number.country_code,
               "national_number": number.national_number,
               "type": get_number_type(number),
               "area_code": extract_area_code(number),
           }
       except Exception as e:
           return {"valid": False, "error": str(e)}
   ```

3. Integrate into purchase endpoint:
   ```python
   # Before calling TextVerified
   validation = validate_phone_number(phone_number)
   if not validation["valid"]:
       raise HTTPException(status_code=400, detail=validation["error"])
   ```

4. Benefits:
   - Catch invalid numbers early (reduce wasted credits)
   - Extract area code for fallback logic
   - Detect number type (mobile/landline)
   - No latency impact (offline validation)

### Integration with Existing Systems

**CarrierAnalytics** (already implemented):
- Tracks carrier preferences vs actual assignments
- Builds success rates from historical data
- Complements libphonenumber validation

**TextVerified API**:
- Carrier preference still sent via `carrier_select_option`
- libphonenumber validates format before sending
- No changes to TextVerified integration

---

## Future Enhancements (Out of Scope)

If carrier guarantee becomes a premium feature:

1. **Phase 3 (Q3 2026)**: Add Numverify API as optional enrichment
   - Post-verification carrier lookup (not blocking)
   - Enrich CarrierAnalytics with real carrier data
   - Enable "Carrier Guarantee" premium tier

2. **Phase 4 (Q4 2026)**: Consider commercial API only if:
   - Volume exceeds 100k verifications/month
   - Customers demand carrier guarantees
   - ROI justifies $50-500/month cost

---

## Decision Record

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Primary Solution** | Google libphonenumber | Free, fast, reliable, industry standard |
| **Implementation Phase** | Q2 2026 | After Milestone 5 completion |
| **Effort Estimate** | 2-3 hours | Simple integration, no external dependencies |
| **Cost** | $0 | Open source, no subscriptions |
| **Latency Impact** | <5ms | Offline validation, no API calls |
| **Fallback Strategy** | CarrierAnalytics | Historical data for success rates |

---

## References

- [Google libphonenumber](https://github.com/google/libphonenumber)
- [Python phonenumbers library](https://github.com/daviddrysdale/python-phonenumbers)
- [Numverify API](https://numverify.com/) (future fallback)
- [Twilio Lookup](https://www.twilio.com/lookup) (alternative)

---

**Status**: Ready for implementation in Q2 2026  
**Owner**: Engineering Team  
**Last Updated**: March 14, 2026
