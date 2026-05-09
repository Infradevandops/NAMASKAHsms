# Push Notifications Implementation Guide

**Task**: PN-01 through PN-07
**Status**: In Progress
**Started**: May 7, 2026
**Target**: 1-2 weeks

---

## Implementation Checklist

### Phase 1: Firebase Setup (PN-01)
- [ ] Create Firebase project
- [ ] Enable Cloud Messaging
- [ ] Generate service account key
- [ ] Configure web push certificates
- [ ] Store credentials in secrets

### Phase 2: Database (PN-02)
- [ ] Verify device_tokens table
- [ ] Add indexes
- [ ] Add token expiry tracking

### Phase 3: Service Layer (PN-03)
- [ ] Implement PushNotificationService
- [ ] Add FCM integration
- [ ] Handle token refresh
- [ ] Batch sending

### Phase 4: API Layer (PN-04)
- [ ] Device registration endpoints
- [ ] Test notification endpoint

### Phase 5: Integration (PN-05)
- [ ] Hook into notification dispatcher
- [ ] SMS arrival notifications
- [ ] Payment notifications
- [ ] Low balance alerts

### Phase 6: Frontend (PN-06)
- [ ] Service worker
- [ ] Permission request
- [ ] Message handling

### Phase 7: Settings UI (PN-07)
- [ ] Push preferences page
- [ ] Device management
- [ ] Test notification

---

## Architecture

```
User Action (SMS arrives, payment completes)
    ↓
NotificationDispatcher
    ↓
PushNotificationService.send_to_user()
    ↓
Query device_tokens for user
    ↓
Send to Firebase Cloud Messaging
    ↓
FCM delivers to user's devices
    ↓
Service Worker receives message
    ↓
Browser shows notification
```

---

## Database Schema

```sql
-- device_tokens (already exists, verify structure)
CREATE TABLE device_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    token TEXT NOT NULL UNIQUE,
    device_type VARCHAR(50),
    device_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_device_tokens_user_id ON device_tokens(user_id);
CREATE INDEX idx_device_tokens_token ON device_tokens(token);
CREATE INDEX idx_device_tokens_active ON device_tokens(active);
```

---

## API Endpoints

```python
POST   /api/push/register        # Register device token
DELETE /api/push/unregister      # Remove device token
POST   /api/push/test            # Send test notification
GET    /api/push/devices         # List user's devices
DELETE /api/push/devices/{id}    # Remove specific device
```

---

## Notification Format

```json
{
  "notification": {
    "title": "🔔 SMS Code Received",
    "body": "WhatsApp: 123456",
    "icon": "/static/icons/icon-192x192.png",
    "badge": "/static/icons/badge-72x72.png",
    "tag": "sms-verification",
    "requireInteraction": true,
    "actions": [
      {
        "action": "view",
        "title": "View Code"
      },
      {
        "action": "copy",
        "title": "Copy Code"
      }
    ]
  },
  "data": {
    "type": "sms_received",
    "verification_id": "12345",
    "sms_code": "123456",
    "url": "/verify"
  }
}
```

---

## Firebase Configuration

### 1. Create Project
```
1. Go to https://console.firebase.google.com
2. Click "Add project"
3. Name: "Namaskah SMS Platform"
4. Disable Google Analytics (optional)
5. Create project
```

### 2. Enable Cloud Messaging
```
1. Project Settings > Cloud Messaging
2. Enable Cloud Messaging API (v1)
3. Note: Legacy API will be deprecated
```

### 3. Generate Service Account
```
1. Project Settings > Service Accounts
2. Click "Generate new private key"
3. Save JSON file as firebase-service-account.json
4. Store in secrets as FIREBASE_SERVICE_ACCOUNT_JSON
```

### 4. Web Push Certificates
```
1. Project Settings > Cloud Messaging > Web Configuration
2. Generate key pair
3. Copy VAPID public key
4. Store as FCM_VAPID_KEY
```

---

## Service Worker

```javascript
// static/js/service-worker.js
self.addEventListener('push', function(event) {
  const data = event.data.json();
  const options = {
    body: data.notification.body,
    icon: data.notification.icon,
    badge: data.notification.badge,
    tag: data.notification.tag,
    requireInteraction: data.notification.requireInteraction,
    actions: data.notification.actions,
    data: data.data
  };

  event.waitUntil(
    self.registration.showNotification(data.notification.title, options)
  );
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();

  if (event.action === 'view') {
    clients.openWindow(event.notification.data.url);
  } else if (event.action === 'copy') {
    // Copy code to clipboard
    navigator.clipboard.writeText(event.notification.data.sms_code);
  } else {
    clients.openWindow('/dashboard');
  }
});
```

---

## Security Considerations

1. **Token Validation**: Verify FCM tokens before storing
2. **User Authorization**: Only send to user's own devices
3. **Rate Limiting**: Prevent notification spam
4. **Data Privacy**: Don't include sensitive data in notification body
5. **Token Expiry**: Clean up expired tokens regularly

---

## Testing Plan

1. **Unit Tests** (Target: 80%)
   - PushNotificationService message formatting
   - Token management
   - Error scenarios

2. **Integration Tests**
   - Device registration
   - Notification sending
   - Token refresh

3. **E2E Tests**
   - User grants permission
   - SMS arrives
   - User receives push notification
   - User clicks notification

4. **Manual Testing**
   - Test on Chrome, Firefox, Edge
   - Test on mobile browsers
   - Test notification actions
   - Test multiple devices

---

## Rollback Plan

If issues arise:
1. Remove `FCM_SERVER_KEY` from Render
2. Service will gracefully skip push notifications
3. Users revert to email/in-app notifications
4. No data loss (device tokens remain in DB)

---

## Cost Estimates

**Firebase Cloud Messaging Pricing:**
- First 10M messages/month: Free
- Additional messages: $0.50 per 1M

**Expected Costs:**
- 1,000 users × 10 notifications/day = 300K/month
- Well within free tier
- Estimated cost: $0/month initially
- At 10,000 users: ~$15-20/month

---

## Next Actions

**Waiting on**: Firebase project creation

Once Firebase is configured:
1. Create migration for device_tokens enhancements
2. Implement PushNotificationService
3. Create API endpoints
4. Hook into notification dispatcher
5. Build service worker
6. Create settings UI

**Estimated Time After Firebase Setup**: 8-10 hours of development
