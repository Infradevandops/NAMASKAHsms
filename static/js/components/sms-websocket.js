class SMSWebSocket {
    constructor(verificationId) {
        this.verificationId = verificationId;
        this.ws = null;
        this.callbacks = {
            onMessage: null,
            onConnect: null,
            onDisconnect: null
        };
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.useFallback = false;
        this.pingInterval = null;
    }

    onMessage(callback) {
        this.callbacks.onMessage = callback;
    }

    onConnect(callback) {
        this.callbacks.onConnect = callback;
    }

    onDisconnect(callback) {
        this.callbacks.onDisconnect = callback;
    }

    connect() {
        if (this.useFallback) return;

        const token = localStorage.getItem('access_token');
        if (!token) {
            console.error('No auth token for SMS WebSocket');
            this.enableFallback();
            return;
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/notifications`;

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log(`[SMS-WS] Connected for verification: ${this.verificationId}`);
                this.reconnectAttempts = 0;

                // Authenticate
                this.ws.send(JSON.stringify({ type: 'auth', token: token }));

                if (this.callbacks.onConnect) this.callbacks.onConnect();

                // Setup Ping to keep connection alive
                this.pingInterval = setInterval(() => {
                    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                        this.ws.send('ping');
                    }
                }, 20000);
            };

            this.ws.onmessage = (event) => {
                if (event.data === 'pong') return;

                try {
                    const message = JSON.parse(event.data);

                    // Route verification events
                    if (message.type === 'verification_event') {
                        // Ensure it's for our specific verification
                        if (message.data && message.data.verification_id === this.verificationId) {
                            if (this.callbacks.onMessage) {
                                this.callbacks.onMessage(message);
                            }
                        }
                    } else {
                        // Pass through other potential messages (like refunds)
                        if (this.callbacks.onMessage) {
                            this.callbacks.onMessage(message);
                        }
                    }
                } catch (e) {
                    console.error('[SMS-WS] Message parse error:', e);
                }
            };

            this.ws.onclose = () => {
                this.cleanup();
                if (this.callbacks.onDisconnect) this.callbacks.onDisconnect();
                this.attemptReconnect();
            };

            this.ws.onerror = (error) => {
                console.error('[SMS-WS] Error:', error);
            };

        } catch (e) {
            console.error('[SMS-WS] Failed to create connection:', e);
            this.enableFallback();
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.warn('[SMS-WS] Max reconnects reached. Falling back to HTTP polling.');
            this.enableFallback();
            return;
        }

        this.reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);
        console.log(`[SMS-WS] Reconnecting in ${delay}ms...`);

        setTimeout(() => this.connect(), delay);
    }

    enableFallback() {
        this.useFallback = true;
        if (this.callbacks.onDisconnect) {
            this.callbacks.onDisconnect(); // Signals UI to show polling status
        }
    }

    cleanup() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }

    close() {
        this.cleanup();
        if (this.ws) {
            this.ws.onclose = null; // Prevent reconnect loop
            this.ws.close();
            this.ws = null;
        }
    }
}
