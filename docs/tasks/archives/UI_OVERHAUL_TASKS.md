# UI Overhaul — Master Task File

**Created**: April 6, 2026  
**Version**: 1.0  
**Status**: Planning → Ready to Execute

---

## ⚠️ GOLDEN RULES (Never Break These)

1. **No backend changes** — pure HTML/CSS/JS only
2. **No API route changes** — all endpoints stay identical
3. **No JS function renames** — all existing `onclick` handlers preserved
4. **No polling logic changes** — `startPolling()`, `stopPolling()`, `poll()` untouched
5. **CSS is additive only** — new classes added, existing ones kept
6. **Test after every task** — verify SMS polling still works before committing
7. **One file at a time** — never edit multiple templates simultaneously

---

## 🔒 SMS POLLING — DO NOT TOUCH LIST

These functions in `verify_modern.html` must never be renamed or restructured:

```
startPolling()         — starts the polling loop
stopPolling()          — clears the timeout
poll()                 — inner async function, fetches status
createVerification()   — calls /api/verification/request
cancelVerification()   — calls /api/verification/cancel/{id}
confirmCancel()        — confirms cancel + refund
resetFlow()            — resets all state
VerificationFlow{}     — state object (all keys must stay)
```

These DOM IDs are wired to polling logic — must stay:

```
#sms-code              — where code is written
#code-received         — shown when code arrives
#phone-number          — displays the phone number
#elapsed-time          — seconds counter
#progress-elapsed      — elapsed text
#progress-remaining    — remaining text
#cancel-btn            — cancel button
#cancel-confirm-btn    — confirm cancel button
#step-1-card           — step 1 container
#step-2-card           — step 2 container
#step-3-card           — step 3 container
#get-number-btn        — triggers createVerification()
#display-verification-id — shows verification ID
.scanning-container    — scanning animation wrapper
.scanning-progress-bar — progress bar fill
```

---

## 📋 PHASE 1 — Design System Foundation

**Goal**: Establish unified CSS tokens across all pages  
**Risk**: Zero — additive only  
**Time**: 2-3 hours  
**Breaks SMS polling**: ❌ No

### Tasks

- [ ] **1.1** Create `static/css/namaskah-ui.css`
  - Unified color tokens (brand red `#E8003D`, neutrals, status colors)
  - Typography scale (Inter font via Google Fonts)
  - Spacing scale (4px base grid)
  - Shadow system (3 levels)
  - Border radius tokens
  - Transition tokens
  - Dark mode variables (prep only, not activated yet)

- [ ] **1.2** Update `templates/base.html`
  - Add `<link>` to `namaskah-ui.css` globally
  - Add Inter font import
  - Keep all existing CSS — do not remove anything

- [ ] **1.3** Update `templates/dashboard_base.html`
  - Replace scattered inline color values with CSS variables
  - Keep all existing classes and IDs intact

- [ ] **1.4** Update `static/css/verification-design-system.css`
  - Align existing tokens with new `namaskah-ui.css` tokens
  - No removals — only additions and variable references

- [ ] **1.5** Verify
  - All pages load without visual regression
  - SMS polling page loads and functions
  - Run CI

---

## 📋 PHASE 2 — SMS Verification UI (Step 3 Rebuild)

**Goal**: Premium SMS polling experience  
**Risk**: MEDIUM — touches verify_modern.html  
**Time**: 4-6 hours  
**Breaks SMS polling**: ❌ No (if rules followed)

### Pre-work Checklist (Do Before Any Code)

- [ ] Read and understand every line of `startPolling()` in `verify_modern.html`
- [ ] Map every DOM ID used by polling (see DO NOT TOUCH LIST above)
- [ ] Confirm `#sms-code`, `#code-received`, `.scanning-container` IDs are preserved
- [ ] Test current SMS polling works end-to-end before touching anything

---

### Task 2.1 — Phone Number Display (Step 3 Card)

**What**: Redesign the phone number display block  
**File**: `templates/verify_modern.html` — Step 3 card only  
**Preserve**: `#phone-number` ID, `copyPhoneNumber()` function  

New design:
```
┌─────────────────────────────────────┐
│  📱  Your Verification Number        │
│                                      │
│  +1 (479) 502-2832                  │
│  ┌──────────┐  ┌──────────────────┐ │
│  │  📋 Copy │  │  🔊 Call/Text    │ │
│  └──────────┘  └──────────────────┘ │
│  Number expires in  ⏱ 09:47         │
└─────────────────────────────────────┘
```

Implementation rules:
- Keep `id="phone-number"` on the number element
- Keep `onclick="copyPhoneNumber()"` on copy button
- Add visual feedback class toggle on copy (CSS only)
- Timer display is cosmetic only — does not affect polling

---

### Task 2.2 — Scanning Animation (Step 3 Card)

**What**: Replace basic scanning animation with premium animated state  
**File**: `templates/verify_modern.html` — scanning-container only  
**Preserve**: `.scanning-container`, `.scanning-progress-bar`, `#elapsed-time`  

New design:
```
┌─────────────────────────────────────┐
│                                      │
│     ◉  Scanning for SMS...          │
│     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│     ████████░░░░░░░░░░░░  47s       │
│                                      │
│     Waiting for code from            │
│     WhatsApp · +1 (479) 502-2832    │
│                                      │
└─────────────────────────────────────┘
```

Implementation rules:
- Keep `.scanning-container` class on wrapper
- Keep `.scanning-progress-bar` class on progress fill
- Keep `id="elapsed-time"` on seconds counter
- Pulsing dot animation via CSS `@keyframes` only
- Progress bar width is still set by `poll()` function — do not change that logic

---

### Task 2.3 — SMS Code Arrival (Step 3 Card)

**What**: Premium code reveal when SMS arrives  
**File**: `templates/verify_modern.html` — `#code-received` section  
**Preserve**: `id="code-received"`, `id="sms-code"`, `onclick="copySMSCode()"`  

New design:
```
┌─────────────────────────────────────┐
│  ✅  SMS Code Received!              │
│                                      │
│  ┌─────────────────────────────┐    │
│  │   1  2  3  4  5  6          │    │  ← digit flip animation
│  └─────────────────────────────┘    │
│                                      │
│  Full message:                       │
│  "Your WhatsApp code is 123456"     │
│                                      │
│  ┌──────────────────────────────┐   │
│  │  📋  Copy Code  ✓ Copied!   │   │  ← state toggle
│  └──────────────────────────────┘   │
│                                      │
│  🔔 Auto-copy: [ON/OFF toggle]      │
└─────────────────────────────────────┘
```

Implementation rules:
- Keep `id="code-received"` on wrapper div
- Keep `id="sms-code"` on code display element
- Keep `onclick="copySMSCode()"` on copy button
- Digit flip animation: CSS only, triggered by adding a class
- Sound: Web Audio API in a NEW function `playArrivalSound()` — called AFTER existing code display logic
- Auto-copy toggle: reads from `localStorage` — does not affect polling

---

### Task 2.4 — Sound on Code Arrival

**What**: Beep/chime sound when SMS code arrives  
**File**: `static/js/sms-arrival-sound.js` (NEW file)  
**Preserve**: Nothing to preserve — new file only  

Implementation:
```javascript
// Web Audio API — no external dependency, no file download
function playArrivalSound() {
    try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        // Pleasant two-tone chime
        [523.25, 659.25].forEach((freq, i) => {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.frequency.value = freq;
            osc.type = 'sine';
            gain.gain.setValueAtTime(0.3, ctx.currentTime + i * 0.15);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + i * 0.15 + 0.4);
            osc.start(ctx.currentTime + i * 0.15);
            osc.stop(ctx.currentTime + i * 0.15 + 0.4);
        });
    } catch(e) { /* silent fail — sound is non-critical */ }
}
```

Hook into existing code — in `verify_modern.html`, find the line:
```javascript
window.toast.success('SMS code received');
```
Add ONE line after it:
```javascript
playArrivalSound();
```

That's the only change to existing logic.

---

### Task 2.5 — Enhanced Timer Display

**What**: Visual ring/arc countdown timer  
**File**: `templates/verify_modern.html` — timer section only  
**Preserve**: `#elapsed-time`, `#progress-elapsed`, `#progress-remaining`  

Implementation:
- SVG circle arc that depletes over 120 seconds
- Arc stroke-dashoffset updated by existing `poll()` timer logic
- Keep all existing `#elapsed-time` and text updates — just add SVG wrapper around them
- Color transitions: green → yellow → red as time runs out

---

### Task 2.6 — Step 3 CSS

**What**: New CSS for all Step 3 enhancements  
**File**: `static/css/sms-polling-ui.css` (NEW file)  
**Preserve**: All existing classes in `verification-design-system.css`  

Contents:
- `.phone-card` — premium phone display
- `.copy-btn-state` — copy button state transitions
- `.digit-flip` — code digit animation
- `.arrival-pulse` — green pulse on code arrival
- `.timer-ring` — SVG timer styles
- `.scanning-pulse` — animated scanning dot
- Sound toggle styles

---

### Task 2.7 — Verify & Test Phase 2

- [ ] SMS polling starts correctly after `createVerification()`
- [ ] Phone number displays in `#phone-number`
- [ ] Timer increments via `#elapsed-time`
- [ ] Code appears in `#sms-code` when received
- [ ] `#code-received` shows when code arrives
- [ ] Sound plays on code arrival
- [ ] Copy button copies phone number
- [ ] Copy button copies SMS code
- [ ] Cancel button works
- [ ] Reset flow works
- [ ] No console errors
- [ ] Run CI

---

## 📋 PHASE 3 — Dashboard & Navigation

**Goal**: Sleek sidebar, header, and dashboard stats  
**Risk**: LOW — layout only  
**Time**: 3-4 hours  
**Breaks SMS polling**: ❌ No

### Tasks

- [ ] **3.1** Sidebar redesign (`components/sidebar.html`)
  - Cleaner icon + label layout
  - Active state with brand red left border
  - Collapsed state on mobile
  - Keep all existing `href` links intact

- [ ] **3.2** Header redesign (`dashboard_base.html`)
  - Cleaner balance display
  - Better tier badge
  - Notification bell refinement
  - Keep all existing IDs and JS hooks

- [ ] **3.3** Dashboard stats cards (`dashboard.html`)
  - Elevated card style
  - Better number typography
  - Subtle gradient accents
  - Keep all existing data-loading JS

- [ ] **3.4** Verify & Test Phase 3
  - All navigation links work
  - Balance displays correctly
  - Tier badge shows correctly
  - Run CI

---

## 📋 PHASE 4 — Wallet & Payments

**Goal**: Premium payment UI  
**Risk**: LOW  
**Time**: 2-3 hours  
**Breaks SMS polling**: ❌ No

### Tasks

- [ ] **4.1** Payment buttons (`wallet.html`)
  - More tactile button design
  - Better visual hierarchy ($10 → $100)
  - Keep all `onclick="addCredits()"` handlers

- [ ] **4.2** Transaction history table
  - Better row design
  - Status chips (completed/pending/failed)
  - Keep all existing pagination JS

- [ ] **4.3** Crypto section
  - Cleaner QR display
  - Better address copy UX
  - Keep all `onclick` handlers

- [ ] **4.4** Verify & Test Phase 4
  - Payment buttons trigger correctly
  - Transaction history loads
  - Run CI

---

## 📋 PHASE 5 — Auth Pages

**Goal**: Premium login/register/reset experience  
**Risk**: LOW  
**Time**: 2-3 hours  
**Breaks SMS polling**: ❌ No

### Tasks

- [ ] **5.1** Login page (`login.html`)
- [ ] **5.2** Register page (`register.html`)
- [ ] **5.3** Password reset (`password_reset.html`, `password_reset_confirm.html`)
- [ ] **5.4** Email verify (`email_verify.html`)
- [ ] **5.5** Verify & Test Phase 5

---

## 📋 PHASE 6 — Remaining Pages

**Goal**: Consistent UI across all remaining pages  
**Risk**: LOW  
**Time**: 4-6 hours  
**Breaks SMS polling**: ❌ No

### Tasks

- [ ] **6.1** Settings (`settings.html`)
- [ ] **6.2** Profile (`profile.html`)
- [ ] **6.3** Analytics (`analytics.html`)
- [ ] **6.4** History (`history.html`)
- [ ] **6.5** API Keys (`api_keys.html`)
- [ ] **6.6** Pricing (`pricing.html`)
- [ ] **6.7** Error pages (`404.html`, `500.html`)
- [ ] **6.8** Admin pages (`admin/dashboard.html`, etc.)
- [ ] **6.9** Landing page (`landing.html`)
- [ ] **6.10** Verify & Test Phase 6

---

## 📋 PHASE 7 — Code Issues (Parallel Track)

**Goal**: Fix Critical/High findings from code scan  
**Risk**: MEDIUM — backend changes  
**Time**: Ongoing  
**Breaks SMS polling**: Only if backend routes change (they won't)

### Tasks

- [ ] **7.1** Fix Critical security findings (from Code Issues Panel)
- [ ] **7.2** Fix High security findings
- [ ] **7.3** Fix Medium code quality findings
- [ ] **7.4** Fix Low/Info findings
- [ ] **7.5** Improve test coverage from 30% → 60%
- [ ] **7.6** Run full CI after each batch

---

## 📊 PROGRESS TRACKER

| Phase | Status | Risk | Time Est | CI |
|-------|--------|------|----------|----|
| 1 — Design System | ⬜ Not Started | Zero | 2-3h | — |
| 2 — SMS Polling UI | ⬜ Not Started | Medium | 4-6h | — |
| 3 — Dashboard/Nav | ⬜ Not Started | Low | 3-4h | — |
| 4 — Wallet | ⬜ Not Started | Low | 2-3h | — |
| 5 — Auth Pages | ⬜ Not Started | Low | 2-3h | — |
| 6 — Remaining Pages | ⬜ Not Started | Low | 4-6h | — |
| 7 — Code Issues | ⬜ Not Started | Medium | Ongoing | — |

**Total Estimated Time**: 19-29 hours

---

## 🎨 DESIGN REFERENCE

### Brand Colors
```
Primary Red:    #E8003D
Primary Dark:   #b3002f
Success:        #10b981
Warning:        #f59e0b
Error:          #ef4444
Info:           #3b82f6
Text Primary:   #1f2937
Text Secondary: #6b7280
Background:     #f9fafb
Card:           #ffffff
Border:         #e5e7eb
```

### Typography
```
Font:           Inter (Google Fonts)
Heading:        700 weight
Body:           400 weight
Label:          600 weight
Code/Number:    'Courier New', monospace
```

### UI Style Reference (from screenshot context)
```
Clean white cards with subtle shadows
Bold section headers
Clear visual hierarchy
Minimal decoration
Functional > decorative
Mobile-first responsive
```

---

## 🚨 EMERGENCY ROLLBACK

If SMS polling breaks at any point:

```bash
# Revert last commit
git revert HEAD

# Or revert specific file
git checkout HEAD~1 -- templates/verify_modern.html
git commit -m "revert: restore verify_modern.html"
git push origin main
```

---

## ✅ DEFINITION OF DONE

Each phase is complete when:
1. All tasks in the phase are checked off
2. SMS polling tested end-to-end (if Phase 2)
3. All pages load without console errors
4. CI passes (all 4 checks green)
5. Mobile responsive check done
6. Committed and pushed to main

---

**Start with**: Phase 1 (zero risk, unblocks all other phases)  
**Then**: Phase 2 (highest user impact)  
**Parallel**: Phase 7 (code issues, independent track)
