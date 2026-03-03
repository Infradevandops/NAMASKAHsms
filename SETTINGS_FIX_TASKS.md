# Settings Page Fix Tasks

## Bug 1 — Account Tab: `GET /api/v1/user/me` → 404
**File:** `templates/settings.html`  
**Line:** `const userRes = await ApiRetry.fetchWithRetry('/api/v1/user/me', ...)`  
**Fix:** Change URL to `/api/user/me` (already aliased in `compatibility_routes.py`)  
Also: replace the `alert(...)` on failure with an inline error (no blocking dialogs).

---

## Bug 2 — Notifications Tab: `PUT /api/user/settings` → 404
**File:** `app/api/compatibility_routes.py`  
**Fix:** Add a `PUT /user/settings` handler that accepts `{ email_notifications, sms_alerts }` and returns 200.  
Stub is fine — persist to `user.preferences` or just return success until a preferences model is wired up.

---

## Bug 3 — Notifications Tab: Field name mismatch on load
**File:** `app/api/compatibility_routes.py`  
**Line:** `GET /user/settings` returns `notifications_enabled` (single bool)  
**Fix:** Return `email_notifications` and `sms_alerts` fields to match what the JS reads:
```python
return {
    ...
    "email_notifications": True,
    "sms_alerts": False,
}
```

---

## Bug 4 — Billing Tab: `GET /api/billing/history` → 404
**File:** `app/api/compatibility_routes.py`  
**Fix:** Add alias `GET /billing/history` → calls `get_payment_history()` from `payment_history_endpoints.py`  
The existing handler lives at `/api/wallet/history` — just alias it.  
Map response: the JS expects a `payments` key with fields `id`, `reference`, `amount_usd`, `status`, `created_at`.  
The existing handler returns `transactions` — remap or add a thin wrapper.

---

## Bug 5 — Billing Tab: `GET /api/billing/refunds` → 404
**File:** `app/api/compatibility_routes.py`  
**Fix:** Add alias `GET /billing/refunds` → calls `get_refund_history()` from `refund_endpoints.py`  
Existing handler lives at `/api/wallet/refunds/history` — alias it.  
JS expects a `refunds` key — existing handler already returns that. ✅

---

## Bug 6 — Billing Tab: `POST /api/billing/refund` → 404
**File:** `app/api/compatibility_routes.py`  
**Fix:** Add alias `POST /billing/refund` → calls `request_refund()` from `refund_endpoints.py`  
JS sends `{ payment_id, reason }` — existing handler expects `{ transaction_id, reason }`.  
Map `payment_id` → `transaction_id` in the alias body.

---

## Execution Order
1. Bug 3 (field rename, lowest risk, same file as Bug 2)
2. Bug 2 (add PUT handler)
3. Bugs 4, 5, 6 (add 3 billing aliases to `compatibility_routes.py`)
4. Bug 1 (fix URL in `settings.html`, remove alert)
