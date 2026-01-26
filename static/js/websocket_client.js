/**
 * WebSocket Client for Real-time Notifications
 * Handles WebSocket connections, reconnection, and message handling
 */

class WebSocketClient {
    constructor(userId, options = {}) {
        this.userId = userId;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
        this.reconnectDelay = options.reconnectDelay || 1000;
        this.maxReconnectDelay = options.maxReconnectDelay || 30000;
        this.heartbeatInterval = options.heartbeatInterval || 30000;
        this.heartbeatTimer = null;
        this.messageHandlers = {};
        this.isManuallyDisconnected = false;

        // Bind methods
        this.connect = this.connect.bind(this);
        this.disconnect = this.disconnect.bind(this);
        this.send = this.send.bind(this);
        this.subscribe = this.subscribe.bind(this);
        this.unsubscribe = this.unsubscribe.bind(this);

        // Initialize
        this.connect();
    }

    connect() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            console.log('WebSocket already connected');
            return;
        }

        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const url = `${protocol}//${window.location.host}/ws/notifications/${this.userId}`;

            console.log(`Connecting to WebSocket: ${url}`);
            this.ws = new WebSocket(url);

            this.ws.onopen = () => this.onOpen();
            this.ws.onmessage = (event) => this.onMessage(event);
            this.ws.onerror = (error) => this.onError(error);
            this.ws.onclose = () => this.onClose();
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            this.attemptReconnect();
        }
    }

    onOpen() {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.isManuallyDisconnected = false;
        this.updateConnectionStatus(true);
        this.startHeartbeat();

        // Emit connected event
        this.emit('connected');

        // Subscribe to default channels
        this.subscribe('notifications');
        this.subscribe('activities');
        this.subscribe('payments');
    }

    onMessage(event) {
        try {
            const message = JSON.parse(event.data);
            console.log('WebSocket message received:', message);

            // Handle different message types
            const messageType = message.type;

            if (messageType === 'pong') {
                console.log('Heartbeat pong received');
                return;
            }

            if (messageType === 'subscribed') {
                console.log(`Subscribed to channel: ${message.channel}`);
                return;
            }

            if (messageType === 'unsubscribed') {
                console.log(`Unsubscribed from channel: ${message.channel}`);
                return;
            }

            // Call registered handlers
            if (this.messageHandlers[messageType]) {
                this.messageHandlers[messageType].forEach((handler) => {
                    try {
                        handler(message);
                    } catch (error) {
                        console.error(`Error in message handler for ${messageType}:`, error);
                    }
                });
            }

            // Emit generic message event
            this.emit('message', message);
        } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
        }
    }

    onError(error) {
        console.error('WebSocket error:', error);
        this.emit('error', error);
    }

    onClose() {
        console.log('WebSocket disconnected');
        this.stopHeartbeat();
        this.updateConnectionStatus(false);
        this.emit('disconnected');

        if (!this.isManuallyDisconnected) {
            this.attemptReconnect();
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('Max reconnection attempts reached, falling back to polling');
            this.emit('fallback_to_polling');
            return;
        }

        this.reconnectAttempts++;
        const delay = Math.min(
            this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
            this.maxReconnectDelay
        );

        console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        setTimeout(() => this.connect(), delay);
    }

    startHeartbeat() {
        this.stopHeartbeat();
        this.heartbeatTimer = setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.send({ type: 'ping' });
            }
        }, this.heartbeatInterval);
    }

    stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    send(message) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.warn('WebSocket not connected, cannot send message');
            return false;
        }

        try {
            this.ws.send(JSON.stringify(message));
            return true;
        } catch (error) {
            console.error('Failed to send WebSocket message:', error);
            return false;
        }
    }

    subscribe(channel) {
        return this.send({
            type: 'subscribe',
            channel: channel,
        });
    }

    unsubscribe(channel) {
        return this.send({
            type: 'unsubscribe',
            channel: channel,
        });
    }

    disconnect() {
        this.isManuallyDisconnected = true;
        this.stopHeartbeat();

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        this.updateConnectionStatus(false);
    }

    on(messageType, handler) {
        if (!this.messageHandlers[messageType]) {
            this.messageHandlers[messageType] = [];
        }
        this.messageHandlers[messageType].push(handler);
    }

    off(messageType, handler) {
        if (this.messageHandlers[messageType]) {
            this.messageHandlers[messageType] = this.messageHandlers[messageType].filter(
                (h) => h !== handler
            );
        }
    }

    emit(eventType, data) {
        const event = new CustomEvent(`websocket:${eventType}`, { detail: data });
        window.dispatchEvent(event);
    }

    updateConnectionStatus(connected) {
        const indicator = document.getElementById('websocket-status');
        if (indicator) {
            indicator.className = connected ? 'connected' : 'disconnected';
            indicator.title = connected ? 'Connected' : 'Disconnected';
            indicator.textContent = connected ? '●' : '○';
        }
    }

    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }

    getStats() {
        return {
            connected: this.isConnected(),
            reconnectAttempts: this.reconnectAttempts,
            maxReconnectAttempts: this.maxReconnectAttempts,
        };
    }
}

// Global WebSocket client instance
let wsClient = null;

// Initialize WebSocket client when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const userId = document.body.dataset.userId || window.userId;
    if (userId) {
        wsClient = new WebSocketClient(userId);

        // Listen for notification messages
        wsClient.on('notification', (message) => {
            console.log('Notification received:', message);
            if (window.toast) {
                window.toast.show(message.title, 'info');
            }
        });

        // Listen for activity messages
        wsClient.on('activity', (message) => {
            console.log('Activity received:', message);
        });

        // Listen for payment messages
        wsClient.on('payment', (message) => {
            console.log('Payment event received:', message);
            if (window.toast) {
                window.toast.show(`Payment: ${message.event_type}`, 'info');
            }
        });

        // Listen for verification messages
        wsClient.on('verification', (message) => {
            console.log('Verification event received:', message);
            if (window.toast) {
                window.toast.show(`Verification: ${message.event_type}`, 'info');
            }
        });

        // Listen for fallback to polling
        window.addEventListener('websocket:fallback_to_polling', () => {
            console.log('Falling back to HTTP polling');
            if (window.startPolling) {
                window.startPolling();
            }
        });
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebSocketClient;
}
