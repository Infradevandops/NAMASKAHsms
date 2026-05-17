/**
 * OneSignal Push Notification Manager
 * Handles push notification subscription and management
 */

class OneSignalManager {
    constructor() {
        this.appId = null;
        this.initialized = false;
        this.subscribed = false;
    }

    /**
     * Initialize OneSignal SDK
     */
    async init() {
        try {
            // Get OneSignal config from backend
            const response = await fetch('/api/onesignal/config', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (!response.ok) {
                console.warn('OneSignal config not available');
                return false;
            }

            const config = await response.json();

            if (!config.enabled || !config.app_id) {
                console.warn('OneSignal not configured');
                return false;
            }

            this.appId = config.app_id;

            // Initialize OneSignal
            window.OneSignal = window.OneSignal || [];
            OneSignal.push(() => {
                OneSignal.init({
                    appId: this.appId,
                    notifyButton: {
                        enable: false // We'll use custom UI
                    },
                    allowLocalhostAsSecureOrigin: true
                });

                // Check if already subscribed
                OneSignal.isPushNotificationsEnabled((isEnabled) => {
                    this.subscribed = isEnabled;
                    console.log('OneSignal subscription status:', isEnabled);
                });
            });

            this.initialized = true;
            return true;

        } catch (error) {
            console.error('Failed to initialize OneSignal:', error);
            return false;
        }
    }

    /**
     * Request push notification permission
     */
    async requestPermission() {
        if (!this.initialized) {
            const initialized = await this.init();
            if (!initialized) {
                throw new Error('OneSignal not initialized');
            }
        }

        return new Promise((resolve, reject) => {
            OneSignal.push(() => {
                OneSignal.showNativePrompt();

                OneSignal.on('subscriptionChange', async (isSubscribed) => {
                    if (isSubscribed) {
                        // Get player ID and register with backend
                        const playerId = await this.getPlayerId();
                        if (playerId) {
                            await this.registerDevice(playerId);
                            this.subscribed = true;
                            resolve(true);
                        } else {
                            reject(new Error('Failed to get player ID'));
                        }
                    } else {
                        resolve(false);
                    }
                });
            });
        });
    }

    /**
     * Get OneSignal player ID
     */
    async getPlayerId() {
        return new Promise((resolve) => {
            OneSignal.push(() => {
                OneSignal.getUserId((playerId) => {
                    resolve(playerId);
                });
            });
        });
    }

    /**
     * Register device with backend
     */
    async registerDevice(playerId) {
        try {
            const response = await fetch('/api/onesignal/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify({
                    player_id: playerId,
                    device_type: 'web'
                })
            });

            if (!response.ok) {
                throw new Error('Failed to register device');
            }

            const data = await response.json();
            console.log('Device registered:', data);

            // Set user tag for targeting
            OneSignal.push(() => {
                OneSignal.sendTag('user_id', localStorage.getItem('user_id'));
            });

            return data;

        } catch (error) {
            console.error('Failed to register device:', error);
            throw error;
        }
    }

    /**
     * Unsubscribe from push notifications
     */
    async unsubscribe() {
        if (!this.initialized) {
            return false;
        }

        return new Promise((resolve) => {
            OneSignal.push(async () => {
                const playerId = await this.getPlayerId();
                if (playerId) {
                    // Unregister from backend
                    await fetch('/api/onesignal/unregister', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                        },
                        body: JSON.stringify({
                            player_id: playerId
                        })
                    });
                }

                OneSignal.setSubscription(false);
                this.subscribed = false;
                resolve(true);
            });
        });
    }

    /**
     * Send test notification
     */
    async sendTestNotification() {
        try {
            const response = await fetch('/api/onesignal/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify({
                    title: 'Test Notification',
                    message: 'This is a test notification from Vrenum'
                })
            });

            if (!response.ok) {
                throw new Error('Failed to send test notification');
            }

            return await response.json();

        } catch (error) {
            console.error('Failed to send test notification:', error);
            throw error;
        }
    }

    /**
     * Check if notifications are supported
     */
    isSupported() {
        return 'Notification' in window && 'serviceWorker' in navigator;
    }

    /**
     * Get current permission status
     */
    getPermissionStatus() {
        if (!this.isSupported()) {
            return 'unsupported';
        }
        return Notification.permission;
    }
}

// Create global instance
window.oneSignalManager = new OneSignalManager();

// Auto-initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    if (localStorage.getItem('access_token')) {
        window.oneSignalManager.init();
    }
});
