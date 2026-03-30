# Admin Balance Sync - Production Implementation Plan

**Date**: March 30, 2026  
**Issue**: Admin balance not syncing with TextVerified, causing 402 errors  
**Requirement**: Maintain transaction history and analytics while syncing admin balance

---

## 🎯 Core Requirements

1. **Admin balance MUST sync with TextVerified** (single source of truth)
2. **Transaction history MUST be preserved** (for analytics, reporting, auditing)
3. **No hardcoded values** (balance comes from TextVerified API)
4. **Regular users unaffected** (continue using local credits + Paystack)
5. **Real-time accuracy** (dashboard shows live TextVerified balance)

---

## 🏗️ Architecture Design

### Dual-Mode Balance System

```
┌─────────────────────────────────────────────────────────────┐
│                     Balance Management                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ADMIN USER (is_admin=true)                                 │
│  ├─ Balance Source: TextVerified API (live)                 │
│  ├─ Display: Real-time API call                             │
│  ├─ Deduction: Record transaction, sync from TV             │
│  ├─ Top-up: Add to TextVerified account                     │
│  └─ Analytics: Track via Transaction table                  │
│                                                              │
│  REGULAR USER (is_admin=false)                              │
│  ├─ Balance Source: users.credits (database)                │
│  ├─ Display: Local database value                           │
│  ├─ Deduction: Local subtraction + transaction record       │
│  ├─ Top-up: Paystack payment                                │
│  └─ Analytics: Track via Transaction table                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Transaction Recording Strategy

### Current Flow (Broken)
```
1. Check local balance (stale)
2. Call TextVerified API (deducts automatically)
3. Deduct from local balance (double deduction)
4. Record transaction
5. Balance diverges over time ❌
```

### New Flow (Fixed)
```
ADMIN:
1. Fetch live TextVerified balance
2. Check if sufficient
3. Call TextVerified API (deducts automatically)
4. Fetch new TextVerified balance
5. Record transaction (old_balance → new_balance)
6. Update local balance = TextVerified balance (for caching)
7. Analytics use transaction records ✅

REGULAR USER:
1. Check local balance
2. Deduct from local balance
3. Record transaction
4. Analytics use transaction records ✅
```

---

## 🔧 Implementation Details

### 1. Balance Retrieval Service

**File**: `app/services/balance_service.py` (NEW)

```python
"""Balance management service with dual-mode support."""

from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.user import User
from app.services.textverified_service import TextVerifiedService
from app.core.logging import get_logger

logger = get_logger(__name__)

class BalanceService:
    """Unified balance service for admin and regular users."""
    
    @staticmethod
    async def get_user_balance(user_id: str, db: Session) -> Dict[str, Any]:
        """Get user balance with source tracking.
        
        Returns:
            {
                "balance": float,
                "source": "textverified" | "local",
                "is_admin": bool,
                "last_synced": datetime (admin only)
            }
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        if user.is_admin:
            # Admin: Always fetch from TextVerified
            try:
                tv_service = TextVerifiedService()
                tv_balance = await tv_service.get_balance()
                live_balance = tv_balance.get("balance", 0.0)
                
                # Update local cache for analytics
                user.credits = live_balance
                user.balance_last_synced = datetime.now(timezone.utc)
                db.commit()
                
                logger.info(f"Admin balance synced: ${live_balance:.2f}")
                
                return {
                    "balance": live_balance,
                    "source": "textverified",
                    "is_admin": True,
                    "last_synced": user.balance_last_synced
                }
            except Exception as e:
                logger.error(f"TextVerified balance fetch failed: {e}")
                # Fallback to cached value with warning
                return {
                    "balance": user.credits,
                    "source": "cached",
                    "is_admin": True,
                    "error": str(e),
                    "last_synced": user.balance_last_synced
                }
        else:
            # Regular user: Use local balance
            return {
                "balance": user.credits,
                "source": "local",
                "is_admin": False
            }
    
    @staticmethod
    async def check_sufficient_balance(
        user_id: str, 
        required_amount: float, 
        db: Session
    ) -> Dict[str, Any]:
        """Check if user has sufficient balance.
        
        Returns:
            {
                "sufficient": bool,
                "current_balance": float,
                "required": float,
                "shortfall": float (if insufficient)
            }
        """
        balance_info = await BalanceService.get_user_balance(user_id, db)
        current_balance = balance_info["balance"]
        sufficient = current_balance >= required_amount
        
        result = {
            "sufficient": sufficient,
            "current_balance": current_balance,
            "required": required_amount,
            "source": balance_info["source"]
        }
        
        if not sufficient:
            result["shortfall"] = required_amount - current_balance
        
        return result
```

---

### 2. Transaction Recording Service

**File**: `app/services/transaction_service.py` (NEW)

```python
"""Transaction recording service for analytics and audit."""

from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.transaction import Transaction
from app.core.logging import get_logger

logger = get_logger(__name__)

class TransactionService:
    """Record all financial transactions for analytics."""
    
    @staticmethod
    def record_sms_purchase(
        db: Session,
        user_id: str,
        amount: float,
        service: str,
        verification_id: str,
        old_balance: float,
        new_balance: float,
        filters: dict = None,
        tier: str = None
    ) -> Transaction:
        """Record SMS purchase transaction.
        
        This creates an audit trail for:
        - Analytics dashboards
        - Spending reports
        - User transaction history
        - Admin monitoring
        """
        transaction = Transaction(
            user_id=user_id,
            amount=-abs(amount),  # Negative for debit
            type="sms_purchase",
            description=f"SMS verification for {service}",
            tier=tier,
            service=service,
            filters=str(filters) if filters else None,
            status="completed",
            reference=f"sms_{verification_id}",
            metadata={
                "verification_id": verification_id,
                "old_balance": old_balance,
                "new_balance": new_balance,
                "filters": filters
            }
        )
        
        db.add(transaction)
        db.flush()
        
        logger.info(
            f"Transaction recorded: user={user_id}, amount=${amount:.2f}, "
            f"balance: ${old_balance:.2f} → ${new_balance:.2f}"
        )
        
        return transaction
    
    @staticmethod
    def record_credit_addition(
        db: Session,
        user_id: str,
        amount: float,
        payment_reference: str,
        payment_method: str = "paystack"
    ) -> Transaction:
        """Record credit addition (top-up)."""
        transaction = Transaction(
            user_id=user_id,
            amount=abs(amount),  # Positive for credit
            type="credit",
            description=f"Credit added via {payment_method}",
            status="completed",
            reference=payment_reference
        )
        
        db.add(transaction)
        db.flush()
        
        logger.info(f"Credit added: user={user_id}, amount=${amount:.2f}")
        return transaction
    
    @staticmethod
    def record_refund(
        db: Session,
        user_id: str,
        amount: float,
        verification_id: str,
        reason: str
    ) -> Transaction:
        """Record refund transaction."""
        transaction = Transaction(
            user_id=user_id,
            amount=abs(amount),  # Positive for refund
            type="refund",
            description=f"Refund: {reason}",
            status="completed",
            reference=f"refund_{verification_id}",
            metadata={
                "verification_id": verification_id,
                "reason": reason
            }
        )
        
        db.add(transaction)
        db.flush()
        
        logger.info(f"Refund recorded: user={user_id}, amount=${amount:.2f}")
        return transaction
```

---

### 3. Modified Purchase Flow

**File**: `app/api/verification/purchase_endpoints.py` (MODIFY)

```python
# BEFORE balance check (line ~180)
from app.services.balance_service import BalanceService
from app.services.transaction_service import TransactionService

# REPLACE lines 189-210 with:
# Check balance using unified service
balance_check = await BalanceService.check_sufficient_balance(
    user_id, sms_cost, db
)

if not balance_check["sufficient"]:
    logger.warning(
        f"User {user_id} insufficient balance: "
        f"${balance_check['current_balance']:.2f} < ${sms_cost:.2f} "
        f"(source: {balance_check['source']})"
    )
    raise HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail=(
            f"Insufficient balance. "
            f"Available: ${balance_check['current_balance']:.2f}, "
            f"Required: ${sms_cost:.2f}"
        )
    )

old_balance = balance_check["current_balance"]

# ... TextVerified API call happens here ...

# REPLACE lines 280-293 with:
# Record transaction and update balance
if user.is_admin:
    # Admin: Fetch new balance from TextVerified
    tv_bal = await tv_service.get_balance()
    new_balance = tv_bal.get("balance", 0.0)
    user.credits = new_balance  # Update cache
    logger.info(
        f"Admin balance synced after purchase: "
        f"${old_balance:.2f} → ${new_balance:.2f}"
    )
else:
    # Regular user: Deduct locally
    user.credits -= Decimal(str(actual_cost))
    new_balance = float(user.credits)
    logger.info(
        f"User balance deducted: "
        f"${old_balance:.2f} → ${new_balance:.2f}"
    )

# Record transaction for BOTH admin and regular users
TransactionService.record_sms_purchase(
    db=db,
    user_id=user_id,
    amount=actual_cost,
    service=request.service,
    verification_id=str(verification.id),
    old_balance=old_balance,
    new_balance=new_balance,
    filters={"area_code": area_code, "carrier": carrier} if (area_code or carrier) else None,
    tier=user_tier
)
```

---

### 4. Modified Wallet Balance Endpoint

**File**: `app/api/core/wallet.py` (MODIFY)

```python
# REPLACE get_wallet_balance function (lines 35-50) with:

@router.get("/balance", response_model=WalletBalanceResponse)
async def get_wallet_balance(
    user_id: str = Depends(get_current_user_id), 
    db: Session = Depends(get_db)
):
    """Get current wallet balance with source tracking."""
    try:
        from app.services.balance_service import BalanceService
        
        balance_info = await BalanceService.get_user_balance(user_id, db)
        user = db.query(User).filter(User.id == user_id).first()
        
        response = WalletBalanceResponse(
            credits=balance_info["balance"],
            credits_usd=balance_info["balance"],
            free_verifications=user.free_verifications if user else 0,
        )
        
        # Add metadata for admin users
        if balance_info.get("is_admin"):
            response.source = balance_info["source"]
            response.last_synced = balance_info.get("last_synced")
            if balance_info.get("error"):
                response.sync_error = balance_info["error"]
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to get wallet balance: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve balance")
```

---

### 5. Database Schema Update

**File**: `migrations/add_balance_sync_fields.sql` (NEW)

```sql
-- Add balance sync tracking for admin users
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS balance_last_synced TIMESTAMP WITH TIME ZONE;

-- Add metadata column to transactions for richer analytics
ALTER TABLE sms_transactions 
ADD COLUMN IF NOT EXISTS metadata JSONB;

-- Create index for faster transaction queries
CREATE INDEX IF NOT EXISTS idx_transactions_user_type 
ON sms_transactions(user_id, type, created_at DESC);

-- Create index for balance sync tracking
CREATE INDEX IF NOT EXISTS idx_users_admin_sync 
ON users(is_admin, balance_last_synced) 
WHERE is_admin = true;
```

---

### 6. Response Schema Update

**File**: `app/schemas/payment.py` (MODIFY)

```python
class WalletBalanceResponse(BaseModel):
    credits: float
    credits_usd: float
    free_verifications: float
    
    # Admin-specific fields
    source: Optional[str] = None  # "textverified", "local", "cached"
    last_synced: Optional[datetime] = None
    sync_error: Optional[str] = None
    
    class Config:
        from_attributes = True
```

---

## 📈 Analytics & Reporting

### Transaction History (Unchanged)

All transactions are recorded in `sms_transactions` table:
- Admin purchases → recorded with TextVerified balance snapshots
- Regular user purchases → recorded with local balance changes
- Refunds → recorded for both user types
- Credits added → recorded for regular users

### Analytics Queries

```sql
-- Total spending by user (works for both admin and regular users)
SELECT user_id, SUM(ABS(amount)) as total_spent
FROM sms_transactions
WHERE type = 'sms_purchase'
GROUP BY user_id;

-- Admin balance sync health
SELECT 
    email,
    credits as cached_balance,
    balance_last_synced,
    EXTRACT(EPOCH FROM (NOW() - balance_last_synced))/60 as minutes_since_sync
FROM users
WHERE is_admin = true;

-- Service usage breakdown
SELECT 
    service,
    COUNT(*) as purchase_count,
    SUM(ABS(amount)) as total_spent
FROM sms_transactions
WHERE type = 'sms_purchase'
GROUP BY service
ORDER BY total_spent DESC;
```

---

## 🧪 Testing Strategy

### Unit Tests

```python
# tests/unit/test_balance_service.py
async def test_admin_balance_fetches_from_textverified():
    """Admin balance should always fetch from TextVerified API."""
    # Mock TextVerified API
    # Call BalanceService.get_user_balance()
    # Assert source == "textverified"
    # Assert balance matches API response

async def test_regular_user_balance_uses_local():
    """Regular user balance should use local database."""
    # Call BalanceService.get_user_balance()
    # Assert source == "local"
    # Assert no TextVerified API call

async def test_transaction_recorded_for_admin():
    """Admin purchases should record transactions."""
    # Create admin purchase
    # Assert transaction exists in database
    # Assert old_balance and new_balance tracked

async def test_transaction_recorded_for_regular_user():
    """Regular user purchases should record transactions."""
    # Create regular user purchase
    # Assert transaction exists in database
    # Assert balance deducted locally
```

### Integration Tests

```python
# tests/integration/test_admin_purchase_flow.py
async def test_admin_purchase_with_sufficient_balance():
    """Admin with sufficient TextVerified balance can purchase."""
    # Mock TextVerified balance = $10
    # Purchase SMS ($2.50)
    # Assert success
    # Assert transaction recorded
    # Assert new balance = $7.50

async def test_admin_purchase_with_insufficient_balance():
    """Admin with insufficient TextVerified balance gets 402."""
    # Mock TextVerified balance = $1
    # Purchase SMS ($2.50)
    # Assert 402 error
    # Assert no transaction recorded
```

---

## 🚀 Deployment Plan

### Phase 1: Database Migration (5 min)
```bash
# Run migration
psql $DATABASE_URL < migrations/add_balance_sync_fields.sql
```

### Phase 2: Deploy New Services (10 min)
```bash
# Add new files
app/services/balance_service.py
app/services/transaction_service.py

# Restart application
./deploy.sh
```

### Phase 3: Update Existing Code (15 min)
```bash
# Modify files
app/api/verification/purchase_endpoints.py
app/api/core/wallet.py
app/schemas/payment.py

# Restart application
./deploy.sh
```

### Phase 4: Verification (10 min)
```bash
# Test admin balance display
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://namaskahsms.onrender.com/api/wallet/balance

# Test admin purchase
# Check transaction history
# Verify analytics dashboard
```

---

## 📊 Monitoring & Alerts

### Key Metrics

1. **Balance Sync Health**
   - Admin balance last synced timestamp
   - Sync failure rate
   - API response time

2. **Transaction Recording**
   - Transactions per hour
   - Failed transaction recordings
   - Balance discrepancies

3. **User Experience**
   - 402 error rate (should decrease)
   - Purchase success rate
   - Balance display latency

### Alerts

```yaml
# Alert if admin balance hasn't synced in 10 minutes
- name: admin_balance_stale
  condition: minutes_since_sync > 10
  severity: warning

# Alert if TextVerified API is down
- name: textverified_api_down
  condition: sync_error_rate > 50%
  severity: critical

# Alert if transaction recording fails
- name: transaction_recording_failed
  condition: failed_transaction_count > 0
  severity: high
```

---

## ✅ Success Criteria

- [ ] Admin balance always shows live TextVerified balance
- [ ] Admin can purchase when TextVerified balance is sufficient
- [ ] Admin gets clear 402 error when TextVerified balance is insufficient
- [ ] All purchases (admin + regular) recorded in transactions table
- [ ] Analytics dashboards work for both user types
- [ ] Transaction history shows complete audit trail
- [ ] No hardcoded balance values
- [ ] Regular users unaffected
- [ ] Balance sync happens in <500ms
- [ ] Zero balance divergence for admin

---

## 🎯 Summary

This solution provides:

1. **Real-time accuracy**: Admin balance = TextVerified balance
2. **Complete audit trail**: All transactions recorded
3. **Analytics support**: Transaction history preserved
4. **Dual-mode system**: Admin (TextVerified) + Regular (local)
5. **Production-grade**: Error handling, monitoring, testing
6. **No hardcoded values**: Balance always from source of truth
7. **Backward compatible**: Regular users unchanged

**Estimated Implementation Time**: 2-3 hours  
**Risk Level**: Low (isolated changes, comprehensive testing)  
**Rollback Plan**: Revert code changes, database migration is additive only
