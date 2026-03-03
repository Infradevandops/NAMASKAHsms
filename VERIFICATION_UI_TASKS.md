# Verification UI Overhaul Tasks

## Changes

### 1 — Wire TextVerified API for live services list
**File:** `app/services/textverified_service.py`

`get_services_list()` currently returns a hardcoded mock. Wire it to the real TextVerified API:
```python
services = self.client.services.list()  # actual SDK call
```
Return shape: `[{ id, name, price }]` where `price` is TextVerified's cost.

Keep mock as fallback if API call fails.

---

### 2 — Add markup-based pricing
**File:** `app/core/config.py`

Add `price_markup: float = 1.8` (configurable via `PRICE_MARKUP` env var).

**File:** `app/api/verification/verification_routes.py` (GET /services) and `services_endpoint.py`

Apply markup when returning prices to frontend:
```python
our_price = round(tv_price * settings.price_markup, 2)
```

This means `PRICE_MARKUP=1.8` on Render = 80% margin. Change the env var to reprice everything instantly. No hardcoded price table.

---

### 3 — Replace service grid with searchable dropdown + "Other" option
**File:** `templates/verify_modern.html`

Replace the `.service-grid` card grid with:
```html
<select id="service-select">
  <option value="">-- Select a service --</option>
  <!-- populated from API, each option has data-price attribute -->
  <option value="other">Other (type service name)</option>
</select>

<!-- shown only when "other" is selected -->
<input type="text" id="custom-service-input" placeholder="Enter service name" style="display:none;">
```

On change: if value is `"other"`, show the text input and clear `selectedService` until user types. Otherwise set `selectedService` and show price from `data-price`.

---

### 4 — Remove country select
**File:** `templates/verify_modern.html`

TextVerified is US-only. Remove the country `<select>` entirely. Hardcode `country: 'US'` in the `createVerification()` POST body. No dropdown needed.

---

### 5 — Remove 🚀 from header
**File:** `templates/verify_modern.html`

Change `<h1>🚀 SMS Verification</h1>` → `<h1>SMS Verification</h1>`

---

### 6 — Show real price in step 2 confirmation
**File:** `templates/verify_modern.html`

`selectedServicePrice` variable set when user picks from dropdown (from `data-price`). Step 2 `pricing-cost` reads this instead of the hardcoded `$0.80`.

---

### 7 — Apply same changes to voice page
**File:** `templates/voice_verify_modern.html`

Same dropdown pattern, same markup pricing, remove country select, remove emoji from header.

---

## Fix Order
1. Config markup (2) — needed by everything else
2. Wire TextVerified API (1)
3. Template changes: dropdown, remove country, remove emoji, real price (3–7)
