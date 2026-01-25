# WebSocket Implementation Roadmap

**Date**: January 25, 2026  
**Phase**: Phase 3 - Week 1  
**Duration**: 1 week  
**Priority**: HIGH  
**Impact**: Transforms notifications from 30s polling to < 100ms real-time

---

## 🎯 Objective

Replace HTTP polling-based notifications with WebSocket for instant, real-time updates with 95% reduction in server load.

---

## 📊 Current vs Target

| Metric | Current (Polling) | Target (WebSocket) | Improvement |
|--------|-------------------|-------------------|-------------|
| Notification Latency | 30 seconds | < 100ms | 300x faster |
| Server Requests/min | 2,000 (1k users) | 0 (1k users) | 100% reduction |
| Bandwidth Usage | High | Low | 95% reduction |
| Scalability | Limited | Unlimited | Infinite |
| User Experience | Delayed | Instant | Transformational |

---

## 🏗️ Architecture

### Backend Stack
```
FastAPI + WebSocket
├─ Connection Manager (track active connections)
├─ Event Broadcaster (send events to connected users)
├─ Message Queue (Redis for scaling)
└─ Fallback (HTTP polling as backup)
```

### Frontend Stack
```
JavaScript WebSocket Client
├─ Connection Management
├─ Reconnection Logic
├─ Message Handling
└─ Fallback to Polling
```

---

## 📋 Implementation Tasks

### Task 1: Backend WebSocket Server (2 days)

**Components**:
1. WebSocket endpoint: `/ws/notifications/{user_id}`
2. Connection manager class
3. Event broadcaster
4. Message queue integration (Redis)
5. Connection lifecycle management

**Code Structure**:
```python
# app/websocket/manager.py
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, user_id: str, websocket: WebSocket)
    async def disconnect(self, user_id: str)
    async def broadcast(self, user_id: str, message: dict)
    async def broadcast_all(self, message: dict)

# app/api/websocket_endpoints.py
@app.websocket("/ws/notifications/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages
    except WebSocketDisconnect:
        manager.disconnect(user_id)
```

**Deliverables**:
- ✅ WebSocket endpoint
- ✅ Connection manager
- ✅ Event broadcaster
- ✅ Error handling
- ✅ Reconnection logic

---

### Task 2: Frontend WebSocket Client (1.5 days)

**Components**:
1. WebSocket connection manager
2. Message handlers
3. Reconnection logic
4. Fallback to polling
5. UI integration

**Code Structure**:
```javascript
// static/js/websocket-client.js
class WebSocketClient {
    constructor(userId) {
        this.userId = userId;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }
    
    connect() {
        this.ws = new WebSocket(`ws://localhost:9527/ws/notifications/${this.userId}`);
        this.ws.onmessage = (event) => this.handleMessage(event);
        this.ws.onerror = (error) => this.handleError(error);
        this.ws.onclose = () => this.handleClose();
    }
    
    handleMessage(event) {
        const notification = JSON.parse(event.data);
        window.toast.success(notification.message);
        window.soundManager.play(notification.type);
    }
    
    reconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            setTimeout(() => this.connect(), 1000 * Math.pow(2, this.reconnectAttempts));
            this.reconnectAttempts++;
        } else {
            // Fallback to polling
            startPolling();
        }
    }
}
```

**Deliverables**:
- ✅ WebSocket client
- ✅ Message handlers
- ✅ Reconnection logic
- ✅ Fallback mechanism
- ✅ Error handling

---

### Task 3: Event Broadcasting (1.5 days)

**Components**:
1. Update notification dispatcher to use WebSocket
2. Broadcast events to connected users
3. Queue events for offline users
4. Handle multiple event types

**Integration Points**:
```python
# Update notification_dispatcher.py
class NotificationDispatcher:
    def __init__(self, db, websocket_manager):
        self.db = db
        self.ws_manager = websocket_manager
    
    async def on_sms_received(self, user_id: str, data: dict):
        # Create notification in DB
        notification = Notification(...)
        self.db.add(notification)
        
        # Broadcast via WebSocket
        await self.ws_manager.broadcast(user_id, {
            'type': 'sms_received',
            'message': 'SMS code received!',
            'data': data
        })
```

**Deliverables**:
- ✅ WebSocket integration
- ✅ Event broadcasting
- ✅ Queue management
- ✅ Offline handling

---

### Task 4: Testing & Optimization (1.5 days)

**Testing**:
1. Unit tests for connection manager
2. Integration tests for event broadcasting
3. Load tests (1000+ concurrent connections)
4. Failover tests
5. Reconnection tests

**Optimization**:
1. Connection pooling
2. Message compression
3. Memory management
4. CPU optimization
5. Bandwidth optimization

**Deliverables**:
- ✅ Test suite
- ✅ Load test results
- ✅ Performance metrics
- ✅ Optimization report

---

## 🔧 Technical Details

### WebSocket Message Format

```json
{
    "type": "notification",
    "event": "sms_received",
    "timestamp": "2026-01-25T10:30:00Z",
    "data": {
        "verification_id": "ver_123",
        "phone_number": "+1 (479) 502-2832",
        "code": "123456"
    }
}
```

### Event Types

```
verification.created
verification.completed
verification.failed
sms.received
voice.received
credit.deducted
refund.issued
balance.low
```

### Connection Lifecycle

```
1. User connects → WebSocket endpoint
2. Manager stores connection
3. Events broadcast to user
4. User disconnects → Manager removes connection
5. If offline → Queue events in Redis
6. User reconnects → Deliver queued events
```

---

## 📈 Performance Targets

| Metric | Target | Current | Improvement |
|--------|--------|---------|-------------|
| Latency | < 100ms | 30s | 300x |
| Connections/server | 10,000 | N/A | Scalable |
| Memory/connection | < 1KB | N/A | Efficient |
| CPU usage | < 50% | 80% | 37% reduction |
| Bandwidth | 1KB/event | 50KB/poll | 98% reduction |

---

## 🚀 Deployment Strategy

### Phase 1: Development (Days 1-3)
- Implement backend WebSocket
- Implement frontend client
- Basic testing

### Phase 2: Testing (Days 4-5)
- Unit tests
- Integration tests
- Load tests

### Phase 3: Deployment (Days 6-7)
- Blue-green deployment
- Gradual rollout (10% → 50% → 100%)
- Monitoring

---

## 🔄 Fallback Strategy

If WebSocket fails:
1. Automatic fallback to HTTP polling
2. User notified (optional)
3. Retry WebSocket connection
4. Exponential backoff (1s, 2s, 4s, 8s, 16s)
5. Max 5 retry attempts

---

## 📊 Success Metrics

### Performance
- ✅ Notification latency < 100ms
- ✅ 10,000+ concurrent connections
- ✅ 99.9% uptime
- ✅ < 50% CPU usage

### User Experience
- ✅ Instant notifications
- ✅ No polling delays
- ✅ Seamless reconnection
- ✅ Offline message queuing

### Business
- ✅ 95% reduction in server load
- ✅ 70% reduction in bandwidth
- ✅ Better scalability
- ✅ Lower infrastructure costs

---

## 🛠️ Tools & Libraries

### Backend
- FastAPI (already using)
- python-socketio (optional, for Socket.IO)
- Redis (for message queue)
- asyncio (for async handling)

### Frontend
- Native WebSocket API (no dependencies)
- Reconnection logic (custom)
- Message handling (custom)

---

## 📝 Code Checklist

- [ ] Connection manager class
- [ ] WebSocket endpoint
- [ ] Event broadcaster
- [ ] Frontend WebSocket client
- [ ] Reconnection logic
- [ ] Fallback to polling
- [ ] Message queue (Redis)
- [ ] Error handling
- [ ] Unit tests
- [ ] Integration tests
- [ ] Load tests
- [ ] Documentation

---

## 🎯 Milestones

| Milestone | Date | Status |
|-----------|------|--------|
| Backend implementation | Day 2 | ⏳ |
| Frontend implementation | Day 3 | ⏳ |
| Testing complete | Day 5 | ⏳ |
| Load testing | Day 6 | ⏳ |
| Production deployment | Day 7 | ⏳ |

---

## 📞 Questions & Decisions

1. **Socket.IO vs Native WebSocket?**
   - Decision: Native WebSocket (simpler, no dependencies)

2. **Message queue (Redis)?**
   - Decision: Yes, for scaling and offline message queuing

3. **Fallback strategy?**
   - Decision: Automatic fallback to polling after 5 retry attempts

4. **Connection timeout?**
   - Decision: 30 minutes (configurable)

5. **Max concurrent connections?**
   - Decision: 10,000 per server (configurable)

---

## 🔗 Related Documents

- PHASE3_ROADMAP.md - Overall Phase 3 plan
- PHASE1_PHASE2_COMPLETE_GUIDE.md - Current implementation
- docs/API_GUIDE.md - API documentation

---

**Status**: READY FOR IMPLEMENTATION ✅  
**Start Date**: February 1, 2026  
**Duration**: 1 week  
**Team**: 2 backend devs, 1 frontend dev

