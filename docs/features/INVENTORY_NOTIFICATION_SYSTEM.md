# Inventory Notification System — Feature Spec

**Created**: November 2026
**Priority**: P1 — Revenue & Retention
**Status**: 📋 Planned — not yet implemented
**Depends on**: TV SDK `verifications.pricing()`, `reservations.details()`, back-order reservation response

---

## Where It Is Visible

### Admin Portal
- **`/admin/alerts`** (`templates/admin/alerts.html`) — primary home. Add a new "📦 Inventory" section to the Active Alerts panel. Stock-out events appear as `alert-warning` cards. Back-order fulfillments appear as `alert-info` cards. Rental expiry warnings appear as `alert-warning` cards. All feed into the existing alert history table.
- **`/admin/dashboard`** → Pricing Governance tab (`#page-pricing`) — the "Live Provider Inventory" table already shows services + prices. Add a stock status column (`🟢 In Stock` / `🔴 Out of Stock`) and a "Watchers" count column showing how many users are watching each out-of-stock service. This gives admin visibility into demand for unavailable services.
- **`/admin/dashboard`** → Institutional Overview tab (`#page-overview`) — add a `stat-card` for "Stock Watches Active" showing total pending watches across all users. Surfaces demand signal at a glance.

### Email (Admin)
- Uses existing `alerting_service.py` → `send_alert()` → `_send_email_alert()` → `ADMIN_NOTIFY_EMAIL`
- Three new alert types wired into `alerting_service.py`:
  - `stock_depleted` — severity `warning` — fires when a service transitions from available → unavailable during stock monitor loop
  - `back_order_queue_depth` — severity `info` — fires when back-order queue for a service exceeds 5 users waiting
  - `rental_expiry_batch` — severity `info` — daily digest of rentals expiring in next 24h (batched, not per-rental)

### Email (User)
- Uses existing `notification_service.py` + `email_notification_service.py`
- Three new user-facing email types:
  - `stock_available` — "WhatsApp numbers are back — buy now →"
  - `rental_ready` — "Your rental number for {service} is ready →"
  - `rental_expiring` — "Your rental expires in 24 hours — renew to keep it →"

### In-App (User)
- Notification center (`/notifications`, `templates/notification_center.html`) — all three types appear here with action CTAs
- Verification picker (`static/js/verification-flow.js`) — out-of-stock services show "🔔 Notify me" button inline
- Rentals page (`templates/rentals_modern.html`) — back-order state shown as "You're in the queue" with cancel option

---

---

## What This Is

TV has no push webhook for stock changes. There is no "service X just went out of stock" event.
The only way to know if something is available is to call the pricing endpoint.

This feature builds a notification layer on top of that constraint so users can:
1. Get notified when an out-of-stock service comes back in stock
2. Get notified when a rental number they want becomes available (back-order)
3. Get notified when their rental is about to expire

All three are retention plays. Users who get notified come back. Users who don't, churn.

---

## Scope — Three Notification Types

### Type 1 — Service Back-in-Stock (Verifications)

**Trigger**: User tries to buy a service that is out of stock (`check_service_available()` returns `available: false`).

**Flow**:
```
User clicks WhatsApp → out of stock error shown
→ "Notify me when available" button appears
→ User clicks → POST /api/notifications/stock-watch
→ Record saved: { user_id, service_name, capability, created_at }
→ Stock monitor checks watched services on every 90s loop
→ When pricing endpoint returns price > 0 for a watched service:
    → Send notification to all watchers
    → Delete the watch record
    → User gets email + in-app notification: "WhatsApp numbers are available again"
```

**Data model**:
```sql
CREATE TABLE stock_watches (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    service_name VARCHAR(100) NOT NULL,
    capability  VARCHAR(20) NOT NULL DEFAULT 'sms',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notified_at TIMESTAMPTZ,
    UNIQUE(user_id, service_name, capability)
);
```

**API**:
```
POST /api/notifications/stock-watch
Body: { "service_name": "whatsapp", "capability": "sms" }
→ 201 Created or 200 if already watching

DELETE /api/notifications/stock-watch/{service_name}
→ 204 No Content

GET /api/notifications/stock-watches
→ List of active watches for current user
```

**Stock monitor integration** (`app/services/stock_monitor.py`):
```python
# After building stock map, check watches
async def notify_stock_watchers(stock_map: dict, db: AsyncSession):
    watches = await db.execute(
        select(StockWatch).where(StockWatch.notified_at.is_(None))
    )
    for watch in watches.scalars():
        service_stock = stock_map.get(watch.service_name, {})
        if service_stock.get("available") and service_stock.get("price"):
            await notification_service.send(
                user_id=watch.user_id,
                type="stock_available",
                data={
                    "service_name": watch.service_name,
                    "price": service_stock["price"],
                    "capability": watch.capability,
                }
            )
            watch.notified_at = datetime.utcnow()
    await db.commit()
```

---

### Type 2 — Rental Back-Order Notification

**What TV gives us**: `ReservationSaleExpanded.back_order_reservations` — when TV has no inventory for a rental, it queues a back-order. The platform currently reads `reservations` from the sale response and ignores `back_order_reservations` entirely.

**Trigger**: User tries to create a rental, TV returns a sale with `reservations=[]` and `back_order_reservations=[{id, service_name, ...}]`.

**Flow**:
```
User requests rental → TV returns back-order (no inventory)
→ Platform detects back_order_reservations is non-empty
→ Store back-order IDs in DB
→ Background job polls reservations.details(id) every 5 minutes
→ When state transitions from back-order to active:
    → Send notification: "Your rental number for {service} is ready"
    → Deduct credits (rental was pre-authorized)
    → Update rental record to active
```

**Data model**:
```sql
CREATE TABLE rental_back_orders (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tv_back_order_id VARCHAR(100) NOT NULL UNIQUE,
    service_name    VARCHAR(100) NOT NULL,
    capability      VARCHAR(20) NOT NULL DEFAULT 'sms',
    requested_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fulfilled_at    TIMESTAMPTZ,
    notified_at     TIMESTAMPTZ,
    credits_held    NUMERIC(10,4) NOT NULL  -- pre-authorized amount
);
```

**create_reservation() fix** (`app/services/textverified_service.py`):
```python
# Current: reads sale.reservations, ignores back_order_reservations
# Fix:
sale = await asyncio.to_thread(self.client.reservations.create, ...)

if sale.reservations:
    # Normal path — inventory available
    reservation = sale.reservations[0]
    return {"status": "active", "reservation": reservation}
elif sale.back_order_reservations:
    # Back-order path — no inventory, queued
    back_order = sale.back_order_reservations[0]
    return {
        "status": "back_ordered",
        "back_order_id": back_order.id,
        "message": "No numbers available right now. We'll notify you when one opens up.",
    }
```

**Background poller** (`app/workers/back_order_monitor.py`):
```python
async def check_back_orders():
    """Runs every 5 minutes. Checks TV for fulfilled back-orders."""
    pending = await db.execute(
        select(RentalBackOrder).where(RentalBackOrder.fulfilled_at.is_(None))
    )
    for order in pending.scalars():
        details = await tv_service.get_reservation_details(order.tv_back_order_id)
        if details.state in ("renewableActive", "nonrenewableActive"):
            order.fulfilled_at = datetime.utcnow()
            await balance_service.deduct(order.user_id, order.credits_held, reason="rental_backorder_fulfilled")
            await notification_service.send(
                user_id=order.user_id,
                type="rental_ready",
                data={"service_name": order.service_name}
            )
    await db.commit()
```

---

### Type 3 — Rental Expiry Warning

**Trigger**: Rental `ends_at` is within 24 hours.

**Flow**:
```
Expiry monitor runs every 15 minutes (already exists)
→ Query rentals where ends_at < NOW() + 24h AND expiry_warned_at IS NULL
→ Send notification: "Your rental number expires in 24 hours — renew to keep it"
→ Set expiry_warned_at = NOW()
```

**Schema addition** (add column to existing rentals table):
```sql
ALTER TABLE rentals ADD COLUMN expiry_warned_at TIMESTAMPTZ;
```

**Expiry monitor addition** (`app/workers/expiry_monitor.py`):
```python
# Add to existing expiry check loop:
expiring_soon = await db.execute(
    select(Rental).where(
        Rental.ends_at < datetime.utcnow() + timedelta(hours=24),
        Rental.expiry_warned_at.is_(None),
        Rental.status == "active"
    )
)
for rental in expiring_soon.scalars():
    await notification_service.send(
        user_id=rental.user_id,
        type="rental_expiring",
        data={"rental_id": str(rental.id), "ends_at": rental.ends_at.isoformat()}
    )
    rental.expiry_warned_at = datetime.utcnow()
await db.commit()
```

---

## UI Changes

### Verification picker — out of stock state
```html
<!-- When service is out of stock, show watch button instead of buy button -->
<button class="btn-watch-stock"
        data-service="whatsapp"
        data-capability="sms"
        onclick="watchStock(this)">
    🔔 Notify me when available
</button>
```

```javascript
async function watchStock(btn) {
    const res = await fetch('/api/notifications/stock-watch', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'X-CSRF-Token': getCsrfToken()},
        body: JSON.stringify({
            service_name: btn.dataset.service,
            capability: btn.dataset.capability
        })
    });
    if (res.ok) {
        btn.textContent = '✅ You\'ll be notified';
        btn.disabled = true;
    }
}
```

### Rental page — back-order state
When `status === "back_ordered"` in the rental creation response:
- Show "You're in the queue" state instead of error
- Show estimated wait (if TV provides it — currently unknown)
- Show "Cancel back-order" button

### Notification center
All three notification types feed into the existing notification center (already built). Add three new notification type handlers:
- `stock_available` → "WhatsApp numbers are back in stock — buy now →"
- `rental_ready` → "Your rental number for {service} is ready →"
- `rental_expiring` → "Your rental expires in 24 hours — renew →"

---

## Implementation Order

| Step | Task | File | Effort |
|------|------|------|--------|
| 1 | `stock_watches` table migration | `alembic/versions/` | 30 min |
| 2 | `StockWatch` model | `app/models/` | 15 min |
| 3 | Stock watch API endpoints (3) | `app/api/core/notifications.py` | 1h |
| 4 | Stock monitor integration | `app/services/stock_monitor.py` | 1h |
| 5 | Verification picker UI — watch button | `static/js/verification-flow.js` | 1h |
| 6 | `create_reservation()` back-order detection | `app/services/textverified_service.py` | 1h |
| 7 | `rental_back_orders` table migration | `alembic/versions/` | 30 min |
| 8 | `RentalBackOrder` model | `app/models/` | 15 min |
| 9 | Back-order monitor worker | `app/workers/back_order_monitor.py` | 2h |
| 10 | Rental page back-order UI | `templates/rentals_modern.html` | 1h |
| 11 | `expiry_warned_at` column migration | `alembic/versions/` | 15 min |
| 12 | Expiry monitor — 24h warning | `app/workers/expiry_monitor.py` | 30 min |
| 13 | Notification center — 3 new types | `templates/notification_center.html` | 1h |
| 14 | Tests | `tests/unit/`, `tests/integration/` | 2h |

**Total estimated effort**: ~12 hours

---

## Acceptance Criteria

- [ ] User on out-of-stock service sees "Notify me" button, not just an error
- [ ] User receives email + in-app notification within 2 stock monitor cycles (≤3 min) of service coming back
- [ ] Watch is auto-deleted after notification sent — no duplicate alerts
- [ ] User can cancel a watch from notification preferences
- [ ] Rental back-order is detected and stored when TV returns `back_order_reservations`
- [ ] User receives notification when back-order is fulfilled
- [ ] Credits are only deducted when back-order is fulfilled, not at request time
- [ ] Rental expiry warning fires 24h before `ends_at`
- [ ] All three notification types appear correctly in notification center
- [ ] No notification sent if user has disabled that notification type in preferences
