# SDK Optimization Opportunities — TextVerified Integration

**Created**: November 2026
**Version**: 4.9.0
**Source truth**: `TV_API_REAL_FLOW.md`, `TV_API_FLOW_GAP_ASSESSMENT.md`, `TV_STOCK_VERIFICATION_FLOW_ASSESSMENT.md`
**Status**: Post `3f805f8a` — all P0 critical fixes deployed. What remains is optimization + money.

---

## TL;DR — Cash on the Table

| Opportunity | Est. Revenue Impact | Effort |
|-------------|--------------------:|--------|
| Annual plans (Pro $250/yr, Custom $350/yr) | 10× upfront cash per user | Trivial |
| Reuse surcharge ($0.25) | +$0.25 per reuse event | Low |
| PAYG API add-on ($10/mo) | Captures segment with no current path | Low |
| Bulk credit discount | Increases avg deposit, reduces Paystack fees | Low |
| Inventory notifications (back-in-stock, back-order, expiry) | Retention — reduces churn | Medium |
| `smsAndVoiceCombo` capability | New product line | Medium |
| `ReservationState` full enum → smarter refund logic | Stops double-refund leak | Medium |
| `reactivate` before report on timeout | Reduces refund rate | ✅ Done |
| Dead code removal (`_fetch_prices_inline` etc.) | Cleaner codebase | Low |
| Stock monitor docstring | 1 line | Trivial |

---

## Ranked Optimization Items

### Rank 1 — `reuse` Action: Charge a Convenience Fee ✅ Implement This

**What TV gives you**: After a verification completes, `VerificationExpanded.reuse.reusable_until` is set for a window (typically 5–15 min). During that window, the user can reuse the same number for a *different* service at a lower TV cost than buying a new number.

**What the platform does today**: Nothing. `reuse` is never read, never surfaced, never offered.

**The play**: When a verification completes and `reusable_until` is in the future, show the user a "Reuse this number" option in the UI. Charge them a flat **$0.25 convenience fee** on top of whatever TV charges for the reuse. If their balance covers it, deduct and fire `verifications.reuse(id)`. If balance is short, the option just doesn't appear — no friction, no failed charge.

**Why $0.25**: It's below the area code surcharge ($0.25 is already a known price point on the platform), it's pure margin since TV's reuse cost is lower than a fresh purchase, and it's genuinely useful for users who need to verify two services back-to-back (e.g. WhatsApp + Telegram on the same session).

**Revenue math**: If 10% of completions trigger a reuse offer and 30% of those convert, at 1,000 verifications/month that's 30 reuse events × $0.25 = **$7.50/month at 1k verifications**. Scales linearly. At 10k verifications/month it's $75/month pure margin, zero TV cost increase.

**Implementation sketch**:
```python
# After verification completes in sms_polling_service.py
if tv_result.reuse and tv_result.reuse.reusable_until:
    reusable_until = tv_result.reuse.reusable_until
    # Store on verification record, push to frontend via WebSocket
    await ws_manager.send_to_user(user_id, {
        "type": "reuse_available",
        "verification_id": verification.id,
        "reusable_until": reusable_until.isoformat(),
        "fee": 0.25,
    })
```

```python
# New endpoint: POST /api/verification/{id}/reuse
async def reuse_verification(id, user, db, balance_service, tv_service):
    verification = get_verification(id, user)
    if not verification.reusable_until or datetime.utcnow() > verification.reusable_until:
        raise HTTPException(410, "Reuse window expired")
    if not await balance_service.check_sufficient_balance(user.id, 0.25):
        raise HTTPException(402, "Insufficient balance")
    await balance_service.deduct(user.id, 0.25, reason="reuse_fee")
    result = await tv_service.reuse_verification(verification.activation_id)
    return result
```

---

### Rank 2 — `smsAndVoiceCombo` Capability: New Product Line

**What TV gives you**: A third `capability` value — `smsAndVoiceCombo`. One number that can receive both SMS and a voice call. TV supports it, the SDK exposes it, the platform never uses it.

**What the platform does today**: Only `sms` and `voice` are offered as separate purchases.

**The play**: Add a "Combo" option to the verification picker. Price it at **$3.13** (base $2.63 + $0.50 premium — same as carrier filter surcharge, which users already accept). This is a genuinely useful feature for services that sometimes send SMS and sometimes call — the user doesn't have to guess which one to buy.

**Revenue math**: Even if only 5% of users pick combo over SMS, at $0.50 extra per combo that's $0.50 × 50 = **$25/month at 1k verifications**. It also reduces refund requests from users who bought SMS but got a voice call (or vice versa).

**Implementation**: Add `smsAndVoiceCombo` to the capability enum in the purchase request schema, pass it through to `verifications.create()`, price it at base + $0.50. The polling path already handles both `sms_content` and voice via `sms.incoming()` — no polling changes needed.

---

### Rank 3 — Full `ReservationState` Enum Mapping: Smarter Refund Logic

**What TV gives you**: 14 reservation states. The platform maps 3 (`pending`, `completed`, `failed`). The unmapped ones that matter:

| TV State | What it means | Platform today | Opportunity |
|----------|--------------|----------------|-------------|
| `verificationReused` | Number was reused | Falls through as unknown | Mark completed, no refund |
| `verificationReactivated` | Window was extended | Falls through | Mark as pending again |
| `verificationRefunded` | TV already refunded | Platform may double-refund | Skip platform refund |
| `renewableActive` | Rental is live | Not handled | Correct rental status |
| `renewableOverdue` | Rental payment missed | Not handled | Trigger user alert |
| `renewableExpired` | Rental ended | Not handled | Correct rental status |

**The cash angle**: `verificationRefunded` is the critical one. If TV has already refunded the user's account balance (their TV account, which flows back to your TV balance), and the platform *also* issues a platform-side refund, you're double-refunding. At scale this is a real leak.

**Implementation**: Add a state mapper in `textverified_service.py`:
```python
TV_STATE_MAP = {
    "verificationPending": "pending",
    "verificationCompleted": "completed",
    "verificationCanceled": "cancelled",
    "verificationTimedOut": "timeout",
    "verificationReported": "reported",
    "verificationRefunded": "refunded_by_provider",  # skip platform refund
    "verificationReused": "completed",
    "verificationReactivated": "pending",
}
```

---

### Rank 4 — `validating` SSE Step: Wire It or Kill It

**What it is**: The `validating` step in the SSE purchase flow fires immediately after `purchasing` completes with zero real work. It's a UX label only.

**The play**: Two options:
- **Kill it** — go straight `purchasing` → `recording`. Saves ~200ms of fake latency.
- **Wire it** — call `verifications.details(id)` to confirm the number is live on TV's side before committing the DB write. Surface `can_cancel` to the frontend so the cancel button is correctly enabled/disabled from the start.

Wiring it is the better call. It adds one real TV API call (~300ms) but gives you a confirmation gate before you debit the user. If TV's `details()` call fails here, you can abort without charging — currently you charge first and find out later.

---

### Rank 5 — `transcribing` SSE Status for Voice

**What it is**: `mark_verification_transcribing()` exists in `verification_status_service.py` but is never called from the SSE purchase path. Voice verifications show as `pending` while transcribing — users think it's still waiting for a call when audio was already received.

**The play**: After `sms.incoming()` yields a voice result (non-null `sms_content`, null `parsed_code`), emit a `transcribing` SSE event before processing. One line in `sms_polling_service.py`. Reduces support tickets from voice users who think their verification is stuck.

---

### Rank 6 — Dead Code Removal

Two functions are confirmed superseded by the SDK `verifications.pricing()` method:
- `_fetch_prices_inline()` in `textverified_service.py`
- `fetch_raw_services_with_quantity()` in `textverified_service.py`

Both are still in the codebase per the active sprint notes. Delete them. They add confusion about which pricing path is authoritative and they bypass the SDK in ways that are fragile (raw JSON field names not in TV's API contract).

---

### Rank 7 — Stock Monitor Docstring

`app/services/stock_monitor.py` → `run_stock_monitor()` docstring says "15-minute refresh". Actual loop is 90s. One line fix.

```python
async def run_stock_monitor() -> None:
    """Background loop — refreshes stock every 90 seconds."""
```

---

## The Gist: Do We Have TV's SDK on Chokehold?

Short answer: **mostly yes, but there are three gaps left**.

### What we're fully extracting

| SDK feature | Platform usage |
|-------------|---------------|
| `verifications.create()` | ✅ Full — area code list, carrier list, max_price, capability |
| `verifications.details()` | ✅ Used in status polling and timeout handler |
| `verifications.cancel()` | ✅ Used on user cancel |
| `verifications.report()` | ✅ Used on timeout, with `can_report` check |
| `verifications.reactivate()` | ✅ Tried before report on timeout |
| `verifications.pricing()` | ✅ Used as live availability gate in both SSE and legacy paths |
| `sms.incoming()` | ✅ Used for polling with `since` filter and real `ends_at` timeout |
| `sms.parsed_code` | ✅ Used first, regex is fallback |
| `reservations.create()` | ✅ Fixed — `RentalDuration` enum, correct response shape |
| `reservations.details()` | ✅ Fixed — was `.get()` |
| `reservations.extend_nonrenewable()` | ✅ Fixed — was `.extend()` |
| `sms.list(data=rental)` | ✅ Fixed — was `.messages()` |

### What we're NOT extracting yet (the gaps)

| SDK feature | Status | Impact |
|-------------|--------|--------|
| `verifications.reuse()` | ❌ Never called | Revenue opportunity (Rank 1 above) |
| `smsAndVoiceCombo` capability | ❌ Never used | New product line (Rank 2 above) |
| Full `ReservationState` enum (14 states) | ⚠️ 3 of 14 mapped | Double-refund risk (Rank 3 above) |

### What TV's SDK structurally can't give us (hard limits)

These are not gaps in our implementation — they're limits of TV's API itself:

| Limitation | Impact |
|------------|--------|
| No bulk pricing endpoint | Checking 100 services = 100 HTTP calls. Stock monitor is inherently slow. |
| No stock depletion webhook | Can't push "out of stock" in real time. Polling only. |
| No `quantity` field in API contract | Can't show "3 left" urgency UI reliably. |
| Synchronous SDK only (`0.1.0a1`) | Every call blocks a thread. `asyncio.to_thread()` is the only wrapper. |
| SDK retry is invisible to our timeout | 3× retry with 1s/2s/4s backoff can silently add 7s to any call. SSE 15s timeout can race this under load. |
| No carrier info on `VerificationExpanded` | Can't verify carrier post-purchase. Carrier enrichment is dead code. |
| Two-step create (POST → follow action) | If step 2 fails, TV may have assigned a number we have no ID for. |
| Alpha SDK (`0.1.0a1`) | API shape can change without notice. No stability guarantee. |

### The one unverified item

Pricing URL `/verifications/pricing` vs `/pricing/verifications` — confirmed as 404 vs 200 on Nov 10 2026 per the gap assessment. The correct path `/pricing/verifications` is deployed. This is closed.

---

## More Cash on the Table (Beyond SDK)

These aren't SDK gaps but they're revenue sitting in the existing architecture.

> Full implementation specs:
> - `docs/features/REVENUE_FEATURES_SPEC.md` — annual plans, reuse surcharge, PAYG API add-on, bulk credit discount
> - `docs/features/INVENTORY_NOTIFICATION_SYSTEM.md` — back-in-stock, back-order, rental expiry

### Annual plan discount
Offer Pro at $250/year (saves user $50 vs monthly, you get 10 months of cash upfront). Custom at $350/year. Improves cash flow and reduces churn. Zero engineering — Paystack plan config + `billing_period` field on subscription record + UI toggle on pricing page. Full spec: `REVENUE_FEATURES_SPEC.md` → Feature 1.

### PAYG API access upsell
API keys are currently Pro+ only. PAYG users with API needs have no path. A $10/month "API add-on" for PAYG users (5 keys, no quota) is a clean upsell that doesn't cannibalize Pro. Needs a `subscription_addons` table, tier gate update, Paystack plan, and upsell UI on the API keys page. Full spec: `REVENUE_FEATURES_SPEC.md` → Feature 3.

### Bulk credit discount
Users who top up $50+ get 5% bonus credits. $100+ gets 10%. $200+ gets 15%. Costs ~$1.39 per $50 deposit at 5% — well within the 44.5% margin. Increases average deposit size and reduces Paystack fee frequency. Full spec: `REVENUE_FEATURES_SPEC.md` → Feature 4.

### Inventory notification system
TV has no push webhook for stock changes. Build a watch layer on top of the existing polling infrastructure:
- **Service back-in-stock**: User on out-of-stock service clicks "Notify me" → stock monitor checks watches on every 90s loop → email + in-app when price > 0
- **Rental back-order**: `ReservationSaleExpanded.back_order_reservations` is ignored today. Detect it, queue a back-order, notify user when TV fulfills it
- **Rental expiry warning**: 24h before `ends_at`, send "Your rental expires soon — renew to keep it"

Full spec: `docs/features/INVENTORY_NOTIFICATION_SYSTEM.md`

### `wake_number` on `sms.incoming()`
TV's `sms.incoming()` has a `wake_number=False` parameter. When `True`, TV sends a wake signal to the number before polling — useful for lines that aren't always-on (cheaper rental lines). Platform never uses it. For rentals, enabling this could improve SMS delivery rates on cheaper number pools.

### Back-order reservations
`ReservationSaleExpanded.back_order_reservations` — when TV has no inventory for a rental, it can queue a back-order. Platform reads `reservations` from the sale response but ignores `back_order_reservations` entirely. Full spec in `docs/features/INVENTORY_NOTIFICATION_SYSTEM.md` → Type 2.

---

## Implementation Priority

| # | Item | Spec | Revenue | Effort | Do When |
|---|------|------|---------|--------|---------|
| 1 | Annual plans (Pro $250/yr, Custom $350/yr) | `REVENUE_FEATURES_SPEC.md` F1 | Direct — 10× upfront cash | Trivial | Now |
| 2 | `reuse` surcharge ($0.25) | `REVENUE_FEATURES_SPEC.md` F2 | Direct — pure margin | Low | Next sprint |
| 3 | PAYG API add-on ($10/mo) | `REVENUE_FEATURES_SPEC.md` F3 | Direct — new segment | Low | Next sprint |
| 4 | Bulk credit discount | `REVENUE_FEATURES_SPEC.md` F4 | Retention + deposit size | Low | Next sprint |
| 5 | Service back-in-stock notifications | `INVENTORY_NOTIFICATION_SYSTEM.md` T1 | Retention | Medium | Next sprint |
| 6 | Rental back-order detection + notify | `INVENTORY_NOTIFICATION_SYSTEM.md` T2 | Retention | Medium | When rentals active |
| 7 | Rental expiry 24h warning | `INVENTORY_NOTIFICATION_SYSTEM.md` T3 | Retention | Low | When rentals active |
| 8 | `smsAndVoiceCombo` capability | — | Direct — new product | Medium | Next sprint |
| 9 | Full `ReservationState` enum | — | Risk — double-refund | Medium | Next sprint |
| 10 | Wire `validating` SSE step | `VERIFICATION_TASKS.md` OPEN-1 | Quality | Low | Next sprint |
| 11 | `transcribing` SSE status for voice | `VERIFICATION_TASKS.md` OPEN-2 | UX / support reduction | Low | Next sprint |
| 12 | Dead code removal | `OPS_SUMMARY.md` | Hygiene | Low | Next sprint |
| 13 | `wake_number` for rentals | — | Quality | Low | When rentals active |
| 14 | Stock monitor docstring | `VERIFICATION_TASKS.md` OPEN-4 | Hygiene | Trivial | Any PR |
