# Admin Balance Sync Assessment & Solution

**Date**: March 30, 2026  
**Issue**: Admin user getting HTTP 402 (Insufficient Credits) when creating verifications  
**Root Cause**: Admin balance not syncing with TextVerified API balance

---

## 🔍 Current Architecture Analysis

### Admin User Balance Flow

**Expected Behavior** (Your Requirement):
- Admin account balance should ALWAYS reflect TextVerified API account balance
- Admin should NOT use separate/external credits
- Admin balance = TextVerified balance (1:1 sync)

**Current Implementation** (What's Actually Happening):
1. **Admin user created** with initial 1000 credits (`init_admin.py:50`)
2. **Balance deduction** happens locally in database (`purchase_endpoints.py:289`)
3. **No automatic sync** from TextVerified balance to admin credits
4. **One-way sync exists** but only BEFORE deduction (`purchase_endpoints.py:280-288`)

### Code Evidence

#### 1. Admin Initialization (`app/core/init_admin.py:50`)
```python
credits, free_verifications, email_verified, subscription_tier,
1000, 1.0, true, 'custom',
```
- Admin starts with $1000 credits
- This is a LOCAL database value, not synced from TextVerified

#### 2. Balance Check Before Purchase (`purchase_endpoints.py:280-288`)
```python
# For admin users, sync from live TextVerified balance first
if user.is_admin:
    try:
        tv_bal = await tv_service.get_balance()
        live_balance = tv_bal.get("balance")
        if live_balance is not None:
            user.credits = live_balance
    except Exception as _sync_err:
        logger.warning(f"TV balance sync before deduct failed: {_sync_err}")
```
- Syncs TextVerified balance to admin credits BEFORE deduction
- If sync fails, uses stale local balance
- **Problem**: This sync happens INSIDE the purchase flow, not proactively

#### 3. Balance Deduction (`purchase_endpoints.py:289-293`)
```python
old_balance = user.credits
user.credits -= type(user.credits)(actual_cost)
new_balance = user.credits
logger.info(f"Deducting ${actual_cost:.2f} from user {user_id}: ${old_balance:.2f} → ${new_balance:.2f}")
```
- Deducts from LOCAL database balance
- Does NOT deduct from TextVerified (TextVerified handles this internally)
- Creates divergence between local and TextVerified balance

---

## 🐛 The Problem

### Scenario That Causes 402 Error

1. **Admin logs in** → Local balance shows $1000 (from init)
2. **Admin creates verification** → 
   - Sync attempts to fetch TextVerified balance
   - If TextVerified balance is $5, local balance updates to $5
   - Purchase costs $2.50
   - Check: $5 >= $2.50 ✅ (passes)
   - Deduction: $5 - $2.50 = $2.50 (local balance)
3. **Admin creates 2nd verification** →
   - Sync attempts to fetch TextVerified balance
   - TextVerified balance is now $2.50 (after first purchase)
   - Local balance updates to $2.50
   - Purchase costs $2.50
   - Check: $2.50 >= $2.50 ✅ (passes)
   - Deduction: $2.50 - $2.50 = $0 (local balance)
4. **Admin creates 3rd verification** →
   - Sync attempts to fetch TextVerified balance
   - TextVerified balance is now $0 (after second purchase)
   - Local balance updates to $0
   - Purchase costs $2.50
   - Check: $0 >= $2.50 ❌ (FAILS)
   - **HTTP 402: Insufficient Credits**

### Why This Happens

- **TextVerified deducts automatically** when you call `create_verification()`
- **Local database also deducts** to track usage
- **Double accounting** creates sync issues
- **Sync only happens at purchase time**, not continuously

---

## ✅ Solution Strategy

### Option 1: Real-Time Sync (Recommended)

**Approach**: Always fetch live TextVerified balance for admin, never use local balance

**Implementation**:

1. **Modify balance check** (`purchase_endpoints.py:189-210`)
   ```python
   # For admin: ALWAYS use live TextVerified balance
   if user.is_admin:
       tv_bal = await tv_service.get_balance()
       live_balance = tv_bal.get("balance", 0.0)
       if live_balance < sms_cost:
           raise HTTPException(
               status_code=status.HTTP_402_PAYMENT_REQUIRED,
               detail=f"Insufficient TextVerified balance: ${live_balance:.2f} < ${sms_cost:.2f}"
           )
   else:
       # Regular users: use local balance
       if user.credits < sms_cost:
           raise HTTPException(...)
   ```

2. **Skip local deduction for admin** (`purchase_endpoints.py:289-293`)
   ```python
   if not user.is_admin:
       old_balance = user.credits
       user.credits -= type(user.credits)(actual_cost)
       new_balance = user.credits
   else:
       # Admin: TextVerified handles deduction
       old_balance = await tv_service.get_balance()
       new_balance = old_balance.get("balance", 0.0)
   ```

3. **Add balance sync endpoint** (for dashboard display)
   ```python
   @router.get("/wallet/balance")
   async def get_balance(user_id: str = Depends(get_current_user_id)):
       user = db.query(User).filter(User.id == user_id).first()
       if user.is_admin:
           tv_service = TextVerifiedService()
           tv_bal = await tv_service.get_balance()
           return {"balance": tv_bal.get("balance", 0.0), "source": "textverified"}
       return {"balance": user.credits, "source": "local"}
   ```

**Pros**:
- ✅ Always accurate (single source of truth)
- ✅ No sync issues
- ✅ Admin balance = TextVerified balance (exactly what you want)

**Cons**:
- ⚠️ Extra API call per purchase (adds ~200ms latency)
- ⚠️ Depends on TextVerified API availability

---

### Option 2: Periodic Background Sync

**Approach**: Sync admin balance every 5 minutes in background

**Implementation**:

1. **Add background task** (`app/core/lifespan.py`)
   ```python
   async def _sync_admin_balance():
       while True:
           try:
               db = SessionLocal()
               admin = db.query(User).filter(User.is_admin == True).first()
               if admin:
                   tv_service = TextVerifiedService()
                   tv_bal = await tv_service.get_balance()
                   admin.credits = tv_bal.get("balance", 0.0)
                   db.commit()
                   logger.info(f"Admin balance synced: ${admin.credits:.2f}")
               db.close()
           except Exception as e:
               logger.error(f"Admin balance sync failed: {e}")
           await asyncio.sleep(300)  # 5 minutes
   
   # In lifespan():
   asyncio.create_task(_sync_admin_balance())
   ```

**Pros**:
- ✅ No extra latency on purchases
- ✅ Works even if TextVerified API is slow

**Cons**:
- ⚠️ Up to 5 minutes stale
- ⚠️ Still has race conditions

---

### Option 3: Hybrid (Best of Both Worlds)

**Approach**: Background sync + real-time check on purchase

**Implementation**:
- Background task syncs every 5 minutes (keeps dashboard accurate)
- Purchase flow does real-time check (ensures accuracy at critical moment)
- Skip local deduction for admin (TextVerified is source of truth)

**Pros**:
- ✅ Dashboard shows near-real-time balance
- ✅ Purchase always uses accurate balance
- ✅ Best user experience

**Cons**:
- ⚠️ Slightly more complex

---

## 🎯 Recommended Implementation

**Use Option 1 (Real-Time Sync)** for simplicity and accuracy.

### Changes Required

1. **Modify `purchase_endpoints.py`** (3 changes)
2. **Modify balance endpoint** (1 change)
3. **Add admin balance indicator** in frontend (optional)

### Testing Checklist

- [ ] Admin can purchase when TextVerified balance is sufficient
- [ ] Admin gets 402 when TextVerified balance is insufficient
- [ ] Admin balance in dashboard matches TextVerified balance
- [ ] Regular users still use local credits (unchanged)
- [ ] Balance updates immediately after purchase

---

## 📊 Regular Users vs Admin

| Feature | Regular Users | Admin User |
|---------|--------------|------------|
| **Balance Source** | Local database (`users.credits`) | TextVerified API |
| **Balance Check** | `user.credits >= cost` | `tv_balance >= cost` |
| **Deduction** | Local: `user.credits -= cost` | TextVerified handles it |
| **Top-up** | Paystack payment | Add funds to TextVerified account |
| **Dashboard Display** | Local balance | Live TextVerified balance |

---

## 🚀 Next Steps

1. **Immediate Fix**: Implement Option 1 (Real-Time Sync)
2. **Test**: Verify admin can purchase with TextVerified balance
3. **Monitor**: Check logs for sync failures
4. **Optimize**: Add caching if TextVerified API is slow (cache for 30s)

---

## 📝 Code Changes Summary

**Files to Modify**:
1. `app/api/verification/purchase_endpoints.py` - Balance check & deduction logic
2. `app/api/billing/wallet.py` - Balance display endpoint
3. `frontend/src/components/Dashboard.jsx` - Show "TextVerified Balance" for admin

**Estimated Time**: 30 minutes  
**Risk Level**: Low (only affects admin user)  
**Testing Required**: Manual testing with admin account

---

## ⚠️ Important Notes

1. **TextVerified deducts automatically** - You don't need to call a separate deduct API
2. **Local balance is for tracking only** - For admin, it should mirror TextVerified
3. **Regular users are unaffected** - They continue using local credits
4. **Admin is special case** - Admin = TextVerified account owner

---

## 🔧 Quick Fix (Temporary)

If you need to test RIGHT NOW before implementing the full solution:

```bash
# Manually sync admin balance from TextVerified
cd "/Users/machine/My Drive/Github Projects/Namaskah. app"
python3 << 'EOF'
import asyncio
from app.core.database import SessionLocal
from app.models.user import User
from app.services.textverified_service import TextVerifiedService

async def sync():
    db = SessionLocal()
    admin = db.query(User).filter(User.is_admin == True).first()
    tv = TextVerifiedService()
    bal = await tv.get_balance()
    admin.credits = bal["balance"]
    db.commit()
    print(f"✅ Admin balance synced: ${admin.credits:.2f}")
    db.close()

asyncio.run(sync())
EOF
```

This will sync your admin balance once. You'll need to run it again after each purchase until the permanent fix is implemented.
