# Billing & Payment History API

## Overview

The billing system provides comprehensive payment processing, credit management, and transaction history tracking. It integrates with Paystack for payment processing and supports multiple payment methods including crypto.

---

## 💳 Payment Endpoints

### Initialize Payment
```bash
POST /api/billing/initialize-payment

Request Body:
{
  "amount_usd": 10.00
}

Response:
{
  "authorization_url": "https://checkout.paystack.com/...",
  "access_code": "abc123",
  "reference": "namaskah_user123_1704307200",
  "amount_usd": 10.00,
  "amount_ngn": 15000.00,
  "status": "pending"
}
```

### Verify Payment
```bash
GET /api/billing/verify-payment/{reference}

Response:
{
  "reference": "namaskah_user123_1704307200",
  "status": "success",
  "amount": 1500000,
  "paid_at": "2026-01-03T12:00:00Z",
  "credited": true,
  "amount_usd": 10.00,
  "amount_ngn": 15000.00
}
```

### Get Payment Details
```bash
GET /api/billing/payment/{reference}

Response:
{
  "reference": "namaskah_user123_1704307200",
  "amount_usd": 10.00,
  "amount_ngn": 15000.00,
  "status": "success",
  "credited": true,
  "payment_method": "paystack",
  "created_at": "2026-01-03T12:00:00Z",
  "webhook_received": true,
  "email": "user@example.com"
}
```

---

## 📜 Payment History

### Get Payment History
```bash
GET /api/billing/history?status=success&skip=0&limit=20

Query Parameters:
- status: Filter by status (pending, success, failed, refunded)
- skip: Pagination offset (default: 0)
- limit: Results per page (1-100, default: 20)

Response:
{
  "total": 45,
  "skip": 0,
  "limit": 20,
  "payments": [
    {
      "reference": "namaskah_user123_1704307200",
      "amount_usd": 10.00,
      "amount_ngn": 15000.00,
      "status": "success",
      "credited": true,
      "payment_method": "paystack",
      "created_at": "2026-01-03T12:00:00Z"
    }
  ]
}
```

### Get Payment Summary
```bash
GET /api/billing/summary

Response:
{
  "current_balance": 25.50,
  "total_paid": 100.00,
  "total_credited": 100.00,
  "successful_payments": 10,
  "failed_payments": 2,
  "pending_payments": 0,
  "total_payments": 12
}
```

---

## 💰 Credit Management

### Get Balance
```bash
GET /api/billing/balance
GET /api/user/balance

Response:
{
  "user_id": "user123",
  "credits": 25.50,
  "free_verifications": 0,
  "currency": "USD",
  "timestamp": "2026-01-03T12:00:00Z"
}
```

### Get Credit History
```bash
GET /api/user/credits/history?transaction_type=credit&skip=0&limit=20

Query Parameters:
- transaction_type: Filter by type (credit, debit, bonus, refund, transfer, admin_reset)
- skip: Pagination offset
- limit: Results per page (1-100)

Response:
{
  "total": 30,
  "skip": 0,
  "limit": 20,
  "transactions": [
    {
      "id": "txn123",
      "amount": 10.00,
      "type": "credit",
      "description": "Payment via Paystack (Ref: namaskah_user123_1704307200)",
      "created_at": "2026-01-03T12:00:00Z"
    }
  ]
}
```

### Get Credit Summary
```bash
GET /api/user/credits/summary

Response:
{
  "current_balance": 25.50,
  "total_credits_added": 100.00,
  "total_credits_deducted": 74.50,
  "total_bonuses": 5.00,
  "total_refunds": 0.00,
  "transaction_count": 30
}
```

---

## 💸 Transaction History

### Get Transactions
```bash
GET /api/billing/transactions?skip=0&limit=10

Response:
{
  "total": 50,
  "skip": 0,
  "limit": 10,
  "transactions": [
    {
      "id": "txn123",
      "amount": 2.50,
      "type": "debit",
      "description": "SMS verification - Telegram",
      "created_at": "2026-01-03T12:00:00Z"
    }
  ]
}
```

---

## 🔄 Refunds (Admin Only)

### Process Refund
```bash
POST /api/billing/refund?reference=namaskah_user123_1704307200&reason=User%20requested

Response:
{
  "reference": "namaskah_user123_1704307200",
  "status": "refunded",
  "amount_refunded": 10.00,
  "new_balance": 15.50,
  "reason": "User requested",
  "timestamp": "2026-01-03T14:00:00Z"
}
```

---

## 🪙 Crypto Payments

### Get Crypto Addresses
```bash
GET /api/billing/crypto-addresses

Response:
{
  "btc_address": "bc1q...",
  "eth_address": "0x...",
  "sol_address": "...",
  "ltc_address": "L..."
}
```

---

## 📊 Pricing Estimation

### Estimate Verification Cost
```bash
GET /api/pricing/estimate?service=telegram&country=US&quantity=5

Response:
{
  "service": "telegram",
  "country": "US",
  "quantity": 5,
  "cost_per_sms": 2.50,
  "total_cost": 12.50,
  "currency": "USD",
  "note": "Actual cost may vary based on your subscription tier"
}
```

### Get Available Services
```bash
GET /api/pricing/services

Response:
{
  "services": {
    "telegram": "Telegram",
    "whatsapp": "WhatsApp",
    "google": "Google",
    "facebook": "Facebook",
    "instagram": "Instagram",
    "twitter": "Twitter",
    "discord": "Discord",
    "tiktok": "TikTok"
  },
  "total": 8
}
```

### Get Available Countries
```bash
GET /api/pricing/countries

Response:
{
  "countries": {
    "US": "United States",
    "CA": "Canada",
    "GB": "United Kingdom",
    "DE": "Germany",
    "FR": "France"
  },
  "total": 5
}
```

---

## 🔔 Webhook Integration

### Paystack Webhook
```bash
POST /api/billing/webhook

Headers:
- x-paystack-signature: <signature>

Events Handled:
- charge.success: Credits user account
- charge.failed: Marks payment as failed

Webhook automatically:
- Verifies signature
- Updates payment status
- Credits user account (idempotent)
- Sends email receipt
- Creates in-app notification
```

---

## 💱 Currency Conversion

The system uses a fixed exchange rate:
- 1 USD = 1,500 NGN
- Amounts stored in both USD and NGN
- Paystack receives amount in Kobo (NGN × 100)

---

## 🔐 Admin Credit Operations

### Add Credits (Admin)
```bash
POST /api/user/credits/add?amount=10&description=Bonus%20credits

Response:
{
  "amount_added": 10.00,
  "old_balance": 15.50,
  "new_balance": 25.50,
  "timestamp": "2026-01-03T12:00:00Z"
}
```

### Deduct Credits (Admin)
```bash
POST /api/user/credits/deduct?amount=5&description=Manual%20adjustment

Response:
{
  "amount_deducted": 5.00,
  "old_balance": 25.50,
  "new_balance": 20.50,
  "timestamp": "2026-01-03T12:00:00Z"
}
```

### Transfer Credits (Admin)
```bash
POST /api/user/credits/transfer?to_user_id=user456&amount=10&description=Transfer

Response:
{
  "from_user_id": "user123",
  "to_user_id": "user456",
  "amount": 10.00,
  "from_user_new_balance": 10.50,
  "to_user_new_balance": 35.00,
  "timestamp": "2026-01-03T12:00:00Z"
}
```

### Reset Credits (Admin)
```bash
POST /api/user/credits/reset?new_amount=0

Response:
{
  "user_id": "user123",
  "old_balance": 10.50,
  "new_balance": 0.00,
  "timestamp": "2026-01-03T12:00:00Z"
}
```

---

## 📝 Payment Status Values

| Status | Description |
|--------|-------------|
| `pending` | Payment initiated, awaiting completion |
| `success` | Payment completed and credits added |
| `failed` | Payment failed or declined |
| `refunded` | Payment refunded to user |

---

## 🔗 Related Documentation

- [Tier Management API](TIER_MANAGEMENT_API.md) - Subscription tier management
- [API Guide](API_GUIDE.md) - Complete API reference
- [Security & Compliance](SECURITY_AND_COMPLIANCE.md) - Security details

---

**Last Updated**: January 3, 2026  
**Version**: 1.0.0
