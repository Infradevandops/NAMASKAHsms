# Design Document: TextVerified Integration

## Overview

The TextVerified Integration module provides a robust interface for the Namaskah SMS application to interact with the TextVerified API service. This design establishes a service-oriented architecture that encapsulates all TextVerified API interactions, providing a clean abstraction layer for the rest of the application.

The integration handles:
- API credential management and validation
- Account balance retrieval and caching
- Health check endpoint for service monitoring
- Comprehensive error handling and resilience
- Audit logging for all API interactions

## Architecture

The TextVerified Integration follows a layered architecture:

```
┌─────────────────────────────────────────┐
│         API Endpoints Layer             │
│  (FastAPI routes for health checks)     │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      TextVerified Service Layer         │
│  (Business logic and API orchestration) │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│    TextVerified Client Layer            │
│  (Official Python SDK wrapper)          │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      TextVerified API (External)        │
│  (Third-party service)                  │
└─────────────────────────────────────────┘
```

### Key Design Principles

1. **Separation of Concerns**: API endpoints are separate from business logic
2. **Dependency Injection**: Configuration is injected, not hardcoded
3. **Error Resilience**: All external API calls are wrapped with error handling
4. **Observability**: All operations are logged for debugging and auditing
5. **Caching**: Balance information is cached to reduce API calls
6. **Graceful Degradation**: Service remains operational even if TextVerified is unavailable

## Components and Interfaces

### 1. TextVerified Service (`app/services/textverified_service.py`)

**Responsibility**: Encapsulates all TextVerified API interactions

**Key Methods**:
- `__init__()` - Initialize service with credentials from environment
- `get_balance()` - Retrieve account balance
- `buy_number(country, service)` - Purchase a phone number
- `check_sms(activation_id)` - Check for received SMS
- `cancel_activation(activation_id)` - Release a phone number
- `get_pricing(country, service)` - Get service pricing

**Configuration**:
- Reads `TEXTVERIFIED_API_KEY` from environment
- Reads `TEXTVERIFIED_EMAIL` from environment
- Validates credentials on initialization
- Logs initialization status

### 2. Health Check Endpoint (`app/api/verification/textverified_endpoints.py`)

**Endpoint**: `GET /api/verification/textverified/health`

**Response Format**:
```json
{
  "status": "operational",
  "balance": 100.50,
  "currency": "USD",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Error Response** (503 Service Unavailable):
```json
{
  "error": "TextVerified service unavailable",
  "details": "Connection timeout",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 3. Configuration Management

**Environment Variables**:
- `TEXTVERIFIED_API_KEY` - API authentication key
- `TEXTVERIFIED_EMAIL` - Account email for authentication

**Validation**:
- Both variables must be present for service to be enabled
- Service logs warning if credentials are missing
- Service gracefully disables if credentials are invalid

## Data Models

### Health Check Response

```python
class HealthCheckResponse(BaseModel):
    status: str  # "operational" or "error"
    balance: Optional[float]  # Account balance in USD
    currency: str  # "USD"
    timestamp: datetime
    error: Optional[str]  # Error message if status is "error"
    details: Optional[str]  # Additional error details
```

### Balance Response

```python
class BalanceResponse(BaseModel):
    balance: float  # Numeric balance value
    currency: str  # "USD"
    cached: bool  # Whether this is cached data
    cache_expires_at: Optional[datetime]
```

## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: Configuration Loading
*For any* environment with TextVerified credentials set, the TextVerified service SHALL successfully load both the API key and email from environment variables.
**Validates: Requirements 1.1, 1.2**

### Property 2: Credential Validation
*For any* TextVerified service instance, if credentials are present and valid, the service SHALL initialize successfully and set enabled flag to true.
**Validates: Requirements 1.4, 1.5**

### Property 3: Missing Credentials Handling
*For any* environment where TextVerified credentials are missing, the service SHALL log a warning and set enabled flag to false without raising an exception.
**Validates: Requirements 1.3**

### Property 4: Health Check Response Format
*For any* successful health check call, the response SHALL contain status, balance (as float), and currency fields, with HTTP status 200.
**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

### Property 5: Balance Data Type
*For any* balance retrieved from the API, the returned value SHALL be a floating-point number representing USD currency.
**Validates: Requirements 3.1, 3.2, 3.3**

### Property 6: Error Response Format
*For any* API error, the system SHALL return an appropriate HTTP status code (401 for auth errors, 503 for unavailability) with descriptive error details.
**Validates: Requirements 2.6, 2.7, 4.2**

### Property 7: Exception Handling
*For any* TextVerified API call that fails, the system SHALL catch the exception, log it with full details, and return a user-friendly error message without crashing.
**Validates: Requirements 4.1, 4.3, 4.5**

### Property 8: Balance Caching
*For any* balance retrieval within a 5-minute window, subsequent calls SHALL return cached data without making additional API calls.
**Validates: Requirements 3.5**

### Property 9: Initialization Logging
*For any* TextVerified service initialization, the system SHALL log the initialization attempt and result (success or failure) with relevant details.
**Validates: Requirements 5.1, 5.2, 5.3**

### Property 10: API Call Logging
*For any* API call made by the TextVerified service, the system SHALL log the call details including method, parameters, response status, and any errors.
**Validates: Requirements 5.4, 5.5**

## Error Handling

### Error Categories

1. **Configuration Errors**
   - Missing API key or email
   - Invalid credentials format
   - Response: Log warning, disable service gracefully

2. **Connection Errors**
   - Network timeout
   - DNS resolution failure
   - Response: HTTP 503, retry with exponential backoff

3. **Authentication Errors**
   - Invalid API key
   - Expired credentials
   - Response: HTTP 401, log security event

4. **API Errors**
   - Invalid parameters
   - Rate limiting
   - Service errors
   - Response: HTTP 400/429/500, descriptive error message

### Retry Strategy

- **Timeout Errors**: Retry up to 3 times with exponential backoff (1s, 2s, 4s)
- **Rate Limiting**: Retry with longer backoff (10s, 20s, 40s)
- **Transient Errors**: Retry up to 2 times
- **Permanent Errors**: No retry, return error immediately

### Logging Strategy

All errors are logged with:
- Error type and message
- Stack trace (for debugging)
- Request parameters (sanitized)
- Response details
- Timestamp
- Request ID (for tracing)

## Testing Strategy

### Unit Testing

Unit tests verify individual components in isolation:

1. **Configuration Loading Tests**
   - Test loading API key from environment
   - Test loading email from environment
   - Test handling missing credentials
   - Test credential validation

2. **Service Initialization Tests**
   - Test successful initialization
   - Test initialization with missing credentials
   - Test initialization with invalid credentials
   - Test logging during initialization

3. **Error Handling Tests**
   - Test exception catching
   - Test error message formatting
   - Test logging of errors
   - Test graceful degradation

4. **Response Format Tests**
   - Test health check response structure
   - Test balance response structure
   - Test error response structure

### Property-Based Testing

Property-based tests verify universal properties across many inputs:

1. **Configuration Property Test**
   - Generate random valid credentials
   - Verify service loads them correctly
   - Verify service is enabled

2. **Health Check Property Test**
   - Generate random balance values
   - Verify response contains all required fields
   - Verify balance is numeric
   - Verify status is "operational"

3. **Error Handling Property Test**
   - Generate random error scenarios
   - Verify errors are caught and logged
   - Verify user-friendly messages are returned
   - Verify application doesn't crash

4. **Caching Property Test**
   - Retrieve balance multiple times within 5 minutes
   - Verify subsequent calls return cached data
   - Verify cache expires after 5 minutes

### Testing Framework

- **Unit Tests**: pytest with fixtures
- **Property Tests**: hypothesis for property-based testing
- **Mocking**: unittest.mock for external API calls
- **Coverage Target**: 85%+ code coverage

## Implementation Notes

### Dependencies

- `textverified` - Official TextVerified Python SDK
- `fastapi` - Web framework
- `sqlalchemy` - Database ORM
- `pydantic` - Data validation

### Configuration

TextVerified credentials are loaded from environment variables:
```bash
TEXTVERIFIED_API_KEY=your_api_key_here
TEXTVERIFIED_EMAIL=your_email@example.com
```

### Caching

Balance is cached using the unified cache system:
- Cache key: `textverified:balance`
- TTL: 5 minutes
- Invalidation: Manual or on error

### Logging

All operations are logged to `app.services.textverified_service`:
- INFO: Successful operations
- WARNING: Configuration issues
- ERROR: API failures and exceptions
- DEBUG: Detailed request/response information

