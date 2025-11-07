// Enhanced Service Worker for caching and offline support
const CACHE_NAME = 'namaskah-v2.0';
const STATIC_CACHE = 'namaskah-static-v2.0';
const API_CACHE = 'namaskah-api-v2.0';

const STATIC_ASSETS = [
    '/',
    '/static/css/style.css',
    '/static/css/enhanced-ui.css',
    '/static/js/enhanced-verification-ui.js',
    '/static/js/performance-optimizer.js',
    '/static/icons/icon-192x192.png'
];

const API_ENDPOINTS = [
    '/auth/me',
    '/monitoring/metrics',
    '/infrastructure/regions'
];

// Install event
self.addEventListener('install', event => {
    event.waitUntil(
        Promise.all([
            caches.open(STATIC_CACHE).then(cache => cache.addAll(STATIC_ASSETS)),
            caches.open(API_CACHE)
        ]).then(() => self.skipWaiting())
    );
});

// Activate event
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== STATIC_CACHE && cacheName !== API_CACHE) {
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch event with advanced caching strategies
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);

    // Static assets - Cache First
    if (STATIC_ASSETS.some(asset => url.pathname.includes(asset))) {
        event.respondWith(cacheFirst(request, STATIC_CACHE));
    }
    // API endpoints - Network First with fallback
    else if (API_ENDPOINTS.some(endpoint => url.pathname.includes(endpoint))) {
        event.respondWith(networkFirst(request, API_CACHE));
    }
    // Other requests - Network Only
    else {
        event.respondWith(fetch(request));
    }
});

// Cache First Strategy
async function cacheFirst(request, cacheName) {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(request);
    
    if (cached) {
        // Update cache in background
        fetch(request).then(response => {
            if (response.ok) {
                cache.put(request, response.clone());
            }
        });
        return cached;
    }
    
    const response = await fetch(request);
    if (response.ok) {
        cache.put(request, response.clone());
    }
    return response;
}

// Network First Strategy
async function networkFirst(request, cacheName) {
    const cache = await caches.open(cacheName);
    
    try {
        const response = await fetch(request);
        if (response.ok) {
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        const cached = await cache.match(request);
        if (cached) {
            return cached;
        }
        throw error;
    }
}

// Background sync for offline actions
self.addEventListener('sync', event => {
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

async function doBackgroundSync() {
    // Sync pending verification requests when online
    const pendingRequests = await getStoredRequests();
    
    for (const request of pendingRequests) {
        try {
            await fetch(request.url, request.options);
            await removeStoredRequest(request.id);
        } catch (error) {
            console.log('Sync failed for request:', request.id);
        }
    }
}

// Push notifications
self.addEventListener('push', event => {
    const options = {
        body: event.data ? event.data.text() : 'New verification update',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/icon-72x72.png',
        vibrate: [200, 100, 200],
        data: {
            url: '/'
        }
    };

    event.waitUntil(
        self.registration.showNotification('Namaskah SMS', options)
    );
});

// Notification click
self.addEventListener('notificationclick', event => {
    event.notification.close();
    
    event.waitUntil(
        clients.openWindow(event.notification.data.url || '/')
    );
});

// Helper functions for IndexedDB operations
async function getStoredRequests() {
    // Simplified - would use IndexedDB in production
    return [];
}

async function removeStoredRequest(id) {
    // Simplified - would use IndexedDB in production
    return true;
}