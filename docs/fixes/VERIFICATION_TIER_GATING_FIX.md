# Verification Page Error Diagnostics

**Issue**: "An unexpected error occurred. Please try again." + PAYG upsell showing for CUSTOM tier users

**Status**: ✅ Fixed in commit 5f1be129

---

## Root Causes Identified

### 1. Tier-Gating Logic Issue
**Problem**: CUSTOM tier users seeing "Want specific area codes? Upgrade to PAYG" message

**Root Cause**: 
- Tier comparison was case-sensitive (e.g., "Custom" vs "custom")
- API response format mismatch (multiple possible field names)
- `applyTierGating()` called before tier fully loaded

**Fix Applied**:
```javascript
// Before
const rank = VerificationFlow.tierRank[VerificationFlow.userTier] || 0;

// After
const normalizedTier = (VerificationFlow.userTier || 'freemium').toLowerCase();
const rank = VerificationFlow.tierRank[normalizedTier] || 0;
```

### 2. Tier Loading Issue
**Problem**: Tier not being detected correctly from API

**Root Cause**:
- API returns `current_tier` but code expected `user.subscription_tier`
- No fallback for different response formats

**Fix Applied**:
```javascript
// Before
if (d.success && d.user) {
    const freshTier = d.user.subscription_tier || 'freemium';
}

// After
let freshTier = 'freemium';
if (d.current_tier) freshTier = d.current_tier;
else if (d.user?.subscription_tier) freshTier = d.user.subscription_tier;
else if (d.tier) freshTier = d.tier;
freshTier = freshTier.toLowerCase();
```

### 3. Verification Creation Error
**Problem**: "An unexpected error occurred" when creating verification

**Root Cause**:
- 409 Conflict errors not being handled with specific message
- Generic error message not helpful for debugging

**Fix Applied**:
```javascript
// Added specific handling for 409 errors
if (msg.includes('409') || msg.includes('Conflict')) {
    window.toast && window.toast.error(
        'This combination of service, area code, and carrier is not available. Please try different filters.'
    );
}
```

---

## How to Verify the Fix

### Step 1: Check Browser Console
Open DevTools (F12) and look for these logs:

```
[TierGating] Tier: custom, Rank: 3, HasService: true
[TierGating] Upsell: HIDE
[TierGating] SubTip: SHOW
[Tier] Updated to: custom
```

**Expected**: 
- Tier should be "custom" (lowercase)
- Rank should be 3 (custom = 3)
- Upsell should be HIDDEN
- SubTip should be SHOWN

### Step 2: Verify API Response
In DevTools Network tab, check `/api/tiers/current` response:

```json
{
  "current_tier": "custom",
  "user": { ... }
}
```

**Expected**: Should have one of these fields:
- `current_tier` ✅
- `user.subscription_tier` ✅
- `tier` ✅

### Step 3: Test Verification Creation
1. Select a service (e.g., Discord)
2. Select an area code (e.g., 212 - New York)
3. Select a carrier (e.g., Verizon)
4. Click "Get Number"

**Expected**: 
- Should show phone number
- Should NOT show "An unexpected error occurred"
- If error occurs, check console for detailed error message

---

## Debugging Commands

### Check Tier in Console
```javascript
console.log('Current Tier:', VerificationFlow.userTier);
console.log('Tier Rank:', VerificationFlow.tierRank[VerificationFlow.userTier.toLowerCase()]);
```

### Force Tier Reload
```javascript
localStorage.removeItem('nsk_tier_cache');
await loadTier();
```

### Check Cached Tier
```javascript
console.log(JSON.parse(localStorage.getItem('nsk_tier_cache')));
```

### Manually Trigger Tier Gating
```javascript
applyTierGating();
```

---

## Files Modified

- `templates/verify_modern.html` - Tier-gating logic fixes

## Commit

- **Hash**: 5f1be129
- **Message**: fix: tier-gating logic for PAYG+ upsell message visibility
- **Changes**: 30 insertions, 14 deletions

---

## Next Steps if Issue Persists

1. **Check API Response Format**
   - Verify `/api/tiers/current` returns correct field
   - May need to update backend if using different field name

2. **Check Tier Cache**
   - Clear localStorage: `localStorage.clear()`
   - Reload page
   - Check if tier loads correctly

3. **Check Network Requests**
   - Verify `/api/tiers/current` returns 200 OK
   - Check response time (should be <1s)
   - Verify Authorization header is present

4. **Check Service Loading**
   - Verify `/api/countries/US/services` returns services
   - Verify `/api/area-codes?country=US` returns area codes
   - Verify `/api/verification/carriers/US` returns carriers

---

## Related Issues

- **409 Conflict Errors**: Occur when carrier/area code combination unavailable
  - Solution: Try different filters or service
  - Backend should return specific error message

- **Services Not Loading**: API timeout or failure
  - Solution: Retry button appears automatically
  - Check network connectivity

- **Balance Not Updating**: Cache issue
  - Solution: Refresh page or clear cache
  - Backend should return current balance

---

**Last Updated**: March 15, 2026
**Status**: ✅ Fixed and Committed
