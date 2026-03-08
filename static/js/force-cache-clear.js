/**
 * Force Cache Clear Script
 * Run this in browser console to immediately clear all caches
 * and reload with fresh i18n.js
 */

(async function forceCacheClear() {
    console.log('🧹 Starting cache clear...');
    
    // 1. Clear all service worker caches
    if ('caches' in window) {
        const cacheNames = await caches.keys();
        console.log(`Found ${cacheNames.length} caches:`, cacheNames);
        
        for (const cacheName of cacheNames) {
            await caches.delete(cacheName);
            console.log(`✓ Deleted cache: ${cacheName}`);
        }
    }
    
    // 2. Unregister all service workers
    if ('serviceWorker' in navigator) {
        const registrations = await navigator.serviceWorker.getRegistrations();
        console.log(`Found ${registrations.length} service workers`);
        
        for (const registration of registrations) {
            await registration.unregister();
            console.log(`✓ Unregistered service worker`);
        }
    }
    
    // 3. Clear localStorage (preserve auth token)
    const token = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');
    localStorage.clear();
    if (token) localStorage.setItem('access_token', token);
    if (refreshToken) localStorage.setItem('refresh_token', refreshToken);
    console.log('✓ Cleared localStorage (preserved auth)');
    
    // 4. Clear sessionStorage
    sessionStorage.clear();
    console.log('✓ Cleared sessionStorage');
    
    // 5. Force reload without cache
    console.log('🔄 Reloading page...');
    window.location.reload(true);
})();
