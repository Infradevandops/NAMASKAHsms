/**
 * Service Worker for Push Notifications
 * Handles push events and notification interactions
 */

const CACHE_NAME = 'namaskah-v1';
const URLS_TO_CACHE = [
    '/',
    '/static/css/mobile-notifications.css',
    '/static/js/mobile-notifications.js',
    '/static/images/icon-192x192.png',
    '/static/images/badge-72x72.png',
];

/**
 * Install event - cache resources
 */
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(URLS_TO_CACHE).catch((error) => {
                console.warn('Failed to cache some resources:', error);
            });
        })
    );
    self.skipWaiting();
});

/**
 * Activate event - clean up old caches
 */
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

/**
 * Fetch event - serve from cache, fallback to network
 */
self.addEventListener('fetch', (event) => {
    if (event.request.method !== 'GET') {
        return;
    }

    event.respondWith(
        caches.match(event.request).then((response) => {
            if (response) {
                return response;
            }

            return fetch(event.request)
                .then((response) => {
                    // Don't cache non-successful responses
                    if (!response || response.status !== 200 || response.type === 'error') {
                        return response;
                    }

                    // Clone the response
                    const responseToCache = response.clone();

                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, responseToCache);
                    });

                    return response;
                })
                .catch(() => {
                    // Return offline page or cached response
                    return caches.match('/');
                });
        })
    );
});

/**
 * Push event - handle incoming push notifications
 */
self.addEventListener('push', (event) => {
    let notificationData = {
        title: 'Namaskah Notification',
        options: {
            icon: '/static/images/icon-192x192.png',
            badge: '/static/images/badge-72x72.png',
            tag: 'notification',
            requireInteraction: false,
        },
    };

    if (event.data) {
        try {
            const data = event.data.json();
            notificationData.title = data.notification?.title || data.title || notificationData.title;
            notificationData.options = {
                ...notificationData.options,
                body: data.notification?.body || data.message || '',
                icon: data.notification?.icon || notificationData.options.icon,
                badge: data.notification?.badge || notificationData.options.badge,
                tag: data.notification?.tag || notificationData.options.tag,
                data: data.data || {},
            };
        } catch (error) {
            console.error('Failed to parse push notification data:', error);
            notificationData.options.body = event.data.text();
        }
    }

    event.waitUntil(
        self.registration.showNotification(notificationData.title, notificationData.options)
    );
});

/**
 * Notification click event - handle notification interactions
 */
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    const urlToOpen = event.notification.data?.link || '/';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
            // Check if there's already a window/tab open with the target URL
            for (let i = 0; i < clientList.length; i++) {
                const client = clientList[i];
                if (client.url === urlToOpen && 'focus' in client) {
                    return client.focus();
                }
            }

            // If not, open a new window/tab with the target URL
            if (clients.openWindow) {
                return clients.openWindow(urlToOpen);
            }
        })
    );
});

/**
 * Notification close event - track notification dismissal
 */
self.addEventListener('notificationclose', (event) => {
    const notificationData = event.notification.data;

    if (notificationData?.notification_id) {
        // Send analytics event to backend
        fetch('/api/notifications/analytics/track', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                notification_id: notificationData.notification_id,
                event: 'dismissed',
            }),
        }).catch((error) => {
            console.error('Failed to track notification dismissal:', error);
        });
    }
});

/**
 * Message event - handle messages from clients
 */
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }

    if (event.data && event.data.type === 'CLEAR_CACHE') {
        caches.delete(CACHE_NAME).then(() => {
            event.ports[0].postMessage({ success: true });
        });
    }
});

/**
 * Sync event - handle background sync for offline notifications
 */
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-notifications') {
        event.waitUntil(
            fetch('/api/notifications/sync', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            }).catch((error) => {
                console.error('Failed to sync notifications:', error);
            })
        );
    }
});
