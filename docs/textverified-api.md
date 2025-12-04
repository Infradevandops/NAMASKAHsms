# TextVerified API Documentation

## Overview

The TextVerified integration provides endpoints for monitoring the TextVerified SMS verification service status and account balance.

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TEXTVERIFIED_API_KEY` | API key for TextVerified authentication | Yes |
| `TEXTVERIFIED_EMAIL` | Email address for TextVerified account | Yes |

### Example Configuration

```bash
# .env file
TEXTVERIFIED_API_KEY=your_api_key_here
TEXTVERIFIED_EMAIL=your_email@example.com
```

## Endpoints

### Health Check

Check the operational status of the TextVerified service.

**Endpoint:** `GET /api/verification/textverified/health`

**Response (200 OK):**
```json
{
  "status": "operational",
  "balance": 100.50,
  "currency": "USD",
  "timestamp": "2024-01-15T10:30:00.000000"
}
```

**Response (401 Unauthorized):**
```json
{
  "detail": {
    "error": "Invalid credentials",
    "details": "TextVerified not configured",
    "timestamp": "2024-01-15T10:30:00.000000"
  }
}
```

**Response (503 Service Unavailable):**
```json
{
  "detail": {
    "error": "TextVerified service unavailable",
    "details": "Connection timeout",
    "timestamp": "2024-01-15T10:30:00.000000"
  }
}
```

### Account Balance

Retrieve the current TextVerified account balance.

**Endpoint:** `GET /api/verification/textverified/balance`

**Response (200 OK):**
```json
{
  "balance": 100.50,
  "currency": "USD",
  "cached": false
}
```

**Response (503 Service Unavailable):**
```json
{
  "detail": {
    "error": "Failed to retrieve balance",
    "details": "API Error",
    "timestamp": "2024-01-15T10:30:00.000000"
  }
}
```

### Service Status (Legacy)

Simple status check endpoint.

**Endpoint:** `GET /api/verification/textverified/status`

**Response (200 OK):**
```json
{
  "status": "operational"
}
```

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Service status: "operational" or "error" |
| `balance` | float | Account balance in USD |
| `currency` | string | Currency code (always "USD") |
| `timestamp` | string | ISO 8601 timestamp |
| `cached` | boolean | Whether balance is from cache |
| `error` | string | Error message (only on error) |
| `details` | string | Additional error details (only on error) |

## Caching

Balance information is cached for 5 minutes to reduce API calls. The `cached` field indicates whether the returned balance is from cache.

## Error Handling

The API uses standard HTTP status codes:

| Code | Description |
|------|-------------|
| 200 | Success |
| 401 | Invalid or missing credentials |
| 503 | Service unavailable |

All errors include descriptive messages to help with troubleshooting.

## Troubleshooting

### Common Issues

1. **"TextVerified not configured"**
   - Ensure `TEXTVERIFIED_API_KEY` and `TEXTVERIFIED_EMAIL` are set
   - Verify the values are correct

2. **"Connection timeout"**
   - Check network connectivity
   - Verify TextVerified service is operational

3. **"Invalid credentials"**
   - Verify API key is valid
   - Check email matches TextVerified account

### Debugging Steps

1. Check environment variables are loaded:
   ```bash
   echo $TEXTVERIFIED_API_KEY
   echo $TEXTVERIFIED_EMAIL
   ```

2. Test the health endpoint:
   ```bash
   curl http://localhost:8000/api/verification/textverified/health
   ```

3. Check application logs for detailed error messages

4. Verify TextVerified account status at https://textverified.com
