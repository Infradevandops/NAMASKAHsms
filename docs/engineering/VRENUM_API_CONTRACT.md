# VRENUM PUBLIC API CONTRACT
# Provider-agnostic verification & rental surface — SDK foundation

**Created**: November 2026
**Status**: ✅ Defined
**Authority**: This document defines what the Vrenum public API exposes and what it deliberately hides.
Any new endpoint or SDK method must conform to these objects and naming conventions.

---

## DESIGN PRINCIPLE

Vrenum is a **multi-provider platform**. TextVerified is provider #1 today.
5sim, Telnyx, PVAPins are already wired. More will come.

The public API and SDK expose **Vrenum's abstraction**, not any provider's.
A consumer of the Vrenum API must be able to switch providers on the backend
with zero changes to their integration code.

---

## PUBLIC OBJECTS

### Verification

What API consumers see when they create or query a verification:

```json
{
  "verification_id": "uuid",
  "phone_number": "+1XXXXXXXXXX",
  "service": "telegram",
  "country": "US",
  "capability": "sms",
  "status": "pending",
  "sms_code": null,
  "sms_text": null,
  "cost": 2.63,
  "created_at": "2026-11-10T12:00:00Z",
  "expires_at": "2026-11-10T12:10:00Z"
}
```

| Field | Type | Notes |
|---|---|---|
| `verification_id` | uuid | Vrenum-assigned. Never expose `activation_id` (provider internal) |
| `phone_number` | E.164 string | Always `+1XXXXXXXXXX` format |
| `service` | string | Lowercase slug: `telegram`, `whatsapp`, `google` |
| `country` | ISO 3166-1 alpha-2 | `US`, `GB`, `CA` |
| `capability` | enum | `sms` \| `voice` \| `combo` |
| `status` | enum | `pending` \| `completed` \| `failed` \| `cancelled` \| `expired` |
| `sms_code` | string \| null | Parsed code only. Null until received |
| `sms_text` | string \| null | Full raw SMS. Null until received |
| `cost` | float | Credits charged. Final after any refunds |
| `created_at` | ISO 8601 | UTC |
| `expires_at` | ISO 8601 | UTC. When the number window closes |

### Rental

```json
{
  "rental_id": "uuid",
  "phone_number": "+1XXXXXXXXXX",
  "service": "telegram",
  "country": "US",
  "duration": "1d",
  "status": "active",
  "cost": 15.00,
  "created_at": "2026-11-10T12:00:00Z",
  "expires_at": "2026-11-11T12:00:00Z"
}
```

| Field | Type | Notes |
|---|---|---|
| `rental_id` | uuid | Vrenum-assigned |
| `duration` | enum | `1d` \| `3d` \| `7d` \| `14d` \| `30d` \| `90d` |
| `status` | enum | `active` \| `expired` \| `cancelled` \| `back_ordered` |

### Message (rental inbox)

```json
{
  "message_id": "uuid",
  "rental_id": "uuid",
  "sender": "+1XXXXXXXXXX",
  "text": "Your code is 123456",
  "received_at": "2026-11-10T12:05:00Z"
}
```

### Service

```json
{
  "service_id": "telegram",
  "name": "Telegram",
  "country": "US",
  "capability": "sms",
  "price": 2.63,
  "available": true,
  "estimated_seconds": 30
}
```

---

## WHAT IS DELIBERATELY HIDDEN

These fields exist internally but are **never exposed** in the public API or SDK:

| Internal field | Reason hidden |
|---|---|
| `activation_id` | Provider-internal order ID (TV concept). Use `verification_id` |
| `provider` | Internal routing. Consumer doesn't care which provider served the request |
| `fallback_applied` | Internal telemetry |
| `same_state_fallback` | Internal telemetry |
| `routing_reason` | Internal telemetry |
| `assigned_area_code` | Internal. Consumer requested an area code — they got it or didn't |
| `requested_area_code` | Internal |
| `operator` | Provider-internal carrier name. Not normalised across providers |
| `voip_rejected` | Internal quality signal |
| `retry_attempts` | Internal |
| `ReservationCapability` | TV enum. Use `capability: "sms" \| "voice" \| "combo"` |
| `RentalDuration` | TV enum. Use `duration: "1d" \| "3d" \| ...` |
| `debit_transaction_id` | Internal billing reference |

---

## API ENDPOINTS (public surface)

### Verifications

```http
POST   /api/v1/verify                    # Create verification
GET    /api/v1/verify/{id}               # Get status + code
DELETE /api/v1/verify/{id}               # Cancel (refund if eligible)
GET    /api/v1/verify/history            # List past verifications
```

### Rentals

```http
POST   /api/v1/rentals                   # Create rental
GET    /api/v1/rentals/{id}              # Get rental status
GET    /api/v1/rentals/{id}/messages     # Get received messages
DELETE /api/v1/rentals/{id}              # Cancel rental
GET    /api/v1/rentals                   # List active rentals
```

### Account

```http
GET    /api/v1/balance                   # Current credit balance
GET    /api/v1/services?country=US       # Available services + prices
GET    /api/v1/countries                 # Supported countries
```

### Streaming (SSE)

```http
POST   /api/v1/verify/stream             # SSE purchase stream
```

SSE events (public):

| Event `step` | Meaning |
|---|---|
| `pricing_check` | Confirming availability |
| `balance_check` | Checking credits |
| `purchasing` | Securing number — cancel still allowed |
| `purchasing_delayed` | Taking longer than expected — do not close tab |
| `recording` | Finalising |
| `complete` | Number assigned — includes `verification_id`, `phone_number`, `ends_at` |
| `failed` | Purchase failed — includes `reason` and `message` |

---

## SDK SURFACE (Python + JS — Q2 2026)

### Python

```python
import vrenum

client = vrenum.Client(api_key="vr_...")

# Verify — polls automatically, returns when code arrives or timeout
session = await client.verify("telegram", country="US", capability="sms")
print(session.sms_code)          # "123456"
print(session.phone_number)      # "+17025551234"

# Verify with area code
session = await client.verify("whatsapp", area_code="212")

# Rental
rental = await client.rentals.create("telegram", country="US", duration="1d")
messages = await client.rentals.messages(rental.rental_id)

# Balance
balance = await client.balance()   # float

# Services
services = await client.services(country="US")
```

### JavaScript

```javascript
import { VrenumClient } from '@vrenum/sdk';

const client = new VrenumClient({ apiKey: 'vr_...' });

// Verify
const session = await client.verify('telegram', { country: 'US' });
console.log(session.smsCode);

// Rental
const rental = await client.rentals.create('telegram', { duration: '1d' });
const messages = await client.rentals.messages(rental.rentalId);
```

---

## SDK RETRY POLICY

Vrenum's own retry policy — independent of any provider's internal retry:

| Operation | Attempts | Backoff |
|---|---|---|
| `verify()` purchase | **1** — never retry purchase | — |
| `verify()` status poll | 3 | 2s, 4s, 8s |
| `rentals.create()` | **1** — never retry purchase | — |
| `rentals.messages()` | 3 | 1s, 2s, 4s |
| `balance()` | 3 | 1s, 2s, 4s |
| `services()` | 3 | 1s, 2s, 4s |

**Why no retry on purchase**: Each attempt may charge the provider balance even on failure.
The orphan reconciliation worker handles the case where a purchase succeeded server-side
but the response was lost. Retrying would risk double-charging.

---

## IDEMPOTENCY

All `POST` endpoints accept `X-Idempotency-Key: <uuid>` header.
Duplicate requests with the same key within 24h return the cached response.
SDK generates idempotency keys automatically.

---

## WEBHOOK PAYLOAD (public)

```json
{
  "event": "verification.completed",
  "verification_id": "uuid",
  "phone_number": "+1XXXXXXXXXX",
  "service": "telegram",
  "sms_code": "123456",
  "sms_text": "Your Telegram code is 123456",
  "received_at": "2026-11-10T12:05:00Z"
}
```

Events: `verification.completed` | `verification.failed` | `verification.expired` | `rental.message_received` | `rental.expired`

Signature: `X-Vrenum-Signature: sha256=<hmac>` — computed over raw body with webhook secret.

---

## VERSIONING

- Current version: `v1`
- Breaking changes increment the version: `/api/v2/...`
- Non-breaking additions (new fields, new events) are added without version bump
- Deprecated fields are kept for 6 months with `X-Deprecated` response header
