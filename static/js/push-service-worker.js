// Service Worker for Push Notifications
// Handles incoming push messages and notification clicks

const CACHE_NAME = 'namaskah-v1';

// Install event
self.addEventListener('install', (event) => {
  console.log('Service Worker: Installing...');
  self.skipWaiting();
});

// Activate event
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activating...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            console.log('Service Worker: Clearing old cache');
            return caches.delete(cache);
          }
        })
      );
    })
  );
  return self.clients.claim();
});

// Push event - handle incoming push notifications
self.addEventListener('push', (event) => {
  console.log('Service Worker: Push received', event);

  let data = {};
  let notification = {
    title: 'Namaskah',
    body: 'You have a new notification',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/badge-72x72.png',
    tag: 'default',
    requireInteraction: false,
    actions: []
  };

  // Parse push data
  if (event.data) {
    try {
      const payload = event.data.json();
      console.log('Push payload:', payload);

      // Extract notification data
      if (payload.notification) {
        notification = {
          ...notification,
          ...payload.notification
        };
      }

      // Extract custom data
      if (payload.data) {
        data = payload.data;
      }
    } catch (e) {
      console.error('Failed to parse push data:', e);
      notification.body = event.data.text();
    }
  }

  // Show notification
  const options = {
    body: notification.body,
    icon: notification.icon,
    badge: notification.badge,
    tag: notification.tag,
    requireInteraction: notification.requireInteraction,
    actions: notification.actions || [],
    data: data,
    vibrate: [200, 100, 200],
    timestamp: Date.now()
  };

  event.waitUntil(
    self.registration.showNotification(notification.title, options)
  );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
  console.log('Notification clicked:', event);

  event.notification.close();

  const data = event.notification.data || {};
  const action = event.action;

  // Handle different actions
  let url = data.url || '/dashboard';

  if (action === 'view') {
    url = data.url || '/dashboard';
  } else if (action === 'copy') {
    // Copy SMS code to clipboard
    if (data.sms_code) {
      event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
          for (const client of clientList) {
            if (client.url.includes(self.location.origin)) {
              client.postMessage({
                type: 'COPY_TO_CLIPBOARD',
                text: data.sms_code
              });
              return;
            }
          }
        })
      );
    }
    return;
  } else if (action === 'topup') {
    url = '/wallet';
  }

  // Open or focus window
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      // Check if there's already a window open
      for (const client of clientList) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          client.focus();
          client.navigate(url);
          return;
        }
      }
      // Open new window
      if (clients.openWindow) {
        return clients.openWindow(url);
      }
    })
  );
});

// Message event - handle messages from main thread
self.addEventListener('message', (event) => {
  console.log('Service Worker: Message received', event.data);

  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Background sync (future enhancement)
self.addEventListener('sync', (event) => {
  console.log('Service Worker: Background sync', event.tag);

  if (event.tag === 'sync-notifications') {
    event.waitUntil(syncNotifications());
  }
});

async function syncNotifications() {
  // Sync unread notifications when back online
  try {
    const response = await fetch('/api/notifications/unread', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });

    if (response.ok) {
      const data = await response.json();
      console.log('Synced notifications:', data);
    }
  } catch (error) {
    console.error('Failed to sync notifications:', error);
  }
}
