# Phase 1: Fix 45 Failing Tests

## Objective
Fix all 45 failing tests to unblock CI/CD and increase coverage to 40-42%

## Timeline
5-7 hours

## Failing Tests Breakdown

### Category A: Activity Feed (6 tests)
**Status:** 1 fixed, 5 remaining

#### ✅ FIXED
- [x] `test_activity_to_dict` - Fixed field name (metadata → activity_data)

#### TODO
- [ ] `test_get_activities_endpoint` - Endpoint test, needs client fixture
- [ ] `test_get_activity_by_id_endpoint` - Endpoint test, needs client fixture
- [ ] `test_get_activity_summary_endpoint` - Endpoint test, needs client fixture
- [ ] `test_export_activities_json` - Endpoint test, needs client fixture
- [ ] `test_export_activities_csv` - Endpoint test, needs client fixture

**Fix Strategy:**
```python
def test_get_activities_endpoint(self, client, test_user):
    """Test getting activities endpoint."""
    # Create test activity
    activity = Activity(
        user_id=test_user.id,
        activity_type="payment",
        resource_type="payment",
        action="completed",
        title="Test Activity"
    )
    db.add(activity)
    db.commit()
    
    # Test endpoint
    response = client.get(f"/api/activities?user_id={test_user.id}")
    assert response.status_code == 200
    assert len(response.json()["activities"]) > 0
```

---

### Category B: Email Notifications (8 tests)
**Status:** All failing

#### TODO
- [ ] `test_send_notification_email` - Mock email service
- [ ] `test_send_verification_initiated_email` - Mock email service
- [ ] `test_send_verification_completed_email` - Mock email service
- [ ] `test_send_low_balance_alert_email` - Mock email service
- [ ] `test_send_daily_digest_email` - Mock email service
- [ ] `test_send_weekly_digest_email` - Mock email service
- [ ] `test_send_test_email_endpoint` - Endpoint test
- [ ] `test_get_email_preferences_endpoint` - Endpoint test

**Fix Strategy:**
```python
@pytest.mark.asyncio
async def test_send_notification_email(self, email_service, test_user):
    """Test sending notification email."""
    with patch.object(email_service, '_send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        
        result = await email_service.send_notification_email(
            user_id=test_user.id,
            subject="Test",
            body="Test body"
        )
        
        assert result is True
        mock_send.assert_called_once()
```

---

### Category C: Payment Tests (3 tests)
**Status:** All failing

#### TODO
- [ ] `test_duplicate_payment_prevented` - Fix idempotency logic
- [ ] `test_concurrent_payment_handling` - Fix concurrency
- [ ] `test_handle_charge_success_webhook` - Fix webhook handling

**Fix Strategy:**
```python
@pytest.mark.asyncio
async def test_duplicate_payment_prevented(self, payment_service, regular_user, db_session):
    """Test that duplicate payments are prevented."""
    reference = "ref_unique_123"
    
    # First payment should succeed
    result1 = await payment_service.credit_user(reference, 10.0, regular_user.id)
    assert result1["status"] == "success"
    
    # Second payment with same reference should be prevented
    result2 = await payment_service.credit_user(reference, 10.0, regular_user.id)
    assert result2["status"] == "duplicate"
```

---

### Category D: Tier Management (4 tests)
**Status:** All failing

#### TODO
- [ ] `test_check_feature_access` - Fix tier configuration
- [ ] `test_can_create_api_key_limits` - Fix tier limits
- [ ] `test_feature_access` (tier_manager) - Fix feature flags
- [ ] `test_can_create_api_key` (tier_manager) - Fix API key limits

**Fix Strategy:**
```python
def test_check_feature_access(self, db_session, regular_user):
    """Test checking feature access by tier."""
    # Freemium user should have limited features
    assert TierManager.can_access_feature(db_session, regular_user.id, "api_keys") is False
    
    # Upgrade to pro
    regular_user.subscription_tier = "pro"
    db_session.commit()
    
    # Pro user should have access
    assert TierManager.can_access_feature(db_session, regular_user.id, "api_keys") is True
```

---

### Category E: WebSocket (4 tests)
**Status:** All failing

#### TODO
- [ ] `test_broadcast_to_channel` - Fix connection manager
- [ ] `test_get_websocket_status_endpoint` - Fix endpoint
- [ ] `test_broadcast_notification_endpoint_admin` - Fix broadcast
- [ ] `test_broadcast_notification_endpoint_non_admin` - Fix permissions

**Fix Strategy:**
```python
@pytest.mark.asyncio
async def test_broadcast_to_channel(self):
    """Test broadcasting to channel."""
    manager = ConnectionManager()
    
    # Simulate connections
    mock_connection = AsyncMock()
    manager.active_connections["channel1"] = [mock_connection]
    
    # Broadcast message
    await manager.broadcast("channel1", {"type": "notification", "data": "test"})
    
    # Verify send was called
    mock_connection.send_json.assert_called_once()
```

---

### Category F: Notification Center (20 tests)
**Status:** All failing

#### TODO
- [ ] `test_get_notification_center` - Fix query logic
- [ ] `test_get_notification_center_with_category_filter` - Fix filtering
- [ ] `test_get_notification_center_with_read_filter` - Fix read status
- [ ] `test_get_notification_center_with_sorting` - Fix sorting
- [ ] `test_get_notification_categories` - Fix categories
- [ ] `test_search_notifications` - Fix search
- [ ] `test_search_notifications_min_length` - Fix validation
- [ ] `test_bulk_mark_as_read` - Fix bulk operations
- [ ] `test_bulk_delete_notifications` - Fix bulk delete
- [ ] `test_export_notifications_json` - Fix export
- [ ] `test_export_notifications_csv` - Fix export
- [ ] `test_user_isolation` - Fix user isolation
- [ ] + 8 more preference tests

**Fix Strategy:**
```python
def test_get_notification_center(self, client, test_user, db_session):
    """Test getting notification center."""
    # Create test notifications
    for i in range(3):
        notification = Notification(
            user_id=test_user.id,
            type="payment",
            title=f"Notification {i}",
            message="Test message"
        )
        db_session.add(notification)
    db_session.commit()
    
    # Test endpoint
    response = client.get(f"/api/notifications?user_id={test_user.id}")
    assert response.status_code == 200
    assert len(response.json()["notifications"]) == 3
```

---

## Execution Plan

### Step 1: Activity Feed (1-2 hours)
1. Review `tests/unit/test_activity_feed.py`
2. Fix endpoint tests with proper client setup
3. Verify all 6 tests pass

### Step 2: Email Notifications (2-3 hours)
1. Review `tests/unit/test_email_notifications.py`
2. Add proper email service mocking
3. Fix async test setup
4. Verify all 8 tests pass

### Step 3: Payment Tests (1-2 hours)
1. Review `tests/unit/test_payment_*.py`
2. Fix idempotency logic
3. Fix Redis mock setup
4. Verify all 3 tests pass

### Step 4: Tier Management (1-2 hours)
1. Review `tests/unit/test_tier_*.py`
2. Fix tier configuration
3. Fix feature access logic
4. Verify all 4 tests pass

### Step 5: WebSocket (2-3 hours)
1. Review `tests/unit/test_websocket.py`
2. Fix connection manager setup
3. Fix broadcast logic
4. Verify all 4 tests pass

### Step 6: Notification Center (3-4 hours)
1. Review `tests/unit/test_notification_*.py`
2. Fix query logic
3. Fix filtering and sorting
4. Verify all 20 tests pass

---

## Verification

After each category:
```bash
# Run category tests
python3 -m pytest tests/unit/test_[category].py -v

# Check coverage
python3 -m pytest tests/unit/ --cov=app --cov-report=term-missing:skip-covered | grep "Total coverage"
```

---

## Success Criteria

- [ ] All 45 tests passing
- [ ] Coverage increased to 40-42%
- [ ] No collection errors
- [ ] CI/CD checks green
- [ ] Code quality passing

---

## Notes

- Use existing fixtures from `tests/conftest.py`
- Mock external services (email, Redis, WebSocket)
- Test both success and error paths
- Keep tests focused and atomic
- Add clear docstrings
