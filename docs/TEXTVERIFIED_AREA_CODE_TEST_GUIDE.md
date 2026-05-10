# TextVerified Area Code Verification - Test Guide

**Date**: May 10, 2026
**Purpose**: Verify area code support for voice verification and rentals
**Status**: Ready to run

---

## 🎯 What This Test Does

This test will verify:
1. ✅ SMS verification with area code (baseline - known to work)
2. ❓ Voice verification with area code (CRITICAL - needs verification)
3. ❓ Voice verification without area code
4. ❓ Rentals with area code (check if supported)
5. ❓ Voice area code success rate (multiple tests)

---

## 🚀 How to Run

### Step 1: Set Environment Variables

```bash
# Set your TextVerified credentials
export TEXTVERIFIED_API_KEY="your_api_key_here"
export TEXTVERIFIED_USERNAME="your_username_here"
```

### Step 2: Run the Test

```bash
cd "/Users/machine/My Drive/Github Projects/Namaskah. app"
python3 scripts/test_textverified_area_codes.py
```

### Step 3: Review Results

The test will output:
- ✅ Success indicators
- ❌ Failure indicators
- 📊 Success rate statistics
- 🎯 Final recommendation

---

## 📊 Expected Output

### If Area Codes Work for Voice

```
================================================================================
TEST 2: Voice Verification with Area Code (CRITICAL TEST)
================================================================================
✅ Voice Verification Created
   Verification ID: abc123
   Phone Number: +12135551234
   Requested Area Code: 213
   Assigned Area Code: 213
   Area Code Matched: True
   Cost: $3.50
   ✅ AREA CODE HONORED - Voice supports area codes!
   ✅ Cancelled to avoid charges

================================================================================
FINAL RECOMMENDATION
================================================================================

✅ DEPLOY VOICE UI WITH AREA CODE OPTION
   - Area codes are honored for voice verification
   - UI implementation is correct
   - Monitor success rate in production
```

### If Area Codes DON'T Work for Voice

```
================================================================================
TEST 2: Voice Verification with Area Code (CRITICAL TEST)
================================================================================
✅ Voice Verification Created
   Verification ID: abc123
   Phone Number: +14795551234
   Requested Area Code: 213
   Assigned Area Code: 479
   Area Code Matched: False
   Cost: $3.50
   ❌ AREA CODE NOT HONORED - Voice does NOT support area codes!
      Requested: 213
      Got: 479
   ✅ Cancelled to avoid charges

================================================================================
FINAL RECOMMENDATION
================================================================================

❌ DO NOT DEPLOY VOICE UI WITH AREA CODE OPTION
   - Area codes are NOT honored for voice verification
   - Remove area code option from voice UI
   - Update documentation to reflect SMS-only support
```

---

## 🎯 What to Do Based on Results

### Scenario 1: Voice Area Codes Work ✅

**Actions**:
1. ✅ Deploy voice UI as-is (area code option stays)
2. ✅ Update documentation: "CONFIRMED - Voice supports area codes"
3. ✅ Monitor success rate in production
4. ✅ Proceed with deployment

**Files to Update**:
- `docs/VOICE_UI_IMPROVEMENTS_COMPLETE.md` - Add "CONFIRMED" badge
- `docs/VOICE_UI_STABILITY_VERIFICATION_SUMMARY.md` - Update status to "VERIFIED"
- `docs/CRITICAL_PROVIDER_VERIFICATION_NEEDED.md` - Mark as resolved

### Scenario 2: Voice Area Codes DON'T Work ❌

**Actions**:
1. ❌ Remove area code option from voice UI
2. ❌ Update all documentation
3. ❌ Add "SMS only" disclaimer
4. ❌ Revert voice UI changes

**Files to Update**:
- `templates/voice_verify_modern.html` - Remove advanced options section
- `docs/VOICE_UI_IMPROVEMENTS_COMPLETE.md` - Document limitation
- `docs/VOICE_UI_STABILITY_VERIFICATION_SUMMARY.md` - Update recommendation
- All other docs - Add "SMS only" notes

**Code Changes**:
```html
<!-- Remove this section from voice_verify_modern.html -->
<div id="voice-advanced-options">
    <!-- Area code selection -->
</div>

<!-- Add this disclaimer instead -->
<div class="info-box">
    ℹ️ Area code selection is available for SMS verification only.
    Voice verification uses any available number.
</div>
```

### Scenario 3: Rentals Support Area Codes ✅

**Actions**:
1. ✅ Add area_code parameter to create_reservation()
2. ✅ Add area code UI to rentals page
3. ✅ Test thoroughly
4. ✅ Document support

**Code Changes**:
```python
# In textverified_service.py
async def create_reservation(
    self,
    service: str,
    country: str = "US",
    duration_hours: float = 24.0,
    area_code: Optional[str] = None  # ← Add this
) -> Dict[str, Any]:
    # ... existing code ...

    reservation = await asyncio.to_thread(
        self.client.reservations.create,
        service_name=service,
        duration=duration_minutes,
        area_code=area_code,  # ← Add this if supported
    )
```

### Scenario 4: Rentals DON'T Support Area Codes ❌

**Actions**:
1. ✅ Current implementation is correct
2. ✅ Document limitation
3. ✅ No changes needed

---

## 💰 Cost Considerations

**Each test will**:
- Create a verification/rental
- Cancel it immediately
- Cost: ~$0.10 per test (cancelled verifications are usually refunded)

**Total estimated cost**: $1-2 for all tests

**Note**: Tests cancel verifications immediately to minimize costs. TextVerified typically refunds cancelled verifications.

---

## 🐛 Troubleshooting

### Error: "TextVerified credentials not set"

**Solution**:
```bash
export TEXTVERIFIED_API_KEY="your_key"
export TEXTVERIFIED_USERNAME="your_username"
```

### Error: "TextVerified service not enabled"

**Solution**:
- Check credentials are correct
- Verify textverified library is installed: `pip install textverified`
- Check API key has sufficient balance

### Error: "Failed to create verification"

**Possible causes**:
- Insufficient balance
- Service not available
- Rate limiting
- Invalid area code

**Solution**:
- Check TextVerified account balance
- Try different service (e.g., "telegram" instead of "google")
- Wait a few minutes and retry

---

## 📝 Manual Testing (Alternative)

If automated test fails, you can test manually:

### Test Voice with Area Code

```python
from app.services.textverified_service import TextVerifiedService
import asyncio

async def test():
    service = TextVerifiedService()

    # Create voice verification with area code 213
    result = await service.create_verification(
        service="google",
        area_code="213",
        capability="voice"
    )

    print(f"Requested: 213")
    print(f"Got: {result['assigned_area_code']}")
    print(f"Match: {result['area_code_matched']}")

    # Cancel to avoid charges
    await service.cancel_verification(result['id'])

asyncio.run(test())
```

---

## 📊 Success Criteria

### For Voice Verification

**Area codes are considered SUPPORTED if**:
- ✅ Success rate ≥ 80%
- ✅ Assigned area code matches requested area code
- ✅ Consistent behavior across multiple tests

**Area codes are considered NOT SUPPORTED if**:
- ❌ Success rate < 80%
- ❌ Assigned area code rarely matches requested
- ❌ Inconsistent or random behavior

### For Rentals

**Area codes are considered SUPPORTED if**:
- ✅ API accepts area_code parameter
- ✅ Assigned number matches requested area code
- ✅ No errors when passing area_code

**Area codes are considered NOT SUPPORTED if**:
- ❌ API rejects area_code parameter (TypeError)
- ❌ API ignores area_code parameter
- ❌ Assigned number doesn't match requested

---

## 🎯 Next Steps After Testing

### If All Tests Pass ✅

1. Update documentation with "CONFIRMED" status
2. Deploy voice UI to production
3. Monitor success rates
4. Collect user feedback

### If Voice Tests Fail ❌

1. Remove area code option from voice UI
2. Update all documentation
3. Add "SMS only" disclaimers
4. Redeploy with corrections

### If Rental Tests Pass ✅

1. Implement area code support for rentals
2. Add UI for area code selection
3. Test thoroughly
4. Deploy as enhancement

---

## 📞 Support

**Questions?**
- Check TextVerified API docs: https://textverified.com/docs
- Review test output carefully
- Check logs for detailed errors

**Issues?**
- Verify credentials are correct
- Check account balance
- Try different services
- Contact TextVerified support

---

**Ready to run? Execute the test script now!**

```bash
python3 scripts/test_textverified_area_codes.py
```

---

**Created**: May 10, 2026
**Status**: Ready to run
**Estimated time**: 5-10 minutes
**Estimated cost**: $1-2
