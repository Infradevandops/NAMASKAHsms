# 🚨 BALANCE SYNC QUICK REFERENCE

**Date**: 2026-04-17  
**Status**: 🔴 CRITICAL - Action Required  
**Time to Fix**: 8-10 hours

---

## 🎯 The Problem (30 Second Summary)

User on **Custom tier** ($35/month) charged **$2.50/SMS** instead of **$0.20/SMS**.  
Dashboard shows **$2.40**, logs show **$6.90**, actual API balance **unknown**.  
No refund notifications. No transaction logs. **Financial records don't match.**

---

## 🔥 4 Critical Issues

| # | Issue | Impact | Fix Time |
|---|-------|--------|----------|
| 1 | **Tier pricing bug** | User overcharged $9.20 | 3 hours |
| 2 | **Balance sync failure** | Frontend shows wrong balance | 2 hours |
| 3 | **Missing refund notifications** | User can't see refunds | 1 hour |
| 4 | **No transaction logs** | No audit trail | 3 hours |

---

## ⚡ Quick Start (5 Minutes)

### 1. Check Actual Balance
```bash
cd "/Users/machine/My Drive/Github Projects/Namaskah. app"
source .env
python3 scripts/check_api_balance.py
```

**Decision Tree**:
- Balance = $2.40 → No refunds, need timeout handling
- Balance = $6.90 → Partial refunds, need frontend sync
- Balance = $12.40 → Full refunds, need sync + notifications
- Balance = other → Investigate further

---

## 🔧 Fix Priority Order

### 1️⃣ Tier Pricing (P0 - Fix First)
**File**: `app/services/sms_service.py`  
**Change**: Add tier-aware pricing before charging user  
**Test**: Create SMS with Custom tier user, verify $0.20 rate

### 2️⃣ Balance Sync (P1 - Fix Second)
**Files**: `app/websocket/manager.py`, frontend WebSocket listener  
**Change**: Send balance_update event after every transaction  
**Test**: Charge user, verify dashboard updates immediately

### 3️⃣ Refund Notifications (P1 - Fix Third)
**File**: `app/services/notification_service.py`  
**Change**: Create notification on refund  
**Test**: Refund SMS, verify notification appears

### 4️⃣ Transaction Logging (P1 - Fix Fourth)
**Files**: New migration, all financial operations  
**Change**: Log every debit/credit with metadata  
**Test**: Perform transaction, verify log entry created

---

## 📊 Evidence Summary

### From Screenshots
- User: Custom tier ($35/month)
- 4 SMS attempted, all "Still Waiting"
- Each charged $2.50 (should be $0.20)
- Dashboard balance: $2.40
- Total spent: $10.00
- Success rate: 0%

### From Logs
- User ID: `2986207f-4e45-4249-91c3-e5e13bae6622`
- Tier confirmed: `custom`
- Balance at 14:16:07: $5.40
- Balance at 14:20:09: $6.90
- Difference: +$1.50 (possible refund)

### Discrepancy
- Dashboard: $2.40
- Log: $6.90
- Gap: $4.50 ❌

---

## 🎯 Success Criteria

✅ Custom tier charged $0.20/SMS (not $2.50)  
✅ Dashboard balance matches API balance  
✅ Refund notifications visible to user  
✅ All transactions logged in database  
✅ Balance updates in real-time (<1s)  
✅ SMS timeout after 10 minutes with auto-refund

---

## 📁 Key Files

### To Read
- `docs/tasks/BALANCE_SYNC_FINANCIAL_INTEGRITY.md` - Full analysis
- `docs/tasks/BALANCE_SYNC_EXECUTIVE_SUMMARY.md` - Executive summary
- `README.md` - Tier pricing table

### To Modify
- `app/services/sms_service.py` - Add tier pricing
- `app/services/tier_service.py` - Add rate calculation
- `app/services/notification_service.py` - Add refund notifications
- `app/websocket/manager.py` - Add balance updates
- `app/models/transaction.py` - Add transaction logging

### To Create
- `migrations/add_transaction_logs.py` - Transaction log table
- `tests/unit/test_tier_pricing.py` - Tier pricing tests
- `tests/integration/test_balance_sync.py` - Balance sync tests

---

## 🧪 Testing Checklist

### Unit Tests
- [ ] Freemium tier: $2.22/SMS
- [ ] Pay-As-You-Go tier: $2.50/SMS
- [ ] Pro tier: $0.30 overage (after $15 quota)
- [ ] Custom tier: $0.20 overage (after $25 quota)

### Integration Tests
- [ ] Create SMS → Balance deducted → Transaction logged
- [ ] Refund SMS → Balance restored → Notification sent
- [ ] WebSocket → Balance updated → Frontend refreshed

### Manual Tests
- [ ] Create SMS with each tier
- [ ] Verify correct rate charged
- [ ] Verify balance updates immediately
- [ ] Verify notification appears
- [ ] Verify transaction log created

---

## 💡 Code Snippets

### Tier Pricing
```python
def get_sms_rate(user: User) -> Decimal:
    tier = user.subscription_tier
    if tier == "custom":
        if user.monthly_usage >= 25.00:
            return Decimal("0.20")  # Overage
        return Decimal("0.00")  # Within quota
    # ... other tiers
```

### Balance Update
```python
await websocket_manager.send_personal_message(
    user_id=user.id,
    message={
        "type": "balance_update",
        "balance": float(new_balance)
    }
)
```

### Refund Notification
```python
await notification_service.create_notification(
    user_id=user.id,
    type="refund",
    title="Refund Processed",
    message=f"${amount:.2f} refunded"
)
```

### Transaction Log
```python
await db.execute(
    insert(TransactionLog).values(
        user_id=user.id,
        transaction_type="REFUND",
        amount=amount,
        balance_before=old_balance,
        balance_after=new_balance
    )
)
```

---

## 📞 Questions?

- **Full Details**: `docs/tasks/BALANCE_SYNC_FINANCIAL_INTEGRITY.md`
- **Executive Summary**: `docs/tasks/BALANCE_SYNC_EXECUTIVE_SUMMARY.md`
- **Balance Check**: `scripts/check_api_balance.py`

---

**START HERE**: Run balance check script, then fix tier pricing first.
