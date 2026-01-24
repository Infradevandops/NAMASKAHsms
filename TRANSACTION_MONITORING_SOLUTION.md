# Transaction Monitoring & Notification Solution

## Current State Analysis

### ✅ What's Working
1. **Auto-refund system exists** (`auto_refund_service.py`)
   - Refunds for timeout/cancelled/failed verifications
   - Duplicate refund prevention
   - Transaction logging

2. **Notification system exists** (`notification_service.py`)
   - In-app notifications
   - Notification history

3. **Payment tracking** (`payment_service.py`)
   - Idempotent credit additions
   - Payment history
   - Transaction records

### ❌ Critical Gaps Identified

1. **Silent Deductions**
   - Credits deducted at line 156 of `consolidated_verification.py`
   - **NO notification sent** when credits are deducted
   - **NO transaction record created** for SMS purchase
   - User only sees balance change, no explanation

2. **Silent Refunds**
   - Refunds happen in `auto_refund_service.py`
   - Notification code exists but **may fail silently**
   - No guarantee user sees refund notification

3. **Missing Transaction Records**
   - SMS purchases don't create Transaction records
   - Only credits/refunds tracked
   - No audit trail for "what did I spend money on?"

4. **No Real-time Balance Updates**
   - Frontend polls balance endpoint
   - No WebSocket/SSE for instant updates
   - User may not notice deduction immediately

---

## Solution: Ultra-Fast Transaction Monitoring

### Phase 1: Immediate Fixes (Week 1)

#### 1.1 Add Transaction Records for SMS Purchases

**File**: `app/api/verification/consolidated_verification.py`

```python
# After line 156: current_user.credits -= base_cost
# ADD THIS:
from app.models.transaction import Transaction

transaction = Transaction(
    user_id=user_id,
    amount=-base_cost,  # Negative for deduction
    type="sms_purchase",
    description=f"{verification_data.service_name} verification ({verification_data.country})",
    service=verification_data.service_name,
    status="completed"
)
db.add(transaction)

# Send instant notification
from app.services.notification_service import NotificationService
notif_service = NotificationService(db)
notif_service.create_notification(
    user_id=user_id,
    notification_type="credit_deducted",
    title="💳 Credits Used",
    message=f"${base_cost:.2f} deducted for {verification_data.service_name} verification. New balance: ${current_user.credits:.2f}",
    link=f"/verify/{verification.id}",
    icon="credit_card"
)

db.commit()
```

#### 1.2 Guarantee Refund Notifications

**File**: `app/services/auto_refund_service.py` (line 115-122)

```python
# REPLACE the try/except block with:
from app.services.notification_service import NotificationService

notif_service = NotificationService(self.db)
try:
    notif_service.create_notification(
        user_id=verification.user_id,
        notification_type="instant_refund",
        title="💰 Instant Refund Processed",
        message=f"${refund_amount:.2f} refunded for {verification.service_name} ({reason}). New balance: ${new_balance:.2f}",
        link="/wallet",
        icon="money_back"
    )
    self.db.commit()  # Ensure notification is saved
    logger.info(f"Refund notification sent to user {verification.user_id}")
except Exception as e:
    logger.error(f"CRITICAL: Failed to send refund notification: {e}", exc_info=True)
    # Don't fail the refund, but alert admin
    # TODO: Send admin alert
```

#### 1.3 Add Payment Credit Notifications

**File**: `app/services/payment_service.py` (after line 85)

```python
# After: payment_credits.inc()
# ADD THIS:
from app.services.notification_service import NotificationService

notif_service = NotificationService(self.db)
notif_service.create_notification(
    user_id=user_id,
    notification_type="credit_added",
    title="✅ Credits Added",
    message=f"${amount:.2f} added to your account. New balance: ${user.credits:.2f}",
    link="/wallet",
    icon="add_circle"
)
self.db.commit()
logger.info(f"Credit notification sent to user {user_id}")
```

---

### Phase 2: Enhanced Monitoring (Week 2)

#### 2.1 Transaction History API Enhancement

**New Endpoint**: `/api/wallet/transactions/detailed`

```python
@router.get("/transactions/detailed")
async def get_detailed_transactions(
    type: Optional[str] = None,  # credit, debit, sms_purchase, refund
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed transaction history with filters."""
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)
    
    if type:
        query = query.filter(Transaction.type == type)
    if start_date:
        query = query.filter(Transaction.created_at >= start_date)
    if end_date:
        query = query.filter(Transaction.created_at <= end_date)
    
    total = query.count()
    transactions = query.order_by(desc(Transaction.created_at)).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "transactions": [
            {
                "id": t.id,
                "amount": t.amount,
                "type": t.type,
                "description": t.description,
                "service": t.service,
                "status": t.status,
                "created_at": t.created_at.isoformat(),
                "balance_after": None  # TODO: Calculate running balance
            }
            for t in transactions
        ]
    }
```

#### 2.2 Real-time Balance Updates (WebSocket)

**New File**: `app/api/websocket/balance.py`

```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set

class BalanceConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
    
    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
    
    async def send_balance_update(self, user_id: str, balance: float, transaction: dict):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json({
                        "type": "balance_update",
                        "balance": balance,
                        "transaction": transaction,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                except:
                    pass

manager = BalanceConnectionManager()

@router.websocket("/ws/balance")
async def balance_websocket(websocket: WebSocket, token: str):
    # Verify token and get user_id
    user_id = verify_token(token)
    await manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
```

#### 2.3 Transaction Monitoring Dashboard

**New Endpoint**: `/api/admin/transactions/monitor`

```python
@router.get("/transactions/monitor")
async def monitor_transactions(
    minutes: int = 60,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Real-time transaction monitoring for admins."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    
    transactions = db.query(Transaction).filter(
        Transaction.created_at >= cutoff
    ).order_by(desc(Transaction.created_at)).all()
    
    summary = {
        "total_transactions": len(transactions),
        "credits_added": sum(t.amount for t in transactions if t.type == "credit" and t.amount > 0),
        "credits_spent": abs(sum(t.amount for t in transactions if t.type == "sms_purchase")),
        "refunds_issued": sum(t.amount for t in transactions if t.type == "verification_refund"),
        "unique_users": len(set(t.user_id for t in transactions)),
        "by_type": {},
        "recent_transactions": []
    }
    
    # Group by type
    for t in transactions:
        summary["by_type"][t.type] = summary["by_type"].get(t.type, 0) + 1
    
    # Recent transactions
    summary["recent_transactions"] = [
        {
            "id": t.id,
            "user_id": t.user_id,
            "amount": t.amount,
            "type": t.type,
            "description": t.description,
            "created_at": t.created_at.isoformat()
        }
        for t in transactions[:20]
    ]
    
    return summary
```

---

### Phase 3: Advanced Features (Week 3-4)

#### 3.1 Transaction Alerts

```python
class TransactionAlertService:
    """Alert service for suspicious transactions."""
    
    def check_suspicious_activity(self, user_id: str, transaction: Transaction):
        """Check for suspicious patterns."""
        # Large deduction
        if transaction.type == "sms_purchase" and abs(transaction.amount) > 50:
            self.send_alert(user_id, "large_deduction", transaction)
        
        # Rapid transactions
        recent = self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.created_at >= datetime.now(timezone.utc) - timedelta(minutes=5)
        ).count()
        
        if recent > 10:
            self.send_alert(user_id, "rapid_transactions", transaction)
        
        # Negative balance
        user = self.db.query(User).filter(User.id == user_id).first()
        if user.credits < 0:
            self.send_alert(user_id, "negative_balance", transaction)
```

#### 3.2 Notification Preferences

```python
class NotificationPreferences(BaseModel):
    __tablename__ = "notification_preferences"
    
    user_id = Column(String, ForeignKey("users.id"), unique=True)
    email_on_credit = Column(Boolean, default=True)
    email_on_debit = Column(Boolean, default=True)
    email_on_refund = Column(Boolean, default=True)
    push_on_credit = Column(Boolean, default=True)
    push_on_debit = Column(Boolean, default=False)
    push_on_refund = Column(Boolean, default=True)
    min_amount_notify = Column(Float, default=0.0)
```

---

## Implementation Priority

### 🔴 Critical (Do First - 2 hours)
1. Add Transaction records for SMS purchases
2. Add notifications for credit deductions
3. Guarantee refund notifications don't fail silently

### 🟡 Important (Week 1 - 8 hours)
4. Enhanced transaction history API
5. Transaction monitoring dashboard
6. Payment credit notifications

### 🟢 Nice to Have (Week 2-3 - 16 hours)
7. WebSocket real-time updates
8. Transaction alerts
9. Notification preferences
10. Email notifications

---

## Testing Checklist

### Manual Testing
- [ ] Create verification → Check notification appears
- [ ] Check transaction record created
- [ ] Cancel verification → Check refund notification
- [ ] Check refund transaction record
- [ ] Add credits via payment → Check notification
- [ ] View transaction history → All types visible

### Automated Testing
```python
def test_sms_purchase_creates_transaction():
    # Create verification
    response = client.post("/api/v1/verify/create", json={...})
    
    # Check transaction created
    transactions = client.get("/api/wallet/transactions").json()
    assert any(t["type"] == "sms_purchase" for t in transactions["transactions"])

def test_sms_purchase_sends_notification():
    # Create verification
    response = client.post("/api/v1/verify/create", json={...})
    
    # Check notification created
    notifications = client.get("/api/notifications").json()
    assert any(n["type"] == "credit_deducted" for n in notifications)
```

---

## Logs to Monitor

### Production Logs to Tail
```bash
# Transaction flow
grep -E "Credits|Transaction|Notification|Refund" logs/app.log | tail -100

# Specific patterns
grep "Credits Used\|Instant Refund\|Credits Added" logs/app.log

# Failed notifications
grep "Failed to send.*notification" logs/app.log

# Balance changes
grep "Balance.*→" logs/app.log
```

### Key Log Patterns to Watch
1. `Credits deducted: User=X, Amount=Y, Service=Z`
2. `Notification sent: Type=credit_deducted, User=X`
3. `Auto-refund processed: Verification=X, Amount=Y`
4. `CRITICAL: Failed to send refund notification`
5. `Transaction created: Type=sms_purchase, Amount=X`

---

## Metrics to Track

```python
# Add these Prometheus metrics
transaction_counter = Counter(
    "transactions_total",
    "Total transactions",
    ["type", "status"]
)

notification_counter = Counter(
    "notifications_total",
    "Total notifications sent",
    ["type", "success"]
)

refund_latency = Histogram(
    "refund_latency_seconds",
    "Time from verification failure to refund"
)
```

---

## Next Steps

1. **Review this document** - Confirm approach
2. **Implement Phase 1** - Critical fixes (2 hours)
3. **Test in staging** - Verify notifications work
4. **Deploy to production** - Monitor logs closely
5. **Implement Phase 2** - Enhanced monitoring (1 week)
6. **User feedback** - Adjust based on usage

---

**Estimated Total Time**: 
- Phase 1 (Critical): 2-4 hours
- Phase 2 (Important): 8-12 hours  
- Phase 3 (Advanced): 16-24 hours
- **Total**: 26-40 hours over 3-4 weeks
