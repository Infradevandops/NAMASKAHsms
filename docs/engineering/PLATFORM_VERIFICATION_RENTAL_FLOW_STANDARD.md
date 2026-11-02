# Platform Verification & Rental Flow Standard
# Provider-Agnostic Canonical Flow

**Created**: October 25, 2026
**Source**: Full SDK source read (`textverified==0.1.0a1`, all 12 files) + platform code cross-reference
**Purpose**: Define the stable, provider-agnostic flow our platform snaps to permanently.
           This is the contract our code must implement regardless of which provider is active.

---

## Research Conclusion: TV Docs vs SDK — Which to Trust?

**Short answer: SDK > API docs, but with caveats.**

The TV v2 API docs describe endpoints and request/response shapes. The SDK wraps those
endpoints but also reveals things the docs don't say explicitly:

| What the SDK reveals that docs don't | Impact |
|--------------------------------------|--------|
| `verifications.create()` is a **two-step** call — POST returns an action href, you follow it to get `VerificationExpanded` | If step 2 fails, TV has assigned a number but we have no ID to cancel it |
| `reservations.create()` returns `ReservationSaleExpanded` (a sale with a list of reservations), not a single rental | Our `create_reservation()` reads fields off the wrong object — confirmed broken |
| `RentalDuration` is an **enum** (`oneDay`, `threeDay`, etc.), not minutes | Our `create_reservation()` passes raw minutes — confirmed broken |
| `sms.incoming()` exits after the **first batch** of unseen messages and returns | Correct for verifications, but means concurrent SMS delivery only yields the first |
| `sms.list()` fetches by **phone number** (`to=`), not by verification ID | All historical SMS to a recycled number are returned — `since` filter is the only guard |
| `PaginatedList` auto-fetches next pages on iteration | `list(self.client.sms.list(...))` in `get_sms()` will exhaust all pages — potentially many HTTP calls |
| `wake_requests.wait_for_number_wake()` is a **blocking** convenience method | Wrapping in `asyncio.to_thread()` is required — it sleeps in a loop |
| `ReservationState` has 15 values including `verificationReused`, `verificationReactivated` | Our platform only handles 3 states — the rest fall through silently |
| `verifications.reactivate()` and `verifications.reuse()` exist | We never call them — missed cost-saving paths |
| `NewVerificationRequest.max_price` exists | TV enforces it server-side — we never pass it |
| `Sms` has NO `audio_url`, NO `transcription` | Voice delivers via `sms_content` text only |
| `VerificationExpanded` has NO `carrier` field | Our carrier enrichment is a confirmed no-op |

**Where the API docs are misleading:**
The TV docs describe `GET /api/pub/v2/services` as returning service listings. They don't
explicitly say what fields are in the raw JSON beyond what the SDK maps. Our platform found
`price` and `quantity` in the raw response empirically — the SDK drops them. This is a real
gap in TV's documentation, not a bug in our code.

**Where the SDK is unreliable:**
It is `0.1.0a1` — pre-release alpha. The two-step create pattern (POST → follow action href)
is an internal SDK convention that could change. The `PaginatedList` auto-pagination means
a single `list()` call can make N HTTP requests silently.

---

## The Canonical Platform Flow

This is the flow our platform must implement. It is provider-agnostic — every provider
adapter must satisfy this contract. TV is the reference implementation.

---

## Part 1 — Verification Flow (SMS & Voice)

### Step 1: Availability Check

**What it does**: Confirm the service has inventory and get the exact price before any charge.

**Provider contract**:
```
INPUT:  service_name, capability ("sms" | "voice"), area_code_requested (bool), carrier_requested (bool)
OUTPUT: { available: bool, price: float | None, reason: str | None }
```

**TV implementation** (SDK method — not raw HTTP):
```python
snap = client.verifications.pricing(
    service_name=service_name,
    area_code=bool(area_code),      # True = filtering requested, affects price
    carrier=bool(carrier),
    number_type=NumberType.VOIP if capability == "voice" else NumberType.MOBILE,
    capability=ReservationCapability.SMS if capability == "sms" else ReservationCapability.VOICE,
)
# snap.price > 0 → available. TextVerifiedError raised → unavailable.
```

**Key facts confirmed from SDK**:
- `area_code` and `carrier` are booleans (do you want filtering?), not the actual values
- Voice must use `NumberType.VOIP` — SDK's own conversion logic confirms this
- `PricingSnapshot` returns only `service_name` and `price` — no quantity, ever
- Raises `TextVerifiedError` if service unavailable — catch this, don't check for null price

**Platform rule**: This call MUST happen before any balance deduction. If it raises or
returns `price=None`, surface the error immediately. Never fall through to purchase.

---

### Step 2: Balance Check

**What it does**: Confirm user has sufficient credits for the calculated cost.

**Provider contract**:
```
INPUT:  user_id, calculated_cost (after markup)
OUTPUT: { sufficient: bool, current_balance: float }
```

This step is platform-internal — no provider call. Must happen after Step 1 so the
price used for the check is the live TV price, not a cached value.

---

### Step 3: Purchase (Number Acquisition)

**What it does**: Acquire a phone number from the provider. This is when the charge commits.

**Provider contract**:
```
INPUT:  service_name, capability, area_code_preference (ordered list | None),
        carrier_preference (list | None), max_price (float | None)
OUTPUT: {
    id: str,                    # provider's verification/activation ID
    phone_number: str,          # E.164 format
    cost: float,                # actual cost charged by provider (raw, before markup)
    ends_at: str,               # ISO8601 — real expiry from provider, NOT hardcoded
    capability: str,
    can_cancel: bool,
    can_report: bool,
    can_reactivate: bool,
    reusable_until: str | None,
    state: str,                 # provider's state string
}
```

**TV implementation** (SDK — two-step internally):
```python
result = client.verifications.create(
    service_name=service_name,
    capability=cap,
    area_code_select_option=area_code_options,  # ordered preference list
    carrier_select_option=carrier_options,
    max_price=max_price,                         # TV enforces this server-side
)
# result is VerificationExpanded — SDK follows the action href internally
# result.ends_at is a real datetime from TV — use it, never hardcode duration
# result.cancel.can_cancel, result.report.can_report, result.reactivate.can_reactivate
# result.reuse.reusable_until
```

**Key facts confirmed from SDK**:
- Two-step internally: POST → follow action href. If step 2 fails, TV has a number
  assigned with no ID returned to us. This is a TV API design gap — nothing we can do.
- `max_price` is passed to TV — TV rejects if price shifted between Step 1 and Step 3.
  Always wire `request.max_price` through to this call.
- `ends_at` is a real datetime per service — WhatsApp may give 60 min, others 10 min.
  Store it in DB. Never use `settings.sms_polling_max_minutes` as the primary timeout.
- `VerificationExpanded` has NO `carrier` field. Do not attempt to read it.

**Platform rule**: Store `ends_at` in DB immediately. Use it as the polling timeout.
Pass `max_price` from the user's request. On any exception, attempt cancel if we have an ID.

---

### Step 4: SMS/Voice Receipt

**What it does**: Wait for the provider to deliver the verification code.

**Two mechanisms — both must be supported**:

#### 4a. Webhook (primary — instant)
TV POSTs to our endpoint the moment SMS arrives. Payload (`SmsWebhookEvent`):
```json
{
  "id": "evt_abc",
  "event": "sms.received",
  "attempt": 1,
  "occurredAt": "...",
  "data": {
    "to": "+17022853600",
    "from": "+12025551234",
    "smsContent": "Your code is 123456",
    "parsedCode": "123456",
    "reservationId": "tv_verification_id",
    "createdAt": "...",
    "encrypted": false
  }
}
```
`parsedCode` is TV's extracted code — use it first. `smsContent` is the full text.
For voice, `smsContent` IS the transcription — there is no `audio_url` field anywhere
in the SDK. Voice delivers as text via the same `Sms` object.

#### 4b. Polling (fallback — when webhook not delivered)
```python
# SDK sms.incoming() — what it actually does internally:
# 1. Calls sms.list(data=verification_obj) → GET /api/pub/v2/sms?to={number}
# 2. Filters by: msg.id not in already_seen AND msg.created_at > (since - polling_interval)
# 3. Yields first batch of unseen messages then EXITS
# 4. Repeats until timeout
#
# Critical: sms.list() fetches by phone number, not verification ID.
# ALL historical SMS to that number are returned — since filter is the only stale guard.
# Use verification.created_at as the `since` value, never datetime.now().
```

**Platform rule for polling**:
- Pass `since=verification.created_at` (the DB value, not TV's)
- Use `ends_at` from DB as the timeout ceiling
- Poll interval: 3s (our current value — SDK default is 1s, 3s is fine)
- On timeout: check `can_reactivate` BEFORE calling `report()`

**SMS object fields** (confirmed from `Sms` dataclass — these are ALL the fields):
```
id, to_value, created_at, encrypted, from_value, sms_content, parsed_code
```
No `audio_url`. No `transcription`. No `carrier`. Voice = `sms_content` is the transcription.

---

### Step 5: Completion or Failure

**Success path**:
```
code = parsed_code or extract_from_sms_content(sms_content)
if capability == "voice" and not code:
    code = sms_content  # the transcription IS the code for voice
mark_verification_completed(db, verification, code, sms_content)
```

**Timeout path** (in order — do NOT skip to report):
```
1. Check can_reactivate on VerificationExpanded
   → If True: call verifications.reactivate(id) → extends window, no repurchase cost
              → restart polling with new ends_at
   → If False or reactivation fails: proceed to step 2

2. Check can_report
   → If True: call verifications.report(id) → TV refunds to account balance
   → If False: log warning, no refund from TV

3. Issue platform refund to user regardless of TV refund outcome
```

**Cancel path** (user-initiated):
```
1. Check can_cancel on VerificationExpanded
   → If True: call verifications.cancel(id) → TV refunds if can_cancel
   → If False: cannot cancel (SMS already received or window closed)
2. Mark verification cancelled in DB
3. Issue platform refund
```

**Reuse path** (user wants another service on same number):
```
1. Check reuse.reusable_until on VerificationExpanded
   → If not None and not expired: call verifications.reuse(id)
   → Creates new verification on same number at lower cost
   → No new purchase needed
```

---

## Part 2 — Rental Flow

### Rental Types (confirmed from SDK)

TV has two rental types with different lifecycles:

| Type | SDK class | Renewable? | Always-on option? | Duration |
|------|-----------|------------|-------------------|----------|
| Renewable | `RenewableRentalExpanded` | Yes — billing cycle | Yes / No (wake required) | Enum: 1/3/7/14/30/90 day, 1 year |
| Non-renewable | `NonrenewableRentalExpanded` | No | Yes / No (wake required) | Same enum |

**`always_on=False` rentals require a wake request before they can receive SMS.**
This is a TV-specific concept — other providers don't have it. The platform must
abstract this away from users.

---

### Rental Step 1: Pricing Check

```python
snap = client.reservations.pricing(
    service_name=service_name,
    area_code=bool(area_code),
    number_type=NumberType.MOBILE,
    capability=ReservationCapability.SMS,
    always_on=always_on,
    is_renewable=is_renewable,
    duration=RentalDuration.ONE_DAY,  # enum, not minutes
    call_forwarding=False,
)
# snap.price is the cost
```

---

### Rental Step 2: Purchase

**TV implementation** (confirmed from SDK — `reservations_api.py`):
```python
sale = client.reservations.create(
    service_name=service_name,
    capability=ReservationCapability.SMS,
    number_type=NumberType.MOBILE,
    duration=RentalDuration.ONE_DAY,    # ENUM — not minutes, not hours
    is_renewable=False,
    always_on=True,                      # True = no wake needed
    allow_back_order_reservations=False, # True = queue if out of stock
    area_code_select_option=["212"],     # optional ordered list
)
# sale is ReservationSaleExpanded — NOT a single rental
# sale.reservations is List[Reservation] — each has .id and .service_name only
# sale.back_order_reservations is List[BackOrderReservationCompact]
# To get full rental details, call reservations.details(sale.reservations[0])
```

**Current platform bug** — `create_reservation()` reads `reservation.number`,
`reservation.total_cost`, `reservation.ends_at` off the sale object. Those fields
don't exist on `ReservationSaleExpanded`. The correct flow:

```python
sale = client.reservations.create(...)
# sale.reservations[0] is a Reservation with only .id and .service_name
rental = client.reservations.details(sale.reservations[0])
# rental is RenewableRentalExpanded or NonrenewableRentalExpanded
# rental.number, rental.state, rental.ends_at (nonrenewable only), rental.refund
```

**`RentalDuration` enum values** (confirmed from `dtypes.py`):
```
oneDay, threeDay, sevenDay, fourteenDay, thirtyDay, ninetyDay, oneYear
```
There is no way to pass arbitrary minutes or hours. Map user-facing duration to the
nearest enum value.

---

### Rental Step 3: Wake (non-always-on rentals only)

```python
# Check if rental needs waking
if not rental.always_on:
    # Estimate window first (non-blocking)
    estimate = client.wake_requests.estimate_usage_window(rental.id)
    # estimate.estimated_window_start, estimate.estimated_window_end

    # Create wake request (two-step internally — POST → follow action)
    wake = client.wake_requests.create(rental.id)
    # wake.is_scheduled, wake.usage_window_start, wake.usage_window_end

    # Wait for window to open (blocking — wrap in asyncio.to_thread)
    wake = client.wake_requests.wait_for_wake_request(wake, poll_frequency=5.0)
    # Now rental is active and can receive SMS
```

**Platform abstraction rule**: Users should never see "wake request" language.
Surface this as "Your number is being activated — ready in ~N minutes."

---

### Rental Step 4: SMS Receipt

Same as verification Step 4 — `sms.list(data=rental_obj)` or webhook.

**Difference from verification**: Rentals can receive multiple SMS over their lifetime.
`sms.incoming()` exits after the first batch — for rentals, call it in a loop or
rely on webhooks exclusively.

---

### Rental Step 5: Extension

```python
# Non-renewable only — extend duration
client.reservations.extend_nonrenewable(
    extension_duration=RentalDuration.ONE_DAY,  # enum
    rental_id=rental_id,
)

# Renewable — managed via billing cycle renewal
client.billing_cycles.renew(billing_cycle_id)
```

**Current platform bug** — `extend_reservation()` calls `self.client.reservations.extend()`
which doesn't exist. Fix: use `extend_nonrenewable()` with a `RentalDuration` enum.

---

### Rental Step 6: Refund / Cancellation

```python
# Non-renewable
client.reservations.refund_nonrenewable(rental_id)
# Check rental.refund.can_refund and rental.refund.refundable_until first

# Renewable
client.reservations.refund_renewable(rental_id)
```

---

## Part 3 — Webhook Events (Full List from SDK)

TV sends webhooks for these event types (from `dtypes.py` webhook dataclasses):

| Event | SDK dataclass | When fired |
|-------|--------------|------------|
| `sms.received` | `WebhookEventSmsWebhookEvent` | SMS arrives on any number |
| `reservation.created` | `WebhookEventReservationCreatedWebhookEvent` | Rental or verification created |
| `backorder.fulfilled` | `WebhookEventBackOrderReservationWebhookEvent` | Back-order rental fulfilled |
| `billing_cycle.*` | `WebhookEventBillingCycleWebhookEvent` | Billing cycle events |

**Our platform currently only handles `sms.received`.** The others are accepted and ignored.
`reservation.created` could be used to confirm a purchase completed on TV's side.
`backorder.fulfilled` is needed if we ever enable `allow_back_order_reservations=True`.

**Webhook `SmsWebhookEvent` fields** (confirmed from `dtypes.py`):
```
to_value, created_at, encrypted, from_value, sms_content, parsed_code, reservation_id
```
`reservation_id` = TV's verification/rental ID = our `activation_id`. Use this to look up
the verification. Fall back to phone number match only if `reservation_id` is absent.

---

## Part 4 — Provider-Agnostic Adapter Contract

Every provider adapter (`TextVerifiedAdapter`, `TelnyxAdapter`, `FiveSimAdapter`, etc.)
must implement this interface. TV is the reference. Other providers approximate it.

```python
class SMSProvider:

    # Verification
    async def check_available(self, service, capability) -> AvailabilityResult
    async def purchase_number(self, service, capability, area_code, max_price) -> PurchaseResult
    async def check_messages(self, order_id, created_after) -> List[MessageResult]
    async def cancel(self, order_id) -> bool
    async def report_failed(self, order_id) -> bool          # triggers provider refund
    async def reactivate(self, order_id) -> bool             # TV only — others return False
    async def reuse(self, order_id) -> bool                  # TV only — others return False

    # Rental
    async def create_rental(self, service, duration, always_on) -> RentalResult
    async def get_rental_messages(self, rental_id) -> List[MessageResult]
    async def extend_rental(self, rental_id, duration) -> bool
    async def cancel_rental(self, rental_id) -> bool

    # Health
    async def get_balance(self) -> float
```

**`PurchaseResult` must always include**:
```python
@dataclass
class PurchaseResult:
    phone_number: str
    order_id: str
    cost: float
    expires_at: str          # ISO8601 — from provider, never hardcoded
    provider: str
    can_cancel: bool = True
    can_report: bool = True
    can_reactivate: bool = False   # TV-specific, False for others
    reusable_until: str = None     # TV-specific, None for others
    area_code_matched: bool = True
    fallback_applied: bool = False
    voip_rejected: bool = False
    retry_attempts: int = 0
```

---

## Part 5 — What TV Does Better Than Standard Providers

Confirmed from full SDK read — these are real features, not marketing:

| Feature | TV SDK | Standard provider |
|---------|--------|-------------------|
| `area_code_select_option` ordered preference list | ✅ TV picks best match from your list | ❌ Single value or none |
| `carrier_select_option` | ✅ Carrier preference | ❌ Rare |
| `max_price` server-side guard on create | ✅ TV rejects if price shifted | ❌ None |
| `reactivate` on timeout | ✅ Extend window, no repurchase | ❌ None |
| `reuse` across services | ✅ Same number, lower cost | ❌ None |
| `smsAndVoiceCombo` capability | ✅ One number for both | ❌ None |
| `parsedCode` on SMS | ✅ TV extracts the code | ❌ You parse it yourself |
| Webhook push on SMS arrival | ✅ Instant, no polling | ❌ Polling only |
| Back-order reservations | ✅ Queue if out of stock | ❌ None |
| Wake requests (non-always-on rentals) | ✅ Cheaper lines, scheduled activation | ❌ None |
| `LineHealth` check on rental | ✅ `reservations.check_health(id)` | ❌ None |
| Billing cycle management | ✅ Bulk renewal, invoices, preview | ❌ None |
| `ReservationState` 15-value enum | ✅ Full lifecycle visibility | ❌ Usually 3-4 states |

---

## Part 6 — Confirmed Broken Calls in Current Platform (Fix List)

All confirmed from SDK source. These will `AttributeError` or produce wrong results in production.

| # | Location | Broken call | Correct call | Severity |
|---|----------|-------------|--------------|----------|
| 1 | `check_reservation_expiry()` | `reservations.get(id)` | `reservations.details(id)` | 🔴 AttributeError |
| 2 | `get_reservation_messages()` | `reservations.messages(id)` | `sms.list(data=rental_obj)` | 🔴 AttributeError |
| 3 | `extend_reservation()` | `reservations.extend(id, minutes)` | `reservations.extend_nonrenewable(duration=RentalDuration.X, rental_id=id)` | 🔴 AttributeError |
| 4 | `get_verification_status()` | `verifications.get(id)` | `verifications.details(id)` | 🔴 AttributeError |
| 5 | `create_reservation()` | reads `.number`, `.total_cost`, `.ends_at` off `ReservationSaleExpanded` | call `reservations.details(sale.reservations[0])` to get `RentalExpanded` | 🔴 AttributeError |
| 6 | `create_reservation()` | passes `duration=int(hours*60)` | pass `duration=RentalDuration.ONE_DAY` (enum) | 🔴 TypeError |
| 7 | `get_verification_details()` | reads `tv.carrier`, `tv.carrier_name` | fields don't exist — always None | 🟡 Silent no-op |
| 8 | `_poll_textverified()` | looks for `audio_url`, `transcription` on Sms | use `sms_content` for voice | 🟡 Voice falls to timeout |
| 9 | `create_verification()` | never passes `max_price` | add `max_price=max_price` to `verifications.create()` | 🟡 Price drift unguarded |
| 10 | `_handle_timeout()` | calls `report()` without checking `can_reactivate` first | check `can_reactivate`, attempt reactivation before reporting | 🟡 Unnecessary refund cost |

---

## Part 7 — Unverified Claims (Require Live VPS Test)

| Claim | Why unverified | How to test |
|-------|---------------|-------------|
| `/api/pub/v2/verifications/pricing` returns 404 | Cloudflare blocks curl from dev machine | `curl` from VPS with bearer token |
| Raw services JSON returns `price` and `quantity` fields | SDK doesn't map them but they may exist | Log raw response from `fetch_raw_services_with_quantity()` in prod |
| Voice pricing with `numberType=mobile` returns wrong price | SDK uses VOIP for voice — but TV may accept mobile too | Compare pricing call results for same service with mobile vs voip |
