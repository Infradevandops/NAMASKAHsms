# 🚨 CRITICAL: Balance Display Issue - Root Cause & Fix

## Problem Statement
Admin dashboard shows **$12.10** but TextVerified account has **$2.40**

---

## Root Cause

There are **TWO SEPARATE BALANCES** in the system:

### 1. Platform Credits (User Balance)
- **Location**: `users.credits` column in database
- **Value**: $12.10
- **Purpose**: User's wallet balance for purchasing SMS verifications
- **Source**: Payments via Paystack, manual credits, refunds

### 2. Provider Balance (TextVerified API)
- **Location**: TextVerified API account (huff_06psalm@icloud.com)
- **Value**: $2.40
- **Purpose**: Actual funds available in TextVerified account to purchase numbers
- **Source**: Manual top-ups to TextVerified account

---

## Current Behavior

### API Response (`/api/billing/balance`)
```json
{
  "credits": 12.10,           // ← User's platform balance (SHOWN)
  "provider_balance": 2.40,   // ← TextVerified balance (HIDDEN)
  "currency": "USD"
}
```

### Frontend Display
- **Regular users**: See `credits` ($12.10) ✅ Correct
- **Admin users**: See `credits` ($12.10) ❌ Wrong - should see `provider_balance` ($2.40)

---

## Why This Matters

**Critical Production Issue:**
- Admin thinks they have $12.10 to spend
- TextVerified only has $2.40 available
- When admin tries to purchase SMS > $2.40, it will FAIL
- This causes confusion and potential service disruption

---

## The Fix

### Option 1: Update Frontend (Recommended)
Modify the dashboard to show `provider_balance` for admin users.

**File**: `static/js/dashboard.js` or admin-specific JS

**Change**:
```javascript
// Current (wrong for admin)
const balance = parseFloat(data.credits) || 0;

// Fixed (correct for admin)
const balance = data.provider_balance !== undefined
  ? parseFloat(data.provider_balance)
  : parseFloat(data.credits) || 0;
```

### Option 2: Update Backend (Alternative)
Change the API to return `provider_balance` as `credits` for admin users.

**File**: `app/api/billing/credit_endpoints.py`

**Change**:
```python
if user.is_admin:
    # For admin, show TextVerified balance as primary
    bal_data = await _get_tv_service().get_balance()
    tv_balance = bal_data.get("balance", 0.0)
    result["credits"] = tv_balance  # ← Override with provider balance
    result["platform_credits"] = user.credits  # ← Keep original as secondary
```

---

## Recommended Solution

**Use Option 2 (Backend Fix)** because:
1. ✅ No frontend changes needed
2. ✅ Works across all admin interfaces
3. ✅ Clear separation: admin sees provider balance, users see platform balance
4. ✅ Maintains backward compatibility

---

## Implementation

See: `fix_admin_balance.py` script

---

## Testing

After fix:
1. Login as admin
2. Check dashboard balance
3. Should show **$2.40** (TextVerified balance)
4. Regular users should still see their platform credits

---

## Long-term Solution

**Sync the balances:**
- When user purchases SMS, deduct from BOTH balances
- When TextVerified is topped up, update admin's platform credits
- Add monitoring to alert when balances diverge

---

**Priority**: 🔴 CRITICAL - Fix immediately before admin makes purchases
