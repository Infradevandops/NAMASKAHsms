# Tier Management API Documentation

## Overview
The NamasKAH SMS platform offers 3 subscription tiers with progressively advanced features:
- **Freemium** (Free - No card required)
- **Starter** ($9/mo)
- **Turbo** ($13.99/mo)

---

## Authentication
All tier management endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

---

## Endpoints

### List Available Tiers
Get information about all available subscription tiers.

**Endpoint:** `GET /api/tiers`

**Authentication:** Not required

**Response:**
```json
[
  {
    "name": "Freemium",
    "tier": "freemium",
    "price_monthly": 0,
    "price_display": "Free",
    "payment_required": false,
    "has_api_access": false,
    "has_area_code_selection": false,
    "has_isp_filtering": false,
    "api_key_limit": 0,
    "daily_verification_limit": 100,
    "country_limit": 5
  },
  ...
]
```

---

### Get Current User Tier
Get the authenticated user's current subscription tier and upgrade options.

**Endpoint:** `GET /api/tiers/current`

**Authentication:** Required

**Response:**
```json
{
  "current_tier": "freemium",
  "tier_name": "Freemium",
  "upgraded_at": null,
  "expires_at": null,
  "days_remaining": null,
  "can_upgrade": true,
  "upgrade_options": ["starter", "turbo"]
}
```

---

### Upgrade Tier
Upgrade to a higher subscription tier.

**Endpoint:** `POST /api/tiers/upgrade`

**Authentication:** Required

**Request Body:**
```json
{
  "target_tier": "starter",  // or "turbo"
  "payment_method_id": "pm_xxxxx"  // Optional Stripe payment method
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Successfully upgraded to Starter tier",
  "new_tier": "starter",
  "expires_at": "2026-01-07T20:57:00Z",
  "payment_required": true,
  "amount_charged": 900
}
```

**Error Response (400 - Invalid upgrade path):**
```json
{
  "detail": "Cannot upgrade from turbo to starter"
}
```

---

### Downgrade Tier
Cancel subscription and return to Freemium tier.

**Endpoint:** `POST /api/tiers/downgrade`

**Authentication:** Required

**Response:**
```json
{
  "success": true,
  "message": "Downgraded to Freemium tier"
}
```

---

## API Key Management

### List API Keys
Get list of all active API keys for the authenticated user.

**Endpoint:** `GET /api/keys`

**Authentication:** Required

**Tier Requirement:** Starter or higher

**Response:**
```json
[
  {
    "id": "key-id-123",
    "name": "Production API Key",
    "key_preview": "...a1b2",
    "is_active": true,
    "request_count": 1523,
    "last_used": "2025-12-07T19:30:00Z",
    "created_at": "2025-11-01T10:00:00Z"
  }
]
```

**Error Response (402 - Freemium user):**
```json
{
  "detail": "API key access requires Starter tier or higher. Please upgrade."
}
```

---

### Generate API Key
Create a new API key.

**Endpoint:** `POST /api/keys/generate`

**Authentication:** Required

**Tier Requirement:** Starter (max 5 keys) or Turbo (unlimited)

**Request Body:**
```json
{
  "name": "My Development Key"
}
```

**Success Response (201):**
```json
{
  "id": "key-id-456",
  "name": "My Development Key",
  "key": "nmsk_aBcDeFgHiJkLmNoPqRsTuVwXyZ123456",  // Only shown once!
  "key_preview": "...3456",
  "created_at": "2025-12-07T20:57:00Z"
}
```

> **⚠️ IMPORTANT:** The full API key is only returned once during creation. Store it securely!

**Error Response (429 - Limit reached):**
```json
{
  "detail": "API key limit reached (5 keys for Starter tier)"
}
```

---

### Revoke API Key
Delete an API key.

**Endpoint:** `DELETE /api/keys/{key_id}`

**Authentication:** Required

**Response:**
```json
{
  "success": true,
  "message": "API key revoked successfully"
}
```

---

### Rotate API Key
Generate a new API key and revoke the old one.

**Endpoint:** `POST /api/keys/{key_id}/rotate`

**Authentication:** Required

**Response:**
```json
{
  "id": "new-key-id",
  "name": "My Development Key",
  "key": "nmsk_newKeyGoesHere123",  // Only shown once!
  "key_preview": "...e123",
  "created_at": "2025-12-07T21:00:00Z"
}
```

---

## Feature Access Endpoints

### Get Available Area Codes
Get list of area codes for a country (Starter+ tier).

**Endpoint:** `GET /api/verification/area-codes/{country}`

**Authentication:** Required

**Tier Requirement:** Starter or higher

**Example:** `GET /api/verification/area-codes/US`

**Response:**
```json
{
  "success": true,
  "country": "US",
  "area_codes": ["212", "310", "415", "646", "917"],
  "tier": "starter"
}
```

**Error (Freemium user):**
```json
{
  "detail": {
    "error": "feature_locked",
    "message": "Area code selection requires Starter tier or higher",
    "current_tier": "freemium",
    "required_tier": "starter",
    "upgrade_url": "/api/tiers/upgrade",
    "upgrade_price": "$9/mo"
  }
}
```

---

### Get Available Carriers
Get list of ISPs/carriers for a country (Turbo tier only).

**Endpoint:** `GET /api/verification/carriers/{country}`

**Authentication:** Required

**Tier Requirement:** Turbo only

**Example:** `GET /api/verification/carriers/US`

**Response:**
```json
{
  "success": true,
  "country": "US",
  "carriers": ["Verizon", "AT&T", "T-Mobile", "Sprint"],
  "tier": "turbo"
}
```

**Error (Starter user):**
```json
{
  "detail": {
    "error": "feature_locked",
    "message": "ISP/Carrier filtering is a Turbo tier exclusive feature",
    "current_tier": "starter",
    "required_tier": "turbo",
    "upgrade_url": "/api/tiers/upgrade",
    "upgrade_price": "$13.99/mo"
  }
}
```

---

## Using API Keys

Once you have an API key, use it instead of Bearer token:

```bash
# Using API key
curl -H "X-API-Key: nmsk_yourKeyHere" \
  https://api.namaskah.com/api/verification/pricing?service=telegram

# Or in Authorization header
curl -H "Authorization: Bearer nmsk_yourKeyHere" \
  https://api.namaskah.com/api/verification/pricing?service=telegram
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| 401 | Unauthorized - Invalid or missing authentication |
| 402 | Payment Required - Feature requires tier upgrade |
| 429 | Too Many Requests - Rate limit or quota exceeded |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error |

---

## Rate Limits

Rate limits vary by tier:

| Tier | Per Minute | Per Hour |
|------|-----------|----------|
| Freemium | 10 | 100 |
| Starter | 50 | 1,000 |
| Turbo | 200 | 10,000 |

---

## Best Practices

1. **Store API keys securely** - Never commit keys to version control
2. **Rotate keys regularly** - Use the rotation endpoint
3. **Monitor usage** - Check key usage stats regularly
4. **Handle 402 errors** - Implement upgrade prompts in your app
5. **Respect rate limits** - Implement exponential backoff

---

## Migration Guide

### Upgrading from Freemium to Starter
1. Call `POST /api/tiers/upgrade` with `target_tier: "starter"`
2. Provide payment method if required
3. Generate API keys via `POST /api/keys/generate`
4. Start using area code selection in verification requests

### Upgrading from Starter to Turbo
1. Call `POST /api/tiers/upgrade` with `target_tier: "turbo"`
2. Access ISP filtering via `/api/verification/carriers`
3. Generate unlimited API keys as needed

---

For questions or support, contact: support@namaskah.com
