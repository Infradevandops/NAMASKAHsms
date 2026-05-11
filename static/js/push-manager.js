/**
 * Push Notification Manager
 * Handles OneSignal integration and push notification management
 */

class PushManager {
    constructor() {
        this.isSupported = this.checkSupport();
        this.initialized = false;
    }

    /**
     * Check if push notifications are supported
     */
    checkSupport() {
        return 'Notification' in window &&
               'serviceWorker' in navigator &&
               'PushManager' in window;
    }

    /**
     * Get current permission status
     */
    getPermissionStatus() {
        if (!this.isSupported) return 'unsupported';
        return Notification.permission;
    }

    /**
     * Initialize OneSignal
     */
    async initialize() {
        if (this.initialized) return;
        if (!this.isSupported) {
            console.warn('[PushManager] Push notifications not supported');
            return;
        }

        try {
            // Check if OneSignal is loaded
            if (typeof OneSignal === 'undefined') {
                console.warn('[PushManager] OneSignal SDK not loaded');
                return;
            }

            await OneSignal.init({
                appId: window.ONESIGNAL_APP_ID || '',
                allowLocalhostAsSecureOrigin: true,
                notifyButton: {
                    enable: false // We use custom UI
                }
            });

            this.initialized = true;
            console.log('[PushManager] Initialized successfully');
        } catch (error) {
            console.error('[PushManager] Initialization failed:', error);
        }
    }

    /**
     * Subscribe to push notifications
     */
    async subscribe() {
        if (!this.isSupported) {
            throw new Error('Push notifications are not supported in your browser');
        }

        await this.initialize();

        try {
            // Request permission
            const permission = await Notification.requestPermission();

            if (permission !== 'granted') {
                throw new Error('Permission denied. Please enable notifications in your browser settings.');
            }

            // Subscribe with OneSignal
            if (typeof OneSignal !== 'undefined') {
                await OneSignal.setSubscription(true);
                const userId = await OneSignal.getUserId();
                console.log('[PushManager] Subscribed with ID:', userId);

                // Register device with backend
                await this.registerDevice(userId);
            }

            return { success: true, permission };
        } catch (error) {
            console.error('[PushManager] Subscription failed:', error);
            throw error;
        }
    }

    /**
     * Unsubscribe from push notifications
     */
    async unsubscribe() {
        try {
            if (typeof OneSignal !== 'undefined') {
                await OneSignal.setSubscription(false);
                console.log('[PushManager] Unsubscribed successfully');
            }

            // Unregister device from backend
            await this.unregisterDevice();

            return { success: true };
        } catch (error) {
            console.error('[PushManager] Unsubscription failed:', error);
            throw error;
        }
    }

    /**
     * Register device with backend
     */
    async registerDevice(playerId) {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) return;

            const response = await fetch('/api/push/devices', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    player_id: playerId,
                    platform: 'web',
                    device_type: this.getDeviceType(),
                    device_name: this.getDeviceName()
                })
            });

            if (!response.ok) {
                console.warn('[PushManager] Failed to register device with backend');
            }
        } catch (error) {
            console.error('[PushManager] Device registration failed:', error);
        }
    }

    /**
     * Unregister device from backend
     */
    async unregisterDevice() {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) return;

            if (typeof OneSignal !== 'undefined') {
                const userId = await OneSignal.getUserId();
                if (userId) {
                    await fetch(`/api/push/devices/${userId}`, {
                        method: 'DELETE',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });
                }
            }
        } catch (error) {
            console.error('[PushManager] Device unregistration failed:', error);
        }
    }

    /**
     * Send test notification
     */
    async sendTestNotification() {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) throw new Error('Not authenticated');

            const response = await fetch('/api/push/test', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to send test notification');
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('[PushManager] Test notification failed:', error);
            throw error;
        }
    }

    /**
     * Get device type
     */
    getDeviceType() {
        const ua = navigator.userAgent;
        if (/mobile/i.test(ua)) return 'Mobile';
        if (/tablet/i.test(ua)) return 'Tablet';
        return 'Desktop';
    }

    /**
     * Get device name
     */
    getDeviceName() {
        const ua = navigator.userAgent;
        let browser = 'Unknown';

        if (ua.includes('Chrome')) browser = 'Chrome';
        else if (ua.includes('Firefox')) browser = 'Firefox';
        else if (ua.includes('Safari')) browser = 'Safari';
        else if (ua.includes('Edge')) browser = 'Edge';

        return `${browser} on ${this.getDeviceType()}`;
    }

    /**
     * Check if user is subscribed
     */
    async isSubscribed() {
        if (!this.isSupported) return false;

        try {
            if (typeof OneSignal !== 'undefined') {
                await this.initialize();
                return await OneSignal.isPushNotificationsEnabled();
            }
            return false;
        } catch (error) {
            console.error('[PushManager] Subscription check failed:', error);
            return false;
        }
    }
}

// Create global instance
window.pushManager = new PushManager();

// Auto-initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.pushManager.initialize().catch(console.error);
    });
} else {
    window.pushManager.initialize().catch(console.error);
}

console.log('[PushManager] Module loaded');
