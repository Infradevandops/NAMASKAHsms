/**
 * WebSocket Client with Auto-Reconnection and Polling Fallback
 */

class ReliableWebSocket {
    constructor(url, options = {}) {
        this.url = url;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 10;
        this.reconnectDelay = options.reconnectDelay || 1000;
        this.maxReconnectDelay = options.maxReconnectDelay || 30000;
        this.heartbeatInterval = options.heartbeatInterval || 30000;
        this.heartbeatTimer = null;
        this.reconnectTimer = null;
        this.messageHandlers = [];
        this.onConnectHandlers = [];
        this.onDisconnectHandlers = [];
        this.isIntentionallyClosed = false;
        this.useFallback = false;
        this.fallbackPollInterval = options.fallbackPollInterval || 5000;
        this.fallbackTimer = null;
    }

    connect() {
        if (this.ws?.readyState === WebSocket.OPEN) return;

        try {
            this.ws = new WebSocket(this.url);
            
            this.ws.onopen = () => {
                console.log('✅ WebSocket connected');
                this.reconnectAttempts = 0;
                this.useFallback = false;
                this.stopFallbackPolling();
                this.startHeartbeat();
                this.onConnectHandlers.forEach(handler => handler());
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    
                    // Ignore heartbeat responses
                    if (data.type === 'pong') return;
                    
                    this.messageHandlers.forEach(handler => handler(data));
                } catch (e) {
                    console.error('WebSocket message parse error:', e);
                }
            };

            this.ws.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
            };

            this.ws.onclose = (event) => {
                console.log('🔌 WebSocket closed:', event.code, event.reason);
                this.stopHeartbeat();
                this.onDisconnectHandlers.forEach(handler => handler());

                if (!this.isIntentionallyClosed) {
                    this.attemptReconnect();
                }
            };
        } catch (error) {
            console.error('WebSocket connection failed:', error);
            this.attemptReconnect();
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.warn('⚠️ Max reconnection attempts reached. Switching to polling fallback.');
            this.useFallback = true;
            this.startFallbackPolling();
            return;
        }

        const delay = Math.min(
            this.reconnectDelay * Math.pow(2, this.reconnectAttempts),
            this.maxReconnectDelay
        );

        console.log(`🔄 Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);

        this.reconnectTimer = setTimeout(() => {
            this.reconnectAttempts++;
            this.connect();
        }, delay);
    }

    startHeartbeat() {
        this.stopHeartbeat();
        this.heartbeatTimer = setInterval(() => {
            if (this.ws?.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({ type: 'ping' }));
            }
        }, this.heartbeatInterval);
    }

    stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    startFallbackPolling() {
        if (this.fallbackTimer) return;
        
        console.log('📡 Starting polling fallback');
        this.fallbackTimer = setInterval(() => {
            this.pollForUpdates();
        }, this.fallbackPollInterval);
        
        // Poll immediately
        this.pollForUpdates();
    }

    stopFallbackPolling() {
        if (this.fallbackTimer) {
            clearInterval(this.fallbackTimer);
            this.fallbackTimer = null;
            console.log('⏹️ Stopped polling fallback');
        }
    }

    async pollForUpdates() {
        // Override this method in subclasses
        console.log('Polling for updates...');
    }

    send(data) {
        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket not connected. Message not sent:', data);
        }
    }

    onMessage(handler) {
        this.messageHandlers.push(handler);
    }

    onConnect(handler) {
        this.onConnectHandlers.push(handler);
    }

    onDisconnect(handler) {
        this.onDisconnectHandlers.push(handler);
    }

    close() {
        this.isIntentionallyClosed = true;
        this.stopHeartbeat();
        this.stopFallbackPolling();
        
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    isConnected() {
        return this.ws?.readyState === WebSocket.OPEN;
    }

    getState() {
        if (!this.ws) return 'CLOSED';
        const states = ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED'];
        return states[this.ws.readyState];
    }
}

// Notification WebSocket
class NotificationWebSocket extends ReliableWebSocket {
    constructor() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${protocol}//${window.location.host}/ws/notifications`;
        super(url, {
            maxReconnectAttempts: 10,
            reconnectDelay: 1000,
            maxReconnectDelay: 30000,
            heartbeatInterval: 30000,
            fallbackPollInterval: 10000
        });
    }

    async pollForUpdates() {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) return;

            const res = await fetch('/api/notifications/unread', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (res.ok) {
                const data = await res.json();
                if (data.notifications?.length > 0) {
                    this.messageHandlers.forEach(handler => {
                        handler({ type: 'notification_update', data: data.notifications });
                    });
                }
            }
        } catch (e) {
            console.error('Polling error:', e);
        }
    }
}

// SMS Status WebSocket
class SMSWebSocket extends ReliableWebSocket {
    constructor(verificationId) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${protocol}//${window.location.host}/ws/sms/${verificationId}`;
        super(url, {
            maxReconnectAttempts: 20,
            reconnectDelay: 2000,
            maxReconnectDelay: 10000,
            heartbeatInterval: 15000,
            fallbackPollInterval: 3000
        });
        this.verificationId = verificationId;
    }

    async pollForUpdates() {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) return;

            const res = await fetch(`/api/verify/status/${this.verificationId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (res.ok) {
                const data = await res.json();
                this.messageHandlers.forEach(handler => {
                    handler({ type: 'sms_update', data });
                });
            }
        } catch (e) {
            console.error('SMS polling error:', e);
        }
    }
}

// Export for use in other scripts
window.ReliableWebSocket = ReliableWebSocket;
window.NotificationWebSocket = NotificationWebSocket;
window.SMSWebSocket = SMSWebSocket;
