# Cache Clear Instructions - i18n Fix

## Problem
The old i18n.js is cached by the service worker, causing translation keys to still appear.

## Solution Deployed

### Automatic (Next Page Load)
The dashboard will now automatically:
1. Detect old cache version
2. Clear service worker caches
3. Reload page with fresh i18n.js

**Just refresh the page once** and it should work!

---

## Manual Fix (If Automatic Doesn't Work)

### Option 1: Hard Refresh (Easiest)
1. **Windows/Linux:** Press `Ctrl + Shift + R` or `Ctrl + F5`
2. **Mac:** Press `Cmd + Shift + R`

This forces the browser to bypass cache.

---

### Option 2: Clear Cache via DevTools
1. Open DevTools (`F12` or `Right-click → Inspect`)
2. Go to **Application** tab
3. Click **Clear storage** (left sidebar)
4. Check all boxes
5. Click **Clear site data**
6. Refresh page

---

### Option 3: Run Console Script
1. Open browser console (`F12` → Console tab)
2. Paste this command:

```javascript
(async function() {
    const cacheNames = await caches.keys();
    for (const name of cacheNames) {
        await caches.delete(name);
        console.log('Deleted:', name);
    }
    const regs = await navigator.serviceWorker.getRegistrations();
    for (const reg of regs) await reg.unregister();
    localStorage.setItem('i18n_version', '20260308f');
    location.reload(true);
})();
```

3. Press Enter
4. Page will reload automatically

---

### Option 4: Load Force Clear Script
1. Open browser console (`F12` → Console tab)
2. Paste this:

```javascript
const script = document.createElement('script');
script.src = '/static/js/force-cache-clear.js';
document.head.appendChild(script);
```

3. Press Enter
4. Page will reload automatically

---

## Verification

After clearing cache, check:

1. **Dashboard title** should show "Dashboard" not "dashboard.title"
2. **Tier card** should show "Custom" not "tiers.current_plan"
3. **Balance** should show "$10.80" not "common.balance"
4. **Sidebar** should show "History" not "verify.title"

### Debug Commands

Open console and run:

```javascript
// Check if new i18n loaded
window.i18n.loaded // Should be true

// Check version
localStorage.getItem('i18n_version') // Should be '20260308f'

// List all i18n elements
window.i18nHelpers.debugI18nElements()

// Force re-translate
window.i18n.translatePage()
```

---

## What Changed

1. **Service Worker:** Cache version bumped to `v4-i18n-fix`
2. **i18n.js:** Version bumped to `v20260308f`
3. **Auto-clear:** Script runs on first load to clear old caches
4. **Meta tags:** Added cache-control headers to prevent caching

---

## If Still Not Working

1. Try **incognito/private mode** - This bypasses all caches
2. Try **different browser** - Confirms it's a cache issue
3. **Clear browser data:**
   - Chrome: Settings → Privacy → Clear browsing data
   - Firefox: Settings → Privacy → Clear Data
   - Safari: Develop → Empty Caches

---

## For Production Deployment

If deploying to Render.com or other hosting:

1. The changes are already pushed to GitHub
2. Render will auto-deploy
3. Users will get automatic cache clear on next visit
4. No manual intervention needed

---

## Technical Details

**Files Changed:**
- `static/sw.js` - Service worker cache version
- `templates/base.html` - Cache-control meta tags
- `templates/dashboard_base.html` - Auto-clear script + version bump
- `static/js/force-cache-clear.js` - Manual clear script

**Cache Strategy:**
1. Automatic detection via localStorage version check
2. Service worker cache deletion
3. Force reload without cache
4. Meta tags prevent future aggressive caching

---

## Success Criteria

✅ No "dashboard.title" visible  
✅ No "tiers.current_plan" visible  
✅ No "common.balance" visible  
✅ All text shows in proper English  
✅ Translations persist after 1 second  
✅ Language switcher works  

---

**Last Updated:** March 8, 2026  
**Cache Version:** v4-i18n-fix  
**i18n Version:** 20260308f
