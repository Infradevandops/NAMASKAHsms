# PURCHASE FLOW UX OVERHAUL — Sprint H
# "Make the wait feel like something is happening"

**Created**: November 2026
**Status**: 📋 Not started
**Reference screenshots**: `docs/artifacts/` — TV's purchase flow captured Oct 31 2026 04:22–05:50
**Depends on**: Sprint G-001 + G-002 must ship first (keepalive + nginx timeout)

---

## WHAT TV ACTUALLY DOES — EXACT SPEC FROM SCREENSHOTS

This is not a guess. These are the exact screens captured from `app.textverified.com`.

### The loading modal structure

Dark full-screen overlay. Single centered card. Three zones:

```
┌─────────────────────────────────┐
│  ×                              │  ← close button top-right
│                                 │
│         WhatsApp                │  ← service name, bold, white, large
│                                 │
│      ┌──────────┐               │
│   ◜  │  [icon]  │  ◝            │  ← white circle with service icon
│      └──────────┘               │    blue arc orbits the circle (not separate)
│                                 │
│  Checking major carrier         │  ← HEADLINE: bold, white/light-grey
│  networks                       │
│                                 │
│  Pinging AT&T • T-Mobile •      │  ← SUBTITLE: lighter grey, smaller
│  Verizon                        │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ Cancel (You will not be     │ │  ← single button, dark grey bg
│ │ charged)                    │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

**The arc spinner**: a thick blue arc (~120° of a circle) that rotates around the
service icon. The icon stays still. The arc orbits it. This is the only animation
besides the text changing. No separate spinner anywhere.

### The exact message sequence (from screenshots, in order)

TV cycles through these headline + subtitle pairs. Each pair shows for ~3-4s.
The headline changes less frequently than the subtitle.

**Phase 1 — Searching** (first ~5s):
- "Searching for unused numbers" / "Filtering out recently recycled numbers"
- "Searching for unused numbers" / "Verifying immediate number pool availability"
- "Searching for unused numbers" / "Scanning number blocks for unused SIM"

**Phase 2 — High demand** (if service is busy, ~5-15s):
- "This service is experiencing high demand" / "Estimating current queue length"
- "This service is experiencing high demand" / "Reserving your place in queue"
- "This service is experiencing high demand" / "We appreciate your patience"

**Phase 3 — Carrier check** (~5-10s):
- "Checking major carrier networks" / "Measuring latency and connection strength"
- "Checking major carrier networks" / "Pinging AT&T • T-Mobile • Verizon"

**Phase 4 — Line availability** (final ~5s):
- "Checking current line availability for selected service" / "Initiating..."
- "Checking current line availability for selected service" / "Connecting to cellular network"
- "Checking current line availability for selected service" / "Connected!"

Total sequence: ~20-30s of continuous message rotation. Never the same text twice
in a row. Always something new happening.

### After number assigned — step 3 modal

TV's step 3 is also a modal (not a page). Key elements:

```
[WhatsApp icon]  WhatsApp SMS Verification     ← icon + title in header row

┌─────────────────────────────────────────┐
│ ℹ  Waiting to receive an SMS from       │  ← blue info banner
│    WhatsApp. Please note that services  │
│    may take multiple attempts to        │
│    succeed.                             │
└─────────────────────────────────────────┘

Use This Number
┌──────────────────────────────┬────────┐
│ [AT&T icon] +1 (702) 285-3600│  Copy  │  ← carrier icon shown next to number
└──────────────────────────────┴────────┘

Price              Time Left
┌──────────────┐   ┌──────────────┐
│    1.50      │   │    58:21     │  ← MM:SS countdown
└──────────────┘   └──────────────┘

┌─────────────────────────────────────────┐
│  Please request only one code.          │  ← warning box, dark bg
│  Multiple requests may result in        │
│  issues with your code.                 │
└─────────────────────────────────────────┘
```

### After SMS received — success state

```
┌─────────────────────────────────────────┐
│ ✓  Successfully Received Your SMS       │  ← green success banner
│    Would you like to do another?        │
└─────────────────────────────────────────┘

Use This Number
┌──────────────────────────────┬────────┐
│ [AT&T icon] +1 (702) 285-3600│  Copy  │
└──────────────────────────────┴────────┘

Price              Time Left
┌──────────────┐   ┌──────────────┐
│    1.50      │   │    54:15     │
└──────────────┘   └──────────────┘

Message
┌─────────────────────────────────┬──────┐
│ <#> Your WhatsApp Business code │ Copy │
│ 876-094 Don't share this code   │      │
│ with others rJbA/XP1K+V         │      │
└─────────────────────────────────┴──────┘

┌─────────────────────────────────────────┐
│  Use again for 0.75 credits (0:47)      │  ← reuse CTA with countdown
└─────────────────────────────────────────┘

┌──────────────┐   ┌──────────────┐
│   Go Back    │   │  Do Another  │
└──────────────┘   └──────────────┘
```

**Key observations from screenshots:**
1. TV shows the **carrier icon** (AT&T logo) next to the number — they know the carrier
   because they assigned it. Vrenum can show this too since `assigned_area_code` maps
   to a carrier pool (AT&T for 702 Las Vegas).
2. The **reuse button** shows exact cost + countdown timer in the button itself:
   "Use again for 0.75 credits (0:47)". Vrenum's reuse banner should match this.
3. TV's **"Do Another"** button is the equivalent of Vrenum's "Start New Verification".
4. The **time left** is MM:SS format counting down from ~60 minutes (TV's window is longer
   than Vrenum's — TV gives 60 min, Vrenum gives 10 min by default).
5. TV shows the **full raw SMS** including the hash prefix and hash suffix — not just the
   parsed code. Vrenum shows only the parsed code. TV's approach is better for debugging.

### TV's webhook auto-disable behaviour (screenshot 04:40:53)

TV's API config page states:
> "Undeliverable webhooks are automatically retried for a period of time. After repeated
> failed webhook delivery attempts, all webhooks will be automatically disabled and you
> will have to manually re-enable your webhooks again."

This is a risk for Vrenum. If the server is down during a deploy and TV fires webhooks
that fail, TV will disable our webhook endpoint. The TV webhook endpoint needs a health
check and auto-re-enable mechanism. Added as H-006 below.

---

## TASKS

### H-001 — Purchase loading modal: arc spinner + exact TV message sequence
**Files**: `templates/verify_modern.html`, `static/js/verification-flow.js`, `static/css/verification-design-system.css`
**Effort**: 2.5h
**Priority**: P0

**The arc spinner** (CSS only — no library):
```css
@keyframes orbit-arc {
    from { transform: rotate(0deg); }
    to   { transform: rotate(360deg); }
}
.orbit-wrapper {
    position: relative;
    width: 96px;
    height: 96px;
    margin: 0 auto 24px;
}
.orbit-arc {
    position: absolute;
    inset: -6px;
    border-radius: 50%;
    border: 4px solid transparent;
    border-top-color: #3b82f6;
    border-right-color: #3b82f6;
    animation: orbit-arc 1.2s linear infinite;
}
.orbit-icon {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #e8f0fe;
    border-radius: 50%;
}
.orbit-icon img {
    width: 52px;
    height: 52px;
    border-radius: 10px;
}
```

**HTML** (replaces `#purchase-loading-card` entirely):
```html
<div class="verification-card" id="purchase-loading-card"
     style="display:none; text-align:center; padding:32px 24px; background:#0f172a; color:#fff; border-radius:20px;">

  <div style="font-size:20px; font-weight:800; margin-bottom:24px;" id="loading-service-title">WhatsApp</div>

  <div class="orbit-wrapper">
    <div class="orbit-arc"></div>
    <div class="orbit-icon">
      <img id="loading-service-icon" src="" onerror="this.style.display='none'">
    </div>
  </div>

  <div id="purchase-loading-headline"
       style="font-size:16px; font-weight:600; color:#e2e8f0; margin-bottom:8px; min-height:48px; transition:opacity 0.3s;">
    Searching for unused numbers
  </div>
  <div id="purchase-loading-subtitle"
       style="font-size:14px; color:#94a3b8; margin-bottom:28px; min-height:40px; transition:opacity 0.3s;">
    Filtering out recently recycled numbers
  </div>

  <button id="purchase-cancel-btn" onclick="cancelPurchase()"
          style="width:100%; padding:14px; background:#1e293b; border:1px solid #334155;
                 border-radius:10px; color:#cbd5e1; font-size:14px; font-weight:600; cursor:pointer;">
    Cancel (You will not be charged)
  </button>
</div>
```

**JS message sequence** (exact TV copy, mapped to SSE steps):
```javascript
const _TV_MESSAGES = [
    // Phase 1 — Searching (pricing_check + early purchasing)
    // NOTE: exact TV copy — "unused" not "never used". Subtitle is a trust signal.
    { h: "Searching for unused numbers",                          s: "Filtering out recently recycled numbers" },
    { h: "Searching for unused numbers",                          s: "Verifying immediate number pool availability" },
    { h: "Searching for unused numbers",                          s: "Scanning number blocks for unused SIM" },
    // Phase 2 — High demand (mid purchasing)
    { h: "This service is experiencing high demand",              s: "Estimating current queue length" },
    { h: "This service is experiencing high demand",              s: "Reserving your place in queue" },
    { h: "This service is experiencing high demand",              s: "We appreciate your patience" },
    // Phase 3 — Carrier check (late purchasing)
    { h: "Checking major carrier networks",                       s: "Measuring latency and connection strength" },
    { h: "Checking major carrier networks",                       s: "Pinging AT&T \u2022 T-Mobile \u2022 Verizon" },
    // Phase 4 — Line availability (recording)
    { h: "Checking current line availability for selected service", s: "Initiating..." },
    { h: "Checking current line availability for selected service", s: "Connecting to cellular network" },
    { h: "Checking current line availability for selected service", s: "Connected!" },
];

let _msgIdx = 0;
let _msgTimer = null;

function startPurchaseMessages() {
    _msgIdx = 0;
    _rotatePurchaseMsg();
    _msgTimer = setInterval(_rotatePurchaseMsg, 3000);
}

function _rotatePurchaseMsg() {
    const msg = _TV_MESSAGES[_msgIdx % _TV_MESSAGES.length];
    const h = document.getElementById('purchase-loading-headline');
    const s = document.getElementById('purchase-loading-subtitle');
    if (h && s) {
        h.style.opacity = '0'; s.style.opacity = '0';
        setTimeout(() => {
            h.textContent = msg.h; s.textContent = msg.s;
            h.style.opacity = '1'; s.style.opacity = '1';
        }, 300);
    }
    _msgIdx++;
}

function stopPurchaseMessages() {
    clearInterval(_msgTimer);
}
```

Call `startPurchaseMessages()` when loading card shows.
Call `stopPurchaseMessages()` on `complete` / `failed`.
Set `document.getElementById('loading-service-title').textContent = serviceLabel` on show.

---

### H-002 — Step 3: carrier icon + MM:SS countdown + full SMS text + reuse button
**Files**: `templates/verify_modern.html`, `static/js/verification-flow.js`
**Effort**: 2h
**Priority**: P0 — step 3 is the most-used screen

**Changes to step 3 card:**

1. **Carrier icon next to number** — map `assigned_area_code` to carrier:
```javascript
const _AC_CARRIER_MAP = {
    // AT&T area codes (sample — expand as needed)
    '702': 'att', '213': 'att', '310': 'att', '404': 'att',
    // T-Mobile
    '212': 'tmobile', '646': 'tmobile', '917': 'tmobile',
    // Verizon
    '617': 'verizon', '781': 'verizon', '508': 'verizon',
};
function _getCarrierIcon(areaCode) {
    const carrier = _AC_CARRIER_MAP[areaCode] || 'generic';
    const icons = {
        att: '🔵', tmobile: '🩷', verizon: '🔴', generic: '📶'
    };
    return icons[carrier] || '📶';
}
```

2. **MM:SS countdown** — replace elapsed counter with countdown from `ends_at`:
```javascript
function startCountdown(endsAtIso) {
    const endsAt = new Date(endsAtIso).getTime();
    const tick = () => {
        const remaining = Math.max(0, endsAt - Date.now());
        const mm = String(Math.floor(remaining / 60000)).padStart(2, '0');
        const ss = String(Math.floor((remaining % 60000) / 1000)).padStart(2, '0');
        const el = document.getElementById('time-left-display');
        if (el) el.textContent = `${mm}:${ss}`;
        if (remaining <= 0) clearInterval(VerificationFlow._countdownTimer);
    };
    tick();
    VerificationFlow._countdownTimer = setInterval(tick, 1000);
}
```

3. **Full SMS text** — show raw `sms_text` alongside parsed code:
```html
<!-- Add below sms-code-display in step-3-card -->
<div id="sms-full-text-box" style="display:none; margin-top:12px; background:#1e293b;
     border-radius:8px; padding:12px 16px; text-align:left;">
  <div style="font-size:11px; color:#64748b; margin-bottom:6px;">Full message</div>
  <div id="sms-full-text" style="font-size:13px; color:#e2e8f0; word-break:break-word;
       font-family:monospace; line-height:1.5;"></div>
</div>
```

4. **Reuse button with countdown** — replace current reuse banner with TV-style inline button:
```html
<button id="reuse-countdown-btn" style="display:none; width:100%; margin-top:12px;
        padding:12px; background:#1e293b; border:1px solid #334155; border-radius:10px;
        color:#93c5fd; font-size:14px; font-weight:600; cursor:pointer;"
        onclick="openReuseModal(VerificationFlow.verificationId)">
  Use again for $0.25 (<span id="reuse-countdown">0:47</span>)
</button>
```

Start reuse countdown from `reusable_until` when `reuse_available` WS event fires.

5. **Info banner** — add TV's "services may take multiple attempts" notice:
```html
<!-- Add at top of scanning-container -->
<div style="background:#1e3a5f; border:1px solid #1d4ed8; border-radius:8px;
     padding:10px 14px; margin-bottom:16px; font-size:13px; color:#93c5fd; text-align:left;">
  ℹ Waiting to receive an SMS. Services may take multiple attempts to succeed.
</div>
```

---

### H-003 — Step 3 scanning: replace radar pulse with TV-style activity feed
**Files**: `templates/verify_modern.html`, `static/css/sms-polling-ui.css`
**Effort**: 1h
**Priority**: P1

Replace the `radar-pulse-ring` + static text with a scrolling log:

```html
<div id="activity-feed" style="text-align:left; font-size:13px; color:#94a3b8;
     max-height:120px; overflow:hidden; margin-bottom:16px;">
  <!-- entries injected by JS, newest at bottom, max 4 visible -->
</div>
```

```javascript
const _SCAN_MSGS = [
    "Polling carrier network...",
    "Listening for incoming SMS...",
    "Scanning AT&T network...",
    "Scanning T-Mobile network...",
    "Checking for new messages...",
    "Waiting for verification code...",
    "Monitoring number activity...",
    "Network scan in progress...",
    "Awaiting SMS delivery...",
    "Checking message queue...",
];

function addActivityEntry(text, isConfirmed = false) {
    const feed = document.getElementById('activity-feed');
    if (!feed) return;
    const entry = document.createElement('div');
    entry.style.cssText = 'padding:3px 0; opacity:0; transition:opacity 0.4s; display:flex; gap:8px; align-items:center;';
    entry.innerHTML = `<span style="color:${isConfirmed ? '#22c55e' : '#3b82f6'};">${isConfirmed ? '✓' : '⟳'}</span> ${text}`;
    feed.appendChild(entry);
    setTimeout(() => { entry.style.opacity = '1'; }, 50);
    // Keep max 4 entries
    while (feed.children.length > 4) {
        feed.children[0].style.opacity = '0';
        setTimeout(() => feed.children[0]?.remove(), 400);
    }
}

function startActivityFeed(phoneNumber) {
    addActivityEntry(`Number secured: ${phoneNumber}`, true);
    let i = 0;
    VerificationFlow._activityTimer = setInterval(() => {
        addActivityEntry(_SCAN_MSGS[i % _SCAN_MSGS.length]);
        i++;
    }, 3000);
}

function stopActivityFeed() {
    clearInterval(VerificationFlow._activityTimer);
    addActivityEntry('SMS code received!', true);
}
```

---

### H-004 — `purchasing_delayed` state (blocked on G-001)
**Files**: `static/js/verification-flow.js`
**Effort**: 30 min
**Priority**: P1
**Blocked by**: G-001

When G-001 fires `purchasing_delayed` SSE event:
- Hide cancel button (charge may have committed)
- Switch headline to: "This service is experiencing high demand"
- Switch subtitle to: "Reserving your place in queue" → cycle patience messages
- Add warning: "Please do not close this tab"

---

### H-005 — Step 0 method picker: add Combo card
**Files**: `templates/verify_modern.html`
**Effort**: 20 min
**Priority**: P2

Third card in the 3-column grid (change grid to `1fr 1fr 1fr`):
```html
<button type="button" onclick="chooseMethod('combo')" ...>
    <span style="font-size:36px;">📱📞</span>
    <span style="font-size:16px;font-weight:700;">SMS + Voice</span>
    <span style="font-size:12px;color:#6b7280;">Best coverage</span>
    <span style="font-size:10px;background:#fef3c7;color:#92400e;
          padding:2px 6px;border-radius:4px;font-weight:600;">+$0.50</span>
</button>
```

---

### H-006 — TV webhook auto-re-enable monitor
**Files**: `app/workers/webhook_health_monitor.py` (new), `app/core/lifespan.py`
**Effort**: 1h
**Priority**: P1 — TV disables our webhook after repeated failures (confirmed in screenshot)

TV's API config page states webhooks are auto-disabled after repeated delivery failures.
This happens during deploys when the server is briefly unreachable.

Background task (runs every 30 min):
1. Call TV's webhook status endpoint to check if webhook is still enabled
2. If disabled: call TV's API to re-enable it, log alert
3. If endpoint URL has changed (e.g. new server IP): update it

```python
async def run_webhook_health_monitor():
    while True:
        try:
            tv = TextVerifiedService()
            if tv.enabled:
                # Check webhook status via TV API
                # Re-enable if disabled
                pass
        except Exception as e:
            logger.error(f"Webhook health monitor error: {e}")
        await asyncio.sleep(1800)  # 30 min
```

---

## PROGRESS SUMMARY

| ID | Task | Effort | Priority | Status |
|----|------|--------|----------|--------|
| H-001 | Loading modal: arc spinner + exact TV message sequence | 2.5h | P0 | 📋 |
| H-002 | Step 3: carrier icon + MM:SS countdown + full SMS + reuse btn | 2h | P0 | 📋 |
| H-003 | Step 3 scanning: activity feed log | 1h | P1 | 📋 |
| H-004 | `purchasing_delayed` state | 30 min | P1 | 📋 (blocked G-001) |
| H-005 | Step 0: Combo method picker card | 20 min | P2 | 📋 |
| H-006 | TV webhook auto-re-enable monitor | 1h | P1 | 📋 |
| **Total** | | **~7.5h** | | **0/6** |

---

## EXECUTION ORDER

```
G-001 + G-002  →  H-001 + H-002 + H-003 + H-006  →  H-004  →  H-005
(stop the leak)   (core UX — independent of G)       (needs G-001)  (polish)
```

---

## KEY DIFFERENCES: TV vs VRENUM AFTER THIS SPRINT

| Element | TV today | Vrenum today | Vrenum after H |
|---------|----------|--------------|----------------|
| Loading animation | Arc orbiting icon | Separate spinner | Arc orbiting icon ✓ |
| Loading messages | 11 rotating pairs, 4 phases | 1 static line | 11 rotating pairs ✓ |
| Background colour | Dark (#0f172a) | White card | Dark card ✓ |
| Step 3 carrier | AT&T icon shown | "Auto" text | Carrier icon from area code ✓ |
| Step 3 timer | MM:SS countdown | Elapsed seconds up | MM:SS countdown ✓ |
| Full SMS text | Shown in message box | Hidden | Shown ✓ |
| Reuse CTA | Button with cost + countdown | Banner | Button with cost + countdown ✓ |
| Activity feed | N/A (TV uses modal) | Radar pulse | Scrolling log ✓ |
| Webhook resilience | Auto-disables on failure | No monitor | Auto-re-enable monitor ✓ |
