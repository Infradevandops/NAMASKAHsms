# SDK Optimization Opportunities — TextVerified Integration

**Created**: November 2026
**Version**: 4.9.9 → 5.0
**Source truth**: `TV_API_REAL_FLOW.md`, `TV_API_FLOW_GAP_ASSESSMENT.md`, `TV_STOCK_VERIFICATION_FLOW_ASSESSMENT.md`
**Status**: All items resolved. See table below.

---

## TL;DR — Cash on the Table

| Opportunity | Est. Revenue Impact | Effort | Status |
|-------------|--------------------:|--------|--------|
| Annual plans (Pro $250/yr, Custom $350/yr) | 10× upfront cash per user | Trivial | ✅ Done `bafb5db1` |
| Reuse surcharge ($0.25) | +$0.25 per reuse event | Low | ✅ Done `7c79789f` |
| PAYG API add-on ($10/mo) | Captures segment with no current path | Low | ✅ Done `bafb5db1` |
| Bulk credit discount | Increases avg deposit, reduces Paystack fees | Low | ✅ Done `7c79789f` |
| Inventory notifications (back-in-stock, back-order, expiry) | Retention — reduces churn | Medium | ✅ Done `506e9b6d` |
| `smsAndVoiceCombo` capability | New product line | Medium | ✅ Done `8b022c7d` |
| `ReservationState` full enum → smarter refund logic | Stops double-refund leak | Medium | ✅ Done `7c79789f` |
| `reactivate` before report on timeout | Reduces refund rate | ✅ Done | ✅ Done `3f805f8a` |
| Dead code removal (`_fetch_prices_inline` etc.) | Cleaner codebase | Low | ✅ Done `7c79789f` |
| Stock monitor docstring | 1 line | Trivial | ✅ Done `7c79789f` |

**All 10 items complete.**

---

## Ranked Optimization Items

### Rank 1 — `reuse` Action: Charge a Convenience Fee ✅ Done `7c79789f`

`reusable_until` stored after completion. WS event `reuse_available` pushed to frontend. `POST /api/verification/{id}/reuse` endpoint deducts $0.25 and calls `verifications.reuse()`. Reuse banner shown in UI with countdown.

---

### Rank 2 — `smsAndVoiceCombo` Capability: New Product Line ✅ Done `8b022c7d`

`capability` schema accepts `"sms_and_voice"`. `pricing_calculator.py` adds `combo_fee = +$0.50`. `textverified_service.py` maps to `ReservationCapability.SMS_AND_VOICE`. SSE body passes `selectedCapability`. UI badge renders `SMS+Voice` in service picker.

---

### Rank 3 — Full `ReservationState` Enum Mapping ✅ Done `7c79789f`

`TV_STATE_MAP` (14 states) added to `TextVerifiedService`. `verificationRefunded` → `refunded_by_provider` skips platform refund. Double-refund guard active.

---

### Rank 4 — `validating` SSE Step: Removed ✅ Done `331db1d5`

Fake `validating` step removed. SSE flow is now `pricing_check → balance_check → purchasing → recording → complete`.

---

### Rank 5 — `transcribing` SSE Status for Voice ✅ Done `7c79789f`

`transcribing` broadcast emitted in `sms_polling_service.py` before `_complete_verification()` when voice audio received.

---

### Rank 6 — Dead Code Removal ✅ Done `7c79789f`

`_fetch_prices_inline()` and `fetch_raw_services_with_quantity()` deleted.

---

### Rank 7 — Stock Monitor Docstring ✅ Done `7c79789f`

`run_stock_monitor()` docstring updated to "90 seconds".

---

## SDK Coverage — Final State

### What we're fully extracting

| SDK feature | Platform usage |
|-------------|---------------|
| `verifications.create()` | ✅ Full — area code list, carrier list, max_price, capability incl. sms_and_voice |
| `verifications.details()` | ✅ Used in status polling and timeout handler |
| `verifications.cancel()` | ✅ Used on user cancel |
| `verifications.report()` | ✅ Used on timeout, with `can_report` check |
| `verifications.reactivate()` | ✅ Tried before report on timeout |
| `verifications.reuse()` | ✅ Called from `/api/verification/{id}/reuse` |
| `verifications.pricing()` | ✅ Used as live availability gate in both SSE and legacy paths |
| `sms.incoming()` | ✅ Used for polling with `since` filter, real `ends_at` timeout, `wake_number=True` |
| `sms.parsed_code` | ✅ Used first, regex is fallback |
| `reservations.create()` | ✅ Fixed — `RentalDuration` enum, correct response shape, back-order detection |
| `reservations.details()` | ✅ Fixed — was `.get()` |
| `reservations.extend_nonrenewable()` | ✅ Fixed — was `.extend()` |
| `sms.list(data=rental)` | ✅ Fixed — was `.messages()` |
| `ReservationState` enum (14 states) | ✅ All 14 mapped in `TV_STATE_MAP` |
| `smsAndVoiceCombo` capability | ✅ Wired end-to-end |
| `reuse.reusable_until` | ✅ Stored, surfaced, monetised |
| `wake_number=True` | ✅ Done `506e9b6d` |
| `back_order_reservations` | ✅ Detected, status returned as `back_ordered` `506e9b6d` |

### No remaining gaps.

### What TV's SDK structurally can't give us (hard limits — unchanged)

| Limitation | Impact |
|------------|--------|
| No bulk pricing endpoint | Checking 100 services = 100 HTTP calls. Stock monitor is inherently slow. |
| No stock depletion webhook | Can't push "out of stock" in real time. Polling only. |
| No `quantity` field in API contract | Can't show "3 left" urgency UI reliably. |
| Synchronous SDK only (`0.1.0a1`) | Every call blocks a thread. `asyncio.to_thread()` is the only wrapper. |
| SDK retry is invisible to our timeout | 3× retry with 1s/2s/4s backoff can silently add 7s to any call. |
| No carrier info on `VerificationExpanded` | Can't verify carrier post-purchase. |
| Alpha SDK (`0.1.0a1`) | API shape can change without notice. No stability guarantee. |

---

## More Cash on the Table (Beyond SDK) — All Done

| Feature | Spec | Status |
|---------|------|--------|
| Annual plans (Pro $250/yr, Custom $350/yr) | `REVENUE_FEATURES_SPEC.md` F1 | ✅ Done `bafb5db1` |
| `reuse` surcharge ($0.25) | `REVENUE_FEATURES_SPEC.md` F2 | ✅ Done `7c79789f` |
| PAYG API add-on ($10/mo) | `REVENUE_FEATURES_SPEC.md` F3 | ✅ Done `bafb5db1` |
| Bulk credit discount | `REVENUE_FEATURES_SPEC.md` F4 | ✅ Done `7c79789f` |
| Service back-in-stock notifications | `INVENTORY_NOTIFICATION_SYSTEM.md` T1 | ✅ Done `506e9b6d` |
| Rental back-order detection + notify | `INVENTORY_NOTIFICATION_SYSTEM.md` T2 | ✅ Done `506e9b6d` |
| Rental expiry 24h warning | `INVENTORY_NOTIFICATION_SYSTEM.md` T3 | ✅ Done `506e9b6d` |
| `smsAndVoiceCombo` capability | — | ✅ Done `8b022c7d` |
| Full `ReservationState` enum | — | ✅ Done `7c79789f` |
| Wire `validating` SSE step (removed) | OPEN-1 | ✅ Done `331db1d5` |
| `transcribing` SSE status for voice | OPEN-2 | ✅ Done `7c79789f` |
| Dead code removal | — | ✅ Done `7c79789f` |
| `wake_number` for rentals | — | ✅ Done `506e9b6d` |
| Stock monitor docstring | — | ✅ Done `7c79789f` |

**All 14 items complete. This document is closed.**
