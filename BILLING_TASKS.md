# Billing Tab — Missing Features

## 1. Invoice Download
- [x] Add "Download PDF" button per payment row in Payment History
- [x] Backend: `GET /api/wallet/invoice/{transaction_id}` — generate JSON receipt (amount, date, reference, user email)
- [x] Upgrade to true PDF (e.g. `reportlab`) — `reportlab==4.2.5` added to requirements

## 2. Subscription Renewal Info
- [x] For Pro/Custom users: show "Renews on {date}" below current plan
- [x] Add "Cancel Subscription" button (with confirmation modal)
- [x] Backend: `POST /api/billing/tiers/cancel` — downgrades to freemium at period end
- [x] Store `subscription_renews_at` on `UserPreference`

## 3. Billing Email & Address
- [x] Add form fields in Billing tab: Billing Email, Billing Address
- [x] Pre-populate from `UserPreference.billing_email` / `UserPreference.billing_address`
- [x] Save via `PUT /api/user/settings`

## 4. Payment Method — Card on File
- [x] Add "Payment Methods" section to Billing tab
- [x] Modal to add/save card via Paystack's card tokenization (`authorization_code`)
- [x] Display saved card (last 4 digits, expiry, card type)
- [x] Allow removing saved card
- [x] Backend: store `paystack_authorization_code`, `card_last4`, `card_type`, `card_expiry` on `UserPreference`
- [x] Backend: `DELETE /api/billing/payment-method` — remove saved card

## 5. Auto-Recharge
- [x] Auto-recharge UI in Billing tab (single source of truth)
- [x] Toggle: enable/disable auto-recharge
- [x] Fields: threshold, recharge amount
- [x] Warning if no card saved
- [x] Backend: `PUT /api/user/settings` wired to `UserPreference`

## 6. Spending Limit / Low-Balance Alert
- [x] "Spending Alerts" section in Billing tab
- [x] Monthly spending cap: blocks debit when exceeded (`credit_service.deduct_credits`)
- [x] Low-balance alert threshold: email sent via `EmailNotificationService` after each debit
- [x] Backend: `spending_limit`, `low_balance_alert_threshold` on `UserPreference`
- [x] Backend: `PUT /api/user/settings` saves these fields

## 7. Payment Method Gate (API users / Pro+)
- [x] Banner in API Keys tab: "Add a payment method to keep your API access uninterrupted"
- [x] Banner in Billing tab if Pro/Custom with no saved card
- [x] Backend: `GET /api/billing/payment-method/status` — returns `{ has_card, card_last4, auto_recharge_enabled }`
- [x] `require_payment_method` hard-block dependency on list/generate API key routes
