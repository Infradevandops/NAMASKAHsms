/**
 * Push Notification Manager
 * Handles Firebase Cloud Messaging integration on the client side
 */

class PushNotificationManager {
  constructor() {
    this.vapidKey = null;
    this.registration = null;
    this.isSupported = 'serviceWorker' in navigator && 'PushManager' in window;
    this.isInitialized = false;
  }

  /**
   * Initialize push notifications
   */
  async initialize() {
    if (!this.isSupported) {
      console.warn('Push notifications not supported in this browser');
      return false;
    }

    try {
      // Get VAPID key from server
      const config = await this.getConfig();
      if (!config.enabled) {
        console.warn('Push notifications not configured on server');
        return false;
      }

      this.vapidKey = config.vapid_key;

      // Register service worker
      this.registration = await navigator.serviceWorker.register(
        '/static/js/push-service-worker.js',
        { scope: '/' }
      );

      console.log('Service Worker registered:', this.registration);

      // Wait for service worker to be ready
      await navigator.serviceWorker.ready;

      this.isInitialized = true;
      return true;
    } catch (error) {
      console.error('Failed to initialize push notifications:', error);
      return false;
    }
  }

  /**
   * Get push notification config from server
   */
  async getConfig() {
    try {
      const response = await fetch('/api/push/config');
      if (!response.ok) {
        throw new Error('Failed to get push config');
      }
      return await response.json();
    } catch (error) {
      console.error('Failed to get push config:', error);
      return { enabled: false };
    }
  }

  /**
   * Request notification permission
   */
  async requestPermission() {
    if (!this.isSupported) {
      return 'denied';
    }

    const permission = await Notification.requestPermission();
    console.log('Notification permission:', permission);
    return permission;
  }

  /**
   * Check current permission status
   */
  getPermissionStatus() {
    if (!this.isSupported) {
      return 'denied';
    }
    return Notification.permission;
  }

  /**
   * Subscribe to push notifications
   */
  async subscribe() {
    if (!this.isInitialized) {
      const initialized = await this.initialize();
      if (!initialized) {
        throw new Error('Failed to initialize push notifications');
      }
    }

    // Check permission
    const permission = await this.requestPermission();
    if (permission !== 'granted') {
      throw new Error('Notification permission denied');
    }

    try {
      // Subscribe to push
      const subscription = await this.registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: this.urlBase64ToUint8Array(this.vapidKey)
      });

      console.log('Push subscription:', subscription);

      // Get device info
      const deviceInfo = this.getDeviceInfo();

      // Register with server
      const token = JSON.stringify(subscription);
      await this.registerDevice(token, deviceInfo);

      return subscription;
    } catch (error) {
      console.error('Failed to subscribe to push:', error);
      throw error;
    }
  }

  /**
   * Unsubscribe from push notifications
   */
  async unsubscribe() {
    if (!this.registration) {
      return false;
    }

    try {
      const subscription = await this.registration.pushManager.getSubscription();
      if (subscription) {
        const token = JSON.stringify(subscription);

        // Unregister from server
        await this.unregisterDevice(token);

        // Unsubscribe from push
        await subscription.unsubscribe();
        console.log('Unsubscribed from push notifications');
        return true;
      }
      return false;
    } catch (error) {
      console.error('Failed to unsubscribe:', error);
      return false;
    }
  }

  /**
   * Get current subscription
   */
  async getSubscription() {
    if (!this.registration) {
      return null;
    }

    try {
      return await this.registration.pushManager.getSubscription();
    } catch (error) {
      console.error('Failed to get subscription:', error);
      return null;
    }
  }

  /**
   * Register device with server
   */
  async registerDevice(token, deviceInfo) {
    const response = await fetch('/api/push/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({
        token: token,
        platform: 'web',
        device_type: deviceInfo.browser,
        device_name: deviceInfo.name
      })
    });

    if (!response.ok) {
      throw new Error('Failed to register device');
    }

    return await response.json();
  }

  /**
   * Unregister device from server
   */
  async unregisterDevice(token) {
    const response = await fetch(`/api/push/unregister?token=${encodeURIComponent(token)}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });

    if (!response.ok) {
      throw new Error('Failed to unregister device');
    }

    return await response.json();
  }

  /**
   * Send test notification
   */
  async sendTestNotification() {
    const response = await fetch('/api/push/test', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });

    if (!response.ok) {
      throw new Error('Failed to send test notification');
    }

    return await response.json();
  }

  /**
   * Get device info
   */
  getDeviceInfo() {
    const ua = navigator.userAgent;
    let browser = 'Unknown';

    if (ua.includes('Firefox')) {
      browser = 'Firefox';
    } else if (ua.includes('Chrome')) {
      browser = 'Chrome';
    } else if (ua.includes('Safari')) {
      browser = 'Safari';
    } else if (ua.includes('Edge')) {
      browser = 'Edge';
    }

    return {
      browser: browser,
      name: `${browser} on ${navigator.platform}`,
      userAgent: ua
    };
  }

  /**
   * Convert VAPID key to Uint8Array
   */
  urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
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
   * Handle messages from service worker
   */
  setupMessageListener() {
    if (!navigator.serviceWorker) {
      return;
    }

    navigator.serviceWorker.addEventListener('message', (event) => {
      console.log('Message from service worker:', event.data);

      if (event.data.type === 'COPY_TO_CLIPBOARD') {
        this.copyToClipboard(event.data.text);
      }
    });
  }

  /**
   * Copy text to clipboard
   */
  async copyToClipboard(text) {
    try {
      await navigator.clipboard.writeText(text);
      console.log('Copied to clipboard:', text);

      // Show toast notification
      if (window.errorHandler) {
        window.errorHandler.showToast('Code copied to clipboard!', 'success');
      }
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  }
}

// Create global instance
window.pushManager = new PushNotificationManager();

// Setup message listener
window.pushManager.setupMessageListener();

// Auto-initialize on page load if user is logged in
document.addEventListener('DOMContentLoaded', () => {
  if (localStorage.getItem('access_token')) {
    window.pushManager.initialize().catch(console.error);
  }
});
