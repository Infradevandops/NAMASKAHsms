/**
 * Mobile Notifications Handler
 * Handles push notifications, service worker registration, and device token management
 */

class MobileNotificationHandler {
    constructor() {
        this.serviceWorkerRegistration = null;
        this.deviceToken = null;
        this.platform = this.detectPlatform();
        this.isSupported = this.checkSupport();
        this.init();
    }

    /**
     * Initialize mobile notification handler
     */
    async init() {
        if (!this.isSupported) {
            console.warn('Push notifications not supported on this device');
            return;
        }

        try {
            // Register service worker
            await this.registerServiceWorker();

            // Request notification permission
            await this.requestNotificationPermission();

            // Get or create device token
            await this.getOrCreateDeviceToken();

            console.log('Mobile notification handler initialized');
        } catch (error) {
            console.error('Failed to initialize mobile notifications:', error);
        }
    }

    /**
     * Detect platform (iOS or Android)
     */
    detectPlatform() {
        const ua = navigator.userAgent.toLowerCase();
        if (/iphone|ipad|ipod/.test(ua)) {
            return 'ios';
        } else if (/android/.test(ua)) {
            return 'android';
        }
        return 'web';
    }

    /**
     * Check if push notifications are supported
     */
    checkSupport() {
        return (
            'serviceWorker' in navigator &&
            'PushManager' in window &&
            'Notification' in window
        );
    }

    /**
     * Register service worker
     */
    async registerServiceWorker() {
        try {
            this.serviceWorkerRegistration = await navigator.serviceWorker.register(
                '/static/js/service-worker.js',
                { scope: '/' }
            );
            console.log('Service worker registered');
        } catch (error) {
            console.error('Service worker registration failed:', error);
        }
    }

    /**
     * Request notification permission
     */
    async requestNotificationPermission() {
        if (Notification.permission === 'granted') {
            return true;
        }

        if (Notification.permission !== 'denied') {
            try {
                const permission = await Notification.requestPermission();
                return permission === 'granted';
            } catch (error) {
                console.error('Failed to request notification permission:', error);
                return false;
            }
        }

        return false;
    }

    /**
     * Get or create device token
     */
    async getOrCreateDeviceToken() {
        try {
            if (!this.serviceWorkerRegistration) {
                console.warn('Service worker not registered');
                return;
            }

            // Check if already subscribed
            let subscription = await this.serviceWorkerRegistration.pushManager.getSubscription();

            if (!subscription) {
                // Create new subscription
                const vapidPublicKey = this.getVapidPublicKey();
                if (!vapidPublicKey) {
                    console.warn('VAPID public key not configured');
                    return;
                }

                subscription = await this.serviceWorkerRegistration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: this.urlBase64ToUint8Array(vapidPublicKey),
                });
            }

            // Extract device token from subscription
            this.deviceToken = this.extractDeviceToken(subscription);

            // Register device token with backend
            await this.registerDeviceToken();

            console.log('Device token obtained and registered');
        } catch (error) {
            console.error('Failed to get or create device token:', error);
        }
    }

    /**
     * Get VAPID public key from page meta tag
     */
    getVapidPublicKey() {
        const meta = document.querySelector('meta[name="vapid-public-key"]');
        return meta ? meta.getAttribute('content') : null;
    }

    /**
     * Convert VAPID public key from base64 to Uint8Array
     */
    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
        const base64 = (base64String + padding)
            .replace(/\-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }

        return outputArray;
    }

    /**
     * Extract device token from subscription
     */
    extractDeviceToken(subscription) {
        const endpoint = subscription.endpoint;
        const auth = subscription.getKey('auth');
        const p256dh = subscription.getKey('p256dh');

        // Create a unique token from subscription data
        const tokenData = {
            endpoint,
            auth: auth ? btoa(String.fromCharCode.apply(null, new Uint8Array(auth))) : null,
            p256dh: p256dh ? btoa(String.fromCharCode.apply(null, new Uint8Array(p256dh))) : null,
        };

        return btoa(JSON.stringify(tokenData));
    }

    /**
     * Register device token with backend
     */
    async registerDeviceToken() {
        try {
            const response = await fetch('/api/notifications/push/register-device', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    device_token: this.deviceToken,
                    platform: this.platform,
                    device_name: this.getDeviceName(),
                }),
            });

            if (!response.ok) {
                throw new Error(`Failed to register device token: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('Device token registered:', data);
        } catch (error) {
            console.error('Failed to register device token:', error);
        }
    }

    /**
     * Get device name
     */
    getDeviceName() {
        const ua = navigator.userAgent;
        if (/iPhone/.test(ua)) return 'iPhone';
        if (/iPad/.test(ua)) return 'iPad';
        if (/Android/.test(ua)) return 'Android Device';
        return 'Web Browser';
    }

    /**
     * Unregister device token
     */
    async unregisterDeviceToken() {
        try {
            if (!this.deviceToken) {
                console.warn('No device token to unregister');
                return;
            }

            const response = await fetch('/api/notifications/push/unregister-device', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    device_token: this.deviceToken,
                }),
            });

            if (!response.ok) {
                throw new Error(`Failed to unregister device token: ${response.statusText}`);
            }

            console.log('Device token unregistered');
        } catch (error) {
            console.error('Failed to unregister device token:', error);
        }
    }

    /**
     * Show local notification
     */
    showNotification(title, options = {}) {
        if (!this.isSupported || Notification.permission !== 'granted') {
            console.warn('Notifications not supported or permission not granted');
            return;
        }

        const defaultOptions = {
            icon: '/static/images/icon-192x192.png',
            badge: '/static/images/badge-72x72.png',
            tag: 'notification',
            requireInteraction: false,
            ...options,
        };

        if (this.serviceWorkerRegistration) {
            this.serviceWorkerRegistration.showNotification(title, defaultOptions);
        } else {
            new Notification(title, defaultOptions);
        }
    }

    /**
     * Send test push notification
     */
    async sendTestNotification() {
        try {
            const response = await fetch('/api/notifications/push/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error(`Failed to send test notification: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('Test notification sent:', data);
            return data;
        } catch (error) {
            console.error('Failed to send test notification:', error);
            throw error;
        }
    }

    /**
     * Get user's devices
     */
    async getUserDevices() {
        try {
            const response = await fetch('/api/notifications/push/devices', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error(`Failed to get devices: ${response.statusText}`);
            }

            const data = await response.json();
            return data.devices || [];
        } catch (error) {
            console.error('Failed to get user devices:', error);
            return [];
        }
    }

    /**
     * Delete device
     */
    async deleteDevice(deviceId) {
        try {
            const response = await fetch(`/api/notifications/push/devices/${deviceId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error(`Failed to delete device: ${response.statusText}`);
            }

            console.log('Device deleted');
            return true;
        } catch (error) {
            console.error('Failed to delete device:', error);
            return false;
        }
    }

    /**
     * Get push preferences
     */
    async getPushPreferences() {
        try {
            const response = await fetch('/api/notifications/push/preferences', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error(`Failed to get push preferences: ${response.statusText}`);
            }

            const data = await response.json();
            return data.preferences || [];
        } catch (error) {
            console.error('Failed to get push preferences:', error);
            return [];
        }
    }

    /**
     * Update push preference
     */
    async updatePushPreference(notificationType, enabled) {
        try {
            const response = await fetch(
                `/api/notifications/push/preferences/${notificationType}?enabled=${enabled}`,
                {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                }
            );

            if (!response.ok) {
                throw new Error(`Failed to update push preference: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('Push preference updated:', data);
            return data.preference;
        } catch (error) {
            console.error('Failed to update push preference:', error);
            throw error;
        }
    }
}

// Initialize mobile notification handler when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.mobileNotificationHandler = new MobileNotificationHandler();
    });
} else {
    window.mobileNotificationHandler = new MobileNotificationHandler();
}
