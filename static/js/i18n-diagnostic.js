/**
 * i18n Diagnostic Script
 * Run this in browser console to diagnose translation issues
 */

(function() {
    console.log('═══════════════════════════════════════');
    console.log('🔍 i18n DIAGNOSTIC REPORT');
    console.log('═══════════════════════════════════════');
    console.log('');
    
    // 1. Check if i18n exists
    console.log('1. i18n Object:');
    if (typeof window.i18n === 'undefined') {
        console.error('   ❌ window.i18n is undefined!');
        console.log('   → i18n.js may not have loaded');
    } else {
        console.log('   ✅ window.i18n exists');
        console.log('   - Locale:', window.i18n.locale);
        console.log('   - Loaded:', window.i18n.loaded);
        console.log('   - Translations count:', Object.keys(window.i18n.translations).length);
        console.log('   - Fallback count:', Object.keys(window.i18n.fallback).length);
    }
    console.log('');
    
    // 2. Check if translations loaded
    console.log('2. Translation Data:');
    if (window.i18n && window.i18n.loaded) {
        console.log('   ✅ Translations loaded');
        
        // Test specific keys
        const testKeys = [
            'dashboard.title',
            'dashboard.subtitle',
            'tiers.current_plan',
            'common.dashboard'
        ];
        
        console.log('   Testing keys:');
        testKeys.forEach(key => {
            const value = window.i18n.t(key);
            if (value === key) {
                console.error(`   ❌ ${key} → "${value}" (not translated)`);
            } else {
                console.log(`   ✅ ${key} → "${value}"`);
            }
        });
    } else {
        console.error('   ❌ Translations not loaded');
    }
    console.log('');
    
    // 3. Check DOM elements
    console.log('3. DOM Elements with data-i18n:');
    const elements = document.querySelectorAll('[data-i18n]');
    console.log(`   Found ${elements.length} elements`);
    
    if (elements.length === 0) {
        console.error('   ❌ No elements with data-i18n found!');
    } else {
        console.log('   First 10 elements:');
        Array.from(elements).slice(0, 10).forEach((el, i) => {
            const key = el.getAttribute('data-i18n');
            const text = el.textContent.trim();
            const isTranslated = text !== key;
            
            if (isTranslated) {
                console.log(`   ${i + 1}. ✅ ${key} → "${text}"`);
            } else {
                console.error(`   ${i + 1}. ❌ ${key} → "${text}" (showing key!)`);
            }
        });
    }
    console.log('');
    
    // 4. Check cache version
    console.log('4. Cache Version:');
    const cacheVersion = localStorage.getItem('i18n_version');
    console.log('   Current:', cacheVersion);
    console.log('   Expected: 20260308g');
    if (cacheVersion !== '20260308g') {
        console.warn('   ⚠️  Cache version mismatch!');
        console.log('   → Try hard refresh (Ctrl+Shift+R)');
    } else {
        console.log('   ✅ Cache version correct');
    }
    console.log('');
    
    // 5. Check service worker
    console.log('5. Service Worker:');
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.getRegistrations().then(regs => {
            if (regs.length === 0) {
                console.log('   ℹ️  No service workers registered');
            } else {
                console.log(`   Found ${regs.length} service worker(s)`);
                regs.forEach((reg, i) => {
                    console.log(`   ${i + 1}. State:`, reg.active?.state || 'unknown');
                });
            }
        });
    } else {
        console.log('   ℹ️  Service Worker not supported');
    }
    console.log('');
    
    // 6. Check caches
    console.log('6. Browser Caches:');
    if ('caches' in window) {
        caches.keys().then(names => {
            if (names.length === 0) {
                console.log('   ℹ️  No caches found');
            } else {
                console.log(`   Found ${names.length} cache(s):`);
                names.forEach((name, i) => {
                    console.log(`   ${i + 1}. ${name}`);
                });
            }
        });
    } else {
        console.log('   ℹ️  Cache API not supported');
    }
    console.log('');
    
    // 7. Recommendations
    console.log('7. Recommendations:');
    const issues = [];
    
    if (typeof window.i18n === 'undefined') {
        issues.push('i18n.js not loaded - check network tab');
    }
    if (window.i18n && !window.i18n.loaded) {
        issues.push('Translations not loaded - check console for errors');
    }
    if (elements.length === 0) {
        issues.push('No data-i18n elements found - wrong page?');
    }
    if (cacheVersion !== '20260308g') {
        issues.push('Old cache version - hard refresh needed');
    }
    
    if (issues.length === 0) {
        console.log('   ✅ No issues detected!');
        console.log('   If you still see translation keys, try:');
        console.log('   1. Hard refresh (Ctrl+Shift+R)');
        console.log('   2. Clear site data in DevTools');
        console.log('   3. Try incognito mode');
    } else {
        console.error('   ❌ Issues found:');
        issues.forEach((issue, i) => {
            console.error(`   ${i + 1}. ${issue}`);
        });
    }
    console.log('');
    
    // 8. Quick fixes
    console.log('8. Quick Fixes:');
    console.log('   Run these commands to fix:');
    console.log('');
    console.log('   // Force re-translate');
    console.log('   window.i18n.translatePage()');
    console.log('');
    console.log('   // Clear cache and reload');
    console.log('   localStorage.setItem("i18n_version", "20260308g");');
    console.log('   location.reload(true);');
    console.log('');
    
    console.log('═══════════════════════════════════════');
    console.log('END OF DIAGNOSTIC REPORT');
    console.log('═══════════════════════════════════════');
})();
