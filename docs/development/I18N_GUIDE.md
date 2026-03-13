# i18n Guide

**Status**: ✅ Implemented  
**Last Updated**: March 8, 2026

---

## How It Works

Translations use a 3-tier loading strategy to eliminate 502 errors and ensure instant loads:

1. **Embedded** — Server injects translations directly into HTML. Zero network requests, works on first visit.
2. **LocalStorage cache** — After first load, translations are cached for 24 hours. Instant on return visits.
3. **Server fetch** — Fallback with 3 retries if both above fail.

### Server side

```python
# app/api/main_routes.py
translations_json = get_translations_for_template(user_locale)
return templates.TemplateResponse("dashboard.html", {
    "translations": translations_json,
    "locale": user_locale
})
```

### Template

```html
<script>
window.EMBEDDED_TRANSLATIONS = {{ translations|safe }};
window.USER_LOCALE = "{{ locale }}";
</script>
<script src="/static/js/i18n.js?v=20260308j"></script>
```

---

## The Core Rule

**Never assign `textContent` or `innerHTML` directly to elements with `data-i18n` attributes.** It overwrites the translation and the element shows the raw key (e.g. `dashboard.title`) after the next translation pass.

### Static content — use `data-i18n` in HTML

```html
<h1 data-i18n="dashboard.title">Dashboard</h1>
```

### Dynamic content — remove `data-i18n` before updating

```javascript
// Option 1: Remove attribute
const el = document.getElementById('tier-name');
el.removeAttribute('data-i18n');
el.textContent = dynamicValue;

// Option 2: Use helper
import { setI18nContent } from '/static/js/i18n-helpers.js';
setI18nContent('tier-name', dynamicValue);
```

### Mixed content — label stays translated, value is dynamic

```html
<span data-i18n="common.balance">Balance</span>:
<span id="balance-value">$0.00</span>
```

---

## Helper Functions

```javascript
// Single element
setI18nContent('element-id', 'content');

// Multiple elements at once
updateMultiple({ 'tier-name': 'Pro', 'tier-price': '$25/month' });

// HTML with child translations
updateI18nHTML('container', '<div data-i18n="key">Text</div>');
```

---

## Debug

```javascript
window.i18n.loaded          // true if loaded
window.i18n.locale          // current language
window.i18n.translatePage() // force re-translate
window.i18nHelpers.debugI18nElements() // list all i18n elements
```

---

## Cache Management

Cache expires automatically after 24 hours. To force a refresh:

```javascript
localStorage.removeItem('translations_en');
localStorage.removeItem('translations_cached_at');
location.reload();
```

---

## Files

| File | Purpose |
|------|---------|
| `static/js/i18n.js` | Core i18n class, MutationObserver, `setContent()`, `setHTML()` |
| `static/js/i18n-helpers.js` | Helper utilities (`setI18nContent`, `updateMultiple`, etc.) |
| `app/utils/i18n.py` | Server-side translation loader with memory cache |
| `static/locales/*.json` | Translation files (en, es, fr, de, ar, hi, ja, pt, zh) |

---

## Known Gaps

- `activity_feed.js` and `real-time-dashboard.js` have bare `textContent` assignments — safe only because those elements have no `data-i18n`, but not formally audited.
- No pluralization support yet.
- No lazy loading (all translations loaded upfront).
