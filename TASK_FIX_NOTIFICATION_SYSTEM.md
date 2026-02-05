# TASK: Fix Broken Notification System

## Objective
Implement real-time WebSocket notifications so users get instant alerts when SMS codes arrive, with sound notifications.

---

## Current State
- ✅ Notifications created in database
- ✅ Auto-refund works
- ✅ SMS polling detects codes
- ❌ WebSocket is placeholder only
- ❌ 30-second delay (polling fallback)
- ❌ No real-time delivery

---

## Task Breakdown

### PHASE 1: Implement WebSocket Backend (HIGH PRIORITY)

#### Task 1.1: Create WebSocket Manager
**File**: `app/websocket/manager.py`

```python
from typing import Dict, Set
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for real-time notifications."""
    
    def __init__(self):
        # user_id -> Set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept and store WebSocket connection."""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected: user={user_id}, total={len(self.active_connections[user_id])}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove WebSocket connection."""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        logger.info(f"WebSocket disconnected: user={user_id}")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user's connections."""
        if user_id not in self.active_connections:
            logger.debug(f"No active connections for user {user_id}")
            return
        
        disconnected = set()
        
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to connection: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected
        for conn in disconnected:
            self.disconnect(conn, user_id)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected users."""
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)
    
    def get_user_connection_count(self, user_id: str) -> int:
        """Get number of active connections for user."""
        return len(self.active_connections.get(user_id, set()))

# Global instance
manager = ConnectionManager()
```

**Acceptance Criteria**:
- [ ] Can connect multiple WebSocket clients per user
- [ ] Can send messages to specific user
- [ ] Handles disconnections gracefully
- [ ] Cleans up stale connections

---

#### Task 1.2: Create WebSocket Endpoint
**File**: `app/api/websocket_endpoints.py`

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from app.websocket.manager import manager
from app.core.dependencies import get_current_user_id_from_token
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["WebSocket"])

@router.websocket("/ws/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    token: str = Query(..., description="JWT token for authentication")
):
    """WebSocket endpoint for real-time notifications."""
    
    # Authenticate user from token
    try:
        user_id = await get_current_user_id_from_token(token)
    except Exception as e:
        logger.error(f"WebSocket auth failed: {e}")
        await websocket.close(code=1008, reason="Authentication failed")
        return
    
    # Connect
    await manager.connect(websocket, user_id)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "WebSocket connected successfully",
            "user_id": user_id
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            
            # Handle ping/pong for keepalive
            if data == "ping":
                await websocket.send_text("pong")
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"WebSocket disconnected normally: {user_id}")
    except Exception as e:
        manager.disconnect(websocket, user_id)
        logger.error(f"WebSocket error: {e}")
```

**Acceptance Criteria**:
- [ ] Authenticates user via JWT token
- [ ] Maintains persistent connection
- [ ] Handles ping/pong keepalive
- [ ] Graceful disconnect handling

---

#### Task 1.3: Update NotificationDispatcher
**File**: `app/services/notification_dispatcher.py`

Replace placeholder with real implementation:

```python
from app.websocket.manager import manager

def _broadcast_notification(self, user_id: str, notification: Dict[str, Any]):
    """Broadcast notification via WebSocket."""
    try:
        # Send via WebSocket
        import asyncio
        asyncio.create_task(manager.send_personal_message(
            {
                "type": "notification",
                "data": notification
            },
            user_id
        ))
        logger.info(f"Notification broadcasted to user {user_id}")
    except Exception as e:
        logger.error(f"Failed to broadcast notification: {e}")
```

**Acceptance Criteria**:
- [ ] Sends notification to WebSocket immediately
- [ ] Doesn't block if WebSocket fails
- [ ] Logs success/failure

---

#### Task 1.4: Add WebSocket Router to Main
**File**: `main.py`

```python
from app.api.websocket_endpoints import router as websocket_router

# In create_app():
fastapi_app.include_router(websocket_router)
```

**Acceptance Criteria**:
- [ ] WebSocket endpoint accessible at `/ws/notifications`
- [ ] No import errors
- [ ] App starts successfully

---

### PHASE 2: Update Frontend WebSocket Client (MEDIUM PRIORITY)

#### Task 2.1: Fix WebSocket Connection
**File**: `static/js/notification-system.js`

Update `initializeWebSocket()` method:

```javascript
initializeWebSocket() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        console.warn('⚠️ No auth token, skipping WebSocket');
        return;
    }
    
    // Use wss:// for HTTPS, ws:// for HTTP
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/notifications?token=${token}`;
    
    try {
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            console.log('✅ WebSocket connected');
            this.reconnectAttempts = 0;
        };
        
        this.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'notification') {
                this.handleRealtimeNotification(data.data);
            }
        };
        
        this.websocket.onerror = (error) => {
            console.error('❌ WebSocket error:', error);
        };
        
        this.websocket.onclose = () => {
            console.log('🔌 WebSocket closed');
            this.attemptReconnect();
        };
        
        // Keepalive ping every 30 seconds
        this.startKeepalive();
        
    } catch (error) {
        console.error('Failed to create WebSocket:', error);
    }
}

handleRealtimeNotification(notification) {
    console.log('📨 Real-time notification received:', notification);
    
    // Update unread count
    this.unreadCount++;
    this.updateBellBadge();
    
    // Show toast
    this.showToast(notification);
    
    // Play sound
    this.playNotificationSound();
    
    // Add to dropdown list
    this.prependNotificationToList(notification);
}

startKeepalive() {
    this.keepaliveInterval = setInterval(() => {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send('ping');
        }
    }, 30000);
}

attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.warn('⚠️ Max reconnect attempts reached');
        return;
    }
    
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`🔄 Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
        this.initializeWebSocket();
    }, delay);
}
```

**Acceptance Criteria**:
- [ ] Connects to WebSocket on page load
- [ ] Handles real-time notifications
- [ ] Shows toast immediately
- [ ] Plays sound on notification
- [ ] Reconnects on disconnect
- [ ] Keepalive ping/pong

---

### PHASE 3: Add Helper Function for Token Auth (MEDIUM PRIORITY)

#### Task 3.1: Create Token Validator
**File**: `app/core/dependencies.py`

```python
import jwt
from fastapi import HTTPException, status
from app.core.config import get_settings

settings = get_settings()

async def get_current_user_id_from_token(token: str) -> str:
    """Extract user_id from JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return user_id
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
```

**Acceptance Criteria**:
- [ ] Validates JWT token
- [ ] Returns user_id
- [ ] Handles expired tokens
- [ ] Handles invalid tokens

---

### PHASE 4: Testing (HIGH PRIORITY)

#### Task 4.1: Manual Testing Checklist

**Test 1: WebSocket Connection**
- [ ] Login to dashboard
- [ ] Open browser DevTools → Network → WS
- [ ] Verify WebSocket connection established
- [ ] Check for "connected" message

**Test 2: Real-Time Notification**
- [ ] Start a verification
- [ ] Wait for SMS code
- [ ] Verify notification appears instantly (< 1 second)
- [ ] Verify sound plays
- [ ] Verify bell badge updates

**Test 3: Reconnection**
- [ ] Disconnect internet
- [ ] Wait 5 seconds
- [ ] Reconnect internet
- [ ] Verify WebSocket reconnects automatically

**Test 4: Multiple Tabs**
- [ ] Open dashboard in 2 tabs
- [ ] Trigger notification
- [ ] Verify both tabs receive notification

**Test 5: Auto-Refund Notification**
- [ ] Start verification
- [ ] Let it timeout
- [ ] Verify refund notification appears
- [ ] Verify balance updated
- [ ] Verify sound plays

---

### PHASE 5: Fallback & Error Handling (MEDIUM PRIORITY)

#### Task 5.1: Graceful Degradation

If WebSocket fails, ensure polling still works:

```javascript
initializeWebSocket() {
    // Try WebSocket first
    try {
        this.setupWebSocket();
    } catch (error) {
        console.warn('WebSocket failed, using polling fallback');
        this.usePollingFallback = true;
    }
}
```

**Acceptance Criteria**:
- [ ] Falls back to polling if WebSocket fails
- [ ] User still gets notifications (delayed)
- [ ] No errors in console

---

## Success Criteria

### Must Have (P0):
- [ ] WebSocket connects successfully
- [ ] Notifications arrive in < 1 second
- [ ] Sound plays on SMS arrival
- [ ] Auto-refund notifications work
- [ ] No console errors

### Should Have (P1):
- [ ] Reconnection on disconnect
- [ ] Multiple tab support
- [ ] Keepalive ping/pong
- [ ] Graceful fallback to polling

### Nice to Have (P2):
- [ ] Desktop notifications API
- [ ] Custom sound preferences
- [ ] Notification history sync

---

## Estimated Time

- **Phase 1**: 4-6 hours (Backend WebSocket)
- **Phase 2**: 2-3 hours (Frontend updates)
- **Phase 3**: 1 hour (Token auth)
- **Phase 4**: 2-3 hours (Testing)
- **Phase 5**: 1-2 hours (Fallback)

**Total**: 10-15 hours

---

## Dependencies

1. ✅ Auth system working (just fixed)
2. ✅ Notification database schema
3. ✅ SMS polling service
4. ✅ Auto-refund service
5. ⚠️ Need to install: `python-multipart` (if not already)

---

## Risks

1. **WebSocket Proxy Issues**: Render/Nginx may need configuration
2. **Browser Compatibility**: Some browsers block WebSocket
3. **Token Expiry**: Need to handle token refresh
4. **Connection Limits**: May need to limit connections per user

---

## Rollback Plan

If WebSocket implementation fails:
1. Keep current polling system (works, just slow)
2. Reduce polling interval to 15 seconds
3. Add visual indicator "Checking for updates..."

---

## Files to Create/Modify

### Create:
- [ ] `app/websocket/__init__.py`
- [ ] `app/websocket/manager.py`
- [ ] `app/api/websocket_endpoints.py`

### Modify:
- [ ] `app/services/notification_dispatcher.py`
- [ ] `static/js/notification-system.js`
- [ ] `app/core/dependencies.py`
- [ ] `main.py`

### Test:
- [ ] Manual testing in browser
- [ ] Multiple tab testing
- [ ] Reconnection testing
- [ ] Load testing (optional)

---

## Next Steps

1. **Immediate**: Deploy current auth fix
2. **Today**: Implement Phase 1 (WebSocket backend)
3. **Tomorrow**: Implement Phase 2 (Frontend)
4. **Day 3**: Testing and refinement

---

## Notes

- WebSocket is the RIGHT solution for real-time notifications
- Current polling works but is suboptimal
- This will significantly improve UX
- Sound already works, just needs instant delivery
- Auto-refund is solid, just needs instant notification
