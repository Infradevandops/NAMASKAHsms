# Phase 3: Infrastructure Tests (170+ Tests)

## Objective
Create infrastructure tests to increase coverage from 55-60% to 75-80%

## Timeline
10-12 hours

## Test Files to Create

### 1. Middleware Tests (40+ tests)
**File:** `tests/unit/test_middleware_comprehensive.py`

**Middleware to Test:**
- CSRF middleware
- Security headers middleware
- Rate limiting middleware
- Request logging middleware
- XSS protection middleware

**Test Template:**
```python
class TestCSRFMiddleware:
    """Test CSRF protection middleware."""
    
    def test_csrf_token_validation(self, client):
        """Test CSRF token validation."""
        # Get CSRF token
        response = client.get("/api/csrf-token")
        csrf_token = response.json()["token"]
        
        # POST without token should fail
        response = client.post("/api/test", json={})
        assert response.status_code == 403
        
        # POST with token should succeed
        response = client.post(
            "/api/test",
            json={},
            headers={"X-CSRF-Token": csrf_token}
        )
        assert response.status_code == 200

class TestSecurityHeaders:
    """Test security headers middleware."""
    
    def test_security_headers_present(self, client):
        """Test security headers are present."""
        response = client.get("/api/health")
        
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"

class TestRateLimiting:
    """Test rate limiting middleware."""
    
    def test_rate_limit_exceeded(self, client):
        """Test rate limit enforcement."""
        # Make requests up to limit
        for i in range(100):
            response = client.get("/api/test")
            if response.status_code == 429:
                break
        
        # Should be rate limited
        assert response.status_code == 429
        assert "Retry-After" in response.headers
```

---

### 2. Core Module Tests (50+ tests)
**File:** `tests/unit/test_core_comprehensive.py`

**Modules to Test:**
- Database operations
- Encryption/decryption
- RBAC (Role-Based Access Control)
- Feature flags
- Cache operations
- Session management

**Test Template:**
```python
class TestDatabaseOperations:
    """Test database operations."""
    
    def test_connection_pooling(self, db):
        """Test database connection pooling."""
        # Create multiple connections
        connections = []
        for i in range(5):
            conn = db.connection()
            connections.append(conn)
        
        # All should be from pool
        assert len(connections) == 5

class TestEncryption:
    """Test encryption/decryption."""
    
    def test_encrypt_decrypt(self):
        """Test encryption and decryption."""
        from app.core.encryption import encrypt, decrypt
        
        plaintext = "sensitive_data"
        encrypted = encrypt(plaintext)
        decrypted = decrypt(encrypted)
        
        assert decrypted == plaintext
        assert encrypted != plaintext

class TestRBAC:
    """Test role-based access control."""
    
    def test_admin_access(self, admin_user):
        """Test admin access."""
        from app.core.rbac import has_permission
        
        assert has_permission(admin_user, "admin:read") is True
        assert has_permission(admin_user, "admin:write") is True

class TestFeatureFlags:
    """Test feature flags."""
    
    def test_feature_flag_enabled(self):
        """Test feature flag enabled."""
        from app.core.feature_flags import is_enabled
        
        # Mock feature flag
        with patch("app.core.feature_flags.get_flag") as mock_get:
            mock_get.return_value = True
            assert is_enabled("new_feature") is True

class TestCache:
    """Test cache operations."""
    
    def test_cache_set_get(self):
        """Test cache set and get."""
        from app.core.unified_cache import cache
        
        cache.set("key", "value", ttl=60)
        assert cache.get("key") == "value"
        
        cache.delete("key")
        assert cache.get("key") is None
```

---

### 3. WebSocket Tests (30+ tests)
**File:** `tests/unit/test_websocket_comprehensive.py`

**Components to Test:**
- Connection management
- Message broadcasting
- Channel subscriptions
- Disconnection handling
- Error scenarios

**Test Template:**
```python
class TestConnectionManager:
    """Test WebSocket connection manager."""
    
    @pytest.mark.asyncio
    async def test_connect_disconnect(self):
        """Test connect and disconnect."""
        manager = ConnectionManager()
        mock_connection = AsyncMock()
        
        # Connect
        manager.connect("user1", "channel1", mock_connection)
        assert "user1" in manager.active_connections.get("channel1", [])
        
        # Disconnect
        manager.disconnect("user1", "channel1")
        assert "user1" not in manager.active_connections.get("channel1", [])
    
    @pytest.mark.asyncio
    async def test_broadcast_message(self):
        """Test broadcasting message."""
        manager = ConnectionManager()
        mock_conn1 = AsyncMock()
        mock_conn2 = AsyncMock()
        
        manager.connect("user1", "channel1", mock_conn1)
        manager.connect("user2", "channel1", mock_conn2)
        
        # Broadcast
        await manager.broadcast("channel1", {"type": "message", "data": "test"})
        
        # Both should receive
        mock_conn1.send_json.assert_called_once()
        mock_conn2.send_json.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_private_message(self):
        """Test private message."""
        manager = ConnectionManager()
        mock_conn = AsyncMock()
        
        manager.connect("user1", "channel1", mock_conn)
        
        # Send private message
        await manager.send_personal("user1", {"type": "private", "data": "test"})
        
        mock_conn.send_json.assert_called_once()
```

---

### 4. Notification System Tests (50+ tests)
**File:** `tests/unit/test_notification_system_comprehensive.py`

**Components to Test:**
- Notification creation
- Notification retrieval with filters
- Preference management
- Quiet hours
- Notification categories
- Bulk operations

**Test Template:**
```python
class TestNotificationSystem:
    """Test notification system."""
    
    def test_create_notification(self, db_session, test_user):
        """Test creating notification."""
        notification = Notification(
            user_id=test_user.id,
            type="payment",
            title="Payment Received",
            message="You received $10"
        )
        db_session.add(notification)
        db_session.commit()
        
        assert notification.id is not None
        assert notification.read is False
    
    def test_get_notifications_with_filter(self, db_session, test_user):
        """Test getting notifications with filter."""
        # Create notifications
        for i in range(3):
            notification = Notification(
                user_id=test_user.id,
                type="payment" if i % 2 == 0 else "verification",
                title=f"Notification {i}"
            )
            db_session.add(notification)
        db_session.commit()
        
        # Filter by type
        notifications = db_session.query(Notification).filter(
            Notification.user_id == test_user.id,
            Notification.type == "payment"
        ).all()
        
        assert len(notifications) == 2
    
    def test_mark_as_read(self, db_session, test_user):
        """Test marking notification as read."""
        notification = Notification(
            user_id=test_user.id,
            type="payment",
            title="Test"
        )
        db_session.add(notification)
        db_session.commit()
        
        notification.read = True
        db_session.commit()
        
        assert notification.read is True
    
    def test_bulk_mark_as_read(self, db_session, test_user):
        """Test bulk marking as read."""
        # Create notifications
        notification_ids = []
        for i in range(5):
            notification = Notification(
                user_id=test_user.id,
                type="payment",
                title=f"Notification {i}"
            )
            db_session.add(notification)
            db_session.flush()
            notification_ids.append(notification.id)
        db_session.commit()
        
        # Bulk update
        db_session.query(Notification).filter(
            Notification.id.in_(notification_ids)
        ).update({"read": True})
        db_session.commit()
        
        # Verify
        unread = db_session.query(Notification).filter(
            Notification.id.in_(notification_ids),
            Notification.read == False
        ).count()
        
        assert unread == 0
    
    def test_notification_preferences(self, db_session, test_user):
        """Test notification preferences."""
        preference = NotificationPreference(
            user_id=test_user.id,
            type="payment",
            enabled=False
        )
        db_session.add(preference)
        db_session.commit()
        
        # Check preference
        pref = db_session.query(NotificationPreference).filter(
            NotificationPreference.user_id == test_user.id,
            NotificationPreference.type == "payment"
        ).first()
        
        assert pref.enabled is False
    
    def test_quiet_hours(self, db_session, test_user):
        """Test quiet hours."""
        preference = NotificationPreference(
            user_id=test_user.id,
            quiet_hours_start="22:00",
            quiet_hours_end="08:00"
        )
        db_session.add(preference)
        db_session.commit()
        
        # Check if in quiet hours
        from datetime import datetime
        current_hour = datetime.now().hour
        
        in_quiet_hours = (
            (preference.quiet_hours_start <= preference.quiet_hours_end and
             preference.quiet_hours_start <= current_hour < preference.quiet_hours_end) or
            (preference.quiet_hours_start > preference.quiet_hours_end and
             (current_hour >= preference.quiet_hours_start or current_hour < preference.quiet_hours_end))
        )
        
        # Verify logic
        assert isinstance(in_quiet_hours, bool)
```

---

## Execution Plan

### Step 1: Middleware Tests (2-3 hours)
1. Create `tests/unit/test_middleware_comprehensive.py`
2. Write 40+ tests for all middleware
3. Test request/response handling
4. Verify all tests pass

### Step 2: Core Module Tests (2-3 hours)
1. Create `tests/unit/test_core_comprehensive.py`
2. Write 50+ tests for core modules
3. Test database, encryption, RBAC, cache
4. Verify all tests pass

### Step 3: WebSocket Tests (2-3 hours)
1. Create `tests/unit/test_websocket_comprehensive.py`
2. Write 30+ tests for WebSocket
3. Test connections, broadcasting, channels
4. Verify all tests pass

### Step 4: Notification System Tests (3-4 hours)
1. Create `tests/unit/test_notification_system_comprehensive.py`
2. Write 50+ tests for notifications
3. Test creation, filtering, preferences
4. Verify all tests pass

---

## Verification

```bash
# Run all infrastructure tests
python3 -m pytest tests/unit/test_*_comprehensive.py -v

# Check coverage
python3 -m pytest tests/unit/ --cov=app --cov-report=term-missing:skip-covered
```

---

## Success Criteria

- [ ] 170+ new tests created
- [ ] All infrastructure tests passing
- [ ] Coverage increased to 75-80%
- [ ] All middleware tested
- [ ] All core modules tested
- [ ] WebSocket functionality tested
- [ ] Notification system tested
