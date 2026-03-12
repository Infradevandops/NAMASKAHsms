# Verification Flow — Implementation Tasks

**Version**: v4.2.0 target  
**Date**: March 12, 2026  
**Scope**: All remaining tasks to complete the verification flow to full vision  
**Color Scheme**: Red/Tinder red (#E8003D) primary, Gold (#F5A623) accents for modals/inner elements

---

## Task Overview

| # | Task | Priority | Effort | Status |
|---|------|----------|--------|--------|
| 1 | Remove 5s timeout — instant load from cache | Critical | 5 min | Pending |
| 2 | Remove loading spinner / disabled input state | Critical | 5 min | Pending |
| 3 | Replace inline dropdown with full-screen gold modal | Critical | 4-6 hrs | Pending |
| 4 | Add remaining 31 service logos (63% → 100%) | High | 1 hr | Pending |
| 5 | Refactor to VerificationFlow controller | High | 2-3 hrs | Pending |
| 6 | Remove dead picker-modal code | Medium | 30 min | Pending |
| 7 | Optimize search to <16ms | Medium | 1 hr | Pending |
| 8 | Add error boundaries | Medium | 1 hr | Pending |
| 9 | Run existing 55 tests | High | 30 min | Pending |
| 10 | Fix freemium upsell colors to match brand | Low | 15 min | Pending |

---

## Task 1 — Remove 5s Timeout (Instant Load from Cache)

**File**: `templates/verify_modern.html`  
**Problem**: ServiceStore.init() returns instantly from cache but we wrap it in a 5s timeout, blocking the page unnecessarily.  
**Impact**: Page load goes from <5s to <50ms on repeat visits.

**Current code** (DOMContentLoaded, ~line 1016):
```js
// Show loading indicator
const serviceInput = document.getElementById('service-search-input');
const spinner = document.getElementById('service-loading-spinner');
if (serviceInput && spinner) {
    serviceInput.disabled = true;
    serviceInput.placeholder = 'Loading services...';
    spinner.style.display = 'block';
}

// Load services first (critical path)
await loadServices();

// Enable input
if (serviceInput && spinner) {
    serviceInput.disabled = false;
    serviceInput.placeholder = 'Search services e.g. Telegram, WhatsApp...';
    spinner.style.display = 'none';
}
```

**Current loadServices()** wraps with 5s timeout:
```js
await Promise.race([
    window.ServiceStore.init(),
    new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 5000))
]);
```

**Replace with**:
```js
// Services load instantly from cache — no spinner, no disabled state
await window.ServiceStore.init();
const services = window.ServiceStore.getAll();
if (services && services.length >= 20) {
    _modalItems['service'] = _buildServiceItems(services);
} else {
    _modalItems['service'] = _buildServiceItems(FALLBACK_SERVICES);
}

window.ServiceStore.subscribe((updated) => {
    if (updated && updated.length >= 20) {
        _modalItems['service'] = _buildServiceItems(updated);
    }
});
```

**DOMContentLoaded becomes**:
```js
document.addEventListener('DOMContentLoaded', async () => {
    await loadServices();                          // instant from cache
    Promise.all([loadTier(), loadBalance()]);      // parallel, non-blocking
    updateProgress(1);

    const preService = new URLSearchParams(window.location.search).get('service');
    if (preService) _preselectService(preService);
});
```

---

## Task 2 — Remove Loading Spinner / Disabled Input

**File**: `templates/verify_modern.html`  
**Problem**: Input is disabled and shows spinner while services load. With Task 1 done, services are instant — no spinner needed.  
**Impact**: Input is always interactive. No perceived delay.

Remove from HTML:
```html
<!-- REMOVE this spinner span entirely -->
<span id="service-loading-spinner" style="display:none; position:absolute; right:10px; ..."></span>
```

Remove from JS — all references to:
- `service-loading-spinner`
- `serviceInput.disabled = true`
- `serviceInput.placeholder = 'Loading services...'`

The input placeholder stays as `Search services e.g. Telegram, WhatsApp...` at all times.

---

## Task 3 — Full-Screen Service Modal (Gold Theme)

**File**: `templates/verify_modern.html`  
**Problem**: Inline dropdown shows max 12 services, light theme, not immersive.  
**Target**: Full-screen modal overlay, gold theme, shows all 84+ services, fixed search bar, pinned section.

### Color Tokens
```
Modal background:  #1C0A00  (very dark warm brown — feels premium, not cold dark)
Modal border:      #3D1F00
Header bg:         #2A1000
Search bg:         #0F0500
Search border:     #5C3000
Section label:     #F5A623  (gold)
Service name:      #FFF8F0  (warm white)
Service price:     #F5A623  (gold)
Pin active:        #F5A623  (gold)
Pin inactive:      #5C3000
Row hover:         #2A1000
Row border:        #2A1000
Overlay:           rgba(0,0,0,0.75)
Close button:      #F5A623
Scrollbar thumb:   #5C3000
```

### HTML — Replace inline dropdown trigger

**Remove** the current `service-inline-dropdown` div and replace the input's `onfocus`/`oninput` with modal trigger:

```html
<!-- Step 1: Service Selection -->
<div class="form-group">
    <label class="form-label">Service <span class="required">*</span></label>
    
    <!-- Trigger button — shows selected service or placeholder -->
    <div id="service-trigger" onclick="openServiceModal()"
        style="width:100%; padding:10px 14px; border:1px solid var(--border-color,#e5e7eb);
               border-radius:8px; font-size:14px; cursor:pointer; display:flex;
               align-items:center; justify-content:space-between; background:#fff;
               box-sizing:border-box; min-height:42px;">
        <div id="service-trigger-content" style="display:flex; align-items:center; gap:10px; color:#9ca3af;">
            <span>Search services e.g. Telegram, WhatsApp...</span>
        </div>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
        </svg>
    </div>
</div>

<!-- Full-Screen Service Modal -->
<div id="service-modal" onclick="if(event.target===this)closeServiceModal()"
    style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.75);
           z-index:9999; align-items:center; justify-content:center;">
    <div style="background:#1C0A00; border:1px solid #3D1F00; border-radius:16px;
                width:min(560px,95vw); max-height:85vh; display:flex; flex-direction:column;
                overflow:hidden; box-shadow:0 24px 64px rgba(0,0,0,0.6);">
        
        <!-- Header -->
        <div style="padding:18px 24px; background:#2A1000; border-bottom:1px solid #3D1F00;
                    display:flex; justify-content:space-between; align-items:center; flex-shrink:0;">
            <span style="color:#FFF8F0; font-size:16px; font-weight:600;">Select Service</span>
            <button onclick="closeServiceModal()"
                style="background:none; border:none; color:#F5A623; font-size:22px;
                       cursor:pointer; line-height:1; padding:0 4px;">&times;</button>
        </div>
        
        <!-- Search bar (fixed, not scrollable) -->
        <div style="padding:14px 20px; background:#2A1000; border-bottom:1px solid #3D1F00; flex-shrink:0;">
            <input type="text" id="modal-service-search"
                placeholder="Search services..."
                oninput="renderServiceModal(this.value)"
                style="width:100%; padding:10px 14px; background:#0F0500; border:1px solid #5C3000;
                       border-radius:8px; color:#FFF8F0; font-size:14px; box-sizing:border-box;
                       outline:none;"
                autocomplete="off" />
        </div>
        
        <!-- Scrollable service list -->
        <div id="modal-service-list"
            style="overflow-y:auto; flex:1; padding:8px 0;
                   scrollbar-width:thin; scrollbar-color:#5C3000 #1C0A00;">
        </div>
    </div>
</div>
```

### JS — Modal open/close/render

```js
function openServiceModal() {
    document.getElementById('service-modal').style.display = 'flex';
    renderServiceModal('');
    setTimeout(() => document.getElementById('modal-service-search').focus(), 50);
}

function closeServiceModal() {
    document.getElementById('service-modal').style.display = 'none';
    document.getElementById('modal-service-search').value = '';
}

function renderServiceModal(q) {
    const list = document.getElementById('modal-service-list');
    const all = (_modalItems['service'] || []).filter(i => i.value !== '__other__');
    const favIds = getFavorites();

    const filtered = q
        ? all.filter(i => i.label.toLowerCase().includes(q.toLowerCase()))
        : all;

    const pinned = filtered.filter(i => favIds.includes(i.value));
    const rest = filtered.filter(i => !favIds.includes(i.value));

    let html = '';

    if (pinned.length && !q) {
        html += `<div style="padding:6px 20px 4px; font-size:11px; font-weight:700;
                             color:#F5A623; letter-spacing:0.8px;">PINNED (${pinned.length})</div>`;
        html += pinned.map(i => _modalServiceRow(i, favIds)).join('');
        html += `<div style="height:1px; background:#3D1F00; margin:8px 0;"></div>`;
    }

    if (rest.length) {
        html += `<div style="padding:6px 20px 4px; font-size:11px; font-weight:700;
                             color:#F5A623; letter-spacing:0.8px;">
                    ALL SERVICES (${rest.length})
                 </div>`;
        html += rest.map(i => _modalServiceRow(i, favIds)).join('');
    }

    if (!filtered.length) {
        html = `<div style="padding:40px 20px; text-align:center; color:#5C3000; font-size:14px;">
                    No services found
                </div>`;
    }

    list.innerHTML = html;
}

function _modalServiceRow(item, favIds) {
    const isFav = favIds.includes(item.value);
    const iconUrl = _getServiceIcon(item.value);
    const safeVal = item.value.replace(/'/g, "\\'");
    const q = document.getElementById('modal-service-search')?.value || '';
    return `
        <div style="display:flex; align-items:center; padding:12px 20px; cursor:pointer;
                    border-bottom:1px solid #2A1000; transition:background 0.12s;"
             onmouseover="this.style.background='#2A1000'"
             onmouseout="this.style.background=''"
             onclick="selectServiceFromModal('${safeVal}')">
            <img src="${iconUrl}" width="28" height="28"
                 style="border-radius:6px; object-fit:contain; margin-right:12px; flex-shrink:0;"
                 onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%2228%22 height=%2228%22 viewBox=%220 0 24 24%22 fill=%22none%22 stroke=%22%23F5A623%22 stroke-width=%221.5%22%3E%3Ccircle cx=%2212%22 cy=%2212%22 r=%2210%22/%3E%3C/svg%3E'"
                 alt="">
            <span style="flex:1; color:#FFF8F0; font-size:14px; font-weight:500;">${item.label}</span>
            <span style="color:#F5A623; font-size:13px; font-weight:600; margin-right:16px;">${item.sub || ''}</span>
            <button onclick="event.stopPropagation(); _togglePinFromModal('${safeVal}', '${q}');"
                style="background:none; border:none; cursor:pointer; font-size:18px; padding:4px;
                       color:${isFav ? '#F5A623' : '#5C3000'}; transition:color 0.15s; flex-shrink:0;"
                onmouseover="this.style.color='#F5A623'"
                onmouseout="this.style.color='${isFav ? '#F5A623' : '#5C3000'}'">&#128204;</button>
        </div>`;
}

function _togglePinFromModal(serviceId, q) {
    toggleFavorite(serviceId);
    renderServiceModal(q);
}

function selectServiceFromModal(value) {
    const items = _modalItems['service'] || [];
    const item = items.find(i => i.value === value);
    if (!item) return;

    selectedService = value;
    selectedServicePrice = item.price || null;

    // Update trigger button to show selected service
    const iconUrl = _getServiceIcon(value);
    document.getElementById('service-trigger-content').innerHTML = `
        <img src="${iconUrl}" width="22" height="22"
             style="border-radius:4px; object-fit:contain;"
             onerror="this.style.display='none'" alt="">
        <span style="color:#111827; font-weight:500;">${item.label}</span>
        <span style="color:#6b7280; font-size:13px; margin-left:4px;">${item.sub || ''}</span>
        <button onclick="event.stopPropagation(); clearServiceSelection();"
            style="background:none; border:none; color:#9ca3af; cursor:pointer;
                   font-size:16px; margin-left:auto; padding:0 4px; line-height:1;">&#x2715;</button>
    `;

    document.getElementById('continue-btn').disabled = false;
    updatePricing();

    const rank = TIER_RANK[userTier] || 0;
    document.getElementById('advanced-options-section').style.display = rank >= 1 ? 'block' : 'none';
    document.getElementById('freemium-upsell').style.display = rank < 1 ? 'block' : 'none';

    closeServiceModal();
}
```

### CSS — Scrollbar styling + modal search focus

Add inside `<style>` block:
```css
#modal-service-list::-webkit-scrollbar { width: 6px; }
#modal-service-list::-webkit-scrollbar-track { background: #1C0A00; }
#modal-service-list::-webkit-scrollbar-thumb { background: #5C3000; border-radius: 3px; }
#modal-service-search:focus { border-color: #F5A623 !important; box-shadow: 0 0 0 2px rgba(245,166,35,0.2); }
#service-trigger:hover { border-color: #E8003D; }
```

### Update clearServiceSelection()

```js
function clearServiceSelection() {
    selectedService = null;
    selectedServicePrice = null;
    document.getElementById('service-trigger-content').innerHTML =
        '<span style="color:#9ca3af;">Search services e.g. Telegram, WhatsApp...</span>';
    document.getElementById('continue-btn').disabled = true;
    document.getElementById('advanced-options-section').style.display = 'none';
    document.getElementById('freemium-upsell').style.display = 'none';
}
```

---

## Task 4 — Add Remaining 31 Service Logos

**File**: `templates/verify_modern.html`  
**Problem**: `_getServiceIcon()` covers 53/84 services. 31 services fall back to generic circle.  
**Impact**: 100% logo coverage, professional appearance throughout.

Add to `_getServiceIcon()` iconMap:
```js
// Missing 31 services — add to existing iconMap
stripe: 'stripe',
square: 'square',
chime: 'chime',
revolut: 'revolut',
alibaba: 'alibabadotcom',
aliexpress: 'aliexpress',
wish: 'wish',
mercari: 'mercari',
poshmark: 'poshmark',
instacart: 'instacart',
seamless: 'seamless',
deliveroo: 'deliveroo',
justeat: 'justeat',
zomato: 'zomato',
swiggy: 'swiggy',
vrbo: 'vrbo',
tripadvisor: 'tripadvisor',
kayak: 'kayak',
hopper: 'hopper',
skyscanner: 'skyscanner',
hotels: 'hotelsdotcom',
pof: 'plentyoffish',
okcupid: 'okcupid',
grindr: 'grindr',
meetme: 'meetme',
roblox: 'roblox',
fortnite: 'epicgames',
valorant: 'valorant',
kakao: 'kakaotalk',
hinge: 'hinge',
match: 'match',
```

Also update the icon color from generic `6366f1` to brand red `E8003D` for unrecognized services:
```js
return `https://cdn.simpleicons.org/${icon}/E8003D`;
```

---

## Task 5 — Refactor to VerificationFlow Controller

**File**: `templates/verify_modern.html`  
**Problem**: 8+ scattered global variables, functions not grouped logically. Hard to test and maintain.  
**Impact**: Clean architecture, easier to debug, testable.

**Replace** the top-level global variables:
```js
// BEFORE — scattered globals
let currentStep = 1;
let selectedService = null;
let selectedServicePrice = null;
let selectedAreaCode = null;
let selectedCarrier = null;
let verificationId = null;
let elapsedSeconds = 0;
let scanInterval = null;
let userTier = 'freemium';
```

**With** a single controller object:
```js
const VerificationFlow = {
    currentStep: 1,
    selectedService: null,
    selectedServicePrice: null,
    selectedAreaCode: null,
    selectedCarrier: null,
    verificationId: null,
    elapsedSeconds: 0,
    scanInterval: null,
    userTier: 'freemium',

    selectService(value, price) {
        this.selectedService = value;
        this.selectedServicePrice = price || null;
    },

    reset() {
        clearTimeout(this.scanInterval);
        this.currentStep = 1;
        this.selectedService = null;
        this.selectedServicePrice = null;
        this.selectedAreaCode = null;
        this.selectedCarrier = null;
        this.verificationId = null;
        this.elapsedSeconds = 0;
        this.scanInterval = null;
    }
};
```

All functions that reference `selectedService`, `verificationId`, etc. update to use `VerificationFlow.selectedService`, `VerificationFlow.verificationId`, etc.

---

## Task 6 — Remove Dead Picker-Modal Code

**File**: `templates/verify_modern.html`  
**Problem**: The old `#picker-modal` HTML and its JS functions (`openModal`, `closeModal`, `renderModalItems`, `filterModal`, `selectModalItem`) are dead code — the inline dropdown replaced them but they were never removed.  
**Impact**: ~80 lines removed, no confusion about which modal is active.

**Remove from HTML**:
```html
<!-- REMOVE entire picker-modal div (~lines 113-125) -->
<div id="picker-modal" style="display:none; position:fixed; ...">
    ...
</div>
```

**Remove from JS**:
- `openModal(type)` function
- `closeModal()` function
- `renderModalItems(items)` function
- `filterModal(q)` function
- `selectModalItem(value)` function
- The `picker-modal` click listener

---

## Task 7 — Optimize Search to <16ms

**File**: `templates/verify_modern.html`  
**Problem**: Search debounce is 300ms. With services in memory, filtering is instant — debounce adds unnecessary delay.  
**Impact**: Search feels instant (60fps).

**Current**:
```js
let _svcDebounce = null;
function filterServicesInline(q) {
    clearTimeout(_svcDebounce);
    _svcDebounce = setTimeout(() => _renderServiceDropdown(q), 300);
}
```

**After Task 3** (modal replaces dropdown), the modal search uses `oninput="renderServiceModal(this.value)"` directly — no debounce needed since rendering from memory is <1ms.

For the modal, remove debounce entirely. The `renderServiceModal()` function filters an in-memory array — it's synchronous and fast.

---

## Task 8 — Add Error Boundaries

**File**: `templates/verify_modern.html`  
**Problem**: If `createVerification()`, `startScanning()`, or `confirmCancel()` throw unexpectedly, the UI can get stuck in a broken state with no recovery path.  
**Impact**: Users always have a way to recover.

Wrap `createVerification()` outer try/catch to also reset button state:
```js
async function createVerification() {
    const btn = document.getElementById('get-number-btn');
    try {
        // ... existing code
    } catch (error) {
        if (btn) { btn.disabled = false; btn.textContent = 'Get Number →'; }
        // ... existing error handling
    }
}
```

Add global unhandled error recovery:
```js
window.addEventListener('unhandledrejection', (e) => {
    console.error('Unhandled rejection in verification flow:', e.reason);
    // Reset any stuck buttons
    const btn = document.getElementById('get-number-btn');
    if (btn && btn.disabled) { btn.disabled = false; btn.textContent = 'Get Number →'; }
    const cancelBtn = document.getElementById('cancel-btn');
    if (cancelBtn) cancelBtn.style.display = 'block';
    document.getElementById('cancel-confirm-btn').style.display = 'none';
});
```

---

## Task 9 — Run Existing 55 Tests

**Files**: `tests/e2e/test_verification_flow.py`, `tests/integration/test_verification_api.py`, `tests/unit/test_verification_flow.py`  
**Problem**: 55 tests written but never run. Unknown if they pass.  
**Impact**: Confidence in the implementation.

```bash
# Run all verification tests
pytest tests/unit/test_verification_flow.py -v
pytest tests/integration/test_verification_api.py -v
pytest tests/e2e/test_verification_flow.py -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=term-missing
```

Fix any failures before proceeding with other tasks.

---

## Task 10 — Fix Freemium Upsell Brand Colors

**File**: `templates/verify_modern.html`  
**Problem**: Freemium upsell uses purple (`#faf5ff`, `#7c3aed`) — doesn't match red/gold brand.  
**Impact**: Consistent brand appearance.

**Current**:
```html
<div id="freemium-upsell" style="background:#faf5ff; border:1px solid #e9d5ff; color:#6b21a8;">
    💡 Want specific area codes? <a href="/pricing" style="color:#7c3aed;">Upgrade to PAYG</a>
</div>
```

**Replace with**:
```html
<div id="freemium-upsell" style="display:none; margin-top:var(--spacing-md); padding:10px 14px;
    background:#fff5f5; border:1px solid #fecaca; border-radius:8px; font-size:13px; color:#991b1b;">
    Want specific area codes or carriers?
    <a href="/pricing" style="color:#E8003D; font-weight:600;">Upgrade to PAYG</a>
</div>
```

Also update the PREMIUM badge on area code / carrier labels from purple to red:
```html
<!-- BEFORE -->
<span style="color:#7c3aed; background:#ede9fe;">PREMIUM</span>

<!-- AFTER -->
<span style="color:#E8003D; background:#fff0f0;">PREMIUM</span>
```

---

## Implementation Order

Execute in this sequence to avoid breaking changes:

1. **Task 9** — Run tests first to establish baseline
2. **Task 1** — Remove 5s timeout (instant load)
3. **Task 2** — Remove spinner/disabled state
4. **Task 6** — Remove dead picker-modal code (cleanup before adding new modal)
5. **Task 3** — Build full-screen gold modal (replaces inline dropdown)
6. **Task 4** — Add remaining 31 logos
7. **Task 10** — Fix brand colors
8. **Task 5** — Refactor to VerificationFlow controller
9. **Task 7** — Optimize search (already handled by Task 3's modal)
10. **Task 8** — Add error boundaries

---

## Success Criteria

After all tasks complete:

- Services load instantly on page load (<50ms from cache)
- Clicking service trigger opens full-screen gold modal
- Modal shows all 84+ services with official logos
- PINNED section shows at top if user has favorites
- Search filters instantly as user types
- All 84 services have official brand logos
- Selecting a service closes modal, shows service in trigger button
- No dead code (old picker-modal removed)
- All 55 tests pass
- Freemium upsell uses red/gold brand colors
- No global variable leaks (VerificationFlow controller)
- Unhandled errors don't leave UI in broken state

---

## Files Modified

| File | Tasks | Type |
|------|-------|------|
| `templates/verify_modern.html` | 1,2,3,4,5,6,7,8,10 | Major rewrite |
| `tests/unit/test_verification_flow.py` | 9 | Run only |
| `tests/integration/test_verification_api.py` | 9 | Run only |
| `tests/e2e/test_verification_flow.py` | 9 | Run only |

---

**Estimated total effort**: 10-12 hours  
**Target version**: v4.2.0  
**Branch**: `feature/verification-flow-v2`
