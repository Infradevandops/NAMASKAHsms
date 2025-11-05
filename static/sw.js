// Service Worker for PWA
const CACHE_NAME = 'namaskah-v2.4.0';
const urlsToCache = [
  '/',
  '/static/css/style.css',
  '/static/css/mobile.css',
  '/static/js/config.js',
  '/static/js/utils.js',
  '/static/js/auth.js',
  '/static/js/services.js',
  '/static/js/verification.js',
  '/static/js/history.js',
  '/static/js/wallet.js',
  '/static/js/rentals.js',
  '/static/js/developer.js',
  '/static/js/settings.js',
  '/static/js/mobile.js',
  '/static/js/biometric.js',
  '/static/js/offline-queue.js',
  '/static/js/main.js',
  '/static/manifest.json'
];

// Install event
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
      .then(() => self.skipWaiting())
  );
});

// Activate event
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
    }).then(() => self.clients.claim())
  );
});

// Fetch event - Network first, fallback to cache
self.addEventListener('fetch', (event) => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') return;
  
  // Validate URL to prevent SSRF
  const url = new URL(event.request.url);
  const allowedOrigins = [self.location.origin];
  
  if (!allowedOrigins.includes(url.origin)) {
    return;
  }
  
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Only cache successful responses
        if (response.status === 200) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
        }
        return response;
      })
      .catch(() => {
        // Network failed, try cache
        return caches.match(event.request).then(cached => {
          return cached || new Response('Offline', { status: 503 });
        });
      })
  );
});

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-verifications') {
    event.waitUntil(syncVerifications());
  }
});

async function syncVerifications() {
  // Sync pending verifications when back online
  const cache = await caches.open(CACHE_NAME);
  const requests = await cache.keys();
  
  for (const request of requests) {
    if (request.url.includes('/verify/')) {
      try {
        await fetch(request);
      } catch (error) {
        console.error('Sync failed:', error);
      }
    }
  }
}

// Push notifications
self.addEventListener('push', (event) => {
  const data = event.data ? event.data.json() : {};
  const title = data.title || 'Namaskah SMS';
  const options = {
    body: data.body || 'New SMS received',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/icon-72x72.png',
    vibrate: [200, 100, 200],
    data: data.url || '/'
  };
  
  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Notification click
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data)
  );
});
