# Namaskah SMS API Guide

**Version**: 2.5.0  
**Last Updated**: 2026-01-18

---

## API Versions

### Current Version (v1)
- **Base URL**: `/api/v1`
- **Status**: Stable
- **Documentation**: Use this guide for all new integrations.

### Legacy API (Deprecated)
- **Base URL**: `/api` (various endpoints)
- **Status**: Deprecated
- **End of Life**: v5.0
- **Note**: All legacy endpoints will return a `Deprecation-Warning` header. Please migrate to `/api/v1`.

---

## Authentication

### JWT Token
All protected endpoints require a JWT token in the `Authorization` header:

```
Authorization: Bearer <token>
```

### Token Expiry
- Access tokens expire after 24 hours
- Refresh tokens expire after 7 days

---

## Response Format

### Success Response
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {}
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message",
  "detail": "Detailed error information",
  "status_code": 400
}
```

---

## Endpoints

### Authentication

#### Register User
- **POST** `/api/v1/auth/register`
- **Body**: `{"email": "user@example.com", "password": "password123"}`
- **Response**: User object with access token

#### Login
- **POST** `/api/v1/auth/login`
- **Body**: `{"email": "user@example.com", "password": "password123"}`
- **Response**: User object with access token

### Verification

#### Create Verification
- **POST** `/api/v1/verify/create`
- **Auth**: Required
- **Body**: `{"service_name": "telegram", "country": "US"}`
- **Response**: Verification object

#### Get Verification Status
- **GET** `/api/v1/verify/{verification_id}`
- **Response**: Verification object

#### Get Verification History
- **GET** `/api/v1/verify/history`
- **Auth**: Required
- **Response**: List of verifications

#### Cancel Verification
- **DELETE** `/api/v1/verify/{verification_id}`
- **Auth**: Required
- **Response**: Success message

### Billing

#### Add Credits
- **POST** `/api/v1/billing/add-credits`
- **Auth**: Required
- **Body**: `{"amount": 50}`
- **Response**: Transaction object

#### Get Balance
- **GET** `/api/v1/user/balance`
- **Auth**: Required
- **Response**: Balance object

### System

#### Health Check
- **GET** `/api/v1/system/health`
- **Response**: Health status

#### Get Countries
- **GET** `/api/v1/countries/`
- **Response**: List of countries

---

## Error Codes

| Code | Message | Description |
|------|---------|-------------|
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 402 | Payment Required | Insufficient credits |
| 403 | Forbidden | CSRF token invalid |
| 404 | Not Found | Resource not found |
| 422 | Validation Error | Invalid input data |
| 500 | Internal Server Error | Server error |

---

## Rate Limiting

- **Limit**: 100 requests per hour
- **Header**: `X-RateLimit-Remaining`

---

## CSRF Protection

All state-changing requests (POST, PUT, DELETE) require a CSRF token:

```
X-CSRF-Token: <token>
```

Token is provided in response headers and cookies.

---

## Examples

### Register and Get Token
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

### Create Verification
```bash
curl -X POST http://localhost:8000/verify/create \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"service_name": "telegram", "country": "US"}'
```

### Add Credits
```bash
curl -X POST http://localhost:8000/api/billing/add-credits \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"amount": 50}'
```

---

## Best Practices

1. **Store tokens securely** - Use httpOnly cookies or secure storage
2. **Refresh tokens** - Refresh before expiry
3. **Handle errors** - Check error responses and retry appropriately
4. **Rate limiting** - Implement exponential backoff
5. **CSRF protection** - Always include CSRF token for state-changing requests

---

## Support

For issues or questions, contact support@namaskah.app

## Tier-Gated Endpoints

### Requires: payg+
- GET /api/keys
- POST /api/keys/generate
- GET /api/affiliate/stats

### Requires: pro+
- POST /api/verify/bulk
- GET /api/analytics/advanced
