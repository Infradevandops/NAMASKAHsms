# PURCHASE FLOW UX OVERHAUL — Sprint H
# "Make the wait feel like something is happening"

**Created**: November 2026
**Status**: 📋 Not started
**Reference screenshots**: `docs/artifacts/` — TV's purchase flow captured Oct–Nov 2026
**Depends on**: Sprint G (G-001 keepalive + G-002 timeout must ship first so the wait is real)

---

## BRIEF

### What TV does during the wait

TV's purchase loading screen is a full engagement loop. While the number is being
assigned (same 5-30s wait we have), the user sees:

- Animated carrier logos cycling: AT&T → T-Mobile → Verizon → Sprint
- Live status text rotating every 2-3s:
  - "Connecting to carrier network..."
  - "Requesting number from AT&T..."
  - "Verifying mobile availability..."
  - "Securing your number..."
  - "Almost there..."
- A progress bar that fills at a realistic pace (not fake 100% — stops at ~85% until confirmed)
- The service logo large and centered
- Estimated time remaining counting down

The effect: the user feels like real work is happening. They stay engaged.
Abandonment during the wait is low because there's always something moving.

### What Vrenum shows today

```
[Service icon — 64px]
"Confirming availability..."
[Pink spinner — 48px]
[Cancel button]
```

That's it. One static line of text. The spinner is the only motion.
If TV takes 15s, the user stares at "Confirming availability..." for 15s
with no indication anything is progressing. Abandonment is high.

### The message rotation that matters

The messages need to feel real — not fake. They should map loosely to what's
actually happening in the SSE steps:

| SSE step | Message sequence (rotate every 2.5s) |
|----------|--------------------------------------|
| `pricing_check` | "Checking availability..." → "Scanning provider network..." |
| `balance_check` | "Verifying your balance..." |
| `purchasing` | "Connecting to carrier network..." → "Requesting number from AT&T..." → "Verifying mobile availability..." → "Securing your number..." → "Almost there..." → "Still working — this can take up to 30s..." (after 10s) |
| `recording` | "Finalising your number..." |
| `purchasing_delayed` (G-001) | "Taking longer than usual..." → "Provider is busy — your number is being secured..." → "Hang tight, almost done..." |

The carrier names (AT&T, T-Mobile, Verizon) are cosmetic — TV doesn't tell us
which carrier assigned the number until after. But they're accurate in the sense
that US numbers come from these carriers. They make the wait feel real.

---

## TASKS

### H-001 — Purchase loading card: animated carrier + message rotation
**File**: `templates/verify_modern.html`, `static/js/verification-flow.js`
**Effort**: 2h
**Priority**: P0 — highest impact, directly reduces abandonment

Replace the current `#purchase-loading-card` with a full engagement card:

**HTML structure** (replaces lines 180–200 in `verify_modern.html`):
```html
<div class="verification-card" id="purchase-loading-card" style="display:none; text-align:center; padding:32px 24px;">

  <!-- Service icon -->
  <img id="loading-service-icon" src="" style="width:72px;height:72px;border-radius:16px;margin-bottom:20px;box-shadow:0 4px 16px rgba(0,0,0,0.1);" onerror="this.style.display='none'">

  <!-- Animated carrier strip -->
  <div id="carrier-strip" style="display:flex;justify-content:center;align-items:center;gap:16px;margin-bottom:20px;height:32px;overflow:hidden;">
    <div class="carrier-logo" data-carrier="AT&T">AT&T</div>
    <div class="carrier-logo" data-carrier="T-Mobile">T-Mobile</div>
    <div class="carrier-logo" data-carrier="Verizon">Verizon</div>
    <div class="carrier-logo" data-carrier="Sprint">Sprint</div>
  </div>

  <!-- Status message (rotates) -->
  <div id="purchase-loading-message" style="font-size:15px;font-weight:600;color:#374151;margin-bottom:8px;min-height:24px;transition:opacity 0.3s;">
    Connecting to carrier network...
  </div>
  <div id="purchase-loading-sub" style="font-size:12px;color:#9ca3af;margin-bottom:20px;">
    Securing a dedicated number for you
  </div>

  <!-- Realistic progress bar (stops at 85% until confirmed) -->
  <div style="background:#f3f4f6;border-radius:8px;height:6px;margin-bottom:20px;overflow:hidden;">
    <div id="purchase-progress-bar" style="height:100%;background:linear-gradient(90deg,#FE3C72,#FF7854);border-radius:8px;width:0%;transition:width 0.8s ease;"></div>
  </div>

  <!-- Elapsed time -->
  <div style="font-size:12px;color:#9ca3af;margin-bottom:20px;">
    <span id="purchase-elapsed">0</span>s elapsed
  </div>

  <!-- Cancel -->
  <button id="purchase-cancel-btn" class="btn btn-secondary" style="width:100%;" onclick="cancelPurchase()">
    Cancel (you will not be charged)
  </button>
</div>
```

**CSS** (add to `verification-design-system.css`):
```css
.carrier-logo {
    font-size: 11px;
    font-weight: 700;
    color: #9ca3af;
    padding: 4px 10px;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    transition: all 0.4s ease;
    opacity: 0.4;
}
.carrier-logo.active {
    color: #374151;
    border-color: #FE3C72;
    background: #fff0f0;
    opacity: 1;
    transform: scale(1.05);
}
```

**JS** (in `verification-flow.js`, replace `updateLoadingMessage` calls):
```javascript
const _PURCHASE_MESSAGES = {
    pricing_check: ["Checking availability...", "Scanning provider network..."],
    balance_check: ["Verifying your balance..."],
    purchasing: [
        "Connecting to carrier network...",
        "Requesting number from AT&T...",
        "Verifying mobile availability...",
        "Securing your number...",
        "Almost there...",
    ],
    purchasing_delayed: [
        "Taking longer than usual...",
        "Provider is busy — your number is being secured...",
        "Hang tight, almost done...",
    ],
    recording: ["Finalising your number..."],
};

const _CARRIERS = ["AT&T", "T-Mobile", "Verizon", "Sprint"];
let _carrierInterval = null;
let _msgInterval = null;
let _elapsedInterval = null;
let _purchaseStartTime = null;

function startPurchaseLoadingUI() {
    _purchaseStartTime = Date.now();
    let carrierIdx = 0;
    let elapsed = 0;

    // Carrier rotation
    const logos = document.querySelectorAll('.carrier-logo');
    _carrierInterval = setInterval(() => {
        logos.forEach(l => l.classList.remove('active'));
        logos[carrierIdx % logos.length]?.classList.add('active');
        carrierIdx++;
    }, 800);

    // Elapsed counter
    _elapsedInterval = setInterval(() => {
        elapsed++;
        const el = document.getElementById('purchase-elapsed');
        if (el) el.textContent = elapsed;
    }, 1000);

    // Progress bar — fills to 85% over 20s, then holds
    let progress = 0;
    const progressInterval = setInterval(() => {
        if (progress < 85) {
            progress += (85 / 20);  // reach 85% in ~20s
            const bar = document.getElementById('purchase-progress-bar');
            if (bar) bar.style.width = Math.min(85, progress) + '%';
        } else {
            clearInterval(progressInterval);
        }
    }, 1000);
    VerificationFlow._progressInterval = progressInterval;
}

function stopPurchaseLoadingUI() {
    clearInterval(_carrierInterval);
    clearInterval(_msgInterval);
    clearInterval(_elapsedInterval);
    clearInterval(VerificationFlow._progressInterval);
    // Fill to 100% on success
    const bar = document.getElementById('purchase-progress-bar');
    if (bar) bar.style.width = '100%';
}

function rotatePurchaseMessages(step) {
    clearInterval(_msgInterval);
    const msgs = _PURCHASE_MESSAGES[step] || _PURCHASE_MESSAGES.purchasing;
    let idx = 0;
    const el = document.getElementById('purchase-loading-message');
    if (el) {
        el.style.opacity = '0';
        setTimeout(() => { el.textContent = msgs[0]; el.style.opacity = '1'; }, 300);
    }
    if (msgs.length > 1) {
        _msgInterval = setInterval(() => {
            idx = (idx + 1) % msgs.length;
            if (el) {
                el.style.opacity = '0';
                setTimeout(() => { el.textContent = msgs[idx]; el.style.opacity = '1'; }, 300);
            }
        }, 2500);
    }
}
```

Call `startPurchaseLoadingUI()` when loading card is shown.
Call `rotatePurchaseMessages(step)` on each SSE step.
Call `stopPurchaseLoadingUI()` on `complete` or `failed`.

---

### H-002 — Step 3 scanning animation: replace radar pulse with activity feed
**File**: `templates/verify_modern.html`, `static/css/sms-polling-ui.css`
**Effort**: 1.5h
**Priority**: P1 — step 3 is where users wait longest (up to 10 min)

Current step 3 scanning container:
```
📡 [radar pulse ring]
"Establishing secure connection..."
[service name]
[elapsed / remaining]
[progress bar]
```

Replace with a live activity feed that shows rolling log entries, like a terminal:

```
✓  Number secured: +1 (212) 555-0142
⟳  Listening for incoming SMS...
⟳  Polling AT&T network...          ← rotates every 3s
⟳  Waiting for verification code...
```

Each new entry fades in from the bottom. Old entries fade out at the top.
Max 4 visible at once. The phone number is shown as the first confirmed entry.

This is the same pattern TV uses in their waiting screen — it looks like real
network activity even though it's cosmetic. The key insight: users tolerate
waiting much better when they can see "something is happening" vs a static spinner.

**Activity messages to rotate** (every 3s, random from pool):
```javascript
const _SCAN_MESSAGES = [
    "Polling carrier network...",
    "Listening for incoming SMS...",
    "Scanning AT&T network...",
    "Scanning T-Mobile network...",
    "Checking for new messages...",
    "Waiting for verification code...",
    "Monitoring number activity...",
    "Network scan in progress...",
    "Awaiting SMS delivery...",
];
```

---

### H-003 — Step 0 method picker: add Combo option
**File**: `templates/verify_modern.html`
**Effort**: 30 min
**Priority**: P2 — surfaces the smsAndVoiceCombo capability added in B-008

Add a third card to the method picker:
```html
<button type="button" onclick="chooseMethod('combo')" ...>
    <span style="font-size:36px;">📱📞</span>
    <span style="font-size:16px;font-weight:700;">SMS + Voice</span>
    <span style="font-size:12px;color:#6b7280;">Best coverage</span>
    <span style="font-size:10px;background:#fef3c7;color:#92400e;padding:2px 6px;border-radius:4px;">+$0.50</span>
</button>
```

`chooseMethod('combo')` sets `VerificationFlow.selectedCapability = 'sms_and_voice'`
and proceeds to step 1 (same as SMS path).

---

### H-004 — Purchase loading card: `purchasing_delayed` state
**File**: `static/js/verification-flow.js`
**Effort**: 30 min
**Priority**: P1 — depends on G-001 (the 12s timeout)
**Blocked by**: G-001

When G-001 fires `purchasing_delayed` SSE event:
- Switch message rotation to `_PURCHASE_MESSAGES.purchasing_delayed`
- Change sub-text to "Your number is being secured — this may take a moment longer"
- Hide cancel button (charge may have committed on TV's side)
- Show "Please wait — do not close this tab" warning
- Progress bar pulses (CSS animation) instead of advancing

```javascript
case 'purchasing_delayed':
    hideCancelButton();
    rotatePurchaseMessages('purchasing_delayed');
    document.getElementById('purchase-loading-sub').textContent =
        'Your number is being secured — please do not close this tab';
    document.getElementById('purchase-progress-bar').style.animation =
        'pulse-bar 1.5s ease-in-out infinite';
    break;
```

---

### H-005 — Step 2 pricing card: show service icon + capability badge
**File**: `templates/verify_modern.html`
**Effort**: 30 min
**Priority**: P2 — polish

Add service icon and capability badge to the pricing confirmation card
so the user can visually confirm what they're about to buy before clicking
"Get Number →".

```html
<!-- Add above pricing rows in step-2-card -->
<div style="display:flex;align-items:center;gap:12px;padding:12px;background:#f9fafb;border-radius:10px;margin-bottom:16px;">
    <img id="pricing-service-icon" src="" style="width:40px;height:40px;border-radius:8px;" onerror="this.style.display='none'">
    <div>
        <div style="font-weight:700;font-size:15px;" id="pricing-service-name">-</div>
        <div id="pricing-capability-badge" style="font-size:11px;margin-top:2px;"></div>
    </div>
</div>
```

---

## PROGRESS SUMMARY

| ID | Task | Effort | Priority | Status |
|----|------|--------|----------|--------|
| H-001 | Purchase loading: carrier animation + message rotation | 2h | P0 | 📋 |
| H-002 | Step 3 scanning: activity feed log | 1.5h | P1 | 📋 |
| H-003 | Step 0: Combo method picker card | 30 min | P2 | 📋 |
| H-004 | `purchasing_delayed` state UI | 30 min | P1 | 📋 (blocked on G-001) |
| H-005 | Step 2: service icon + capability badge | 30 min | P2 | 📋 |
| **Total** | | **~5h** | | **0/5** |

---

## EXECUTION ORDER

```
G-001 + G-002 (Sprint G)  →  H-001 + H-002  →  H-004  →  H-003 + H-005
(stop the leak first)         (core UX)          (delayed state)  (polish)
```

H-001 and H-002 can ship independently of Sprint G — they improve UX regardless
of whether the timeout fix is live. H-004 requires G-001 to be deployed first.

---

## WHAT THIS IS NOT

- Not fake progress. The progress bar stops at 85% until TV confirms.
  The carrier names are cosmetic but accurate (US numbers come from these carriers).
  The activity log messages are cosmetic but plausible.
  Nothing claims a specific carrier was assigned — that's not knowable until after.

- Not a redesign of the verification flow. Steps 1/2/3 structure stays the same.
  This is purely the loading states between and within those steps.

- Not a mobile-first rewrite. The existing responsive layout is fine.
  These changes work at all screen sizes.
