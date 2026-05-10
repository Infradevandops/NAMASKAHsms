# Area Code Tier Gating - Manual Testing Checklist

**Date**: Ready for Testing
**Status**: Implementation Complete - Ready for QA
**Tester**: _____________

---

## ✅ Pre-Testing Setup

### Environment Setup
- [ ] Local development server running (`./start.sh` or `uvicorn main:app`)
- [ ] Database migrations applied
- [ ] Test users created for all 4 tiers:
  - [ ] Freemium user (email: freemium@test.com)
  - [ ] PAYG user (email: payg@test.com)
  - [ ] Pro user (email: pro@test.com)
  - [ ] Custom user (email: custom@test.com)
- [ ] Each test user has sufficient credits ($50+)
- [ ] Browser DevTools open (Network + Console tabs)

### Test Data
```sql
-- Create test users (run in database)
INSERT INTO users (id, email, subscription_tier, credits) VALUES
  ('test_freemium', 'freemium@test.com', 'freemium', 50.0),
  ('test_payg', 'payg@test.com', 'payg', 50.0),
  ('test_pro', 'pro@test.com', 'pro', 50.0),
  ('test_custom', 'custom@test.com', 'custom', 50.0);
```

---

## 🧪 Test Suite 1: Voice Verification

### Test 1.1: Freemium User - Area Code Hidden
**User**: freemium@test.com

**Steps**:
1. [ ] Login as Freemium user
2. [ ] Navigate to Voice Verification page (`/voice-verify`)
3. [ ] Select a service (e.g., WhatsApp)
4. [ ] Click "Advanced Options"

**Expected Results**:
- [ ] Area code section is NOT visible
- [ ] No area code dropdown shown
- [ ] No badge or help text displayed
- [ ] Can proceed with verification without area code

**Actual Results**: _____________

**Status**: ⬜ Pass ⬜ Fail

---

### Test 1.2: PAYG User - Area Code with Fee
**User**: payg@test.com

**Steps**:
1. [ ] Login as PAYG user
2. [ ] Navigate to Voice Verification page
3. [ ] Select a service
4. [ ] Click "Advanced Options"
5. [ ] Observe area code section

**Expected Results**:
- [ ] Area code section IS visible
- [ ] Badge shows "+$0.25" in yellow background
- [ ] Help text: "$0.25 fee applies when area code is selected. Upgrade to Pro..."
- [ ] Upgrade link present and clickable
- [ ] Area code dropdown populated with options

**Actual Results**: _____________

**Status**: ⬜ Pass ⬜ Fail

---

### Test 1.3: PAYG User - Create Voice with Area Code
**User**: payg@test.com

**Steps**:
1. [ ] Continue from Test 1.2
2. [ ] Select area code "212 - New York, NY"
3. [ ] Click "Continue"
4. [ ] Review pricing breakdown
5. [ ] Note current balance
6. [ ] Click "Request Verification"
7. [ ] Wait for response

**Expected Results**:
- [ ] Pricing shows base cost + $0.25 area code fee
- [ ] Total cost = base + $0.25
- [ ] API call includes `area_code: "212"`
- [ ] Response includes `area_code_fee: 0.25`
- [ ] Balance deducted = total cost (base + $0.25)
- [ ] Success message shows fee breakdown
- [ ] Phone number received with 212 area code

**Actual Results**:
- Base cost: $_______
- Area code fee: $_______
- Total cost: $_______
- Balance before: $_______
- Balance after: $_______
- Phone number: _____________

**Status**: ⬜ Pass ⬜ Fail

---

### Test 1.4: PAYG User - Create Voice WITHOUT Area Code
**User**: payg@test.com

**Steps**:
1. [ ] Navigate to Voice Verification page
2. [ ] Select a service
3. [ ] Click "Advanced Options"
4. [ ] Leave area code as "Any Area Code (Fastest)"
5. [ ] Click "Continue" and "Request Verification"

**Expected Results**:
- [ ] No area code fee charged
- [ ] Total cost = base cost only
- [ ] Response shows `area_code_fee: 0.0`
- [ ] Balance deducted = base cost only

**Actual Results**: _____________

**Status**: ⬜ Pass ⬜ Fail

---

### Test 1.5: Pro User - Area Code Included
**User**: pro@test.com

**Steps**:
1. [ ] Login as Pro user
2. [ ] Navigate to Voice Verification page
3. [ ] Select a service
4. [ ] Click "Advanced Options"
5. [ ] Observe area code section

**Expected Results**:
- [ ] Area code section IS visible
- [ ] Badge shows "Included" in green background
- [ ] Help text: "Area code selection is included in your plan..."
- [ ] No upgrade prompt
- [ ] Area code dropdown available

**Actual Results**: _____________

**Status**: ⬜ Pass ⬜ Fail

---

### Test 1.6: Pro User - Create Voice with Area Code
**User**: pro@test.com

**Steps**:
1. [ ] Continue from Test 1.5
2. [ ] Select area code "415 - San Francisco, CA"
3. [ ] Click "Continue" and "Request Verification"

**Expected Results**:
- [ ] NO area code fee charged
- [ ] Total cost = base cost only
- [ ] Response shows `area_code_fee: 0.0`
- [ ] Balance deducted = base cost only
- [ ] Phone number received with 415 area code

**Actual Results**:
- Total cost: $_______
- Area code fee: $_______
- Balance deducted: $_______
- Phone number: _____________

**Status**: ⬜ Pass ⬜ Fail

---

### Test 1.7: Custom User - Area Code Included
**User**: custom@test.com

**Steps**:
1. [ ] Login as Custom user
2. [ ] Navigate to Voice Verification page
3. [ ] Select a service, expand advanced options
4. [ ] Select area code "305 - Miami, FL"
5. [ ] Create verification

**Expected Results**:
- [ ] Badge shows "Included" in green
- [ ] NO area code fee charged
- [ ] Total cost = base cost only
- [ ] Phone number with 305 area code

**Actual Results**: _____________

**Status**: ⬜ Pass ⬜ Fail

---

## 🧪 Test Suite 2: Number Rentals

### Test 2.1: Freemium User - Rentals Blocked
**User**: freemium@test.com

**Steps**:
1. [ ] Login as Freemium user
2. [ ] Navigate to Rentals page (`/rentals`)
3. [ ] Select a service
4. [ ] Select duration (24h)
5. [ ] Observe area code section

**Expected Results**:
- [ ] Area code section is NOT visible
- [ ] No area code dropdown
- [ ] No badge or help text
- [ ] (Note: Rentals require Pro+ tier, so request will fail anyway)

**Actual Results**: _____________

**Status**: ⬜ Pass ⬜ Fail

---

### Test 2.2: PAYG User - Rentals Blocked (Pro+ Required)
**User**: payg@test.com

**Steps**:
1. [ ] Login as PAYG user
2. [ ] Navigate to Rentals page
3. [ ] Select service and duration
4. [ ] Click "Rent Number"

**Expected Results**:
- [ ] Error: "Number rentals require Pro tier or higher"
- [ ] Request blocked at API level
- [ ] No credits deducted

**Actual Results**: _____________

**Status**: ⬜ Pass ⬜ Fail

---

### Test 2.3: Pro User - Rental Area Code Section
**User**: pro@test.com

**Steps**:
1. [ ] Login as Pro user
2. [ ] Navigate to Rentals page
3. [ ] Select a service (e.g., WhatsApp)
4. [ ] Select duration (24h - $15.00)
5. [ ] Observe area code section

**Expected Results**:
- [ ] Area code section IS visible
- [ ] Badge shows "Included" in green
- [ ] Help text: "Area code selection is included..."
- [ ] Area code dropdown with 10 cities
- [ ] Pricing breakdown section visible

**Actual Results**: _____________

**Status**: ⬜ Pass ⬜ Fail

---

### Test 2.4: Pro User - Rental WITHOUT Area Code
**User**: pro@test.com

**Steps**:
1. [ ] Continue from Test 2.3
2. [ ] Leave area code as "Any Area Code"
3. [ ] Note pricing breakdown
4. [ ] Click "Rent Number"

**Expected Results**:
- [ ] Pricing breakdown shows:
  - Base Cost: $15.00
  - Area Code Fee: (not shown or $0.00)
  - Total: $15.00
- [ ] No area code fee charged
- [ ] Balance deducted = $15.00
- [ ] Rental created successfully

**Actual Results**:
- Base cost: $_______
- Total cost: $_______
- Balance deducted: $_______

**Status**: ⬜ Pass ⬜ Fail

---

### Test 2.5: Pro User - Rental WITH Area Code
**User**: pro@test.com

**Steps**:
1. [ ] Navigate to Rentals page
2. [ ] Select service and duration (24h)
3. [ ] Select area code "212 - New York, NY"
4. [ ] Observe pricing breakdown update
5. [ ] Note current balance
6. [ ] Click "Rent Number"

**Expected Results**:
- [ ] Pricing breakdown shows:
  - Base Cost: $15.00
  - Area Code Fee: $0.00 (or not shown)
  - Total: $15.00
- [ ] NO extra fee for area code (included in Pro)
- [ ] API call includes `area_code: "212"`
- [ ] Response shows `area_code_fee: 0.0`
- [ ] Balance deducted = $15.00 (no extra fee)
- [ ] Phone number received with 212 area code
- [ ] Success message shows cost breakdown

**Actual Results**:
- Base cost: $_______
- Area code fee: $_______
- Total cost: $_______
- Balance before: $_______
- Balance after: $_______
- Phone number: _____________

**Status**: ⬜ Pass ⬜ Fail

---

### Test 2.6: Custom User - Rental with Area Code
**User**: custom@test.com

**Steps**:
1. [ ] Login as Custom user
2. [ ] Navigate to Rentals page
3. [ ] Select service, duration (72h - $35.00)
4. [ ] Select area code "415 - San Francisco, CA"
5. [ ] Create rental

**Expected Results**:
- [ ] Badge shows "Included" in green
- [ ] NO area code fee charged
- [ ] Total cost = base cost only ($35.00)
- [ ] Phone number with 415 area code

**Actual Results**: _____________

**Status**: ⬜ Pass ⬜ Fail

---

## 🧪 Test Suite 3: Edge Cases

### Test 3.1: Insufficient Balance with Fee
**User**: payg@test.com (set credits to $2.00)

**Steps**:
1. [ ] Set PAYG user credits to $2.00
2. [ ] Try to create voice verification with area code
3. [ ] Base cost ~$2.50, area code fee $0.25, total ~$2.75

**Expected Results**:
- [ ] Error: "Insufficient balance"
- [ ] Shows required amount vs available
- [ ] No credits deducted
- [ ] No verification created

**Actual Results**: _____________

**Status**: ⬜ Pass ⬜ Fail

---

### Test 3.2: Area Code Unavailable
**User**: pro@test.com

**Steps**:
1. [ ] Select a service with limited area code availability
2. [ ] Select a rare area code
3. [ ] Attempt to create verification

**Expected Results**:
- [ ] Error or fallback to alternative area code
- [ ] User notified of unavailability
- [ ] Alternative area codes suggested (if applicable)
- [ ] Credits not deducted if failed

**Actual Results**: _____________

**Status**: ⬜ Pass ⬜ Fail

---

### Test 3.3: Upgrade Link Functionality
**User**: payg@test.com

**Steps**:
1. [ ] Navigate to Voice or Rental page
2. [ ] Observe help text with upgrade link
3. [ ] Click "Upgrade to Pro" link

**Expected Results**:
- [ ] Redirects to `/billing/tiers` page
- [ ] Tier comparison page loads
- [ ] Can view Pro tier benefits
- [ ] Can initiate upgrade process

**Actual Results**: _____________

**Status**: ⬜ Pass ⬜ Fail

---

### Test 3.4: Real-Time Pricing Update
**User**: payg@test.com (Rental page)

**Steps**:
1. [ ] Navigate to Rentals page
2. [ ] Select service and duration
3. [ ] Note pricing breakdown
4. [ ] Select area code
5. [ ] Observe pricing update
6. [ ] Deselect area code (back to "Any")
7. [ ] Observe pricing update again

**Expected Results**:
- [ ] Pricing updates in real-time
- [ ] Area code fee appears when selected
- [ ] Area code fee disappears when deselected
- [ ] Total cost recalculates correctly
- [ ] No page refresh needed

**Actual Results**: _____________

**Status**: ⬜ Pass ⬜ Fail

---

## 🧪 Test Suite 4: Cross-Browser Testing

### Test 4.1: Chrome
- [ ] Voice page renders correctly
- [ ] Rental page renders correctly
- [ ] Badges display properly
- [ ] Pricing updates work
- [ ] API calls successful

**Status**: ⬜ Pass ⬜ Fail

---

### Test 4.2: Firefox
- [ ] Voice page renders correctly
- [ ] Rental page renders correctly
- [ ] Badges display properly
- [ ] Pricing updates work
- [ ] API calls successful

**Status**: ⬜ Pass ⬜ Fail

---

### Test 4.3: Safari
- [ ] Voice page renders correctly
- [ ] Rental page renders correctly
- [ ] Badges display properly
- [ ] Pricing updates work
- [ ] API calls successful

**Status**: ⬜ Pass ⬜ Fail

---

### Test 4.4: Mobile (Chrome/Safari)
- [ ] Pages responsive on mobile
- [ ] Dropdowns work on touch
- [ ] Badges readable
- [ ] Pricing breakdown fits screen
- [ ] Can complete full flow

**Status**: ⬜ Pass ⬜ Fail

---

## 🧪 Test Suite 5: API Validation

### Test 5.1: Voice API Request Format
**User**: payg@test.com

**Steps**:
1. [ ] Open DevTools Network tab
2. [ ] Create voice verification with area code "212"
3. [ ] Inspect request payload

**Expected Request**:
```json
{
  "service": "whatsapp",
  "country": "US",
  "capability": "voice",
  "area_codes": ["212"]
}
```

**Actual Request**: _____________

**Status**: ⬜ Pass ⬜ Fail

---

### Test 5.2: Voice API Response Format
**Expected Response**:
```json
{
  "success": true,
  "verification_id": "...",
  "phone_number": "+12125551234",
  "cost": 2.75,
  "base_cost": 2.50,
  "area_code_fee": 0.25,
  "requested_area_code": "212",
  "assigned_area_code": "212"
}
```

**Actual Response**: _____________

**Status**: ⬜ Pass ⬜ Fail

---

### Test 5.3: Rental API Request Format
**User**: pro@test.com

**Expected Request**:
```json
{
  "service": "whatsapp",
  "duration_hours": 24.0,
  "area_code": "212"
}
```

**Actual Request**: _____________

**Status**: ⬜ Pass ⬜ Fail

---

### Test 5.4: Rental API Response Format
**Expected Response**:
```json
{
  "rental_id": "...",
  "phone_number": "+12125551234",
  "cost": 15.00,
  "base_cost": 15.00,
  "area_code_fee": 0.00,
  "requested_area_code": "212",
  "expires_at": "..."
}
```

**Actual Response**: _____________

**Status**: ⬜ Pass ⬜ Fail

---

## 📊 Test Summary

### Overall Results
- **Total Tests**: 25
- **Passed**: _______
- **Failed**: _______
- **Skipped**: _______
- **Pass Rate**: _______%

### Critical Issues Found
1. _____________
2. _____________
3. _____________

### Minor Issues Found
1. _____________
2. _____________
3. _____________

### Recommendations
1. _____________
2. _____________
3. _____________

---

## ✅ Sign-Off

**Tester Name**: _____________
**Date**: _____________
**Signature**: _____________

**Ready for Production**: ⬜ Yes ⬜ No (explain): _____________

---

## 📝 Notes

Additional observations, bugs, or feedback:

_____________________________________________
_____________________________________________
_____________________________________________
