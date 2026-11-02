# TextVerified API — Real Flow (SDK Source Truth)

**Created**: October 25, 2026
**Updated**: October 25, 2026 — corrections after full SDK cross-reference
**Source**: `textverified==0.1.0a1` wheel extracted from PyPI — every `.py` file read
**SDK Repo**: https://github.com/Westbold/PythonClient
**Purpose**: Ground-truth reference for gap analysis and stock/UI fix planning

> **Verification note**: All claims cross-referenced against both SDK source and platform code.
> Claims marked ⚠️ UNVERIFIED require a live test from the VPS — Cloudflare blocks direct
> curl from dev machines.

---

## 1. What the SDK Actually Is

`textverified==0.1.0a1` is an alpha package published August 2025 by Westbold LLC.
It is a thin REST wrapper — no caching, no retry beyond 429/5xx, no async.
Every method is **synchronous and blocking**. Our platform wraps it in `asyncio.to_thread()`.

Auth flow (from `textverified.py`):
```
POST /api/pub/v2/auth
Headers: X-API-KEY, X-API-USERNAME
Response: { token, expiresAt }
→ Bearer token stored, refreshed automatically before every request
```

The SDK mounts a `requests.Session` with `Retry(total=3, status_forcelist=[429,500,502,503,504], backoff_factor=1)`.
That means on a 503 it will silently retry 3 times with 1s/2s/4s backoff before raising.
**Our platform does not know this is happening** — the `asyncio.to_thread()` call just blocks longer.

---

## 2. Services Endpoint — What It Actually Returns

```python
# services_api.py
GET /api/pub/v2/services?numberType=mobile&reservationType=verification
→ List[Service]

@dataclass
class Service:
    service_name: str   # slug e.g. "whatsapp"
    capability: ReservationCapability  # "sms" | "voice" | "smsAndVoiceCombo"
```

**That is all.** The SDK `Service` object has exactly 2 fields: `service_name` and `capability`.

**No price. No quantity. No stock signal whatsoever.**

This is the critical truth our previous docs got wrong. The services list endpoint does NOT return price or quantity. Our `fetch_raw_services_with_quantity()` bypasses the SDK and hits the raw JSON endpoint directly trying to read `quantity`, `qty`, `availableCount` etc. — those fields do not exist in the SDK schema and are not guaranteed by TV's API contract.

### What `price=null` actually means

There is no `price` field on the services list response at all. The `price` our platform reads comes from a **separate pricing endpoint** called per-service. When our code says "price=null means out of stock" — that is our own inference, not a TV API contract.

The real availability signal from TV is: **if `verifications.pricing()` raises or returns a price of 0, the service is unavailable.**

---

## 3. Pricing Endpoint — Real Signature

```python
# verifications_api.py
POST /api/pub/v2/pricing/verifications
Body: VerificationPriceCheckRequest

@dataclass
class VerificationPriceCheckRequest:
    service_name: str
    area_code: bool       # True = you want area code filtering (affects price)
    carrier: bool         # True = you want carrier filtering (affects price)
    number_type: NumberType   # "mobile" | "voip" | "landline"
    capability: ReservationCapability  # "sms" | "voice" | "smsAndVoiceCombo"

→ PricingSnapshot

@dataclass
class PricingSnapshot:
    service_name: str
    price: float          # total cost — this is the ONLY field returned
```

**Key facts from the real SDK:**

1. The pricing endpoint is at `/api/pub/v2/pricing/verifications` — NOT `/api/pub/v2/verifications/pricing` as our `check_service_available()` and `_fetch_prices_inline()` currently call. **Our platform is hitting the wrong URL.**

2. `area_code` and `carrier` are **booleans** (do you want filtering?), not the actual area code value. Passing `area_code=True` means "I want area code filtering" and TV charges more for it.

3. `capability` is required and affects price. Voice costs more than SMS. `smsAndVoiceCombo` exists as a third option our platform never uses.

4. `PricingSnapshot` only has `service_name` and `price`. No `quantity` field. Ever.

5. The SDK's `pricing()` method auto-converts a `NewVerificationRequest` to a `VerificationPriceCheckRequest` and sets `number_type=NumberType.VOIP` when `capability=VOICE`. Our raw HTTP call in `check_service_available()` always sends `"numberType": "mobile"` even for voice — this is wrong per the SDK's own conversion logic.

---

## 4. Verification Create — Real Flow

```python
# verifications_api.py
POST /api/pub/v2/verifications
Body: NewVerificationRequest

@dataclass
class NewVerificationRequest:
    service_name: str
    capability: ReservationCapability
    area_code_select_option: Optional[List[str]]  # ordered preference list
    carrier_select_option: Optional[List[str]]
    service_not_listed_name: Optional[str]
    max_price: Optional[float]                    # TV-side price guard
```

**Two-step response** (this is not documented anywhere in our codebase):

```
Step 1: POST /api/pub/v2/verifications
        → Response body is an ACTION object (href + method), not the verification
        
Step 2: Follow the action href (GET /api/pub/v2/verifications/{id})
        → Returns VerificationExpanded
```

Our platform calls `self.client.verifications.create(...)` which handles both steps internally. But if the second step (following the action) fails or times out, we get an exception with no verification ID — meaning we cannot cancel or report the number TV may have already assigned.

```python
@dataclass
class VerificationExpanded:
    number: str
    created_at: datetime
    ends_at: datetime
    id: str
    cancel: CancelAction       # { can_cancel: bool }
    reactivate: ReactivationAction  # { can_reactivate: bool }
    report: ReportAction       # { can_report: bool }
    reuse: ReuseAction         # { reusable_until: Optional[datetime] }
    service_name: str
    state: ReservationState
    total_cost: float
```

**No `carrier` field. No `audio_url`. No `transcription`.** These do not exist on `VerificationExpanded`. Our `get_verification_details()` tries to read `tv.carrier` and `tv.carrier_name` — both will always be `None` because the SDK dataclass does not have those fields.

### ReservationState — Full Enum (our code only handles a subset)

```
verificationPending
verificationCompleted
verificationCanceled
verificationTimedOut
verificationReported
verificationRefunded
verificationReused
verificationReactivated
renewableActive / renewableOverdue / renewableExpired / renewableRefunded
nonrenewableActive / nonrenewableExpired / nonrenewableRefunded
```

Our platform maps TV state to our own `pending/completed/failed` — but we never check `verificationReused` or `verificationReactivated`. These are real states TV can return.

---

## 5. SMS Polling — Real Behaviour

```python
# sms_api.py
sms.incoming(
    data=verification_obj,   # VerificationExpanded
    timeout=600.0,
    polling_interval=1.0,    # default 1s — our code passes 3.0
    since=datetime,
    wake_number=False,
)
→ Iterator[Sms]
```

**What `incoming()` actually does (from source):**

```python
earliest_msg = since - timedelta(seconds=polling_interval)  # leniency window
already_seen = set()

while time.monotonic() - start_time < timeout:
    time.sleep(polling_interval)
    all_messages = self.list(data=data, ...)   # GET /api/pub/v2/sms?to={number}
    unseen = [m for m in all_messages if m.id not in already_seen and m.created_at > earliest_msg]
    if unseen:
        for msg in unseen:
            already_seen.add(msg.id)
            yield msg
        return   # ← EXITS after first batch
```

**Critical facts:**

1. `incoming()` calls `sms.list()` on every poll tick. `sms.list()` is a paginated GET — it fetches ALL SMS for that number, not just new ones. On every 3-second tick our platform makes a full paginated fetch.

2. `incoming()` **exits after the first batch of unseen messages** — it does not keep yielding. Our `poll_sms_standard()` iterates it with `for sms in self.client.sms.incoming(...)` and returns on the first yield. This is correct behaviour but means if TV delivers two SMS simultaneously, only the first batch is processed.

3. The `Sms` dataclass:
```python
@dataclass
class Sms:
    id: str
    to_value: str
    created_at: datetime
    encrypted: bool
    from_value: Optional[str]
    sms_content: Optional[str]
    parsed_code: Optional[str]
```
**No `audio_url`. No `transcription`.** Voice verifications deliver their result through the same `Sms` object with `sms_content` containing the transcription text. There is no separate audio URL field in the SDK. Our code looking for `audio_url` and `transcription` attributes on the SMS object will always get `None`.

4. `sms.list()` fetches by `to` (the phone number), not by verification ID. This means if a number was recycled and used for a previous verification, `sms.list()` returns ALL historical SMS to that number. The `since` filter in `incoming()` is the only guard against stale SMS — and it uses `earliest_msg = since - polling_interval` which adds a leniency window that could let in SMS from 3 seconds before the verification was created.

---

## 6. Verification Actions — What Each Does

| Action | SDK method | TV endpoint | When valid |
|--------|-----------|-------------|------------|
| Cancel | `verifications.cancel(id)` | `POST /api/pub/v2/verifications/{id}/cancel` | `can_cancel=True` |
| Report | `verifications.report(id)` | `POST /api/pub/v2/verifications/{id}/report` | `can_report=True` |
| Reactivate | `verifications.reactivate(id)` | `POST /api/pub/v2/verifications/{id}/reactivate` | `can_reactivate=True` |
| Reuse | `verifications.reuse(id)` | `POST /api/pub/v2/verifications/{id}/reuse` | `reusable_until` not None |

**Reactivate and Reuse are never used by our platform.** These are real TV features:
- **Reactivate**: Resume a timed-out verification (extends the window). Free retry without repurchasing.
- **Reuse**: Use the same number for a different service verification. Costs less than a new purchase.

Both could reduce refund rates and cost significantly for users who need to retry.

---

## 7. The Real Stock Problem — Root Cause from SDK

The services list (`GET /api/pub/v2/services`) returns `service_name` + `capability` only. **No price, no quantity.**

To know if a service is in stock you must call the pricing endpoint per service. If it returns a price > 0, it's in stock. If it raises a `TextVerifiedError`, it's out of stock.

Our stock monitor calls `fetch_raw_services_with_quantity()` which bypasses the SDK and hits the raw JSON endpoint looking for `quantity` fields. The SDK schema (`Service` dataclass) has no quantity field — meaning TV's API contract does not guarantee that field exists. It may be present in the raw JSON sometimes, but it is not a stable signal.

**The only reliable in-stock signal is: call `verifications.pricing()` for the service and capability you want to purchase. If it returns a price > 0, it's available right now.**

### Why users see "in stock" but get "out of stock" on purchase

Timeline of a typical failure:

```
T+0:00   Stock monitor runs → calls fetch_raw_services_with_quantity()
         WhatsApp: price=$0.50, quantity=null → available=True (price signal)
         Cache written: services:stock TTL=120s

T+0:30   User opens service picker → sees WhatsApp as "in stock" ✅

T+0:45   Another user (or competitor) buys the last WhatsApp number on TV

T+1:10   User clicks WhatsApp → SSE starts
         check_service_available() → POST /api/pub/v2/pricing/verifications
         → BUT this hits the wrong URL path (see Gap 1 below)
         → Falls back to cache price → still shows available

T+1:15   verifications.create() fires → TV has no inventory
         → TextVerifiedError raised → "Provider temporarily unavailable"
         → User charged nothing but waited 15+ seconds
```

---

## 8. Gaps — Confirmed from SDK Source

### Gap 1 — Wrong pricing endpoint URL (CRITICAL)
**Our code**: `POST /api/pub/v2/verifications/pricing`
**SDK source**: `POST /api/pub/v2/pricing/verifications`

Every call to `check_service_available()` and `_fetch_prices_inline()` is hitting the wrong path. This explains why these calls may silently fail or return unexpected responses. The 404 or error is being swallowed by the `except Exception` handler which returns `{"available": False, "reason": str(e)}` — making every service appear unavailable to the pre-check, which then falls through to the cache.

**Fix** in `textverified_service.py`:
```python
# check_service_available() and _fetch_prices_inline() and _fetch_and_cache_pricing()
# Change:
f"{self.client.base_url}/api/pub/v2/verifications/pricing"
# To:
f"{self.client.base_url}/api/pub/v2/pricing/verifications"
```

Or better — use the SDK method directly:
```python
snap = self.client.verifications.pricing(
    service_name=service_name,
    area_code=False,
    carrier=False,
    number_type=NumberType.MOBILE,
    capability=ReservationCapability.SMS,
)
# snap.price is the cost, raises TextVerifiedError if unavailable
```

---

### Gap 2 — Voice pricing uses wrong `number_type`
**SDK source** (`verifications_api.py` line ~90):
```python
# SDK auto-converts NewVerificationRequest for voice:
number_type=NumberType.VOIP if data.capability == ReservationCapability.VOICE else NumberType.MOBILE
```

Our `check_service_available()` always sends `"numberType": "mobile"` even for voice. TV's pricing for voice uses `NumberType.VOIP`. We are getting SMS/mobile pricing for voice requests.

---

### Gap 3 — `carrier` field does not exist on `VerificationExpanded`
Our `get_verification_details()` reads `tv.carrier` and `tv.carrier_name`. The `VerificationExpanded` dataclass has no such fields. These will always be `None`. The carrier enrichment in `_poll_textverified()` is a no-op.

---

### Gap 4 — `audio_url` and `transcription` do not exist on `Sms`
The `Sms` dataclass has: `id`, `to_value`, `created_at`, `encrypted`, `from_value`, `sms_content`, `parsed_code`. No audio, no transcription. Voice verifications deliver their result as `sms_content` text (the transcription). Our code looking for `sms.audio_url` and `sms.transcription` always gets `None` — voice completions that have a transcription in `sms_content` will be processed correctly, but the audio_url branch is dead code.

---

### Gap 5 — `reactivate` is never used (missed cost-saving feature)
When a verification times out, TV sets `can_reactivate=True` for a window. Our platform immediately calls `report()` and issues a refund. We could instead call `reactivate()` to extend the window and retry — no repurchase cost. This is especially valuable for popular services that time out due to SMS delay, not actual unavailability.

---

### Gap 6 — `reuse` is never used (missed cost-saving feature)
`reuse.reusable_until` on `VerificationExpanded` tells us how long the number can be reused for a different service. If a user wants to verify two services back-to-back, we could reuse the same number at lower cost instead of purchasing a new one.

---

### Gap 7 — `max_price` on `NewVerificationRequest` is never passed
The SDK supports a `max_price` field on verification creation — TV will reject the purchase if the price exceeds this value. Our platform has a `max_price` guard in the request schema but never passes it to `verifications.create()`. This means TV could charge more than the user expected if prices shift between the pricing check and the create call.

---

### Gap 8 — SDK retry strategy is invisible to our timeout logic
The SDK session has `Retry(total=3, backoff_factor=1)` on 429/5xx. A single `verifications.create()` call can silently take up to 1+2+4=7 extra seconds on top of the normal response time. Our `asyncio.wait_for(..., timeout=15.0)` wrapping the create call may not be long enough under load. The SSE `purchasing` step could time out on our side while TV is still processing.

---

## 9. Stock Spinner / Live Stock UI — What to Build

The core problem: TV has no push mechanism for stock changes. There is no webhook for "service X just went out of stock." The only way to know is to call the pricing endpoint.

### Recommended approach for live stock in the UI

**Server-Sent Events stock stream** — a new endpoint that streams stock changes to the service picker:

```
GET /api/services/stock/stream   (SSE)
→ Fires immediately with current stock map
→ Re-checks TV pricing for top-N popular services every 30s
→ Pushes delta updates: { service: "whatsapp", available: false, price: null }
```

The frontend service picker subscribes to this stream. When a service flips to unavailable, it greys out in real time without a page refresh.

**For the spinner specifically** — when a user hovers or clicks a service, fire a single `check_service_available()` call (with the correct URL) before showing the price. This is a ~500ms live check that confirms availability at the moment of intent, not 15 minutes ago.

### What TV does better than standard providers

| Feature | TV | Standard provider |
|---------|----|--------------------|
| `area_code_select_option` ordered list | ✅ Preference chain, TV picks best match | ❌ Usually single value or none |
| `carrier_select_option` | ✅ Carrier preference | ❌ Rare |
| `max_price` guard on create | ✅ TV rejects if price shifted | ❌ None |
| `reactivate` on timeout | ✅ Extend window, no repurchase | ❌ None |
| `reuse` across services | ✅ Same number, lower cost | ❌ None |
| `smsAndVoiceCombo` capability | ✅ One number for both | ❌ None |
| `parsedCode` on SMS | ✅ TV extracts the code for you | ❌ You parse it yourself |
| Webhook push on SMS arrival | ✅ Instant, no polling needed | ❌ Polling only |
| Back-order reservations (rentals) | ✅ Queue if out of stock | ❌ None |
| Wake requests (rentals) | ✅ Non-always-on lines, cheaper | ❌ None |

### Where TV falls short vs institutional grade

| Gap | Impact |
|-----|--------|
| No stock/quantity signal on services list | Forces per-service pricing calls to check availability |
| No webhook for stock depletion | Cannot push "out of stock" events to clients |
| Pricing endpoint is per-service, not bulk | Checking 100 services = 100 HTTP calls |
| No `quantity` field in API contract | Cannot show "3 left" style urgency UI |
| Alpha SDK (`0.1.0a1`) — no stability guarantee | API shape can change without notice |
| Synchronous SDK only — no async client | Every call blocks a thread |
| Two-step create (POST → follow action) | If step 2 fails, number is assigned but we have no ID |
| No carrier info on `VerificationExpanded` | Cannot verify carrier post-purchase |

---

## 10. Corrections to Previous Claims

### Correction 1 — Pricing URL gap is UNVERIFIED

Gap 1 in this doc states our code hits the wrong pricing URL. The SDK uses
`/api/pub/v2/pricing/verifications`. Our raw bypass in `check_service_available()` and
`_fetch_prices_inline()` uses `/api/pub/v2/verifications/pricing`.

`TV_PURCHASE_FLOW_ALIGNMENT_TASK.md` (written before SDK was read) already shows the correct
URL `/api/pub/v2/pricing/verifications` in its `check_service_available()` implementation —
suggesting the author knew the correct path. Whether TV accepts both paths is **⚠️ UNVERIFIED**
without a live test from the VPS. Do not treat this as a confirmed bug until tested.

### Correction 2 — Voice gap fix suggestion is wrong

Gap 4 in `TV_API_FLOW_GAP_ASSESSMENT.md` suggests fixing voice by reading `sms.audio_url`
and `sms.transcription`. The `Sms` dataclass has no such fields — `getattr(sms, "audio_url", None)`
will always return `None`. Voice delivers its result as `sms_content` text (the transcription).
The fix is to handle `sms_content` correctly for voice, not to look for non-existent fields.

### Correction 3 — Services list raw JSON vs SDK schema

The SDK `Service` dataclass maps only `service_name` + `capability`. However
`fetch_raw_services_with_quantity()` deliberately bypasses the SDK and reads the raw JSON
response, which the original developer found empirically to contain `price` and `quantity`
fields. The SDK not mapping them does not mean the raw API doesn't return them. This is
an intentional bypass, not a bug. Whether those fields are stable is unverified.

---

## 11. Rental Path — Broken SDK Calls (Confirmed from SDK Source)

These are confirmed `AttributeError` failures in production whenever the rental path is exercised.
None of these methods exist in the SDK.

### Broken call 1 — `reservations.get()` does not exist
**File**: `app/services/textverified_service.py` → `check_reservation_expiry()`
```python
# Current (broken):
res = await asyncio.to_thread(self.client.reservations.get, reservation_id)
# Fix — use the correct SDK method:
res = await asyncio.to_thread(self.client.reservations.details, reservation_id)
# Note: .details() returns Union[RenewableRentalExpanded, NonrenewableRentalExpanded]
# Both have ends_at and state fields
```

### Broken call 2 — `reservations.messages()` does not exist
**File**: `app/services/textverified_service.py` → `get_reservation_messages()`
```python
# Current (broken):
messages = await asyncio.to_thread(self.client.reservations.messages, reservation_id)
# Fix — SMS for rentals goes through sms.list():
rental_obj = await asyncio.to_thread(self.client.reservations.details, reservation_id)
messages = await asyncio.to_thread(
    lambda: list(self.client.sms.list(data=rental_obj))
)
```

### Broken call 3 — `reservations.extend()` does not exist
**File**: `app/services/textverified_service.py` → `extend_reservation()`
```python
# Current (broken):
await asyncio.to_thread(self.client.reservations.extend, reservation_id, extra_minutes)
# Fix — SDK uses extend_nonrenewable() with a RentalDuration enum, not raw minutes:
from textverified.data import RentalDuration
# Map hours to the nearest RentalDuration enum value, then:
await asyncio.to_thread(
    self.client.reservations.extend_nonrenewable,
    extension_duration=RentalDuration.ONE_DAY,  # map from extra_hours
    rental_id=reservation_id,
)
```

### Broken call 4 — `verifications.get()` does not exist
**File**: `app/services/textverified_service.py` → `get_verification_status()`
```python
# Current (broken):
status = await asyncio.to_thread(self.client.verifications.get, activation_id)
# Fix:
status = await asyncio.to_thread(self.client.verifications.details, activation_id)
# VerificationExpanded has: .state (ReservationState enum), .id, .number, .ends_at
# It does NOT have .status, .sms_code, .sms_text, .carrier — those don't exist
```

### Broken call 5 — `create_reservation()` passes wrong duration type
**File**: `app/services/textverified_service.py` → `create_reservation()`
```python
# Current (broken) — passes duration as int minutes:
params = {"service_name": service, "duration": duration_minutes}
reservation = await asyncio.to_thread(self.client.reservations.create, **params)
# SDK NewRentalRequest.duration expects RentalDuration enum, not int.
# Also: reservations.create() returns ReservationSaleExpanded, not a single reservation.
# ReservationSaleExpanded has .reservations (List[Reservation]) and .back_order_reservations.
# The code then reads reservation.number, reservation.total_cost, reservation.ends_at
# directly off the sale object — those fields don't exist there.
```

---

## 12. Implementation Status

**Last updated**: November 2, 2026 — all confirmed fixes deployed to production

| # | Fix | File | Status |
|---|-----|------|--------|
| 1 | `reservations.get()` → `reservations.details()` | `textverified_service.py` | ✅ Deployed `3f805f8a` |
| 2 | `reservations.messages()` → `sms.list(data=rental)` | `textverified_service.py` | ✅ Deployed `3f805f8a` |
| 3 | `reservations.extend()` → `extend_nonrenewable(RentalDuration)` | `textverified_service.py` | ✅ Deployed `3f805f8a` |
| 4 | `verifications.get()` → `verifications.details()` | `textverified_service.py` | ✅ Deployed `3f805f8a` |
| 5 | `create_reservation()` duration enum + sale → details() response | `textverified_service.py` | ✅ Deployed `3f805f8a` |
| 6 | `check_service_available()` now uses SDK `verifications.pricing()` | `textverified_service.py` | ✅ Deployed `3f805f8a` |
| 7 | Voice pricing uses `NumberType.VOIP` | `textverified_service.py` | ✅ Deployed `3f805f8a` |
| 8 | `max_price` wired to `verifications.create()` | `textverified_service.py` | ✅ Deployed `3f805f8a` |
| 9 | Dead `carrier` reads removed from `get_verification_details()` | `textverified_service.py` | ✅ Deployed `3f805f8a` |
| 10 | `reactivate_verification()` method added | `textverified_service.py` | ✅ Deployed `3f805f8a` |
| 11 | Voice: `sms_content` used as transcription, no `audio_url` lookup | `sms_polling_service.py` | ✅ Deployed `3f805f8a` |
| 12 | `_complete_verification()` signature cleaned | `sms_polling_service.py` | ✅ Deployed `3f805f8a` |
| 13 | Dead carrier enrichment task removed from `_poll_textverified()` | `sms_polling_service.py` | ✅ Deployed `3f805f8a` |
| 14 | `_handle_timeout()`: reactivate → check can_report → report order | `sms_polling_service.py` | ✅ Deployed `3f805f8a` |
| 15 | `check_service_available()` receives `capability` in legacy path | `purchase_endpoints.py` | ✅ Deployed `3f805f8a` |
| 16 | `check_service_available()` receives `capability` in SSE path | `purchase_endpoints.py` | ✅ Deployed `3f805f8a` |
| 17 | `ends_at` persisted to DB in SSE recording step | `purchase_endpoints.py` | ✅ Deployed `3f805f8a` |
| 18 | Pricing URL `/verifications/pricing` vs `/pricing/verifications` | `textverified_service.py` | ⚠️ Unverified — needs live VPS test |

## 13. Live Verification Tests Needed

Run these from the server to confirm fixes are working:

```bash
# 1. Provider connected?
docker compose exec app python -c "
import asyncio; from app.services.textverified_service import TextVerifiedService
tv = TextVerifiedService(); print('enabled:', tv.enabled)
print(asyncio.run(tv.get_balance()))
"

# 2. Services loading with prices?
docker compose exec app python -c "
import asyncio; from app.services.textverified_service import TextVerifiedService
tv = TextVerifiedService()
svcs = asyncio.run(tv.get_services_list())
print(f'{len(svcs)} services'); print(svcs[0] if svcs else 'EMPTY')
"

# 3. check_service_available() working?
docker compose exec app python -c "
import asyncio; from app.services.textverified_service import TextVerifiedService
tv = TextVerifiedService()
print(asyncio.run(tv.check_service_available('whatsapp', capability='sms')))
"

# 4. Pricing URL test
TOKEN=$(curl -s -X POST https://www.textverified.com/api/pub/v2/auth \
  -H \"X-API-KEY: \$TEXTVERIFIED_API_KEY\" -H \"X-API-USERNAME: \$TEXTVERIFIED_EMAIL\" \
  | python3 -c \"import sys,json; print(json.load(sys.stdin)['token'])\")
curl -s -X POST https://www.textverified.com/api/pub/v2/pricing/verifications \
  -H \"Authorization: Bearer \$TOKEN\" -H \"Content-Type: application/json\" \
  -d '{\"serviceName\":\"whatsapp\",\"areaCode\":false,\"carrier\":false,\"numberType\":\"mobile\",\"capability\":\"sms\"}'
```
