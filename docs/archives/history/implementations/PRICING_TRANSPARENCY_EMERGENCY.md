# 🚨 PRICING TRANSPARENCY EMERGENCY

**Status**: ✅ FIXED (v4.5.0)  
**Date**: April 2026  
**Severity**: Was P0 — Display Price ≠ Charged Price  
**Resolution**: Provider-price-driven billing across all product types

---

## What Was Broken

Users saw one price in the service list but got charged a completely different amount.

| Path | Source | Example (Telegram) |
|------|--------|--------------------|
| **Display** (services_endpoint.py) | TextVerified API → real price × markup | $1.50 × 1.1 = **$1.65** |
| **Billing** (pricing_calculator.py) | Hardcoded `base_sms_cost` from tier config | **$2.50** (always) |
| **Rentals** (rental_service.py) | Hardcoded $0.25/hour | **$6.00/day** (regardless of provider cost) |

---

## What Was Fixed

### 1. `pricing_calculator.py` — Provider-Price-Driven Billing

`calculate_sms_cost()` now accepts `provider_price` parameter:
- When provided: `base_cost = provider_price × settings.price_markup`
- Fallback only: uses tier `base_sms_cost` (if provider price unavailable)
- Response now includes `price_source` ("provider" or "fallback") and `provider_cost`

`calculate_rental_cost()` now accepts `provider_cost` parameter:
- When provided: `total_cost = provider_cost × settings.price_markup`
- Fallback only: $0.25/hour flat rate

### 2. `purchase_endpoints.py` — Fetches Real Price Before Billing

New `_get_provider_price(service)` helper looks up the real TextVerified price
from the cached service list before calling the pricing calculator.

### 3. `pricing_endpoints.py` — Price-Check Uses Same Logic

The `/pricing` endpoint now also fetches the real provider price, so the
pre-purchase price check returns the exact amount that will be billed.

### 4. `rental_service.py` — Provider-First Purchase Flow

Rentals now purchase from the provider FIRST to get the real cost, then
calculate the user price as `provider_cost × markup`.

### 5. Config Updates

- `price_markup`: 1.8 → **1.1** (10% margin)
- `ngn_usd_rate`: 1600 → **1500**

---

## Pricing Flow (After Fix)

```
User requests Telegram SMS verification
  → _get_provider_price("telegram") → $1.50 (from TextVerified cache)
  → PricingCalculator.calculate_sms_cost(provider_price=1.50)
    → base_cost = $1.50 × 1.1 = $1.65
    → + filter_charges (if PAYG)
    → + overage_charge (if over quota)
    → total_cost = $1.65
  → User is charged $1.65 ← MATCHES what they saw in the service list
```

---

## Files Modified

| File | Change |
|------|--------|
| `app/services/pricing_calculator.py` | Accept `provider_price`, use it × markup as base cost |
| `app/api/verification/purchase_endpoints.py` | Fetch real price before billing |
| `app/api/verification/pricing_endpoints.py` | Fetch real price for price-check |
| `app/services/rental_service.py` | Use actual provider reservation cost |
| `app/core/config.py` | Markup 1.1, NGN rate 1500 |
| `.env` | Markup 1.1, NGN rate 1500 |

---

## Validation Checklist

- [ ] Display price matches charged price for 5 random services
- [ ] Overage charges reflect actual provider cost + markup
- [ ] `price_source` field in pricing response shows "provider" (not "fallback")
- [ ] Rental cost reflects actual TextVerified reservation cost × markup
- [ ] Price-check endpoint returns same amount as billing

---

**Owner**: Engineering  
**Related**: [PRICING_SYSTEM_ANALYSIS.md](../analysis/PRICING_SYSTEM_ANALYSIS.md), [PRICING_DISPLAY_FIX.md](../engineering/PRICING_DISPLAY_FIX.md)
