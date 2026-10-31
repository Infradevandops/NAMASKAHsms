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

## Phase 6 — TV Webhook for Instant SMS Delivery (Eliminates Polling)

### What TV Sends

TV POSTs to our endpoint URL when an SMS arrives. Payload structure (from SDK):

```json
{
  "id": "evt_abc123",
  "event": "sms.received",
  "attempt": 1,
  "occurredAt": "2026-10-31T04:23:00Z",
  "data": {
    "to": "+17022853600",
    "from": "+12025551234",
    "smsContent": "Your WhatsApp code is 876-094",
    "parsedCode": "876094",
    "reservationId": "tv_verification_id_here",
    "createdAt": "2026-10-31T04:23:00Z",
    "encrypted": false
  }
}
```

TV retries on failure. After repeated failures TV auto-disables the webhook and requires manual re-enable.

### Registration

TV's webhook UI (app.textverified.com → API Configuration → API Webhooks):
- Enable Webhooks toggle
- Endpoint URL field
- Save + Send Test buttons

Set endpoint URL to: `https://vrenum.app/api/verification/webhook/tv`

### Step 6a — Webhook endpoint

**New file:** `app/api/verification/tv_webhook.py`

```python
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.core.unified_cache import cache
from app.models.verification import Verification
from app.websocket.manager import websocket_manager
import logging, json

router = APIRouter(prefix="/api/verification/webhook", tags=["tv-webhook"])
logger = logging.getLogger(__name__)

_SEEN_KEY = "tv:webhook:seen:{}"  # dedup by event id, TTL 24h

@router.post("/tv")
async def tv_sms_webhook(request: Request, db: Session = Depends(get_db)):
    """Receive SMS delivery webhooks from TextVerified.
    Eliminates polling — SMS arrives here instantly.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_id = payload.get("id", "")
    event_type = payload.get("event", "")

    # Deduplicate (TV retries on failure)
    if event_id:
        seen_key = _SEEN_KEY.format(event_id)
        if await cache.get(seen_key):
            return {"ok": True, "duplicate": True}
        await cache.set(seen_key, 1, ttl=86400)

    if event_type != "sms.received":
        # Accept but ignore non-SMS events (billing, backorder, etc.)
        return {"ok": True}

    data = payload.get("data", {})
    reservation_id = data.get("reservationId")  # TV's verification ID = our activation_id
    phone_number = data.get("to")
    sms_content = data.get("smsContent", "")
    parsed_code = data.get("parsedCode", "")

    if not reservation_id and not phone_number:
        logger.warning(f"TV webhook missing reservationId and to: {payload}")
        return {"ok": True}

    # Find our verification by activation_id (TV's reservation ID)
    verification = None
    if reservation_id:
        verification = (
            db.query(Verification)
            .filter(Verification.activation_id == reservation_id)
            .first()
        )
    if not verification and phone_number:
        # Fallback: match by phone number (strip formatting)
        clean = phone_number.replace("+", "").replace("-", "").replace(" ", "")
        verification = (
            db.query(Verification)
            .filter(
                Verification.phone_number.contains(clean[-10:]),
                Verification.status == "pending",
            )
            .order_by(Verification.created_at.desc())
            .first()
        )

    if not verification:
        logger.warning(f"TV webhook: no verification found for reservationId={reservation_id} phone={phone_number}")
        return {"ok": True}  # Return 200 so TV doesn't retry

    if verification.status != "pending":
        return {"ok": True}  # Already completed

    # Update verification
    verification.status = "completed"
    verification.sms_code = parsed_code or _extract_code(sms_content)
    verification.sms_text = sms_content
    db.commit()

    logger.info(
        f"TV webhook: SMS delivered for verification {verification.id} "
        f"user={verification.user_id} code={verification.sms_code}"
    )

    # Push to user via WebSocket (instant delivery to browser)
    try:
        await websocket_manager.send_to_user(
            str(verification.user_id),
            {
                "type": "sms_received",
                "verification_id": str(verification.id),
                "sms_code": verification.sms_code,
                "sms_text": sms_content,
                "phone_number": verification.phone_number,
            }
        )
    except Exception as e:
        logger.warning(f"WebSocket push failed (non-fatal): {e}")

    return {"ok": True}


def _extract_code(text: str) -> str:
    """Fallback code extraction if parsedCode is empty."""
    import re
    hyphen = re.findall(r"\b(\d{3}-\d{3})\b", text)
    plain = re.findall(r"\b(\d{4,8})\b", text)
    if hyphen:
        return hyphen[-1].replace("-", "")
    if plain:
        return plain[-1]
    return ""
```

### Step 6b — Mount the router

**File:** `main.py` (or wherever verification routers are mounted)

```python
from app.api.verification.tv_webhook import router as tv_webhook_router
app.include_router(tv_webhook_router)
```

### Step 6c — Frontend: listen for WebSocket `sms_received` event

**File:** `static/js/verification-flow.js`

In the WebSocket message handler (or in `startPolling`):

```js
// In the existing WebSocket notification handler or add to sms-websocket.js:
if (message.type === 'sms_received' &&
    message.verification_id === VerificationFlow.verificationId) {
    // Instant delivery — no polling needed
    stopPolling();
    document.getElementById('sms-code').textContent = message.sms_code;
    document.getElementById('code-received').style.display = 'block';
    document.querySelector('.scanning-container').style.display = 'none';
    window.toast.success('SMS code received!');
    playArrivalSound();
    if (localStorage.getItem('nsk_auto_copy') === 'true') {
        navigator.clipboard.writeText(message.sms_code).catch(() => {});
    }
    localStorage.removeItem('active_verification_id');
}
```

Polling remains as fallback for when WebSocket is disconnected.

### Step 6d — Register webhook URL with TV

After deploying:
1. Go to app.textverified.com → API Configuration → API Webhooks
2. Enable Webhooks toggle ON
3. Endpoint URL: `https://vrenum.app/api/verification/webhook/tv`
4. Click Save
5. Click Send Test — verify our endpoint returns `{"ok": true}`

### Webhook Acceptance Criteria

- [ ] `POST /api/verification/webhook/tv` returns 200 for all TV event types
- [ ] Duplicate events (same `id`) are silently ignored
- [ ] SMS code updates verification status to `completed` in DB
- [ ] WebSocket push delivers code to browser instantly
- [ ] Polling continues as fallback if WebSocket disconnected
- [ ] TV's "Send Test" button returns success
- [ ] Non-SMS events (billing, backorder) accepted but ignored
- [ ] Endpoint registered in TV dashboard

---

## Files to Modify (Complete List)

| File | Change |
|------|--------|
| `app/api/verification/purchase_endpoints.py` | Add `ends_at`/`created_at` to response; add SSE endpoint |
| `app/api/verification/tv_webhook.py` | **New file** — TV SMS webhook receiver |
| `app/services/textverified_service.py` | Add `check_service_available()` |
| `static/js/verification-flow.js` | Dynamic window, SSE client, orphan recovery, WebSocket SMS handler |
| `templates/verify_modern.html` | Loading state card |
| `main.py` | Mount tv_webhook router |
