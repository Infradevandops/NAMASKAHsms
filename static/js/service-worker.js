/**
 * Service Worker — Vrenum PWA v2
 * Production-grade: versioned cache, stale-while-revalidate for assets,
 * network-first for API, offline fallback for navigation.
 */

const CACHE_VERSION = '2.0.0';
const STATIC_CACHE = `vrenum-static-${CACHE_VERSION}`;
const RUNTIME_CACHE = `vrenum-runtime-${CACHE_VERSION}`;

const PRECACHE_URLS = [
    '/',
    '/offline',
    '/static/css/vrenum-ui.css',
    '/static/css/pwa-mobile.css',
    '/static/css/responsive.css',
    '/static/css/glassmorphism.css',
    '/static/js/formatMoney.js',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png',
    '/static/manifest.json',
];

/* ─── INSTALL ─────────────────────────────────────────────────────────── */
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(STATIC_CACHE).then((cache) => {
            return cache.addAll(PRECACHE_URLS).catch((err) => {
                console.warn('SW: precache partial failure:', err);
            });
        })
    );
    self.skipWaiting();
});

/* ─── ACTIVATE ────────────────────────────────────────────────────────── */
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((names) => {
            return Promise.all(
                names
                    .filter((n) => n !== STATIC_CACHE && n !== RUNTIME_CACHE)
                    .map((n) => caches.delete(n))
            );
        })
    );
    self.clients.claim();
});

/* ─── FETCH STRATEGY ──────────────────────────────────────────────────── */
self.addEventListener('fetch', (event) => {
    const { request } = event;
    if (request.method !== 'GET') return;

    const url = new URL(request.url);

    // API calls: network-only (never cache auth/data)
    if (url.pathname.startsWith('/api/')) return;

    // Static assets: stale-while-revalidate
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(staleWhileRevalidate(request));
        return;
    }

    // Navigation: network-first with offline fallback
    if (request.mode === 'navigate') {
        event.respondWith(networkFirstWithOffline(request));
        return;
    }

    // Everything else: network-first
    event.respondWith(
        fetch(request).catch(() => caches.match(request))
    );
});

/**
 * Stale-while-revalidate: serve from cache immediately,
 * update cache in background.
 */
async function staleWhileRevalidate(request) {
    const cache = await caches.open(RUNTIME_CACHE);
    const cached = await cache.match(request);

    const fetchPromise = fetch(request).then((response) => {
        if (response && response.status === 200) {
            cache.put(request, response.clone());
        }
        return response;
    }).catch(() => cached);

    return cached || fetchPromise;
}

/**
 * Network-first for navigation, fallback to offline page.
 */
async function networkFirstWithOffline(request) {
    try {
        const response = await fetch(request);
        // Cache successful navigation responses
        if (response.status === 200) {
            const cache = await caches.open(RUNTIME_CACHE);
            cache.put(request, response.clone());
        }
        return response;
    } catch (e) {
        const cached = await caches.match(request);
        if (cached) return cached;
        return caches.match('/offline');
    }
});

/* ─── PUSH NOTIFICATIONS ──────────────────────────────────────────────── */
self.addEventListener('push', (event) => {
    let data = { title: 'Vrenum', options: {} };

    if (event.data) {
        try {
            const payload = event.data.json();
            data.title = payload.notification?.title || payload.title || data.title;
            data.options = {
                body: payload.notification?.body || payload.message || '',
                icon: '/static/icons/icon-192x192.png',
                badge: '/static/icons/icon-72x72.png',
                tag: payload.notification?.tag || 'vrenum',
                data: payload.data || {},
            };
        } catch (e) {
            data.options.body = event.data.text();
        }
    }

    event.waitUntil(self.registration.showNotification(data.title, data.options));
});

/* ─── NOTIFICATION CLICK ──────────────────────────────────────────────── */
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const url = event.notification.data?.link || '/';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then((list) => {
            for (const client of list) {
                if (client.url === url && 'focus' in client) return client.focus();
            }
            if (clients.openWindow) return clients.openWindow(url);
        })
    );
});

/* ─── MESSAGE (cache control from client) ─────────────────────────────── */
self.addEventListener('message', (event) => {
    if (event.data?.type === 'SKIP_WAITING') self.skipWaiting();
    if (event.data?.type === 'CLEAR_CACHE') {
        Promise.all([
            caches.delete(STATIC_CACHE),
            caches.delete(RUNTIME_CACHE),
        ]).then(() => {
            event.ports[0]?.postMessage({ success: true });
        });
    }
    if (event.data?.type === 'GET_VERSION') {
        event.ports[0]?.postMessage({ version: CACHE_VERSION });
    }
});
