# Admin Panel Overhaul - Quick Reference Card

## 📋 Documents

| Document | Purpose | Location |
|----------|---------|----------|
| **ADMIN_OVERHAUL_PLAN.md** | 7-phase strategic roadmap | `docs/deployment/` |
| **PHASE1_IMPLEMENTATION_GUIDE.md** | Step-by-step integration guide | `docs/deployment/` |
| **ADMIN_OVERHAUL_SUMMARY.md** | Executive summary | Root directory |
| **This File** | Quick reference | Root directory |

---

## 🚀 Phase 1 Quick Start

### Files Created (Ready to Use)
```
✅ app/models/user_event.py                    # UserEvent model
✅ app/services/event_tracking_service.py      # Event tracking service
✅ app/api/admin/analytics.py                  # Analytics endpoints
✅ alembic/versions/add_user_events_analytics.py  # Database migration
```

### Integration Steps (2-3 hours)

#### 1. Register Model
**File**: `app/models/__init__.py`
```python
from app.models.user_event import UserEvent
```

#### 2. Register Router
**File**: `main.py`
```python
from app.api.admin.analytics import router as analytics_router
app.include_router(analytics_router)
```

#### 3. Run Migration
```bash
alembic upgrade head
```

#### 4. Add Event Tracking (6 places)
- `app/api/auth_routes.py` - Signup & Login
- `app/api/verification/` - Verification events
- `app/services/payment_service.py` - Payment events
- Tier change endpoints - Tier events

#### 5. Update Dashboard
**File**: `templates/admin/dashboard.html`
- Add analytics tab button
- Add analytics tab page
- Add script reference

#### 6. Create Frontend Manager
**File**: `static/js/admin/analytics.js`
- AnalyticsManager class
- Load overview, at-risk users, live events

---

## 📊 Analytics Endpoints

### Overview
```
GET /api/admin/analytics/overview
```
Returns: total_users, new_users_30d, active_users_7d, success_rate, revenue, etc.

### Cohort Analysis
```
GET /api/admin/analytics/users/cohorts
```
Returns: Retention curves by signup date

### At-Risk Users
```
GET /api/admin/analytics/users/at-risk?days_inactive=7&limit=50
```
Returns: Users inactive for N days

### Live Events
```
GET /api/admin/analytics/events/live?event_type=signup&limit=100
```
Returns: Recent events with user info

### Event Stats
```
GET /api/admin/analytics/events/stats
```
Returns: Total events, unique users, event type breakdown

### Daily Revenue
```
GET /api/admin/analytics/revenue/daily?days=30
```
Returns: Daily revenue breakdown

### Popular Services
```
GET /api/admin/analytics/services/popular?limit=10
```
Returns: Top services by count and revenue

---

## 🎯 Event Types to Track

### User Lifecycle
- `signup` - User registration
- `login` - User login
- `logout` - User logout
- `email_verified` - Email verification
- `password_changed` - Password change

### Verification
- `first_verification` - First SMS verification
- `verification_success` - Successful verification
- `verification_failed` - Failed verification

### Payments
- `payment_initiated` - Payment started
- `payment_completed` - Payment successful
- `payment_failed` - Payment failed
- `refund_issued` - Refund processed

### Tier Management
- `tier_upgrade` - Tier upgrade
- `tier_downgrade` - Tier downgrade

### Features
- `feature_used` - Feature engagement
- `api_key_generated` - API key created
- `rental_created` - Rental created
- `voice_verification_started` - Voice verification started

### Account
- `account_suspended` - Account suspended
- `account_activated` - Account activated
- `account_deleted` - Account deleted
- `mfa_enabled` - MFA enabled
- `mfa_disabled` - MFA disabled

### Support
- `support_ticket_created` - Support ticket created

---

## 💾 Database Tables

### user_events
```sql
CREATE TABLE user_events (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    metadata JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP NOT NULL
);
```

### daily_user_snapshots
```sql
CREATE TABLE daily_user_snapshots (
    id UUID PRIMARY KEY,
    snapshot_date DATE NOT NULL UNIQUE,
    total_users INT,
    active_users INT,
    new_users INT,
    churned_users INT,
    total_revenue DECIMAL(12,2),
    total_verifications INT,
    avg_verification_cost DECIMAL(8,2),
    created_at TIMESTAMP NOT NULL
);
```

### feature_usage
```sql
CREATE TABLE feature_usage (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    usage_count INT DEFAULT 1,
    last_used TIMESTAMP,
    created_at TIMESTAMP NOT NULL
);
```

### admin_alerts
```sql
CREATE TABLE admin_alerts (
    id UUID PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(255),
    description TEXT,
    metadata JSONB,
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP
);
```

---

## 🔧 Code Snippets

### Track Signup
```python
from app.services.event_tracking_service import EventTrackingService

event_service = EventTrackingService(db)
event_service.track_signup(
    user_id=str(user.id),
    metadata={"email": user.email}
)
```

### Track Login
```python
event_service.track_login(
    user_id=str(user.id),
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent")
)
```

### Track Verification
```python
event_service.track_verification(
    user_id=str(user.id),
    service_name="WhatsApp",
    success=True,
    cost=2.50,
    metadata={"verification_id": str(verification.id)}
)
```

### Track Payment
```python
event_service.track_payment(
    user_id=str(user.id),
    amount=50.00,
    success=True,
    metadata={"payment_method": "paystack"}
)
```

### Track Tier Change
```python
event_service.track_tier_change(
    user_id=str(user.id),
    from_tier="freemium",
    to_tier="pro",
    metadata={"reason": "user_upgrade"}
)
```

### Get At-Risk Users
```python
from app.services.event_tracking_service import EventTrackingService

service = EventTrackingService(db)
at_risk = service.get_user_events(
    user_id=user_id,
    event_type=UserEvent.VERIFICATION_SUCCESS,
    limit=100
)
```

---

## 📈 Dashboard Tab Structure

### Analytics Tab
```
┌─ Overview Metrics
│  ├─ Total Users
│  ├─ New Users (30d)
│  ├─ Active Users (7d)
│  └─ Success Rate
│
├─ At-Risk Users
│  └─ Table: Email, Last Activity, Days Inactive, Verifications
│
├─ Live Events
│  └─ Auto-refreshing feed of recent events
│
└─ Popular Services
   └─ Top 10 services by count
```

---

## 🧪 Testing Commands

### Verify Migration
```bash
psql -U postgres -d vrenum_db -c "\dt user_events"
```

### Test Event Creation
```bash
curl -X POST http://localhost:8000/api/admin/analytics/test-event \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "event_type": "test"}'
```

### Test Overview Endpoint
```bash
curl http://localhost:8000/api/admin/analytics/overview \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test At-Risk Users
```bash
curl http://localhost:8000/api/admin/analytics/users/at-risk \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test Live Events
```bash
curl http://localhost:8000/api/admin/analytics/events/live \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] Code reviewed
- [ ] Tests passing
- [ ] Database backup created
- [ ] Rollback plan documented

### Deployment
- [ ] Models registered
- [ ] Router registered
- [ ] Migration run
- [ ] Event tracking added to 6 endpoints
- [ ] Dashboard updated
- [ ] Frontend manager created
- [ ] Scripts added

### Post-Deployment
- [ ] Endpoints tested
- [ ] Events being tracked
- [ ] Dashboard displaying data
- [ ] No errors in logs
- [ ] Performance acceptable
- [ ] Monitoring alerts configured

---

## 🚨 Troubleshooting

### Events Not Being Tracked
1. Check EventTrackingService is imported
2. Verify migration ran: `alembic current`
3. Check logs for errors
4. Verify user_id is valid UUID

### Endpoints Returning Errors
1. Check admin authentication
2. Verify database connection
3. Check SQL queries in logs
4. Review error messages

### Dashboard Not Showing Data
1. Check browser console for JS errors
2. Verify API endpoints accessible
3. Check that events exist in database
4. Verify token is valid

### Performance Issues
1. Check event processing latency
2. Monitor database query times
3. Check for N+1 queries
4. Consider data archival

---

## 📞 Support

### Documentation
- Strategic: `ADMIN_OVERHAUL_PLAN.md`
- Implementation: `PHASE1_IMPLEMENTATION_GUIDE.md`
- Summary: `ADMIN_OVERHAUL_SUMMARY.md`

### Code
- Models: `app/models/user_event.py`
- Service: `app/services/event_tracking_service.py`
- API: `app/api/admin/analytics.py`

### Questions
- Check inline code comments
- Review docstrings
- Check test cases
- Review troubleshooting section

---

## 📅 Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Phase 1: Event Tracking | 3-4 days | ✅ Ready |
| Phase 2: Lifecycle Analytics | 3-4 days | 📋 Planned |
| Phase 3: Revenue Intelligence | 2-3 days | 📋 Planned |
| Phase 4: Feature Analytics | 2-3 days | 📋 Planned |
| Phase 5: Dashboards | 3-4 days | 📋 Planned |
| Phase 6: Alerts | 3-4 days | 📋 Planned |
| Phase 7: Reporting | 2-3 days | 📋 Planned |
| **Total** | **~3-4 weeks** | **📋 Planned** |

---

## 🎯 Success Metrics

### Phase 1
- ✅ Events tracked for all key actions
- ✅ Analytics endpoints working
- ✅ Dashboard displaying data
- ✅ No performance degradation

### Overall
- ✅ Churn reduced by 10%
- ✅ ARPU increased by 15%
- ✅ Support tickets reduced by 20%
- ✅ Decision-making speed improved by 50%

---

**Last Updated**: May 18, 2026  
**Status**: ✅ Phase 1 Ready for Implementation  
**Owner**: Engineering Team
