# Verification UI Overhaul Tasks

## Changes

### ✅ 1 — Wire TextVerified API for live services list
**File:** `app/services/textverified_service.py` — `get_services_list()` calls `client.services.list(NumberType.MOBILE, ReservationType.VERIFICATION)`. Base price fetched once via `client.verifications.pricing()` (flat rate across services). Mock is fallback on any error.

---

### ✅ 2 — Add markup-based pricing
**File:** `app/core/config.py` — `price_markup: float = 1.8` added (configurable via `PRICE_MARKUP` env var).

**File:** `app/api/verification/services_endpoint.py` — applies `round(tv_price * settings.price_markup, 2)` to all services.

`PRICE_MARKUP=1.8` set on Render.

---

### ✅ 3 — Replace service grid with searchable dropdown + "Other" option
**File:** `templates/verify_modern.html` — `.service-grid` replaced with `<select>` populated from API (with `data-price`) + hidden text input shown when "Other" selected.

---

### ✅ 4 — Remove country select
**File:** `templates/verify_modern.html` — country `<select>` removed. `country: 'US'` hardcoded in POST body.

---

### ✅ 5 — Remove 🚀 from header
**File:** `templates/verify_modern.html` — `<h1>SMS Verification</h1>`

---

### ✅ 6 — Show real price in step 2 confirmation
**File:** `templates/verify_modern.html` — `selectedServicePrice` from `data-price` attribute. `pricing-cost` shows real price or "Market rate" for Other.

---

### ✅ 7 — Apply same changes to voice page
**File:** `templates/voice_verify_modern.html` — same dropdown + Other pattern, real price in step 2.

---

## All tasks complete ✅
