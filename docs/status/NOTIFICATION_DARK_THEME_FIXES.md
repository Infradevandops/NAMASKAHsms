# Notification & Dark Theme Fix Tasks

**Created**: October 26, 2026
**Status**: All items unresolved — previous fixes did not deploy correctly or had root causes not addressed
**Priority**: P1 — visible to all users on dashboard

---

## Root Cause Summary (Diagnosed)

Before fixing anything, understand why the previous session's fixes didn't work:

| Fix attempted | Why it didn't work |
|---|---|
| `theme-manager.js` sets `data-theme="dark"` | `theme-manager.js` is only loaded in `info.html` — **not in `dashboard_base.html`**. So on the dashboard, `applyTheme()` never runs. |
| `notification-improvements.css` dark mode via `[data-theme="dark"]` | Correct selectors, but `data-theme` is never set on dashboard pages (see above). |
| `notification_center_modal.css` dark mode via `html.dark-mode` | `html.dark-mode` class IS set by... nothing on the dashboard either — `theme-manager.js` isn't loaded. |
| Dropdown `position: fixed` | This fix is correct and should work once deployed. Verify it's live. |
| `openVerificationModal()` fallback to `/verify` | This fix is correct. Verify it's live. |

---

## Task 1 — Load `theme-manager.js` on Dashboard

**File**: `templates/dashboard_base.html`
**Problem**: `theme-manager.js` is only loaded in `info.html`. The dashboard never sets `data-theme` or `html.dark-mode` class, so all dark theme CSS is dead.
**Fix**: Add `<script src="/static/js/theme-manager.js"></script>` to the `{% block scripts %}` section of `dashboard_base.html`, **before** `notification-system.js`.

```html
<!-- In templates/dashboard_base.html, scripts block -->
<script src="/static/js/theme-manager.js"></script>
<script src="/static/js/notification-system.js"></script>
```

**Acceptance criteria**:
1. Open dashboard in dark mode (toggle dark mode if needed)
2. Inspect `<html>` in DevTools → must have both `class="dark-mode"` AND `data-theme="dark"`
3. If `data-theme="dark"` is present, all `[data-theme="dark"]` CSS in `notification-improvements.css` and `dark-mode-universal.css` will apply automatically

---

## Task 2 — Notification Dropdown Dark Theme

**Files**: `static/css/notification-improvements.css`
**Problem**: `.notification-dropdown` background is hardcoded `background: white`. The `[data-theme="dark"]` override exists in the file but only works after Task 1 is done (theme-manager must be loaded).
**Dependency**: Task 1 must be done first.

**Verify after Task 1**:
1. Open dashboard in dark mode
2. Click the bell icon
3. Dropdown background must be dark (`#1e293b` / `var(--gray-800)`) — not white
4. Dropdown arrow (`::before` pseudo-element) must also be dark
5. Notification items must have dark text and dark borders

**If still broken after Task 1**, the CSS variable `--gray-800` may not be defined in dark mode scope. Check `dark-mode-universal.css` for `--gray-800` definition under `[data-theme="dark"]`. If missing, add explicit hex fallbacks to the selectors in `notification-improvements.css`:

```css
[data-theme="dark"] .notification-dropdown {
    background: #1e293b;  /* explicit fallback if var not defined */
    border-color: #334155;
}
```

**Acceptance criteria**:
1. Bell dropdown opens with dark background in dark mode
2. Header section (`.dropdown-header`) is darker than the list area
3. Notification item text is light-colored, not black-on-dark
4. Dropdown arrow matches the dropdown background color
5. In light mode, dropdown is still white — no regression

---

## Task 3 — Notification Center Modal Dark Theme

**File**: `static/css/notification_center_modal.css`
**Problem**: Modal uses `html.dark-mode` selectors (already added). These will work once Task 1 is done since `theme-manager.js` adds both the class and `data-theme` attribute.
**Dependency**: Task 1 must be done first.

**Verify after Task 1**:
1. Open dashboard in dark mode
2. Click bell → click "View All" (or whatever opens `#notification-center-modal`)
3. The slide-in panel must have dark background, not white
4. Sidebar, toolbar, list items all dark

**Acceptance criteria**:
1. `.notification-modal-panel` background is dark (`#1e2433`)
2. `.notification-modal-sidebar` background is darker (`#151b2d`)
3. All text is light-colored
4. Borders use dark color (`#2d3748`)
5. Search input has dark background
6. In light mode, modal is still white — no regression

---

## Task 4 — Notification Dropdown Position (Verify Deploy)

**File**: `static/css/notification-improvements.css`
**Problem**: Previous fix changed `.notification-dropdown` to `position: fixed; top: 68px; right: 16px; z-index: 9999`. This is correct but needs to be verified as live.

**Verify**:
1. Open dashboard
2. Click bell icon
3. Scroll the page up and down while dropdown is open
4. Dropdown must stay fixed at top-right — it must NOT scroll with the page
5. Dropdown must NOT be clipped by the header

**If still broken** (dropdown clipped or scrolls), confirm the CSS in production matches:
```css
.notification-dropdown {
    position: fixed;
    top: 68px;
    right: 16px;
    z-index: 9999;
    /* NOT position: absolute */
}
```

**Acceptance criteria**:
1. Dropdown appears at top-right of viewport, not clipped
2. Dropdown stays in place when page is scrolled
3. Dropdown appears above all other elements (z-index working)
4. On mobile (< 768px), dropdown width is `calc(100vw - 32px)` and still visible

---

## Task 5 — "New Verification" Button (Verify Deploy)

**File**: `static/js/dashboard.js`
**Problem**: Previous fix added fallback `window.location.href = '/verify'` when `#verification-modal` not found. Needs to be verified as live.

**Verify**:
1. Open dashboard
2. Click "New Verification" button (or "Quick Verification" button)
3. Must navigate to `/verify` page — no JS error, no silent fail

**If still broken**, check `dashboard.js` `openVerificationModal()` function contains:
```js
function openVerificationModal() {
  const modal = document.getElementById('verification-modal');
  if (modal) {
    // ... modal logic
  } else {
    window.location.href = '/verify';
  }
}
```

**Acceptance criteria**:
1. Clicking "New Verification" navigates to `/verify`
2. No JS console errors on click
3. Browser console does NOT show `Cannot read properties of null` errors

---

## Task 6 — Duplicate Notifications (Redis Distributed Lock)

**Files**: `app/services/sms_polling_service.py` (or wherever timeout handling lives)
**Problem**: Two gunicorn workers both catch the same verification timeout → both fire "Still Waiting" and "Verification Timeout - Refunded" notifications. User sees duplicates.

**Fix**: Wrap the timeout handler in a Redis distributed lock using a key like `lock:verification_timeout:{verification_id}` with a short TTL (e.g. 30s). Only the worker that acquires the lock processes the timeout.

```python
lock_key = f"lock:verification_timeout:{verification_id}"
acquired = await redis.set(lock_key, "1", nx=True, ex=30)
if not acquired:
    return  # another worker is handling this
# ... process timeout, send notification, issue refund
```

**Acceptance criteria**:
1. Trigger a verification timeout (wait for a real one, or mock it in a test)
2. Only ONE "Still Waiting" notification appears in the bell dropdown
3. Only ONE "Verification Timeout - Refunded" notification appears
4. Redis key `lock:verification_timeout:{id}` exists briefly then expires
5. Unit test: mock two concurrent calls to the timeout handler with same verification ID → assert notification service called exactly once

---

## Task 7 — `/api/notifications/categories` 405 Error

**Problem**: Something is calling `GET /api/notifications/categories` but the endpoint returns 405 (Method Not Allowed), meaning it either expects POST or doesn't exist.

**Diagnose first**:
```bash
grep -rn "notifications/categories" app/api/
grep -rn "notifications/categories" static/js/
```

**Fix options**:
- If the endpoint exists but is POST-only and the JS is calling GET → change the JS call to POST
- If the endpoint doesn't exist → add it as GET, or remove the JS call if it's unused

**Acceptance criteria**:
1. No 405 errors in browser network tab for `/api/notifications/categories`
2. If the endpoint is used, it returns valid category data
3. If the endpoint is unused, the JS call is removed

---

## Testing Checklist (Run After All Fixes)

Run these manually in the browser after deploying all fixes:

```
[ ] 1. Toggle dark mode on dashboard → html element has data-theme="dark" AND class="dark-mode"
[ ] 2. Bell dropdown opens with dark background in dark mode
[ ] 3. Bell dropdown opens with white background in light mode (no regression)
[ ] 4. Notification center modal (View All) is dark in dark mode
[ ] 5. Dropdown stays fixed at top-right when scrolling
[ ] 6. Dropdown is not clipped by header
[ ] 7. "New Verification" button navigates to /verify
[ ] 8. No JS console errors on dashboard load
[ ] 9. No 405 errors in network tab
[ ] 10. Duplicate notifications do not appear for same verification timeout
```

---

## Deploy Order

1. Task 1 (theme-manager in dashboard_base.html) — unblocks Tasks 2, 3
2. Tasks 2, 3 — verify dark theme works after Task 1
3. Tasks 4, 5 — verify previous fixes are live
4. Task 7 — quick fix, independent
5. Task 6 — Redis lock, most complex, do last
