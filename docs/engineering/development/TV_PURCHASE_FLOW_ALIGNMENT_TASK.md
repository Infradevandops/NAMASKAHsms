# Task: TV Purchase Flow — Correct Implementation

**Status:** Ready to implement
**Priority:** Critical
**Area:** Verification purchase flow end-to-end
**Created:** October 31, 2026

---

## The Core Problem

Our verification flow is built on wrong assumptions about how TV works.
Three bugs compound each other:

1. **Wrong window duration** — hardcoded 2 min, TV gives variable duration (observed ~60 min for WhatsApp). We cancel valid verifications and refund users who still have 58 minutes left.
2. **No real pre-purchase check** — we charge first, fail after. TV checks availability before charging.
3. **Blocking purchase with no feedback** — `verifications.create()` can take 5-30s. User sees a spinner with no information. If it takes long they think it's broken.

---

## Principle: Every Step Must Be Real

TV's loading states ("Checking carrier networks", "Scanning number blocks") are UX animations on their side — their public API does not expose those internal steps. We do NOT copy fake animations.

**What we DO have that is real:**
- `POST /api/pub/v2/pricing/verifications` — confirms service is purchasable right now, returns exact price. Fails if service unavailable.
- `verifications.create()` — single blocking call, takes 5-30s, returns `VerificationExpanded` with real `ends_at`
- `ends_at` on `VerificationExpanded` — exact expiry timestamp from TV. Use this, never hardcode duration.
- `GET /api/pub/v2/services` — real quantity per service (already implemented, 2-min refresh)

**Architecture: SSE streaming purchase**

Replace the single blocking POST with a Server-Sent Events stream. Each event maps to a real backend operation:

```
Frontend opens SSE to POST /api/verification/request/stream
  ↓
Backend streams:
  {step: "pricing_check",  msg: "Confirming availability..."}   ← real TV pricing call
  {step: "balance_check",  msg: "Checking your balance..."}     ← real DB query
  {step: "purchasing",     msg: "Securing your number..."}      ← verifications.create() blocks here (5-30s)
  {step: "validating",     msg: "Validating number..."}         ← VOIP/area code check
  {step: "recording",      msg: "Almost done..."}               ← DB write + debit
  {step: "complete",       phone_number, ends_at, verification_id, created_at}
  OR
  {step: "failed",         reason: "no_inventory"|"insufficient_balance"|..., message: "..."}
```

"Cancel (you will not be charged)" is shown until `purchasing` step completes — because that's when the charge actually happens.

---

## Files to Change

```
app/api/verification/purchase_endpoints.py   — add SSE endpoint, add ends_at to response
app/services/textverified_service.py         — add check_service_available()
static/js/verification-flow.js               — SSE client, dynamic window from ends_at, orphan recovery
templates/verify_modern.html                 — loading state card
```

---

## Implementation Walkthrough

### Step 1 — Add `ends_at` + `created_at` to existing purchase response

**File:** `app/api/verification/purchase_endpoints.py`

In the `response` dict (around line 661), add:
```python
"ends_at": purchase_result.expires_at,          # from VerificationExpanded.ends_at
"created_at": verification.created_at.isoformat(),
```

`purchase_result.expires_at` is already set in `textverified_adapter.py` from `result["ends_at"]`.

---

### Step 2 — Add `check_service_available()` to TextVerifiedService

**File:** `app/services/textverified_service.py`

New method — calls TV pricing endpoint before purchase to confirm service is available:

```python
async def check_service_available(self, service_name: str) -> dict:
    """Pre-purchase availability check via TV pricing endpoint.
    Returns {available: bool, price: float|None, reason: str|None}
    """
    if not self.enabled:
        return {"available": False, "reason": "provider_disabled"}
    try:
        self.client.refresh_bearer()
        resp = self.client.session.post(
            f"{self.client.base_url}/api/pub/v2/pricing/verifications",
            headers={"Authorization": f"Bearer {self.client.bearer.token}",
                     "User-Agent": self.client.user_agent},
            json={"serviceName": service_name, "areaCode": False,
                  "carrier": False, "numberType": "mobile", "capability": "sms"},
            timeout=8.0,
        )
        if resp.ok:
            data = resp.json()
            payload = data.get("data", data)
            price = payload.get("price")
            if price is not None and float(price) > 0:
                return {"available": True, "price": float(price)}
            return {"available": False, "reason": "no_inventory"}
        return {"available": False, "reason": f"http_{resp.status_code}"}
    except Exception as e:
        return {"available": False, "reason": str(e)}
```

---

### Step 3 — SSE streaming endpoint

**File:** `app/api/verification/purchase_endpoints.py`

Add new route alongside existing POST:

```python
from fastapi.responses import StreamingResponse
import json as _json

@router.post("/request/stream")
async def create_verification_stream(request: VerificationRequest, ...):
    """SSE streaming purchase — each event maps to a real operation."""

    async def event_stream():
        def sse(step, **kwargs):
            data = _json.dumps({"step": step, **kwargs})
            return f"data: {data}\n\n"

        # Step 1: pricing check (real TV API call)
        yield sse("pricing_check", message="Confirming availability with provider...")
        tv_svc = TextVerifiedService()
        check = await tv_svc.check_service_available(request.service)
        if not check["available"]:
            yield sse("failed", reason="no_inventory",
                      message="No numbers available for this service right now.")
            return

        # Step 2: balance check (real DB query)
        yield sse("balance_check", message="Checking your balance...")
        user = db.query(User).filter(User.id == user_id).first()
        price = check["price"]
        if float(user.credits or 0) < price:
            yield sse("failed", reason="insufficient_balance",
                      message="Insufficient balance. Please add credits.")
            return

        # Step 3: purchase (real TV create — blocks 5-30s)
        yield sse("purchasing", message="Securing your number...")
        try:
            purchase_result = await provider_router.purchase_with_failover(...)
        except ProviderError as e:
            await record_purchase_outcome(request.service, False)
            yield sse("failed", reason=e.category, message=e.user_message)
            return

        # Step 4: validate (VOIP/area code — our logic)
        yield sse("validating", message="Validating number quality...")

        # Step 5: record (DB write + debit)
        yield sse("recording", message="Almost done...")
        # ... DB operations ...

        # Step 6: complete
        yield sse("complete",
                  verification_id=str(verification.id),
                  phone_number=purchase_result.phone_number,
                  ends_at=purchase_result.expires_at,
                  created_at=verification.created_at.isoformat(),
                  cost=actual_cost)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

Keep existing `POST /request` intact for API key users and backward compat.

---

### Step 4 — Frontend: dynamic window from `ends_at`

**File:** `static/js/verification-flow.js`

**Remove hardcoded duration:**
```js
// REMOVE THIS:
const totalDurationMs = 120000; // 2 minutes standard

// REPLACE WITH (computed once on first poll or from purchase response):
if (!VerificationFlow.totalDurationMs && data.ends_at && data.created_at) {
    VerificationFlow.totalDurationMs =
        new Date(data.ends_at) - new Date(data.created_at);
}
const totalDurationMs = VerificationFlow.totalDurationMs || 3600000; // fallback 60min
```

**Store `ends_at` from purchase response:**
```js
// In createVerification() success handler:
VerificationFlow.endsAt = data.ends_at;
VerificationFlow.createdAt = data.created_at;
VerificationFlow.totalDurationMs =
    new Date(data.ends_at) - new Date(data.created_at);
```

**Update polling timeout:**
```js
// Auto-timeout only when server's ends_at is reached, not after 2 min:
if (remainingMs <= 0) {
    stopPolling();
    window.toast.error('Verification window closed.');
    goBack();
    return;
}
```

---

### Step 5 — Frontend: SSE client for purchase

**File:** `static/js/verification-flow.js`

Replace `createVerification()` fetch with SSE:

```js
async function createVerification() {
    // ... validation ...

    showPurchaseLoadingState("Confirming availability...");

    const response = await fetch('/api/verification/request/stream', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ service: serviceId, country: 'US', capability: 'sms', ... })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const lines = decoder.decode(value).split('\n');
        for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            const event = JSON.parse(line.slice(6));

            switch (event.step) {
                case 'pricing_check':
                    updateLoadingMessage("Confirming availability...");
                    break;
                case 'balance_check':
                    updateLoadingMessage("Checking your balance...");
                    break;
                case 'purchasing':
                    updateLoadingMessage("Securing your number...");
                    hideCancelButton(); // charge is happening now
                    break;
                case 'validating':
                    updateLoadingMessage("Validating number...");
                    break;
                case 'recording':
                    updateLoadingMessage("Almost done...");
                    break;
                case 'complete':
                    hidePurchaseLoadingState();
                    VerificationFlow.verificationId = event.verification_id;
                    VerificationFlow.endsAt = event.ends_at;
                    VerificationFlow.createdAt = event.created_at;
                    VerificationFlow.totalDurationMs =
                        new Date(event.ends_at) - new Date(event.created_at);
                    localStorage.setItem('active_verification_id', event.verification_id);
                    document.getElementById('phone-number').textContent =
                        formatPhone(event.phone_number);
                    updateProgress(3);
                    startPolling();
                    break;
                case 'failed':
                    hidePurchaseLoadingState();
                    await record_purchase_outcome_frontend(serviceId, false);
                    showError(event.message);
                    break;
            }
        }
    }
}
```

---

### Step 6 — Loading state card in template

**File:** `templates/verify_modern.html`

Add between step-2-card and step-3-card:

```html
<!-- Purchase Loading State -->
<div class="verification-card" id="purchase-loading-card" style="display:none; text-align:center;">
    <div style="font-size:48px; margin-bottom:16px;">
        <img id="loading-service-icon" src="" style="width:64px;height:64px;border-radius:12px;">
    </div>
    <div class="scanning-text" id="purchase-loading-message">Confirming availability...</div>
    <div style="margin-top:24px;">
        <div style="width:48px;height:48px;border:3px solid rgba(254,60,114,0.2);
             border-top-color:#FE3C72;border-radius:50%;animation:spin 0.8s linear infinite;
             margin:0 auto;"></div>
    </div>
    <button id="purchase-cancel-btn" class="btn btn-secondary"
            style="margin-top:24px; width:100%;"
            onclick="cancelPurchase()">
        Cancel (you will not be charged)
    </button>
</div>
```

---

### Step 7 — Orphaned verification recovery

**File:** `static/js/verification-flow.js`

In `DOMContentLoaded`:

```js
// Check for orphaned active verification
const orphanId = localStorage.getItem('active_verification_id');
if (orphanId) {
    const token = localStorage.getItem('access_token');
    fetch(`/api/verification/status/${orphanId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
    }).then(r => r.json()).then(data => {
        if (data.status === 'pending') {
            // Restore active session
            VerificationFlow.verificationId = orphanId;
            if (data.ends_at) {
                VerificationFlow.endsAt = data.ends_at;
                VerificationFlow.totalDurationMs =
                    new Date(data.ends_at) - Date.now() + (Date.now() - new Date(data.created_at));
            }
            document.getElementById('phone-number').textContent =
                formatPhone(data.phone_number);
            updateProgress(3);
            startPolling();
            window.toast && window.toast.info('Resuming your active verification.');
        } else {
            localStorage.removeItem('active_verification_id');
        }
    }).catch(() => localStorage.removeItem('active_verification_id'));
}
```

---

## Acceptance Criteria

- [ ] Verification countdown uses real `ends_at` from TV — no hardcoded duration
- [ ] Progress bar fills over actual window (could be 10 min or 60 min depending on service)
- [ ] "Cancel (you will not be charged)" visible until `purchasing` step fires
- [ ] Cancel button disappears once charge is committed
- [ ] Each loading message maps to a real backend operation
- [ ] If pricing check fails → user sees error immediately, no charge
- [ ] If balance insufficient → user sees error immediately, no charge
- [ ] If TV create fails → user sees specific error, no charge
- [ ] Navigating away during active verification → returning to /verify restores session
- [ ] `localStorage.active_verification_id` cleared on completion/failure/cancel
- [ ] Existing `POST /api/verification/request` still works (API key users)

---

## What We Are NOT Doing

- Not copying TV's "Checking carrier networks / Pinging AT&T" animations — those are TV's internal UX with no API backing
- Not giving users 60 minutes by default — we give them whatever TV's `ends_at` says
- Not implementing the reuse feature (TV's "Use again for 0.75 credits") — future task
- Not implementing TV webhooks yet — future task (eliminates polling entirely)
