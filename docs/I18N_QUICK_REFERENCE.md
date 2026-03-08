# i18n Quick Reference Card

## 🚨 Golden Rule

**Never directly assign `textContent` or `innerHTML` to elements with `data-i18n` attributes!**

---

## ✅ DO THIS

### Static Content (HTML)
```html
<h1 data-i18n="dashboard.title">Dashboard</h1>
<p data-i18n="dashboard.subtitle">Overview</p>
```

### Dynamic Content (JavaScript)

#### Option 1: Remove data-i18n
```javascript
const el = document.getElementById('tier-name');
el.removeAttribute('data-i18n');
el.textContent = dynamicValue;
```

#### Option 2: Use Helpers
```javascript
import { setI18nContent } from '/static/js/i18n-helpers.js';
setI18nContent('tier-name', dynamicValue);
```

#### Option 3: Wait for i18n
```javascript
await window.i18nReady;
const el = document.getElementById('welcome');
el.setAttribute('data-i18n', 'dashboard.welcome');
el.textContent = window.i18n.t('dashboard.welcome');
```

---

## ❌ DON'T DO THIS

```javascript
// ❌ BAD: Overwrites translation
document.getElementById('tier-name').textContent = 'Pro';

// ❌ BAD: Doesn't preserve data-i18n
element.innerHTML = '<div>Content</div>';

// ❌ BAD: Not waiting for i18n
element.textContent = i18n.t('key'); // i18n might not be loaded
```

---

## 🛠️ Helper Functions

```javascript
// Single element
setI18nContent('element-id', 'content');

// Multiple elements
updateMultiple({
    'tier-name': 'Pro',
    'tier-price': '$25/month'
});

// HTML with child translations
updateI18nHTML('container', '<div data-i18n="key">Text</div>');

// Batch update with options
batchUpdate([
    { id: 'name', content: 'John', removeI18n: true },
    { id: 'welcome', translationKey: 'dashboard.welcome' }
]);
```

---

## 🐛 Debug Commands

```javascript
// Check if loaded
window.i18n.loaded

// List all i18n elements
window.i18nHelpers.debugI18nElements()

// Force re-translate
window.i18n.translatePage()

// Current language
window.i18n.locale
```

---

## 📋 Checklist for New Features

- [ ] Does element have `data-i18n`?
- [ ] Will content be updated dynamically?
- [ ] If yes, remove `data-i18n` before update
- [ ] Or use helper functions
- [ ] Test with language switcher
- [ ] Verify no "key.name" showing in UI

---

## 🔗 Full Documentation

See `docs/I18N_IMPLEMENTATION_GUIDE.md` for complete details.
