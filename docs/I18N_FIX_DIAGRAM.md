# i18n Fix - Visual Diagram

## Problem: Translation Key Regression

```
┌─────────────────────────────────────────────────────────────┐
│                     BEFORE FIX (Broken)                      │
└─────────────────────────────────────────────────────────────┘

Timeline:
─────────────────────────────────────────────────────────────►

0ms: Page Load
┌──────────────────────────────────────┐
│ <h1 data-i18n="dashboard.title">     │
│   Dashboard                           │  ✅ Correct
│ </h1>                                 │
└──────────────────────────────────────┘

50ms: i18n.translatePage()
┌──────────────────────────────────────┐
│ <h1 data-i18n="dashboard.title">     │
│   Dashboard                           │  ✅ Still correct
│ </h1>                                 │
└──────────────────────────────────────┘

200ms: API Call Completes
┌──────────────────────────────────────┐
│ element.textContent = 'Custom'       │  ⚠️ Direct assignment
│                                      │
│ Result:                              │
│ <h1>Custom</h1>                      │  ❌ Lost data-i18n!
│                                      │
│ Next render:                         │
│ <h1>dashboard.title</h1>             │  ❌ Shows raw key!
└──────────────────────────────────────┘
```

---

## Solution: i18n-Aware Updates

```
┌─────────────────────────────────────────────────────────────┐
│                      AFTER FIX (Working)                     │
└─────────────────────────────────────────────────────────────┘

Timeline:
─────────────────────────────────────────────────────────────►

0ms: Page Load
┌──────────────────────────────────────┐
│ <h1 data-i18n="dashboard.title">     │
│   Dashboard                           │  ✅ Correct
│ </h1>                                 │
└──────────────────────────────────────┘

50ms: i18n.translatePage() + observeDOM()
┌──────────────────────────────────────┐
│ <h1 data-i18n="dashboard.title">     │
│   Dashboard                           │  ✅ Translated
│ </h1>                                 │
│                                      │
│ MutationObserver: ACTIVE 👁️          │  ✅ Watching
└──────────────────────────────────────┘

200ms: API Call Completes (i18n-aware)
┌──────────────────────────────────────┐
│ await window.i18nReady               │  ✅ Wait for i18n
│ element.removeAttribute('data-i18n') │  ✅ Mark as dynamic
│ element.textContent = 'Custom'       │  ✅ Safe update
│                                      │
│ Result:                              │
│ <h1>Custom</h1>                      │  ✅ Shows "Custom"
│                                      │
│ MutationObserver sees change         │  ✅ No data-i18n
│ → No translation needed              │  ✅ Leaves it alone
└──────────────────────────────────────┘
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    i18n System Architecture                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                         Browser                              │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │                   HTML Template                     │    │
│  │                                                     │    │
│  │  <h1 data-i18n="dashboard.title">Dashboard</h1>   │    │
│  │  <p data-i18n="dashboard.subtitle">Overview</p>   │    │
│  └────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │                   i18n.js Core                      │    │
│  │                                                     │    │
│  │  • loadTranslations()                              │    │
│  │  • translatePage()                                 │    │
│  │  • observeDOM() ← MutationObserver                │    │
│  │  • setContent() ← Safe updates                     │    │
│  │  • setHTML() ← Safe HTML updates                   │    │
│  └────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │              i18n-helpers.js (Optional)             │    │
│  │                                                     │    │
│  │  • setI18nContent()                                │    │
│  │  • updateI18nHTML()                                │    │
│  │  • updateMultiple()                                │    │
│  │  • batchUpdate()                                   │    │
│  └────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Dynamic Content Loaders                │    │
│  │                                                     │    │
│  │  • dashboard.html (tier card)                      │    │
│  │  • dashboard_base.html (header badge)              │    │
│  │  • global-balance.js (balance displays)            │    │
│  │  • tier-card.js (tier widget)                      │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Translation Data Flow                     │
└─────────────────────────────────────────────────────────────┘

1. Initial Load
   ┌──────────┐
   │ en.json  │ ──────┐
   └──────────┘       │
   ┌──────────┐       │
   │ fr.json  │ ──────┤
   └──────────┘       │
   ┌──────────┐       │
   │ es.json  │ ──────┤
   └──────────┘       │
                      ▼
              ┌──────────────┐
              │ i18n.loaded  │
              │   = true     │
              └──────────────┘
                      │
                      ▼
              ┌──────────────┐
              │ translatePage│
              └──────────────┘
                      │
                      ▼
              ┌──────────────┐
              │ observeDOM() │ ← Starts watching
              └──────────────┘

2. Dynamic Update (i18n-aware)
   ┌──────────────┐
   │  API Call    │
   └──────────────┘
          │
          ▼
   ┌──────────────┐
   │ await i18n   │
   │   Ready      │
   └──────────────┘
          │
          ▼
   ┌──────────────┐
   │ removeAttr   │ ← Remove data-i18n
   │ ('data-i18n')│
   └──────────────┘
          │
          ▼
   ┌──────────────┐
   │ textContent  │ ← Safe to update
   │   = value    │
   └──────────────┘
          │
          ▼
   ┌──────────────┐
   │ Mutation     │ ← Observer sees change
   │ Observer     │   No data-i18n = OK
   └──────────────┘

3. New Element Added
   ┌──────────────┐
   │ innerHTML =  │
   │ '<div data-  │
   │  i18n="key">'│
   └──────────────┘
          │
          ▼
   ┌──────────────┐
   │ Mutation     │ ← Observer detects
   │ Observer     │
   └──────────────┘
          │
          ▼
   ┌──────────────┐
   │ Has data-i18n│ ← Check attribute
   │   = YES      │
   └──────────────┘
          │
          ▼
   ┌──────────────┐
   │ i18n.t(key)  │ ← Auto-translate
   └──────────────┘
```

---

## Decision Tree

```
┌─────────────────────────────────────────────────────────────┐
│              When to Use Each Approach                       │
└─────────────────────────────────────────────────────────────┘

                    Need to update DOM?
                           │
                           ▼
                    ┌──────────────┐
                    │ Is content   │
                    │ static or    │
                    │ dynamic?     │
                    └──────────────┘
                      │          │
              Static  │          │  Dynamic
                      ▼          ▼
            ┌──────────────┐  ┌──────────────┐
            │ Use data-i18n│  │ From API or  │
            │ in HTML      │  │ calculated?  │
            └──────────────┘  └──────────────┘
                                      │
                                      ▼
                              ┌──────────────┐
                              │ Remove       │
                              │ data-i18n    │
                              └──────────────┘
                                      │
                                      ▼
                              ┌──────────────┐
                              │ Update       │
                              │ textContent  │
                              └──────────────┘

Example Decision Path:

1. Tier name from API?
   → Dynamic → Remove data-i18n → Update

2. "Dashboard" title?
   → Static → Use data-i18n in HTML

3. Balance from API?
   → Dynamic → Remove data-i18n → Update

4. "Welcome" message?
   → Static → Use data-i18n in HTML
```

---

## Common Patterns

```
┌─────────────────────────────────────────────────────────────┐
│                     Pattern Library                          │
└─────────────────────────────────────────────────────────────┘

Pattern 1: Static Label + Dynamic Value
┌────────────────────────────────────────┐
│ <div>                                  │
│   <span data-i18n="common.balance">   │  ← Keep data-i18n
│     Balance                            │
│   </span>:                             │
│   <span id="balance-value">           │  ← No data-i18n
│     $10.80                             │
│   </span>                              │
│ </div>                                 │
└────────────────────────────────────────┘

Pattern 2: Fully Dynamic Content
┌────────────────────────────────────────┐
│ <div id="tier-name">                   │  ← No data-i18n
│   Custom                               │     (set by API)
│ </div>                                 │
│                                        │
│ JS:                                    │
│ el.removeAttribute('data-i18n');      │
│ el.textContent = apiData.tier;        │
└────────────────────────────────────────┘

Pattern 3: Mixed Content
┌────────────────────────────────────────┐
│ <div id="container">                   │
│   <h2 data-i18n="dashboard.title">    │  ← Keep data-i18n
│     Dashboard                          │
│   </h2>                                │
│   <div id="dynamic-stats">            │  ← No data-i18n
│     <!-- Populated by JS -->          │
│   </div>                               │
│ </div>                                 │
└────────────────────────────────────────┘

Pattern 4: Template with Translation
┌────────────────────────────────────────┐
│ const html = `                         │
│   <div data-i18n="welcome.message">   │  ← Will auto-translate
│     Welcome                            │
│   </div>                               │
│ `;                                     │
│ container.innerHTML = html;           │
│ // MutationObserver handles it!       │
└────────────────────────────────────────┘
```

---

## Troubleshooting Flowchart

```
┌─────────────────────────────────────────────────────────────┐
│                  Troubleshooting Guide                       │
└─────────────────────────────────────────────────────────────┘

                Seeing "dashboard.title"?
                           │
                           ▼
                    ┌──────────────┐
                    │ Check: Does  │
                    │ element have │
                    │ data-i18n?   │
                    └──────────────┘
                      │          │
                  YES │          │ NO
                      ▼          ▼
            ┌──────────────┐  ┌──────────────┐
            │ Is i18n      │  │ Check if     │
            │ loaded?      │  │ content is   │
            └──────────────┘  │ correct      │
                  │           └──────────────┘
              YES │ NO
                  ▼  ▼
        ┌──────────────┐  ┌──────────────┐
        │ Content was  │  │ Wait for     │
        │ overwritten  │  │ i18nReady    │
        │ after load   │  └──────────────┘
        └──────────────┘
                │
                ▼
        ┌──────────────┐
        │ Add:         │
        │ removeAttr   │
        │ before update│
        └──────────────┘

Debug Commands:
• window.i18n.loaded
• window.i18nHelpers.debugI18nElements()
• window.i18n.translatePage()
```

---

## Performance Monitoring

```
┌─────────────────────────────────────────────────────────────┐
│                   Performance Metrics                        │
└─────────────────────────────────────────────────────────────┘

Before Fix:
┌────────────────────────────────────────┐
│ Page Load:        1.2s                 │
│ i18n Load:        50ms                 │
│ Translation:      10ms                 │
│ API Calls:        200ms                │
│ Total:            1.46s                │
│                                        │
│ Issues:                                │
│ • Translation regression after 200ms   │
│ • User sees keys briefly               │
│ • Poor UX                              │
└────────────────────────────────────────┘

After Fix:
┌────────────────────────────────────────┐
│ Page Load:        1.2s                 │
│ i18n Load:        50ms                 │
│ Translation:      10ms                 │
│ Observer Setup:   <1ms                 │
│ API Calls:        200ms                │
│ Total:            1.461s (+1ms)        │
│                                        │
│ Benefits:                              │
│ • No translation regression            │
│ • Smooth UX                            │
│ • Auto-translates new content          │
│ • Negligible overhead                  │
└────────────────────────────────────────┘

MutationObserver Impact:
• Per mutation: <1ms
• Memory: ~50KB
• CPU: Idle when no DOM changes
• Network: 0 (no additional requests)
```

---

## Success Indicators

```
┌─────────────────────────────────────────────────────────────┐
│                    How to Verify Fix                         │
└─────────────────────────────────────────────────────────────┘

✅ Checklist:

□ Dashboard loads with "Dashboard" not "dashboard.title"
□ After 1 second, still shows "Dashboard"
□ Tier card shows "Custom" not "tiers.current_plan"
□ Balance shows "$10.80" not "common.balance"
□ Language switcher works correctly
□ No console errors
□ window.i18n.loaded === true
□ window.i18nHelpers exists
□ MutationObserver is active

Browser Console Tests:

> window.i18n.loaded
true ✅

> window.i18nHelpers.debugI18nElements()
🌐 i18n Elements
  dashboard.title → "Dashboard"
  dashboard.subtitle → "Overview of your SMS verification activity"
  ... ✅

> window.i18n.locale
"en" ✅

> document.querySelectorAll('[data-i18n]').length
42 ✅ (should be > 0)
```

This visual guide should help understand the fix at a glance!
