# Voice vs SMS Verification - Technical Documentation

## Overview
This document outlines the differences between Voice and SMS verification flows in the Namaskah platform.

## Feature Comparison

| Feature | SMS Verification | Voice Verification |
|---------|-----------------|-------------------|
| **Capability** | SMS codes via text | Voice codes via phone call |
| **Countries** | 50+ countries | US only (TextVerified limitation) |
| **Tier Access** | All tiers | Starter+ (Freemium blocked) |
| **Area Code Selection** | Turbo tier | Turbo tier |
| **ISP/Carrier Filter** | Turbo tier | Turbo tier |
| **Polling Interval** | 5s initial, 10s later | 5s constant |
| **Timeout** | 20 minutes | 5 minutes |
| **Estimated Cost** | $2.00-$4.00 | $3.50 |
| **Notifications** | ✅ All events | ✅ All events |
| **Auto-Polling** | ✅ Background service | ✅ Background service |
| **Retry Logic** | ✅ 3 attempts | ✅ 3 attempts |

## API Endpoints

### Unified Status Endpoint
```
GET /api/verification/{id}
```
Works for both SMS and Voice verifications. Returns:
```json
{
  "verification_id": "uuid",
  "status": "pending|completed|failed",
  "phone_number": "+1234567890",
  "sms_code": "123456",
  "capability": "sms|voice",
  "cost": 3.50
}
```

### Voice Creation Endpoint
```
POST /api/verification/voice/create
```
Request:
```json
{
  "service": "google",
  "area_code": "415",  // Turbo only
  "carrier": "verizon" // Turbo only
}
```

## Configuration

### Environment Variables
```bash
# Voice polling settings
VOICE_POLLING_INTERVAL_SECONDS=5
VOICE_POLLING_TIMEOUT_MINUTES=5
VOICE_ESTIMATED_COST=3.50
VOICE_MAX_RETRY_ATTEMPTS=3
```

### Settings Class
```python
from app.core.config import get_settings
settings = get_settings()

# Access voice settings
settings.voice_polling_interval_seconds  # 5
settings.voice_polling_timeout_minutes   # 5
settings.voice_estimated_cost            # 3.50
settings.voice_max_retry_attempts        # 3
```

## Polling Services

### SMS Polling Service
- **File**: `app/services/sms_polling_service.py`
- **Interval**: 5s initial, 10s after 10 attempts
- **Timeout**: 20 minutes
- **Features**: Adaptive polling, per-verification tasks

### Voice Polling Service
- **File**: `app/services/voice_polling_service.py`
- **Interval**: 5s constant
- **Timeout**: 5 minutes (voice calls are faster)
- **Features**: Retry logic, safe notifications, context manager

## Error Handling

### Retry Logic
Both services implement exponential backoff:
```python
for attempt in range(settings.voice_max_retry_attempts):
    try:
        result = api_call()
        break
    except Exception as e:
        if attempt == settings.voice_max_retry_attempts - 1:
            raise
        await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s
```

### Safe Notifications
Notifications wrapped in try/except to prevent verification failure:
```python
try:
    notification_service.create_notification(...)
except Exception as notif_error:
    logger.warning(f"Notification failed: {notif_error}")
    # Verification continues successfully
```

### Database Connection Management
Using context manager to prevent leaks:
```python
with get_db_session() as db:
    # DB operations
    # Automatic cleanup on exception
```

## Tier Restrictions

### Freemium
- SMS: ✅ Random numbers only
- Voice: ❌ Blocked

### Starter ($9/mo)
- SMS: ✅ Area code selection
- Voice: ✅ Basic voice verification

### Turbo ($13.99/mo)
- SMS: ✅ Area code + ISP/carrier
- Voice: ✅ Area code + ISP/carrier

## Monitoring

### Metrics to Track
```python
# Voice verification metrics
voice_verifications_created_total
voice_verifications_completed_total
voice_verifications_failed_total
voice_polling_duration_seconds
voice_api_retry_attempts_total
```

### Logs to Monitor
```bash
# Success
[voice_polling] Voice code received: {verification_id}

# Timeout
[voice_polling] Voice verification timeout: {verification_id}

# API Failure
[voice_polling] Failed to poll voice verification {id} after 3 attempts

# Notification Failure (non-critical)
[voice_verification] Notification failed but verification succeeded
```

## Best Practices

### 1. Always Check Balance First
```python
if user.credits < settings.voice_estimated_cost:
    raise HTTPException(status_code=402, detail="Insufficient credits")
```

### 2. Use Config Values
```python
# ❌ Bad
await asyncio.sleep(5)

# ✅ Good
await asyncio.sleep(settings.voice_polling_interval_seconds)
```

### 3. Safe Notifications
```python
try:
    notification_service.create_notification(...)
except Exception as e:
    logger.warning(f"Notification failed: {e}")
    # Don't raise - verification succeeded
```

### 4. Retry External API Calls
```python
for attempt in range(settings.voice_max_retry_attempts):
    try:
        result = external_api_call()
        break
    except Exception:
        if attempt == settings.voice_max_retry_attempts - 1:
            raise
        await asyncio.sleep(2 ** attempt)
```

## Troubleshooting

### Voice Codes Not Arriving
1. Check TextVerified API status
2. Verify polling service is running: `ps aux | grep voice_polling`
3. Check logs: `tail -f logs/app.log | grep voice_polling`
4. Verify timeout settings: 5 minutes may be too short for some services

### High API Failure Rate
1. Check retry attempts: `settings.voice_max_retry_attempts`
2. Increase backoff time in retry logic
3. Implement circuit breaker pattern
4. Monitor TextVerified API health

### Database Connection Leaks
1. Verify context manager usage in polling service
2. Check for unclosed sessions: `SELECT * FROM pg_stat_activity`
3. Monitor connection pool: `settings.database_pool_size`

## Future Improvements

### Priority 1: Unified Polling Service
Merge SMS and Voice polling into single service:
```python
class VerificationPollingService:
    async def poll_verification(self, verification):
        if verification.capability == "voice":
            return await self._poll_voice(verification)
        else:
            return await self._poll_sms(verification)
```

### Priority 2: Circuit Breaker
Prevent cascading failures:
```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def poll_textverified_api(self, activation_id):
    return self.tv_service.client.verifications.get(activation_id)
```

### Priority 3: Metrics & Observability
Add Prometheus metrics:
```python
from prometheus_client import Counter, Histogram

voice_polls_total = Counter('voice_polls_total', 'Total voice polls')
voice_poll_duration = Histogram('voice_poll_duration_seconds', 'Poll duration')
```

## References

- [TextVerified API Documentation](https://docs.textverified.com)
- [SMS Polling Service](../app/services/sms_polling_service.py)
- [Voice Polling Service](../app/services/voice_polling_service.py)
- [Configuration Settings](../app/core/config.py)
