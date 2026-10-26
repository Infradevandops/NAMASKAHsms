# Frontend Upgrade Plan

**Created**: October 25, 2026
**Version**: 4.9.0
**Priority**: Medium
**Status**: 🔄 Pending

---

## Context

Full frontend audit completed on v4.9.0. The frontend is server-rendered Jinja2 + vanilla JS.
No build step, no bundler. Landing page uses Tailwind CDN + Alpine.js. Dashboard uses a custom
design system. All changes below are non-breaking — each can be shipped independently.

---

## Category 1 — Performance

### P1 — Remove Tailwind CDN, use CLI build

**Problem**: `landing.html` loads `cdn.tailwindcss.com` which ships the full ~3MB Tailwind
library to every visitor on every page load.

**Fix**:
```bash
# Install Tailwind CLI (no Node project needed)
npm install -D tailwindcss

# Create tailwind.config.js at project root
cat > tailwind.config.js << 'EOF'
module.exports = {
  content: ["./templates/**/*.html"],
  darkMode: ['selector', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        brand: { 400: '#FF6B9D', 500: '#FE3C72', 600: '#E0245E' }
      }
    }
  }
}
EOF

# Build
npx tailwindcss -i ./static/css/tailwind-input.css -o ./static/css/tailwind.min.css --minify
```

Create `static/css/tailwind-input.css`:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

In `landing.html`, replace:
```html
<!-- REMOVE -->
<script src="https://cdn.tailwindcss.com" nonce="..."></script>
<script nonce="...">tailwind.config = { ... }</script>

<!-- ADD -->
<link rel="stylesheet" href="/static/css/tailwind.min.css">
```

Add to `scripts/Makefile`:
```makefile
css:
	npx tailwindcss -i ./static/css/tailwind-input.css -o ./static/css/tailwind.min.css --minify
```

**Add to deploy workflow** (`.github/workflows/deploy.yml`) before the SSH step:
```yaml
- name: Build CSS
  run: npx tailwindcss -i ./static/css/tailwind-input.css -o ./static/css/tailwind.min.css --minify
```

**Verification**:
- [ ] `landing.html` loads with no CDN Tailwind script tag
- [ ] All Tailwind classes still render correctly
- [ ] Lighthouse performance score improves (remove 3MB script)

---

### P2 — Fix double `dark-mode-universal.css` load

**Problem**: `dashboard_base.html` includes `dark-mode-universal.css` twice in `head_extra`.

**Fix** in `templates/dashboard_base.html` — remove the duplicate:
```diff
 <link rel="stylesheet" href="/static/css/dark-mode-universal.css">
-<link rel="stylesheet" href="/static/css/dark-mode-universal.css">
```

**Verification**:
- [ ] Browser DevTools Network tab shows `dark-mode-universal.css` loaded once per page

---

### P3 — Defer analytics scripts, load Sabilytics post-consent

**Problem**: Both GA4 and Sabilytics load on every page including unauthenticated ones.
Sabilytics has no `defer` and blocks rendering.

**Fix** in `templates/base.html`:
```diff
-<script async src="https://www.googletagmanager.com/gtag/js?id=G-M15PBV1P55"></script>
+<script async defer src="https://www.googletagmanager.com/gtag/js?id=G-M15PBV1P55"></script>

-<script async src="https://www.sabilytics.com/script.js" data-site="ek3athooftac" data-domain="vrenum.app"></script>
+<!-- Sabilytics loaded after consent — see cookie consent script below -->
```

In the `acceptCookies()` function (base.html and landing.html — see Category 4 for dedup):
```diff
 function acceptCookies() {
     localStorage.setItem('cookie_consent', 'accepted');
     document.getElementById('cookie-consent').style.display = 'none';
+    // Load analytics after consent
+    if (!document.querySelector('script[src*="sabilytics"]')) {
+        const s = document.createElement('script');
+        s.async = true;
+        s.src = 'https://www.sabilytics.com/script.js';
+        s.dataset.site = 'ek3athooftac';
+        s.dataset.domain = 'vrenum.app';
+        document.head.appendChild(s);
+    }
 }
```

Also load Sabilytics on init if consent already given:
```js
(function() {
    if (localStorage.getItem('cookie_consent') === 'accepted') {
        const s = document.createElement('script');
        s.async = true;
        s.src = 'https://www.sabilytics.com/script.js';
        s.dataset.site = 'ek3athooftac';
        s.dataset.domain = 'vrenum.app';
        document.head.appendChild(s);
    }
})();
```

**Verification**:
- [ ] Network tab: Sabilytics does not load on fresh visit before consent
- [ ] Sabilytics loads after clicking Accept
- [ ] GA4 still fires pageview events

---

### P4 — Standardize cache-busting version tokens

**Problem**: Version strings are inconsistent (`?v=20260506`, `?v=20260208-ultra`, no version).
Some files get stale caches, some get busted on every deploy.

**Fix**: Use a single version token injected by the server. In `app/api/main_routes.py` (or
wherever templates are rendered), add the app version to the template context:

```python
# In the base template context helper
context["asset_version"] = settings.version.replace(".", "")  # "490"
```

In `templates/base.html` and `templates/dashboard_base.html`, replace all `?v=XXXXXXXX` with:
```html
<link rel="stylesheet" href="/static/css/design-system.css?v={{ asset_version }}">
<script src="/static/js/dashboard-ultra-stable.js?v={{ asset_version }}"></script>
```

**Verification**:
- [ ] All versioned assets use `?v={{ asset_version }}`
- [ ] Bumping `settings.version` in `.env` busts all caches

---

### P5 — Remove dead `real-time-dashboard.js` comment

**Problem**: `dashboard_base.html` has a commented-out script tag that has been disabled
"temporarily" with no resolution plan.

**Fix** in `templates/dashboard_base.html`:
```diff
-<!-- Temporarily disabled: causing errors
-<script src="/static/js/real-time-dashboard.js" defer></script>
--->
```

Then either fix `real-time-dashboard.js` or delete it:
```bash
# Check if anything imports it
grep -r "real-time-dashboard" templates/ static/ --include="*.html" --include="*.js"
# If only the one commented reference — delete it
rm static/js/real-time-dashboard.js
```

**Verification**:
- [ ] No commented script tags in `dashboard_base.html`
- [ ] `real-time-dashboard.js` either works or is deleted

---

### P6 — Move `pwa-mobile.css` out of public pages

**Problem**: `pwa-mobile.css` is loaded in `base.html` (all pages) but only applies to the
authenticated dashboard PWA experience.

**Fix**: Remove from `base.html`, add to `dashboard_base.html` only.

In `templates/base.html`:
```diff
-<link rel="stylesheet" href="/static/css/pwa-mobile.css">
```

In `templates/dashboard_base.html` (already loads it via landing.html include — verify first):
```html
<link rel="stylesheet" href="/static/css/pwa-mobile.css">
```

**Verification**:
- [ ] Landing page network tab: `pwa-mobile.css` not loaded
- [ ] Dashboard pages: `pwa-mobile.css` still loaded

---

## Category 2 — JS Architecture

### J1 — Extract verify page inline JS to a file

**Problem**: `verify_modern.html` has ~1,200 lines of inline `<script>` containing the entire
verification flow state machine. It cannot be cached, tested, or reused.

**Fix**: Extract to `static/js/verification-flow.js`.

Steps:
1. Cut everything inside the `<script nonce="...">` block in `verify_modern.html`
2. Paste into `static/js/verification-flow.js` — no changes needed to the code itself
3. Replace the inline block with:

```html
<script src="/static/js/verification-flow.js?v={{ asset_version }}"></script>
```

The nonce is only needed for inline scripts — external `src` scripts don't need it under
the current CSP config (static files are same-origin).

**Note**: The `sms-websocket.js` script at the bottom of the template stays as-is.

**Verification**:
- [ ] `/verify` page works identically after extraction
- [ ] Browser DevTools Sources tab shows `verification-flow.js` as a cacheable resource
- [ ] No JS errors in console

---

### J2 — Fix `btn-primary` color conflict between design system and injected styles

**Problem**: `dashboard-ultra-stable.js` calls `injectStyles()` which appends a `<style>` tag
defining `.btn-primary { background: #3b82f6 }` (blue). The design system defines
`.btn-primary` as `#FE3C72` (brand pink). Whichever loads last wins — this is a race condition.

**Fix**: Remove the `injectStyles()` call and the entire injected style block from
`dashboard-ultra-stable.js`. All those styles already exist in `design-system.css`.

In `static/js/dashboard-ultra-stable.js`:
```diff
-function injectStyles() {
-    if (document.getElementById('dashboard-ultra-styles')) return;
-    const style = document.createElement('style');
-    style.id = 'dashboard-ultra-styles';
-    style.textContent = `...`; // entire block
-    document.head.appendChild(style);
-}

 function init() {
-    injectStyles();
     initButtons();
 }
```

The modal, button, form, and animation styles in that injected block are already covered by
`design-system.css`. The only styles that may be missing are `.type-card` and `.upgrade-card`
— add those to `design-system.css`:

```css
/* Verification type picker cards */
.type-card {
    background: var(--gray-50);
    border: 2px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 20px 12px;
    cursor: pointer;
    text-align: center;
    transition: border-color var(--transition-base), background var(--transition-base);
    font-family: var(--font-family);
}
.type-card:hover {
    border-color: var(--color-primary);
    background: var(--color-primary-light);
}

/* Upgrade tier picker cards */
.upgrade-card {
    border: 2px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: var(--space-4);
    margin-bottom: var(--space-3);
    cursor: pointer;
    transition: border-color var(--transition-base);
}
.upgrade-card:hover {
    border-color: var(--color-primary);
}
```

**Verification**:
- [ ] Dashboard buttons are brand pink (`#FE3C72`), not blue
- [ ] Verification type picker modal renders correctly
- [ ] Upgrade modal tier cards render correctly

---

### J3 — Remove duplicate `getAuthToken` / `getAuthHeaders` implementations

**Problem**: `auth-helpers.js` exports `getAuthToken` and `getAuthHeaders` as ES modules, but
`dashboard-ultra-stable.js` and `sidebar.html` each define their own identical versions as
plain functions. Three implementations of the same logic.

**Fix**: `dashboard-ultra-stable.js` is an IIFE (non-module), so it can't import ES modules
directly. The cleanest non-breaking fix is to use `window.AuthHelpers` which `auth-helpers.js`
already exposes:

In `static/js/dashboard-ultra-stable.js`, replace the local definitions:
```diff
-function getAuthToken() {
-    return localStorage.getItem('access_token') ||
-           document.cookie.split('; ').find(...)?.split('=')[1];
-}
-function getAuthHeaders() {
-    const token = getAuthToken();
-    return { 'Content-Type': 'application/json', 'Authorization': token ? `Bearer ${token}` : '' };
-}
+function getAuthToken() {
+    return window.AuthHelpers?.getAuthToken() || localStorage.getItem('access_token');
+}
+function getAuthHeaders() {
+    return { 'Content-Type': 'application/json', ...( window.AuthHelpers?.getAuthHeaders() || {} ) };
+}
```

Load `auth-helpers.js` before `dashboard-ultra-stable.js` in `dashboard_base.html`:
```html
<!-- auth-helpers must load before dashboard-ultra-stable -->
<script type="module" src="/static/js/auth-helpers.js"></script>
<script src="/static/js/dashboard-ultra-stable.js"></script>
```

`sidebar.html` already uses `localStorage.getItem('access_token')` directly — leave it as-is
since it's a simple one-liner, not a full reimplementation.

**Verification**:
- [ ] Dashboard API calls still authenticate correctly
- [ ] No `window.AuthHelpers is undefined` errors in console

---

### J4 — Remove duplicate `scroll-timeline.js`

**Problem**: Both `static/js/scroll-timeline.js` and `static/js/modules/scroll-timeline.js`
exist. One is stale.

**Fix**:
```bash
# Check which one is actually referenced
grep -r "scroll-timeline" templates/ static/ --include="*.html" --include="*.js"
```

Delete whichever is not referenced. If both are referenced, consolidate to one and update
the reference.

**Verification**:
- [ ] Only one `scroll-timeline.js` exists
- [ ] No 404s for the deleted file

---

### J5 — Remove or wire up `moduleLoader.js`

**Problem**: `moduleLoader.js` exists but all scripts are loaded with plain `<script src>` tags.
The file is dead code.

**Fix**:
```bash
grep -r "moduleLoader" templates/ static/ --include="*.html" --include="*.js"
```

If nothing references it — delete it:
```bash
rm static/js/moduleLoader.js
```

If it is referenced somewhere, wire it up properly or remove the reference.

**Verification**:
- [ ] No orphaned `moduleLoader.js` in the repo

---

## Category 3 — UX / Interaction

### U1 — Replace service worker `confirm()` with toast banner

**Problem**: `base.html` uses a blocking `confirm()` dialog for SW update prompts.

**Fix** in `templates/base.html`, replace the SW update handler:
```diff
-if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
-    if (confirm('A new version is available. Reload to update?')) {
-        newWorker.postMessage({ type: 'SKIP_WAITING' });
-        window.location.reload();
-    }
-}
+if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
+    showUpdateBanner(newWorker);
+}
```

Add the banner function (before the SW registration block):
```html
<script>
function showUpdateBanner(newWorker) {
    const existing = document.getElementById('sw-update-banner');
    if (existing) return;
    const banner = document.createElement('div');
    banner.id = 'sw-update-banner';
    banner.style.cssText = 'position:fixed;bottom:80px;left:50%;transform:translateX(-50%);background:#1f2937;color:white;padding:12px 20px;border-radius:10px;box-shadow:0 4px 20px rgba(0,0,0,0.3);z-index:9998;display:flex;align-items:center;gap:12px;font-size:14px;white-space:nowrap;';
    banner.innerHTML = `
        <span>A new version is available.</span>
        <button onclick="(function(){document.getElementById('sw-update-banner').remove();newWorker.postMessage({type:'SKIP_WAITING'});window.location.reload();})()" style="background:#FE3C72;color:white;border:none;padding:6px 14px;border-radius:6px;font-weight:600;cursor:pointer;font-size:13px;">Reload</button>
        <button onclick="document.getElementById('sw-update-banner').remove()" style="background:transparent;color:#9ca3af;border:none;cursor:pointer;font-size:18px;line-height:1;padding:0 4px;">&times;</button>
    `;
    document.body.appendChild(banner);
}
</script>
```

**Verification**:
- [ ] No `confirm()` dialog appears on SW update
- [ ] Banner appears at bottom of screen with Reload / dismiss buttons

---

### U2 — Replace sidebar `confirm()` dialogs with inline UI

**Problem**: `sidebar.html` uses `confirm()` in two places:
1. `showUpgradePrompt()` — asks user to upgrade via confirm dialog
2. `logout()` — asks "Are you sure you want to logout?"

**Fix for logout** — remove the confirm, just log out:
```diff
 function logout() {
-    if (!confirm('Are you sure you want to logout?')) return;
     const token = localStorage.getItem('access_token');
     fetch('/api/auth/logout', { ... })
```

Logout confirmation is unnecessary friction. The user clicked Logout intentionally.

**Fix for upgrade prompt** — replace `confirm()` with a toast that links to pricing:
```diff
-function showUpgradePrompt(requiredTier, featureName) {
-    const message = `${featureName} requires ${tierNames[requiredTier]}.\n\nUpgrade now?`;
-    if (confirm(message)) { window.location.href = '/pricing'; }
-}
+function showUpgradePrompt(requiredTier, featureName) {
+    const tierNames = { payg: 'Pay-As-You-Go', pro: 'Pro', custom: 'Custom' };
+    if (window.toast) {
+        window.toast.info(
+            `${featureName.trim()} requires ${tierNames[requiredTier] || requiredTier} — <a href="/pricing" style="color:white;text-decoration:underline;">Upgrade →</a>`,
+            { duration: 5000, html: true }
+        );
+    } else {
+        window.location.href = '/pricing?upgrade=' + requiredTier;
+    }
+}
```

**Verification**:
- [ ] Clicking a locked nav item shows a toast, not a confirm dialog
- [ ] Logout button logs out immediately without a confirm dialog

---

### U3 — Replace preset `prompt()` with inline input

**Problem**: `verify_modern.html` (or `verification-flow.js` after J1) uses `prompt()` to
name a preset.

**Fix**: Replace `saveCurrentAsPreset()` with an inline input that appears in the presets section:

```diff
-async function saveCurrentAsPreset() {
-    const svc = VerificationFlow.selectedService;
-    if (!svc) return;
-    const name = prompt('Preset name (e.g. "WhatsApp NY")');
-    if (!name || !name.trim()) return;
-    // ... save logic
-}
+async function saveCurrentAsPreset() {
+    const svc = VerificationFlow.selectedService;
+    if (!svc) return;
+
+    // Show inline input instead of prompt()
+    const presetsSection = document.getElementById('presets-section');
+    if (document.getElementById('preset-name-input-row')) return; // already open
+
+    const row = document.createElement('div');
+    row.id = 'preset-name-input-row';
+    row.style.cssText = 'display:flex;gap:8px;margin-top:8px;';
+    row.innerHTML = `
+        <input id="preset-name-input" type="text" placeholder='e.g. "WhatsApp NY"'
+            style="flex:1;padding:6px 10px;border:1px solid #e5e7eb;border-radius:6px;font-size:13px;"
+            onkeydown="if(event.key==='Enter')confirmSavePreset();if(event.key==='Escape')cancelSavePreset();">
+        <button onclick="confirmSavePreset()" style="background:#FE3C72;color:white;border:none;padding:6px 12px;border-radius:6px;font-size:12px;font-weight:600;cursor:pointer;">Save</button>
+        <button onclick="cancelSavePreset()" style="background:none;border:1px solid #e5e7eb;padding:6px 10px;border-radius:6px;font-size:12px;cursor:pointer;">Cancel</button>
+    `;
+    presetsSection.appendChild(row);
+    setTimeout(() => document.getElementById('preset-name-input')?.focus(), 50);
+}
+
+function cancelSavePreset() {
+    document.getElementById('preset-name-input-row')?.remove();
+}
+
+async function confirmSavePreset() {
+    const input = document.getElementById('preset-name-input');
+    const name = (input?.value || '').trim();
+    if (!name) { input?.focus(); return; }
+    cancelSavePreset();
+    const svc = VerificationFlow.selectedService;
+    try {
+        const token = localStorage.getItem('access_token');
+        const ac = document.getElementById('area-code-search-input')?.value || null;
+        const res = await fetch('/api/presets/', {
+            method: 'POST',
+            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
+            body: JSON.stringify({ name, service_id: svc, country_id: 'US', area_code: ac || null })
+        });
+        if (!res.ok) { const d = await res.json().catch(()=>({})); window.toast?.error(d.detail || 'Failed to save'); return; }
+        _presets.push(await res.json());
+        renderPresets();
+        window.toast?.success('Preset saved');
+    } catch(e) { window.toast?.error('Failed to save preset'); }
+}
```

**Verification**:
- [ ] Clicking "+ Save" shows an inline input row, not a browser prompt
- [ ] Enter key saves, Escape cancels
- [ ] Preset appears in the list after saving

---

### U4 — Fix i18n version as server-injected variable

**Problem**: `dashboard_base.html` has a hardcoded version string `'20260308j'` that forces
a hard page reload for any user on a new device. Updating it requires a template edit.

**Fix**: Inject the version from the server. In the route that renders dashboard pages,
add to context:

```python
context["i18n_version"] = settings.version  # e.g. "4.9.0"
```

In `templates/dashboard_base.html`:
```diff
-const I18N_FIX_VERSION = '20260308j';
+const I18N_FIX_VERSION = '{{ i18n_version }}';
```

Also update the `i18n.js` script tag to use the same token:
```diff
-<script src="/static/js/i18n.js?v=20260308j"></script>
+<script src="/static/js/i18n.js?v={{ asset_version }}"></script>
```

**Verification**:
- [ ] `I18N_FIX_VERSION` in page source matches current app version
- [ ] No forced reload on fresh dashboard visit after deploy

---

### U5 — Add spinner to "Get Number" button during verification

**Problem**: The "Get Number" button only changes text to "Creating..." with no visual spinner,
which looks frozen on slow connections.

**Fix** in `verification-flow.js` (after J1), update `createVerification()`:
```diff
-if (btn) { btn.disabled = true; btn.textContent = 'Creating...'; }
+if (btn) {
+    btn.disabled = true;
+    btn.innerHTML = '<span style="display:inline-block;width:14px;height:14px;border:2px solid rgba(255,255,255,0.4);border-top-color:white;border-radius:50%;animation:spin 0.8s linear infinite;margin-right:8px;vertical-align:middle;"></span>Creating...';
+}
```

On completion/error, restore:
```diff
-if (btn) { btn.disabled = false; btn.textContent = 'Get Number →'; }
+if (btn) { btn.disabled = false; btn.innerHTML = 'Get Number →'; }
```

**Verification**:
- [ ] Spinner appears inside button while verification is being created
- [ ] Button returns to normal text on success or error

---

## Category 4 — CSS / Design System

### C1 — Deduplicate cookie consent into a shared include

**Problem**: The cookie consent banner HTML and its JS functions are copy-pasted identically
in both `base.html` and `landing.html`. One change requires updating both files.

**Fix**: Create `templates/includes/cookie_consent.html`:

```html
<!-- Cookie Consent Banner -->
<div id="cookie-consent" style="display:none;position:fixed;bottom:0;left:0;right:0;background:#1f2937;color:white;padding:16px 24px;padding-bottom:calc(16px + env(safe-area-inset-bottom));z-index:9999;box-shadow:0 -4px 20px rgba(0,0,0,0.2);">
    <div style="max-width:1200px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;">
        <p style="margin:0;font-size:14px;flex:1;min-width:200px;">We use cookies to improve your experience. By continuing, you agree to our <a href="/cookies" style="color:#FE3C72;text-decoration:underline;">Cookie Policy</a>.</p>
        <div style="display:flex;gap:8px;">
            <button onclick="acceptCookies()" style="background:#FE3C72;color:white;border:none;padding:8px 20px;border-radius:6px;font-weight:600;cursor:pointer;font-size:14px;">Accept</button>
            <button onclick="declineCookies()" style="background:transparent;color:#9CA3AF;border:1px solid #4B5563;padding:8px 20px;border-radius:6px;font-weight:600;cursor:pointer;font-size:14px;">Decline</button>
        </div>
    </div>
</div>
<script>
(function() {
    if (!localStorage.getItem('cookie_consent')) {
        document.getElementById('cookie-consent').style.display = 'block';
    }
    // Load analytics if already consented
    if (localStorage.getItem('cookie_consent') === 'accepted') {
        if (!document.querySelector('script[src*="sabilytics"]')) {
            const s = document.createElement('script');
            s.async = true; s.src = 'https://www.sabilytics.com/script.js';
            s.dataset.site = 'ek3athooftac'; s.dataset.domain = 'vrenum.app';
            document.head.appendChild(s);
        }
    }
})();
function acceptCookies() {
    localStorage.setItem('cookie_consent', 'accepted');
    document.getElementById('cookie-consent').style.display = 'none';
    if (!document.querySelector('script[src*="sabilytics"]')) {
        const s = document.createElement('script');
        s.async = true; s.src = 'https://www.sabilytics.com/script.js';
        s.dataset.site = 'ek3athooftac'; s.dataset.domain = 'vrenum.app';
        document.head.appendChild(s);
    }
}
function declineCookies() {
    localStorage.setItem('cookie_consent', 'declined');
    document.getElementById('cookie-consent').style.display = 'none';
}
</script>
```

In `templates/base.html` and `templates/landing.html`, replace the inline cookie consent
block with:
```html
{% include "includes/cookie_consent.html" %}
```

**Verification**:
- [ ] Cookie banner appears on both landing and dashboard pages
- [ ] Accept/Decline work on both
- [ ] Only one copy of the code exists

---

### C2 — Add missing design system classes used by dashboard-ultra-stable

**Problem**: After J2 removes `injectStyles()`, two card classes used by the dashboard
modals (`type-card`, `upgrade-card`) won't have styles. Add them to `design-system.css`.

This is covered in J2 above — the CSS additions go into `design-system.css`.

No separate steps needed beyond what J2 specifies.

---

### C3 — Audit `glassmorphism.css` usage

**Problem**: `glassmorphism.css` is loaded on both landing and dashboard. Verify it's
actually used on both or remove the unused load.

**Fix**:
```bash
# Check which classes from glassmorphism.css are used in templates
grep -r "glass\|glassmorphism\|backdrop-filter" templates/ --include="*.html" | grep -v ".venv"
```

If only used on landing — remove from `dashboard.html`:
```diff
-<link rel="stylesheet" href="/static/css/glassmorphism.css?v=20260518">
```

If used on both — leave as-is.

**Verification**:
- [ ] No visual regressions after removing unused load

---

## Category 5 — Security / Correctness

### S1 — Sanitize `current_user.id` in GA4 template

**Problem**: `base.html` interpolates `current_user.id` directly into a JS string without
escaping. Safe for UUIDs but fragile.

**Fix** in `templates/base.html`:
```diff
-'user_id': '{{ current_user.id if current_user is defined and current_user else "" }}'
+'user_id': {{ (current_user.id if current_user is defined and current_user else "") | tojson }}
```

**Verification**:
- [ ] Page source shows `'user_id': "some-uuid"` with proper JSON encoding
- [ ] GA4 still receives user_id correctly

---

### S2 — Document JWT localStorage risk and migration path

**Problem**: `access_token` is stored in `localStorage` across the entire app. This is
vulnerable to XSS — any injected script can read it. The secure alternative is `httpOnly`
cookies set by the server.

**This is a larger architectural change** — do not implement in this sprint. Document it
as a tracked risk.

**Immediate mitigation** (already partially in place):
- CSP headers are active (via `SecurityHeadersMiddleware`) — reduces XSS surface
- XSS protection middleware is active
- Input sanitization utils exist in `app/utils/sanitization.py`

**Migration path for a future sprint**:
1. Add `Set-Cookie: access_token=...; HttpOnly; Secure; SameSite=Strict` on login response
2. Update all `fetch()` calls to use `credentials: 'include'` instead of `Authorization` header
3. Remove `localStorage.setItem('access_token', ...)` from auth flow
4. Update `auth-helpers.js` to read from cookie instead of localStorage

**Verification for this sprint**:
- [ ] This item is tracked in `docs/tasks/` as a future security sprint item
- [ ] No new `localStorage.setItem('access_token')` calls added in this sprint

---

## Execution Order

Tasks are grouped by dependency. All items within a group can run in parallel.

```
Sprint 1 — No-risk, isolated fixes (do these first):
  P2  Fix double dark-mode-universal.css load          (1 line delete)
  P5  Remove dead real-time-dashboard.js comment       (1 line delete + file delete)
  J4  Remove duplicate scroll-timeline.js              (grep + delete)
  J5  Remove/wire moduleLoader.js                      (grep + delete)
  S1  Sanitize current_user.id in GA4                  (1 line change)

Sprint 2 — Low-risk UX fixes:
  U1  Replace SW update confirm() with banner          (add function + modify handler)
  U2  Replace sidebar confirm() dialogs                (2 function changes)
  U3  Replace preset prompt() with inline input        (replace 1 function, add 2)
  U4  Fix i18n version as server-injected variable     (backend + template change)
  U5  Add spinner to Get Number button                 (2 line changes)

Sprint 3 — Medium effort, high impact:
  J2  Fix btn-primary color conflict                   (remove injectStyles + add CSS)
  C1  Deduplicate cookie consent into include          (new file + 2 template edits)
  C3  Audit glassmorphism.css usage                    (grep + conditional remove)
  P3  Defer analytics, load Sabilytics post-consent    (base.html + C1 dependency)
  P6  Move pwa-mobile.css out of public pages          (2 template edits)

Sprint 4 — Larger effort:
  J1  Extract verify page inline JS to file            (cut/paste + script tag)
  J3  Deduplicate getAuthToken/getAuthHeaders          (dashboard-ultra-stable.js)
  P4  Standardize cache-busting version tokens         (backend context + all templates)
  P1  Remove Tailwind CDN, use CLI build               (tailwind CLI setup + CI change)
```

---

## Completion Checklist

| ID | Task | Sprint | Status |
|---|---|---|---|
| P1 | Remove Tailwind CDN | 4 | ⏸️ (deferred — needs Node.js on CI) |
| P2 | Fix double dark-mode-universal.css | 1 | ✅ |
| P3 | Defer analytics / post-consent Sabilytics | 3 | ✅ |
| P4 | Standardize cache-busting tokens | 4 | ✅ |
| P5 | Remove dead real-time-dashboard.js | 1 | ✅ |
| P6 | Move pwa-mobile.css to dashboard only | 3 | ✅ |
| J1 | Extract verify inline JS to file | 4 | ✅ |
| J2 | Fix btn-primary color conflict | 3 | ✅ |
| J3 | Deduplicate auth helpers | 4 | ✅ |
| J4 | Remove duplicate scroll-timeline.js | 1 | ✅ |
| J5 | Remove/wire moduleLoader.js | 1 | ✅ (keep — used by main.js) |
| U1 | Replace SW update confirm() | 2 | ✅ |
| U2 | Replace sidebar confirm() dialogs | 2 | ✅ |
| U3 | Replace preset prompt() | 2 | ✅ |
| U4 | Fix i18n version server-injected | 2 | ✅ |
| U5 | Add spinner to Get Number button | 2 | ✅ |
| C1 | Deduplicate cookie consent | 3 | ✅ |
| C2 | Add missing design system classes | 3 | ✅ (part of J2) |
| C3 | Audit glassmorphism.css | 3 | ✅ (used on both — kept) |
| S1 | Sanitize user_id in GA4 | 1 | ✅ |
| S2 | Document JWT localStorage risk | — | ⏳ |

**Done when**: All Sprint 1–3 items complete. Sprint 4 items scheduled for next feature cycle.
