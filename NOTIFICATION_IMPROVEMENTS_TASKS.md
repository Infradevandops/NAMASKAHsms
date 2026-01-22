# 📋 VERIFICATION FLOW - NOTIFICATION IMPROVEMENTS TASK LIST

**Created**: 2026-01-22
**Priority**: HIGH
**Estimated Time**: 2-3 hours total

---

## 🎯 OBJECTIVE

Enhance verification flow with instant, comprehensive in-app notifications for all user actions and system events.

---

## ✅ COMPLETED (Already Fixed)

- [x] Automatic refund system
- [x] Two-phase commit (API first, charge after)
- [x] Idempotency protection
- [x] Circuit breaker implementation
- [x] Basic notifications (low balance, SMS received, timeout)

---

## 🚀 PHASE 1: CRITICAL NOTIFICATIONS (25 minutes)

### Task 1.1: Enhanced Cancellation Notification
**Priority**: CRITICAL | **Time**: 10 min

**File**: `app/api/verification/cancel_endpoint.py`

**Action**: Add instant notification when user cancels verification

```python
# After successful cancellation
notif_service.create_notification(
    user_id=user_id,
    notification_type="verification_cancelled",
    title="❌ Verification Cancelled",
    message=f"${refund_amount:.2f} refunded instantly to your account"
)
```

**Acceptance Criteria**:
- [x] Notification appears immediately after cancellation
- [x] Shows refund amount
- [x] Shows new balance

---

### Task 1.2: Prominent Instant Refund Alert
**Priority**: CRITICAL | **Time**: 5 min

**File**: `app/services/auto_refund_service.py`

**Action**: Enhance existing refund notification to be more prominent

```python
# Update existing notification
notif_service.create_notification(
    user_id=verification.user_id,
    notification_type="instant_refund",
    title="💰 Instant Refund Processed",
    message=f"${refund_amount:.2f} refunded for {service} - New balance: ${new_balance:.2f}"
)
```

**Acceptance Criteria**:
- [x] Clear refund amount displayed
- [x] Shows reason (timeout/cancelled/failed)
- [x] Shows updated balance

---

### Task 1.3: API Failure Notification
**Priority**: HIGH | **Time**: 10 min

**File**: `app/api/verification/purchase_endpoints.py`

**Action**: Notify user when TextVerified API fails

```python
# In exception handler
except Exception as api_error:
    db.rollback()
    
    # Notify user
    try:
        notif_service = NotificationService(db)
        notif_service.create_notification(
            user_id=user_id,
            notification_type="verification_failed",
            title="⚠️ Verification Failed",
            message="SMS service temporarily unavailable. Your credits were not charged."
        )
    except:
        pass
    
    raise HTTPException(...)
```

**Acceptance Criteria**:
- [x] User notified immediately on API failure
- [x] Confirms no charge was made
- [x] Suggests retry

---

## 🔔 PHASE 2: ENHANCED NOTIFICATIONS (1 hour)

### Task 2.1: Order Initiated Enhancement
**Priority**: MEDIUM | **Time**: 10 min

**File**: `app/api/verification/purchase_endpoints.py`

**Action**: Enhance existing notification with more details

```python
notif_service.create_notification(
    user_id=user_id,
    notification_type="verification_initiated",
    title="🎯 Verification Started",
    message=f"Purchasing {service} number in {country} for ${cost:.2f}"
)
```

**Acceptance Criteria**:
- [x] Shows service name
- [x] Shows country
- [x] Shows exact cost

---

### Task 2.2: Number Purchased Confirmation
**Priority**: MEDIUM | **Time**: 15 min

**File**: `app/api/verification/purchase_endpoints.py`

**Action**: Add notification after successful number purchase

```python
# After db.commit()
notif_service.create_notification(
    user_id=user_id,
    notification_type="number_purchased",
    title="📱 Number Purchased",
    message=f"Phone: {phone_number} - Waiting for SMS code..."
)
```

**Acceptance Criteria**:
- [x] Shows purchased phone number
- [x] Indicates waiting for SMS
- [x] Links to verification status

---

### Task 2.3: SMS Polling Progress Updates
**Priority**: MEDIUM | **Time**: 20 min

**File**: `app/services/sms_polling_service.py`

**Action**: Add periodic progress notifications

```python
# After 2 minutes of polling
if attempt == 4:  # 2 minutes at 30s intervals
    notif_service.create_notification(
        user_id=verification.user_id,
        notification_type="verification_progress",
        title="⏳ Still Waiting",
        message=f"Waiting for SMS code for {service}..."
    )
```

**Acceptance Criteria**:
- [x] Progress update after 2 minutes
- [x] Not too frequent (avoid spam)
- [x] Clear status indication

---

### Task 2.4: SMS Code Received Enhancement
**Priority**: MEDIUM | **Time**: 10 min

**File**: `app/services/sms_polling_service.py`

**Action**: Enhance existing notification with code preview

```python
notif_service.create_notification(
    user_id=verification.user_id,
    notification_type="verification_complete",
    title="✅ SMS Code Received!",
    message=f"Code: {sms_code} for {service_name}"
)
```

**Acceptance Criteria**:
- [x] Shows actual code
- [x] Shows service name
- [x] Prominent success indicator

---

### Task 2.5: Balance Update Notifications
**Priority**: LOW | **Time**: 5 min

**File**: `app/api/verification/purchase_endpoints.py`

**Action**: Show balance after charge

```python
# After credit deduction
if new_balance < old_balance:
    notif_service.create_notification(
        user_id=user_id,
        notification_type="balance_update",
        title="💳 Balance Updated",
        message=f"${actual_cost:.2f} charged - New balance: ${new_balance:.2f}"
    )
```

**Acceptance Criteria**:
- [x] Shows amount charged
- [x] Shows new balance
- [x] Clear transaction record

---

## 🌐 PHASE 3: REAL-TIME PUSH (Future Sprint)

### Task 3.1: WebSocket/SSE Implementation
**Priority**: LOW | **Time**: 4-6 hours

**Action**: Implement real-time push notifications

**Components**:
- WebSocket server setup
- Client-side connection handler
- Event broadcasting system
- Reconnection logic

**Acceptance Criteria**:
- [ ] Real-time updates without refresh
- [ ] Automatic reconnection
- [ ] Fallback to polling

---

### Task 3.2: Notification Preferences
**Priority**: LOW | **Time**: 2-3 hours

**Action**: User notification settings

**Features**:
- Email notifications toggle
- In-app notifications toggle
- Notification frequency settings
- Quiet hours

**Acceptance Criteria**:
- [ ] User can control notification types
- [ ] Settings persist
- [ ] Respects user preferences

---

## 📊 TESTING CHECKLIST

### Manual Testing
- [ ] Create verification → Check "initiated" notification
- [ ] Wait for SMS → Check "received" notification
- [ ] Cancel verification → Check "cancelled" + refund notification
- [ ] Trigger timeout → Check "timeout" + refund notification
- [ ] Cause API failure → Check "failed" notification
- [ ] Check balance updates → Verify amounts correct

### Automated Testing
- [ ] Unit tests for notification creation
- [ ] Integration tests for notification flow
- [ ] E2E tests for user journey

---

## 🚀 DEPLOYMENT PLAN

### Phase 1 (Today)
1. Implement Task 1.1, 1.2, 1.3 (25 min)
2. Test locally (10 min)
3. Deploy to production (5 min)
4. Monitor for 1 hour

### Phase 2 (This Week)
1. Implement Task 2.1-2.5 (1 hour)
2. Test thoroughly (30 min)
3. Deploy to production
4. Monitor for 24 hours

### Phase 3 (Next Sprint)
1. Plan WebSocket architecture
2. Implement and test
3. Gradual rollout

---

## 📈 SUCCESS METRICS

### Immediate (24 hours)
- [ ] 100% of events have notifications
- [ ] 0 missed notifications
- [ ] User feedback positive

### Short-term (1 week)
- [ ] 50% reduction in "where's my refund?" tickets
- [ ] 30% reduction in status check API calls
- [ ] 90%+ user satisfaction

### Long-term (1 month)
- [ ] Real-time updates implemented
- [ ] User preferences available
- [ ] 95%+ notification delivery rate

---

## 🔧 ROLLBACK PLAN

If notifications cause issues:
1. Disable new notifications (feature flag)
2. Revert to basic notifications
3. Fix issues in staging
4. Redeploy

---

## 📝 NOTES

- Keep notifications concise and actionable
- Use emojis for visual clarity
- Include relevant amounts and balances
- Link to relevant pages when possible
- Avoid notification spam (max 1 per event)

---

**Status**: READY TO IMPLEMENT
**Owner**: Development Team
**Reviewer**: Product Manager
**Due Date**: Phase 1 (Today), Phase 2 (This Week)
