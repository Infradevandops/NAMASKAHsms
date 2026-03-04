# Billing Tab — Missing Features

## 1. Invoice Download
- [ ] Add "Download PDF" button per payment row in Payment History
- [ ] Backend: `GET /api/wallet/invoice/{transaction_id}` — generate PDF receipt (amount, date, reference, user email)
- [ ] Use a lightweight lib (e.g. `reportlab` or `weasyprint`)

## 2. Subscription Renewal Info
- [ ] For Pro/Custom users: show "Renews on {date}" below current plan
- [ ] Add "Cancel Subscription" button (with confirmation modal)
- [ ] Backend: `POST /api/billing/tiers/cancel` — downgrades to freemium at period end
- [ ] Store `subscription_renews_at` on `UserPreference` or `User` model

## 3. Billing Email & Address
- [ ] Add form fields in Billing tab: Billing Email, Billing Address
- [ ] Pre-populate from `UserPreference.billing_email` / `UserPreference.billing_address`
- [ ] Save via `PUT /api/user/settings` (extend payload to include billing fields)

## 4. Payment Method — Card on File
- [ ] Add "Payment Methods" section to Billing tab
- [ ] Modal to add/save card via Paystack's card tokenization (`authorization_code`)
- [ ] Display saved card (last 4 digits, expiry, card type)
- [ ] Allow removing saved card
- [ ] Backend: store `paystack_authorization_code`, `card_last4`, `card_type`, `card_expiry` on `UserPreference`
- [ ] Backend: `DELETE /api/billing/payment-method` — remove saved card

## 5. Auto-Recharge
- [ ] Move auto-recharge UI from Wallet page into Billing tab (single source of truth)
- [ ] Toggle: enable/disable auto-recharge
- [ ] Fields: threshold (recharge when balance drops below $X), recharge amount
- [ ] Requires saved card on file — show warning if no card saved
- [ ] Backend: `PUT /api/user/settings` already has `auto_recharge` / `recharge_amount` on `UserPreference` — wire up

## 6. Spending Limit / Low-Balance Alert
- [ ] Add "Spending Alerts" section to Billing tab
- [ ] Monthly spending cap: warn or block when exceeded
- [ ] Low-balance alert threshold: email when balance drops below $X
- [ ] Backend: store `spending_limit`, `low_balance_threshold` on `UserPreference`
- [ ] Backend: `PUT /api/user/settings` — extend to save these fields
- [ ] Trigger: check thresholds in payment service after each debit

## 7. Payment Method Gate (API users / Pro+)
- [ ] Middleware/dependency: `require_payment_method` — blocks API key usage if no card on file and balance < threshold
- [ ] Show banner in API Keys tab: "Add a payment method to keep your API access uninterrupted"
- [ ] Show banner in Billing tab if Pro/Custom with no saved card
- [ ] Backend: `GET /api/billing/payment-method/status` — returns `{ has_card: bool, card_last4, auto_recharge_enabled }`
