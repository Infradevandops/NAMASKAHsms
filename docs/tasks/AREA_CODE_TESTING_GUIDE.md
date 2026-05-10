# 🧪 Area Code Tier Gating - Testing Guide (Step-by-Step)

**Version**: v4.7.0
**Status**: Ready for Testing
**Estimated Time**: 4-6 hours

---

## 📋 Pre-Testing Setup

### Step 1: Environment Setup

**Option A: Local Development**
```bash
# 1. Navigate to project
cd "/Users/machine/My Drive/Github Projects/Namaskah. app"

# 2. Start the application
./start.sh
# OR
uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# 3. Verify server is running
curl http://localhost:8000/api/health
```

**Option B: Staging Environment**
```bash
# Use staging URL
https://staging.namaskah.app
```

---

### Step 2: Create Test Users

**Option A: Using Script** (Recommended)
```bash
# Run the setup script
python3 scripts/setup_test_users.py
```

**Option B: Manual SQL**
```sql
-- Connect to database
psql $DATABASE_URL

-- Create test users
INSERT INTO users (id, email, username, password_hash, subscription_tier, credits, email_verified, is_active) VALUES
  ('test_freemium', 'freemium@test.com', 'test_freemium', '$2b$12$...', 'freemium', 50.0, true, true),
  ('test_payg', 'payg@test.com', 'test_payg', '$2b$12$...', 'payg', 50.0, true, true),
  ('test_pro', 'pro@test.com', 'test_pro', '$2b$12$...', 'pro', 50.0, true, true),
  ('test_custom', 'custom@test.com', 'test_custom', '$2b$12$...', 'custom', 50.0, true, true);

-- Password for all: test123
```

**Option C: Use Existing Users**
- Identify 4 existing users (one per tier)
- Note their credentials
- Ensure they have sufficient credits ($50+)

---

### Step 3: Verify Test Users

```bash
# Check users exist
curl http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"payg@test.com","password":"test123"}'

# Should return access_token
```

---

## 🧪 Testing Phase 1: Critical Path (Priority 1)

### Test 1: PAYG Voice with Area Code ⭐ CRITICAL

**Objective**: Verify PAYG users are charged $0.25 for voice area code

**Steps**:
1. Login as `payg@test.com` / `test123`
2. Navigate to `/voice-verify`
3. Select service: "WhatsApp"
4. Click "Advanced Options"
5. **Verify**: Badge shows "+$0.25" in yellow
6. **Verify**: Help text mentions upgrade to Pro
7. Select area code: "212 - New York, NY"
8. Click "Continue"
9. **Verify**: Pricing shows base + $0.25 fee
10. Note current balance: $______
11. Click "Request Verification"
12. **Verify**: Success message
13. **Verify**: Balance deducted = base + $0.25
14. **Verify**: Phone number has 212 area code

**Expected Results**:
- ✅ Badge: "+$0.25" (yellow)
- ✅ Fee charged: $0.25
- ✅ Total = Base + $0.25
- ✅ Phone: +1-212-XXX-XXXX

**Pass/Fail**: ⬜

---

### Test 2: PAYG Rental with Area Code ⭐ CRITICAL

**Objective**: Verify PAYG users are charged $0.50 for rental area code

**Steps**:
1. Login as `payg@test.com` / `test123`
2. Navigate to `/rentals`
3. Select service: "WhatsApp"
4. Select duration: "24h - $15.00"
5. **Verify**: Badge shows "+$0.50" in yellow
6. **Verify**: Help text mentions upgrade to Pro
7. Select area code: "212 - New York, NY"
8. **Verify**: Pricing breakdown updates:
   - Base Cost: $15.00
   - Area Code Fee: $0.50
   - Total: $15.50
9. Note current balance: $______
10. Click "Rent Number"
11. **Verify**: Success message
12. **Verify**: Balance deducted = $15.50
13. **Verify**: Phone number has 212 area code

**Expected Results**:
- ✅ Badge: "+$0.50" (yellow)
- ✅ Fee charged: $0.50
- ✅ Total = $15.50
- ✅ Phone: +1-212-XXX-XXXX

**Pass/Fail**: ⬜

---

### Test 3: Pro Voice with Area Code ⭐ CRITICAL

**Objective**: Verify Pro users get area code included (no fee)

**Steps**:
1. Login as `pro@test.com` / `test123`
2. Navigate to `/voice-verify`
3. Select service: "WhatsApp"
4. Click "Advanced Options"
5. **Verify**: Badge shows "Included" in green
6. **Verify**: Help text confirms included
7. Select area code: "415 - San Francisco, CA"
8. Click "Continue"
9. **Verify**: Pricing shows NO area code fee
10. Note current balance: $______
11. Click "Request Verification"
12. **Verify**: Balance deducted = base only (no fee)
13. **Verify**: Phone number has 415 area code

**Expected Results**:
- ✅ Badge: "Included" (green)
- ✅ Fee charged: $0.00
- ✅ Total = Base only
- ✅ Phone: +1-415-XXX-XXXX

**Pass/Fail**: ⬜

---

### Test 4: Pro Rental with Area Code ⭐ CRITICAL

**Objective**: Verify Pro users get rental area code included (no fee)

**Steps**:
1. Login as `pro@test.com` / `test123`
2. Navigate to `/rentals`
3. Select service: "WhatsApp"
4. Select duration: "24h - $15.00"
5. **Verify**: Badge shows "Included" in green
6. Select area code: "212 - New York, NY"
7. **Verify**: Pricing breakdown:
   - Base Cost: $15.00
   - Area Code Fee: $0.00 (or not shown)
   - Total: $15.00
8. Note current balance: $______
9. Click "Rent Number"
10. **Verify**: Balance deducted = $15.00 (no fee)
11. **Verify**: Phone number has 212 area code

**Expected Results**:
- ✅ Badge: "Included" (green)
- ✅ Fee charged: $0.00
- ✅ Total = $15.00
- ✅ Phone: +1-212-XXX-XXXX

**Pass/Fail**: ⬜

---

### Test 5: Freemium Blocked ⭐ CRITICAL

**Objective**: Verify Freemium users cannot access area code selection

**Steps**:
1. Login as `freemium@test.com` / `test123`
2. Navigate to `/voice-verify`
3. Select service: "WhatsApp"
4. Click "Advanced Options"
5. **Verify**: Area code section is NOT visible
6. Navigate to `/rentals`
7. **Verify**: Area code section is NOT visible
8. **Verify**: Cannot select area code

**Expected Results**:
- ✅ Voice: Area code hidden
- ✅ Rental: Area code hidden
- ✅ No way to select area code

**Pass/Fail**: ⬜

---

## 📊 Quick Results Summary

### Critical Tests (Must Pass)
- [ ] Test 1: PAYG Voice ($0.25 fee)
- [ ] Test 2: PAYG Rental ($0.50 fee)
- [ ] Test 3: Pro Voice (included)
- [ ] Test 4: Pro Rental (included)
- [ ] Test 5: Freemium (blocked)

**Pass Rate**: ___/5 (___%)

---

## 🐛 Bug Reporting

If you find a bug, document it here:

### Bug Template
```markdown
**Bug #**: ___
**Severity**: Critical / Major / Minor
**Test**: Test #___

**Description**:
[What went wrong]

**Expected**:
[What should happen]

**Actual**:
[What actually happened]

**Steps to Reproduce**:
1.
2.
3.

**Screenshots**: [Attach if available]
```

---

## ✅ Testing Completion

### When All 5 Critical Tests Pass:
1. ✅ Mark tests as complete
2. ✅ Document any bugs found
3. ✅ Update `AREA_CODE_MANUAL_TESTING_CHECKLIST.md`
4. ✅ Proceed to remaining 20 tests (if time permits)
5. ✅ Sign off on QA approval

### If Any Critical Test Fails:
1. ❌ Document the failure
2. ❌ Report to development team
3. ❌ Wait for bug fix
4. ❌ Retest after fix

---

## 📞 Need Help?

### Documentation
- **Full Test Checklist**: `AREA_CODE_MANUAL_TESTING_CHECKLIST.md` (25 tests)
- **Quick Reference**: `AREA_CODE_QUICK_REFERENCE.md`
- **QA Handoff**: `AREA_CODE_QA_HANDOFF.md`

### Common Issues
- **Can't login**: Check user exists in database
- **No area code section**: Check user tier
- **Wrong fee**: Check tier configuration
- **API error**: Check server logs

---

## 🎯 Success Criteria

**Minimum to Proceed**:
- ✅ All 5 critical tests passing
- ✅ No critical bugs found
- ✅ Fee calculations accurate
- ✅ Balance deductions correct

**Ready for Staging**: When all 5 critical tests pass

---

**Testing Started**: ___________
**Testing Completed**: ___________
**Tester**: ___________
**Result**: ⬜ Pass ⬜ Fail
