# 🚨 URGENT: Manual Refund Procedure

**User ID**: `2986207f-4e45-4249-91c3-e5e13bae6622`  
**Amount Owed**: $10.00  
**Reason**: Tier pricing bug + No SMS received (0% success rate)  
**Priority**: IMMEDIATE

---

## 💰 REFUND BREAKDOWN

### What User Paid
- 4 SMS × $2.50 = **$10.00 charged**

### What User Should Have Paid
- User tier: Custom ($35/month with $25 quota)
- 4 SMS × $0.20 = $0.80
- But within $25 monthly quota = **$0.00**

### What User Received
- 4 SMS stuck in "Still Waiting"
- 0 codes received
- 0% success rate
- **Nothing delivered**

### Refund Calculation
- Charged: $10.00
- Should have paid: $0.00
- Received: Nothing
- **REFUND DUE: $10.00**

---

## 🔧 METHOD 1: Database Direct Refund (Fastest)

### Step 1: Connect to Database
```bash
# Production database
psql $DATABASE_URL

# Or if using local connection
psql -h localhost -U postgres -d namaskah
```

### Step 2: Check Current Balance
```sql
SELECT 
    id, 
    email, 
    subscription_tier, 
    balance,
    monthly_usage
FROM users 
WHERE id = '2986207f-4e45-4249-91c3-e5e13bae6622';
```

**Expected Output:**
```
id: 2986207f-4e45-4249-91c3-e5e13bae6622
email: [user email]
tier: custom
balance: $2.40 (current)
```

### Step 3: Issue Refund
```sql
-- Add $10.00 to user balance
UPDATE users 
SET balance = balance + 10.00,
    updated_at = NOW()
WHERE id = '2986207f-4e45-4249-91c3-e5e13bae6622';

-- Verify new balance
SELECT email, balance FROM users 
WHERE id = '2986207f-4e45-4249-91c3-e5e13bae6622';
```

**Expected Result:**
```
balance: $12.40 (was $2.40, now $12.40)
```

### Step 4: Update SMS Verification Status
```sql
-- Mark all 4 SMS as REFUNDED
UPDATE sms_verifications 
SET status = 'REFUNDED',
    refunded = true,
    refund_amount = cost,
    refund_reason = 'Tier pricing bug - manual refund issued',
    updated_at = NOW()
WHERE user_id = '2986207f-4e45-4249-91c3-e5e13bae6622'
  AND status = 'PENDING'
  AND created_at >= '2026-04-17 14:00:00';

-- Verify update
SELECT id, service, phone_number, cost, status, refunded 
FROM sms_verifications 
WHERE user_id = '2986207f-4e45-4249-91c3-e5e13bae6622'
ORDER BY created_at DESC 
LIMIT 4;
```

### Step 5: Create Transaction Record (if table exists)
```sql
-- Check if transaction_logs table exists
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_name = 'transaction_logs'
);

-- If exists, insert refund record
INSERT INTO transaction_logs (
    id,
    user_id,
    transaction_type,
    amount,
    balance_before,
    balance_after,
    tier,
    reason,
    metadata,
    created_at
) VALUES (
    gen_random_uuid(),
    '2986207f-4e45-4249-91c3-e5e13bae6622',
    'REFUND',
    10.00,
    2.40,
    12.40,
    'custom',
    'Manual refund: Tier pricing bug + SMS timeout (4 failed verifications)',
    '{"sms_count": 4, "original_rate": 2.50, "correct_rate": 0.00, "issue": "tier_pricing_bug"}'::jsonb,
    NOW()
);
```

---

## 🔧 METHOD 2: API Endpoint (If Available)

### Check if refund endpoint exists
```bash
# Search for refund endpoint
grep -r "refund" app/api/
```

### If endpoint exists, use it:
```bash
# Get admin token
TOKEN="your_admin_token"

# Issue refund
curl -X POST https://your-api.com/api/admin/refund \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "2986207f-4e45-4249-91c3-e5e13bae6622",
    "amount": 10.00,
    "reason": "Tier pricing bug - 4 failed SMS verifications"
  }'
```

---

## 🔧 METHOD 3: Python Script (Safest)

### Create refund script
```python
# scripts/issue_refund.py
import asyncio
import sys
from decimal import Decimal
from datetime import datetime

sys.path.insert(0, '.')

async def issue_refund():
    from app.core.database import get_db
    from app.models.user import User
    from app.models.verification import SMSVerification
    from sqlalchemy import select, update
    
    user_id = "2986207f-4e45-4249-91c3-e5e13bae6622"
    refund_amount = Decimal("10.00")
    
    async for db in get_db():
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User {user_id} not found")
            return
        
        print(f"User: {user.email}")
        print(f"Tier: {user.subscription_tier}")
        print(f"Current Balance: ${user.balance:.2f}")
        
        # Calculate new balance
        old_balance = user.balance
        new_balance = old_balance + refund_amount
        
        print(f"\nRefund Amount: ${refund_amount:.2f}")
        print(f"New Balance: ${new_balance:.2f}")
        
        # Confirm
        confirm = input("\nProceed with refund? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Refund cancelled")
            return
        
        # Update user balance
        user.balance = new_balance
        
        # Update SMS verifications
        await db.execute(
            update(SMSVerification)
            .where(SMSVerification.user_id == user_id)
            .where(SMSVerification.status == "PENDING")
            .where(SMSVerification.created_at >= datetime(2026, 4, 17, 14, 0, 0))
            .values(
                status="REFUNDED",
                refunded=True,
                refund_amount=SMSVerification.cost,
                refund_reason="Tier pricing bug - manual refund",
                updated_at=datetime.utcnow()
            )
        )
        
        await db.commit()
        
        print("\n✅ Refund issued successfully!")
        print(f"   Old Balance: ${old_balance:.2f}")
        print(f"   New Balance: ${new_balance:.2f}")
        print(f"   Refunded: ${refund_amount:.2f}")
        
        # Send notification (if service available)
        try:
            from app.services.notification_service import NotificationService
            notification_service = NotificationService(db)
            
            await notification_service.create_notification(
                user_id=user.id,
                type="refund",
                title="Refund Processed",
                message=f"${refund_amount:.2f} refunded due to system error. We apologize for the inconvenience.",
                category="billing"
            )
            print("✅ Notification sent")
        except Exception as e:
            print(f"⚠️  Could not send notification: {e}")
        
        break

if __name__ == "__main__":
    asyncio.run(issue_refund())
```

### Run the script
```bash
cd "/Users/machine/My Drive/Github Projects/Namaskah. app"
python3 scripts/issue_refund.py
```

---

## 📧 NOTIFY USER

After issuing refund, send email:

```
Subject: Refund Issued - We Apologize

Hi [User Name],

We've identified a system error that affected your recent SMS verifications on April 17, 2026.

REFUND DETAILS:
- Amount: $10.00
- Reason: System pricing error + SMS delivery failure
- New Balance: $12.40

WHAT HAPPENED:
- 4 SMS verifications were charged but did not deliver codes
- Our system incorrectly applied pricing for your Custom tier
- We've issued a full refund and fixed the issue

WHAT WE'VE DONE:
- Refunded $10.00 to your account
- Fixed the tier pricing system
- Implemented automatic refunds for failed SMS
- Added timeout protection (10 minutes)

We sincerely apologize for this inconvenience. Your trust is important to us.

If you have any questions, please reply to this email.

Best regards,
Namaskah Team
```

---

## ✅ VERIFICATION CHECKLIST

After issuing refund:

- [ ] User balance updated: $2.40 → $12.40
- [ ] 4 SMS verifications marked as REFUNDED
- [ ] Transaction log created (if table exists)
- [ ] User notification sent
- [ ] Email sent to user
- [ ] Refund documented in admin notes
- [ ] Screenshot taken of database state
- [ ] Incident logged for audit

---

## 🔒 PREVENT FUTURE OCCURRENCES

### Immediate (Today)
1. Fix tier pricing bug
2. Add SMS timeout (10 min)
3. Add auto-refund on timeout

### Short-term (This Week)
4. Audit all Custom tier users for similar issues
5. Issue refunds to any affected users
6. Add transaction logging
7. Add refund notifications

### Long-term (This Month)
8. Add financial monitoring dashboard
9. Add alerts for pricing discrepancies
10. Add daily reconciliation script
11. Add automated refund system

---

## 📊 AUDIT TRAIL

Document this refund:

```
Date: 2026-04-17
User ID: 2986207f-4e45-4249-91c3-e5e13bae6622
Amount: $10.00
Reason: Tier pricing bug + SMS timeout (4 failed verifications)
Method: [Database/API/Script]
Issued By: [Your Name]
Verified By: [Verifier Name]
Status: [Pending/Complete]
```

---

## 🚨 CRITICAL NOTES

1. **This is not optional** - User paid for service not received
2. **Legal requirement** - Must refund for undelivered services
3. **Trust issue** - User will lose confidence if not refunded
4. **Compliance** - Payment processor terms require refunds for failed services
5. **Reputation** - Word spreads fast about platforms that don't refund

---

**NEXT STEP**: Choose method (recommend Method 3 - Python script) and issue refund immediately.
