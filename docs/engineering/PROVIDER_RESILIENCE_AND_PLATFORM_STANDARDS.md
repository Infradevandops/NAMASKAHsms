# PROVIDER RESILIENCE & VRENUM PLATFORM STANDARDS
# Task File — Sprint G

**Created**: November 2026
**Status**: 📋 Not started
**Authority**: This doc defines Vrenum's inhouse retry/timeout standards AND the public SDK/API contract surface.
**Depends on**: `provider_router.py`, `purchase_endpoints.py`, `textverified_service.py`

---

## BRIEF

### The Core Problem

TV's SDK has an **invisible 3× retry** (1s + 2s + 4s = 7s overhead) baked into every call.
The platform's SSE stream has **no explicit timeout** on the purchase call — it relies on nginx
and the browser's EventSource to close the connection after ~15s of silence.

Worst-case timeline for a single `verifications.create()` under load:

```
Thread queue wait (saturated pool):  +5s
TV call attempt 1:                   +3s  → timeout
TV internal retry 1 (1s backoff):    +1s
TV call attempt 2:                   +3s  → timeout
TV internal retry 2 (2s backoff):    +2s
TV call attempt 3:                   +3s  → timeout
TV internal retry 3 (4s backoff):    +4s
─────────────────────────────────────────
Total:                               ~21s
```

Browser drops SSE at ~15s. TV may still assign a number at second 18.
Result: **TV charged, user not charged, no DB record. Silent money leak.**

### The Bigger Picture — Why This Matters for the Platform

Vrenum is a **hybrid multi-provider platform**. TV is provider #1 today.
5sim, Telnyx, PVAPins are already wired. More will come.

Every provider has its own retry behaviour, timeout characteristics, and failure modes.
Vrenum cannot inherit each provider's internal retry policy — it needs its **own standards**
that sit above all providers and apply uniformly regardless of which provider is active.

This is the same reason Vrenum has `ProviderRouter`, `PurchaseResult`, `ProviderError` —
a provider-agnostic contract layer. The timeout/retry/reconciliation layer is the missing piece
of that contract.

---

## ANSWERS TO DESIGN QUESTIONS

### Q: Should Vrenum's inhouse retry delay be 7s or 15s?

**Neither. Vrenum should not retry at the purchase level at all.**

Here's why:

- TV already retries 3× internally. If Vrenum also retries, you get 3 × 3 = 9 TV calls per
  user request. At 50 concurrent users that's 450 TV calls in flight simultaneously.
- Purchase retries are dangerous — each attempt may charge TV's balance even if it fails.
  You can't know if a failed call actually assigned a number until you check `verifications.list()`.
- The correct pattern is: **one attempt, hard timeout, orphan reconciliation**.

Vrenum's inhouse timeout budget:

```
TV call budget:     12s   (under the 15s SSE window, above TV's 7s retry overhead)
SSE stream budget:  25s   (nginx proxy_read_timeout — gives 13s of breathing room)
Orphan window:     120s   (reconciliation worker checks for ghost purchases)
```

The 7s is TV's problem. The 12s is Vrenum's hard ceiling on how long it will wait.
The 25s is the SSE connection lifetime — long enough to reconcile live if needed (see G-003).

### Q: Is orphan reconciliation part of the Vrenum inhouse SDK/API?

**Yes — it's a first-class platform primitive, not a TV-specific hack.**

Every provider can produce orphan purchases:
- TV: invisible retry assigns number after client timeout
- 5sim: network partition between purchase and response
- Telnyx: webhook delivery failure after number assigned
- Future providers: same class of problem

The orphan reconciliation worker is provider-agnostic. It queries each provider's
"recent purchases" endpoint, cross-references against the `verifications` table,
and heals any gaps. It belongs in `app/workers/orphan_reconciliation.py` and is
wired into lifespan alongside the back-order monitor.

### Q: What goes into the Vrenum public SDK and API?

See Sprint G-005 below. Short answer:

The **public API** exposes Vrenum's abstraction, not TV's. Users of the Vrenum API
never see `activation_id`, `ReservationCapability`, `RentalDuration`, or any TV concept.
They see `verification_id`, `capability` (sms/voice/combo), `duration` (1d/3d/7d/30d).

The **public SDK** (Python + JS, planned Q2 2026) wraps the public API with:
- Automatic retry with Vrenum's own backoff (not TV's)
- Idempotency key generation
- Polling helpers (`wait_for_code()`)
- Webhook verification

The SDK does NOT expose provider internals. A user of the Vrenum SDK should be able
to switch from TV to 5sim on the backend with zero SDK changes.

### Q: Does 25s SSE timeout allow live reconciliation?

**Yes, that's the design intent.**

With `asyncio.wait_for(timeout=12s)` on the TV call:
- If TV responds in <12s → normal `complete` SSE event, user sees number immediately
- If TV times out at 12s → `purchasing_delayed` SSE event sent, connection stays open
- Orphan reconciliation worker fires within 60s → finds the ghost purchase → pushes
  `complete` via WebSocket to the user's active session

The SSE connection itself closes after `complete` or `failed`. The 25s window is for
the purchase call. After that, WebSocket takes over for async delivery.

So the flow under delay is:
```
0s:   SSE opens, pricing_check, balance_check, purchasing
12s:  asyncio.wait_for fires → yield sse("purchasing_delayed", message="Taking longer than expected...")
12s:  SSE connection stays open (nginx allows 25s)
18s:  TV assigns number (thread still running)
20s:  Orphan worker detects ghost → creates Verification row → deducts credits
20s:  WebSocket pushes "verification_ready" to user's browser
25s:  SSE closes (nginx timeout) — but user already has number via WS
```

This is why 25s is the right SSE timeout, not 15s. It gives the orphan worker time
to reconcile and deliver via WS before the SSE connection dies.

---

## TASKS

### G-001 — Hard timeout on TV purchase call in SSE stream
**File**: `app/api/verification/purchase_endpoints.py`
**Effort**: 30 min
**Priority**: P0 — stops money leak

Wrap `purchase_with_failover()` in `asyncio.wait_for(timeout=12.0)`.
On `TimeoutError`: yield `purchasing_delayed` SSE event (not `failed`),
write a pending reconciliation record to Redis, keep SSE open.

```python
# Redis key: purchase_pending:{user_id}:{service}:{started_at_unix}
# TTL: 120s
# Value: {user_id, service, country, capability, area_code, cost, started_at}
```

Do NOT yield `failed` on timeout — the purchase may still succeed server-side.
`failed` is only for confirmed provider errors.

---

### G-002 — SSE keepalive ping + nginx timeout fix
**Files**: `app/api/verification/purchase_endpoints.py`, server nginx config
**Effort**: 30 min
**Priority**: P0 — prevents browser dropping connection before reconciliation

Add a background keepalive task inside `event_stream()` that yields
`": keepalive\n\n"` every 5s. SSE comments are ignored by browsers but
reset nginx's idle timeout counter.

```python
async def _keepalive(stop_event: asyncio.Event):
    while not stop_event.is_set():
        await asyncio.sleep(5)
        if not stop_event.is_set():
            yield ": keepalive\n\n"
```

Server nginx config (deploy step, not code):
```nginx
proxy_read_timeout 30s;
proxy_send_timeout 30s;
```

---

### G-003 — Orphan reconciliation worker
**File**: `app/workers/orphan_reconciliation.py` (new)
**Effort**: 2h
**Priority**: P1 — safety net for G-001

Background loop (60s interval). For each provider:
1. Read all `purchase_pending:*` keys from Redis
2. Query provider's recent verifications (TV: `verifications.list()` last 5 min)
3. Match by `(service, started_at ± 30s)` — no activation_id available yet
4. On match: create `Verification` row, deduct credits, push WS `verification_ready`
5. On no match after 120s: yield `failed` via WS, clean up Redis key

Provider interface addition (all adapters must implement):
```python
async def list_recent_purchases(self, since_seconds: int = 300) -> list[dict]:
    """Return purchases made in the last N seconds. Provider-agnostic shape:
    [{order_id, phone_number, service, created_at, cost, status}]
    """
```

This is the first method that goes into the **Vrenum provider contract** beyond
`purchase_number()` and `cancel()`.

---

### G-004 — Provider contract: timeout + retry standards
**File**: `app/services/providers/base_provider.py`
**Effort**: 1h
**Priority**: P1 — enforces standards across all current + future providers

Add to `SMSProvider` base class:

```python
# Vrenum inhouse standards — all providers must respect these
PURCHASE_TIMEOUT_S: float = 12.0   # Hard ceiling on purchase call
CANCEL_TIMEOUT_S: float = 5.0      # Cancel must be fast
STATUS_TIMEOUT_S: float = 8.0      # Status check ceiling
MAX_PURCHASE_ATTEMPTS: int = 1     # Vrenum never retries at purchase level
                                   # Provider's own internal retry is their business
                                   # but Vrenum's timeout overrides it
```

Add `asyncio.wait_for(timeout=self.PURCHASE_TIMEOUT_S)` wrapper in
`TextVerifiedAdapter.purchase_number()`, `FiveSimAdapter.purchase_number()`,
`TelnyxAdapter.purchase_number()`, `PVAPinsAdapter.purchase_number()`.

This means the 12s timeout is enforced at the adapter level, not just in the SSE
endpoint — so the legacy `/request` path is also protected.

---

### G-005 — Vrenum public API contract definition
**File**: `docs/engineering/VRENUM_API_CONTRACT.md` (new)
**Effort**: 2h (doc only, no code)
**Priority**: P2 — foundation for SDK

Define the provider-agnostic surface that the public API and SDK expose.
Nothing TV-specific leaks through.

**Public verification object** (what API consumers see):
```json
{
  "verification_id": "uuid",
  "phone_number": "+1XXXXXXXXXX",
  "service": "telegram",
  "country": "US",
  "capability": "sms | voice | combo",
  "status": "pending | completed | failed | cancelled | expired",
  "sms_code": "123456",
  "cost": 2.63,
  "created_at": "ISO8601",
  "expires_at": "ISO8601"
}
```

**What is deliberately hidden from public API**:
- `activation_id` (TV internal) → use `verification_id`
- `ReservationCapability` → use `capability`
- `RentalDuration` enum → use `duration_hours` integer
- `provider` field → internal routing, not exposed
- `fallback_applied`, `same_state_fallback` → internal telemetry
- `routing_reason` → internal telemetry

**Public rental object**:
```json
{
  "rental_id": "uuid",
  "phone_number": "+1XXXXXXXXXX",
  "service": "telegram",
  "country": "US",
  "duration": "1d | 3d | 7d | 14d | 30d | 90d",
  "status": "active | expired | cancelled | back_ordered",
  "cost": 15.00,
  "expires_at": "ISO8601"
}
```

**Vrenum SDK methods** (Python + JS, Q2 2026):
```python
client.verify(service, country, capability="sms", area_code=None)
    → VerificationSession  # polls automatically, yields code

client.rentals.create(service, country, duration="1d")
    → Rental

client.rentals.messages(rental_id)
    → list[Message]

client.balance()
    → float

client.services(country="US")
    → list[Service]
```

SDK retry policy (Vrenum's own, not TV's):
- `verify()`: no retry on purchase, 3× retry on status poll (2s, 4s, 8s)
- `rentals.create()`: no retry
- All other reads: 3× retry with exponential backoff

---

### G-006 — Provider health circuit breaker
**File**: `app/services/providers/circuit_breaker.py` (new)
**Effort**: 2h
**Priority**: P2 — enables safe multi-provider expansion

Simple per-provider circuit breaker. Three states: CLOSED (normal), OPEN (failing),
HALF-OPEN (testing recovery).

```python
class CircuitBreaker:
    failure_threshold: int = 5      # open after 5 failures in window
    window_seconds: int = 60        # rolling window
    recovery_timeout: int = 30      # try again after 30s in OPEN state
    half_open_max_calls: int = 1    # only 1 test call in HALF-OPEN
```

`ProviderRouter.get_provider()` checks circuit state before routing.
If primary is OPEN, skip directly to failover without attempting the call.

This is what makes the multi-provider architecture actually safe at scale —
a degraded TV doesn't cascade into 50 concurrent 12s timeouts.

---

## PROGRESS SUMMARY

| ID | Task | Effort | Priority | Status |
|----|------|--------|----------|--------|
| G-001 | Hard timeout (12s) on TV purchase in SSE | 30 min | P0 | 📋 |
| G-002 | SSE keepalive + nginx 30s timeout | 30 min | P0 | 📋 |
| G-003 | Orphan reconciliation worker | 2h | P1 | 📋 |
| G-004 | Provider contract: timeout standards in base_provider | 1h | P1 | 📋 |
| G-005 | Vrenum public API contract doc + SDK surface definition | 2h | P2 | 📋 |
| G-006 | Per-provider circuit breaker | 2h | P2 | 📋 |
| **Total** | | **~8h** | | **0/6** |

---

## EXECUTION ORDER

```
G-001 + G-002  →  deploy  →  G-003  →  G-004  →  G-005  →  G-006
(stop the leak)   (nginx)   (safety net)  (standards)  (contract)  (scale)
```

G-001 and G-002 are the only ones that need to ship before the next deploy.
G-003 through G-006 can be a single sprint after that.

---

## WHAT THIS IS NOT

- Not a GraphQL layer. REST is the right call for this platform at this scale.
  GraphQL adds schema maintenance overhead with zero benefit when the query surface
  is well-defined (verify, rent, check balance, list services).

- Not a provider abstraction rewrite. `ProviderRouter`, `PurchaseResult`, `ProviderError`
  are already the right abstraction. This sprint adds the missing resilience layer on top.

- Not TV-specific. Every task here applies equally to 5sim, Telnyx, PVAPins, and any
  provider added in the future. That's the point.
